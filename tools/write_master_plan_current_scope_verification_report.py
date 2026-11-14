#!/usr/bin/env python3
"""Write/verify the current-scope master-plan verification gate report."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"
STATUS_NOT_READY = "NOT_READY-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_current_scope_verification_20260731")
DEFAULT_LOG_DIR = DEFAULT_ROOT / "logs"
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_current_scope_verification_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_current_scope_verification_report.md"
DEFAULT_FINAL_READINESS = Path(
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
    "master_plan_final_readiness_report.json"
)
DEFAULT_FULL_REPRO = Path(
    "docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/"
    "master_plan_full_reproducibility_report.json"
)
DEFAULT_CUDA_REVALIDATION = Path(
    "docs/codex_audit/evidence/master_plan_cuda_revalidation_20260731/"
    "master_plan_cuda_revalidation_report.json"
)
DEFAULT_CURRENT_PARALLEL_CAPABILITY = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)
DEFAULT_CURRENT_SCOPE_OPERATOR_RUNBOOK = Path(
    "docs/codex_audit/evidence/current_scope_operator_runbook_20260803/"
    "current_scope_operator_runbook_report.json"
)

GATES = [
    "engineering_h2_production_evidence",
    "academic_evidence",
    "academic_current_priority_scope",
    "strict_external_source_update",
    "strict_real_cad_update",
    "strict_fire_calibration_update",
    "strict_blocker_matrix",
    "strict_artifact_intake_manifest",
    "strict_artifact_drop_preflight",
    "gpu_runtime_recovery",
    "cuda_revalidation",
    "full_reproducibility",
    "current_parallel_capability_matrix",
    "current_scope_operator_runbook",
    "final_readiness",
]


class CurrentScopeError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CurrentScopeError(message)


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
        raise CurrentScopeError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CurrentScopeError(f"invalid JSON evidence {path}: {exc}") from exc
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


def read_exitcode(path: Path) -> str:
    require(path.is_file(), f"missing exitcode file: {path}")
    return path.read_text(encoding="utf-8", errors="replace").strip()


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    log_dir = Path(args.log_dir)
    final_readiness_path = Path(args.final_readiness)
    full_repro_path = Path(args.full_repro)
    cuda_revalidation_path = Path(args.cuda_revalidation)
    current_parallel_capability_path = Path(args.current_parallel_capability)
    current_scope_operator_runbook_path = Path(args.current_scope_operator_runbook)
    final_readiness = load_json(final_readiness_path)
    full_repro = load_json(full_repro_path)
    cuda_revalidation = load_json(cuda_revalidation_path)
    current_parallel_capability = load_json(current_parallel_capability_path)
    current_scope_operator_runbook = load_json(current_scope_operator_runbook_path)

    gate_results = {}
    evidence_files = []
    for gate in GATES:
        log_path = log_dir / f"{gate}.log"
        exit_path = log_dir / f"{gate}.exitcode"
        exitcode = read_exitcode(exit_path)
        gate_results[gate] = {
            "exitcode": exitcode,
            "ready": exitcode == "0",
        }
        evidence_files.append(evidence_entry(f"{gate}_log", log_path))
        evidence_files.append(evidence_entry(f"{gate}_exitcode", exit_path))

    overall_exit = read_exitcode(DEFAULT_ROOT / "master_plan_current_scope_verification.exitcode")
    all_ready = overall_exit == "0" and all(item["ready"] for item in gate_results.values())
    status = STATUS_PASS if all_ready else STATUS_NOT_READY

    evidence_files.extend(
        [
            evidence_entry("master_plan_current_scope_verification_exitcode", DEFAULT_ROOT / "master_plan_current_scope_verification.exitcode"),
            evidence_entry("master_plan_final_readiness_report", final_readiness_path),
            evidence_entry("master_plan_full_reproducibility_report", full_repro_path),
            evidence_entry("master_plan_cuda_revalidation_report", cuda_revalidation_path),
            evidence_entry("current_parallel_capability_matrix_report", current_parallel_capability_path),
            evidence_entry("current_scope_operator_runbook_report", current_scope_operator_runbook_path),
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "current_scope_verification_ready": all_ready,
            "overall_exitcode": overall_exit,
            "gate_count": len(GATES),
            "passed_gate_count": sum(1 for item in gate_results.values() if item["ready"]),
            "final_readiness_status": final_readiness.get("status"),
            "current_user_priority_ready": final_readiness.get("summary", {}).get("current_user_priority_ready"),
            "strict_master_plan_complete": final_readiness.get("summary", {}).get("strict_master_plan_complete"),
            "full_reproducibility_status": full_repro.get("status"),
            "current_cuda_runtime_ready": full_repro.get("summary", {}).get("current_cuda_runtime_ready"),
            "cuda_revalidation_status": cuda_revalidation.get("status"),
            "current_parallel_capability_status": current_parallel_capability.get("status"),
            "cpu_mpi_ready_for_all_current_scenarios": current_parallel_capability.get("summary", {}).get("cpu_mpi_ready_for_all_current_scenarios"),
            "single_gpu_ready_for_all_current_scenarios": current_parallel_capability.get("summary", {}).get("single_gpu_ready_for_all_current_scenarios"),
            "multi_gpu_mpi_cuda_ready_for_all_current_scenarios": current_parallel_capability.get("summary", {}).get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios"),
            "current_scope_operator_runbook_status": current_scope_operator_runbook.get("status"),
            "current_scope_operator_runbook_ready": current_scope_operator_runbook.get("summary", {}).get("operator_runbook_ready"),
        },
        "gate_results": gate_results,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    gates = data.get("gate_results")
    require(isinstance(gates, dict), "missing gate_results")
    require(set(gates) == set(GATES), "unexpected gate set")
    require(summary.get("passed_gate_count") == len(GATES), "not all current-scope gates passed")
    require(summary.get("current_user_priority_ready") is True, "final readiness no longer current-user ready")
    require(summary.get("current_parallel_capability_status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX", "current parallel capability matrix is not passing")
    require(summary.get("cpu_mpi_ready_for_all_current_scenarios") is True, "CPU/MPI readiness is not ready for all current scenarios")
    require(summary.get("single_gpu_ready_for_all_current_scenarios") is True, "single-GPU readiness is not ready for all current scenarios")
    require(summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True, "multi-GPU MPI+CUDA readiness is not ready for all current scenarios")
    require(summary.get("current_scope_operator_runbook_status") == "PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK", "current-scope operator runbook is not passing")
    require(summary.get("current_scope_operator_runbook_ready") is True, "current-scope operator runbook is not ready")
    require(summary.get("strict_master_plan_complete") is False, "strict master-plan should remain separately tracked")
    require(
        summary.get("cuda_revalidation_status") in {
            "DEFERRED-MASTER-PLAN-CUDA-REVALIDATION-GPU-RUNTIME-NOT-READY",
            "PASS-MASTER-PLAN-CUDA-REVALIDATION",
        },
        "CUDA revalidation status changed unexpectedly",
    )
    if data.get("status") == STATUS_PASS:
        require(summary.get("current_scope_verification_ready") is True, "PASS report must be ready")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Master Plan Current-Scope Verification",
        "",
        f"- Status: `{report['status']}`",
        f"- Overall exitcode: `{summary['overall_exitcode']}`",
        f"- Passed gates: `{summary['passed_gate_count']}/{summary['gate_count']}`",
        f"- Final readiness status: `{summary['final_readiness_status']}`",
        f"- Full reproducibility status: `{summary['full_reproducibility_status']}`",
        f"- CUDA revalidation status: `{summary['cuda_revalidation_status']}`",
        f"- Current parallel capability status: `{summary['current_parallel_capability_status']}`",
        f"- CPU/MPI all-current-scenarios ready: `{summary['cpu_mpi_ready_for_all_current_scenarios']}`",
        f"- Single-GPU all-current-scenarios ready: `{summary['single_gpu_ready_for_all_current_scenarios']}`",
        f"- Multi-GPU MPI+CUDA all-current-scenarios ready: `{summary['multi_gpu_mpi_cuda_ready_for_all_current_scenarios']}`",
        f"- Current-scope operator runbook status: `{summary['current_scope_operator_runbook_status']}`",
        "",
        "## Gates",
        "",
    ]
    for gate, result in report["gate_results"].items():
        lines.append(f"- `{gate}`: exitcode `{result['exitcode']}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--final-readiness", default=str(DEFAULT_FINAL_READINESS))
    parser.add_argument("--full-repro", default=str(DEFAULT_FULL_REPRO))
    parser.add_argument("--cuda-revalidation", default=str(DEFAULT_CUDA_REVALIDATION))
    parser.add_argument("--current-parallel-capability", default=str(DEFAULT_CURRENT_PARALLEL_CAPABILITY))
    parser.add_argument("--current-scope-operator-runbook", default=str(DEFAULT_CURRENT_SCOPE_OPERATOR_RUNBOOK))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"master_plan_current_scope_verification VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"master_plan_current_scope_verification PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
