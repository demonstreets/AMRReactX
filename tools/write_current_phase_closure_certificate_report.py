#!/usr/bin/env python3
"""Write/verify the current-phase closure certificate."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_phase_closure_certificate_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_phase_closure_certificate_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_phase_closure_certificate_report.md"

ACCEPTANCE_GATE = Path(
    "docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/"
    "project_closeout_acceptance_gate_report.json"
)
FINAL_HANDOFF = Path(
    "docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/"
    "current_scope_final_handoff_note_report.json"
)
QUICKSTART_SMOKE = Path(
    "docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/"
    "current_operator_quickstart_smoke_report.json"
)
DELIVERY_PACKAGE = Path(
    "docs/codex_audit/evidence/current_scope_delivery_package_20260812/"
    "current_scope_delivery_package_report.json"
)
STRICT_COMPLETION_GATE = Path(
    "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
    "strict_master_plan_completion_gate_report.json"
)
FULL_LOG_DIR = Path("docs/codex_audit/evidence/current_scope_last_run_20260807")
FULL_LOG_GLOB = "current_scope_verify_after_*.log"


class ClosureCertificateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureCertificateError(message)


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
        raise ClosureCertificateError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ClosureCertificateError(f"invalid JSON evidence {path}: {exc}") from exc
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
    raise ClosureCertificateError("no passing full current-scope log found")


def build_report() -> dict[str, Any]:
    acceptance = load_json(ACCEPTANCE_GATE)
    final_handoff = load_json(FINAL_HANDOFF)
    quickstart = load_json(QUICKSTART_SMOKE)
    delivery = load_json(DELIVERY_PACKAGE)
    strict_gate = load_json(STRICT_COMPLETION_GATE)
    latest_log = latest_passing_full_log()

    asum = acceptance["summary"]
    hsum = final_handoff["summary"]
    qsum = quickstart["summary"]
    dsum = delivery["summary"]
    strictsum = strict_gate["summary"]

    current_phase_closeable = all(
        [
            acceptance.get("status") == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
            asum.get("current_phase_acceptance_allowed") is True,
            final_handoff.get("status") == "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
            hsum.get("current_scope_final_handoff_note_ready") is True,
            quickstart.get("status") == "PASS-CURRENT-OPERATOR-QUICKSTART-SMOKE",
            qsum.get("current_operator_quickstart_smoke_ready") is True,
            delivery.get("status") == "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
            dsum.get("current_scope_delivery_package_ready") is True,
            full_log_passed(latest_log),
        ]
    )
    done = asum.get("strict_external_artifact_done_count")
    missing = asum.get("strict_external_artifact_missing_count")
    open_blockers = strictsum.get("open_strict_blocker_count")
    strict_allowed = strictsum.get("strict_master_plan_completion_allowed") is True
    strict_final_allowed = asum.get("strict_final_acceptance_allowed") is True
    artifact_counts_consistent = (
        isinstance(done, int)
        and isinstance(missing, int)
        and 0 <= done <= 14
        and 0 <= missing <= 14
        and done + missing == 14
    )
    blocker_count_consistent = isinstance(open_blockers, int) and 0 <= open_blockers <= 3
    strict_still_open = not strict_allowed and not strict_final_allowed

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "current project phase closure certificate; not strict master-plan completion",
        "summary": {
            "current_phase_closure_certificate_ready": current_phase_closeable and strict_still_open,
            "current_phase_closeable": current_phase_closeable,
            "strict_master_plan_closure_allowed": strict_allowed,
            "strict_master_plan_still_open": strict_still_open,
            "current_phase_acceptance_allowed": asum.get("current_phase_acceptance_allowed"),
            "strict_final_acceptance_allowed": strict_final_allowed,
            "current_operator_quickstart_smoke_ready": qsum.get("current_operator_quickstart_smoke_ready"),
            "current_scope_final_handoff_note_ready": hsum.get("current_scope_final_handoff_note_ready"),
            "current_scope_delivery_package_ready": dsum.get("current_scope_delivery_package_ready"),
            "strict_external_artifact_done_count": done,
            "strict_external_artifact_missing_count": missing,
            "strict_external_artifact_counts_consistent": artifact_counts_consistent,
            "open_strict_blocker_count": open_blockers,
            "strict_blocker_count_consistent": blocker_count_consistent,
            "last_full_current_scope_log": str(latest_log),
            "last_full_current_scope_log_passed": full_log_passed(latest_log),
        },
        "closure_decision": {
            "current_phase": "CLOSED_FOR_CURRENT_USABLE_SCOPE",
            "strict_master_plan": "NOT_CLOSED_AWAITING_EXTERNAL_ARTIFACTS",
            "operator_start_here": final_handoff.get("operator_handoff", {}).get("start_here", []),
        },
        "evidence_files": [
            evidence_entry("project_closeout_acceptance_gate", ACCEPTANCE_GATE),
            evidence_entry("current_scope_final_handoff_note", FINAL_HANDOFF),
            evidence_entry("current_operator_quickstart_smoke", QUICKSTART_SMOKE),
            evidence_entry("current_scope_delivery_package", DELIVERY_PACKAGE),
            evidence_entry("strict_master_plan_completion_gate", STRICT_COMPLETION_GATE),
            evidence_entry("last_full_current_scope_log", latest_log),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_phase_closure_certificate_ready") is True, "closure certificate is not ready")
    require(summary.get("current_phase_closeable") is True, "current phase is not closeable")
    require(summary.get("strict_master_plan_closure_allowed") is False, "strict master-plan closure overclaimed")
    require(summary.get("strict_master_plan_still_open") is True, "strict master-plan boundary missing")
    require(summary.get("current_phase_acceptance_allowed") is True, "current phase acceptance not allowed")
    require(summary.get("strict_final_acceptance_allowed") is False, "strict final acceptance overclaimed")
    require(summary.get("current_operator_quickstart_smoke_ready") is True, "quickstart smoke is not ready")
    require(summary.get("current_scope_final_handoff_note_ready") is True, "final handoff is not ready")
    require(summary.get("current_scope_delivery_package_ready") is True, "delivery package is not ready")
    require(summary.get("strict_external_artifact_counts_consistent") is True, "strict artifact counts inconsistent")
    require(summary.get("strict_blocker_count_consistent") is True, "strict blocker count inconsistent")
    done = summary.get("strict_external_artifact_done_count")
    missing = summary.get("strict_external_artifact_missing_count")
    blockers = summary.get("open_strict_blocker_count")
    require(isinstance(done, int) and isinstance(missing, int), "strict artifact counts are not integers")
    require(done + missing == 14, "strict artifact counts do not sum to 14")
    require(isinstance(blockers, int) and 0 <= blockers <= 3, "strict blocker count outside expected range")
    require(summary.get("last_full_current_scope_log_passed") is True, "last full current-scope log did not pass")
    decision = data.get("closure_decision", {})
    require(decision.get("current_phase") == "CLOSED_FOR_CURRENT_USABLE_SCOPE", "current phase decision changed")
    require(
        decision.get("strict_master_plan") == "NOT_CLOSED_AWAITING_EXTERNAL_ARTIFACTS",
        "strict master-plan decision changed",
    )
    start_here = decision.get("operator_start_here", [])
    require("python3 tools/write_current_operator_quickstart_smoke_report.py" in start_here, "quickstart writer missing")
    require("bash tools/verify_current_operator_quickstart_smoke.sh" in start_here, "quickstart verifier missing")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    decision = report["closure_decision"]
    lines = [
        "# Current Phase Closure Certificate",
        "",
        f"- Status: `{report['status']}`",
        f"- Current phase closeable: `{summary['current_phase_closeable']}`",
        f"- Strict master-plan closure allowed: `{summary['strict_master_plan_closure_allowed']}`",
        f"- Strict external artifacts done/missing: `{summary['strict_external_artifact_done_count']}/{summary['strict_external_artifact_missing_count']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        f"- Last full current-scope log: `{summary['last_full_current_scope_log']}`",
        "",
        "## Decision",
        "",
        f"- Current phase: `{decision['current_phase']}`",
        f"- Strict master-plan: `{decision['strict_master_plan']}`",
        "",
        "## Operator Start Here",
        "",
    ]
    for command in decision["operator_start_here"]:
        lines.append(f"- `{command}`")
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
        print(f"current_phase_closure_certificate VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_phase_closure_certificate PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
