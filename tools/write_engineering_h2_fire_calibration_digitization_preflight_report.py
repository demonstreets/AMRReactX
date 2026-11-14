#!/usr/bin/env python3
"""Write/verify H2 fire calibration digitization preflight evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from write_engineering_h2_fire_calibration_dataset_ingestion_report import (
    REQUIRED_METADATA_ALIGNMENT,
    REQUIRED_OVERPRESSURE_COLUMNS,
    REQUIRED_RADIATION_COLUMNS,
)

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724')
DEFAULT_DATASET_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset'
)
DEFAULT_TEMPLATE_ROOT = DEFAULT_ROOT / 'templates'
DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/'
    'fire_calibration_public_source_triage_report.json'
)
DEFAULT_DATASET_INGESTION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
    'fire_calibration_dataset_ingestion_report.json'
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'fire_calibration_digitization_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'fire_calibration_digitization_preflight_report.md'


class FireCalibrationDigitizationPreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FireCalibrationDigitizationPreflightError(message)


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
        raise FireCalibrationDigitizationPreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise FireCalibrationDigitizationPreflightError(f'invalid JSON evidence {path}: {exc}') from exc
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


def write_templates(template_root: Path) -> list[Path]:
    template_root.mkdir(parents=True, exist_ok=True)
    metadata = template_root / 'calibration_metadata_template.json'
    radiation = template_root / 'radiation_metrics_template.csv'
    overpressure = template_root / 'overpressure_metrics_template.csv'
    source_registry = template_root / 'fire_calibration_source_registry_template.csv'
    uncertainty = template_root / 'fire_calibration_digitization_uncertainty_template.csv'
    metadata.write_text(
        json.dumps(
            {
                'schema_version': 1,
                'dataset_type': 'h2_fire_consequence_calibration_agreement',
                'case': 'engineering_h2_fire_consequence_screening',
                'source_type': '<field_test|wind_tunnel|literature_digitized>',
                'source': {
                    'title': '<selected radiation and overpressure source title(s)>',
                    'url': '<public URL if available>',
                    'doi': '<DOI if available>',
                    'source_file_path': '<local PDF/figure/table path>',
                    'source_file_sha256': '<64 hex sha256>',
                },
                'case_alignment': {key: True for key in REQUIRED_METADATA_ALIGNMENT},
                'uncertainty': {
                    'radiation': '<heat-flux instrument or digitization uncertainty basis>',
                    'overpressure': '<pressure gauge or digitization uncertainty basis>',
                },
            },
            indent=2,
            sort_keys=True,
        )
        + '\n',
        encoding='utf-8',
    )
    write_rows(
        radiation,
        [
            list(REQUIRED_RADIATION_COLUMNS),
            ['radiation_1m', '1.0', '<positive W/m2>', '<positive W/m2>', '<=0.75', '<instrument/table/figure basis>'],
        ],
    )
    write_rows(
        overpressure,
        [
            list(REQUIRED_OVERPRESSURE_COLUMNS),
            ['overpressure_1m', '1.0', '<positive kPa>', '<positive kPa>', '<=0.75', '<gauge/table/figure basis>'],
        ],
    )
    write_rows(
        source_registry,
        [
            ['family', 'candidate_id', 'title', 'url_or_doi', 'selected_for_calibration', 'required_digitization'],
            ['radiation', 'mdpi_jet_fire_2024', 'Study on Thermal Radiation Characteristics and the Multi-Point Source Model of Hydrogen Jet Fire', 'https://www.mdpi.com/2076-3417/14/16/7098', 'false', 'heat flux distances and values'],
            ['overpressure', 'hyindoor_low_strength_enclosure_2017', 'Experimental studies on vented deflagrations in a low strength enclosure', '10.1016/j.ijhydene.2016.06.223', 'false', 'peak pressure gauge readings'],
        ],
    )
    write_rows(
        uncertainty,
        [
            ['artifact', 'source_basis', 'method', 'calibration_points_or_table', 'estimated_uncertainty', 'review_status'],
            ['radiation_metrics.csv', '<figure/table/source>', '<original table|figure digitization>', '<axis/table details>', '<flux uncertainty>', 'pending'],
            ['overpressure_metrics.csv', '<figure/table/source>', '<original table|figure digitization>', '<axis/table details>', '<pressure uncertainty>', 'pending'],
        ],
    )
    return [metadata, radiation, overpressure, source_registry, uncertainty]


def gate_row(name: str, passed: bool, evidence: str | list[str], gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else [],
        'gap': '' if passed else gap,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    dataset_root = Path(args.dataset_root)
    template_root = Path(args.template_root)
    public_source_path = Path(args.public_source_triage_report)
    ingestion_path = Path(args.dataset_ingestion_report)
    public_source = load_json(public_source_path)
    ingestion = load_json(ingestion_path)
    templates = write_templates(template_root)
    source_summary = public_source.get('summary') if isinstance(public_source.get('summary'), dict) else {}
    ingestion_inputs = ingestion.get('current_inputs') if isinstance(ingestion.get('current_inputs'), dict) else {}
    public_source_ready = (
        public_source.get('status') == 'PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE'
        and source_summary.get('public_source_registry_available') is True
        and source_summary.get('radiation_candidate_available') is True
        and source_summary.get('overpressure_candidate_available') is True
    )
    dataset_ready = ingestion.get('status') == 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION'
    missing_artifacts = [
        {
            'artifact': 'calibration_metadata.json',
            'required_action': 'select calibration sources and record source hash, uncertainty, and all case-alignment booleans',
        },
        {
            'artifact': 'radiation_metrics.csv',
            'required_action': 'digitize or obtain heat-flux measurements with distances, tolerances, and source basis',
        },
        {
            'artifact': 'overpressure_metrics.csv',
            'required_action': 'digitize or obtain peak overpressure measurements with distances, tolerances, and source basis',
        },
        {
            'artifact': 'calibrated_fire_consequence_report',
            'required_action': 'rerun the official fire consequence report with the generated calibration dataset JSON',
        },
    ]
    matrix = [
        gate_row(
            'public_source_registry_available',
            public_source_ready,
            str(public_source_path),
            'Generate fire calibration public-source triage with radiation and overpressure candidates.',
        ),
        gate_row(
            'digitization_templates_available',
            all(path.is_file() for path in templates),
            [str(path) for path in templates],
            'Create fire calibration metadata, metric, source registry, and uncertainty templates.',
        ),
        gate_row(
            'calibration_metadata_ingested',
            ingestion_inputs.get('metadata_available') is True,
            str(dataset_root / 'calibration_metadata.json'),
            'Fill and validate calibration_metadata.json.',
        ),
        gate_row(
            'radiation_metrics_ingested',
            ingestion_inputs.get('radiation_metrics_available') is True,
            str(dataset_root / 'radiation_metrics.csv'),
            'Fill and validate radiation_metrics.csv.',
        ),
        gate_row(
            'overpressure_metrics_ingested',
            ingestion_inputs.get('overpressure_metrics_available') is True,
            str(dataset_root / 'overpressure_metrics.csv'),
            'Fill and validate overpressure_metrics.csv.',
        ),
        gate_row(
            'dataset_ingestion_ready',
            dataset_ready,
            str(ingestion_path),
            'The official fire calibration dataset ingestion report must PASS.',
        ),
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Fire Calibration Digitization Preflight',
        'dataset_root': str(dataset_root),
        'template_root': str(template_root),
        'clears_fire_consequence_blocker': False,
        'ready_for_dataset_ingestion': dataset_ready,
        'missing_artifacts': [] if dataset_ready else missing_artifacts,
        'summary': {
            'public_source_registry_available': public_source_ready,
            'radiation_candidate_available': source_summary.get('radiation_candidate_available') is True,
            'overpressure_candidate_available': source_summary.get('overpressure_candidate_available') is True,
            'template_count': len(templates),
            'templates_available': all(path.is_file() for path in templates),
            'dataset_ingestion_status': ingestion.get('status'),
            'metadata_available': ingestion_inputs.get('metadata_available') is True,
            'radiation_metrics_available': ingestion_inputs.get('radiation_metrics_available') is True,
            'overpressure_metrics_available': ingestion_inputs.get('overpressure_metrics_available') is True,
            'ready_for_dataset_ingestion': dataset_ready,
            'missing_artifact_count': 0 if dataset_ready else len(missing_artifacts),
        },
        'quality_gate_matrix': matrix,
        'evidence_files': [
            evidence_entry('fire_calibration_public_source_triage_report', public_source_path),
            evidence_entry('fire_calibration_dataset_ingestion_report', ingestion_path),
        ]
        + [evidence_entry(f'fire_calibration_template_{idx}', path) for idx, path in enumerate(templates, 1)],
        'limitations': [
            'This preflight creates and verifies calibration digitization templates only; it does not ingest experimental data.',
            'The fire-consequence blocker remains open until ingestion, dataset building, and calibrated consequence agreement all pass.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('clears_fire_consequence_blocker') is False, 'digitization preflight cannot clear fire blocker')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('public_source_registry_available') is True, 'public source registry missing')
    require(summary.get('radiation_candidate_available') is True, 'radiation candidate missing')
    require(summary.get('overpressure_candidate_available') is True, 'overpressure candidate missing')
    require(summary.get('templates_available') is True, 'digitization templates missing')
    require(int(summary.get('template_count', 0)) >= 5, 'too few digitization templates')
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
        '# Engineering H2 Fire Calibration Digitization Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Dataset root: `{report['dataset_root']}`",
        f"Ready for dataset ingestion: `{report['ready_for_dataset_ingestion']}`",
        f"Clears fire-consequence blocker: `{report['clears_fire_consequence_blocker']}`",
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
    parser.add_argument('--template-root', default=str(DEFAULT_TEMPLATE_ROOT))
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
                'engineering_h2_fire_calibration_digitization_preflight VERIFY-PASS '
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
            'engineering_h2_fire_calibration_digitization_preflight PASS '
            f"json={out_json} md={out_md} missing_artifacts={report['summary']['missing_artifact_count']}"
        )
        return 0
    except FireCalibrationDigitizationPreflightError as exc:
        print(f'engineering_h2_fire_calibration_digitization_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
