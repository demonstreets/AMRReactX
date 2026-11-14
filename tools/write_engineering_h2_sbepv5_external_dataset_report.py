#!/usr/bin/env python3
"""Build/verify SBEPV5 D27 external plume dataset evidence for reference agreement."""
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
STATUS_READY = 'PASS-SBEPV5-D27-EXTERNAL-PLUME-DATASET'
STATUS_NOT_READY = 'NOT_READY-SBEPV5-D27-EXTERNAL-PLUME-DATASET'
H2_LFL_VOLUME_FRACTION = 0.04

DEFAULT_INGESTION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
    'sbepv5_d27_dataset_ingestion_report.json'
)
DEFAULT_SCOUT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/'
    'hybrid_largegrid_8rank_120step_scout_report.json'
)
DEFAULT_PLUME_OBSERVATION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_plume_observation_20260723/'
    'h2_plume_observation_report.json'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/'
    'sbepv5_d27_external_dataset_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/'
    'sbepv5_d27_external_dataset_report.md'
)
DEFAULT_EXTERNAL_DATASET_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/'
    'sbepv5_d27_external_plume_dataset.json'
)

RELIABLE_SENSORS = (1, 2, 5, 7, 8, 9, 10, 12)


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


def sanitize_key(value: Any) -> str:
    text = re.sub(r'[^A-Za-z0-9]+', '_', str(value).strip())
    text = re.sub(r'_+', '_', text).strip('_').lower()
    return text or 'unnamed'


def row_float(row: dict[str, str], key: str, label: str) -> float:
    require(key in row, f'{label} missing column {key}')
    require(finite(row[key]), f'{label} non-finite {key}: {row.get(key)!r}')
    return float(row[key])


def arrival_time(rows: list[dict[str, str]], column: str, threshold_percent: float) -> float | None:
    previous_time: float | None = None
    previous_value: float | None = None
    for row in rows:
        time_s = row_float(row, 'time_s', column)
        value = row_float(row, column, column)
        if value >= threshold_percent:
            if previous_time is None or previous_value is None or value == previous_value:
                return time_s
            frac = (threshold_percent - previous_value) / (value - previous_value)
            return previous_time + frac * (time_s - previous_time)
        previous_time = time_s
        previous_value = value
    return None


def experimental_metrics(dataset_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    timeseries_path = dataset_root / 'experimental_timeseries.csv'
    rows = read_csv(timeseries_path)
    metrics: list[dict[str, Any]] = []
    peaks: dict[str, float] = {}
    arrivals: dict[str, float | None] = {}
    for sensor_id in RELIABLE_SENSORS:
        label = f'Gas{sensor_id:02d}'
        column = f'{label}_vol_percent'
        require(column in rows[0], f'experimental timeseries missing {column}')
        values = [row_float(row, column, column) for row in rows]
        peak_fraction = max(values) / 100.0
        peaks[label] = peak_fraction
        key = sanitize_key(label)
        metrics.append({
            'name': f'{label} peak H2 volume fraction',
            'metric_type': 'sensor_concentration',
            'simulation_summary_key': f'observation_sensor_{key}_peak_X',
            'quantity': 'peak_H2_volume_fraction',
            'units': 'volume_fraction',
            'reference_value': peak_fraction,
            'reference_basis': f'SBEPV5 D27 experimental {label} peak concentration from ingested time series',
            'tolerance_abs': 0.02,
            'tolerance_rel': 0.30,
        })
        arrival = arrival_time(rows, column, H2_LFL_VOLUME_FRACTION * 100.0)
        arrivals[label] = arrival
        if arrival is not None:
            metrics.append({
                'name': f'{label} LFL arrival time',
                'metric_type': 'arrival_time',
                'simulation_summary_key': f'observation_sensor_{key}_arrival_time_lfl',
                'quantity': 'time_to_4_percent_H2',
                'units': 's',
                'reference_value': arrival,
                'reference_basis': f'SBEPV5 D27 experimental {label} first crossing of 4 vol% H2',
                'tolerance_abs': 5.0,
                'tolerance_rel': 0.30,
            })
    return metrics, {'peak_volume_fraction': peaks, 'arrival_time_lfl_s': arrivals}


def sensor_ids_from_observation(report: dict[str, Any]) -> set[str]:
    outputs = report.get('outputs') if isinstance(report.get('outputs'), dict) else {}
    path = Path(str(outputs.get('sensor_timeseries_csv', '')))
    if not path.is_file():
        return set()
    rows = read_csv(path)
    return {str(row.get('sensor_id', '')).strip() for row in rows if str(row.get('sensor_id', '')).strip()}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_path = Path(args.dataset_ingestion_report)
    scout_path = Path(args.scout_report)
    observation_path = Path(args.plume_observation_report)
    external_dataset_path = Path(args.external_dataset_json)
    ingestion = load_json(ingestion_path)
    scout = load_json(scout_path)
    observation = load_json(observation_path)

    blocking_gaps: list[str] = []
    if ingestion.get('status') != 'PASS-SBEPV5-D27-DATASET-INGESTION':
        blocking_gaps.append('sbepv5_dataset_ingestion_not_passed')
        if isinstance(ingestion.get('blocking_gaps'), list):
            blocking_gaps.extend(str(item) for item in ingestion['blocking_gaps'])
    if scout.get('status') != 'PASS-HYBRID-CFD-SCOUT':
        blocking_gaps.append('scout_report_not_passed')
    if observation.get('status') != 'PASS-H2-PLUME-OBSERVATION':
        blocking_gaps.append('plume_observation_report_not_passed')
    obs_summary = observation.get('summary') if isinstance(observation.get('summary'), dict) else {}
    if obs_summary.get('case_matched_external_benchmark') is not True:
        blocking_gaps.append('plume_observation_not_case_matched_to_sbepv5_d27')
    if finite(obs_summary.get('time_end')) and float(obs_summary['time_end']) < 120.0:
        blocking_gaps.append('plume_observation_time_end_before_sbepv5_120s')

    dataset_root = Path(str(ingestion.get('dataset_root', '')))
    metrics: list[dict[str, Any]] = []
    metric_summary: dict[str, Any] = {}
    if ingestion.get('status') == 'PASS-SBEPV5-D27-DATASET-INGESTION':
        metrics, metric_summary = experimental_metrics(dataset_root)
        observed = sensor_ids_from_observation(observation)
        expected = {f'Gas{sid:02d}' for sid in RELIABLE_SENSORS}
        missing = sorted(expected - observed)
        if missing:
            blocking_gaps.append('plume_observation_missing_reliable_sbepv5_sensor_ids:' + ','.join(missing))

    ready = not blocking_gaps
    external_dataset_written = False
    external_dataset: dict[str, Any] | None = None
    if ready:
        metadata = load_json(dataset_root / 'dataset_metadata.json')
        source = metadata.get('source') if isinstance(metadata.get('source'), dict) else {}
        digitization = metadata.get('digitization') if isinstance(metadata.get('digitization'), dict) else {}
        case_alignment = metadata.get('case_alignment') if isinstance(metadata.get('case_alignment'), dict) else {}
        for key in ('geometry', 'release_rate', 'release_direction', 'boundary_conditions'):
            if case_alignment.get(key) is not True:
                blocking_gaps.append(f'dataset_metadata_case_alignment_{key}_not_true')
        ready = not blocking_gaps
        if ready:
            external_dataset = {
                'schema_version': 1,
                'dataset_type': 'external_h2_plume_shape_agreement',
                'dataset_name': 'HySafe SBEPV5 GexCon D27 ingested sensor concentration agreement',
                'case': scout.get('case'),
                'source_type': 'literature_digitized',
                'source': source,
                'digitization': digitization,
                'case_alignment': case_alignment,
                'comparison_basis': 'sbepv5_d27_reliable_sensor_concentration_and_arrival_metrics',
                'metrics': metrics,
            }
            external_dataset_path.parent.mkdir(parents=True, exist_ok=True)
            external_dataset_path.write_text(
                json.dumps(external_dataset, indent=2, sort_keys=True) + '\n',
                encoding='utf-8',
            )
            external_dataset_written = True

    evidence_files = [
        evidence_entry('dataset_ingestion_report', ingestion_path),
        evidence_entry('scout_report', scout_path),
        evidence_entry('plume_observation_report', observation_path),
    ]
    if external_dataset_written:
        evidence_files.append(evidence_entry('external_plume_dataset_json', external_dataset_path))

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'title': 'HySafe SBEPV5 D27 External Plume Dataset Builder',
        'clears_reference_data_blocker': False,
        'dataset_ingestion_report': str(ingestion_path),
        'scout_report': str(scout_path),
        'plume_observation_report': str(observation_path),
        'external_dataset_json': str(external_dataset_path) if external_dataset_written else None,
        'external_dataset_written': external_dataset_written,
        'current_inputs': {
            'dataset_ingestion_passed': ingestion.get('status') == 'PASS-SBEPV5-D27-DATASET-INGESTION',
            'scout_report_passed': scout.get('status') == 'PASS-HYBRID-CFD-SCOUT',
            'plume_observation_passed': observation.get('status') == 'PASS-H2-PLUME-OBSERVATION',
            'plume_observation_case_matched_to_sbepv5': obs_summary.get('case_matched_external_benchmark') is True,
            'plume_observation_time_end_s': obs_summary.get('time_end'),
        },
        'candidate_metric_count': len(metrics),
        'candidate_metric_summary': metric_summary,
        'blocking_gaps': blocking_gaps,
        'evidence_files': evidence_files,
        'limitations': [
            'This builder prepares the external plume dataset JSON consumed by the official reference-agreement report.',
            'The builder report itself does not clear the reference-data blocker.',
            'External validation is only claimed after the official reference-agreement report passes with the generated dataset JSON.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark_id mismatch')
    require(data.get('clears_reference_data_blocker') is False, 'builder report cannot clear blocker')
    gaps = data.get('blocking_gaps')
    require(isinstance(gaps, list), 'blocking_gaps missing')
    if data.get('status') == STATUS_READY:
        require(not gaps, 'ready builder report contains blocking gaps')
        require(data.get('external_dataset_written') is True, 'ready builder did not write external dataset')
        dataset_path = Path(str(data.get('external_dataset_json', '')))
        dataset = load_json(dataset_path)
        require(dataset.get('dataset_type') == 'external_h2_plume_shape_agreement', 'bad external dataset type')
        require(isinstance(dataset.get('metrics'), list) and len(dataset['metrics']) >= 2, 'external dataset metrics missing')
    else:
        require(bool(gaps), 'not-ready builder report must contain blocking gaps')
        require(data.get('external_dataset_written') is False, 'not-ready builder must not write external dataset')
    inputs = data.get('current_inputs')
    require(isinstance(inputs, dict), 'current_inputs missing')
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
        '# HySafe SBEPV5 D27 External Plume Dataset Builder',
        '',
        f"Status: `{report['status']}`",
        f"External dataset written: `{report['external_dataset_written']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        '',
        '## Current Inputs',
        '',
    ]
    for key, value in report['current_inputs'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Blocking Gaps', '']
    for gap in report['blocking_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Outputs', '']
    lines.append(f"- External dataset JSON: `{report['external_dataset_json']}`")
    lines.append(f"- Candidate metric count: `{report['candidate_metric_count']}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-ingestion-report', default=str(DEFAULT_INGESTION_REPORT))
    parser.add_argument('--scout-report', default=str(DEFAULT_SCOUT_REPORT))
    parser.add_argument('--plume-observation-report', default=str(DEFAULT_PLUME_OBSERVATION_REPORT))
    parser.add_argument('--external-dataset-json', default=str(DEFAULT_EXTERNAL_DATASET_JSON))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_sbepv5_external_dataset VERIFY-PASS '
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
            'engineering_h2_sbepv5_external_dataset PASS '
            f"json={out_json} md={out_md} status={report['status']} gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except DatasetError as exc:
        print(f'engineering_h2_sbepv5_external_dataset FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
