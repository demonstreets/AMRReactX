#!/usr/bin/env python3
"""
amrex_reader.py — Lightweight AMReX plotfile reader (HyperCLaw-V1.1 format).

Reads AMReX plotfile directory and returns numpy arrays. Does NOT require
yt, h5py, or AMReX Python bindings — only numpy.

Usage:
    import amrex_reader
    data = amrex_reader.read_plotfile("plt00050")
    print(data['x_velocity'].shape)  # (ny, nx) for 2D
"""

import os
import re
import struct
import numpy as np


class PlotfileError(Exception):
    """Error reading AMReX plotfile."""
    pass


# ─── Header parsing ──────────────────────────────────────────────────────────

def _parse_header(header_path):
    """Parse AMReX plotfile Header file.

    Returns dict with: version, ncomp, comp_names, ndim, time, finest_level,
    prob_lo, prob_hi, dx, level_prefixes.
    """
    with open(header_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    result = {}
    idx = 0

    # Line 0: version string
    result['version'] = lines[idx]; idx += 1

    # Line 1: number of components
    result['ncomp'] = int(lines[idx]); idx += 1

    # Next ncomp entries: component names
    result['comp_names'] = []
    for _ in range(result['ncomp']):
        result['comp_names'].append(lines[idx]); idx += 1

    # ndim, time, finest_level
    result['ndim'] = int(lines[idx]); idx += 1
    result['time'] = float(lines[idx]); idx += 1
    result['finest_level'] = int(lines[idx]); idx += 1

    nlevels = result['finest_level'] + 1  # unused but informative

    # prob_lo, prob_hi
    result['prob_lo'] = [float(x) for x in lines[idx].split()]; idx += 1
    result['prob_hi'] = [float(x) for x in lines[idx].split()]; idx += 1

    # ── Skip intermediate lines until we hit the dx block ──
    # The intermediate section contains:
    #   nprocs per level, box coordinates, step numbers, ref ratios
    # We key off: dx lines are pure space-separated floats matching ndim.
    # We also need to collect level_prefixes (Level_X/Cell) that appear after dx.
    #
    # Strategy: scan forward; when we encounter a line with ndim floats
    # that looks like dx (positive small numbers), start collecting dx lines.
    dx_lines = []
    remaining = []
    in_dx = False
    dx_count = 0

    while idx < len(lines):
        tokens = lines[idx].split()
        # Try to interpret as all floats
        try:
            vals = [float(t) for t in tokens]
            if len(vals) >= result['ndim'] and all(v > 0 for v in vals[:result['ndim']]):
                # This looks like a dx line
                in_dx = True
                dx_lines.append(vals[:result['ndim']])
                dx_count += 1
                idx += 1
                continue
        except ValueError:
            pass

        if in_dx:
            # We've finished dx — everything after is level prefixes etc.
            remaining.append(lines[idx])
        idx += 1

    if not dx_lines:
        raise PlotfileError(f"No dx lines found in Header: {header_path}")

    result['dx'] = dx_lines

    # Extract level prefixes from remaining lines
    result['level_prefixes'] = []
    for line in remaining:
        if re.match(r'Level_\d+/Cell', line):
            result['level_prefixes'].append(line)

    return result


# ─── Fab data reading ────────────────────────────────────────────────────────

def _parse_header_structured(header_path):
    """Parse AMReX Header using the structural dx block."""
    with open(header_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    result = {}
    idx = 0
    result['version'] = lines[idx]; idx += 1
    result['ncomp'] = int(lines[idx]); idx += 1
    result['comp_names'] = []
    for _ in range(result['ncomp']):
        result['comp_names'].append(lines[idx]); idx += 1
    result['ndim'] = int(lines[idx]); idx += 1
    result['time'] = float(lines[idx]); idx += 1
    result['finest_level'] = int(lines[idx]); idx += 1
    result['prob_lo'] = [float(x) for x in lines[idx].split()]; idx += 1
    result['prob_hi'] = [float(x) for x in lines[idx].split()]; idx += 1

    try:
        idx += result['finest_level']
        idx += 1
        idx += 1
        dx_lines = []
        for _ in range(result['finest_level'] + 1):
            vals = [float(t) for t in lines[idx].split()]
            if len(vals) < result['ndim'] or not all(v > 0.0 for v in vals[:result['ndim']]):
                raise ValueError(lines[idx])
            dx_lines.append(vals[:result['ndim']])
            idx += 1
        remaining = lines[idx:]
    except (IndexError, ValueError):
        return _parse_header(header_path)

    if len(dx_lines) != result['finest_level'] + 1:
        raise PlotfileError(
            f"Expected {result['finest_level'] + 1} dx lines in Header, got {len(dx_lines)}: {header_path}")
    result['dx'] = dx_lines
    result['level_prefixes'] = [
        line for line in remaining if re.match(r'Level_\d+/Cell', line)
    ]
    return result


def _read_fab_data(filepath, ncomp, nx, ny, nz=1, offset=0):
    """Read binary FabOnDisk data from a Cell_D file.

    The file consists of an ASCII header (ending with a newline)
    followed by binary float64 data in Fortran order (component fastest,
    then x, then y, then z).

    Returns: numpy array of shape (ncomp, ny, nx) for 2D.
    """
    with open(filepath, 'rb') as f:
        f.seek(offset)
        raw = f.read()

    # Find the ASCII header boundary.
    # Pattern: the ASCII FAB header ends with ") <ncomp>\n"
    pattern = re.compile(rb'\)[ \t]*' + str(ncomp).encode() + rb'[ \t]*\n')
    matches = list(pattern.finditer(raw))

    if matches:
        data_start = matches[0].end()
    else:
        # Fallback: find a newline followed by sensible float64 values
        found = False
        for pos in range(50, min(300, len(raw) - 8)):
            if raw[pos:pos + 1] == b'\n':
                try:
                    test = struct.unpack('d', raw[pos + 1:pos + 9])[0]
                    if abs(test) < 1e100 and not np.isnan(test):
                        data_start = pos + 1
                        found = True
                        break
                except Exception:
                    pass
        if not found:
            raise PlotfileError(
                f"Cannot find binary data boundary in {filepath}")

    expected = ncomp * nx * ny * nz
    actual = (len(raw) - data_start) // 8
    if actual < expected:
        raise PlotfileError(
            f"Data size mismatch in {filepath}: "
            f"expected {expected} doubles, got {actual}")

    data = np.frombuffer(raw, dtype=np.float64, count=expected, offset=data_start)

    if nz == 1:
        data = data.reshape(nx, ny, ncomp, order='F')
    else:
        data = data.reshape(nx, ny, nz, ncomp, order='F')

    return data


def _read_level(plotfile_dir, level, ncomp, dx):
    """Read all boxes from a single AMR level and assemble into a uniform grid."""
    level_dir = os.path.join(plotfile_dir, f'Level_{level}')
    cell_h = os.path.join(level_dir, 'Cell_H')

    if not os.path.exists(cell_h):
        raise PlotfileError(f"Cell_H not found: {cell_h}")

    with open(cell_h, 'r') as f:
        hlines = f.readlines()

    # Find FabOnDisk entries
    fab_files = []
    for line in hlines:
        s = line.strip()
        if s.startswith('FabOnDisk:'):
            parts = s.split()
            if len(parts) >= 2:
                offset = int(parts[2]) if len(parts) >= 3 else 0
                fab_files.append((parts[1], offset))

    if not fab_files:
        raise PlotfileError(f"No FabOnDisk entries in {cell_h}")

    all_data = []
    boxes = []

    for fab_name, fab_offset in fab_files:
        fab_path = os.path.join(level_dir, fab_name)
        if not os.path.exists(fab_path):
            continue

        # Read ASCII FAB header to get box dimensions
        with open(fab_path, 'rb') as f_raw:
            f_raw.seek(fab_offset)
            header_bytes = f_raw.read(300)

        # Parse box from ASCII FAB header
        # 2D: ((xlo,ylo) (xhi,yhi) (type))
        # 3D: ((xlo,ylo,zlo) (xhi,yhi,zhi) (type))
        box_3d = re.search(
            rb'\(\((\d+),(\d+),(\d+)\)\s*\((\d+),(\d+),(\d+)\)',
            header_bytes)
        box_2d = re.search(
            rb'\(\((\d+),(\d+)\)\s*\((\d+),(\d+)\)',
            header_bytes)

        if box_3d:
            xlo, ylo, zlo = [int(box_3d.group(i)) for i in range(1, 4)]
            xhi, yhi, zhi = [int(box_3d.group(i)) for i in range(4, 7)]
        elif box_2d:
            xlo, ylo = int(box_2d.group(1)), int(box_2d.group(2))
            xhi, yhi = int(box_2d.group(3)), int(box_2d.group(4))
            zlo, zhi = 0, 0
        else:
            raise PlotfileError(
                f"Cannot parse box from FAB header in {fab_path}")
        nx = xhi - xlo + 1
        ny = yhi - ylo + 1
        nz = zhi - zlo + 1

        data = _read_fab_data(fab_path, ncomp, nx, ny, nz, fab_offset)
        all_data.append(data)
        boxes.append((xlo, xhi, ylo, yhi, zlo, zhi))

    # Single box: return directly with an all-covered mask.
    if len(all_data) == 1:
        nx = boxes[0][1] - boxes[0][0] + 1
        ny = boxes[0][3] - boxes[0][2] + 1
        nz = boxes[0][5] - boxes[0][4] + 1
        coverage_shape = (nx, ny, nz) if all_data[0].ndim == 4 else (nx, ny)
        return all_data[0], {
            'xlo': boxes[0][0], 'xhi': boxes[0][1],
            'ylo': boxes[0][2], 'yhi': boxes[0][3],
            'zlo': boxes[0][4], 'zhi': boxes[0][5],
            'nx': nx,
            'ny': ny,
            'nz': nz,
            'dx': dx,
            'coverage': np.ones(coverage_shape, dtype=bool),
        }

    # AMReX may tile a level in any coordinate direction. Place each Fab at
    # its actual index-space offset and require every covered cell exactly once.
    xlo_global = min(box[0] for box in boxes)
    xhi_global = max(box[1] for box in boxes)
    ylo_global = min(box[2] for box in boxes)
    yhi_global = max(box[3] for box in boxes)
    zlo_global = min(box[4] for box in boxes)
    zhi_global = max(box[5] for box in boxes)
    nx_global = xhi_global - xlo_global + 1
    ny_global = yhi_global - ylo_global + 1
    nz_global = zhi_global - zlo_global + 1

    is_3d = all_data[0].ndim == 4
    if is_3d:
        stitched = np.full(
            (nx_global, ny_global, nz_global, ncomp), np.nan,
            dtype=all_data[0].dtype)
        coverage = np.zeros((nx_global, ny_global, nz_global), dtype=bool)
        for box, data in zip(boxes, all_data):
            xlo, xhi, ylo, yhi, zlo, zhi = box
            xs = slice(xlo - xlo_global, xhi - xlo_global + 1)
            ys = slice(ylo - ylo_global, yhi - ylo_global + 1)
            zs = slice(zlo - zlo_global, zhi - zlo_global + 1)
            if np.any(coverage[xs, ys, zs]):
                raise PlotfileError('Overlapping boxes in multi-box 3D plotfile')
            stitched[xs, ys, zs, :] = data[:, :, :, :]
            coverage[xs, ys, zs] = True
        return stitched, {
            'xlo': xlo_global, 'xhi': xhi_global,
            'ylo': ylo_global, 'yhi': yhi_global,
            'zlo': zlo_global, 'zhi': zhi_global,
            'nx': nx_global, 'ny': ny_global, 'nz': nz_global, 'dx': dx,
            'coverage': coverage,
        }

    stitched = np.full((nx_global, ny_global, ncomp), np.nan,
                       dtype=all_data[0].dtype)
    coverage = np.zeros((nx_global, ny_global), dtype=bool)
    for box, data in zip(boxes, all_data):
        xlo, xhi, ylo, yhi = box[:4]
        xs = slice(xlo - xlo_global, xhi - xlo_global + 1)
        ys = slice(ylo - ylo_global, yhi - ylo_global + 1)
        if np.any(coverage[xs, ys]):
            raise PlotfileError('Overlapping boxes in multi-box 2D plotfile')
        stitched[xs, ys, :] = data[:, :, :]
        coverage[xs, ys] = True

    return stitched, {
        'xlo': xlo_global, 'xhi': xhi_global,
        'ylo': ylo_global, 'yhi': yhi_global,
        'zlo': zlo_global, 'zhi': zhi_global,
        'nx': nx_global, 'ny': ny_global, 'nz': nz_global, 'dx': dx,
        'coverage': coverage,
    }


def _finest_domain_shape(meta, dx):
    """Return the whole-domain cell count at the supplied cell size."""
    shape = []
    for dim in range(meta['ndim']):
        span = meta['prob_hi'][dim] - meta['prob_lo'][dim]
        cells = int(round(span / dx[dim]))
        if cells <= 0:
            raise PlotfileError(
                f"Invalid domain extent on axis {dim}: span={span}, dx={dx[dim]}")
        if not np.isclose(cells * dx[dim], span, rtol=1e-8, atol=1e-12):
            raise PlotfileError(
                f"Domain extent is not an integer number of cells on axis {dim}: "
                f"span={span}, dx={dx[dim]}, cells={cells}")
        shape.append(cells)
    return tuple(shape)


def _refinement_ratio_to_finest(level_dx, finest_dx, ndim):
    """Infer the integer refinement ratio from a level to the finest level."""
    ratios = []
    for dim in range(ndim):
        raw = level_dx[dim] / finest_dx[dim]
        ratio = int(round(raw))
        if ratio < 1 or not np.isclose(raw, ratio, rtol=1e-8, atol=1e-12):
            raise PlotfileError(
                f"Non-integer refinement ratio on axis {dim}: "
                f"level_dx={level_dx[dim]}, finest_dx={finest_dx[dim]}")
        ratios.append(ratio)
    return tuple(ratios)


def _upsample_to_finest(data, ratios, ndim):
    """Nearest-cell expand level data onto the finest index space."""
    upsampled = data
    for axis, ratio in enumerate(ratios[:ndim]):
        if ratio > 1:
            upsampled = np.repeat(upsampled, ratio, axis=axis)
    return upsampled


def _read_composite_levels(plotfile_dir, meta):
    """Read all AMR levels and overlay them on the finest-resolution grid."""
    finest_level = meta['finest_level']
    if finest_level >= len(meta['dx']):
        raise PlotfileError(
            f"Finest level {finest_level} dx not found in Header")

    ndim = meta['ndim']
    ncomp = meta['ncomp']
    finest_dx = meta['dx'][finest_level]
    domain_shape = _finest_domain_shape(meta, finest_dx)

    if ndim > 2:
        composite_shape = domain_shape + (ncomp,)
        coverage_shape = domain_shape
    else:
        composite_shape = domain_shape[:2] + (ncomp,)
        coverage_shape = domain_shape[:2]
    composite = np.full(composite_shape, np.nan, dtype=np.float64)
    coverage = np.zeros(coverage_shape, dtype=np.int16)

    for level in range(finest_level + 1):
        if level >= len(meta['dx']):
            raise PlotfileError(f"Level {level} dx not found in Header")
        level_dx = meta['dx'][level]
        level_data, level_grid = _read_level(plotfile_dir, level, ncomp, level_dx)
        ratios = _refinement_ratio_to_finest(level_dx, finest_dx, ndim)
        fine_data = _upsample_to_finest(level_data, ratios, ndim)

        x0 = level_grid.get('xlo', 0) * ratios[0]
        x1 = (level_grid.get('xhi', level_grid['nx'] - 1) + 1) * ratios[0]
        y0 = level_grid.get('ylo', 0) * ratios[1]
        y1 = (level_grid.get('yhi', level_grid['ny'] - 1) + 1) * ratios[1]

        level_coverage = level_grid.get('coverage')
        if level_coverage is None:
            level_coverage = np.ones(level_data.shape[:ndim], dtype=bool)
        fine_coverage = _upsample_to_finest(level_coverage, ratios, ndim).astype(bool)

        if ndim > 2:
            z0 = level_grid.get('zlo', 0) * ratios[2]
            z1 = (level_grid.get('zhi', level_grid['nz'] - 1) + 1) * ratios[2]
            expected = (x1 - x0, y1 - y0, z1 - z0, ncomp)
            expected_mask = expected[:3]
            if fine_data.shape != expected:
                raise PlotfileError(
                    f"Upsampled level {level} shape mismatch: "
                    f"got {fine_data.shape}, expected {expected}")
            if fine_coverage.shape != expected_mask:
                raise PlotfileError(
                    f"Upsampled level {level} coverage mismatch: "
                    f"got {fine_coverage.shape}, expected {expected_mask}")
            target = composite[x0:x1, y0:y1, z0:z1, :]
            target[fine_coverage, :] = fine_data[fine_coverage, :]
            cov_target = coverage[x0:x1, y0:y1, z0:z1]
            cov_target[fine_coverage] = level + 1
        else:
            expected = (x1 - x0, y1 - y0, ncomp)
            expected_mask = expected[:2]
            if fine_data.shape != expected:
                raise PlotfileError(
                    f"Upsampled level {level} shape mismatch: "
                    f"got {fine_data.shape}, expected {expected}")
            if fine_coverage.shape != expected_mask:
                raise PlotfileError(
                    f"Upsampled level {level} coverage mismatch: "
                    f"got {fine_coverage.shape}, expected {expected_mask}")
            target = composite[x0:x1, y0:y1, :]
            target[fine_coverage, :] = fine_data[fine_coverage, :]
            cov_target = coverage[x0:x1, y0:y1]
            cov_target[fine_coverage] = level + 1

    if np.any(coverage == 0) or np.any(~np.isfinite(composite)):
        missing = int(np.count_nonzero(coverage == 0))
        raise PlotfileError(
            f"Composite AMR plotfile has {missing} uncovered finest cells")

    grid_meta = {
        'xlo': 0, 'xhi': domain_shape[0] - 1,
        'ylo': 0, 'yhi': domain_shape[1] - 1,
        'zlo': 0, 'zhi': (domain_shape[2] - 1) if ndim > 2 else 0,
        'nx': domain_shape[0], 'ny': domain_shape[1],
        'nz': domain_shape[2] if ndim > 2 else 1,
        'dx': finest_dx,
        'composite': True,
        'finest_level': finest_level,
    }
    return composite, grid_meta


# ─── Main API ────────────────────────────────────────────────────────────────

def read_plotfile(plotfile_dir):
    """Read an AMReX plotfile and return structured data.

    Args:
        plotfile_dir: Path to plotfile directory (e.g., "plt00050")

    Returns:
        dict with keys:
            fields: dict of numpy arrays keyed by component name
            time: simulation time
            prob_lo, prob_hi: domain bounds
            dx: list of cell sizes per level
            x, y: cell-centered coordinate arrays
            grid: metadata dict (nx, ny, dx)

    Raises:
        PlotfileError on read failure.
    """
    header_path = os.path.join(plotfile_dir, 'Header')
    if not os.path.exists(header_path):
        raise PlotfileError(f"Header not found: {header_path}")

    meta = _parse_header_structured(header_path)

    if meta['finest_level'] > 0:
        data, grid_meta = _read_composite_levels(plotfile_dir, meta)
        dx = grid_meta['dx']
    else:
        level = 0
        if level >= len(meta['dx']):
            raise PlotfileError(f"Level {level} dx not found")

        dx = meta['dx'][level]
        data, grid_meta = _read_level(plotfile_dir, level, meta['ncomp'], dx)
        level_coverage = grid_meta.get('coverage')
        if level_coverage is not None and np.any(~level_coverage):
            missing = int(np.count_nonzero(~level_coverage))
            raise PlotfileError(
                f"Single-level plotfile has {missing} uncovered cells")
        if np.any(~np.isfinite(data)):
            raise PlotfileError(
                "Single-level plotfile contains uncovered or non-finite cells")

    # Build field dict
    fields = {}
    for i, name in enumerate(meta['comp_names']):
        if data.ndim == 4:
            fields[name] = data[:, :, :, i]
        else:
            fields[name] = data[:, :, i]

    nx, ny = grid_meta['nx'], grid_meta['ny']
    nz = grid_meta.get('nz', 1)
    plo, phi = meta['prob_lo'], meta['prob_hi']

    xlo = grid_meta.get('xlo', 0)
    ylo = grid_meta.get('ylo', 0)
    zlo = grid_meta.get('zlo', 0)
    result = {
        'fields': fields,
        'time': meta['time'],
        'prob_lo': plo,
        'prob_hi': phi,
        'dx': dx,
        'grid': grid_meta,
        'comp_names': meta['comp_names'],
        'ndim': meta['ndim'],
        'finest_level': meta['finest_level'],
        'x': plo[0] + (xlo + np.arange(nx, dtype=float) + 0.5) * dx[0],
        'y': plo[1] + (ylo + np.arange(ny, dtype=float) + 0.5) * dx[1],
    }
    if meta['ndim'] > 2:
        result['z'] = plo[2] + (zlo + np.arange(nz, dtype=float) + 0.5) * dx[2]

    return result


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <plotfile_directory>")
        sys.exit(1)

    data = read_plotfile(sys.argv[1])
    print(f"Time: {data['time']}")
    print(f"Components: {', '.join(data['comp_names'][:8])}...")
    nz = data['grid'].get('nz', 1)
    print(f"Grid: {data['grid']['nx']} x {data['grid']['ny']} x {nz}")
    for name in data['comp_names'][:5]:
        arr = data['fields'][name]
        print(f"  {name}: shape={arr.shape}, range=[{arr.min():.4e}, {arr.max():.4e}]")
