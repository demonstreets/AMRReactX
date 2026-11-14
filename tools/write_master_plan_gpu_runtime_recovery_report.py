#!/usr/bin/env python3
"""Write/verify GPU runtime recovery diagnostics for the master-plan evidence chain."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_DEFERRED = "DEFERRED-MASTER-PLAN-GPU-RUNTIME-RECOVERY-REQUIRES-DRIVER-RELOAD"
STATUS_READY = "PASS-MASTER-PLAN-GPU-RUNTIME-READY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/gpu_diagnostic")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "gpu_runtime_recovery_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "gpu_runtime_recovery_report.md"
DEFAULT_VERSION_LOG = DEFAULT_ROOT / "nvidia_runtime_version_diagnostic.log"
DEFAULT_VERSION_SUMMARY = DEFAULT_ROOT / "nvidia_runtime_version_diagnostic_summary.json"
DEFAULT_RELOAD_LOG = DEFAULT_ROOT / "nvidia_reload_preflight.log"
DEFAULT_RELOAD_SUMMARY = DEFAULT_ROOT / "nvidia_reload_preflight_summary.json"
DEFAULT_CUDA_LOG = DEFAULT_ROOT / "cuda_preflight_diagnostic.log"
DEFAULT_CUDA_EXITCODE = DEFAULT_ROOT / "cuda_preflight_diagnostic.exitcode"


class GpuRecoveryError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GpuRecoveryError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GpuRecoveryError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GpuRecoveryError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def read_exitcode(path: Path) -> int:
    require(path.is_file(), f"missing exitcode evidence: {path}")
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    require(text.isdigit(), f"invalid exitcode in {path}: {text!r}")
    return int(text)


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    version_log = Path(args.version_log)
    version_summary_path = Path(args.version_summary)
    reload_log = Path(args.reload_log)
    reload_summary_path = Path(args.reload_summary)
    cuda_log = Path(args.cuda_log)
    cuda_exitcode_path = Path(args.cuda_exitcode)

    version_summary = load_json(version_summary_path)
    reload_summary = load_json(reload_summary_path)
    cuda_exitcode = read_exitcode(cuda_exitcode_path)

    mismatch = version_summary.get("diagnosis") == "loaded_kernel_module_version_differs_from_user_space_nvml"
    no_device_users = reload_summary.get("nvidia_device_users_detected") is False
    cuda_runtime_ready = cuda_exitcode == 0 and not mismatch

    status = STATUS_READY if cuda_runtime_ready else STATUS_DEFERRED
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "current_cuda_runtime_ready": cuda_runtime_ready,
            "cuda_require_preflight_exitcode": cuda_exitcode,
            "nvidia_smi_driver_library_mismatch": version_summary.get("nvidia_smi_driver_library_mismatch"),
            "kernel_module_version_proc": version_summary.get("kernel_module_version_proc"),
            "nvml_library_version_reported_by_nvidia_smi": version_summary.get(
                "nvml_library_version_reported_by_nvidia_smi"
            ),
            "modinfo_nvidia_version": version_summary.get("modinfo_nvidia_version"),
            "nvidia_device_users_detected": reload_summary.get("nvidia_device_users_detected"),
            "reload_action_recommended": reload_summary.get("reload_action_recommended"),
            "recovery_recommendation": (
                "Reboot the server or, with administrator approval and after confirming no GPU users, "
                "reload the NVIDIA kernel modules so the loaded kernel module matches the 580.173 user-space NVML libraries. "
                "After recovery, rerun tools/codex_preflight_environment.sh --require-cuda and the relevant CUDA smoke/engineering GPU cases."
            ),
            "hot_reload_preflight_note": (
                "No /dev/nvidia* users were detected by the preflight, but nvidia_drm/nvidia_modeset are loaded; "
                "a reboot is preferred over hot reload for this workstation state."
            ) if no_device_users else (
                "GPU device users were detected; do not hot reload until those jobs are stopped."
            ),
        },
        "evidence_files": [
            evidence_entry("nvidia_runtime_version_diagnostic_log", version_log),
            evidence_entry("nvidia_runtime_version_diagnostic_summary", version_summary_path),
            evidence_entry("nvidia_reload_preflight_log", reload_log),
            evidence_entry("nvidia_reload_preflight_summary", reload_summary_path),
            evidence_entry("cuda_preflight_diagnostic_log", cuda_log),
            evidence_entry("cuda_preflight_diagnostic_exitcode", cuda_exitcode_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_READY, STATUS_DEFERRED}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    if data.get("status") == STATUS_DEFERRED:
        require(summary.get("current_cuda_runtime_ready") is False, "deferred report must record CUDA runtime not ready")
        require(
            summary.get("nvidia_smi_driver_library_mismatch") is True,
            "deferred report must identify the NVIDIA driver/library mismatch",
        )
        require(
            summary.get("kernel_module_version_proc") != summary.get("nvml_library_version_reported_by_nvidia_smi"),
            "deferred report must show different kernel/user-space versions",
        )
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# GPU Runtime Recovery Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Current CUDA runtime ready: `{s['current_cuda_runtime_ready']}`",
        f"- CUDA require-preflight exitcode: `{s['cuda_require_preflight_exitcode']}`",
        f"- Kernel module version: `{s['kernel_module_version_proc']}`",
        f"- NVML user-space version: `{s['nvml_library_version_reported_by_nvidia_smi']}`",
        f"- `modinfo nvidia` version: `{s['modinfo_nvidia_version']}`",
        f"- Device users detected: `{s['nvidia_device_users_detected']}`",
        f"- Recommended action: `{s['reload_action_recommended']}`",
        "",
        s["recovery_recommendation"],
        "",
        s["hot_reload_preflight_note"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version-log", default=str(DEFAULT_VERSION_LOG))
    parser.add_argument("--version-summary", default=str(DEFAULT_VERSION_SUMMARY))
    parser.add_argument("--reload-log", default=str(DEFAULT_RELOAD_LOG))
    parser.add_argument("--reload-summary", default=str(DEFAULT_RELOAD_SUMMARY))
    parser.add_argument("--cuda-log", default=str(DEFAULT_CUDA_LOG))
    parser.add_argument("--cuda-exitcode", default=str(DEFAULT_CUDA_EXITCODE))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"gpu_runtime_recovery VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"gpu_runtime_recovery PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
