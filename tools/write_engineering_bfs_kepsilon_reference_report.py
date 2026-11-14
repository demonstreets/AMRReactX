#!/usr/bin/env python3
"""Write/verify engineering BFS k-epsilon reference-validation evidence.

This report is deliberately allowed to record a NOT_READY result.  A failing
Backward-Facing Step validation is still useful evidence as long as the failure
is explicit, machine-readable, and does not masquerade as a passing gate.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_bfs  # noqa: E402

SCHEMA_VERSION = 1
PASS_STATUS = 'PASS-BFS-KEPSILON-REFERENCE'
NOT_READY_STATUS = 'NOT_READY-BFS-KEPSILON-REFERENCE'

DEFAULT_PLOTFILE = Path('examples/engineering/backward_facing_step/plt02057')
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
    'bfs_kepsilon_reference_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
    'bfs_kepsilon_reference_report.md'
)
DEFAULT_LOGLAW_VALIDATOR = Path('tools/validate_bfs_loglaw_profile_plotfile.py')
DEFAULT_SENSITIVITY_SCOUT_SCRIPT = Path('tools/codex_scout_engineering_bfs_kepsilon_sensitivity.sh')
DEFAULT_PREFLIGHT_REPORTS = (
    (
        'refined_208x56_lowcfl_5000step_reference_attempt',
        Path(
            'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
            'bfs_kepsilon_preflight_208_lowcfl_5000_report.json'
        ),
    ),
    (
        'base_104x28_current_input',
        Path(
            'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
            'bfs_kepsilon_preflight_base_report.json'
        ),
    ),
    (
        'refined_208x56_default_cfl',
        Path(
            'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
            'bfs_kepsilon_preflight_208_default_report.json'
        ),
    ),
    (
        'refined_208x56_lowcfl_500step',
        Path(
            'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/'
            'bfs_kepsilon_preflight_208_lowcfl_report.json'
        ),
    ),
)
DEFAULT_SENSITIVITY_CASES = (
    (
        '208x56_4rank_default_cfl',
        Path('/tmp/codex_bfs_refine_208x56_4rank_20260721'),
    ),
    (
        '208x56_serial_cfl005_500step',
        Path('/tmp/codex_bfs_refine_208x56_serial_cfl005_20260721'),
    ),
)


class ReportError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReportError(message)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def number_or_none(value: Any) -> float | None:
    return float(value) if finite(value) else None


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


def run_bfs_validator(plotfile: Path) -> tuple[dict[str, Any], str, int]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = validate_bfs.validate(str(plotfile))
    stdout = buf.getvalue()
    rc = 0 if result.get('verdict') == 'PASS' else 1
    return result, stdout, rc


def run_loglaw_validator(plotfile: Path, validator: Path) -> dict[str, Any]:
    require(validator.is_file(), f'missing log-law validator: {validator}')
    proc = subprocess.run(
        [sys.executable, str(validator), '--plotfile', str(plotfile)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    text = proc.stdout.strip()
    linf = None
    match = re.search(r'linf=([0-9.eE+-]+)', text)
    if match:
        linf = float(match.group(1))
    return {
        'command': [sys.executable, str(validator), '--plotfile', str(plotfile)],
        'returncode': proc.returncode,
        'stdout': text,
        'linf': linf,
        'passed': proc.returncode == 0,
    }


def latest_plotfile(run_dir: Path) -> Path | None:
    plots = sorted(p for p in run_dir.glob('plt_ref*') if (p / 'Header').is_file())
    return plots[-1] if plots else None


def summarize_sensitivity_case(label: str, run_dir: Path) -> dict[str, Any]:
    run_log = run_dir / 'run.log'
    item: dict[str, Any] = {
        'label': label,
        'path': str(run_dir),
        'exists': run_dir.is_dir(),
        'run_log_exists': run_log.is_file(),
    }
    if not run_dir.is_dir() or not run_log.is_file():
        item['status'] = 'MISSING'
        return item

    text = run_log.read_text(encoding='utf-8', errors='replace')
    item.update({
        'run_log_sha256': sha256_file(run_log),
        'amrex_finalized': 'AMReX (26.05) finalized' in text or 'AMReX finalized' in text,
        'nan_abort': 'NaNs detected' in text,
        'sigabrt': 'SIGABRT' in text,
        'unused_parmparse_variables': 'Unused ParmParse Variables' in text,
    })

    steps = [int(m.group(1)) for m in re.finditer(r'STEP \[(\d+)\]', text)]
    times = [float(m.group(1)) for m in re.finditer(r'Time: ([0-9.eE+-]+), dt', text)]
    item['max_step_seen'] = max(steps) if steps else None
    item['last_time_seen'] = times[-1] if times else None

    plot = latest_plotfile(run_dir)
    item['latest_plotfile'] = str(plot) if plot else None
    if plot is not None:
        try:
            bfs, stdout, rc = run_bfs_validator(plot)
            item.update({
                'bfs_validator_returncode': rc,
                'bfs_validator_verdict': bfs.get('verdict'),
                'reattachment_x_h': number_or_none(bfs.get('xr_h')),
                'recirculation_length_h': number_or_none(bfs.get('recirc_length_h')),
                'bfs_validator_stdout': stdout,
            })
        except Exception as exc:  # pragma: no cover - defensive evidence path
            item['bfs_validator_error'] = str(exc)

    if item.get('nan_abort'):
        item['status'] = 'FAIL-NAN'
    elif item.get('amrex_finalized'):
        item['status'] = 'COMPLETE-SCOUT'
    else:
        item['status'] = 'INCOMPLETE'
    return item


def summarize_preflight_report(label: str, path: Path) -> dict[str, Any]:
    item: dict[str, Any] = {
        'label': label,
        'path': str(path),
        'exists': path.is_file(),
    }
    if not path.is_file():
        item['status'] = 'MISSING'
        item['blocking_gaps'] = ['bfs_preflight_report_missing']
        return item
    data = load_json(path)
    summary = data.get('summary', {}) if isinstance(data.get('summary'), dict) else {}
    item.update({
        'status': data.get('status'),
        'sha256': sha256_file(path),
        'input_file': data.get('input_file'),
        'grid_nx': summary.get('nx'),
        'grid_ny': summary.get('ny'),
        'cells_per_step_height': summary.get('cells_per_step_height'),
        'cfl': summary.get('cfl'),
        'dt_shrink': summary.get('dt_shrink'),
        'max_step': summary.get('max_step'),
        'stop_time': summary.get('stop_time'),
        'high_nan_risk_refined_grid': summary.get('high_nan_risk_refined_grid'),
        'blocks_production_readiness': summary.get('blocks_production_readiness'),
        'blocking_gaps': data.get('blocking_gaps', []),
        'diagnostic_gaps': data.get('diagnostic_gaps', []),
    })
    return item


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plotfile = Path(args.plotfile)
    require((plotfile / 'Header').is_file(), f'missing AMReX plotfile Header: {plotfile}/Header')

    bfs_result, bfs_stdout, bfs_rc = run_bfs_validator(plotfile)
    loglaw = run_loglaw_validator(plotfile, Path(args.loglaw_validator))

    cf_data = bfs_result.get('cf_data', {})
    grid = {}
    time = None
    first_line = ''
    header = plotfile / 'Header'
    if header.is_file():
        lines = header.read_text(encoding='utf-8', errors='replace').splitlines()
        first_line = lines[0] if lines else ''
    try:
        pf = validate_bfs.read_plotfile(str(plotfile))
        grid = pf.get('grid', {}) if isinstance(pf.get('grid'), dict) else {}
        time = number_or_none(pf.get('time'))
    except Exception as exc:  # pragma: no cover - defensive evidence path
        grid = {'read_error': str(exc)}

    nx = int(grid.get('nx', 0)) if str(grid.get('nx', '')).isdigit() else 0
    ny = int(grid.get('ny', 0)) if str(grid.get('ny', '')).isdigit() else 0

    preflight_reports = (
        [summarize_preflight_report(label, path) for label, path in DEFAULT_PREFLIGHT_REPORTS]
        if args.include_preflight else []
    )

    blockers: list[str] = []
    if bfs_rc != 0:
        blockers.append('bfs_reattachment_or_recirculation_reference_validation_failed')
    if nx < args.min_nx or ny < args.min_ny:
        blockers.append('bfs_reference_grid_below_engineering_minimum')
    preflight_pass_count = sum(
        1 for item in preflight_reports
        if item.get('status') == 'PASS-BFS-KEPSILON-PREFLIGHT'
    )
    preflight_case_ready = (not args.include_preflight) or preflight_pass_count > 0
    if not preflight_case_ready:
        blockers.append('bfs_kepsilon_case_preflight_not_ready')

    status = PASS_STATUS if not blockers else NOT_READY_STATUS
    x = cf_data.get('x', [])
    cf = cf_data.get('cf', [])
    finite_cf = [float(v) for v in cf if finite(v)]

    sensitivity_cases = (
        [summarize_sensitivity_case(label, path) for label, path in DEFAULT_SENSITIVITY_CASES]
        if args.include_sensitivity else []
    )

    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering BFS k-epsilon Reference Validation',
        'plotfile': str(plotfile),
        'plotfile_header_sha256': sha256_file(header),
        'plotfile_header_first_line': first_line,
        'reference_case': {
            'name': 'Backward-Facing Step turbulent flow',
            'reference': 'Driver and Seegmiller (1985), reattachment length X_R/H approx 6.26',
            'required_xr_h': validate_bfs.X_R_REF,
            'xr_relative_tolerance': validate_bfs.X_R_TOL,
            'minimum_recirculation_length_h': validate_bfs.MIN_RECIRC_LENGTH,
        },
        'summary': {
            'status': status,
            'grid_nx': nx,
            'grid_ny': ny,
            'time': time,
            'bfs_validator_returncode': bfs_rc,
            'bfs_validator_verdict': bfs_result.get('verdict'),
            'reattachment_x_h': number_or_none(bfs_result.get('xr_h')),
            'recirculation_length_h': number_or_none(bfs_result.get('recirc_length_h')),
            'cf_sample_count': len(x) if hasattr(x, '__len__') else 0,
            'cf_finite_count': len(finite_cf),
            'cf_min': min(finite_cf) if finite_cf else None,
            'cf_max': max(finite_cf) if finite_cf else None,
            'loglaw_validator_returncode': loglaw['returncode'],
            'loglaw_linf': loglaw['linf'],
            'loglaw_passed': loglaw['passed'],
            'preflight_report_count': len(preflight_reports),
            'preflight_pass_count': preflight_pass_count,
            'preflight_case_ready': preflight_case_ready,
            'sensitivity_case_count': len(sensitivity_cases),
            'blocks_production_readiness': status != PASS_STATUS,
        },
        'bfs_validator': {
            'returncode': bfs_rc,
            'stdout': bfs_stdout,
            'notes': bfs_result.get('notes', []),
        },
        'loglaw_validator': loglaw,
        'blocking_gaps': blockers,
        'diagnostic_gaps': (
            ['bfs_loglaw_profile_plotfile_validation_failed']
            if loglaw['returncode'] != 0 else []
        ),
        'preflight_reports': preflight_reports,
        'sensitivity_cases': sensitivity_cases,
        'evidence_files': [
            evidence_entry('validate_bfs.py', Path('tools/validate_bfs.py')),
            evidence_entry('validate_bfs_loglaw_profile_plotfile.py', Path(args.loglaw_validator)),
            evidence_entry('codex_scout_engineering_bfs_kepsilon_sensitivity.sh', Path(args.sensitivity_scout_script)),
            *[
                evidence_entry(f'bfs_kepsilon_preflight_{label}', path)
                for label, path in DEFAULT_PREFLIGHT_REPORTS
                if args.include_preflight
            ],
            evidence_entry('plotfile_header', header),
        ],
        'limitations': [
            'Current plotfile is treated as evidence of the present BFS validation state, not as a production-qualified turbulent BFS benchmark.',
            'PASS requires BFS reattachment and recirculation reference validation to pass on an adequate engineering grid.',
            'The preflight reports check input-deck readiness before launching expensive refined-grid or parallel runs.',
            'The log-law profile validator is retained as a diagnostic because the evolved EB-BFS plotfile is not an initial analytic log-law profile.',
            'Sensitivity-case directories under /tmp are summarized when present but are not required as durable release evidence.',
        ],
    }
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        '# Engineering BFS k-epsilon Reference Validation',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
        f"- Plotfile: `{report['plotfile']}`",
        f"- Grid: `{s['grid_nx']} x {s['grid_ny']}`",
        f"- BFS validator: `{s['bfs_validator_verdict']}` rc `{s['bfs_validator_returncode']}`",
        f"- X_R/H: `{s['reattachment_x_h']}`",
        f"- Recirculation length/H: `{s['recirculation_length_h']}`",
        f"- Log-law validator rc: `{s['loglaw_validator_returncode']}` linf `{s['loglaw_linf']}`",
        f"- Preflight reports: `{s['preflight_pass_count']}` / `{s['preflight_report_count']}` pass",
        '',
        '## Blocking Gaps',
        '',
    ]
    for item in report['blocking_gaps']:
        lines.append(f'- `{item}`')
    lines += [
        '',
        '## Diagnostic Gaps',
        '',
    ]
    for item in report.get('diagnostic_gaps', []):
        lines.append(f'- `{item}`')
    lines += [
        '',
        '## Preflight Reports',
        '',
    ]
    for item in report.get('preflight_reports', []):
        lines.append(
            f"- `{item.get('label')}`: `{item.get('status')}` "
            f"grid `{item.get('grid_nx')} x {item.get('grid_ny')}` "
            f"H/dy `{item.get('cells_per_step_height')}` "
            f"CFL `{item.get('cfl')}` dt_shrink `{item.get('dt_shrink')}` "
            f"NaN-risk `{item.get('high_nan_risk_refined_grid')}`"
        )
    lines += [
        '',
        '## Sensitivity Cases',
        '',
    ]
    for item in report.get('sensitivity_cases', []):
        lines.append(
            f"- `{item.get('label')}`: `{item.get('status')}` "
            f"step `{item.get('max_step_seen')}` time `{item.get('last_time_seen')}` "
            f"X_R/H `{item.get('reattachment_x_h')}` recirc `{item.get('recirculation_length_h')}`"
        )
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ReportError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == SCHEMA_VERSION, f'schema_version mismatch in {path}')
    require(data.get('status') in {PASS_STATUS, NOT_READY_STATUS}, f'invalid status in {path}')
    summary = data.get('summary', {})
    require(isinstance(summary, dict), 'summary missing or not an object')
    require(summary.get('bfs_validator_verdict') in {'PASS', 'FAIL'}, 'invalid BFS validator verdict')
    require(isinstance(summary.get('blocks_production_readiness'), bool), 'missing production blocker boolean')
    gaps = data.get('blocking_gaps', [])
    require(isinstance(gaps, list), 'blocking_gaps missing or not a list')
    sensitivity_cases = data.get('sensitivity_cases', [])
    require(isinstance(sensitivity_cases, list), 'sensitivity_cases missing or not a list')
    preflight_reports = data.get('preflight_reports', [])
    require(isinstance(preflight_reports, list), 'preflight_reports missing or not a list')
    for item in preflight_reports:
        require(item.get('status') in {'PASS-BFS-KEPSILON-PREFLIGHT', 'NOT_READY-BFS-KEPSILON-PREFLIGHT'}, 'invalid preflight status')
        require(isinstance(item.get('blocking_gaps', []), list), 'invalid preflight blocking gaps')
    if data.get('status') == PASS_STATUS:
        require(summary.get('bfs_validator_returncode') == 0, 'PASS report has nonzero BFS validator rc')
        require(not gaps, 'PASS report must not have blocking gaps')
        require(
            summary.get('preflight_pass_count') == summary.get('preflight_report_count'),
            'PASS report has non-passing preflight evidence',
        )
    else:
        require(summary.get('blocks_production_readiness') is True, 'NOT_READY report must block production readiness')
        require(bool(gaps), 'NOT_READY report must list blocking gaps')
    for item in data.get('evidence_files', []):
        p = Path(item.get('path', ''))
        require(p.is_file(), f'referenced evidence file missing: {p}')
        require(sha256_file(p) == item.get('sha256'), f'referenced evidence hash mismatch: {p}')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plotfile', default=str(DEFAULT_PLOTFILE))
    ap.add_argument('--loglaw-validator', default=str(DEFAULT_LOGLAW_VALIDATOR))
    ap.add_argument('--sensitivity-scout-script', default=str(DEFAULT_SENSITIVITY_SCOUT_SCRIPT))
    ap.add_argument('--min-nx', type=int, default=160)
    ap.add_argument('--min-ny', type=int, default=32)
    ap.add_argument('--no-include-sensitivity', action='store_true')
    ap.add_argument('--no-include-preflight', action='store_true')
    ap.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)
    args.include_sensitivity = not args.no_include_sensitivity
    args.include_preflight = not args.no_include_preflight

    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            s = data['summary']
            print(
                'engineering_bfs_kepsilon_reference_report VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"bfs_rc={s['bfs_validator_returncode']} loglaw_rc={s['loglaw_validator_returncode']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        s = report['summary']
        print(
            'engineering_bfs_kepsilon_reference_report PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"bfs_rc={s['bfs_validator_returncode']} loglaw_rc={s['loglaw_validator_returncode']}"
        )
        return 0
    except ReportError as exc:
        print(f'engineering_bfs_kepsilon_reference_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
