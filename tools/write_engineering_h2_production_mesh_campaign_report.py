#!/usr/bin/env python3
"""Write/verify a campaign-level summary of engineering H2 production-mesh scouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PASS_STATUS = 'PASS-PRODUCTION-MESH-CAMPAIGN-SCOUT'
PASS_FULL_DURATION_STATUS = 'PASS-PRODUCTION-MESH-FULL-DURATION-CAMPAIGN'
NOT_READY_STATUS = 'NOT_READY-PRODUCTION-MESH-CAMPAIGN-SCOUT'

DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/'
    'production_mesh_campaign_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/'
    'production_mesh_campaign_report.md'
)

DEFAULT_REPORTS = (
    ('production_mesh_4rank_120step', Path('docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json')),
    ('production_mesh_8rank_120step', Path('docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json')),
    ('production_mesh_16rank_120step', Path('docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json')),
    ('production_mesh_4rank_600step', Path('docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/production_mesh_600step_stability_scout_report.json')),
    ('production_mesh_8rank_600step', Path('docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json')),
    ('production_mesh_4rank_1200step', Path('docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json')),
)

DEFAULT_FULL_DURATION_RUN_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run'
)


class ReportError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReportError(message)


def finite_number(value: Any) -> bool:
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


def summarize_case(label: str, path: Path) -> dict[str, Any]:
    data = load_json(path)
    summary = data.get('summary', {}) if isinstance(data.get('summary'), dict) else {}
    status = str(data.get('status', ''))
    blockers: list[str] = []
    if status not in {'PASS-SCOUT', 'PASS-STABILITY'}:
        blockers.append('production_mesh_case_status_not_pass')
    for key in ('ranks', 'max_step', 'base_cell_count', 'amr_equivalent_fine_cell_count', 'baseline_plotfiles', 'amr_plotfiles', 'amr_finest_level'):
        if key not in summary:
            blockers.append(f'production_mesh_case_missing_{key}')
    for key in ('cloud_rel_diff', 'peak_rel_diff'):
        if not finite_number(summary.get(key)):
            blockers.append(f'production_mesh_case_nonfinite_{key}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'status': status,
        'ranks': int(summary.get('ranks', 0) or 0),
        'max_step': int(summary.get('max_step', 0) or 0),
        'base_cell_count': int(summary.get('base_cell_count', 0) or 0),
        'amr_equivalent_fine_cell_count': int(summary.get('amr_equivalent_fine_cell_count', 0) or 0),
        'baseline_plotfiles': int(summary.get('baseline_plotfiles', 0) or 0),
        'amr_plotfiles': int(summary.get('amr_plotfiles', 0) or 0),
        'amr_finest_level': int(summary.get('amr_finest_level', 0) or 0),
        'cloud_rel_diff': float(summary.get('cloud_rel_diff')) if finite_number(summary.get('cloud_rel_diff')) else None,
        'peak_rel_diff': float(summary.get('peak_rel_diff')) if finite_number(summary.get('peak_rel_diff')) else None,
        'blocking_gaps': blockers,
    }


def parse_setting(path: Path, key: str) -> str:
    text = path.read_text(encoding='utf-8', errors='replace')
    prefix = f'{key} ='
    for line in text.splitlines():
        if line.strip().startswith(prefix):
            return line.split('=', 1)[1].strip()
    raise ReportError(f'missing {key} in {path}')


def parse_n_cell(path: Path) -> tuple[int, int, int]:
    raw = parse_setting(path, 'amr.n_cell')
    parts = raw.split()
    require(len(parts) == 3, f'invalid amr.n_cell in {path}: {raw}')
    return tuple(int(part) for part in parts)


def summarize_full_duration_run(run_root: Path, args: argparse.Namespace) -> dict[str, Any] | None:
    if not run_root.exists():
        return None
    import csv

    blockers: list[str] = []
    summary_csv = run_root / 'reduced_long_summary.csv'
    case_report = run_root / 'engineering_case_report.json'
    if not summary_csv.exists() and not case_report.exists():
        return None
    if not summary_csv.is_file():
        blockers.append('full_duration_reduced_long_summary_missing')
        rows: list[dict[str, str]] = []
    else:
        with summary_csv.open(newline='', encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
        if len(rows) != 2:
            blockers.append('full_duration_summary_missing_baseline_or_amr')
    by_case = {str(row.get('case')): row for row in rows}
    base = by_case.get('baseline', {})
    amr = by_case.get('amr', {})
    if not case_report.is_file():
        blockers.append('full_duration_engineering_case_report_missing')
    else:
        data = load_json(case_report)
        if data.get('status') != 'PASS':
            blockers.append('full_duration_engineering_case_report_not_pass')

    base_input = run_root / 'baseline/run/input.codex_open_domain_plan_amr_baseline_smoke'
    amr_input = run_root / 'amr/run/input.codex_open_domain_plan_amr_level1_smoke'
    if not base_input.is_file() or not amr_input.is_file():
        blockers.append('full_duration_inputs_missing')
        base_n = (0, 0, 0)
        amr_n = (0, 0, 0)
    else:
        base_n = parse_n_cell(base_input)
        amr_n = parse_n_cell(amr_input)
    base_cells = base_n[0] * base_n[1] * base_n[2]
    fine_cells = (amr_n[0] * 2) * (amr_n[1] * 2) * (amr_n[2] * 2)
    ranks = int(amr.get('ranks', 0) or 0)
    max_step = int(amr.get('max_step', 0) or 0)
    baseline_plotfiles = int(base.get('plotfiles', 0) or 0)
    amr_plotfiles = int(amr.get('plotfiles', 0) or 0)
    for case_name, row in (('baseline', base), ('amr', amr)):
        if not row:
            blockers.append(f'full_duration_{case_name}_summary_missing')
            continue
        if int(row.get('final_step', 0) or 0) != max_step:
            blockers.append(f'full_duration_{case_name}_final_step_mismatch')
        if float(row.get('final_cloud_volume', 0.0) or 0.0) <= 0.0:
            blockers.append(f'full_duration_{case_name}_cloud_missing')
        if int(row.get('final_flammable_planes', 0) or 0) < 1:
            blockers.append(f'full_duration_{case_name}_flammable_planes_missing')
        validation = run_root / case_name / 'validation.log'
        mpi_validation = run_root / case_name / 'mpi_validation.log'
        if not validation.is_file() or 'PASS' not in validation.read_text(encoding='utf-8', errors='replace'):
            blockers.append(f'full_duration_{case_name}_validation_not_pass')
        if not mpi_validation.is_file() or 'PASS' not in mpi_validation.read_text(encoding='utf-8', errors='replace'):
            blockers.append(f'full_duration_{case_name}_mpi_validation_not_pass')
        final_plot = run_root / case_name / 'run' / f'plt{max_step:05d}'
        if not final_plot.is_dir():
            blockers.append(f'full_duration_{case_name}_final_plotfile_missing')

    if ranks < args.full_duration_min_ranks:
        blockers.append('full_duration_ranks_below_minimum')
    if max_step < args.full_duration_min_step:
        blockers.append('full_duration_steps_below_minimum')
    if min(baseline_plotfiles, amr_plotfiles) < args.full_duration_min_plotfiles:
        blockers.append('full_duration_plotfiles_below_minimum')
    if base_cells < args.min_base_cells or fine_cells < args.min_fine_cells:
        blockers.append('full_duration_mesh_below_minimum')
    cloud_rel = float(amr.get('cloud_rel_diff', 0.0) or 0.0)
    peak_rel = float(amr.get('peak_rel_diff', 0.0) or 0.0)
    if cloud_rel > args.full_duration_max_cloud_rel_diff:
        blockers.append('full_duration_cloud_difference_above_limit')
    if peak_rel > args.full_duration_max_peak_rel_diff:
        blockers.append('full_duration_peak_difference_above_limit')

    return {
        'label': 'production_mesh_4rank_7200step_full_duration',
        'path': str(run_root),
        'status': 'PASS-FULL-DURATION' if not blockers else 'NOT_READY-FULL-DURATION',
        'ranks': ranks,
        'max_step': max_step,
        'base_cell_count': base_cells,
        'amr_equivalent_fine_cell_count': fine_cells,
        'baseline_plotfiles': baseline_plotfiles,
        'amr_plotfiles': amr_plotfiles,
        'amr_finest_level': int(amr.get('finest_level', 0) or 0),
        'cloud_rel_diff': cloud_rel,
        'peak_rel_diff': peak_rel,
        'full_plotfile_archive': min(baseline_plotfiles, amr_plotfiles) >= args.full_duration_min_plotfiles,
        'blocking_gaps': blockers,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    cases = [summarize_case(label, path) for label, path in DEFAULT_REPORTS]
    full_duration_case = summarize_full_duration_run(Path(args.full_duration_run_root), args)
    if full_duration_case is not None:
        cases.append(full_duration_case)
    blockers: list[str] = []
    if any(case['blocking_gaps'] for case in cases):
        blockers.append('production_mesh_case_evidence_invalid')
    ranks = sorted({case['ranks'] for case in cases if case['ranks'] > 0})
    max_steps = [case['max_step'] for case in cases]
    max_base_cells = max(case['base_cell_count'] for case in cases)
    max_fine_cells = max(case['amr_equivalent_fine_cell_count'] for case in cases)
    max_cloud_rel = max(case['cloud_rel_diff'] for case in cases if case['cloud_rel_diff'] is not None)
    max_peak_rel = max(case['peak_rel_diff'] for case in cases if case['peak_rel_diff'] is not None)
    if not {4, 8, 16}.issubset(set(ranks)):
        blockers.append('production_mesh_campaign_rank_sweep_incomplete')
    if max(max_steps) < args.min_max_step:
        blockers.append('production_mesh_campaign_duration_below_scout_minimum')
    if max_base_cells < args.min_base_cells or max_fine_cells < args.min_fine_cells:
        blockers.append('production_mesh_campaign_mesh_below_minimum')
    if max_cloud_rel > args.max_cloud_rel_diff:
        blockers.append('production_mesh_campaign_cloud_difference_above_limit')
    if max_peak_rel > args.max_peak_rel_diff:
        blockers.append('production_mesh_campaign_peak_difference_above_limit')
    full_duration_ready = (
        full_duration_case is not None
        and not full_duration_case['blocking_gaps']
        and full_duration_case['status'] == 'PASS-FULL-DURATION'
    )

    status = (
        PASS_FULL_DURATION_STATUS
        if not blockers and full_duration_ready else
        (PASS_STATUS if not blockers else NOT_READY_STATUS)
    )
    production_size_ready = status in {PASS_STATUS, PASS_FULL_DURATION_STATUS}
    evidence_files = [evidence_entry(label, path) for label, path in DEFAULT_REPORTS]
    if full_duration_case is not None:
        full_root = Path(args.full_duration_run_root)
        for label, path in (
            ('production_mesh_full_duration_reduced_long_summary', full_root / 'reduced_long_summary.csv'),
            ('production_mesh_full_duration_engineering_case_report', full_root / 'engineering_case_report.json'),
            ('production_mesh_full_duration_engineering_case_report_md', full_root / 'engineering_case_report.md'),
        ):
            if path.is_file():
                evidence_files.append(evidence_entry(label, path))
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 Production Mesh Campaign',
        'campaign_scale': (
            'engineering_production_mesh_full_duration_campaign'
            if full_duration_ready else
            'engineering_production_mesh_stability_scout'
        ),
        'evidence_tier': (
            'production_mesh_full_duration_campaign'
            if full_duration_ready else
            'production_mesh_campaign_scout'
        ),
        'production_campaign': full_duration_ready,
        'production_size_mesh_campaign': production_size_ready,
        'full_duration_campaign': full_duration_ready,
        'overnight_campaign': full_duration_ready,
        'full_plotfile_archive': full_duration_ready,
        'clears_campaign_scale_blocker': full_duration_ready,
        'summary': {
            'case_count': len(cases),
            'pass_case_count': sum(1 for case in cases if not case['blocking_gaps']),
            'ranks_covered': ranks,
            'max_step': max(max_steps),
            'max_base_cell_count': max_base_cells,
            'max_amr_equivalent_fine_cell_count': max_fine_cells,
            'max_cloud_rel_diff': max_cloud_rel,
            'max_peak_rel_diff': max_peak_rel,
            'production_size_mesh_campaign': production_size_ready,
            'full_duration_campaign': full_duration_ready,
            'full_duration_case': full_duration_case,
            'blocks_production_readiness': not full_duration_ready,
        },
        'cases': cases,
        'blocking_gaps': blockers,
        'evidence_files': evidence_files,
        'limitations': [
            (
                'This report aggregates production-mesh rank-sweep scouts plus a 4-rank full-duration production-mesh run.'
                if full_duration_ready else
                'This report aggregates existing production-mesh scout and stability evidence at campaign level.'
            ),
            (
                'The full-duration evidence is a 4-rank production-mesh campaign member; 8/16-rank full-duration repetitions remain future hardening.'
                if full_duration_ready else
                'It proves production-mesh scout coverage, not full-duration production acceptance.'
            ),
            'It does not clear scheduler acceptance, real CAD cleanup, external reference-data, or calibrated fire consequence blockers.',
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        '# Engineering H2 Production Mesh Campaign Scout',
        '',
        f"Status: `{report['status']}`",
        f"Campaign scale: `{report['campaign_scale']}`",
        f"Production-size mesh campaign: `{report['production_size_mesh_campaign']}`",
        f"Full-duration campaign: `{report['full_duration_campaign']}`",
        '',
        '## Summary',
        '',
        f"- Cases: `{s['pass_case_count']}` / `{s['case_count']}` pass",
        f"- Ranks covered: `{s['ranks_covered']}`",
        f"- Max step: `{s['max_step']}`",
        f"- Max base cells: `{s['max_base_cell_count']}`",
        f"- Max AMR-equivalent fine cells: `{s['max_amr_equivalent_fine_cell_count']}`",
        f"- Max cloud relative difference: `{s['max_cloud_rel_diff']}`",
        f"- Max peak relative difference: `{s['max_peak_rel_diff']}`",
        '',
        '## Cases',
        '',
        '| Case | Status | Ranks | Steps | Base cells | Fine cells | Cloud rel | Peak rel |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for case in report['cases']:
        lines.append(
            f"| `{case['label']}` | `{case['status']}` | {case['ranks']} | {case['max_step']} | "
            f"{case['base_cell_count']} | {case['amr_equivalent_fine_cell_count']} | "
            f"{case['cloud_rel_diff']} | {case['peak_rel_diff']} |"
        )
    lines.extend(['', '## Blocking Gaps', ''])
    if report['blocking_gaps']:
        for item in report['blocking_gaps']:
            lines.append(f'- `{item}`')
    else:
        lines.append('- none')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {PASS_STATUS, PASS_FULL_DURATION_STATUS, NOT_READY_STATUS}, 'invalid status')
    summary = data.get('summary', {})
    require(isinstance(summary, dict), 'missing summary')
    require(isinstance(data.get('cases'), list) and data['cases'], 'missing cases')
    require(isinstance(data.get('blocking_gaps'), list), 'missing blocking_gaps')
    if data.get('status') == PASS_STATUS:
        require(not data.get('blocking_gaps'), 'PASS report has blocking gaps')
        require(data.get('production_size_mesh_campaign') is True, 'PASS report is not production-size mesh')
        require(data.get('full_duration_campaign') is False, 'scout report must not claim full duration')
    if data.get('status') == PASS_FULL_DURATION_STATUS:
        require(not data.get('blocking_gaps'), 'PASS full-duration report has blocking gaps')
        require(data.get('production_campaign') is True, 'full-duration campaign must claim production campaign')
        require(data.get('production_size_mesh_campaign') is True, 'full-duration campaign must be production-size mesh')
        require(data.get('full_duration_campaign') is True, 'full-duration campaign flag missing')
        require(data.get('full_plotfile_archive') is True, 'full-duration campaign must preserve plotfile archive')
        full_case = summary.get('full_duration_case', {})
        require(isinstance(full_case, dict), 'missing full_duration_case summary')
        require(full_case.get('status') == 'PASS-FULL-DURATION', 'full_duration_case did not PASS')
    for item in data.get('evidence_files', []):
        p = Path(item.get('path', ''))
        require(p.is_file(), f'referenced evidence file missing: {p}')
        require(sha256_file(p) == item.get('sha256'), f'referenced evidence hash mismatch: {p}')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--min-max-step', type=int, default=1200)
    ap.add_argument('--min-base-cells', type=int, default=65536)
    ap.add_argument('--min-fine-cells', type=int, default=524288)
    ap.add_argument('--max-cloud-rel-diff', type=float, default=0.05)
    ap.add_argument('--max-peak-rel-diff', type=float, default=0.05)
    ap.add_argument('--full-duration-run-root', default=str(DEFAULT_FULL_DURATION_RUN_ROOT))
    ap.add_argument('--full-duration-min-ranks', type=int, default=4)
    ap.add_argument('--full-duration-min-step', type=int, default=7200)
    ap.add_argument('--full-duration-min-plotfiles', type=int, default=31)
    ap.add_argument('--full-duration-max-cloud-rel-diff', type=float, default=0.25)
    ap.add_argument('--full-duration-max-peak-rel-diff', type=float, default=0.25)
    ap.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)

    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            s = data['summary']
            print(
                'engineering_h2_production_mesh_campaign_report VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"cases={s['pass_case_count']}/{s['case_count']} max_step={s['max_step']}"
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
            'engineering_h2_production_mesh_campaign_report PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"cases={report['summary']['pass_case_count']}/{report['summary']['case_count']}"
        )
        return 0
    except ReportError as exc:
        print(f'engineering_h2_production_mesh_campaign_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
