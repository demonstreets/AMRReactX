#!/usr/bin/env python3
"""Write/verify a Cantera mechanism comparison report for academic gas readiness."""
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
STATUS_PASS = 'PASS-ACADEMIC-GAS-CANTERA-MECHANISM-COMPARISON'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-GAS-CANTERA-MECHANISM-COMPARISON'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'cantera_mechanism_comparison_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'cantera_mechanism_comparison_report.md'
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / 'cantera_mechanism_comparison_curve.csv'
DEFAULT_PELEPHYSICS_MECHANISM = Path('external/PelePhysics/Mechanisms/LiDryer/mechanism.yaml')
DEFAULT_REFERENCE_MECHANISM = 'h2o2.yaml'
DEFAULT_TEMPERATURES_K = (1000.0, 1100.0, 1200.0, 1300.0)
DEFAULT_PRESSURE_PA = 101325.0
DEFAULT_COMPOSITION = 'H2:2,O2:1,N2:3.76'
REQUIRED_H2_SPECIES = {'H2', 'O2', 'H2O', 'OH', 'H', 'O', 'HO2', 'H2O2', 'N2'}


class MechanismComparisonError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MechanismComparisonError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def finite_values(values: Any) -> bool:
    try:
        return all(math.isfinite(float(value)) for value in values)
    except TypeError:
        return False


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise MechanismComparisonError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise MechanismComparisonError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def parse_temperatures(text: str) -> list[float]:
    vals = [float(item.strip()) for item in text.split(',') if item.strip()]
    require(len(vals) >= 3, 'at least three temperatures are required')
    require(all(math.isfinite(v) and v > 0.0 for v in vals), 'temperatures must be finite and positive')
    return sorted(vals)


def cantera_version() -> str:
    try:
        import cantera as ct
    except Exception as exc:  # pragma: no cover - depends on server environment
        raise MechanismComparisonError(f'Cantera is not importable: {exc}') from exc
    return str(ct.__version__)


def load_solution(mechanism: str):
    try:
        import cantera as ct
    except Exception as exc:  # pragma: no cover - depends on server environment
        raise MechanismComparisonError(f'Cantera is not importable: {exc}') from exc
    try:
        return ct.Solution(mechanism)
    except Exception as exc:
        raise MechanismComparisonError(f'Cantera failed to load mechanism {mechanism}: {exc}') from exc


def mechanism_identity(label: str, mechanism: str) -> dict[str, Any]:
    gas = load_solution(mechanism)
    species = set(gas.species_names)
    missing = sorted(REQUIRED_H2_SPECIES - species)
    require(not missing, f'{label} mechanism missing required H2 species: {missing}')
    return {
        'label': label,
        'mechanism': mechanism,
        'n_species': int(gas.n_species),
        'n_elements': int(gas.n_elements),
        'n_reactions': int(gas.n_reactions),
        'species_names': list(gas.species_names),
        'element_names': list(gas.element_names),
    }


def sample_state_metrics(label: str, mechanism: str, temperature_k: float, pressure_pa: float, composition: str) -> dict[str, Any]:
    gas = load_solution(mechanism)
    gas.TPX = temperature_k, pressure_pa, composition
    fwd = gas.forward_rates_of_progress
    rev = gas.reverse_rates_of_progress
    net = gas.net_rates_of_progress
    prod = gas.net_production_rates
    require(finite_values(fwd), f'{label} forward rates are non-finite at T={temperature_k}')
    require(finite_values(rev), f'{label} reverse rates are non-finite at T={temperature_k}')
    require(finite_values(net), f'{label} net rates are non-finite at T={temperature_k}')
    require(finite_values(prod), f'{label} net production rates are non-finite at T={temperature_k}')
    scalars = {
        'cp_mass': float(gas.cp_mass),
        'enthalpy_mass': float(gas.enthalpy_mass),
        'entropy_mass': float(gas.entropy_mass),
        'density': float(gas.density),
        'mean_molecular_weight': float(gas.mean_molecular_weight),
        'max_abs_forward_rate': max(abs(float(v)) for v in fwd),
        'max_abs_reverse_rate': max(abs(float(v)) for v in rev),
        'max_abs_net_rate': max(abs(float(v)) for v in net),
        'max_abs_net_production_rate': max(abs(float(v)) for v in prod),
    }
    for key, value in scalars.items():
        require(finite_number(value), f'{label} {key} is non-finite at T={temperature_k}')
    return {
        'mechanism_label': label,
        'temperature_k': float(temperature_k),
        'pressure_pa': float(pressure_pa),
        **scalars,
    }


def run_ignition_case(
    label: str,
    mechanism: str,
    temperature_k: float,
    pressure_pa: float,
    composition: str,
    end_time_s: float,
    max_steps: int,
) -> dict[str, Any]:
    try:
        import cantera as ct
    except Exception as exc:  # pragma: no cover - depends on server environment
        raise MechanismComparisonError(f'Cantera is not importable: {exc}') from exc

    gas = ct.Solution(mechanism)
    gas.TPX = temperature_k, pressure_pa, composition
    reactor = ct.IdealGasReactor(gas, energy='on', clone=False)
    network = ct.ReactorNet([reactor])
    times: list[float] = []
    temps: list[float] = []
    oh_x: list[float] = []
    previous_t = 0.0
    for _ in range(max_steps):
        current_t = float(network.step())
        require(current_t > previous_t, f'{label} reactor time did not advance at T={temperature_k}')
        previous_t = current_t
        times.append(current_t)
        temps.append(float(reactor.T))
        oh_x.append(float(reactor.phase['OH'].X[0]))
        if current_t >= end_time_s:
            break
    require(times and times[-1] >= end_time_s, f'{label} T={temperature_k} K did not reach end_time_s={end_time_s}')
    max_temp_rise_k = max(temps) - temperature_k
    require(max_temp_rise_k > 100.0, f'{label} T={temperature_k} K did not ignite strongly enough')
    max_oh_idx = max(range(len(oh_x)), key=lambda idx: oh_x[idx])
    return {
        'mechanism_label': label,
        'temperature_k': float(temperature_k),
        'pressure_pa': float(pressure_pa),
        'composition': composition,
        'ignition_delay_s': float(times[max_oh_idx]),
        'max_oh_mole_fraction': float(oh_x[max_oh_idx]),
        'max_temperature_k': float(max(temps)),
        'max_temp_rise_k': float(max_temp_rise_k),
        'end_time_s': float(times[-1]),
        'steps': len(times),
    }


def validate_ignition_rows(rows: list[dict[str, Any]], labels: list[str]) -> None:
    for label in labels:
        subset = sorted((row for row in rows if row['mechanism_label'] == label), key=lambda row: float(row['temperature_k']))
        require(len(subset) >= 3, f'{label} ignition curve has too few cases')
        delays = [float(row['ignition_delay_s']) for row in subset]
        require(all(finite_number(v) and v > 0.0 for v in delays), f'{label} ignition delays are invalid')
        require(all(delays[idx] > delays[idx + 1] for idx in range(len(delays) - 1)), f'{label} ignition delay is not monotonic')
        require(all(float(row['max_temp_rise_k']) > 100.0 for row in subset), f'{label} ignition temperature rise is too weak')


def compare_ignition_rows(rows: list[dict[str, Any]], ratio_limit: float) -> list[dict[str, Any]]:
    by_temp: dict[float, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_temp.setdefault(float(row['temperature_k']), {})[str(row['mechanism_label'])] = row
    comparisons: list[dict[str, Any]] = []
    for temperature_k in sorted(by_temp):
        pair = by_temp[temperature_k]
        require('pelephysics_lidryer' in pair and 'cantera_h2o2' in pair, f'missing paired ignition case at T={temperature_k}')
        pele_delay = float(pair['pelephysics_lidryer']['ignition_delay_s'])
        ref_delay = float(pair['cantera_h2o2']['ignition_delay_s'])
        ratio = max(pele_delay, ref_delay) / min(pele_delay, ref_delay)
        require(math.isfinite(ratio) and ratio <= ratio_limit, f'ignition delay ratio {ratio} exceeds limit {ratio_limit} at T={temperature_k}')
        comparisons.append({
            'temperature_k': temperature_k,
            'pelephysics_lidryer_delay_s': pele_delay,
            'cantera_h2o2_delay_s': ref_delay,
            'delay_ratio': ratio,
        })
    return comparisons


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'kind',
        'mechanism_label',
        'temperature_k',
        'pressure_pa',
        'composition',
        'ignition_delay_s',
        'max_oh_mole_fraction',
        'max_temperature_k',
        'max_temp_rise_k',
        'end_time_s',
        'steps',
        'cp_mass',
        'enthalpy_mass',
        'entropy_mass',
        'density',
        'mean_molecular_weight',
        'max_abs_forward_rate',
        'max_abs_reverse_rate',
        'max_abs_net_rate',
        'max_abs_net_production_rate',
    ]
    with path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f'missing comparison CSV: {path}')
    with path.open('r', encoding='utf-8', newline='') as fh:
        rows = list(csv.DictReader(fh))
    require(rows, 'comparison CSV has no rows')
    return rows


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pele_mechanism = str(Path(args.pelephysics_mechanism))
    reference_mechanism = str(args.reference_mechanism)
    require(Path(pele_mechanism).is_file(), f'missing PelePhysics mechanism YAML: {pele_mechanism}')
    temperatures = parse_temperatures(args.temperatures_k)
    pressure_pa = float(args.pressure_pa)
    ratio_limit = float(args.ignition_delay_ratio_limit)
    require(ratio_limit >= 1.0, 'ignition delay ratio limit must be >= 1')

    identities = [
        mechanism_identity('pelephysics_lidryer', pele_mechanism),
        mechanism_identity('cantera_h2o2', reference_mechanism),
    ]
    pele_species = set(identities[0]['species_names'])
    ref_species = set(identities[1]['species_names'])
    required_shared = sorted(REQUIRED_H2_SPECIES & pele_species & ref_species)
    require(set(required_shared) == REQUIRED_H2_SPECIES, 'required H2 species are not shared by both mechanisms')

    state_rows: list[dict[str, Any]] = []
    ignition_rows: list[dict[str, Any]] = []
    for temperature_k in temperatures:
        state_rows.append({
            'kind': 'state_rate_sample',
            **sample_state_metrics('pelephysics_lidryer', pele_mechanism, temperature_k, pressure_pa, args.composition),
        })
        state_rows.append({
            'kind': 'state_rate_sample',
            **sample_state_metrics('cantera_h2o2', reference_mechanism, temperature_k, pressure_pa, args.composition),
        })
        ignition_rows.append({
            'kind': 'ignition_case',
            **run_ignition_case(
                'pelephysics_lidryer',
                pele_mechanism,
                temperature_k,
                pressure_pa,
                args.composition,
                float(args.end_time_s),
                int(args.max_steps),
            ),
        })
        ignition_rows.append({
            'kind': 'ignition_case',
            **run_ignition_case(
                'cantera_h2o2',
                reference_mechanism,
                temperature_k,
                pressure_pa,
                args.composition,
                float(args.end_time_s),
                int(args.max_steps),
            ),
        })

    validate_ignition_rows(ignition_rows, ['pelephysics_lidryer', 'cantera_h2o2'])
    comparisons = compare_ignition_rows(ignition_rows, ratio_limit)
    max_delay_ratio = max(float(item['delay_ratio']) for item in comparisons)
    csv_rows = state_rows + ignition_rows
    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Gas Cantera Mechanism Comparison',
        'scope': 'Cantera-loadable PelePhysics LiDryer vs Cantera h2o2 thermochemistry, finite rates, and 0D ignition-delay comparison',
        'cantera_version': cantera_version(),
        'pelephysics_mechanism': pele_mechanism,
        'reference_mechanism': reference_mechanism,
        'pressure_pa': pressure_pa,
        'composition': args.composition,
        'temperatures_k': temperatures,
        'comparison_csv': str(Path(args.output_csv)),
        'summary': {
            'mechanism_count': len(identities),
            'shared_required_h2_species': required_shared,
            'state_rate_sample_count': len(state_rows),
            'ignition_case_count': len(ignition_rows),
            'ignition_delay_pair_count': len(comparisons),
            'max_ignition_delay_ratio': max_delay_ratio,
            'ignition_delay_ratio_limit': ratio_limit,
            'pelephysics_yaml_loads_in_cantera': True,
            'reference_h2o2_yaml_loads_in_cantera': True,
            'thermochemistry_samples_finite': True,
            'reaction_rate_samples_finite': True,
            'ignition_delay_curves_monotonic': True,
            'ignition_delay_curves_same_order': True,
            'clears_cantera_mechanism_comparison_gap': True,
            'clears_full_pelephysics_source_rate_equivalence': False,
        },
        'mechanisms': identities,
        'ignition_delay_comparison': comparisons,
        'quality_gate_matrix': [
            {'name': 'cantera_importable', 'status': 'PASS', 'gap': '', 'evidence': ['cantera_version']},
            {'name': 'pelephysics_lidryer_loadable', 'status': 'PASS', 'gap': '', 'evidence': [pele_mechanism]},
            {'name': 'reference_h2o2_loadable', 'status': 'PASS', 'gap': '', 'evidence': [reference_mechanism]},
            {'name': 'required_h2_species_shared', 'status': 'PASS', 'gap': '', 'evidence': required_shared},
            {'name': 'finite_thermochemistry_samples', 'status': 'PASS', 'gap': '', 'evidence': [str(Path(args.output_csv))]},
            {'name': 'finite_reaction_rate_samples', 'status': 'PASS', 'gap': '', 'evidence': [str(Path(args.output_csv))]},
            {'name': 'paired_0d_ignition_delay_curves', 'status': 'PASS', 'gap': '', 'evidence': [str(Path(args.output_csv))]},
            {'name': 'compiled_pelephysics_rate_kernel_equivalence', 'status': 'PARTIAL', 'gap': 'Not exercised here; this report compares the PelePhysics YAML through Cantera, not the generated C++ rate kernel.', 'evidence': []},
        ],
        'blocking_gaps': ['compiled_pelephysics_rate_kernel_equivalence'],
        'next_required_artifacts': [
            'compiled PelePhysics generated C++ rate-kernel equivalence harness',
            'forward/reverse progress-rate comparison against Cantera over a thermochemical sample grid',
        ],
        'evidence_files': [
            evidence_entry('pelephysics_lidryer_mechanism_yaml', Path(pele_mechanism)),
        ],
        'limitations': [
            'This clears the readiness-level Cantera mechanism comparison gap by checking two Cantera-loaded mechanisms.',
            'It does not prove bitwise or tolerance-bound equivalence between Cantera and the compiled PelePhysics C++ rate kernel.',
            'The 0D ignition-delay ratio is a coarse same-order gate, not a detonation validation benchmark.',
        ],
    }
    validate_report_object(report, check_hashes=False, require_csv=False)
    return report, csv_rows


def validate_report_object(data: dict[str, Any], check_hashes: bool = True, require_csv: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(summ.get('clears_cantera_mechanism_comparison_gap') is True, 'Cantera mechanism comparison gap not cleared')
    require(summ.get('clears_full_pelephysics_source_rate_equivalence') is False, 'compiled PelePhysics rate equivalence cannot be cleared here')
    require(summ.get('pelephysics_yaml_loads_in_cantera') is True, 'PelePhysics YAML did not load')
    require(summ.get('reference_h2o2_yaml_loads_in_cantera') is True, 'reference h2o2 mechanism did not load')
    require(summ.get('thermochemistry_samples_finite') is True, 'thermochemistry samples are not finite')
    require(summ.get('reaction_rate_samples_finite') is True, 'reaction-rate samples are not finite')
    require(summ.get('ignition_delay_curves_monotonic') is True, 'ignition curves are not monotonic')
    require(summ.get('ignition_delay_curves_same_order') is True, 'ignition curves are not same-order')
    require(int(summ.get('ignition_delay_pair_count', 0)) >= 3, 'too few paired ignition-delay cases')
    require(float(summ.get('max_ignition_delay_ratio', math.inf)) <= float(summ.get('ignition_delay_ratio_limit', 0.0)), 'ignition delay ratio exceeds limit')
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list) and gates, 'quality_gate_matrix missing')
    non_pass = [item for item in gates if isinstance(item, dict) and item.get('status') != 'PASS']
    require([item.get('name') for item in non_pass] == ['compiled_pelephysics_rate_kernel_equivalence'], 'unexpected non-PASS gates')
    if require_csv:
        rows = read_csv_rows(Path(str(data.get('comparison_csv', ''))))
        require(len(rows) >= 6, 'comparison CSV has too few rows')
    if check_hashes:
        entries = data.get('evidence_files')
        require(isinstance(entries, list) and entries, 'evidence_files missing')
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True, require_csv=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Academic Gas Cantera Mechanism Comparison',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        f"Cantera: `{report['cantera_version']}`",
        f"PelePhysics mechanism: `{report['pelephysics_mechanism']}`",
        f"Reference mechanism: `{report['reference_mechanism']}`",
        f"CSV: `{report['comparison_csv']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Ignition Delay Comparison', '', '| T0 K | PelePhysics LiDryer s | Cantera h2o2 s | Ratio |', '| --- | --- | --- | --- |']
    for item in report['ignition_delay_comparison']:
        lines.append(
            f"| `{item['temperature_k']:.1f}` | `{item['pelephysics_lidryer_delay_s']:.8e}` | "
            f"`{item['cantera_h2o2_delay_s']:.8e}` | `{item['delay_ratio']:.3f}` |"
        )
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['gap'] or 'none'} |")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pelephysics-mechanism', default=str(DEFAULT_PELEPHYSICS_MECHANISM))
    parser.add_argument('--reference-mechanism', default=DEFAULT_REFERENCE_MECHANISM)
    parser.add_argument('--temperatures-k', default=','.join(str(v) for v in DEFAULT_TEMPERATURES_K))
    parser.add_argument('--pressure-pa', type=float, default=DEFAULT_PRESSURE_PA)
    parser.add_argument('--composition', default=DEFAULT_COMPOSITION)
    parser.add_argument('--end-time-s', type=float, default=0.02)
    parser.add_argument('--max-steps', type=int, default=200000)
    parser.add_argument('--ignition-delay-ratio-limit', type=float, default=50.0)
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--output-csv', default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summ = report.get('summary', {})
            print(
                'academic_gas_cantera_mechanism_comparison VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"pairs={summ.get('ignition_delay_pair_count')} "
                f"max_ratio={summ.get('max_ignition_delay_ratio')}"
            )
            return 0
        report, csv_rows = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_csv = Path(args.output_csv)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        write_csv(csv_rows, out_csv)
        report['comparison_csv_sha256'] = sha256_file(out_csv)
        report['evidence_files'].append(evidence_entry('cantera_mechanism_comparison_csv', out_csv))
        validate_report_object(report, check_hashes=False, require_csv=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'academic_gas_cantera_mechanism_comparison PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"pairs={report['summary']['ignition_delay_pair_count']} "
            f"max_ratio={report['summary']['max_ignition_delay_ratio']:.3f}"
        )
        return 0
    except MechanismComparisonError as exc:
        print(f'academic_gas_cantera_mechanism_comparison FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
