#!/usr/bin/env python3
"""Write/verify selftest evidence for the SBEPV5 D27 dataset ingestion gate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import write_engineering_h2_sbepv5_dataset_ingestion_report as ingestion

SCHEMA_VERSION = 1
STATUS = 'PASS-SBEPV5-D27-DATASET-INGESTION-SELFTEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'sbepv5_d27_dataset_ingestion_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'sbepv5_d27_dataset_ingestion_selftest_report.md'


class SelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelftestError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {'label': label, 'path': str(path), 'sha256': sha256_file(path), 'size_bytes': path.stat().st_size}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise SelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise SelftestError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_metadata(root: Path, label: str) -> None:
    metadata = {
        'schema_version': 1,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'source': {
            'url': f'https://example.invalid/sbepv5/{label}/source',
            'type': 'controlled_fixture_literature_digitized',
        },
        'digitization': {
            'method': 'scripted gate validation fixture',
            'operator_or_tool': 'codex ingestion gate verifier',
            'source_figures_or_tables': ['Figure 2', 'Figure 4', 'Figure 5'],
        },
        'digitized_dataset_sha256': '0' * 64,
        'case_alignment': {
            'geometry': True,
            'release_rate': True,
            'release_direction': True,
            'boundary_conditions': True,
        },
    }
    (root / 'dataset_metadata.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def write_sensor_coordinates(root: Path, gas_labels: bool) -> None:
    rows = []
    reliable = {1, 2, 5, 7, 8, 9, 10, 12}
    for sid in range(1, 13):
        rows.append({
            'sensor_id': f'Gas{sid:02d}' if gas_labels else str(sid),
            'x_m': f'{0.08 + 0.08 * (sid - 1):.3f}',
            'y_m': '0.100',
            'z_m': f'{0.20 + 0.05 * ((sid - 1) % 3):.3f}',
            'reliability': 'reliable' if sid in reliable else 'unreliable',
            'source_basis': 'controlled gate fixture figure digitization record',
            'digitization_uncertainty_m': '0.010',
        })
    write_csv(
        root / 'sensor_coordinates.csv',
        ['sensor_id', 'x_m', 'y_m', 'z_m', 'reliability', 'source_basis', 'digitization_uncertainty_m'],
        rows,
    )


def write_baffle_geometry(root: Path) -> None:
    rows = []
    for bid, x0 in enumerate((0.20, 0.42, 0.64, 0.86), 1):
        rows.append({
            'baffle_id': bid,
            'x_min_m': f'{x0:.3f}',
            'x_max_m': f'{x0 + 0.020:.3f}',
            'y_min_m': '0.000',
            'y_max_m': '0.200',
            'z_min_m': '0.000',
            'z_max_m': '0.300',
            'source_basis': 'controlled gate fixture geometry record',
            'digitization_uncertainty_m': '0.010',
        })
    write_csv(
        root / 'baffle_geometry.csv',
        ['baffle_id', 'x_min_m', 'x_max_m', 'y_min_m', 'y_max_m', 'z_min_m', 'z_max_m', 'source_basis', 'digitization_uncertainty_m'],
        rows,
    )


def write_timeseries(root: Path) -> None:
    fieldnames = ['time_s'] + [f'Gas{sid:02d}_vol_percent' for sid in range(1, 13)]
    rows = []
    for step in range(25):
        t = step * 5.0
        row: dict[str, Any] = {'time_s': f'{t:.1f}'}
        for sid in range(1, 13):
            scale = 0.5 + 0.05 * sid
            row[f'Gas{sid:02d}_vol_percent'] = f'{min(18.0, max(0.0, (t - 10.0) * scale / 5.0)):.3f}'
        rows.append(row)
    write_csv(root / 'experimental_timeseries.csv', fieldnames, rows)


def write_positive_fixture(root: Path, gas_labels: bool) -> None:
    root.mkdir(parents=True, exist_ok=True)
    write_metadata(root, 'gas_labels' if gas_labels else 'numeric_ids')
    write_sensor_coordinates(root, gas_labels)
    write_baffle_geometry(root)
    write_timeseries(root)


def write_negative_fixture(root: Path) -> None:
    write_positive_fixture(root, gas_labels=False)
    metadata = load_json(root / 'dataset_metadata.json')
    metadata['digitization']['method'] = 'placeholder synthetic selftest method'
    (root / 'dataset_metadata.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    rows = []
    with (root / 'sensor_coordinates.csv').open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    rows[0]['sensor_id'] = '1'
    rows[1]['sensor_id'] = '1'
    rows[2]['source_basis'] = '<replace with source figure>'
    write_csv(
        root / 'sensor_coordinates.csv',
        ['sensor_id', 'x_m', 'y_m', 'z_m', 'reliability', 'source_basis', 'digitization_uncertainty_m'],
        rows,
    )


def run_ingestion_case(root: Path, label: str, dataset_root: Path) -> dict[str, Any]:
    output_json = root / f'{label}_ingestion_report.json'
    output_md = root / f'{label}_ingestion_report.md'
    args = argparse.Namespace(
        benchmark_spec_report=str(ingestion.DEFAULT_SPEC_REPORT),
        dataset_root=str(dataset_root),
        output_json=str(output_json),
        output_md=str(output_md),
    )
    report = ingestion.build_report(args)
    ingestion.validate_report_object(report, check_hashes=False)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    ingestion.write_markdown(report, output_md)
    ingestion.validate_report_object(load_json(output_json), check_hashes=True)
    return {
        'label': label,
        'dataset_root': str(dataset_root),
        'report_json': str(output_json),
        'status': report['status'],
        'blocking_gap_count': len(report['blocking_gaps']),
        'sensor_coordinates_available': report['current_inputs']['exact_sensor_coordinates_available'],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.output_json).parent
    fixture_root = root / 'fixtures'
    numeric_root = fixture_root / 'positive_numeric_sensor_ids'
    gas_root = fixture_root / 'positive_gas_sensor_ids'
    negative_root = fixture_root / 'negative_placeholder_duplicate_sensor'
    write_positive_fixture(numeric_root, gas_labels=False)
    write_positive_fixture(gas_root, gas_labels=True)
    write_negative_fixture(negative_root)

    cases = [
        run_ingestion_case(root, 'positive_numeric_sensor_ids', numeric_root),
        run_ingestion_case(root, 'positive_gas_sensor_ids', gas_root),
        run_ingestion_case(root, 'negative_placeholder_duplicate_sensor', negative_root),
    ]
    positive_passed = [case for case in cases if case['label'].startswith('positive_') and case['status'] == ingestion.STATUS_READY]
    negative_refused = [
        case for case in cases
        if case['label'].startswith('negative_') and case['status'] == ingestion.STATUS_NOT_READY
    ]
    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'SBEPV5 D27 Dataset Ingestion Gate Selftest',
        'synthetic_selftest_only': True,
        'does_not_clear_production_blockers': True,
        'case_results': cases,
        'summary': {
            'positive_case_count': 2,
            'positive_passed_count': len(positive_passed),
            'negative_case_count': 1,
            'negative_refused_count': len(negative_refused),
            'numeric_sensor_id_fixture_passed': any(
                case['label'] == 'positive_numeric_sensor_ids' and case['status'] == ingestion.STATUS_READY
                for case in cases
            ),
            'gas_sensor_id_fixture_passed': any(
                case['label'] == 'positive_gas_sensor_ids' and case['status'] == ingestion.STATUS_READY
                for case in cases
            ),
        },
        'evidence_files': [
            evidence_entry(f"{case['label']}_ingestion_report", Path(case['report_json']))
            for case in cases
        ],
        'limitations': [
            'This is fixture-only gate evidence and must not be used as external SBEPV5 production data.',
            'Production credit still requires controlled external sensor, baffle, metadata, and time-series artifacts.',
        ],
    }
    validate_report_object(report, check_hashes=True)
    return report


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('synthetic_selftest_only') is True, 'selftest flag missing')
    require(data.get('does_not_clear_production_blockers') is True, 'selftest cannot clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('positive_case_count', 0)) == 2, 'positive case count mismatch')
    require(int(summary.get('positive_passed_count', 0)) == 2, 'positive fixtures did not pass')
    require(int(summary.get('negative_case_count', 0)) == 1, 'negative case count mismatch')
    require(int(summary.get('negative_refused_count', 0)) == 1, 'negative fixture was not refused')
    require(summary.get('numeric_sensor_id_fixture_passed') is True, 'numeric sensor ID fixture did not pass')
    require(summary.get('gas_sensor_id_fixture_passed') is True, 'Gas-label sensor ID fixture did not pass')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and len(entries) == 3, 'evidence_files mismatch')
    if check_hashes:
        for item in entries:
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence hash mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# SBEPV5 D27 Dataset Ingestion Gate Selftest',
        '',
        f"Status: `{report['status']}`",
        f"Synthetic selftest only: `{report['synthetic_selftest_only']}`",
        f"Does not clear production blockers: `{report['does_not_clear_production_blockers']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Case Results', '']
    for case in report['case_results']:
        lines.append(f"- `{case['label']}`: `{case['status']}`, gaps `{case['blocking_gap_count']}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report_object(report, check_hashes=True)
            summary = report['summary']
            print(
                'engineering_h2_sbepv5_dataset_ingestion_selftest VERIFY-PASS '
                f"json={args.verify_json} positive={summary['positive_passed_count']} "
                f"negative={summary['negative_refused_count']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_sbepv5_dataset_ingestion_selftest PASS '
            f"json={out_json} md={out_md} positive={report['summary']['positive_passed_count']} "
            f"negative={report['summary']['negative_refused_count']}"
        )
        return 0
    except (SelftestError, ingestion.IngestionError) as exc:
        print(f'engineering_h2_sbepv5_dataset_ingestion_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
