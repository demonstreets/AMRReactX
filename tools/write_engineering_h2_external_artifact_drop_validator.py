#!/usr/bin/env python3
"""Write/verify the engineering H2 external artifact drop validation report."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 5
STATUS_READY = 'PASS-H2-EXTERNAL-ARTIFACT-DROP'
STATUS_NOT_READY = 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724')
DEFAULT_DROP_ROOT = DEFAULT_ROOT / 'drop'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_drop_validator_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_drop_validator_report.md'
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)

CAD_EXTENSIONS = {'.step', '.stp', '.iges', '.igs', '.brep', '.sat', '.x_t', '.x_b', '.stl', '.obj'}
GEOMETRY_EXTENSIONS = {'.stl', '.obj', '.ply', '.vtk', '.vtp', '.step', '.stp'}
SBEPV5_SENSORS = tuple(range(1, 13))
SBEPV5_TIMESERIES_COLUMNS = ('time_s',) + tuple(f'Gas{sid:02d}_vol_percent' for sid in SBEPV5_SENSORS)
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
CONTENT_QUALITY_GATE_LEVEL = 'strict-v5-placeholder-free'


class DropValidatorError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DropValidatorError(message)


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
        raise DropValidatorError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise DropValidatorError(f'invalid JSON evidence {path}: {exc}') from exc
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline='', encoding='utf-8') as fh:
            rows = [dict(row) for row in csv.DictReader(fh)]
    except OSError as exc:
        raise DropValidatorError(f'failed reading CSV {path}: {exc}') from exc
    return rows


def to_float(value: Any, label: str, gaps: list[str]) -> float | None:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        gaps.append(f'invalid_float:{label}:{value}')
        return None
    if parsed != parsed or parsed in (float('inf'), float('-inf')):
        gaps.append(f'nonfinite_float:{label}:{value}')
        return None
    return parsed


def parse_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text in {'true', 'yes', '1', 'pass', 'passed'}:
        return True
    if text in {'false', 'no', '0', 'fail', 'failed'}:
        return False
    return None


def parse_triplet(value: Any, label: str, gaps: list[str]) -> tuple[float, float, float] | None:
    parts = [item.strip() for item in str(value).replace(';', ',').split(',') if item.strip()]
    if len(parts) != 3:
        gaps.append(f'invalid_triplet:{label}:{value}')
        return None
    parsed = [to_float(item, label, gaps) for item in parts]
    if any(item is None for item in parsed):
        return None
    return parsed[0], parsed[1], parsed[2]  # type: ignore[return-value]


def normalize_sbepv5_sensor_id(value: Any) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    if text.lower().startswith('gas'):
        text = text[3:]
    try:
        sensor_id = int(text)
    except ValueError:
        return None
    if sensor_id not in SBEPV5_SENSORS:
        return None
    return sensor_id


def text_has_synthetic_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return any(text_has_synthetic_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(text_has_synthetic_marker(item) for item in value)
    text = str(value).lower()
    return any(marker in text for marker in SYNTHETIC_MARKERS)


def text_has_placeholder_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return any(text_has_placeholder_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(text_has_placeholder_marker(item) for item in value)
    text = str(value).strip().lower()
    if not text:
        return False
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def reject_synthetic_marker(summary: dict[str, Any], gaps: list[str], allow_synthetic_selftest: bool) -> None:
    if allow_synthetic_selftest:
        return
    if text_has_synthetic_marker(summary):
        gaps.append('synthetic_or_selftest_marker_present_without_allow_synthetic_selftest')


def reject_placeholder_marker(summary: Any, gaps: list[str], allow_synthetic_selftest: bool) -> None:
    if allow_synthetic_selftest:
        return
    if text_has_placeholder_marker(summary):
        gaps.append('placeholder_or_template_marker_present_without_replacement')


def csv_has_columns(path: Path, required: tuple[str, ...], min_rows: int = 1) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, [f'missing_csv:{path}']
    rows = read_csv_rows(path)
    gaps: list[str] = []
    if len(rows) < min_rows:
        gaps.append(f'csv_too_few_rows:{path}:{len(rows)}<{min_rows}')
    columns = set(rows[0].keys()) if rows else set()
    missing = [item for item in required if item not in columns]
    if missing:
        gaps.append(f'csv_missing_columns:{path}:' + ','.join(missing))
    return not gaps, {'path': str(path), 'row_count': len(rows), 'columns': sorted(columns), 'sha256': sha256_file(path)}, gaps


def ensure_drop_scaffold(drop_root: Path) -> None:
    for path in (
        drop_root / 'real_cad_cleanup' / 'source_cad',
        drop_root / 'real_cad_cleanup' / 'cleaned_geometry',
        drop_root / 'external_plume_shape_reference',
        drop_root / 'fire_consequence_calibration',
    ):
        path.mkdir(parents=True, exist_ok=True)
    readme = drop_root / 'README.md'
    if not readme.exists():
        readme.write_text(
            '# Engineering H2 External Artifact Drop\n\n'
            'Stage externally supplied production evidence here before copying it into the controlled evidence tree.\n'
            'Run `python3 tools/write_engineering_h2_external_artifact_drop_validator.py` before ingestion.\n',
            encoding='utf-8',
        )


def file_record(path: Path, validator: str, ok: bool, gaps: list[str], summary: dict[str, Any] | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        'path': str(path),
        'validator': validator,
        'present': path.exists(),
        'valid': ok,
        'gaps': gaps,
    }
    if path.is_file():
        record['sha256'] = sha256_file(path)
        record['size_bytes'] = path.stat().st_size
    if summary:
        record['summary'] = summary
    return record


def count_files(path: Path, extensions: set[str]) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(item for item in path.rglob('*') if item.is_file() and item.suffix.lower() in extensions)


def safe_relative_path(value: Any) -> str | None:
    rel = str(value).strip()
    if not rel:
        return None
    path = Path(rel)
    if path.is_absolute() or '..' in path.parts:
        return None
    return rel.replace('\\', '/')


def validate_json_file(path: Path, required_keys: tuple[str, ...]) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, [f'missing_json:{path}']
    data = load_json(path)
    gaps = [f'json_missing_key:{path}:{key}' for key in required_keys if not data.get(key)]
    return not gaps, {'path': str(path), 'keys': sorted(data.keys()), 'sha256': sha256_file(path)}, gaps


def validate_real_cad_artifact(drop_root: Path, artifact: str, allow_synthetic_selftest: bool) -> dict[str, Any]:
    root = drop_root / 'real_cad_cleanup'
    if artifact == 'real_cad_cleanup_manifest.json':
        path = root / 'real_cad_cleanup_manifest.json'
        ok, summary, gaps = validate_json_file(path, ('schema_version', 'geometries'))
        if ok:
            data = load_json(path)
            geometries = data.get('geometries')
            if not isinstance(geometries, list) or len(geometries) < 3:
                gaps.append('manifest_geometries_count_less_than_3')
            else:
                labels = set()
                for idx, geometry in enumerate(geometries):
                    if not isinstance(geometry, dict):
                        gaps.append(f'manifest_geometry_not_object:{idx}')
                        continue
                    label = str(geometry.get('label', '')).strip()
                    source = str(geometry.get('source', '')).strip()
                    cleaned = str(geometry.get('cleaned', '')).strip()
                    if not label:
                        gaps.append(f'manifest_geometry_missing_label:{idx}')
                    if label in labels:
                        gaps.append(f'manifest_geometry_duplicate_label:{label}')
                    labels.add(label)
                    if not source:
                        gaps.append(f'manifest_geometry_missing_source:{label or idx}')
                    if not cleaned:
                        gaps.append(f'manifest_geometry_missing_cleaned:{label or idx}')
            summary['geometry_count'] = len(geometries) if isinstance(geometries, list) else 0
            reject_synthetic_marker(data, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(data, gaps, allow_synthetic_selftest)
            ok = not gaps
        return file_record(path, 'real_cad_cleanup_manifest_json', ok, gaps, summary)
    if artifact == 'source_cad/*':
        path = root / 'source_cad'
        files = count_files(path, CAD_EXTENSIONS)
        gaps = [] if len(files) >= 3 else [f'source_cad_file_count:{len(files)}<3']
        if not allow_synthetic_selftest:
            for item in files[:20]:
                try:
                    head = item.read_text(encoding='utf-8', errors='ignore')[:4096]
                except OSError:
                    head = ''
                if text_has_synthetic_marker({'name': item.name, 'head': head}):
                    gaps.append(f'source_cad_synthetic_marker:{item}')
                if text_has_placeholder_marker({'head': head}):
                    gaps.append(f'source_cad_placeholder_marker:{item}')
        return {
            'path': str(path),
            'validator': 'real_cad_source_cad_directory',
            'present': path.is_dir(),
            'valid': not gaps,
            'file_count': len(files),
            'files': [str(item) for item in files[:20]],
            'gaps': gaps,
        }
    if artifact == 'cleaned_geometry/*':
        path = root / 'cleaned_geometry'
        files = count_files(path, GEOMETRY_EXTENSIONS)
        gaps = [] if len(files) >= 3 else [f'cleaned_geometry_file_count:{len(files)}<3']
        if not allow_synthetic_selftest:
            for item in files[:20]:
                try:
                    head = item.read_text(encoding='utf-8', errors='ignore')[:4096]
                except OSError:
                    head = ''
                if text_has_synthetic_marker({'name': item.name, 'head': head}):
                    gaps.append(f'cleaned_geometry_synthetic_marker:{item}')
                if text_has_placeholder_marker({'head': head}):
                    gaps.append(f'cleaned_geometry_placeholder_marker:{item}')
        return {
            'path': str(path),
            'validator': 'real_cad_cleaned_geometry_directory',
            'present': path.is_dir(),
            'valid': not gaps,
            'file_count': len(files),
            'files': [str(item) for item in files[:20]],
            'gaps': gaps,
        }
    if artifact in {'cleanup_quality_records', 'real_cad_cleanup_quality_record.csv'}:
        path = root / 'real_cad_cleanup_quality_record.csv'
        ok, summary, gaps = csv_has_columns(
            path,
            (
                'label',
                'units_declared',
                'watertight_or_closed_surface',
                'nondegenerate_elements',
                'positive_volume_or_area',
                'bbox_min_m',
                'bbox_max_m',
                'tool_or_method',
                'reviewer',
            ),
            min_rows=3,
        )
        if ok:
            rows = read_csv_rows(path)
            labels: set[str] = set()
            for idx, row in enumerate(rows):
                label = row.get('label', '').strip()
                if not label:
                    gaps.append(f'cleanup_quality_missing_label:{idx}')
                if label in labels:
                    gaps.append(f'cleanup_quality_duplicate_label:{label}')
                labels.add(label)
                if str(row.get('units_declared', '')).strip().lower() != 'm':
                    gaps.append(f'cleanup_quality_units_not_m:{label or idx}')
                for key in ('watertight_or_closed_surface', 'nondegenerate_elements', 'positive_volume_or_area'):
                    if parse_bool(row.get(key)) is not True:
                        gaps.append(f'cleanup_quality_boolean_not_true:{label or idx}:{key}')
                bbox_min = parse_triplet(row.get('bbox_min_m'), f'{label or idx}:bbox_min_m', gaps)
                bbox_max = parse_triplet(row.get('bbox_max_m'), f'{label or idx}:bbox_max_m', gaps)
                if bbox_min and bbox_max and any(lo >= hi for lo, hi in zip(bbox_min, bbox_max)):
                    gaps.append(f'cleanup_quality_bbox_not_positive:{label or idx}')
            reject_synthetic_marker(rows, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(rows, gaps, allow_synthetic_selftest)
            summary['label_count'] = len(labels)
            ok = not gaps
        return file_record(path, 'real_cad_cleanup_quality_record_csv', ok, gaps, summary)
    if artifact == 'real_cad_data_room_index.csv':
        path = root / 'real_cad_data_room_index.csv'
        ok, summary, gaps = csv_has_columns(
            path,
            ('file_role', 'label', 'relative_path', 'sha256', 'source_type', 'revision', 'owner_or_supplier'),
            min_rows=6,
        )
        if ok:
            rows = read_csv_rows(path)
            roles = {row.get('file_role', '').strip() for row in rows}
            if 'source_cad' not in roles:
                gaps.append('data_room_index_missing_source_cad_role')
            if 'cleaned_geometry' not in roles:
                gaps.append('data_room_index_missing_cleaned_geometry_role')
            for idx, row in enumerate(rows):
                rel = str(row.get('relative_path', '')).strip()
                expected_hash = str(row.get('sha256', '')).strip().lower()
                if not rel:
                    gaps.append(f'data_room_index_missing_relative_path:{idx}')
                    continue
                if Path(rel).is_absolute() or '..' in Path(rel).parts:
                    gaps.append(f'data_room_index_unsafe_relative_path:{rel}')
                    continue
                source_path = root / rel
                if not source_path.is_file():
                    gaps.append(f'data_room_index_referenced_file_missing:{rel}')
                    continue
                actual_hash = sha256_file(source_path).lower()
                if expected_hash != actual_hash:
                    gaps.append(f'data_room_index_sha256_mismatch:{rel}')
            reject_synthetic_marker(rows, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(rows, gaps, allow_synthetic_selftest)
            summary['role_count'] = len(roles)
            ok = not gaps
        return file_record(path, 'real_cad_data_room_index_csv', ok, gaps, summary)
    raise DropValidatorError(f'unknown real-CAD artifact: {artifact}')


def validate_plume_artifact(drop_root: Path, artifact: str, allow_synthetic_selftest: bool) -> dict[str, Any]:
    root = drop_root / 'external_plume_shape_reference'
    if artifact == 'dataset_metadata.json':
        path = root / 'dataset_metadata.json'
        ok, summary, gaps = validate_json_file(path, ('schema_version', 'benchmark_id', 'source', 'digitization'))
        if ok:
            data = load_json(path)
            if data.get('benchmark_id') != 'hysafe_sbepv5_d27':
                ok = False
                gaps.append('dataset_metadata_benchmark_id_mismatch')
            source = data.get('source')
            digitization = data.get('digitization')
            if not isinstance(source, dict):
                gaps.append('dataset_metadata_source_not_object')
            elif not any(source.get(key) for key in ('url', 'doi', 'source_file_sha256', 'type')):
                gaps.append('dataset_metadata_source_missing_url_doi_or_hash')
            if not isinstance(digitization, dict):
                gaps.append('dataset_metadata_digitization_not_object')
            elif not digitization.get('method'):
                gaps.append('dataset_metadata_digitization_missing_method')
            reject_synthetic_marker(data, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(data, gaps, allow_synthetic_selftest)
            ok = not gaps
        return file_record(path, 'sbepv5_dataset_metadata_json', ok, gaps, summary)
    if artifact == 'sensor_coordinates.csv':
        path = root / 'sensor_coordinates.csv'
        ok, summary, gaps = csv_has_columns(
            path,
            ('sensor_id', 'x_m', 'y_m', 'z_m', 'reliability', 'source_basis', 'digitization_uncertainty_m'),
            min_rows=12,
        )
        if ok:
            rows = read_csv_rows(path)
            sensor_ids: set[int] = set()
            raw_sensor_ids: set[str] = set()
            duplicate_sensor_ids: set[int] = set()
            for row in rows:
                raw = row.get('sensor_id', '').strip()
                raw_sensor_ids.add(raw)
                normalized = normalize_sbepv5_sensor_id(raw)
                if normalized is None:
                    gaps.append(f'sensor_coordinates_invalid_sensor_id:{raw}')
                    continue
                if normalized in sensor_ids:
                    duplicate_sensor_ids.add(normalized)
                sensor_ids.add(normalized)
            expected = set(SBEPV5_SENSORS)
            missing = sorted(expected - sensor_ids)
            extra = sorted(sensor_ids - expected)
            if missing:
                gaps.append('sensor_coordinates_missing_sensors:' + ','.join(map(str, missing)))
            if extra:
                gaps.append('sensor_coordinates_extra_sensors:' + ','.join(map(str, extra)))
            if duplicate_sensor_ids:
                gaps.append(
                    'sensor_coordinates_duplicate_sensors:' + ','.join(map(str, sorted(duplicate_sensor_ids)))
                )
            for row in rows:
                sid = row.get('sensor_id', '').strip()
                for key in ('x_m', 'y_m', 'z_m'):
                    to_float(row.get(key), f'{sid}:{key}', gaps)
                unc = to_float(row.get('digitization_uncertainty_m'), f'{sid}:digitization_uncertainty_m', gaps)
                if unc is not None and not (0.0 <= unc <= 0.02):
                    gaps.append(f'sensor_coordinates_uncertainty_gt_0p02m:{sid}:{unc}')
            reject_synthetic_marker(rows, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(rows, gaps, allow_synthetic_selftest)
            summary['sensor_count'] = len(sensor_ids)
            summary['sensor_id_conventions_observed'] = sorted({
                'gas_label' if raw.lower().startswith('gas') else 'numeric'
                for raw in raw_sensor_ids
                if raw
            })
            ok = not gaps
        return file_record(path, 'sbepv5_sensor_coordinates_csv', ok, gaps, summary)
    if artifact == 'baffle_geometry.csv':
        path = root / 'baffle_geometry.csv'
        ok, summary, gaps = csv_has_columns(
            path,
            ('baffle_id', 'x_min_m', 'x_max_m', 'y_min_m', 'y_max_m', 'z_min_m', 'z_max_m', 'source_basis', 'digitization_uncertainty_m'),
            min_rows=4,
        )
        if ok:
            rows = read_csv_rows(path)
            baffles = {row.get('baffle_id', '').strip() for row in rows}
            for row in rows:
                bid = row.get('baffle_id', '').strip()
                bounds = {}
                for key in ('x_min_m', 'x_max_m', 'y_min_m', 'y_max_m', 'z_min_m', 'z_max_m'):
                    bounds[key] = to_float(row.get(key), f'{bid}:{key}', gaps)
                for axis in ('x', 'y', 'z'):
                    lo = bounds.get(f'{axis}_min_m')
                    hi = bounds.get(f'{axis}_max_m')
                    if lo is not None and hi is not None and lo >= hi:
                        gaps.append(f'baffle_geometry_nonpositive_extent:{bid}:{axis}')
                unc = to_float(row.get('digitization_uncertainty_m'), f'{bid}:digitization_uncertainty_m', gaps)
                if unc is not None and not (0.0 <= unc <= 0.02):
                    gaps.append(f'baffle_geometry_uncertainty_gt_0p02m:{bid}:{unc}')
            reject_synthetic_marker(rows, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(rows, gaps, allow_synthetic_selftest)
            summary['baffle_count'] = len(baffles)
            ok = not gaps
        return file_record(path, 'sbepv5_baffle_geometry_csv', ok, gaps, summary)
    if artifact == 'experimental_timeseries.csv':
        path = root / 'experimental_timeseries.csv'
        ok, summary, gaps = csv_has_columns(path, SBEPV5_TIMESERIES_COLUMNS, min_rows=2)
        if ok:
            rows = read_csv_rows(path)
            times: list[float] = []
            for idx, row in enumerate(rows):
                t = to_float(row.get('time_s'), f'timeseries:{idx}:time_s', gaps)
                if t is not None:
                    times.append(t)
                for col in SBEPV5_TIMESERIES_COLUMNS[1:]:
                    val = to_float(row.get(col), f'timeseries:{idx}:{col}', gaps)
                    if val is not None and not (0.0 <= val <= 100.0):
                        gaps.append(f'timeseries_concentration_out_of_range:{idx}:{col}:{val}')
            if len(times) == len(rows):
                if any(curr <= prev for prev, curr in zip(times, times[1:])):
                    gaps.append('timeseries_time_not_strictly_increasing')
                if times[0] > 0.0:
                    gaps.append(f'timeseries_first_time_after_zero:{times[0]}')
                if times[-1] < 120.0:
                    gaps.append(f'timeseries_does_not_reach_120s:{times[-1]}')
            reject_synthetic_marker(rows, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(rows, gaps, allow_synthetic_selftest)
            summary['time_start_s'] = min(times) if times else None
            summary['time_end_s'] = max(times) if times else None
            ok = not gaps
        return file_record(path, 'sbepv5_experimental_timeseries_csv', ok, gaps, summary)
    raise DropValidatorError(f'unknown plume artifact: {artifact}')


def validate_fire_artifact(drop_root: Path, artifact: str, allow_synthetic_selftest: bool) -> dict[str, Any]:
    root = drop_root / 'fire_consequence_calibration'
    if artifact == 'calibration_metadata.json':
        path = root / 'calibration_metadata.json'
        ok, summary, gaps = validate_json_file(path, ('schema_version', 'dataset_type', 'case', 'source', 'case_alignment'))
        if ok:
            data = load_json(path)
            source = data.get('source')
            alignment = data.get('case_alignment')
            if not isinstance(source, dict):
                gaps.append('calibration_metadata_source_not_object')
            elif not any(source.get(key) for key in ('url', 'doi', 'source_file_sha256', 'type')):
                gaps.append('calibration_metadata_source_missing_url_doi_or_hash')
            if not isinstance(alignment, dict):
                gaps.append('calibration_metadata_case_alignment_not_object')
            elif not all(value is True for value in alignment.values()):
                gaps.append('calibration_metadata_case_alignment_not_all_true')
            reject_synthetic_marker(data, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(data, gaps, allow_synthetic_selftest)
            ok = not gaps
        return file_record(path, 'fire_calibration_metadata_json', ok, gaps, summary)
    if artifact == 'radiation_metrics.csv':
        path = root / 'radiation_metrics.csv'
        ok, summary, gaps = csv_has_columns(
            path,
            ('metric_id', 'distance_m', 'reference_flux_w_m2', 'tolerance_abs_w_m2', 'tolerance_rel', 'source_basis'),
            min_rows=1,
        )
        if ok:
            rows = read_csv_rows(path)
            for idx, row in enumerate(rows):
                mid = row.get('metric_id', str(idx)).strip()
                distance = to_float(row.get('distance_m'), f'{mid}:distance_m', gaps)
                flux = to_float(row.get('reference_flux_w_m2'), f'{mid}:reference_flux_w_m2', gaps)
                abs_tol = to_float(row.get('tolerance_abs_w_m2'), f'{mid}:tolerance_abs_w_m2', gaps)
                rel_tol = to_float(row.get('tolerance_rel'), f'{mid}:tolerance_rel', gaps)
                if distance is not None and distance <= 0.0:
                    gaps.append(f'radiation_metric_distance_not_positive:{mid}:{distance}')
                if flux is not None and flux <= 0.0:
                    gaps.append(f'radiation_metric_flux_not_positive:{mid}:{flux}')
                if abs_tol is not None and abs_tol <= 0.0:
                    gaps.append(f'radiation_metric_abs_tolerance_not_positive:{mid}:{abs_tol}')
                if rel_tol is not None and not (0.0 < rel_tol <= 1.0):
                    gaps.append(f'radiation_metric_rel_tolerance_out_of_range:{mid}:{rel_tol}')
            reject_synthetic_marker(rows, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(rows, gaps, allow_synthetic_selftest)
            ok = not gaps
        return file_record(path, 'fire_radiation_metrics_csv', ok, gaps, summary)
    if artifact == 'overpressure_metrics.csv':
        path = root / 'overpressure_metrics.csv'
        ok, summary, gaps = csv_has_columns(
            path,
            ('metric_id', 'distance_m', 'reference_overpressure_kpa', 'tolerance_abs_kpa', 'tolerance_rel', 'source_basis'),
            min_rows=1,
        )
        if ok:
            rows = read_csv_rows(path)
            for idx, row in enumerate(rows):
                mid = row.get('metric_id', str(idx)).strip()
                distance = to_float(row.get('distance_m'), f'{mid}:distance_m', gaps)
                pressure = to_float(row.get('reference_overpressure_kpa'), f'{mid}:reference_overpressure_kpa', gaps)
                abs_tol = to_float(row.get('tolerance_abs_kpa'), f'{mid}:tolerance_abs_kpa', gaps)
                rel_tol = to_float(row.get('tolerance_rel'), f'{mid}:tolerance_rel', gaps)
                if distance is not None and distance <= 0.0:
                    gaps.append(f'overpressure_metric_distance_not_positive:{mid}:{distance}')
                if pressure is not None and pressure <= 0.0:
                    gaps.append(f'overpressure_metric_pressure_not_positive:{mid}:{pressure}')
                if abs_tol is not None and abs_tol <= 0.0:
                    gaps.append(f'overpressure_metric_abs_tolerance_not_positive:{mid}:{abs_tol}')
                if rel_tol is not None and not (0.0 < rel_tol <= 1.0):
                    gaps.append(f'overpressure_metric_rel_tolerance_out_of_range:{mid}:{rel_tol}')
            reject_synthetic_marker(rows, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(rows, gaps, allow_synthetic_selftest)
            ok = not gaps
        return file_record(path, 'fire_overpressure_metrics_csv', ok, gaps, summary)
    if artifact == 'calibrated_fire_consequence_report':
        path = root / 'calibrated_fire_consequence_report.json'
        ok, summary, gaps = validate_json_file(path, ('status', 'summary'))
        if ok:
            data = load_json(path)
            if data.get('status') != 'PASS-CALIBRATED-CONSEQUENCE-AGREEMENT':
                ok = False
                gaps.append('calibrated_fire_consequence_report_status_not_pass_calibrated')
            reject_synthetic_marker(data, gaps, allow_synthetic_selftest)
            reject_placeholder_marker(data, gaps, allow_synthetic_selftest)
            ok = not gaps
        return file_record(path, 'calibrated_fire_consequence_report_json', ok, gaps, summary)
    raise DropValidatorError(f'unknown fire artifact: {artifact}')


def validate_artifact(drop_root: Path, domain: str, artifact: str, allow_synthetic_selftest: bool) -> dict[str, Any]:
    if domain == 'real_cad_cleanup':
        return validate_real_cad_artifact(drop_root, artifact, allow_synthetic_selftest)
    if domain == 'external_plume_shape_reference':
        return validate_plume_artifact(drop_root, artifact, allow_synthetic_selftest)
    if domain == 'fire_consequence_calibration':
        return validate_fire_artifact(drop_root, artifact, allow_synthetic_selftest)
    raise DropValidatorError(f'unknown domain: {domain}')


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def real_cad_cross_file_gaps(drop_root: Path) -> list[str]:
    root = drop_root / 'real_cad_cleanup'
    manifest_path = root / 'real_cad_cleanup_manifest.json'
    quality_path = root / 'real_cad_cleanup_quality_record.csv'
    index_path = root / 'real_cad_data_room_index.csv'
    gaps: list[str] = []
    if not (manifest_path.is_file() and quality_path.is_file() and index_path.is_file()):
        return gaps

    manifest = load_json(manifest_path)
    geometries = manifest.get('geometries')
    if not isinstance(geometries, list):
        return gaps
    manifest_records: dict[str, dict[str, str]] = {}
    for idx, geometry in enumerate(geometries):
        if not isinstance(geometry, dict):
            continue
        label = str(geometry.get('label', '')).strip()
        source = safe_relative_path(geometry.get('source'))
        cleaned = safe_relative_path(geometry.get('cleaned'))
        if not label or not source or not cleaned:
            continue
        manifest_records[label] = {'source_cad': source, 'cleaned_geometry': cleaned}
        for rel, role in ((source, 'source_cad'), (cleaned, 'cleaned_geometry')):
            path = root / rel
            if not path.is_file():
                gaps.append(f'cad_manifest_referenced_{role}_missing:{label}:{rel}')

    manifest_labels = set(manifest_records)
    quality_rows = read_csv_rows(quality_path)
    quality_labels = [row.get('label', '').strip() for row in quality_rows if row.get('label', '').strip()]
    for label in duplicate_values(quality_labels):
        gaps.append(f'cad_quality_duplicate_label:{label}')
    quality_set = set(quality_labels)
    for label in sorted(manifest_labels - quality_set):
        gaps.append(f'cad_quality_missing_manifest_label:{label}')
    for label in sorted(quality_set - manifest_labels):
        gaps.append(f'cad_quality_label_not_in_manifest:{label}')

    index_rows = read_csv_rows(index_path)
    role_label_paths: dict[tuple[str, str], list[str]] = {}
    indexed_source_cleaned_labels: set[str] = set()
    for row in index_rows:
        role = row.get('file_role', '').strip()
        label = row.get('label', '').strip()
        rel = safe_relative_path(row.get('relative_path'))
        if role in {'source_cad', 'cleaned_geometry'} and label:
            indexed_source_cleaned_labels.add(label)
        if role in {'source_cad', 'cleaned_geometry'} and label and rel:
            role_label_paths.setdefault((role, label), []).append(rel)

    for label in sorted(manifest_labels - indexed_source_cleaned_labels):
        gaps.append(f'cad_index_missing_manifest_label:{label}')
    for label in sorted(indexed_source_cleaned_labels - manifest_labels):
        gaps.append(f'cad_index_label_not_in_manifest:{label}')

    for label, paths in manifest_records.items():
        for role, expected_rel in paths.items():
            indexed = role_label_paths.get((role, label), [])
            if len(indexed) != 1:
                gaps.append(f'cad_index_role_label_count:{label}:{role}:{len(indexed)}')
                continue
            actual_rel = indexed[0]
            if actual_rel != expected_rel:
                gaps.append(f'cad_index_manifest_path_mismatch:{label}:{role}:{actual_rel}!={expected_rel}')

    referenced = {rel for paths in manifest_records.values() for rel in paths.values()}
    actual = {
        str(path.relative_to(root)).replace('\\', '/')
        for subdir, extensions in (('source_cad', CAD_EXTENSIONS), ('cleaned_geometry', GEOMETRY_EXTENSIONS))
        for path in count_files(root / subdir, extensions)
    }
    for rel in sorted(actual - referenced):
        gaps.append(f'cad_unreferenced_file:{rel}')
    return gaps


def plume_cross_file_gaps(drop_root: Path) -> list[str]:
    root = drop_root / 'external_plume_shape_reference'
    sensor_path = root / 'sensor_coordinates.csv'
    baffle_path = root / 'baffle_geometry.csv'
    gaps: list[str] = []
    if sensor_path.is_file():
        sensor_ids = [row.get('sensor_id', '').strip() for row in read_csv_rows(sensor_path) if row.get('sensor_id', '').strip()]
        for sid in duplicate_values(sensor_ids):
            gaps.append(f'plume_sensor_duplicate_id:{sid}')
    if baffle_path.is_file():
        baffle_ids = [row.get('baffle_id', '').strip() for row in read_csv_rows(baffle_path) if row.get('baffle_id', '').strip()]
        for bid in duplicate_values(baffle_ids):
            gaps.append(f'plume_baffle_duplicate_id:{bid}')
    return gaps


def fire_cross_file_gaps(drop_root: Path) -> list[str]:
    root = drop_root / 'fire_consequence_calibration'
    gaps: list[str] = []
    for filename, label in (
        ('radiation_metrics.csv', 'fire_radiation_metric'),
        ('overpressure_metrics.csv', 'fire_overpressure_metric'),
    ):
        path = root / filename
        if not path.is_file():
            continue
        metric_ids = [row.get('metric_id', '').strip() for row in read_csv_rows(path) if row.get('metric_id', '').strip()]
        for metric_id in duplicate_values(metric_ids):
            gaps.append(f'{label}_duplicate_id:{metric_id}')
    return gaps


def domain_cross_file_gaps(drop_root: Path, domain: str) -> list[str]:
    if domain == 'real_cad_cleanup':
        return real_cad_cross_file_gaps(drop_root)
    if domain == 'external_plume_shape_reference':
        return plume_cross_file_gaps(drop_root)
    if domain == 'fire_consequence_calibration':
        return fire_cross_file_gaps(drop_root)
    return []


def closure_records(closure_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records = closure_manifest.get('domain_closure_records')
    require(isinstance(records, list) and records, 'closure manifest domain records missing')
    return [item for item in records if isinstance(item, dict)]


def build_domain_record(drop_root: Path, closure_record: dict[str, Any], allow_synthetic_selftest: bool) -> dict[str, Any]:
    domain = str(closure_record.get('domain', ''))
    artifact_records = closure_record.get('artifact_records')
    require(isinstance(artifact_records, list), f'{domain} artifact records missing')
    validations = []
    for item in artifact_records:
        require(isinstance(item, dict), f'{domain} artifact item is not an object')
        artifact = str(item.get('artifact', ''))
        validation = validate_artifact(drop_root, domain, artifact, allow_synthetic_selftest)
        validations.append(
            {
                'artifact': artifact,
                'target_path': item.get('target_path'),
                'drop_validation': validation,
            }
        )
    valid_count = sum(1 for item in validations if item['drop_validation'].get('valid') is True)
    domain_quality_gaps = domain_cross_file_gaps(drop_root, domain)
    domain_ready = valid_count == len(validations) and not domain_quality_gaps
    return {
        'domain': domain,
        'blocker': closure_record.get('blocker'),
        'artifact_count': len(validations),
        'valid_artifact_count': valid_count,
        'missing_or_invalid_artifact_count': len(validations) - valid_count,
        'domain_quality_gap_count': len(domain_quality_gaps),
        'domain_quality_gaps': domain_quality_gaps,
        'drop_ready_for_ingestion': domain_ready,
        'artifact_validations': validations,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    drop_root = Path(args.drop_root)
    if args.ensure_scaffold:
        ensure_drop_scaffold(drop_root)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    closure = load_json(closure_path)
    domains = [build_domain_record(drop_root, item, args.allow_synthetic_selftest) for item in closure_records(closure)]
    total_artifacts = sum(int(item['artifact_count']) for item in domains)
    valid_artifacts = sum(int(item['valid_artifact_count']) for item in domains)
    missing_or_invalid = total_artifacts - valid_artifacts
    domain_quality_gaps = sum(int(item['domain_quality_gap_count']) for item in domains)
    ready = missing_or_invalid == 0 and domain_quality_gaps == 0 and total_artifacts > 0
    status = STATUS_READY if ready else STATUS_NOT_READY
    quality_gate_matrix = [
        {
            'name': 'closure_manifest_attached',
            'status': 'PASS' if closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST' else 'MISSING',
            'evidence': str(closure_path),
            'gap': '',
        },
        {
            'name': 'drop_scaffold_exists',
            'status': 'PASS' if drop_root.is_dir() else 'MISSING',
            'evidence': str(drop_root),
            'gap': '',
        },
        {
            'name': 'artifact_count_matches_closure_manifest',
            'status': 'PASS' if total_artifacts == int(closure.get('total_missing_artifact_count', -1)) else 'MISSING',
            'evidence': f'drop={total_artifacts} closure={closure.get("total_missing_artifact_count")}',
            'gap': '',
        },
        {
            'name': 'not_ready_state_preserves_missing_external_data',
            'status': 'PASS' if ready or missing_or_invalid >= 1 or domain_quality_gaps >= 1 else 'MISSING',
            'evidence': f'missing_or_invalid={missing_or_invalid} domain_quality_gaps={domain_quality_gaps}',
            'gap': '',
        },
        {
            'name': 'does_not_clear_production_blockers',
            'status': 'PASS',
            'evidence': 'drop validation is pre-ingestion evidence only',
            'gap': '',
        },
        {
            'name': 'strict_content_quality_checks_enabled',
            'status': 'PASS',
            'evidence': f'test_fixture_data_allowed={args.allow_synthetic_selftest}',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 External Artifact Drop Validator',
        'drop_root': str(drop_root),
        'content_quality_gate_level': CONTENT_QUALITY_GATE_LEVEL,
        'test_fixture_data_allowed': args.allow_synthetic_selftest,
        'production_blocker_closure_manifest_report': str(closure_path),
        'total_expected_artifact_count': total_artifacts,
        'valid_artifact_count': valid_artifacts,
        'missing_or_invalid_artifact_count': missing_or_invalid,
        'domain_quality_gap_count': domain_quality_gaps,
        'ready_for_controlled_ingestion': ready,
        'remaining_blocker_count': closure.get('remaining_blocker_count'),
        'does_not_clear_production_blockers': True,
        'domain_records': domains,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [evidence_entry('production_blocker_closure_manifest_report', closure_path)],
        'limitations': [
            'This validator checks an external artifact drop before ingestion; it does not copy files into the controlled evidence tree.',
            'A PASS drop still requires domain ingestion reports, scorecard, blocker preflight, rebuild manifest, and final verifier to pass before production readiness can change.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('content_quality_gate_level') == CONTENT_QUALITY_GATE_LEVEL, 'content quality gate level mismatch')
    require(int(data.get('total_expected_artifact_count', 0)) == 14, 'expected artifact count must be 14')
    require(data.get('does_not_clear_production_blockers') is True, 'drop validator must not clear blockers')
    if data.get('status') == STATUS_READY:
        require(data.get('ready_for_controlled_ingestion') is True, 'PASS drop is not ready for ingestion')
        require(int(data.get('missing_or_invalid_artifact_count', -1)) == 0, 'PASS drop has missing artifacts')
    else:
        require(data.get('ready_for_controlled_ingestion') is False, 'NOT_READY drop marked ready')
        require(
            int(data.get('missing_or_invalid_artifact_count', 0)) >= 1
            or int(data.get('domain_quality_gap_count', 0)) >= 1,
            'NOT_READY drop must retain missing artifacts or domain quality gaps',
        )
    domains = data.get('domain_records')
    require(isinstance(domains, list) and len(domains) == 3, 'domain_records must contain three domains')
    for domain in domains:
        require(isinstance(domain, dict), 'domain record is not an object')
        require('domain_quality_gap_count' in domain, f"{domain.get('domain')} missing domain_quality_gap_count")
        if data.get('status') == STATUS_READY:
            require(int(domain.get('domain_quality_gap_count', -1)) == 0, f"{domain.get('domain')} has domain quality gaps")
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'drop validator quality gate failed')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence hash mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 External Artifact Drop Validator',
        '',
        f"Status: `{report['status']}`",
        f"Drop root: `{report['drop_root']}`",
        f"Content QA: `{report['content_quality_gate_level']}`",
        f"Allow test fixture data: `{report['test_fixture_data_allowed']}`",
        f"Expected artifacts: `{report['total_expected_artifact_count']}`",
        f"Valid artifacts: `{report['valid_artifact_count']}`",
        f"Missing or invalid artifacts: `{report['missing_or_invalid_artifact_count']}`",
        f"Domain quality gaps: `{report['domain_quality_gap_count']}`",
        f"Ready for controlled ingestion: `{report['ready_for_controlled_ingestion']}`",
        '',
        '## Domain Records',
        '',
    ]
    for domain in report['domain_records']:
        lines.append(f"### {domain['domain']}")
        lines.append(f"- Artifacts: `{domain['valid_artifact_count']}/{domain['artifact_count']}`")
        lines.append(f"- Domain quality gaps: `{domain['domain_quality_gap_count']}`")
        lines.append(f"- Ready: `{domain['drop_ready_for_ingestion']}`")
        for gap in domain.get('domain_quality_gaps', []):
            lines.append(f"- Domain gap: `{gap}`")
        for item in domain['artifact_validations']:
            validation = item['drop_validation']
            lines.append(f"- `{item['artifact']}`: valid=`{validation['valid']}` gaps=`{';'.join(validation['gaps'])}`")
        lines.append('')
    lines += ['## Quality Gates', '']
    for row in report['quality_gate_matrix']:
        lines.append(f"- `{row['name']}`: `{row['status']}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drop-root', default=str(DEFAULT_DROP_ROOT))
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--no-ensure-scaffold', action='store_true')
    parser.add_argument('--allow-synthetic-selftest', action='store_true')
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    args.ensure_scaffold = not args.no_ensure_scaffold
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_external_artifact_drop_validator VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"valid={report['valid_artifact_count']}/{report['total_expected_artifact_count']}"
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
            'engineering_h2_external_artifact_drop_validator PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"valid={report['valid_artifact_count']}/{report['total_expected_artifact_count']}"
        )
        return 0
    except DropValidatorError as exc:
        print(f'engineering_h2_external_artifact_drop_validator FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
