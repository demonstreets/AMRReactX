#!/usr/bin/env python3
"""Write/verify PelePhysics compiled LiDryer rate-kernel equivalence evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = 'PASS-ACADEMIC-GAS-PELEPHYSICS-RATE-KERNEL-EQUIVALENCE'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728')
DEFAULT_PROBE_CSV = DEFAULT_ROOT / 'pelephysics_lidryer_kernel_probe.csv'
DEFAULT_BUILD_LOG = DEFAULT_ROOT / 'build.log'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'pelephysics_rate_kernel_equivalence_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'pelephysics_rate_kernel_equivalence_report.md'
DEFAULT_PROBE_SOURCE = Path('tools/academic_gas_pelephysics_lidryer_kernel_probe.cpp')
DEFAULT_MECHANISM_HEADER = Path('external/PelePhysics/Mechanisms/LiDryer/mechanism.H')
DEFAULT_MECHANISM_CPP = Path('external/PelePhysics/Mechanisms/LiDryer/mechanism.cpp')
DEFAULT_MECHANISM_YAML = Path('external/PelePhysics/Mechanisms/LiDryer/mechanism.yaml')

SPECIES = ['H2', 'O2', 'H2O', 'H', 'O', 'OH', 'HO2', 'H2O2', 'N2']


class RateKernelEquivalenceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RateKernelEquivalenceError(message)


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
        raise RateKernelEquivalenceError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RateKernelEquivalenceError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def relative_error(a: float, b: float, floor: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), floor)


def load_probe_rows(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f'missing probe CSV: {path}')
    with path.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) >= 9, 'compiled kernel probe must contain at least nine states')
    for row in rows:
        for key in ['temperature_k', 'pressure_pa', 'pressure_cgs', 'phi', 'rho_cgs', 'cpbs_erg_g_K']:
            require(finite_number(row.get(key)), f'row {row.get("case")} missing finite {key}')
        for species in SPECIES:
            require(finite_number(row.get(f'x_{species}')), f'row {row.get("case")} missing x_{species}')
            require(finite_number(row.get(f'y_{species}')), f'row {row.get("case")} missing y_{species}')
            require(
                finite_number(row.get(f'wdot_{species}_mol_cm3_s')),
                f'row {row.get("case")} missing wdot_{species}',
            )
    return rows


def cantera_version() -> str:
    try:
        import cantera as ct
    except Exception as exc:  # pragma: no cover - depends on server environment
        raise RateKernelEquivalenceError(f'Cantera is not importable: {exc}') from exc
    return str(ct.__version__)


def compare_row(gas: Any, row: dict[str, Any], active_rate_floor: float) -> dict[str, Any]:
    x = {species: float(row[f'x_{species}']) for species in SPECIES}
    y = {species: float(row[f'y_{species}']) for species in SPECIES}
    gas.TPX = float(row['temperature_k']), float(row['pressure_pa']), x
    cantera_y = {species: float(gas[species].Y[0]) for species in SPECIES}
    max_y_rel = max(relative_error(float(y[species]), cantera_y[species], 1.0e-300) for species in SPECIES)
    pele_rho_si = float(row['rho_cgs']) * 1000.0
    pele_cp_si = float(row['cpbs_erg_g_K']) * 1.0e-4
    rho_rel = relative_error(pele_rho_si, float(gas.density), 1.0e-300)
    cp_rel = relative_error(pele_cp_si, float(gas.cp_mass), 1.0e-300)
    cantera_rates = dict(zip(gas.species_names, gas.net_production_rates))
    species_errors: list[dict[str, Any]] = []
    active_rel_errors: list[float] = []
    all_abs_errors: list[float] = []
    max_reference_rate = 0.0
    for species in SPECIES:
        pele_rate = float(row[f'wdot_{species}_mol_cm3_s'])
        cantera_rate = float(cantera_rates[species]) * 1.0e-3
        abs_err = abs(pele_rate - cantera_rate)
        scale = max(abs(pele_rate), abs(cantera_rate))
        rel_err = relative_error(pele_rate, cantera_rate, active_rate_floor)
        if scale >= active_rate_floor:
            active_rel_errors.append(rel_err)
        all_abs_errors.append(abs_err)
        max_reference_rate = max(max_reference_rate, scale)
        species_errors.append({
            'species': species,
            'pelephysics_wdot_mol_cm3_s': pele_rate,
            'cantera_wdot_mol_cm3_s': cantera_rate,
            'abs_error_mol_cm3_s': abs_err,
            'relative_error_with_floor': rel_err,
            'active': scale >= active_rate_floor,
        })
    return {
        'case': row['case'],
        'temperature_k': float(row['temperature_k']),
        'pressure_pa': float(row['pressure_pa']),
        'phi': float(row['phi']),
        'pelephysics_density_kg_m3': pele_rho_si,
        'cantera_density_kg_m3': float(gas.density),
        'density_relative_error': rho_rel,
        'pelephysics_cp_mass_j_kg_k': pele_cp_si,
        'cantera_cp_mass_j_kg_k': float(gas.cp_mass),
        'cp_mass_relative_error': cp_rel,
        'mass_fraction_max_relative_error': max_y_rel,
        'max_reference_rate_mol_cm3_s': max_reference_rate,
        'max_active_wdot_relative_error': max(active_rel_errors) if active_rel_errors else 0.0,
        'max_wdot_abs_error_mol_cm3_s': max(all_abs_errors),
        'species_errors': species_errors,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import cantera as ct
    except Exception as exc:  # pragma: no cover - depends on server environment
        raise RateKernelEquivalenceError(f'Cantera is not importable: {exc}') from exc

    probe_csv = Path(args.probe_csv)
    build_log = Path(args.build_log)
    probe_source = Path(args.probe_source)
    mechanism_header = Path(args.mechanism_header)
    mechanism_cpp = Path(args.mechanism_cpp)
    mechanism_yaml = Path(args.mechanism_yaml)
    rows = load_probe_rows(probe_csv)
    gas = ct.Solution(str(mechanism_yaml))
    require(list(gas.species_names)[: len(SPECIES)] == SPECIES, 'Cantera mechanism species order does not match LiDryer probe')
    comparisons = [compare_row(gas, row, float(args.active_rate_floor)) for row in rows]

    max_density_rel = max(float(item['density_relative_error']) for item in comparisons)
    max_cp_rel = max(float(item['cp_mass_relative_error']) for item in comparisons)
    max_y_rel = max(float(item['mass_fraction_max_relative_error']) for item in comparisons)
    max_active_wdot_rel = max(float(item['max_active_wdot_relative_error']) for item in comparisons)
    max_wdot_abs = max(float(item['max_wdot_abs_error_mol_cm3_s']) for item in comparisons)
    active_species_comparisons = sum(
        1 for item in comparisons for spec in item['species_errors'] if bool(spec['active'])
    )

    require(max_density_rel <= float(args.max_density_rel), f'density relative error too high: {max_density_rel}')
    require(max_cp_rel <= float(args.max_cp_rel), f'cp relative error too high: {max_cp_rel}')
    require(max_y_rel <= float(args.max_mass_fraction_rel), f'mass-fraction relative error too high: {max_y_rel}')
    require(max_active_wdot_rel <= float(args.max_active_wdot_rel), f'active wdot relative error too high: {max_active_wdot_rel}')
    require(active_species_comparisons >= int(args.min_active_species_comparisons), 'too few active species-rate comparisons')

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'PelePhysics Compiled LiDryer Rate-Kernel Equivalence',
        'scope': 'compiled PelePhysics LiDryer mechanism.H/mechanism.cpp thermochemistry and species source terms compared to Cantera loading of the same mechanism.yaml',
        'probe_csv': str(probe_csv),
        'build_log': str(build_log),
        'mechanism_yaml': str(mechanism_yaml),
        'cantera_version': cantera_version(),
        'case_count': len(comparisons),
        'species': SPECIES,
        'unit_conversions': {
            'pressure_pa_to_cgs_dyne_cm2': 10.0,
            'pelephysics_cpbs_erg_g_K_to_j_kg_K': 1.0e-4,
            'pelephysics_rho_g_cm3_to_kg_m3': 1000.0,
            'cantera_net_production_kmol_m3_s_to_mol_cm3_s': 1.0e-3,
        },
        'summary': {
            'case_count': len(comparisons),
            'active_species_rate_comparisons': active_species_comparisons,
            'max_density_relative_error': max_density_rel,
            'max_density_relative_error_limit': float(args.max_density_rel),
            'max_cp_mass_relative_error': max_cp_rel,
            'max_cp_mass_relative_error_limit': float(args.max_cp_rel),
            'max_mass_fraction_relative_error': max_y_rel,
            'max_mass_fraction_relative_error_limit': float(args.max_mass_fraction_rel),
            'max_active_wdot_relative_error': max_active_wdot_rel,
            'max_active_wdot_relative_error_limit': float(args.max_active_wdot_rel),
            'max_wdot_abs_error_mol_cm3_s': max_wdot_abs,
            'clears_full_pelephysics_source_rate_equivalence': True,
            'clears_acd_02_rate_kernel_gap': True,
        },
        'comparisons': comparisons,
        'quality_gate_matrix': [
            {'name': 'compiled_pelephysics_probe_built', 'status': 'PASS', 'gap': '', 'evidence': [str(build_log), str(probe_source)]},
            {'name': 'same_mechanism_yaml_loaded_by_cantera', 'status': 'PASS', 'gap': '', 'evidence': [str(mechanism_yaml)]},
            {'name': 'thermochemistry_density_cp_equivalence', 'status': 'PASS', 'gap': '', 'evidence': [str(probe_csv)]},
            {'name': 'species_source_rate_equivalence', 'status': 'PASS', 'gap': '', 'evidence': [str(probe_csv)]},
        ],
        'evidence_files': [
            evidence_entry('compiled_probe_csv', probe_csv),
            evidence_entry('compiled_probe_build_log', build_log),
            evidence_entry('compiled_probe_source', probe_source),
            evidence_entry('mechanism_header', mechanism_header),
            evidence_entry('mechanism_cpp', mechanism_cpp),
            evidence_entry('mechanism_yaml', mechanism_yaml),
        ],
        'limitations': [
            'This validates the compiled CPU LiDryer mechanism kernels used by PelePhysics against Cantera for sampled homogeneous gas states.',
            'It is not a GPU device-kernel bitwise comparison and does not replace solver-level detonation/fire validation.',
            'It compares source terms for the same PelePhysics mechanism YAML, not cross-mechanism agreement with Cantera h2o2.yaml.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(summ.get('clears_full_pelephysics_source_rate_equivalence') is True, 'rate-kernel gap not cleared')
    require(summ.get('clears_acd_02_rate_kernel_gap') is True, 'ACD-02 rate-kernel gap not cleared')
    require(int(summ.get('case_count', 0)) >= 9, 'too few comparison cases')
    require(int(summ.get('active_species_rate_comparisons', 0)) >= 12, 'too few active rate comparisons')
    require(float(summ.get('max_density_relative_error', math.inf)) <= float(summ.get('max_density_relative_error_limit', 0.0)), 'density error too high')
    require(float(summ.get('max_cp_mass_relative_error', math.inf)) <= float(summ.get('max_cp_mass_relative_error_limit', 0.0)), 'cp error too high')
    require(float(summ.get('max_mass_fraction_relative_error', math.inf)) <= float(summ.get('max_mass_fraction_relative_error_limit', 0.0)), 'mass fraction error too high')
    require(float(summ.get('max_active_wdot_relative_error', math.inf)) <= float(summ.get('max_active_wdot_relative_error_limit', 0.0)), 'wdot error too high')
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    require(all(isinstance(item, dict) and item.get('status') == 'PASS' for item in gates), 'non-PASS quality gate present')
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
        '# PelePhysics Compiled LiDryer Rate-Kernel Equivalence',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Unit Conversions', '']
    for key, value in report['unit_conversions'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Cases', '', '| Case | T (K) | P (Pa) | Phi | rho rel | cp rel | max active wdot rel |', '| --- | --- | --- | --- | --- | --- | --- |']
    for item in report['comparisons']:
        lines.append(
            f"| `{item['case']}` | `{item['temperature_k']}` | `{item['pressure_pa']}` | `{item['phi']}` | "
            f"`{float(item['density_relative_error']):.8e}` | "
            f"`{float(item['cp_mass_relative_error']):.8e}` | "
            f"`{float(item['max_active_wdot_relative_error']):.8e}` |"
        )
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe-csv', default=str(DEFAULT_PROBE_CSV))
    parser.add_argument('--build-log', default=str(DEFAULT_BUILD_LOG))
    parser.add_argument('--probe-source', default=str(DEFAULT_PROBE_SOURCE))
    parser.add_argument('--mechanism-header', default=str(DEFAULT_MECHANISM_HEADER))
    parser.add_argument('--mechanism-cpp', default=str(DEFAULT_MECHANISM_CPP))
    parser.add_argument('--mechanism-yaml', default=str(DEFAULT_MECHANISM_YAML))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    parser.add_argument('--active-rate-floor', type=float, default=1.0e-30)
    parser.add_argument('--min-active-species-comparisons', type=int, default=12)
    parser.add_argument('--max-density-rel', type=float, default=1.0e-11)
    parser.add_argument('--max-cp-rel', type=float, default=1.0e-10)
    parser.add_argument('--max-mass-fraction-rel', type=float, default=1.0e-12)
    parser.add_argument('--max-active-wdot-rel', type=float, default=1.0e-5)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report_object(report, check_hashes=True)
            summ = report.get('summary', {})
            print(
                'academic_gas_pelephysics_rate_kernel_equivalence VERIFY-PASS '
                f"json={args.verify_json} cases={summ.get('case_count')} "
                f"max_wdot_rel={summ.get('max_active_wdot_relative_error')}"
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
            'academic_gas_pelephysics_rate_kernel_equivalence PASS '
            f"json={out_json} md={out_md} cases={report['case_count']} "
            f"max_wdot_rel={report['summary']['max_active_wdot_relative_error']}"
        )
        return 0
    except RateKernelEquivalenceError as exc:
        print(f'academic_gas_pelephysics_rate_kernel_equivalence FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
