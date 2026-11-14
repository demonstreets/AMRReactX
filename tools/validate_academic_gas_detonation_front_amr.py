#!/usr/bin/env python3
"""Validate a gas detonation AMR-front plotfile pair."""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
from pathlib import Path

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader

SPECIES = ['H2', 'O2', 'H2O', 'H', 'O', 'OH', 'HO2', 'H2O2', 'N2']


def fail(message: str) -> None:
    raise SystemExit(f'FAIL: {message}')


def require_field(fields: dict[str, object], name: str) -> np.ndarray:
    if name not in fields:
        fail(f'plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        fail(f'non-finite values in {name}')
    return arr


def species_density(fields: dict[str, object], rho: np.ndarray, species: str) -> np.ndarray:
    rho_name = f'rho_{species}'
    y_name = f'Y({species})'
    if rho_name in fields:
        return require_field(fields, rho_name)
    if y_name in fields:
        return rho * require_field(fields, y_name)
    fail(f'plotfile lacks {rho_name} or {y_name}')


def species_fraction(fields: dict[str, object], rho: np.ndarray, species: str) -> np.ndarray:
    y_name = f'Y({species})'
    if y_name in fields:
        return require_field(fields, y_name)
    return species_density(fields, rho, species) / np.maximum(rho, 1.0e-300)


def integrated_mass(arr: np.ndarray, plot: dict[str, object]) -> float:
    dx = np.asarray(plot['dx'][: int(plot['ndim'])], dtype=float)
    return float(np.sum(arr) * np.prod(dx))


def argmax_x(arr: np.ndarray, x: np.ndarray) -> float:
    idx = np.unravel_index(int(np.argmax(arr)), arr.shape)[0]
    return float(x[idx])


def level_boxes(plotfile: Path, level: int) -> list[tuple[int, int, int, int, int, int]]:
    cell_h = plotfile / f'Level_{level}' / 'Cell_H'
    if not cell_h.is_file():
        return []
    boxes: list[tuple[int, int, int, int, int, int]] = []
    for line in cell_h.read_text(encoding='utf-8', errors='replace').splitlines():
        if not line.strip().startswith('FabOnDisk:'):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        fab_path = plotfile / f'Level_{level}' / parts[1]
        offset = int(parts[2]) if len(parts) >= 3 else 0
        if not fab_path.is_file():
            continue
        with fab_path.open('rb') as fh:
            fh.seek(offset)
            header = fh.read(300)
        match3 = re.search(
            rb'\(\((\d+),(\d+),(\d+)\)\s*\((\d+),(\d+),(\d+)\)',
            header,
        )
        match2 = re.search(rb'\(\((\d+),(\d+)\)\s*\((\d+),(\d+)\)', header)
        if match3:
            xlo, ylo, zlo = [int(match3.group(i)) for i in range(1, 4)]
            xhi, yhi, zhi = [int(match3.group(i)) for i in range(4, 7)]
        elif match2:
            xlo, ylo = int(match2.group(1)), int(match2.group(2))
            xhi, yhi = int(match2.group(3)), int(match2.group(4))
            zlo, zhi = 0, 0
        else:
            fail(f'cannot parse AMR box from {fab_path}')
        boxes.append((xlo, xhi, ylo, yhi, zlo, zhi))
    return boxes


def level_cell_count(boxes: list[tuple[int, int, int, int, int, int]]) -> int:
    total = 0
    for xlo, xhi, ylo, yhi, zlo, zhi in boxes:
        total += (xhi - xlo + 1) * (yhi - ylo + 1) * (zhi - zlo + 1)
    return total


def front_refined(plot: dict[str, object], plotfile: Path, front_x: float, level: int) -> tuple[bool, int, int, float]:
    boxes = level_boxes(plotfile, level)
    cell_count = level_cell_count(boxes)
    if not boxes:
        return False, 0, 0, 0.0
    dx = np.asarray(plot['dx'][: int(plot['ndim'])], dtype=float)
    prob_lo = np.asarray(plot['prob_lo'][: int(plot['ndim'])], dtype=float)
    grid = plot['grid']
    full_cells = int(grid['nx']) * int(grid['ny']) * int(grid.get('nz', 1))
    level_fraction = cell_count / max(full_cells, 1)
    pad = 2.0 * float(dx[0])
    covered = False
    front_box_count = 0
    for xlo, xhi, _ylo, _yhi, _zlo, _zhi in boxes:
        x_left = float(prob_lo[0]) + xlo * float(dx[0])
        x_right = float(prob_lo[0]) + (xhi + 1) * float(dx[0])
        if x_left - pad <= front_x <= x_right + pad:
            covered = True
            front_box_count += 1
    return covered, len(boxes), cell_count, level_fraction


def scalar_metrics(p0: dict[str, object], p1: dict[str, object]) -> dict[str, float]:
    f0, f1 = p0['fields'], p1['fields']
    rho0 = require_field(f0, 'density')
    rho1 = require_field(f1, 'density')
    temp0 = require_field(f0, 'Temp')
    temp1 = require_field(f1, 'Temp')
    if float(np.min(rho1)) <= 0.0:
        fail('final density is nonpositive')
    if float(np.min(temp1)) <= 0.0:
        fail('final temperature is nonpositive')

    x0 = np.asarray(p0['x'], dtype=float)
    x1 = np.asarray(p1['x'], dtype=float)
    temp_front0 = argmax_x(temp0, x0)
    temp_front1 = argmax_x(temp1, x1)
    dt = float(p1['time']) - float(p0['time'])
    if dt <= 0.0:
        fail(f'final time {p1["time"]} is not after initial time {p0["time"]}')
    front_shift = temp_front1 - temp_front0
    front_speed = front_shift / dt
    front_shift_cells = front_shift / float(p1['dx'][0])

    species0 = {name: species_density(f0, rho0, name) for name in SPECIES}
    species1 = {name: species_density(f1, rho1, name) for name in SPECIES}
    y_min = min(float(np.min(species_fraction(f1, rho1, name))) for name in SPECIES)
    y_sum = sum(species_fraction(f1, rho1, name) for name in SPECIES)
    species_closure_rel = float(np.max(np.abs(y_sum - 1.0)))
    total_mass0 = integrated_mass(rho0, p0)
    total_mass1 = integrated_mass(rho1, p1)
    mass_rel = abs(total_mass1 - total_mass0) / max(abs(total_mass0), 1.0e-300)

    h2_mass0 = integrated_mass(species0['H2'], p0)
    h2_mass1 = integrated_mass(species1['H2'], p1)
    h2o_mass0 = integrated_mass(species0['H2O'], p0)
    h2o_mass1 = integrated_mass(species1['H2O'], p1)
    return {
        'time0': float(p0['time']),
        'time1': float(p1['time']),
        'grid_nx': float(p1['grid']['nx']),
        'grid_ny': float(p1['grid']['ny']),
        'grid_nz': float(p1['grid'].get('nz', 1)),
        'finest_level0': float(p0['finest_level']),
        'finest_level1': float(p1['finest_level']),
        'temp_front0': temp_front0,
        'temp_front1': temp_front1,
        'front_shift': front_shift,
        'front_shift_cells': front_shift_cells,
        'front_speed': front_speed,
        'temp_max0': float(np.max(temp0)),
        'temp_max1': float(np.max(temp1)),
        'temp_mean_delta': abs(float(np.mean(temp1)) - float(np.mean(temp0))),
        'species_y_min': y_min,
        'species_closure_rel': species_closure_rel,
        'mass_rel': mass_rel,
        'h2_mass0': h2_mass0,
        'h2_mass1': h2_mass1,
        'h2_mass_delta_abs': abs(h2_mass1 - h2_mass0),
        'h2o_mass0': h2o_mass0,
        'h2o_mass1': h2o_mass1,
        'h2o_mass_delta_abs': abs(h2o_mass1 - h2o_mass0),
    }


def require_thresholds(metrics: dict[str, float], args: argparse.Namespace) -> None:
    if int(metrics['grid_nz']) < 4:
        fail('expected a maintained 3D slab with at least four z cells')
    if metrics['front_shift'] <= args.min_front_shift:
        fail(f'thermal front did not move right enough: {metrics["front_shift"]}')
    if metrics['front_shift_cells'] < args.min_front_shift_cells:
        fail(f'thermal front shift too small in cells: {metrics["front_shift_cells"]}')
    if not (args.min_front_speed <= metrics['front_speed'] <= args.max_front_speed):
        fail(f'thermal front speed {metrics["front_speed"]} outside [{args.min_front_speed}, {args.max_front_speed}]')
    if metrics['temp_mean_delta'] <= args.min_temp_mean_delta:
        fail(f'temperature mean changed too little: {metrics["temp_mean_delta"]}')
    if metrics['h2o_mass_delta_abs'] <= args.min_h2o_mass_delta:
        fail(f'H2O mass changed too little: {metrics["h2o_mass_delta_abs"]}')
    if metrics['species_y_min'] < -abs(args.allow_small_negative_y):
        fail(f'final species mass fraction is too negative: {metrics["species_y_min"]}')
    if metrics['species_closure_rel'] > args.max_species_closure_rel:
        fail(f'species mass-fraction closure error too large: {metrics["species_closure_rel"]}')
    if metrics['mass_rel'] > args.max_mass_rel:
        fail(f'total mass changed unexpectedly: {metrics["mass_rel"]}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initial', required=True)
    parser.add_argument('--final', required=True)
    parser.add_argument('--expect-amr', action='store_true')
    parser.add_argument('--refined-level', type=int, default=1)
    parser.add_argument('--min-front-shift', type=float, default=0.01)
    parser.add_argument('--min-front-shift-cells', type=float, default=3.0)
    parser.add_argument('--min-front-speed', type=float, default=1.0e4)
    parser.add_argument('--max-front-speed', type=float, default=1.0e8)
    parser.add_argument('--min-temp-mean-delta', type=float, default=1.0)
    parser.add_argument('--min-h2o-mass-delta', type=float, default=1.0e-12)
    parser.add_argument('--max-mass-rel', type=float, default=5.0e-11)
    parser.add_argument('--max-species-closure-rel', type=float, default=1.0e-10)
    parser.add_argument('--allow-small-negative-y', type=float, default=1.0e-3)
    parser.add_argument('--min-refined-cell-fraction', type=float, default=1.0e-4)
    parser.add_argument('--max-refined-cell-fraction', type=float, default=0.85)
    args = parser.parse_args()

    initial = Path(args.initial)
    final = Path(args.final)
    p0 = amrex_reader.read_plotfile(str(initial))
    p1 = amrex_reader.read_plotfile(str(final))
    if int(p0['ndim']) != 3 or int(p1['ndim']) != 3:
        fail(f'expected 3D plotfiles, got ndim={p0["ndim"]}/{p1["ndim"]}')
    metrics = scalar_metrics(p0, p1)
    require_thresholds(metrics, args)

    front_is_refined = False
    refined_box_count = 0
    refined_cell_count = 0
    refined_cell_fraction = 0.0
    if args.expect_amr:
        if int(p1['finest_level']) < args.refined_level:
            fail(f'expected finest level >= {args.refined_level}, got {p1["finest_level"]}')
        front_is_refined, refined_box_count, refined_cell_count, refined_cell_fraction = front_refined(
            p1,
            final,
            metrics['temp_front1'],
            args.refined_level,
        )
        if refined_cell_count <= 0:
            fail('AMR run produced no refined cells')
        if not (args.min_refined_cell_fraction <= refined_cell_fraction <= args.max_refined_cell_fraction):
            fail(f'AMR refined cell fraction outside limits: {refined_cell_fraction}')
        if not front_is_refined:
            fail('AMR refined level does not cover the thermal front')

    print(
        'academic_gas_detonation_front_amr_validation PASS '
        f'time0={metrics["time0"]:.8g} time1={metrics["time1"]:.8g} '
        f'grid_nx={metrics["grid_nx"]:.0f} grid_ny={metrics["grid_ny"]:.0f} grid_nz={metrics["grid_nz"]:.0f} '
        f'finest_level0={metrics["finest_level0"]:.0f} finest_level1={metrics["finest_level1"]:.0f} '
        f'temp_front0={metrics["temp_front0"]:.8g} temp_front1={metrics["temp_front1"]:.8g} '
        f'front_shift={metrics["front_shift"]:.8g} front_shift_cells={metrics["front_shift_cells"]:.8g} '
        f'front_speed={metrics["front_speed"]:.8e} '
        f'temp_max0={metrics["temp_max0"]:.8g} temp_max1={metrics["temp_max1"]:.8g} '
        f'temp_mean_delta={metrics["temp_mean_delta"]:.8e} '
        f'species_y_min={metrics["species_y_min"]:.8e} '
        f'species_closure_rel={metrics["species_closure_rel"]:.8e} '
        f'mass_rel={metrics["mass_rel"]:.8e} '
        f'h2_mass_delta_abs={metrics["h2_mass_delta_abs"]:.8e} '
        f'h2o_mass_delta_abs={metrics["h2o_mass_delta_abs"]:.8e} '
        f'front_refined={1 if front_is_refined else 0} '
        f'refined_box_count={refined_box_count} '
        f'refined_cell_count={refined_cell_count} '
        f'refined_cell_fraction={refined_cell_fraction:.8e}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
