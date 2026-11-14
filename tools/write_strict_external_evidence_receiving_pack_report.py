#!/usr/bin/env python3
"""Write/verify the strict external evidence receiving pack.

This report is an operator handoff bundle for the remaining strict master-plan
artifacts. It does not mark any external evidence as complete; it proves that
the expected drop targets, templates, validation commands, and blocker mapping
are all available and internally consistent before real data is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_evidence_receiving_pack_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_evidence_receiving_pack_report.md"

DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
DROP_CHECKLIST = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/"
    "strict_external_artifact_drop_checklist_report.json"
)
ACTION_PACK = Path(
    "docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/"
    "strict_master_plan_closeout_action_pack_report.json"
)
COMPLETION_GATE = Path(
    "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
    "strict_master_plan_completion_gate_report.json"
)
UNBLOCK_RUNBOOK = Path("docs/codex_audit/strict_master_plan_unblock_runbook.md")

EXPECTED_COUNTS = {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}
EXPECTED_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class ReceivingPackError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceivingPackError(message)


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
        raise ReceivingPackError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReceivingPackError(f"invalid JSON evidence {path}: {exc}") from exc
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


def checklist_by_label(checklist: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for item in checklist.get("checklist_items", []):
        label = item.get("label")
        require(isinstance(label, str) and label, "checklist item missing label")
        items[label] = item
    return items


def domain_entries(index: dict[str, Any], checklist: dict[str, Any]) -> list[dict[str, Any]]:
    checklist_items = checklist_by_label(checklist)
    entries: list[dict[str, Any]] = []
    for domain in index.get("domain_drop_index", []):
        name = domain.get("domain")
        require(name in EXPECTED_COUNTS, f"unexpected domain: {name}")
        files: list[dict[str, Any]] = []
        for check in domain.get("checks", []):
            label = check.get("label")
            require(label in checklist_items, f"drop-index item missing from checklist: {label}")
            checklist_item = checklist_items[label]
            files.append(
                {
                    "label": label,
                    "kind": check.get("kind"),
                    "target_path": check.get("target_path"),
                    "template_path": check.get("template_path"),
                    "currently_present": check.get("currently_present") is True,
                    "checklist_done": checklist_item.get("done") is True,
                    "csv_header": check.get("csv_header"),
                    "json_required_keys": check.get("json_required_keys"),
                    "preflight": "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
                }
            )
        files = sorted(files, key=lambda item: str(item["label"]))
        entries.append(
            {
                "domain": name,
                "required_file_count": len(files),
                "present_file_count": sum(1 for item in files if item["currently_present"]),
                "missing_file_count": sum(1 for item in files if not item["currently_present"]),
                "files": files,
            }
        )
    return sorted(entries, key=lambda item: str(item["domain"]))


def build_report() -> dict[str, Any]:
    index = load_json(DROP_INDEX)
    checklist = load_json(DROP_CHECKLIST)
    action_pack = load_json(ACTION_PACK)
    completion_gate = load_json(COMPLETION_GATE)

    index_summary = index["summary"]
    checklist_summary = checklist["summary"]
    action_summary = action_pack["summary"]
    gate_summary = completion_gate["summary"]
    domains = domain_entries(index, checklist)

    counts_by_domain = {entry["domain"]: entry["required_file_count"] for entry in domains}
    total_required = sum(entry["required_file_count"] for entry in domains)
    total_present = sum(entry["present_file_count"] for entry in domains)
    total_missing = sum(entry["missing_file_count"] for entry in domains)
    blockers = set(gate_summary.get("open_strict_blockers", []))

    ready = (
        index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX"
        and index_summary.get("strict_external_artifact_drop_index_ready") is True
        and checklist.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST"
        and checklist_summary.get("strict_external_artifact_drop_checklist_ready") is True
        and action_pack.get("status") == "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK"
        and action_summary.get("strict_master_plan_closeout_action_pack_ready") is True
        and completion_gate.get("status") == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS"
        and gate_summary.get("strict_master_plan_completion_gate_ready") is True
        and counts_by_domain == EXPECTED_COUNTS
        and total_required == 14
        and total_present == action_summary.get("done_action_item_count")
        and total_missing == action_summary.get("missing_action_item_count")
        and blockers == EXPECTED_BLOCKERS
        and UNBLOCK_RUNBOOK.is_file()
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "strict external evidence receiving pack for plume, real CAD, and fire calibration artifacts",
        "summary": {
            "strict_external_evidence_receiving_pack_ready": ready,
            "domain_count": len(domains),
            "required_file_count": total_required,
            "present_file_count": total_present,
            "missing_file_count": total_missing,
            "counts_by_domain": counts_by_domain,
            "strict_completion_allowed": gate_summary.get("strict_master_plan_completion_allowed"),
            "strict_master_plan_still_open": action_summary.get("strict_master_plan_still_open"),
            "open_strict_blocker_count": len(blockers),
            "open_strict_blockers": sorted(blockers),
            "drop_index_ready": index_summary.get("strict_external_artifact_drop_index_ready"),
            "drop_checklist_ready": checklist_summary.get("strict_external_artifact_drop_checklist_ready"),
            "action_pack_ready": action_summary.get("strict_master_plan_closeout_action_pack_ready"),
            "completion_gate_ready": gate_summary.get("strict_master_plan_completion_gate_ready"),
        },
        "receiving_domains": domains,
        "operator_commands": {
            "print_drop_index": "python3 tools/codex_print_strict_external_artifact_drop_index.py",
            "print_drop_index_json": "python3 tools/codex_print_strict_external_artifact_drop_index.py --json",
            "preflight_after_copy": "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
            "rebuild_current_scope": "bash tools/run_current_scope_release_refresh.sh",
        },
        "strict_boundary": {
            "does_not_mark_external_artifacts_complete": True,
            "does_not_allow_strict_master_plan_closure": True,
            "real_external_files_still_required": total_missing > 0,
        },
        "evidence_files": [
            evidence_entry("strict_external_artifact_drop_index", DROP_INDEX),
            evidence_entry("strict_external_artifact_drop_checklist", DROP_CHECKLIST),
            evidence_entry("strict_master_plan_closeout_action_pack", ACTION_PACK),
            evidence_entry("strict_master_plan_completion_gate", COMPLETION_GATE),
            evidence_entry("strict_master_plan_unblock_runbook", UNBLOCK_RUNBOOK),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_external_evidence_receiving_pack_ready") is True, "receiving pack is not ready")
    require(summary.get("domain_count") == 3, "unexpected domain count")
    require(summary.get("required_file_count") == 14, "unexpected required file count")
    require(summary.get("counts_by_domain") == EXPECTED_COUNTS, "unexpected per-domain counts")
    present = summary.get("present_file_count")
    missing = summary.get("missing_file_count")
    require(isinstance(present, int) and isinstance(missing, int), "present/missing counts must be integers")
    require(present + missing == 14, "present/missing counts do not add to 14")
    require(summary.get("strict_completion_allowed") is False, "strict completion unexpectedly allowed")
    require(summary.get("strict_master_plan_still_open") is True, "strict master plan should still be open")
    require(set(summary.get("open_strict_blockers", [])) == EXPECTED_BLOCKERS, "unexpected strict blockers")
    boundary = data.get("strict_boundary")
    require(isinstance(boundary, dict), "missing strict boundary")
    require(boundary.get("does_not_mark_external_artifacts_complete") is True, "receiving pack overclaims artifacts")
    require(boundary.get("does_not_allow_strict_master_plan_closure") is True, "receiving pack overclaims closure")
    domains = data.get("receiving_domains")
    require(isinstance(domains, list) and len(domains) == 3, "invalid receiving domains")
    for domain in domains:
        require(domain.get("domain") in EXPECTED_COUNTS, "unexpected receiving domain")
        require(domain.get("required_file_count") == EXPECTED_COUNTS[domain["domain"]], "bad domain file count")
        files = domain.get("files")
        require(isinstance(files, list) and len(files) == domain.get("required_file_count"), "invalid domain files")
        for item in files:
            require(item.get("target_path"), "missing target path")
            require(item.get("template_path"), "missing template path")
            require(item.get("preflight") == "bash tools/verify_strict_artifact_drop_contract_preflight.sh", "bad preflight")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Evidence Receiving Pack",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['strict_external_evidence_receiving_pack_ready']}`",
        f"- Required files: `{summary['required_file_count']}`",
        f"- Present files: `{summary['present_file_count']}`",
        f"- Missing files: `{summary['missing_file_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
        "## Commands",
        "",
        "```bash",
        report["operator_commands"]["print_drop_index"],
        report["operator_commands"]["print_drop_index_json"],
        report["operator_commands"]["preflight_after_copy"],
        report["operator_commands"]["rebuild_current_scope"],
        "```",
        "",
        "## Receiving Domains",
        "",
    ]
    for domain in report["receiving_domains"]:
        lines.extend(
            [
                f"### {domain['domain']}",
                "",
                f"- Required: `{domain['required_file_count']}`",
                f"- Present: `{domain['present_file_count']}`",
                f"- Missing: `{domain['missing_file_count']}`",
                "",
            ]
        )
        for item in domain["files"]:
            lines.append(f"- `{item['label']}`")
            lines.append(f"  target: `{item['target_path']}`")
            lines.append(f"  template: `{item['template_path']}`")
    lines.extend(
        [
            "",
            "## Strict Boundary",
            "",
            "- This receiving pack does not mark external artifacts complete.",
            "- This receiving pack does not allow strict master-plan closure.",
            "- Real external files are still required before strict closeout.",
        ]
    )
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
        print(f"strict_external_evidence_receiving_pack VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_evidence_receiving_pack PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
