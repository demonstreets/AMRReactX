#!/usr/bin/env python3
"""Write/verify current full reproducibility evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS_CPU_CUDA_READY = "PASS-MASTER-PLAN-FULL-CPU-CUDA-REPRODUCIBILITY"
STATUS_PASS_CPU_GPU_ENV_DEFERRED = "PASS-MASTER-PLAN-FULL-CPU-REPRO-CUDA-RUNTIME-DEFERRED"
STATUS_NOT_READY = "NOT_READY-MASTER-PLAN-FULL-REPRODUCIBILITY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_full_reproducibility_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_full_reproducibility_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_full_reproducibility_report.md"
DEFAULT_FULL_CPU_LOG = DEFAULT_ROOT / "gate_logs/reproducible_gate_full_cpu.log"
DEFAULT_FULL_CPU_EXITCODE = DEFAULT_ROOT / "gate_logs/reproducible_gate_full_cpu.exitcode"
DEFAULT_CUDA_DIAG_LOG = DEFAULT_ROOT / "gpu_diagnostic/cuda_preflight_diagnostic.log"
DEFAULT_CUDA_DIAG_EXITCODE = DEFAULT_ROOT / "gpu_diagnostic/cuda_preflight_diagnostic.exitcode"

DEFAULT_ENGINEERING_GPU_FIRE = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_gpu_fire_obstacle_20260727/"
    "pipe_rack_gpu_fire_obstacle_report.json"
)
DEFAULT_ENGINEERING_REACTING_CUDA = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_cuda_2000step_20260727/"
    "pipe_rack_direct_reacting_cuda_report.json"
)
DEFAULT_ENGINEERING_REACTING_MPI_CUDA = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_2000step_20260727/"
    "pipe_rack_direct_reacting_mpi_cuda_report.json"
)
DEFAULT_GPU_RECOVERY = Path(
    "docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/gpu_diagnostic/"
    "gpu_runtime_recovery_report.json"
)
DEFAULT_CUDA_REVALIDATION = Path(
    "docs/codex_audit/evidence/master_plan_cuda_revalidation_20260731/"
    "master_plan_cuda_revalidation_report.json"
)


class ReproError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReproError(message)


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
        raise ReproError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReproError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def read_exitcode(path: Path) -> int:
    require(path.is_file(), f"missing exitcode file: {path}")
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    require(text.isdigit(), f"invalid exitcode in {path}: {text!r}")
    return int(text)


def log_contains(path: Path, needle: str) -> bool:
    return needle in path.read_text(encoding="utf-8", errors="replace")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    full_cpu_log = Path(args.full_cpu_log)
    full_cpu_exitcode = Path(args.full_cpu_exitcode)
    cuda_diag_log = Path(args.cuda_diag_log)
    cuda_diag_exitcode = Path(args.cuda_diag_exitcode)
    gpu_fire_path = Path(args.engineering_gpu_fire)
    reacting_cuda_path = Path(args.engineering_reacting_cuda)
    reacting_mpi_cuda_path = Path(args.engineering_reacting_mpi_cuda)
    gpu_recovery_path = Path(args.gpu_recovery)
    cuda_revalidation_path = Path(args.cuda_revalidation)

    full_cpu_rc = read_exitcode(full_cpu_exitcode)
    cuda_rc = read_exitcode(cuda_diag_exitcode)
    gpu_fire = load_json(gpu_fire_path)
    reacting_cuda = load_json(reacting_cuda_path)
    reacting_mpi_cuda = load_json(reacting_mpi_cuda_path)
    gpu_recovery = load_json(gpu_recovery_path)
    cuda_revalidation = load_json(cuda_revalidation_path)

    full_cpu_ready = (
        full_cpu_rc == 0
        and log_contains(full_cpu_log, "[codex-repro] PASS  smoke_all")
        and log_contains(full_cpu_log, "all requested reproducibility checks passed")
    )
    cuda_runtime_ready = cuda_rc == 0
    cuda_runtime_blocker = ""
    if not cuda_runtime_ready and log_contains(cuda_diag_log, "Driver/library version mismatch"):
        cuda_runtime_blocker = "nvidia_nvml_driver_library_version_mismatch"
    elif not cuda_runtime_ready:
        cuda_runtime_blocker = "cuda_require_preflight_failed"

    historical_gpu_evidence_ready = (
        str(gpu_fire.get("status", "")).startswith("PASS")
        and str(reacting_cuda.get("status", "")).startswith("PASS")
        and str(reacting_mpi_cuda.get("status", "")).startswith("PASS")
    )

    cuda_revalidation_ready = cuda_revalidation.get("status") == "PASS-MASTER-PLAN-CUDA-REVALIDATION"
    gpu_runtime_ready = gpu_recovery.get("status") == "PASS-MASTER-PLAN-GPU-RUNTIME-READY"
    if full_cpu_ready and historical_gpu_evidence_ready and cuda_runtime_ready and gpu_runtime_ready and cuda_revalidation_ready:
        status = STATUS_PASS_CPU_CUDA_READY
    elif full_cpu_ready and historical_gpu_evidence_ready and not cuda_runtime_ready:
        status = STATUS_PASS_CPU_GPU_ENV_DEFERRED
    else:
        status = STATUS_NOT_READY

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "full_cpu_reproducibility_ready": full_cpu_ready,
            "current_cuda_runtime_ready": cuda_runtime_ready,
            "current_cuda_runtime_blocker": cuda_runtime_blocker,
            "gpu_runtime_recovery_status": gpu_recovery.get("status"),
            "gpu_runtime_kernel_module_version": gpu_recovery.get("summary", {}).get("kernel_module_version_proc"),
            "gpu_runtime_nvml_user_space_version": gpu_recovery.get("summary", {}).get(
                "nvml_library_version_reported_by_nvidia_smi"
            ),
            "gpu_runtime_recommended_action": gpu_recovery.get("summary", {}).get("reload_action_recommended"),
            "cuda_revalidation_status": cuda_revalidation.get("status"),
            "gpu_runtime_ready": gpu_runtime_ready,
            "cuda_revalidation_current_ready": cuda_revalidation_ready,
            "cuda_revalidation_script_ready": cuda_revalidation.get("summary", {}).get(
                "cuda_revalidation_script_ready"
            ),
            "historical_engineering_gpu_case_evidence_ready": historical_gpu_evidence_ready,
            "full_cpu_repro_exitcode": full_cpu_rc,
            "cuda_require_preflight_exitcode": cuda_rc,
            "interpretation": (
                "Current source state passes the full CPU reproducibility gate including smoke_all, "
                "the current CUDA runtime is healthy, and the current CUDA revalidation gate passes."
                if status == STATUS_PASS_CPU_CUDA_READY
                else (
                    "Current source state passes the full CPU reproducibility gate including smoke_all. "
                    "CUDA build/runtime dependencies are installed, and historical engineering GPU/MPI-CUDA case evidence is present, "
                    "but the current server GPU runtime cannot be revalidated until the NVIDIA NVML driver/library mismatch is cleared."
                )
            ),
        },
        "evidence_files": [
            evidence_entry("full_cpu_reproducible_gate_log", full_cpu_log),
            evidence_entry("full_cpu_reproducible_gate_exitcode", full_cpu_exitcode),
            evidence_entry("cuda_preflight_diagnostic_log", cuda_diag_log),
            evidence_entry("cuda_preflight_diagnostic_exitcode", cuda_diag_exitcode),
            evidence_entry("engineering_pipe_rack_gpu_fire_obstacle_report", gpu_fire_path),
            evidence_entry("engineering_pipe_rack_direct_reacting_cuda_report", reacting_cuda_path),
            evidence_entry("engineering_pipe_rack_direct_reacting_mpi_cuda_report", reacting_mpi_cuda_path),
            evidence_entry("gpu_runtime_recovery_report", gpu_recovery_path),
            evidence_entry("cuda_revalidation_report", cuda_revalidation_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(
        data.get("status") in {STATUS_PASS_CPU_CUDA_READY, STATUS_PASS_CPU_GPU_ENV_DEFERRED, STATUS_NOT_READY},
        "invalid status",
    )
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("full_cpu_reproducibility_ready") is True, "full CPU reproducibility is not ready")
    require(
        summary.get("historical_engineering_gpu_case_evidence_ready") is True,
        "historical engineering GPU evidence is not ready",
    )
    if data.get("status") == STATUS_PASS_CPU_CUDA_READY:
        require(summary.get("current_cuda_runtime_ready") is True, "PASS requires current CUDA runtime ready")
        require(summary.get("gpu_runtime_recovery_status") == "PASS-MASTER-PLAN-GPU-RUNTIME-READY", "GPU runtime not ready")
        require(
            summary.get("cuda_revalidation_status") == "PASS-MASTER-PLAN-CUDA-REVALIDATION",
            "CUDA revalidation is not PASS",
        )
        require(summary.get("cuda_revalidation_current_ready") is True, "current CUDA revalidation not ready")
    if data.get("status") == STATUS_PASS_CPU_GPU_ENV_DEFERRED:
        require(summary.get("current_cuda_runtime_ready") is False, "deferred CUDA report must record current runtime not ready")
        require(
            summary.get("current_cuda_runtime_blocker") == "nvidia_nvml_driver_library_version_mismatch",
            "unexpected CUDA runtime blocker",
        )
        require(
            summary.get("gpu_runtime_recovery_status")
            == "DEFERRED-MASTER-PLAN-GPU-RUNTIME-RECOVERY-REQUIRES-DRIVER-RELOAD",
            "missing deferred GPU runtime recovery report",
        )
        require(
            summary.get("cuda_revalidation_status")
            == "DEFERRED-MASTER-PLAN-CUDA-REVALIDATION-GPU-RUNTIME-NOT-READY",
            "missing deferred CUDA revalidation report",
        )
        require(summary.get("cuda_revalidation_script_ready") is True, "CUDA revalidation script is not ready")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Master Plan Full Reproducibility Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Full CPU reproducibility: `{summary['full_cpu_reproducibility_ready']}`",
        f"- Current CUDA runtime ready: `{summary['current_cuda_runtime_ready']}`",
        f"- Current CUDA blocker: `{summary['current_cuda_runtime_blocker']}`",
        f"- Historical engineering GPU case evidence ready: `{summary['historical_engineering_gpu_case_evidence_ready']}`",
        "",
        (
            "The current source state passes the full CPU reproducibility gate including `smoke_all`; "
            "the server CUDA runtime is healthy, and the current CUDA revalidation gate passes."
            if report["status"] == STATUS_PASS_CPU_CUDA_READY
            else (
                "The current source state passes the full CPU reproducibility gate including `smoke_all`. "
                "CUDA toolchain and SUNDIALS CUDA libraries are present, but the current server runtime reports "
                "`Driver/library version mismatch` from `nvidia-smi`, so CUDA rerun is deferred until the server GPU driver state is repaired."
            )
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-cpu-log", default=str(DEFAULT_FULL_CPU_LOG))
    parser.add_argument("--full-cpu-exitcode", default=str(DEFAULT_FULL_CPU_EXITCODE))
    parser.add_argument("--cuda-diag-log", default=str(DEFAULT_CUDA_DIAG_LOG))
    parser.add_argument("--cuda-diag-exitcode", default=str(DEFAULT_CUDA_DIAG_EXITCODE))
    parser.add_argument("--engineering-gpu-fire", default=str(DEFAULT_ENGINEERING_GPU_FIRE))
    parser.add_argument("--engineering-reacting-cuda", default=str(DEFAULT_ENGINEERING_REACTING_CUDA))
    parser.add_argument("--engineering-reacting-mpi-cuda", default=str(DEFAULT_ENGINEERING_REACTING_MPI_CUDA))
    parser.add_argument("--gpu-recovery", default=str(DEFAULT_GPU_RECOVERY))
    parser.add_argument("--cuda-revalidation", default=str(DEFAULT_CUDA_REVALIDATION))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"master_plan_full_reproducibility VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"master_plan_full_reproducibility PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
