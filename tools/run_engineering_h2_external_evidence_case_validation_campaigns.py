#!/usr/bin/env python3
"""Guarded launcher for engineering H2 external-evidence validation campaigns."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/'
    'h2_external_evidence_case_validation_plan.json'
)
DEFAULT_EXTERNAL_PLUME_DATASET_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/'
    'sbepv5_d27_external_dataset_report.json'
)
DEFAULT_FIRE_CALIBRATION_DATASET_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/'
    'fire_calibration_dataset_report.json'
)
DEFAULT_LEDGER_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724')
DEFAULT_LEDGER_JSON = DEFAULT_LEDGER_ROOT / 'h2_case_validation_runner_ledger.json'
DEFAULT_LEDGER_MD = DEFAULT_LEDGER_ROOT / 'h2_case_validation_runner_ledger.md'
CONFIRM_TOKEN = 'H2_CASE_VALIDATION_READY'
LEDGER_STATUSES = {
    'DRYRUN-H2-CASE-VALIDATION-RUNNER-LEDGER',
    'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER',
    'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER',
    'FAIL-H2-CASE-VALIDATION-RUNNER-LEDGER',
}
PLACEHOLDER_FIELDS = {
    '<generated_external_plume_dataset_json>': (
        'external_dataset_json',
        'PASS-SBEPV5-D27-EXTERNAL-PLUME-DATASET',
    ),
    '<generated_fire_calibration_dataset_json>': (
        'calibration_dataset_json',
        'PASS-H2-FIRE-CALIBRATION-DATASET',
    ),
}


class RunnerError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RunnerError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise RunnerError(f'missing case validation plan: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RunnerError(f'invalid case validation plan {path}: {exc}') from exc
    require(isinstance(data, dict), f'case validation plan is not an object: {path}')
    return data


def load_optional_json(path: Path) -> dict[str, Any] | None:
    try:
        return load_json(path)
    except RunnerError:
        return None


def selected_campaigns(plan: dict[str, Any], campaign_id: str) -> list[dict[str, Any]]:
    campaigns = plan.get('case_validation_campaigns')
    require(isinstance(campaigns, list) and campaigns, 'case_validation_campaigns missing')
    items = [item for item in campaigns if isinstance(item, dict)]
    if campaign_id == 'all':
        return items
    selected = [item for item in items if item.get('campaign_id') == campaign_id]
    require(selected, f'unknown campaign: {campaign_id}')
    return selected


def placeholder_report_paths(args: argparse.Namespace) -> dict[str, Path]:
    return {
        '<generated_external_plume_dataset_json>': Path(args.external_plume_dataset_report),
        '<generated_fire_calibration_dataset_json>': Path(args.fire_calibration_dataset_report),
    }


def placeholder_resolution(report_paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    resolution: dict[str, dict[str, Any]] = {}
    for placeholder, (field, ready_status) in PLACEHOLDER_FIELDS.items():
        report_path = report_paths[placeholder]
        report = load_optional_json(report_path)
        value = report.get(field) if isinstance(report, dict) else None
        ready = bool(
            isinstance(report, dict)
            and report.get('status') == ready_status
            and isinstance(value, str)
            and value
            and Path(value).is_file()
        )
        resolution[placeholder] = {
            'report': str(report_path),
            'field': field,
            'expected_status': ready_status,
            'report_status': report.get('status') if isinstance(report, dict) else None,
            'resolved_path': value if isinstance(value, str) else None,
            'resolved_path_exists': Path(value).is_file() if isinstance(value, str) and value else False,
            'ready': ready,
        }
    return resolution


def resolve_command(command: str, resolution: dict[str, dict[str, Any]]) -> tuple[str, list[str], int]:
    text = command
    unresolved: list[str] = []
    resolved_count = 0
    for placeholder, item in resolution.items():
        if placeholder not in text:
            continue
        if item.get('ready') is True and item.get('resolved_path'):
            text = text.replace(placeholder, str(item['resolved_path']))
            resolved_count += 1
        else:
            unresolved.append(placeholder)
    return text, unresolved, resolved_count


def command_resolution(campaigns: list[dict[str, Any]], report_paths: dict[str, Path]) -> list[dict[str, Any]]:
    resolution = placeholder_resolution(report_paths)
    rows: list[dict[str, Any]] = []
    for campaign in campaigns:
        commands = campaign.get('commands_after_external_artifacts_pass')
        require(isinstance(commands, list) and commands, f"{campaign.get('campaign_id')} commands missing")
        for command in commands:
            text = str(command)
            resolved, unresolved, resolved_count = resolve_command(text, resolution)
            raw_placeholder_count = sum(text.count(item) for item in PLACEHOLDER_FIELDS)
            rows.append(
                {
                    'campaign_id': campaign.get('campaign_id'),
                    'raw_command': text,
                    'resolved_command': resolved,
                    'raw_placeholder_count': raw_placeholder_count,
                    'resolved_placeholder_count': resolved_count,
                    'unresolved_placeholders': unresolved,
                    'ready': not unresolved,
                }
            )
    return rows


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def unresolved_commands(campaigns: list[dict[str, Any]], report_paths: dict[str, Path]) -> list[str]:
    unresolved: list[str] = []
    for row in command_resolution(campaigns, report_paths):
        for placeholder in row['unresolved_placeholders']:
            unresolved.append(f"{row['campaign_id']}::{placeholder}::{row['raw_command']}")
    return unresolved


def build_summary(
    plan: dict[str, Any],
    campaigns: list[dict[str, Any]],
    execute: bool,
    report_paths: dict[str, Path],
) -> dict[str, Any]:
    ready = [item for item in campaigns if item.get('ready_to_execute_after_controlled_copy') is True]
    blocked = [item for item in campaigns if item.get('ready_to_execute_after_controlled_copy') is not True]
    resolved_rows = command_resolution(campaigns, report_paths)
    unresolved = [
        placeholder
        for row in resolved_rows
        for placeholder in row['unresolved_placeholders']
    ]
    return {
        'plan_status': plan.get('status'),
        'plan_schema_version': plan.get('schema_version'),
        'selected_campaign_count': len(campaigns),
        'selected_ready_campaign_count': len(ready),
        'selected_blocked_campaign_count': len(blocked),
        'execute_requested': execute,
        'campaign_ids': [item.get('campaign_id') for item in campaigns],
        'blocked_campaign_ids': [item.get('campaign_id') for item in blocked],
        'raw_placeholder_command_count': sum(1 for row in resolved_rows if row['raw_placeholder_count'] > 0),
        'resolved_placeholder_count': sum(int(row['resolved_placeholder_count']) for row in resolved_rows),
        'unresolved_command_count': sum(1 for row in resolved_rows if row['unresolved_placeholders']),
        'unresolved_placeholder_count': len(unresolved),
    }


def run_campaigns(campaigns: list[dict[str, Any]], report_paths: dict[str, Path]) -> tuple[list[dict[str, Any]], str | None]:
    results: list[dict[str, Any]] = []
    for campaign in campaigns:
        commands = campaign.get('commands_after_external_artifacts_pass')
        require(isinstance(commands, list) and commands, f"{campaign.get('campaign_id')} commands missing")
        for command in commands:
            resolved, unresolved, _ = resolve_command(str(command), placeholder_resolution(report_paths))
            require(not unresolved, f'unresolved placeholders for {campaign.get("campaign_id")}: {", ".join(unresolved)}')
            argv = shlex.split(resolved)
            require(argv, f'empty command for {campaign.get("campaign_id")}')
            print(f"[engineering-h2-case-runner] {' '.join(argv)}", flush=True)
            started = utc_now()
            t0 = time.monotonic()
            result = subprocess.run(argv, check=False)
            elapsed = time.monotonic() - t0
            row = {
                'campaign_id': campaign.get('campaign_id'),
                'raw_command': str(command),
                'resolved_command': resolved,
                'argv': argv,
                'started_utc': started,
                'finished_utc': utc_now(),
                'elapsed_seconds': round(elapsed, 6),
                'returncode': result.returncode,
                'status': 'PASS' if result.returncode == 0 else 'FAIL',
            }
            results.append(row)
            if result.returncode != 0:
                return results, f'command failed rc={result.returncode}: {command}'
    return results, None


def build_ledger(
    *,
    plan_path: Path,
    campaign_id: str,
    execute: bool,
    summary: dict[str, Any],
    command_rows: list[dict[str, Any]],
    report_paths: dict[str, Path],
    status: str,
    refusal_reason: str | None,
    command_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        'schema_version': 1,
        'status': status,
        'generated_utc': utc_now(),
        'plan': str(plan_path),
        'campaign_selector': campaign_id,
        'execute_requested': execute,
        'confirm_token_required': CONFIRM_TOKEN,
        'refusal_reason': refusal_reason,
        'summary': summary,
        'placeholder_reports': {key: str(path) for key, path in report_paths.items()},
        'command_resolution': command_rows,
        'command_results': command_results,
        'does_not_clear_production_blockers': True,
        'limitations': [
            'This ledger records guarded campaign launch decisions and command return codes only.',
            'It does not certify plume, CAD, fire, or detonation agreement by itself.',
            'Production blockers remain open until accepted external artifacts are ingested and validation metrics pass.',
        ],
    }


def write_ledger(report: dict[str, Any], json_path: Path | None, md_path: Path | None) -> None:
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        summary = report.get('summary', {})
        lines = [
            '# Engineering H2 Case Validation Runner Ledger',
            '',
            f"Status: `{report.get('status')}`",
            f"Generated UTC: `{report.get('generated_utc')}`",
            f"Campaign selector: `{report.get('campaign_selector')}`",
            f"Execute requested: `{report.get('execute_requested')}`",
            f"Selected campaigns: `{summary.get('selected_campaign_count')}`",
            f"Ready campaigns: `{summary.get('selected_ready_campaign_count')}`",
            f"Blocked campaigns: `{summary.get('selected_blocked_campaign_count')}`",
            f"Unresolved commands: `{summary.get('unresolved_command_count')}`",
            f"Refusal reason: `{report.get('refusal_reason') or 'none'}`",
            '',
            '## Command Resolution',
        ]
        for row in report.get('command_resolution', []):
            lines.append(
                f"- `{row.get('campaign_id')}` ready=`{row.get('ready')}` "
                f"unresolved=`{row.get('unresolved_placeholders')}` command=`{row.get('resolved_command')}`"
            )
        lines.extend(['', '## Command Results'])
        if report.get('command_results'):
            for row in report['command_results']:
                lines.append(
                    f"- `{row.get('campaign_id')}` status=`{row.get('status')}` "
                    f"returncode=`{row.get('returncode')}` elapsed_s=`{row.get('elapsed_seconds')}`"
                )
        else:
            lines.append('- No commands executed.')
        lines.extend(['', '## Limitations'])
        for item in report.get('limitations', []):
            lines.append(f'- {item}')
        md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def validate_ledger_object(data: dict[str, Any]) -> None:
    require(data.get('schema_version') == 1, 'ledger schema_version mismatch')
    status = str(data.get('status', ''))
    require(status in LEDGER_STATUSES, f'invalid ledger status: {status}')
    require(data.get('confirm_token_required') == CONFIRM_TOKEN, 'ledger confirm token mismatch')
    require(data.get('does_not_clear_production_blockers') is True, 'ledger must not clear production blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'ledger summary missing')
    require(int(summary.get('selected_campaign_count', 0)) >= 1, 'ledger selected campaign count missing')
    require(summary.get('execute_requested') == data.get('execute_requested'), 'ledger execute flag mismatch')
    command_rows = data.get('command_resolution')
    require(isinstance(command_rows, list) and command_rows, 'ledger command resolution missing')
    campaign_ids = {str(item) for item in summary.get('campaign_ids', []) if str(item)}
    require(campaign_ids, 'ledger campaign ids missing')
    unresolved_rows = 0
    for row in command_rows:
        require(isinstance(row, dict), 'ledger command-resolution row is not an object')
        require(str(row.get('campaign_id', '')) in campaign_ids, 'ledger command row campaign not selected')
        require(str(row.get('raw_command', '')).strip(), 'ledger command row missing raw command')
        require(str(row.get('resolved_command', '')).strip(), 'ledger command row missing resolved command')
        require(isinstance(row.get('unresolved_placeholders'), list), 'ledger unresolved placeholders must be a list')
        if row.get('unresolved_placeholders'):
            unresolved_rows += 1
    require(
        unresolved_rows == int(summary.get('unresolved_command_count', -1)),
        'ledger unresolved command count mismatch',
    )
    results = data.get('command_results')
    require(isinstance(results, list), 'ledger command_results missing')
    if status == 'DRYRUN-H2-CASE-VALIDATION-RUNNER-LEDGER':
        require(data.get('execute_requested') is False, 'DRYRUN ledger marked execute requested')
        require(data.get('refusal_reason') is None, 'DRYRUN ledger has refusal reason')
        require(not results, 'DRYRUN ledger recorded command results')
    elif status == 'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER':
        require(data.get('execute_requested') is True, 'REFUSED ledger missing execute request')
        require(str(data.get('refusal_reason', '')).strip(), 'REFUSED ledger missing refusal reason')
        require(not results, 'REFUSED ledger recorded command results')
    elif status == 'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER':
        require(data.get('execute_requested') is True, 'PASS ledger missing execute request')
        require(data.get('refusal_reason') is None, 'PASS ledger has refusal reason')
        require(int(summary.get('selected_blocked_campaign_count', -1)) == 0, 'PASS ledger has blocked campaigns')
        require(int(summary.get('unresolved_command_count', -1)) == 0, 'PASS ledger has unresolved commands')
        require(results, 'PASS ledger has no command results')
        for row in results:
            require(isinstance(row, dict), 'PASS command result row is not an object')
            require(str(row.get('campaign_id', '')) in campaign_ids, 'PASS result campaign not selected')
            require(row.get('status') == 'PASS', 'PASS ledger contains non-PASS command result')
            require(int(row.get('returncode', -1)) == 0, 'PASS ledger contains nonzero returncode')
    else:
        require(data.get('execute_requested') is True, 'FAIL ledger missing execute request')
        require(results, 'FAIL ledger has no command results')
        require(
            any(isinstance(row, dict) and row.get('status') == 'FAIL' for row in results)
            or str(data.get('refusal_reason', '')).strip(),
            'FAIL ledger has neither failed command result nor failure reason',
        )


def verify_ledger(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_ledger_object(data)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', default=str(DEFAULT_PLAN))
    parser.add_argument('--campaign', default='all')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--confirm-token', default='')
    parser.add_argument('--json-summary', action='store_true')
    parser.add_argument('--json-commands', action='store_true')
    parser.add_argument('--external-plume-dataset-report', default=str(DEFAULT_EXTERNAL_PLUME_DATASET_REPORT))
    parser.add_argument('--fire-calibration-dataset-report', default=str(DEFAULT_FIRE_CALIBRATION_DATASET_REPORT))
    parser.add_argument('--ledger-json', default='')
    parser.add_argument('--ledger-md', default='')
    parser.add_argument('--verify-ledger', default='')
    args = parser.parse_args(argv)
    try:
        if args.verify_ledger:
            ledger = verify_ledger(Path(args.verify_ledger))
            summary = ledger['summary']
            print(
                'engineering_h2_case_validation_runner_ledger VERIFY-PASS '
                f"json={args.verify_ledger} status={ledger['status']} "
                f"campaigns={summary['selected_campaign_count']} "
                f"results={len(ledger['command_results'])}"
            )
            return 0
        plan_path = Path(args.plan)
        plan = load_json(plan_path)
        require(plan.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN', 'case validation plan did not PASS')
        campaigns = selected_campaigns(plan, args.campaign)
        report_paths = placeholder_report_paths(args)
        summary = build_summary(plan, campaigns, args.execute, report_paths)
        command_rows = command_resolution(campaigns, report_paths)
        ledger_json = Path(args.ledger_json) if args.ledger_json else None
        ledger_md = Path(args.ledger_md) if args.ledger_md else None
        if args.json_summary:
            print(json.dumps(summary, indent=2, sort_keys=True))
        elif args.json_commands:
            print(json.dumps(command_rows, indent=2, sort_keys=True))
        else:
            print(
                'engineering_h2_case_validation_runner '
                f"campaigns={summary['selected_campaign_count']} "
                f"ready={summary['selected_ready_campaign_count']} "
                f"blocked={summary['selected_blocked_campaign_count']} "
                f"execute={args.execute}"
            )
        if not args.execute:
            write_ledger(
                build_ledger(
                    plan_path=plan_path,
                    campaign_id=args.campaign,
                    execute=args.execute,
                    summary=summary,
                    command_rows=command_rows,
                    report_paths=report_paths,
                    status='DRYRUN-H2-CASE-VALIDATION-RUNNER-LEDGER',
                    refusal_reason=None,
                    command_results=[],
                ),
                ledger_json,
                ledger_md,
            )
            return 0
        refusal_reason = None
        if args.confirm_token != CONFIRM_TOKEN:
            refusal_reason = f'execute requires --confirm-token {CONFIRM_TOKEN}'
        elif summary['selected_blocked_campaign_count'] != 0:
            refusal_reason = 'one or more selected campaigns are not ready'
        unresolved = unresolved_commands(campaigns, report_paths)
        if refusal_reason is None and unresolved:
            refusal_reason = 'one or more selected commands still contain unresolved placeholders'
        if refusal_reason is not None:
            write_ledger(
                build_ledger(
                    plan_path=plan_path,
                    campaign_id=args.campaign,
                    execute=args.execute,
                    summary=summary,
                    command_rows=command_rows,
                    report_paths=report_paths,
                    status='REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER',
                    refusal_reason=refusal_reason,
                    command_results=[],
                ),
                ledger_json,
                ledger_md,
            )
            raise RunnerError(refusal_reason)
        command_results, failure = run_campaigns(campaigns, report_paths)
        write_ledger(
            build_ledger(
                plan_path=plan_path,
                campaign_id=args.campaign,
                execute=args.execute,
                summary=summary,
                command_rows=command_rows,
                report_paths=report_paths,
                status='PASS-H2-CASE-VALIDATION-RUNNER-LEDGER' if failure is None else 'FAIL-H2-CASE-VALIDATION-RUNNER-LEDGER',
                refusal_reason=failure,
                command_results=command_results,
            ),
            ledger_json,
            ledger_md,
        )
        require(failure is None, str(failure))
        return 0
    except RunnerError as exc:
        print(f'engineering_h2_case_validation_runner REFUSED {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
