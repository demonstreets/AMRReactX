#!/usr/bin/env python3
"""Write/verify ACD-07 academic reacting spray detonation validation report."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = 'PASS-ACADEMIC-SPRAY-DETONATION-VALIDATION'
DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_spray_detonation_validation_20260728')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'case_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_spray_detonation_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_spray_detonation_validation_report.md'

VALIDATION_RE = re.compile(
    r'academic_spray_detonation_validation PASS .*?'
    r'time=(?P<time>[-+0-9.eE]+)\s+'
    r'pressure_front=(?P<pressure_front0>[-+0-9.eE]+):(?P<pressure_front1>[-+0-9.eE]+)\s+'
    r'pressure_front_shift=(?P<pressure_front_shift>[-+0-9.eE]+)\s+'
    r'pressure_front_shift_cells=(?P<pressure_front_shift_cells>[-+0-9.eE]+)\s+'
    r'temp_front=(?P<temp_front0>[-+0-9.eE]+):(?P<temp_front1>[-+0-9.eE]+)\s+'
    r'temp_front_shift=(?P<temp_front_shift>[-+0-9.eE]+)\s+'
    r'heat_release_absmax=(?P<heat_release_absmax>[-+0-9.eE]+)\s+'
    r'o2_consumption=(?P<o2_consumption>[-+0-9.eE]+)\s+'
    r'fuel_vapor_increase=(?P<fuel_vapor_increase>[-+0-9.eE]+)\s+'
    r'particles=(?P<particle_count0>\d+):(?P<particle_count1>\d+)\s+'
    r'particle_growth=(?P<particle_growth>[-+0-9.eE]+)\s+'
    r'spray_mass_loss_rel=(?P<spray_mass_loss_rel>[-+0-9.eE]+)\s+'
    r'spray_x_vel_absmax=(?P<spray_x_vel_absmax>[-+0-9.eE]+)\s+'
    r'spray_temp_increase=(?P<spray_temp_increase>[-+0-9.eE]+)\s+'
    r'surface_area_ratio=(?P<surface_area_ratio>[-+0-9.eE]+)\s+'
    r'd32_max=(?P<d32_max>[-+0-9.eE]+)\s+'
    r'species_closure_rel=(?P<species_closure_rel>[-+0-9.eE]+)'
)


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, str]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {'label': label, 'path': str(path), 'sha256': sha256_file(path)}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise ReportError(f'failed to read JSON {path}: {exc}') from exc


def parse_validation(path: Path) -> dict[str, float]:
    text = path.read_text()
    match = VALIDATION_RE.search(text)
    require(match is not None, f'validation log is not PASS: {path}')
    return {key: float(value) for key, value in match.groupdict().items()}


def read_manifest(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(isinstance(data.get('cases'), list) and data['cases'], 'manifest has no cases')
    return data


def validate_case(case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    validation_log = Path(str(case.get('validation_log', '')))
    run_log = Path(str(case.get('run_log', '')))
    input_file = Path(str(case.get('input_file', '')))
    initial = Path(str(case.get('plotfile_initial', '')))
    mid = Path(str(case.get('plotfile_mid', '')))
    final = Path(str(case.get('plotfile_final', '')))
    for path, label in [
        (validation_log, 'validation_log'),
        (run_log, 'run_log'),
        (input_file, 'input_file'),
        (initial / 'Header', 'initial Header'),
        (final / 'Header', 'final Header'),
        (initial / 'particles' / 'Header', 'initial particle Header'),
        (final / 'particles' / 'Header', 'final particle Header'),
    ]:
        require(path.is_file(), f'missing {label}: {path}')
    if str(case.get('plotfile_mid', '')):
        require((mid / 'Header').is_file(), f'missing mid Header: {mid / "Header"}')
    metrics = parse_validation(validation_log)
    require(metrics['pressure_front_shift'] >= args.min_pressure_front_shift, 'pressure front shift below threshold')
    require(metrics['pressure_front_shift_cells'] >= args.min_front_shift_cells, 'pressure front shift in cells below threshold')
    require(metrics['temp_front_shift'] >= args.min_temp_front_shift, 'temperature front shift below threshold')
    require(metrics['heat_release_absmax'] >= args.min_heat_release_absmax, 'heat release below threshold')
    require(metrics['o2_consumption'] >= args.min_o2_consumption, 'O2 consumption below threshold')
    require(metrics['fuel_vapor_increase'] >= args.min_fuel_vapor_increase, 'fuel vapor response below threshold')
    require(metrics['particle_growth'] >= args.min_particle_growth, 'particle growth below threshold')
    require(metrics['spray_x_vel_absmax'] >= args.min_spray_velocity, 'spray velocity below threshold')
    require(metrics['spray_temp_increase'] >= args.min_spray_temp_increase, 'spray temperature increase below threshold')
    require(metrics['spray_mass_loss_rel'] >= args.min_spray_mass_loss_rel, 'spray mass loss below threshold')
    require(metrics['surface_area_ratio'] > 1.0, 'surface area did not grow')
    require(metrics['species_closure_rel'] <= args.max_species_closure_rel, 'species closure above threshold')
    return {**case, 'metrics': metrics}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = read_manifest(manifest_path)
    cases = [validate_case(case, args) for case in manifest['cases']]
    main_case = cases[0]
    metrics = main_case['metrics']
    summary = {
        'case_count': len(cases),
        'main_case': main_case.get('name'),
        'pressure_front_shift': metrics['pressure_front_shift'],
        'pressure_front_shift_cells': metrics['pressure_front_shift_cells'],
        'temp_front_shift': metrics['temp_front_shift'],
        'heat_release_absmax': metrics['heat_release_absmax'],
        'o2_consumption': metrics['o2_consumption'],
        'fuel_vapor_increase': metrics['fuel_vapor_increase'],
        'particle_count0': metrics['particle_count0'],
        'particle_count1': metrics['particle_count1'],
        'particle_growth_factor': metrics['particle_growth'],
        'spray_mass_loss_rel': metrics['spray_mass_loss_rel'],
        'spray_x_vel_absmax': metrics['spray_x_vel_absmax'],
        'spray_temp_increase': metrics['spray_temp_increase'],
        'surface_area_ratio': metrics['surface_area_ratio'],
        'd32_max': metrics['d32_max'],
        'species_closure_rel': metrics['species_closure_rel'],
        'clears_acd_07_reacting_spray_response_gate': True,
        'clears_acd_07_closed_gas_particle_budget_gap': False,
        'clears_acd_07_full_cellular_gas_liquid_detonation_gap': False,
        'clears_acd_07_external_reference_gap': False,
        'clears_acd_07_spray_detonation_gap': False,
    }
    quality_gates = [
        {'name': 'reacting_spray_input_contract', 'status': 'PASS', 'gap': '', 'evidence': [main_case['input_file']]},
        {'name': 'detonation_style_pressure_temperature_front', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {'name': 'stiff_reaction_heat_release_response', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {'name': 'spray_breakup_particle_growth', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {'name': 'droplet_motion_evaporation_thermal_response', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {'name': 'finite_conservative_species_closure', 'status': 'PASS', 'gap': '', 'evidence': [main_case['plotfile_final']]},
        {
            'name': 'closed_gas_particle_budget',
            'status': 'NOT_READY',
            'gap': 'The maintained case proves stable reacting spray response and gas species closure, but not a closed gas+particle mass, momentum, and total-energy budget.',
            'evidence': [main_case['validation_log']],
        },
        {
            'name': 'full_cellular_gas_liquid_detonation',
            'status': 'NOT_READY',
            'gap': 'The current 2D shock-droplet gate is detonation-style and does not certify full cellular gas-liquid detonation morphology.',
            'evidence': [main_case['validation_log']],
        },
        {
            'name': 'external_spray_detonation_reference',
            'status': 'NOT_READY',
            'gap': 'No external reacting spray detonation reference or experiment comparison is attached.',
            'evidence': [],
        },
    ]
    evidence_files = [
        evidence_entry('case_manifest', manifest_path),
        evidence_entry('runner', Path('tools/codex_run_academic_spray_detonation_validation.sh')),
        evidence_entry('validator', Path('tools/validate_academic_spray_detonation.py')),
        evidence_entry('report_writer', Path('tools/write_academic_spray_detonation_validation_report.py')),
        evidence_entry('shock_droplet_prob_cpp', Path('examples/academic/shock_droplet/prob.cpp')),
        evidence_entry('shock_droplet_prob_H', Path('examples/academic/shock_droplet/prob.H')),
    ]
    for idx, case in enumerate(cases):
        evidence_files.extend([
            evidence_entry(f'case_{idx}_input', Path(str(case['input_file']))),
            evidence_entry(f'case_{idx}_run_log', Path(str(case['run_log']))),
            evidence_entry(f'case_{idx}_validation_log', Path(str(case['validation_log']))),
            evidence_entry(f'case_{idx}_initial_plot_header', Path(str(case['plotfile_initial'])) / 'Header'),
            evidence_entry(f'case_{idx}_final_plot_header', Path(str(case['plotfile_final'])) / 'Header'),
            evidence_entry(f'case_{idx}_initial_particles_header', Path(str(case['plotfile_initial'])) / 'particles' / 'Header'),
            evidence_entry(f'case_{idx}_final_particles_header', Path(str(case['plotfile_final'])) / 'particles' / 'Header'),
        ])
        if str(case.get('plotfile_mid', '')):
            evidence_files.append(evidence_entry(f'case_{idx}_mid_plot_header', Path(str(case['plotfile_mid'])) / 'Header'))
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Reacting Spray Detonation Validation',
        'scope': 'PeleC heptane-air reacting shock-droplet gate with CVODE chemistry, spray particles, KHRT breakup, evaporation/momentum coupling, and propagating high-pressure/high-temperature front',
        'summary': summary,
        'cases': cases,
        'quality_gates': quality_gates,
        'evidence_files': evidence_files,
        'limitations': [
            'This is an in-repository 2D reacting spray shock/detonation-style gate using the simplified heptane_3sp chemistry, not an external experimental spray-detonation benchmark.',
            'The gate proves coupled reacting gas plus Euler-Lagrange spray stability and front propagation; it does not certify full cellular gas-liquid detonation morphology.',
            'The ACD-05 droplet gate remains the focused droplet-physics validation; this ACD-07 gate exercises the coupled end-to-end path.',
            'The broad ACD-07 spray/gas-liquid detonation validation gap remains open until closed gas+particle budgets, cellular morphology, and/or external reference agreement are attached.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'status mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('clears_acd_07_reacting_spray_response_gate') is True, 'ACD-07 response gate flag missing')
    require(summary.get('clears_acd_07_closed_gas_particle_budget_gap') is False, 'ACD-07 budget gap must remain open')
    require(summary.get('clears_acd_07_full_cellular_gas_liquid_detonation_gap') is False, 'ACD-07 cellular detonation gap must remain open')
    require(summary.get('clears_acd_07_external_reference_gap') is False, 'ACD-07 external reference gap must remain open')
    require(summary.get('clears_acd_07_spray_detonation_gap') is False, 'broad ACD-07 clear flag must remain false')
    require(float(summary.get('pressure_front_shift_cells', 0.0)) >= 5.0, 'pressure front shift too small')
    require(float(summary.get('heat_release_absmax', 0.0)) >= 1.0, 'heat release too small')
    require(float(summary.get('particle_growth_factor', 0.0)) >= 2.0, 'particle growth too small')
    require(float(summary.get('spray_x_vel_absmax', 0.0)) >= 100.0, 'spray velocity too small')
    require(float(summary.get('spray_temp_increase', 0.0)) >= 50.0, 'spray temperature response too small')
    require(float(summary.get('surface_area_ratio', 0.0)) > 1.0, 'surface area did not grow')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    non_pass = [g.get('name') for g in gates if isinstance(g, dict) and g.get('status') != 'PASS']
    require(
        non_pass == [
            'closed_gas_particle_budget',
            'full_cellular_gas_liquid_detonation',
            'external_spray_detonation_reference',
        ],
        f'unexpected non-PASS gates: {non_pass}',
    )
    if check_hashes:
        entries = data.get('evidence_files')
        require(isinstance(entries, list) and entries, 'evidence files missing')
        for item in entries:
            require(isinstance(item, dict), 'evidence entry not object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Academic Reacting Spray Detonation Validation',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key in [
        'main_case', 'pressure_front_shift', 'pressure_front_shift_cells',
        'temp_front_shift', 'heat_release_absmax', 'o2_consumption',
        'fuel_vapor_increase', 'particle_count0', 'particle_count1',
        'particle_growth_factor', 'spray_mass_loss_rel',
        'spray_x_vel_absmax', 'spray_temp_increase', 'surface_area_ratio',
        'species_closure_rel', 'clears_acd_07_reacting_spray_response_gate',
        'clears_acd_07_closed_gas_particle_budget_gap',
        'clears_acd_07_full_cellular_gas_liquid_detonation_gap',
        'clears_acd_07_external_reference_gap',
        'clears_acd_07_spray_detonation_gap',
    ]:
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Evidence | Gap |', '| --- | --- | --- | --- |']
    for gate in report['quality_gates']:
        evidence = '; '.join(str(x) for x in gate.get('evidence', []))
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {evidence} | {gate.get('gap') or 'none'} |")
    lines += ['', '## Cases', '', '| Case | Front shift cells | Heat release | Particles | Spray velocity |',
              '| --- | --- | --- | --- | --- |']
    for case in report['cases']:
        m = case['metrics']
        lines.append(
            f"| `{case.get('name')}` | `{m['pressure_front_shift_cells']:.8g}` | "
            f"`{m['heat_release_absmax']:.8e}` | `{int(m['particle_count0'])}->{int(m['particle_count1'])}` | "
            f"`{m['spray_x_vel_absmax']:.8e}` |"
        )
    lines += ['', '## Limitations', '']
    lines.extend(f"- {item}" for item in report['limitations'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    parser.add_argument('--min-pressure-front-shift', type=float, default=0.5)
    parser.add_argument('--min-temp-front-shift', type=float, default=0.4)
    parser.add_argument('--min-front-shift-cells', type=float, default=5.0)
    parser.add_argument('--min-heat-release-absmax', type=float, default=1.0)
    parser.add_argument('--min-o2-consumption', type=float, default=1.0e-4)
    parser.add_argument('--min-fuel-vapor-increase', type=float, default=5.0e-4)
    parser.add_argument('--min-particle-growth', type=float, default=2.0)
    parser.add_argument('--min-spray-velocity', type=float, default=100.0)
    parser.add_argument('--min-spray-temp-increase', type=float, default=50.0)
    parser.add_argument('--min-spray-mass-loss-rel', type=float, default=1.0e-5)
    parser.add_argument('--max-species-closure-rel', type=float, default=2.0e-12)
    args = parser.parse_args()

    try:
        if args.verify_json:
            path = Path(args.verify_json)
            data = load_json(path)
            validate_report_object(data, check_hashes=True)
            print(
                'academic_spray_detonation_validation VERIFY-PASS '
                f'json={path} front_cells={data["summary"].get("pressure_front_shift_cells")} '
                f'particles={data["summary"].get("particle_count0")}->{data["summary"].get("particle_count1")}'
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        write_markdown(report, out_md)
        print(
            'academic_spray_detonation_validation PASS '
            f'json={out_json} status={report["status"]} '
            f'front_cells={report["summary"].get("pressure_front_shift_cells")} '
            f'particles={report["summary"].get("particle_count0")}->{report["summary"].get("particle_count1")}'
        )
        return 0
    except ReportError as exc:
        print(f'academic_spray_detonation_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
