#!/usr/bin/env python3
"""Write/verify HySafe SBEPV5 D27 external dataset ingestion readiness evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS_READY = 'PASS-SBEPV5-D27-DATASET-INGESTION'
STATUS_NOT_READY = 'NOT_READY-SBEPV5-D27-DATASET-INGESTION'

DEFAULT_SPEC_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_spec_20260723/'
    'hysafe_sbepv5_d27_benchmark_spec_report.json'
)
DEFAULT_DATASET_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
    'sbepv5_d27_dataset_ingestion_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
    'sbepv5_d27_dataset_ingestion_report.md'
)

EXPECTED_SENSORS = tuple(range(1, 13))
RELIABLE_SENSORS = (1, 2, 5, 7, 8, 9, 10, 12)
UNRELIABLE_SENSORS = (3, 4, 6, 11)
TIMESERIES_COLUMNS = ('time_s',) + tuple(f'Gas{sid:02d}_vol_percent' for sid in EXPECTED_SENSORS)
SYNTHETIC_MARKERS = ('synthetic', 'selftest', 'codex-selftest', 'negative selftest')
PLACEHOLDER_MARKERS = (
    '<',
    'replace',
    'pending',
    'todo',
    'tbd',
    'placeholder',
    'fill in',
    'to be supplied',
)


class IngestionError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise IngestionError(message)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def text_has_marker(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        return any(text_has_marker(item, markers) for item in value.values())
    if isinstance(value, list):
        return any(text_has_marker(item, markers) for item in value)
    text = str(value).strip().lower()
    if not text:
        return False
    return any(marker in text for marker in markers)


def reject_synthetic_or_placeholder_markers(value: Any, gaps: list[str], label: str) -> None:
    if text_has_marker(value, SYNTHETIC_MARKERS):
        gaps.append(f'{label}_synthetic_or_selftest_marker_present')
    if text_has_marker(value, PLACEHOLDER_MARKERS):
        gaps.append(f'{label}_placeholder_or_template_marker_present')


def parse_sensor_id(value: Any) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    if text.lower().startswith('gas'):
        text = text[3:]
    try:
        sensor_id = int(text)
    except ValueError:
        return None
    if sensor_id not in EXPECTED_SENSORS:
        return None
    return sensor_id


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
        raise IngestionError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise IngestionError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f'empty CSV: {path}')
    return rows


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def row_float(row: dict[str, str], key: str, label: str) -> float:
    require(key in row, f'{label} missing column {key}')
    require(finite(row[key]), f'{label} non-finite {key}: {row.get(key)!r}')
    return float(row[key])


def validate_spec(spec_path: Path) -> dict[str, Any]:
    spec = load_json(spec_path)
    require(spec.get('status') == 'PASS-EXTERNAL-PLUME-BENCHMARK-SPEC', 'benchmark spec report is not PASS')
    require(spec.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark spec is not HySafe SBEPV5 D27')
    return spec


def check_metadata(path: Path) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, ['dataset_metadata_json_missing']
    metadata = load_json(path)
    gaps: list[str] = []
    if metadata.get('schema_version') != 1:
        gaps.append('dataset_metadata_schema_version_missing_or_invalid')
    if metadata.get('benchmark_id') != 'hysafe_sbepv5_d27':
        gaps.append('dataset_metadata_benchmark_id_mismatch')
    source = metadata.get('source')
    if not isinstance(source, dict) or not (source.get('url') or source.get('doi')):
        gaps.append('dataset_metadata_source_url_or_doi_missing')
    digitization = metadata.get('digitization')
    if not isinstance(digitization, dict):
        gaps.append('dataset_digitization_metadata_missing')
    else:
        for key in ('method', 'operator_or_tool', 'source_figures_or_tables'):
            if not digitization.get(key):
                gaps.append(f'dataset_digitization_{key}_missing')
    if not metadata.get('original_dataset_sha256') and not metadata.get('digitized_dataset_sha256'):
        gaps.append('dataset_source_hash_missing')
    reject_synthetic_or_placeholder_markers(metadata, gaps, 'dataset_metadata')
    return not gaps, metadata, gaps


def check_sensor_coordinates(path: Path, vessel: dict[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, ['sensor_coordinates_csv_missing']
    rows = read_csv(path)
    gaps: list[str] = []
    seen: set[int] = set()
    x_max = float(vessel['x_width'])
    y_max = float(vessel['y_depth'])
    z_max = float(vessel['z_height'])
    required_cols = {
        'sensor_id',
        'x_m',
        'y_m',
        'z_m',
        'reliability',
        'source_basis',
        'digitization_uncertainty_m',
    }
    if not required_cols <= set(rows[0].keys()):
        missing = sorted(required_cols - set(rows[0].keys()))
        gaps.append('sensor_coordinates_missing_columns:' + ','.join(missing))
        return False, {'row_count': len(rows)}, gaps
    max_uncertainty = 0.0
    for idx, row in enumerate(rows, 1):
        sid = parse_sensor_id(row['sensor_id'])
        if sid is None:
            gaps.append(f'sensor_coordinates_invalid_sensor_id_row_{idx}')
            continue
        if sid in seen:
            gaps.append(f'sensor_coordinates_duplicate_sensor_id_{sid}')
        seen.add(sid)
        x = row_float(row, 'x_m', f'sensor {sid}')
        y = row_float(row, 'y_m', f'sensor {sid}')
        z = row_float(row, 'z_m', f'sensor {sid}')
        uncertainty = row_float(row, 'digitization_uncertainty_m', f'sensor {sid}')
        max_uncertainty = max(max_uncertainty, uncertainty)
        if not (0.0 <= x <= x_max and 0.0 <= y <= y_max and 0.0 <= z <= z_max):
            gaps.append(f'sensor_{sid}_coordinate_outside_vessel')
        if uncertainty < 0.0 or uncertainty > 0.02:
            gaps.append(f'sensor_{sid}_digitization_uncertainty_out_of_bounds')
        reliability = row['reliability'].strip().lower()
        if sid in RELIABLE_SENSORS and reliability != 'reliable':
            gaps.append(f'sensor_{sid}_reliability_should_be_reliable')
        if sid in UNRELIABLE_SENSORS and reliability != 'unreliable':
            gaps.append(f'sensor_{sid}_reliability_should_be_unreliable')
        if not row['source_basis'].strip():
            gaps.append(f'sensor_{sid}_source_basis_missing')
    reject_synthetic_or_placeholder_markers(rows, gaps, 'sensor_coordinates')
    missing_sensors = sorted(set(EXPECTED_SENSORS) - seen)
    extra_sensors = sorted(seen - set(EXPECTED_SENSORS))
    if missing_sensors:
        gaps.append('sensor_coordinates_missing_sensor_ids:' + ','.join(map(str, missing_sensors)))
    if extra_sensors:
        gaps.append('sensor_coordinates_unexpected_sensor_ids:' + ','.join(map(str, extra_sensors)))
    return not gaps, {
        'row_count': len(rows),
        'sensor_ids': sorted(seen),
        'max_digitization_uncertainty_m': max_uncertainty,
        'sha256': sha256_file(path),
    }, gaps


def check_baffle_geometry(path: Path, vessel: dict[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, ['baffle_geometry_csv_missing']
    rows = read_csv(path)
    gaps: list[str] = []
    required_cols = {
        'baffle_id',
        'x_min_m',
        'x_max_m',
        'y_min_m',
        'y_max_m',
        'z_min_m',
        'z_max_m',
        'source_basis',
        'digitization_uncertainty_m',
    }
    if not required_cols <= set(rows[0].keys()):
        missing = sorted(required_cols - set(rows[0].keys()))
        gaps.append('baffle_geometry_missing_columns:' + ','.join(missing))
        return False, {'row_count': len(rows)}, gaps
    seen: set[int] = set()
    x_bound = float(vessel['x_width'])
    y_bound = float(vessel['y_depth'])
    z_bound = float(vessel['z_height'])
    for idx, row in enumerate(rows, 1):
        try:
            bid = int(row['baffle_id'])
        except ValueError:
            gaps.append(f'baffle_geometry_invalid_baffle_id_row_{idx}')
            continue
        seen.add(bid)
        x0 = row_float(row, 'x_min_m', f'baffle {bid}')
        x1 = row_float(row, 'x_max_m', f'baffle {bid}')
        y0 = row_float(row, 'y_min_m', f'baffle {bid}')
        y1 = row_float(row, 'y_max_m', f'baffle {bid}')
        z0 = row_float(row, 'z_min_m', f'baffle {bid}')
        z1 = row_float(row, 'z_max_m', f'baffle {bid}')
        uncertainty = row_float(row, 'digitization_uncertainty_m', f'baffle {bid}')
        if not (0.0 <= x0 <= x1 <= x_bound and 0.0 <= y0 <= y1 <= y_bound and 0.0 <= z0 <= z1 <= z_bound):
            gaps.append(f'baffle_{bid}_bounds_outside_vessel')
        if (x1 - x0) <= 0.0 or (y1 - y0) <= 0.0 or (z1 - z0) <= 0.0:
            gaps.append(f'baffle_{bid}_nonpositive_extent')
        if uncertainty < 0.0 or uncertainty > 0.02:
            gaps.append(f'baffle_{bid}_digitization_uncertainty_out_of_bounds')
        if not row['source_basis'].strip():
            gaps.append(f'baffle_{bid}_source_basis_missing')
    reject_synthetic_or_placeholder_markers(rows, gaps, 'baffle_geometry')
    if seen != {1, 2, 3, 4}:
        gaps.append('baffle_geometry_expected_ids_1_2_3_4')
    return not gaps, {'row_count': len(rows), 'baffle_ids': sorted(seen), 'sha256': sha256_file(path)}, gaps


def check_timeseries(path: Path) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, ['experimental_timeseries_csv_missing']
    rows = read_csv(path)
    gaps: list[str] = []
    columns = set(rows[0].keys())
    missing = [col for col in TIMESERIES_COLUMNS if col not in columns]
    if missing:
        return False, {'row_count': len(rows)}, ['experimental_timeseries_missing_columns:' + ','.join(missing)]
    previous_time = -math.inf
    peak_by_sensor = {sid: 0.0 for sid in RELIABLE_SENSORS}
    first_time: float | None = None
    last_time: float | None = None
    for idx, row in enumerate(rows, 1):
        time_s = row_float(row, 'time_s', f'timeseries row {idx}')
        if first_time is None:
            first_time = time_s
        last_time = time_s
        if time_s < previous_time:
            gaps.append(f'experimental_timeseries_time_not_monotone_row_{idx}')
        previous_time = time_s
        for sid in RELIABLE_SENSORS:
            key = f'Gas{sid:02d}_vol_percent'
            value = row_float(row, key, f'timeseries row {idx} {key}')
            if value < -5.0 or value > 100.0:
                gaps.append(f'experimental_timeseries_{key}_out_of_range_row_{idx}')
            peak_by_sensor[sid] = max(peak_by_sensor[sid], value)
    if len(rows) < 25:
        gaps.append('experimental_timeseries_too_few_rows')
    if first_time is None or first_time > 1.0:
        gaps.append('experimental_timeseries_start_time_after_1s')
    if last_time is None or last_time < 120.0:
        gaps.append('experimental_timeseries_end_time_before_120s')
    if not any(value >= 4.0 for value in peak_by_sensor.values()):
        gaps.append('experimental_timeseries_no_reliable_sensor_reaches_lfl')
    reject_synthetic_or_placeholder_markers(rows, gaps, 'experimental_timeseries')
    return not gaps, {
        'row_count': len(rows),
        'time_start_s': first_time,
        'time_end_s': last_time,
        'reliable_sensor_peak_vol_percent': {str(k): v for k, v in peak_by_sensor.items()},
        'sha256': sha256_file(path),
    }, gaps


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    spec_path = Path(args.benchmark_spec_report)
    spec = validate_spec(spec_path)
    dataset_root = Path(args.dataset_root)
    vessel = spec['geometry']['vessel_dimensions_m']
    metadata_path = dataset_root / 'dataset_metadata.json'
    sensor_path = dataset_root / 'sensor_coordinates.csv'
    baffle_path = dataset_root / 'baffle_geometry.csv'
    timeseries_path = dataset_root / 'experimental_timeseries.csv'

    metadata_ok, metadata_summary, metadata_gaps = check_metadata(metadata_path)
    sensor_ok, sensor_summary, sensor_gaps = check_sensor_coordinates(sensor_path, vessel)
    baffle_ok, baffle_summary, baffle_gaps = check_baffle_geometry(baffle_path, vessel)
    timeseries_ok, timeseries_summary, timeseries_gaps = check_timeseries(timeseries_path)
    blocking_gaps = metadata_gaps + sensor_gaps + baffle_gaps + timeseries_gaps
    ready = not blocking_gaps

    evidence_files = [evidence_entry('benchmark_spec_report', spec_path)]
    for label, path, ok in (
        ('dataset_metadata', metadata_path, metadata_ok),
        ('sensor_coordinates', sensor_path, sensor_ok),
        ('baffle_geometry', baffle_path, baffle_ok),
        ('experimental_timeseries', timeseries_path, timeseries_ok),
    ):
        if ok:
            evidence_files.append(evidence_entry(label, path))

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'title': 'HySafe SBEPV5 D27 Dataset Ingestion Readiness',
        'benchmark_spec_report': str(spec_path),
        'dataset_root': str(dataset_root),
        'clears_reference_data_blocker': False,
        'current_inputs': {
            'dataset_metadata_available': metadata_ok,
            'exact_sensor_coordinates_available': sensor_ok,
            'exact_baffle_geometry_available': baffle_ok,
            'experimental_timeseries_available': timeseries_ok,
        },
        'metadata_summary': metadata_summary,
        'sensor_coordinate_summary': sensor_summary,
        'baffle_geometry_summary': baffle_summary,
        'timeseries_summary': timeseries_summary,
        'blocking_gaps': blocking_gaps,
        'required_dataset_files': {
            'dataset_metadata_json': str(metadata_path),
            'sensor_coordinates_csv': str(sensor_path),
            'baffle_geometry_csv': str(baffle_path),
            'experimental_timeseries_csv': str(timeseries_path),
        },
        'schema_requirements': {
            'content_quality_gate_level': 'strict-v1-placeholder-free-and-non-synthetic',
            'accepted_sensor_id_formats': ['1', '01', 'Gas01'],
            'sensor_coordinates_csv_columns': [
                'sensor_id',
                'x_m',
                'y_m',
                'z_m',
                'reliability',
                'source_basis',
                'digitization_uncertainty_m',
            ],
            'baffle_geometry_csv_columns': [
                'baffle_id',
                'x_min_m',
                'x_max_m',
                'y_min_m',
                'y_max_m',
                'z_min_m',
                'z_max_m',
                'source_basis',
                'digitization_uncertainty_m',
            ],
            'experimental_timeseries_csv_columns': list(TIMESERIES_COLUMNS),
        },
        'evidence_files': evidence_files,
        'limitations': [
            'This report validates the external dataset ingestion package before reference-agreement scoring.',
            'It cannot clear the production reference-data blocker by itself.',
            'The official reference-agreement report must still be regenerated with a passing external plume dataset JSON.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark_id mismatch')
    require(data.get('clears_reference_data_blocker') is False, 'ingestion report cannot clear reference-data blocker')
    inputs = data.get('current_inputs')
    require(isinstance(inputs, dict), 'current_inputs missing')
    for key in (
        'dataset_metadata_available',
        'exact_sensor_coordinates_available',
        'exact_baffle_geometry_available',
        'experimental_timeseries_available',
    ):
        require(key in inputs, f'current_inputs missing {key}')
    gaps = data.get('blocking_gaps')
    require(isinstance(gaps, list), 'blocking_gaps missing')
    if data.get('status') == STATUS_READY:
        require(not gaps, 'ready ingestion report contains blocking gaps')
        require(all(inputs.values()), 'ready ingestion report has missing inputs')
    else:
        require(bool(gaps), 'not-ready ingestion report must contain blocking gaps')
    requirements = data.get('schema_requirements')
    require(isinstance(requirements, dict), 'schema_requirements missing')
    require(
        requirements.get('content_quality_gate_level') == 'strict-v1-placeholder-free-and-non-synthetic',
        'content quality gate level mismatch',
    )
    formats = requirements.get('accepted_sensor_id_formats')
    require(isinstance(formats, list) and {'1', 'Gas01'} <= set(formats), 'accepted sensor id formats missing')
    require('experimental_timeseries_csv_columns' in requirements, 'timeseries schema missing')
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
        '# HySafe SBEPV5 D27 Dataset Ingestion Readiness',
        '',
        f"Status: `{report['status']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        f"Dataset root: `{report['dataset_root']}`",
        '',
        '## Current Inputs',
        '',
    ]
    for key, value in report['current_inputs'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Blocking Gaps', '']
    for gap in report['blocking_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Required Dataset Files', '']
    for key, value in report['required_dataset_files'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Schema Requirements', '']
    for key, value in report['schema_requirements'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-spec-report', default=str(DEFAULT_SPEC_REPORT))
    parser.add_argument('--dataset-root', default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_sbepv5_dataset_ingestion VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} gaps={len(data['blocking_gaps'])}"
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
            'engineering_h2_sbepv5_dataset_ingestion PASS '
            f"json={out_json} md={out_md} status={report['status']} gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except IngestionError as exc:
        print(f'engineering_h2_sbepv5_dataset_ingestion FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
