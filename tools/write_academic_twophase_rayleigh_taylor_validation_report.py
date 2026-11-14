#!/usr/bin/env python3
"""Write/verify a multi-resolution two-phase Rayleigh-Taylor validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-TWOPHASE-RAYLEIGH-TAYLOR-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'case_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_twophase_rayleigh_taylor_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_twophase_rayleigh_taylor_validation_report.md'

GROWTH_RE = re.compile(
    r'rayleigh_taylor_growth_validation PASS .*?'
    r'time=(?P<time>[-+0-9.eE]+)\s+'
    r'grid=\((?P<nx>\d+),\s*(?P<ny>\d+)\)\s+'
    r'mode=(?P<mode>\d+)\s+'
    r'initial_amp=(?P<initial_amp>[-+0-9.eE]+)\s+'
    r'final_amp=(?P<final_amp>[-+0-9.eE]+)\s+'
    r'growth_ratio=(?P<growth_ratio>[-+0-9.eE]+)\s+'
    r'growth_rate=(?P<growth_rate>[-+0-9.eE]+)\s+'
    r'mass_rel=(?P<mass_rel>[-+0-9.eE]+)\s+'
    r'vof_mass_rel=(?P<vof_mass_rel>[-+0-9.eE]+)'
)
CONSERVATION_RE = re.compile(
    r'rayleigh_taylor_plotfile_validation PASS .*?'
    r'time=(?P<time>[-+0-9.eE]+).*?'
    r'rho_range=(?P<rho_min>[-+0-9.eE]+):(?P<rho_max>[-+0-9.eE]+)\s+'
    r'alpha_range=(?P<alpha_min>[-+0-9.eE]+):(?P<alpha_max>[-+0-9.eE]+)\s+'
    r'mass_rel=(?P<mass_rel>[-+0-9.eE]+)\s+'
    r'vof_mass_rel=(?P<vof_mass_rel>[-+0-9.eE]+)\s+'
    r'ymom_linf=(?P<ymom_linf>[-+0-9.eE]+)'
)
TREND_RE = re.compile(
    r'rayleigh_taylor_resolution_trend PASS .*?'
    r'grids=(?P<grids>\S+)\s+'
    r'time=(?P<time>[-+0-9.eE]+)\s+'
    r'mode=(?P<mode>\d+).*?'
    r'rate_spread=(?P<rate_spread>[-+0-9.eE]+)\s+'
    r'mass_max=(?P<mass_max>[-+0-9.eE]+)\s+'
    r'vof_mass_max=(?P<vof_mass_max>[-+0-9.eE]+)'
)


class TwoPhaseRTError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TwoPhaseRTError(message)


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
    except FileNotFoundError as exc:
        raise TwoPhaseRTError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise TwoPhaseRTError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def parse_log(path: Path, regex: re.Pattern[str], label: str) -> dict[str, Any]:
    require(path.is_file(), f'missing {label} log: {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    match = regex.search(text)
    require(match is not None, f'{label} log does not contain PASS metrics: {path}')
    out: dict[str, Any] = {'path': str(path), 'verdict': 'PASS'}
    for key, value in match.groupdict().items():
        if key in {'grids'}:
            out[key] = value
        else:
            try:
                out[key] = int(value)
            except ValueError:
                out[key] = float(value)
    return out


def validate_case(case: dict[str, Any], args: argparse.Namespace) -> None:
    growth = case['growth_metrics']
    conservation = case['conservation_metrics']
    require(int(growth['ny']) == 2 * int(growth['nx']), f'{case["name"]} unexpected aspect ratio')
    require(float(growth['growth_ratio']) >= float(args.min_growth_ratio), f'{case["name"]} growth ratio too low')
    require(float(growth['growth_rate']) > 0.0, f'{case["name"]} growth rate is nonpositive')
    require(float(growth['mass_rel']) <= float(args.mass_rtol), f'{case["name"]} growth mass drift too high')
    require(float(growth['vof_mass_rel']) <= float(args.mass_rtol), f'{case["name"]} growth VOF mass drift too high')
    require(float(conservation['mass_rel']) <= float(args.mass_rtol), f'{case["name"]} conservation mass drift too high')
    require(float(conservation['vof_mass_rel']) <= float(args.mass_rtol), f'{case["name"]} conservation VOF mass drift too high')
    require(float(conservation['alpha_min']) >= -float(args.alpha_tol), f'{case["name"]} alpha undershoot too large')
    require(float(conservation['alpha_max']) <= 1.0 + float(args.alpha_tol), f'{case["name"]} alpha overshoot too large')
    require(float(conservation['ymom_linf']) > 0.0, f'{case["name"]} has no momentum response')


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    cases_in = manifest.get('cases')
    require(isinstance(cases_in, list) and len(cases_in) >= 3, 'manifest must contain at least three RT cases')
    trend_log = Path(str(manifest.get('resolution_trend_log', '')))
    build_log = Path(str(manifest.get('build_log', '')))
    trend = parse_log(trend_log, TREND_RE, 'resolution trend')
    require(float(trend['rate_spread']) <= float(args.max_rate_spread), 'RT growth-rate spread too high')
    require(float(trend['mass_max']) <= float(args.mass_rtol), 'RT trend mass drift too high')
    require(float(trend['vof_mass_max']) <= float(args.mass_rtol), 'RT trend VOF mass drift too high')

    cases: list[dict[str, Any]] = []
    evidence_files = [
        evidence_entry('case_manifest', manifest_path),
        evidence_entry('build_log', build_log),
        evidence_entry('resolution_trend_log', trend_log),
    ]
    for item in cases_in:
        require(isinstance(item, dict), 'manifest case is not an object')
        name = str(item.get('name', ''))
        run_log = Path(str(item.get('run_log', '')))
        input_path = Path(str(item.get('input_file', '')))
        conservation_log = Path(str(item.get('conservation_log', '')))
        growth_log = Path(str(item.get('growth_log', '')))
        case = {
            'name': name,
            'n_cell': [int(v) for v in item['n_cell']],
            'run_dir': str(item.get('run_dir', '')),
            'input_file': str(input_path),
            'run_log': str(run_log),
            'plotfile_initial': str(item.get('plotfile_initial', '')),
            'plotfile_final': str(item.get('plotfile_final', '')),
            'conservation_log': str(conservation_log),
            'growth_log': str(growth_log),
            'conservation_metrics': parse_log(conservation_log, CONSERVATION_RE, f'{name} conservation'),
            'growth_metrics': parse_log(growth_log, GROWTH_RE, f'{name} growth'),
        }
        validate_case(case, args)
        cases.append(case)
        evidence_files.extend([
            evidence_entry(f'{name}_input', input_path),
            evidence_entry(f'{name}_run_log', run_log),
            evidence_entry(f'{name}_conservation_log', conservation_log),
            evidence_entry(f'{name}_growth_log', growth_log),
        ])

    cases.sort(key=lambda case: int(case['n_cell'][0]))
    max_mass_rel = max(float(case['conservation_metrics']['mass_rel']) for case in cases)
    max_vof_mass_rel = max(float(case['conservation_metrics']['vof_mass_rel']) for case in cases)
    max_alpha_overshoot = max(max(0.0, float(case['conservation_metrics']['alpha_max']) - 1.0) for case in cases)
    max_alpha_undershoot = max(max(0.0, -float(case['conservation_metrics']['alpha_min'])) for case in cases)
    min_growth_ratio = min(float(case['growth_metrics']['growth_ratio']) for case in cases)

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Two-Phase Rayleigh-Taylor Validation',
        'scope': 'multi-resolution VOF two-phase Rayleigh-Taylor instability growth, boundedness, momentum response, and conserved-mass validation',
        'case_manifest': str(manifest_path),
        'case_count': len(cases),
        'cases': cases,
        'summary': {
            'case_count': len(cases),
            'resolutions': [case['n_cell'] for case in cases],
            'mode': int(trend['mode']),
            'time': float(trend['time']),
            'growth_rate_spread': float(trend['rate_spread']),
            'growth_rate_spread_limit': float(args.max_rate_spread),
            'min_growth_ratio': min_growth_ratio,
            'min_growth_ratio_limit': float(args.min_growth_ratio),
            'max_mass_rel': max_mass_rel,
            'max_vof_mass_rel': max_vof_mass_rel,
            'mass_rtol': float(args.mass_rtol),
            'max_alpha_overshoot': max_alpha_overshoot,
            'max_alpha_undershoot': max_alpha_undershoot,
            'clears_acd_04_two_phase_validation_gap': True,
            'clears_acd_08_two_phase_interface_amr_gap': False,
        },
        'quality_gate_matrix': [
            {'name': 'multi_resolution_rt_runs', 'status': 'PASS', 'gap': '', 'evidence': [str(manifest_path)]},
            {'name': 'vof_mass_conservation', 'status': 'PASS', 'gap': '', 'evidence': [case['conservation_log'] for case in cases]},
            {'name': 'alpha_boundedness', 'status': 'PASS', 'gap': '', 'evidence': [case['conservation_log'] for case in cases]},
            {'name': 'rt_growth_trend', 'status': 'PASS', 'gap': '', 'evidence': [str(trend_log)]},
            {
                'name': 'two_phase_interface_amr_validation',
                'status': 'PARTIAL',
                'gap': 'This gate uses uniform grids; two-phase interface-specific AMR validation is separate.',
                'evidence': [],
            },
        ],
        'blocking_gaps': ['two_phase_interface_amr_validation'],
        'next_required_artifacts': ['two-phase interface-specific AMR validation'],
        'evidence_files': evidence_files,
        'limitations': [
            'This validates VOF two-phase Rayleigh-Taylor behavior on uniform grids.',
            'It does not validate two-phase interface-specific AMR tagging/refinement.',
            'It is not a gas-liquid detonation or spray-combustion validation case.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(summ.get('clears_acd_04_two_phase_validation_gap') is True, 'ACD-04 gap not cleared')
    require(summ.get('clears_acd_08_two_phase_interface_amr_gap') is False, 'ACD-08 AMR gap cannot be cleared here')
    require(int(summ.get('case_count', 0)) >= 3, 'too few cases')
    require(float(summ.get('growth_rate_spread', math.inf)) <= float(summ.get('growth_rate_spread_limit', 0.0)), 'growth spread too high')
    require(float(summ.get('min_growth_ratio', 0.0)) >= float(summ.get('min_growth_ratio_limit', math.inf)), 'growth ratio too low')
    require(float(summ.get('max_mass_rel', math.inf)) <= float(summ.get('mass_rtol', 0.0)), 'mass drift too high')
    require(float(summ.get('max_vof_mass_rel', math.inf)) <= float(summ.get('mass_rtol', 0.0)), 'VOF mass drift too high')
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    non_pass = [item.get('name') for item in gates if isinstance(item, dict) and item.get('status') != 'PASS']
    require(non_pass == ['two_phase_interface_amr_validation'], f'unexpected non-PASS gates: {non_pass}')
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
        '# Academic Two-Phase Rayleigh-Taylor Validation',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Cases', '', '| Case | n_cell | Growth ratio | Growth rate | Mass rel | VOF mass rel | Alpha range |', '| --- | --- | --- | --- | --- | --- | --- |']
    for case in report['cases']:
        growth = case['growth_metrics']
        cons = case['conservation_metrics']
        lines.append(
            f"| `{case['name']}` | `{case['n_cell']}` | `{float(growth['growth_ratio']):.8g}` | "
            f"`{float(growth['growth_rate']):.8g}` | `{float(cons['mass_rel']):.8e}` | "
            f"`{float(cons['vof_mass_rel']):.8e}` | "
            f"`{float(cons['alpha_min']):.8g}:{float(cons['alpha_max']):.8g}` |"
        )
    lines += ['', '## Quality Gates', '', '| Gate | Status | Evidence | Gap |', '| --- | --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        evidence = '; '.join(item['evidence']) or 'none'
        gap_text = item['gap'] or 'none'
        lines.append(f"| `{item['name']}` | `{item['status']}` | {evidence} | {gap_text} |")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    parser.add_argument('--min-growth-ratio', type=float, default=1.02)
    parser.add_argument('--max-rate-spread', type=float, default=0.60)
    parser.add_argument('--mass-rtol', type=float, default=2.0e-5)
    parser.add_argument('--alpha-tol', type=float, default=1.0e-8)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report_object(report, check_hashes=True)
            summ = report.get('summary', {})
            print(
                'academic_twophase_rayleigh_taylor_validation VERIFY-PASS '
                f"json={args.verify_json} cases={summ.get('case_count')} "
                f"growth_spread={summ.get('growth_rate_spread')} "
                f"max_vof_mass_rel={summ.get('max_vof_mass_rel')}"
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
            'academic_twophase_rayleigh_taylor_validation PASS '
            f"json={out_json} md={out_md} cases={report['case_count']} "
            f"growth_spread={report['summary']['growth_rate_spread']}"
        )
        return 0
    except TwoPhaseRTError as exc:
        print(f'academic_twophase_rayleigh_taylor_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
