#!/usr/bin/env python3
"""Write/verify the engineering H2 case-validation-plan gate selftest report."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN-SELFTEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_evidence_case_validation_plan_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_evidence_case_validation_plan_selftest_report.md'
DEFAULT_ACCEPTANCE_WORKSHEET = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724/'
    'h2_external_evidence_acceptance_worksheet.json'
)


class CaseValidationPlanSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CaseValidationPlanSelftestError(message)


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
        raise CaseValidationPlanSelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise CaseValidationPlanSelftestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def write_fixture(base: dict[str, Any], path: Path, all_valid: bool) -> None:
    fixture = copy.deepcopy(base)
    rows = fixture.get('worksheet_rows')
    require(isinstance(rows, list) and len(rows) == 14, 'base worksheet rows mismatch')
    for row in rows:
        require(isinstance(row, dict), 'worksheet row is not an object')
        row['current_present'] = all_valid
        row['current_valid'] = all_valid
        row['current_gaps'] = [] if all_valid else row.get('current_gaps', [])
    summary = fixture.setdefault('summary', {})
    require(isinstance(summary, dict), 'worksheet summary is not an object')
    summary['valid_artifact_row_count'] = 14 if all_valid else 0
    summary['missing_or_invalid_artifact_row_count'] = 0 if all_valid else 14
    summary['drop_valid_artifact_count'] = 14 if all_valid else 0
    summary['ready_for_external_evidence_acceptance'] = bool(all_valid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fixture, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def run_tool(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def build_case(root: Path, name: str, worksheet_path: Path) -> dict[str, Any]:
    plan_json = root / name / 'h2_external_evidence_case_validation_plan.json'
    plan_md = root / name / 'h2_external_evidence_case_validation_plan.md'
    cmd = [
        sys.executable,
        'tools/write_engineering_h2_external_evidence_case_validation_plan.py',
        '--external-evidence-acceptance-worksheet-report',
        str(worksheet_path),
        '--output-json',
        str(plan_json),
        '--output-md',
        str(plan_md),
    ]
    result = run_tool(cmd)
    require(result.returncode == 0, f'{name} plan generation failed: {result.stderr or result.stdout}')
    verify = run_tool(
        [
            sys.executable,
            'tools/write_engineering_h2_external_evidence_case_validation_plan.py',
            '--verify-json',
            str(plan_json),
        ]
    )
    require(verify.returncode == 0, f'{name} plan verify failed: {verify.stderr or verify.stdout}')
    plan = load_json(plan_json)
    summary = plan.get('summary') if isinstance(plan.get('summary'), dict) else {}
    return {
        'name': name,
        'worksheet_fixture': str(worksheet_path),
        'plan_json': str(plan_json),
        'plan_md': str(plan_md),
        'generation_stdout': result.stdout.strip(),
        'verify_stdout': verify.stdout.strip(),
        'campaign_count': summary.get('case_validation_campaign_count'),
        'ready_campaign_count': summary.get('ready_case_validation_campaign_count'),
        'integrated_replay_ready': summary.get('integrated_replay_ready'),
        'worksheet_valid_artifact_row_count': summary.get('worksheet_valid_artifact_row_count'),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    base_path = Path(args.external_evidence_acceptance_worksheet_report)
    root = Path(args.root)
    base = load_json(base_path)
    negative_fixture = root / 'fixtures' / 'missing_artifacts_worksheet.json'
    positive_fixture = root / 'fixtures' / 'all_valid_worksheet.json'
    write_fixture(base, negative_fixture, all_valid=False)
    write_fixture(base, positive_fixture, all_valid=True)
    negative = build_case(root, 'negative_missing_artifacts', negative_fixture)
    positive = build_case(root, 'positive_all_valid_artifacts', positive_fixture)
    require(int(negative['campaign_count']) == 4, 'negative campaign count mismatch')
    require(int(negative['ready_campaign_count']) == 0, 'negative fixture opened campaigns')
    require(negative['integrated_replay_ready'] is False, 'negative fixture opened integrated replay')
    require(int(positive['campaign_count']) == 4, 'positive campaign count mismatch')
    require(int(positive['ready_campaign_count']) == 4, 'positive fixture did not open all campaigns')
    require(positive['integrated_replay_ready'] is True, 'positive fixture did not open integrated replay')
    quality_gate_matrix = [
        {
            'name': 'negative_fixture_keeps_campaigns_blocked',
            'status': 'PASS',
            'evidence': f"ready={negative['ready_campaign_count']} integrated={negative['integrated_replay_ready']}",
            'gap': '',
        },
        {
            'name': 'positive_fixture_opens_all_campaigns',
            'status': 'PASS',
            'evidence': f"ready={positive['ready_campaign_count']} integrated={positive['integrated_replay_ready']}",
            'gap': '',
        },
        {
            'name': 'selftest_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'fixture-only reports are written under isolated selftest root',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Evidence Case Validation Plan Selftest',
        'external_evidence_acceptance_worksheet_report': str(base_path),
        'selftest_root': str(root),
        'selftest_only': True,
        'does_not_clear_production_blockers': True,
        'summary': {
            'negative_campaign_count': negative['campaign_count'],
            'negative_ready_campaign_count': negative['ready_campaign_count'],
            'negative_integrated_replay_ready': negative['integrated_replay_ready'],
            'positive_campaign_count': positive['campaign_count'],
            'positive_ready_campaign_count': positive['ready_campaign_count'],
            'positive_integrated_replay_ready': positive['integrated_replay_ready'],
        },
        'cases': [negative, positive],
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('engineering_h2_external_evidence_acceptance_worksheet_report', base_path),
            evidence_entry('negative_missing_artifacts_plan', Path(negative['plan_json'])),
            evidence_entry('positive_all_valid_artifacts_plan', Path(positive['plan_json'])),
        ],
        'limitations': [
            'This is a fixture-only gate selftest; it does not provide real external data or run CFD campaigns.',
            'The positive fixture proves campaign gating logic only and must not be interpreted as production readiness.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('selftest_only') is True, 'selftest_only missing')
    require(data.get('does_not_clear_production_blockers') is True, 'selftest must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('negative_campaign_count', 0)) == 4, 'negative campaign count mismatch')
    require(int(summary.get('negative_ready_campaign_count', -1)) == 0, 'negative fixture opened campaigns')
    require(summary.get('negative_integrated_replay_ready') is False, 'negative fixture opened integrated replay')
    require(int(summary.get('positive_campaign_count', 0)) == 4, 'positive campaign count mismatch')
    require(int(summary.get('positive_ready_campaign_count', -1)) == 4, 'positive fixture did not open campaigns')
    require(summary.get('positive_integrated_replay_ready') is True, 'positive fixture did not open integrated replay')
    cases = data.get('cases')
    require(isinstance(cases, list) and len(cases) == 2, 'selftest cases mismatch')
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
        '# Engineering H2 External Evidence Case Validation Plan Selftest',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Cases', '']
    for item in report['cases']:
        lines.append(
            f"- `{item['name']}`: campaigns `{item['campaign_count']}`, "
            f"ready `{item['ready_campaign_count']}`, integrated `{item['integrated_replay_ready']}`"
        )
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
    parser.add_argument('--external-evidence-acceptance-worksheet-report', default=str(DEFAULT_ACCEPTANCE_WORKSHEET))
    parser.add_argument('--root', default=str(DEFAULT_ROOT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_evidence_case_validation_plan_selftest VERIFY-PASS '
                f"json={args.verify_json} negative_ready={summary['negative_ready_campaign_count']} "
                f"positive_ready={summary['positive_ready_campaign_count']}"
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
            'engineering_h2_external_evidence_case_validation_plan_selftest PASS '
            f"json={out_json} md={out_md} negative_ready={report['summary']['negative_ready_campaign_count']} "
            f"positive_ready={report['summary']['positive_ready_campaign_count']}"
        )
        return 0
    except CaseValidationPlanSelftestError as exc:
        print(f'engineering_h2_external_evidence_case_validation_plan_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
