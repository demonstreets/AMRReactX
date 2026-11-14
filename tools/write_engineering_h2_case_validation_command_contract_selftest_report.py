#!/usr/bin/env python3
"""Write/verify negative selftests for the engineering H2 case-validation command contract."""
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
STATUS = 'PASS-H2-CASE-VALIDATION-COMMAND-CONTRACT-SELFTEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_command_contract_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_command_contract_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_command_contract_selftest_report.md'
DEFAULT_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/'
    'h2_external_evidence_case_validation_plan.json'
)
DEFAULT_CONTRACT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_command_contract_20260724/'
    'h2_case_validation_command_contract_report.json'
)
CONTRACT_TOOL = Path('tools/write_engineering_h2_case_validation_command_contract_report.py')


class CommandContractSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CommandContractSelftestError(message)


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
        raise CommandContractSelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise CommandContractSelftestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def run_command(argv: list[str]) -> dict[str, Any]:
    result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        'argv': argv,
        'returncode': result.returncode,
        'stdout': result.stdout.strip(),
        'stderr': result.stderr.strip(),
    }


def mutate_plan(base: dict[str, Any], mutation: str) -> dict[str, Any]:
    plan = copy.deepcopy(base)
    campaigns = plan.get('case_validation_campaigns')
    require(isinstance(campaigns, list) and len(campaigns) == 4, 'base campaign count mismatch')
    if mutation == 'missing_script':
        commands = campaigns[0].get('commands_after_external_artifacts_pass')
        require(isinstance(commands, list) and commands, 'missing_script fixture has no commands')
        commands[0] = 'python3 tools/missing_case_validation_contract_selftest.py'
    elif mutation == 'unsupported_option':
        commands = campaigns[1].get('commands_after_external_artifacts_pass')
        require(isinstance(commands, list) and len(commands) >= 3, 'unsupported_option fixture has no target command')
        commands[2] = (
            'python3 tools/write_engineering_h2_reference_agreement_report.py '
            '--definitely-unsupported-contract-selftest-option'
        )
    else:
        raise CommandContractSelftestError(f'unknown mutation: {mutation}')
    plan['synthetic_selftest_only'] = True
    plan['does_not_clear_production_blockers'] = True
    return plan


def build_negative_case(root: Path, base_plan: dict[str, Any], name: str) -> dict[str, Any]:
    plan_path = root / 'fixtures' / f'{name}_case_validation_plan.json'
    out_json = root / f'{name}_contract_report_should_not_pass.json'
    out_md = root / f'{name}_contract_report_should_not_pass.md'
    write_json(plan_path, mutate_plan(base_plan, name))
    result = run_command(
        [
            sys.executable,
            str(CONTRACT_TOOL),
            '--case-validation-plan-report',
            str(plan_path),
            '--output-json',
            str(out_json),
            '--output-md',
            str(out_md),
        ]
    )
    require(result['returncode'] != 0, f'{name} negative fixture unexpectedly passed')
    return {
        'name': name,
        'fixture_plan': str(plan_path),
        'returncode': result['returncode'],
        'stdout_tail': result['stdout'][-1200:],
        'stderr_tail': result['stderr'][-1200:],
        'refused': True,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.output_json).parent
    plan_path = Path(args.case_validation_plan_report)
    contract_path = Path(args.command_contract_report)
    root.mkdir(parents=True, exist_ok=True)
    base_plan = load_json(plan_path)
    positive_verify = run_command([sys.executable, str(CONTRACT_TOOL), '--verify-json', str(contract_path)])
    require(positive_verify['returncode'] == 0, 'positive command contract verify failed')
    missing_script = build_negative_case(root, base_plan, 'missing_script')
    unsupported_option = build_negative_case(root, base_plan, 'unsupported_option')
    quality_gate_matrix = [
        {
            'name': 'positive_contract_verifies',
            'status': 'PASS' if positive_verify['returncode'] == 0 else 'FAIL',
            'evidence': positive_verify['stdout'] or positive_verify['stderr'],
            'gap': '',
        },
        {
            'name': 'missing_script_fixture_refused',
            'status': 'PASS' if missing_script['refused'] else 'FAIL',
            'evidence': f"returncode={missing_script['returncode']}",
            'gap': '',
        },
        {
            'name': 'unsupported_option_fixture_refused',
            'status': 'PASS' if unsupported_option['refused'] else 'FAIL',
            'evidence': f"returncode={unsupported_option['returncode']}",
            'gap': '',
        },
        {
            'name': 'selftest_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'fixture-only command-contract selftest',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Case Validation Command Contract Selftest',
        'case_validation_plan_report': str(plan_path),
        'command_contract_report': str(contract_path),
        'selftest_only': True,
        'does_not_clear_production_blockers': True,
        'summary': {
            'positive_verify_returncode': positive_verify['returncode'],
            'negative_case_count': 2,
            'negative_refused_count': 2,
            'missing_script_refused': missing_script['refused'],
            'unsupported_option_refused': unsupported_option['refused'],
        },
        'positive_verify': positive_verify,
        'negative_cases': [missing_script, unsupported_option],
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('engineering_h2_external_evidence_case_validation_plan_report', plan_path),
            evidence_entry('engineering_h2_case_validation_command_contract_report', contract_path),
            evidence_entry('engineering_h2_case_validation_command_contract_tool', CONTRACT_TOOL),
            evidence_entry('missing_script_negative_fixture_plan', Path(missing_script['fixture_plan'])),
            evidence_entry('unsupported_option_negative_fixture_plan', Path(unsupported_option['fixture_plan'])),
        ],
        'limitations': [
            'This selftest mutates isolated copies of the case-validation plan and does not run CFD validation campaigns.',
            'Negative fixture rejection proves command-contract gate behavior only and does not clear production blockers.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('selftest_only') is True, 'selftest_only missing')
    require(data.get('does_not_clear_production_blockers') is True, 'selftest must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('positive_verify_returncode', -1)) == 0, 'positive command contract did not verify')
    require(int(summary.get('negative_case_count', 0)) == 2, 'negative case count mismatch')
    require(int(summary.get('negative_refused_count', 0)) == 2, 'negative fixtures were not both refused')
    require(summary.get('missing_script_refused') is True, 'missing script fixture was not refused')
    require(summary.get('unsupported_option_refused') is True, 'unsupported option fixture was not refused')
    cases = data.get('negative_cases')
    require(isinstance(cases, list) and len(cases) == 2, 'negative cases mismatch')
    require(all(int(item.get('returncode', 0)) != 0 for item in cases if isinstance(item, dict)), 'negative case passed')
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
        '# Engineering H2 Case Validation Command Contract Selftest',
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
    lines += ['', '## Negative Cases', '']
    for item in report['negative_cases']:
        lines.append(f"- `{item['name']}`: returncode `{item['returncode']}`")
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
    parser.add_argument('--case-validation-plan-report', default=str(DEFAULT_PLAN))
    parser.add_argument('--command-contract-report', default=str(DEFAULT_CONTRACT_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_case_validation_command_contract_selftest VERIFY-PASS '
                f"json={args.verify_json} negative_refused={summary['negative_refused_count']}"
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
            'engineering_h2_case_validation_command_contract_selftest PASS '
            f"json={out_json} md={out_md} negative_refused={report['summary']['negative_refused_count']}"
        )
        return 0
    except CommandContractSelftestError as exc:
        print(f'engineering_h2_case_validation_command_contract_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
