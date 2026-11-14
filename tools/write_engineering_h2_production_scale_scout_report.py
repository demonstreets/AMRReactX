#!/usr/bin/env python3
"""Package and verify compact H2 engineering scout evidence reports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
REPO_TOKEN = '${REPO_ROOT}'
USER_TOKEN = '${USER_HOME}'
REQUIRED_FILES = [
    'engineering_case_report.json',
    'engineering_case_report.md',
    'reduced_long_summary.csv',
    'plan_amr_compare_summary.csv',
    'amr_overhead_summary.csv',
    'baseline/validation.log',
    'baseline/profile_validation.log',
    'baseline/hazard_summary.log',
    'baseline/hazard_planes.log',
    'baseline/hazard_timeseries.log',
    'baseline/mpi_validation.log',
    'baseline/run/input.codex_open_domain_plan_amr_baseline_smoke',
    'amr/validation.log',
    'amr/profile_validation.log',
    'amr/hazard_summary.log',
    'amr/hazard_planes.log',
    'amr/hazard_timeseries.log',
    'amr/mpi_validation.log',
    'amr/run/input.codex_open_domain_plan_amr_level1_smoke',
]
FAIL_MARKERS = ('FAIL', 'Traceback', 'RuntimeError', 'Segmentation fault', 'SIGSEGV', 'Backtrace', 'Unused ParmParse Variables')


class ReportError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def sanitize_text(text: str, repo_root: Path, source_root: Path) -> str:
    home = Path.home()
    text = text.replace(str(source_root), '${SCOUT_ROOT}')
    text = text.replace(str(repo_root), REPO_TOKEN)
    text = text.replace(str(home), USER_TOKEN)
    return text


def copy_sanitized(src: Path, dst: Path, repo_root: Path, source_root: Path) -> dict[str, Any]:
    if not src.is_file():
        raise ReportError(f'missing required scout evidence: {src}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = read_text(src)
    except UnicodeDecodeError:
        shutil.copyfile(src, dst)
        sanitized = False
    else:
        cleaned = sanitize_text(text, repo_root, source_root)
        dst.write_text(cleaned, encoding='utf-8')
        sanitized = cleaned != text
    return {
        'path': str(dst),
        'relative_path': str(dst),
        'sha256': sha256_file(dst),
        'size_bytes': dst.stat().st_size,
        'sanitized': sanitized,
    }


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ReportError(f'empty CSV: {path}')
    return rows


def finite_float(value: str, label: str) -> float:
    try:
        out = float(value)
    except ValueError as exc:
        raise ReportError(f'invalid float {label}={value!r}') from exc
    if not math.isfinite(out):
        raise ReportError(f'nonfinite float {label}={value!r}')
    return out


def parse_n_cell(input_path: Path) -> tuple[int, int, int]:
    text = read_text(input_path)
    m = re.search(r'^amr\.n_cell\s*=\s*([0-9]+)\s+([0-9]+)\s+([0-9]+)\s*$', text, re.M)
    if not m:
        raise ReportError(f'missing amr.n_cell in {input_path}')
    return tuple(int(m.group(i)) for i in range(1, 4))


def parse_max_step(input_path: Path) -> int:
    text = read_text(input_path)
    m = re.search(r'^amr\.max_step\s*=\s*([0-9]+)\s*$', text, re.M)
    if not m:
        raise ReportError(f'missing amr.max_step in {input_path}')
    return int(m.group(1))


def scan_failure_markers(files: list[Path]) -> None:
    hits = []
    for path in files:
        if path.suffix not in {'.log', '.md', '.csv'} and 'input.' not in path.name:
            continue
        text = read_text(path)
        for marker in FAIL_MARKERS:
            if marker in text and 'VERIFY-PASS' not in text:
                hits.append(f'{path}:{marker}')
        if re.search(r'(?<![A-Za-z0-9_])(?:nan|inf)(?![A-Za-z0-9_])', text, re.I):
            hits.append(f'{path}:nonfinite-token')
    if hits:
        raise ReportError('failure markers found in packaged scout evidence: ' + '; '.join(hits[:20]))


def stability_duration_class(case_name: str, max_step: int) -> str:
    name = case_name.lower()
    if '1200step' in name or max_step >= 1200:
        return 'production_mesh_1200step_stability_scout'
    if '600step' in name or max_step >= 600:
        return 'production_mesh_600step_stability_scout'
    if 'long-stability' in name or max_step >= 300:
        return 'reduced_long_stability_scout'
    return 'short_production_scale_scout'


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    source_root = Path(args.source_root).resolve()
    evidence_root = Path(args.evidence_root)
    files_root = evidence_root / 'files'
    repo_root = Path(args.repo_root).resolve()
    copied = []
    copied_paths = []
    for rel in REQUIRED_FILES:
        dst = files_root / rel
        copied.append(copy_sanitized(source_root / rel, dst, repo_root, source_root))
        copied_paths.append(dst)
    scan_failure_markers(copied_paths)

    reduced_rows = load_csv(files_root / 'reduced_long_summary.csv')
    compare_rows = load_csv(files_root / 'plan_amr_compare_summary.csv')
    overhead_rows = load_csv(files_root / 'amr_overhead_summary.csv')
    if len(reduced_rows) != 2 or len(compare_rows) != 2:
        raise ReportError('expected baseline/amr rows in reduced-long and compare summaries')
    base_row = next(r for r in reduced_rows if r.get('case') == 'baseline')
    amr_row = next(r for r in reduced_rows if r.get('case') == 'amr')
    compare_amr = next(r for r in compare_rows if r.get('case') == 'amr')
    overhead = next((r for r in overhead_rows if r.get('case') == 'amr'), overhead_rows[-1])

    base_n = parse_n_cell(files_root / 'baseline/run/input.codex_open_domain_plan_amr_baseline_smoke')
    amr_n = parse_n_cell(files_root / 'amr/run/input.codex_open_domain_plan_amr_level1_smoke')
    max_step = parse_max_step(files_root / 'amr/run/input.codex_open_domain_plan_amr_level1_smoke')
    base_cells = base_n[0] * base_n[1] * base_n[2]
    amr_equiv_fine = (amr_n[0] * 2) * (amr_n[1] * 2) * (amr_n[2] * 2)
    ranks = int(amr_row['ranks'])
    cloud_rel = finite_float(compare_amr['cloud_rel_diff'], 'cloud_rel_diff')
    peak_rel = finite_float(compare_amr['peak_rel_diff'], 'peak_rel_diff')
    mean_cells_ratio = finite_float(overhead['mean_ncells_ratio'], 'mean_ncells_ratio')
    advance_ratio = finite_float(overhead['advance_seconds_ratio'], 'advance_seconds_ratio')
    final_cloud = finite_float(amr_row['final_cloud_volume'], 'amr_final_cloud_volume')
    final_peak = finite_float(amr_row['final_peak_X'], 'amr_final_peak_X')
    criteria = {
        'min_ranks': args.min_ranks,
        'min_max_step': args.min_max_step,
        'min_base_cells': args.min_base_cells,
        'min_equivalent_fine_cells': args.min_equivalent_fine_cells,
        'min_plotfiles': args.min_plotfiles,
        'max_cloud_rel_diff': args.max_cloud_rel_diff,
        'max_peak_rel_diff': args.max_peak_rel_diff,
        'max_mean_ncells_ratio': args.max_mean_ncells_ratio,
        'max_advance_seconds_ratio': args.max_advance_seconds_ratio,
    }
    if ranks < args.min_ranks:
        raise ReportError(f'{args.case_name} requires at least {args.min_ranks} ranks, got {ranks}')
    if max_step < args.min_max_step:
        raise ReportError(f'{args.case_name} requires at least {args.min_max_step} steps, got {max_step}')
    if base_cells < args.min_base_cells:
        raise ReportError(f'{args.case_name} base grid too small: {base_cells}')
    if amr_equiv_fine < args.min_equivalent_fine_cells:
        raise ReportError(f'{args.case_name} equivalent fine grid too small: {amr_equiv_fine}')
    if int(base_row['plotfiles']) < args.min_plotfiles or int(amr_row['plotfiles']) < args.min_plotfiles:
        raise ReportError(f'{args.case_name} plotfile count below {args.min_plotfiles}')
    if cloud_rel > args.max_cloud_rel_diff or peak_rel > args.max_peak_rel_diff:
        raise ReportError(f'AMR drift too large for scout: cloud={cloud_rel} peak={peak_rel}')
    if mean_cells_ratio > args.max_mean_ncells_ratio or advance_ratio > args.max_advance_seconds_ratio:
        raise ReportError(f'AMR overhead too large for scout: cells={mean_cells_ratio} advance={advance_ratio}')
    if final_cloud <= 0.0 or final_peak <= 0.0:
        raise ReportError('AMR final hazard metrics are not positive')
    duration_class = stability_duration_class(args.case_name, max_step)

    limitations = [
        'This is a production-scale scout, not a final production-size campaign.',
        'It packages compact logs/summaries/inputs only, not full AMReX plotfile directories.',
        'It does not prove external reference-data agreement, real CAD geometry, scheduler allocation, or overnight stability.',
    ]
    if 'long-stability' in args.case_name:
        limitations = [
            'This is a 300-step long-stability scout, not an overnight or full-duration production campaign.',
            'It packages compact logs/summaries/inputs only, not full AMReX plotfile directories.',
            'It does not prove external reference-data agreement, real CAD geometry, scheduler allocation, or calibrated fire/radiation metrics.',
        ]

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': args.status,
        'case': args.case_name,
        'title': args.title,
        'evidence_root': str(evidence_root),
        'evidence_tier': 'engineering_cfd_scout',
        'stability_duration_class': duration_class,
        'production_campaign': False,
        'production_size_mesh_campaign': False,
        'overnight_campaign': False,
        'full_duration_campaign': False,
        'full_plotfile_archive': False,
        'criteria': criteria,
        'summary': {
            'ranks': ranks,
            'max_step': max_step,
            'base_n_cell': list(base_n),
            'base_cell_count': base_cells,
            'amr_finest_level': int(amr_row['finest_level']),
            'amr_equivalent_fine_n_cell': [amr_n[0] * 2, amr_n[1] * 2, amr_n[2] * 2],
            'amr_equivalent_fine_cell_count': amr_equiv_fine,
            'baseline_plotfiles': int(base_row['plotfiles']),
            'amr_plotfiles': int(amr_row['plotfiles']),
            'amr_final_cloud_volume': final_cloud,
            'amr_final_peak_X': final_peak,
            'cloud_rel_diff': cloud_rel,
            'peak_rel_diff': peak_rel,
            'mean_ncells_ratio': mean_cells_ratio,
            'advance_seconds_ratio': advance_ratio,
        },
        'files': copied,
        'limitations': limitations,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        f"# {report.get('title', 'H2 Production-Scale Scout Report')}",
        '',
        f"Status: `{report['status']}`",
        f"Evidence tier: `{report.get('evidence_tier', 'engineering_cfd_scout')}`",
        f"Stability duration class: `{report.get('stability_duration_class', 'short_production_scale_scout')}`",
        f"Production campaign: `{report.get('production_campaign', False)}`",
        f"Production-size mesh campaign: `{report.get('production_size_mesh_campaign', False)}`",
        f"Overnight campaign: `{report.get('overnight_campaign', False)}`",
        f"Full-duration campaign: `{report.get('full_duration_campaign', False)}`",
        f"Full plotfile archive: `{report.get('full_plotfile_archive', False)}`",
        '',
        '## Summary',
        '',
        f"- Ranks: `{s['ranks']}`",
        f"- Max step: `{s['max_step']}`",
        f"- Base grid: `{s['base_n_cell']}` = `{s['base_cell_count']}` cells",
        f"- AMR equivalent fine grid: `{s['amr_equivalent_fine_n_cell']}` = `{s['amr_equivalent_fine_cell_count']}` cells",
        f"- AMR finest level: `{s['amr_finest_level']}`",
        f"- AMR final cloud volume: `{s['amr_final_cloud_volume']:.8e}`",
        f"- AMR final peak X: `{s['amr_final_peak_X']:.8e}`",
        f"- AMR cloud relative difference: `{s['cloud_rel_diff']:.8e}`",
        f"- AMR peak relative difference: `{s['peak_rel_diff']:.8e}`",
        f"- Mean cell-count ratio: `{s['mean_ncells_ratio']:.8e}`",
        f"- Advance-seconds ratio: `{s['advance_seconds_ratio']:.8e}`",
        '',
        '## Limitations',
        '',
    ]
    for item in report['limitations']:
        lines.append(f'- {item}')
    lines += ['', '## Packaged Files', '']
    for item in report['files']:
        lines.append(f"- `{item['path']}` sha256 `{item['sha256'][:16]}`")
    path.write_text('\n'.join(lines) + '\n')


def verify_report(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if data.get('schema_version') != SCHEMA_VERSION:
        raise ReportError('schema version mismatch')
    if data.get('status') not in {'PASS-SCOUT', 'PASS-STABILITY'}:
        raise ReportError(f'unexpected status {data.get("status")}')
    if 'stability_duration_class' in data and not isinstance(data['stability_duration_class'], str):
        raise ReportError('stability_duration_class must be a string')
    for key in ('production_campaign', 'production_size_mesh_campaign', 'overnight_campaign', 'full_duration_campaign', 'full_plotfile_archive'):
        if key in data and not isinstance(data[key], bool):
            raise ReportError(f'{key} must be a boolean')
    s = data.get('summary', {})
    criteria = data.get('criteria') or {
        'min_ranks': 4,
        'min_max_step': 100,
        'min_base_cells': 25000,
        'min_equivalent_fine_cells': 0,
        'min_plotfiles': 0,
        'max_cloud_rel_diff': 0.20,
        'max_peak_rel_diff': 0.20,
        'max_mean_ncells_ratio': 3.0,
        'max_advance_seconds_ratio': 3.0,
    }
    if (s.get('ranks', 0) < criteria.get('min_ranks', 0) or
            s.get('max_step', 0) < criteria.get('min_max_step', 0) or
            s.get('base_cell_count', 0) < criteria.get('min_base_cells', 0) or
            s.get('amr_equivalent_fine_cell_count', 0) < criteria.get('min_equivalent_fine_cells', 0) or
            s.get('baseline_plotfiles', 0) < criteria.get('min_plotfiles', 0) or
            s.get('amr_plotfiles', 0) < criteria.get('min_plotfiles', 0)):
        raise ReportError('summary does not meet scout minimums')
    if (s.get('cloud_rel_diff', 1.0e99) > criteria.get('max_cloud_rel_diff', 1.0e99) or
            s.get('peak_rel_diff', 1.0e99) > criteria.get('max_peak_rel_diff', 1.0e99) or
            s.get('mean_ncells_ratio', 1.0e99) > criteria.get('max_mean_ncells_ratio', 1.0e99) or
            s.get('advance_seconds_ratio', 1.0e99) > criteria.get('max_advance_seconds_ratio', 1.0e99)):
        raise ReportError('summary exceeds scout drift or overhead limits')
    for item in data.get('files', []):
        p = Path(item['path'])
        if not p.is_file():
            raise ReportError(f'missing packaged file: {p}')
        if sha256_file(p) != item.get('sha256'):
            raise ReportError(f'hash mismatch: {p}')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root')
    ap.add_argument('--evidence-root')
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--output-json')
    ap.add_argument('--output-md')
    ap.add_argument('--verify-json')
    ap.add_argument('--case-name', default='h2-open-domain-plan-amr-mpi-production-scale-scout')
    ap.add_argument('--title', default='H2 Production-Scale Scout Report')
    ap.add_argument('--status', default='PASS-SCOUT')
    ap.add_argument('--min-ranks', type=int, default=4)
    ap.add_argument('--min-max-step', type=int, default=100)
    ap.add_argument('--min-base-cells', type=int, default=25000)
    ap.add_argument('--min-equivalent-fine-cells', type=int, default=200000)
    ap.add_argument('--min-plotfiles', type=int, default=7)
    ap.add_argument('--max-cloud-rel-diff', type=float, default=0.20)
    ap.add_argument('--max-peak-rel-diff', type=float, default=0.20)
    ap.add_argument('--max-mean-ncells-ratio', type=float, default=3.0)
    ap.add_argument('--max-advance-seconds-ratio', type=float, default=3.0)
    args = ap.parse_args(argv)
    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            s = data['summary']
            print('engineering_h2_production_scale_scout_report VERIFY-PASS ' +
                  f"json={args.verify_json} status={data['status']} ranks={s['ranks']} " +
                  f"base_cells={s['base_cell_count']} fine_cells={s['amr_equivalent_fine_cell_count']}")
            return 0
        if not args.source_root or not args.evidence_root or not args.output_json or not args.output_md:
            raise ReportError('--source-root, --evidence-root, --output-json, and --output-md are required unless --verify-json is used')
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        write_markdown(report, out_md)
        s = report['summary']
        print('engineering_h2_production_scale_scout_report PASS ' +
              f"json={out_json} md={out_md} ranks={s['ranks']} base_cells={s['base_cell_count']} " +
              f"fine_cells={s['amr_equivalent_fine_cell_count']} cloud_rel={s['cloud_rel_diff']:.8e}")
        return 0
    except (ReportError, OSError, KeyError, StopIteration, ValueError) as exc:
        print(f'engineering_h2_production_scale_scout_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
