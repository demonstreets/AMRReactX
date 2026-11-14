#!/usr/bin/env python3
"""Write and verify the engineering H2 fire calibration package report."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from write_engineering_h2_fire_calibration_dataset_ingestion_report import (
    DEFAULT_DATASET_ROOT,
    DEFAULT_OUTPUT_JSON as DEFAULT_INGESTION_JSON,
    REQUIRED_METADATA_ALIGNMENT,
    REQUIRED_OVERPRESSURE_COLUMNS,
    REQUIRED_RADIATION_COLUMNS,
    STATUS_READY as INGESTION_READY_STATUS,
)

SCHEMA_VERSION = 5
STATUS_READY = 'PASS-H2-FIRE-CALIBRATION-PACKAGE'
STATUS_NOT_READY = 'NOT_READY-H2-FIRE-CALIBRATION-PACKAGE'
DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_fire_calibration_package_20260723')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'fire_calibration_package_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'fire_calibration_package_report.md'
DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/'
    'fire_calibration_public_source_triage_report.json'
)
DEFAULT_LITERATURE_METRIC_PREFLIGHT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/'
    'fire_calibration_literature_metric_preflight_report.json'
)
DEFAULT_INGESTION_SELFTEST_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/'
    'fire_calibration_dataset_ingestion_selftest_report.json'
)


class FireCalibrationPackageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FireCalibrationPackageError(message)


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
        raise FireCalibrationPackageError(f'missing JSON: {path}') from exc
    except json.JSONDecodeError as exc:
        raise FireCalibrationPackageError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def write_csv_template(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def metadata_template() -> dict[str, Any]:
    return {
        'schema_version': 1,
        'dataset_type': 'h2_fire_consequence_calibration_agreement',
        'case': 'engineering_h2_fire_consequence_screening',
        'source_type': 'literature_digitized',
        'source': {
            'title': 'Replace with fire/blast experiment or field-test source',
            'url': 'https://replace-with-public-source-or-use-doi',
            'doi': '',
            'notes': 'Use field_test, wind_tunnel, or literature_digitized only.',
        },
        'case_alignment': {key: False for key in REQUIRED_METADATA_ALIGNMENT},
        'uncertainty': {
            'radiation': 'Replace with heat-flux instrument/digitization uncertainty basis.',
            'overpressure': 'Replace with pressure gauge/digitization uncertainty basis.',
        },
    }


def intake_checklist_lines() -> list[str]:
    rows = [
        ['item', 'required_evidence', 'production_rule'],
        ['calibration_metadata.json', 'external fire/blast source metadata', 'schema_version=1 and correct dataset_type'],
        ['source_type', 'source classification', 'field_test|wind_tunnel|literature_digitized'],
        ['source.title', 'source title', 'non-empty'],
        ['source.url_or_doi', 'public URL or DOI', 'at least one non-empty identifier'],
        ['case_alignment.fuel', 'fuel match basis', 'true'],
        ['case_alignment.release_or_cloud_mass', 'release/cloud mass match basis', 'true'],
        ['case_alignment.ignition_or_burn_basis', 'ignition or burn basis match', 'true'],
        ['case_alignment.radiation_measurement_basis', 'radiation measurement basis', 'true'],
        ['case_alignment.overpressure_measurement_basis', 'overpressure measurement basis', 'true'],
        ['case_alignment.boundary_conditions', 'boundary condition match basis', 'true'],
        ['uncertainty.radiation', 'heat flux uncertainty basis', 'non-empty'],
        ['uncertainty.overpressure', 'pressure uncertainty basis', 'non-empty'],
        ['literature_metric_preflight', 'radiation and overpressure public metric anchors', 'PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT'],
        ['radiation_metrics.csv', 'distance, reference flux, absolute/relative tolerance, source basis', 'one or more rows, tolerance_rel <= 0.75'],
        ['overpressure_metrics.csv', 'distance, reference peak overpressure, absolute/relative tolerance, source basis', 'one or more rows, tolerance_rel <= 0.75'],
        ['dataset_builder', 'calibration dataset JSON generated from passed ingestion', 'builder report can run only after ingestion PASS'],
        ['fire_consequence_report', 'official consequence report run with calibration dataset JSON', 'required before clearing fire-consequence blocker'],
    ]
    return [','.join(f'"{cell}"' for cell in row) for row in rows]


def write_package_templates(dataset_root: Path) -> list[Path]:
    dataset_root.mkdir(parents=True, exist_ok=True)
    readme = dataset_root / 'README.md'
    metadata = dataset_root / 'calibration_metadata_template.json'
    radiation = dataset_root / 'radiation_metrics_template.csv'
    overpressure = dataset_root / 'overpressure_metrics_template.csv'
    checklist = dataset_root / 'fire_calibration_intake_checklist.csv'
    readme.write_text(
        '\n'.join(
            [
                '# Engineering H2 Fire Calibration Dataset',
                '',
                'This directory is the ingestion root for external H2 fire and blast calibration evidence.',
                '',
                'Required production data files:',
                '- `calibration_metadata.json`',
                '- `radiation_metrics.csv`',
                '- `overpressure_metrics.csv`',
                '',
                'Templates in this directory show the required schema. The ingestion report remains NOT_READY until real calibration data files pass validation.',
                '',
                '`fire_calibration_intake_checklist.csv` lists the production intake rules that must be backed by controlled external evidence.',
                '',
                'Production credit is only claimed after the official fire consequence report passes with the generated calibration dataset JSON.',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    metadata.write_text(json.dumps(metadata_template(), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_csv_template(
        radiation,
        REQUIRED_RADIATION_COLUMNS,
        [
            {
                'metric_id': 'radiation_1m',
                'distance_m': '1.0',
                'reference_flux_w_m2': '<positive measured heat flux>',
                'tolerance_abs_w_m2': '<positive absolute tolerance>',
                'tolerance_rel': '<0.75 or tighter>',
                'source_basis': 'Replace with instrument, figure, table, or digitization basis.',
            }
        ],
    )
    write_csv_template(
        overpressure,
        REQUIRED_OVERPRESSURE_COLUMNS,
        [
            {
                'metric_id': 'overpressure_1m',
                'distance_m': '1.0',
                'reference_overpressure_kpa': '<positive measured peak overpressure>',
                'tolerance_abs_kpa': '<positive absolute tolerance>',
                'tolerance_rel': '<0.75 or tighter>',
                'source_basis': 'Replace with gauge, figure, table, or digitization basis.',
            }
        ],
    )
    checklist.write_text('\n'.join(intake_checklist_lines()) + '\n', encoding='utf-8')
    return [readme, metadata, radiation, overpressure, checklist]


def gate_row(name: str, passed: bool, evidence: str, gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else '',
        'gap': '' if passed else gap,
    }


def build_quality_gate_matrix(
    ingestion: dict[str, Any],
    ingestion_selftest: dict[str, Any],
    public_source_triage: dict[str, Any],
    literature_metric: dict[str, Any],
    ready: bool,
) -> list[dict[str, Any]]:
    inputs = ingestion.get('current_inputs', {}) if isinstance(ingestion.get('current_inputs'), dict) else {}
    source_summary = (
        public_source_triage.get('summary', {})
        if isinstance(public_source_triage.get('summary'), dict)
        else {}
    )
    literature_summary = (
        literature_metric.get('summary', {})
        if isinstance(literature_metric.get('summary'), dict)
        else {}
    )
    metadata = ingestion.get('metadata_summary', {}) if isinstance(ingestion.get('metadata_summary'), dict) else {}
    radiation = ingestion.get('radiation_summary', {}) if isinstance(ingestion.get('radiation_summary'), dict) else {}
    overpressure = ingestion.get('overpressure_summary', {}) if isinstance(ingestion.get('overpressure_summary'), dict) else {}
    alignment = metadata.get('case_alignment', {}) if isinstance(metadata.get('case_alignment'), dict) else {}
    source = metadata.get('source', {}) if isinstance(metadata.get('source'), dict) else {}
    source_ok = bool(metadata.get('source_type') in {'field_test', 'wind_tunnel', 'literature_digitized'} and (source.get('url') or source.get('doi')))
    alignment_ok = bool(alignment and all(alignment.get(key) is True for key in REQUIRED_METADATA_ALIGNMENT))
    radiation_count = int(radiation.get('row_count', 0)) if isinstance(radiation.get('row_count', 0), int) else 0
    overpressure_count = int(overpressure.get('row_count', 0)) if isinstance(overpressure.get('row_count', 0), int) else 0
    selftest_summary = (
        ingestion_selftest.get('summary', {})
        if isinstance(ingestion_selftest.get('summary'), dict)
        else {}
    )
    selftest_ok = (
        ingestion_selftest.get('status') == 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION-SELFTEST'
        and int(selftest_summary.get('positive_passed_count', 0)) == 2
        and int(selftest_summary.get('negative_refused_count', 0)) == 1
        and selftest_summary.get('placeholder_negative_refused') is True
        and selftest_summary.get('duplicate_metric_negative_refused') is True
    )
    return [
        gate_row(
            'public_source_triage_ready',
            public_source_triage.get('status') == 'PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE',
            'public fire calibration source triage passed',
            'Generate the fire calibration public-source triage report.',
        ),
        gate_row(
            'radiation_and_overpressure_candidates_available',
            source_summary.get('radiation_candidate_available') is True
            and source_summary.get('overpressure_candidate_available') is True,
            'radiation and overpressure public source candidates identified',
            'Identify at least one radiation and one overpressure calibration candidate source.',
        ),
        gate_row(
            'literature_metric_preflight_ready',
            literature_metric.get('status') == 'PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT'
            and literature_summary.get('radiation_metric_anchor_available') is True
            and literature_summary.get('overpressure_metric_anchor_available') is True,
            'public radiation and overpressure metric anchors are machine-checkable',
            'Generate the H2 fire calibration literature metric preflight report.',
        ),
        gate_row(
            'ingestion_report_passed',
            ingestion.get('status') == INGESTION_READY_STATUS,
            INGESTION_READY_STATUS,
            'Fire calibration dataset ingestion must pass before package is builder-ready.',
        ),
        gate_row(
            'ingestion_strict_gate_selftest_passed',
            selftest_ok,
            'fire calibration ingestion strict-gate selftest passed',
            'Generate and verify fire calibration dataset ingestion selftest evidence.',
        ),
        gate_row(
            'metadata_available',
            inputs.get('metadata_available') is True,
            'calibration_metadata.json accepted by ingestion',
            'Provide calibration_metadata.json with the required schema.',
        ),
        gate_row(
            'experimental_source_identified',
            source_ok,
            f"{metadata.get('source_type')} with public identifier",
            'Use field_test, wind_tunnel, or literature_digitized source_type with URL or DOI.',
        ),
        gate_row(
            'case_alignment_complete',
            alignment_ok,
            'all required case_alignment fields are true',
            'Set all required fuel, release/cloud mass, burn/ignition, measurement, and boundary-condition alignment fields to true with evidence.',
        ),
        gate_row(
            'radiation_metrics_available',
            inputs.get('radiation_metrics_available') is True,
            f'{radiation_count} radiation metric row(s) accepted',
            'Provide radiation_metrics.csv with positive values, tolerances, and source basis.',
        ),
        gate_row(
            'overpressure_metrics_available',
            inputs.get('overpressure_metrics_available') is True,
            f'{overpressure_count} overpressure metric row(s) accepted',
            'Provide overpressure_metrics.csv with positive values, tolerances, and source basis.',
        ),
        gate_row(
            'radiation_and_overpressure_families_present',
            radiation_count > 0 and overpressure_count > 0,
            f'radiation={radiation_count}, overpressure={overpressure_count}',
            'Both radiation and overpressure calibration families are required.',
        ),
        gate_row(
            'package_ready_for_dataset_builder',
            ready,
            'dataset builder may consume the ingested calibration package',
            'The package is not builder-ready until every ingestion and quality gate passes.',
        ),
        gate_row(
            'package_does_not_claim_final_calibration',
            True,
            'package remains an intake gate; final blocker clearance requires calibrated consequence report',
            '',
        ),
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    dataset_root = Path(args.dataset_root)
    ingestion_report_path = Path(args.ingestion_report)
    ingestion_selftest_path = Path(args.ingestion_selftest_report)
    public_source_triage_path = Path(args.public_source_triage_report)
    literature_metric_path = Path(args.literature_metric_preflight_report)
    template_files = write_package_templates(dataset_root)
    ingestion = load_json(ingestion_report_path)
    ingestion_selftest = load_json(ingestion_selftest_path)
    public_source_triage = load_json(public_source_triage_path)
    literature_metric = load_json(literature_metric_path)
    blocking_gaps: list[str] = []
    if ingestion.get('status') != INGESTION_READY_STATUS:
        blocking_gaps.append('fire_calibration_dataset_ingestion_not_passed')
        if isinstance(ingestion.get('blocking_gaps'), list):
            blocking_gaps.extend(str(item) for item in ingestion['blocking_gaps'])
    selftest_summary = (
        ingestion_selftest.get('summary', {})
        if isinstance(ingestion_selftest.get('summary'), dict)
        else {}
    )
    if ingestion_selftest.get('status') != 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION-SELFTEST':
        blocking_gaps.append('fire_calibration_dataset_ingestion_selftest_not_passed')

    required = ingestion.get('required_dataset_files', {})
    required_files = {
        'calibration_metadata_json': str(dataset_root / 'calibration_metadata.json'),
        'radiation_metrics_csv': str(dataset_root / 'radiation_metrics.csv'),
        'overpressure_metrics_csv': str(dataset_root / 'overpressure_metrics.csv'),
    }
    if isinstance(required, dict):
        required_files.update({str(k): str(v) for k, v in required.items()})

    ready = not blocking_gaps
    literature_summary = (
        literature_metric.get('summary', {})
        if isinstance(literature_metric.get('summary'), dict)
        else {}
    )
    quality_gate_matrix = build_quality_gate_matrix(
        ingestion,
        ingestion_selftest,
        public_source_triage,
        literature_metric,
        ready,
    )
    evidence_files = [evidence_entry('fire_calibration_dataset_ingestion_report', ingestion_report_path)]
    evidence_files.append(evidence_entry('fire_calibration_dataset_ingestion_selftest_report', ingestion_selftest_path))
    evidence_files.append(evidence_entry('fire_calibration_public_source_triage_report', public_source_triage_path))
    evidence_files.append(evidence_entry('fire_calibration_literature_metric_preflight_report', literature_metric_path))
    evidence_files.extend(evidence_entry(path.stem, path) for path in template_files)
    if ready:
        for label, raw_path in required_files.items():
            evidence_files.append(evidence_entry(label, Path(raw_path)))

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 Fire Calibration Package',
        'dataset_root': str(dataset_root),
        'ingestion_report': str(ingestion_report_path),
        'ingestion_selftest_report': str(ingestion_selftest_path),
        'public_source_triage_report': str(public_source_triage_path),
        'literature_metric_preflight_report': str(literature_metric_path),
        'ingestion_status': ingestion.get('status'),
        'ingestion_schema_version': ingestion.get('schema_version'),
        'ingestion_content_quality_gate_level': (
            ingestion.get('schema_requirements', {}).get('content_quality_gate_level')
            if isinstance(ingestion.get('schema_requirements'), dict)
            else None
        ),
        'ingestion_selftest_status': ingestion_selftest.get('status'),
        'public_source_triage_status': public_source_triage.get('status'),
        'literature_metric_preflight_status': literature_metric.get('status'),
        'package_ready_for_dataset_builder': ready,
        'clears_fire_consequence_blocker': False,
        'required_dataset_files': required_files,
        'template_files': [str(path) for path in template_files],
        'blocking_gaps': blocking_gaps,
        'quality_gate_matrix': quality_gate_matrix,
        'current_inputs': {
            'metadata_available': ingestion.get('current_inputs', {}).get('metadata_available')
            if isinstance(ingestion.get('current_inputs'), dict)
            else None,
            'radiation_metrics_available': ingestion.get('current_inputs', {}).get('radiation_metrics_available')
            if isinstance(ingestion.get('current_inputs'), dict)
            else None,
            'overpressure_metrics_available': ingestion.get('current_inputs', {}).get('overpressure_metrics_available')
            if isinstance(ingestion.get('current_inputs'), dict)
            else None,
            'ingestion_schema_version': ingestion.get('schema_version'),
            'ingestion_content_quality_gate_level': (
                ingestion.get('schema_requirements', {}).get('content_quality_gate_level')
                if isinstance(ingestion.get('schema_requirements'), dict)
                else None
            ),
            'ingestion_selftest_status': ingestion_selftest.get('status'),
            'ingestion_selftest_positive_passed_count': selftest_summary.get('positive_passed_count'),
            'ingestion_selftest_negative_refused_count': selftest_summary.get('negative_refused_count'),
            'ingestion_selftest_placeholder_negative_refused': selftest_summary.get('placeholder_negative_refused'),
            'ingestion_selftest_duplicate_metric_negative_refused': selftest_summary.get(
                'duplicate_metric_negative_refused'
            ),
            'public_source_triage_available': (
                public_source_triage.get('status') == 'PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE'
            ),
            'public_source_missing_artifact_count': (
                public_source_triage.get('summary', {}).get('missing_artifact_count')
                if isinstance(public_source_triage.get('summary'), dict)
                else None
            ),
            'literature_metric_anchor_available': (
                literature_summary.get('radiation_metric_anchor_available') is True
                and literature_summary.get('overpressure_metric_anchor_available') is True
            ),
            'literature_metric_missing_artifact_count': literature_summary.get('missing_artifact_count'),
        },
        'evidence_files': evidence_files,
        'limitations': [
            'This package prepares external fire/blast calibration data for ingestion and does not clear the fire-consequence blocker by itself.',
            'The default package is NOT_READY until real metadata, radiation, and overpressure calibration files pass ingestion.',
            'Production credit requires the official fire consequence report to pass with the generated calibration dataset JSON.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, f"invalid status {data.get('status')}")
    require(data.get('clears_fire_consequence_blocker') is False, 'package report cannot clear fire blocker')
    require(
        data.get('public_source_triage_status') == 'PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE',
        'public-source triage did not PASS',
    )
    require(
        data.get('literature_metric_preflight_status')
        == 'PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT',
        'literature metric preflight did not PASS',
    )
    require(int(data.get('ingestion_schema_version', 0)) >= 2, 'ingestion schema too old')
    require(
        data.get('ingestion_content_quality_gate_level') == 'strict-v1-placeholder-free-and-non-synthetic',
        'ingestion content quality gate mismatch',
    )
    require(
        data.get('ingestion_selftest_status') == 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION-SELFTEST',
        'ingestion selftest did not PASS',
    )
    require(isinstance(data.get('required_dataset_files'), dict), 'required_dataset_files missing')
    require(isinstance(data.get('template_files'), list) and data['template_files'], 'template_files missing')
    inputs = data.get('current_inputs')
    require(isinstance(inputs, dict), 'current_inputs missing')
    require(inputs.get('public_source_triage_available') is True, 'public-source triage unavailable')
    require(inputs.get('literature_metric_anchor_available') is True, 'literature metric anchors unavailable')
    require(int(inputs.get('ingestion_selftest_positive_passed_count', 0)) == 2, 'ingestion selftest positive mismatch')
    require(int(inputs.get('ingestion_selftest_negative_refused_count', 0)) == 1, 'ingestion selftest negative mismatch')
    require(inputs.get('ingestion_selftest_placeholder_negative_refused') is True, 'ingestion selftest placeholder not refused')
    require(
        inputs.get('ingestion_selftest_duplicate_metric_negative_refused') is True,
        'ingestion selftest duplicate metric not refused',
    )
    require(
        int(inputs.get('literature_metric_missing_artifact_count', 0)) >= 1,
        'literature metric missing-artifact count too small',
    )
    gaps = data.get('blocking_gaps')
    require(isinstance(gaps, list), 'blocking_gaps missing')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    failed_matrix = [item for item in matrix if isinstance(item, dict) and item.get('status') != 'PASS']
    if data.get('status') == STATUS_READY:
        require(data.get('package_ready_for_dataset_builder') is True, 'READY package is not builder-ready')
        require(not gaps, 'READY package still has blocking gaps')
        require(not failed_matrix, 'READY package has failed quality gates')
    else:
        require(data.get('package_ready_for_dataset_builder') is False, 'NOT_READY package cannot be builder-ready')
        require(gaps, 'NOT_READY package must list blocking gaps')
        require(failed_matrix, 'NOT_READY package must list failed quality gates')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence hash mismatch: {path}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Fire Calibration Package',
        '',
        f"Status: `{report['status']}`",
        f"Dataset root: `{report['dataset_root']}`",
        f"Ingestion status: `{report['ingestion_status']}`",
        f"Package ready for dataset builder: `{report['package_ready_for_dataset_builder']}`",
        f"Clears fire-consequence blocker: `{report['clears_fire_consequence_blocker']}`",
        '',
        '## Current Inputs',
        '',
    ]
    for key, value in report['current_inputs'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Required Dataset Files', '']
    for key, value in report['required_dataset_files'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Blocking Gaps', '']
    for gap in report['blocking_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Quality Gate Matrix', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        gap = item['gap'] or item['evidence']
        lines.append(f"| `{item['name']}` | `{item['status']}` | {gap} |")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument('--ingestion-report', default=str(DEFAULT_INGESTION_JSON))
    parser.add_argument('--ingestion-selftest-report', default=str(DEFAULT_INGESTION_SELFTEST_REPORT))
    parser.add_argument('--public-source-triage-report', default=str(DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT))
    parser.add_argument('--literature-metric-preflight-report', default=str(DEFAULT_LITERATURE_METRIC_PREFLIGHT_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_fire_calibration_package VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"builder_ready={report['package_ready_for_dataset_builder']}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_fire_calibration_package PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except FireCalibrationPackageError as exc:
        print(f'engineering_h2_fire_calibration_package FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
