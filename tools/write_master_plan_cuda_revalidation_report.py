#!/usr/bin/env python3
"""Write/verify post-recovery CUDA revalidation evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-MASTER-PLAN-CUDA-REVALIDATION"
STATUS_DEFERRED = "DEFERRED-MASTER-PLAN-CUDA-REVALIDATION-GPU-RUNTIME-NOT-READY"
STATUS_NOT_READY = "NOT_READY-MASTER-PLAN-CUDA-REVALIDATION"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_cuda_revalidation_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_cuda_revalidation_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_cuda_revalidation_report.md"
DEFAULT_LOG_DIR = DEFAULT_ROOT / "logs"
DEFAULT_SCRIPT = Path("tools/run_master_plan_cuda_revalidation.sh")
DEFAULT_GPU_RECOVERY = Path(
    "docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/gpu_diagnostic/"
    "gpu_runtime_recovery_report.json"
)


class CudaRevalidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CudaRevalidationError(message)


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
        raise CudaRevalidationError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CudaRevalidationError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def read_exitcode(path: Path) -> str:
    require(path.is_file(), f"missing exitcode evidence: {path}")
    return path.read_text(encoding="utf-8", errors="replace").strip()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def log_contains(path: Path, needle: str) -> bool:
    return path.is_file() and needle in path.read_text(encoding="utf-8", errors="replace")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    log_dir = Path(args.log_dir)
    script_path = Path(args.script)
    gpu_recovery_path = Path(args.gpu_recovery)
    gpu_recovery = load_json(gpu_recovery_path)

    cuda_preflight_log = log_dir / "cuda_preflight.log"
    cuda_preflight_exit = read_exitcode(log_dir / "cuda_preflight.exitcode")
    repro_exit_path = log_dir / "reproducible_gate_require_cuda.exitcode"
    repro_exit = read_exitcode(repro_exit_path) if repro_exit_path.is_file() else "MISSING"
    overall_exit = read_exitcode(DEFAULT_ROOT / "cuda_revalidation.exitcode")

    cuda_preflight_ready = cuda_preflight_exit == "0"
    require_cuda_repro_ready = repro_exit == "0"
    current_runtime_blocker = ""
    if not cuda_preflight_ready and log_contains(cuda_preflight_log, "Driver/library version mismatch"):
        current_runtime_blocker = "nvidia_nvml_driver_library_version_mismatch"
    elif not cuda_preflight_ready:
        current_runtime_blocker = "cuda_preflight_failed"

    script_text = script_path.read_text(encoding="utf-8", errors="replace")
    machine_local_patterns = ["/" + "home/cj/", "/" + "tmp/"]
    script_machine_local_clean = not any(pattern in script_text for pattern in machine_local_patterns)

    status = STATUS_NOT_READY
    if cuda_preflight_ready and require_cuda_repro_ready and overall_exit == "0":
        status = STATUS_PASS
    elif current_runtime_blocker == "nvidia_nvml_driver_library_version_mismatch":
        status = STATUS_DEFERRED

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "cuda_revalidation_script_ready": script_path.is_file() and script_machine_local_clean,
            "cuda_revalidation_script_machine_local_clean": script_machine_local_clean,
            "current_cuda_preflight_ready": cuda_preflight_ready,
            "require_cuda_reproducible_gate_ready": require_cuda_repro_ready,
            "cuda_revalidation_overall_exitcode": overall_exit,
            "cuda_preflight_exitcode": cuda_preflight_exit,
            "require_cuda_reproducible_gate_exitcode": repro_exit,
            "current_runtime_blocker": current_runtime_blocker,
            "gpu_runtime_recovery_status": gpu_recovery.get("status"),
            "post_recovery_command": (
                "SUNDIALS_CUDA_DIR=<cuda-capable-sundials> PATH=<cuda-bin>:$PATH "
                "LD_LIBRARY_PATH=<sundials-lib>:<cuda-lib64>:$LD_LIBRARY_PATH "
                "bash tools/run_master_plan_cuda_revalidation.sh"
            ),
            "optional_long_engineering_command": (
                "CODEX_CUDA_REVALIDATION_RUN_ENGINEERING_LONG=1 "
                "SUNDIALS_CUDA_DIR=<cuda-capable-sundials> PATH=<cuda-bin>:$PATH "
                "LD_LIBRARY_PATH=<sundials-lib>:<cuda-lib64>:$LD_LIBRARY_PATH "
                "bash tools/run_master_plan_cuda_revalidation.sh"
            ),
        },
        "evidence_files": [
            evidence_entry("cuda_revalidation_script", script_path),
            evidence_entry("cuda_preflight_log", cuda_preflight_log),
            evidence_entry("cuda_preflight_exitcode", log_dir / "cuda_preflight.exitcode"),
            evidence_entry("reproducible_gate_require_cuda_exitcode", repro_exit_path),
            evidence_entry("cuda_revalidation_exitcode", DEFAULT_ROOT / "cuda_revalidation.exitcode"),
            evidence_entry("gpu_runtime_recovery_report", gpu_recovery_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_DEFERRED, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("cuda_revalidation_script_ready") is True, "CUDA revalidation script not ready")
    require(
        summary.get("cuda_revalidation_script_machine_local_clean") is True,
        "CUDA revalidation script contains machine-local paths",
    )
    if data.get("status") == STATUS_DEFERRED:
        require(summary.get("current_cuda_preflight_ready") is False, "deferred report must have failed CUDA preflight")
        require(
            summary.get("current_runtime_blocker") == "nvidia_nvml_driver_library_version_mismatch",
            "unexpected deferred runtime blocker",
        )
        require(
            summary.get("gpu_runtime_recovery_status")
            == "DEFERRED-MASTER-PLAN-GPU-RUNTIME-RECOVERY-REQUIRES-DRIVER-RELOAD",
            "deferred CUDA revalidation must link GPU recovery report",
        )
    if data.get("status") == STATUS_PASS:
        require(summary.get("current_cuda_preflight_ready") is True, "PASS requires CUDA preflight")
        require(summary.get("require_cuda_reproducible_gate_ready") is True, "PASS requires CUDA reproducible gate")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# CUDA Revalidation Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Revalidation script ready: `{s['cuda_revalidation_script_ready']}`",
        f"- Current CUDA preflight ready: `{s['current_cuda_preflight_ready']}`",
        f"- Require-CUDA reproducible gate ready: `{s['require_cuda_reproducible_gate_ready']}`",
        f"- Current runtime blocker: `{s['current_runtime_blocker']}`",
        "",
        "## Post-Recovery Command",
        "",
        f"`{s['post_recovery_command']}`",
        "",
        "## Optional Long Engineering Command",
        "",
        f"`{s['optional_long_engineering_command']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--script", default=str(DEFAULT_SCRIPT))
    parser.add_argument("--gpu-recovery", default=str(DEFAULT_GPU_RECOVERY))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"cuda_revalidation VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"cuda_revalidation PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
