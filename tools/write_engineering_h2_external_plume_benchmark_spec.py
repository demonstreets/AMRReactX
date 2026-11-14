#!/usr/bin/env python3
"""Write/verify a machine-checkable public H2 plume benchmark case specification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-EXTERNAL-PLUME-BENCHMARK-SPEC'

DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_spec_20260723/'
    'hysafe_sbepv5_d27_benchmark_spec_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_spec_20260723/'
    'hysafe_sbepv5_d27_benchmark_spec_report.md'
)


class SpecError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SpecError(message)


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
        raise SpecError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise SpecError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def build_sbepv5_d27_report() -> dict[str, Any]:
    reliable_sensors = [1, 2, 5, 7, 8, 9, 10, 12]
    unreliable_sensors = [3, 4, 6, 11]
    preparation_gaps = [
        'exact_baffle_positions_require_source_figure_digitization',
        'exact_sensor_coordinates_require_source_figure_or_tabular_data',
        'experimental_120s_sensor_timeseries_excel_not_ingested',
        'case_matched_pelelmex_input_not_generated_from_this_spec',
    ]
    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'HySafe SBEPV5 / GexCon D27 External H2 Plume Benchmark Specification',
        'clears_reference_data_blocker': False,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'source': {
            'title': 'Results of the HySafe CFD Validation Benchmark SBEPV5',
            'authors': [
                'T. Jordan',
                'J. Garcia',
                'O. Hansen',
                'A. Huser',
                'S. Ledin',
                'P. Middha',
                'V. Molkov',
                'J. Travis',
                'A. G. Venetsanos',
                'F. Verbecke',
                'J. Xiao',
            ],
            'publication_year': 2007,
            'venue': '2nd International Conference on Hydrogen Safety, San Sebastian',
            'urls': [
                'https://publikationen.bibliothek.kit.edu/230068969',
                'https://www.h2knowledgecentre.com/content/conference289',
                'https://www.researchgate.net/publication/311396790_Results_of_the_HySafe_CFD_Validation_Benchmark_SBEPV5',
            ],
            'source_type': 'literature_digitized',
        },
        'experiment': {
            'case_id': 'D27',
            'test_year': 2003,
            'experiment_organizations': ['GexCon', 'Norsk Hydro', 'Statoil'],
            'description': (
                'Low-momentum horizontal pure-H2 jet release into a baffled, '
                'partially confined multi-compartment vessel.'
            ),
        },
        'geometry': {
            'coordinate_system': 'paper_table_x_width_y_depth_z_vertical',
            'vessel_dimensions_m': {'x_width': 1.20, 'y_depth': 0.20, 'z_height': 0.90},
            'compartment_count': 12,
            'baffle_count': 4,
            'baffle_plate_dimensions_m': {'y_depth': 0.20, 'z_height': 0.30},
            'baffle_position_status': 'requires_source_figure_digitization',
            'vent_opening': {
                'wall': 'opposite_release_location',
                'description': 'central vent opening about 0.01 m above floor',
                'dimensions_m': {'y_width': 0.10, 'z_height': 0.20},
                'exact_position_status': 'requires_source_figure_digitization',
            },
        },
        'release': {
            'gas': 'pure_H2',
            'release_period_s': 60.0,
            'nozzle_diameter_m': 0.012,
            'exit_velocity_m_s': 10.17,
            'flow_rate_normal_l_s': 1.15,
            'jet_exit_location_m': {'x': 0.03, 'y': 0.10, 'z': 0.145},
            'release_direction': 'horizontal_toward_vent_wall_from_paper_geometry',
            'direction_status': 'requires_case_input_confirmation_against_source_figure',
        },
        'measurements': {
            'sensor_count': 12,
            'sensor_location_description': 'one H2 concentration sensor per compartment on the rear wall',
            'sensor_coordinate_status': 'requires_source_figure_or_tabular_data',
            'reliable_sensor_ids': reliable_sensors,
            'unreliable_sensor_ids': unreliable_sensors,
            'sensor_accuracy_volume_percent_h2': 1.0,
            'timeseries_duration_s': 120.0,
            'available_dataset_description': (
                'Transient volumetric H2 concentration recordings for 12 monitor locations '
                'reported as MS Excel data in the benchmark paper.'
            ),
            'dataset_ingested': False,
        },
        'required_program_outputs': [
            'case-matched baffled-box geometry including vent and release nozzle',
            'transient H2 concentration sampling at the 12 monitor locations',
            'arrival-time metrics for reliable sensors',
            'peak and late-release concentration metrics for reliable sensors',
            'source metadata and digitization uncertainty for each literature-derived trace',
        ],
        'recommended_acceptance_metrics': [
            {'metric_type': 'arrival_time', 'sensor_ids': reliable_sensors, 'threshold_volume_fraction_h2': 0.04},
            {'metric_type': 'sensor_concentration_peak', 'sensor_ids': reliable_sensors},
            {'metric_type': 'sensor_concentration_release_end', 'sensor_ids': reliable_sensors, 'time_s': 60.0},
            {'metric_type': 'sensor_concentration_late', 'sensor_ids': reliable_sensors, 'time_s': 120.0},
        ],
        'summary': {
            'case_spec_available': True,
            'release_geometry_metadata_available': True,
            'reliable_sensor_subset_declared': True,
            'exact_sensor_coordinates_available': False,
            'experimental_timeseries_dataset_ingested': False,
            'preparation_gap_count': len(preparation_gaps),
        },
        'pre_ingestion_gaps': preparation_gaps,
        'limitations': [
            'This report fixes the public benchmark specification used for future case setup.',
            'It does not contain digitized experimental traces and does not clear production reference-data validation.',
            'Exact baffle and sensor coordinates still require source-figure digitization or original tabular data.',
        ],
    }
    validate_report_object(report, check_hashes=False)
    return report


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, f'invalid status: {data.get("status")}')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'unexpected benchmark_id')
    require(data.get('clears_reference_data_blocker') is False, 'benchmark spec cannot clear reference-data blocker')
    source = data.get('source')
    require(isinstance(source, dict), 'source missing')
    urls = source.get('urls')
    require(isinstance(urls, list) and len(urls) >= 2, 'source urls missing')
    require(source.get('source_type') == 'literature_digitized', 'source_type must be literature_digitized')
    geom = data.get('geometry')
    require(isinstance(geom, dict), 'geometry missing')
    dims = geom.get('vessel_dimensions_m') if isinstance(geom.get('vessel_dimensions_m'), dict) else {}
    require(finite(dims.get('x_width')) and finite(dims.get('y_depth')) and finite(dims.get('z_height')), 'vessel dimensions incomplete')
    require(int(geom.get('compartment_count', 0)) == 12, 'compartment_count must be 12')
    require(int(geom.get('baffle_count', 0)) == 4, 'baffle_count must be 4')
    release = data.get('release')
    require(isinstance(release, dict), 'release missing')
    for key in ('release_period_s', 'nozzle_diameter_m', 'exit_velocity_m_s', 'flow_rate_normal_l_s'):
        require(finite(release.get(key)), f'release {key} missing or non-finite')
    loc = release.get('jet_exit_location_m') if isinstance(release.get('jet_exit_location_m'), dict) else {}
    require(finite(loc.get('x')) and finite(loc.get('y')) and finite(loc.get('z')), 'jet exit location incomplete')
    meas = data.get('measurements')
    require(isinstance(meas, dict), 'measurements missing')
    reliable = meas.get('reliable_sensor_ids')
    unreliable = meas.get('unreliable_sensor_ids')
    require(isinstance(reliable, list) and len(reliable) >= 4, 'reliable_sensor_ids missing')
    require(isinstance(unreliable, list) and set(unreliable) == {3, 4, 6, 11}, 'unreliable_sensor_ids mismatch')
    require(meas.get('dataset_ingested') is False, 'benchmark spec must not claim dataset ingestion')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('case_spec_available') is True, 'case spec flag missing')
    require(summary.get('experimental_timeseries_dataset_ingested') is False, 'summary must not claim timeseries ingestion')
    gaps = data.get('pre_ingestion_gaps')
    require(isinstance(gaps, list) and gaps, 'pre_ingestion_gaps missing')
    require('experimental_120s_sensor_timeseries_excel_not_ingested' in gaps, 'timeseries ingestion gap missing')
    if check_hashes:
        entries = data.get('evidence_files', [])
        require(isinstance(entries, list), 'evidence_files must be a list when present')
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# HySafe SBEPV5 / GexCon D27 Benchmark Spec',
        '',
        f"Status: `{report['status']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        '',
        '## Source',
        '',
        f"- Title: `{report['source']['title']}`",
        f"- Venue: `{report['source']['venue']}`",
        '- URLs:',
    ]
    for url in report['source']['urls']:
        lines.append(f'  - {url}')
    lines += [
        '',
        '## Geometry And Release',
        '',
        f"- Vessel dimensions m: `{report['geometry']['vessel_dimensions_m']}`",
        f"- Compartments: `{report['geometry']['compartment_count']}`",
        f"- Baffles: `{report['geometry']['baffle_count']}`",
        f"- Vent opening: `{report['geometry']['vent_opening']}`",
        f"- Release: `{report['release']}`",
        '',
        '## Measurements',
        '',
        f"- Reliable sensors: `{report['measurements']['reliable_sensor_ids']}`",
        f"- Unreliable sensors: `{report['measurements']['unreliable_sensor_ids']}`",
        f"- Sensor coordinate status: `{report['measurements']['sensor_coordinate_status']}`",
        f"- Dataset ingested: `{report['measurements']['dataset_ingested']}`",
        '',
        '## Pre-Ingestion Gaps',
        '',
    ]
    for gap in report['pre_ingestion_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Required Program Outputs', '']
    for item in report['required_program_outputs']:
        lines.append(f'- {item}')
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
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_external_plume_benchmark_spec VERIFY-PASS '
                f"json={args.verify_json} benchmark_id={data['benchmark_id']}"
            )
            return 0
        report = build_sbepv5_d27_report()
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_external_plume_benchmark_spec PASS '
            f'json={out_json} md={out_md} benchmark_id={report["benchmark_id"]}'
        )
        return 0
    except SpecError as exc:
        print(f'engineering_h2_external_plume_benchmark_spec FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
