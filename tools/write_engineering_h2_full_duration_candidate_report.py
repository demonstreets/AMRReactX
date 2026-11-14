#!/usr/bin/env python3
"""Write/verify an engineering H2 full-duration campaign candidate report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PASS_STATUS = 'PASS-FULL-DURATION-CANDIDATE'
PASS_EXECUTED_STATUS = 'PASS-FULL-DURATION-EXECUTED'
NOT_READY_STATUS = 'NOT_READY-FULL-DURATION-CANDIDATE'

DEFAULT_PRODUCTION_MESH_CAMPAIGN = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.json'
)
DEFAULT_STABILITY_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json'
)
DEFAULT_DISK_CLEANUP_AUDIT = Path(
    'docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/disk_cleanup_audit_report.json'
)
DEFAULT_WRAPPER = Path('tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh')
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/'
    'full_duration_candidate_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/'
    'full_duration_candidate_report.md'
)


class ReportError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReportError(message)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


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
        raise ReportError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON in {path}: {exc}') from exc
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


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def inspect_executed_run(
    run_root: Path,
    args: argparse.Namespace,
    target_plotfiles: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Return executed-run evidence when the target log dir contains a complete run."""
    summary_csv = run_root / 'reduced_long_summary.csv'
    case_report_path = run_root / 'engineering_case_report.json'
    if not summary_csv.exists() and not case_report_path.exists():
        return None, []

    import csv

    gaps: list[str] = []
    evidence: dict[str, Any] = {
        'run_root': str(run_root),
        'summary_csv': str(summary_csv),
        'engineering_case_report': str(case_report_path),
    }

    if not summary_csv.is_file():
        gaps.append('executed_run_reduced_long_summary_missing')
        return None, gaps
    if not case_report_path.is_file():
        gaps.append('executed_run_engineering_case_report_missing')
        return None, gaps

    try:
        with summary_csv.open(newline='', encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
    except Exception as exc:
        gaps.append(f'executed_run_summary_unreadable:{exc}')
        return None, gaps
    if len(rows) != 2:
        gaps.append('executed_run_summary_expected_baseline_and_amr_rows')
        return None, gaps

    by_case = {str(row.get('case')): row for row in rows}
    for case_name in ('baseline', 'amr'):
        row = by_case.get(case_name)
        if row is None:
            gaps.append(f'executed_run_{case_name}_summary_missing')
            continue
        if int(row.get('ranks', 0) or 0) != args.target_ranks:
            gaps.append(f'executed_run_{case_name}_rank_mismatch')
        if int(row.get('max_step', 0) or 0) != args.target_max_step:
            gaps.append(f'executed_run_{case_name}_max_step_mismatch')
        if int(row.get('plot_int', 0) or 0) != args.target_plot_int:
            gaps.append(f'executed_run_{case_name}_plot_int_mismatch')
        if int(row.get('plotfiles', 0) or 0) < target_plotfiles:
            gaps.append(f'executed_run_{case_name}_plotfiles_below_target')
        if int(row.get('final_step', 0) or 0) != args.target_max_step:
            gaps.append(f'executed_run_{case_name}_final_step_mismatch')
        if case_name == 'amr' and int(row.get('finest_level', 0) or 0) < 1:
            gaps.append('executed_run_amr_finest_level_missing')
        if float(row.get('final_cloud_volume', 0.0) or 0.0) <= 0.0:
            gaps.append(f'executed_run_{case_name}_final_cloud_missing')
        if int(row.get('final_flammable_planes', 0) or 0) < 1:
            gaps.append(f'executed_run_{case_name}_flammable_planes_missing')

    try:
        case_report = load_json(case_report_path)
    except ReportError as exc:
        gaps.append(f'executed_run_case_report_invalid:{exc}')
        return None, gaps
    if case_report.get('status') != 'PASS':
        gaps.append('executed_run_case_report_not_pass')
    if int(case_report.get('schema_version', 0) or 0) != 1:
        gaps.append('executed_run_case_report_schema_mismatch')

    for rel in (
        'baseline/validation.log',
        'baseline/mpi_validation.log',
        'baseline/hazard_timeseries.log',
        'amr/validation.log',
        'amr/mpi_validation.log',
        'amr/hazard_timeseries.log',
        'plan_amr_compare_summary.csv',
        'amr_overhead_summary.csv',
    ):
        path = run_root / rel
        if not path.is_file():
            gaps.append(f'executed_run_required_evidence_missing:{rel}')
            continue
        if path.suffix == '.log':
            text = read_text(path)
            if 'PASS' not in text:
                gaps.append(f'executed_run_required_log_without_pass:{rel}')

    evidence.update({
        'baseline': by_case.get('baseline', {}),
        'amr': by_case.get('amr', {}),
        'case_report_status': case_report.get('status'),
        'case_report_generated_at_utc': case_report.get('generated_at_utc'),
    })
    return (evidence if not gaps else None), gaps


def git_value(args: list[str]) -> str:
    try:
        return subprocess.check_output(['git', *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ''


def disk_free_bytes(path: Path) -> int:
    usage = shutil.disk_usage(path)
    return int(usage.free)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    mesh_campaign_path = Path(args.production_mesh_campaign_report)
    stability_path = Path(args.stability_scout_report)
    disk_audit_path = Path(args.disk_cleanup_audit_report)
    wrapper = Path(args.wrapper)
    mesh_campaign = load_json(mesh_campaign_path)
    stability = load_json(stability_path)
    disk_audit = load_json(disk_audit_path)
    stability_summary = stability.get('summary', {}) if isinstance(stability.get('summary'), dict) else {}
    mesh_summary = mesh_campaign.get('summary', {}) if isinstance(mesh_campaign.get('summary'), dict) else {}
    disk_requirement = (
        disk_audit.get('full_duration_disk_requirement', {})
        if isinstance(disk_audit.get('full_duration_disk_requirement'), dict) else {}
    )
    disk_summary = disk_audit.get('summary', {}) if isinstance(disk_audit.get('summary'), dict) else {}

    blockers: list[str] = []
    valid_mesh_campaign_statuses = {
        'PASS-PRODUCTION-MESH-CAMPAIGN-SCOUT',
        'PASS-PRODUCTION-MESH-FULL-DURATION-CAMPAIGN',
    }
    if mesh_campaign.get('status') not in valid_mesh_campaign_statuses:
        blockers.append('production_mesh_campaign_scout_not_pass')
    if stability.get('status') not in {'PASS-STABILITY', 'PASS-SCOUT'}:
        blockers.append('baseline_stability_scout_not_pass')
    if int(stability_summary.get('max_step', 0) or 0) < args.baseline_min_step:
        blockers.append('baseline_stability_scout_too_short')
    if int(mesh_summary.get('max_base_cell_count', 0) or 0) < args.min_base_cells:
        blockers.append('production_mesh_base_cell_count_below_candidate_minimum')
    if int(mesh_summary.get('max_amr_equivalent_fine_cell_count', 0) or 0) < args.min_fine_cells:
        blockers.append('production_mesh_fine_cell_count_below_candidate_minimum')
    if not wrapper.is_file():
        blockers.append('full_duration_wrapper_missing')
    if disk_audit.get('status') not in {'PASS-DISK-CLEANUP-AUDIT', 'NOT_READY-DISK-CLEANUP-AUDIT'}:
        blockers.append('disk_cleanup_audit_missing_or_invalid')

    free_bytes = disk_free_bytes(Path('.'))
    required_archive_bytes = int(args.min_free_gb * 1024**3)
    if free_bytes < required_archive_bytes:
        blockers.append('insufficient_free_disk_for_full_duration_candidate')

    target_plotfiles = args.target_max_step // args.target_plot_int + 1
    executed_evidence, executed_gaps = inspect_executed_run(
        Path(args.target_log_dir),
        args,
        target_plotfiles,
    )
    blockers.extend(executed_gaps)
    executed = executed_evidence is not None and not executed_gaps
    status = PASS_EXECUTED_STATUS if executed and not blockers else (PASS_STATUS if not blockers else NOT_READY_STATUS)
    command = [
        'env',
        f'CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS={args.target_ranks}',
        f'CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP={args.target_max_step}',
        f'CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT={args.target_plot_int}',
        f'CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES={target_plotfiles}',
        f'RUN_TIMEOUT={args.run_timeout_s}',
        f'JOBS={args.jobs}',
        f'CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LOG_DIR={args.target_log_dir}',
        'bash',
        str(wrapper),
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 Full-Duration Candidate',
        'candidate_tier': 'full_duration_execution_candidate',
        'production_campaign': False,
        'production_size_mesh_campaign': True,
        'full_duration_campaign': executed,
        'overnight_campaign': executed,
        'full_plotfile_archive': executed,
        'executed': executed,
        'clears_stability_duration_blocker': executed,
        'repo': {
            'branch': git_value(['rev-parse', '--abbrev-ref', 'HEAD']),
            'commit': git_value(['rev-parse', 'HEAD']),
            'dirty_short_sha256': hashlib.sha256(git_value(['status', '--short']).encode('utf-8')).hexdigest(),
        },
        'target': {
            'ranks': args.target_ranks,
            'jobs': args.jobs,
            'max_step': args.target_max_step,
            'plot_int': args.target_plot_int,
            'expected_plotfiles_per_case': target_plotfiles,
            'expected_simulation_time_s': args.target_max_step * 1.0e-3,
            'run_timeout_s': args.run_timeout_s,
            'target_log_dir': args.target_log_dir,
            'command': command,
        },
        'baseline_evidence': {
            'production_mesh_campaign_status': mesh_campaign.get('status'),
            'production_mesh_campaign_max_step': mesh_summary.get('max_step'),
            'production_mesh_campaign_ranks_covered': mesh_summary.get('ranks_covered'),
            'production_mesh_campaign_max_base_cells': mesh_summary.get('max_base_cell_count'),
            'production_mesh_campaign_max_fine_cells': mesh_summary.get('max_amr_equivalent_fine_cell_count'),
            'stability_scout_status': stability.get('status'),
            'stability_scout_max_step': stability_summary.get('max_step'),
            'stability_scout_ranks': stability_summary.get('ranks'),
            'stability_scout_cloud_rel_diff': stability_summary.get('cloud_rel_diff'),
            'stability_scout_peak_rel_diff': stability_summary.get('peak_rel_diff'),
        },
        'disk_cleanup_audit': {
            'status': disk_audit.get('status'),
            'current_free_gb': disk_requirement.get('current_free_gb'),
            'deficit_gb': disk_requirement.get('deficit_gb'),
            'review_candidate_gb': disk_summary.get('review_candidate_gb'),
            'review_candidates_cover_deficit': disk_summary.get('review_candidates_cover_deficit'),
            'destructive_actions_performed': disk_audit.get('destructive_actions_performed'),
        },
        'resource_preflight': {
            'free_bytes': free_bytes,
            'free_gb': free_bytes / 1024**3,
            'min_required_free_gb': args.min_free_gb,
            'disk_preflight_passed': free_bytes >= required_archive_bytes,
        },
        'executed_evidence': executed_evidence,
        'blocking_gaps': blockers,
        'evidence_files': [
            evidence_entry('production_mesh_campaign_report', mesh_campaign_path),
            evidence_entry('production_mesh_1200step_stability_scout_report', stability_path),
            evidence_entry('disk_cleanup_audit_report', disk_audit_path),
            evidence_entry('full_duration_wrapper', wrapper),
            *(
                [
                    evidence_entry('full_duration_reduced_long_summary', Path(args.target_log_dir) / 'reduced_long_summary.csv'),
                    evidence_entry('full_duration_engineering_case_report', Path(args.target_log_dir) / 'engineering_case_report.json'),
                    evidence_entry('full_duration_engineering_case_report_md', Path(args.target_log_dir) / 'engineering_case_report.md'),
                ]
                if executed else []
            ),
        ],
        'limitations': [
            (
                'This report includes executed full-duration reduced-long evidence and clears the stability-duration blocker.'
                if executed else
                'This report is a launch preflight and candidate run contract; it does not claim the full-duration run has executed.'
            ),
            (
                'It remains an internal engineering evidence artifact and does not replace external safety certification.'
                if executed else
                'It does not clear the stability/full-duration blocker until executed evidence is archived and verified.'
            ),
            'The target command is intentionally machine-readable so it can be submitted by scheduler or run manually under controlled conditions.',
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    target = report['target']
    resource = report['resource_preflight']
    lines = [
        '# Engineering H2 Full-Duration Candidate',
        '',
        f"Status: `{report['status']}`",
        f"Candidate tier: `{report['candidate_tier']}`",
        f"Executed: `{report['executed']}`",
        f"Clears stability-duration blocker: `{report['clears_stability_duration_blocker']}`",
        '',
        '## Target',
        '',
        f"- Ranks: `{target['ranks']}`",
        f"- Max step: `{target['max_step']}`",
        f"- Plot interval: `{target['plot_int']}`",
        f"- Expected plotfiles per case: `{target['expected_plotfiles_per_case']}`",
        f"- Expected simulation time: `{target['expected_simulation_time_s']}` s",
        '',
        '## Resource Preflight',
        '',
        f"- Free GB: `{resource['free_gb']:.2f}`",
        f"- Required free GB: `{resource['min_required_free_gb']}`",
        f"- Disk preflight passed: `{resource['disk_preflight_passed']}`",
        '',
        '## Blocking Gaps',
        '',
    ]
    if report['blocking_gaps']:
        for item in report['blocking_gaps']:
            lines.append(f'- `{item}`')
    else:
        lines.append('- none')
    lines.extend(['', '## Command', '', '```bash', ' '.join(target['command']), '```', ''])
    if report.get('executed_evidence'):
        evidence = report['executed_evidence']
        lines.extend([
            '## Executed Evidence',
            '',
            f"- Run root: `{evidence['run_root']}`",
            f"- Summary CSV: `{evidence['summary_csv']}`",
            f"- Engineering case report: `{evidence['engineering_case_report']}`",
            '',
        ])
    path.write_text('\n'.join(lines), encoding='utf-8')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {PASS_STATUS, PASS_EXECUTED_STATUS, NOT_READY_STATUS}, 'invalid status')
    require(data.get('candidate_tier') == 'full_duration_execution_candidate', 'invalid candidate_tier')
    executed = data.get('executed') is True
    if executed:
        require(data.get('status') == PASS_EXECUTED_STATUS, 'executed report must use executed status')
        require(data.get('full_duration_campaign') is True, 'executed report must claim full-duration completion')
        require(data.get('full_plotfile_archive') is True, 'executed report must preserve full plotfile archive')
        require(data.get('clears_stability_duration_blocker') is True, 'executed report must clear stability-duration blocker')
        require(isinstance(data.get('executed_evidence'), dict), 'executed report missing executed_evidence')
    else:
        require(data.get('full_duration_campaign') is False, 'candidate report must not claim full-duration completion')
    target = data.get('target', {})
    require(isinstance(target, dict), 'missing target')
    require(int(target.get('max_step', 0)) >= 7200, 'target max_step below candidate minimum')
    require(int(target.get('expected_plotfiles_per_case', 0)) >= 25, 'target plotfile count too low')
    resource = data.get('resource_preflight', {})
    require(isinstance(resource, dict), 'missing resource_preflight')
    require(isinstance(data.get('blocking_gaps'), list), 'missing blocking_gaps')
    for item in data.get('evidence_files', []):
        p = Path(item.get('path', ''))
        require(p.is_file(), f'referenced evidence file missing: {p}')
        require(sha256_file(p) == item.get('sha256'), f'referenced evidence hash mismatch: {p}')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--production-mesh-campaign-report', default=str(DEFAULT_PRODUCTION_MESH_CAMPAIGN))
    ap.add_argument('--stability-scout-report', default=str(DEFAULT_STABILITY_SCOUT))
    ap.add_argument('--disk-cleanup-audit-report', default=str(DEFAULT_DISK_CLEANUP_AUDIT))
    ap.add_argument('--wrapper', default=str(DEFAULT_WRAPPER))
    ap.add_argument('--baseline-min-step', type=int, default=1200)
    ap.add_argument('--min-base-cells', type=int, default=65536)
    ap.add_argument('--min-fine-cells', type=int, default=524288)
    ap.add_argument('--target-ranks', type=int, default=8)
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--target-max-step', type=int, default=7200)
    ap.add_argument('--target-plot-int', type=int, default=240)
    ap.add_argument('--run-timeout-s', type=int, default=43200)
    ap.add_argument('--min-free-gb', type=float, default=20.0)
    ap.add_argument('--target-log-dir', default='docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/run')
    ap.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)

    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            target = data['target']
            print(
                'engineering_h2_full_duration_candidate_report VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"ranks={target['ranks']} max_step={target['max_step']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_full_duration_candidate_report PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"ranks={report['target']['ranks']} max_step={report['target']['max_step']}"
        )
        return 0
    except ReportError as exc:
        print(f'engineering_h2_full_duration_candidate_report FAIL {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
