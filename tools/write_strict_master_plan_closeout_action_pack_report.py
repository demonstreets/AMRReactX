#!/usr/bin/env python3
"""Write/verify a strict master-plan closeout action pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_master_plan_closeout_action_pack_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_master_plan_closeout_action_pack_report.md"

DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
DROP_CHECKLIST = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/"
    "strict_external_artifact_drop_checklist_report.json"
)
COMPLETION_GATE = Path(
    "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
    "strict_master_plan_completion_gate_report.json"
)
CLOSURE_CERTIFICATE = Path(
    "docs/codex_audit/evidence/current_phase_closure_certificate_20260812/"
    "current_phase_closure_certificate_report.json"
)
INTAKE_MANIFEST = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/"
    "master_plan_strict_artifact_intake_manifest_report.json"
)

EXPECTED_DOMAINS = {"external_plume", "real_cad", "fire_calibration"}
EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class CloseoutActionPackError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CloseoutActionPackError(message)


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
        raise CloseoutActionPackError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CloseoutActionPackError(f"invalid JSON evidence {path}: {exc}") from exc
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


def _checklist_entries_by_label(checklist: dict[str, Any]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    stack: list[Any] = [checklist]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            label = item.get("label")
            if isinstance(label, str):
                found[label] = item
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return found


def _action_items(drop_index: dict[str, Any], checklist: dict[str, Any]) -> list[dict[str, Any]]:
    checklist_by_label = _checklist_entries_by_label(checklist)
    items: list[dict[str, Any]] = []
    for domain in drop_index.get("domain_drop_index", []):
        require(isinstance(domain, dict), "invalid drop-index domain entry")
        domain_name = domain.get("domain")
        require(domain_name in EXPECTED_DOMAINS, f"unexpected domain: {domain_name}")
        for check in domain.get("checks", []):
            require(isinstance(check, dict), "invalid drop-index check entry")
            label = str(check.get("label"))
            checklist_entry = checklist_by_label.get(label, {})
            target = str(check.get("target_path") or "")
            template = str(check.get("template_path") or "")
            present = check.get("currently_present") is True
            checklist_status = None
            if checklist_entry:
                checklist_status = "DONE" if checklist_entry.get("done") is True else "MISSING"
            items.append(
                {
                    "domain": domain_name,
                    "label": label,
                    "target_path": target,
                    "template_path": template,
                    "kind": check.get("kind"),
                    "currently_present": present,
                    "status": "DONE" if present else "MISSING",
                    "csv_header": check.get("csv_header"),
                    "json_required_keys": check.get("json_required_keys"),
                    "checklist_entry_status": checklist_status,
                    "operator_action": (
                        "No action needed; the contract artifact is present."
                        if present
                        else "Copy/fill the template into target_path, then rerun the strict artifact preflight."
                    ),
                }
            )
    return sorted(items, key=lambda item: (str(item["domain"]), str(item["label"])))


def build_report() -> dict[str, Any]:
    drop_index = load_json(DROP_INDEX)
    checklist = load_json(DROP_CHECKLIST)
    gate = load_json(COMPLETION_GATE)
    closure = load_json(CLOSURE_CERTIFICATE)
    intake = load_json(INTAKE_MANIFEST)

    drop_summary = drop_index["summary"]
    checklist_summary = checklist["summary"]
    gate_summary = gate["summary"]
    closure_summary = closure["summary"]
    intake_summary = intake["summary"]

    items = _action_items(drop_index, checklist)
    by_domain: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "missing": 0, "done": 0})
    for item in items:
        domain = str(item["domain"])
        by_domain[domain]["total"] += 1
        by_domain[domain]["missing"] += 1 if item["status"] == "MISSING" else 0
        by_domain[domain]["done"] += 1 if item["status"] == "DONE" else 0

    missing_count = sum(1 for item in items if item["status"] == "MISSING")
    done_count = sum(1 for item in items if item["status"] == "DONE")
    open_blockers = set(gate_summary.get("open_strict_blockers", []))

    ready = (
        drop_index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX"
        and drop_summary.get("strict_external_artifact_drop_index_ready") is True
        and checklist.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST"
        and checklist_summary.get("strict_external_artifact_drop_checklist_ready") is True
        and gate.get("status") == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS"
        and gate_summary.get("strict_master_plan_completion_gate_ready") is True
        and gate_summary.get("strict_master_plan_completion_allowed") is False
        and closure.get("status") == "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE"
        and closure_summary.get("current_phase_closeable") is True
        and intake.get("status") == "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST"
        and intake_summary.get("artifact_intake_ready") is True
        and set(by_domain) == EXPECTED_DOMAINS
        and open_blockers == EXPECTED_STRICT_BLOCKERS
        and len(items) == 14
        and missing_count + done_count == 14
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "machine-verifiable closeout action pack for the strict master-plan residual artifacts",
        "summary": {
            "strict_master_plan_closeout_action_pack_ready": ready,
            "current_phase_closeable": closure_summary.get("current_phase_closeable"),
            "strict_master_plan_completion_allowed": gate_summary.get("strict_master_plan_completion_allowed"),
            "strict_master_plan_still_open": gate_summary.get("strict_master_plan_complete") is False,
            "domain_count": len(by_domain),
            "required_action_item_count": len(items),
            "done_action_item_count": done_count,
            "missing_action_item_count": missing_count,
            "open_strict_blocker_count": len(open_blockers),
            "open_strict_blockers": sorted(open_blockers),
            "post_drop_minimum_command_sequence": [
                "python3 tools/write_master_plan_strict_artifact_intake_manifest_report.py",
                "bash tools/verify_master_plan_strict_artifact_intake_manifest.sh",
                "python3 tools/write_strict_artifact_drop_contract_preflight_report.py",
                "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
                "python3 tools/write_strict_external_artifact_drop_checklist_report.py",
                "bash tools/verify_strict_external_artifact_drop_checklist.sh",
                "python3 tools/write_strict_master_plan_completion_gate_report.py",
                "bash tools/verify_strict_master_plan_completion_gate.sh",
                "bash tools/run_current_scope_release_refresh.sh",
            ],
        },
        "domain_summary": dict(sorted(by_domain.items())),
        "action_items": items,
        "evidence_files": [
            evidence_entry("strict_external_artifact_drop_index", DROP_INDEX),
            evidence_entry("strict_external_artifact_drop_checklist", DROP_CHECKLIST),
            evidence_entry("strict_master_plan_completion_gate", COMPLETION_GATE),
            evidence_entry("current_phase_closure_certificate", CLOSURE_CERTIFICATE),
            evidence_entry("master_plan_strict_artifact_intake_manifest", INTAKE_MANIFEST),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_master_plan_closeout_action_pack_ready") is True, "action pack is not ready")
    require(summary.get("current_phase_closeable") is True, "current phase is not closeable")
    require(summary.get("strict_master_plan_completion_allowed") is False, "strict completion should still be blocked")
    require(summary.get("strict_master_plan_still_open") is True, "strict master plan should still be open")
    require(summary.get("domain_count") == 3, "unexpected domain count")
    require(summary.get("required_action_item_count") == 14, "unexpected action item count")
    missing = summary.get("missing_action_item_count")
    done = summary.get("done_action_item_count")
    require(isinstance(missing, int), "missing action count is not an integer")
    require(isinstance(done, int), "done action count is not an integer")
    require(0 <= missing <= 14, "missing action count outside range")
    require(0 <= done <= 14, "done action count outside range")
    require(missing + done == 14, "missing and done action counts do not add to 14")
    require(set(summary.get("open_strict_blockers", [])) == EXPECTED_STRICT_BLOCKERS, "unexpected strict blockers")
    action_items = data.get("action_items")
    require(isinstance(action_items, list) and len(action_items) == 14, "invalid action item list")
    for item in action_items:
        require(item.get("domain") in EXPECTED_DOMAINS, "invalid action item domain")
        require(item.get("target_path"), "missing target path")
        require(item.get("template_path"), "missing template path")
        require(item.get("status") in {"DONE", "MISSING"}, "invalid action item status")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Strict Master-Plan Closeout Action Pack",
        "",
        f"- Status: `{report['status']}`",
        f"- Current phase closeable: `{s['current_phase_closeable']}`",
        f"- Strict master-plan completion allowed: `{s['strict_master_plan_completion_allowed']}`",
        f"- Domains: `{s['domain_count']}`",
        f"- Action items done/missing: `{s['done_action_item_count']}/{s['missing_action_item_count']}`",
        "",
        "## Required Command Sequence After Artifact Drop",
        "",
    ]
    for command in s["post_drop_minimum_command_sequence"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Domain Summary", ""])
    for domain, values in report["domain_summary"].items():
        lines.append(
            f"- `{domain}`: total `{values['total']}`, done `{values['done']}`, missing `{values['missing']}`"
        )
    lines.extend(["", "## Action Items", ""])
    for item in report["action_items"]:
        lines.append(f"- `{item['domain']}.{item['label']}`: `{item['status']}`")
        lines.append(f"  target: `{item['target_path']}`")
        lines.append(f"  template: `{item['template_path']}`")
        if item.get("json_required_keys"):
            lines.append(f"  json_required_keys: `{','.join(item['json_required_keys'])}`")
        if item.get("csv_header"):
            lines.append(f"  csv_header: `{','.join(item['csv_header'])}`")
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
        print(f"strict_master_plan_closeout_action_pack VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_master_plan_closeout_action_pack PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
