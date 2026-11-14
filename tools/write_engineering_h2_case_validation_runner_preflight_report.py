#!/usr/bin/env python3
"""Write/verify the engineering H2 case validation runner preflight report."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-CASE-VALIDATION-RUNNER-PREFLIGHT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_runner_preflight_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_runner_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_runner_preflight_report.md'
DEFAULT_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/'
    'h2_external_evidence_case_validation_plan.json'
)
DEFAULT_RUNNER = Path('tools/run_engineering_h2_external_evidence_case_validation_campaigns.py')
DEFAULT_EXTERNAL_PLUME_DATASET_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/'
    'sbepv5_d27_external_dataset_report.json'
)
DEFAULT_FIRE_CALIBRATION_DATASET_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/'
    'fire_calibration_dataset_report.json'
)
DEFAULT_PLACEHOLDER_FIXTURE_ROOT = DEFAULT_ROOT / 'placeholder_resolution_fixture'


class RunnerPreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RunnerPreflightError(message)


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
        raise RunnerPreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RunnerPreflightError(f'invalid JSON evidence {path}: {exc}') from exc
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
    result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        'argv': argv,
        'returncode': result.returncode,
        'stdout': result.stdout.strip(),
        'stderr': result.stderr.strip(),
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def build_placeholder_resolution_fixture(root: Path) -> dict[str, Path]:
    if root.exists():
        shutil.rmtree(root)
    plume_dataset = root / 'sbepv5_d27_external_plume_dataset.json'
    fire_dataset = root / 'h2_fire_consequence_calibration_dataset.json'
    plume_report = root / 'sbepv5_d27_external_dataset_report.json'
    fire_report = root / 'fire_calibration_dataset_report.json'
    write_json(
        plume_dataset,
        {
            'dataset_type': 'synthetic_runner_placeholder_resolution_selftest',
            'synthetic_selftest_only': True,
            'case': 'sbepv5_d27',
        },
    )
    write_json(
        fire_dataset,
        {
            'dataset_type': 'synthetic_runner_placeholder_resolution_selftest',
            'synthetic_selftest_only': True,
            'case': 'engineering_h2_fire_consequence',
        },
    )
    write_json(
        plume_report,
        {
            'schema_version': 1,
            'status': 'PASS-SBEPV5-D27-EXTERNAL-PLUME-DATASET',
            'external_dataset_json': str(plume_dataset),
            'synthetic_selftest_only': True,
            'does_not_clear_production_blockers': True,
        },
    )
    write_json(
        fire_report,
        {
            'schema_version': 1,
            'status': 'PASS-H2-FIRE-CALIBRATION-DATASET',
            'calibration_dataset_json': str(fire_dataset),
            'synthetic_selftest_only': True,
            'does_not_clear_production_blockers': True,
        },
    )
    return {
        'plume_dataset': plume_dataset,
        'fire_dataset': fire_dataset,
        'plume_report': plume_report,
        'fire_report': fire_report,
    }


def placeholder_positive_selftest(runner_path: Path, plan_path: Path, fixture_root: Path) -> dict[str, Any]:
    fixture = build_placeholder_resolution_fixture(fixture_root)
    result = run_command(
        [
            sys.executable,
            str(runner_path),
            '--plan',
            str(plan_path),
            '--external-plume-dataset-report',
            str(fixture['plume_report']),
            '--fire-calibration-dataset-report',
            str(fixture['fire_report']),
            '--json-commands',
        ]
    )
    require(result['returncode'] == 0, f'positive placeholder selftest failed: {result["stderr"] or result["stdout"]}')
    try:
        rows = json.loads(result['stdout'])
    except json.JSONDecodeError as exc:
        raise RunnerPreflightError(f'positive placeholder selftest did not emit JSON: {exc}') from exc
    require(isinstance(rows, list) and rows, 'positive placeholder selftest rows missing')
    raw_placeholder_commands = [item for item in rows if isinstance(item, dict) and item.get('raw_placeholder_count')]
    unresolved_rows = [item for item in rows if isinstance(item, dict) and item.get('unresolved_placeholders')]
    resolved_placeholder_count = sum(int(item.get('resolved_placeholder_count', 0)) for item in rows if isinstance(item, dict))
    return {
        'synthetic_selftest_only': True,
        'does_not_clear_production_blockers': True,
        'fixture_root': str(fixture_root),
        'fixture_files': {name: str(path) for name, path in fixture.items()},
        'runner_returncode': result['returncode'],
        'raw_placeholder_command_count': len(raw_placeholder_commands),
        'resolved_placeholder_count': resolved_placeholder_count,
        'unresolved_command_count': len(unresolved_rows),
        'all_placeholders_resolved': len(raw_placeholder_commands) == 2 and resolved_placeholder_count == 2 and not unresolved_rows,
        'command_resolution': rows,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plan_path = Path(args.case_validation_plan_report)
    runner_path = Path(args.runner)
    external_plume_dataset_path = Path(args.external_plume_dataset_report)
    fire_calibration_dataset_path = Path(args.fire_calibration_dataset_report)
    placeholder_fixture_root = Path(args.placeholder_fixture_root)
    require(runner_path.is_file(), f'missing runner: {runner_path}')
    plan = load_json(plan_path)
    plan_summary = plan.get('summary') if isinstance(plan.get('summary'), dict) else {}
    dryrun = run_command([sys.executable, str(runner_path), '--plan', str(plan_path), '--json-summary'])
    require(dryrun['returncode'] == 0, f'dry-run failed: {dryrun["stderr"] or dryrun["stdout"]}')
    try:
        dryrun_summary = json.loads(dryrun['stdout'])
    except json.JSONDecodeError as exc:
        raise RunnerPreflightError(f'dry-run did not emit JSON summary: {exc}') from exc
    command_resolution = run_command([sys.executable, str(runner_path), '--plan', str(plan_path), '--json-commands'])
    require(
        command_resolution['returncode'] == 0,
        f'command-resolution dry-run failed: {command_resolution["stderr"] or command_resolution["stdout"]}',
    )
    try:
        command_rows = json.loads(command_resolution['stdout'])
    except json.JSONDecodeError as exc:
        raise RunnerPreflightError(f'command-resolution dry-run did not emit JSON: {exc}') from exc
    require(isinstance(command_rows, list) and command_rows, 'command-resolution rows missing')
    ledger_json = DEFAULT_ROOT / 'blocked_execute_refusal_ledger.json'
    ledger_md = DEFAULT_ROOT / 'blocked_execute_refusal_ledger.md'
    execute_refusal = run_command(
        [
            sys.executable,
            str(runner_path),
            '--plan',
            str(plan_path),
            '--execute',
            '--confirm-token',
            'H2_CASE_VALIDATION_READY',
            '--ledger-json',
            str(ledger_json),
            '--ledger-md',
            str(ledger_md),
        ]
    )
    require(execute_refusal['returncode'] != 0, 'execute unexpectedly succeeded while campaigns are blocked')
    require(
        'not ready' in execute_refusal['stderr'].lower()
        or int(dryrun_summary.get('selected_blocked_campaign_count', 0)) >= 1,
        'execute refusal reason did not preserve blocked-campaign state',
    )
    refusal_ledger = load_json(ledger_json)
    refusal_ledger_summary = (
        refusal_ledger.get('summary') if isinstance(refusal_ledger.get('summary'), dict) else {}
    )
    require(refusal_ledger.get('status') == 'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER', 'refusal ledger status mismatch')
    require(refusal_ledger.get('execute_requested') is True, 'refusal ledger did not record execute request')
    require(refusal_ledger.get('does_not_clear_production_blockers') is True, 'refusal ledger must not clear blockers')
    require(not refusal_ledger.get('command_results'), 'refusal ledger unexpectedly records executed commands')
    require(
        int(refusal_ledger_summary.get('selected_blocked_campaign_count', 0)) >= 1,
        'refusal ledger did not preserve blocked campaign count',
    )
    positive_placeholder_selftest = placeholder_positive_selftest(runner_path, plan_path, placeholder_fixture_root)
    require(
        positive_placeholder_selftest['all_placeholders_resolved'] is True,
        'positive placeholder selftest did not resolve all placeholders',
    )
    quality_gate_matrix = [
        {
            'name': 'runner_dryrun_lists_all_campaigns',
            'status': 'PASS'
            if int(dryrun_summary.get('selected_campaign_count', 0)) == int(plan_summary.get('case_validation_campaign_count', 0))
            else 'MISSING',
            'evidence': f"runner={dryrun_summary.get('selected_campaign_count')} plan={plan_summary.get('case_validation_campaign_count')}",
            'gap': '',
        },
        {
            'name': 'runner_dryrun_preserves_blocked_campaigns',
            'status': 'PASS' if int(dryrun_summary.get('selected_blocked_campaign_count', 0)) >= 1 else 'MISSING',
            'evidence': f"blocked={dryrun_summary.get('selected_blocked_campaign_count')}",
            'gap': '',
        },
        {
            'name': 'runner_execute_refuses_when_blocked',
            'status': 'PASS' if execute_refusal['returncode'] != 0 else 'MISSING',
            'evidence': f"returncode={execute_refusal['returncode']}",
            'gap': '',
        },
        {
            'name': 'runner_writes_refusal_ledger_when_blocked',
            'status': 'PASS'
            if refusal_ledger.get('status') == 'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER'
            and not refusal_ledger.get('command_results')
            else 'MISSING',
            'evidence': (
                f"status={refusal_ledger.get('status')} "
                f"blocked={refusal_ledger_summary.get('selected_blocked_campaign_count')} "
                f"command_results={len(refusal_ledger.get('command_results', []))}"
            ),
            'gap': '',
        },
        {
            'name': 'runner_preserves_unresolved_placeholders_until_builder_outputs_exist',
            'status': 'PASS' if int(dryrun_summary.get('unresolved_command_count', 0)) >= 1 else 'MISSING',
            'evidence': (
                f"raw_placeholder_commands={dryrun_summary.get('raw_placeholder_command_count')} "
                f"resolved_placeholders={dryrun_summary.get('resolved_placeholder_count')} "
                f"unresolved_commands={dryrun_summary.get('unresolved_command_count')}"
            ),
            'gap': '',
        },
        {
            'name': 'runner_resolves_placeholders_from_ready_builder_reports',
            'status': 'PASS' if positive_placeholder_selftest['all_placeholders_resolved'] is True else 'MISSING',
            'evidence': (
                f"resolved={positive_placeholder_selftest['resolved_placeholder_count']} "
                f"unresolved={positive_placeholder_selftest['unresolved_command_count']}"
            ),
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Case Validation Runner Preflight',
        'case_validation_plan_report': str(plan_path),
        'runner': str(runner_path),
        'summary': {
            'runner_dryrun_returncode': dryrun['returncode'],
            'runner_execute_refusal_returncode': execute_refusal['returncode'],
            'selected_campaign_count': dryrun_summary.get('selected_campaign_count'),
            'selected_ready_campaign_count': dryrun_summary.get('selected_ready_campaign_count'),
            'selected_blocked_campaign_count': dryrun_summary.get('selected_blocked_campaign_count'),
            'raw_placeholder_command_count': dryrun_summary.get('raw_placeholder_command_count'),
            'resolved_placeholder_count': dryrun_summary.get('resolved_placeholder_count'),
            'unresolved_command_count': dryrun_summary.get('unresolved_command_count'),
            'unresolved_placeholder_count': dryrun_summary.get('unresolved_placeholder_count'),
            'execute_refused': execute_refusal['returncode'] != 0,
            'refusal_ledger_status': refusal_ledger.get('status'),
            'refusal_ledger_written': ledger_json.is_file() and ledger_md.is_file(),
            'refusal_ledger_command_result_count': len(refusal_ledger.get('command_results', [])),
            'positive_placeholder_selftest_all_resolved': positive_placeholder_selftest['all_placeholders_resolved'],
            'positive_placeholder_selftest_resolved_placeholder_count': positive_placeholder_selftest[
                'resolved_placeholder_count'
            ],
            'positive_placeholder_selftest_unresolved_command_count': positive_placeholder_selftest[
                'unresolved_command_count'
            ],
        },
        'dryrun': dryrun,
        'command_resolution': command_rows,
        'positive_placeholder_selftest': positive_placeholder_selftest,
        'execute_refusal': execute_refusal,
        'refusal_ledger': refusal_ledger,
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_h2_external_evidence_case_validation_plan_report', plan_path),
            evidence_entry('engineering_h2_case_validation_runner', runner_path),
            evidence_entry('engineering_h2_sbepv5_external_dataset_report', external_plume_dataset_path),
            evidence_entry('engineering_h2_fire_calibration_dataset_report', fire_calibration_dataset_path),
            evidence_entry('blocked_execute_refusal_ledger_json', ledger_json),
            evidence_entry('blocked_execute_refusal_ledger_md', ledger_md),
            evidence_entry('synthetic_placeholder_plume_dataset_report', placeholder_fixture_root / 'sbepv5_d27_external_dataset_report.json'),
            evidence_entry('synthetic_placeholder_fire_dataset_report', placeholder_fixture_root / 'fire_calibration_dataset_report.json'),
            evidence_entry('synthetic_placeholder_plume_dataset_json', placeholder_fixture_root / 'sbepv5_d27_external_plume_dataset.json'),
            evidence_entry('synthetic_placeholder_fire_dataset_json', placeholder_fixture_root / 'h2_fire_consequence_calibration_dataset.json'),
        ],
        'limitations': [
            'This preflight proves launcher guard behavior only; it does not execute CFD validation campaigns.',
            'Campaign execution remains blocked until real external evidence is accepted and the launcher receives explicit confirmation.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'preflight must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('runner_dryrun_returncode', -1)) == 0, 'runner dry-run did not pass')
    require(int(summary.get('selected_campaign_count', 0)) == 4, 'runner campaign count mismatch')
    require(int(summary.get('selected_ready_campaign_count', -1)) == 0, 'runner marked campaigns ready unexpectedly')
    require(int(summary.get('selected_blocked_campaign_count', 0)) == 4, 'runner blocked campaign count mismatch')
    require(int(summary.get('raw_placeholder_command_count', 0)) == 2, 'runner raw placeholder command count mismatch')
    require(int(summary.get('resolved_placeholder_count', -1)) == 0, 'runner resolved placeholders unexpectedly')
    require(int(summary.get('unresolved_command_count', 0)) == 2, 'runner unresolved command count mismatch')
    require(int(summary.get('unresolved_placeholder_count', 0)) == 2, 'runner unresolved placeholder count mismatch')
    require(summary.get('execute_refused') is True, 'runner execute was not refused')
    require(int(summary.get('runner_execute_refusal_returncode', 0)) != 0, 'runner execute returncode did not fail')
    require(summary.get('refusal_ledger_status') == 'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER', 'refusal ledger status mismatch')
    require(summary.get('refusal_ledger_written') is True, 'refusal ledger files were not written')
    require(int(summary.get('refusal_ledger_command_result_count', -1)) == 0, 'refusal ledger recorded executed commands')
    require(summary.get('positive_placeholder_selftest_all_resolved') is True, 'positive placeholder selftest failed')
    require(
        int(summary.get('positive_placeholder_selftest_resolved_placeholder_count', 0)) == 2,
        'positive placeholder selftest resolved count mismatch',
    )
    require(
        int(summary.get('positive_placeholder_selftest_unresolved_command_count', -1)) == 0,
        'positive placeholder selftest left unresolved commands',
    )
    command_rows = data.get('command_resolution')
    require(isinstance(command_rows, list) and len(command_rows) >= 10, 'command resolution rows missing')
    require(
        sum(1 for item in command_rows if isinstance(item, dict) and item.get('raw_placeholder_count')) == 2,
        'command resolution did not preserve two placeholder commands',
    )
    positive = data.get('positive_placeholder_selftest')
    require(isinstance(positive, dict), 'positive placeholder selftest missing')
    require(positive.get('synthetic_selftest_only') is True, 'positive placeholder selftest must be synthetic only')
    require(
        positive.get('does_not_clear_production_blockers') is True,
        'positive placeholder selftest must not clear blockers',
    )
    refusal_ledger = data.get('refusal_ledger')
    require(isinstance(refusal_ledger, dict), 'refusal ledger missing')
    require(refusal_ledger.get('status') == 'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER', 'invalid refusal ledger status')
    require(refusal_ledger.get('execute_requested') is True, 'refusal ledger execute flag mismatch')
    require(refusal_ledger.get('does_not_clear_production_blockers') is True, 'refusal ledger must not clear blockers')
    require(not refusal_ledger.get('command_results'), 'refusal ledger unexpectedly has command results')
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
        '# Engineering H2 Case Validation Runner Preflight',
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
    parser.add_argument('--case-validation-plan-report', default=str(DEFAULT_PLAN))
    parser.add_argument('--runner', default=str(DEFAULT_RUNNER))
    parser.add_argument('--external-plume-dataset-report', default=str(DEFAULT_EXTERNAL_PLUME_DATASET_REPORT))
    parser.add_argument('--fire-calibration-dataset-report', default=str(DEFAULT_FIRE_CALIBRATION_DATASET_REPORT))
    parser.add_argument('--placeholder-fixture-root', default=str(DEFAULT_PLACEHOLDER_FIXTURE_ROOT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_case_validation_runner_preflight VERIFY-PASS '
                f"json={args.verify_json} ready={summary['selected_ready_campaign_count']} "
                f"blocked={summary['selected_blocked_campaign_count']}"
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
            'engineering_h2_case_validation_runner_preflight PASS '
            f"json={out_json} md={out_md} ready={report['summary']['selected_ready_campaign_count']} "
            f"blocked={report['summary']['selected_blocked_campaign_count']}"
        )
        return 0
    except RunnerPreflightError as exc:
        print(f'engineering_h2_case_validation_runner_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
