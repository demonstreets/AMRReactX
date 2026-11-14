#!/usr/bin/env python3
"""Validate closed fixed-particle spray budget from AMReX particle DATA."""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from write_academic_droplet_spray_budget_preflight_report import (  # noqa: E402
    read_particle_binary_budget,
)


def fail(message: str) -> None:
    raise SystemExit(f'FAIL: {message}')


def parse_inputs(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def require_input_contract(values: dict[str, str]) -> None:
    expected = {
        'pelec.do_spray_particles': '1',
        'particles.mass_transfer': '0',
        'particles.mom_transfer': '0',
        'particles.fixed_parts': '1',
        'amr.plot_files_output': '1',
    }
    for key, want in expected.items():
        got = values.get(key)
        if got != want:
            fail(f'input {key}={got!r}, expected {want!r}')
    periodic = values.get('geometry.is_periodic', '')
    if not periodic.startswith('1 '):
        fail(f'input geometry.is_periodic={periodic!r}, expected periodic x')


def log_is_clean(path: Path, expected_step: int) -> None:
    text = path.read_text(errors='replace')
    if f'STEP = {expected_step}' not in text:
        fail(f'run log does not show expected final step {expected_step}: {path}')
    if 'AMReX' not in text or 'finalized' not in text:
        fail(f'run log does not show AMReX finalized: {path}')
    if re.search(r'\b(?:nan|inf|SIGSEGV|Segmentation|Backtrace|Abort)\b', text, re.IGNORECASE):
        fail(f'run log contains failure token: {path}')


def rel_delta(initial: float, final: float) -> float:
    return (final - initial) / max(abs(initial), 1.0e-300)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--run-log', required=True)
    parser.add_argument('--initial', required=True)
    parser.add_argument('--final', required=True)
    parser.add_argument('--expected-step', type=int, default=100)
    parser.add_argument('--max-mass-rel-drift', type=float, default=1.0e-14)
    parser.add_argument('--max-diameter-rel-drift', type=float, default=1.0e-14)
    parser.add_argument('--max-coordinate-abs-drift', type=float, default=1.0e-14)
    parser.add_argument('--max-temperature-rel-drift', type=float, default=1.0e-14)
    args = parser.parse_args()

    input_path = Path(args.input)
    run_log = Path(args.run_log)
    initial_path = Path(args.initial)
    final_path = Path(args.final)
    require_input_contract(parse_inputs(input_path))
    log_is_clean(run_log, args.expected_step)

    b0 = read_particle_binary_budget(initial_path, input_path)
    b1 = read_particle_binary_budget(final_path, input_path)
    if b0['particle_count'] <= 0 or b1['particle_count'] != b0['particle_count']:
        fail(f'particle count drifted: {b0["particle_count"]}->{b1["particle_count"]}')

    mass_rel = abs(rel_delta(float(b0['mass_sum']), float(b1['mass_sum'])))
    diam_rel = abs(rel_delta(float(b0['diam_sum']), float(b1['diam_sum'])))
    xcoord_abs = abs(float(b1['xcoord_sum']) - float(b0['xcoord_sum']))
    ycoord_abs = abs(float(b1['ycoord_sum']) - float(b0['ycoord_sum']))
    temp_rel = abs(rel_delta(float(b0['thermal_mass_temperature_sum']), float(b1['thermal_mass_temperature_sum'])))
    xmom_rel_observed = abs(rel_delta(float(b0['xmom_sum']), float(b1['xmom_sum'])))
    ymom_abs_observed = abs(float(b1['ymom_sum']) - float(b0['ymom_sum']))
    if mass_rel > args.max_mass_rel_drift:
        fail(f'particle mass drift too high: {mass_rel:.8e}')
    if diam_rel > args.max_diameter_rel_drift:
        fail(f'particle diameter drift too high: {diam_rel:.8e}')
    if xcoord_abs > args.max_coordinate_abs_drift:
        fail(f'particle x-coordinate drift too high: {xcoord_abs:.8e}')
    if ycoord_abs > args.max_coordinate_abs_drift:
        fail(f'particle y-coordinate drift too high: {ycoord_abs:.8e}')
    if temp_rel > args.max_temperature_rel_drift:
        fail(f'particle mass-temperature drift too high: {temp_rel:.8e}')
    if not all(math.isfinite(float(b1[key])) for key in ('mass_sum', 'xmom_sum', 'ymom_sum', 'kinetic_energy_sum')):
        fail('non-finite particle budget metric')

    print(
        'academic_spray_closed_particle_budget PASS '
        f'particles={b0["particle_count"]}->{b1["particle_count"]} '
        f'mass_rel_drift={mass_rel:.8e} '
        f'diam_rel_drift={diam_rel:.8e} '
        f'xcoord_abs_drift={xcoord_abs:.8e} '
        f'ycoord_abs_drift={ycoord_abs:.8e} '
        f'thermal_rel_drift={temp_rel:.8e} '
        f'xmom_rel_observed={xmom_rel_observed:.8e} '
        f'ymom_abs_observed={ymom_abs_observed:.8e} '
        f'mass={float(b1["mass_sum"]):.12e} '
        f'xmom_observed={float(b1["xmom_sum"]):.12e} '
        f'kinetic_observed={float(b1["kinetic_energy_sum"]):.12e} '
        f'mass_model={b1["mass_model"]}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
