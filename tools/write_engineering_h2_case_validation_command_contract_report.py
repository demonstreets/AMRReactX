#!/usr/bin/env python3
"""Write/verify the engineering H2 case-validation command contract report."""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-CASE-VALIDATION-COMMAND-CONTRACT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_command_contract_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_command_contract_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_command_contract_report.md'
DEFAULT_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/'
    'h2_external_evidence_case_validation_plan.json'
)


class CommandContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CommandContractError(message)


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
        raise CommandContractError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise CommandContractError(f'invalid JSON evidence {path}: {exc}') from exc
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


def run_help(script_path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(script_path), '--help'],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(result.returncode == 0, f'--help failed for {script_path}: {result.stderr or result.stdout}')
    return f'{result.stdout}\n{result.stderr}'


def option_tokens(argv: list[str]) -> list[str]:
    return [item for item in argv[2:] if item.startswith('--')]


def command_record(campaign_id: str, command: str) -> dict[str, Any]:
    argv = shlex.split(command)
    gaps: list[str] = []
    if not argv:
        return {
            'campaign_id': campaign_id,
            'command': command,
            'command_type': 'empty',
            'script_path': None,
            'options': [],
            'placeholder_count': command.count('<'),
            'status': 'FAIL',
            'gaps': ['empty_command'],
        }
    command_type = argv[0]
    script_path: Path | None = None
    options: list[str] = []
    help_checked = False
    if command_type == 'python3':
        if len(argv) < 2:
            gaps.append('missing_python_script')
        else:
            script_path = Path(argv[1])
            if not script_path.is_file():
                gaps.append(f'missing_script:{script_path}')
            else:
                options = option_tokens(argv)
                help_text = run_help(script_path)
                help_checked = True
                for option in options:
                    if option not in help_text:
                        gaps.append(f'unsupported_option:{script_path}:{option}')
    elif command_type == 'bash':
        if len(argv) < 2:
            gaps.append('missing_bash_script')
        else:
            script_path = Path(argv[1])
            if not script_path.is_file():
                gaps.append(f'missing_script:{script_path}')
    else:
        gaps.append(f'unsupported_command_type:{command_type}')
    return {
        'campaign_id': campaign_id,
        'command': command,
        'command_type': command_type,
        'script_path': str(script_path) if script_path else None,
        'options': options,
        'help_checked': help_checked,
        'placeholder_count': command.count('<'),
        'status': 'PASS' if not gaps else 'FAIL',
        'gaps': gaps,
    }


def collect_commands(plan: dict[str, Any]) -> list[dict[str, str]]:
    campaigns = plan.get('case_validation_campaigns')
    require(isinstance(campaigns, list) and campaigns, 'case_validation_campaigns missing')
    rows: list[dict[str, str]] = []
    for campaign in campaigns:
        require(isinstance(campaign, dict), 'campaign is not an object')
        campaign_id = str(campaign.get('campaign_id'))
        commands = campaign.get('commands_after_external_artifacts_pass')
        require(isinstance(commands, list) and commands, f'{campaign_id}: commands missing')
        for command in commands:
            rows.append({'campaign_id': campaign_id, 'command': str(command)})
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plan_path = Path(args.case_validation_plan_report)
    plan = load_json(plan_path)
    require(plan.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN', 'case validation plan did not PASS')
    commands = collect_commands(plan)
    command_records = [command_record(row['campaign_id'], row['command']) for row in commands]
    script_paths = sorted(
        {Path(str(item['script_path'])) for item in command_records if item.get('script_path')},
        key=str,
    )
    failed = [item for item in command_records if item.get('status') != 'PASS']
    python_commands = [item for item in command_records if item.get('command_type') == 'python3']
    bash_commands = [item for item in command_records if item.get('command_type') == 'bash']
    option_count = sum(len(item.get('options', [])) for item in command_records)
    placeholder_commands = [item for item in command_records if int(item.get('placeholder_count', 0)) > 0]
    quality_gate_matrix = [
        {
            'name': 'all_campaign_commands_have_supported_contracts',
            'status': 'PASS' if not failed else 'FAIL',
            'evidence': f'passed={len(command_records) - len(failed)}/{len(command_records)}',
            'gap': '; '.join(gap for item in failed for gap in item.get('gaps', [])),
        },
        {
            'name': 'python_command_options_exist_in_help',
            'status': 'PASS' if not failed else 'FAIL',
            'evidence': f'python_commands={len(python_commands)} option_checks={option_count}',
            'gap': '',
        },
        {
            'name': 'placeholder_commands_are_known_and_audited',
            'status': 'PASS' if len(placeholder_commands) == 2 else 'FAIL',
            'evidence': f'placeholder_commands={len(placeholder_commands)}',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Case Validation Command Contract',
        'case_validation_plan_report': str(plan_path),
        'summary': {
            'campaign_count': len(plan.get('case_validation_campaigns', [])),
            'command_count': len(command_records),
            'python_command_count': len(python_commands),
            'bash_command_count': len(bash_commands),
            'placeholder_command_count': len(placeholder_commands),
            'option_check_count': option_count,
            'failed_command_count': len(failed),
            'missing_or_unsupported_contract_count': sum(len(item.get('gaps', [])) for item in command_records),
        },
        'command_records': command_records,
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [evidence_entry('engineering_h2_external_evidence_case_validation_plan_report', plan_path)]
        + [evidence_entry(f'case_validation_command_script_{idx:02d}', path) for idx, path in enumerate(script_paths, 1)],
        'limitations': [
            'This report audits command availability and CLI contracts only; it does not execute CFD validation campaigns.',
            'Placeholder dataset commands remain blocked until external builder reports write real accepted dataset JSON files.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'report must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('campaign_count', 0)) == 4, 'campaign count mismatch')
    require(int(summary.get('command_count', 0)) == 17, 'command count mismatch')
    require(int(summary.get('python_command_count', 0)) == 12, 'python command count mismatch')
    require(int(summary.get('bash_command_count', 0)) == 5, 'bash command count mismatch')
    require(int(summary.get('placeholder_command_count', 0)) == 2, 'placeholder command count mismatch')
    require(int(summary.get('option_check_count', 0)) >= 4, 'option check count too small')
    require(int(summary.get('failed_command_count', -1)) == 0, 'one or more command contracts failed')
    require(int(summary.get('missing_or_unsupported_contract_count', -1)) == 0, 'command contract gaps remain')
    records = data.get('command_records')
    require(isinstance(records, list) and len(records) == 17, 'command_records mismatch')
    require(all(item.get('status') == 'PASS' for item in records if isinstance(item, dict)), 'failed command record')
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
        '# Engineering H2 Case Validation Command Contract',
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
    lines += ['', '## Commands', '']
    for item in report['command_records']:
        lines.append(f"- `{item['campaign_id']}`: `{item['command']}` -> `{item['status']}`")
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
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_case_validation_command_contract VERIFY-PASS '
                f"json={args.verify_json} commands={summary['command_count']} "
                f"options={summary['option_check_count']}"
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
            'engineering_h2_case_validation_command_contract PASS '
            f"json={out_json} md={out_md} commands={report['summary']['command_count']} "
            f"options={report['summary']['option_check_count']}"
        )
        return 0
    except CommandContractError as exc:
        print(f'engineering_h2_case_validation_command_contract FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
