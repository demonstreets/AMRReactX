#!/usr/bin/env python3
"""Write/verify the master-plan completion audit report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_completion_audit_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_completion_audit_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_completion_audit_report.md"

MASTER_PLAN = Path("../pele_cfd_master_plan.md")
FINAL_READINESS = Path(
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
    "master_plan_final_readiness_report.json"
)
CURRENT_SCOPE = Path(
    "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
    "master_plan_current_scope_verification_report.json"
)
PARALLEL_CAPABILITY = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)
OPERATOR_RUNBOOK = Path(
    "docs/codex_audit/evidence/current_scope_operator_runbook_20260803/"
    "current_scope_operator_runbook_report.json"
)
STRICT_BLOCKER = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)
STRICT_UNBLOCK = Path(
    "docs/codex_audit/evidence/strict_master_plan_unblock_runbook_20260803/"
    "strict_master_plan_unblock_runbook_report.json"
)

EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class CompletionAuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CompletionAuditError(message)


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
        raise CompletionAuditError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CompletionAuditError(f"invalid JSON evidence {path}: {exc}") from exc
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
    final = load_json(FINAL_READINESS)
    current = load_json(CURRENT_SCOPE)
    parallel = load_json(PARALLEL_CAPABILITY)
    operator = load_json(OPERATOR_RUNBOOK)
    strict = load_json(STRICT_BLOCKER)
    strict_unblock = load_json(STRICT_UNBLOCK)

    strict_summary = strict.get("summary", {})
    open_blockers = set(strict_summary.get("open_strict_blockers", []))
    current_scope_ready = current.get("status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"
    final_ready = final.get("status") == "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS"
    parallel_ready = parallel.get("status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX"
    operator_ready = operator.get("status") == "PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK"
    strict_unblock_ready = strict_unblock.get("status") == "PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK"
    strict_complete = strict_summary.get("strict_master_plan_complete") is True
    strict_blocker_set_ok = open_blockers == EXPECTED_STRICT_BLOCKERS

    audit_ready = (
        MASTER_PLAN.is_file()
        and current_scope_ready
        and final_ready
        and parallel_ready
        and operator_ready
        and strict_unblock_ready
        and not strict_complete
        and strict_blocker_set_ok
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "summary": {
            "completion_audit_ready": audit_ready,
            "goal_complete": False,
            "current_scope_ready": current_scope_ready,
            "current_user_priority_ready": final.get("summary", {}).get("current_user_priority_ready"),
            "parallel_capability_ready": parallel.get("summary", {}).get("current_parallel_capability_matrix_ready"),
            "operator_runbook_ready": operator.get("summary", {}).get("operator_runbook_ready"),
            "strict_unblock_runbook_ready": strict_unblock.get("summary", {}).get("strict_master_plan_unblock_runbook_ready"),
            "strict_master_plan_complete": strict_complete,
            "open_strict_blocker_count": strict_summary.get("open_strict_blocker_count"),
            "strict_blocker_set_matches_expected": strict_blocker_set_ok,
            "master_current_scope_gate_count": current.get("summary", {}).get("gate_count"),
            "master_current_scope_passed_gate_count": current.get("summary", {}).get("passed_gate_count"),
            "master_plan_path": str(MASTER_PLAN),
        },
        "scope_assessment": {
            "current_scope": {
                "status": "ACHIEVED",
                "evidence": str(CURRENT_SCOPE),
                "interpretation": "Current engineering-first CPU/GPU/MPI scope is reproducible and evidence-backed.",
            },
            "strict_master_plan": {
                "status": "INCOMPLETE",
                "evidence": str(STRICT_BLOCKER),
                "interpretation": "Strict original master-plan completion remains blocked by external artifacts.",
            },
        },
        "open_strict_blockers": sorted(open_blockers),
        "next_action_runbook": "docs/codex_audit/strict_master_plan_unblock_runbook.md",
        "evidence_files": [
            evidence_entry("master_plan", MASTER_PLAN),
            evidence_entry("master_plan_final_readiness_report", FINAL_READINESS),
            evidence_entry("master_plan_current_scope_verification_report", CURRENT_SCOPE),
            evidence_entry("current_parallel_capability_matrix_report", PARALLEL_CAPABILITY),
            evidence_entry("current_scope_operator_runbook_report", OPERATOR_RUNBOOK),
            evidence_entry("strict_blocker_matrix_report", STRICT_BLOCKER),
            evidence_entry("strict_master_plan_unblock_runbook_report", STRICT_UNBLOCK),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid completion audit status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("completion_audit_ready") is True, "completion audit is not ready")
    require(summary.get("goal_complete") is False, "goal must not be marked complete while strict blockers are open")
    require(summary.get("current_scope_ready") is True, "current scope is not ready")
    require(summary.get("current_user_priority_ready") is True, "final readiness is not current-user ready")
    require(summary.get("parallel_capability_ready") is True, "parallel capability is not ready")
    require(summary.get("operator_runbook_ready") is True, "operator runbook is not ready")
    require(summary.get("strict_unblock_runbook_ready") is True, "strict unblock runbook is not ready")
    require(summary.get("strict_master_plan_complete") is False, "strict master plan unexpectedly complete")
    require(summary.get("open_strict_blocker_count") == 3, "unexpected strict blocker count")
    require(summary.get("strict_blocker_set_matches_expected") is True, "strict blocker set changed")
    require(summary.get("master_current_scope_gate_count") == 15, "unexpected current-scope gate count")
    require(summary.get("master_current_scope_passed_gate_count") == 15, "not all current-scope gates passed")
    blockers = set(data.get("open_strict_blockers", []))
    require(blockers == EXPECTED_STRICT_BLOCKERS, "open strict blocker list changed")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Master-Plan Completion Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Current scope ready: `{summary['current_scope_ready']}`",
        f"- Goal complete: `{summary['goal_complete']}`",
        f"- Strict master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        f"- Current-scope gates: `{summary['master_current_scope_passed_gate_count']}/{summary['master_current_scope_gate_count']}`",
        f"- Next-action runbook: `{report['next_action_runbook']}`",
        "",
        "## Open Strict Blockers",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["open_strict_blockers"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"master_plan_completion_audit VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"master_plan_completion_audit PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
