#!/usr/bin/env python3
"""Build/verify H2 fire calibration dataset JSON for consequence agreement."""
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

SCHEMA_VERSION = 1
STATUS_READY = 'PASS-H2-FIRE-CALIBRATION-DATASET'
STATUS_NOT_READY = 'NOT_READY-H2-FIRE-CALIBRATION-DATASET'

DEFAULT_FIRE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/'
    'fire_consequence_metrics_report.json'
)
DEFAULT_INGESTION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
    'fire_calibration_dataset_ingestion_report.json'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/'
    'fire_calibration_dataset_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/'
    'fire_calibration_dataset_report.md'
)
DEFAULT_CALIBRATION_DATASET_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/'
    'h2_fire_consequence_calibration_dataset.json'
)


class DatasetError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise DatasetError(message)


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
        raise DatasetError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise DatasetError(f'invalid JSON in {path}: {exc}') from exc
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


def distance_token(distance_m: float) -> str:
    return f'{float(distance_m):g}'.replace('.', 'p').replace('-', 'm') + 'm'


def distance_summary_keys_available(fire: dict[str, Any]) -> bool:
    summary = fire.get('summary') if isinstance(fire.get('summary'), dict) else {}
    radiation = fire.get('radiation_by_distance')
    overpressure = fire.get('overpressure_by_distance')
    if not isinstance(radiation, list) or not isinstance(overpressure, list):
        return False
    distances = []
    for item in radiation:
        if not isinstance(item, dict) or not finite(item.get('distance_m')):
            return False
        distances.append(float(item['distance_m']))
    overpressure_distances = []
    for item in overpressure:
        if not isinstance(item, dict) or not finite(item.get('distance_m')):
            return False
        overpressure_distances.append(float(item['distance_m']))
    if not distances or distances != overpressure_distances:
        return False
    for distance in distances:
        token = distance_token(float(distance))
        required = (
            f'screening_flux_at_{token}_w_m2',
            f'screening_overpressure_at_{token}_kpa',
        )
        if any(key not in summary or not finite(summary.get(key)) for key in required):
            return False
    return True


def positive_float(row: dict[str, str], key: str, label: str) -> float:
    require(key in row, f'{label} missing column {key}')
    require(finite(row[key]), f'{label} non-finite {key}: {row.get(key)!r}')
    value = float(row[key])
    require(value > 0.0, f'{label} {key} must be positive')
    return value


def build_metric(row: dict[str, str], family: str) -> dict[str, Any]:
    metric_id = row.get('metric_id', '').strip()
    distance = positive_float(row, 'distance_m', metric_id or family)
    token = distance_token(distance)
    if family == 'radiation':
        reference = positive_float(row, 'reference_flux_w_m2', metric_id)
        tolerance_abs = positive_float(row, 'tolerance_abs_w_m2', metric_id)
        summary_key = f'screening_flux_at_{token}_w_m2'
        units = 'W/m2'
        quantity = 'radiation_heat_flux'
    else:
        reference = positive_float(row, 'reference_overpressure_kpa', metric_id)
        tolerance_abs = positive_float(row, 'tolerance_abs_kpa', metric_id)
        summary_key = f'screening_overpressure_at_{token}_kpa'
        units = 'kPa'
        quantity = 'peak_overpressure'
    tolerance_rel = positive_float(row, 'tolerance_rel', metric_id)
    return {
        'name': metric_id or f'{family}_{token}',
        'family': family,
        'quantity': quantity,
        'units': units,
        'simulation_summary_key': summary_key,
        'reference_value': reference,
        'reference_basis': row.get('source_basis', '').strip(),
        'tolerance_abs': tolerance_abs,
        'tolerance_rel': tolerance_rel,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    fire_path = Path(args.fire_report)
    ingestion_path = Path(args.ingestion_report)
    calibration_dataset_path = Path(args.calibration_dataset_json)
    fire = load_json(fire_path)
    ingestion = load_json(ingestion_path)
    summary = fire.get('summary') if isinstance(fire.get('summary'), dict) else {}
    blocking_gaps: list[str] = []
    if fire.get('status') != 'PASS-SCREENING':
        blocking_gaps.append('fire_screening_report_not_passed')
    if ingestion.get('status') != 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION':
        blocking_gaps.append('fire_calibration_dataset_ingestion_not_passed')
        if isinstance(ingestion.get('blocking_gaps'), list):
            blocking_gaps.extend(str(item) for item in ingestion['blocking_gaps'])

    metrics: list[dict[str, Any]] = []
    dataset_root = Path(str(ingestion.get('dataset_root', '')))
    if ingestion.get('status') == 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION':
        radiation_rows = read_csv(dataset_root / 'radiation_metrics.csv')
        overpressure_rows = read_csv(dataset_root / 'overpressure_metrics.csv')
        metrics = [build_metric(row, 'radiation') for row in radiation_rows]
        metrics.extend(build_metric(row, 'overpressure') for row in overpressure_rows)
        for metric in metrics:
            key = str(metric['simulation_summary_key'])
            if key not in summary:
                blocking_gaps.append(f'fire_calibration_simulation_summary_key_missing:{key}')
            elif not finite(summary.get(key)):
                blocking_gaps.append(f'fire_calibration_simulation_summary_key_nonfinite:{key}')

    ready = not blocking_gaps
    dataset_written = False
    if ready:
        metadata = load_json(dataset_root / 'calibration_metadata.json')
        dataset = {
            'schema_version': 1,
            'dataset_type': 'h2_fire_consequence_calibration_agreement',
            'case': metadata.get('case'),
            'source_type': metadata.get('source_type'),
            'source': metadata.get('source'),
            'case_alignment': metadata.get('case_alignment'),
            'uncertainty': metadata.get('uncertainty'),
            'metrics': metrics,
        }
        calibration_dataset_path.parent.mkdir(parents=True, exist_ok=True)
        calibration_dataset_path.write_text(json.dumps(dataset, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        dataset_written = True

    evidence_files = [
        evidence_entry('fire_consequence_report', fire_path),
        evidence_entry('fire_calibration_dataset_ingestion_report', ingestion_path),
    ]
    if dataset_written:
        evidence_files.append(evidence_entry('fire_calibration_dataset_json', calibration_dataset_path))
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 Fire Calibration Dataset Builder',
        'fire_consequence_report': str(fire_path),
        'fire_calibration_dataset_ingestion_report': str(ingestion_path),
        'calibration_dataset_json': str(calibration_dataset_path) if dataset_written else None,
        'calibration_dataset_written': dataset_written,
        'clears_fire_consequence_blocker': False,
        'candidate_metric_count': len(metrics),
        'current_inputs': {
            'fire_screening_report_passed': fire.get('status') == 'PASS-SCREENING',
            'dataset_ingestion_passed': ingestion.get('status') == 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION',
            'distance_summary_keys_available': distance_summary_keys_available(fire),
        },
        'blocking_gaps': blocking_gaps,
        'evidence_files': evidence_files,
        'limitations': [
            'This builder writes the calibration dataset JSON consumed by the fire consequence report.',
            'It does not clear the fire-consequence blocker by itself.',
            'Production credit requires the official fire consequence report to pass with --calibration-dataset-json.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('clears_fire_consequence_blocker') is False, 'builder report cannot clear fire blocker')
    gaps = data.get('blocking_gaps')
    require(isinstance(gaps, list), 'blocking_gaps missing')
    if data.get('status') == STATUS_READY:
        require(not gaps, 'ready builder report contains blocking gaps')
        require(data.get('calibration_dataset_written') is True, 'ready builder did not write calibration dataset')
        dataset = load_json(Path(str(data.get('calibration_dataset_json', ''))))
        require(dataset.get('dataset_type') == 'h2_fire_consequence_calibration_agreement', 'bad calibration dataset type')
        families = {item.get('family') for item in dataset.get('metrics', []) if isinstance(item, dict)}
        require({'radiation', 'overpressure'} <= families, 'calibration dataset must include radiation and overpressure')
    else:
        require(bool(gaps), 'not-ready builder report must contain blocking gaps')
        require(data.get('calibration_dataset_written') is False, 'not-ready builder must not write dataset JSON')
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
        '# Engineering H2 Fire Calibration Dataset Builder',
        '',
        f"Status: `{report['status']}`",
        f"Calibration dataset written: `{report['calibration_dataset_written']}`",
        f"Clears fire-consequence blocker: `{report['clears_fire_consequence_blocker']}`",
        '',
        '## Current Inputs',
        '',
    ]
    for key, value in report['current_inputs'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Blocking Gaps', '']
    for gap in report['blocking_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fire-report', default=str(DEFAULT_FIRE_REPORT))
    parser.add_argument('--ingestion-report', default=str(DEFAULT_INGESTION_REPORT))
    parser.add_argument('--calibration-dataset-json', default=str(DEFAULT_CALIBRATION_DATASET_JSON))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_fire_calibration_dataset VERIFY-PASS '
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
            'engineering_h2_fire_calibration_dataset PASS '
            f"json={out_json} md={out_md} status={report['status']} gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except DatasetError as exc:
        print(f'engineering_h2_fire_calibration_dataset FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
