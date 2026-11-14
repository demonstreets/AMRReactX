#!/usr/bin/env python3
"""Write/verify the engineering H2 external artifact operator receipt report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_READY = 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT'
STATUS_NOT_READY = 'NOT_READY-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT'
RECEIPT_GATE_LEVEL = 'strict-v1-operator-source-legal-attestation'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_operator_receipt_20260724')
DEFAULT_DROP_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/drop')
DEFAULT_RECEIPT = DEFAULT_DROP_ROOT / 'operator_receipt.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_operator_receipt_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_operator_receipt_report.md'
DEFAULT_DATA_ROOM = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724/'
    'h2_production_blocker_data_room_report.json'
)
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_INTAKE_KIT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724/'
    'h2_external_evidence_intake_kit_manifest.json'
)

EXPECTED_DOMAINS = {
    'real_cad_cleanup',
    'external_plume_shape_reference',
    'fire_consequence_calibration',
}
PLACEHOLDER_MARKERS = (
    '<',
    'replace',
    'pending',
    'todo',
    'tbd',
    'placeholder',
    'fill in',
    'to be supplied',
)
ALLOWED_CONFIDENTIALITY = {'public', 'internal', 'controlled', 'restricted'}


class OperatorReceiptError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OperatorReceiptError(message)


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
        raise OperatorReceiptError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise OperatorReceiptError(f'invalid JSON evidence {path}: {exc}') from exc
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


def text_has_placeholder_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return any(text_has_placeholder_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(text_has_placeholder_marker(item) for item in value)
    text = str(value).strip().lower()
    return bool(text) and any(marker in text for marker in PLACEHOLDER_MARKERS)


def parse_iso_utc(value: Any, label: str, gaps: list[str]) -> None:
    text = str(value).strip()
    if not text:
        gaps.append(f'missing_timestamp:{label}')
        return
    try:
        parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        gaps.append(f'invalid_timestamp:{label}:{text}')
        return
    if parsed.tzinfo is None:
        gaps.append(f'timestamp_missing_timezone:{label}:{text}')


def require_nonplaceholder_text(data: dict[str, Any], key: str, gaps: list[str]) -> None:
    value = data.get(key)
    if not str(value or '').strip():
        gaps.append(f'receipt_missing_key:{key}')
    elif text_has_placeholder_marker(value):
        gaps.append(f'receipt_placeholder_value:{key}')


def receipt_domains(receipt: dict[str, Any]) -> set[str]:
    domains = receipt.get('domains')
    if isinstance(domains, list):
        return {str(item).strip() for item in domains if str(item).strip()}
    return set()


def validate_receipt(receipt_path: Path, drop_root: Path, closure_manifest: dict[str, Any]) -> dict[str, Any]:
    if not receipt_path.is_file():
        return {
            'present': False,
            'valid': False,
            'gaps': [f'missing_operator_receipt:{receipt_path}'],
            'summary': {},
        }
    gaps: list[str] = []
    try:
        receipt = load_json(receipt_path)
    except OperatorReceiptError as exc:
        return {'present': True, 'valid': False, 'gaps': [str(exc)], 'summary': {}}

    for key in ('receipt_id', 'operator_name', 'operator_role', 'organization', 'supplier_or_source'):
        require_nonplaceholder_text(receipt, key, gaps)
    if receipt.get('schema_version') != 1:
        gaps.append(f"receipt_schema_version_not_1:{receipt.get('schema_version')}")
    if str(receipt.get('artifact_drop_root', '')).strip() != str(drop_root):
        gaps.append('receipt_artifact_drop_root_mismatch')
    parse_iso_utc(receipt.get('received_at_utc'), 'received_at_utc', gaps)
    if text_has_placeholder_marker(receipt):
        gaps.append('receipt_placeholder_or_template_marker_present')

    domains = receipt_domains(receipt)
    if domains != EXPECTED_DOMAINS:
        gaps.append('receipt_domain_set_mismatch:' + ','.join(sorted(domains)))
    closure_domains = {
        str(item.get('domain'))
        for item in closure_manifest.get('domain_closure_records', [])
        if isinstance(item, dict)
    }
    if domains and domains != closure_domains:
        gaps.append('receipt_domain_set_differs_from_closure_manifest')

    package = receipt.get('source_package')
    if not isinstance(package, dict):
        gaps.append('receipt_source_package_not_object')
    else:
        require_nonplaceholder_text(package, 'package_label', gaps)
        package_hash = str(package.get('package_sha256', '')).strip().lower()
        if not re.fullmatch(r'[0-9a-f]{64}', package_hash):
            gaps.append('receipt_source_package_sha256_invalid')
        try:
            size_bytes = int(package.get('size_bytes'))
        except (TypeError, ValueError):
            gaps.append('receipt_source_package_size_bytes_invalid')
        else:
            if size_bytes <= 0:
                gaps.append('receipt_source_package_size_bytes_not_positive')

    legal = receipt.get('legal_review')
    if not isinstance(legal, dict):
        gaps.append('receipt_legal_review_not_object')
    else:
        require_nonplaceholder_text(legal, 'license_or_permission', gaps)
        confidentiality = str(legal.get('confidentiality_classification', '')).strip().lower()
        if confidentiality not in ALLOWED_CONFIDENTIALITY:
            gaps.append(f'receipt_confidentiality_classification_invalid:{confidentiality}')
        if legal.get('export_control_reviewed') is not True:
            gaps.append('receipt_export_control_not_reviewed')
        if legal.get('redistribution_or_internal_use_permitted') is not True:
            gaps.append('receipt_redistribution_or_internal_use_not_permitted')

    attestations = receipt.get('domain_attestations')
    if not isinstance(attestations, list):
        gaps.append('receipt_domain_attestations_not_list')
        attestation_domains: set[str] = set()
    else:
        attestation_domains = {str(item.get('domain', '')).strip() for item in attestations if isinstance(item, dict)}
        if attestation_domains != EXPECTED_DOMAINS:
            gaps.append('receipt_domain_attestation_set_mismatch:' + ','.join(sorted(attestation_domains)))
        for item in attestations:
            if not isinstance(item, dict):
                gaps.append('receipt_domain_attestation_not_object')
                continue
            domain = str(item.get('domain', '')).strip()
            for key in (
                'artifact_manifest_included',
                'source_rights_confirmed',
                'no_synthetic_or_placeholder_values',
                'confidentiality_reviewed',
                'export_control_reviewed',
            ):
                if item.get(key) is not True:
                    gaps.append(f'receipt_domain_attestation_not_true:{domain}:{key}')

    return {
        'present': True,
        'valid': not gaps,
        'gaps': gaps,
        'summary': {
            'receipt_id': receipt.get('receipt_id'),
            'operator_name': receipt.get('operator_name'),
            'organization': receipt.get('organization'),
            'received_at_utc': receipt.get('received_at_utc'),
            'domain_count': len(domains),
            'domain_attestation_count': len(attestation_domains),
        },
        'sha256': sha256_file(receipt_path),
        'size_bytes': receipt_path.stat().st_size,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    receipt_path = Path(args.operator_receipt)
    drop_root = Path(args.drop_root)
    data_room_path = Path(args.production_blocker_data_room_report)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    intake_kit_path = Path(args.external_evidence_intake_kit_report)
    data_room = load_json(data_room_path)
    closure = load_json(closure_path)
    intake = load_json(intake_kit_path)
    validation = validate_receipt(receipt_path, drop_root, closure)
    ready = validation['valid'] is True
    status = STATUS_READY if ready else STATUS_NOT_READY
    quality_gate_matrix = [
        {
            'name': 'data_room_attached',
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
            'name': 'intake_kit_attached',
            'status': 'PASS' if intake.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-INTAKE-KIT-MANIFEST' else 'MISSING',
            'evidence': str(intake_kit_path),
            'gap': '',
        },
        {
            'name': 'operator_receipt_gate_enforced',
            'status': 'PASS',
            'evidence': f"gate={RECEIPT_GATE_LEVEL} receipt_present={validation['present']} gaps={len(validation['gaps'])}",
            'gap': '',
        },
        {
            'name': 'not_ready_receipt_does_not_clear_blockers',
            'status': 'PASS'
            if ready or int(data_room.get('remaining_blocker_count', 0)) >= 1
            else 'MISSING',
            'evidence': f"ready={ready} remaining_blockers={data_room.get('remaining_blocker_count')}",
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 External Artifact Operator Receipt',
        'receipt_gate_level': RECEIPT_GATE_LEVEL,
        'operator_receipt_path': str(receipt_path),
        'drop_root': str(drop_root),
        'receipt_present': validation['present'],
        'receipt_valid': validation['valid'],
        'receipt_validation_gap_count': len(validation['gaps']),
        'receipt_validation_gaps': validation['gaps'],
        'receipt_validation': validation,
        'ready_for_external_artifact_acceptance': ready,
        'does_not_clear_production_blockers': True,
        'expected_domains': sorted(EXPECTED_DOMAINS),
        'remaining_blocker_count': data_room.get('remaining_blocker_count'),
        'total_missing_artifact_count': data_room.get('total_missing_artifact_count'),
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('production_blocker_data_room_report', data_room_path),
            evidence_entry('production_blocker_closure_manifest_report', closure_path),
            evidence_entry('external_evidence_intake_kit_manifest', intake_kit_path),
        ],
        'limitations': [
            'This receipt gate validates operator/source/legal attestations for a staged external artifact drop; it does not supply external evidence.',
            'A PASS receipt is required before real external artifacts should be accepted for controlled ingestion, but it does not by itself clear production blockers.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('receipt_gate_level') == RECEIPT_GATE_LEVEL, 'receipt gate level mismatch')
    require(data.get('does_not_clear_production_blockers') is True, 'receipt gate must not clear blockers')
    require(set(data.get('expected_domains', [])) == EXPECTED_DOMAINS, 'expected domains mismatch')
    gap_count = int(data.get('receipt_validation_gap_count', -1))
    require(gap_count >= 0, 'receipt gap count invalid')
    if data.get('status') == STATUS_READY:
        require(data.get('receipt_present') is True, 'PASS receipt report missing receipt')
        require(data.get('receipt_valid') is True, 'PASS receipt report invalid')
        require(gap_count == 0, 'PASS receipt report has gaps')
        require(data.get('ready_for_external_artifact_acceptance') is True, 'PASS receipt not ready for acceptance')
    else:
        require(data.get('receipt_valid') is False, 'NOT_READY receipt report marked valid')
        require(gap_count >= 1, 'NOT_READY receipt report must retain receipt gaps')
        require(data.get('ready_for_external_artifact_acceptance') is False, 'NOT_READY receipt marked ready')
        require(int(data.get('remaining_blocker_count', 0)) >= 1, 'NOT_READY receipt unexpectedly has no blockers')
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
        '# Engineering H2 External Artifact Operator Receipt',
        '',
        f"Status: `{report['status']}`",
        f"Receipt gate: `{report['receipt_gate_level']}`",
        f"Receipt path: `{report['operator_receipt_path']}`",
        f"Receipt present: `{report['receipt_present']}`",
        f"Receipt valid: `{report['receipt_valid']}`",
        f"Receipt validation gaps: `{report['receipt_validation_gap_count']}`",
        f"Ready for external artifact acceptance: `{report['ready_for_external_artifact_acceptance']}`",
        '',
        '## Receipt Gaps',
        '',
    ]
    for gap in report['receipt_validation_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Quality Gates', '']
    for row in report['quality_gate_matrix']:
        lines.append(f"- `{row['name']}`: `{row['status']}`")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
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
    parser.add_argument('--operator-receipt', default=str(DEFAULT_RECEIPT))
    parser.add_argument('--drop-root', default=str(DEFAULT_DROP_ROOT))
    parser.add_argument('--production-blocker-data-room-report', default=str(DEFAULT_DATA_ROOM))
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--external-evidence-intake-kit-report', default=str(DEFAULT_INTAKE_KIT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_external_artifact_operator_receipt VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"present={report['receipt_present']} gaps={report['receipt_validation_gap_count']}"
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
            'engineering_h2_external_artifact_operator_receipt PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"present={report['receipt_present']} gaps={report['receipt_validation_gap_count']}"
        )
        return 0
    except OperatorReceiptError as exc:
        print(f'engineering_h2_external_artifact_operator_receipt FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
