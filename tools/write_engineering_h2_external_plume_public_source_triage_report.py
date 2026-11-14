#!/usr/bin/env python3
"""Write/verify public-source triage for the HySafe SBEPV5 D27 H2 plume benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS = 'PASS-H2-EXTERNAL-PLUME-PUBLIC-SOURCE-TRIAGE'

DEFAULT_OUTPUT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / 'external_plume_public_source_triage_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / 'external_plume_public_source_triage_report.md'


class SourceTriageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceTriageError(message)


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
        raise SourceTriageError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise SourceTriageError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    sources = [
        {
            'id': 'kitopen_230068969',
            'kind': 'repository_metadata',
            'title': 'Results of the HySafe CFD validation benchmark SBEPV5',
            'url': 'https://publikationen.bibliothek.kit.edu/230068969',
            'publisher_or_host': 'KITopen',
            'production_use': 'preferred bibliographic anchor for public source identity',
        },
        {
            'id': 'researchgate_311396790',
            'kind': 'paper_full_text_page',
            'title': 'Results of the HySafe CFD Validation Benchmark SBEPV5',
            'url': 'https://www.researchgate.net/publication/311396790_Results_of_the_HySafe_CFD_Validation_Benchmark_SBEPV5',
            'publisher_or_host': 'ResearchGate mirror of ICHS 2007 paper',
            'production_use': 'publicly readable paper text and figure captions for geometry/release/measurement facts',
        },
        {
            'id': 'h2knowledgecentre_conference289',
            'kind': 'conference_record',
            'title': 'Results of the HySafe CFD Validation Benchmark SBEPV5',
            'url': 'https://www.h2knowledgecentre.com/content/conference289',
            'publisher_or_host': 'Hydrogen Knowledge Centre',
            'production_use': 'secondary bibliographic record and abstract',
        },
        {
            'id': 'slideserve_8677333',
            'kind': 'presentation_transcript_secondary',
            'title': 'Results of the HySafe CFD Validation Benchmark SBEPV5',
            'url': 'https://www.slideserve.com/nilson/results-of-the-hysafe-cfd-validation-benchmark-sbepv5-powerpoint-ppt-presentation',
            'publisher_or_host': 'SlideServe transcript',
            'production_use': 'secondary cross-check for sensor layout, release period, nozzle, exit velocity, and flow rate',
        },
    ]
    extracted_facts = [
        {
            'fact_id': 'vessel_dimensions',
            'value': {'x_width_m': 1.20, 'y_depth_m': 0.20, 'z_height_m': 0.90},
            'source_ids': ['researchgate_311396790', 'slideserve_8677333'],
            'production_status': 'usable_for_case_scaffold',
        },
        {
            'fact_id': 'test_case',
            'value': {'case_id': 'D27', 'selection_basis': 'low-momentum SBEPV5 validation test'},
            'source_ids': ['researchgate_311396790'],
            'production_status': 'usable_for_case_scaffold',
        },
        {
            'fact_id': 'release_conditions',
            'value': {
                'release_period_s': 60.0,
                'nozzle_diameter_m': 0.012,
                'exit_velocity_m_s': 10.17,
                'flow_rate_normal_l_s': 1.15,
                'jet_exit_location_m': {'x': 0.03, 'y': 0.10, 'z': 0.145},
                'gas': 'pure_H2',
            },
            'source_ids': ['researchgate_311396790', 'slideserve_8677333'],
            'production_status': 'usable_for_case_scaffold',
        },
        {
            'fact_id': 'compartment_and_baffle_summary',
            'value': {
                'compartment_count': 12,
                'baffle_count': 4,
                'baffle_plate_dimensions_m': {'y_depth': 0.20, 'z_height': 0.30},
            },
            'source_ids': ['researchgate_311396790'],
            'production_status': 'usable_for_case_scaffold_but_exact_positions_need_digitization',
        },
        {
            'fact_id': 'sensor_summary',
            'value': {
                'sensor_count': 12,
                'sensor_type': 'Oldham OLCT20D thermal-conductivity H2 concentration sensors',
                'sensor_accuracy_volume_percent_h2': 1.0,
                'reliable_sensor_ids': [1, 2, 5, 7, 8, 9, 10, 12],
                'unreliable_sensor_ids': [3, 4, 6, 11],
            },
            'source_ids': ['researchgate_311396790', 'slideserve_8677333'],
            'production_status': 'usable_for_reliable_sensor_filter_but_exact_coordinates_need_digitization',
        },
        {
            'fact_id': 'experimental_dataset_summary',
            'value': {
                'duration_s': 120.0,
                'format_reported_by_paper': 'MS Excel',
                'quantity': 'volumetric H2 concentration at 12 monitor locations',
            },
            'source_ids': ['researchgate_311396790'],
            'production_status': 'not_ingested_original_excel_or_digitized_csv_required',
        },
    ]
    missing_artifacts = [
        {
            'artifact': 'sensor_coordinates.csv',
            'why_missing': 'public figure/transcript identifies layout and reliable sensors but no machine-readable exact coordinates are attached',
            'required_action': 'digitize Figure 4/source figure or obtain original tabular sensor coordinates',
        },
        {
            'artifact': 'baffle_geometry.csv',
            'why_missing': 'public text gives count and plate dimensions but exact baffle bounds still require figure digitization/original geometry',
            'required_action': 'digitize Figure 2/source geometry or obtain original CAD/table',
        },
        {
            'artifact': 'experimental_timeseries.csv',
            'why_missing': 'paper reports MS Excel dataset and plots but no local accepted 12-sensor CSV/Excel file is ingested',
            'required_action': 'obtain original Excel data or digitize published curves with source and uncertainty metadata',
        },
        {
            'artifact': 'dataset_metadata.json',
            'why_missing': 'dataset source hashes and digitization provenance cannot be completed until source data files are local',
            'required_action': 'record URL/DOI, source file hashes, digitization method, uncertainty, and case-alignment booleans',
        },
    ]
    artifact_resolution_matrix = [
        {
            'artifact': 'dataset_metadata.json',
            'public_sources_identified': True,
            'source_identity_sufficient': True,
            'numeric_data_available_in_public_text': False,
            'local_controlled_file_present': False,
            'can_clear_ingestion_gate': False,
            'usable_source_ids': ['kitopen_230068969', 'researchgate_311396790', 'h2knowledgecentre_conference289'],
            'required_next_step': 'download or receive the source document/data package, hash it locally, and record provenance plus case-alignment booleans',
        },
        {
            'artifact': 'sensor_coordinates.csv',
            'public_sources_identified': True,
            'source_identity_sufficient': True,
            'numeric_data_available_in_public_text': False,
            'local_controlled_file_present': False,
            'can_clear_ingestion_gate': False,
            'usable_source_ids': ['researchgate_311396790', 'slideserve_8677333'],
            'required_next_step': 'digitize the sensor-position figure or obtain the original Gas01..Gas12 coordinate table with uncertainty records',
        },
        {
            'artifact': 'baffle_geometry.csv',
            'public_sources_identified': True,
            'source_identity_sufficient': True,
            'numeric_data_available_in_public_text': False,
            'local_controlled_file_present': False,
            'can_clear_ingestion_gate': False,
            'usable_source_ids': ['researchgate_311396790'],
            'required_next_step': 'digitize the geometry figure or obtain original baffle bounds for all four baffles',
        },
        {
            'artifact': 'experimental_timeseries.csv',
            'public_sources_identified': True,
            'source_identity_sufficient': True,
            'numeric_data_available_in_public_text': False,
            'local_controlled_file_present': False,
            'can_clear_ingestion_gate': False,
            'usable_source_ids': ['researchgate_311396790'],
            'required_next_step': 'obtain the original Excel file or digitize all reliable-sensor curves through 120 s with uncertainty metadata',
        },
    ]
    public_fact_to_case_input_map = [
        {
            'input_field': 'geometry.domain_dimensions_m',
            'status': 'PUBLIC_FACT_AVAILABLE',
            'source_fact_ids': ['vessel_dimensions'],
            'blocked_reason': '',
        },
        {
            'input_field': 'release.nozzle_diameter_m',
            'status': 'PUBLIC_FACT_AVAILABLE',
            'source_fact_ids': ['release_conditions'],
            'blocked_reason': '',
        },
        {
            'input_field': 'release.exit_velocity_m_s',
            'status': 'PUBLIC_FACT_AVAILABLE',
            'source_fact_ids': ['release_conditions'],
            'blocked_reason': '',
        },
        {
            'input_field': 'release.duration_s',
            'status': 'PUBLIC_FACT_AVAILABLE',
            'source_fact_ids': ['release_conditions'],
            'blocked_reason': '',
        },
        {
            'input_field': 'sensors.coordinates',
            'status': 'NEEDS_DIGITIZATION_OR_ORIGINAL_TABLE',
            'source_fact_ids': ['sensor_summary'],
            'blocked_reason': 'public material identifies sensors but not a controlled machine-readable coordinate table',
        },
        {
            'input_field': 'baffles.bounds',
            'status': 'NEEDS_DIGITIZATION_OR_ORIGINAL_TABLE',
            'source_fact_ids': ['compartment_and_baffle_summary'],
            'blocked_reason': 'public material gives baffle count and dimensions but not exact bounds for every baffle',
        },
        {
            'input_field': 'reference.experimental_timeseries',
            'status': 'NEEDS_ORIGINAL_EXCEL_OR_DIGITIZED_CURVES',
            'source_fact_ids': ['experimental_dataset_summary'],
            'blocked_reason': 'the paper states that an Excel dataset exists, but no accepted local file is present',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Plume Public Source Triage',
        'benchmark_id': 'hysafe_sbepv5_d27',
        'clears_reference_data_blocker': False,
        'sources': sources,
        'extracted_facts': extracted_facts,
        'artifact_resolution_matrix': artifact_resolution_matrix,
        'public_fact_to_case_input_map': public_fact_to_case_input_map,
        'missing_artifacts': missing_artifacts,
        'summary': {
            'public_source_registry_available': True,
            'artifact_resolution_matrix_row_count': len(artifact_resolution_matrix),
            'artifact_resolution_clearable_count': sum(
                1 for item in artifact_resolution_matrix if item['can_clear_ingestion_gate']
            ),
            'public_fact_to_case_input_map_row_count': len(public_fact_to_case_input_map),
            'case_input_public_fact_available_count': sum(
                1 for item in public_fact_to_case_input_map if item['status'] == 'PUBLIC_FACT_AVAILABLE'
            ),
            'case_input_needs_digitization_count': sum(
                1 for item in public_fact_to_case_input_map if item['status'] != 'PUBLIC_FACT_AVAILABLE'
            ),
            'public_geometry_release_summary_available': True,
            'public_sensor_reliability_summary_available': True,
            'public_timeseries_existence_documented': True,
            'exact_sensor_coordinate_table_available': False,
            'exact_baffle_geometry_table_available': False,
            'original_excel_timeseries_available_locally': False,
            'ready_for_dataset_ingestion': False,
            'clears_external_plume_reference_blocker': False,
            'missing_artifact_count': len(missing_artifacts),
        },
        'quality_gate_matrix': [
            {'name': 'public_source_registry_available', 'status': 'PASS', 'gap': '', 'evidence': [item['url'] for item in sources]},
            {'name': 'geometry_release_facts_extracted', 'status': 'PASS', 'gap': '', 'evidence': ['vessel_dimensions', 'release_conditions']},
            {'name': 'sensor_reliability_facts_extracted', 'status': 'PASS', 'gap': '', 'evidence': ['sensor_summary']},
            {
                'name': 'artifact_resolution_matrix_retains_blockers',
                'status': 'PASS',
                'gap': '',
                'evidence': ['all required ingestion artifacts have explicit non-clearable resolution rows'],
            },
            {
                'name': 'case_input_map_separates_public_facts_from_digitization',
                'status': 'PASS',
                'gap': '',
                'evidence': ['public case-scaffold facts are separated from unavailable sensor/baffle/timeseries data'],
            },
            {
                'name': 'exact_sensor_coordinates_available',
                'status': 'MISSING',
                'gap': 'Exact Gas01..Gas12 coordinates are not present as local source-controlled data.',
                'evidence': [],
            },
            {
                'name': 'exact_baffle_geometry_available',
                'status': 'MISSING',
                'gap': 'Exact baffle bounds are not present as local source-controlled data.',
                'evidence': [],
            },
            {
                'name': 'experimental_timeseries_available',
                'status': 'MISSING',
                'gap': 'Original Excel or accepted digitized 12-sensor concentration time series is not local.',
                'evidence': [],
            },
        ],
        'limitations': [
            'This triage report records public-source facts and data-acquisition gaps; it does not ingest experimental data.',
            'Production reference agreement still requires local exact coordinates, baffle geometry, and concentration time series.',
        ],
    }


def validate_report_object(data: dict[str, Any]) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'unexpected benchmark id')
    require(data.get('clears_reference_data_blocker') is False, 'triage cannot clear reference-data blocker')
    sources = data.get('sources')
    require(isinstance(sources, list) and len(sources) >= 3, 'source registry incomplete')
    source_ids = {str(item.get('id')) for item in sources if isinstance(item, dict)}
    require('kitopen_230068969' in source_ids, 'KITopen source missing')
    require('researchgate_311396790' in source_ids, 'ResearchGate source missing')
    facts = data.get('extracted_facts')
    require(isinstance(facts, list) and len(facts) >= 5, 'extracted facts incomplete')
    fact_ids = {str(item.get('fact_id')) for item in facts if isinstance(item, dict)}
    for required in ('vessel_dimensions', 'release_conditions', 'sensor_summary', 'experimental_dataset_summary'):
        require(required in fact_ids, f'missing extracted fact: {required}')
    matrix = data.get('artifact_resolution_matrix')
    require(isinstance(matrix, list) and len(matrix) >= 4, 'artifact resolution matrix incomplete')
    artifacts = {str(item.get('artifact')) for item in matrix if isinstance(item, dict)}
    for required in ('dataset_metadata.json', 'sensor_coordinates.csv', 'baffle_geometry.csv', 'experimental_timeseries.csv'):
        require(required in artifacts, f'missing artifact resolution row: {required}')
    for item in matrix:
        require(isinstance(item, dict), 'artifact resolution row is not an object')
        require(item.get('public_sources_identified') is True, 'artifact row missing public source identity')
        require(item.get('local_controlled_file_present') is False, 'triage cannot claim local controlled files')
        require(item.get('can_clear_ingestion_gate') is False, 'triage cannot clear ingestion gate')
        require(bool(item.get('required_next_step')), 'artifact row missing next step')
    case_map = data.get('public_fact_to_case_input_map')
    require(isinstance(case_map, list) and len(case_map) >= 6, 'case input map incomplete')
    statuses = {str(item.get('status')) for item in case_map if isinstance(item, dict)}
    require('PUBLIC_FACT_AVAILABLE' in statuses, 'case input map lacks public fact rows')
    require(any(status.startswith('NEEDS_') for status in statuses), 'case input map lacks blocked digitization rows')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('public_source_registry_available') is True, 'source registry not available')
    require(int(summary.get('artifact_resolution_matrix_row_count', 0)) >= 4, 'artifact resolution row count too small')
    require(int(summary.get('artifact_resolution_clearable_count', -1)) == 0, 'triage cannot mark artifacts clearable')
    require(int(summary.get('public_fact_to_case_input_map_row_count', 0)) >= 6, 'case input map row count too small')
    require(int(summary.get('case_input_public_fact_available_count', 0)) >= 3, 'public case fact count too small')
    require(int(summary.get('case_input_needs_digitization_count', 0)) >= 3, 'digitization-needed count too small')
    require(summary.get('public_geometry_release_summary_available') is True, 'geometry/release summary missing')
    require(summary.get('ready_for_dataset_ingestion') is False, 'triage cannot be dataset-ingestion ready')
    require(summary.get('clears_external_plume_reference_blocker') is False, 'triage cannot clear blocker')
    require(int(summary.get('missing_artifact_count', 0)) >= 3, 'missing artifact count too small')
    quality = data.get('quality_gate_matrix')
    require(isinstance(quality, list) and quality, 'quality gate matrix missing')
    quality_names = {str(item.get('name')) for item in quality if isinstance(item, dict)}
    require('artifact_resolution_matrix_retains_blockers' in quality_names, 'artifact resolution quality gate missing')
    require('case_input_map_separates_public_facts_from_digitization' in quality_names, 'case input map quality gate missing')
    missing = [item for item in quality if isinstance(item, dict) and item.get('status') == 'MISSING']
    require(missing, 'triage must retain missing gates for exact external data')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 External Plume Public Source Triage',
        '',
        f"Status: `{report['status']}`",
        f"Benchmark: `{report['benchmark_id']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        '',
        '## Sources',
        '',
    ]
    for item in report['sources']:
        lines.append(f"- `{item['id']}`: {item['url']} ({item['production_use']})")
    lines += ['', '## Extracted Facts', '']
    for item in report['extracted_facts']:
        lines.append(f"- `{item['fact_id']}`: `{item['value']}` status `{item['production_status']}`")
    lines += ['', '## Artifact Resolution Matrix', '']
    for item in report['artifact_resolution_matrix']:
        lines.append(
            f"- `{item['artifact']}`: clearable `{item['can_clear_ingestion_gate']}`, "
            f"local file `{item['local_controlled_file_present']}`; {item['required_next_step']}"
        )
    lines += ['', '## Public Fact To Case Input Map', '']
    for item in report['public_fact_to_case_input_map']:
        lines.append(f"- `{item['input_field']}`: `{item['status']}`")
    lines += ['', '## Missing Artifacts', '']
    for item in report['missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['gap'] or 'none'} |")
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
            validate_report_object(report)
            print(
                'engineering_h2_external_plume_public_source_triage VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"missing_artifacts={report['summary']['missing_artifact_count']}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_external_plume_public_source_triage PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"missing_artifacts={report['summary']['missing_artifact_count']}"
        )
        return 0
    except SourceTriageError as exc:
        print(f'engineering_h2_external_plume_public_source_triage FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
