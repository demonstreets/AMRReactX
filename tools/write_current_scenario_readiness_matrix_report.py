#!/usr/bin/env python3
"""Write/verify the user-facing current scenario readiness matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-SCENARIO-READINESS-MATRIX"
STATUS_NOT_READY = "NOT_READY-CURRENT-SCENARIO-READINESS-MATRIX"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_scenario_readiness_matrix_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_scenario_readiness_matrix_report.md"

PARALLEL_MATRIX = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)
FINAL_READINESS = Path(
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
    "master_plan_final_readiness_report.json"
)
STATE_SNAPSHOT = Path(
    "docs/codex_audit/evidence/current_scope_state_snapshot_20260803/"
    "current_scope_state_snapshot_report.json"
)

SCENARIO_LABELS = {
    "engineering_h2_leak_diffusion_fire": "Engineering H2 leak / dispersion / ignition / fire",
    "engineering_multifuel_lng_lpg_surrogate_sources": (
        "Engineering multi-fuel gas sources / gasified LNG-LPG surrogate workflows"
    ),
    "academic_gas_detonation": "Academic gas-phase detonation",
    "academic_gas_liquid_twophase_detonation": "Academic gas-liquid / two-phase detonation",
}

SCENARIO_PROGRESS_KEYS = {
    "engineering_h2_leak_diffusion_fire": "engineering_progress_estimate_percent",
    "engineering_multifuel_lng_lpg_surrogate_sources": "engineering_progress_estimate_percent",
    "academic_gas_detonation": "academic_gas_progress_estimate_percent",
    "academic_gas_liquid_twophase_detonation": "academic_twophase_progress_estimate_percent",
}


class ScenarioReadinessError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScenarioReadinessError(message)


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
        raise ScenarioReadinessError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScenarioReadinessError(f"invalid JSON evidence {path}: {exc}") from exc
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


def build_report() -> dict[str, Any]:
    parallel = load_json(PARALLEL_MATRIX)
    final = load_json(FINAL_READINESS)
    snapshot = load_json(STATE_SNAPSHOT)

    parallel_summary = parallel.get("summary", {})
    final_summary = final.get("summary", {})
    capabilities = parallel.get("capabilities", {})
    require(isinstance(parallel_summary, dict), "parallel matrix missing summary")
    require(isinstance(final_summary, dict), "final readiness missing summary")
    require(isinstance(capabilities, dict), "parallel matrix missing capabilities")

    scenarios: dict[str, Any] = {}
    for scenario_id, label in SCENARIO_LABELS.items():
        capability = capabilities.get(scenario_id)
        require(isinstance(capability, dict), f"missing capability scenario: {scenario_id}")
        modes = capability.get("modes")
        require(isinstance(modes, dict), f"missing modes for {scenario_id}")
        scenario_ready = capability.get("ready") is True
        mode_ready = {
            "cpu_mpi": modes.get("cpu_mpi", {}).get("ready") is True,
            "single_gpu": modes.get("single_gpu", {}).get("ready") is True,
            "multi_gpu_mpi_cuda": modes.get("multi_gpu_mpi_cuda", {}).get("ready") is True,
        }
        scenarios[scenario_id] = {
            "label": label,
            "ready": scenario_ready and all(mode_ready.values()),
            "progress_estimate_percent": final_summary.get(SCENARIO_PROGRESS_KEYS[scenario_id]),
            "answer_for_current_use": "yes_current_priority_scope",
            "modes": mode_ready,
            "evidence_paths": {
                mode: modes.get(mode, {}).get("path")
                for mode in ["cpu_mpi", "single_gpu", "multi_gpu_mpi_cuda"]
            },
            "limitation": capability.get("limitation", ""),
        }

    all_ready = all(item["ready"] for item in scenarios.values())
    strict_blockers = final_summary.get("deferred_strict_master_plan_blockers", [])
    status = STATUS_PASS if all_ready and parallel.get("status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX" else STATUS_NOT_READY

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "overall_progress_estimate_percent": final_summary.get("overall_progress_estimate_percent"),
            "current_user_priority_ready": final_summary.get("current_user_priority_ready") is True,
            "strict_master_plan_complete": final_summary.get("strict_master_plan_complete") is True,
            "scenario_count": len(scenarios),
            "ready_scenario_count": sum(1 for item in scenarios.values() if item["ready"]),
            "cpu_mpi_ready_for_all_current_scenarios": parallel_summary.get("cpu_mpi_ready_for_all_current_scenarios") is True,
            "single_gpu_ready_for_all_current_scenarios": parallel_summary.get("single_gpu_ready_for_all_current_scenarios") is True,
            "multi_gpu_mpi_cuda_ready_for_all_current_scenarios": parallel_summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True,
            "deferred_strict_master_plan_blocker_count": final_summary.get("deferred_strict_master_plan_blocker_count"),
            "deferred_strict_master_plan_blockers": strict_blockers,
            "source_snapshot_status": snapshot.get("status"),
        },
        "scenarios": scenarios,
        "evidence_files": [
            evidence_entry("current_parallel_capability_matrix", PARALLEL_MATRIX),
            evidence_entry("master_plan_final_readiness", FINAL_READINESS),
            evidence_entry("current_scope_state_snapshot", STATE_SNAPSHOT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    require(data.get("status") == STATUS_PASS, "scenario readiness matrix is not passing")

    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_user_priority_ready") is True, "current user priority is not ready")
    require(summary.get("strict_master_plan_complete") is False, "strict master-plan completion should remain explicit")
    require(summary.get("scenario_count") == 4, "unexpected scenario count")
    require(summary.get("ready_scenario_count") == 4, "not all scenarios are ready")
    require(summary.get("cpu_mpi_ready_for_all_current_scenarios") is True, "CPU/MPI readiness is not global")
    require(summary.get("single_gpu_ready_for_all_current_scenarios") is True, "single GPU readiness is not global")
    require(summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True, "multi-GPU MPI+CUDA readiness is not global")
    require(summary.get("deferred_strict_master_plan_blocker_count") == 3, "unexpected deferred strict blocker count")
    require(summary.get("source_snapshot_status") == "PASS-CURRENT-SCOPE-STATE-SNAPSHOT", "source snapshot is not passing")

    scenarios = data.get("scenarios")
    require(isinstance(scenarios, dict), "missing scenarios")
    require(set(scenarios) == set(SCENARIO_LABELS), "unexpected scenario set")
    for scenario_id, scenario in scenarios.items():
        require(scenario.get("ready") is True, f"{scenario_id} is not ready")
        require(scenario.get("progress_estimate_percent"), f"{scenario_id} missing progress estimate")
        require(scenario.get("answer_for_current_use") == "yes_current_priority_scope", f"{scenario_id} has unexpected use answer")
        modes = scenario.get("modes")
        require(isinstance(modes, dict), f"{scenario_id} missing modes")
        for mode in ["cpu_mpi", "single_gpu", "multi_gpu_mpi_cuda"]:
            require(modes.get(mode) is True, f"{scenario_id}.{mode} is not ready")
            evidence_path = Path(scenario.get("evidence_paths", {}).get(mode, ""))
            require(evidence_path.is_file(), f"{scenario_id}.{mode} missing evidence path: {evidence_path}")

    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Scenario Readiness Matrix",
        "",
        f"- Status: `{report['status']}`",
        f"- Overall current-priority progress estimate: `{summary['overall_progress_estimate_percent']}`",
        f"- Current user-priority ready: `{summary['current_user_priority_ready']}`",
        f"- Strict master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Deferred strict blockers: `{summary['deferred_strict_master_plan_blocker_count']}`",
        "",
        "| Scenario | Progress | CPU/MPI | Single GPU | Multi-GPU MPI+CUDA | Current-use answer |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for scenario in report["scenarios"].values():
        modes = scenario["modes"]
        lines.append(
            f"| {scenario['label']} | `{scenario['progress_estimate_percent']}` | "
            f"`{modes['cpu_mpi']}` | `{modes['single_gpu']}` | "
            f"`{modes['multi_gpu_mpi_cuda']}` | `{scenario['answer_for_current_use']}` |"
        )
    lines.extend(["", "## Limits"])
    for scenario_id, scenario in report["scenarios"].items():
        lines.append(f"- `{scenario_id}`: {scenario['limitation']}")
    lines.extend(["", "## Deferred Strict Blockers"])
    for blocker in summary["deferred_strict_master_plan_blockers"]:
        lines.append(f"- `{blocker}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_JSON), help="output JSON report path")
    parser.add_argument("--markdown", default=str(DEFAULT_OUTPUT_MD), help="output Markdown report path")
    parser.add_argument("--verify-json", help="verify an existing JSON report instead of writing one")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_scenario_readiness_matrix VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, Path(args.markdown))
    print(f"current_scenario_readiness_matrix PASS json={output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
