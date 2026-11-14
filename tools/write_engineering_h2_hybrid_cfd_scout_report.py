#!/usr/bin/env python3
"""Package and verify H2 engineering hybrid MPI/OpenMP CFD scout evidence."""
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
DEFAULT_SOURCE_ROOT = Path('/tmp/codex_h2_leak_open_domain_plan_amr_hybrid_20260720_rerun5')
DEFAULT_EVIDENCE_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720'
)
REPO_TOKEN = '${REPO_ROOT}'
HOME_TOKEN = '${USER_HOME}'
SCOUT_TOKEN = '${SCOUT_ROOT}'
REQUIRED_FILES = [
    'plan_amr_compare_summary.csv',
    'amr_overhead_summary.csv',
    'inputs/input.codex_open_domain_plan_amr_baseline_smoke',
    'inputs/input.codex_open_domain_plan_amr_level1_smoke',
    'baseline/validation.log',
    'baseline/profile_validation.log',
    'baseline/hazard_summary.log',
    'baseline/hazard_planes.log',
    'baseline/hazard_planes.csv',
    'baseline/hazard_timeseries.log',
    'baseline/hazard_timeseries.csv',
    'baseline/hybrid_validation.log',
    'baseline/run/input.codex_open_domain_plan_amr_baseline_smoke',
    'amr/validation.log',
    'amr/profile_validation.log',
    'amr/hazard_summary.log',
    'amr/hazard_planes.log',
    'amr/hazard_planes.csv',
    'amr/hazard_timeseries.log',
    'amr/hazard_timeseries.csv',
    'amr/hybrid_validation.log',
    'amr/run/input.codex_open_domain_plan_amr_level1_smoke',
]
FAIL_MARKERS = (
    'FAIL',
    'Traceback',
    'RuntimeError',
    'Segmentation fault',
    'SIGSEGV',
    'Backtrace',
    'Unused ParmParse Variables',
)


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ReportError(f'missing report: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON report {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON report is not an object: {path}')
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def finite_float(value: str, label: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ReportError(f'invalid float {label}={value!r}') from exc
    require(math.isfinite(out), f'nonfinite float {label}={value!r}')
    return out


def int_value(value: str, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ReportError(f'invalid int {label}={value!r}') from exc


def sanitize_text(text: str, repo_root: Path, source_root: Path) -> str:
    text = text.replace(str(source_root), SCOUT_TOKEN)
    text = text.replace(str(repo_root), REPO_TOKEN)
    text = text.replace(str(Path.home()), HOME_TOKEN)
    return text


def copy_sanitized(src: Path, dst: Path, repo_root: Path, source_root: Path) -> dict[str, Any]:
    require(src.is_file(), f'missing required hybrid CFD evidence: {src}')
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
    require(rows, f'empty CSV: {path}')
    return rows


def row_by_case(rows: list[dict[str, str]], case: str, label: str) -> dict[str, str]:
    matches = [r for r in rows if r.get('case') == case]
    require(len(matches) == 1, f'{label} expected one {case} row, found {len(matches)}')
    return matches[0]


def parse_setting(path: Path, key: str) -> str:
    text = read_text(path)
    m = re.search(rf'^{re.escape(key)}\s*=\s*(.+?)\s*$', text, re.M)
    require(m is not None, f'missing {key} in {path}')
    return m.group(1)


def parse_n_cell(path: Path) -> tuple[int, int, int]:
    raw = parse_setting(path, 'amr.n_cell')
    parts = raw.split()
    require(len(parts) == 3, f'amr.n_cell must have 3 entries in {path}: {raw}')
    return tuple(int(p) for p in parts)


def scan_failure_markers(paths: list[Path]) -> None:
    hits = []
    for path in paths:
        if path.suffix not in {'.log', '.csv'} and 'input.' not in path.name:
            continue
        text = read_text(path)
        for marker in FAIL_MARKERS:
            if marker in text:
                hits.append(f'{path}:{marker}')
        if re.search(r'(?<![A-Za-z0-9_])(?:nan|inf)(?![A-Za-z0-9_])', text, re.I):
            hits.append(f'{path}:nonfinite-token')
    require(not hits, 'failure markers found in hybrid CFD evidence: ' + '; '.join(hits[:20]))


def parse_hybrid_validation(path: Path) -> dict[str, Any]:
    text = read_text(path).strip()
    require('parallel_smoke_log_validation PASS' in text, f'hybrid validation did not PASS: {path}')
    out: dict[str, Any] = {'raw': text}
    for key in ('solver', 'mode', 'ranks', 'threads', 'final_time', 'finalized', 'warning'):
        m = re.search(rf'\b{key}=([^\s]+)', text)
        if m:
            out[key] = m.group(1)
    for key in ('ranks', 'threads', 'finalized'):
        if key in out:
            out[key] = int(out[key])
    if 'final_time' in out:
        out['final_time'] = float(out['final_time'])
    return out


def plot_metadata(source_root: Path, case: str, max_step: int) -> dict[str, Any]:
    sys.path.insert(0, str(Path.cwd() / 'tools'))
    import amrex_reader  # noqa: E402

    plot = source_root / case / 'run' / f'plt{max_step:05d}'
    require(plot.is_dir(), f'missing final plotfile for {case}: {plot}')
    header = plot / 'Header'
    meta = amrex_reader._parse_header(str(header))
    levels = []
    total_fabs = 0
    for level in range(int(meta['finest_level']) + 1):
        cell_h = plot / f'Level_{level}' / 'Cell_H'
        require(cell_h.is_file(), f'missing Cell_H for {case} Level_{level}: {cell_h}')
        fab_count = sum(1 for line in read_text(cell_h).splitlines() if line.strip().startswith('FabOnDisk:'))
        total_fabs += fab_count
        levels.append({'level': level, 'fab_count': fab_count})
    return {
        'path': str(plot),
        'header_sha256': sha256_file(header),
        'finest_level': int(meta['finest_level']),
        'levels': levels,
        'total_fab_count': total_fabs,
    }


def case_summary(
    case: str,
    compare_row: dict[str, str],
    overhead_row: dict[str, str],
    hybrid: dict[str, Any],
    plot: dict[str, Any],
) -> dict[str, Any]:
    return {
        'case': case,
        'finest_level': int_value(compare_row['finest_level'], f'{case}.finest_level'),
        'finest_fab_count': int_value(compare_row['finest_fab_count'], f'{case}.finest_fab_count'),
        'total_fab_count': int_value(overhead_row['total_fab_count'], f'{case}.total_fab_count'),
        'regrid_count': int_value(compare_row['regrid_count'], f'{case}.regrid_count'),
        'made_level1': int_value(compare_row['made_level1'], f'{case}.made_level1'),
        'mass_ratio': finite_float(compare_row['mass_ratio'], f'{case}.mass_ratio'),
        'mass_ratioN': finite_float(compare_row['mass_ratioN'], f'{case}.mass_ratioN'),
        'cloud_volume': finite_float(compare_row['cloud_volume'], f'{case}.cloud_volume'),
        'cloud_species_mass': finite_float(compare_row['cloud_species_mass'], f'{case}.cloud_species_mass'),
        'max_X': finite_float(compare_row['max_X'], f'{case}.max_X'),
        'active_planes': int_value(compare_row['active_planes'], f'{case}.active_planes'),
        'flammable_planes': int_value(compare_row['flammable_planes'], f'{case}.flammable_planes'),
        'plotfiles': int_value(compare_row['plotfiles'], f'{case}.plotfiles'),
        'advance_seconds': finite_float(overhead_row['advance_seconds'], f'{case}.advance_seconds'),
        'mean_ncells': finite_float(overhead_row['mean_ncells'], f'{case}.mean_ncells'),
        'hybrid_validation': hybrid,
        'plot_metadata': plot,
    }


def evidence_hash_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    source_root = Path(args.source_root).resolve()
    evidence_root = Path(args.evidence_root)
    files_root = evidence_root / 'files'
    copied = []
    copied_paths = []
    for rel in REQUIRED_FILES:
        dst = files_root / rel
        copied.append(copy_sanitized(source_root / rel, dst, repo_root, source_root))
        copied_paths.append(dst)
    scan_failure_markers(copied_paths)

    compare_rows = load_csv(files_root / 'plan_amr_compare_summary.csv')
    overhead_rows = load_csv(files_root / 'amr_overhead_summary.csv')
    require(len(compare_rows) == 2, 'expected baseline/amr rows in plan-AMR comparison summary')
    require(len(overhead_rows) == 2, 'expected baseline/amr rows in AMR overhead summary')
    compare_base = row_by_case(compare_rows, 'baseline', 'plan-AMR summary')
    compare_amr = row_by_case(compare_rows, 'amr', 'plan-AMR summary')
    overhead_base = row_by_case(overhead_rows, 'baseline', 'AMR overhead summary')
    overhead_amr = row_by_case(overhead_rows, 'amr', 'AMR overhead summary')

    baseline_input = files_root / 'baseline/run/input.codex_open_domain_plan_amr_baseline_smoke'
    amr_input = files_root / 'amr/run/input.codex_open_domain_plan_amr_level1_smoke'
    max_step = int(parse_setting(amr_input, 'amr.max_step'))
    plot_int = int(parse_setting(amr_input, 'amr.plot_int'))
    base_n_cell = parse_n_cell(baseline_input)
    amr_n_cell = parse_n_cell(amr_input)
    base_cells = base_n_cell[0] * base_n_cell[1] * base_n_cell[2]
    amr_equiv_fine = (amr_n_cell[0] * 2) * (amr_n_cell[1] * 2) * (amr_n_cell[2] * 2)

    baseline_hybrid = parse_hybrid_validation(files_root / 'baseline/hybrid_validation.log')
    amr_hybrid = parse_hybrid_validation(files_root / 'amr/hybrid_validation.log')
    baseline_plot = plot_metadata(source_root, 'baseline', max_step)
    amr_plot = plot_metadata(source_root, 'amr', max_step)

    baseline = case_summary('baseline', compare_base, overhead_base, baseline_hybrid, baseline_plot)
    amr = case_summary('amr', compare_amr, overhead_amr, amr_hybrid, amr_plot)

    cloud_rel = finite_float(compare_amr['cloud_rel_diff'], 'cloud_rel_diff')
    peak_rel = finite_float(compare_amr['peak_rel_diff'], 'peak_rel_diff')
    centroid_abs = finite_float(compare_amr['centroid_abs_diff'], 'centroid_abs_diff')
    downstream_abs = finite_float(compare_amr['downstream_abs_diff'], 'downstream_abs_diff')
    mean_ncells_ratio = finite_float(overhead_amr['mean_ncells_ratio'], 'mean_ncells_ratio')
    advance_seconds_ratio = finite_float(overhead_amr['advance_seconds_ratio'], 'advance_seconds_ratio')
    final_plotfile_bytes_ratio = finite_float(overhead_amr['final_plotfile_bytes_ratio'], 'final_plotfile_bytes_ratio')

    criteria = {
        'expected_solver': 'pelelmex',
        'expected_mode': 'hybrid',
        'min_ranks': args.min_ranks,
        'min_threads_per_rank': args.min_threads,
        'min_max_step': args.min_max_step,
        'min_plotfiles': args.min_plotfiles,
        'max_cloud_rel_diff': args.max_cloud_rel_diff,
        'max_peak_rel_diff': args.max_peak_rel_diff,
        'max_centroid_abs_diff': args.max_centroid_abs_diff,
        'max_downstream_abs_diff': args.max_downstream_abs_diff,
        'max_advance_seconds_ratio': args.max_advance_seconds_ratio,
    }
    validate_summary(
        baseline,
        amr,
        max_step,
        cloud_rel,
        peak_rel,
        centroid_abs,
        downstream_abs,
        advance_seconds_ratio,
        criteria,
    )

    if max_step >= 120 and base_cells >= 65536:
        scope_line = (
            'This is a production-mesh interactive hybrid MPI/OpenMP CFD scout, '
            'not a scheduler-managed full production campaign.'
        )
    else:
        scope_line = (
            f'This is a short {max_step}-step interactive hybrid MPI/OpenMP CFD scout, '
            'not a scheduler-managed production campaign.'
        )

    report = {
        'schema_version': SCHEMA_VERSION,
        'title': 'Engineering H2 Hybrid MPI/OpenMP CFD Scout',
        'status': 'PASS-HYBRID-CFD-SCOUT',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'case': 'engineering-h2-open-domain-plan-amr-hybrid-cfd-scout',
        'source_log_root': str(source_root),
        'evidence_root': str(evidence_root),
        'criteria': criteria,
        'summary': {
            'ranks': int(amr_hybrid['ranks']),
            'threads_per_rank': int(amr_hybrid['threads']),
            'max_step': max_step,
            'plot_int': plot_int,
            'base_n_cell': list(base_n_cell),
            'base_cell_count': base_cells,
            'amr_n_cell': list(amr_n_cell),
            'amr_equivalent_fine_cell_count': amr_equiv_fine,
            'baseline_plotfiles': baseline['plotfiles'],
            'amr_plotfiles': amr['plotfiles'],
            'baseline_final_time': baseline_hybrid['final_time'],
            'amr_final_time': amr_hybrid['final_time'],
            'amr_finest_level': amr['finest_level'],
            'amr_finest_fab_count': amr['finest_fab_count'],
            'amr_total_fab_count': amr['total_fab_count'],
            'regrid_count': amr['regrid_count'],
            'cloud_rel_diff': cloud_rel,
            'peak_rel_diff': peak_rel,
            'centroid_abs_diff': centroid_abs,
            'downstream_abs_diff': downstream_abs,
            'mean_ncells_ratio': mean_ncells_ratio,
            'advance_seconds_ratio': advance_seconds_ratio,
            'final_plotfile_bytes_ratio': final_plotfile_bytes_ratio,
        },
        'cases': [baseline, amr],
        'files': copied,
        'plotfile_metadata_note': 'Plotfiles are intentionally not copied; only Header hashes and FAB metadata are preserved.',
        'limitations': [
            scope_line,
            'The scout verifies the real PeleLMeX hybrid executable, AMR Level_1 creation, H2 hazard post-processing, and bounded AMR-vs-baseline drift.',
            'It does not prove long-duration hybrid scaling, production-size geometry, queue integration, calibrated fire consequences, or reference-data agreement.',
            'The MPI implementation reports thread support level 0; this run does not request MPI calls from multiple OpenMP threads, so the warning is tracked but accepted for this scout.',
        ],
    }
    return report


def validate_case(case: dict[str, Any], criteria: dict[str, Any]) -> None:
    hv = case.get('hybrid_validation', {}) if isinstance(case.get('hybrid_validation'), dict) else {}
    require(hv.get('solver') == criteria['expected_solver'], f'{case.get("case")} solver mismatch')
    require(hv.get('mode') == criteria['expected_mode'], f'{case.get("case")} mode mismatch')
    require(int(hv.get('ranks', 0)) >= int(criteria['min_ranks']), f'{case.get("case")} rank count too small')
    require(int(hv.get('threads', 0)) >= int(criteria['min_threads_per_rank']), f'{case.get("case")} thread count too small')
    require(int(hv.get('finalized', 0)) == 1, f'{case.get("case")} did not finalize')
    require(finite_number(hv.get('final_time')) and float(hv['final_time']) > 0.0, f'{case.get("case")} final_time invalid')
    require(int(case.get('plotfiles', 0)) >= int(criteria['min_plotfiles']), f'{case.get("case")} plotfiles too few')
    require(0.90 <= float(case.get('mass_ratio', 0.0)) <= 1.10, f'{case.get("case")} mass_ratio out of range')
    require(float(case.get('cloud_volume', 0.0)) > 0.0, f'{case.get("case")} cloud_volume not positive')
    require(float(case.get('cloud_species_mass', 0.0)) > 0.0, f'{case.get("case")} cloud_species_mass not positive')
    require(float(case.get('max_X', 0.0)) > 0.0, f'{case.get("case")} max_X not positive')


def validate_summary(
    baseline: dict[str, Any],
    amr: dict[str, Any],
    max_step: int,
    cloud_rel: float,
    peak_rel: float,
    centroid_abs: float,
    downstream_abs: float,
    advance_seconds_ratio: float,
    criteria: dict[str, Any],
) -> None:
    require(max_step >= int(criteria['min_max_step']), 'max_step too small')
    validate_case(baseline, criteria)
    validate_case(amr, criteria)
    require(int(baseline.get('finest_level', -1)) == 0, 'baseline finest level must be 0')
    require(int(amr.get('finest_level', 0)) >= 1, 'AMR finest level must be at least 1')
    require(int(amr.get('made_level1', 0)) == 1, 'AMR did not make level 1')
    require(int(amr.get('regrid_count', 0)) >= 1, 'AMR did not regrid')
    require(cloud_rel <= float(criteria['max_cloud_rel_diff']), 'cloud_rel_diff too large')
    require(peak_rel <= float(criteria['max_peak_rel_diff']), 'peak_rel_diff too large')
    require(centroid_abs <= float(criteria['max_centroid_abs_diff']), 'centroid_abs_diff too large')
    require(downstream_abs <= float(criteria['max_downstream_abs_diff']), 'downstream_abs_diff too large')
    require(advance_seconds_ratio <= float(criteria['max_advance_seconds_ratio']), 'advance_seconds_ratio too large')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == 'PASS-HYBRID-CFD-SCOUT', 'status mismatch')
    criteria = data.get('criteria') if isinstance(data.get('criteria'), dict) else {}
    summary = data.get('summary') if isinstance(data.get('summary'), dict) else {}
    cases = data.get('cases') if isinstance(data.get('cases'), list) else []
    require(len(cases) == 2, 'expected two case summaries')
    by_case = {case.get('case'): case for case in cases if isinstance(case, dict)}
    require({'baseline', 'amr'} <= set(by_case), 'missing baseline/amr case summaries')
    validate_summary(
        by_case['baseline'],
        by_case['amr'],
        int(summary.get('max_step', 0)),
        float(summary.get('cloud_rel_diff', 1.0e9)),
        float(summary.get('peak_rel_diff', 1.0e9)),
        float(summary.get('centroid_abs_diff', 1.0e9)),
        float(summary.get('downstream_abs_diff', 1.0e9)),
        float(summary.get('advance_seconds_ratio', 1.0e9)),
        criteria,
    )
    for item in data.get('files', []):
        p = Path(str(item.get('path', '')))
        require(p.is_file(), f'missing packaged evidence file: {p}')
        require(sha256_file(p) == item.get('sha256'), f'packaged evidence hash mismatch: {p}')
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        '# Engineering H2 Hybrid MPI/OpenMP CFD Scout',
        '',
        f"Status: `{report['status']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        f"Parallel mode: `{s['ranks']} MPI x {s['threads_per_rank']} OMP`",
        f"Max step / plot interval: `{s['max_step']}` / `{s['plot_int']}`",
        f"AMR finest level / fabs: `{s['amr_finest_level']}` / `{s['amr_finest_fab_count']}`",
        f"Regrid count: `{s['regrid_count']}`",
        f"Cloud rel diff: `{s['cloud_rel_diff']:.8e}`",
        f"Peak-X rel diff: `{s['peak_rel_diff']:.8e}`",
        f"Centroid abs diff: `{s['centroid_abs_diff']:.8e}`",
        f"Downstream abs diff: `{s['downstream_abs_diff']:.8e}`",
        f"Advance seconds ratio: `{s['advance_seconds_ratio']:.8e}`",
        '',
        '## Evidence',
    ]
    for item in report['files']:
        lines.append(f"- `{item['relative_path']}` sha256=`{item['sha256']}`")
    lines.extend(['', '## Limitations'])
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', default=str(DEFAULT_SOURCE_ROOT))
    parser.add_argument('--repo-root', default='.')
    parser.add_argument('--evidence-root')
    parser.add_argument('--output-json', default=str(DEFAULT_EVIDENCE_ROOT / 'hybrid_cfd_scout_report.json'))
    parser.add_argument('--output-md', default=str(DEFAULT_EVIDENCE_ROOT / 'hybrid_cfd_scout_report.md'))
    parser.add_argument('--verify-json')
    parser.add_argument('--min-ranks', type=int, default=4)
    parser.add_argument('--min-threads', type=int, default=2)
    parser.add_argument('--min-max-step', type=int, default=40)
    parser.add_argument('--min-plotfiles', type=int, default=3)
    parser.add_argument('--max-cloud-rel-diff', type=float, default=0.45)
    parser.add_argument('--max-peak-rel-diff', type=float, default=0.50)
    parser.add_argument('--max-centroid-abs-diff', type=float, default=0.08)
    parser.add_argument('--max-downstream-abs-diff', type=float, default=0.15)
    parser.add_argument('--max-advance-seconds-ratio', type=float, default=4.0)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.verify_json and args.evidence_root is None:
        args.evidence_root = str(Path(args.output_json).parent)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            s = report['summary']
            print(
                'engineering_h2_hybrid_cfd_scout_report VERIFY-PASS '
                f"json={args.verify_json} ranks={s['ranks']} threads={s['threads_per_rank']} "
                f"cloud_rel_diff={s['cloud_rel_diff']:.8e} peak_rel_diff={s['peak_rel_diff']:.8e}"
            )
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        write_json(report, output_json)
        write_markdown(report, output_md)
        verify_report(output_json)
        s = report['summary']
        print(
            'engineering_h2_hybrid_cfd_scout_report PASS '
            f"json={output_json} md={output_md} ranks={s['ranks']} threads={s['threads_per_rank']} "
            f"cloud_rel_diff={s['cloud_rel_diff']:.8e} peak_rel_diff={s['peak_rel_diff']:.8e}"
        )
        return 0
    except ReportError as exc:
        print(f'engineering_h2_hybrid_cfd_scout_report FAIL {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
