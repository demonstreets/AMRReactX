#!/usr/bin/env python3
"""Write/verify a HySafe SBEPV5 D27 PeleLMeX case package scaffold."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-SBEPV5-D27-CASE-PACKAGE-SCAFFOLD'

DEFAULT_SPEC_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_spec_20260723/'
    'hysafe_sbepv5_d27_benchmark_spec_report.json'
)
DEFAULT_INGESTION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
    'sbepv5_d27_dataset_ingestion_report.json'
)
DEFAULT_PACKAGE_ROOT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/'
    'sbepv5_d27_case_package_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/'
    'sbepv5_d27_case_package_report.md'
)

RELIABLE_SENSORS = (1, 2, 5, 7, 8, 9, 10, 12)
UNRELIABLE_SENSORS = (3, 4, 6, 11)


class CasePackageError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise CasePackageError(message)


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
        raise CasePackageError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise CasePackageError(f'invalid JSON in {path}: {exc}') from exc
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + '\n', encoding='utf-8')


def pelelmex_input(spec: dict[str, Any], mode: str) -> str:
    release = spec['release']
    if mode == 'reference':
        n_cell = '240 40 180'
        max_grid = '20'
        dt = '1.0e-2'
        plot_int = '100'
    else:
        n_cell = '60 10 45'
        max_grid = '10'
        dt = '2.0e-2'
        plot_int = '50'
    return f"""
# HySafe SBEPV5 / GexCon D27 PeleLMeX {mode} case scaffold.
# Generated from the audited benchmark specification. This input is not
# production-runnable until exact baffle/sensor coordinates and the dataset
# package have passed their ingestion gates.

peleLM.lo_bc = NoSlipWallAdiab NoSlipWallAdiab NoSlipWallAdiab
peleLM.hi_bc = NoSlipWallAdiab NoSlipWallAdiab NoSlipWallAdiab
peleLM.v = 1
peleLM.incompressible = 0
peleLM.sdc_iterMax = 1
peleLM.num_init_iter = 1
peleLM.floor_species = 1
peleLM.user_defined_ext_sources = 1
peleLM.have_divu = 1
peleLM.advection_scheme = Godunov_PLM
peleLM.do_react = 0
peleLM.chem_integrator = ReactorNull
peleLM.do_les = 1
peleLM.les_model = kepsilon
peleLM.aux_vars = k epsilon
peleLM.ke_k_amb = 0.05
peleLM.ke_eps_amb = 0.01
peleLM.ke_prod_lim = 1.6
peleLM.ke_wall_functions = 1

amr.n_cell = {n_cell}
amr.max_level = 1
amr.ref_ratio = 2
amr.max_grid_size = {max_grid}
amr.blocking_factor = 5
amr.plot_int = {plot_int}
amr.check_int = -1
amr.regrid_int = 2
amr.stop_time = 120.0
amr.max_step = 12000

geometry.prob_lo = 0.0 0.0 0.0
geometry.prob_hi = 1.20 0.20 0.90
geometry.coord_sys = 0
geometry.is_periodic = 0 0 0

codex.case_id = hysafe_sbepv5_d27
codex.case_mode = {mode}
codex.release_gas = pure_H2
codex.release_period_s = {release['release_period_s']}
codex.nozzle_diameter_m = {release['nozzle_diameter_m']}
codex.exit_velocity_m_s = {release['exit_velocity_m_s']}
codex.flow_rate_normal_l_s = {release['flow_rate_normal_l_s']}
codex.jet_exit_location_m = {release['jet_exit_location_m']['x']} {release['jet_exit_location_m']['y']} {release['jet_exit_location_m']['z']}
codex.sensor_file = sensors_template.csv
codex.baffle_file = baffle_geometry_template.csv
codex.dataset_metadata_file = dataset_metadata_template.json
codex.experimental_timeseries_file = experimental_timeseries_template.csv
codex.time_step_s = {dt}
"""


def sensors_template() -> str:
    lines = ['sensor_id,x_m,y_m,z_m,reliability,source_basis,digitization_uncertainty_m']
    for sensor_id in range(1, 13):
        reliability = 'reliable' if sensor_id in RELIABLE_SENSORS else 'unreliable'
        lines.append(f'{sensor_id},,,,{reliability},requires_source_figure_or_original_table,')
    return '\n'.join(lines)


def baffle_template() -> str:
    lines = ['baffle_id,x_min_m,x_max_m,y_min_m,y_max_m,z_min_m,z_max_m,source_basis,digitization_uncertainty_m']
    for baffle_id in range(1, 5):
        lines.append(f'{baffle_id},,,,,,,requires_source_figure_digitization,')
    return '\n'.join(lines)


def experimental_timeseries_template() -> str:
    columns = ['time_s'] + [f'Gas{sensor_id:02d}_vol_percent' for sensor_id in range(1, 13)]
    return ','.join(columns)


def metadata_template(spec: dict[str, Any]) -> str:
    return json.dumps(
        {
            'schema_version': 1,
            'benchmark_id': 'hysafe_sbepv5_d27',
            'source': spec['source'],
            'digitization': {
                'method': '',
                'operator_or_tool': '',
                'source_figures_or_tables': [],
                'notes': 'Fill from original Excel data or audited literature digitization.',
            },
            'original_dataset_sha256': '',
            'digitized_dataset_sha256': '',
            'case_alignment': {
                'geometry': False,
                'release_rate': False,
                'release_direction': False,
                'boundary_conditions': False,
            },
        },
        indent=2,
        sort_keys=True,
    )


def readme_text() -> str:
    return """
# HySafe SBEPV5 / GexCon D27 Case Package

This package is a scaffold generated from the audited public benchmark
specification. It intentionally keeps the runnable flag false until the
following files are filled from source data and pass the ingestion gate:

- `dataset_metadata_template.json`
- `sensors_template.csv`
- `baffle_geometry_template.csv`
- `experimental_timeseries_template.csv`

The `inputs.sbepv5_d27_scout` and `inputs.sbepv5_d27_reference` files encode
the vessel size and release metadata from the benchmark specification. They are
not an external validation claim. After exact geometry and sensor data are
ingested, the case should be run to 120 s, plume observations should be
extracted with matching sensor IDs, and the SBEPV5 external dataset builder
should generate the official `external_plume_dataset_json`.
"""


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    spec_path = Path(args.benchmark_spec_report)
    ingestion_path = Path(args.dataset_ingestion_report)
    package_root = Path(args.package_root)
    spec = load_json(spec_path)
    require(spec.get('status') == 'PASS-EXTERNAL-PLUME-BENCHMARK-SPEC', 'benchmark spec report is not PASS')
    require(spec.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark spec is not HySafe SBEPV5 D27')
    ingestion = load_json(ingestion_path) if ingestion_path.is_file() else None
    ingestion_inputs = ingestion.get('current_inputs') if isinstance(ingestion, dict) else {}
    case_runnable = (
        isinstance(ingestion_inputs, dict)
        and ingestion_inputs.get('dataset_metadata_available') is True
        and ingestion_inputs.get('exact_sensor_coordinates_available') is True
        and ingestion_inputs.get('exact_baffle_geometry_available') is True
        and ingestion_inputs.get('experimental_timeseries_available') is True
    )
    runnable_gaps = []
    if not case_runnable:
        runnable_gaps = [
            'dataset_metadata_json_missing_or_not_passed',
            'exact_sensor_coordinates_missing_or_not_passed',
            'exact_baffle_geometry_missing_or_not_passed',
            'experimental_timeseries_missing_or_not_passed',
        ]

    files = {
        'scout_input': package_root / 'inputs.sbepv5_d27_scout',
        'reference_input': package_root / 'inputs.sbepv5_d27_reference',
        'sensor_template': package_root / 'sensors_template.csv',
        'baffle_template': package_root / 'baffle_geometry_template.csv',
        'metadata_template': package_root / 'dataset_metadata_template.json',
        'experimental_timeseries_template': package_root / 'experimental_timeseries_template.csv',
        'readme': package_root / 'README.md',
    }
    write_text(files['scout_input'], pelelmex_input(spec, 'scout'))
    write_text(files['reference_input'], pelelmex_input(spec, 'reference'))
    write_text(files['sensor_template'], sensors_template())
    write_text(files['baffle_template'], baffle_template())
    write_text(files['metadata_template'], metadata_template(spec))
    write_text(files['experimental_timeseries_template'], experimental_timeseries_template())
    write_text(files['readme'], readme_text())

    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'title': 'HySafe SBEPV5 D27 PeleLMeX Case Package Scaffold',
        'benchmark_spec_report': str(spec_path),
        'dataset_ingestion_report': str(ingestion_path) if ingestion else None,
        'package_root': str(package_root),
        'case_package_available': True,
        'case_runnable': case_runnable,
        'case_alignment_ready': case_runnable,
        'clears_reference_data_blocker': False,
        'package_files': {key: str(value) for key, value in files.items()},
        'runnable_blocking_gaps': runnable_gaps,
        'release_summary': spec['release'],
        'geometry_summary': spec['geometry'],
        'sensor_summary': spec['measurements'],
        'evidence_files': [
            evidence_entry('benchmark_spec_report', spec_path),
            *( [evidence_entry('dataset_ingestion_report', ingestion_path)] if ingestion else [] ),
            *(evidence_entry(label, path) for label, path in files.items()),
        ],
        'limitations': [
            'This report proves the SBEPV5 case package scaffold exists.',
            'It does not prove that the case has been run or validated against external data.',
            'case_runnable remains false until exact geometry, sensors, metadata, and experimental time series pass ingestion.',
        ],
    }
    validate_report_object(report, check_hashes=False)
    return report


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, f'invalid status: {data.get("status")}')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark_id mismatch')
    require(data.get('case_package_available') is True, 'case package availability flag missing')
    require(data.get('clears_reference_data_blocker') is False, 'case package cannot clear reference-data blocker')
    files = data.get('package_files')
    require(isinstance(files, dict), 'package_files missing')
    for key in (
        'scout_input',
        'reference_input',
        'sensor_template',
        'baffle_template',
        'metadata_template',
        'experimental_timeseries_template',
        'readme',
    ):
        require(key in files, f'package_files missing {key}')
        path = Path(str(files[key]))
        require(path.is_file(), f'missing package file {key}: {path}')
    if data.get('case_runnable') is True:
        require(data.get('case_alignment_ready') is True, 'runnable package must be alignment-ready')
        require(not data.get('runnable_blocking_gaps'), 'runnable package has blocking gaps')
    else:
        gaps = data.get('runnable_blocking_gaps')
        require(isinstance(gaps, list) and gaps, 'non-runnable package must list blocking gaps')
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
        '# HySafe SBEPV5 D27 Case Package Scaffold',
        '',
        f"Status: `{report['status']}`",
        f"Case runnable: `{report['case_runnable']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        f"Package root: `{report['package_root']}`",
        '',
        '## Package Files',
        '',
    ]
    for key, value in report['package_files'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Runnable Blocking Gaps', '']
    for gap in report['runnable_blocking_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-spec-report', default=str(DEFAULT_SPEC_REPORT))
    parser.add_argument('--dataset-ingestion-report', default=str(DEFAULT_INGESTION_REPORT))
    parser.add_argument('--package-root', default=str(DEFAULT_PACKAGE_ROOT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_sbepv5_case_package VERIFY-PASS '
                f"json={args.verify_json} runnable={data['case_runnable']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_sbepv5_case_package PASS '
            f"json={out_json} md={out_md} runnable={report['case_runnable']}"
        )
        return 0
    except CasePackageError as exc:
        print(f'engineering_h2_sbepv5_case_package FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
