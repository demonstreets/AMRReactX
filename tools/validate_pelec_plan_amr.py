#!/usr/bin/env python3
"""Validate PeleC plan-AMR detonation plotfile hierarchy and front coverage."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import amrex_reader  # noqa: E402


BOX_RE = re.compile(r"\(\(([-+]?\d+),([-+]?\d+)(?:,[-+]?\d+)?\)\s*\(([-+]?\d+),([-+]?\d+)(?:,[-+]?\d+)?\)")


def parse_dx_block(header_path: Path, ndim: int, nlevels: int):
    float_lines = []
    for line in header_path.read_text().splitlines():
        tokens = line.strip().split()
        if len(tokens) != ndim:
            continue
        try:
            vals = [float(tok) for tok in tokens]
        except ValueError:
            continue
        if all(val > 0.0 for val in vals):
            float_lines.append(vals)
    for i in range(0, len(float_lines) - nlevels + 1):
        block = float_lines[i:i + nlevels]
        ok = True
        for lev in range(nlevels - 1):
            ratios = [block[lev][d] / block[lev + 1][d] for d in range(ndim)]
            rounded = [round(r) for r in ratios]
            if not all(r >= 1.0 for r in ratios):
                ok = False
                break
            if not all(abs(r - rounded[d]) < 1.0e-12 for d, r in enumerate(ratios)):
                ok = False
                break
            if len(set(rounded)) != 1:
                ok = False
                break
        if ok:
            return block
    raise RuntimeError(f"could not identify AMR dx block in {header_path}")


def parse_cell_boxes(plotfile: Path, level: int):
    cell_h = plotfile / f"Level_{level}" / "Cell_H"
    if not cell_h.exists():
        raise RuntimeError(f"missing Cell_H for level {level}: {cell_h}")
    boxes = []
    for line in cell_h.read_text().splitlines():
        if line.strip().startswith("FabOnDisk:"):
            break
        match = BOX_RE.search(line.strip())
        if match:
            xlo, ylo, xhi, yhi = [int(match.group(i)) for i in range(1, 5)]
            if xhi < xlo or yhi < ylo:
                raise RuntimeError(f"invalid box in {cell_h}: {line}")
            boxes.append((xlo, xhi, ylo, yhi))
    if not boxes:
        raise RuntimeError(f"no boxes parsed from {cell_h}")
    return boxes


def total_cells(boxes):
    return sum((xhi - xlo + 1) * (yhi - ylo + 1) for xlo, xhi, ylo, yhi in boxes)


def physical_bounds(boxes, dx, prob_lo):
    xlo = min(b[0] for b in boxes)
    xhi = max(b[1] for b in boxes)
    ylo = min(b[2] for b in boxes)
    yhi = max(b[3] for b in boxes)
    return (
        prob_lo[0] + xlo * dx[0],
        prob_lo[0] + (xhi + 1) * dx[0],
        prob_lo[1] + ylo * dx[1],
        prob_lo[1] + (yhi + 1) * dx[1],
    )


def contains(bounds, x, y, pad=0.0):
    xlo, xhi, ylo, yhi = bounds
    return (xlo - pad) <= x <= (xhi + pad) and (ylo - pad) <= y <= (yhi + pad)


def max_location(plot, field_name):
    fields = plot["fields"]
    if field_name not in fields:
        raise RuntimeError(f"field {field_name!r} missing from plotfile")
    arr = np.asarray(fields[field_name])
    if not np.all(np.isfinite(arr)):
        raise RuntimeError(f"field {field_name!r} contains non-finite values")
    iy, ix = np.unravel_index(np.nanargmax(arr.T), arr.T.shape)
    x = float(plot["x"][ix])
    y = float(plot["y"][iy])
    return x, y, float(arr[ix, iy])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plotfile", required=True, type=Path)
    parser.add_argument("--min-level1-fraction", type=float, default=0.05)
    parser.add_argument("--max-level1-fraction", type=float, default=0.80)
    parser.add_argument("--require-finest-level", type=int, default=1)
    args = parser.parse_args()

    header = amrex_reader._parse_header(str(args.plotfile / "Header"))
    if header["finest_level"] < args.require_finest_level:
        raise RuntimeError(
            f"finest_level={header['finest_level']} < {args.require_finest_level}")
    dx_levels = parse_dx_block(
        args.plotfile / "Header", header["ndim"], header["finest_level"] + 1)
    if len(dx_levels) <= args.require_finest_level:
        raise RuntimeError("Header does not contain dx for requested AMR level")

    coarse = amrex_reader.read_plotfile(str(args.plotfile))
    coarse_boxes = parse_cell_boxes(args.plotfile, 0)
    boxes = parse_cell_boxes(args.plotfile, args.require_finest_level)
    level_cells = total_cells(boxes)
    coarse_dx = dx_levels[0]
    fine_dx = dx_levels[args.require_finest_level]
    prob_lo = header["prob_lo"]
    ref_ratio_x = round(coarse_dx[0] / fine_dx[0])
    ref_ratio_y = round(coarse_dx[1] / fine_dx[1])
    if ref_ratio_x < 1 or ref_ratio_y < 1:
        raise RuntimeError(f"invalid AMR dx ratio: coarse_dx={coarse_dx} fine_dx={fine_dx}")
    domain_cells = total_cells(coarse_boxes) * ref_ratio_x * ref_ratio_y
    fraction = level_cells / domain_cells
    if not (args.min_level1_fraction <= fraction <= args.max_level1_fraction):
        raise RuntimeError(
            f"level1 coverage fraction {fraction:.6g} outside "
            f"[{args.min_level1_fraction}, {args.max_level1_fraction}]")

    bounds = physical_bounds(boxes, fine_dx, prob_lo)
    temp_x, temp_y, temp_max = max_location(coarse, "Temp")
    h2o_x, h2o_y, h2o_max = max_location(coarse, "rho_H2O")
    pad = max(fine_dx)
    if not contains(bounds, temp_x, temp_y, pad=pad):
        raise RuntimeError(
            f"level1 bounds {bounds} do not cover max Temp at ({temp_x}, {temp_y})")
    if not contains(bounds, h2o_x, h2o_y, pad=pad):
        raise RuntimeError(
            f"level1 bounds {bounds} do not cover max rho_H2O at ({h2o_x}, {h2o_y})")

    print(
        "pelec_plan_amr_validation PASS "
        f"finest_level={header['finest_level']} "
        f"level1_boxes={len(boxes)} level1_cells={level_cells} "
        f"ref_ratio=({ref_ratio_x},{ref_ratio_y}) "
        f"fine_domain_cells={domain_cells} coverage_fraction={fraction:.8f} "
        f"level1_bounds=({bounds[0]:.8g},{bounds[1]:.8g},{bounds[2]:.8g},{bounds[3]:.8g}) "
        f"temp_max={temp_max:.8g} temp_xy=({temp_x:.8g},{temp_y:.8g}) "
        f"h2o_max={h2o_max:.8g} h2o_xy=({h2o_x:.8g},{h2o_y:.8g})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
