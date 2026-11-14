#!/usr/bin/env python3
"""Write/verify the final current-scope handoff note evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE"
VOLATILE_HASH_LABELS = {"current_status_cli"}

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_scope_final_handoff_note_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_scope_final_handoff_note_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_scope_final_handoff_note_report.md"

DELIVERY_PACKAGE = Path(
    "docs/codex_audit/evidence/current_scope_delivery_package_20260812/"
    "current_scope_delivery_package_report.json"
)
ACCEPTANCE_GATE = Path(
    "docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/"
    "project_closeout_acceptance_gate_report.json"
)
CLOSEOUT_FORECAST = Path(
    "docs/codex_audit/evidence/project_closeout_forecast_20260812/"
    "project_closeout_forecast_report.json"
)
STRICT_COMPLETION_GATE = Path(
    "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
    "strict_master_plan_completion_gate_report.json"
)
STRICT_ARTIFACT_DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
STRICT_ARTIFACT_DROP_CHECKLIST = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/"
    "strict_external_artifact_drop_checklist_report.json"
)
RELEASE_CANDIDATE = Path(
    "docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/"
    "current_scope_release_candidate_handoff_report.json"
)
CURRENT_STATUS = Path(
    "docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json"
)
README = Path("README.md")
RUNBOOK = Path("docs/codex_audit/current_scope_operator_runbook.md")
FULL_LOG_DIR = Path("docs/codex_audit/evidence/current_scope_last_run_20260807")
FULL_LOG_GLOB = "current_scope_verify_after_*.log"

REQUIRED_COMMANDS = [
    "python3 tools/codex_print_current_status.py",
    "python3 tools/codex_print_current_status.py --json",
    "bash tools/codex_verify_current_scope.sh",
    "python3 tools/write_project_closeout_forecast_report.py",
    "bash tools/verify_project_closeout_forecast.sh",
    "python3 tools/write_strict_master_plan_completion_gate_report.py",
    "bash tools/verify_strict_master_plan_completion_gate.sh",
    "python3 tools/write_strict_external_artifact_drop_index_report.py",
    "bash tools/verify_strict_external_artifact_drop_index.sh",
    "python3 tools/write_strict_external_artifact_drop_checklist_report.py",
    "bash tools/verify_strict_external_artifact_drop_checklist.sh",
    "python3 tools/write_current_scope_delivery_package_report.py",
    "bash tools/verify_current_scope_delivery_package.sh",
    "python3 tools/write_project_closeout_acceptance_gate_report.py",
    "bash tools/verify_project_closeout_acceptance_gate.sh",
    "python3 tools/write_current_scope_final_handoff_note_report.py",
    "bash tools/verify_current_scope_final_handoff_note.sh",
    "python3 tools/write_current_operator_quickstart_smoke_report.py",
    "bash tools/verify_current_operator_quickstart_smoke.sh",
]

REQUIRED_DOC_SNIPPETS = [
    "Current-Scope Final Handoff Note",
    "Current-Scope Delivery Package",
    "Project Closeout Forecast",
    "Project Closeout Acceptance Gate",
    "Current Operator Quickstart Smoke",
    "Strict Master-Plan Completion Gate",
    "Strict External Artifact Drop Index",
    "Strict External Artifact Drop Checklist",
    "current scope can be closed now: yes",
    "strict master-plan can be closed now: no",
    "strict completion allowed: no",
    "strict closeout requires external artifacts: yes",
    "docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/current_operator_quickstart_smoke_report.json",
    "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
    "docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/current_scope_final_handoff_note_report.json",
]

EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class FinalHandoffError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FinalHandoffError(message)


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
        raise FinalHandoffError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FinalHandoffError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    entry = {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    if label in VOLATILE_HASH_LABELS:
        entry["hash_verification"] = "skipped-cycle-reference"
    return entry


def doc_missing_snippets(path: Path) -> list[str]:
    require(path.is_file(), f"missing document: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    return [snippet for snippet in REQUIRED_DOC_SNIPPETS + REQUIRED_COMMANDS if snippet not in text]


def full_log_passed(path: Path) -> bool:
    require(path.is_file(), f"missing full current-scope log: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    return "[current-scope] PASS current-scope verification chain" in text and "CURRENT_SCOPE_RC=0" in text


def latest_passing_full_log() -> Path:
    require(FULL_LOG_DIR.is_dir(), f"missing full current-scope log directory: {FULL_LOG_DIR}")
    candidates = sorted(FULL_LOG_DIR.glob(FULL_LOG_GLOB), key=lambda path: path.stat().st_mtime, reverse=True)
    require(candidates, f"no full current-scope logs match {FULL_LOG_DIR / FULL_LOG_GLOB}")
    for path in candidates:
        if full_log_passed(path):
            return path
    raise FinalHandoffError(f"no passing full current-scope log found under {FULL_LOG_DIR}")


def build_report() -> dict[str, Any]:
    delivery = load_json(DELIVERY_PACKAGE)
    acceptance = load_json(ACCEPTANCE_GATE)
    closeout = load_json(CLOSEOUT_FORECAST)
    strict_gate = load_json(STRICT_COMPLETION_GATE)
    drop_index = load_json(STRICT_ARTIFACT_DROP_INDEX)
    drop_checklist = load_json(STRICT_ARTIFACT_DROP_CHECKLIST)
    release = load_json(RELEASE_CANDIDATE)
    current_status = load_json(CURRENT_STATUS)

    dsum = delivery["summary"]
    asum = acceptance["summary"]
    csum = closeout["summary"]
    strictgatesum = strict_gate["summary"]
    dropindexsum = drop_index["summary"]
    dropchecklistsum = drop_checklist["summary"]
    rsum = release["summary"]
    ssum = current_status["summary"]
    open_blockers = set(dsum.get("open_strict_blockers", []))
    readme_missing = doc_missing_snippets(README)
    runbook_missing = doc_missing_snippets(RUNBOOK)
    last_full_log = latest_passing_full_log()

    handoff_ready = all(
        [
            delivery.get("status") == "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
            dsum.get("current_scope_delivery_package_ready") is True,
            acceptance.get("status") == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
            asum.get("current_phase_acceptance_allowed") is True,
            asum.get("strict_final_acceptance_allowed") is False,
            closeout.get("status") == "PASS-PROJECT-CLOSEOUT-FORECAST",
            csum.get("current_scope_can_be_closed_now") is True,
            csum.get("strict_master_plan_can_be_closed_now") is False,
            strict_gate.get("status") == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS",
            strictgatesum.get("strict_master_plan_completion_gate_ready") is True,
            strictgatesum.get("current_scope_closure_allowed") is True,
            strictgatesum.get("strict_master_plan_completion_allowed") is False,
            drop_index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
            dropindexsum.get("strict_external_artifact_drop_index_ready") is True,
            drop_checklist.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST",
            dropchecklistsum.get("strict_external_artifact_drop_checklist_ready") is True,
            release.get("status") == "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF",
            rsum.get("release_candidate_can_be_used_for_current_priority_scope") is True,
            current_status.get("status") == "PASS-CURRENT-STATUS-CLI",
            ssum.get("current_status_cli_ready") is True,
            open_blockers == EXPECTED_STRICT_BLOCKERS,
            full_log_passed(last_full_log),
            not readme_missing,
            not runbook_missing,
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "human-facing final handoff note for the current usable scope",
        "summary": {
            "current_scope_final_handoff_note_ready": handoff_ready,
            "delivery_package_status": delivery["status"],
            "delivery_package_ready": dsum["current_scope_delivery_package_ready"],
            "acceptance_gate_status": acceptance["status"],
            "current_phase_acceptance_allowed": asum["current_phase_acceptance_allowed"],
            "strict_final_acceptance_allowed": asum["strict_final_acceptance_allowed"],
            "release_candidate_status": release["status"],
            "release_candidate_usable_for_current_priority_scope": rsum[
                "release_candidate_can_be_used_for_current_priority_scope"
            ],
            "current_scope_can_be_closed_now": csum["current_scope_can_be_closed_now"],
            "current_scope_closeout_estimate": csum["current_scope_closeout_estimate"],
            "strict_master_plan_complete": dsum["strict_master_plan_complete"],
            "strict_master_plan_can_be_closed_now": csum["strict_master_plan_can_be_closed_now"],
            "strict_master_plan_completion_gate_status": strict_gate["status"],
            "strict_master_plan_completion_gate_ready": strictgatesum[
                "strict_master_plan_completion_gate_ready"
            ],
            "strict_completion_current_scope_closure_allowed": strictgatesum[
                "current_scope_closure_allowed"
            ],
            "strict_completion_allowed": strictgatesum["strict_master_plan_completion_allowed"],
            "strict_completion_external_artifacts_missing": strictgatesum["strict_external_artifacts_missing"],
            "strict_external_artifact_drop_index_status": drop_index["status"],
            "strict_external_artifact_drop_index_ready": dropindexsum[
                "strict_external_artifact_drop_index_ready"
            ],
            "strict_external_artifact_drop_checklist_status": drop_checklist["status"],
            "strict_external_artifact_drop_checklist_ready": dropchecklistsum[
                "strict_external_artifact_drop_checklist_ready"
            ],
            "strict_external_artifact_drop_checklist_missing_file_count": dropchecklistsum["missing_file_count"],
            "strict_external_artifact_drop_checklist_done_count": dropchecklistsum["checklist_done_count"],
            "strict_closeout_requires_external_artifacts": csum["strict_closeout_requires_external_artifacts"],
            "open_strict_blocker_count": dsum["open_strict_blocker_count"],
            "open_strict_blockers": sorted(open_blockers),
            "last_full_current_scope_log": str(last_full_log),
            "last_full_current_scope_log_glob": str(FULL_LOG_DIR / FULL_LOG_GLOB),
            "last_full_current_scope_log_passed": full_log_passed(last_full_log),
            "required_command_count": len(REQUIRED_COMMANDS),
            "required_doc_snippet_count": len(REQUIRED_DOC_SNIPPETS),
            "readme_missing_snippet_count": len(readme_missing),
            "runbook_missing_snippet_count": len(runbook_missing),
        },
        "operator_handoff": {
            "start_here": [
                "cd <my-pele-repository-root>",
                "python3 tools/codex_print_current_status.py",
                "python3 tools/write_current_operator_quickstart_smoke_report.py",
                "bash tools/verify_current_operator_quickstart_smoke.sh",
                "bash tools/codex_verify_current_scope.sh",
            ],
            "current_scope_is_usable": True,
            "strict_master_plan_is_complete": False,
            "handoff_documents": {
                "readme": str(README),
                "operator_runbook": str(RUNBOOK),
                "delivery_package_report": str(DELIVERY_PACKAGE),
                "project_closeout_acceptance_gate_report": str(ACCEPTANCE_GATE),
                "current_operator_quickstart_smoke_report": (
                    "docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/"
                    "current_operator_quickstart_smoke_report.json"
                ),
                "closeout_forecast_report": str(CLOSEOUT_FORECAST),
                "strict_completion_gate_report": str(STRICT_COMPLETION_GATE),
                "strict_external_artifact_drop_index_report": str(STRICT_ARTIFACT_DROP_INDEX),
                "strict_external_artifact_drop_checklist_report": str(STRICT_ARTIFACT_DROP_CHECKLIST),
            },
        },
        "missing_doc_snippets": {
            "readme": readme_missing,
            "operator_runbook": runbook_missing,
        },
        "evidence_files": [
            evidence_entry("current_scope_delivery_package", DELIVERY_PACKAGE),
            evidence_entry("project_closeout_acceptance_gate", ACCEPTANCE_GATE),
            evidence_entry("project_closeout_forecast", CLOSEOUT_FORECAST),
            evidence_entry("strict_master_plan_completion_gate", STRICT_COMPLETION_GATE),
            evidence_entry("strict_external_artifact_drop_index", STRICT_ARTIFACT_DROP_INDEX),
            evidence_entry("strict_external_artifact_drop_checklist", STRICT_ARTIFACT_DROP_CHECKLIST),
            evidence_entry("current_scope_release_candidate_handoff", RELEASE_CANDIDATE),
            evidence_entry("current_status_cli", CURRENT_STATUS),
            evidence_entry("last_full_current_scope_log", last_full_log),
            evidence_entry("readme", README),
            evidence_entry("operator_runbook", RUNBOOK),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_scope_final_handoff_note_ready") is True, "final handoff note is not ready")
    require(summary.get("delivery_package_status") == "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE", "delivery package not passing")
    require(summary.get("delivery_package_ready") is True, "delivery package not ready")
    require(
        summary.get("acceptance_gate_status") == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
        "acceptance gate not passing",
    )
    require(summary.get("current_phase_acceptance_allowed") is True, "current phase acceptance not allowed")
    require(summary.get("strict_final_acceptance_allowed") is False, "strict final acceptance unexpectedly allowed")
    require(summary.get("release_candidate_status") == "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF", "release candidate not passing")
    require(summary.get("release_candidate_usable_for_current_priority_scope") is True, "release candidate not usable")
    require(summary.get("current_scope_can_be_closed_now") is True, "current scope is not closable")
    require(summary.get("strict_master_plan_complete") is False, "strict master plan unexpectedly complete")
    require(summary.get("strict_master_plan_can_be_closed_now") is False, "strict closeout overclaimed")
    require(
        summary.get("strict_master_plan_completion_gate_status")
        == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS",
        "strict completion gate status is unexpected",
    )
    require(summary.get("strict_master_plan_completion_gate_ready") is True, "strict completion gate is not ready")
    require(
        summary.get("strict_completion_current_scope_closure_allowed") is True,
        "strict completion gate does not allow current-scope closure",
    )
    require(summary.get("strict_completion_allowed") is False, "strict completion gate overclaims completion")
    require(
        summary.get("strict_completion_external_artifacts_missing") is True,
        "strict completion gate lost external-artifact boundary",
    )
    require(
        summary.get("strict_external_artifact_drop_index_status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
        "strict external artifact drop index status is not passing",
    )
    require(
        summary.get("strict_external_artifact_drop_index_ready") is True,
        "strict external artifact drop index is not ready",
    )
    require(
        summary.get("strict_external_artifact_drop_checklist_status")
        == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST",
        "strict external artifact drop checklist status is not passing",
    )
    require(
        summary.get("strict_external_artifact_drop_checklist_ready") is True,
        "strict external artifact drop checklist is not ready",
    )
    checklist_missing_count = summary.get("strict_external_artifact_drop_checklist_missing_file_count")
    checklist_done_count = summary.get("strict_external_artifact_drop_checklist_done_count")
    require(isinstance(checklist_missing_count, int), "drop checklist missing count is not an integer")
    require(isinstance(checklist_done_count, int), "drop checklist done count is not an integer")
    require(0 <= checklist_missing_count <= 14, "drop checklist missing count is outside the contract range")
    require(0 <= checklist_done_count <= 14, "drop checklist done count is outside the contract range")
    require(
        checklist_missing_count + checklist_done_count == 14,
        "drop checklist done and missing counts do not match contract total",
    )
    require(summary.get("strict_closeout_requires_external_artifacts") is True, "strict external artifact boundary missing")
    require(summary.get("open_strict_blocker_count") == 3, "unexpected blocker count")
    require(set(summary.get("open_strict_blockers", [])) == EXPECTED_STRICT_BLOCKERS, "unexpected blocker set")
    require(summary.get("last_full_current_scope_log_passed") is True, "latest full log did not pass")
    require(summary.get("readme_missing_snippet_count") == 0, "README handoff snippets missing")
    require(summary.get("runbook_missing_snippet_count") == 0, "runbook handoff snippets missing")
    handoff = data.get("operator_handoff")
    require(isinstance(handoff, dict), "missing operator handoff")
    require(handoff.get("current_scope_is_usable") is True, "operator handoff does not mark current scope usable")
    require(handoff.get("strict_master_plan_is_complete") is False, "operator handoff overclaims strict completion")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            if entry.get("label") in VOLATILE_HASH_LABELS:
                require(
                    entry.get("hash_verification") == "skipped-cycle-reference",
                    f"missing cycle-reference hash policy for {path}",
                )
                continue
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current-Scope Final Handoff Note",
        "",
        f"- Status: `{report['status']}`",
        f"- Final handoff note ready: `{summary['current_scope_final_handoff_note_ready']}`",
        f"- Current phase acceptance allowed: `{summary['current_phase_acceptance_allowed']}`",
        f"- Strict final acceptance allowed: `{summary['strict_final_acceptance_allowed']}`",
        f"- Current scope can be closed now: `{summary['current_scope_can_be_closed_now']}`",
        f"- Current scope closeout estimate: `{summary['current_scope_closeout_estimate']}`",
        f"- Strict master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Strict master-plan can be closed now: `{summary['strict_master_plan_can_be_closed_now']}`",
        f"- Strict completion gate: `{summary['strict_master_plan_completion_gate_status']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        f"- Strict external artifact drop index: `{summary['strict_external_artifact_drop_index_status']}`",
        f"- Strict external artifact drop checklist: `{summary['strict_external_artifact_drop_checklist_status']}`",
        f"- Strict closeout requires external artifacts: `{summary['strict_closeout_requires_external_artifacts']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        "",
        "## Start Here",
        "",
    ]
    for command in report["operator_handoff"]["start_here"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Handoff Documents", ""])
    for label, value in report["operator_handoff"]["handoff_documents"].items():
        lines.append(f"- `{label}`: `{value}`")
    lines.extend(["", "## Open Strict Blockers", ""])
    for blocker in summary["open_strict_blockers"]:
        lines.append(f"- `{blocker}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_scope_final_handoff_note VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_scope_final_handoff_note PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
