#!/usr/bin/env python3
"""Write/verify the engineering H2 external evidence intake kit manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS = 'PASS-H2-EXTERNAL-EVIDENCE-INTAKE-KIT-MANIFEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_evidence_intake_kit_manifest.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_evidence_intake_kit_manifest.md'
DEFAULT_DATA_ROOM = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724/'
    'h2_production_blocker_data_room_report.json'
)
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_OPERATOR_RECEIPT_TEMPLATE = DEFAULT_ROOT / 'templates' / 'operator_receipt_template.json'

TEMPLATE_KITS = {
    'real_cad_cleanup': [
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/README.md',
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json',
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_intake_checklist.csv',
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index_template.csv',
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record_template.csv',
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/source_cad/README.md',
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/cleaned_geometry/README.md',
    ],
    'external_plume_shape_reference': [
        'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json',
        'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv',
        'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv',
        'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv',
        'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv',
    ],
    'fire_consequence_calibration': [
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/README.md',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_intake_checklist.csv',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/calibration_metadata_template.json',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/radiation_metrics_template.csv',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/overpressure_metrics_template.csv',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/fire_calibration_source_registry_template.csv',
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/fire_calibration_digitization_uncertainty_template.csv',
    ],
}

OPERATOR_RECEIPT_TEMPLATE = {
    'schema_version': 1,
    'receipt_id': '<replace-with-unique-receipt-id>',
    'operator_name': '<replace-with-person-accepting-drop>',
    'operator_role': '<replace-with-role>',
    'organization': '<replace-with-organization>',
    'supplier_or_source': '<replace-with-supplier-or-public-source>',
    'received_at_utc': '<replace-with-ISO-8601-UTC-timestamp>',
    'artifact_drop_root': 'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/drop',
    'domains': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
    'source_package': {
        'package_label': '<replace-with-package-label-or-archive-name>',
        'package_sha256': '<64 hex sha256>',
        'size_bytes': '<positive integer byte count>',
    },
    'legal_review': {
        'license_or_permission': '<replace-with-license-or-permission-record>',
        'confidentiality_classification': '<public|internal|controlled|restricted>',
        'export_control_reviewed': False,
        'redistribution_or_internal_use_permitted': False,
    },
    'domain_attestations': [
        {
            'domain': 'real_cad_cleanup',
            'artifact_manifest_included': False,
            'source_rights_confirmed': False,
            'no_synthetic_or_placeholder_values': False,
            'confidentiality_reviewed': False,
            'export_control_reviewed': False,
        },
        {
            'domain': 'external_plume_shape_reference',
            'artifact_manifest_included': False,
            'source_rights_confirmed': False,
            'no_synthetic_or_placeholder_values': False,
            'confidentiality_reviewed': False,
            'export_control_reviewed': False,
        },
        {
            'domain': 'fire_consequence_calibration',
            'artifact_manifest_included': False,
            'source_rights_confirmed': False,
            'no_synthetic_or_placeholder_values': False,
            'confidentiality_reviewed': False,
            'export_control_reviewed': False,
        },
    ],
}


class IntakeKitError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntakeKitError(message)


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
        raise IntakeKitError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise IntakeKitError(f'invalid JSON evidence {path}: {exc}') from exc
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


def template_entry(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    present = path.is_file()
    item: dict[str, Any] = {
        'path': path_text,
        'present': present,
    }
    if present:
        item.update(
            {
                'sha256': sha256_file(path),
                'size_bytes': path.stat().st_size,
            }
        )
    else:
        item.update({'sha256': None, 'size_bytes': None})
    return item


def ensure_operator_receipt_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(OPERATOR_RECEIPT_TEMPLATE, indent=2, sort_keys=True) + '\n'
    if not path.exists() or path.read_text(encoding='utf-8') != text:
        path.write_text(text, encoding='utf-8')


def domain_kit(domain: str, paths: list[str]) -> dict[str, Any]:
    templates = [template_entry(path) for path in paths]
    missing = [item['path'] for item in templates if not item['present']]
    return {
        'domain': domain,
        'template_count': len(templates),
        'present_template_count': len(templates) - len(missing),
        'missing_template_count': len(missing),
        'all_templates_present': not missing,
        'templates': templates,
        'missing_templates': missing,
    }


def data_room_domains(data: dict[str, Any]) -> set[str]:
    records = data.get('domain_records')
    require(isinstance(records, list), 'data-room domain_records missing')
    return {str(item.get('domain')) for item in records if isinstance(item, dict)}


def closure_domains(data: dict[str, Any]) -> set[str]:
    records = data.get('domain_closure_records')
    require(isinstance(records, list), 'closure manifest domain_closure_records missing')
    return {str(item.get('domain')) for item in records if isinstance(item, dict)}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    data_room_path = Path(args.production_blocker_data_room_report)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    operator_receipt_template_path = Path(args.operator_receipt_template)
    ensure_operator_receipt_template(operator_receipt_template_path)
    data_room = load_json(data_room_path)
    closure = load_json(closure_path)
    kits = [domain_kit(domain, paths) for domain, paths in TEMPLATE_KITS.items()]
    operator_receipt_template = template_entry(str(operator_receipt_template_path))
    total_templates = sum(int(item['template_count']) for item in kits) + 1
    present_templates = sum(int(item['present_template_count']) for item in kits) + int(
        operator_receipt_template['present'] is True
    )
    all_templates_present = all(item['all_templates_present'] for item in kits) and operator_receipt_template['present'] is True
    total_missing = int(data_room.get('total_missing_artifact_count', -1))
    closure_missing = int(closure.get('total_missing_artifact_count', -2))
    data_domains = data_room_domains(data_room)
    closure_domain_set = closure_domains(closure)
    expected_domains = set(TEMPLATE_KITS)
    consistency = {
        'data_room_status': data_room.get('status'),
        'closure_manifest_status': closure.get('status'),
        'data_room_missing_artifact_count': total_missing,
        'closure_manifest_missing_artifact_count': closure_missing,
        'missing_artifact_count_matches': total_missing == closure_missing,
        'data_room_domains': sorted(data_domains),
        'closure_manifest_domains': sorted(closure_domain_set),
        'domain_sets_match': data_domains == closure_domain_set == expected_domains,
        'remaining_blocker_count': data_room.get('remaining_blocker_count'),
    }
    ready_for_handoff = (
        all_templates_present
        and consistency['missing_artifact_count_matches']
        and consistency['domain_sets_match']
        and data_room.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM'
        and closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST'
    )
    quality_gate_matrix = [
        {
            'name': 'data_room_report_attached',
            'status': 'PASS' if data_room.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM' else 'MISSING',
            'evidence': str(data_room_path),
            'gap': '',
        },
        {
            'name': 'closure_manifest_attached',
            'status': 'PASS'
            if closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST'
            else 'MISSING',
            'evidence': str(closure_path),
            'gap': '',
        },
        {
            'name': 'all_required_templates_present',
            'status': 'PASS' if all_templates_present else 'MISSING',
            'evidence': f'{present_templates}/{total_templates} template(s)',
            'gap': '' if all_templates_present else 'one or more intake templates are missing',
        },
        {
            'name': 'operator_receipt_template_present',
            'status': 'PASS' if operator_receipt_template['present'] is True else 'MISSING',
            'evidence': str(operator_receipt_template_path),
            'gap': '',
        },
        {
            'name': 'missing_artifact_count_consistent',
            'status': 'PASS' if consistency['missing_artifact_count_matches'] else 'MISSING',
            'evidence': f"data_room={total_missing} closure={closure_missing}",
            'gap': '',
        },
        {
            'name': 'domain_sets_consistent',
            'status': 'PASS' if consistency['domain_sets_match'] else 'MISSING',
            'evidence': ','.join(sorted(expected_domains)),
            'gap': '',
        },
        {
            'name': 'does_not_clear_production_blockers',
            'status': 'PASS' if total_missing > 0 and int(data_room.get('remaining_blocker_count', 0)) > 0 else 'MISSING',
            'evidence': f"missing_artifacts={total_missing} remaining_blockers={data_room.get('remaining_blocker_count')}",
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Evidence Intake Kit Manifest',
        'production_blocker_data_room_report': str(data_room_path),
        'production_blocker_closure_manifest_report': str(closure_path),
        'total_template_count': total_templates,
        'present_template_count': present_templates,
        'all_required_templates_present': all_templates_present,
        'operator_receipt_template': operator_receipt_template,
        'operator_receipt_template_present': operator_receipt_template['present'],
        'ready_for_external_data_handoff': ready_for_handoff,
        'does_not_clear_production_blockers': True,
        'total_missing_artifact_count': total_missing,
        'remaining_blocker_count': data_room.get('remaining_blocker_count'),
        'closure_manifest_consistency': consistency,
        'domain_kits': kits,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('production_blocker_data_room_report', data_room_path),
            evidence_entry('production_blocker_closure_manifest_report', closure_path),
        ],
        'limitations': [
            'This intake kit manifest verifies handoff templates and hashes; it does not supply the missing external evidence.',
            'Production readiness remains blocked until real CAD, SBEPV5 external plume data, and calibrated fire consequence metrics are ingested and reverified.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(set(TEMPLATE_KITS) == {str(item.get('domain')) for item in data.get('domain_kits', [])}, 'domain kits mismatch')
    require(int(data.get('total_template_count', 0)) >= 23, 'too few intake templates')
    require(data.get('all_required_templates_present') is True, 'required intake templates are missing')
    require(data.get('operator_receipt_template_present') is True, 'operator receipt template is missing')
    receipt_template = data.get('operator_receipt_template')
    require(isinstance(receipt_template, dict), 'operator_receipt_template entry missing')
    receipt_template_path = Path(str(receipt_template.get('path', '')))
    require(receipt_template_path.is_file(), f'missing operator receipt template file: {receipt_template_path}')
    if check_hashes:
        require(
            sha256_file(receipt_template_path) == receipt_template.get('sha256'),
            f'operator receipt template sha256 mismatch: {receipt_template_path}',
        )
    require(data.get('ready_for_external_data_handoff') is True, 'intake kit is not ready for external data handoff')
    require(data.get('does_not_clear_production_blockers') is True, 'intake kit must not clear production blockers')
    require(int(data.get('total_missing_artifact_count', 0)) >= 1, 'intake kit unexpectedly has no missing artifacts')
    require(int(data.get('remaining_blocker_count', 0)) >= 1, 'intake kit unexpectedly has no blockers')
    consistency = data.get('closure_manifest_consistency')
    require(isinstance(consistency, dict), 'closure_manifest_consistency missing')
    require(consistency.get('data_room_status') == 'PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM', 'data-room did not PASS')
    require(
        consistency.get('closure_manifest_status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST',
        'closure manifest did not PASS',
    )
    require(consistency.get('missing_artifact_count_matches') is True, 'missing artifact counts do not match')
    require(consistency.get('domain_sets_match') is True, 'domain sets do not match')
    require(
        int(consistency.get('data_room_missing_artifact_count', -1))
        == int(data.get('total_missing_artifact_count', -2)),
        'data-room missing artifact count differs from intake kit summary',
    )
    for kit in data.get('domain_kits', []):
        require(isinstance(kit, dict), 'domain kit is not an object')
        require(kit.get('all_templates_present') is True, f"{kit.get('domain')} has missing templates")
        templates = kit.get('templates')
        require(isinstance(templates, list) and templates, f"{kit.get('domain')} templates missing")
        for item in templates:
            require(isinstance(item, dict), 'template entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing template file: {path}')
            if check_hashes:
                require(sha256_file(path) == item.get('sha256'), f'template sha256 mismatch: {path}')
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


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 External Evidence Intake Kit Manifest',
        '',
        f"Status: `{report['status']}`",
        f"Total templates: `{report['total_template_count']}`",
        f"All templates present: `{report['all_required_templates_present']}`",
        f"Operator receipt template present: `{report['operator_receipt_template_present']}`",
        f"Ready for external data handoff: `{report['ready_for_external_data_handoff']}`",
        f"Remaining blockers: `{report['remaining_blocker_count']}`",
        f"Total missing artifacts: `{report['total_missing_artifact_count']}`",
        '',
        '## Domain Kits',
        '',
    ]
    for kit in report['domain_kits']:
        lines.append(f"### {kit['domain']}")
        lines.append(f"- Templates: `{kit['present_template_count']}/{kit['template_count']}`")
        for item in kit['templates']:
            lines.append(f"- `{item['path']}` sha256 `{str(item['sha256'])[:16]}`")
        lines.append('')
    receipt_template = report['operator_receipt_template']
    lines += ['## Operator Receipt Template', '']
    lines.append(f"- `{receipt_template['path']}` sha256 `{str(receipt_template['sha256'])[:16]}`")
    lines.append('')
    lines += ['## Quality Gates', '']
    for row in report['quality_gate_matrix']:
        lines.append(f"- `{row['name']}`: `{row['status']}`")
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
    parser.add_argument('--production-blocker-data-room-report', default=str(DEFAULT_DATA_ROOM))
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--operator-receipt-template', default=str(DEFAULT_OPERATOR_RECEIPT_TEMPLATE))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_external_evidence_intake_kit_manifest VERIFY-PASS '
                f"json={args.verify_json} templates={report['total_template_count']} "
                f"missing_artifacts={report['total_missing_artifact_count']}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_external_evidence_intake_kit_manifest PASS '
            f"json={out_json} md={out_md} templates={report['total_template_count']} "
            f"missing_artifacts={report['total_missing_artifact_count']}"
        )
        return 0
    except IntakeKitError as exc:
        print(f'engineering_h2_external_evidence_intake_kit_manifest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
