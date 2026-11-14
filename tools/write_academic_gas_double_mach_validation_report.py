#!/usr/bin/env python3
"""Write/verify the academic gas Double-Mach reflection validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728')
DEFAULT_CASE_SUMMARY = DEFAULT_ROOT / 'double_mach_reflection_8step' / 'case_summary.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_gas_double_mach_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_gas_double_mach_validation_report.md'

METRIC_RE = re.compile(r'^double_mach_plotfile_validation PASS\s+(.*)$', re.MULTILINE)


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


def parse_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in text.split():
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        values[key] = value.rstrip(',')
    return values


def parse_range(value: str) -> tuple[float, float]:
    left, right = value.split(':', 1)
    return float(left), float(right)


def parse_post_state(value: str) -> dict[str, float]:
    state: dict[str, float] = {}
    for item in value.split(','):
        key, raw = item.split(':', 1)
        state[key] = float(raw)
    return state


def parse_validation_log(path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing validation log: {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    match = METRIC_RE.search(text)
    require(match is not None, f'validation PASS line missing in {path}')
    raw = parse_key_values(match.group(1))
    require(raw.get('grid'), 'missing grid metric')
    nx, ny = [int(item) for item in raw['grid'].split('x', 1)]
    rho_min, rho_max = parse_range(raw['rho_range'])
    p_min, p_max = parse_range(raw['p_range'])
    metrics = {
        'time': float(raw['time']),
        'grid_nx': nx,
        'grid_ny': ny,
        'rho_min': rho_min,
        'rho_max': rho_max,
        'pressure_min': p_min,
        'pressure_max': p_max,
        'post_state': parse_post_state(raw['post']),
        'pre_state': parse_post_state(raw['pre']),
        'front_x': float(raw['front_x']),
        'min_expected_front': float(raw['min_expected_front']),
    }
    require(metrics['time'] > 0.0, 'time must be positive')
    require(metrics['grid_nx'] >= 64 and metrics['grid_ny'] >= 16, 'grid is unexpectedly small')
    require(metrics['rho_min'] > 0.0 and metrics['pressure_min'] > 0.0, 'nonphysical minima')
    require(metrics['front_x'] >= metrics['min_expected_front'], 'front did not meet minimum advancement')
    return metrics


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case_summary_path = Path(args.case_summary)
    case_summary = load_json(case_summary_path)
    validation_log = Path(str(case_summary['validation_log']))
    run_log = Path(str(case_summary['run_log']))
    runner_log = Path(str(case_summary['runner_log']))
    input_file = Path(str(case_summary['input_file']))
    final_plot = Path(str(case_summary['final_plot']))
    metrics = parse_validation_log(validation_log)
    require(run_log.is_file(), f'missing run log: {run_log}')
    require(runner_log.is_file(), f'missing runner log: {runner_log}')
    require(input_file.is_file(), f'missing input file: {input_file}')
    require(final_plot.is_dir(), f'missing final plotfile directory: {final_plot}')
    run_text = run_log.read_text(encoding='utf-8', errors='replace')
    require('AMReX' in run_text and 'finalized' in run_text, 'AMReX finalization marker missing')
    require('Unused ParmParse' not in run_text, 'unused ParmParse variables found')
    bad_tokens = ('nan', 'NaN', 'NAN', 'inf', 'SIGSEGV', 'SIGABRT', 'Abort::')
    require(not any(token in run_text for token in bad_tokens), 'run log contains failure token')
    summary = {
        'clears_qlt_03_double_mach_gap': True,
        'time': metrics['time'],
        'grid': f"{metrics['grid_nx']}x{metrics['grid_ny']}",
        'rho_min': metrics['rho_min'],
        'rho_max': metrics['rho_max'],
        'pressure_min': metrics['pressure_min'],
        'pressure_max': metrics['pressure_max'],
        'front_x': metrics['front_x'],
        'min_expected_front': metrics['min_expected_front'],
        'post_state': metrics['post_state'],
        'pre_state': metrics['pre_state'],
    }
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Gas Double-Mach Reflection Validation',
        'scope': (
            'PeleC inviscid GammaLaw Double-Mach reflection strong-shock gate: '
            'front advancement, Rankine-Hugoniot plateau states, positive density/pressure, '
            'finite fields, and clean AMReX finalization'
        ),
        'case': case_summary,
        'summary': summary,
        'quality_gates': [
            {'name': 'run_finalized_without_failure_tokens', 'status': 'PASS', 'gap': '', 'evidence': [str(run_log)]},
            {'name': 'positive_finite_density_pressure', 'status': 'PASS', 'gap': '', 'evidence': [str(validation_log)]},
            {'name': 'rankine_hugoniot_plateau_states', 'status': 'PASS', 'gap': '', 'evidence': [str(validation_log)]},
            {'name': 'shock_front_advancement', 'status': 'PASS', 'gap': '', 'evidence': [str(validation_log)]},
        ],
        'evidence_files': [
            evidence_entry('case_summary', case_summary_path),
            evidence_entry('input_file', input_file),
            evidence_entry('run_log', run_log),
            evidence_entry('runner_log', runner_log),
            evidence_entry('validation_log', validation_log),
            evidence_entry('runner', Path('tools/codex_run_academic_gas_double_mach_validation.sh')),
            evidence_entry('smoke_runner', Path('tools/codex_smoke_academic_double_mach.sh')),
            evidence_entry('validator', Path('tools/validate_double_mach_plotfile.py')),
            evidence_entry('report_writer', Path('tools/write_academic_gas_double_mach_validation_report.py')),
        ],
        'limitations': [
            'This is an in-repository short Double-Mach reflection gate, not a full external literature benchmark.',
            'The gate strengthens QLT-03 standard validation coverage but does not by itself clear MMS or bubble-rise gaps.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'invalid status')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('clears_qlt_03_double_mach_gap') is True, 'Double-Mach clear flag missing')
    require(float(summary.get('time', 0.0)) > 0.0, 'time must be positive')
    require(float(summary.get('rho_min', 0.0)) > 0.0, 'rho_min must be positive')
    require(float(summary.get('pressure_min', 0.0)) > 0.0, 'pressure_min must be positive')
    require(float(summary.get('front_x', 0.0)) >= float(summary.get('min_expected_front', 1.0e300)), 'front gate failed')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality_gates missing')
    for gate in gates:
        require(isinstance(gate, dict), 'quality gate is not an object')
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
        '# Academic Gas Double-Mach Reflection Validation',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Scope',
        '',
        report['scope'],
        '',
        '## Key Metrics',
        '',
        f"- Time: `{summary['time']}`",
        f"- Grid: `{summary['grid']}`",
        f"- Density range: `{summary['rho_min']}` to `{summary['rho_max']}`",
        f"- Pressure range: `{summary['pressure_min']}` to `{summary['pressure_max']}`",
        f"- Front x: `{summary['front_x']}` minimum expected `{summary['min_expected_front']}`",
        '',
        '## Quality Gates',
        '',
    ]
    for gate in report['quality_gates']:
        lines.append(f"- `{gate['name']}`: `{gate['status']}`")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-summary', default=str(DEFAULT_CASE_SUMMARY))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'academic_gas_double_mach_validation VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"front_x={summary['front_x']} grid={summary['grid']}"
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
            'academic_gas_double_mach_validation PASS '
            f"json={out_json} md={out_md} status={report['status']}"
        )
        return 0
    except ReportError as exc:
        print(f'academic_gas_double_mach_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
