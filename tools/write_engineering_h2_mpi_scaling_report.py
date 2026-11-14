#!/usr/bin/env python3
"""Write and verify an engineering H2 production-mesh MPI scaling scout report."""
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

DEFAULT_REPORTS = [
    Path('docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json'),
    Path('docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json'),
    Path('docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json'),
]

class ScalingError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScalingError(message)


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
        raise ScalingError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ScalingError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def case_report_path(report: dict[str, Any]) -> Path:
    for item in report.get('files', []):
        if item.get('label') == 'engineering_case_report_json' or str(item.get('path', '')).endswith('/engineering_case_report.json'):
            return Path(str(item['path']))
    raise ScalingError(f"missing engineering_case_report_json in {report.get('case')}")


def report_row(report_path: Path) -> dict[str, Any]:
    report = load_json(report_path)
    summary = report.get('summary') if isinstance(report.get('summary'), dict) else {}
    case_path = case_report_path(report)
    case = load_json(case_path)
    reduced = case.get('reduced_long', {}) if isinstance(case.get('reduced_long'), dict) else {}
    overhead = case.get('amr_overhead', {}) if isinstance(case.get('amr_overhead'), dict) else {}
    compare = case.get('plan_amr_compare', {}) if isinstance(case.get('plan_amr_compare'), dict) else {}
    amr = reduced.get('amr', {}) if isinstance(reduced.get('amr'), dict) else {}
    baseline = reduced.get('baseline', {}) if isinstance(reduced.get('baseline'), dict) else {}
    deltas = reduced.get('amr_deltas', {}) if isinstance(reduced.get('amr_deltas'), dict) else {}
    ratios = overhead.get('amr_ratios', {}) if isinstance(overhead.get('amr_ratios'), dict) else {}
    amr_overhead = overhead.get('amr', {}) if isinstance(overhead.get('amr'), dict) else {}
    baseline_overhead = overhead.get('baseline', {}) if isinstance(overhead.get('baseline'), dict) else {}
    compare_amr = compare.get('amr', {}) if isinstance(compare.get('amr'), dict) else {}
    compare_baseline = compare.get('baseline', {}) if isinstance(compare.get('baseline'), dict) else {}

    ranks = int(summary.get('ranks', amr.get('ranks', 0)))
    row = {
        'report_path': str(report_path),
        'report_sha256': sha256_file(report_path),
        'case_report_path': str(case_path),
        'case_report_sha256': sha256_file(case_path),
        'case': report.get('case'),
        'status': report.get('status'),
        'ranks': ranks,
        'max_step': int(summary.get('max_step', amr.get('max_step', 0))),
        'baseline_plotfiles': int(summary.get('baseline_plotfiles', baseline.get('plotfiles', 0))),
        'amr_plotfiles': int(summary.get('amr_plotfiles', amr.get('plotfiles', 0))),
        'base_cell_count': int(summary.get('base_cell_count', 0)),
        'amr_equivalent_fine_cell_count': int(summary.get('amr_equivalent_fine_cell_count', 0)),
        'baseline_fabs': baseline.get('fabs'),
        'amr_fabs': amr.get('fabs'),
        'baseline_finest_fab_count': compare_baseline.get('finest_fab_count'),
        'amr_finest_fab_count': compare_amr.get('finest_fab_count'),
        'cloud_rel_diff': float(deltas.get('cloud_rel_diff', summary.get('cloud_rel_diff'))),
        'peak_rel_diff': float(deltas.get('peak_rel_diff', summary.get('peak_rel_diff'))),
        'centroid_abs_diff': float(deltas.get('centroid_abs_diff')),
        'downstream_abs_diff': float(deltas.get('downstream_abs_diff')),
        'mean_ncells_ratio': float(ratios.get('mean_ncells_ratio', summary.get('mean_ncells_ratio'))),
        'advance_seconds_ratio': float(ratios.get('advance_seconds_ratio', summary.get('advance_seconds_ratio'))),
        'final_plotfile_bytes_ratio': float(ratios.get('final_plotfile_bytes_ratio')),
        'baseline_advance_seconds': float(baseline_overhead.get('advance_seconds')),
        'amr_advance_seconds': float(amr_overhead.get('advance_seconds')),
    }
    return row


def assert_row(row: dict[str, Any]) -> None:
    require(row['status'] == 'PASS-SCOUT', f"{row['report_path']} status is not PASS-SCOUT")
    require(row['ranks'] in {4, 8, 16}, f"unexpected rank count {row['ranks']}")
    require(row['max_step'] >= 120, f"rank {row['ranks']} max_step too small")
    require(row['baseline_plotfiles'] >= 5 and row['amr_plotfiles'] >= 5, f"rank {row['ranks']} plotfiles too small")
    require(row['base_cell_count'] >= 60000, f"rank {row['ranks']} base cell count too small")
    require(row['amr_equivalent_fine_cell_count'] >= 500000, f"rank {row['ranks']} fine cell count too small")
    for key in ['cloud_rel_diff', 'peak_rel_diff', 'centroid_abs_diff', 'downstream_abs_diff', 'mean_ncells_ratio', 'advance_seconds_ratio', 'baseline_advance_seconds', 'amr_advance_seconds']:
        require(finite(row.get(key)), f"rank {row['ranks']} nonfinite {key}")
    require(row['cloud_rel_diff'] <= 0.20, f"rank {row['ranks']} cloud_rel_diff too high")
    require(row['peak_rel_diff'] <= 0.20, f"rank {row['ranks']} peak_rel_diff too high")
    require(row['centroid_abs_diff'] <= 0.01, f"rank {row['ranks']} centroid drift too high")
    require(row['downstream_abs_diff'] <= 0.02, f"rank {row['ranks']} downstream drift too high")
    require(row['mean_ncells_ratio'] <= 4.0, f"rank {row['ranks']} mean_ncells_ratio too high")
    require(row['advance_seconds_ratio'] <= 4.0, f"rank {row['ranks']} advance_seconds_ratio too high")
    require(int(row.get('baseline_finest_fab_count') or 0) >= row['ranks'], f"rank {row['ranks']} baseline FAB count below rank count")
    require(int(row.get('amr_finest_fab_count') or 0) >= row['ranks'], f"rank {row['ranks']} AMR finest FAB count below rank count")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report_paths = [Path(p) for p in args.report]
    rows = [report_row(p) for p in report_paths]
    rows.sort(key=lambda r: r['ranks'])
    require([r['ranks'] for r in rows] == [4, 8, 16], f"expected rank series [4, 8, 16], got {[r['ranks'] for r in rows]}")
    for row in rows:
        assert_row(row)

    base_cells = {r['base_cell_count'] for r in rows}
    fine_cells = {r['amr_equivalent_fine_cell_count'] for r in rows}
    max_steps = {r['max_step'] for r in rows}
    require(len(base_cells) == 1 and len(fine_cells) == 1 and len(max_steps) == 1, 'rank rows do not use the same mesh/step configuration')

    cloud_values = [r['cloud_rel_diff'] for r in rows]
    peak_values = [r['peak_rel_diff'] for r in rows]
    overhead_values = [r['advance_seconds_ratio'] for r in rows]
    baseline_times = [r['baseline_advance_seconds'] for r in rows]
    amr_times = [r['amr_advance_seconds'] for r in rows]
    require(max(cloud_values) - min(cloud_values) <= args.max_hazard_rel_spread, 'cloud_rel_diff spread across ranks too large')
    require(max(peak_values) - min(peak_values) <= args.max_hazard_rel_spread, 'peak_rel_diff spread across ranks too large')
    require(max(overhead_values) <= args.max_amr_overhead_ratio, 'AMR overhead ratio too large across ranks')
    require(baseline_times[0] > baseline_times[-1], 'baseline runtime does not improve from 4 to 16 ranks')
    require(amr_times[0] > amr_times[-1], 'AMR runtime does not improve from 4 to 16 ranks')

    b4 = rows[0]['baseline_advance_seconds']
    a4 = rows[0]['amr_advance_seconds']
    for row in rows:
        row['baseline_speedup_vs_4rank'] = b4 / row['baseline_advance_seconds']
        row['amr_speedup_vs_4rank'] = a4 / row['amr_advance_seconds']
        row['baseline_parallel_efficiency_vs_4rank'] = row['baseline_speedup_vs_4rank'] / (row['ranks'] / 4.0)
        row['amr_parallel_efficiency_vs_4rank'] = row['amr_speedup_vs_4rank'] / (row['ranks'] / 4.0)

    report = {
        'schema_version': SCHEMA_VERSION,
        'status': 'PASS-SCALING-SCOUT',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'scaling_type': 'engineering-h2-production-mesh-amr-mpi-short-scout',
        'rank_series': [r['ranks'] for r in rows],
        'criteria': {
            'max_hazard_rel_spread': args.max_hazard_rel_spread,
            'max_amr_overhead_ratio': args.max_amr_overhead_ratio,
            'require_runtime_improvement_4_to_16': True,
            'require_finest_fabs_at_least_ranks': True,
        },
        'summary': {
            'rank_count': len(rows),
            'base_cell_count': rows[0]['base_cell_count'],
            'amr_equivalent_fine_cell_count': rows[0]['amr_equivalent_fine_cell_count'],
            'max_step': rows[0]['max_step'],
            'cloud_rel_diff_spread': max(cloud_values) - min(cloud_values),
            'peak_rel_diff_spread': max(peak_values) - min(peak_values),
            'max_advance_seconds_ratio': max(overhead_values),
            'baseline_speedup_4_to_16': rows[-1]['baseline_speedup_vs_4rank'],
            'amr_speedup_4_to_16': rows[-1]['amr_speedup_vs_4rank'],
            'baseline_efficiency_4_to_16': rows[-1]['baseline_parallel_efficiency_vs_4rank'],
            'amr_efficiency_4_to_16': rows[-1]['amr_parallel_efficiency_vs_4rank'],
            'rank16_amr_finest_fab_count': rows[-1]['amr_finest_fab_count'],
        },
        'rank_rows': rows,
        'evidence_files': [evidence_entry(f'production_mesh_{r["ranks"]}rank_scout_report', Path(r['report_path'])) for r in rows] + [evidence_entry(f'production_mesh_{r["ranks"]}rank_case_report', Path(r['case_report_path'])) for r in rows],
        'limitations': [
            'This is a short interactive production-mesh scaling scout, not a scheduler-managed performance study.',
            'It verifies rank consistency, bounded AMR-vs-baseline hazard drift, FAB distribution, and runtime improvement from 4 to 16 ranks on one synthetic H2 leak case.',
            'It does not prove production-size scaling, queue/affinity behavior, hybrid MPI/OpenMP safety, overnight stability, real-CAD geometry, or external reference-data agreement.',
        ],
    }
    return report


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == SCHEMA_VERSION, f'{path} schema_version mismatch')
    require(data.get('status') == 'PASS-SCALING-SCOUT', f'{path} status is not PASS-SCALING-SCOUT')
    rows = data.get('rank_rows')
    require(isinstance(rows, list) and len(rows) == 3, f'{path} rank_rows must have 3 rows')
    require([int(r.get('ranks', 0)) for r in rows] == [4, 8, 16], f'{path} rank series mismatch')
    for row in rows:
        assert_row(row)
    summary = data.get('summary') if isinstance(data.get('summary'), dict) else {}
    require(finite(summary.get('baseline_speedup_4_to_16')) and float(summary['baseline_speedup_4_to_16']) > 1.0, 'missing baseline 4-to-16 speedup')
    require(finite(summary.get('amr_speedup_4_to_16')) and float(summary['amr_speedup_4_to_16']) > 1.0, 'missing AMR 4-to-16 speedup')
    for item in data.get('evidence_files', []):
        p = Path(str(item.get('path', '')))
        require(p.is_file(), f'missing evidence file: {p}')
        require(sha256_file(p) == item.get('sha256'), f'evidence hash mismatch: {p}')
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        '# Engineering H2 Production-Mesh MPI Scaling Scout',
        '',
        f"Status: `{report['status']}`",
        f"Rank series: `{report['rank_series']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        f"Base cells: `{s['base_cell_count']}`",
        f"AMR equivalent fine cells: `{s['amr_equivalent_fine_cell_count']}`",
        f"Max step: `{s['max_step']}`",
        f"Cloud rel diff spread: `{s['cloud_rel_diff_spread']:.8e}`",
        f"Peak rel diff spread: `{s['peak_rel_diff_spread']:.8e}`",
        f"Max AMR advance seconds ratio: `{s['max_advance_seconds_ratio']:.8e}`",
        f"Baseline speedup 4-to-16: `{s['baseline_speedup_4_to_16']:.8e}`",
        f"AMR speedup 4-to-16: `{s['amr_speedup_4_to_16']:.8e}`",
        f"16-rank AMR finest FAB count: `{s['rank16_amr_finest_fab_count']}`",
        '',
        '## Rank Rows',
        '',
        '| Ranks | Baseline s | AMR s | AMR/baseline | Cloud rel | Peak rel | AMR FABs | Baseline speedup | AMR speedup |',
        '| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for row in report['rank_rows']:
        lines.append(
            f"| {row['ranks']} | {row['baseline_advance_seconds']:.6f} | {row['amr_advance_seconds']:.6f} | "
            f"{row['advance_seconds_ratio']:.6f} | {row['cloud_rel_diff']:.8e} | {row['peak_rel_diff']:.8e} | "
            f"{row['amr_finest_fab_count']} | {row['baseline_speedup_vs_4rank']:.6f} | {row['amr_speedup_vs_4rank']:.6f} |"
        )
    lines.extend(['', '## Evidence Files', ''])
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines.extend(['', '## Limitations', ''])
    for item in report['limitations']:
        lines.append(f'- {item}')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report', action='append', default=[], help='Production-mesh scout report JSON; defaults to 4/8/16 rank reports')
    ap.add_argument('--output-json')
    ap.add_argument('--output-md')
    ap.add_argument('--verify-json')
    ap.add_argument('--max-hazard-rel-spread', type=float, default=1.0e-10)
    ap.add_argument('--max-amr-overhead-ratio', type=float, default=4.0)
    args = ap.parse_args(argv)
    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            s = data['summary']
            print(
                'engineering_h2_mpi_scaling_report VERIFY-PASS '
                f"json={args.verify_json} ranks={data['rank_series']} "
                f"baseline_speedup_4_to_16={s['baseline_speedup_4_to_16']:.8e} "
                f"amr_speedup_4_to_16={s['amr_speedup_4_to_16']:.8e}"
            )
            return 0
        if not args.report:
            args.report = [str(p) for p in DEFAULT_REPORTS]
        if not args.output_json or not args.output_md:
            raise ScalingError('--output-json and --output-md are required unless --verify-json is used')
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        s = report['summary']
        print(
            'engineering_h2_mpi_scaling_report PASS '
            f"json={out_json} md={out_md} ranks={report['rank_series']} "
            f"baseline_speedup_4_to_16={s['baseline_speedup_4_to_16']:.8e} "
            f"amr_speedup_4_to_16={s['amr_speedup_4_to_16']:.8e}"
        )
        return 0
    except (ScalingError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f'engineering_h2_mpi_scaling_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
