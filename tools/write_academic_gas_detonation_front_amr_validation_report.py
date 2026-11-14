#!/usr/bin/env python3
"""Write/verify the academic gas detonation-front AMR validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-GAS-DETONATION-FRONT-AMR-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'case_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_gas_detonation_front_amr_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_gas_detonation_front_amr_validation_report.md'
REMOTE_REPO_ROOT_TEXT = '/' + '/'.join(('home', 'cj', 'my-pele'))
REMOTE_REPO_ROOT = Path(REMOTE_REPO_ROOT_TEXT)

METRIC_RE = re.compile(r'^academic_gas_detonation_front_amr_validation PASS\s+(.*)$', re.MULTILINE)


class DetonationFrontAMRError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DetonationFrontAMRError(message)


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
        raise DetonationFrontAMRError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise DetonationFrontAMRError(f'invalid JSON evidence {path}: {exc}') from exc
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


def validate_common_case(case: dict[str, Any]) -> None:
    metrics = case['metrics']
    for key in [
        'front_shift',
        'front_shift_cells',
        'front_speed',
        'temp_mean_delta',
        'h2o_mass_delta_abs',
        'mass_rel',
        'species_closure_rel',
    ]:
        require(finite_number(metrics.get(key)), f'{case["name"]} missing finite metric {key}')
    require(float(metrics['front_shift']) > 0.0, f'{case["name"]} front did not move forward')
    require(float(metrics['front_shift_cells']) >= 3.0, f'{case["name"]} front shift too small in cells')
    require(1.0e4 <= float(metrics['front_speed']) <= 1.0e8, f'{case["name"]} front speed out of sanity bounds')
    require(float(metrics['temp_mean_delta']) > 1.0, f'{case["name"]} temperature field changed too little')
    require(float(metrics['h2o_mass_delta_abs']) > 1.0e-12, f'{case["name"]} H2O product mass changed too little')
    require(float(metrics['mass_rel']) <= 5.0e-11, f'{case["name"]} mass conservation failed')
    require(float(metrics['species_closure_rel']) <= 1.0e-10, f'{case["name"]} species closure failed')


def validate_amr_case(case: dict[str, Any], max_refined_fraction: float) -> None:
    validate_common_case(case)
    metrics = case['metrics']
    require(case.get('amr_enabled') is True, f'{case["name"]} is not marked AMR-enabled')
    require(float(metrics.get('finest_level1', 0.0)) >= 1.0, f'{case["name"]} did not produce a refined level')
    require(float(metrics.get('front_refined', 0.0)) == 1.0, f'{case["name"]} did not refine the front')
    require(float(metrics.get('refined_cell_count', 0.0)) > 0.0, f'{case["name"]} has no refined cells')
    fraction = float(metrics.get('refined_cell_fraction', math.inf))
    require(1.0e-4 <= fraction <= max_refined_fraction, f'{case["name"]} refined-cell fraction outside limits: {fraction}')


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    cases_in = manifest.get('cases')
    require(isinstance(cases_in, list) and len(cases_in) >= 2, 'manifest must contain AMR and uniform reference cases')
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
            'role': str(item.get('role', '')),
            'amr_enabled': bool(item.get('amr_enabled', False)),
            'run_dir': archive_path_text(run_dir),
            'input_file': archive_path_text(input_path),
            'run_log': archive_path_text(run_log),
            'validation_log': archive_path_text(validation_log),
            'n_cell': [int(v) for v in item['n_cell']],
            'max_level': int(item.get('max_level', 0)),
            'ref_ratio': int(item.get('ref_ratio', 1)),
            'max_step': int(item['max_step']),
            'plotfile_initial': archive_path_text(Path(str(item['plotfile_initial']))),
            'plotfile_final': archive_path_text(Path(str(item['plotfile_final']))),
            'metrics': metrics,
        }
        validate_common_case(case)
        if case['amr_enabled']:
            validate_amr_case(case, float(args.max_refined_cell_fraction))
        cases.append(case)
        evidence_files.extend([
            evidence_entry(f'{name}_input', input_path),
            evidence_entry(f'{name}_run_log', run_log),
            evidence_entry(f'{name}_validation_log', validation_log),
        ])

    amr_cases = [case for case in cases if case['amr_enabled']]
    uniform_cases = [case for case in cases if case['role'] == 'uniform_fine_reference']
    require(len(amr_cases) >= 1, 'manifest contains no AMR-enabled case')
    require(len(uniform_cases) >= 1, 'manifest contains no uniform fine reference case')
    amr_case = amr_cases[0]
    uniform_case = uniform_cases[0]
    amr_speed = float(amr_case['metrics']['front_speed'])
    uniform_speed = float(uniform_case['metrics']['front_speed'])
    speed_rel_diff = abs(amr_speed - uniform_speed) / max(abs(uniform_speed), 1.0e-300)
    require(speed_rel_diff <= float(args.max_amr_uniform_speed_rel_diff), f'AMR/uniform speed difference too high: {speed_rel_diff}')

    max_mass_rel = max(float(case['metrics']['mass_rel']) for case in cases)
    max_species_closure_rel = max(float(case['metrics']['species_closure_rel']) for case in cases)
    min_front_shift_cells = min(float(case['metrics']['front_shift_cells']) for case in cases)
    amr_refined_fraction = float(amr_case['metrics']['refined_cell_fraction'])
    equivalent_uniform_cells = (
        int(amr_case['n_cell'][0])
        * int(amr_case['n_cell'][1])
        * int(amr_case['n_cell'][2])
        * int(amr_case['ref_ratio']) ** 3
    )
    amr_actual_finest_cells = float(amr_case['metrics']['refined_cell_count'])
    refined_cell_savings_fraction = 1.0 - amr_actual_finest_cells / max(float(equivalent_uniform_cells), 1.0)

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Gas Detonation-Front AMR Validation',
        'scope': '3D PeleC ZND-style detonation AMR tagging, front refinement, conservation, and uniform-fine consistency gate',
        'case_manifest': str(manifest_path),
        'case_count': len(cases),
        'cases': cases,
        'summary': {
            'case_count': len(cases),
            'amr_case': amr_case['name'],
            'uniform_fine_reference_case': uniform_case['name'],
            'amr_front_speed_m_per_s': amr_speed,
            'uniform_fine_front_speed_m_per_s': uniform_speed,
            'amr_uniform_speed_rel_diff': speed_rel_diff,
            'max_amr_uniform_speed_rel_diff_limit': float(args.max_amr_uniform_speed_rel_diff),
            'amr_refined_cell_fraction': amr_refined_fraction,
            'max_refined_cell_fraction_limit': float(args.max_refined_cell_fraction),
            'refined_cell_savings_fraction_vs_full_level1_uniform': refined_cell_savings_fraction,
            'max_mass_rel': max_mass_rel,
            'max_species_closure_rel': max_species_closure_rel,
            'min_front_shift_cells': min_front_shift_cells,
            'clears_detonation_front_amr_validation_gap': True,
            'clears_external_literature_detonation_benchmark': False,
        },
        'quality_gate_matrix': [
            {'name': 'amr_refined_level_created', 'status': 'PASS', 'gap': '', 'evidence': [amr_case['validation_log']]},
            {'name': 'detonation_front_refined', 'status': 'PASS', 'gap': '', 'evidence': [amr_case['validation_log']]},
            {'name': 'amr_refinement_efficiency', 'status': 'PASS', 'gap': '', 'evidence': [amr_case['validation_log']]},
            {'name': 'amr_uniform_front_speed_consistency', 'status': 'PASS', 'gap': '', 'evidence': [str(manifest_path)]},
            {'name': 'mass_and_species_closure', 'status': 'PASS', 'gap': '', 'evidence': [case['validation_log'] for case in cases]},
            {
                'name': 'external_literature_reference',
                'status': 'PARTIAL',
                'gap': 'This is an in-repository AMR gate; no external literature detonation AMR benchmark is attached.',
                'evidence': [],
            },
        ],
        'blocking_gaps': ['external_literature_reference'],
        'next_required_artifacts': [
            'external or canonical literature detonation-front AMR benchmark for full academic certification',
        ],
        'evidence_files': evidence_files,
        'limitations': [
            'This clears the maintained detonation-front AMR readiness gate using solver-generated 3D evidence.',
            'The AMR comparison is against an in-repository uniform-fine reference, not an external experiment.',
            'The case is a thin 3D ZND-style slab and does not represent full cellular detonation morphology.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(summ.get('clears_detonation_front_amr_validation_gap') is True, 'AMR gap not cleared')
    require(int(summ.get('case_count', 0)) >= 2, 'too few cases')
    require(
        float(summ.get('amr_uniform_speed_rel_diff', math.inf))
        <= float(summ.get('max_amr_uniform_speed_rel_diff_limit', 0.0)),
        'AMR/uniform speed difference too high',
    )
    require(float(summ.get('amr_refined_cell_fraction', math.inf)) <= float(summ.get('max_refined_cell_fraction_limit', 0.0)), 'AMR refined fraction too high')
    require(float(summ.get('max_mass_rel', math.inf)) <= 5.0e-11, 'mass conservation gap')
    require(float(summ.get('max_species_closure_rel', math.inf)) <= 1.0e-10, 'species closure gap')
    require(float(summ.get('min_front_shift_cells', 0.0)) >= 3.0, 'front shift too small')
    cases = data.get('cases')
    require(isinstance(cases, list) and len(cases) == int(summ['case_count']), 'case count mismatch')
    for case in cases:
        require(isinstance(case, dict), 'case is not an object')
        validate_common_case(case)
        if bool(case.get('amr_enabled', False)):
            validate_amr_case(case, float(summ['max_refined_cell_fraction_limit']))
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    non_pass = [item.get('name') for item in gates if isinstance(item, dict) and item.get('status') != 'PASS']
    require(non_pass == ['external_literature_reference'], f'unexpected non-PASS gates: {non_pass}')
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
        '# Academic Gas Detonation-Front AMR Validation',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Cases', '', '| Case | Role | AMR | n_cell | Front speed | Finest level | Refined fraction | Mass rel |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for case in report['cases']:
        metrics = case['metrics']
        lines.append(
            f"| `{case['name']}` | `{case['role']}` | `{case['amr_enabled']}` | "
            f"`{case['n_cell']}` | `{float(metrics['front_speed']):.8e}` | "
            f"`{int(float(metrics['finest_level1']))}` | "
            f"`{float(metrics.get('refined_cell_fraction', 0.0)):.8e}` | "
            f"`{float(metrics['mass_rel']):.8e}` |"
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
    parser.add_argument('--max-amr-uniform-speed-rel-diff', type=float, default=0.30)
    parser.add_argument('--max-refined-cell-fraction', type=float, default=0.85)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report_object(report, check_hashes=True)
            summ = report.get('summary', {})
            print(
                'academic_gas_detonation_front_amr_validation VERIFY-PASS '
                f"json={args.verify_json} cases={summ.get('case_count')} "
                f"speed_rel_diff={summ.get('amr_uniform_speed_rel_diff')} "
                f"refined_fraction={summ.get('amr_refined_cell_fraction')}"
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
            'academic_gas_detonation_front_amr_validation PASS '
            f"json={out_json} md={out_md} cases={report['case_count']} "
            f"speed_rel_diff={report['summary']['amr_uniform_speed_rel_diff']}"
        )
        return 0
    except DetonationFrontAMRError as exc:
        print(f'academic_gas_detonation_front_amr_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
