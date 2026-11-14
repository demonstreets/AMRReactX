#!/usr/bin/env python3
"""Write/verify readiness evidence for external H2 plume benchmark validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 6
STATUS_READY = 'PASS-EXTERNAL-PLUME-BENCHMARK'
STATUS_NOT_READY = 'NOT_READY-EXTERNAL-PLUME-BENCHMARK'

DEFAULT_REFERENCE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/'
    'h2_reference_agreement_report.json'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_readiness_20260723/'
    'external_plume_benchmark_readiness_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_readiness_20260723/'
    'external_plume_benchmark_readiness_report.md'
)
DEFAULT_INTAKE_CHECKLIST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_readiness_20260723/'
    'external_plume_benchmark_intake_checklist.csv'
)
DEFAULT_PLUME_OBSERVATION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_plume_observation_20260723/'
    'h2_plume_observation_report.json'
)
DEFAULT_BENCHMARK_SPEC_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_spec_20260723/'
    'hysafe_sbepv5_d27_benchmark_spec_report.json'
)
DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/'
    'external_plume_public_source_triage_report.json'
)
DEFAULT_DATASET_INGESTION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
    'sbepv5_d27_dataset_ingestion_report.json'
)
DEFAULT_DIGITIZATION_PREFLIGHT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724/'
    'sbepv5_d27_digitization_preflight_report.json'
)
DEFAULT_LITERATURE_METRIC_PREFLIGHT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_literature_metric_preflight_20260724/'
    'sbepv5_d27_literature_metric_preflight_report.json'
)
DEFAULT_CASE_PACKAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/'
    'sbepv5_d27_case_package_report.json'
)
DEFAULT_CASE_PACKAGE_PREFLIGHT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_preflight_20260723/'
    'sbepv5_d27_case_package_preflight_report.json'
)
DEFAULT_EXTERNAL_DATASET_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/'
    'sbepv5_d27_external_dataset_report.json'
)
DEFAULT_D27_PROGRAM_SCOUT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_program_scout_run_20260727/'
    'sbepv5_d27_scout_run_report.json'
)

PUBLIC_BENCHMARK_CANDIDATES = [
    {
        'id': 'hysafe_sbepv5_d27',
        'title': 'HySafe CFD validation benchmark SBEPV5, GexCon D27',
        'source_type': 'literature_digitized',
        'url': 'https://publikationen.bibliothek.kit.edu/230068969',
        'doi_or_secondary': 'ICHS 2007 proceedings; public repository metadata',
        'available_evidence': [
            '1.20 m x 0.20 m x 0.90 m baffled compartment geometry',
            'pure H2 horizontal release for 60 s through a 12 mm nozzle',
            '1.15 normal L/s release rate and 10.17 m/s exit velocity',
            '12 rear-wall H2 concentration sensors; reliable sensor subset identified',
            'published arrival-time and concentration-history comparison plots',
        ],
        'required_program_outputs': [
            'case-matched baffled-box geometry and vent opening',
            'transient point-probe/sensor concentration sampling at the 12 monitor locations',
            'digitized experimental concentration traces or accepted tabular data',
            'arrival-time and concentration tolerance checks for reliable sensors',
        ],
    },
    {
        'id': 'large_volume_lh2_open_space_2024',
        'title': 'Large-volume liquid hydrogen release in open space',
        'source_type': 'field_test',
        'url': 'https://www.mdpi.com/2076-3417/14/9/3645',
        'doi_or_secondary': 'Applied Sciences 14(9), 3645',
        'available_evidence': [
            'open-space LH2 release experiment with concentration sensors',
            'reported 180 kg release over 38 s through a 0.25 m2 vent area',
            'reported farthest downwind flammable-cloud distance and height',
        ],
        'required_program_outputs': [
            'cryogenic liquid-hydrogen source model or justified gas-equivalent surrogate',
            'flammable-cloud maximum downwind distance and vertical extent over time',
            'case-matched wind and terrain/substrate conditions',
            'radiation/consequence coupling kept separate from plume-shape validation',
        ],
    },
]


class ReadinessError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReadinessError(message)


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
        raise ReadinessError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReadinessError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return load_json(path)


def write_intake_checklist(path: Path) -> Path:
    rows = [
        ['item', 'required_evidence', 'production_rule'],
        ['benchmark_spec', 'public benchmark specification report', 'PASS-EXTERNAL-PLUME-BENCHMARK-SPEC'],
        ['case_package', 'case-matched input scaffold and geometry references', 'PASS-SBEPV5-D27-CASE-PACKAGE-SCAFFOLD'],
        ['case_preflight', 'reference source resolution and template consistency', 'PASS-SBEPV5-D27-CASE-PACKAGE-PREFLIGHT'],
        ['dataset_metadata.json', 'source, DOI/URL, digitization and source hash metadata', 'dataset ingestion PASS'],
        ['sensor_coordinates.csv', '12 Gas sensor coordinates, reliability, source basis and uncertainty', 'all expected sensors in vessel and uncertainty <= 0.02 m'],
        ['baffle_geometry.csv', 'four baffles with source basis and uncertainty', 'ids 1..4, positive extents, inside vessel'],
        ['literature_metric_preflight', 'Gas09/Gas10 arrival-time and sensor-priority metric anchors', 'PASS-SBEPV5-D27-LITERATURE-METRIC-PREFLIGHT'],
        ['experimental_timeseries.csv', 'Gas01..Gas12 concentration history', 'monotone time, >=25 rows, start <=1 s, end >=120 s'],
        ['plume_observation', 'program sensor sampling, downwind extent and vertical extent', 'PASS-H2-PLUME-OBSERVATION with required metrics'],
        ['external_dataset_json', 'external plume agreement dataset generated by builder', 'PASS-SBEPV5-D27-EXTERNAL-PLUME-DATASET'],
        ['reference_agreement', 'official reference agreement with external plume dataset', 'external_plume_shape_dataset_agreement true'],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(','.join(f'"{cell}"' for cell in row) for row in rows) + '\n', encoding='utf-8')
    return path


def gate_row(name: str, passed: bool, evidence: str, gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else '',
        'gap': '' if passed else gap,
    }


def build_quality_gate_matrix(current_outputs: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        gate_row(
            'public_source_triage_ready',
            current_outputs['public_source_triage_available'] is True,
            'public-source triage report fixes source registry and acquisition gaps',
            'Generate the public-source triage report for the selected external plume benchmark.',
        ),
        gate_row(
            'digitization_preflight_ready',
            current_outputs['digitization_preflight_available'] is True,
            'SBEPV5 D27 digitization templates and source triage are available',
            'Generate the SBEPV5 D27 digitization preflight report.',
        ),
        gate_row(
            'literature_metric_preflight_ready',
            current_outputs['literature_metric_preflight_available'] is True,
            'SBEPV5 D27 literature-level arrival and priority sensor metric anchors are available',
            'Generate the SBEPV5 D27 literature metric preflight report.',
        ),
        gate_row(
            'benchmark_spec_ready',
            current_outputs['case_spec_report_available'] is True,
            'SBEPV5 D27 benchmark spec report passed',
            'Generate and verify the SBEPV5 D27 benchmark specification report.',
        ),
        gate_row(
            'case_package_scaffold_ready',
            current_outputs['case_package_report_available'] is True,
            'case scaffold package report passed',
            'Generate the case-matched PeleLMeX input/geometry scaffold.',
        ),
        gate_row(
            'case_package_preflight_ready',
            current_outputs['case_package_preflight_report_available'] is True
            and current_outputs['case_package_reference_source_resolution_ready'] is True,
            'case package preflight passed and reference sources resolve',
            'Run and pass case package preflight including reference source resolution.',
        ),
        gate_row(
            'case_package_runnable',
            current_outputs['case_package_runnable'] is True,
            'case package is runnable',
            'Provide all source data and generated geometry/input artifacts required to run the SBEPV5 case.',
        ),
        gate_row(
            'd27_program_scout_runnable',
            current_outputs['sbepv5_d27_program_scout_run_available'] is True,
            'D27-style program-side CUDA scout ran with baffles, sensors, plume extents and copied evidence',
            'Run and verify the SBEPV5 D27 program-side scout report.',
        ),
        gate_row(
            'dataset_metadata_available',
            current_outputs['dataset_metadata_available'] is True,
            'dataset metadata ingested',
            'Provide dataset_metadata.json with benchmark id, source URL/DOI, digitization metadata, and source hash.',
        ),
        gate_row(
            'exact_sensor_coordinates_available',
            current_outputs['exact_sensor_coordinates_available'] is True,
            'all exact sensor coordinates ingested',
            'Provide sensor_coordinates.csv for Gas01..Gas12 with reliability/source basis/uncertainty.',
        ),
        gate_row(
            'exact_baffle_geometry_available',
            current_outputs['exact_baffle_geometry_available'] is True,
            'baffle geometry ingested',
            'Provide baffle_geometry.csv for baffles 1..4 with source basis and uncertainty.',
        ),
        gate_row(
            'digitized_experimental_timeseries_available',
            current_outputs['digitized_experimental_timeseries_available'] is True,
            'experimental concentration timeseries ingested',
            'Provide experimental_timeseries.csv covering Gas01..Gas12 through at least 120 s.',
        ),
        gate_row(
            'program_sensor_sampling_available',
            current_outputs['sensor_timeseries_sampling_available'] is True,
            'program plume observation includes sensor time series',
            'Program output must include transient point-probe concentration sampling.',
        ),
        gate_row(
            'program_extent_metrics_available',
            current_outputs['maximum_downwind_extent_available'] is True
            and current_outputs['maximum_vertical_extent_available'] is True,
            'program plume observation includes downwind and vertical extents',
            'Program output must expose flammable cloud downwind and vertical extents.',
        ),
        gate_row(
            'external_dataset_json_written',
            current_outputs['external_plume_dataset_json_written'] is True,
            'external plume dataset JSON was generated',
            'External dataset builder must write the shape-agreement dataset JSON.',
        ),
        gate_row(
            'reference_agreement_uses_external_shape_dataset',
            current_outputs['external_plume_shape_dataset_agreement'] is True,
            'official reference agreement includes external plume shape dataset',
            'Regenerate h2_reference_agreement_report with the generated external plume dataset JSON and passing checks.',
        ),
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    reference_path = Path(args.reference_report)
    reference = load_json(reference_path)
    observation_path = Path(args.plume_observation_report)
    observation = optional_json(observation_path)
    benchmark_spec_path = Path(args.benchmark_spec_report)
    benchmark_spec = optional_json(benchmark_spec_path)
    public_source_triage_path = Path(args.public_source_triage_report)
    public_source_triage = optional_json(public_source_triage_path)
    dataset_ingestion_path = Path(args.dataset_ingestion_report)
    dataset_ingestion = optional_json(dataset_ingestion_path)
    digitization_preflight_path = Path(args.digitization_preflight_report)
    digitization_preflight = optional_json(digitization_preflight_path)
    literature_metric_path = Path(args.literature_metric_preflight_report)
    literature_metric = optional_json(literature_metric_path)
    case_package_path = Path(args.case_package_report)
    case_package = optional_json(case_package_path)
    case_preflight_path = Path(args.case_package_preflight_report)
    case_preflight = optional_json(case_preflight_path)
    external_dataset_path = Path(args.external_dataset_report)
    external_dataset = optional_json(external_dataset_path)
    d27_program_scout_path = Path(args.d27_program_scout_report)
    d27_program_scout = optional_json(d27_program_scout_path)
    summary = reference.get('summary') if isinstance(reference.get('summary'), dict) else {}
    external_ok = reference.get('external_plume_shape_dataset_agreement') is True
    clears = reference.get('clears_reference_data_blocker') is True
    obs_summary = (
        observation.get('summary')
        if isinstance(observation, dict) and isinstance(observation.get('summary'), dict)
        else {}
    )
    observation_ok = (
        isinstance(observation, dict)
        and observation.get('status') == 'PASS-H2-PLUME-OBSERVATION'
        and obs_summary.get('sensor_timeseries_available') is True
        and obs_summary.get('plume_extents_available') is True
        and finite(obs_summary.get('max_flammable_x'))
        and finite(obs_summary.get('max_flammable_z'))
    )
    spec_summary = (
        benchmark_spec.get('summary')
        if isinstance(benchmark_spec, dict) and isinstance(benchmark_spec.get('summary'), dict)
        else {}
    )
    spec_ok = (
        isinstance(benchmark_spec, dict)
        and benchmark_spec.get('status') == 'PASS-EXTERNAL-PLUME-BENCHMARK-SPEC'
        and benchmark_spec.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and spec_summary.get('case_spec_available') is True
        and spec_summary.get('release_geometry_metadata_available') is True
        and spec_summary.get('reliable_sensor_subset_declared') is True
    )
    triage_summary = (
        public_source_triage.get('summary')
        if isinstance(public_source_triage, dict) and isinstance(public_source_triage.get('summary'), dict)
        else {}
    )
    triage_ok = (
        isinstance(public_source_triage, dict)
        and public_source_triage.get('status') == 'PASS-H2-EXTERNAL-PLUME-PUBLIC-SOURCE-TRIAGE'
        and public_source_triage.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and triage_summary.get('public_source_registry_available') is True
        and triage_summary.get('public_geometry_release_summary_available') is True
        and triage_summary.get('public_sensor_reliability_summary_available') is True
        and triage_summary.get('ready_for_dataset_ingestion') is False
    )
    ingestion_inputs = (
        dataset_ingestion.get('current_inputs')
        if isinstance(dataset_ingestion, dict) and isinstance(dataset_ingestion.get('current_inputs'), dict)
        else {}
    )
    ingestion_ok = (
        isinstance(dataset_ingestion, dict)
        and dataset_ingestion.get('status') == 'PASS-SBEPV5-D27-DATASET-INGESTION'
        and dataset_ingestion.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and all(ingestion_inputs.get(key) is True for key in (
            'dataset_metadata_available',
            'exact_sensor_coordinates_available',
            'exact_baffle_geometry_available',
            'experimental_timeseries_available',
        ))
    )
    digitization_summary = (
        digitization_preflight.get('summary')
        if isinstance(digitization_preflight, dict) and isinstance(digitization_preflight.get('summary'), dict)
        else {}
    )
    digitization_preflight_ok = (
        isinstance(digitization_preflight, dict)
        and digitization_preflight.get('status') == 'PASS-SBEPV5-D27-DIGITIZATION-PREFLIGHT'
        and digitization_preflight.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and digitization_summary.get('public_source_registry_available') is True
        and digitization_summary.get('templates_available') is True
    )
    literature_metric_summary = (
        literature_metric.get('summary')
        if isinstance(literature_metric, dict) and isinstance(literature_metric.get('summary'), dict)
        else {}
    )
    literature_metric_ok = (
        isinstance(literature_metric, dict)
        and literature_metric.get('status') == 'PASS-SBEPV5-D27-LITERATURE-METRIC-PREFLIGHT'
        and literature_metric.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and literature_metric_summary.get('literature_metric_anchor_available') is True
        and literature_metric.get('clears_reference_data_blocker') is False
        and literature_metric_summary.get('ready_for_reference_agreement_consumption') is False
    )
    external_dataset_ok = (
        isinstance(external_dataset, dict)
        and external_dataset.get('status') == 'PASS-SBEPV5-D27-EXTERNAL-PLUME-DATASET'
        and external_dataset.get('external_dataset_written') is True
    )
    case_package_ok = (
        isinstance(case_package, dict)
        and case_package.get('status') == 'PASS-SBEPV5-D27-CASE-PACKAGE-SCAFFOLD'
        and case_package.get('case_package_available') is True
    )
    case_preflight_ok = (
        isinstance(case_preflight, dict)
        and case_preflight.get('status') == 'PASS-SBEPV5-D27-CASE-PACKAGE-PREFLIGHT'
        and case_preflight.get('case_scaffold_preflight_passed') is True
    )
    scout_outputs = (
        d27_program_scout.get('validated_outputs')
        if isinstance(d27_program_scout, dict) and isinstance(d27_program_scout.get('validated_outputs'), dict)
        else {}
    )
    scout_input = (
        d27_program_scout.get('input_summary')
        if isinstance(d27_program_scout, dict) and isinstance(d27_program_scout.get('input_summary'), dict)
        else {}
    )
    d27_program_scout_ok = (
        isinstance(d27_program_scout, dict)
        and d27_program_scout.get('status') == 'PASS-SBEPV5-D27-PROGRAM-SCOUT-RUN'
        and d27_program_scout.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and d27_program_scout.get('clears_reference_data_blocker') is False
        and scout_outputs.get('cuda_run') is True
        and scout_outputs.get('program_sensor_sampling_available') is True
        and scout_outputs.get('program_downwind_extent_available') is True
        and scout_outputs.get('program_vertical_extent_available') is True
        and scout_outputs.get('case_matched_external_dataset_ingested') is False
        and int(scout_input.get('baffle_stl_count', 0)) == 4
    )

    current_outputs = {
        'public_source_triage_available': triage_ok,
        'public_source_missing_artifact_count': (
            triage_summary.get('missing_artifact_count') if triage_ok else None
        ),
        'digitization_preflight_available': digitization_preflight_ok,
        'digitization_preflight_missing_artifact_count': (
            digitization_summary.get('missing_artifact_count') if digitization_preflight_ok else None
        ),
        'literature_metric_preflight_available': literature_metric_ok,
        'literature_metric_anchor_available': (
            literature_metric_summary.get('literature_metric_anchor_available') if literature_metric_ok else False
        ),
        'literature_metric_missing_artifact_count': (
            literature_metric_summary.get('missing_artifact_count') if literature_metric_ok else None
        ),
        'literature_metric_ready_for_reference_agreement_consumption': (
            literature_metric_summary.get('ready_for_reference_agreement_consumption') if literature_metric_ok else False
        ),
        'case_spec_report_available': spec_ok,
        'case_package_report_available': case_package_ok,
        'case_package_preflight_report_available': case_preflight_ok,
        'case_package_reference_source_resolution_ready': (
            case_preflight_ok and case_preflight.get('reference_input_source_resolution_ready') is True
        ),
        'case_package_runnable': case_package_ok and case_package.get('case_runnable') is True,
        'case_matched_pelelmex_input_template_available': (
            case_package_ok
            and isinstance(case_package.get('package_files'), dict)
            and bool(case_package['package_files'].get('reference_input'))
        ),
        'sbepv5_d27_program_scout_run_available': d27_program_scout_ok,
        'sbepv5_d27_program_scout_cuda_run': bool(scout_outputs.get('cuda_run')) if d27_program_scout_ok else False,
        'sbepv5_d27_program_scout_baffle_stl_count': scout_input.get('baffle_stl_count') if d27_program_scout_ok else None,
        'sbepv5_d27_program_scout_plotfile_count': scout_outputs.get('plotfile_count') if d27_program_scout_ok else None,
        'sbepv5_d27_program_scout_sensor_timeseries_rows': scout_outputs.get('sensor_timeseries_rows') if d27_program_scout_ok else None,
        'release_geometry_metadata_available': spec_ok,
        'reliable_sensor_subset_declared': spec_ok,
        'dataset_ingestion_report_available': isinstance(dataset_ingestion, dict),
        'dataset_metadata_available': ingestion_inputs.get('dataset_metadata_available') is True,
        'exact_sensor_coordinates_available': ingestion_inputs.get('exact_sensor_coordinates_available') is True,
        'exact_baffle_geometry_available': ingestion_inputs.get('exact_baffle_geometry_available') is True,
        'digitized_experimental_timeseries_available': (
            ingestion_inputs.get('experimental_timeseries_available') is True
        ),
        'external_dataset_builder_report_available': isinstance(external_dataset, dict),
        'external_plume_dataset_json_written': external_dataset_ok,
        'threshold_reference_agreement': reference.get('threshold_reference_agreement') is True,
        'external_plume_shape_dataset_agreement': external_ok,
        'amr_peak_x_available': finite(summary.get('amr_peak_x')),
        'amr_lel_cloud_volume_available': finite(summary.get('amr_lel_cloud_volume')),
        'amr_final_flammable_planes_available': finite(summary.get('amr_final_flammable_planes')),
        'sensor_timeseries_sampling_available': observation_ok,
        'maximum_downwind_extent_available': observation_ok,
        'maximum_vertical_extent_available': observation_ok,
        'case_matched_external_dataset_ingested': ingestion_ok and external_dataset_ok and external_ok and clears,
        'plume_observation_report_available': observation_ok,
    }
    blocking_gaps: list[str] = []
    if not current_outputs['case_matched_external_dataset_ingested']:
        blocking_gaps.append('case_matched_external_plume_dataset_not_ingested')
    if not current_outputs['sensor_timeseries_sampling_available']:
        blocking_gaps.append('transient_sensor_probe_output_missing_for_sbepv5_style_validation')
    if not current_outputs['maximum_downwind_extent_available']:
        blocking_gaps.append('flammable_cloud_downwind_extent_metric_missing')
    if not current_outputs['maximum_vertical_extent_available']:
        blocking_gaps.append('flammable_cloud_vertical_extent_metric_missing')

    quality_gate_matrix = build_quality_gate_matrix(current_outputs)
    failed_quality_gates = [
        item['name'] for item in quality_gate_matrix
        if item['status'] != 'PASS'
    ]
    if failed_quality_gates and 'external_plume_quality_gates_not_all_passed' not in blocking_gaps:
        blocking_gaps.append('external_plume_quality_gates_not_all_passed')
    ready = not blocking_gaps and not failed_quality_gates
    checklist_path = write_intake_checklist(Path(args.intake_checklist))
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 External Plume Benchmark Readiness',
        'reference_agreement_report': str(reference_path),
        'plume_observation_report': str(observation_path) if observation else None,
        'benchmark_spec_report': str(benchmark_spec_path) if benchmark_spec else None,
        'public_source_triage_report': str(public_source_triage_path) if public_source_triage else None,
        'digitization_preflight_report': str(digitization_preflight_path) if digitization_preflight else None,
        'literature_metric_preflight_report': str(literature_metric_path) if literature_metric else None,
        'dataset_ingestion_report': str(dataset_ingestion_path) if dataset_ingestion else None,
        'case_package_report': str(case_package_path) if case_package else None,
        'case_package_preflight_report': str(case_preflight_path) if case_preflight else None,
        'external_dataset_report': str(external_dataset_path) if external_dataset else None,
        'd27_program_scout_report': str(d27_program_scout_path) if d27_program_scout else None,
        'clears_reference_data_blocker': ready,
        'current_outputs': current_outputs,
        'quality_gate_matrix': quality_gate_matrix,
        'candidate_public_benchmarks': PUBLIC_BENCHMARK_CANDIDATES,
        'public_source_missing_artifacts': (
            public_source_triage.get('missing_artifacts')
            if isinstance(public_source_triage, dict) and isinstance(public_source_triage.get('missing_artifacts'), list)
            else []
        ),
        'digitization_missing_artifacts': (
            digitization_preflight.get('missing_artifacts')
            if isinstance(digitization_preflight, dict) and isinstance(digitization_preflight.get('missing_artifacts'), list)
            else []
        ),
        'literature_metric_missing_artifacts': (
            literature_metric.get('missing_artifacts')
            if isinstance(literature_metric, dict) and isinstance(literature_metric.get('missing_artifacts'), list)
            else []
        ),
        'benchmark_pre_ingestion_gaps': (
            dataset_ingestion.get('blocking_gaps')
            if isinstance(dataset_ingestion, dict) and isinstance(dataset_ingestion.get('blocking_gaps'), list)
            else (
                benchmark_spec.get('pre_ingestion_gaps')
                if isinstance(benchmark_spec, dict) and isinstance(benchmark_spec.get('pre_ingestion_gaps'), list)
                else ['benchmark_case_spec_report_missing']
            )
        ),
        'blocking_gaps': blocking_gaps,
        'next_required_artifacts': [
            'case-matched PeleLMeX input and geometry generated from the selected benchmark specification',
            'exact SBEPV5 D27 baffle placement/wall attachment and sensor coordinates replacing the program-scout approximations',
            'exact sensor and baffle coordinates digitized from source figures or original tabular data',
            'program sensor probes compared against SBEPV5 Gas09/Gas10 literature arrival-time anchors',
            'digitized or tabulated experimental dataset with source metadata and uncertainty/tolerances',
            'official h2_reference_agreement_report regenerated with --external-plume-dataset-json',
        ],
        'evidence_files': [evidence_entry('external_plume_intake_checklist', checklist_path), evidence_entry('reference_agreement_report', reference_path)] + (
            [evidence_entry('plume_observation_report', observation_path)] if observation else []
        ) + (
            [evidence_entry('benchmark_spec_report', benchmark_spec_path)] if benchmark_spec else []
        ) + (
            [evidence_entry('public_source_triage_report', public_source_triage_path)] if public_source_triage else []
        ) + (
            [evidence_entry('digitization_preflight_report', digitization_preflight_path)] if digitization_preflight else []
        ) + (
            [evidence_entry('literature_metric_preflight_report', literature_metric_path)] if literature_metric else []
        ) + (
            [evidence_entry('dataset_ingestion_report', dataset_ingestion_path)] if dataset_ingestion else []
        ) + (
            [evidence_entry('case_package_report', case_package_path)] if case_package else []
        ) + (
            [evidence_entry('case_package_preflight_report', case_preflight_path)] if case_preflight else []
        ) + (
            [evidence_entry('external_dataset_report', external_dataset_path)] if external_dataset else []
        ) + (
            [evidence_entry('d27_program_scout_report', d27_program_scout_path)] if d27_program_scout else []
        ),
        'limitations': [
            'This readiness report does not clear the production reference-data blocker.',
            'It records public benchmark candidates and machine-checkable output gaps before experimental agreement can be claimed.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    outputs = data.get('current_outputs')
    require(isinstance(outputs, dict), 'current_outputs missing')
    for key in (
        'case_spec_report_available',
        'public_source_triage_available',
        'digitization_preflight_available',
        'literature_metric_preflight_available',
        'literature_metric_anchor_available',
        'literature_metric_ready_for_reference_agreement_consumption',
        'release_geometry_metadata_available',
        'reliable_sensor_subset_declared',
        'digitized_experimental_timeseries_available',
        'dataset_ingestion_report_available',
        'dataset_metadata_available',
        'exact_baffle_geometry_available',
        'external_dataset_builder_report_available',
        'external_plume_dataset_json_written',
        'case_package_report_available',
        'case_package_preflight_report_available',
        'case_package_reference_source_resolution_ready',
        'case_package_runnable',
        'case_matched_pelelmex_input_template_available',
        'sbepv5_d27_program_scout_run_available',
        'sbepv5_d27_program_scout_cuda_run',
        'sbepv5_d27_program_scout_baffle_stl_count',
        'sbepv5_d27_program_scout_plotfile_count',
        'sbepv5_d27_program_scout_sensor_timeseries_rows',
    ):
        require(key in outputs, f'current_outputs missing {key}')
    gaps = data.get('blocking_gaps')
    require(isinstance(gaps, list), 'blocking_gaps missing')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    failed_matrix = [
        item for item in matrix
        if isinstance(item, dict)
        and item.get('status') != 'PASS'
    ]
    if data.get('status') == STATUS_READY:
        require(not gaps, 'ready report contains blocking gaps')
        require(not failed_matrix, 'ready report has failed quality gates')
        require(data.get('clears_reference_data_blocker') is True, 'ready report does not clear blocker')
    else:
        require(bool(gaps), 'not-ready report must contain blocking gaps')
        require(failed_matrix, 'not-ready report must list failed quality gates')
        require(data.get('clears_reference_data_blocker') is False, 'not-ready report cannot clear blocker')
    candidates = data.get('candidate_public_benchmarks')
    require(isinstance(candidates, list) and len(candidates) >= 1, 'candidate benchmark list missing')
    for item in candidates:
        require(isinstance(item, dict), 'candidate benchmark is not an object')
        require(bool(item.get('id')), 'candidate id missing')
        require(bool(item.get('url')), 'candidate url missing')
        require(isinstance(item.get('required_program_outputs'), list), 'candidate required outputs missing')
    missing_artifacts = data.get('public_source_missing_artifacts')
    require(isinstance(missing_artifacts, list), 'public_source_missing_artifacts missing')
    digitization_missing_artifacts = data.get('digitization_missing_artifacts')
    require(isinstance(digitization_missing_artifacts, list), 'digitization_missing_artifacts missing')
    literature_metric_missing_artifacts = data.get('literature_metric_missing_artifacts')
    require(isinstance(literature_metric_missing_artifacts, list), 'literature_metric_missing_artifacts missing')
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
        '# Engineering H2 External Plume Benchmark Readiness',
        '',
        f"Status: `{report['status']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        '',
        '## Current Outputs',
        '',
    ]
    for key, value in report['current_outputs'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Quality Gate Matrix', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        gap = item['gap'] or item['evidence']
        lines.append(f"| `{item['name']}` | `{item['status']}` | {gap} |")
    lines += ['', '## Benchmark Preparation Gaps', '']
    for gap in report['benchmark_pre_ingestion_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Public Source Missing Artifacts', '']
    for item in report['public_source_missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
    lines += ['', '## Digitization Missing Artifacts', '']
    for item in report['digitization_missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
    lines += ['', '## Literature Metric Missing Artifacts', '']
    for item in report['literature_metric_missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
    lines += ['', '## Candidate Public Benchmarks', '']
    for item in report['candidate_public_benchmarks']:
        lines.append(f"### {item['id']}")
        lines.append(f"- Title: `{item['title']}`")
        lines.append(f"- Source type: `{item['source_type']}`")
        lines.append(f"- URL: {item['url']}")
        lines.append('- Required program outputs:')
        for required in item['required_program_outputs']:
            lines.append(f'  - {required}')
        lines.append('')
    lines += ['## Blocking Gaps', '']
    for gap in report['blocking_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Next Required Artifacts', '']
    for item in report['next_required_artifacts']:
        lines.append(f'- {item}')
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-report', default=str(DEFAULT_REFERENCE_REPORT))
    parser.add_argument('--plume-observation-report', default=str(DEFAULT_PLUME_OBSERVATION_REPORT))
    parser.add_argument('--benchmark-spec-report', default=str(DEFAULT_BENCHMARK_SPEC_REPORT))
    parser.add_argument('--public-source-triage-report', default=str(DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT))
    parser.add_argument('--dataset-ingestion-report', default=str(DEFAULT_DATASET_INGESTION_REPORT))
    parser.add_argument('--digitization-preflight-report', default=str(DEFAULT_DIGITIZATION_PREFLIGHT_REPORT))
    parser.add_argument('--literature-metric-preflight-report', default=str(DEFAULT_LITERATURE_METRIC_PREFLIGHT_REPORT))
    parser.add_argument('--case-package-report', default=str(DEFAULT_CASE_PACKAGE_REPORT))
    parser.add_argument('--case-package-preflight-report', default=str(DEFAULT_CASE_PACKAGE_PREFLIGHT_REPORT))
    parser.add_argument('--external-dataset-report', default=str(DEFAULT_EXTERNAL_DATASET_REPORT))
    parser.add_argument('--d27-program-scout-report', default=str(DEFAULT_D27_PROGRAM_SCOUT_REPORT))
    parser.add_argument('--intake-checklist', default=str(DEFAULT_INTAKE_CHECKLIST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_external_plume_benchmark_readiness VERIFY-PASS '
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
            'engineering_h2_external_plume_benchmark_readiness PASS '
            f"json={out_json} md={out_md} status={report['status']} gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except ReadinessError as exc:
        print(f'engineering_h2_external_plume_benchmark_readiness FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
