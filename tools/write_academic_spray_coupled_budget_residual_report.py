#!/usr/bin/env python3
"""Write/verify gas-particle coupled budget residual diagnostics for ACD-05/07."""
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
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL'
STATUS_PASS = 'PASS-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL'
DEFAULT_PREFLIGHT = Path(
    'docs/codex_audit/evidence/academic_droplet_spray_budget_preflight_20260729/'
    'academic_droplet_spray_budget_preflight_report.json'
)
DEFAULT_SPRAY_SOURCE_BUDGET = Path(
    'docs/codex_audit/evidence/academic_spray_source_budget_validation_20260729/'
    'academic_spray_source_budget_validation_report.json'
)
DEFAULT_SPRAY_DETONATION_SOURCE_BUDGET = Path(
    'docs/codex_audit/evidence/academic_spray_detonation_source_budget_validation_20260729/'
    'academic_spray_detonation_source_budget_validation_report.json'
)
DEFAULT_CLOSED_CV_BUDGET = Path(
    'docs/codex_audit/evidence/academic_spray_closed_control_volume_budget_20260729/'
    'academic_spray_closed_control_volume_budget_report.json'
)
DEFAULT_REACTING_CLOSED_CV_BUDGET = Path(
    'docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729/'
    'academic_reacting_spray_closed_control_volume_budget_report.json'
)
DEFAULT_OUTPUT_ROOT = Path('docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729')
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / 'academic_spray_coupled_budget_residual_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / 'academic_spray_coupled_budget_residual_report.md'


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
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        raise ReportError(f'failed to read JSON {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def finite(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ReportError(f'{label} is not numeric: {value!r}') from exc
    require(math.isfinite(number), f'{label} is not finite: {number!r}')
    return number


def rel(value: float, reference: float) -> float:
    return value / max(abs(reference), 1.0e-300)


def case_delta(case: dict[str, Any], section: str, key: str) -> float:
    try:
        return finite(case['deltas'][section][key]['delta'], f'{case.get("name")}.{section}.{key}.delta')
    except KeyError as exc:
        raise ReportError(f'missing delta {section}.{key} in case {case.get("name")}') from exc


def case_final(case: dict[str, Any], section: str, key: str) -> float:
    try:
        return finite(case['final'][section][key], f'{case.get("name")}.final.{section}.{key}')
    except KeyError as exc:
        raise ReportError(f'missing final {section}.{key} in case {case.get("name")}') from exc


def analyze_case(case: dict[str, Any], max_particle_plotfield_rel_diff: float) -> dict[str, Any]:
    name = str(case.get('name', 'unknown'))
    gas_mass_delta = case_delta(case, 'gas', 'mass_integral')
    particle_mass_delta = case_delta(case, 'particle_binary_budget', 'mass_sum')
    spray_mass_delta = case_delta(case, 'spray_plotfield', 'mass_raw_sum')
    particle_shed_mass_delta = case_delta(case, 'particle_binary_budget', 'shed_mass_sum')
    gas_xmom_delta = case_delta(case, 'gas', 'xmom_integral')
    particle_xmom_delta = case_delta(case, 'particle_binary_budget', 'xmom_sum')
    gas_rho_e_delta = case_delta(case, 'gas', 'rho_E_integral')
    particle_thermal_delta = case_delta(case, 'particle_binary_budget', 'thermal_mass_temperature_sum')
    final_mass = case_final(case, 'particle_binary_budget', 'mass_sum')
    plotfield_mass_rel = finite(
        case['final']['particle_to_plotfield_mass_relative_difference'],
        f'{name}.final.particle_to_plotfield_mass_relative_difference',
    )
    mass_residual = gas_mass_delta + particle_mass_delta
    spray_particle_delta_mismatch = spray_mass_delta - particle_mass_delta
    shed_vs_loss_residual = particle_shed_mass_delta + particle_mass_delta
    xmom_residual = gas_xmom_delta + particle_xmom_delta
    energy_proxy_residual = gas_rho_e_delta + particle_thermal_delta
    particle_lost_mass = -particle_mass_delta
    mass_residual_over_particle_loss = rel(mass_residual, particle_lost_mass)
    return {
        'name': name,
        'source_report': case.get('source_report'),
        'input_file': case.get('input_file'),
        'run_log': case.get('run_log'),
        'gas_mass_delta': gas_mass_delta,
        'particle_mass_delta': particle_mass_delta,
        'spray_plotfield_mass_delta': spray_mass_delta,
        'particle_shed_mass_delta': particle_shed_mass_delta,
        'gas_plus_particle_mass_residual': mass_residual,
        'gas_plus_particle_mass_residual_over_particle_loss': mass_residual_over_particle_loss,
        'spray_particle_delta_mismatch': spray_particle_delta_mismatch,
        'spray_particle_delta_mismatch_rel_final_particle_mass': rel(spray_particle_delta_mismatch, final_mass),
        'shed_mass_minus_particle_loss_residual': shed_vs_loss_residual,
        'shed_mass_minus_particle_loss_rel_particle_loss': rel(shed_vs_loss_residual, particle_lost_mass),
        'gas_xmom_delta': gas_xmom_delta,
        'particle_xmom_delta': particle_xmom_delta,
        'gas_plus_particle_xmom_residual': xmom_residual,
        'gas_rho_E_delta': gas_rho_e_delta,
        'particle_thermal_proxy_delta': particle_thermal_delta,
        'energy_proxy_residual': energy_proxy_residual,
        'particle_plotfield_mass_relative_difference_final': plotfield_mass_rel,
        'particle_plotfield_mass_consistent': plotfield_mass_rel <= max_particle_plotfield_rel_diff,
        'particle_mass_loss_positive': particle_mass_delta < 0.0,
        'gas_mass_increases': gas_mass_delta > 0.0,
        'closed_mass_budget_passes': False,
        'closed_momentum_budget_passes': False,
        'closed_energy_budget_passes': False,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    preflight_path = Path(args.preflight_report)
    spray_source_budget_path = Path(args.spray_source_budget_validation_report)
    spray_detonation_source_budget_path = Path(args.spray_detonation_source_budget_validation_report)
    closed_cv_budget_path = Path(args.closed_control_volume_budget_report)
    reacting_closed_cv_budget_path = Path(args.reacting_closed_control_volume_budget_report)
    preflight = load_json(preflight_path)
    spray_source_budget = load_json(spray_source_budget_path)
    spray_detonation_source_budget = load_json(spray_detonation_source_budget_path)
    closed_cv_budget = load_json(closed_cv_budget_path)
    reacting_closed_cv_budget = load_json(reacting_closed_cv_budget_path)
    require(
        preflight.get('status') == 'PASS-ACADEMIC-DROPLET-SPRAY-PLOTFIELD-BUDGET-PREFLIGHT',
        'preflight report is not PASS',
    )
    require(
        spray_source_budget.get('status') == 'PASS-ACADEMIC-SPRAY-SOURCE-BUDGET-VALIDATION',
        'spray source-budget validation report is not PASS',
    )
    require(
        spray_detonation_source_budget.get('status') == 'PASS-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION',
        'spray detonation source-budget validation report is not PASS',
    )
    require(
        closed_cv_budget.get('status') == 'PASS-ACADEMIC-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET',
        'closed control-volume budget report is not PASS',
    )
    require(
        reacting_closed_cv_budget.get('status') == 'PASS-ACADEMIC-REACTING-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET',
        'reacting closed control-volume budget report is not PASS',
    )
    spray_source_summary = spray_source_budget.get('summary', {})
    spray_detonation_source_summary = spray_detonation_source_budget.get('summary', {})
    closed_cv_summary = closed_cv_budget.get('summary', {})
    reacting_closed_cv_summary = reacting_closed_cv_budget.get('summary', {})
    require(isinstance(spray_source_summary, dict), 'spray source-budget summary missing')
    require(isinstance(spray_detonation_source_summary, dict), 'spray detonation source-budget summary missing')
    source_history_available = (
        spray_source_summary.get('clears_acd_05_gas_source_history_budget') is True
        and spray_source_summary.get('clears_acd_05_full_gas_particle_budget') is True
        and spray_detonation_source_summary.get('clears_acd_07_reacting_spray_detonation_budget') is True
    )
    closed_control_volume_available = (
        closed_cv_summary.get('clears_acd_05_closed_control_volume_mass_momentum_energy_budget') is True
        and reacting_closed_cv_summary.get('clears_acd_07_reacting_control_volume_total_budget') is True
    )
    cases = preflight.get('cases')
    require(isinstance(cases, list) and len(cases) >= 2, 'preflight report must contain droplet and spray cases')
    diagnostics = [analyze_case(case, args.max_particle_plotfield_rel_diff) for case in cases]
    max_particle_plotfield = max(item['particle_plotfield_mass_relative_difference_final'] for item in diagnostics)
    max_mass_residual_ratio = max(abs(item['gas_plus_particle_mass_residual_over_particle_loss']) for item in diagnostics)
    max_shed_residual_ratio = max(abs(item['shed_mass_minus_particle_loss_rel_particle_loss']) for item in diagnostics)
    all_particle_plotfield_consistent = all(item['particle_plotfield_mass_consistent'] for item in diagnostics)
    all_signs_consistent = all(item['particle_mass_loss_positive'] and item['gas_mass_increases'] for item in diagnostics)
    summary = {
        'case_count': len(diagnostics),
        'cases': [item['name'] for item in diagnostics],
        'max_particle_plotfield_mass_relative_difference': max_particle_plotfield,
        'max_gas_plus_particle_mass_residual_over_particle_loss': max_mass_residual_ratio,
        'max_shed_mass_residual_over_particle_loss': max_shed_residual_ratio,
        'particle_plotfield_mass_consistency_ready': all_particle_plotfield_consistent,
        'mass_transfer_signs_consistent': all_signs_consistent,
        'source_history_accounting_available': source_history_available,
        'spray_source_budget_status': spray_source_budget.get('status'),
        'spray_source_budget_particle_source_relative_mismatch': spray_source_summary.get(
            'particle_source_relative_mismatch'
        ),
        'spray_source_budget_gas_mass_source_relative_error': spray_source_summary.get(
            'gas_mass_source_relative_error'
        ),
        'spray_source_budget_fuel_source_relative_error': spray_source_summary.get(
            'fuel_source_relative_error'
        ),
        'spray_source_budget_energy_source_relative_error': spray_source_summary.get(
            'energy_source_relative_error'
        ),
        'spray_detonation_source_budget_status': spray_detonation_source_budget.get('status'),
        'spray_detonation_source_budget_particle_source_relative_mismatch': spray_detonation_source_summary.get(
            'particle_source_relative_mismatch'
        ),
        'spray_detonation_source_budget_heat_release_absmax': spray_detonation_source_summary.get(
            'heatRelease_absmax'
        ),
        'spray_detonation_source_budget_pressure_front_shift_cells': spray_detonation_source_summary.get(
            'pressure_front_shift_cells'
        ),
        'closed_control_volume_available': closed_control_volume_available,
        'closed_control_volume_budget_status': closed_cv_budget.get('status'),
        'reacting_closed_control_volume_budget_status': reacting_closed_cv_budget.get('status'),
        'closed_control_volume_total_mass_relative_error': closed_cv_summary.get('relative_errors', {}).get('total_mass'),
        'closed_control_volume_total_xmom_relative_error': closed_cv_summary.get('relative_errors', {}).get('total_xmom'),
        'reacting_closed_control_volume_total_mass_relative_error': reacting_closed_cv_summary.get('relative_errors', {}).get('total_mass'),
        'reacting_closed_control_volume_total_xmom_relative_error': reacting_closed_cv_summary.get('relative_errors', {}).get('total_xmom'),
        'clears_acd_05_coupled_budget_gap': closed_control_volume_available,
        'clears_acd_07_coupled_budget_gap': closed_control_volume_available,
        'clears_full_closed_gas_particle_budget_gap': closed_control_volume_available,
    }
    gates = [
        {
            'name': 'particle_binary_to_spray_plotfield_mass_consistency',
            'status': 'PASS' if all_particle_plotfield_consistent else 'FAIL',
            'evidence': str(preflight_path),
            'gap': '' if all_particle_plotfield_consistent else 'particle binary mass and spray_mass plotfield disagree',
        },
        {
            'name': 'mass_transfer_direction_sanity',
            'status': 'PASS' if all_signs_consistent else 'FAIL',
            'evidence': str(preflight_path),
            'gap': '' if all_signs_consistent else 'particle mass loss or gas mass response has unexpected sign',
        },
        {
            'name': 'closed_control_volume_case',
            'status': 'PASS' if closed_control_volume_available else 'NOT_READY',
            'evidence': [str(closed_cv_budget_path), str(reacting_closed_cv_budget_path)],
            'gap': '' if closed_control_volume_available else 'Missing PASS closed control-volume budget reports.',
        },
        {
            'name': 'source_history_accounting',
            'status': 'PASS' if source_history_available else 'FAIL',
            'evidence': [str(spray_source_budget_path), str(spray_detonation_source_budget_path)],
            'gap': '' if source_history_available else 'Maintained spray source-history evidence is incomplete.',
        },
        {
            'name': 'gas_particle_mass_momentum_energy_closure',
            'status': 'PASS' if closed_control_volume_available else 'NOT_READY',
            'evidence': [str(closed_cv_budget_path), str(reacting_closed_cv_budget_path), str(preflight_path)],
            'gap': '' if closed_control_volume_available else 'Closed gas+particle mass/momentum/energy budget reports are incomplete.',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS if closed_control_volume_available else STATUS_NOT_READY,
        'title': 'Academic Spray Coupled Budget Residual Diagnostics',
        'scope': 'Quantify gas-particle coupled mass/momentum/energy residuals from maintained droplet and reacting spray plotfile evidence while linking dedicated source-history budget evidence',
        'preflight_report': str(preflight_path),
        'summary': summary,
        'cases': diagnostics,
        'quality_gates': gates,
        'evidence_files': [
            evidence_entry('droplet_spray_budget_preflight_report', preflight_path),
            evidence_entry('spray_source_budget_validation_report', spray_source_budget_path),
            evidence_entry('spray_detonation_source_budget_validation_report', spray_detonation_source_budget_path),
            evidence_entry('closed_control_volume_budget_report', closed_cv_budget_path),
            evidence_entry('reacting_closed_control_volume_budget_report', reacting_closed_cv_budget_path),
            evidence_entry('report_writer', Path('tools/write_academic_spray_coupled_budget_residual_report.py')),
        ],
        'limitations': [
            'Endpoint gas+particle residuals from response-oriented droplet/spray cases are retained as diagnostics and are not used as closure evidence.',
            'Closed-control-volume credit is carried by the dedicated nonreacting and reacting periodic budget reports consumed by this rollup.',
            'This rollup closes coupled-budget accounting, but it is not a full cellular gas-liquid detonation morphology/reference gate.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_PASS, STATUS_NOT_READY}, 'status mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('particle_plotfield_mass_consistency_ready') is True, 'particle/plotfield mass consistency not ready')
    require(summary.get('mass_transfer_signs_consistent') is True, 'mass-transfer sign sanity failed')
    require(summary.get('source_history_accounting_available') is True, 'source-history accounting evidence must be linked')
    require(
        summary.get('spray_source_budget_status') == 'PASS-ACADEMIC-SPRAY-SOURCE-BUDGET-VALIDATION',
        'invalid spray source-budget status',
    )
    require(
        summary.get('spray_detonation_source_budget_status')
        == 'PASS-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION',
        'invalid spray detonation source-budget status',
    )
    require(
        float(summary.get('spray_source_budget_particle_source_relative_mismatch', 1.0)) <= 1.0e-3,
        'spray source-budget particle/source mismatch too large',
    )
    require(
        float(summary.get('spray_source_budget_gas_mass_source_relative_error', 1.0)) <= 1.0e-3,
        'spray source-budget gas mass source error too large',
    )
    require(
        float(summary.get('spray_source_budget_fuel_source_relative_error', 1.0)) <= 1.0e-3,
        'spray source-budget fuel source error too large',
    )
    require(
        float(summary.get('spray_source_budget_energy_source_relative_error', 1.0)) <= 1.0e-3,
        'spray source-budget energy source error too large',
    )
    require(
        float(summary.get('spray_detonation_source_budget_particle_source_relative_mismatch', 1.0)) <= 5.0e-3,
        'spray detonation source-budget particle/source mismatch too large',
    )
    require(
        float(summary.get('spray_detonation_source_budget_heat_release_absmax', 0.0)) > 0.0,
        'spray detonation source-budget heat release must be nonzero',
    )
    require(
        float(summary.get('spray_detonation_source_budget_pressure_front_shift_cells', 0.0)) > 0.0,
        'spray detonation source-budget front must move',
    )
    if data.get('status') == STATUS_PASS:
        require(summary.get('closed_control_volume_available') is True, 'closed control-volume case must be available')
        require(summary.get('clears_acd_05_coupled_budget_gap') is True, 'must clear ACD-05 coupled budget')
        require(summary.get('clears_acd_07_coupled_budget_gap') is True, 'must clear ACD-07 coupled budget')
        require(summary.get('clears_full_closed_gas_particle_budget_gap') is True, 'must clear full coupled budget')
        require(summary.get('closed_control_volume_budget_status') == 'PASS-ACADEMIC-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET', 'invalid closed CV status')
        require(summary.get('reacting_closed_control_volume_budget_status') == 'PASS-ACADEMIC-REACTING-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET', 'invalid reacting closed CV status')
    else:
        require(summary.get('closed_control_volume_available') is False, 'NOT_READY report must not mark closed control-volume available')
        require(summary.get('clears_full_closed_gas_particle_budget_gap') is False, 'NOT_READY report must not clear full coupled budget')
    require(float(summary.get('max_particle_plotfield_mass_relative_difference', 1.0)) <= 1.0e-12, 'particle/plotfield mass mismatch too large')
    require(float(summary.get('max_gas_plus_particle_mass_residual_over_particle_loss', 0.0)) > 1.0, 'diagnostic endpoint residual unexpectedly looks closed; check response-case diagnostics')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    non_pass = [g.get('name') for g in gates if isinstance(g, dict) and g.get('status') != 'PASS']
    if data.get('status') == STATUS_PASS:
        require(non_pass == [], f'unexpected non-PASS gates: {non_pass}')
    else:
        require(
            non_pass == ['closed_control_volume_case', 'gas_particle_mass_momentum_energy_closure'],
            f'unexpected non-PASS gates: {non_pass}',
        )
    cases = data.get('cases')
    require(isinstance(cases, list) and len(cases) >= 2, 'case diagnostics missing')
    for case in cases:
        require(isinstance(case, dict), 'case diagnostic is not an object')
        require(case.get('particle_plotfield_mass_consistent') is True, f"particle plotfield mismatch: {case.get('name')}")
        require(case.get('closed_mass_budget_passes') is False, f"case must not pass mass budget: {case.get('name')}")
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
        '# Academic Spray Coupled Budget Residual Diagnostics',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key in [
        'case_count',
        'max_particle_plotfield_mass_relative_difference',
        'max_gas_plus_particle_mass_residual_over_particle_loss',
        'max_shed_mass_residual_over_particle_loss',
        'particle_plotfield_mass_consistency_ready',
        'mass_transfer_signs_consistent',
        'source_history_accounting_available',
        'closed_control_volume_available',
        'clears_acd_05_coupled_budget_gap',
        'clears_acd_07_coupled_budget_gap',
    ]:
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines += ['', '## Cases', '', '| Case | gas+particle mass residual / particle loss | particle/plotfield mass rel diff |', '| --- | ---: | ---: |']
    for case in report['cases']:
        lines.append(
            f"| `{case['name']}` | `{case['gas_plus_particle_mass_residual_over_particle_loss']}` | "
            f"`{case['particle_plotfield_mass_relative_difference_final']}` |"
        )
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for gate in report['quality_gates']:
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {gate.get('gap') or 'none'} |")
    lines += ['', '## Limitations', '']
    lines.extend(f"- {item}" for item in report['limitations'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight-report', default=str(DEFAULT_PREFLIGHT))
    parser.add_argument('--spray-source-budget-validation-report', default=str(DEFAULT_SPRAY_SOURCE_BUDGET))
    parser.add_argument('--spray-detonation-source-budget-validation-report', default=str(DEFAULT_SPRAY_DETONATION_SOURCE_BUDGET))
    parser.add_argument('--closed-control-volume-budget-report', default=str(DEFAULT_CLOSED_CV_BUDGET))
    parser.add_argument('--reacting-closed-control-volume-budget-report', default=str(DEFAULT_REACTING_CLOSED_CV_BUDGET))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    parser.add_argument('--max-particle-plotfield-rel-diff', type=float, default=1.0e-12)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report_object(report, check_hashes=True)
            print(
                'academic_spray_coupled_budget_residual VERIFY-PASS '
                f'json={args.verify_json} status={report["status"]}'
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
            'academic_spray_coupled_budget_residual PASS '
            f'json={out_json} status={report["status"]}'
        )
        return 0
    except ReportError as exc:
        print(f'academic_spray_coupled_budget_residual FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
