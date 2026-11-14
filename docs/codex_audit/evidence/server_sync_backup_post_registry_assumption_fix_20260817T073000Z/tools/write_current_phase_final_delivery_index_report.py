#!/usr/bin/env python3
"""Write/verify the current-phase final delivery index."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-PHASE-FINAL-DELIVERY-INDEX"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_phase_final_delivery_index_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_phase_final_delivery_index_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_phase_final_delivery_index_report.md"

README = Path("README.md")
RUNBOOK = Path("docs/codex_audit/current_scope_operator_runbook.md")
STATUS_CLI = Path("tools/codex_print_current_status.py")
RELEASE_REFRESH_WRAPPER = Path("tools/run_current_scope_release_refresh.sh")
DELIVERY_PACKAGE = Path(
    "docs/codex_audit/evidence/current_scope_delivery_package_20260812/"
    "current_scope_delivery_package_report.json"
)
FINAL_HANDOFF = Path(
    "docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/"
    "current_scope_final_handoff_note_report.json"
)
CLOSURE_CERTIFICATE = Path(
    "docs/codex_audit/evidence/current_phase_closure_certificate_20260812/"
    "current_phase_closure_certificate_report.json"
)
ACTION_PACK = Path(
    "docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/"
    "strict_master_plan_closeout_action_pack_report.json"
)
STATUS_CLI_REPORT = Path(
    "docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json"
)
SNAPSHOT = Path(
    "docs/codex_audit/evidence/current_scope_state_snapshot_20260803/"
    "current_scope_state_snapshot_report.json"
)
FULL_LOG_DIR = Path("docs/codex_audit/evidence/current_scope_last_run_20260807")
FULL_LOG_GLOB = "current_scope_verify_after_*.log"

EXPECTED_STRICT_MISSING_TOTAL = 14


class FinalDeliveryIndexError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FinalDeliveryIndexError(message)


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
        raise FinalDeliveryIndexError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FinalDeliveryIndexError(f"invalid JSON evidence {path}: {exc}") from exc
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
    return "CURRENT_SCOPE_RC=0" in text and "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION" in text


def latest_passing_full_log() -> Path:
    candidates = sorted(FULL_LOG_DIR.glob(FULL_LOG_GLOB), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        if full_log_passed(path):
            return path
    raise FinalDeliveryIndexError(f"no passing full current-scope log found in {FULL_LOG_DIR}")


def build_report() -> dict[str, Any]:
    delivery = load_json(DELIVERY_PACKAGE)
    handoff = load_json(FINAL_HANDOFF)
    closure = load_json(CLOSURE_CERTIFICATE)
    action_pack = load_json(ACTION_PACK)
    status_cli = load_json(STATUS_CLI_REPORT)
    snapshot = load_json(SNAPSHOT)
    latest_log = latest_passing_full_log()

    delivery_summary = delivery["summary"]
    handoff_summary = handoff["summary"]
    closure_summary = closure["summary"]
    action_summary = action_pack["summary"]
    status_summary = status_cli["summary"]
    snapshot_summary = snapshot["summary"]

    ready = all(
        [
            README.is_file(),
            RUNBOOK.is_file(),
            STATUS_CLI.is_file(),
            RELEASE_REFRESH_WRAPPER.is_file(),
            delivery.get("status") == "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
            delivery_summary.get("current_scope_delivery_package_ready") is True,
            handoff.get("status") == "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
            handoff_summary.get("current_scope_final_handoff_note_ready") is True,
            handoff_summary.get("readme_missing_snippet_count") == 0,
            handoff_summary.get("runbook_missing_snippet_count") == 0,
            closure.get("status") == "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE",
            closure_summary.get("current_phase_closeable") is True,
            closure_summary.get("strict_master_plan_closure_allowed") is False,
            action_pack.get("status") == "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK",
            action_summary.get("strict_master_plan_closeout_action_pack_ready") is True,
            action_summary.get("done_action_item_count") == 0,
            action_summary.get("missing_action_item_count") == EXPECTED_STRICT_MISSING_TOTAL,
            action_summary.get("strict_master_plan_completion_allowed") is False,
            status_cli.get("status") == "PASS-CURRENT-STATUS-CLI",
            status_summary.get("current_status_cli_ready") is True,
            snapshot.get("status") == "PASS-CURRENT-SCOPE-STATE-SNAPSHOT",
            snapshot_summary.get("current_scope_state_snapshot_ready") is True,
            full_log_passed(latest_log),
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "single-page index for the current closeable phase and remaining strict closeout actions",
        "summary": {
            "current_phase_final_delivery_index_ready": ready,
            "current_phase_closeable": closure_summary.get("current_phase_closeable"),
            "strict_master_plan_closure_allowed": closure_summary.get("strict_master_plan_closure_allowed"),
            "strict_master_plan_still_open": closure_summary.get("strict_master_plan_still_open"),
            "strict_action_item_done_count": action_summary.get("done_action_item_count"),
            "strict_action_item_missing_count": action_summary.get("missing_action_item_count"),
            "latest_full_current_scope_log": str(latest_log),
            "latest_full_current_scope_log_passed": full_log_passed(latest_log),
            "state_snapshot_key_report_count": snapshot_summary.get("key_report_count"),
        },
        "start_here": [
            "cd <my-pele-repo-root>",
            "python3 tools/codex_print_current_status.py",
            "python3 tools/codex_print_current_status.py --json",
            "bash tools/run_current_scope_release_refresh.sh",
        ],
        "delivery_documents": {
            "readme": str(README),
            "operator_runbook": str(RUNBOOK),
            "current_status_cli": str(STATUS_CLI),
            "release_refresh_wrapper": str(RELEASE_REFRESH_WRAPPER),
            "delivery_package_report": str(DELIVERY_PACKAGE),
            "final_handoff_note_report": str(FINAL_HANDOFF),
            "closure_certificate_report": str(CLOSURE_CERTIFICATE),
            "strict_closeout_action_pack_report": str(ACTION_PACK),
            "latest_full_current_scope_log": str(latest_log),
        },
        "current_scope_claim": {
            "engineering_v1_closeable": True,
            "strict_master_plan_complete": False,
            "strict_master_plan_remaining_external_artifacts": EXPECTED_STRICT_MISSING_TOTAL,
        },
        "evidence_files": [
            evidence_entry("readme", README),
            evidence_entry("operator_runbook", RUNBOOK),
            evidence_entry("current_status_cli", STATUS_CLI),
            evidence_entry("release_refresh_wrapper", RELEASE_REFRESH_WRAPPER),
            evidence_entry("current_scope_delivery_package", DELIVERY_PACKAGE),
            evidence_entry("current_scope_final_handoff_note", FINAL_HANDOFF),
            evidence_entry("current_phase_closure_certificate", CLOSURE_CERTIFICATE),
            evidence_entry("strict_closeout_action_pack", ACTION_PACK),
            evidence_entry("current_status_cli_report", STATUS_CLI_REPORT),
            evidence_entry("current_scope_state_snapshot", SNAPSHOT),
            evidence_entry("latest_full_current_scope_log", latest_log),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_phase_final_delivery_index_ready") is True, "final delivery index not ready")
    require(summary.get("current_phase_closeable") is True, "current phase is not closeable")
    require(summary.get("strict_master_plan_closure_allowed") is False, "strict closure was overclaimed")
    require(summary.get("strict_master_plan_still_open") is True, "strict master plan should still be open")
    require(summary.get("strict_action_item_done_count") == 0, "unexpected strict done count")
    require(
        summary.get("strict_action_item_missing_count") == EXPECTED_STRICT_MISSING_TOTAL,
        "unexpected strict missing count",
    )
    require(summary.get("latest_full_current_scope_log_passed") is True, "latest full log not passing")
    claim = data.get("current_scope_claim")
    require(isinstance(claim, dict), "missing current scope claim")
    require(claim.get("engineering_v1_closeable") is True, "engineering v1 should be closeable")
    require(claim.get("strict_master_plan_complete") is False, "strict master plan should not be complete")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Current Phase Final Delivery Index",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{s['current_phase_final_delivery_index_ready']}`",
        f"- Current phase closeable: `{s['current_phase_closeable']}`",
        f"- Strict master-plan closure allowed: `{s['strict_master_plan_closure_allowed']}`",
        f"- Strict action items done/missing: `{s['strict_action_item_done_count']}/{s['strict_action_item_missing_count']}`",
        f"- Latest full current-scope log: `{s['latest_full_current_scope_log']}`",
        "",
        "## Start Here",
        "",
    ]
    for command in report["start_here"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Delivery Documents", ""])
    for label, value in report["delivery_documents"].items():
        lines.append(f"- `{label}`: `{value}`")
    lines.extend(["", "## Boundary", ""])
    lines.append("- Current engineering/user-priority phase is closeable.")
    lines.append("- Strict master-plan completion remains open until the 14 external artifacts are provided and pass intake.")
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
        validate_report(data)
        print(f"current_phase_final_delivery_index VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_phase_final_delivery_index PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
