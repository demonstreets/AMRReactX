#!/usr/bin/env python3
"""Write/verify the academic two-phase interface AMR validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-TWOPHASE-INTERFACE-AMR-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'case_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_twophase_interface_amr_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_twophase_interface_amr_validation_report.md'

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
    r'alpha_range=(?P<alpha_min>[-+0-9.eE]+):(?P<alpha_max>[-+0-9.eE]+)\s+'
    r'mass_rel=(?P<mass_rel>[-+0-9.eE]+)\s+'
    r'vof_mass_rel=(?P<vof_mass_rel>[-+0-9.eE]+)\s+'
    r'ymom_linf=(?P<ymom_linf>[-+0-9.eE]+)'
)
INTERFACE_AMR_RE = re.compile(
    r'academic_twophase_interface_amr_validation PASS .*?'
    r'time=(?P<time>[-+0-9.eE]+)\s+'
    r'grid=\((?P<nx>\d+),\s*(?P<ny>\d+)\)\s+'
    r'finest_level=(?P<finest_level>\d+).*?'
    r'mass_rel=(?P<mass_rel>[-+0-9.eE]+)\s+'
    r'vof_mass_rel=(?P<vof_mass_rel>[-+0-9.eE]+)\s+'
    r'ymom_linf=(?P<ymom_linf>[-+0-9.eE]+)\s+'
    r'interface_cells=(?P<interface_cells>\d+)\s+'
    r'interface_refined_cells=(?P<interface_refined_cells>\d+)\s+'
    r'interface_refined_fraction=(?P<interface_refined_fraction>[-+0-9.eE]+)\s+'
    r'refined_box_count=(?P<refined_box_count>\d+)\s+'
    r'refined_cell_count=(?P<refined_cell_count>\d+)\s+'
    r'refined_cell_fraction=(?P<refined_cell_fraction>[-+0-9.eE]+)'
)


class TwoPhaseInterfaceAMRError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TwoPhaseInterfaceAMRError(message)


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
        raise TwoPhaseInterfaceAMRError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise TwoPhaseInterfaceAMRError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def parse_log(path: Path, regex: re.Pattern[str], label: str) -> dict[str, Any]:
    require(path.is_file(), f'missing {label} log: {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    match = regex.search(text)
    require(match is not None, f'{label} log does not contain PASS metrics: {path}')
    out: dict[str, Any] = {'path': str(path), 'verdict': 'PASS'}
    for key, value in match.groupdict().items():
        try:
            out[key] = int(value)
        except ValueError:
            out[key] = float(value)
    return out


def rel_diff(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1.0e-300)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    cases_in = manifest.get('cases')
    require(isinstance(cases_in, list) and len(cases_in) >= 2, 'manifest must contain AMR and uniform reference cases')
    evidence_files = [evidence_entry('case_manifest', manifest_path)]
    build_log = Path(str(manifest.get('build_log', '')))
    evidence_files.append(evidence_entry('build_log', build_log))

    cases: list[dict[str, Any]] = []
    for item in cases_in:
        require(isinstance(item, dict), 'manifest case is not an object')
        name = str(item.get('name', ''))
        role = str(item.get('role', ''))
        input_path = Path(str(item.get('input_file', '')))
        run_log = Path(str(item.get('run_log', '')))
        conservation_log = Path(str(item.get('conservation_log', '')))
        growth_log = Path(str(item.get('growth_log', '')))
        case: dict[str, Any] = {
            'name': name,
            'role': role,
            'amr_enabled': bool(item.get('amr_enabled')),
            'n_cell': [int(v) for v in item['n_cell']],
            'plotfile_initial': str(item.get('plotfile_initial', '')),
            'plotfile_final': str(item.get('plotfile_final', '')),
            'input_file': str(input_path),
            'run_log': str(run_log),
            'conservation_log': str(conservation_log),
            'growth_log': str(growth_log),
            'conservation_metrics': parse_log(conservation_log, CONSERVATION_RE, f'{name} conservation'),
            'growth_metrics': parse_log(growth_log, GROWTH_RE, f'{name} growth'),
        }
        evidence_files.extend([
            evidence_entry(f'{name}_input', input_path),
            evidence_entry(f'{name}_run_log', run_log),
            evidence_entry(f'{name}_conservation_log', conservation_log),
            evidence_entry(f'{name}_growth_log', growth_log),
        ])
        if case['amr_enabled']:
            interface_log = Path(str(item.get('interface_amr_log', '')))
            case['interface_amr_log'] = str(interface_log)
            case['interface_amr_metrics'] = parse_log(interface_log, INTERFACE_AMR_RE, f'{name} interface AMR')
            evidence_files.append(evidence_entry(f'{name}_interface_amr_log', interface_log))
        cases.append(case)

    amr_cases = [case for case in cases if case['amr_enabled']]
    uniform_cases = [case for case in cases if not case['amr_enabled']]
    require(len(amr_cases) == 1, f'expected exactly one AMR case, got {len(amr_cases)}')
    require(len(uniform_cases) >= 1, 'expected at least one uniform-fine reference case')
    amr_case = amr_cases[0]
    uniform_case = uniform_cases[0]
    amr_iface = amr_case['interface_amr_metrics']
    amr_growth = amr_case['growth_metrics']
    uniform_growth = uniform_case['growth_metrics']

    interface_refined_fraction = float(amr_iface['interface_refined_fraction'])
    refined_cell_fraction = float(amr_iface['refined_cell_fraction'])
    growth_rate_rel_diff = rel_diff(float(amr_growth['growth_rate']), float(uniform_growth['growth_rate']))
    growth_ratio_rel_diff = rel_diff(float(amr_growth['growth_ratio']), float(uniform_growth['growth_ratio']))
    max_mass_rel = max(float(case['conservation_metrics']['mass_rel']) for case in cases)
    max_vof_mass_rel = max(float(case['conservation_metrics']['vof_mass_rel']) for case in cases)
    min_growth_ratio = min(float(case['growth_metrics']['growth_ratio']) for case in cases)

    require(interface_refined_fraction >= float(args.min_interface_refined_fraction), 'interface refined fraction too low')
    require(float(amr_iface['finest_level']) >= 1, 'AMR case did not create a refined level')
    require(0.0 < refined_cell_fraction <= float(args.max_refined_cell_fraction), 'refined fraction outside limits')
    require(max_mass_rel <= float(args.mass_rtol), 'mass drift too high')
    require(max_vof_mass_rel <= float(args.mass_rtol), 'VOF mass drift too high')
    require(min_growth_ratio >= float(args.min_growth_ratio), 'RT growth ratio too low')
    require(growth_rate_rel_diff <= float(args.max_growth_rate_rel_diff), 'AMR/uniform growth-rate difference too high')

    equivalent_uniform_cells = int(amr_case['n_cell'][0]) * 2 * int(amr_case['n_cell'][1]) * 2
    refined_cell_savings_fraction = 1.0 - float(amr_iface['refined_cell_count']) / max(float(equivalent_uniform_cells), 1.0)

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Two-Phase Interface AMR Validation',
        'scope': 'Rayleigh-Taylor VOF interface-specific AMR tagging/refinement, conservation, boundedness, and uniform-fine consistency gate',
        'case_manifest': str(manifest_path),
        'case_count': len(cases),
        'cases': cases,
        'summary': {
            'case_count': len(cases),
            'amr_case': amr_case['name'],
            'uniform_reference_case': uniform_case['name'],
            'interface_refined_fraction': interface_refined_fraction,
            'min_interface_refined_fraction': float(args.min_interface_refined_fraction),
            'amr_refined_cell_fraction': refined_cell_fraction,
            'max_refined_cell_fraction_limit': float(args.max_refined_cell_fraction),
            'refined_cell_savings_fraction_vs_full_level1_uniform': refined_cell_savings_fraction,
            'amr_uniform_growth_rate_rel_diff': growth_rate_rel_diff,
            'amr_uniform_growth_ratio_rel_diff': growth_ratio_rel_diff,
            'max_growth_rate_rel_diff_limit': float(args.max_growth_rate_rel_diff),
            'min_growth_ratio': min_growth_ratio,
            'min_growth_ratio_limit': float(args.min_growth_ratio),
            'max_mass_rel': max_mass_rel,
            'max_vof_mass_rel': max_vof_mass_rel,
            'mass_rtol': float(args.mass_rtol),
            'clears_acd_08_two_phase_interface_amr_gap': True,
        },
        'quality_gate_matrix': [
            {'name': 'amr_refined_level_created', 'status': 'PASS', 'gap': '', 'evidence': [amr_case['interface_amr_log']]},
            {'name': 'two_phase_interface_refined', 'status': 'PASS', 'gap': '', 'evidence': [amr_case['interface_amr_log']]},
            {'name': 'amr_refinement_efficiency', 'status': 'PASS', 'gap': '', 'evidence': [amr_case['interface_amr_log']]},
            {'name': 'vof_mass_conservation', 'status': 'PASS', 'gap': '', 'evidence': [case['conservation_log'] for case in cases]},
            {'name': 'alpha_boundedness', 'status': 'PASS', 'gap': '', 'evidence': [case['conservation_log'] for case in cases]},
            {'name': 'amr_uniform_growth_consistency', 'status': 'PASS', 'gap': '', 'evidence': [case['growth_log'] for case in cases]},
        ],
        'blocking_gaps': [],
        'next_required_artifacts': [],
        'evidence_files': evidence_files,
        'limitations': [
            'This validates two-phase interface AMR on the maintained Rayleigh-Taylor case.',
            'The maintained gate includes a buffered AMR run that advances beyond the step-3000 regrid; unbuffered exploratory AMR runs remain a known coarse-fine-boundary instability mode.',
            'It is not a gas-liquid detonation, spray-combustion, or external literature benchmark.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(summ.get('clears_acd_08_two_phase_interface_amr_gap') is True, 'ACD-08 AMR gap not cleared')
    require(float(summ.get('interface_refined_fraction', 0.0)) >= float(summ.get('min_interface_refined_fraction', math.inf)), 'interface refined fraction too low')
    require(float(summ.get('amr_refined_cell_fraction', math.inf)) <= float(summ.get('max_refined_cell_fraction_limit', 0.0)), 'refined fraction too high')
    require(float(summ.get('amr_uniform_growth_rate_rel_diff', math.inf)) <= float(summ.get('max_growth_rate_rel_diff_limit', 0.0)), 'AMR/uniform growth-rate rel diff too high')
    require(float(summ.get('min_growth_ratio', 0.0)) >= float(summ.get('min_growth_ratio_limit', math.inf)), 'growth ratio too low')
    require(float(summ.get('max_mass_rel', math.inf)) <= float(summ.get('mass_rtol', 0.0)), 'mass drift too high')
    require(float(summ.get('max_vof_mass_rel', math.inf)) <= float(summ.get('mass_rtol', 0.0)), 'VOF mass drift too high')
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    require(all(item.get('status') == 'PASS' for item in gates if isinstance(item, dict)), 'quality gate failed')
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
        '# Academic Two-Phase Interface AMR Validation',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Cases', '', '| Case | Role | AMR | n_cell | Growth ratio | Growth rate | Interface refined | Refined fraction |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for case in report['cases']:
        growth = case['growth_metrics']
        iface = case.get('interface_amr_metrics', {})
        lines.append(
            f"| `{case['name']}` | `{case['role']}` | `{case['amr_enabled']}` | `{case['n_cell']}` | "
            f"`{float(growth['growth_ratio']):.8g}` | `{float(growth['growth_rate']):.8g}` | "
            f"`{iface.get('interface_refined_fraction', '')}` | `{iface.get('refined_cell_fraction', '')}` |"
        )
    lines += ['', '## Quality Gates', '', '| Gate | Status | Evidence | Gap |', '| --- | --- | --- | --- |']
    for gate in report['quality_gate_matrix']:
        evidence = '; '.join(str(item) for item in gate.get('evidence', [])) or 'none'
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {evidence} | {gate.get('gap', '') or 'none'} |")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    parser.add_argument('--min-interface-refined-fraction', type=float, default=0.55)
    parser.add_argument('--max-refined-cell-fraction', type=float, default=0.90)
    parser.add_argument('--min-growth-ratio', type=float, default=1.02)
    parser.add_argument('--max-growth-rate-rel-diff', type=float, default=0.55)
    parser.add_argument('--mass-rtol', type=float, default=2.0e-5)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            summ = data['summary']
            print(
                'academic_twophase_interface_amr_validation VERIFY-PASS '
                f"json={args.verify_json} interface_refined_fraction={summ.get('interface_refined_fraction')} "
                f"growth_rate_rel_diff={summ.get('amr_uniform_growth_rate_rel_diff')}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=True)
        out_json = Path(args.output_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, Path(args.output_md))
        summ = report['summary']
        print(
            'academic_twophase_interface_amr_validation PASS '
            f"json={out_json} status={report['status']} "
            f"interface_refined_fraction={summ.get('interface_refined_fraction')} "
            f"growth_rate_rel_diff={summ.get('amr_uniform_growth_rate_rel_diff')}"
        )
        return 0
    except TwoPhaseInterfaceAMRError as exc:
        print(f'academic_twophase_interface_amr_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
