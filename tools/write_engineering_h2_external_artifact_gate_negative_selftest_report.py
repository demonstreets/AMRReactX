#!/usr/bin/env python3
"""Run/write/verify a negative synthetic self-test for the engineering H2 external artifact gates."""
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
STATUS = 'PASS-H2-EXTERNAL-ARTIFACT-GATE-NEGATIVE-SELFTEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_gate_negative_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_gate_negative_selftest_report.md'
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)


class NegativeSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NegativeSelftestError(message)


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
        raise NegativeSelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise NegativeSelftestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def run_expect_nonzero(argv: list[str]) -> dict[str, Any]:
    record = run_command(argv)
    require(record['returncode'] != 0, f"command unexpectedly passed: {record['command']}")
    return record


def write_bad_fixture(drop_root: Path) -> None:
    # One malformed JSON is enough to prove bad inputs are not silently promoted.
    bad_root = drop_root / 'real_cad_cleanup'
    bad_root.mkdir(parents=True, exist_ok=True)
    (bad_root / 'real_cad_cleanup_manifest.json').write_text('{"schema_version": 1}\n', encoding='utf-8')
    (bad_root / 'source_cad').mkdir(parents=True, exist_ok=True)
    (bad_root / 'source_cad' / 'only_one.stp').write_text('ISO-10303-21 negative selftest\n', encoding='utf-8')


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.output_json).parent
    drop_root = root / 'negative_fixture' / 'drop'
    drop_report = root / 'negative_drop_validator_report.json'
    drop_md = root / 'negative_drop_validator_report.md'
    plan_report = root / 'negative_ingestion_plan.json'
    plan_md = root / 'negative_ingestion_plan.md'
    copy_report = root / 'negative_controlled_copy_report.json'
    copy_md = root / 'negative_controlled_copy_report.md'
    closure_path = Path(args.production_blocker_closure_manifest_report)

    root.mkdir(parents=True, exist_ok=True)
    write_bad_fixture(drop_root)

    py = sys.executable
    commands = []
    commands.append(
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_drop_validator.py',
                '--drop-root',
                str(drop_root),
                '--production-blocker-closure-manifest-report',
                str(closure_path),
                '--output-json',
                str(drop_report),
                '--output-md',
                str(drop_md),
            ]
        )
    )
    commands.append(run_expect_zero([py, 'tools/write_engineering_h2_external_artifact_drop_validator.py', '--verify-json', str(drop_report)]))
    commands.append(
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_ingestion_plan.py',
                '--external-artifact-drop-validator-report',
                str(drop_report),
                '--production-blocker-closure-manifest-report',
                str(closure_path),
                '--output-json',
                str(plan_report),
                '--output-md',
                str(plan_md),
            ]
        )
    )
    commands.append(run_expect_zero([py, 'tools/write_engineering_h2_external_artifact_ingestion_plan.py', '--verify-json', str(plan_report)]))
    commands.append(
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
                '--external-artifact-ingestion-plan-report',
                str(plan_report),
                '--output-json',
                str(copy_report),
                '--output-md',
                str(copy_md),
            ]
        )
    )
    commands.append(run_expect_zero([py, 'tools/write_engineering_h2_external_artifact_controlled_copy_report.py', '--verify-json', str(copy_report)]))
    refused_apply = run_expect_nonzero(
        [
            py,
            'tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
            '--external-artifact-ingestion-plan-report',
            str(plan_report),
            '--apply',
            '--confirm-controlled-copy',
            'H2_EXTERNAL_ARTIFACTS_READY',
            '--output-json',
            str(root / 'negative_apply_should_not_exist.json'),
            '--output-md',
            str(root / 'negative_apply_should_not_exist.md'),
        ]
    )
    commands.append(refused_apply)

    drop = load_json(drop_report)
    plan = load_json(plan_report)
    copy = load_json(copy_report)
    quality_gate_matrix = [
        {
            'name': 'negative_drop_is_not_ready',
            'status': 'PASS'
            if drop.get('status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'
            and int(drop.get('missing_or_invalid_artifact_count', 0)) >= 1
            else 'MISSING',
            'evidence': str(drop_report),
            'gap': '',
        },
        {
            'name': 'negative_ingestion_is_not_ready',
            'status': 'PASS'
            if plan.get('status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'
            and int(plan.get('missing_or_invalid_copy_action_count', 0)) >= 1
            else 'MISSING',
            'evidence': str(plan_report),
            'gap': '',
        },
        {
            'name': 'negative_controlled_copy_no_writes',
            'status': 'PASS'
            if copy.get('status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
            and copy.get('applied_copy_actions') is False
            and int(copy.get('copied_file_count', -1)) == 0
            else 'MISSING',
            'evidence': str(copy_report),
            'gap': '',
        },
        {
            'name': 'negative_apply_refused',
            'status': 'PASS' if int(refused_apply.get('returncode', 0)) != 0 else 'MISSING',
            'evidence': refused_apply.get('output_tail', ''),
            'gap': '',
        },
        {
            'name': 'does_not_clear_production_blockers',
            'status': 'PASS',
            'evidence': 'negative self-test is gate-mechanics evidence only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Artifact Gate Negative Synthetic Self-Test',
        'negative_selftest_only': True,
        'does_not_clear_production_blockers': True,
        'production_blocker_closure_manifest_report': str(closure_path),
        'negative_drop_root': str(drop_root),
        'negative_reports': {
            'drop_validator': str(drop_report),
            'ingestion_plan': str(plan_report),
            'controlled_copy': str(copy_report),
        },
        'summary': {
            'drop_status': drop.get('status'),
            'drop_valid_artifact_count': drop.get('valid_artifact_count'),
            'drop_total_expected_artifact_count': drop.get('total_expected_artifact_count'),
            'drop_missing_or_invalid_artifact_count': drop.get('missing_or_invalid_artifact_count'),
            'ingestion_status': plan.get('status'),
            'ingestion_ready_copy_action_count': plan.get('ready_copy_action_count'),
            'ingestion_missing_or_invalid_copy_action_count': plan.get('missing_or_invalid_copy_action_count'),
            'controlled_copy_status': copy.get('status'),
            'controlled_copy_copied_file_count': copy.get('copied_file_count'),
            'controlled_copy_applied_copy_actions': copy.get('applied_copy_actions'),
            'apply_refused_returncode': refused_apply.get('returncode'),
        },
        'command_records': commands,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('production_blocker_closure_manifest_report', closure_path),
            evidence_entry('negative_drop_validator_report', drop_report),
            evidence_entry('negative_ingestion_plan_report', plan_report),
            evidence_entry('negative_controlled_copy_report', copy_report),
        ],
        'limitations': [
            'This negative self-test uses deliberately incomplete synthetic input.',
            'It proves bad external artifact drops stay NOT_READY and cannot be applied.',
            'It must not be used to clear real-CAD, SBEPV5, or fire-calibration blockers.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('negative_selftest_only') is True, 'negative self-test must be marked synthetic')
    require(data.get('does_not_clear_production_blockers') is True, 'negative self-test must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('drop_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP', 'negative drop unexpectedly ready')
    require(int(summary.get('drop_valid_artifact_count', -1)) < 14, 'negative drop validated all artifacts')
    require(summary.get('ingestion_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'negative ingestion unexpectedly ready')
    require(int(summary.get('ingestion_ready_copy_action_count', -1)) < 14, 'negative ingestion planned all copy actions')
    require(summary.get('controlled_copy_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY', 'negative controlled copy unexpectedly ready')
    require(summary.get('controlled_copy_applied_copy_actions') is False, 'negative controlled copy applied actions')
    require(int(summary.get('controlled_copy_copied_file_count', -1)) == 0, 'negative controlled copy wrote files')
    require(int(summary.get('apply_refused_returncode', 0)) != 0, 'negative apply was not refused')
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
        '# Engineering H2 External Artifact Gate Negative Synthetic Self-Test',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Quality Gates', '']
    for item in report['quality_gate_matrix']:
        lines.append(f"- `{item['name']}`: `{item['status']}`")
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
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_artifact_gate_negative_selftest VERIFY-PASS '
                f"json={args.verify_json} drop_status={summary['drop_status']} "
                f"apply_rc={summary['apply_refused_returncode']}"
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
            'engineering_h2_external_artifact_gate_negative_selftest PASS '
            f"json={out_json} md={out_md} drop_status={summary['drop_status']} "
            f"apply_rc={summary['apply_refused_returncode']}"
        )
        return 0
    except NegativeSelftestError as exc:
        print(f'engineering_h2_external_artifact_gate_negative_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
