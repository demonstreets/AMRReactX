#!/usr/bin/env python3
"""Write/verify negative selftests for the engineering H2 case-validation runner ledger."""
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
STATUS = 'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER-SELFTEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_runner_ledger_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_runner_ledger_selftest_report.md'
DEFAULT_LEDGER = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724/'
    'h2_case_validation_runner_ledger.json'
)
RUNNER = Path('tools/run_engineering_h2_external_evidence_case_validation_campaigns.py')


class RunnerLedgerSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RunnerLedgerSelftestError(message)


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
        raise RunnerLedgerSelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RunnerLedgerSelftestError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def run_verify(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(RUNNER), '--verify-ledger', str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        'argv': [sys.executable, str(RUNNER), '--verify-ledger', str(path)],
        'returncode': result.returncode,
        'stdout_tail': result.stdout.strip()[-1200:],
        'stderr_tail': result.stderr.strip()[-1200:],
    }


def first_command_result(base: dict[str, Any], status: str = 'PASS', returncode: int = 0) -> dict[str, Any]:
    command_rows = base.get('command_resolution')
    require(isinstance(command_rows, list) and command_rows, 'base ledger command rows missing')
    first = command_rows[0]
    require(isinstance(first, dict), 'base ledger first command row invalid')
    return {
        'campaign_id': first.get('campaign_id'),
        'raw_command': first.get('raw_command'),
        'resolved_command': first.get('resolved_command'),
        'argv': ['python3', 'tools/write_engineering_h2_real_cad_intake_preflight_report.py'],
        'started_utc': '2026-07-24T00:00:00Z',
        'finished_utc': '2026-07-24T00:00:01Z',
        'elapsed_seconds': 1.0,
        'returncode': returncode,
        'status': status,
    }


def mutate_ledger(base: dict[str, Any], mutation: str) -> dict[str, Any]:
    ledger = copy.deepcopy(base)
    summary = ledger.get('summary')
    require(isinstance(summary, dict), 'base ledger summary missing')
    if mutation == 'dryrun_with_command_results':
        ledger['command_results'] = [first_command_result(base)]
    elif mutation == 'pass_with_blocked_campaigns':
        ledger['status'] = 'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER'
        ledger['execute_requested'] = True
        summary['execute_requested'] = True
        summary['selected_blocked_campaign_count'] = 1
        summary['unresolved_command_count'] = 0
        summary['unresolved_placeholder_count'] = 0
        ledger['command_results'] = [first_command_result(base)]
    elif mutation == 'pass_with_nonzero_returncode':
        ledger['status'] = 'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER'
        ledger['execute_requested'] = True
        summary['execute_requested'] = True
        summary['selected_blocked_campaign_count'] = 0
        summary['unresolved_command_count'] = 0
        summary['unresolved_placeholder_count'] = 0
        ledger['command_results'] = [first_command_result(base, status='FAIL', returncode=7)]
    elif mutation == 'command_campaign_not_selected':
        command_rows = ledger.get('command_resolution')
        require(isinstance(command_rows, list) and command_rows, 'base ledger command rows missing')
        first = command_rows[0]
        require(isinstance(first, dict), 'base ledger first command row invalid')
        first['campaign_id'] = 'synthetic_unselected_campaign'
    else:
        raise RunnerLedgerSelftestError(f'unknown mutation: {mutation}')
    ledger['synthetic_selftest_only'] = True
    return ledger


def build_negative_case(root: Path, base: dict[str, Any], mutation: str) -> dict[str, Any]:
    fixture = root / 'fixtures' / f'{mutation}_ledger.json'
    write_json(fixture, mutate_ledger(base, mutation))
    result = run_verify(fixture)
    require(result['returncode'] != 0, f'{mutation} ledger fixture unexpectedly passed')
    return {
        'name': mutation,
        'fixture_ledger': str(fixture),
        'returncode': result['returncode'],
        'stdout_tail': result['stdout_tail'],
        'stderr_tail': result['stderr_tail'],
        'refused': True,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.output_json).parent
    root.mkdir(parents=True, exist_ok=True)
    ledger_path = Path(args.ledger)
    require(RUNNER.is_file(), f'missing runner: {RUNNER}')
    base = load_json(ledger_path)
    positive = run_verify(ledger_path)
    require(positive['returncode'] == 0, 'positive runner ledger verify failed')
    mutations = [
        'dryrun_with_command_results',
        'pass_with_blocked_campaigns',
        'pass_with_nonzero_returncode',
        'command_campaign_not_selected',
    ]
    negatives = [build_negative_case(root, base, mutation) for mutation in mutations]
    quality_gate_matrix = [
        {
            'name': 'positive_runner_ledger_verifies',
            'status': 'PASS' if positive['returncode'] == 0 else 'FAIL',
            'evidence': positive['stdout_tail'] or positive['stderr_tail'],
            'gap': '',
        },
        {
            'name': 'all_mutated_ledgers_are_refused',
            'status': 'PASS' if all(item['refused'] for item in negatives) else 'FAIL',
            'evidence': f"refused={sum(1 for item in negatives if item['refused'])}/{len(negatives)}",
            'gap': '',
        },
        {
            'name': 'selftest_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'fixture-only runner-ledger selftest',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Case Validation Runner Ledger Selftest',
        'runner': str(RUNNER),
        'runner_ledger': str(ledger_path),
        'selftest_only': True,
        'does_not_clear_production_blockers': True,
        'summary': {
            'positive_verify_returncode': positive['returncode'],
            'negative_case_count': len(negatives),
            'negative_refused_count': sum(1 for item in negatives if item['refused']),
            'dryrun_with_command_results_refused': negatives[0]['refused'],
            'pass_with_blocked_campaigns_refused': negatives[1]['refused'],
            'pass_with_nonzero_returncode_refused': negatives[2]['refused'],
            'command_campaign_not_selected_refused': negatives[3]['refused'],
        },
        'positive_verify': positive,
        'negative_cases': negatives,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('engineering_h2_case_validation_runner', RUNNER),
            evidence_entry('engineering_h2_case_validation_runner_ledger', ledger_path),
        ]
        + [evidence_entry(f'{item["name"]}_fixture_ledger', Path(item['fixture_ledger'])) for item in negatives],
        'limitations': [
            'This selftest mutates isolated copies of the runner ledger and does not run CFD validation campaigns.',
            'Negative fixture rejection proves ledger gate behavior only and does not clear production blockers.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('selftest_only') is True, 'selftest_only missing')
    require(data.get('does_not_clear_production_blockers') is True, 'selftest must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('positive_verify_returncode', -1)) == 0, 'positive ledger did not verify')
    require(int(summary.get('negative_case_count', 0)) == 4, 'negative case count mismatch')
    require(int(summary.get('negative_refused_count', 0)) == 4, 'negative fixtures were not all refused')
    for key in (
        'dryrun_with_command_results_refused',
        'pass_with_blocked_campaigns_refused',
        'pass_with_nonzero_returncode_refused',
        'command_campaign_not_selected_refused',
    ):
        require(summary.get(key) is True, f'{key} was not refused')
    negatives = data.get('negative_cases')
    require(isinstance(negatives, list) and len(negatives) == 4, 'negative cases mismatch')
    require(all(int(item.get('returncode', 0)) != 0 for item in negatives if isinstance(item, dict)), 'negative case passed')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'quality gate failed')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and len(entries) == 6, 'evidence_files mismatch')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence hash mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Case Validation Runner Ledger Selftest',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Negative Cases', '']
    for item in report['negative_cases']:
        lines.append(f"- `{item['name']}`: refused `{item['refused']}`, returncode `{item['returncode']}`")
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
    parser.add_argument('--ledger', default=str(DEFAULT_LEDGER))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_case_validation_runner_ledger_selftest VERIFY-PASS '
                f"json={args.verify_json} negative_refused={summary['negative_refused_count']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_case_validation_runner_ledger_selftest PASS '
            f"json={out_json} md={out_md} negative_refused={report['summary']['negative_refused_count']}"
        )
        return 0
    except RunnerLedgerSelftestError as exc:
        print(f'engineering_h2_case_validation_runner_ledger_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
