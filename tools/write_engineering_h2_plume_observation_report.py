#!/usr/bin/env python3
"""Extract H2 plume extents and point-probe observations from AMReX plotfiles."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader  # noqa: E402
from validate_h2_leak_hazard_summary import (  # noqa: E402
    field3,
    fluid_volume_fraction,
    species_mole_fraction,
)

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-PLUME-OBSERVATION'

DEFAULT_RUN_DIR = Path(
    'docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run/cases/'
    'plan-amr-mpi-reduced-long/amr/run'
)
DEFAULT_OUTPUT_DIR = Path(
    'docs/codex_audit/evidence/engineering_h2_plume_observation_20260723'
)
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_DIR / 'h2_plume_observation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_DIR / 'h2_plume_observation_report.md'
DEFAULT_EXTENTS_CSV = DEFAULT_OUTPUT_DIR / 'plume_extents.csv'
DEFAULT_SENSORS_CSV = DEFAULT_OUTPUT_DIR / 'sensor_timeseries.csv'


class ObservationError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ObservationError(message)


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


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ObservationError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ObservationError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def discover_plotfiles(run_dir: Path) -> list[Path]:
    require(run_dir.is_dir(), f'run directory missing: {run_dir}')
    paths: list[Path] = []
    for item in run_dir.iterdir():
        if item.is_dir() and re.fullmatch(r'plt\d+', item.name) and (item / 'Header').is_file():
            paths.append(item)
    return sorted(paths, key=lambda p: int(p.name[3:]))


def default_sensors(pf: dict[str, Any]) -> list[dict[str, Any]]:
    x = np.asarray(pf['x'], dtype=float)
    y = np.asarray(pf['y'], dtype=float)
    z = np.asarray(pf.get('z', [0.0]), dtype=float)
    yc = float(y[len(y) // 2])
    zc = float(z[len(z) // 2])
    return [
        {'id': 'domain_line_25pct', 'x': float(x[len(x) // 4]), 'y': yc, 'z': zc},
        {'id': 'domain_line_50pct', 'x': float(x[len(x) // 2]), 'y': yc, 'z': zc},
        {'id': 'domain_line_75pct', 'x': float(x[(3 * len(x)) // 4]), 'y': yc, 'z': zc},
    ]


def load_sensors(path: str | None, first_pf: dict[str, Any]) -> tuple[str, list[dict[str, Any]], Path | None]:
    if not path:
        return 'default_domain_centerline_not_external_benchmark', default_sensors(first_pf), None
    sensor_path = Path(path)
    data = load_json(sensor_path)
    require(data.get('schema_version') == 1, 'sensor schema_version must be 1')
    sensors = data.get('sensors')
    require(isinstance(sensors, list) and sensors, 'sensor list missing')
    cleaned: list[dict[str, Any]] = []
    for idx, sensor in enumerate(sensors):
        require(isinstance(sensor, dict), f'sensor {idx} is not an object')
        sid = str(sensor.get('id', f'sensor_{idx}')).strip()
        require(bool(sid), f'sensor {idx} id missing')
        coords = {axis: sensor.get(axis) for axis in ('x', 'y', 'z')}
        for axis, value in coords.items():
            require(finite(value), f'sensor {sid} coordinate {axis} is not finite')
        cleaned.append({'id': sid, 'x': float(coords['x']), 'y': float(coords['y']), 'z': float(coords['z'])})
    return str(data.get('sensor_basis', 'user_supplied')), cleaned, sensor_path


def validate_sensors_inside_domain(sensors: list[dict[str, Any]], pf: dict[str, Any]) -> None:
    lo = [float(v) for v in pf['prob_lo']]
    hi = [float(v) for v in pf['prob_hi']]
    axes = ('x', 'y', 'z')
    for sensor in sensors:
        for axis_index, axis in enumerate(axes):
            value = float(sensor[axis])
            require(
                lo[axis_index] - 1.0e-12 <= value <= hi[axis_index] + 1.0e-12,
                (
                    f"sensor {sensor['id']} coordinate {axis}={value:.12e} "
                    f"outside domain [{lo[axis_index]:.12e}, {hi[axis_index]:.12e}]"
                ),
            )


def nearest_index(coords: np.ndarray, value: float, label: str) -> int:
    require(coords.size > 0, f'empty coordinate array for {label}')
    idx = int(np.argmin(np.abs(coords - float(value))))
    return idx


def bracket_indices(coords: np.ndarray, value: float, label: str) -> tuple[int, int, float]:
    require(coords.size > 0, f'empty coordinate array for {label}')
    x = float(value)
    require(
        float(coords[0]) - 1.0e-12 <= x <= float(coords[-1]) + 1.0e-12,
        (
            f'{label}={x:.12e} outside cell-center interpolation range '
            f'[{float(coords[0]):.12e}, {float(coords[-1]):.12e}]'
        ),
    )
    if coords.size == 1:
        return 0, 0, 0.0
    hi = int(np.searchsorted(coords, x, side='left'))
    if hi <= 0:
        return 0, 0, 0.0
    if hi >= coords.size:
        last = int(coords.size - 1)
        return last, last, 0.0
    lo = hi - 1
    denom = float(coords[hi] - coords[lo])
    require(denom > 0.0, f'non-increasing coordinate array for {label}')
    weight = (x - float(coords[lo])) / denom
    return lo, hi, float(weight)


def trilinear_sample(
    values: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    sensor: dict[str, Any],
) -> float:
    i0, i1, wx = bracket_indices(x, float(sensor['x']), 'sensor x')
    j0, j1, wy = bracket_indices(y, float(sensor['y']), 'sensor y')
    k0, k1, wz = bracket_indices(z, float(sensor['z']), 'sensor z')
    value = 0.0
    for ii, ax in ((i0, 1.0 - wx), (i1, wx)):
        for jj, ay in ((j0, 1.0 - wy), (j1, wy)):
            for kk, az in ((k0, 1.0 - wz), (k1, wz)):
                weight = ax * ay * az
                if weight != 0.0:
                    value += weight * float(values[ii, jj, kk])
    return value


def plume_metrics(pf: dict[str, Any], species: str, lfl: float, ufl: float) -> tuple[dict[str, Any], np.ndarray]:
    fields = pf['fields']
    raw_shape = field3(fields, 'density').shape
    volume_fraction = fluid_volume_fraction(fields, raw_shape)
    fluid = volume_fraction > 0.0
    x_sp = species_mole_fraction(fields, species, volume_fraction)
    require(np.all(np.isfinite(x_sp[fluid])), f'non-finite fluid X({species})')
    cloud = (x_sp >= lfl) & (x_sp <= ufl) & fluid
    cell_volume = float(np.prod(np.asarray(pf['dx'][:pf['ndim']], dtype=float)))
    cell_volumes = cell_volume * volume_fraction
    peak_index = np.unravel_index(int(np.argmax(np.where(fluid, x_sp, -1.0))), x_sp.shape)

    metrics: dict[str, Any] = {
        'time': float(pf['time']),
        'cloud_cells': int(np.count_nonzero(cloud)),
        'cloud_volume': float(np.sum(cell_volumes[cloud])),
        'peak_X': float(np.max(x_sp[fluid])) if np.any(fluid) else 0.0,
        'peak_i': int(peak_index[0]),
        'peak_j': int(peak_index[1]),
        'peak_k': int(peak_index[2]) if len(peak_index) > 2 else 0,
    }
    x = np.asarray(pf['x'], dtype=float)
    y = np.asarray(pf['y'], dtype=float)
    z = np.asarray(pf.get('z', [0.0]), dtype=float)
    metrics.update({
        'peak_x': float(x[peak_index[0]]),
        'peak_y': float(y[peak_index[1]]),
        'peak_z': float(z[peak_index[2]]) if len(peak_index) > 2 else float(z[0]),
    })
    if metrics['cloud_cells'] > 0:
        ix, iy, iz = np.where(cloud) if cloud.ndim == 3 else (*np.where(cloud), np.zeros(metrics['cloud_cells'], dtype=int))
        metrics.update({
            'flammable_x_min': float(x[int(np.min(ix))]),
            'flammable_x_max': float(x[int(np.max(ix))]),
            'flammable_y_min': float(y[int(np.min(iy))]),
            'flammable_y_max': float(y[int(np.max(iy))]),
            'flammable_z_min': float(z[int(np.min(iz))]),
            'flammable_z_max': float(z[int(np.max(iz))]),
            'flammable_x_extent': float(x[int(np.max(ix))] - x[int(np.min(ix))]),
            'flammable_y_extent': float(y[int(np.max(iy))] - y[int(np.min(iy))]),
            'flammable_z_extent': float(z[int(np.max(iz))] - z[int(np.min(iz))]),
        })
    else:
        for key in (
            'flammable_x_min', 'flammable_x_max', 'flammable_y_min', 'flammable_y_max',
            'flammable_z_min', 'flammable_z_max', 'flammable_x_extent',
            'flammable_y_extent', 'flammable_z_extent',
        ):
            metrics[key] = None
    return metrics, x_sp


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    if not (0.0 <= args.lfl < args.ufl <= 1.0):
        raise ObservationError('invalid LFL/UFL bounds')
    require(args.sensor_sampling in {'trilinear', 'nearest'}, 'invalid sensor sampling mode')
    run_dir = Path(args.run_dir)
    plotfiles = discover_plotfiles(run_dir)
    require(len(plotfiles) >= args.min_plotfiles, f'plotfile count {len(plotfiles)} below minimum {args.min_plotfiles}')
    first_pf = amrex_reader.read_plotfile(str(plotfiles[0]))
    require(first_pf['ndim'] == 3, f'expected 3D plotfiles, got ndim={first_pf["ndim"]}')
    sensor_basis, sensors, sensor_path = load_sensors(args.sensors_json, first_pf)
    require(len(sensors) >= args.min_sensors, f'sensor count {len(sensors)} below minimum {args.min_sensors}')
    validate_sensors_inside_domain(sensors, first_pf)

    extent_rows: list[dict[str, Any]] = []
    sensor_rows: list[dict[str, Any]] = []
    max_cloud_volume = 0.0
    max_peak_x = 0.0
    max_flammable_x = None
    max_flammable_z = None
    max_sensor_sample_distance = 0.0
    times: list[float] = []

    for plotfile in plotfiles:
        pf = amrex_reader.read_plotfile(str(plotfile))
        require(pf['ndim'] == 3, f'expected 3D plotfile: {plotfile}')
        metrics, x_sp = plume_metrics(pf, args.species, args.lfl, args.ufl)
        times.append(float(metrics['time']))
        max_cloud_volume = max(max_cloud_volume, float(metrics['cloud_volume']))
        max_peak_x = max(max_peak_x, float(metrics['peak_X']))
        if metrics['flammable_x_max'] is not None:
            max_flammable_x = (
                float(metrics['flammable_x_max']) if max_flammable_x is None
                else max(max_flammable_x, float(metrics['flammable_x_max']))
            )
        if metrics['flammable_z_max'] is not None:
            max_flammable_z = (
                float(metrics['flammable_z_max']) if max_flammable_z is None
                else max(max_flammable_z, float(metrics['flammable_z_max']))
            )
        extent_rows.append({'plotfile': plotfile.name, **metrics})
        x = np.asarray(pf['x'], dtype=float)
        y = np.asarray(pf['y'], dtype=float)
        z = np.asarray(pf.get('z', [0.0]), dtype=float)
        for sensor in sensors:
            i = nearest_index(x, float(sensor['x']), 'x')
            j = nearest_index(y, float(sensor['y']), 'y')
            k = nearest_index(z, float(sensor['z']), 'z')
            nearest_cell_distance = math.sqrt(
                (float(sensor['x']) - float(x[i])) ** 2
                + (float(sensor['y']) - float(y[j])) ** 2
                + (float(sensor['z']) - float(z[k])) ** 2
            )
            sample_value = (
                trilinear_sample(x_sp, x, y, z, sensor)
                if args.sensor_sampling == 'trilinear' else float(x_sp[i, j, k])
            )
            max_sensor_sample_distance = max(max_sensor_sample_distance, nearest_cell_distance)
            sensor_rows.append({
                'plotfile': plotfile.name,
                'time': f'{float(metrics["time"]):.12e}',
                'sensor_id': sensor['id'],
                'sensor_sampling': args.sensor_sampling,
                'requested_x': f'{float(sensor["x"]):.12e}',
                'requested_y': f'{float(sensor["y"]):.12e}',
                'requested_z': f'{float(sensor["z"]):.12e}',
                'sample_x': f'{float(sensor["x"] if args.sensor_sampling == "trilinear" else x[i]):.12e}',
                'sample_y': f'{float(sensor["y"] if args.sensor_sampling == "trilinear" else y[j]):.12e}',
                'sample_z': f'{float(sensor["z"] if args.sensor_sampling == "trilinear" else z[k]):.12e}',
                'nearest_cell_x': f'{float(x[i]):.12e}',
                'nearest_cell_y': f'{float(y[j]):.12e}',
                'nearest_cell_z': f'{float(z[k]):.12e}',
                'nearest_cell_distance': f'{nearest_cell_distance:.12e}',
                'sample_distance': f'{nearest_cell_distance:.12e}',
                f'X({args.species})': f'{sample_value:.12e}',
                'inside_flammable_limits': bool(args.lfl <= sample_value <= args.ufl),
            })

    require(np.all(np.diff(np.asarray(times)) > 0.0), 'plotfile times are not strictly increasing')
    require(max_cloud_volume > 0.0, 'no flammable cloud volume observed')
    require(max_flammable_x is not None, 'no flammable x extent observed')
    require(max_flammable_z is not None, 'no flammable z extent observed')

    extents_csv = Path(args.extents_csv)
    sensors_csv = Path(args.sensors_csv)
    extent_fields = list(extent_rows[0].keys())
    sensor_fields = list(sensor_rows[0].keys())
    write_csv(extents_csv, extent_rows, extent_fields)
    write_csv(sensors_csv, sensor_rows, sensor_fields)

    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Plume Observation Extraction',
        'run_dir': str(run_dir),
        'species': args.species,
        'lfl': args.lfl,
        'ufl': args.ufl,
        'plotfile_count': len(plotfiles),
        'sensor_count': len(sensors),
        'sensor_basis': sensor_basis,
        'sensor_sampling': args.sensor_sampling,
        'summary': {
            'time_start': min(times),
            'time_end': max(times),
            'max_cloud_volume': max_cloud_volume,
            'max_peak_X': max_peak_x,
            'max_flammable_x': max_flammable_x,
            'max_flammable_z': max_flammable_z,
            'extent_rows': len(extent_rows),
            'sensor_rows': len(sensor_rows),
            'plume_extents_available': True,
            'sensor_timeseries_available': True,
            'all_sensors_inside_domain': True,
            'max_sensor_sample_distance': max_sensor_sample_distance,
            'max_nearest_cell_distance': max_sensor_sample_distance,
            'case_matched_external_benchmark': bool(args.case_matched_external_benchmark),
        },
        'sensors': sensors,
        'outputs': {
            'plume_extents_csv': str(extents_csv),
            'sensor_timeseries_csv': str(sensors_csv),
        },
        'evidence_files': [
            evidence_entry('plume_extents_csv', extents_csv),
            evidence_entry('sensor_timeseries_csv', sensors_csv),
        ] + ([evidence_entry('sensors_json', sensor_path)] if sensor_path else []),
        'limitations': [
            'This report proves extraction capability for plume extents and point-probe time series.',
            'It does not by itself prove agreement with an external field-test, wind-tunnel, or literature-digitized benchmark.',
        ],
    }
    validate_report_object(report, check_hashes=False)
    return report


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(int(data.get('plotfile_count', 0)) > 0, 'plotfile_count missing')
    require(int(data.get('sensor_count', 0)) > 0, 'sensor_count missing')
    require(data.get('sensor_sampling') in {'trilinear', 'nearest', None}, 'invalid sensor_sampling')
    summary = data.get('summary') if isinstance(data.get('summary'), dict) else {}
    for key in ('max_cloud_volume', 'max_peak_X', 'max_flammable_x', 'max_flammable_z'):
        require(finite(summary.get(key)), f'missing finite summary {key}')
    require(float(summary['max_cloud_volume']) > 0.0, 'max_cloud_volume must be positive')
    require(float(summary['max_peak_X']) > 0.0, 'max_peak_X must be positive')
    require(summary.get('plume_extents_available') is True, 'plume extents not available')
    require(summary.get('sensor_timeseries_available') is True, 'sensor time series not available')
    require(summary.get('all_sensors_inside_domain') is True, 'one or more sensors are outside domain')
    require(finite(summary.get('max_sensor_sample_distance')), 'missing max_sensor_sample_distance')
    require(float(summary['max_sensor_sample_distance']) >= 0.0, 'negative max_sensor_sample_distance')
    require(finite(summary.get('max_nearest_cell_distance')), 'missing max_nearest_cell_distance')
    require(float(summary['max_nearest_cell_distance']) >= 0.0, 'negative max_nearest_cell_distance')
    outputs = data.get('outputs') if isinstance(data.get('outputs'), dict) else {}
    for key in ('plume_extents_csv', 'sensor_timeseries_csv'):
        path = Path(str(outputs.get(key, '')))
        require(path.is_file(), f'missing output {key}: {path}')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and len(entries) >= 2, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Engineering H2 Plume Observation Extraction',
        '',
        f"Status: `{report['status']}`",
        f"Run directory: `{report['run_dir']}`",
        f"Sensor basis: `{report['sensor_basis']}`",
        f"Sensor sampling: `{report['sensor_sampling']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in summary.items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Outputs', '']
    for key, value in report['outputs'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', default=str(DEFAULT_RUN_DIR))
    parser.add_argument('--sensors-json')
    parser.add_argument('--species', default='H2')
    parser.add_argument('--lfl', type=float, default=0.04)
    parser.add_argument('--ufl', type=float, default=0.75)
    parser.add_argument('--min-plotfiles', type=int, default=2)
    parser.add_argument('--min-sensors', type=int, default=1)
    parser.add_argument('--sensor-sampling', choices=('trilinear', 'nearest'), default='trilinear')
    parser.add_argument('--case-matched-external-benchmark', action='store_true')
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--extents-csv', default=str(DEFAULT_EXTENTS_CSV))
    parser.add_argument('--sensors-csv', default=str(DEFAULT_SENSORS_CSV))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_plume_observation_report VERIFY-PASS '
                f"json={args.verify_json} plotfiles={data['plotfile_count']} sensors={data['sensor_count']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_plume_observation_report PASS '
            f"json={out_json} md={out_md} plotfiles={report['plotfile_count']} sensors={report['sensor_count']}"
        )
        return 0
    except ObservationError as exc:
        print(f'engineering_h2_plume_observation_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
