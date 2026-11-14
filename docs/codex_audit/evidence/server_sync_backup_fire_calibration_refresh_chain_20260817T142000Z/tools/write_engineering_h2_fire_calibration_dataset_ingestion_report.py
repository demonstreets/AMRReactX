#!/usr/bin/env python3
"""Write/verify H2 fire/radiation/overpressure calibration dataset ingestion readiness."""
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
STATUS_READY = 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION'
STATUS_NOT_READY = 'NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION'

DEFAULT_FIRE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/'
    'fire_consequence_metrics_report.json'
)
DEFAULT_DATASET_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
    'fire_calibration_dataset_ingestion_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
    'fire_calibration_dataset_ingestion_report.md'
)

EXPERIMENTAL_SOURCE_TYPES = {'field_test', 'wind_tunnel', 'literature_digitized'}
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
REQUIRED_METADATA_ALIGNMENT = (
    'fuel',
    'release_or_cloud_mass',
    'ignition_or_burn_basis',
    'radiation_measurement_basis',
    'overpressure_measurement_basis',
    'boundary_conditions',
)
REQUIRED_RADIATION_COLUMNS = (
    'metric_id',
    'distance_m',
    'reference_flux_w_m2',
    'tolerance_abs_w_m2',
    'tolerance_rel',
    'source_basis',
)
REQUIRED_OVERPRESSURE_COLUMNS = (
    'metric_id',
    'distance_m',
    'reference_overpressure_kpa',
    'tolerance_abs_kpa',
    'tolerance_rel',
    'source_basis',
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


def text_has_marker(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        return any(text_has_marker(item, markers) for item in value.values())
    if isinstance(value, list):
        return any(text_has_marker(item, markers) for item in value)
    if value is None:
        return False
    text = str(value).strip().lower()
    return bool(text and any(marker in text for marker in markers))


def reject_synthetic_or_placeholder_markers(value: Any, gaps: list[str], label: str) -> None:
    if text_has_marker(value, SYNTHETIC_MARKERS):
        gaps.append(f'{label}_contains_synthetic_or_selftest_marker')
    if text_has_marker(value, PLACEHOLDER_MARKERS):
        gaps.append(f'{label}_contains_placeholder_marker')


def check_metadata(path: Path) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, ['fire_calibration_metadata_json_missing']
    data = load_json(path)
    gaps: list[str] = []
    reject_synthetic_or_placeholder_markers(data, gaps, 'fire_calibration_metadata')
    if data.get('schema_version') != 1:
        gaps.append('fire_calibration_metadata_schema_version_invalid')
    if data.get('dataset_type') != 'h2_fire_consequence_calibration_agreement':
        gaps.append('fire_calibration_metadata_dataset_type_invalid')
    if not data.get('case'):
        gaps.append('fire_calibration_metadata_case_missing')
    source_type = data.get('source_type')
    if source_type not in EXPERIMENTAL_SOURCE_TYPES:
        gaps.append('fire_calibration_metadata_source_type_not_experimental')
    source = data.get('source')
    if not isinstance(source, dict) or not source.get('title') or not (source.get('url') or source.get('doi')):
        gaps.append('fire_calibration_metadata_source_missing_title_or_public_identifier')
    alignment = data.get('case_alignment')
    if not isinstance(alignment, dict):
        gaps.append('fire_calibration_metadata_case_alignment_missing')
    else:
        for key in REQUIRED_METADATA_ALIGNMENT:
            if alignment.get(key) is not True:
                gaps.append(f'fire_calibration_metadata_case_alignment_{key}_not_true')
    uncertainty = data.get('uncertainty')
    if not isinstance(uncertainty, dict):
        gaps.append('fire_calibration_metadata_uncertainty_missing')
    else:
        if not uncertainty.get('radiation'):
            gaps.append('fire_calibration_metadata_radiation_uncertainty_missing')
        if not uncertainty.get('overpressure'):
            gaps.append('fire_calibration_metadata_overpressure_uncertainty_missing')
    return not gaps, {
        'case': data.get('case'),
        'source_type': source_type,
        'source': source,
        'case_alignment': alignment,
    }, gaps


def positive_float(row: dict[str, str], key: str, label: str) -> float:
    require(key in row, f'{label} missing column {key}')
    require(finite(row[key]), f'{label} non-finite {key}: {row.get(key)!r}')
    value = float(row[key])
    require(value > 0.0, f'{label} {key} must be positive')
    return value


def check_metric_csv(
    path: Path,
    columns: tuple[str, ...],
    value_key: str,
    family: str,
) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, [f'{family}_calibration_csv_missing']
    rows = read_csv(path)
    gaps: list[str] = []
    reject_synthetic_or_placeholder_markers(rows, gaps, f'{family}_calibration')
    missing = [col for col in columns if col not in rows[0]]
    if missing:
        return False, {'row_count': len(rows)}, [f'{family}_calibration_missing_columns:' + ','.join(missing)]
    seen_ids: set[str] = set()
    distances: list[float] = []
    values: list[float] = []
    for idx, row in enumerate(rows, 1):
        metric_id = row.get('metric_id', '').strip()
        if not metric_id:
            gaps.append(f'{family}_calibration_metric_id_missing_row_{idx}')
        if metric_id in seen_ids:
            gaps.append(f'{family}_calibration_duplicate_metric_id:{metric_id}')
        seen_ids.add(metric_id)
        try:
            distances.append(positive_float(row, 'distance_m', f'{family} row {idx}'))
            values.append(positive_float(row, value_key, f'{family} row {idx}'))
            positive_float(row, columns[3], f'{family} row {idx}')
            tol_rel = positive_float(row, 'tolerance_rel', f'{family} row {idx}')
            if tol_rel > 0.75:
                gaps.append(f'{family}_calibration_tolerance_rel_too_wide_row_{idx}')
        except IngestionError as exc:
            gaps.append(str(exc))
        if not row.get('source_basis', '').strip():
            gaps.append(f'{family}_calibration_source_basis_missing_row_{idx}')
    if len(rows) < 1:
        gaps.append(f'{family}_calibration_needs_at_least_one_metric')
    return not gaps, {
        'row_count': len(rows),
        'metric_ids': sorted(seen_ids),
        'distance_range_m': [min(distances), max(distances)] if distances else None,
        'reference_value_range': [min(values), max(values)] if values else None,
        'sha256': sha256_file(path),
    }, gaps


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    fire_report_path = Path(args.fire_report)
    dataset_root = Path(args.dataset_root)
    fire_report = load_json(fire_report_path)
    if fire_report.get('status') not in {'PASS-SCREENING', 'PASS-CALIBRATED-CONSEQUENCE-AGREEMENT'}:
        raise IngestionError(f'fire consequence report has unexpected status: {fire_report.get("status")}')

    metadata_path = dataset_root / 'calibration_metadata.json'
    radiation_path = dataset_root / 'radiation_metrics.csv'
    overpressure_path = dataset_root / 'overpressure_metrics.csv'
    metadata_ok, metadata_summary, metadata_gaps = check_metadata(metadata_path)
    radiation_ok, radiation_summary, radiation_gaps = check_metric_csv(
        radiation_path,
        REQUIRED_RADIATION_COLUMNS,
        'reference_flux_w_m2',
        'radiation',
    )
    overpressure_ok, overpressure_summary, overpressure_gaps = check_metric_csv(
        overpressure_path,
        REQUIRED_OVERPRESSURE_COLUMNS,
        'reference_overpressure_kpa',
        'overpressure',
    )
    blocking_gaps = metadata_gaps + radiation_gaps + overpressure_gaps
    ready = not blocking_gaps
    evidence_files = [evidence_entry('fire_consequence_report', fire_report_path)]
    for label, path, ok in (
        ('fire_calibration_metadata', metadata_path, metadata_ok),
        ('radiation_metrics', radiation_path, radiation_ok),
        ('overpressure_metrics', overpressure_path, overpressure_ok),
    ):
        if ok:
            evidence_files.append(evidence_entry(label, path))
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 Fire Calibration Dataset Ingestion',
        'dataset_root': str(dataset_root),
        'fire_consequence_report': str(fire_report_path),
        'clears_fire_consequence_blocker': False,
        'current_inputs': {
            'metadata_available': metadata_ok,
            'radiation_metrics_available': radiation_ok,
            'overpressure_metrics_available': overpressure_ok,
        },
        'metadata_summary': metadata_summary,
        'radiation_summary': radiation_summary,
        'overpressure_summary': overpressure_summary,
        'required_dataset_files': {
            'calibration_metadata_json': str(metadata_path),
            'radiation_metrics_csv': str(radiation_path),
            'overpressure_metrics_csv': str(overpressure_path),
        },
        'schema_requirements': {
            'content_quality_gate_level': 'strict-v1-placeholder-free-and-non-synthetic',
            'calibration_metadata_required_alignment': list(REQUIRED_METADATA_ALIGNMENT),
            'radiation_metrics_csv_columns': list(REQUIRED_RADIATION_COLUMNS),
            'overpressure_metrics_csv_columns': list(REQUIRED_OVERPRESSURE_COLUMNS),
        },
        'blocking_gaps': blocking_gaps,
        'evidence_files': evidence_files,
        'limitations': [
            'This report validates availability and schema of external fire/blast calibration data.',
            'It does not calibrate the model or clear the fire-consequence blocker.',
            'The fire consequence metrics report must still pass with --calibration-dataset-json before production credit is claimed.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('clears_fire_consequence_blocker') is False, 'ingestion report cannot clear fire blocker')
    inputs = data.get('current_inputs')
    require(isinstance(inputs, dict), 'current_inputs missing')
    for key in ('metadata_available', 'radiation_metrics_available', 'overpressure_metrics_available'):
        require(key in inputs, f'current_inputs missing {key}')
    gaps = data.get('blocking_gaps')
    require(isinstance(gaps, list), 'blocking_gaps missing')
    if data.get('status') == STATUS_READY:
        require(not gaps, 'ready report contains blocking gaps')
        require(all(inputs.values()), 'ready report has missing inputs')
    else:
        require(bool(gaps), 'not-ready report must contain blocking gaps')
    requirements = data.get('schema_requirements')
    require(isinstance(requirements, dict), 'schema_requirements missing')
    require(
        requirements.get('content_quality_gate_level') == 'strict-v1-placeholder-free-and-non-synthetic',
        'content quality gate mismatch',
    )
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
        '# Engineering H2 Fire Calibration Dataset Ingestion',
        '',
        f"Status: `{report['status']}`",
        f"Clears fire-consequence blocker: `{report['clears_fire_consequence_blocker']}`",
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
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fire-report', default=str(DEFAULT_FIRE_REPORT))
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
                'engineering_h2_fire_calibration_dataset_ingestion VERIFY-PASS '
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
            'engineering_h2_fire_calibration_dataset_ingestion PASS '
            f"json={out_json} md={out_md} status={report['status']} gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except IngestionError as exc:
        print(f'engineering_h2_fire_calibration_dataset_ingestion FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
