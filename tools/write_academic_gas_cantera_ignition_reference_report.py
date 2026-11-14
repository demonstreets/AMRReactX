#!/usr/bin/env python3
"""Write/verify a Cantera H2/O2 0D ignition-delay reference curve."""
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
STATUS_PASS = 'PASS-ACADEMIC-GAS-CANTERA-IGNITION-REFERENCE'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-GAS-CANTERA-IGNITION-REFERENCE'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'cantera_ignition_reference_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'cantera_ignition_reference_report.md'
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / 'cantera_ignition_reference_curve.csv'

DEFAULT_TEMPERATURES_K = (1000.0, 1100.0, 1200.0, 1300.0)
DEFAULT_PRESSURE_PA = 101325.0
DEFAULT_COMPOSITION = 'H2:2,O2:1,N2:3.76'


class CanteraIgnitionReferenceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CanteraIgnitionReferenceError(message)


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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise CanteraIgnitionReferenceError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise CanteraIgnitionReferenceError(f'invalid JSON evidence {path}: {exc}') from exc
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
    require(len(vals) >= 3, 'at least three temperatures are required for a reference curve')
    require(all(math.isfinite(v) and v > 0.0 for v in vals), 'temperatures must be finite and positive')
    return vals


def run_cantera_case(
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
        raise CanteraIgnitionReferenceError(f'Cantera is not importable: {exc}') from exc

    gas = ct.Solution(mechanism)
    gas.TPX = temperature_k, pressure_pa, composition
    required_species = {'H2', 'O2', 'H2O', 'OH'}
    missing_species = sorted(required_species - set(gas.species_names))
    require(not missing_species, f'mechanism missing required species: {missing_species}')

    reactor = ct.IdealGasReactor(gas, energy='on', clone=False)
    network = ct.ReactorNet([reactor])
    times: list[float] = []
    temps: list[float] = []
    oh_x: list[float] = []
    previous_t = 0.0
    for _ in range(max_steps):
        current_t = network.step()
        if current_t <= previous_t:
            raise CanteraIgnitionReferenceError('Cantera reactor time did not advance')
        previous_t = current_t
        times.append(float(current_t))
        temps.append(float(reactor.T))
        oh_x.append(float(reactor.phase['OH'].X[0]))
        if current_t >= end_time_s:
            break
    require(times and times[-1] >= end_time_s, f'case T={temperature_k} K did not reach end_time_s={end_time_s}')
    max_temp_rise_k = max(temps) - temperature_k
    require(max_temp_rise_k > 100.0, f'case T={temperature_k} K did not ignite strongly enough')
    max_oh_idx = max(range(len(oh_x)), key=lambda idx: oh_x[idx])
    ignition_delay_s = times[max_oh_idx]
    return {
        'temperature_k': temperature_k,
        'pressure_pa': pressure_pa,
        'composition': composition,
        'ignition_delay_s': ignition_delay_s,
        'max_oh_mole_fraction': oh_x[max_oh_idx],
        'max_temperature_k': max(temps),
        'max_temp_rise_k': max_temp_rise_k,
        'end_time_s': times[-1],
        'steps': len(times),
    }


def write_curve_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'temperature_k',
        'pressure_pa',
        'composition',
        'ignition_delay_s',
        'max_oh_mole_fraction',
        'max_temperature_k',
        'max_temp_rise_k',
        'end_time_s',
        'steps',
    ]
    with path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def read_curve_csv(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f'missing curve CSV: {path}')
    with path.open('r', encoding='utf-8', newline='') as fh:
        rows = list(csv.DictReader(fh))
    require(rows, 'curve CSV has no rows')
    return rows


def validate_curve_rows(rows: list[dict[str, Any]]) -> None:
    require(len(rows) >= 3, 'curve must contain at least three cases')
    temps = [float(row['temperature_k']) for row in rows]
    delays = [float(row['ignition_delay_s']) for row in rows]
    require(temps == sorted(temps), 'temperatures must be sorted ascending')
    require(all(finite_number(v) and float(v) > 0.0 for v in delays), 'ignition delays must be positive')
    require(
        all(delays[idx] > delays[idx + 1] for idx in range(len(delays) - 1)),
        'ignition delay must decrease monotonically with initial temperature',
    )
    for row in rows:
        require(float(row['max_temp_rise_k']) > 100.0, f"weak ignition at T={row['temperature_k']}")
        require(float(row['max_oh_mole_fraction']) > 0.0, f"missing OH peak at T={row['temperature_k']}")
        require(int(float(row['steps'])) > 0, f"invalid step count at T={row['temperature_k']}")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    temperatures = parse_temperatures(args.temperatures_k)
    curve_path = Path(args.output_csv)
    rows = [
        run_cantera_case(
            args.mechanism,
            temperature_k,
            float(args.pressure_pa),
            args.composition,
            float(args.end_time_s),
            int(args.max_steps),
        )
        for temperature_k in temperatures
    ]
    rows.sort(key=lambda row: row['temperature_k'])
    write_curve_csv(rows, curve_path)
    validate_curve_rows([{key: str(value) for key, value in row.items()} for row in rows])
    delays = [float(row['ignition_delay_s']) for row in rows]
    temperatures_out = [float(row['temperature_k']) for row in rows]
    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Gas Cantera H2/O2 Ignition Reference Curve',
        'mechanism': args.mechanism,
        'cantera_version': cantera_version(),
        'pressure_pa': float(args.pressure_pa),
        'composition': args.composition,
        'temperatures_k': temperatures_out,
        'curve_csv': str(curve_path),
        'curve_csv_sha256': sha256_file(curve_path),
        'summary': {
            'case_count': len(rows),
            'min_temperature_k': min(temperatures_out),
            'max_temperature_k': max(temperatures_out),
            'min_ignition_delay_s': min(delays),
            'max_ignition_delay_s': max(delays),
            'delay_monotonic_decreases_with_temperature': True,
            'reference_curve_available': True,
            'clears_zero_d_ignition_delay_reference_curve_gap': True,
            'clears_cantera_mechanism_comparison_gap': False,
        },
        'cases': rows,
        'quality_gate_matrix': [
            {'name': 'cantera_importable', 'status': 'PASS', 'gap': '', 'evidence': ['cantera_version']},
            {'name': 'mechanism_loadable', 'status': 'PASS', 'gap': '', 'evidence': [args.mechanism]},
            {'name': 'multi_temperature_curve', 'status': 'PASS', 'gap': '', 'evidence': [str(curve_path)]},
            {'name': 'monotonic_temperature_response', 'status': 'PASS', 'gap': '', 'evidence': [str(curve_path)]},
            {
                'name': 'pele_mechanism_equivalence',
                'status': 'MISSING',
                'gap': 'This report generates a Cantera reference curve but does not compare PelePhysics generated rates/species against Cantera.',
                'evidence': [],
            },
        ],
        'evidence_files': [
            evidence_entry('cantera_ignition_reference_curve_csv', curve_path),
        ],
        'limitations': [
            'This report provides a Cantera reference curve only; it does not prove Pele/PelePhysics mechanism equivalence.',
            'The curve is constant-volume 0D kinetics evidence and does not prove multidimensional detonation accuracy.',
        ],
    }
    validate_report_object(report, check_hashes=False)
    return report


def cantera_version() -> str:
    try:
        import cantera as ct
    except Exception as exc:  # pragma: no cover - depends on server environment
        raise CanteraIgnitionReferenceError(f'Cantera is not importable: {exc}') from exc
    return str(ct.__version__)


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_PASS, STATUS_NOT_READY}, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(summ.get('reference_curve_available') is True, 'reference curve must be available')
    require(summ.get('clears_zero_d_ignition_delay_reference_curve_gap') is True, 'reference curve gap not cleared')
    require(summ.get('clears_cantera_mechanism_comparison_gap') is False, 'this report cannot clear mechanism equivalence')
    require(int(summ.get('case_count', 0)) >= 3, 'too few Cantera cases')
    curve = Path(str(data.get('curve_csv', '')))
    rows = read_curve_csv(curve)
    validate_curve_rows(rows)
    if check_hashes:
        require(sha256_file(curve) == data.get('curve_csv_sha256'), 'curve CSV sha256 mismatch')
        entries = data.get('evidence_files')
        require(isinstance(entries, list) and entries, 'evidence_files missing')
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
    lines = [
        '# Academic Gas Cantera H2/O2 Ignition Reference Curve',
        '',
        f"Status: `{report['status']}`",
        f"Mechanism: `{report['mechanism']}`",
        f"Cantera: `{report['cantera_version']}`",
        f"Curve CSV: `{report['curve_csv']}` sha256 `{report['curve_csv_sha256'][:16]}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Cases', '', '| T0 K | ignition delay s | max OH | max T K | steps |', '| --- | --- | --- | --- | --- |']
    for item in report['cases']:
        lines.append(
            f"| `{item['temperature_k']:.1f}` | `{item['ignition_delay_s']:.8e}` | "
            f"`{item['max_oh_mole_fraction']:.8e}` | `{item['max_temperature_k']:.3f}` | `{item['steps']}` |"
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
    parser.add_argument('--mechanism', default='h2o2.yaml')
    parser.add_argument('--temperatures-k', default=','.join(str(v) for v in DEFAULT_TEMPERATURES_K))
    parser.add_argument('--pressure-pa', type=float, default=DEFAULT_PRESSURE_PA)
    parser.add_argument('--composition', default=DEFAULT_COMPOSITION)
    parser.add_argument('--end-time-s', type=float, default=0.02)
    parser.add_argument('--max-steps', type=int, default=200000)
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
                'academic_gas_cantera_ignition_reference VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"cases={summ.get('case_count')} "
                f"delay_range=[{summ.get('min_ignition_delay_s')},{summ.get('max_ignition_delay_s')}]"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'academic_gas_cantera_ignition_reference PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"cases={report['summary']['case_count']}"
        )
        return 0
    except CanteraIgnitionReferenceError as exc:
        print(f'academic_gas_cantera_ignition_reference FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
