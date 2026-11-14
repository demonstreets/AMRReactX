#!/usr/bin/env python3
"""Write/verify the academic two-phase bubble-rise validation report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728')
DEFAULT_CASE_SUMMARY = DEFAULT_ROOT / 'bubble_rise_buoyancy_6000step_low_cfl' / 'case_summary.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_twophase_bubble_rise_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_twophase_bubble_rise_validation_report.md'
DEFAULT_LONG_WINDOW_PROBE_GATE = (
    DEFAULT_ROOT / 'long_window_probe_gate_20260729' / 'bubble_rise_long_window_probe_gate_report.json'
)
DEFAULT_INVISCID_LONG_WINDOW_REPORT = Path(
    'docs/codex_audit/evidence/academic_twophase_bubble_rise_inviscid_long_window_validation_20260729/'
    'academic_twophase_bubble_rise_inviscid_long_window_validation_report.json'
)
DEFAULT_MOL_LONG_WINDOW_REPORT = Path(
    'docs/codex_audit/evidence/academic_twophase_bubble_rise_mol_long_window_validation_20260729/'
    'academic_twophase_bubble_rise_mol_long_window_validation_report.json'
)

METRIC_RE = re.compile(r'^academic_twophase_bubble_rise_validation PASS\s+(.*)$', re.MULTILINE)


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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ReportError(f'missing JSON: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON root is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def parse_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in text.split():
        if '=' in item:
            key, value = item.split('=', 1)
            values[key] = value.rstrip(',')
    return values


def parse_validation_log(path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing validation log: {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    match = METRIC_RE.search(text)
    require(match is not None, f'validation PASS line missing in {path}')
    raw = parse_values(match.group(1))
    nx, ny = [int(item) for item in raw['grid'].split('x', 1)]
    rho_min, rho_max = [float(item) for item in raw['rho_range'].split(':', 1)]
    alpha_min, alpha_max = [float(item) for item in raw['alpha_range'].split(':', 1)]
    metrics = {
        'time0': float(raw['time0']),
        'time1': float(raw['time1']),
        'grid_nx': nx,
        'grid_ny': ny,
        'rho_min': rho_min,
        'rho_max': rho_max,
        'alpha_min': alpha_min,
        'alpha_max': alpha_max,
        'mass_rel_drift': float(raw['mass_rel_drift']),
        'adv_mass_rel_drift': float(raw['adv_mass_rel_drift']),
        'light_y0': float(raw['light_y0']),
        'light_y1': float(raw['light_y1']),
        'centroid_rise': float(raw['centroid_rise']),
        'ymom_sum': float(raw['ymom_sum']),
        'ymom_absmax': float(raw['ymom_absmax']),
    }
    require(metrics['time1'] > metrics['time0'], 'final time must advance')
    require(metrics['rho_min'] > 0.0, 'density minimum must be positive')
    require(metrics['alpha_min'] >= -0.05 and metrics['alpha_max'] <= 1.05, 'alpha is out of gate bounds')
    require(metrics['centroid_rise'] > 0.0, 'bubble centroid did not rise')
    require(metrics['ymom_sum'] > 0.0, 'integrated y momentum must be upward')
    return metrics


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case_summary_path = Path(args.case_summary)
    case = load_json(case_summary_path)
    input_file = Path(str(case['input_file']))
    build_log = Path(str(case['build_log']))
    run_log = Path(str(case['run_log']))
    validation_log = Path(str(case['validation_log']))
    initial_plot = Path(str(case['initial_plot']))
    final_plot = Path(str(case['final_plot']))
    long_window_probe_gate = Path(args.long_window_probe_gate_report)
    inviscid_long_window_report = Path(args.inviscid_long_window_report)
    inviscid_long = load_json(inviscid_long_window_report) if inviscid_long_window_report.is_file() else {}
    inviscid_long_summary = inviscid_long.get('summary') if isinstance(inviscid_long.get('summary'), dict) else {}
    mol_long_window_report = Path(args.mol_long_window_report)
    mol_long = load_json(mol_long_window_report) if mol_long_window_report.is_file() else {}
    mol_long_summary = mol_long.get('summary') if isinstance(mol_long.get('summary'), dict) else {}
    for path in (input_file, build_log, run_log, validation_log):
        require(path.is_file(), f'missing evidence file: {path}')
    run_text = run_log.read_text(encoding='utf-8', errors='replace')
    run_returncode = int(case.get('run_returncode', 1))
    validation_returncode = int(case.get('validation_returncode', 1))
    blocking_reasons: list[str] = []
    if run_returncode != 0:
        blocking_reasons.append('bubble_rise_run_failed')
    if 'AMReX' not in run_text or 'finalized' not in run_text:
        blocking_reasons.append('amrex_finalization_missing')
    if 'Unused ParmParse' in run_text:
        blocking_reasons.append('unused_parmparse_variables')
    if any(token in run_text for token in ('nan', 'NaN', 'NAN')):
        blocking_reasons.append('nan_detected')
    if any(token in run_text for token in ('SIGSEGV', 'SIGABRT', 'Abort::')):
        blocking_reasons.append('abort_or_signal_detected')
    if validation_returncode != 0:
        blocking_reasons.append('bubble_rise_validation_failed')

    metrics: dict[str, Any] = {}
    status = STATUS_NOT_READY
    if not blocking_reasons:
        for path in (initial_plot, final_plot):
            require(path.is_dir(), f'missing plotfile directory: {path}')
        metrics = parse_validation_log(validation_log)
        status = STATUS_PASS
    summary = {
        'clears_qlt_03_short_time_bubble_response_gap': status == STATUS_PASS,
        'clears_qlt_03_canonical_long_time_bubble_rise_gap': False,
        'clears_inviscid_long_window_bubble_rise_stability': inviscid_long.get('status') == 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-INVISCID-LONG-WINDOW-VALIDATION',
        'inviscid_long_window_steps': int(inviscid_long_summary.get('max_step', 0)),
        'inviscid_long_window_centroid_rise': inviscid_long_summary.get('centroid_rise'),
        'inviscid_long_window_final_time': inviscid_long_summary.get('time1'),
        'clears_mol_long_window_bubble_rise_stability': mol_long.get('status') == 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-MOL-LONG-WINDOW-VALIDATION',
        'mol_long_window_steps': int(mol_long_summary.get('max_step', 0)),
        'mol_long_window_centroid_rise': mol_long_summary.get('centroid_rise'),
        'mol_long_window_final_time': mol_long_summary.get('time1'),
        'clears_qlt_03_bubble_rise_gap': False,
        'blocking_reasons': blocking_reasons,
        **metrics,
    }
    gates = [
        {
            'name': 'run_finalized_without_failure_tokens',
            'status': 'PASS' if not any(reason in blocking_reasons for reason in (
                'bubble_rise_run_failed',
                'amrex_finalization_missing',
                'unused_parmparse_variables',
                'nan_detected',
                'abort_or_signal_detected',
            )) else 'NOT_READY',
            'gap': '' if not blocking_reasons else 'The bubble-rise run does not yet provide a clean finalization gate.',
            'evidence': [str(run_log)],
        },
        {
            'name': 'positive_finite_state',
            'status': 'PASS' if status == STATUS_PASS else 'NOT_READY',
            'gap': '' if status == STATUS_PASS else 'The validation log did not prove a positive finite final state.',
            'evidence': [str(validation_log)],
        },
        {
            'name': 'bounded_vof_alpha',
            'status': 'PASS' if status == STATUS_PASS else 'NOT_READY',
            'gap': '' if status == STATUS_PASS else 'The validation log did not prove bounded VOF alpha.',
            'evidence': [str(validation_log)],
        },
        {
            'name': 'mass_and_advected_scalar_conservation',
            'status': 'PASS' if status == STATUS_PASS else 'NOT_READY',
            'gap': '' if status == STATUS_PASS else 'The validation log did not prove conservation within tolerance.',
            'evidence': [str(validation_log)],
        },
        {
            'name': 'upward_light_phase_centroid_motion',
            'status': 'PASS' if status == STATUS_PASS else 'NOT_READY',
            'gap': '' if status == STATUS_PASS else 'The validation log did not prove measurable upward light-phase motion.',
            'evidence': [str(validation_log)],
        },
        {
            'name': 'inviscid_long_window_stability',
            'status': 'PASS' if inviscid_long.get('status') == 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-INVISCID-LONG-WINDOW-VALIDATION' else 'NOT_READY',
            'gap': '' if inviscid_long.get('status') == 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-INVISCID-LONG-WINDOW-VALIDATION' else 'The inviscid long-window bubble-rise report is missing or not passing.',
            'evidence': [str(inviscid_long_window_report)],
        },
        {
            'name': 'mol_long_window_stability',
            'status': 'PASS' if mol_long.get('status') == 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-MOL-LONG-WINDOW-VALIDATION' else 'NOT_READY',
            'gap': '' if mol_long.get('status') == 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-MOL-LONG-WINDOW-VALIDATION' else 'The MOL long-window bubble-rise report is missing or not passing.',
            'evidence': [str(mol_long_window_report)],
        },
        {
            'name': 'canonical_long_time_bubble_rise_stability',
            'status': 'NOT_READY',
            'gap': 'Formal long-window probe gate records non-finite or negative-internal-energy diagnostics; only the short-time buoyancy-response gate is cleared.',
            'evidence': [
                str(long_window_probe_gate),
            ],
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Academic Two-Phase Bubble-Rise Validation',
        'scope': (
            'PeleC two-phase VOF bubble-rise gate with a problem-specific buoyancy source: '
            'positive finite state, bounded volume fraction, conservative density/advected scalar, '
            'upward light-phase centroid motion, and clean AMReX finalization'
        ),
        'case': case,
        'summary': summary,
        'quality_gates': gates,
        'evidence_files': [
            evidence_entry('case_summary', case_summary_path),
            evidence_entry('input_file', input_file),
            evidence_entry('build_log', build_log),
            evidence_entry('run_log', run_log),
            evidence_entry('validation_log', validation_log),
            evidence_entry('runner', Path('tools/codex_run_academic_twophase_bubble_rise_validation.sh')),
            evidence_entry('validator', Path('tools/validate_academic_twophase_bubble_rise.py')),
            evidence_entry('report_writer', Path('tools/write_academic_twophase_bubble_rise_validation_report.py')),
            evidence_entry('long_window_probe_gate_report', long_window_probe_gate),
            evidence_entry('inviscid_long_window_report', inviscid_long_window_report),
            evidence_entry('mol_long_window_report', mol_long_window_report),
            evidence_entry('prob_H', Path('examples/academic/bubble_rise/prob.H')),
            evidence_entry('prob_cpp', Path('examples/academic/bubble_rise/prob.cpp')),
            evidence_entry('prob_parm_H', Path('examples/academic/bubble_rise/prob_parm.H')),
        ],
        'limitations': [
            'This is a maintained in-repository strengthened short-time, low-CFL buoyancy-response stability gate, not an external benchmark of a canonical long-time bubble-rise experiment.',
            'The 6000-step low-CFL gate proves positive finite state, conservation, bounded alpha, and a measurable upward light-phase response.',
            'Phase-consistent smooth-interface inviscid and do_mol=1 30000-step long-window gates are now attached; external canonical long-time bubble deformation remains a follow-up rather than being claimed by this report.',
            'The gate clears only the short-time buoyancy-response component of QLT-03; canonical long-time bubble-rise validation remains open.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_PASS, STATUS_NOT_READY}, 'invalid status')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    if data.get('status') == STATUS_PASS:
        require(
            summary.get('clears_qlt_03_short_time_bubble_response_gap') is True,
            'short-time bubble response clear flag missing',
        )
        require(
            summary.get('clears_qlt_03_canonical_long_time_bubble_rise_gap') is False,
            'PASS short-time report must not clear canonical long-time bubble-rise',
        )
        require(
            summary.get('clears_qlt_03_bubble_rise_gap') is False,
            'PASS short-time report must not clear the broad bubble-rise gap',
        )
        require(float(summary.get('centroid_rise', 0.0)) > 0.0, 'centroid rise must be positive')
        require(float(summary.get('ymom_sum', 0.0)) > 0.0, 'ymom_sum must be positive')
        require(float(summary.get('mass_rel_drift', 1.0)) <= 1.0e-10, 'mass drift exceeds report gate')
        require(float(summary.get('adv_mass_rel_drift', 1.0)) <= 1.0e-10, 'advected scalar drift exceeds report gate')
    else:
        require(
            summary.get('clears_qlt_03_short_time_bubble_response_gap') is False,
            'NOT_READY report must not clear short-time bubble response',
        )
        require(summary.get('clears_qlt_03_bubble_rise_gap') is False, 'NOT_READY report must not clear QLT-03 bubble-rise')
        require(summary.get('blocking_reasons'), 'NOT_READY report must list blocking reasons')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality_gates missing')
    for gate in gates:
        require(isinstance(gate, dict), 'quality gate is not an object')
        require(gate.get('status') in {'PASS', 'NOT_READY'}, f"invalid quality gate status: {gate.get('name')}")
        if data.get('status') == STATUS_PASS and gate.get('name') != 'canonical_long_time_bubble_rise_stability':
            require(gate.get('status') == 'PASS', f"quality gate not PASS: {gate.get('name')}")
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Academic Two-Phase Bubble-Rise Validation',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Key Metrics',
        '',
        f"- Clears QLT-03 short-time bubble-response gap: `{summary['clears_qlt_03_short_time_bubble_response_gap']}`",
        f"- Clears QLT-03 canonical long-time bubble-rise gap: `{summary['clears_qlt_03_canonical_long_time_bubble_rise_gap']}`",
        f"- Clears broad QLT-03 bubble-rise gap: `{summary['clears_qlt_03_bubble_rise_gap']}`",
        f"- Blocking reasons: `{summary.get('blocking_reasons', [])}`",
        f"- Time: `{summary.get('time0')}` to `{summary.get('time1')}`",
        f"- Grid: `{summary.get('grid_nx')}x{summary.get('grid_ny')}`",
        f"- Alpha range: `{summary.get('alpha_min')}` to `{summary.get('alpha_max')}`",
        f"- Mass relative drift: `{summary.get('mass_rel_drift')}`",
        f"- Advected-scalar relative drift: `{summary.get('adv_mass_rel_drift')}`",
        f"- Light centroid y: `{summary.get('light_y0')}` to `{summary.get('light_y1')}`",
        f"- Integrated y momentum: `{summary.get('ymom_sum')}`",
        '',
        '## Evidence Files',
        '',
    ]
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-summary', default=str(DEFAULT_CASE_SUMMARY))
    parser.add_argument('--long-window-probe-gate-report', default=str(DEFAULT_LONG_WINDOW_PROBE_GATE))
    parser.add_argument('--inviscid-long-window-report', default=str(DEFAULT_INVISCID_LONG_WINDOW_REPORT))
    parser.add_argument('--mol-long-window-report', default=str(DEFAULT_MOL_LONG_WINDOW_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'academic_twophase_bubble_rise_validation VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"short_time={summary['clears_qlt_03_short_time_bubble_response_gap']} "
                f"long_time={summary['clears_qlt_03_canonical_long_time_bubble_rise_gap']} "
                f"blocking={summary.get('blocking_reasons', [])}"
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
            'academic_twophase_bubble_rise_validation PASS '
            f"json={out_json} md={out_md} status={report['status']}"
        )
        return 0
    except ReportError as exc:
        print(f'academic_twophase_bubble_rise_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
