#!/usr/bin/env python3
"""Write/verify the engineering H2 external evidence acceptance worksheet."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-EXTERNAL-EVIDENCE-ACCEPTANCE-WORKSHEET'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_evidence_acceptance_worksheet.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_evidence_acceptance_worksheet.md'
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / 'h2_external_evidence_acceptance_worksheet.csv'
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_INTAKE_KIT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724/'
    'h2_external_evidence_intake_kit_manifest.json'
)
DEFAULT_OPERATOR_RECEIPT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_operator_receipt_20260724/'
    'h2_external_artifact_operator_receipt_report.json'
)
DEFAULT_DROP_VALIDATOR = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
    'h2_external_artifact_drop_validator_report.json'
)
DEFAULT_DASHBOARD = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724/'
    'h2_external_evidence_operations_dashboard.json'
)

EXPECTED_DOMAINS = {
    'real_cad_cleanup',
    'external_plume_shape_reference',
    'fire_consequence_calibration',
}
VALIDATION_COMMAND = 'python3 tools/write_engineering_h2_external_artifact_drop_validator.py'
CONTROLLED_COPY_COMMAND = (
    'python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py '
    '--apply --confirm-controlled-copy H2_EXTERNAL_ARTIFACTS_READY'
)
REBUILD_COMMAND = 'bash tools/rebuild_engineering_h2_evidence_chain.sh'


class AcceptanceWorksheetError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceWorksheetError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise AcceptanceWorksheetError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise AcceptanceWorksheetError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def domain_templates(intake_kit: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    kits = intake_kit.get('domain_kits')
    require(isinstance(kits, list), 'intake kit domain_kits missing')
    for kit in kits:
        if not isinstance(kit, dict):
            continue
        domain = str(kit.get('domain', ''))
        templates = kit.get('templates')
        require(isinstance(templates, list), f'{domain} templates missing')
        result[domain] = [
            str(item.get('path'))
            for item in templates
            if isinstance(item, dict) and item.get('present') is True and item.get('path')
        ]
    return result


def drop_validation_index(drop: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    records = drop.get('domain_records')
    require(isinstance(records, list), 'drop validator domain_records missing')
    for record in records:
        if not isinstance(record, dict):
            continue
        domain = str(record.get('domain', ''))
        validations = record.get('artifact_validations')
        require(isinstance(validations, list), f'{domain} artifact_validations missing')
        for item in validations:
            if isinstance(item, dict):
                result[(domain, str(item.get('artifact', '')))] = item
    return result


def artifact_rows(closure: dict[str, Any], intake_kit: dict[str, Any], drop: dict[str, Any]) -> list[dict[str, Any]]:
    template_map = domain_templates(intake_kit)
    validation_map = drop_validation_index(drop)
    records = closure.get('domain_closure_records')
    require(isinstance(records, list), 'closure manifest domain_closure_records missing')
    rows: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        domain = str(record.get('domain', ''))
        require(domain in EXPECTED_DOMAINS, f'unexpected domain: {domain}')
        commands = record.get('domain_command_sequence')
        require(isinstance(commands, list) and commands, f'{domain} command sequence missing')
        artifacts = record.get('artifact_records')
        require(isinstance(artifacts, list), f'{domain} artifact_records missing')
        for artifact_record in artifacts:
            if not isinstance(artifact_record, dict):
                continue
            artifact = str(artifact_record.get('artifact', ''))
            validation = validation_map.get((domain, artifact), {})
            drop_validation = validation.get('drop_validation', {}) if isinstance(validation, dict) else {}
            gaps = drop_validation.get('gaps', []) if isinstance(drop_validation, dict) else []
            rows.append(
                {
                    'domain': domain,
                    'blocker': record.get('blocker'),
                    'artifact': artifact,
                    'drop_path': drop_validation.get('path') if isinstance(drop_validation, dict) else None,
                    'target_path': artifact_record.get('target_path'),
                    'required_action': artifact_record.get('required_action', ''),
                    'current_present': drop_validation.get('present') if isinstance(drop_validation, dict) else False,
                    'current_valid': drop_validation.get('valid') if isinstance(drop_validation, dict) else False,
                    'current_gaps': gaps if isinstance(gaps, list) else [],
                    'validator': drop_validation.get('validator') if isinstance(drop_validation, dict) else None,
                    'template_paths_for_domain': template_map.get(domain, []),
                    'validation_command': VALIDATION_COMMAND,
                    'controlled_copy_command_after_all_rows_valid': CONTROLLED_COPY_COMMAND,
                    'domain_rebuild_commands_after_copy': commands,
                    'final_rebuild_command': REBUILD_COMMAND,
                    'acceptance_criteria': [
                        'operator_receipt_valid',
                        'artifact_drop_validator_row_valid',
                        'no_placeholder_or_synthetic_fixture_values',
                        'controlled_copy_target_path_matches_closure_manifest',
                        'dependent_domain_reports_rebuilt',
                        'full_production_verifier_passed',
                    ],
                    'closure_state': artifact_record.get('closure_state', 'WAITING_FOR_EXTERNAL_DATA'),
                    'does_not_clear_production_blockers': True,
                }
            )
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    closure_path = Path(args.production_blocker_closure_manifest_report)
    intake_path = Path(args.external_evidence_intake_kit_report)
    receipt_path = Path(args.external_artifact_operator_receipt_report)
    drop_path = Path(args.external_artifact_drop_validator_report)
    dashboard_path = Path(args.external_evidence_operations_dashboard_report)

    closure = load_json(closure_path)
    intake_kit = load_json(intake_path)
    operator_receipt = load_json(receipt_path)
    drop = load_json(drop_path)
    dashboard = load_json(dashboard_path)

    rows = artifact_rows(closure, intake_kit, drop)
    domain_count = len({row['domain'] for row in rows})
    valid_rows = sum(1 for row in rows if row.get('current_valid') is True)
    missing_or_invalid_rows = len(rows) - valid_rows
    ready_for_acceptance = (
        len(rows) == 14
        and valid_rows == len(rows)
        and operator_receipt.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT'
        and drop.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-DROP'
        and dashboard.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD'
    )
    quality_gate_matrix = [
        {
            'name': 'closure_manifest_attached',
            'status': 'PASS'
            if closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST'
            else 'MISSING',
            'evidence': str(closure_path),
            'gap': '',
        },
        {
            'name': 'intake_kit_attached',
            'status': 'PASS' if intake_kit.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-INTAKE-KIT-MANIFEST' else 'MISSING',
            'evidence': str(intake_path),
            'gap': '',
        },
        {
            'name': 'worksheet_has_all_expected_rows',
            'status': 'PASS' if len(rows) == 14 else 'MISSING',
            'evidence': f'rows={len(rows)}',
            'gap': '',
        },
        {
            'name': 'worksheet_domains_complete',
            'status': 'PASS' if {row['domain'] for row in rows} == EXPECTED_DOMAINS else 'MISSING',
            'evidence': ','.join(sorted({row['domain'] for row in rows})),
            'gap': '',
        },
        {
            'name': 'operator_receipt_gate_attached',
            'status': 'PASS'
            if operator_receipt.get('status')
            in {
                'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
                'NOT_READY-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
            }
            else 'MISSING',
            'evidence': str(receipt_path),
            'gap': '',
        },
        {
            'name': 'drop_validator_attached',
            'status': 'PASS'
            if drop.get('status') in {'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'}
            else 'MISSING',
            'evidence': str(drop_path),
            'gap': '',
        },
        {
            'name': 'worksheet_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'acceptance worksheet is handoff planning evidence only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Evidence Acceptance Worksheet',
        'production_blocker_closure_manifest_report': str(closure_path),
        'external_evidence_intake_kit_report': str(intake_path),
        'external_artifact_operator_receipt_report': str(receipt_path),
        'external_artifact_drop_validator_report': str(drop_path),
        'external_evidence_operations_dashboard_report': str(dashboard_path),
        'worksheet_csv': str(Path(args.output_csv)),
        'summary': {
            'domain_count': domain_count,
            'worksheet_row_count': len(rows),
            'valid_artifact_row_count': valid_rows,
            'missing_or_invalid_artifact_row_count': missing_or_invalid_rows,
            'operator_receipt_status': operator_receipt.get('status'),
            'operator_receipt_ready_for_acceptance': operator_receipt.get('ready_for_external_artifact_acceptance'),
            'drop_status': drop.get('status'),
            'drop_valid_artifact_count': drop.get('valid_artifact_count'),
            'drop_total_expected_artifact_count': drop.get('total_expected_artifact_count'),
            'dashboard_status': dashboard.get('status'),
            'ready_for_external_evidence_acceptance': ready_for_acceptance,
        },
        'worksheet_rows': rows,
        'operator_workflow': [
            {
                'step': 'fill_operator_receipt',
                'command': 'edit docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/drop/operator_receipt.json',
                'purpose': 'Provide operator/source/legal attestation for the real external artifact drop.',
            },
            {
                'step': 'stage_external_artifacts',
                'command': 'place real files in each worksheet row drop_path',
                'purpose': 'Populate all required CAD, plume-reference, and fire-calibration artifacts.',
            },
            {'step': 'validate_drop', 'command': VALIDATION_COMMAND, 'purpose': 'Validate all artifact rows.'},
            {
                'step': 'controlled_copy',
                'command': CONTROLLED_COPY_COMMAND,
                'purpose': 'Copy validated external evidence into controlled target paths after explicit confirmation.',
            },
            {'step': 'rebuild_and_verify', 'command': REBUILD_COMMAND, 'purpose': 'Rebuild the full evidence chain.'},
        ],
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_h2_production_blocker_closure_manifest_report', closure_path),
            evidence_entry('engineering_h2_external_evidence_intake_kit_manifest', intake_path),
            evidence_entry('engineering_h2_external_artifact_operator_receipt_report', receipt_path),
            evidence_entry('engineering_h2_external_artifact_drop_validator_report', drop_path),
            evidence_entry('engineering_h2_external_evidence_operations_dashboard_report', dashboard_path),
        ],
        'limitations': [
            'This worksheet is an operator handoff and acceptance ledger; it does not fabricate or supply missing external evidence.',
            'It cannot clear production blockers until a valid operator receipt, valid external artifact drop, controlled copy, domain rebuilds, and the full production verifier all pass.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'worksheet must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('domain_count', 0)) == 3, 'domain count mismatch')
    require(int(summary.get('worksheet_row_count', 0)) == 14, 'worksheet row count mismatch')
    require(
        int(summary.get('drop_total_expected_artifact_count', 0)) == 14,
        'drop total expected artifact count mismatch',
    )
    require(
        int(summary.get('valid_artifact_row_count', -1)) == int(summary.get('drop_valid_artifact_count', -2)),
        'worksheet valid rows must match drop validator valid artifacts',
    )
    require(
        summary.get('operator_receipt_status')
        in {
            'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
            'NOT_READY-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
        },
        'invalid operator receipt status',
    )
    require(
        summary.get('drop_status') in {'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'},
        'invalid drop status',
    )
    rows = data.get('worksheet_rows')
    require(isinstance(rows, list) and len(rows) == 14, 'worksheet_rows must contain 14 artifacts')
    domains = {str(row.get('domain')) for row in rows if isinstance(row, dict)}
    require(domains == EXPECTED_DOMAINS, f'worksheet domains mismatch: {domains}')
    for row in rows:
        require(isinstance(row, dict), 'worksheet row is not an object')
        require(str(row.get('artifact', '')).strip(), 'worksheet row missing artifact')
        require(str(row.get('drop_path', '')).startswith('docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/drop/'), 'unsafe or missing drop path')
        require(str(row.get('target_path', '')).startswith('docs/codex_audit/evidence/'), 'unsafe or missing target path')
        require(str(row.get('validation_command')) == VALIDATION_COMMAND, 'unexpected validation command')
        require(str(row.get('final_rebuild_command')) == REBUILD_COMMAND, 'unexpected final rebuild command')
        require(row.get('does_not_clear_production_blockers') is True, 'worksheet row must not clear blockers')
        require(isinstance(row.get('acceptance_criteria'), list) and len(row['acceptance_criteria']) >= 6, 'acceptance criteria incomplete')
    workflow = data.get('operator_workflow')
    require(isinstance(workflow, list) and len(workflow) >= 5, 'operator workflow incomplete')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'quality gate failed')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence hash mismatch: {path}')
        csv_path = Path(str(data.get('worksheet_csv', '')))
        require(csv_path.is_file(), f'missing worksheet CSV: {csv_path}')
        with csv_path.open(newline='', encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
        require(len(rows) == 14, 'worksheet CSV row count mismatch')


def write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = [
        'domain',
        'artifact',
        'drop_path',
        'target_path',
        'current_present',
        'current_valid',
        'validator',
        'required_action',
        'validation_command',
        'final_rebuild_command',
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in report['worksheet_rows']:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 External Evidence Acceptance Worksheet',
        '',
        f"Status: `{report['status']}`",
        f"Worksheet CSV: `{report['worksheet_csv']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Artifact Rows', '']
    for row in report['worksheet_rows']:
        lines.append(
            f"- `{row['domain']}` / `{row['artifact']}`: valid `{row['current_valid']}`, "
            f"drop `{row['drop_path']}`, target `{row['target_path']}`"
        )
    lines += ['', '## Operator Workflow', '']
    for item in report['operator_workflow']:
        lines.append(f"- `{item['step']}`: `{item['command']}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--external-evidence-intake-kit-report', default=str(DEFAULT_INTAKE_KIT))
    parser.add_argument('--external-artifact-operator-receipt-report', default=str(DEFAULT_OPERATOR_RECEIPT))
    parser.add_argument('--external-artifact-drop-validator-report', default=str(DEFAULT_DROP_VALIDATOR))
    parser.add_argument('--external-evidence-operations-dashboard-report', default=str(DEFAULT_DASHBOARD))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--output-csv', default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_evidence_acceptance_worksheet VERIFY-PASS '
                f"json={args.verify_json} rows={summary['worksheet_row_count']} "
                f"valid={summary['valid_artifact_row_count']}/"
                f"{summary['drop_total_expected_artifact_count']}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_csv = Path(args.output_csv)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        write_csv(report, out_csv)
        print(
            'engineering_h2_external_evidence_acceptance_worksheet PASS '
            f"json={out_json} md={out_md} csv={out_csv} "
            f"rows={report['summary']['worksheet_row_count']} "
            f"valid={report['summary']['valid_artifact_row_count']}/"
            f"{report['summary']['drop_total_expected_artifact_count']}"
        )
        return 0
    except AcceptanceWorksheetError as exc:
        print(f'engineering_h2_external_evidence_acceptance_worksheet FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
