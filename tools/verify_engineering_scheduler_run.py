#!/usr/bin/env python3
"""Verify completed scheduler-run evidence for an engineering H2 campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FAIL_MARKERS = (
    'Traceback',
    'RuntimeError',
    'Segmentation fault',
    'SIGSEGV',
    'Backtrace',
    'Unused ParmParse Variables',
)


class SchedulerRunError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SchedulerRunError(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return str(path)


def marker_values() -> list[str]:
    values = [str(Path.home()), os.environ.get('HOME', '')]
    for key, value in os.environ.items():
        upper_key = key.upper()
        if any(token in upper_key for token in ('PASS', 'PASSWORD', 'SECRET', 'TOKEN')):
            values.append(value)
    return sorted({value for value in values if value and len(value) > 3})


def no_private_markers(text: str) -> bool:
    return not any(marker in text for marker in marker_values())


def load_json(path: Path, repo: Path, checks: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    if not path.is_file():
        checks.append({'name': f'{label}_exists', 'status': 'MISSING', 'path': rel(path, repo)})
        return None
    raw = path.read_text(encoding='utf-8')
    if not no_private_markers(raw):
        checks.append({'name': f'{label}_private_markers', 'status': 'FAIL', 'path': rel(path, repo)})
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        checks.append({'name': f'{label}_json_parse', 'status': 'FAIL', 'path': rel(path, repo), 'detail': str(exc)})
        return None
    checks.append({'name': f'{label}_exists', 'status': 'PASS', 'path': rel(path, repo), 'sha256': sha256_text(raw)})
    return data


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str = '', **extra: Any) -> None:
    record: dict[str, Any] = {'name': name, 'status': 'PASS' if ok else 'FAIL'}
    if detail:
        record['detail'] = detail
    record.update(extra)
    checks.append(record)


def check_name_for_token(token: str) -> str:
    name = token.replace('#SBATCH', 'sbatch')
    name = re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_').lower()
    return f'scheduler_script_contains_{name}'


def verify_scheduler_manifest(manifest: dict[str, Any] | None, evidence_root: Path, repo: Path, checks: list[dict[str, Any]]) -> dict[str, int]:
    expected = {'ranks': 0, 'threads': 0}
    if manifest is None:
        return expected
    add_check(checks, 'scheduler_manifest_schema', manifest.get('schema_version') == 1)
    add_check(checks, 'scheduler_manifest_status', manifest.get('status') in {'READY', 'READY_WITH_WARNINGS'}, str(manifest.get('status')))
    resources = manifest.get('resources', {})
    expected['ranks'] = int(resources.get('ranks', 0) or 0)
    expected['threads'] = int(resources.get('threads_per_rank', 0) or 0)
    add_check(checks, 'scheduler_resources_positive', expected['ranks'] >= 1 and expected['threads'] >= 1, f"ranks={expected['ranks']} threads={expected['threads']}")
    script = manifest.get('script', {})
    script_path = repo / script.get('path', '')
    if script_path.is_file():
        script_text = script_path.read_text(encoding='utf-8')
        add_check(checks, 'scheduler_script_sha256', sha256_text(script_text) == script.get('sha256'), rel(script_path, repo))
        add_check(checks, 'scheduler_script_no_private_markers', no_private_markers(script_text), rel(script_path, repo))
        for token in ('#SBATCH --ntasks=', '#SBATCH --cpus-per-task=', 'write_engineering_runtime_affinity_manifest.py', 'run_engineering_h2_campaign.py', 'verify_engineering_scheduler_run.py'):
            add_check(checks, check_name_for_token(token), token in script_text, token)
    else:
        add_check(checks, 'scheduler_script_exists', False, rel(script_path, repo))
    plan = manifest.get('execution_plan', {}) if isinstance(manifest.get('execution_plan'), dict) else {}
    add_check(checks, 'scheduler_execution_plan_present', bool(plan))
    add_check(
        checks,
        'scheduler_execution_plan_tier',
        plan.get('plan_tier') == 'scheduler_managed_production_scout_candidate',
        str(plan.get('plan_tier', '')),
    )
    add_check(checks, 'scheduler_execution_plan_run_mode', plan.get('run_mode') == 'slurm_batch', str(plan.get('run_mode', '')))
    outputs = plan.get('expected_outputs', {}) if isinstance(plan.get('expected_outputs'), dict) else {}
    for key in ('evidence_root', 'campaign_run_root', 'runtime_affinity_manifest', 'campaign_run_summary', 'scheduler_run_report'):
        add_check(checks, f'scheduler_execution_plan_output_{key}', bool(outputs.get(key)), str(outputs.get(key, '')))
    closure = plan.get('closure_criteria', [])
    add_check(checks, 'scheduler_execution_plan_closure_criteria', isinstance(closure, list) and len(closure) >= 4, f'count={len(closure) if isinstance(closure, list) else "na"}')
    return expected



def local_executor_evidence_ok(
    runtime: dict[str, Any] | None,
    campaign: dict[str, Any] | None,
    expected: dict[str, int],
) -> bool:
    if runtime is None or campaign is None:
        return False
    if runtime.get('status') != 'PASS' or campaign.get('status') != 'PASS':
        return False
    requested = runtime.get('requested', {}) if isinstance(runtime.get('requested'), dict) else {}
    ranks = int(requested.get('ranks', 0) or 0)
    threads = int(requested.get('threads_per_rank', 0) or 0)
    if ranks != expected.get('ranks') or threads != expected.get('threads'):
        return False
    rows = runtime.get('mpi_probe', {}).get('rows', [])
    if not isinstance(rows, list) or len(rows) != ranks:
        return False
    cases = campaign.get('cases', [])
    if not isinstance(cases, list) or not cases:
        return False
    return all(
        case.get('status') == 'PASS'
        and not case.get('missing_required_files')
        and not case.get('log_failure_markers')
        and bool(case.get('required_file_hashes'))
        for case in cases
    )


def verify_submit_attempt(
    submit: dict[str, Any] | None,
    checks: list[dict[str, Any]],
    *,
    allow_local_executor_fallback: bool,
    local_executor_ok: bool,
) -> None:
    if submit is None:
        return
    add_check(checks, 'scheduler_submit_attempt_schema', submit.get('schema_version') == 1)
    status = str(submit.get('status', ''))
    add_check(
        checks,
        'scheduler_submit_attempt_status_known',
        status in {'SUBMITTED', 'CONTROLLER_UNAVAILABLE', 'POLICY_REJECTED', 'SUBMIT_FAILED', 'SBATCH_MISSING', 'NOT_RUN'},
        status,
    )
    attempt = submit.get('attempt', {}) if isinstance(submit.get('attempt'), dict) else {}
    add_check(checks, 'scheduler_submit_sbatch_available', bool(attempt.get('available')), str(attempt.get('executable', '')))
    accepted = status == 'SUBMITTED' and bool(attempt.get('job_id'))
    local_fallback = (
        allow_local_executor_fallback
        and status == 'CONTROLLER_UNAVAILABLE'
        and local_executor_ok
    )
    if allow_local_executor_fallback:
        add_check(
            checks,
            'scheduler_local_executor_fallback_evidence',
            local_fallback,
            (
                'local executor accepted because Slurm controller is unavailable and runtime/campaign evidence passed'
                if local_fallback else
                f'status={status} local_executor_ok={local_executor_ok}'
            ),
        )
    add_check(
        checks,
        'scheduler_submit_job_accepted',
        accepted or local_fallback,
        f"status={status} returncode={attempt.get('returncode')} detail={attempt.get('detail', '')}",
    )

def verify_runtime(runtime: dict[str, Any] | None, expected: dict[str, int], checks: list[dict[str, Any]], require_scheduler_env: bool) -> None:
    if runtime is None:
        return
    add_check(checks, 'runtime_status_pass', runtime.get('status') == 'PASS', str(runtime.get('status')))
    requested = runtime.get('requested', {})
    ranks = int(requested.get('ranks', 0) or 0)
    threads = int(requested.get('threads_per_rank', 0) or 0)
    add_check(checks, 'runtime_ranks_match_scheduler', ranks == expected.get('ranks'), f'runtime={ranks} scheduler={expected.get("ranks")}')
    add_check(checks, 'runtime_threads_match_scheduler', threads == expected.get('threads'), f'runtime={threads} scheduler={expected.get("threads")}')
    rows = runtime.get('mpi_probe', {}).get('rows', [])
    add_check(checks, 'runtime_probe_rows_match_ranks', isinstance(rows, list) and len(rows) == ranks, f'rows={len(rows) if isinstance(rows, list) else "na"} ranks={ranks}')
    if isinstance(rows, list):
        add_check(checks, 'runtime_probe_affinity_nonempty', all(int(row.get('affinity_count', 0) or 0) > 0 for row in rows))
    scheduler_env = runtime.get('scheduler_environment', {})
    if require_scheduler_env:
        add_check(checks, 'runtime_scheduler_environment_present', bool(scheduler_env), 'expected SLURM/PBS scheduler variables in scheduled run')


def verify_campaign(summary: dict[str, Any] | None, expected_suite: str, checks: list[dict[str, Any]]) -> None:
    if summary is None:
        return
    add_check(checks, 'campaign_status_pass', summary.get('status') == 'PASS', str(summary.get('status')))
    if expected_suite:
        add_check(checks, 'campaign_suite_match', summary.get('suite') == expected_suite, f"summary={summary.get('suite')} expected={expected_suite}")
    cases = summary.get('cases', [])
    add_check(checks, 'campaign_has_cases', isinstance(cases, list) and len(cases) >= 1, f'cases={len(cases) if isinstance(cases, list) else "na"}')
    if isinstance(cases, list):
        add_check(checks, 'campaign_all_cases_pass', all(case.get('status') == 'PASS' for case in cases), ','.join(str(case.get('status')) for case in cases))
        add_check(checks, 'campaign_no_missing_required_files', all(not case.get('missing_required_files') for case in cases))
        add_check(checks, 'campaign_no_log_failure_markers', all(not case.get('log_failure_markers') for case in cases))
        add_check(checks, 'campaign_required_hashes_present', all(case.get('required_file_hashes') for case in cases))


def scan_logs(evidence_root: Path, repo: Path, checks: list[dict[str, Any]]) -> None:
    logs = [p for p in evidence_root.rglob('*') if p.is_file() and p.suffix in {'.log', '.out', '.err'}]
    hits: list[str] = []
    nonfinite: list[str] = []
    private_hits: list[str] = []
    for path in sorted(logs):
        text = path.read_text(encoding='utf-8', errors='replace')
        rel_path = rel(path, repo)
        if not no_private_markers(text):
            private_hits.append(rel_path)
        for marker in FAIL_MARKERS:
            if marker in text:
                hits.append(f'{rel_path}:{marker}')
        if re.search(r'(?<![A-Za-z0-9_])(?:nan|inf)(?![A-Za-z0-9_])', text, re.IGNORECASE):
            nonfinite.append(rel_path)
    add_check(checks, 'scheduler_log_files_scanned', True, f'logs={len(logs)}')
    add_check(checks, 'scheduler_logs_no_failure_markers', not hits, '; '.join(hits[:20]))
    add_check(checks, 'scheduler_logs_no_nonfinite_tokens', not nonfinite, '; '.join(nonfinite[:20]))
    add_check(checks, 'scheduler_logs_no_private_markers', not private_hits, '; '.join(private_hits[:20]))


def summarize_status(checks: list[dict[str, Any]], allow_incomplete: bool) -> str:
    missing = any(check['status'] == 'MISSING' for check in checks)
    failed = any(check['status'] == 'FAIL' for check in checks)
    if not missing and not failed:
        return 'PASS'
    if allow_incomplete:
        return 'NOT_READY'
    return 'FAIL'



def verify_existing_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SchedulerRunError(f'missing scheduler run report: {path}')
    raw = path.read_text(encoding='utf-8')
    require(no_private_markers(raw), 'report contains machine-local/private strings')
    try:
        report = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SchedulerRunError(f'invalid scheduler run report JSON: {exc}') from exc
    require(report.get('schema_version') == 1, 'schema_version is not 1')
    require(report.get('status') in {'PASS', 'NOT_READY', 'FAIL'}, f"unexpected status {report.get('status')}")
    checks = report.get('checks')
    require(isinstance(checks, list) and checks, 'checks missing')
    statuses = {str(check.get('status')) for check in checks if isinstance(check, dict)}
    require(statuses <= {'PASS', 'FAIL', 'MISSING'}, f'unexpected check statuses {sorted(statuses)}')
    if report.get('status') == 'PASS':
        require(statuses == {'PASS'}, 'PASS report contains non-PASS checks')
    if report.get('status') == 'NOT_READY':
        require(bool(statuses & {'FAIL', 'MISSING'}), 'NOT_READY report must contain FAIL or MISSING checks')
    outputs = report.get('outputs', {})
    require(isinstance(outputs, dict), 'outputs is not an object')
    return report

def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering Scheduler Run Report',
        '',
        f"Status: `{report['status']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        f"Evidence root: `{report['evidence_root']}`",
        f"Suite: `{report['suite']}`",
        '',
        '## Checks',
        '',
        '| Check | Status | Detail |',
        '| --- | --- | --- |',
    ]
    for check in report['checks']:
        detail = str(check.get('detail') or check.get('path') or '')
        lines.append(f"| `{check['name']}` | `{check['status']}` | `{detail}` |")
    lines.extend(['', '## Limitations', ''])
    for item in report['limitations']:
        lines.append(f'- {item}')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', default='engineering_scheduler_h2_20260720')
    parser.add_argument('--verify-json', type=Path, help='Verify an existing scheduler-run report without rewriting it')
    parser.add_argument('--manifest-json', type=Path)
    parser.add_argument('--runtime-json', type=Path)
    parser.add_argument('--campaign-json', type=Path)
    parser.add_argument('--submit-attempt-json', type=Path)
    parser.add_argument('--output-json', type=Path)
    parser.add_argument('--output-md', type=Path)
    parser.add_argument('--allow-incomplete', action='store_true', help='Write NOT_READY reports instead of failing when scheduled outputs are missing')
    parser.add_argument('--no-require-scheduler-env', action='store_true', help='Do not require scheduler variables in the runtime-affinity manifest')
    parser.add_argument('--allow-local-executor-fallback', action='store_true', help='Accept audited local executor evidence when sbatch reports CONTROLLER_UNAVAILABLE')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repo_root()
    if args.verify_json:
        try:
            report = verify_existing_report(args.verify_json)
        except SchedulerRunError as exc:
            print(f'engineering_scheduler_run_report VERIFY-FAIL {exc}', file=sys.stderr)
            return 1
        print(
            'engineering_scheduler_run_report VERIFY-PASS ' +
            f"json={args.verify_json} status={report['status']} checks={len(report['checks'])}"
        )
        return 0
    evidence_root = repo / 'docs' / 'codex_audit' / 'evidence' / args.evidence_dir
    manifest_json = args.manifest_json or evidence_root / 'scheduler_campaign_manifest.json'
    runtime_json = args.runtime_json or evidence_root / 'runtime_affinity_manifest.json'
    campaign_json = args.campaign_json or evidence_root / 'campaign_run_summary.json'
    submit_attempt_json = args.submit_attempt_json or evidence_root / 'scheduler_submit_attempt.json'
    output_json = args.output_json or evidence_root / 'scheduler_run_report.json'
    output_md = args.output_md or evidence_root / 'scheduler_run_report.md'
    checks: list[dict[str, Any]] = []

    manifest = load_json(manifest_json, repo, checks, 'scheduler_manifest')
    expected = verify_scheduler_manifest(manifest, evidence_root, repo, checks)
    runtime = load_json(runtime_json, repo, checks, 'runtime_affinity_manifest')
    verify_runtime(runtime, expected, checks, not args.no_require_scheduler_env)
    campaign = load_json(campaign_json, repo, checks, 'campaign_run_summary')
    verify_campaign(campaign, str(manifest.get('suite', '') if manifest else ''), checks)
    submit_attempt = load_json(submit_attempt_json, repo, checks, 'scheduler_submit_attempt')
    local_executor_ok = local_executor_evidence_ok(runtime, campaign, expected)
    verify_submit_attempt(
        submit_attempt,
        checks,
        allow_local_executor_fallback=args.allow_local_executor_fallback,
        local_executor_ok=local_executor_ok,
    )
    if evidence_root.is_dir():
        scan_logs(evidence_root, repo, checks)
    else:
        add_check(checks, 'evidence_root_exists', False, rel(evidence_root, repo))

    status = summarize_status(checks, args.allow_incomplete)
    report = {
        'schema_version': 1,
        'status': status,
        'generated_at_utc': utc_now(),
        'evidence_root': rel(evidence_root, repo),
        'suite': manifest.get('suite', '') if manifest else '',
        'campaign': manifest.get('campaign', '') if manifest else '',
        'checks': checks,
        'outputs': {
            'scheduler_manifest': rel(manifest_json, repo),
            'runtime_affinity_manifest': rel(runtime_json, repo),
            'campaign_run_summary': rel(campaign_json, repo),
            'scheduler_submit_attempt': rel(submit_attempt_json, repo),
        },
        'limitations': [
            (
                'PASS proves presence and consistency of scheduler manifest, generated SLURM script hash, runtime-affinity evidence, campaign summary, required-output hashes, scanned scheduler logs, and an audited local executor fallback when the SLURM controller is unavailable.'
                if args.allow_local_executor_fallback else
                'PASS proves presence and consistency of scheduler manifest, generated SLURM script hash, runtime-affinity evidence, campaign summary, required-output hashes, and scanned scheduler logs.'
            ),
            'PASS does not by itself prove reference-data agreement, production mesh convergence, GPU scaling, or overnight stability beyond the scheduled campaign duration.',
            'NOT_READY means the scheduler package exists but one or more scheduled-run outputs are still missing, incomplete, or not accepted by the scheduler controller.',
        ],
    }
    raw = json.dumps(report, indent=2, sort_keys=True) + '\n'
    require(no_private_markers(raw), 'report contains machine-local/private strings')
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(raw, encoding='utf-8')
    write_markdown(report, output_md)

    print(
        'engineering_scheduler_run_report ' + status + ' ' +
        f'checks={len(checks)} json={rel(output_json, repo)} md={rel(output_md, repo)}'
    )
    return 0 if status == 'PASS' or (status == 'NOT_READY' and args.allow_incomplete) else 1


if __name__ == '__main__':
    raise SystemExit(main())
