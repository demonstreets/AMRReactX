#!/usr/bin/env python3
"""Run and summarize curated engineering H2 CFD validation campaigns."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CampaignCase:
    name: str
    suite: str
    script: str
    log_env: str
    required_files: tuple[str, ...]
    description: str
    default_timeout_s: int
    extra_env: tuple[tuple[str, str], ...] = ()


CASES: tuple[CampaignCase, ...] = (
    CampaignCase(
        name='open-domain',
        suite='h2-core',
        script='tools/codex_smoke_engineering_h2_leak_open_domain.sh',
        log_env='CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR',
        required_files=('validation.log', 'profile_validation.log', 'hazard_summary.log', 'hazard_planes.csv', 'hazard_timeseries.csv'),
        description='Open-domain flammable H2 leak plume and hazard diagnostics.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='release-rate',
        suite='h2-core',
        script='tools/codex_smoke_engineering_h2_leak_open_domain_release_rate.sh',
        log_env='CODEX_H2_LEAK_RELEASE_LOG_DIR',
        required_files=('release_rate_summary.csv',),
        description='Low/high release-rate response and cloud-strength trend.',
        default_timeout_s=1200,
    ),
    CampaignCase(
        name='crosswind',
        suite='h2-core',
        script='tools/codex_smoke_engineering_h2_leak_open_domain_crosswind.sh',
        log_env='CODEX_H2_LEAK_CROSSWIND_LOG_DIR',
        required_files=('crosswind_summary.csv',),
        description='Baseline/crosswind lateral plume response.',
        default_timeout_s=1200,
    ),
    CampaignCase(
        name='low-wind',
        suite='h2-core',
        script='tools/codex_smoke_engineering_h2_leak_open_domain_low_wind.sh',
        log_env='CODEX_H2_LEAK_LOW_WIND_LOG_DIR',
        required_files=('low_wind_summary.csv',),
        description='Low ambient wind source-region retention response.',
        default_timeout_s=1200,
    ),
    CampaignCase(
        name='pressure-orifice',
        suite='h2-source-physics',
        script='tools/codex_smoke_engineering_h2_leak_pressure_orifice.sh',
        log_env='CODEX_H2_LEAK_PRESSURE_ORIFICE_LOG_DIR',
        required_files=('validation.log',),
        description='Pressure-orifice mass-flow source model.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='real-gas-orifice',
        suite='h2-source-physics',
        script='tools/codex_smoke_engineering_h2_leak_real_gas_orifice.sh',
        log_env='CODEX_H2_LEAK_REAL_GAS_ORIFICE_LOG_DIR',
        required_files=('validation.log',),
        description='Compressibility-factor pressure-orifice scaling.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='tank-blowdown',
        suite='h2-source-physics',
        script='tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh',
        log_env='CODEX_H2_LEAK_TANK_BLOWDOWN_LOG_DIR',
        required_files=('validation.log',),
        description='Transient tank inventory and pressure-depletion source.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='real-gas-tank-blowdown',
        suite='h2-source-physics',
        script='tools/codex_smoke_engineering_h2_leak_real_gas_tank_blowdown.sh',
        log_env='CODEX_H2_LEAK_REAL_GAS_TANK_BLOWDOWN_LOG_DIR',
        required_files=('validation.log',),
        description='Real-gas tank-blowdown source scaling.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='pipe-loss',
        suite='h2-source-physics',
        script='tools/codex_smoke_engineering_h2_leak_pipe_loss.sh',
        log_env='CODEX_H2_LEAK_PIPE_LOSS_LOG_DIR',
        required_files=('validation.log',),
        description='Equivalent pipe/valve loss pressure reduction.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='linepack-blowdown',
        suite='h2-source-physics',
        script='tools/codex_smoke_engineering_h2_leak_linepack_blowdown.sh',
        log_env='CODEX_H2_LEAK_LINEPACK_BLOWDOWN_LOG_DIR',
        required_files=('validation.log',),
        description='Lumped linepack inventory depletion.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='linepack-valve-schedule',
        suite='h2-source-physics',
        script='tools/codex_smoke_engineering_h2_leak_linepack_valve_schedule.sh',
        log_env='CODEX_H2_LEAK_LINEPACK_VALVE_LOG_DIR',
        required_files=('validation.log',),
        description='Delayed/ramped linepack valve schedule.',
        default_timeout_s=900,
    ),
    CampaignCase(
        name='tank-farm',
        suite='h2-geometry',
        script='tools/codex_smoke_engineering_h2_leak_tank_farm.sh',
        log_env='CODEX_H2_LEAK_TANK_FARM_LOG_DIR',
        required_files=('tank_farm_summary.csv',),
        description='Compact three-cylinder tank-farm EB union smoke.',
        default_timeout_s=1200,
    ),
    CampaignCase(
        name='stl-multifile',
        suite='h2-geometry',
        script='tools/codex_smoke_engineering_h2_leak_stl_multifile_obstacle.sh',
        log_env='CODEX_H2_LEAK_STL_MULTIFILE_LOG_DIR',
        required_files=('stl_obstacle_summary.csv',),
        description='Merged multi-file STL obstacle dispersion smoke.',
        default_timeout_s=1200,
    ),
    CampaignCase(
        name='stl-perfile-transform',
        suite='h2-geometry',
        script='tools/codex_smoke_engineering_h2_leak_stl_perfile_transform.sh',
        log_env='CODEX_H2_LEAK_STL_PERFILE_LOG_DIR',
        required_files=('stl_obstacle_summary.csv',),
        description='Per-file STL transform and merged geometry smoke.',
        default_timeout_s=1200,
    ),
    CampaignCase(
        name='plan-amr-mpi-rank-sweep',
        suite='h2-amr-mpi',
        script='tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_rank_sweep.sh',
        log_env='CODEX_H2_LEAK_PLAN_AMR_MPI_RANK_SWEEP_LOG_DIR',
        required_files=('rank_sweep_summary.csv',),
        description='2/4-rank dynamic plan-AMR MPI hazard consistency.',
        default_timeout_s=2400,
    ),
    CampaignCase(
        name='plan-amr-mpi-reduced-long',
        suite='h2-production-scout',
        script='tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh',
        log_env='CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LOG_DIR',
        required_files=('reduced_long_summary.csv', 'engineering_case_report.json', 'engineering_case_report.md'),
        description='4-rank 200-step dynamic plan-AMR MPI reduced-long stability scout.',
        default_timeout_s=3600,
    ),
)

SUITE_ALIASES: dict[str, tuple[str, ...]] = {
    'h2-core': ('h2-core',),
    'h2-source-physics': ('h2-source-physics',),
    'h2-geometry': ('h2-geometry',),
    'h2-amr-mpi': ('h2-amr-mpi',),
    'h2-production-scout': ('h2-production-scout',),
    'engineering-h2-core': ('h2-core', 'h2-source-physics', 'h2-geometry'),
    'engineering-h2-production': ('h2-core', 'h2-source-physics', 'h2-geometry', 'h2-amr-mpi', 'h2-production-scout'),
}

FAIL_MARKERS = (
    'FAIL',
    'Traceback',
    'RuntimeError',
    'Segmentation fault',
    'SIGSEGV',
    'Backtrace',
    'Unused ParmParse Variables',
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def repo_metadata(repo: Path) -> dict[str, Any]:
    def git(args: list[str]) -> str:
        try:
            return subprocess.check_output(['git', *args], cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ''

    return {
        'branch': git(['rev-parse', '--abbrev-ref', 'HEAD']),
        'commit': git(['rev-parse', 'HEAD']),
        'dirty_short': git(['status', '--short']),
    }


def select_cases(suite: str, only: list[str]) -> list[CampaignCase]:
    known = {case.name: case for case in CASES}
    if only:
        missing = [name for name in only if name not in known]
        if missing:
            raise SystemExit('unknown case(s): ' + ', '.join(missing))
        return [known[name] for name in only]
    if suite not in SUITE_ALIASES:
        raise SystemExit(f'unknown suite {suite!r}; use --list-suites')
    suites = set(SUITE_ALIASES[suite])
    return [case for case in CASES if case.suite in suites]


def validate_case_definition(repo: Path, case: CampaignCase) -> None:
    script = repo / case.script
    if not script.is_file():
        raise SystemExit(f'{case.name}: missing script {script}')
    if not os.access(script, os.X_OK):
        raise SystemExit(f'{case.name}: script is not executable {script}')
    if not case.required_files:
        raise SystemExit(f'{case.name}: no required output files configured')


def scan_case_logs(case_root: Path) -> list[str]:
    hits: list[str] = []
    for log in sorted(case_root.rglob('*.log')):
        text = log.read_text(encoding='utf-8', errors='replace')
        rel = log.relative_to(case_root)
        for marker in FAIL_MARKERS:
            if marker in text:
                hits.append(f'{rel}:{marker}')
    return hits


def collect_required_files(case_root: Path, required: tuple[str, ...]) -> tuple[list[dict[str, str]], list[str]]:
    files: list[dict[str, str]] = []
    missing: list[str] = []
    for rel in required:
        path = case_root / rel
        if path.is_file():
            files.append({'path': str(path), 'sha256': sha256_file(path)})
        else:
            missing.append(str(path))
    return files, missing


def run_case(repo: Path, output_root: Path, case: CampaignCase, args: argparse.Namespace) -> dict[str, Any]:
    case_root = output_root / 'cases' / case.name
    case_root.mkdir(parents=True, exist_ok=True)
    log_path = case_root / 'campaign_case.log'
    env = os.environ.copy()
    env[case.log_env] = str(case_root)
    env['JOBS'] = str(args.jobs)
    env['RUN_TIMEOUT'] = str(args.run_timeout_s)
    for key, value in case.extra_env:
        env[key] = value
    if args.reuse_existing and case.name == 'plan-amr-mpi-reduced-long':
        env['CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_REUSE_EXISTING'] = 'TRUE'
    command = ['bash', case.script]
    record: dict[str, Any] = {
        'name': case.name,
        'suite': case.suite,
        'description': case.description,
        'script': case.script,
        'log_env': case.log_env,
        'root': str(case_root),
        'command': command,
        'required_files': list(case.required_files),
        'started_at_utc': utc_now(),
    }
    if args.dry_run:
        record.update({'status': 'DRY-RUN', 'returncode': None, 'duration_s': 0.0, 'case_log': str(log_path)})
        return record

    timeout_s = args.case_timeout_s if args.case_timeout_s is not None else case.default_timeout_s
    start = time.monotonic()
    try:
        with log_path.open('w', encoding='utf-8') as log_fh:
            proc = subprocess.run(
                command,
                cwd=repo,
                env=env,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout_s,
            )
        returncode: int | None = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        with log_path.open('a', encoding='utf-8') as log_fh:
            log_fh.write(f'\nengineering_h2_campaign TIMEOUT case={case.name} timeout_s={timeout_s}\n')
        returncode = None
        timed_out = True
    duration_s = time.monotonic() - start
    files, missing = collect_required_files(case_root, case.required_files)
    log_hits = scan_case_logs(case_root)
    status = 'PASS'
    if timed_out:
        status = 'TIMEOUT'
    elif returncode != 0:
        status = 'FAIL'
    elif missing:
        status = 'FAIL'
    elif log_hits:
        status = 'FAIL'
    record.update({
        'status': status,
        'returncode': returncode,
        'duration_s': duration_s,
        'finished_at_utc': utc_now(),
        'timeout_s': timeout_s,
        'case_log': str(log_path),
        'required_file_hashes': files,
        'missing_required_files': missing,
        'log_failure_markers': log_hits[:50],
    })
    return record


def build_summary(campaign: str, suite: str, output_root: Path, cases: list[dict[str, Any]], dry_run: bool, repo: Path) -> dict[str, Any]:
    status = 'DRY-RUN' if dry_run else ('PASS' if all(case['status'] == 'PASS' for case in cases) else 'FAIL')
    return {
        'schema_version': 1,
        'campaign': campaign,
        'suite': suite,
        'status': status,
        'generated_at_utc': utc_now(),
        'output_root': str(output_root),
        'host': platform.node(),
        'python': sys.version.split()[0],
        'repo': repo_metadata(repo),
        'case_count': len(cases),
        'cases': cases,
        'evidence_tier': 'workflow_regression',
        'campaign_scale': 'engineering_regression_smoke',
        'production_campaign': False,
        'production_size_mesh_campaign': False,
        'full_duration_campaign': False,
        'limitations': [
            'Campaign runner proves orchestration, logging, return-code capture, and required-output collection for selected engineering H2 cases.',
            'It does not by itself prove production-scale CFD accuracy, real CAD cleanup, scheduler affinity, overnight stability, fire heat-release validation, or reference-data agreement.',
        ],
    }


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Engineering H2 Campaign: {summary['campaign']}",
        '',
        f"Status: `{summary['status']}`",
        f"Suite: `{summary['suite']}`",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        f"Output root: `{summary['output_root']}`",
        f"Host: `{summary['host']}`",
        f"Repo commit: `{summary['repo'].get('commit', '')}`",
        f"Case count: `{summary['case_count']}`",
        f"Evidence tier: `{summary.get('evidence_tier', 'workflow_regression')}`",
        f"Campaign scale: `{summary.get('campaign_scale', 'engineering_regression_smoke')}`",
        f"Production campaign: `{summary.get('production_campaign', False)}`",
        f"Production-size mesh campaign: `{summary.get('production_size_mesh_campaign', False)}`",
        f"Full-duration campaign: `{summary.get('full_duration_campaign', False)}`",
        '',
        '## Cases',
        '',
        '| Case | Suite | Status | Duration s | Root |',
        '| --- | --- | --- | ---: | --- |',
    ]
    for case in summary['cases']:
        duration = case.get('duration_s')
        duration_text = '' if duration is None else f'{float(duration):.2f}'
        lines.append(f"| `{case['name']}` | `{case['suite']}` | `{case['status']}` | {duration_text} | `{case['root']}` |")
    lines.extend(['', '## Limitations', ''])
    for item in summary['limitations']:
        lines.append(f'- {item}')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', default='engineering-h2-production-readiness', help='Campaign label')
    parser.add_argument('--suite', default='engineering-h2-core', help='Suite name or alias')
    parser.add_argument('--only', action='append', default=[], help='Run only this case name; repeatable')
    parser.add_argument('--output-root', type=Path, default=None, help='Campaign output root')
    parser.add_argument('--dry-run', action='store_true', help='Validate selected cases and write summary without running CFD cases')
    parser.add_argument('--reuse-existing', action='store_true', help='Allow wrappers that support reuse to reuse existing case evidence')
    parser.add_argument('--jobs', type=int, default=int(os.environ.get('JOBS', '4')), help='Build/run job count passed to wrappers')
    parser.add_argument('--run-timeout-s', type=int, default=int(os.environ.get('RUN_TIMEOUT', '1800')), help='RUN_TIMEOUT passed to shell wrappers')
    parser.add_argument('--case-timeout-s', type=int, default=None, help='Python subprocess timeout per case; default is case-specific')
    parser.add_argument('--output-json', type=Path, default=None, help='Summary JSON path')
    parser.add_argument('--output-md', type=Path, default=None, help='Summary Markdown path')
    parser.add_argument('--list-cases', action='store_true', help='Print configured cases and exit')
    parser.add_argument('--list-suites', action='store_true', help='Print configured suites and exit')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    if args.list_suites:
        for name, suites in sorted(SUITE_ALIASES.items()):
            print(f'{name}: {",".join(suites)}')
        return 0
    if args.list_cases:
        for case in CASES:
            print(f'{case.name}\t{case.suite}\t{case.script}\t{case.description}')
        return 0
    selected = select_cases(args.suite, args.only)
    for case in selected:
        validate_case_definition(repo, case)
    output_root = args.output_root or Path('/tmp') / f'codex_engineering_h2_campaign_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    case_records = []
    for case in selected:
        print(f'engineering_h2_campaign START case={case.name} suite={case.suite}')
        record = run_case(repo, output_root, case, args)
        case_records.append(record)
        print(f"engineering_h2_campaign {record['status']} case={case.name} root={record['root']}")
        if not args.dry_run and record['status'] != 'PASS':
            break
    summary = build_summary(args.campaign, args.suite, output_root, case_records, args.dry_run, repo)
    output_json = args.output_json or output_root / 'campaign_run_summary.json'
    output_md = args.output_md or output_root / 'campaign_run_summary.md'
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_markdown(summary, output_md)
    print(f"engineering_h2_campaign {summary['status']} suite={args.suite} cases={len(case_records)} json={output_json} md={output_md}")
    return 0 if summary['status'] in ('PASS', 'DRY-RUN') else 1


if __name__ == '__main__':
    raise SystemExit(main())
