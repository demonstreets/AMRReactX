#!/usr/bin/env python3
"""Write/verify preflight evidence for the HySafe SBEPV5 D27 case package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-SBEPV5-D27-CASE-PACKAGE-PREFLIGHT'

DEFAULT_CASE_PACKAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/'
    'sbepv5_d27_case_package_report.json'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_preflight_20260723/'
    'sbepv5_d27_case_package_preflight_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_preflight_20260723/'
    'sbepv5_d27_case_package_preflight_report.md'
)

EXPECTED_RELIABLE = {'1', '2', '5', '7', '8', '9', '10', '12'}
EXPECTED_UNRELIABLE = {'3', '4', '6', '11'}


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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise PreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise PreflightError(f'invalid JSON in {path}: {exc}') from exc
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


def parse_input(path: Path) -> dict[str, str]:
    params: dict[str, str] = {}
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        params[key.strip()] = value.strip()
    return params


def floats(raw: str, count: int, label: str) -> list[float]:
    parts = raw.split()
    require(len(parts) == count, f'{label} expected {count} values, got {len(parts)}')
    values = [float(item) for item in parts]
    require(all(math.isfinite(item) for item in values), f'{label} contains non-finite values')
    return values


def ints(raw: str, count: int, label: str) -> list[int]:
    values = [int(item) for item in raw.split()]
    require(len(values) == count, f'{label} expected {count} values, got {len(values)}')
    require(all(item > 0 for item in values), f'{label} values must be positive')
    return values


def approx(value: Any, expected: float, tol: float = 1.0e-12) -> bool:
    return finite(value) and abs(float(value) - expected) <= tol


def check_input(path: Path, mode: str) -> dict[str, Any]:
    params = parse_input(path)
    required = [
        'peleLM.lo_bc',
        'peleLM.hi_bc',
        'peleLM.user_defined_ext_sources',
        'peleLM.do_react',
        'peleLM.les_model',
        'amr.n_cell',
        'amr.stop_time',
        'geometry.prob_lo',
        'geometry.prob_hi',
        'codex.case_id',
        'codex.case_mode',
        'codex.release_period_s',
        'codex.nozzle_diameter_m',
        'codex.exit_velocity_m_s',
        'codex.flow_rate_normal_l_s',
        'codex.jet_exit_location_m',
        'codex.sensor_file',
        'codex.baffle_file',
        'codex.experimental_timeseries_file',
    ]
    missing = [key for key in required if key not in params]
    require(not missing, f'{mode} input missing keys: {", ".join(missing)}')
    require(params['codex.case_id'] == 'hysafe_sbepv5_d27', f'{mode} case_id mismatch')
    require(params['codex.case_mode'] == mode, f'{mode} case_mode mismatch')
    require(params['peleLM.user_defined_ext_sources'] == '1', f'{mode} user source is not enabled')
    require(params['peleLM.do_react'] == '0', f'{mode} should be non-reacting dispersion')
    require(params['peleLM.les_model'] == 'kepsilon', f'{mode} should use kepsilon LES/RANS closure')
    require(params['geometry.prob_lo'] == '0.0 0.0 0.0', f'{mode} prob_lo mismatch')
    prob_hi = floats(params['geometry.prob_hi'], 3, f'{mode} geometry.prob_hi')
    require(prob_hi == [1.20, 0.20, 0.90], f'{mode} geometry.prob_hi mismatch: {prob_hi}')
    n_cell = ints(params['amr.n_cell'], 3, f'{mode} amr.n_cell')
    cell = [prob_hi[idx] / n_cell[idx] for idx in range(3)]
    nozzle = float(params['codex.nozzle_diameter_m'])
    nozzle_cells = nozzle / max(cell)
    release = {
        'period_s': float(params['codex.release_period_s']),
        'nozzle_diameter_m': nozzle,
        'exit_velocity_m_s': float(params['codex.exit_velocity_m_s']),
        'flow_rate_normal_l_s': float(params['codex.flow_rate_normal_l_s']),
        'jet_exit_location_m': floats(params['codex.jet_exit_location_m'], 3, f'{mode} jet_exit_location_m'),
    }
    require(approx(release['period_s'], 60.0), f'{mode} release period mismatch')
    require(approx(release['nozzle_diameter_m'], 0.012), f'{mode} nozzle diameter mismatch')
    require(approx(release['exit_velocity_m_s'], 10.17), f'{mode} exit velocity mismatch')
    require(approx(release['flow_rate_normal_l_s'], 1.15), f'{mode} flow rate mismatch')
    require(release['jet_exit_location_m'] == [0.03, 0.1, 0.145], f'{mode} jet exit location mismatch')
    stop_time = float(params['amr.stop_time'])
    require(stop_time >= 120.0, f'{mode} stop_time must cover 120 s')
    return {
        'path': str(path),
        'n_cell': n_cell,
        'cell_size_m': cell,
        'max_cell_size_m': max(cell),
        'nozzle_cells_on_coarsest_spacing': nozzle_cells,
        'source_resolution_ready': nozzle_cells >= (2.0 if mode == 'reference' else 0.5),
        'stop_time_s': stop_time,
        'release': release,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f'empty CSV: {path}')
    return rows


def check_sensor_template(path: Path) -> dict[str, Any]:
    rows = read_csv(path)
    seen = {str(row.get('sensor_id', '')).strip() for row in rows}
    require(seen == {str(i) for i in range(1, 13)}, 'sensor template must contain exactly sensors 1..12')
    reliable = {str(row['sensor_id']) for row in rows if row.get('reliability') == 'reliable'}
    unreliable = {str(row['sensor_id']) for row in rows if row.get('reliability') == 'unreliable'}
    require(reliable == EXPECTED_RELIABLE, 'reliable sensor subset mismatch')
    require(unreliable == EXPECTED_UNRELIABLE, 'unreliable sensor subset mismatch')
    return {'sensor_count': len(rows), 'reliable': sorted(reliable, key=int), 'unreliable': sorted(unreliable, key=int)}


def check_baffle_template(path: Path) -> dict[str, Any]:
    rows = read_csv(path)
    seen = {str(row.get('baffle_id', '')).strip() for row in rows}
    require(seen == {'1', '2', '3', '4'}, 'baffle template must contain baffles 1..4')
    return {'baffle_count': len(rows)}


def check_timeseries_template(path: Path) -> dict[str, Any]:
    header = path.read_text(encoding='utf-8').splitlines()[0].split(',')
    expected = ['time_s'] + [f'Gas{i:02d}_vol_percent' for i in range(1, 13)]
    require(header == expected, 'experimental timeseries template header mismatch')
    return {'columns': header, 'sensor_columns': len(header) - 1}


def check_metadata_template(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == 1, 'metadata template schema_version mismatch')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'metadata template benchmark_id mismatch')
    alignment = data.get('case_alignment')
    require(isinstance(alignment, dict), 'metadata template case_alignment missing')
    return {'case_alignment_keys': sorted(alignment)}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    package_report_path = Path(args.case_package_report)
    package = load_json(package_report_path)
    require(package.get('status') == 'PASS-SBEPV5-D27-CASE-PACKAGE-SCAFFOLD', 'case package report did not PASS')
    files = package.get('package_files')
    require(isinstance(files, dict), 'case package files missing')
    paths = {key: Path(str(value)) for key, value in files.items()}
    scout = check_input(paths['scout_input'], 'scout')
    reference = check_input(paths['reference_input'], 'reference')
    sensor = check_sensor_template(paths['sensor_template'])
    baffle = check_baffle_template(paths['baffle_template'])
    timeseries = check_timeseries_template(paths['experimental_timeseries_template'])
    metadata = check_metadata_template(paths['metadata_template'])
    source_resolution_ready = bool(reference['source_resolution_ready'])
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'title': 'HySafe SBEPV5 D27 Case Package Preflight',
        'case_package_report': str(package_report_path),
        'case_runnable': package.get('case_runnable') is True,
        'case_scaffold_preflight_passed': True,
        'reference_input_source_resolution_ready': source_resolution_ready,
        'scout_input_source_resolution_ready': bool(scout['source_resolution_ready']),
        'production_validation_ready': False,
        'clears_reference_data_blocker': False,
        'input_checks': {'scout': scout, 'reference': reference},
        'template_checks': {
            'sensors': sensor,
            'baffles': baffle,
            'experimental_timeseries': timeseries,
            'dataset_metadata': metadata,
        },
        'remaining_runtime_gaps': package.get('runnable_blocking_gaps', []),
        'evidence_files': [
            evidence_entry('case_package_report', package_report_path),
            *(evidence_entry(key, path) for key, path in paths.items()),
        ],
        'limitations': [
            'This preflight checks package self-consistency and source-region resolution of the scaffold.',
            'It does not run PeleLMeX and does not clear the external reference-data blocker.',
            'production_validation_ready remains false until the exact dataset is ingested and a 120 s case-matched run is completed.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, f'invalid status: {data.get("status")}')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark_id mismatch')
    require(data.get('case_scaffold_preflight_passed') is True, 'preflight did not pass')
    require(data.get('reference_input_source_resolution_ready') is True, 'reference source resolution is not ready')
    require(data.get('production_validation_ready') is False, 'preflight cannot claim production validation')
    require(data.get('clears_reference_data_blocker') is False, 'preflight cannot clear reference-data blocker')
    inputs = data.get('input_checks')
    require(isinstance(inputs, dict) and {'scout', 'reference'} <= set(inputs), 'input checks missing')
    templates = data.get('template_checks')
    require(isinstance(templates, dict), 'template checks missing')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# HySafe SBEPV5 D27 Case Package Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Reference source resolution ready: `{report['reference_input_source_resolution_ready']}`",
        f"Case runnable: `{report['case_runnable']}`",
        f"Production validation ready: `{report['production_validation_ready']}`",
        '',
        '## Input Checks',
        '',
    ]
    for name, check in report['input_checks'].items():
        lines.append(f"- `{name}` n_cell: `{check['n_cell']}`")
        lines.append(f"- `{name}` max cell size m: `{check['max_cell_size_m']}`")
        lines.append(f"- `{name}` nozzle cells: `{check['nozzle_cells_on_coarsest_spacing']}`")
    lines += ['', '## Remaining Runtime Gaps', '']
    for gap in report['remaining_runtime_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-package-report', default=str(DEFAULT_CASE_PACKAGE_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_sbepv5_case_package_preflight VERIFY-PASS '
                f"json={args.verify_json} reference_resolution={data['reference_input_source_resolution_ready']}"
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
            'engineering_h2_sbepv5_case_package_preflight PASS '
            f"json={out_json} md={out_md} reference_resolution={report['reference_input_source_resolution_ready']}"
        )
        return 0
    except PreflightError as exc:
        print(f'engineering_h2_sbepv5_case_package_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
