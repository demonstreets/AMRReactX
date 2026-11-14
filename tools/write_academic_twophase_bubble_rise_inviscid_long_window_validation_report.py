#!/usr/bin/env python3
"""Write/verify inviscid long-window bubble-rise validation evidence."""
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
STATUS_PASS = 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-INVISCID-LONG-WINDOW-VALIDATION'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-TWOPHASE-BUBBLE-RISE-INVISCID-LONG-WINDOW-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_twophase_bubble_rise_inviscid_long_window_validation_20260729')
DEFAULT_CASE_SUMMARY = DEFAULT_ROOT / 'bubble_rise_buoyancy_inviscid_30000step_smooth_interface' / 'case_summary.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_twophase_bubble_rise_inviscid_long_window_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_twophase_bubble_rise_inviscid_long_window_validation_report.md'

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


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ReportError(f'missing JSON: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON root is not an object: {path}')
    return data


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
    return {
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


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case_summary_path = Path(args.case_summary)
    case = load_json(case_summary_path)
    input_file = Path(str(case['input_file']))
    build_log = Path(str(case['build_log']))
    run_log = Path(str(case['run_log']))
    validation_log = Path(str(case['validation_log']))
    initial_plot = Path(str(case['initial_plot']))
    final_plot = Path(str(case['final_plot']))

    for path in (input_file, build_log, run_log, validation_log):
        require(path.is_file(), f'missing evidence file: {path}')
    run_text = run_log.read_text(encoding='utf-8', errors='replace')
    run_returncode = int(case.get('run_returncode', 1))
    validation_returncode = int(case.get('validation_returncode', 1))
    blocking_reasons: list[str] = []
    if run_returncode != 0:
        blocking_reasons.append('bubble_rise_inviscid_long_run_failed')
    if 'AMReX' not in run_text or 'finalized' not in run_text:
        blocking_reasons.append('amrex_finalization_missing')
    if 'Unused ParmParse' in run_text:
        blocking_reasons.append('unused_parmparse_variables')
    if any(token in run_text for token in ('nan', 'NaN', 'NAN')):
        blocking_reasons.append('nan_detected')
    if any(token in run_text for token in ('SIGSEGV', 'SIGABRT', 'Abort::')):
        blocking_reasons.append('abort_or_signal_detected')
    if validation_returncode != 0:
        blocking_reasons.append('bubble_rise_inviscid_long_validation_failed')

    metrics: dict[str, Any] = {}
    status = STATUS_NOT_READY
    if not blocking_reasons:
        require(initial_plot.is_dir(), f'missing initial plotfile directory: {initial_plot}')
        require(final_plot.is_dir(), f'missing final plotfile directory: {final_plot}')
        metrics = parse_validation_log(validation_log)
        status = STATUS_PASS

    summary = {
        'clears_inviscid_long_window_bubble_rise_stability': status == STATUS_PASS,
        'clears_qlt_03_short_time_bubble_response_gap': False,
        'clears_qlt_03_canonical_viscous_long_time_bubble_rise_gap': False,
        'clears_qlt_03_bubble_rise_gap': False,
        'blocking_reasons': blocking_reasons,
        'max_step': int(case.get('max_step', 0)),
        'cfl': float(case.get('cfl', 0.0)),
        'do_mol': int(case.get('do_mol', 1)),
        'p0': float(case.get('p0', 0.0)),
        'interface_width': float(case.get('interface_width', 0.0)),
        'buoyancy_accel': float(case.get('buoyancy_accel', 0.0)),
        **metrics,
    }
    gates = [
        {
            'name': 'run_finalized_without_failure_tokens',
            'status': 'PASS' if not any(reason in blocking_reasons for reason in (
                'bubble_rise_inviscid_long_run_failed',
                'amrex_finalization_missing',
                'unused_parmparse_variables',
                'nan_detected',
                'abort_or_signal_detected',
            )) else 'NOT_READY',
            'gap': '' if not blocking_reasons else 'The inviscid long-window run did not finalize cleanly.',
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
            'name': 'scope_limited_to_inviscid_long_window',
            'status': 'PASS',
            'gap': '',
            'evidence': [str(input_file)],
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Academic Two-Phase Bubble-Rise Inviscid Long-Window Validation',
        'scope': (
            'PeleC two-phase VOF bubble-rise long-window stability gate with problem-specific '
            'buoyancy source and molecular transport disabled and a smooth phase-consistent initial interface; this proves extended positive, '
            'finite, conservative inviscid source-coupled behavior but not canonical viscous '
            'bubble-rise validation.'
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
            evidence_entry('runner', Path('tools/codex_run_academic_twophase_bubble_rise_inviscid_long_window_validation.sh')),
            evidence_entry('validator', Path('tools/validate_academic_twophase_bubble_rise.py')),
            evidence_entry('report_writer', Path('tools/write_academic_twophase_bubble_rise_inviscid_long_window_validation_report.py')),
            evidence_entry('prob_H', Path('examples/academic/bubble_rise/prob.H')),
            evidence_entry('prob_cpp', Path('examples/academic/bubble_rise/prob.cpp')),
            evidence_entry('prob_parm_H', Path('examples/academic/bubble_rise/prob_parm.H')),
        ],
        'limitations': [
            'This evidence does not clear the canonical viscous long-time bubble-rise gap because molecular transport is disabled.',
            'The maintained viscous 6000-step short-time gate and the formal long-window NOT_READY probe remain separate evidence.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'status mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('clears_inviscid_long_window_bubble_rise_stability') is True, 'inviscid long-window stability not cleared')
    require(summary.get('clears_qlt_03_canonical_viscous_long_time_bubble_rise_gap') is False, 'must not clear viscous canonical long-time gap')
    require(summary.get('clears_qlt_03_bubble_rise_gap') is False, 'must not clear broad QLT-03 bubble-rise gap')
    require(summary.get('blocking_reasons') == [], 'blocking reasons must be empty')
    require(int(summary.get('max_step', 0)) >= 30000, 'max_step below long-window threshold')
    require(int(summary.get('do_mol', 1)) == 0, 'inviscid validation must have do_mol=0')
    require(float(summary.get('p0', -1.0)) == 1.0, 'inviscid long-window validation must declare p0=1.0')
    require(float(summary.get('interface_width', 0.0)) >= 0.0125, 'interface width below smooth-interface gate')
    require(float(summary.get('time1', 0.0)) >= 1.5e-4, 'final time below long-window threshold')
    require(float(summary.get('rho_min', 0.0)) > 0.0, 'rho_min not positive')
    require(float(summary.get('alpha_min', -1.0)) >= -5.0e-2, 'alpha_min below tolerance')
    require(float(summary.get('alpha_max', 2.0)) <= 1.05, 'alpha_max above tolerance')
    require(float(summary.get('mass_rel_drift', 1.0)) <= 1.0e-10, 'mass drift too large')
    require(float(summary.get('adv_mass_rel_drift', 1.0)) <= 1.0e-10, 'advected mass drift too large')
    require(float(summary.get('centroid_rise', 0.0)) >= 2.0e-10, 'centroid rise too small')
    require(float(summary.get('ymom_sum', 0.0)) > 0.0, 'final y momentum is not upward')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality_gates missing')
    failed = [gate.get('name') for gate in gates if isinstance(gate, dict) and gate.get('status') != 'PASS']
    require(not failed, f'non-PASS gates: {failed}')
    evidence = data.get('evidence_files')
    require(isinstance(evidence, list) and evidence, 'evidence_files missing')
    if check_hashes:
        for item in evidence:
            require(isinstance(item, dict), 'invalid evidence entry')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(item.get('sha256') == sha256_file(path), f'evidence hash mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Academic Two-Phase Bubble-Rise Inviscid Long-Window Validation',
        '',
        f"- Status: `{report['status']}`",
        f"- Max step: `{summary.get('max_step')}`",
        f"- Final time: `{summary.get('time1')}`",
        f"- Centroid rise: `{summary.get('centroid_rise')}`",
        f"- Mass relative drift: `{summary.get('mass_rel_drift')}`",
        f"- Advected mass relative drift: `{summary.get('adv_mass_rel_drift')}`",
        f"- do_mol: `{summary.get('do_mol')}`",
        f"- p0: `{summary.get('p0')}`",
        '',
        '## Scope',
        '',
        report['scope'],
        '',
        '## Gates',
        '',
        '| Gate | Status |',
        '| --- | --- |',
    ]
    for gate in report['quality_gates']:
        lines.append(f"| `{gate['name']}` | `{gate['status']}` |")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-summary', default=str(DEFAULT_CASE_SUMMARY))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args()
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'academic_twophase_bubble_rise_inviscid_long_window_validation VERIFY-PASS '
                f'json={args.verify_json} status={data["status"]}'
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, Path(args.output_md))
        print(
            'academic_twophase_bubble_rise_inviscid_long_window_validation PASS '
            f'json={out_json} status={report["status"]}'
        )
        return 0
    except ReportError as exc:
        print(f'academic_twophase_bubble_rise_inviscid_long_window_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
