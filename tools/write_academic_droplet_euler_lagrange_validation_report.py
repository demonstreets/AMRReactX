#!/usr/bin/env python3
"""Write/verify ACD-05 academic Euler-Lagrange droplet validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-DROPLET-EULER-LAGRANGE-VALIDATION'
DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'case_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_droplet_euler_lagrange_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_droplet_euler_lagrange_validation_report.md'

VALIDATION_RE = re.compile(
    r'academic_droplet_euler_lagrange_validation PASS .*?'
    r'time=(?P<time>[-+0-9.eE]+)\s+'
    r'particles=(?P<particles0>\d+):(?P<particles1>\d+)\s+'
    r'particle_growth=(?P<particle_growth>[-+0-9.eE]+)\s+'
    r'spray_mass_loss_rel=(?P<spray_mass_loss_rel>[-+0-9.eE]+)\s+'
    r'spray_x_vel_absmax=(?P<spray_x_vel_absmax>[-+0-9.eE]+)\s+'
    r'spray_temp_max=(?P<spray_temp_max>[-+0-9.eE]+)\s+'
    r'surface_area_ratio=(?P<surface_area_ratio>[-+0-9.eE]+)\s+'
    r'd32_max=(?P<d32_max>[-+0-9.eE]+)\s+'
    r'gas_fuel_sum=(?P<gas_fuel_sum>[-+0-9.eE]+)'
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
    data = {key: float(value) for key, value in match.groupdict().items()}
    data['particle_count0'] = data.pop('particles0')
    data['particle_count1'] = data.pop('particles1')
    return data


def read_manifest(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(isinstance(data.get('cases'), list) and data['cases'], 'manifest has no cases')
    return data


def validate_case(case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    validation_log = Path(str(case.get('validation_log', '')))
    run_log = Path(str(case.get('run_log', '')))
    input_file = Path(str(case.get('input_file', '')))
    initial = Path(str(case.get('plotfile_initial', '')))
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
    metrics = parse_validation(validation_log)
    require(metrics['particle_growth'] >= args.min_particle_growth, 'particle growth below threshold')
    require(metrics['spray_mass_loss_rel'] >= args.min_mass_loss_rel, 'spray mass loss below threshold')
    require(metrics['spray_x_vel_absmax'] >= args.min_spray_velocity, 'spray velocity below threshold')
    require(metrics['surface_area_ratio'] > 1.0, 'surface area did not increase')
    require(abs(metrics['gas_fuel_sum']) <= args.max_gas_fuel_abs_sum, 'gas fuel closure drift too high')
    return {
        **case,
        'metrics': metrics,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = read_manifest(manifest_path)
    cases = [validate_case(case, args) for case in manifest['cases']]
    main_case = cases[0]
    metrics = main_case['metrics']
    summary = {
        'case_count': len(cases),
        'main_case': main_case.get('name'),
        'particle_count0': metrics['particle_count0'],
        'particle_count1': metrics['particle_count1'],
        'particle_growth_factor': metrics['particle_growth'],
        'spray_mass_loss_rel': metrics['spray_mass_loss_rel'],
        'spray_x_vel_absmax': metrics['spray_x_vel_absmax'],
        'spray_temp_max': metrics['spray_temp_max'],
        'surface_area_ratio': metrics['surface_area_ratio'],
        'd32_max': metrics['d32_max'],
        'gas_fuel_sum': metrics['gas_fuel_sum'],
        'min_particle_growth': float(args.min_particle_growth),
        'min_mass_loss_rel': float(args.min_mass_loss_rel),
        'min_spray_velocity': float(args.min_spray_velocity),
        'max_gas_fuel_abs_sum': float(args.max_gas_fuel_abs_sum),
        'clears_acd_05_response_gate': True,
        'clears_acd_05_closed_gas_particle_budget_gap': False,
        'clears_acd_05_external_reference_gap': False,
        'clears_acd_05_euler_lagrange_gap': False,
    }
    quality_gates = [
        {'name': 'spray_particle_path_enabled', 'status': 'PASS', 'gap': '', 'evidence': [main_case['input_file']]},
        {'name': 'khrt_breakup_particle_growth', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {'name': 'droplet_motion_response', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {'name': 'evaporation_heat_mass_response', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {'name': 'eulerian_spray_fields_finite', 'status': 'PASS', 'gap': '', 'evidence': [main_case['plotfile_final']]},
        {
            'name': 'closed_gas_particle_budget',
            'status': 'NOT_READY',
            'gap': 'The maintained case proves finite response and scalar closure, but does not yet compute a closed gas+particle mass, momentum, and total-energy budget.',
            'evidence': [main_case['validation_log']],
        },
        {
            'name': 'external_breakup_reference',
            'status': 'NOT_READY',
            'gap': 'No external shock-droplet breakup or evaporation reference comparison is attached.',
            'evidence': [],
        },
    ]
    evidence_files = [
        evidence_entry('case_manifest', manifest_path),
        evidence_entry('runner', Path('tools/codex_run_academic_droplet_euler_lagrange_validation.sh')),
        evidence_entry('validator', Path('tools/validate_academic_droplet_euler_lagrange.py')),
        evidence_entry('report_writer', Path('tools/write_academic_droplet_euler_lagrange_validation_report.py')),
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
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Droplet Euler-Lagrange Validation',
        'scope': 'PeleC spray-particle shock-droplet KHRT breakup, droplet motion, evaporation/thermal response, and Eulerian spray-field coupling gate',
        'summary': summary,
        'cases': cases,
        'quality_gates': quality_gates,
        'evidence_files': evidence_files,
        'limitations': [
            'This validates a maintained shock-droplet spray-particle case; it is not yet an end-to-end gas-liquid detonation.',
            'The gate proves KHRT breakup and Eulerian spray-field coupling through PeleC derived fields and particle headers, not an external experimental breakup benchmark.',
            'The D2-law unit evidence remains the maintained analytic evaporation check; this gate adds motion, breakup, and two-way-coupling evidence for ACD-05.',
            'The broad ACD-05 Euler-Lagrange validation gap remains open until a closed gas+particle mass, momentum, and total-energy budget or external reference comparison is attached.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'status mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('clears_acd_05_response_gate') is True, 'ACD-05 response gate flag missing')
    require(summary.get('clears_acd_05_closed_gas_particle_budget_gap') is False, 'ACD-05 budget gap must remain open')
    require(summary.get('clears_acd_05_external_reference_gap') is False, 'ACD-05 external reference gap must remain open')
    require(summary.get('clears_acd_05_euler_lagrange_gap') is False, 'broad ACD-05 clear flag must remain false')
    require(float(summary.get('particle_growth_factor', 0.0)) >= float(summary.get('min_particle_growth', math.inf)), 'particle growth below threshold')
    require(float(summary.get('spray_mass_loss_rel', 0.0)) >= float(summary.get('min_mass_loss_rel', math.inf)), 'spray mass loss below threshold')
    require(float(summary.get('spray_x_vel_absmax', 0.0)) >= float(summary.get('min_spray_velocity', math.inf)), 'spray velocity below threshold')
    require(float(summary.get('surface_area_ratio', 0.0)) > 1.0, 'surface area did not grow')
    require(abs(float(summary.get('gas_fuel_sum', math.inf))) <= float(summary.get('max_gas_fuel_abs_sum', 0.0)), 'gas fuel closure drift too high')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    non_pass = [g.get('name') for g in gates if isinstance(g, dict) and g.get('status') != 'PASS']
    require(non_pass == ['closed_gas_particle_budget', 'external_breakup_reference'], f'unexpected non-PASS gates: {non_pass}')
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
        '# Academic Droplet Euler-Lagrange Validation',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key in [
        'main_case', 'particle_count0', 'particle_count1',
        'particle_growth_factor', 'spray_mass_loss_rel',
        'spray_x_vel_absmax', 'spray_temp_max', 'surface_area_ratio',
        'd32_max', 'gas_fuel_sum', 'clears_acd_05_response_gate',
        'clears_acd_05_closed_gas_particle_budget_gap',
        'clears_acd_05_external_reference_gap',
        'clears_acd_05_euler_lagrange_gap',
    ]:
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Evidence | Gap |', '| --- | --- | --- | --- |']
    for gate in report['quality_gates']:
        evidence = '; '.join(str(x) for x in gate.get('evidence', []))
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {evidence} | {gate.get('gap') or 'none'} |")
    lines += ['', '## Cases', '', '| Case | Particles | Growth | Mass loss | Velocity | Surface area ratio |',
              '| --- | --- | --- | --- | --- | --- |']
    for case in report['cases']:
        m = case['metrics']
        lines.append(
            f"| `{case.get('name')}` | `{int(m['particle_count0'])}->{int(m['particle_count1'])}` | "
            f"`{m['particle_growth']:.8g}` | `{m['spray_mass_loss_rel']:.8e}` | "
            f"`{m['spray_x_vel_absmax']:.8e}` | `{m['surface_area_ratio']:.8e}` |"
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
    parser.add_argument('--min-particle-growth', type=float, default=2.0)
    parser.add_argument('--min-spray-velocity', type=float, default=100.0)
    parser.add_argument('--min-mass-loss-rel', type=float, default=1.0e-5)
    parser.add_argument('--max-gas-fuel-abs-sum', type=float, default=1.0e-12)
    args = parser.parse_args()

    try:
        if args.verify_json:
            path = Path(args.verify_json)
            data = load_json(path)
            validate_report_object(data, check_hashes=True)
            print(
                'academic_droplet_euler_lagrange_validation VERIFY-PASS '
                f'json={path} particle_growth={data["summary"].get("particle_growth_factor")} '
                f'mass_loss={data["summary"].get("spray_mass_loss_rel")}'
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
            'academic_droplet_euler_lagrange_validation PASS '
            f'json={out_json} status={report["status"]} '
            f'particle_growth={report["summary"].get("particle_growth_factor")} '
            f'mass_loss={report["summary"].get("spray_mass_loss_rel")}'
        )
        return 0
    except ReportError as exc:
        print(f'academic_droplet_euler_lagrange_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
