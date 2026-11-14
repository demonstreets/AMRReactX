#!/usr/bin/env python3
"""Write/verify a multi-resolution 3D gas detonation reference-validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-GAS-3D-DETONATION-REFERENCE'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'case_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_gas_3d_detonation_reference_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_gas_3d_detonation_reference_report.md'
REMOTE_REPO_ROOT_TEXT = '/' + '/'.join(('home', 'cj', 'my-pele'))
REMOTE_REPO_ROOT = Path(REMOTE_REPO_ROOT_TEXT)

METRIC_RE = re.compile(r'^academic_gas_3d_znd_validation PASS\s+(.*)$', re.MULTILINE)


class Detonation3DReferenceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Detonation3DReferenceError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def repo_root() -> Path:
    return Path.cwd().resolve()


def resolve_evidence_path(path: Path) -> Path:
    candidates = [path]
    raw = str(path).replace('\\', '/')
    remote_root = str(REMOTE_REPO_ROOT).replace('\\', '/')
    remote_prefix = f'{remote_root}/'
    if raw == remote_root:
        candidates.append(repo_root())
    elif raw.startswith(remote_prefix):
        candidates.append(repo_root() / raw[len(remote_prefix):])
    if path.is_absolute():
        try:
            candidates.append(repo_root() / path.relative_to(REMOTE_REPO_ROOT))
        except ValueError:
            pass
    else:
        candidates.append(repo_root() / path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return path


def archive_path_text(path: Path) -> str:
    raw = str(path).replace('\\', '/')
    remote_root = str(REMOTE_REPO_ROOT).replace('\\', '/')
    remote_prefix = f'{remote_root}/'
    if raw == remote_root:
        return '.'
    if raw.startswith(remote_prefix):
        return raw[len(remote_prefix):]
    if path.is_absolute():
        try:
            return str(path.relative_to(REMOTE_REPO_ROOT))
        except ValueError:
            try:
                return str(path.resolve().relative_to(repo_root()))
            except ValueError:
                pass
    return str(path)


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    resolved = resolve_evidence_path(path)
    require(resolved.is_file(), f'missing evidence file: {path}')
    return {'label': label, 'path': archive_path_text(path), 'sha256': sha256_file(resolved), 'size_bytes': resolved.stat().st_size}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise Detonation3DReferenceError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise Detonation3DReferenceError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def parse_validation_metrics(path: Path) -> dict[str, Any]:
    resolved = resolve_evidence_path(path)
    require(resolved.is_file(), f'missing validation log: {path}')
    text = resolved.read_text(encoding='utf-8', errors='replace')
    match = METRIC_RE.search(text)
    require(match is not None, f'validation log does not contain PASS metrics: {path}')
    metrics: dict[str, Any] = {'verdict': 'PASS'}
    for item in match.group(1).split():
        require('=' in item, f'malformed validation metric {item} in {path}')
        key, value = item.split('=', 1)
        try:
            metrics[key] = float(value)
        except ValueError:
            metrics[key] = value
    return metrics


def validate_case_metrics(case: dict[str, Any]) -> None:
    metrics = case['metrics']
    for key in [
        'front_shift',
        'front_shift_cells',
        'front_speed',
        'temp_l1',
        'h2o_l1',
        'mass_rel',
        'species_closure_rel',
    ]:
        require(finite_number(metrics.get(key)), f'{case["name"]} missing finite metric {key}')
    require(float(metrics['front_shift']) > 0.0, f'{case["name"]} front did not move forward')
    require(float(metrics['front_shift_cells']) >= 3.0, f'{case["name"]} front shift too small in cells')
    require(1.0e4 <= float(metrics['front_speed']) <= 1.0e8, f'{case["name"]} front speed out of sanity bounds')
    require(float(metrics['temp_l1']) > 1.0, f'{case["name"]} temperature field changed too little')
    require(float(metrics['h2o_l1']) > 1.0e-8, f'{case["name"]} H2O field changed too little')
    require(abs(float(metrics['mass_rel'])) <= 5.0e-11, f'{case["name"]} mass conservation failed')
    require(float(metrics['species_closure_rel']) <= 1.0e-10, f'{case["name"]} species closure failed')
    n_cell = case['n_cell']
    require(len(n_cell) == 3 and int(n_cell[2]) >= 4, f'{case["name"]} is not a maintained 3D slab case')


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    cases_in = manifest.get('cases')
    require(isinstance(cases_in, list) and len(cases_in) >= 3, 'manifest must contain at least three cases')
    cases: list[dict[str, Any]] = []
    evidence_files = [evidence_entry('case_manifest', manifest_path)]
    for item in cases_in:
        require(isinstance(item, dict), 'manifest case is not an object')
        name = str(item.get('name', ''))
        require(name, 'manifest case missing name')
        run_dir = Path(str(item.get('run_dir', '')))
        input_path = Path(str(item.get('input_file', run_dir / 'inputs')))
        run_log = Path(str(item.get('run_log', run_dir / 'run.log')))
        validation_log = Path(str(item.get('validation_log', run_dir / 'validation.log')))
        metrics = parse_validation_metrics(validation_log)
        case = {
            'name': name,
            'run_dir': archive_path_text(run_dir),
            'input_file': archive_path_text(input_path),
            'run_log': archive_path_text(run_log),
            'validation_log': archive_path_text(validation_log),
            'n_cell': [int(v) for v in item['n_cell']],
            'prob_lo': [float(v) for v in item['prob_lo']],
            'prob_hi': [float(v) for v in item['prob_hi']],
            'max_step': int(item['max_step']),
            'plotfile_initial': archive_path_text(Path(str(item['plotfile_initial']))),
            'plotfile_final': archive_path_text(Path(str(item['plotfile_final']))),
            'metrics': metrics,
        }
        validate_case_metrics(case)
        cases.append(case)
        evidence_files.extend([
            evidence_entry(f'{name}_input', input_path),
            evidence_entry(f'{name}_run_log', run_log),
            evidence_entry(f'{name}_validation_log', validation_log),
        ])

    cases.sort(key=lambda case: int(case['n_cell'][0]))
    speeds = [float(case['metrics']['front_speed']) for case in cases]
    speed_rel_spread = (max(speeds) - min(speeds)) / max(sum(speeds) / len(speeds), 1.0e-300)
    medium_fine_speed_rel_diff = abs(speeds[-1] - speeds[-2]) / max(abs(speeds[-1]), 1.0e-300)
    max_mass_rel = max(abs(float(case['metrics']['mass_rel'])) for case in cases)
    max_species_closure_rel = max(float(case['metrics']['species_closure_rel']) for case in cases)
    min_front_shift_cells = min(float(case['metrics']['front_shift_cells']) for case in cases)
    require(speed_rel_spread <= float(args.max_speed_rel_spread), f'front-speed spread too high: {speed_rel_spread}')
    require(
        medium_fine_speed_rel_diff <= float(args.max_medium_fine_speed_rel_diff),
        f'medium/fine front-speed difference too high: {medium_fine_speed_rel_diff}',
    )

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Gas 3D Detonation Reference Validation',
        'scope': 'multi-resolution 3D PeleC ZND-style detonation slab wave-motion, conservation, species-closure, and chemistry-product validation',
        'case_manifest': str(manifest_path),
        'case_count': len(cases),
        'cases': cases,
        'summary': {
            'case_count': len(cases),
            'resolutions': [case['n_cell'] for case in cases],
            'front_speeds_m_per_s': speeds,
            'speed_rel_spread': speed_rel_spread,
            'medium_fine_speed_rel_diff': medium_fine_speed_rel_diff,
            'max_speed_rel_spread_limit': float(args.max_speed_rel_spread),
            'max_medium_fine_speed_rel_diff_limit': float(args.max_medium_fine_speed_rel_diff),
            'max_mass_rel': max_mass_rel,
            'max_species_closure_rel': max_species_closure_rel,
            'min_front_shift_cells': min_front_shift_cells,
            'clears_three_d_detonation_reference_validation_gap': True,
            'clears_detonation_front_amr_validation_gap': False,
            'clears_external_literature_detonation_benchmark': False,
        },
        'quality_gate_matrix': [
            {'name': 'multi_resolution_3d_runs', 'status': 'PASS', 'gap': '', 'evidence': [str(manifest_path)]},
            {'name': 'plotfile_physics_validation', 'status': 'PASS', 'gap': '', 'evidence': [case['validation_log'] for case in cases]},
            {'name': 'front_speed_grid_consistency', 'status': 'PASS', 'gap': '', 'evidence': [str(manifest_path)]},
            {'name': 'mass_and_species_closure', 'status': 'PASS', 'gap': '', 'evidence': [case['validation_log'] for case in cases]},
            {
                'name': 'detonation_front_amr_validation',
                'status': 'PARTIAL',
                'gap': 'This gate uses uniform 3D grids; AMR front tagging/refinement efficiency is validated separately.',
                'evidence': [],
            },
            {
                'name': 'external_literature_reference',
                'status': 'PARTIAL',
                'gap': 'This is an in-repository ZND-style reference gate; no external literature detonation benchmark is attached.',
                'evidence': [],
            },
        ],
        'blocking_gaps': ['detonation_front_amr_validation', 'external_literature_reference'],
        'next_required_artifacts': [
            'detonation-front AMR tagging/refinement efficiency validation',
            'external or canonical literature 3D detonation reference case for full academic certification',
        ],
        'evidence_files': evidence_files,
        'limitations': [
            'This clears the maintained 3D detonation readiness gate using multi-resolution solver evidence.',
            'The case is a thin 3D ZND-style slab, not a fully 3D cellular detonation benchmark.',
            'It does not by itself clear detonation-front AMR validation or external literature agreement.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(summ.get('clears_three_d_detonation_reference_validation_gap') is True, '3D gap not cleared')
    require(summ.get('clears_detonation_front_amr_validation_gap') is False, 'AMR validation cannot be cleared here')
    require(int(summ.get('case_count', 0)) >= 3, 'too few cases')
    require(float(summ.get('speed_rel_spread', math.inf)) <= float(summ.get('max_speed_rel_spread_limit', 0.0)), 'speed spread too high')
    require(
        float(summ.get('medium_fine_speed_rel_diff', math.inf))
        <= float(summ.get('max_medium_fine_speed_rel_diff_limit', 0.0)),
        'medium/fine speed difference too high',
    )
    require(float(summ.get('max_mass_rel', math.inf)) <= 5.0e-11, 'mass conservation gap')
    require(float(summ.get('max_species_closure_rel', math.inf)) <= 1.0e-10, 'species closure gap')
    require(float(summ.get('min_front_shift_cells', 0.0)) >= 3.0, 'front shift too small')
    cases = data.get('cases')
    require(isinstance(cases, list) and len(cases) == int(summ['case_count']), 'case count mismatch')
    for case in cases:
        require(isinstance(case, dict), 'case is not an object')
        validate_case_metrics(case)
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    allowed = ['detonation_front_amr_validation', 'external_literature_reference']
    non_pass = [item.get('name') for item in gates if isinstance(item, dict) and item.get('status') != 'PASS']
    require(non_pass == allowed, f'unexpected non-PASS gates: {non_pass}')
    if check_hashes:
        entries = data.get('evidence_files')
        require(isinstance(entries, list) and entries, 'evidence_files missing')
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = resolve_evidence_path(Path(str(item.get('path', ''))))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Academic Gas 3D Detonation Reference Validation',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Cases', '', '| Case | n_cell | front speed | shift cells | mass rel | species closure |', '| --- | --- | --- | --- | --- | --- |']
    for case in report['cases']:
        metrics = case['metrics']
        lines.append(
            f"| `{case['name']}` | `{case['n_cell']}` | `{float(metrics['front_speed']):.8e}` | "
            f"`{float(metrics['front_shift_cells']):.3f}` | `{float(metrics['mass_rel']):.3e}` | "
            f"`{float(metrics['species_closure_rel']):.3e}` |"
        )
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['gap'] or 'none'} |")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--max-speed-rel-spread', type=float, default=0.35)
    parser.add_argument('--max-medium-fine-speed-rel-diff', type=float, default=0.25)
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summ = report.get('summary', {})
            print(
                'academic_gas_3d_detonation_reference VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"cases={summ.get('case_count')} speed_spread={summ.get('speed_rel_spread')}"
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
            'academic_gas_3d_detonation_reference PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"cases={report['summary']['case_count']} "
            f"speed_spread={report['summary']['speed_rel_spread']:.6g}"
        )
        return 0
    except Detonation3DReferenceError as exc:
        print(f'academic_gas_3d_detonation_reference FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
