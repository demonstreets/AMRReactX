#!/usr/bin/env python3
"""Preflight an engineering Backward-Facing Step k-epsilon case.

The preflight is intentionally conservative: it does not claim CFD validation.
It checks whether the input deck is a plausible engineering BFS reference run
before spending compute on a long or parallel solve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PASS_STATUS = 'PASS-BFS-KEPSILON-PREFLIGHT'
NOT_READY_STATUS = 'NOT_READY-BFS-KEPSILON-PREFLIGHT'

DEFAULT_INPUT = Path('examples/engineering/backward_facing_step/input.yaml')
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
    'bfs_kepsilon_preflight_base_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
    'bfs_kepsilon_preflight_base_report.md'
)


class PreflightError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise PreflightError(message)


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


def split_values(value: str) -> list[str]:
    return [part for part in value.strip().split() if part]


def parse_number(value: str) -> float | None:
    parts = split_values(value)
    if len(parts) != 1:
        return None
    try:
        return float(parts[0])
    except ValueError:
        return None


def parse_int_pair(value: str) -> tuple[int, int] | None:
    parts = split_values(value)
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def parse_float_pair(value: str) -> tuple[float, float] | None:
    parts = split_values(value)
    if len(parts) < 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def parse_input(path: Path) -> dict[str, str]:
    require(path.is_file(), f'missing input file: {path}')
    params: dict[str, str] = {}
    for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if key:
            params[key] = value
    return params


def parse_override(text: str) -> tuple[str, str]:
    if '=' not in text:
        raise PreflightError(f'invalid override, expected key=value: {text}')
    key, value = text.split('=', 1)
    key = key.strip()
    value = value.strip()
    require(bool(key), f'invalid override key: {text}')
    require(bool(value), f'invalid override value: {text}')
    return key, value


def rel_close(a: float, b: float, tol: float = 1.0e-9) -> bool:
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= tol * scale


def bool_from_check(ok: bool, gap: str, gaps: list[str]) -> bool:
    if not ok:
        gaps.append(gap)
    return ok


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    input_path = Path(args.input)
    params = parse_input(input_path)
    overrides = [parse_override(text) for text in args.override]
    for key, value in overrides:
        params[key] = value

    gaps: list[str] = []
    diagnostics: list[str] = []

    prob_lo = parse_float_pair(params.get('geometry.prob_lo', ''))
    prob_hi = parse_float_pair(params.get('geometry.prob_hi', ''))
    eb_lo = parse_float_pair(params.get('eb2.box_lo', ''))
    eb_hi = parse_float_pair(params.get('eb2.box_hi', ''))
    n_cell = parse_int_pair(params.get('amr.n_cell', ''))
    blocking_factor_f = parse_number(params.get('amr.blocking_factor', ''))
    max_grid_size_f = parse_number(params.get('amr.max_grid_size', ''))
    max_step_f = parse_number(params.get('amr.max_step', ''))
    stop_time = parse_number(params.get('amr.stop_time', ''))
    dt_shrink = parse_number(params.get('amr.dt_shrink', ''))
    cfl = parse_number(params.get('amr.cfl', ''))

    required_keys = [
        'geometry.prob_lo',
        'geometry.prob_hi',
        'amr.n_cell',
        'amr.blocking_factor',
        'amr.max_grid_size',
        'amr.max_step',
        'amr.stop_time',
        'amr.dt_shrink',
        'amr.cfl',
        'peleLM.les_model',
        'peleLM.ke_wall_functions',
        'eb2.geom_type',
        'eb2.box_lo',
        'eb2.box_hi',
        'eb2.box_has_fluid_inside',
    ]
    missing_keys = [key for key in required_keys if key not in params]
    if missing_keys:
        gaps.append('bfs_required_input_keys_missing')

    nx = ny = 0
    if n_cell is None:
        gaps.append('bfs_grid_n_cell_invalid')
    else:
        nx, ny = n_cell

    blocking_factor = int(blocking_factor_f) if finite(blocking_factor_f) else 0
    max_grid_size = int(max_grid_size_f) if finite(max_grid_size_f) else 0
    max_step = int(max_step_f) if finite(max_step_f) else 0

    dx = dy = None
    step_height = None
    cells_per_step_height = None
    step_x_index = None
    if prob_lo and prob_hi and n_cell and nx > 0 and ny > 0:
        dx = (prob_hi[0] - prob_lo[0]) / nx
        dy = (prob_hi[1] - prob_lo[1]) / ny
    else:
        gaps.append('bfs_domain_or_grid_extent_invalid')

    if eb_lo and eb_hi:
        step_height = eb_hi[1] - eb_lo[1]
    else:
        gaps.append('bfs_eb_step_box_invalid')

    if dx is not None and dy is not None:
        bool_from_check(rel_close(dx, dy, 1.0e-6), 'bfs_grid_cells_not_square', gaps)
    if step_height is not None and dy is not None and dy > 0:
        cells_per_step_height = step_height / dy
        bool_from_check(
            cells_per_step_height >= args.min_cells_per_h,
            'bfs_step_height_resolution_below_engineering_minimum',
            gaps,
        )
    if prob_lo and dx is not None and dx > 0:
        step_x_index = (0.0 - prob_lo[0]) / dx
        bool_from_check(
            abs(step_x_index - round(step_x_index)) <= 1.0e-6,
            'bfs_step_x0_not_grid_aligned',
            gaps,
        )

    if n_cell:
        bool_from_check(nx >= args.min_nx and ny >= args.min_ny, 'bfs_grid_below_engineering_minimum', gaps)
        if blocking_factor > 0:
            bool_from_check(
                nx % blocking_factor == 0 and ny % blocking_factor == 0,
                'bfs_grid_not_divisible_by_blocking_factor',
                gaps,
            )
        else:
            gaps.append('bfs_blocking_factor_invalid')
    if max_grid_size <= 0:
        gaps.append('bfs_max_grid_size_invalid')
    elif n_cell and max(nx, ny) > max_grid_size and blocking_factor > 0:
        diagnostics.append('bfs_domain_will_split_into_multiple_boxes')

    bool_from_check(params.get('peleLM.les_model') == 'kepsilon', 'bfs_kepsilon_model_not_enabled', gaps)
    bool_from_check(params.get('peleLM.ke_wall_functions') == '1', 'bfs_kepsilon_wall_functions_not_enabled', gaps)
    bool_from_check(params.get('eb2.geom_type') == 'box', 'bfs_eb_box_geometry_not_enabled', gaps)
    bool_from_check(params.get('eb2.box_has_fluid_inside') == '0', 'bfs_eb_step_solid_box_not_configured', gaps)

    if stop_time is None:
        gaps.append('bfs_stop_time_invalid')
    else:
        bool_from_check(stop_time >= args.min_stop_time, 'bfs_stop_time_below_reference_duration', gaps)
    if max_step <= 0:
        gaps.append('bfs_max_step_invalid')
    else:
        bool_from_check(max_step >= args.min_max_step, 'bfs_max_step_below_reference_duration', gaps)
    if cfl is None:
        gaps.append('bfs_cfl_invalid')
    else:
        bool_from_check(cfl <= args.max_cfl, 'bfs_cfl_above_refined_grid_stability_limit', gaps)
    if dt_shrink is None:
        gaps.append('bfs_dt_shrink_invalid')
    else:
        bool_from_check(
            dt_shrink <= args.max_dt_shrink,
            'bfs_dt_shrink_above_refined_grid_stability_limit',
            gaps,
        )

    high_nan_risk = bool(
        n_cell
        and nx >= args.min_nx
        and ny >= args.min_ny
        and (
            (cfl is not None and cfl > args.max_cfl)
            or (dt_shrink is not None and dt_shrink > args.max_dt_shrink)
        )
    )
    if high_nan_risk:
        diagnostics.append('bfs_refined_grid_high_nan_risk_from_cfl_or_dt_shrink')

    status = PASS_STATUS if not gaps else NOT_READY_STATUS
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering BFS k-epsilon Case Preflight',
        'label': args.label,
        'input_file': str(input_path),
        'input_sha256': sha256_file(input_path),
        'overrides': [{'key': key, 'value': value} for key, value in overrides],
        'thresholds': {
            'min_nx': args.min_nx,
            'min_ny': args.min_ny,
            'min_cells_per_h': args.min_cells_per_h,
            'min_stop_time': args.min_stop_time,
            'min_max_step': args.min_max_step,
            'max_cfl': args.max_cfl,
            'max_dt_shrink': args.max_dt_shrink,
        },
        'summary': {
            'status': status,
            'nx': nx,
            'ny': ny,
            'dx': dx,
            'dy': dy,
            'step_height': step_height,
            'cells_per_step_height': cells_per_step_height,
            'step_x_index': step_x_index,
            'grid_aligned_to_step_x0': (
                abs(step_x_index - round(step_x_index)) <= 1.0e-6
                if finite(step_x_index) else False
            ),
            'blocking_factor': blocking_factor,
            'max_grid_size': max_grid_size,
            'max_step': max_step,
            'stop_time': stop_time,
            'cfl': cfl,
            'dt_shrink': dt_shrink,
            'kepsilon_enabled': params.get('peleLM.les_model') == 'kepsilon',
            'wall_functions_enabled': params.get('peleLM.ke_wall_functions') == '1',
            'eb_box_step_configured': (
                params.get('eb2.geom_type') == 'box'
                and params.get('eb2.box_has_fluid_inside') == '0'
                and eb_lo is not None
                and eb_hi is not None
            ),
            'missing_required_keys': missing_keys,
            'high_nan_risk_refined_grid': high_nan_risk,
            'blocks_production_readiness': status != PASS_STATUS,
        },
        'blocking_gaps': gaps,
        'diagnostic_gaps': diagnostics,
        'limitations': [
            'This preflight checks input-deck readiness only; it does not replace CFD reference validation.',
            'PASS means the case is suitable to attempt an engineering BFS k-epsilon reference run, not that the run will pass.',
            'The CFL and dt_shrink thresholds are set from observed refined-grid NaN sensitivity and should be tightened when better evidence is available.',
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        '# Engineering BFS k-epsilon Case Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Label: `{report['label']}`",
        '',
        '## Summary',
        '',
        f"- Grid: `{s['nx']} x {s['ny']}`",
        f"- dx/dy: `{s['dx']}` / `{s['dy']}`",
        f"- Cells per step height: `{s['cells_per_step_height']}`",
        f"- Step x=0 grid aligned: `{s['grid_aligned_to_step_x0']}`",
        f"- max_step/stop_time: `{s['max_step']}` / `{s['stop_time']}`",
        f"- CFL/dt_shrink: `{s['cfl']}` / `{s['dt_shrink']}`",
        f"- High NaN risk on refined grid: `{s['high_nan_risk_refined_grid']}`",
        '',
        '## Blocking Gaps',
        '',
    ]
    if report['blocking_gaps']:
        for item in report['blocking_gaps']:
            lines.append(f'- `{item}`')
    else:
        lines.append('- none')
    lines += ['', '## Diagnostic Gaps', '']
    if report['diagnostic_gaps']:
        for item in report['diagnostic_gaps']:
            lines.append(f'- `{item}`')
    else:
        lines.append('- none')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise PreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise PreflightError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == SCHEMA_VERSION, f'schema_version mismatch in {path}')
    require(data.get('status') in {PASS_STATUS, NOT_READY_STATUS}, f'invalid status in {path}')
    summary = data.get('summary', {})
    require(isinstance(summary, dict), 'summary missing or not an object')
    require(isinstance(summary.get('blocks_production_readiness'), bool), 'missing production blocker boolean')
    require(Path(data.get('input_file', '')).is_file(), 'input_file missing')
    require(sha256_file(Path(data['input_file'])) == data.get('input_sha256'), 'input_file hash mismatch')
    gaps = data.get('blocking_gaps', [])
    require(isinstance(gaps, list), 'blocking_gaps missing or not a list')
    if data.get('status') == PASS_STATUS:
        require(not gaps, 'PASS report must not have blocking gaps')
        require(summary.get('blocks_production_readiness') is False, 'PASS report blocks production')
    else:
        require(bool(gaps), 'NOT_READY report must list blocking gaps')
        require(summary.get('blocks_production_readiness') is True, 'NOT_READY report must block production')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', default=str(DEFAULT_INPUT))
    ap.add_argument('--label', default='base_104x28_current_input')
    ap.add_argument('--override', action='append', default=[], help='Override one input key, e.g. amr.cfl=0.05')
    ap.add_argument('--min-nx', type=int, default=208)
    ap.add_argument('--min-ny', type=int, default=56)
    ap.add_argument('--min-cells-per-h', type=float, default=6.0)
    ap.add_argument('--min-stop-time', type=float, default=0.5)
    ap.add_argument('--min-max-step', type=int, default=5000)
    ap.add_argument('--max-cfl', type=float, default=0.10)
    ap.add_argument('--max-dt-shrink', type=float, default=0.01)
    ap.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)

    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            s = data['summary']
            print(
                'engineering_bfs_kepsilon_case_preflight VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"grid={s.get('nx')}x{s.get('ny')} gaps={len(data.get('blocking_gaps', []))}"
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
            'engineering_bfs_kepsilon_case_preflight PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except PreflightError as exc:
        print(f'engineering_bfs_kepsilon_case_preflight FAIL {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
