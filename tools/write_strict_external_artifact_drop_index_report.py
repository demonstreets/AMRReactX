#!/usr/bin/env python3
"""Write an operator-facing index for strict external artifact drops."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_artifact_drop_index_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_artifact_drop_index_report.md"

INTAKE_MANIFEST = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/"
    "master_plan_strict_artifact_intake_manifest_report.json"
)
DROP_CONTRACT = Path(
    "docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/"
    "strict_artifact_drop_contract_preflight_report.json"
)
TEMPLATE_LINT = Path(
    "docs/codex_audit/evidence/strict_artifact_template_lint_20260803/"
    "strict_artifact_template_lint_report.json"
)
COMPLETION_GATE = Path(
    "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
    "strict_master_plan_completion_gate_report.json"
)

EXPECTED_DOMAINS = {"external_plume", "real_cad", "fire_calibration"}
EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}

CONTRACT_TO_TEMPLATE_LABEL = {
    "external_plume.dataset_metadata": "external_plume_metadata",
    "external_plume.sensor_coordinates": "external_plume_sensor_coordinates",
    "external_plume.baffle_geometry": "external_plume_baffle_geometry",
    "external_plume.experimental_timeseries": "external_plume_experimental_timeseries",
    "external_plume.digitization_uncertainty_record": "external_plume_digitization_uncertainty",
    "real_cad.real_cad_cleanup_manifest": "real_cad_cleanup_manifest",
    "real_cad.real_cad_data_room_index": "real_cad_data_room_index",
    "real_cad.real_cad_cleanup_quality_record": "real_cad_cleanup_quality_record",
    "real_cad.real_cad_boundary_tags": "real_cad_boundary_tags",
    "fire_calibration.calibration_metadata": "fire_calibration_metadata",
    "fire_calibration.radiation_metrics": "fire_calibration_radiation_metrics",
    "fire_calibration.overpressure_metrics": "fire_calibration_overpressure_metrics",
    "fire_calibration.fire_calibration_source_registry": "fire_calibration_source_registry",
    "fire_calibration.fire_calibration_digitization_uncertainty": (
        "fire_calibration_digitization_uncertainty"
    ),
}


class DropIndexError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DropIndexError(message)


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
        raise DropIndexError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DropIndexError(f"invalid JSON evidence {path}: {exc}") from exc
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


def template_by_label(template_lint: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for entry in template_lint.get("templates", []):
        if isinstance(entry, dict) and isinstance(entry.get("label"), str):
            out[entry["label"]] = entry
    return out


def build_report() -> dict[str, Any]:
    intake = load_json(INTAKE_MANIFEST)
    contract = load_json(DROP_CONTRACT)
    lint = load_json(TEMPLATE_LINT)
    gate = load_json(COMPLETION_GATE)

    intake_summary = intake["summary"]
    contract_summary = contract["summary"]
    lint_summary = lint["summary"]
    gate_summary = gate["summary"]

    templates = template_by_label(lint)
    checks_by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for check in contract.get("checks", []):
        require(isinstance(check, dict), "invalid contract check entry")
        domain = check.get("domain")
        require(domain in EXPECTED_DOMAINS, f"unexpected contract domain: {domain}")
        label = str(check.get("label", ""))
        template_label = CONTRACT_TO_TEMPLATE_LABEL.get(label, label.replace(".", "_"))
        template = templates.get(template_label)
        required = check.get("required") is not False
        checks_by_domain[domain].append(
            {
                "label": label,
                "target_path": check.get("path"),
                "kind": check.get("kind"),
                "required": required,
                "currently_present": check.get("present") is True,
                "template_path": template.get("path") if template else None,
                "json_required_keys": template.get("actual_keys") if template and template.get("kind") == "json" else None,
                "csv_header": template.get("expected_header") if template and template.get("kind") == "csv" else None,
            }
        )

    domain_entries = []
    for domain in sorted(EXPECTED_DOMAINS):
        checks = sorted(checks_by_domain[domain], key=lambda item: str(item["label"]))
        required_checks = [check for check in checks if check["required"]]
        present_checks = [check for check in checks if check["currently_present"]]
        domain_entries.append(
            {
                "domain": domain,
                "required_artifact_count": len(checks),
                "required_flagged_artifact_count": len(required_checks),
                "currently_present_artifact_count": len(present_checks),
                "ready_for_user_drop": bool(required_checks),
                "checks": checks,
            }
        )

    open_blockers = set(gate_summary.get("open_strict_blockers", []))
    ready = (
        intake.get("status") == "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST"
        and intake_summary.get("artifact_intake_ready") is True
        and contract.get("status") == "PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT"
        and contract_summary.get("strict_artifact_drop_contract_preflight_ready") is True
        and lint.get("status") == "PASS-STRICT-ARTIFACT-TEMPLATE-LINT"
        and lint_summary.get("strict_artifact_template_lint_ready") is True
        and gate.get("status") == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS"
        and gate_summary.get("strict_master_plan_completion_gate_ready") is True
        and set(checks_by_domain) == EXPECTED_DOMAINS
        and open_blockers == EXPECTED_STRICT_BLOCKERS
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "operator index for strict external artifact drop paths, templates, and blockers",
        "summary": {
            "strict_external_artifact_drop_index_ready": ready,
            "domain_count": len(domain_entries),
            "template_count": lint_summary.get("template_count"),
            "contract_check_count": contract_summary.get("contract_check_count"),
            "awaiting_missing_artifact_count": contract_summary.get("awaiting_missing_artifact_count"),
            "present_contract_artifact_count": contract_summary.get("present_contract_artifact_count"),
            "strict_completion_gate_status": gate.get("status"),
            "strict_completion_allowed": gate_summary.get("strict_master_plan_completion_allowed"),
            "open_strict_blocker_count": len(open_blockers),
            "open_strict_blockers": sorted(open_blockers),
            "domains": sorted(EXPECTED_DOMAINS),
        },
        "domain_drop_index": domain_entries,
        "operator_next_steps": [
            "Copy each *_template file to the matching non-template target path listed in domain_drop_index.",
            "Fill JSON required keys and CSV headers without renaming columns.",
            "Run bash tools/verify_strict_artifact_drop_contract_preflight.sh before asking for strict closeout.",
            "Then run bash tools/run_current_scope_release_refresh.sh to rebuild all closure evidence.",
        ],
        "evidence_files": [
            evidence_entry("strict_artifact_intake_manifest", INTAKE_MANIFEST),
            evidence_entry("strict_artifact_drop_contract_preflight", DROP_CONTRACT),
            evidence_entry("strict_artifact_template_lint", TEMPLATE_LINT),
            evidence_entry("strict_master_plan_completion_gate", COMPLETION_GATE),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_external_artifact_drop_index_ready") is True, "drop index is not ready")
    require(summary.get("domain_count") == 3, "unexpected domain count")
    require(summary.get("template_count") == 16, "unexpected template count")
    require(summary.get("contract_check_count") == 14, "unexpected contract check count")
    missing_count = summary.get("awaiting_missing_artifact_count")
    present_count = summary.get("present_contract_artifact_count")
    require(isinstance(missing_count, int), "missing artifact count is not an integer")
    require(isinstance(present_count, int), "present artifact count is not an integer")
    require(0 <= missing_count <= 14, "missing artifact count is outside the contract range")
    require(0 <= present_count <= 14, "present artifact count is outside the contract range")
    require(missing_count + present_count == 14, "present and missing artifact counts do not match contract total")
    require(summary.get("strict_completion_allowed") is False, "strict completion should not be allowed yet")
    require(set(summary.get("open_strict_blockers", [])) == EXPECTED_STRICT_BLOCKERS, "unexpected blocker set")
    domains = data.get("domain_drop_index")
    require(isinstance(domains, list) and len(domains) == 3, "invalid domain index")
    for domain in domains:
        require(domain.get("domain") in EXPECTED_DOMAINS, "invalid domain entry")
        require(domain.get("required_artifact_count", 0) > 0, "domain has no required artifacts")
        for check in domain.get("checks", []):
            require(check.get("target_path"), "missing target path")
            require(check.get("template_path"), "missing template path")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Drop Index",
        "",
        f"- Status: `{report['status']}`",
        f"- Domains: `{summary['domain_count']}`",
        f"- Templates: `{summary['template_count']}`",
        f"- Required contract artifacts: `{summary['contract_check_count']}`",
        f"- Awaiting missing artifacts: `{summary['awaiting_missing_artifact_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
        "## Operator Next Steps",
        "",
    ]
    for step in report["operator_next_steps"]:
        lines.append(f"- {step}")
    for domain in report["domain_drop_index"]:
        lines.extend(["", f"## {domain['domain']}", ""])
        for check in domain["checks"]:
            lines.append(f"- `{check['label']}`")
            lines.append(f"  target: `{check['target_path']}`")
            lines.append(f"  template: `{check['template_path']}`")
            if check.get("csv_header"):
                lines.append(f"  csv_header: `{','.join(check['csv_header'])}`")
            if check.get("json_required_keys"):
                lines.append(f"  json_keys: `{','.join(check['json_required_keys'])}`")
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
        print(f"strict_external_artifact_drop_index VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_artifact_drop_index PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
