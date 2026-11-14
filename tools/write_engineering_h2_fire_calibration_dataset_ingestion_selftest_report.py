#!/usr/bin/env python3
"""Write/verify fire calibration dataset ingestion strict-gate selftest evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import write_engineering_h2_fire_calibration_dataset_ingestion_report as ingestion

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION-SELFTEST'
DEFAULT_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727'
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'fire_calibration_dataset_ingestion_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'fire_calibration_dataset_ingestion_selftest_report.md'


class SelftestError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SelftestError(message)


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


def write_csv(path: Path, rows: list[dict[str, Any]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def positive_metadata(case: str) -> dict[str, Any]:
    return {
        'schema_version': 1,
        'dataset_type': 'h2_fire_consequence_calibration_agreement',
        'case': case,
        'source_type': 'literature_digitized',
        'source': {
            'title': 'Controlled validation publication for fire consequence calibration',
            'doi': '10.0000/h2-fire-validation',
        },
        'case_alignment': {
            'fuel': True,
            'release_or_cloud_mass': True,
            'ignition_or_burn_basis': True,
            'radiation_measurement_basis': True,
            'overpressure_measurement_basis': True,
            'boundary_conditions': True,
        },
        'uncertainty': {
            'radiation': 'Digitized heat-flux uncertainty is bounded by instrument and graph resolution.',
            'overpressure': 'Digitized pressure uncertainty is bounded by gauge and graph resolution.',
        },
    }


def radiation_rows() -> list[dict[str, Any]]:
    return [
        {
            'metric_id': 'rad_near',
            'distance_m': 6.0,
            'reference_flux_w_m2': 14500.0,
            'tolerance_abs_w_m2': 1600.0,
            'tolerance_rel': 0.18,
            'source_basis': 'digitized heat-flux gauge at near-field station',
        },
        {
            'metric_id': 'rad_far',
            'distance_m': 12.0,
            'reference_flux_w_m2': 5200.0,
            'tolerance_abs_w_m2': 700.0,
            'tolerance_rel': 0.22,
            'source_basis': 'digitized heat-flux gauge at far-field station',
        },
    ]


def overpressure_rows() -> list[dict[str, Any]]:
    return [
        {
            'metric_id': 'op_near',
            'distance_m': 8.0,
            'reference_overpressure_kpa': 17.0,
            'tolerance_abs_kpa': 2.5,
            'tolerance_rel': 0.25,
            'source_basis': 'digitized peak pressure gauge at near-field station',
        },
        {
            'metric_id': 'op_far',
            'distance_m': 16.0,
            'reference_overpressure_kpa': 5.0,
            'tolerance_abs_kpa': 1.0,
            'tolerance_rel': 0.30,
            'source_basis': 'digitized peak pressure gauge at far-field station',
        },
    ]


def write_dataset(root: Path, case: str, polluted: bool = False) -> None:
    root.mkdir(parents=True, exist_ok=True)
    metadata = positive_metadata(case)
    rad = radiation_rows()
    op = overpressure_rows()
    if polluted:
        metadata['source']['title'] = 'placeholder synthetic selftest source'
        metadata['uncertainty']['radiation'] = '<replace with heat-flux uncertainty>'
        rad[0]['source_basis'] = '<replace with radiation source basis>'
        op[0]['metric_id'] = op[1]['metric_id']
    (root / 'calibration_metadata.json').write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    write_csv(root / 'radiation_metrics.csv', rad, ingestion.REQUIRED_RADIATION_COLUMNS)
    write_csv(root / 'overpressure_metrics.csv', op, ingestion.REQUIRED_OVERPRESSURE_COLUMNS)


def run_ingestion_case(repo_root: Path, label: str, dataset_root: Path) -> dict[str, Any]:
    report = ingestion.build_report(
        SimpleNamespace(
            fire_report=str(ingestion.DEFAULT_FIRE_REPORT),
            dataset_root=str(dataset_root),
        )
    )
    out_json = DEFAULT_ROOT / 'fixtures' / f'{label}_ingestion_report.json'
    out_md = DEFAULT_ROOT / 'fixtures' / f'{label}_ingestion_report.md'
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    ingestion.write_markdown(report, out_md)
    ingestion.validate_report_object(report, check_hashes=False)
    return {
        'label': label,
        'status': report['status'],
        'blocking_gaps': report['blocking_gaps'],
        'report': str(out_json),
        'report_sha256': sha256_file(out_json),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    fixture_root = root / 'fixtures'
    positive_literature = fixture_root / 'positive_literature_digitized'
    positive_wind_tunnel = fixture_root / 'positive_wind_tunnel'
    negative_placeholder = fixture_root / 'negative_placeholder_duplicate_metric'
    write_dataset(positive_literature, 'fire_gate_validation_literature_digitized', polluted=False)
    write_dataset(positive_wind_tunnel, 'fire_gate_validation_wind_tunnel', polluted=False)
    metadata_path = positive_wind_tunnel / 'calibration_metadata.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    metadata['source_type'] = 'wind_tunnel'
    metadata['source'] = {
        'title': 'Controlled wind tunnel validation publication',
        'url': 'https://example.invalid/h2-fire-wind-tunnel-validation',
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_dataset(negative_placeholder, 'fire_negative_placeholder_duplicate_metric', polluted=True)

    cases = [
        run_ingestion_case(root, 'positive_literature_digitized', positive_literature),
        run_ingestion_case(root, 'positive_wind_tunnel', positive_wind_tunnel),
        run_ingestion_case(root, 'negative_placeholder_duplicate_metric', negative_placeholder),
    ]
    positive = [case for case in cases if case['label'].startswith('positive_')]
    negative = [case for case in cases if case['label'].startswith('negative_')]
    positive_passed = [case for case in positive if case['status'] == ingestion.STATUS_READY]
    negative_refused = [case for case in negative if case['status'] == ingestion.STATUS_NOT_READY]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Fire Calibration Dataset Ingestion Selftest',
        'synthetic_selftest_only': True,
        'does_not_clear_production_blockers': True,
        'fixture_root': str(fixture_root),
        'cases': cases,
        'summary': {
            'positive_case_count': len(positive),
            'positive_passed_count': len(positive_passed),
            'negative_case_count': len(negative),
            'negative_refused_count': len(negative_refused),
            'placeholder_negative_refused': any(
                case['label'] == 'negative_placeholder_duplicate_metric'
                and case['status'] == ingestion.STATUS_NOT_READY
                and any('placeholder' in gap for gap in case['blocking_gaps'])
                for case in negative
            ),
            'duplicate_metric_negative_refused': any(
                case['label'] == 'negative_placeholder_duplicate_metric'
                and case['status'] == ingestion.STATUS_NOT_READY
                and any('duplicate_metric_id' in gap for gap in case['blocking_gaps'])
                for case in negative
            ),
        },
        'evidence_files': [
            evidence_entry(case['label'] + '_ingestion_report', Path(case['report']))
            for case in cases
        ],
        'limitations': [
            'This is synthetic gate-validation evidence only and cannot clear production blockers.',
            'Production credit requires controlled external fire calibration files and official consequence agreement.',
        ],
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise SelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise SelftestError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), 'JSON evidence is not an object')
    return data


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('synthetic_selftest_only') is True, 'selftest must be marked synthetic only')
    require(data.get('does_not_clear_production_blockers') is True, 'selftest cannot clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('positive_case_count', 0)) == 2, 'positive case count mismatch')
    require(int(summary.get('positive_passed_count', 0)) == 2, 'positive fixtures did not pass')
    require(int(summary.get('negative_case_count', 0)) == 1, 'negative case count mismatch')
    require(int(summary.get('negative_refused_count', 0)) == 1, 'negative fixture was not refused')
    require(summary.get('placeholder_negative_refused') is True, 'placeholder negative fixture not refused')
    require(summary.get('duplicate_metric_negative_refused') is True, 'duplicate metric negative fixture not refused')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and len(entries) == 3, 'evidence_files mismatch')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Fire Calibration Dataset Ingestion Selftest',
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
    lines += ['', '## Cases', '']
    for case in report['cases']:
        lines.append(f"- `{case['label']}`: `{case['status']}` gaps `{len(case['blocking_gaps'])}`")
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(DEFAULT_ROOT))
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
                'engineering_h2_fire_calibration_dataset_ingestion_selftest VERIFY-PASS '
                f"json={args.verify_json} positive={summary['positive_passed_count']} "
                f"negative={summary['negative_refused_count']}"
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
            'engineering_h2_fire_calibration_dataset_ingestion_selftest PASS '
            f"json={out_json} md={out_md} positive={report['summary']['positive_passed_count']} "
            f"negative={report['summary']['negative_refused_count']}"
        )
        return 0
    except (SelftestError, ingestion.IngestionError) as exc:
        print(f'engineering_h2_fire_calibration_dataset_ingestion_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
