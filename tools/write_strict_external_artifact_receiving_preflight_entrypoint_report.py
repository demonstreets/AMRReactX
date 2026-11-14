#!/usr/bin/env python3
"""Write/verify the strict external artifact receiving preflight entrypoint report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-RECEIVING-PREFLIGHT-ENTRYPOINT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_artifact_receiving_preflight_entrypoint_20260820")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_artifact_receiving_preflight_entrypoint_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_artifact_receiving_preflight_entrypoint_report.md"

WRAPPER = Path("tools/run_strict_external_artifact_receiving_preflight.sh")
DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
DROP_CHECKLIST = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/"
    "strict_external_artifact_drop_checklist_report.json"
)
RECEIVING_PACK = Path(
    "docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/"
    "strict_external_evidence_receiving_pack_report.json"
)
CN_HANDOFF = Path(
    "docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/"
    "strict_external_artifact_cn_handoff_report.json"
)
CLOSEOUT_ACTION_PACK = Path(
    "docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/"
    "strict_master_plan_closeout_action_pack_report.json"
)
STATUS_CLI = Path(
    "docs/codex_audit/evidence/current_status_cli_20260803/"
    "current_status_cli_report.json"
)
H2_FIRE_RESIDUAL_BUDGET = Path(
    "docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/"
    "h2_fire_calibration_residual_budget_report.json"
)
PREFLIGHT_LOG_DIR = Path("docs/codex_audit/evidence/strict_external_artifact_receiving_preflight_20260820")
PREFLIGHT_LOG_GLOB = "strict_external_artifact_receiving_preflight_*.log"

REQUIRED_WRAPPER_SNIPPETS = [
    "python3 tools/codex_print_strict_external_artifact_drop_index.py",
    "python3 tools/write_master_plan_strict_artifact_intake_manifest_report.py",
    "bash tools/verify_master_plan_strict_artifact_intake_manifest.sh",
    "python3 tools/write_master_plan_strict_artifact_drop_preflight_report.py",
    "bash tools/verify_master_plan_strict_artifact_drop_preflight.sh",
    "python3 tools/write_strict_artifact_drop_contract_preflight_report.py",
    "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
    "python3 tools/write_strict_external_artifact_drop_index_report.py",
    "bash tools/verify_strict_external_artifact_drop_index.sh",
    "python3 tools/write_strict_external_artifact_drop_checklist_report.py",
    "bash tools/verify_strict_external_artifact_drop_checklist.sh",
    "python3 tools/write_strict_external_evidence_receiving_pack_report.py",
    "bash tools/verify_strict_external_evidence_receiving_pack.sh",
    "python3 tools/write_strict_external_artifact_cn_handoff_report.py",
    "bash tools/verify_strict_external_artifact_cn_handoff.sh",
    "python3 tools/write_strict_master_plan_closeout_action_pack_report.py",
    "bash tools/verify_strict_master_plan_closeout_action_pack.sh",
    "python3 tools/write_current_status_cli_report.py",
    "bash tools/verify_current_status_cli.sh",
    "STRICT_EXTERNAL_ARTIFACT_RECEIVING_PREFLIGHT_RC=$rc",
]


class ReceivingPreflightEntrypointError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceivingPreflightEntrypointError(message)


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
        raise ReceivingPreflightEntrypointError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReceivingPreflightEntrypointError(f"invalid JSON evidence {path}: {exc}") from exc
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
    return (
        "STRICT_EXTERNAL_ARTIFACT_RECEIVING_PREFLIGHT_RC=0" in text
        and "current_status_cli VERIFY-PASS" in text
        and "strict_external_artifact_cn_handoff VERIFY-PASS" in text
    )


def latest_passing_log() -> Path:
    require(PREFLIGHT_LOG_DIR.is_dir(), f"missing preflight log directory: {PREFLIGHT_LOG_DIR}")
    candidates = sorted(PREFLIGHT_LOG_DIR.glob(PREFLIGHT_LOG_GLOB), key=lambda path: path.stat().st_mtime, reverse=True)
    require(candidates, f"no preflight logs match {PREFLIGHT_LOG_DIR / PREFLIGHT_LOG_GLOB}")
    for path in candidates:
        if log_has_success(path):
            return path
    raise ReceivingPreflightEntrypointError(f"no passing preflight log found under {PREFLIGHT_LOG_DIR}")


def build_report() -> dict[str, Any]:
    drop_index = load_json(DROP_INDEX)
    drop_checklist = load_json(DROP_CHECKLIST)
    receiving_pack = load_json(RECEIVING_PACK)
    cn_handoff = load_json(CN_HANDOFF)
    closeout_action_pack = load_json(CLOSEOUT_ACTION_PACK)
    status_cli = load_json(STATUS_CLI)
    fire_residual_budget = load_json(H2_FIRE_RESIDUAL_BUDGET)

    wrapper_syntax_ok, wrapper_syntax_output = bash_syntax_ok(WRAPPER)
    wrapper_missing = missing_snippets(WRAPPER, REQUIRED_WRAPPER_SNIPPETS)
    latest_log = latest_passing_log()

    receiving_summary = receiving_pack["summary"]
    status_summary = status_cli["summary"]
    fire_residual_summary = fire_residual_budget["summary"]
    ready = all(
        [
            WRAPPER.is_file(),
            wrapper_syntax_ok,
            not wrapper_missing,
            drop_index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
            drop_index["summary"].get("strict_external_artifact_drop_index_ready") is True,
            drop_checklist.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST",
            drop_checklist["summary"].get("strict_external_artifact_drop_checklist_ready") is True,
            receiving_pack.get("status") == "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK",
            receiving_summary.get("strict_external_evidence_receiving_pack_ready") is True,
            cn_handoff.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF",
            cn_handoff["summary"].get("strict_external_artifact_cn_handoff_ready") is True,
            closeout_action_pack.get("status") == "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK",
            closeout_action_pack["summary"].get("strict_master_plan_closeout_action_pack_ready") is True,
            status_cli.get("status") == "PASS-CURRENT-STATUS-CLI",
            status_summary.get("current_status_cli_ready") is True,
            fire_residual_budget.get("status") == "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET",
            fire_residual_summary.get("fire_calibration_residual_budget_ready") is True,
            log_has_success(latest_log),
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "summary": {
            "strict_external_artifact_receiving_preflight_entrypoint_ready": ready,
            "wrapper_path": str(WRAPPER),
            "wrapper_bash_syntax_ok": wrapper_syntax_ok,
            "wrapper_missing_snippet_count": len(wrapper_missing),
            "latest_passing_preflight_log": str(latest_log),
            "latest_passing_preflight_log_passed": log_has_success(latest_log),
            "required_file_count": receiving_summary.get("required_file_count"),
            "present_file_count": receiving_summary.get("present_file_count"),
            "missing_file_count": receiving_summary.get("missing_file_count"),
            "open_strict_blocker_count": receiving_summary.get("open_strict_blocker_count"),
            "open_strict_blockers": receiving_summary.get("open_strict_blockers"),
            "strict_completion_allowed": receiving_summary.get("strict_completion_allowed"),
            "external_artifact_file_presence_is_not_strict_completion": True,
            "fire_calibration_files_present_but_strict_credit_blocked": (
                receiving_summary.get("present_file_count", 0) > 0
                and fire_residual_summary.get("production_fire_calibration_claim_allowed") is False
            ),
            "fire_residual_budget_ready": fire_residual_summary.get("fire_calibration_residual_budget_ready"),
            "fire_residual_budget_clears_strict_blocker": fire_residual_summary.get(
                "residual_budget_clears_strict_blocker"
            ),
            "fire_production_calibration_claim_allowed": fire_residual_summary.get(
                "production_fire_calibration_claim_allowed"
            ),
            "fire_pressure_agreement_ready": fire_residual_summary.get("pressure_agreement_ready"),
            "fire_radiation_agreement_ready": fire_residual_summary.get("radiation_agreement_ready"),
            "fire_pressure_missing_artifact_count": fire_residual_summary.get("pressure_missing_artifact_count"),
            "fire_radiation_missing_artifact_count": fire_residual_summary.get("radiation_missing_artifact_count"),
            "current_status_cli_ready": status_summary.get("current_status_cli_ready"),
            "goal_complete": status_summary.get("goal_complete"),
        },
        "operator_commands": [
            "bash tools/run_strict_external_artifact_receiving_preflight.sh",
            "python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py",
            "bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh",
        ],
        "wrapper_checks": {
            "missing_snippets": wrapper_missing,
            "bash_syntax_output": wrapper_syntax_output,
        },
        "evidence_files": [
            evidence_entry("strict_external_artifact_receiving_preflight_wrapper", WRAPPER),
            evidence_entry("strict_external_artifact_drop_index", DROP_INDEX),
            evidence_entry("strict_external_artifact_drop_checklist", DROP_CHECKLIST),
            evidence_entry("strict_external_evidence_receiving_pack", RECEIVING_PACK),
            evidence_entry("strict_external_artifact_cn_handoff", CN_HANDOFF),
            evidence_entry("strict_master_plan_closeout_action_pack", CLOSEOUT_ACTION_PACK),
            evidence_entry("h2_fire_calibration_residual_budget", H2_FIRE_RESIDUAL_BUDGET),
            evidence_entry("latest_passing_preflight_log", latest_log),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(
        summary.get("strict_external_artifact_receiving_preflight_entrypoint_ready") is True,
        "receiving preflight entrypoint is not ready",
    )
    require(summary.get("wrapper_bash_syntax_ok") is True, "wrapper bash syntax is not ok")
    require(summary.get("wrapper_missing_snippet_count") == 0, "wrapper is missing required snippets")
    require(summary.get("latest_passing_preflight_log_passed") is True, "latest preflight log did not pass")
    require(summary.get("required_file_count") == 14, "unexpected required file count")
    present = summary.get("present_file_count")
    missing = summary.get("missing_file_count")
    require(isinstance(present, int) and isinstance(missing, int), "present/missing counts must be integers")
    require(present + missing == 14, "present/missing counts do not add to 14")
    require(summary.get("open_strict_blocker_count") in {0, 1, 2, 3}, "unexpected strict blocker count")
    require(
        summary.get("external_artifact_file_presence_is_not_strict_completion") is True,
        "file-presence distinction is missing",
    )
    require(summary.get("fire_residual_budget_ready") is True, "fire residual budget is not ready")
    require(
        summary.get("fire_production_calibration_claim_allowed") is False,
        "fire production calibration claim unexpectedly allowed by receiving preflight",
    )
    require(
        summary.get("fire_residual_budget_clears_strict_blocker") is False,
        "fire residual budget unexpectedly clears strict blocker",
    )
    require(summary.get("fire_pressure_agreement_ready") is False, "pressure agreement unexpectedly ready")
    require(summary.get("fire_radiation_agreement_ready") is False, "radiation agreement unexpectedly ready")
    require(
        isinstance(summary.get("fire_pressure_missing_artifact_count"), int),
        "missing pressure artifact count is not recorded",
    )
    require(
        isinstance(summary.get("fire_radiation_missing_artifact_count"), int),
        "missing radiation artifact count is not recorded",
    )
    require(summary.get("current_status_cli_ready") is True, "status CLI is not ready")
    commands = data.get("operator_commands")
    require(isinstance(commands, list), "missing operator commands")
    require(
        "bash tools/run_strict_external_artifact_receiving_preflight.sh" in commands,
        "missing receiving preflight command",
    )
    checks = data.get("wrapper_checks")
    require(isinstance(checks, dict), "missing wrapper checks")
    require(checks.get("missing_snippets") == [], "wrapper still has missing snippets")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Receiving Preflight Entrypoint Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['strict_external_artifact_receiving_preflight_entrypoint_ready']}`",
        f"- Wrapper: `{summary['wrapper_path']}`",
        f"- Latest passing log: `{summary['latest_passing_preflight_log']}`",
        f"- Required files: `{summary['required_file_count']}`",
        f"- Present files: `{summary['present_file_count']}`",
        f"- Missing files: `{summary['missing_file_count']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        f"- File presence is strict completion: `{not summary['external_artifact_file_presence_is_not_strict_completion']}`",
        f"- Fire production calibration claim allowed: `{summary['fire_production_calibration_claim_allowed']}`",
        f"- Fire pressure agreement ready: `{summary['fire_pressure_agreement_ready']}`",
        f"- Fire radiation agreement ready: `{summary['fire_radiation_agreement_ready']}`",
        "",
        "## File Presence vs Strict Credit",
        "",
        "The receiving preflight distinguishes filesystem presence from strict production credit. "
        "A file can exist and pass schema checks while the strict blocker remains open if the artifact "
        "does not yet prove case-aligned physics agreement.",
        "",
        "For the fire consequence blocker, current residuals are:",
        "",
        f"- Pressure missing artifact count: `{summary['fire_pressure_missing_artifact_count']}`",
        f"- Radiation missing artifact count: `{summary['fire_radiation_missing_artifact_count']}`",
        f"- Residual budget clears strict blocker: `{summary['fire_residual_budget_clears_strict_blocker']}`",
        "",
        "## Commands",
        "",
        "```bash",
        *report["operator_commands"],
        "```",
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
        validate_report(data)
        print(
            "strict_external_artifact_receiving_preflight_entrypoint VERIFY-PASS "
            f"json={args.verify_json} status={data['status']}"
        )
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
