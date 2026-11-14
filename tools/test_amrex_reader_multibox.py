#!/usr/bin/env python3
import sys
import tempfile
from pathlib import Path

import numpy as np

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
import amrex_reader


def fab_values(box, ncomp):
    xlo, xhi, ylo, yhi, zlo, zhi = box
    nx = xhi - xlo + 1
    ny = yhi - ylo + 1
    nz = zhi - zlo + 1
    if nz == 1 and zlo == 0 and zhi == 0:
        data = np.zeros((nx, ny, ncomp), dtype=np.float64)
        for i, x in enumerate(range(xlo, xhi + 1)):
            for j, y in enumerate(range(ylo, yhi + 1)):
                for n in range(ncomp):
                    data[i, j, n] = 1000.0 * n + 100.0 * x + 10.0 * y
        return data
    data = np.zeros((nx, ny, nz, ncomp), dtype=np.float64)
    for i, x in enumerate(range(xlo, xhi + 1)):
        for j, y in enumerate(range(ylo, yhi + 1)):
            for k, z in enumerate(range(zlo, zhi + 1)):
                for n in range(ncomp):
                    data[i, j, k, n] = 1000.0 * n + 100.0 * x + 10.0 * y + z
    return data


def expected_global(shape, ncomp, ndim):
    if ndim == 2:
        nx, ny = shape
        data = np.zeros((nx, ny, ncomp), dtype=np.float64)
        for x in range(nx):
            for y in range(ny):
                for n in range(ncomp):
                    data[x, y, n] = 1000.0 * n + 100.0 * x + 10.0 * y
        return data
    nx, ny, nz = shape
    data = np.zeros((nx, ny, nz, ncomp), dtype=np.float64)
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                for n in range(ncomp):
                    data[x, y, z, n] = 1000.0 * n + 100.0 * x + 10.0 * y + z
    return data


def write_plotfile(root, ndim, boxes, ncomp=2):
    root = Path(root)
    level = root / 'Level_0'
    level.mkdir(parents=True)
    comp_names = ['density', 'Y(H2)'][:ncomp]
    dx = [0.5, 0.25, 0.125][:ndim]
    prob_lo = [0.0, 0.0, 0.0][:ndim]
    max_hi = [max(box[1] for box in boxes), max(box[3] for box in boxes)]
    if ndim == 3:
        max_hi.append(max(box[5] for box in boxes))
    prob_hi = [(max_hi[d] + 1) * dx[d] for d in range(ndim)]
    with open(root / 'Header', 'w', encoding='utf-8') as fh:
        fh.write('HyperCLaw-V1.1\n')
        fh.write(f'{ncomp}\n')
        for name in comp_names:
            fh.write(f'{name}\n')
        fh.write(f'{ndim}\n')
        fh.write('0.25\n')
        fh.write('0\n')
        fh.write(' '.join(str(v) for v in prob_lo) + '\n')
        fh.write(' '.join(str(v) for v in prob_hi) + '\n')
        fh.write(' '.join(str(v) for v in dx) + '\n')
        fh.write('Level_0/Cell\n')
    with open(level / 'Cell_H', 'w', encoding='utf-8') as fh:
        for idx, box in enumerate(boxes):
            name = f'Cell_D_{idx:05d}'
            fh.write(f'FabOnDisk: {name} 0\n')
            write_fab(level / name, ndim, box, ncomp)


def write_fab(path, ndim, box, ncomp):
    xlo, xhi, ylo, yhi, zlo, zhi = box
    if ndim == 2:
        header = f'FAB (({xlo},{ylo}) ({xhi},{yhi}) (0,0)) {ncomp}\n'
    else:
        header = f'FAB (({xlo},{ylo},{zlo}) ({xhi},{yhi},{zhi}) (0,0,0)) {ncomp}\n'
    data = fab_values(box, ncomp)
    with open(path, 'wb') as fh:
        fh.write(header.encode('ascii'))
        fh.write(np.asarray(data, dtype=np.float64).ravel(order='F').tobytes())


def write_level(root, level_index, ndim, boxes, ncomp=2):
    level = Path(root) / f'Level_{level_index}'
    level.mkdir(parents=True)
    with open(level / 'Cell_H', 'w', encoding='utf-8') as fh:
        for idx, box in enumerate(boxes):
            name = f'Cell_D_{idx:05d}'
            fh.write(f'FabOnDisk: {name} 0\n')
            write_fab(level / name, ndim, box, ncomp)


def write_sparse_amr_plotfile(root, ncomp=2):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    comp_names = ['density', 'Y(H2)'][:ncomp]
    with open(root / 'Header', 'w', encoding='utf-8') as fh:
        fh.write('HyperCLaw-V1.1\n')
        fh.write(f'{ncomp}\n')
        for name in comp_names:
            fh.write(f'{name}\n')
        fh.write('3\n')
        fh.write('0.25\n')
        fh.write('1\n')
        fh.write('0.0 0.0 0.0\n')
        fh.write('2.0 1.0 2.0\n')
        fh.write('1.0 1.0 1.0\n')
        fh.write('0.5 0.5 0.5\n')
        fh.write('Level_0/Cell\n')
        fh.write('Level_1/Cell\n')
    write_level(root, 0, 3, [(0, 1, 0, 0, 0, 1)], ncomp)
    write_level(root, 1, 3, [
        (0, 0, 0, 0, 0, 1),
        (3, 3, 1, 1, 2, 3),
    ], ncomp)


def require(condition, message):
    if not condition:
        raise SystemExit(f'FAIL: {message}')


def require_close(actual, expected, message):
    if not np.allclose(actual, expected, rtol=0.0, atol=0.0):
        raise SystemExit(f'FAIL: {message}: got {actual!r}, expected {expected!r}')


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        p3 = tmp / 'plt00003'
        write_plotfile(p3, 3, [(0, 1, 0, 2, 0, 1), (2, 3, 0, 2, 0, 1)])
        pf3 = amrex_reader.read_plotfile(str(p3))
        require(pf3['fields']['density'].shape == (4, 3, 2), '3D stitched shape')
        require_close(pf3['fields']['density'], expected_global((4, 3, 2), 2, 3)[:, :, :, 0], '3D density stitch')
        require_close(pf3['fields']['Y(H2)'], expected_global((4, 3, 2), 2, 3)[:, :, :, 1], '3D component stitch')
        require_close(pf3['x'], np.array([0.25, 0.75, 1.25, 1.75]), '3D x coordinates')
        require_close(pf3['y'], np.array([0.125, 0.375, 0.625]), '3D y coordinates')
        require_close(pf3['z'], np.array([0.0625, 0.1875]), '3D z coordinates')

        p2 = tmp / 'plt00002'
        write_plotfile(p2, 2, [(0, 3, 0, 0, 0, 0), (0, 3, 1, 2, 0, 0)])
        pf2 = amrex_reader.read_plotfile(str(p2))
        require(pf2['fields']['density'].shape == (4, 3), '2D stitched shape')
        require_close(pf2['fields']['density'], expected_global((4, 3), 2, 2)[:, :, 0], '2D density stitch')

        gap = tmp / 'plt00004'
        write_plotfile(gap, 3, [(0, 0, 0, 0, 0, 0), (2, 2, 0, 0, 0, 0)])
        try:
            amrex_reader.read_plotfile(str(gap))
        except amrex_reader.PlotfileError as exc:
            require('uncovered cells' in str(exc), '3D gap error message')
        else:
            raise SystemExit('FAIL: 3D gap did not raise')

        amr = tmp / 'plt00006'
        write_sparse_amr_plotfile(amr)
        pf_amr = amrex_reader.read_plotfile(str(amr))
        amr_density = pf_amr['fields']['density']
        require(pf_amr['finest_level'] == 1, 'sparse AMR finest level')
        require(amr_density.shape == (4, 2, 4), 'sparse AMR composite shape')
        require_close(amr_density[3, 1, 3], 313.0, 'sparse AMR fine overlay')
        require_close(amr_density[2, 1, 2], 101.0, 'sparse AMR coarse fallback')

        newline_payload = tmp / 'newline_payload_fab'
        newline_payload.write_bytes(
            b'FAB ((0,0,0) (0,0,0) (0,0,0)) 1\n' +
            b'\x0a\x00\x00\x00\x00\x00\x00\x00')
        newline_data = amrex_reader._read_fab_data(newline_payload, 1, 1, 1, 1, 0)
        require(newline_data.shape == (1, 1, 1), 'FAB payload may start with newline byte')

        overlap = tmp / 'plt00005'
        write_plotfile(overlap, 3, [(0, 1, 0, 0, 0, 0), (1, 2, 0, 0, 0, 0)])
        try:
            amrex_reader.read_plotfile(str(overlap))
        except amrex_reader.PlotfileError as exc:
            require('Overlapping boxes' in str(exc), '3D overlap error message')
        else:
            raise SystemExit('FAIL: 3D overlap did not raise')

    print('amrex_reader_multibox_smoke PASS dims=2,3 gap_guard=1 overlap_guard=1 sparse_amr=1 newline_payload=1')


if __name__ == '__main__':
    main()
