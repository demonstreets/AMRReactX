#!/usr/bin/env python3
"""Write/verify a lightweight operator quickstart smoke report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-OPERATOR-QUICKSTART-SMOKE"
STATUS_NOT_READY = "NOT_READY-CURRENT-OPERATOR-QUICKSTART-SMOKE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_operator_quickstart_smoke_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_operator_quickstart_smoke_report.md"

ACCEPTANCE_GATE = Path(
    "docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/"
    "project_closeout_acceptance_gate_report.json"
)
FINAL_HANDOFF = Path(
    "docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/"
    "current_scope_final_handoff_note_report.json"
)
CURRENT_STATUS = Path("docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json")

TEXT_SNIPPETS = [
    "my-pele current evidence-backed status",
    "project closeout acceptance gate: PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
    "current phase acceptance allowed: yes",
    "strict final acceptance allowed: no",
    "strict external artifacts done/missing:",
    "current-scope final handoff note: PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
]


class QuickstartSmokeError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise QuickstartSmokeError(message)


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
        raise QuickstartSmokeError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise QuickstartSmokeError(f"invalid JSON evidence {path}: {exc}") from exc
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


def run_command(argv: list[str]) -> dict[str, Any]:
    proc = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_head": proc.stdout[:4000],
        "stderr_head": proc.stderr[:4000],
    }


def json_counts_ok(data: dict[str, Any]) -> bool:
    done = data.get("project_closeout_strict_external_artifact_done_count")
    missing = data.get("project_closeout_strict_external_artifact_missing_count")
    if not isinstance(done, int) or not isinstance(missing, int):
        return False
    return 0 <= done <= 14 and 0 <= missing <= 14 and done + missing == 14


def drop_counts_ok(data: dict[str, Any]) -> bool:
    required = data.get("required_file_count")
    present = data.get("present_file_count")
    missing = data.get("missing_file_count")
    if not all(isinstance(value, int) for value in [required, present, missing]):
        return False
    return required == 14 and 0 <= present <= 14 and 0 <= missing <= 14 and present + missing == 14


def build_report() -> dict[str, Any]:
    acceptance = load_json(ACCEPTANCE_GATE)
    final_handoff = load_json(FINAL_HANDOFF)

    status_text = run_command(["python3", "tools/codex_print_current_status.py"])
    status_json = run_command(["python3", "tools/codex_print_current_status.py", "--json"])
    drop_text = run_command(["python3", "tools/codex_print_strict_external_artifact_drop_index.py"])
    drop_json = run_command(["python3", "tools/codex_print_strict_external_artifact_drop_index.py", "--json"])

    parsed_status = json.loads(status_json["stdout"]) if status_json["returncode"] == 0 else {}
    parsed_drop = json.loads(drop_json["stdout"]) if drop_json["returncode"] == 0 else {}
    missing_text_snippets = [snippet for snippet in TEXT_SNIPPETS if snippet not in status_text["stdout"]]
    ready = all(
        [
            acceptance.get("status") == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
            final_handoff.get("status") == "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
            status_text["returncode"] == 0,
            status_json["returncode"] == 0,
            drop_text["returncode"] == 0,
            drop_json["returncode"] == 0,
            not missing_text_snippets,
            parsed_status.get("project_closeout_acceptance_gate_status")
            == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
            parsed_status.get("project_closeout_acceptance_gate_ready") is True,
            parsed_status.get("project_closeout_current_phase_acceptance_allowed") is True,
            parsed_status.get("project_closeout_strict_final_acceptance_allowed") is False,
            json_counts_ok(parsed_status),
            drop_counts_ok(parsed_drop),
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "current_operator_quickstart_smoke_ready": ready,
            "status_text_returncode": status_text["returncode"],
            "status_json_returncode": status_json["returncode"],
            "drop_text_returncode": drop_text["returncode"],
            "drop_json_returncode": drop_json["returncode"],
            "missing_text_snippet_count": len(missing_text_snippets),
            "project_closeout_acceptance_gate_status": parsed_status.get(
                "project_closeout_acceptance_gate_status"
            ),
            "project_closeout_acceptance_gate_ready": parsed_status.get(
                "project_closeout_acceptance_gate_ready"
            ),
            "current_phase_acceptance_allowed": parsed_status.get(
                "project_closeout_current_phase_acceptance_allowed"
            ),
            "strict_final_acceptance_allowed": parsed_status.get(
                "project_closeout_strict_final_acceptance_allowed"
            ),
            "strict_external_artifact_done_count": parsed_status.get(
                "project_closeout_strict_external_artifact_done_count"
            ),
            "strict_external_artifact_missing_count": parsed_status.get(
                "project_closeout_strict_external_artifact_missing_count"
            ),
            "drop_index_required_file_count": parsed_drop.get("required_file_count"),
            "drop_index_present_file_count": parsed_drop.get("present_file_count"),
            "drop_index_missing_file_count": parsed_drop.get("missing_file_count"),
        },
        "command_runs": {
            "status_text": status_text,
            "status_json": status_json,
            "drop_text": drop_text,
            "drop_json": drop_json,
        },
        "missing_text_snippets": missing_text_snippets,
        "evidence_files": [
            evidence_entry("project_closeout_acceptance_gate", ACCEPTANCE_GATE),
            evidence_entry("current_scope_final_handoff_note", FINAL_HANDOFF),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_operator_quickstart_smoke_ready") is True, "quickstart smoke is not ready")
    require(summary.get("status_text_returncode") == 0, "status text command failed")
    require(summary.get("status_json_returncode") == 0, "status JSON command failed")
    require(summary.get("drop_text_returncode") == 0, "drop index text command failed")
    require(summary.get("drop_json_returncode") == 0, "drop index JSON command failed")
    require(summary.get("missing_text_snippet_count") == 0, "quickstart text snippets missing")
    require(
        summary.get("project_closeout_acceptance_gate_status") == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
        "acceptance gate status missing from status CLI",
    )
    require(summary.get("project_closeout_acceptance_gate_ready") is True, "acceptance gate readiness missing")
    require(summary.get("current_phase_acceptance_allowed") is True, "current phase acceptance not allowed")
    require(summary.get("strict_final_acceptance_allowed") is False, "strict final acceptance overclaimed")
    done = summary.get("strict_external_artifact_done_count")
    missing = summary.get("strict_external_artifact_missing_count")
    present = summary.get("drop_index_present_file_count")
    awaiting = summary.get("drop_index_missing_file_count")
    required = summary.get("drop_index_required_file_count")
    for label, value in [("done", done), ("missing", missing), ("present", present), ("awaiting", awaiting)]:
        require(isinstance(value, int), f"{label} artifact count is not an integer")
        require(0 <= value <= 14, f"{label} artifact count is outside range")
    require(required == 14, "unexpected drop index required file count")
    require(done + missing == 14, "status CLI done/missing counts do not sum to 14")
    require(present + awaiting == 14, "drop index present/missing counts do not sum to 14")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Operator Quickstart Smoke",
        "",
        f"- Status: `{report['status']}`",
        f"- Quickstart smoke ready: `{summary['current_operator_quickstart_smoke_ready']}`",
        f"- Status CLI text return code: `{summary['status_text_returncode']}`",
        f"- Status CLI JSON return code: `{summary['status_json_returncode']}`",
        f"- Drop index text return code: `{summary['drop_text_returncode']}`",
        f"- Drop index JSON return code: `{summary['drop_json_returncode']}`",
        f"- Current phase acceptance allowed: `{summary['current_phase_acceptance_allowed']}`",
        f"- Strict final acceptance allowed: `{summary['strict_final_acceptance_allowed']}`",
        f"- Strict external artifacts done/missing: `{summary['strict_external_artifact_done_count']}/{summary['strict_external_artifact_missing_count']}`",
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
        print(f"current_operator_quickstart_smoke VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_operator_quickstart_smoke PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
