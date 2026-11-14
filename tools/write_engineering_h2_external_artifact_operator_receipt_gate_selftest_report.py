#!/usr/bin/env python3
"""Run/write/verify an isolated self-test for the H2 external artifact operator receipt gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT-GATE-SELFTEST'
EXPECTED_RECEIPT_GATE_LEVEL = 'strict-v1-operator-source-legal-attestation'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_operator_receipt_gate_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_operator_receipt_gate_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_operator_receipt_gate_selftest_report.md'
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_INTAKE_KIT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724/'
    'h2_external_evidence_intake_kit_manifest.json'
)

DOMAINS = (
    'real_cad_cleanup',
    'external_plume_shape_reference',
    'fire_consequence_calibration',
)


class ReceiptGateSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptGateSelftestError(message)


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
        raise ReceiptGateSelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReceiptGateSelftestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def run_command(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        'command': ' '.join(argv),
        'returncode': completed.returncode,
        'output_tail': completed.stdout[-2000:],
    }


def run_expect_zero(argv: list[str]) -> dict[str, Any]:
    record = run_command(argv)
    require(record['returncode'] == 0, f"command failed: {record['command']}\n{record['output_tail']}")
    return record


def domain_attestations(value: bool) -> list[dict[str, Any]]:
    return [
        {
            'domain': domain,
            'artifact_manifest_included': value,
            'source_rights_confirmed': value,
            'no_synthetic_or_placeholder_values': value,
            'confidentiality_reviewed': value,
            'export_control_reviewed': value,
        }
        for domain in DOMAINS
    ]


def valid_receipt(drop_root: Path) -> dict[str, Any]:
    return {
        'schema_version': 1,
        'receipt_id': 'receipt-gate-valid-001',
        'operator_name': 'QA Operator',
        'operator_role': 'evidence intake reviewer',
        'organization': 'Codex Engineering Verification',
        'supplier_or_source': 'controlled receipt gate fixture',
        'received_at_utc': '2026-07-24T00:00:00+00:00',
        'artifact_drop_root': str(drop_root),
        'domains': list(DOMAINS),
        'source_package': {
            'package_label': 'receipt-gate-valid-package.tar.gz',
            'package_sha256': 'a' * 64,
            'size_bytes': 1024,
        },
        'legal_review': {
            'license_or_permission': 'internal verification fixture permission record',
            'confidentiality_classification': 'internal',
            'export_control_reviewed': True,
            'redistribution_or_internal_use_permitted': True,
        },
        'domain_attestations': domain_attestations(True),
    }


def invalid_template_receipt(drop_root: Path, intake_kit: dict[str, Any]) -> dict[str, Any]:
    template = intake_kit.get('operator_receipt_template')
    require(isinstance(template, dict), 'intake kit missing operator receipt template entry')
    template_path = Path(str(template.get('path', '')))
    require(template_path.is_file(), f'missing operator receipt template: {template_path}')
    receipt = load_json(template_path)
    receipt['artifact_drop_root'] = str(drop_root)
    return receipt


def receipt_gap_sample(report: dict[str, Any], limit: int = 20) -> list[str]:
    gaps = report.get('receipt_validation_gaps')
    if isinstance(gaps, list):
        return [str(item) for item in gaps[:limit]]
    return []


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.output_json).parent
    closure_path = Path(args.production_blocker_closure_manifest_report)
    intake_kit_path = Path(args.external_evidence_intake_kit_report)
    intake_kit = load_json(intake_kit_path)
    py = sys.executable

    positive_drop = root / 'positive_fixture' / 'drop'
    negative_drop = root / 'negative_fixture' / 'drop'
    positive_receipt = positive_drop / 'operator_receipt.json'
    negative_receipt = negative_drop / 'operator_receipt.json'
    positive_report = root / 'positive_operator_receipt_report.json'
    positive_md = root / 'positive_operator_receipt_report.md'
    negative_report = root / 'negative_operator_receipt_report.json'
    negative_md = root / 'negative_operator_receipt_report.md'

    write_json(positive_receipt, valid_receipt(positive_drop))
    write_json(negative_receipt, invalid_template_receipt(negative_drop, intake_kit))

    commands = [
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_operator_receipt_report.py',
                '--operator-receipt',
                str(positive_receipt),
                '--drop-root',
                str(positive_drop),
                '--production-blocker-closure-manifest-report',
                str(closure_path),
                '--external-evidence-intake-kit-report',
                str(intake_kit_path),
                '--output-json',
                str(positive_report),
                '--output-md',
                str(positive_md),
            ]
        ),
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_operator_receipt_report.py',
                '--operator-receipt',
                str(positive_receipt),
                '--drop-root',
                str(positive_drop),
                '--verify-json',
                str(positive_report),
            ]
        ),
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_operator_receipt_report.py',
                '--operator-receipt',
                str(negative_receipt),
                '--drop-root',
                str(negative_drop),
                '--production-blocker-closure-manifest-report',
                str(closure_path),
                '--external-evidence-intake-kit-report',
                str(intake_kit_path),
                '--output-json',
                str(negative_report),
                '--output-md',
                str(negative_md),
            ]
        ),
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_operator_receipt_report.py',
                '--operator-receipt',
                str(negative_receipt),
                '--drop-root',
                str(negative_drop),
                '--verify-json',
                str(negative_report),
            ]
        ),
    ]

    positive = load_json(positive_report)
    negative = load_json(negative_report)
    negative_gaps = receipt_gap_sample(negative)
    negative_placeholder_detected = any('placeholder' in gap or 'template' in gap for gap in negative_gaps)
    quality_gate_matrix = [
        {
            'name': 'positive_receipt_fixture_passes_gate',
            'status': 'PASS'
            if positive.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT'
            and positive.get('receipt_gate_level') == EXPECTED_RECEIPT_GATE_LEVEL
            and positive.get('receipt_valid') is True
            and int(positive.get('receipt_validation_gap_count', -1)) == 0
            else 'MISSING',
            'evidence': str(positive_report),
            'gap': '',
        },
        {
            'name': 'template_receipt_fixture_is_rejected',
            'status': 'PASS'
            if negative.get('status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT'
            and negative.get('receipt_gate_level') == EXPECTED_RECEIPT_GATE_LEVEL
            and negative.get('receipt_valid') is False
            and int(negative.get('receipt_validation_gap_count', 0)) >= 1
            else 'MISSING',
            'evidence': str(negative_report),
            'gap': '',
        },
        {
            'name': 'template_placeholder_gap_detected',
            'status': 'PASS' if negative_placeholder_detected else 'MISSING',
            'evidence': ';'.join(negative_gaps),
            'gap': '',
        },
        {
            'name': 'selftest_does_not_clear_production_blockers',
            'status': 'PASS'
            if positive.get('does_not_clear_production_blockers') is True
            and negative.get('does_not_clear_production_blockers') is True
            else 'MISSING',
            'evidence': 'isolated receipt fixtures only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Artifact Operator Receipt Gate Self-Test',
        'selftest_only': True,
        'does_not_clear_production_blockers': True,
        'receipt_gate_level': EXPECTED_RECEIPT_GATE_LEVEL,
        'positive_receipt_report': str(positive_report),
        'negative_receipt_report': str(negative_report),
        'summary': {
            'positive_status': positive.get('status'),
            'positive_receipt_valid': positive.get('receipt_valid'),
            'positive_gap_count': positive.get('receipt_validation_gap_count'),
            'negative_status': negative.get('status'),
            'negative_receipt_valid': negative.get('receipt_valid'),
            'negative_gap_count': negative.get('receipt_validation_gap_count'),
            'negative_placeholder_gap_detected': negative_placeholder_detected,
            'negative_gap_sample': negative_gaps,
        },
        'command_records': commands,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('production_blocker_closure_manifest_report', closure_path),
            evidence_entry('external_evidence_intake_kit_manifest', intake_kit_path),
            evidence_entry('positive_operator_receipt_report', positive_report),
            evidence_entry('negative_operator_receipt_report', negative_report),
        ],
        'limitations': [
            'This self-test uses isolated receipt fixtures and must not be used to clear real external-data blockers.',
            'The positive fixture proves the receipt gate can pass a complete receipt; the negative fixture proves the template cannot pass unchanged.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('selftest_only') is True, 'receipt gate self-test must be marked selftest-only')
    require(data.get('does_not_clear_production_blockers') is True, 'self-test must not clear blockers')
    require(data.get('receipt_gate_level') == EXPECTED_RECEIPT_GATE_LEVEL, 'receipt gate level mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('positive_status') == 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT', 'positive receipt did not pass')
    require(summary.get('positive_receipt_valid') is True, 'positive receipt is invalid')
    require(int(summary.get('positive_gap_count', -1)) == 0, 'positive receipt has gaps')
    require(summary.get('negative_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT', 'template receipt was not rejected')
    require(summary.get('negative_receipt_valid') is False, 'template receipt marked valid')
    require(int(summary.get('negative_gap_count', 0)) >= 1, 'template receipt did not retain gaps')
    require(summary.get('negative_placeholder_gap_detected') is True, 'template receipt placeholder gap not detected')
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
    summary = report['summary']
    lines = [
        '# Engineering H2 External Artifact Operator Receipt Gate Self-Test',
        '',
        f"Status: `{report['status']}`",
        f"Self-test only: `{report['selftest_only']}`",
        f"Receipt gate: `{report['receipt_gate_level']}`",
        f"Positive status: `{summary['positive_status']}` gaps=`{summary['positive_gap_count']}`",
        f"Negative status: `{summary['negative_status']}` gaps=`{summary['negative_gap_count']}`",
        f"Negative placeholder gap detected: `{summary['negative_placeholder_gap_detected']}`",
        '',
        '## Negative Gap Sample',
        '',
    ]
    for gap in summary['negative_gap_sample']:
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
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--external-evidence-intake-kit-report', default=str(DEFAULT_INTAKE_KIT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_artifact_operator_receipt_gate_selftest VERIFY-PASS '
                f"json={args.verify_json} positive={summary['positive_status']} "
                f"negative={summary['negative_status']}"
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
        summary = report['summary']
        print(
            'engineering_h2_external_artifact_operator_receipt_gate_selftest PASS '
            f"json={out_json} md={out_md} positive={summary['positive_status']} "
            f"negative={summary['negative_status']}"
        )
        return 0
    except ReceiptGateSelftestError as exc:
        print(f'engineering_h2_external_artifact_operator_receipt_gate_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
