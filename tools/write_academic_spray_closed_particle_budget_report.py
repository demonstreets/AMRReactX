#!/usr/bin/env python3
"""Write/verify closed fixed-particle spray budget validation report."""
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from write_academic_droplet_spray_budget_preflight_report import (  # noqa: E402
    read_particle_binary_budget,
)

SCHEMA_VERSION = 1
STATUS_PASS = 'PASS-ACADEMIC-SPRAY-CLOSED-PARTICLE-BUDGET'
DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'case_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_spray_closed_particle_budget_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_spray_closed_particle_budget_report.md'

VALIDATION_RE = re.compile(
    r'academic_spray_closed_particle_budget PASS .*?'
    r'particles=(?P<particles0>\d+)->(?P<particles1>\d+)\s+'
    r'mass_rel_drift=(?P<mass_rel_drift>[-+0-9.eE]+)\s+'
    r'diam_rel_drift=(?P<diam_rel_drift>[-+0-9.eE]+)\s+'
    r'xcoord_abs_drift=(?P<xcoord_abs_drift>[-+0-9.eE]+)\s+'
    r'ycoord_abs_drift=(?P<ycoord_abs_drift>[-+0-9.eE]+)\s+'
    r'thermal_rel_drift=(?P<thermal_rel_drift>[-+0-9.eE]+)\s+'
    r'xmom_rel_observed=(?P<xmom_rel_observed>[-+0-9.eE]+)\s+'
    r'ymom_abs_observed=(?P<ymom_abs_observed>[-+0-9.eE]+)\s+'
    r'mass=(?P<mass>[-+0-9.eE]+)\s+'
    r'xmom_observed=(?P<xmom_observed>[-+0-9.eE]+)\s+'
    r'kinetic_observed=(?P<kinetic_observed>[-+0-9.eE]+)\s+'
    r'mass_model=(?P<mass_model>\S+)'
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


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {'label': label, 'path': str(path), 'sha256': sha256_file(path), 'size_bytes': path.stat().st_size}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise ReportError(f'failed to read JSON {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def parse_validation(path: Path) -> dict[str, float]:
    text = path.read_text()
    match = VALIDATION_RE.search(text)
    require(match is not None, f'validation log is not PASS: {path}')
    groups = match.groupdict()
    data = {key: float(value) for key, value in groups.items() if key != 'mass_model'}
    data['mass_model'] = groups['mass_model']
    data['particle_count0'] = data.pop('particles0')
    data['particle_count1'] = data.pop('particles1')
    return data


def read_manifest(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(isinstance(data.get('cases'), list) and data['cases'], 'manifest has no cases')
    return data


def validate_case(case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    input_file = Path(str(case.get('input_file', '')))
    run_log = Path(str(case.get('run_log', '')))
    validation_log = Path(str(case.get('validation_log', '')))
    initial = Path(str(case.get('plotfile_initial', '')))
    final = Path(str(case.get('plotfile_final', '')))
    for path, label in [
        (input_file, 'input_file'),
        (run_log, 'run_log'),
        (validation_log, 'validation_log'),
        (initial / 'particles' / 'Header', 'initial particle Header'),
        (final / 'particles' / 'Header', 'final particle Header'),
    ]:
        require(path.is_file(), f'missing {label}: {path}')
    metrics = parse_validation(validation_log)
    b0 = read_particle_binary_budget(initial, input_file)
    b1 = read_particle_binary_budget(final, input_file)
    require(b0['particle_count'] == b1['particle_count'], 'particle count drifted')
    require(metrics['mass_rel_drift'] <= args.max_mass_rel_drift, 'mass drift above threshold')
    require(metrics['diam_rel_drift'] <= args.max_diameter_rel_drift, 'diameter drift above threshold')
    require(metrics['xcoord_abs_drift'] <= args.max_coordinate_abs_drift, 'x coordinate drift above threshold')
    require(metrics['ycoord_abs_drift'] <= args.max_coordinate_abs_drift, 'y coordinate drift above threshold')
    require(metrics['thermal_rel_drift'] <= args.max_temperature_rel_drift, 'thermal proxy drift above threshold')
    require(abs(float(b1['mass_sum']) - metrics['mass']) / max(abs(metrics['mass']), 1.0e-300) <= 1.0e-11, 'reported mass mismatch')
    return {**case, 'metrics': metrics, 'initial_particle_budget': b0, 'final_particle_budget': b1}


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
        'mass_model': metrics['mass_model'],
        'mass_rel_drift': metrics['mass_rel_drift'],
        'diam_rel_drift': metrics['diam_rel_drift'],
        'xcoord_abs_drift': metrics['xcoord_abs_drift'],
        'ycoord_abs_drift': metrics['ycoord_abs_drift'],
        'thermal_rel_drift': metrics['thermal_rel_drift'],
        'xmom_rel_observed': metrics['xmom_rel_observed'],
        'ymom_abs_observed': metrics['ymom_abs_observed'],
        'mass': metrics['mass'],
        'xmom_observed': metrics['xmom_observed'],
        'kinetic_observed': metrics['kinetic_observed'],
        'clears_acd_05_closed_fixed_particle_budget_subgap': True,
        'clears_acd_05_full_gas_particle_budget_gap': False,
        'clears_acd_07_full_reacting_spray_budget_gap': False,
    }
    quality_gates = [
        {'name': 'closed_fixed_particle_input_contract', 'status': 'PASS', 'gap': '', 'evidence': [main_case['input_file']]},
        {'name': 'particle_binary_budget_parser', 'status': 'PASS', 'gap': '', 'evidence': [main_case['plotfile_final']]},
        {'name': 'fixed_particle_mass_geometry_thermal_budget', 'status': 'PASS', 'gap': '', 'evidence': [main_case['validation_log']]},
        {
            'name': 'fixed_particle_velocity_momentum_budget',
            'status': 'OBSERVED_ONLY',
            'gap': 'The spray_test fixed_parts configuration resets particle velocity, so particle momentum is reported as an observation rather than a conservation gate.',
            'evidence': [main_case['validation_log']],
        },
        {
            'name': 'full_gas_particle_budget_with_coupling',
            'status': 'NOT_READY',
            'gap': 'This closed fixed-particle case proves particle binary budget closure, but it does not exercise evaporating/reacting gas-particle source-term closure.',
            'evidence': [main_case['validation_log']],
        },
    ]
    evidence_files = [
        evidence_entry('case_manifest', manifest_path),
        evidence_entry('runner', Path('tools/codex_run_academic_spray_closed_particle_budget.sh')),
        evidence_entry('validator', Path('tools/validate_academic_spray_closed_particle_budget.py')),
        evidence_entry('report_writer', Path('tools/write_academic_spray_closed_particle_budget_report.py')),
        evidence_entry('particle_budget_parser', Path('tools/write_academic_droplet_spray_budget_preflight_report.py')),
    ]
    for idx, case in enumerate(cases):
        evidence_files.extend([
            evidence_entry(f'case_{idx}_input', Path(str(case['input_file']))),
            evidence_entry(f'case_{idx}_run_log', Path(str(case['run_log']))),
            evidence_entry(f'case_{idx}_validation_log', Path(str(case['validation_log']))),
            evidence_entry(f'case_{idx}_initial_particles_header', Path(str(case['plotfile_initial'])) / 'particles' / 'Header'),
            evidence_entry(f'case_{idx}_final_particles_header', Path(str(case['plotfile_final'])) / 'particles' / 'Header'),
        ])
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Spray Closed Particle Budget',
        'scope': 'Periodic fixed-particle spray_test case validating native AMReX particle DATA particle count, parcel-mass proxy, geometry, diameter, and thermal-proxy invariance',
        'summary': summary,
        'cases': cases,
        'quality_gates': quality_gates,
        'evidence_files': evidence_files,
        'limitations': [
            'This is a closed fixed-particle budget sanity gate and does not replace evaporating/reacting gas-particle source-term closure.',
            'The spray_test fixture writes zero number_density, so parcel mass uses a documented unit-number-density fallback from liquid density and diameter.',
            'Particle velocity/momentum is observed only because fixed_parts resets particle velocity in this case.',
            'ACD-05 full credit still needs external breakup/reference validation or a coupled gas-particle budget including source histories.',
            'ACD-07 full credit still needs reacting spray/gas-liquid detonation morphology and closed coupled budgets.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'status mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('clears_acd_05_closed_fixed_particle_budget_subgap') is True, 'closed fixed-particle budget did not clear')
    require(summary.get('clears_acd_05_full_gas_particle_budget_gap') is False, 'must not clear full ACD-05 gas-particle budget')
    require(summary.get('clears_acd_07_full_reacting_spray_budget_gap') is False, 'must not clear ACD-07 reacting spray budget')
    for key in ('mass_rel_drift', 'diam_rel_drift', 'xcoord_abs_drift', 'ycoord_abs_drift', 'thermal_rel_drift'):
        require(float(summary.get(key, math.inf)) <= 1.0e-14, f'{key} above threshold')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    non_pass = [g.get('name') for g in gates if isinstance(g, dict) and g.get('status') != 'PASS']
    require(
        non_pass == ['fixed_particle_velocity_momentum_budget', 'full_gas_particle_budget_with_coupling'],
        f'unexpected non-PASS gates: {non_pass}',
    )
    if check_hashes:
        entries = data.get('evidence_files')
        require(isinstance(entries, list) and entries, 'evidence files missing')
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Academic Spray Closed Particle Budget',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key in [
        'main_case', 'particle_count0', 'particle_count1', 'mass_model', 'mass_rel_drift',
        'diam_rel_drift', 'xcoord_abs_drift', 'ycoord_abs_drift', 'thermal_rel_drift',
        'xmom_rel_observed', 'ymom_abs_observed', 'mass', 'xmom_observed',
        'kinetic_observed', 'clears_acd_05_closed_fixed_particle_budget_subgap',
        'clears_acd_05_full_gas_particle_budget_gap',
        'clears_acd_07_full_reacting_spray_budget_gap',
    ]:
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for gate in report['quality_gates']:
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {gate.get('gap') or 'none'} |")
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
    parser.add_argument('--max-mass-rel-drift', type=float, default=1.0e-14)
    parser.add_argument('--max-diameter-rel-drift', type=float, default=1.0e-14)
    parser.add_argument('--max-coordinate-abs-drift', type=float, default=1.0e-14)
    parser.add_argument('--max-temperature-rel-drift', type=float, default=1.0e-14)
    args = parser.parse_args()

    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'academic_spray_closed_particle_budget VERIFY-PASS '
                f'json={args.verify_json} mass_rel_drift={data["summary"].get("mass_rel_drift")}'
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
            'academic_spray_closed_particle_budget PASS '
            f'json={out_json} mass_rel_drift={report["summary"].get("mass_rel_drift")}'
        )
        return 0
    except ReportError as exc:
        print(f'academic_spray_closed_particle_budget FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
