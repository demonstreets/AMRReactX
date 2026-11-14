#!/usr/bin/env python3
"""Write/verify the current-scope release refresh entrypoint report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-SCOPE-RELEASE-REFRESH-ENTRYPOINT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_scope_release_refresh_entrypoint_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_scope_release_refresh_entrypoint_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_scope_release_refresh_entrypoint_report.md"

WRAPPER = Path("tools/run_current_scope_release_refresh.sh")
README = Path("README.md")
RUNBOOK = Path("docs/codex_audit/current_scope_operator_runbook.md")
DELIVERY_PACKAGE = Path(
    "docs/codex_audit/evidence/current_scope_delivery_package_20260812/"
    "current_scope_delivery_package_report.json"
)
FINAL_HANDOFF = Path(
    "docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/"
    "current_scope_final_handoff_note_report.json"
)
QUICKSTART_SMOKE = Path(
    "docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/"
    "current_operator_quickstart_smoke_report.json"
)
CLOSURE_CERTIFICATE = Path(
    "docs/codex_audit/evidence/current_phase_closure_certificate_20260812/"
    "current_phase_closure_certificate_report.json"
)
STRICT_CLOSEOUT_ACTION_PACK = Path(
    "docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/"
    "strict_master_plan_closeout_action_pack_report.json"
)
FINAL_DELIVERY_INDEX = Path(
    "docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/"
    "current_phase_final_delivery_index_report.json"
)
COMMAND_INVENTORY = Path(
    "docs/codex_audit/evidence/current_operator_command_inventory_20260803/"
    "current_operator_command_inventory_report.json"
)
WORKTREE_HYGIENE = Path(
    "docs/codex_audit/evidence/current_worktree_hygiene_20260803/"
    "current_worktree_hygiene_report.json"
)
SUNDIALS_LOCAL_LINK_AUDIT = Path(
    "docs/codex_audit/evidence/sundials_local_link_audit_20260820/"
    "sundials_local_link_audit_report.json"
)
WORKTREE_REVIEW_QUEUE = Path(
    "docs/codex_audit/evidence/current_worktree_review_queue_20260820/"
    "current_worktree_review_queue_report.json"
)
STATUS_CLI = Path(
    "docs/codex_audit/evidence/current_status_cli_20260803/"
    "current_status_cli_report.json"
)
STATE_SNAPSHOT = Path(
    "docs/codex_audit/evidence/current_scope_state_snapshot_20260803/"
    "current_scope_state_snapshot_report.json"
)
HASH_CYCLE_GUARD = Path(
    "docs/codex_audit/evidence/current_report_hash_cycle_guard_20260818/"
    "current_report_hash_cycle_guard_report.json"
)
FULL_LOG_DIR = Path("docs/codex_audit/evidence/current_scope_last_run_20260807")
FULL_LOG_GLOB = "current_scope_verify_after_*.log"

REQUIRED_WRAPPER_SNIPPETS = [
    "bash tools/codex_verify_current_scope.sh",
    "CURRENT_SCOPE_RC=$rc",
    "python3 tools/write_current_scope_delivery_package_report.py",
    "bash tools/verify_current_scope_delivery_package.sh",
    "python3 tools/write_current_scope_final_handoff_note_report.py",
    "bash tools/verify_current_scope_final_handoff_note.sh",
    "python3 tools/write_current_operator_quickstart_smoke_report.py",
    "bash tools/verify_current_operator_quickstart_smoke.sh",
    "python3 tools/write_current_phase_closure_certificate_report.py",
    "bash tools/verify_current_phase_closure_certificate.sh",
    "python3 tools/write_strict_master_plan_closeout_action_pack_report.py",
    "bash tools/verify_strict_master_plan_closeout_action_pack.sh",
    "bash tools/run_strict_external_artifact_receiving_preflight.sh",
    "python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py",
    "bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh",
    "python3 tools/write_current_phase_final_delivery_index_report.py",
    "bash tools/verify_current_phase_final_delivery_index.sh",
    "python3 tools/write_current_worktree_hygiene_report.py",
    "bash tools/verify_current_worktree_hygiene.sh",
    "python3 tools/write_current_worktree_source_ledger_report.py",
    "bash tools/verify_current_worktree_source_ledger.sh",
    "python3 tools/write_current_case_output_cleanup_manifest_report.py",
    "bash tools/verify_current_case_output_cleanup_manifest.sh",
    "python3 tools/write_sundials_local_link_audit_report.py",
    "bash tools/verify_sundials_local_link_audit.sh",
    "python3 tools/write_current_worktree_review_queue_report.py",
    "bash tools/verify_current_worktree_review_queue.sh",
    "python3 tools/write_current_phase_release_manifest_report.py",
    "bash tools/verify_current_phase_release_manifest.sh",
    "python3 tools/write_current_status_cli_report.py",
    "bash tools/verify_current_status_cli.sh",
    "python3 tools/write_current_report_hash_cycle_guard_report.py",
    "bash tools/verify_current_report_hash_cycle_guard.sh",
    "bash tools/verify_current_scope_state_snapshot.sh",
]

REQUIRED_DOC_SNIPPETS = [
    "Current-Scope Release Refresh",
    "bash tools/run_current_scope_release_refresh.sh",
    "PASS-CURRENT-SCOPE-RELEASE-REFRESH-ENTRYPOINT",
    "docs/codex_audit/evidence/current_scope_release_refresh_entrypoint_20260812/current_scope_release_refresh_entrypoint_report.json",
]


class ReleaseRefreshEntrypointError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseRefreshEntrypointError(message)


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
        raise ReleaseRefreshEntrypointError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseRefreshEntrypointError(f"invalid JSON evidence {path}: {exc}") from exc
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


def bash_syntax_ok(path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["bash", "-n", str(path)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    return result.returncode == 0, result.stdout.strip()


def missing_snippets(path: Path, snippets: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [snippet for snippet in snippets if snippet not in text]


def log_has_success(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return "[current-scope] PASS current-scope verification chain" in text and "CURRENT_SCOPE_RC=0" in text


def latest_passing_log() -> Path:
    require(FULL_LOG_DIR.is_dir(), f"missing full log directory: {FULL_LOG_DIR}")
    candidates = sorted(FULL_LOG_DIR.glob(FULL_LOG_GLOB), key=lambda path: path.stat().st_mtime, reverse=True)
    require(candidates, f"no full logs match {FULL_LOG_DIR / FULL_LOG_GLOB}")
    for path in candidates:
        if log_has_success(path):
            return path
    raise ReleaseRefreshEntrypointError(f"no passing full current-scope log found under {FULL_LOG_DIR}")


def build_report() -> dict[str, Any]:
    delivery = load_json(DELIVERY_PACKAGE)
    final_handoff = load_json(FINAL_HANDOFF)
    quickstart = load_json(QUICKSTART_SMOKE)
    closure_certificate = load_json(CLOSURE_CERTIFICATE)
    strict_closeout_action_pack = load_json(STRICT_CLOSEOUT_ACTION_PACK)
    final_delivery_index = load_json(FINAL_DELIVERY_INDEX)
    command_inventory = load_json(COMMAND_INVENTORY)
    hygiene = load_json(WORKTREE_HYGIENE)
    sundials_audit = load_json(SUNDIALS_LOCAL_LINK_AUDIT)
    review_queue = load_json(WORKTREE_REVIEW_QUEUE)
    status_cli = load_json(STATUS_CLI)
    snapshot = load_json(STATE_SNAPSHOT)
    hash_cycle_guard = load_json(HASH_CYCLE_GUARD)
    wrapper_syntax_ok, wrapper_syntax_output = bash_syntax_ok(WRAPPER)
    wrapper_missing = missing_snippets(WRAPPER, REQUIRED_WRAPPER_SNIPPETS)
    readme_missing = missing_snippets(README, REQUIRED_DOC_SNIPPETS)
    runbook_missing = missing_snippets(RUNBOOK, REQUIRED_DOC_SNIPPETS)
    latest_log = latest_passing_log()

    ready = all(
        [
            WRAPPER.is_file(),
            wrapper_syntax_ok,
            not wrapper_missing,
            not readme_missing,
            not runbook_missing,
            delivery.get("status") == "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
            delivery["summary"].get("current_scope_delivery_package_ready") is True,
            final_handoff.get("status") == "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
            final_handoff["summary"].get("current_scope_final_handoff_note_ready") is True,
            quickstart.get("status") == "PASS-CURRENT-OPERATOR-QUICKSTART-SMOKE",
            quickstart["summary"].get("current_operator_quickstart_smoke_ready") is True,
            closure_certificate.get("status") == "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE",
            closure_certificate["summary"].get("current_phase_closure_certificate_ready") is True,
            strict_closeout_action_pack.get("status") == "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK",
            strict_closeout_action_pack["summary"].get("strict_master_plan_closeout_action_pack_ready") is True,
            strict_closeout_action_pack["summary"].get("strict_master_plan_completion_allowed") is False,
            final_delivery_index.get("status") == "PASS-CURRENT-PHASE-FINAL-DELIVERY-INDEX",
            final_delivery_index["summary"].get("current_phase_final_delivery_index_ready") is True,
            command_inventory.get("status") == "PASS-CURRENT-OPERATOR-COMMAND-INVENTORY",
            command_inventory["summary"].get("current_operator_command_inventory_ready") is True,
            command_inventory["summary"].get("missing_tool_count") == 0,
            command_inventory["summary"].get("syntax_failure_count") == 0,
            hygiene.get("status") == "AUDITED-CURRENT-WORKTREE-HYGIENE",
            hygiene["summary"].get("worktree_hygiene_audited") is True,
            sundials_audit.get("status") == "PASS-SUNDIALS-LOCAL-LINK-AUDIT",
            sundials_audit["summary"].get("audit_ready") is True,
            sundials_audit["summary"].get("safe_to_auto_restore") is False,
            review_queue.get("status") == "PASS-CURRENT-WORKTREE-REVIEW-QUEUE",
            review_queue["summary"].get("review_queue_ready") is True,
            status_cli.get("status") == "PASS-CURRENT-STATUS-CLI",
            status_cli["summary"].get("current_status_cli_ready") is True,
            snapshot.get("status") == "PASS-CURRENT-SCOPE-STATE-SNAPSHOT",
            snapshot["summary"].get("current_scope_state_snapshot_ready") is True,
            hash_cycle_guard.get("status") == "PASS-CURRENT-REPORT-HASH-CYCLE-GUARD",
            hash_cycle_guard["summary"].get("current_report_hash_cycle_guard_ready") is True,
            hash_cycle_guard["summary"].get("failure_count") == 0,
            log_has_success(latest_log),
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "summary": {
            "current_scope_release_refresh_entrypoint_ready": ready,
            "wrapper_path": str(WRAPPER),
            "wrapper_bash_syntax_ok": wrapper_syntax_ok,
            "wrapper_missing_snippet_count": len(wrapper_missing),
            "readme_missing_snippet_count": len(readme_missing),
            "runbook_missing_snippet_count": len(runbook_missing),
            "delivery_package_ready": delivery["summary"]["current_scope_delivery_package_ready"],
            "final_handoff_note_ready": final_handoff["summary"]["current_scope_final_handoff_note_ready"],
            "operator_quickstart_smoke_ready": quickstart["summary"][
                "current_operator_quickstart_smoke_ready"
            ],
            "current_phase_closure_certificate_ready": closure_certificate["summary"][
                "current_phase_closure_certificate_ready"
            ],
            "strict_master_plan_closeout_action_pack_ready": strict_closeout_action_pack["summary"][
                "strict_master_plan_closeout_action_pack_ready"
            ],
            "strict_master_plan_closeout_action_pack_missing_count": strict_closeout_action_pack["summary"][
                "missing_action_item_count"
            ],
            "strict_master_plan_closeout_action_pack_completion_allowed": strict_closeout_action_pack["summary"][
                "strict_master_plan_completion_allowed"
            ],
            "current_phase_final_delivery_index_ready": final_delivery_index["summary"][
                "current_phase_final_delivery_index_ready"
            ],
            "current_operator_command_inventory_ready": command_inventory["summary"][
                "current_operator_command_inventory_ready"
            ],
            "current_operator_command_inventory_command_count": command_inventory["summary"][
                "command_count"
            ],
            "current_operator_command_inventory_required_snippet_count": command_inventory["summary"][
                "required_snippet_count"
            ],
            "current_operator_command_inventory_missing_required_snippet_count": command_inventory["summary"][
                "missing_required_snippet_count"
            ],
            "current_operator_command_inventory_missing_tool_count": command_inventory["summary"][
                "missing_tool_count"
            ],
            "current_operator_command_inventory_syntax_failure_count": command_inventory["summary"][
                "syntax_failure_count"
            ],
            "current_worktree_hygiene_ready": hygiene["summary"]["worktree_hygiene_audited"],
            "current_worktree_dirty_entry_count": hygiene["summary"]["dirty_entry_count"],
            "sundials_local_link_audit_ready": sundials_audit["summary"]["audit_ready"],
            "sundials_local_link_drift_present": sundials_audit["summary"]["local_link_drift_present"],
            "sundials_local_link_safe_to_auto_restore": sundials_audit["summary"]["safe_to_auto_restore"],
            "current_worktree_review_queue_ready": review_queue["summary"]["review_queue_ready"],
            "current_worktree_review_queue_high_attention_count": review_queue["summary"][
                "high_attention_entry_count"
            ],
            "current_status_cli_ready": status_cli["summary"]["current_status_cli_ready"],
            "state_snapshot_ready": snapshot["summary"]["current_scope_state_snapshot_ready"],
            "current_report_hash_cycle_guard_ready": hash_cycle_guard["summary"][
                "current_report_hash_cycle_guard_ready"
            ],
            "current_report_hash_cycle_guard_failure_count": hash_cycle_guard["summary"]["failure_count"],
            "latest_passing_full_current_scope_log": str(latest_log),
            "latest_passing_full_current_scope_log_passed": log_has_success(latest_log),
        },
        "missing_snippets": {
            "wrapper": wrapper_missing,
            "readme": readme_missing,
            "operator_runbook": runbook_missing,
        },
        "wrapper_syntax_output": wrapper_syntax_output,
        "operator_command": "bash tools/run_current_scope_release_refresh.sh",
        "evidence_files": [
            evidence_entry("release_refresh_wrapper", WRAPPER),
            evidence_entry("readme", README),
            evidence_entry("operator_runbook", RUNBOOK),
            evidence_entry("current_scope_delivery_package", DELIVERY_PACKAGE),
            evidence_entry("current_scope_final_handoff_note", FINAL_HANDOFF),
            evidence_entry("current_operator_quickstart_smoke", QUICKSTART_SMOKE),
            evidence_entry("current_phase_closure_certificate", CLOSURE_CERTIFICATE),
            evidence_entry("strict_master_plan_closeout_action_pack", STRICT_CLOSEOUT_ACTION_PACK),
            evidence_entry("current_phase_final_delivery_index", FINAL_DELIVERY_INDEX),
            evidence_entry("current_operator_command_inventory", COMMAND_INVENTORY),
            evidence_entry("current_worktree_hygiene", WORKTREE_HYGIENE),
            evidence_entry("sundials_local_link_audit", SUNDIALS_LOCAL_LINK_AUDIT),
            evidence_entry("current_worktree_review_queue", WORKTREE_REVIEW_QUEUE),
            evidence_entry("latest_passing_full_current_scope_log", latest_log),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_scope_release_refresh_entrypoint_ready") is True, "release refresh entrypoint not ready")
    require(summary.get("wrapper_bash_syntax_ok") is True, "wrapper bash syntax check failed")
    require(summary.get("wrapper_missing_snippet_count") == 0, "wrapper required snippets missing")
    require(summary.get("readme_missing_snippet_count") == 0, "README release-refresh snippets missing")
    require(summary.get("runbook_missing_snippet_count") == 0, "runbook release-refresh snippets missing")
    require(summary.get("delivery_package_ready") is True, "delivery package not ready")
    require(summary.get("final_handoff_note_ready") is True, "final handoff note not ready")
    require(summary.get("operator_quickstart_smoke_ready") is True, "operator quickstart smoke not ready")
    require(
        summary.get("current_phase_closure_certificate_ready") is True,
        "current phase closure certificate not ready",
    )
    require(
        summary.get("strict_master_plan_closeout_action_pack_ready") is True,
        "strict closeout action pack not ready",
    )
    require(
        summary.get("strict_master_plan_closeout_action_pack_completion_allowed") is False,
        "strict closeout action pack overclaimed completion",
    )
    require(
        summary.get("current_phase_final_delivery_index_ready") is True,
        "current phase final delivery index not ready",
    )
    require(
        summary.get("current_operator_command_inventory_ready") is True,
        "current operator command inventory not ready",
    )
    require(
        isinstance(summary.get("current_operator_command_inventory_command_count"), int)
        and summary.get("current_operator_command_inventory_command_count") >= 300,
        "current operator command inventory command count is too small",
    )
    require(
        isinstance(summary.get("current_operator_command_inventory_required_snippet_count"), int)
        and summary.get("current_operator_command_inventory_required_snippet_count") >= 60,
        "current operator command inventory required-snippet count is too small",
    )
    require(
        summary.get("current_operator_command_inventory_missing_required_snippet_count") == 0,
        "current operator command inventory is missing required snippets",
    )
    require(
        summary.get("current_operator_command_inventory_missing_tool_count") == 0,
        "current operator command inventory has missing tools",
    )
    require(
        summary.get("current_operator_command_inventory_syntax_failure_count") == 0,
        "current operator command inventory has syntax failures",
    )
    require(summary.get("current_worktree_hygiene_ready") is True, "current worktree hygiene not audited")
    require(summary.get("sundials_local_link_audit_ready") is True, "SUNDIALS local link audit not ready")
    require(summary.get("sundials_local_link_safe_to_auto_restore") is False, "SUNDIALS auto-restore guard missing")
    require(summary.get("current_worktree_review_queue_ready") is True, "current worktree review queue not ready")
    require(
        isinstance(summary.get("current_worktree_review_queue_high_attention_count"), int)
        and summary.get("current_worktree_review_queue_high_attention_count") > 0,
        "current worktree review queue high-attention count missing",
    )
    require(summary.get("current_status_cli_ready") is True, "current status CLI not ready")
    require(summary.get("state_snapshot_ready") is True, "state snapshot not ready")
    require(summary.get("current_report_hash_cycle_guard_ready") is True, "hash-cycle guard not ready")
    require(summary.get("current_report_hash_cycle_guard_failure_count") == 0, "hash-cycle guard has failures")
    require(summary.get("latest_passing_full_current_scope_log_passed") is True, "latest full log not passing")
    require(data.get("operator_command") == "bash tools/run_current_scope_release_refresh.sh", "unexpected operator command")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current-Scope Release Refresh Entrypoint",
        "",
        f"- Status: `{report['status']}`",
        f"- Entrypoint ready: `{summary['current_scope_release_refresh_entrypoint_ready']}`",
        f"- Wrapper: `{summary['wrapper_path']}`",
        f"- Operator command: `{report['operator_command']}`",
        f"- Latest passing full current-scope log: `{summary['latest_passing_full_current_scope_log']}`",
        f"- Delivery package ready: `{summary['delivery_package_ready']}`",
        f"- Final handoff note ready: `{summary['final_handoff_note_ready']}`",
        f"- Operator quickstart smoke ready: `{summary['operator_quickstart_smoke_ready']}`",
        f"- Current phase closure certificate ready: `{summary['current_phase_closure_certificate_ready']}`",
        f"- Strict closeout action pack ready: `{summary['strict_master_plan_closeout_action_pack_ready']}`",
        f"- Strict closeout action pack missing items: `{summary['strict_master_plan_closeout_action_pack_missing_count']}`",
        f"- Current phase final delivery index ready: `{summary['current_phase_final_delivery_index_ready']}`",
        f"- Current operator command inventory ready: `{summary['current_operator_command_inventory_ready']}`",
        f"- Current operator command inventory commands: `{summary['current_operator_command_inventory_command_count']}`",
        f"- Current operator command inventory required snippets: `{summary['current_operator_command_inventory_required_snippet_count']}`",
        f"- Current operator command inventory missing required snippets: `{summary['current_operator_command_inventory_missing_required_snippet_count']}`",
        f"- Current operator command inventory missing tools: `{summary['current_operator_command_inventory_missing_tool_count']}`",
        f"- Current operator command inventory syntax failures: `{summary['current_operator_command_inventory_syntax_failure_count']}`",
        f"- Current worktree hygiene ready: `{summary['current_worktree_hygiene_ready']}`",
        f"- Current worktree dirty entries: `{summary['current_worktree_dirty_entry_count']}`",
        f"- SUNDIALS local link audit ready: `{summary['sundials_local_link_audit_ready']}`",
        f"- SUNDIALS local link drift present: `{summary['sundials_local_link_drift_present']}`",
        f"- SUNDIALS safe to auto-restore: `{summary['sundials_local_link_safe_to_auto_restore']}`",
        f"- Current worktree review queue ready: `{summary['current_worktree_review_queue_ready']}`",
        f"- Current worktree review queue high-attention entries: `{summary['current_worktree_review_queue_high_attention_count']}`",
        f"- Current status CLI ready: `{summary['current_status_cli_ready']}`",
        f"- State snapshot ready: `{summary['state_snapshot_ready']}`",
        f"- Report hash-cycle guard ready: `{summary['current_report_hash_cycle_guard_ready']}`",
        f"- Report hash-cycle guard failures: `{summary['current_report_hash_cycle_guard_failure_count']}`",
    ]
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
        print(f"current_scope_release_refresh_entrypoint VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_scope_release_refresh_entrypoint PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
