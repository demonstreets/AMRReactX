#!/usr/bin/env python3
"""Write/verify SBEPV5 D27 digitization preflight evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-SBEPV5-D27-DIGITIZATION-PREFLIGHT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724')
DEFAULT_DATASET_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset'
)
DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/'
    'external_plume_public_source_triage_report.json'
)
DEFAULT_DATASET_INGESTION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
    'sbepv5_d27_dataset_ingestion_report.json'
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'sbepv5_d27_digitization_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'sbepv5_d27_digitization_preflight_report.md'

EXPECTED_SENSORS = tuple(range(1, 13))
RELIABLE_SENSORS = (1, 2, 5, 7, 8, 9, 10, 12)
UNRELIABLE_SENSORS = (3, 4, 6, 11)
TIMESERIES_COLUMNS = ('time_s',) + tuple(f'Gas{sid:02d}_vol_percent' for sid in EXPECTED_SENSORS)


class DigitizationPreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DigitizationPreflightError(message)


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
        raise DigitizationPreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise DigitizationPreflightError(f'invalid JSON evidence {path}: {exc}') from exc
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


def write_rows(path: Path, rows: list[list[str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(','.join(f'"{cell}"' for cell in row) for row in rows) + '\n', encoding='utf-8')
    return path


def write_templates(dataset_root: Path) -> list[Path]:
    dataset_root.mkdir(parents=True, exist_ok=True)
    metadata = dataset_root / 'dataset_metadata_template.json'
    sensors = dataset_root / 'sensor_coordinates_template.csv'
    baffles = dataset_root / 'baffle_geometry_template.csv'
    timeseries = dataset_root / 'experimental_timeseries_template.csv'
    uncertainty = dataset_root / 'digitization_uncertainty_record_template.csv'
    metadata.write_text(
        json.dumps(
            {
                'schema_version': 1,
                'benchmark_id': 'hysafe_sbepv5_d27',
                'source': {
                    'url': 'https://publikationen.bibliothek.kit.edu/230068969',
                    'doi': '',
                    'source_file_path': '<local PDF/image/Excel path>',
                    'source_file_sha256': '<64 hex sha256>',
                },
                'digitization': {
                    'method': '<original_excel|figure_digitization|hybrid>',
                    'operator_or_tool': '<tool name/version and operator>',
                    'source_figures_or_tables': ['Figure 2', 'Figure 4', 'Figure 5.a-c'],
                    'axis_calibration_points': '<record plot axis calibration points if figure digitized>',
                    'quality_review': '<reviewer/date>',
                },
                'original_dataset_sha256': '',
                'digitized_dataset_sha256': '<64 hex sha256 after CSV is complete>',
                'case_alignment': {
                    'geometry': True,
                    'release_rate': True,
                    'release_direction': True,
                    'boundary_conditions': True,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + '\n',
        encoding='utf-8',
    )
    write_rows(
        sensors,
        [
            ['sensor_id', 'x_m', 'y_m', 'z_m', 'reliability', 'source_basis', 'digitization_uncertainty_m'],
            ['1', '<x>', '<y>', '<z>', 'reliable', 'Figure 4 or original table', '<=0.02'],
            ['3', '<x>', '<y>', '<z>', 'unreliable', 'Figure 4 or original table', '<=0.02'],
        ],
    )
    write_rows(
        baffles,
        [
            ['baffle_id', 'x_min_m', 'x_max_m', 'y_min_m', 'y_max_m', 'z_min_m', 'z_max_m', 'source_basis', 'digitization_uncertainty_m'],
            ['1', '<x0>', '<x1>', '<y0>', '<y1>', '<z0>', '<z1>', 'Figure 2 or original CAD/table', '<=0.02'],
        ],
    )
    write_rows(
        timeseries,
        [
            list(TIMESERIES_COLUMNS),
            ['0.0'] + ['<vol_percent>' for _ in EXPECTED_SENSORS],
            ['120.0'] + ['<vol_percent>' for _ in EXPECTED_SENSORS],
        ],
    )
    write_rows(
        uncertainty,
        [
            ['artifact', 'source_basis', 'method', 'axis_or_geometry_calibration', 'estimated_uncertainty', 'review_status'],
            ['sensor_coordinates.csv', 'Figure 4/original table', '<method>', '<calibration points>', '<=0.02 m', 'pending'],
            ['baffle_geometry.csv', 'Figure 2/original table', '<method>', '<calibration points>', '<=0.02 m', 'pending'],
            ['experimental_timeseries.csv', 'Figure 5.a-c/original Excel', '<method>', '<axis calibration>', '<vol% and time uncertainty>', 'pending'],
        ],
    )
    return [metadata, sensors, baffles, timeseries, uncertainty]


def gate_row(name: str, passed: bool, evidence: str | list[str], gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else [],
        'gap': '' if passed else gap,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    dataset_root = Path(args.dataset_root)
    public_source_path = Path(args.public_source_triage_report)
    ingestion_path = Path(args.dataset_ingestion_report)
    public_source = load_json(public_source_path)
    ingestion = load_json(ingestion_path)
    templates = write_templates(dataset_root)
    triage_summary = public_source.get('summary') if isinstance(public_source.get('summary'), dict) else {}
    ingestion_inputs = ingestion.get('current_inputs') if isinstance(ingestion.get('current_inputs'), dict) else {}
    public_source_ready = (
        public_source.get('status') == 'PASS-H2-EXTERNAL-PLUME-PUBLIC-SOURCE-TRIAGE'
        and public_source.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and triage_summary.get('public_source_registry_available') is True
    )
    missing_artifacts = [
        {
            'artifact': 'dataset_metadata.json',
            'required_action': 'replace the metadata template with URL/DOI, source file hash, digitization method, uncertainty basis, and case-alignment booleans',
        },
        {
            'artifact': 'sensor_coordinates.csv',
            'required_action': 'digitize or obtain Gas01..Gas12 coordinates with reliability tags and <=0.02 m uncertainty',
        },
        {
            'artifact': 'baffle_geometry.csv',
            'required_action': 'digitize or obtain baffles 1..4 bounds with source basis and <=0.02 m uncertainty',
        },
        {
            'artifact': 'experimental_timeseries.csv',
            'required_action': 'obtain original Excel or digitize Gas01..Gas12 concentration histories through at least 120 s',
        },
    ]
    dataset_ready = ingestion.get('status') == 'PASS-SBEPV5-D27-DATASET-INGESTION'
    matrix = [
        gate_row(
            'public_source_registry_available',
            public_source_ready,
            str(public_source_path),
            'Generate public-source triage for HySafe SBEPV5 D27.',
        ),
        gate_row(
            'digitization_templates_available',
            all(path.is_file() for path in templates),
            [str(path) for path in templates],
            'Create metadata, coordinate, geometry, timeseries, and uncertainty templates.',
        ),
        gate_row(
            'dataset_metadata_ingested',
            ingestion_inputs.get('dataset_metadata_available') is True,
            str(dataset_root / 'dataset_metadata.json'),
            'Fill and validate dataset_metadata.json.',
        ),
        gate_row(
            'sensor_coordinates_ingested',
            ingestion_inputs.get('exact_sensor_coordinates_available') is True,
            str(dataset_root / 'sensor_coordinates.csv'),
            'Fill and validate sensor_coordinates.csv.',
        ),
        gate_row(
            'baffle_geometry_ingested',
            ingestion_inputs.get('exact_baffle_geometry_available') is True,
            str(dataset_root / 'baffle_geometry.csv'),
            'Fill and validate baffle_geometry.csv.',
        ),
        gate_row(
            'experimental_timeseries_ingested',
            ingestion_inputs.get('experimental_timeseries_available') is True,
            str(dataset_root / 'experimental_timeseries.csv'),
            'Fill and validate experimental_timeseries.csv.',
        ),
        gate_row(
            'dataset_ingestion_ready',
            dataset_ready,
            str(ingestion_path),
            'The official SBEPV5 D27 dataset ingestion report must PASS.',
        ),
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'title': 'HySafe SBEPV5 D27 Digitization Preflight',
        'dataset_root': str(dataset_root),
        'clears_reference_data_blocker': False,
        'ready_for_dataset_ingestion': dataset_ready,
        'source_candidates': public_source.get('sources', []),
        'missing_artifacts': [] if dataset_ready else missing_artifacts,
        'summary': {
            'public_source_registry_available': public_source_ready,
            'template_count': len(templates),
            'templates_available': all(path.is_file() for path in templates),
            'dataset_ingestion_status': ingestion.get('status'),
            'dataset_metadata_available': ingestion_inputs.get('dataset_metadata_available') is True,
            'sensor_coordinates_available': ingestion_inputs.get('exact_sensor_coordinates_available') is True,
            'baffle_geometry_available': ingestion_inputs.get('exact_baffle_geometry_available') is True,
            'experimental_timeseries_available': ingestion_inputs.get('experimental_timeseries_available') is True,
            'ready_for_dataset_ingestion': dataset_ready,
            'missing_artifact_count': 0 if dataset_ready else len(missing_artifacts),
        },
        'quality_gate_matrix': matrix,
        'evidence_files': [
            evidence_entry('public_source_triage_report', public_source_path),
            evidence_entry('dataset_ingestion_report', ingestion_path),
        ]
        + [evidence_entry(f'digitization_template_{idx}', path) for idx, path in enumerate(templates, 1)],
        'limitations': [
            'This preflight creates and verifies digitization templates only; it does not ingest original experimental data.',
            'The reference-data blocker remains open until dataset ingestion, external dataset building, and official reference agreement all pass.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark_id mismatch')
    require(data.get('clears_reference_data_blocker') is False, 'digitization preflight cannot clear blocker')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('public_source_registry_available') is True, 'public source registry missing')
    require(summary.get('templates_available') is True, 'digitization templates missing')
    require(int(summary.get('template_count', 0)) >= 4, 'too few digitization templates')
    if summary.get('ready_for_dataset_ingestion') is not True:
        missing = data.get('missing_artifacts')
        require(isinstance(missing, list) and missing, 'not-ready preflight must list missing artifacts')
        require(int(summary.get('missing_artifact_count', 0)) >= 1, 'missing artifact count too small')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality gate matrix missing')
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
        '# HySafe SBEPV5 D27 Digitization Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Dataset root: `{report['dataset_root']}`",
        f"Ready for dataset ingestion: `{report['ready_for_dataset_ingestion']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Missing Artifacts', '']
    for item in report['missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['gap'] or 'none'} |")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
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
    parser.add_argument('--dataset-root', default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument('--public-source-triage-report', default=str(DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT))
    parser.add_argument('--dataset-ingestion-report', default=str(DEFAULT_DATASET_INGESTION_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_sbepv5_digitization_preflight VERIFY-PASS '
                f"json={args.verify_json} missing_artifacts={report['summary']['missing_artifact_count']} "
                f"templates={report['summary']['template_count']}"
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
            'engineering_h2_sbepv5_digitization_preflight PASS '
            f"json={out_json} md={out_md} missing_artifacts={report['summary']['missing_artifact_count']}"
        )
        return 0
    except DigitizationPreflightError as exc:
        print(f'engineering_h2_sbepv5_digitization_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
