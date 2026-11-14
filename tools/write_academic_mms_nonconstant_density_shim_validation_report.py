#!/usr/bin/env python3
"""Write/verify the academic nonconstant-density MMS shim validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-MMS-NONCONSTANT-DENSITY-SHIM-VALIDATION'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-MMS-NONCONSTANT-DENSITY-SHIM-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729')
DEFAULT_CASE_SUMMARY = DEFAULT_ROOT / 'mms_nonconstant_density_stationary_8cell_1step' / 'case_summary.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_mms_nonconstant_density_shim_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_mms_nonconstant_density_shim_validation_report.md'

PASS_RE = re.compile(r'^academic_mms_nonconstant_density_shim_validation PASS\s+(.*)$', re.MULTILINE)


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


def parse_key_values(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for item in text.split():
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        try:
            parsed = float(value.rstrip(','))
        except ValueError:
            continue
        require(math.isfinite(parsed), f'non-finite validation metric: {key}')
        values[key] = parsed
    return values


def parse_validation_log(path: Path) -> dict[str, float]:
    require(path.is_file(), f'missing validation log: {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    match = PASS_RE.search(text)
    require(match is not None, f'validation PASS line missing in {path}')
    values = parse_key_values(match.group(1))
    required = {
        'max_primary_error',
        'max_primary_residual',
        'pressure_error',
        'rhoE_residual',
        'pressure_error_relative',
        'rhoE_residual_relative',
        'rho_mms_error',
        'u_mms_error',
        'v_mms_error',
        'w_mms_error',
        'rho_residual',
        'rhou_residual',
        'rhov_residual',
        'rhow_residual',
    }
    missing = sorted(required - set(values))
    require(not missing, f'missing validation metrics: {missing}')
    require(values['max_primary_error'] <= 1.0e-10, 'primary MMS error exceeds gate')
    require(values['max_primary_residual'] <= 1.0e-10, 'primary residual exceeds gate')
    require(values['pressure_error_relative'] <= 1.0e-7, 'relative pressure error exceeds gate')
    require(values['rhoE_residual_relative'] <= 1.0e-7, 'relative energy residual exceeds gate')
    return values


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case_summary_path = Path(args.case_summary)
    case = load_json(case_summary_path)
    input_file = Path(str(case['input_file']))
    build_log = Path(str(case['build_log']))
    run_log = Path(str(case['run_log']))
    validation_log = Path(str(case['validation_log']))
    shim_home = Path(str(case['masa_shim_home']))
    shim_header = shim_home / 'include' / 'masa.h'
    shim_lib = shim_home / 'lib' / 'libmasa.a'
    for path in (input_file, build_log, run_log, validation_log, shim_header, shim_lib):
        require(path.is_file(), f'missing evidence file: {path}')

    run_text = run_log.read_text(encoding='utf-8', errors='replace')
    run_returncode = int(case.get('run_returncode', 1))
    validation_returncode = int(case.get('validation_returncode', 1))
    blocking_reasons: list[str] = []
    if run_returncode != 0:
        blocking_reasons.append('mms_nonconstant_density_run_failed')
    if validation_returncode != 0:
        blocking_reasons.append('mms_nonconstant_density_validation_failed')
    if 'MASA shim: nonconstant-density stationary manufactured solution' not in run_text:
        blocking_reasons.append('nonconstant_density_shim_banner_missing')
    if any(token in run_text for token in ('NaN', 'nan', 'SIGSEGV', 'SIGABRT', 'Abort::')):
        blocking_reasons.append('failure_token_detected')
    if 'AMReX' not in run_text or 'finalized' not in run_text:
        blocking_reasons.append('amrex_finalization_missing')
    if case.get('uses_external_masa') is not False:
        blocking_reasons.append('case_must_declare_external_masa_false')
    if case.get('manufactured_solution_kind') != 'nonconstant_density_stationary':
        blocking_reasons.append('unexpected_manufactured_solution_kind')

    metrics: dict[str, Any] = {}
    status = STATUS_NOT_READY
    if not blocking_reasons:
        metrics = parse_validation_log(validation_log)
        status = STATUS_PASS

    summary = {
        'clears_qlt_03_nonconstant_mms_shim_gap': status == STATUS_PASS,
        'clears_external_nonlinear_masa_benchmark': False,
        'uses_external_masa': False,
        'manufactured_solution_kind': case.get('manufactured_solution_kind'),
        'blocking_reasons': blocking_reasons,
        **metrics,
    }
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Academic MMS Nonconstant-Density Shim Validation',
        'scope': (
            'PeleC MMS RegTest validation with a generated MASA-compatible nonconstant-density, '
            'zero-velocity, constant-pressure stationary manufactured state. This exercises spatially '
            'varying exact-field evaluation, MMS source wiring, error derives, clean finalization, '
            'and relative pressure/energy residual gates without claiming external MASA coverage.'
        ),
        'case': case,
        'summary': summary,
        'quality_gates': [
            {
                'name': 'nonconstant_density_shim_built',
                'status': 'PASS' if shim_header.is_file() and shim_lib.is_file() else 'NOT_READY',
                'gap': '',
                'evidence': [str(shim_header), str(shim_lib)],
            },
            {
                'name': 'mms_run_finalized_without_failure_tokens',
                'status': 'PASS' if status == STATUS_PASS else 'NOT_READY',
                'gap': '' if status == STATUS_PASS else 'MMS run did not provide a clean finalization gate.',
                'evidence': [str(run_log)],
            },
            {
                'name': 'nonconstant_density_primary_errors_near_roundoff',
                'status': 'PASS' if status == STATUS_PASS else 'NOT_READY',
                'gap': '' if status == STATUS_PASS else 'Density/velocity error or residual gate failed.',
                'evidence': [str(validation_log)],
            },
            {
                'name': 'pressure_and_energy_relative_residuals_bounded',
                'status': 'PASS' if status == STATUS_PASS else 'NOT_READY',
                'gap': '' if status == STATUS_PASS else 'Pressure or energy relative residual gate failed.',
                'evidence': [str(validation_log)],
            },
            {
                'name': 'scope_guard_does_not_claim_external_masa',
                'status': 'PASS',
                'gap': '',
                'evidence': [str(case_summary_path)],
            },
        ],
        'evidence_files': [
            evidence_entry('case_summary', case_summary_path),
            evidence_entry('input_file', input_file),
            evidence_entry('masa_shim_header', shim_header),
            evidence_entry('masa_shim_static_library', shim_lib),
            evidence_entry('build_log', build_log),
            evidence_entry('run_log', run_log),
            evidence_entry('validation_log', validation_log),
            evidence_entry('runner', Path('tools/codex_run_academic_mms_nonconstant_density_shim_validation.sh')),
            evidence_entry('report_writer', Path('tools/write_academic_mms_nonconstant_density_shim_validation_report.py')),
        ],
        'limitations': [
            'This is a nonconstant in-repository MASA-compatible shim, not the external nonlinear MASA/MetaPhysicL benchmark.',
            'The exact state is stationary with zero velocity and constant pressure; it strengthens MMS spatial-field coverage but does not exercise all nonlinear source terms.',
            'The report intentionally sets clears_external_nonlinear_masa_benchmark=false to avoid overclaiming QLT-03 closure.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_PASS, STATUS_NOT_READY}, 'invalid status')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('uses_external_masa') is False, 'report must declare uses_external_masa=false')
    require(
        summary.get('clears_external_nonlinear_masa_benchmark') is False,
        'shim report must not clear external nonlinear MASA benchmark',
    )
    if data.get('status') == STATUS_PASS:
        require(summary.get('clears_qlt_03_nonconstant_mms_shim_gap') is True, 'nonconstant MMS clear flag missing')
        require(float(summary.get('max_primary_error', 1.0)) <= 1.0e-10, 'primary MMS error exceeds gate')
        require(float(summary.get('max_primary_residual', 1.0)) <= 1.0e-10, 'primary residual exceeds gate')
        require(float(summary.get('pressure_error_relative', 1.0)) <= 1.0e-7, 'pressure relative error exceeds gate')
        require(float(summary.get('rhoE_residual_relative', 1.0)) <= 1.0e-7, 'energy relative residual exceeds gate')
    else:
        require(summary.get('clears_qlt_03_nonconstant_mms_shim_gap') is False, 'NOT_READY report must not clear MMS shim')
        require(summary.get('blocking_reasons'), 'NOT_READY report must list blocking reasons')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality_gates missing')
    for gate in gates:
        require(isinstance(gate, dict), 'quality gate is not an object')
        require(gate.get('status') in {'PASS', 'NOT_READY'}, f"invalid quality gate status: {gate.get('name')}")
        if data.get('status') == STATUS_PASS:
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
        '# Academic MMS Nonconstant-Density Shim Validation',
        '',
        f"Status: `{report['status']}`",
        '',
        f"Scope: {report['scope']}",
        '',
        '## Summary',
        '',
    ]
    for key in (
        'clears_qlt_03_nonconstant_mms_shim_gap',
        'clears_external_nonlinear_masa_benchmark',
        'uses_external_masa',
        'manufactured_solution_kind',
        'max_primary_error',
        'max_primary_residual',
        'pressure_error_relative',
        'rhoE_residual_relative',
    ):
        if key in summary:
            lines.append(f'- `{key}`: `{summary[key]}`')
    lines += ['', '## Quality Gates', '']
    for gate in report['quality_gates']:
        lines.append(f"- `{gate['name']}`: `{gate['status']}`")
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
                'academic_mms_nonconstant_density_shim_validation VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"primary_error={summary.get('max_primary_error')} "
                f"pressure_rel={summary.get('pressure_error_relative')}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'academic_mms_nonconstant_density_shim_validation PASS '
            f"json={out_json} md={out_md} status={report['status']}"
        )
        return 0
    except ReportError as exc:
        print(f'academic_mms_nonconstant_density_shim_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
