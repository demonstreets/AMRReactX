#!/usr/bin/env python3
"""Write/verify ACD-05/ACD-07 droplet-spray plotfield budget preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amrex_reader  # noqa: E402

SCHEMA_VERSION = 1
STATUS_PASS = 'PASS-ACADEMIC-DROPLET-SPRAY-PLOTFIELD-BUDGET-PREFLIGHT'
DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_droplet_spray_budget_preflight_20260729')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_droplet_spray_budget_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_droplet_spray_budget_preflight_report.md'
DEFAULT_DROPLET_REPORT = Path(
    'docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/'
    'academic_droplet_euler_lagrange_validation_report.json'
)
DEFAULT_SPRAY_REPORT = Path(
    'docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/'
    'academic_spray_detonation_validation_report.json'
)

GAS_FIELDS = ('density', 'xmom', 'ymom', 'rho_E', 'Temp', 'pressure')
SPRAY_FIELDS = ('spray_mass', 'spray_x_vel', 'spray_y_vel', 'spray_temp', 'spray_surf_area', 'd32')
PARTICLE_REQUIRED_REAL_COMPONENTS = (
    'xvel', 'yvel', 'temperature', 'diam', 'spray_mf_NC7H16',
    'number_density', 'shed_mass',
)


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


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise ReportError(f'failed to read JSON {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def parse_inputs(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def parse_liquid_density(input_file: Path) -> float:
    values = parse_inputs(input_file)
    fuel = values.get('particles.fuel_species', 'NC7H16').strip('"')
    for key in (f'particles.{fuel}_rho', 'particles.NC7H16_rho'):
        if key not in values:
            continue
        try:
            rho = float(values[key].split()[0])
        except (IndexError, ValueError) as exc:
            raise ReportError(f'cannot parse liquid density {key} from {input_file}: {exc}') from exc
        require(math.isfinite(rho) and rho > 0.0, f'liquid density must be positive: {input_file}')
        return rho
    raise ReportError(f'missing liquid density for fuel {fuel}: {input_file}')


def json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if value.size > 64:
            return {
                'array_shape': list(value.shape),
                'array_dtype': str(value.dtype),
                'true_count': int(np.count_nonzero(value)) if value.dtype == bool else None,
            }
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def field(plot: dict[str, object], name: str) -> np.ndarray:
    fields = plot.get('fields')
    require(isinstance(fields, dict) and name in fields, f'missing plot field {name}')
    arr = np.asarray(fields[name], dtype=float)
    require(np.isfinite(arr).all(), f'non-finite plot field {name}')
    return arr


def rel_delta(initial: float, final: float) -> float:
    denom = max(abs(initial), 1.0e-300)
    return (final - initial) / denom


def particle_header(path: Path) -> dict[str, Any]:
    header = path / 'particles' / 'Header'
    require(header.is_file(), f'missing particle Header: {header}')
    lines = header.read_text().splitlines()
    require(len(lines) >= 18, f'particle Header too short: {header}')
    try:
        spatial_dim = int(lines[1])
        nreal = int(lines[2])
        real_components = lines[3:3 + nreal]
        int_start = 3 + nreal
        nint = int(lines[int_start])
        int_components = lines[int_start + 1:int_start + 1 + nint]
        meta_start = int_start + 1 + nint
        particle_count = int(lines[meta_start + 1])
        next_id = int(lines[meta_start + 2])
        finest_level = int(lines[meta_start + 3])
    except (IndexError, ValueError) as exc:
        raise ReportError(f'cannot parse particle Header {header}: {exc}') from exc
    missing_real = [name for name in PARTICLE_REQUIRED_REAL_COMPONENTS if name not in real_components]
    data_files = sorted((path / 'particles').glob('Level_*/DATA_*'))
    particle_h_files = sorted((path / 'particles').glob('Level_*/Particle_H'))
    return {
        'path': str(header),
        'spatial_dim': spatial_dim,
        'real_component_count': nreal,
        'real_components': real_components,
        'int_component_count': nint,
        'int_components': int_components,
        'particle_count': particle_count,
        'next_id': next_id,
        'finest_level': finest_level,
        'missing_required_real_components': missing_real,
        'data_file_count': len(data_files),
        'data_size_bytes': int(sum(item.stat().st_size for item in data_files)),
        'particle_h_file_count': len(particle_h_files),
    }


def read_particle_binary_budget(path: Path, input_file: Path) -> dict[str, Any]:
    header = particle_header(path)
    liquid_density = parse_liquid_density(input_file)
    spatial_dim = int(header['spatial_dim'])
    real_components = list(header['real_components'])
    value_names = [f'coord_{idx}' for idx in range(spatial_dim)] + real_components
    missing = [
        name for name in ('xvel', 'yvel', 'temperature', 'diam', 'number_density')
        if name not in real_components
    ]
    require(not missing, f'particle binary budget missing required components: {missing}')
    value_count = len(value_names)
    record_size = 8 + value_count * 8
    data_files = sorted((path / 'particles').glob('Level_*/DATA_*'))
    require(data_files, f'missing particle DATA files under {path / "particles"}')

    rows: list[dict[str, float]] = []
    data_file_records: list[dict[str, Any]] = []
    for data_file in data_files:
        raw = data_file.read_bytes()
        require(len(raw) % record_size == 0, f'particle DATA size is not a multiple of record size: {data_file}')
        count = len(raw) // record_size
        data_file_records.append({'path': str(data_file), 'records': count, 'size_bytes': len(raw)})
        payload_offset = count * 8
        for idx in range(count):
            offset = payload_offset + idx * value_count * 8
            vals = struct.unpack_from(f'<{value_count}d', raw, offset)
            rows.append(dict(zip(value_names, vals)))
    require(
        len(rows) == int(header['particle_count']),
        f'particle count mismatch in DATA files: {len(rows)} != {header["particle_count"]}',
    )

    mass_sum = 0.0
    xmom_sum = 0.0
    ymom_sum = 0.0
    kinetic_sum = 0.0
    thermal_proxy_sum = 0.0
    shed_mass_sum = 0.0
    diam_min = math.inf
    diam_max = -math.inf
    temp_min = math.inf
    temp_max = -math.inf
    xvel_absmax = 0.0
    yvel_absmax = 0.0
    number_density_min = math.inf
    number_density_max = -math.inf
    for row in rows:
        diam = float(row['diam'])
        ndens = float(row['number_density'])
        temp = float(row['temperature'])
        xvel = float(row['xvel'])
        yvel = float(row['yvel'])
        require(math.isfinite(diam) and diam > 0.0, 'particle diameter must be finite and positive')
        require(math.isfinite(ndens) and ndens >= 0.0, 'particle number density must be finite and nonnegative')
        mass = ndens * liquid_density * math.pi * diam**3 / 6.0
        mass_sum += mass
        xmom_sum += mass * xvel
        ymom_sum += mass * yvel
        kinetic_sum += 0.5 * mass * (xvel * xvel + yvel * yvel)
        thermal_proxy_sum += mass * temp
        shed_mass_sum += float(row.get('shed_mass', 0.0))
        diam_min = min(diam_min, diam)
        diam_max = max(diam_max, diam)
        temp_min = min(temp_min, temp)
        temp_max = max(temp_max, temp)
        xvel_absmax = max(xvel_absmax, abs(xvel))
        yvel_absmax = max(yvel_absmax, abs(yvel))
        number_density_min = min(number_density_min, ndens)
        number_density_max = max(number_density_max, ndens)
    require(math.isfinite(mass_sum) and mass_sum > 0.0, 'particle mass sum must be finite and positive')
    return {
        'parser_status': 'PASS',
        'layout': 'amrex_particle_soa_idcpu_then_aos_real_payload',
        'record_size_bytes': record_size,
        'value_names': value_names,
        'data_files': data_file_records,
        'liquid_density': liquid_density,
        'particle_count': len(rows),
        'mass_sum': float(mass_sum),
        'xmom_sum': float(xmom_sum),
        'ymom_sum': float(ymom_sum),
        'kinetic_energy_sum': float(kinetic_sum),
        'thermal_mass_temperature_sum': float(thermal_proxy_sum),
        'shed_mass_sum': float(shed_mass_sum),
        'diam_min': float(diam_min),
        'diam_max': float(diam_max),
        'temperature_min': float(temp_min),
        'temperature_max': float(temp_max),
        'xvel_absmax': float(xvel_absmax),
        'yvel_absmax': float(yvel_absmax),
        'number_density_min': float(number_density_min),
        'number_density_max': float(number_density_max),
    }


def read_plot(path: Path) -> dict[str, object]:
    require(path.is_dir(), f'missing plotfile: {path}')
    return amrex_reader.read_plotfile(str(path))


def cell_volume(plot: dict[str, object]) -> float:
    dx = [float(x) for x in plot.get('dx', [])]
    ndim = int(plot.get('ndim', len(dx)))
    require(dx and ndim > 0, 'plotfile missing dx/ndim')
    return float(math.prod(dx[:ndim]))


def integral(arr: np.ndarray, volume: float) -> float:
    return float(np.sum(arr) * volume)


def raw_sum(arr: np.ndarray) -> float:
    return float(np.sum(arr))


def plot_budget(path: Path) -> dict[str, Any]:
    plot = read_plot(path)
    cv = cell_volume(plot)
    density = field(plot, 'density')
    xmom = field(plot, 'xmom')
    ymom = field(plot, 'ymom')
    rho_e = field(plot, 'rho_E')
    spray_mass = field(plot, 'spray_mass')
    spray_x_vel = field(plot, 'spray_x_vel')
    spray_y_vel = field(plot, 'spray_y_vel')
    spray_temp = field(plot, 'spray_temp')
    required = {name: field(plot, name) for name in (*GAS_FIELDS, *SPRAY_FIELDS)}
    gas = {
        'mass_integral': integral(density, cv),
        'xmom_integral': integral(xmom, cv),
        'ymom_integral': integral(ymom, cv),
        'rho_E_integral': integral(rho_e, cv),
        'temperature_min': float(np.min(required['Temp'])),
        'pressure_min': float(np.min(required['pressure'])),
    }
    spray = {
        'mass_raw_sum': raw_sum(spray_mass),
        'mass_volume_integral': integral(spray_mass, cv),
        'xmom_raw_sum_proxy': raw_sum(spray_mass * spray_x_vel),
        'ymom_raw_sum_proxy': raw_sum(spray_mass * spray_y_vel),
        'xmom_volume_integral_proxy': integral(spray_mass * spray_x_vel, cv),
        'ymom_volume_integral_proxy': integral(spray_mass * spray_y_vel, cv),
        'kinetic_energy_raw_sum_proxy': raw_sum(0.5 * spray_mass * (spray_x_vel**2 + spray_y_vel**2)),
        'kinetic_energy_volume_integral_proxy': integral(0.5 * spray_mass * (spray_x_vel**2 + spray_y_vel**2), cv),
        'thermal_raw_sum_proxy': raw_sum(spray_mass * spray_temp),
        'thermal_volume_integral_proxy': integral(spray_mass * spray_temp, cv),
        'temperature_max': float(np.max(spray_temp)),
        'surface_area_raw_sum': raw_sum(required['spray_surf_area']),
        'd32_max': float(np.max(required['d32'])),
    }
    species = {}
    comp_names = plot.get('comp_names')
    if isinstance(comp_names, list) and {'Y(NC7H16)', 'Y(O2)', 'Y(N2)'}.issubset(set(comp_names)):
        closure = field(plot, 'Y(NC7H16)') + field(plot, 'Y(O2)') + field(plot, 'Y(N2)')
        species['species_closure_absmax'] = float(np.max(np.abs(closure - 1.0)))
    return {
        'path': str(path),
        'time': float(plot['time']),
        'ndim': int(plot['ndim']),
        'finest_level': int(plot['finest_level']),
        'grid': json_safe(plot['grid']),
        'cell_volume': cv,
        'gas': gas,
        'spray_plotfield': spray,
        'species': species,
        'particle_header': particle_header(path),
    }


def compare_budgets(initial: dict[str, Any], final: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for section, keys in {
        'gas': ('mass_integral', 'xmom_integral', 'ymom_integral', 'rho_E_integral'),
        'spray_plotfield': (
            'mass_raw_sum', 'mass_volume_integral', 'xmom_raw_sum_proxy',
            'ymom_raw_sum_proxy', 'kinetic_energy_raw_sum_proxy',
            'thermal_raw_sum_proxy',
        ),
        'particle_binary_budget': (
            'mass_sum', 'xmom_sum', 'ymom_sum', 'kinetic_energy_sum',
            'thermal_mass_temperature_sum', 'shed_mass_sum',
        ),
    }.items():
        checks[section] = {}
        for key in keys:
            v0 = float(initial[section][key])
            v1 = float(final[section][key])
            checks[section][key] = {
                'initial': v0,
                'final': v1,
                'delta': v1 - v0,
                'relative_delta': rel_delta(v0, v1),
            }
    return checks


def case_from_report(report: dict[str, Any], label: str) -> dict[str, Any]:
    cases = report.get('cases')
    require(isinstance(cases, list) and cases, f'{label} report has no cases')
    case = cases[0]
    require(isinstance(case, dict), f'{label} case is not an object')
    return case


def build_case(label: str, source_report: Path, report: dict[str, Any]) -> dict[str, Any]:
    case = case_from_report(report, label)
    initial_path = Path(str(case.get('plotfile_initial', '')))
    final_path = Path(str(case.get('plotfile_final', '')))
    input_path = Path(str(case.get('input_file', '')))
    require(input_path.is_file(), f'missing input file: {input_path}')
    initial = plot_budget(initial_path)
    final = plot_budget(final_path)
    initial['particle_binary_budget'] = read_particle_binary_budget(initial_path, input_path)
    final['particle_binary_budget'] = read_particle_binary_budget(final_path, input_path)
    declared = (
        not initial['particle_header']['missing_required_real_components']
        and not final['particle_header']['missing_required_real_components']
    )
    parser_ready = (
        initial['particle_binary_budget']['parser_status'] == 'PASS'
        and final['particle_binary_budget']['parser_status'] == 'PASS'
    )
    for snapshot in (initial, final):
        particle_mass = float(snapshot['particle_binary_budget']['mass_sum'])
        plotfield_mass = float(snapshot['spray_plotfield']['mass_raw_sum'])
        snapshot['particle_to_plotfield_mass_relative_difference'] = abs(
            particle_mass - plotfield_mass
        ) / max(abs(plotfield_mass), 1.0e-300)
    return {
        'label': label,
        'name': case.get('name'),
        'source_report': str(source_report),
        'input_file': case.get('input_file'),
        'run_log': case.get('run_log'),
        'validation_log': case.get('validation_log'),
        'initial': initial,
        'final': final,
        'deltas': compare_budgets(initial, final),
        'particle_schema_declares_budget_components': declared,
        'particle_binary_budget_parser_ready': parser_ready,
        'closed_gas_particle_budget_ready': False,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    droplet_path = Path(args.droplet_report)
    spray_path = Path(args.spray_report)
    droplet_report = load_json(droplet_path)
    spray_report = load_json(spray_path)
    cases = [
        build_case('droplet_euler_lagrange', droplet_path, droplet_report),
        build_case('reacting_spray_detonation', spray_path, spray_report),
    ]
    for item in cases:
        require(item['final']['time'] > item['initial']['time'], f"{item['label']} final time is not after initial")
        require(item['initial']['gas']['mass_integral'] > 0.0, f"{item['label']} initial gas mass nonpositive")
        require(item['final']['gas']['mass_integral'] > 0.0, f"{item['label']} final gas mass nonpositive")
        require(item['initial']['spray_plotfield']['mass_raw_sum'] > 0.0, f"{item['label']} initial spray mass nonpositive")
        require(item['final']['spray_plotfield']['mass_raw_sum'] > 0.0, f"{item['label']} final spray mass nonpositive")
        require(item['initial']['particle_header']['particle_count'] > 0, f"{item['label']} initial particles nonpositive")
        require(item['final']['particle_header']['particle_count'] > 0, f"{item['label']} final particles nonpositive")
        require(item['particle_binary_budget_parser_ready'] is True, f"{item['label']} particle binary parser not ready")
        require(
            item['initial']['particle_to_plotfield_mass_relative_difference'] <= args.max_particle_plotfield_mass_rel_diff,
            f"{item['label']} initial particle/plotfield mass mismatch",
        )
        require(
            item['final']['particle_to_plotfield_mass_relative_difference'] <= args.max_particle_plotfield_mass_rel_diff,
            f"{item['label']} final particle/plotfield mass mismatch",
        )
    summary = {
        'case_count': len(cases),
        'plotfield_budget_cases_ready': True,
        'particle_headers_declare_required_components': all(
            item['particle_schema_declares_budget_components'] for item in cases
        ),
        'per_particle_binary_budget_parser_ready': all(item['particle_binary_budget_parser_ready'] for item in cases),
        'clears_projected_plotfield_budget_preflight': True,
        'clears_acd_05_closed_gas_particle_budget_gap': False,
        'clears_acd_07_closed_gas_particle_budget_gap': False,
        'clears_full_closed_gas_particle_budget_gap': False,
        'max_particle_plotfield_mass_relative_difference': max(
            item[snapshot]['particle_to_plotfield_mass_relative_difference']
            for item in cases
            for snapshot in ('initial', 'final')
        ),
        'droplet_spray_mass_loss_rel_plotfield': cases[0]['deltas']['spray_plotfield']['mass_raw_sum']['relative_delta'],
        'droplet_particle_mass_loss_rel': cases[0]['deltas']['particle_binary_budget']['mass_sum']['relative_delta'],
        'spray_spray_mass_loss_rel_plotfield': cases[1]['deltas']['spray_plotfield']['mass_raw_sum']['relative_delta'],
        'spray_particle_mass_loss_rel': cases[1]['deltas']['particle_binary_budget']['mass_sum']['relative_delta'],
        'spray_species_closure_absmax_final': cases[1]['final']['species'].get('species_closure_absmax'),
    }
    quality_gates = [
        {'name': 'droplet_plotfield_budget_fields_present', 'status': 'PASS', 'gap': '', 'evidence': [cases[0]['source_report']]},
        {'name': 'spray_plotfield_budget_fields_present', 'status': 'PASS', 'gap': '', 'evidence': [cases[1]['source_report']]},
        {'name': 'finite_gas_and_spray_plotfield_integrals', 'status': 'PASS', 'gap': '', 'evidence': [cases[0]['source_report'], cases[1]['source_report']]},
        {'name': 'particle_headers_declare_budget_components', 'status': 'PASS', 'gap': '', 'evidence': [cases[0]['initial']['particle_header']['path'], cases[1]['initial']['particle_header']['path']]},
        {'name': 'per_particle_binary_budget_parser', 'status': 'PASS', 'gap': '', 'evidence': [cases[0]['final']['particle_header']['path'], cases[1]['final']['particle_header']['path']]},
        {'name': 'particle_budget_matches_spray_plotfield_mass', 'status': 'PASS', 'gap': '', 'evidence': [cases[0]['source_report'], cases[1]['source_report']]},
        {
            'name': 'closed_gas_particle_budget',
            'status': 'NOT_READY',
            'gap': 'Gas conservative fields, Eulerian spray plotfield projections, and native particle binary budgets can be integrated, but these open-boundary shock-tube cases do not include boundary-flux and coupling-source histories needed to close total gas+particle mass, momentum, and total energy.',
            'evidence': [cases[0]['source_report'], cases[1]['source_report']],
        },
    ]
    evidence_files = [
        evidence_entry('report_writer', Path('tools/write_academic_droplet_spray_budget_preflight_report.py')),
        evidence_entry('droplet_report', droplet_path),
        evidence_entry('spray_report', spray_path),
    ]
    for idx, item in enumerate(cases):
        evidence_files.extend([
            evidence_entry(f'case_{idx}_input', Path(str(item['input_file']))),
            evidence_entry(f'case_{idx}_validation_log', Path(str(item['validation_log']))),
            evidence_entry(f'case_{idx}_initial_plot_header', Path(item['initial']['path']) / 'Header'),
            evidence_entry(f'case_{idx}_final_plot_header', Path(item['final']['path']) / 'Header'),
            evidence_entry(f'case_{idx}_initial_particles_header', Path(item['initial']['particle_header']['path'])),
            evidence_entry(f'case_{idx}_final_particles_header', Path(item['final']['particle_header']['path'])),
        ])
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS,
        'title': 'Academic Droplet/Spray Plotfield Budget Preflight',
        'scope': 'ACD-05/ACD-07 gas conservative field plus Eulerian spray plotfield and native AMReX particle-binary budget preflight',
        'summary': summary,
        'cases': cases,
        'quality_gates': quality_gates,
        'evidence_files': evidence_files,
        'limitations': [
            'The report integrates gas conservative variables, Eulerian spray plotfield projections, and native AMReX particle DATA budgets from maintained plotfiles.',
            'Particle kinetic energy and mass-temperature sums are directly reconstructed from particle DATA; full total-energy closure still needs solver coupling-source and boundary-flux histories.',
            'Broad ACD-05/ACD-07 budget credit remains open until an in-code budget diagnostic or closed-domain case closes gas+particle mass, momentum, and total energy including boundary/coupling terms.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS_PASS, 'status mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('plotfield_budget_cases_ready') is True, 'plotfield budget cases are not ready')
    require(summary.get('particle_headers_declare_required_components') is True, 'particle headers missing required components')
    require(summary.get('per_particle_binary_budget_parser_ready') is True, 'particle binary parser did not clear')
    require(summary.get('clears_projected_plotfield_budget_preflight') is True, 'projected plotfield budget preflight did not clear')
    require(summary.get('clears_acd_05_closed_gas_particle_budget_gap') is False, 'ACD-05 budget gap must remain open')
    require(summary.get('clears_acd_07_closed_gas_particle_budget_gap') is False, 'ACD-07 budget gap must remain open')
    cases = data.get('cases')
    require(isinstance(cases, list) and len(cases) == 2, 'expected two cases')
    for item in cases:
        require(isinstance(item, dict), 'case is not an object')
        require(item.get('particle_binary_budget_parser_ready') is True, 'case particle binary parser did not clear')
        require(item.get('closed_gas_particle_budget_ready') is False, 'case closed budget readiness must be false')
        initial = item.get('initial')
        final = item.get('final')
        require(isinstance(initial, dict) and isinstance(final, dict), 'case budgets missing')
        require(float(final.get('time', 0.0)) > float(initial.get('time', math.inf)), 'case final time not after initial')
        require(float(initial['gas']['mass_integral']) > 0.0, 'initial gas mass nonpositive')
        require(float(final['gas']['mass_integral']) > 0.0, 'final gas mass nonpositive')
        require(float(initial['spray_plotfield']['mass_raw_sum']) > 0.0, 'initial spray mass nonpositive')
        require(float(final['spray_plotfield']['mass_raw_sum']) > 0.0, 'final spray mass nonpositive')
        require(float(initial['particle_binary_budget']['mass_sum']) > 0.0, 'initial particle mass nonpositive')
        require(float(final['particle_binary_budget']['mass_sum']) > 0.0, 'final particle mass nonpositive')
        require(float(initial['particle_to_plotfield_mass_relative_difference']) <= 1.0e-10, 'initial particle/plotfield mass mismatch')
        require(float(final['particle_to_plotfield_mass_relative_difference']) <= 1.0e-10, 'final particle/plotfield mass mismatch')
        require(not initial['particle_header']['missing_required_real_components'], 'initial particle header missing required components')
        require(not final['particle_header']['missing_required_real_components'], 'final particle header missing required components')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    non_pass = [g.get('name') for g in gates if isinstance(g, dict) and g.get('status') != 'PASS']
    require(non_pass == ['closed_gas_particle_budget'], f'unexpected non-PASS gates: {non_pass}')
    if check_hashes:
        entries = data.get('evidence_files')
        require(isinstance(entries, list) and entries, 'evidence files missing')
        for item in entries:
            require(isinstance(item, dict), 'evidence entry not object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f'{value:.8e}'
    return str(value)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Academic Droplet/Spray Plotfield Budget Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key in [
        'case_count',
        'plotfield_budget_cases_ready',
        'particle_headers_declare_required_components',
        'per_particle_binary_budget_parser_ready',
        'clears_projected_plotfield_budget_preflight',
        'clears_acd_05_closed_gas_particle_budget_gap',
        'clears_acd_07_closed_gas_particle_budget_gap',
        'clears_full_closed_gas_particle_budget_gap',
        'max_particle_plotfield_mass_relative_difference',
        'droplet_spray_mass_loss_rel_plotfield',
        'droplet_particle_mass_loss_rel',
        'spray_spray_mass_loss_rel_plotfield',
        'spray_particle_mass_loss_rel',
        'spray_species_closure_absmax_final',
    ]:
        lines.append(f"- `{key}`: `{fmt(summary.get(key))}`")
    lines += ['', '## Budget Deltas', '', '| Case | Gas mass rel delta | Gas energy rel delta | Spray mass rel delta | Particle mass rel delta | Particle count |',
              '| --- | --- | --- | --- | --- | --- |']
    for item in report['cases']:
        gas = item['deltas']['gas']
        spray = item['deltas']['spray_plotfield']
        particle = item['deltas']['particle_binary_budget']
        p0 = item['initial']['particle_header']['particle_count']
        p1 = item['final']['particle_header']['particle_count']
        lines.append(
            f"| `{item['label']}` | `{gas['mass_integral']['relative_delta']:.8e}` | "
            f"`{gas['rho_E_integral']['relative_delta']:.8e}` | "
            f"`{spray['mass_raw_sum']['relative_delta']:.8e}` | "
            f"`{particle['mass_sum']['relative_delta']:.8e}` | `{p0}->{p1}` |"
        )
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for gate in report['quality_gates']:
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {gate.get('gap') or 'none'} |")
    lines += ['', '## Limitations', '']
    lines.extend(f"- {item}" for item in report['limitations'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--droplet-report', default=str(DEFAULT_DROPLET_REPORT))
    parser.add_argument('--spray-report', default=str(DEFAULT_SPRAY_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    parser.add_argument('--max-particle-plotfield-mass-rel-diff', type=float, default=1.0e-10)
    args = parser.parse_args()

    try:
        if args.verify_json:
            path = Path(args.verify_json)
            data = load_json(path)
            validate_report_object(data, check_hashes=True)
            print(
                'academic_droplet_spray_budget_preflight VERIFY-PASS '
                f'json={path} cases={data["summary"].get("case_count")} '
                f'closed_budget={data["summary"].get("clears_full_closed_gas_particle_budget_gap")}'
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        write_markdown(report, out_md)
        print(
            'academic_droplet_spray_budget_preflight PASS '
            f'json={out_json} cases={report["summary"].get("case_count")} '
            f'closed_budget={report["summary"].get("clears_full_closed_gas_particle_budget_gap")}'
        )
        return 0
    except ReportError as exc:
        print(f'academic_droplet_spray_budget_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
