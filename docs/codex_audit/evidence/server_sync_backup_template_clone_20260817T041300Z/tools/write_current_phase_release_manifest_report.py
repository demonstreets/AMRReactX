#!/usr/bin/env python3
"""Write/verify a hash manifest for the current closeable project phase."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-PHASE-RELEASE-MANIFEST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_phase_release_manifest_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_phase_release_manifest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_phase_release_manifest_report.md"

HASHED_ARTIFACTS = [
    ("readme", Path("README.md")),
    ("operator_runbook", Path("docs/codex_audit/current_scope_operator_runbook.md")),
    ("current_scope_verify_script", Path("tools/codex_verify_current_scope.sh")),
    ("release_refresh_wrapper", Path("tools/run_current_scope_release_refresh.sh")),
    ("current_status_cli", Path("tools/codex_print_current_status.py")),
    ("project_closeout_forecast_writer", Path("tools/write_project_closeout_forecast_report.py")),
    ("project_closeout_acceptance_gate_writer", Path("tools/write_project_closeout_acceptance_gate_report.py")),
    ("current_scope_delivery_package_writer", Path("tools/write_current_scope_delivery_package_report.py")),
    ("current_scope_final_handoff_note_writer", Path("tools/write_current_scope_final_handoff_note_report.py")),
    ("current_operator_quickstart_smoke_writer", Path("tools/write_current_operator_quickstart_smoke_report.py")),
    ("current_phase_closure_certificate_writer", Path("tools/write_current_phase_closure_certificate_report.py")),
    ("current_scope_release_refresh_entrypoint_writer", Path("tools/write_current_scope_release_refresh_entrypoint_report.py")),
    ("current_phase_final_delivery_index_writer", Path("tools/write_current_phase_final_delivery_index_report.py")),
    ("current_phase_final_delivery_index_verifier", Path("tools/verify_current_phase_final_delivery_index.sh")),
    ("strict_master_plan_completion_gate_writer", Path("tools/write_strict_master_plan_completion_gate_report.py")),
    ("strict_external_artifact_drop_index_writer", Path("tools/write_strict_external_artifact_drop_index_report.py")),
    ("strict_external_artifact_drop_checklist_writer", Path("tools/write_strict_external_artifact_drop_checklist_report.py")),
    ("strict_external_evidence_receiving_pack_writer", Path("tools/write_strict_external_evidence_receiving_pack_report.py")),
    ("strict_external_evidence_receiving_pack_verifier", Path("tools/verify_strict_external_evidence_receiving_pack.sh")),
    ("strict_master_plan_closeout_action_pack_writer", Path("tools/write_strict_master_plan_closeout_action_pack_report.py")),
    ("strict_master_plan_closeout_action_pack_verifier", Path("tools/verify_strict_master_plan_closeout_action_pack.sh")),
    ("project_closeout_forecast_report", Path("docs/codex_audit/evidence/project_closeout_forecast_20260812/project_closeout_forecast_report.json")),
    ("project_closeout_acceptance_gate_report", Path("docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/project_closeout_acceptance_gate_report.json")),
    ("current_scope_delivery_package_report", Path("docs/codex_audit/evidence/current_scope_delivery_package_20260812/current_scope_delivery_package_report.json")),
    ("current_scope_final_handoff_note_report", Path("docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/current_scope_final_handoff_note_report.json")),
    ("current_operator_quickstart_smoke_report", Path("docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/current_operator_quickstart_smoke_report.json")),
    ("current_phase_closure_certificate_report", Path("docs/codex_audit/evidence/current_phase_closure_certificate_20260812/current_phase_closure_certificate_report.json")),
    ("current_scope_release_refresh_entrypoint_report", Path("docs/codex_audit/evidence/current_scope_release_refresh_entrypoint_20260812/current_scope_release_refresh_entrypoint_report.json")),
    ("current_phase_final_delivery_index_report", Path("docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/current_phase_final_delivery_index_report.json")),
    ("current_worktree_hygiene_report", Path("docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json")),
    ("strict_master_plan_completion_gate_report", Path("docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/strict_master_plan_completion_gate_report.json")),
    ("strict_external_artifact_drop_index_report", Path("docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/strict_external_artifact_drop_index_report.json")),
    ("strict_external_artifact_drop_checklist_report", Path("docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/strict_external_artifact_drop_checklist_report.json")),
    ("strict_external_evidence_receiving_pack_report", Path("docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/strict_external_evidence_receiving_pack_report.json")),
    ("strict_master_plan_closeout_action_pack_report", Path("docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.json")),
]

FULL_LOG_DIR = Path("docs/codex_audit/evidence/current_scope_last_run_20260807")
FULL_LOG_GLOB = "current_scope_verify_after_*.log"


class ReleaseManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseManifestError(message)


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
        raise ReleaseManifestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseManifestError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def artifact_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing release artifact: {path}")
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
    raise ReleaseManifestError("no passing full current-scope log found")


def build_report() -> dict[str, Any]:
    closure = load_json(
        Path("docs/codex_audit/evidence/current_phase_closure_certificate_20260812/current_phase_closure_certificate_report.json")
    )
    acceptance = load_json(
        Path("docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/project_closeout_acceptance_gate_report.json")
    )
    hygiene = load_json(
        Path("docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json")
    )
    latest_log = latest_passing_full_log()
    artifacts = [artifact_entry(label, path) for label, path in HASHED_ARTIFACTS]
    artifacts.append(artifact_entry("latest_full_current_scope_log", latest_log))

    closure_summary = closure["summary"]
    acceptance_summary = acceptance["summary"]
    ready = all(
        [
            closure.get("status") == "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE",
            closure_summary.get("current_phase_closure_certificate_ready") is True,
            closure_summary.get("last_full_current_scope_log") == str(latest_log),
            acceptance.get("status") == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
            acceptance_summary.get("current_phase_acceptance_allowed") is True,
            acceptance_summary.get("strict_final_acceptance_allowed") is False,
            hygiene.get("status") == "AUDITED-CURRENT-WORKTREE-HYGIENE",
            hygiene.get("summary", {}).get("worktree_hygiene_audited") is True,
            len(artifacts) == len(HASHED_ARTIFACTS) + 1,
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "hash manifest for the current closeable phase artifacts",
        "summary": {
            "current_phase_release_manifest_ready": ready,
            "hashed_artifact_count": len(artifacts),
            "latest_full_current_scope_log": str(latest_log),
            "latest_full_current_scope_log_passed": full_log_passed(latest_log),
            "current_phase_closeable": closure_summary.get("current_phase_closeable"),
            "strict_master_plan_closure_allowed": closure_summary.get("strict_master_plan_closure_allowed"),
            "strict_external_artifact_done_count": closure_summary.get("strict_external_artifact_done_count"),
            "strict_external_artifact_missing_count": closure_summary.get("strict_external_artifact_missing_count"),
            "worktree_hygiene_status": hygiene.get("status"),
            "worktree_hygiene_audited": hygiene.get("summary", {}).get("worktree_hygiene_audited"),
            "worktree_dirty_entry_count": hygiene.get("summary", {}).get("dirty_entry_count"),
            "worktree_generated_or_case_output_entry_count": hygiene.get("summary", {}).get(
                "generated_or_case_output_entry_count"
            ),
        },
        "hashed_artifacts": artifacts,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_phase_release_manifest_ready") is True, "release manifest is not ready")
    require(summary.get("hashed_artifact_count") == len(HASHED_ARTIFACTS) + 1, "unexpected artifact count")
    require(summary.get("latest_full_current_scope_log_passed") is True, "latest full current-scope log not passing")
    require(summary.get("current_phase_closeable") is True, "current phase is not closeable")
    require(summary.get("strict_master_plan_closure_allowed") is False, "strict master-plan closure overclaimed")
    require(summary.get("worktree_hygiene_status") == "AUDITED-CURRENT-WORKTREE-HYGIENE", "worktree hygiene not audited")
    require(summary.get("worktree_hygiene_audited") is True, "worktree hygiene audited flag missing")
    done = summary.get("strict_external_artifact_done_count")
    missing = summary.get("strict_external_artifact_missing_count")
    require(isinstance(done, int) and isinstance(missing, int), "strict artifact counts are not integers")
    require(0 <= done <= 14 and 0 <= missing <= 14, "strict artifact counts are outside range")
    require(done + missing == 14, "strict artifact counts do not sum to 14")
    artifacts = data.get("hashed_artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == len(HASHED_ARTIFACTS) + 1, "invalid artifact list")
    if verify_hashes:
        labels = set()
        for entry in artifacts:
            require(isinstance(entry, dict), "invalid artifact entry")
            labels.add(entry.get("label"))
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing release artifact: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch: {path}")
        require(len(labels) == len(artifacts), "duplicate artifact labels")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Phase Release Manifest",
        "",
        f"- Status: `{report['status']}`",
        f"- Manifest ready: `{summary['current_phase_release_manifest_ready']}`",
        f"- Hashed artifacts: `{summary['hashed_artifact_count']}`",
        f"- Latest full current-scope log: `{summary['latest_full_current_scope_log']}`",
        f"- Current phase closeable: `{summary['current_phase_closeable']}`",
        f"- Strict master-plan closure allowed: `{summary['strict_master_plan_closure_allowed']}`",
        f"- Worktree hygiene: `{summary['worktree_hygiene_status']}`",
        f"- Worktree dirty entries: `{summary['worktree_dirty_entry_count']}`",
        "",
        "## Hashed Artifacts",
        "",
    ]
    for entry in report["hashed_artifacts"]:
        lines.append(f"- `{entry['label']}` `{entry['sha256']}` `{entry['path']}`")
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
        print(f"current_phase_release_manifest VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_phase_release_manifest PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
