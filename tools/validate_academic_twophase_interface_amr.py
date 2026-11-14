#!/usr/bin/env python3
"""Validate two-phase Rayleigh-Taylor interface-specific AMR refinement."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader


def fail(message: str) -> None:
    raise SystemExit(f'FAIL: {message}')


def require_field(fields: dict[str, object], name: str) -> np.ndarray:
    if name not in fields:
        fail(f'plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        fail(f'non-finite values in {name}')
    return arr


def level_boxes(plotfile: Path, level: int) -> list[tuple[int, int, int, int]]:
    cell_h = plotfile / f'Level_{level}' / 'Cell_H'
    if not cell_h.is_file():
        return []
    boxes: list[tuple[int, int, int, int]] = []
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
        match2 = re.search(rb'\(\((\d+),(\d+)\)\s*\((\d+),(\d+)\)', header)
        match3 = re.search(
            rb'\(\((\d+),(\d+),(\d+)\)\s*\((\d+),(\d+),(\d+)\)',
            header,
        )
        if match2:
            xlo, ylo = int(match2.group(1)), int(match2.group(2))
            xhi, yhi = int(match2.group(3)), int(match2.group(4))
        elif match3:
            xlo, ylo = int(match3.group(1)), int(match3.group(2))
            xhi, yhi = int(match3.group(4)), int(match3.group(5))
        else:
            fail(f'cannot parse AMR box from {fab_path}')
        boxes.append((xlo, xhi, ylo, yhi))
    return boxes


def refined_mask(shape: tuple[int, int], boxes: list[tuple[int, int, int, int]]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    nx, ny = shape
    for xlo, xhi, ylo, yhi in boxes:
        xs = slice(max(0, xlo), min(nx, xhi + 1))
        ys = slice(max(0, ylo), min(ny, yhi + 1))
        if xs.start < xs.stop and ys.start < ys.stop:
            mask[xs, ys] = True
    return mask


def interface_metrics(plot: dict[str, object], plotfile: Path, args: argparse.Namespace) -> dict[str, float]:
    fields = plot['fields']
    rho = require_field(fields, 'density')
    rho_e = require_field(fields, 'rho_e')
    temp = require_field(fields, 'Temp')
    adv = require_field(fields, 'rho_adv_0')
    ymom = require_field(fields, 'ymom')
    if float(np.min(rho)) <= 0.0 or float(np.min(rho_e)) <= 0.0 or float(np.min(temp)) <= 0.0:
        fail(
            'nonphysical state '
            f'rho_min={np.min(rho):.8e} rho_e_min={np.min(rho_e):.8e} temp_min={np.min(temp):.8e}'
        )
    alpha = adv / rho
    if float(np.min(alpha)) < -args.alpha_tol or float(np.max(alpha)) > 1.0 + args.alpha_tol:
        fail(f'alpha out of bounds range={np.min(alpha):.8e}:{np.max(alpha):.8e}')
    if alpha.ndim != 2:
        fail(f'expected 2D composite RT field, got shape={alpha.shape}')
    if int(plot['finest_level']) < args.refined_level:
        fail(f'expected finest level >= {args.refined_level}, got {plot["finest_level"]}')

    boxes = level_boxes(plotfile, args.refined_level)
    if not boxes:
        fail(f'plotfile has no Level_{args.refined_level} boxes')
    rmask = refined_mask(alpha.shape, boxes)
    refined_cells = int(np.count_nonzero(rmask))
    total_cells = int(alpha.size)
    if refined_cells <= 0:
        fail('AMR run produced no refined cells')

    imask = (alpha >= args.interface_alpha_lo) & (alpha <= args.interface_alpha_hi)
    interface_cells = int(np.count_nonzero(imask))
    if interface_cells <= 0:
        fail(
            'no interface cells in requested alpha band '
            f'[{args.interface_alpha_lo}, {args.interface_alpha_hi}]'
        )
    interface_refined = int(np.count_nonzero(imask & rmask))
    interface_refined_fraction = interface_refined / max(interface_cells, 1)
    refined_cell_fraction = refined_cells / max(total_cells, 1)
    if interface_refined_fraction < args.min_interface_refined_fraction:
        fail(
            'interface refined fraction too low '
            f'{interface_refined_fraction:.8e} < {args.min_interface_refined_fraction:.8e}'
        )
    if not (args.min_refined_cell_fraction <= refined_cell_fraction <= args.max_refined_cell_fraction):
        fail(
            'refined cell fraction outside limits '
            f'{refined_cell_fraction:.8e} not in '
            f'[{args.min_refined_cell_fraction:.8e}, {args.max_refined_cell_fraction:.8e}]'
        )

    mass = float(np.sum(rho))
    vof_mass = float(np.sum(adv))
    ymom_linf = float(np.max(np.abs(ymom)))
    if ymom_linf <= 0.0:
        fail('gravity produced no measurable momentum response')
    return {
        'time': float(plot['time']),
        'grid_nx': float(alpha.shape[0]),
        'grid_ny': float(alpha.shape[1]),
        'finest_level': float(plot['finest_level']),
        'alpha_min': float(np.min(alpha)),
        'alpha_max': float(np.max(alpha)),
        'rho_min': float(np.min(rho)),
        'rho_max': float(np.max(rho)),
        'mass': mass,
        'vof_mass': vof_mass,
        'ymom_linf': ymom_linf,
        'interface_cells': float(interface_cells),
        'interface_refined_cells': float(interface_refined),
        'interface_refined_fraction': interface_refined_fraction,
        'refined_box_count': float(len(boxes)),
        'refined_cell_count': float(refined_cells),
        'refined_cell_fraction': refined_cell_fraction,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initial', required=True)
    parser.add_argument('--final', required=True)
    parser.add_argument('--refined-level', type=int, default=1)
    parser.add_argument('--interface-alpha-lo', type=float, default=0.05)
    parser.add_argument('--interface-alpha-hi', type=float, default=0.95)
    parser.add_argument('--min-interface-refined-fraction', type=float, default=0.55)
    parser.add_argument('--min-refined-cell-fraction', type=float, default=1.0e-4)
    parser.add_argument('--max-refined-cell-fraction', type=float, default=0.90)
    parser.add_argument('--alpha-tol', type=float, default=1.0e-8)
    parser.add_argument('--mass-rtol', type=float, default=2.0e-5)
    args = parser.parse_args()

    initial = amrex_reader.read_plotfile(args.initial)
    final = amrex_reader.read_plotfile(args.final)
    metrics = interface_metrics(final, Path(args.final), args)
    rho0 = require_field(initial['fields'], 'density')
    adv0 = require_field(initial['fields'], 'rho_adv_0')
    mass0 = float(np.sum(rho0))
    vof0 = float(np.sum(adv0))
    metrics['mass_rel'] = abs(metrics['mass'] - mass0) / max(abs(mass0), 1.0)
    metrics['vof_mass_rel'] = abs(metrics['vof_mass'] - vof0) / max(abs(vof0), 1.0)
    if metrics['mass_rel'] > args.mass_rtol:
        fail(f'mass drift too high: {metrics["mass_rel"]:.8e}')
    if metrics['vof_mass_rel'] > args.mass_rtol:
        fail(f'VOF mass drift too high: {metrics["vof_mass_rel"]:.8e}')

    print(
        'academic_twophase_interface_amr_validation PASS '
        f'time={metrics["time"]:.12g} '
        f'grid=({int(metrics["grid_nx"])},{int(metrics["grid_ny"])}) '
        f'finest_level={int(metrics["finest_level"])} '
        f'alpha_range={metrics["alpha_min"]:.8e}:{metrics["alpha_max"]:.8e} '
        f'rho_range={metrics["rho_min"]:.8e}:{metrics["rho_max"]:.8e} '
        f'mass_rel={metrics["mass_rel"]:.8e} '
        f'vof_mass_rel={metrics["vof_mass_rel"]:.8e} '
        f'ymom_linf={metrics["ymom_linf"]:.8e} '
        f'interface_cells={int(metrics["interface_cells"])} '
        f'interface_refined_cells={int(metrics["interface_refined_cells"])} '
        f'interface_refined_fraction={metrics["interface_refined_fraction"]:.8e} '
        f'refined_box_count={int(metrics["refined_box_count"])} '
        f'refined_cell_count={int(metrics["refined_cell_count"])} '
        f'refined_cell_fraction={metrics["refined_cell_fraction"]:.8e}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
