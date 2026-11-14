#!/usr/bin/env python3
"""Read AMReX plotfile k-field statistics using offsets from Cell_H."""
import numpy as np
import struct, sys, os

plt_dir = sys.argv[1] if len(sys.argv) > 1 else "plt00015"

# Read Header
with open(f"{plt_dir}/Header") as f:
    lines = f.readlines()
nvars = int(lines[1].strip())
comp_names = [lines[i].strip() for i in range(2, 2+nvars)]
k_idx = comp_names.index("k")
eps_idx = comp_names.index("epsilon")
print(f"Variables: {comp_names}")
print(f"k={k_idx}, eps={eps_idx}")

# Read Cell_H to get box info and offsets
offsets = []
boxes = []
with open(f"{plt_dir}/Level_0/Cell_H") as f:
    f.readline()  # version
    f.readline()  # ?
    ncomp_h = int(f.readline().strip())
    f.readline()  # ngrow
    # Read box list
    line = f.readline().strip()
    # Format: "(NBOXES 0" or "(NBOXES"
    parts_init = line.replace("(", "").split()
    nboxes = int(parts_init[0])
    for _ in range(nboxes):
        line = f.readline().strip()
        # Parse ((lo0,lo1,lo2) (hi0,hi1,hi2) (0,0,0))
        cleaned = line.replace("(", "").replace(")", "").replace(",", " ")
        parts = cleaned.split()
        lo = [int(parts[0]), int(parts[1]), int(parts[2])]
        hi = [int(parts[3]), int(parts[4]), int(parts[5])]
        boxes.append((lo, hi))
    f.readline()  # )
    n_on_disk = int(f.readline().strip())
    for _ in range(n_on_disk):
        line = f.readline().strip()
        # "FabOnDisk: Cell_D_00000 OFFSET"
        parts = line.split()
        offsets.append(int(parts[-1]))

print(f"Boxes: {nboxes}, on_disk: {n_on_disk}")
for i, ((lo, hi), off) in enumerate(zip(boxes, offsets)):
    nx = hi[0] - lo[0] + 1
    ny = hi[1] - lo[1] + 1
    nz = hi[2] - lo[2] + 1
    print(f"  Box {i}: [{lo}]->[{hi}] cells={nx}x{ny}x{nz}={nx*ny*nz} offset={off}")

# Read data from Cell_D file
data_file = f"{plt_dir}/Level_0/Cell_D_00000"
with open(data_file, "rb") as f:
    all_k = []
    all_eps = []
    
    for idx, ((lo, hi), offset) in enumerate(zip(boxes, offsets)):
        f.seek(offset)
        nx = hi[0] - lo[0] + 1
        ny = hi[1] - lo[1] + 1
        nz = hi[2] - lo[2] + 1
        n_cells = nx * ny * nz
        
        # Skip FAB header: 6 doubles (48 bytes)
        # Actually the header might be different size. Let's try reading 48 bytes
        # and then see what works.
        header_bytes = f.read(90)  # empirically 90 bytes for this format
        
        # Read data
        if idx < len(offsets) - 1:
            data_bytes = offsets[idx+1] - offset - 90
        else:
            # Last box: read to end
            data_bytes = -1
            f.seek(0, 2)
            data_bytes = f.tell() - offset - 90
            f.seek(offset + 90)
        
        raw = f.read(data_bytes)
        expected = n_cells * nvars * 8
        if len(raw) < expected:
            print(f"  Box {idx}: WARNING read {len(raw)} bytes, expected {expected}")
            raw = raw[:expected]
        
        data = np.frombuffer(raw, dtype=np.float64)
        if len(data) >= n_cells * nvars:
            data = data[:n_cells * nvars].reshape(nvars, n_cells)
        else:
            print(f"  Box {idx}: not enough data ({len(data)} vs {n_cells*nvars}), skipping")
            continue
        
        k_vals = data[k_idx, :]
        eps_vals = data[eps_idx, :]
        all_k.append(k_vals)
        all_eps.append(eps_vals)

k_all = np.concatenate(all_k)
eps_all = np.concatenate(all_eps)
k_all = np.maximum(k_all, 0.0)
eps_all = np.maximum(eps_all, 0.0)

# Stats
pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
k_pct = np.percentile(k_all, pcts)
eps_pct = np.percentile(eps_all, pcts)

print(f"\n===== k STATISTICS (step 15, t=0.489s) =====")
print(f"Total cells: {len(k_all):,}")
print(f"Min: {k_all.min():.6e}, Max: {k_all.max():.6e}, Mean: {k_all.mean():.6e}")
print(f"Percentiles:")
for p, v in zip(pcts, k_pct):
    print(f"  P{p:2d}: {v:.6e}")

print(f"\n===== epsilon STATISTICS =====")
print(f"Min: {eps_all.min():.6e}, Max: {eps_all.max():.6e}, Mean: {eps_all.mean():.6e}")
for p, v in zip(pcts, eps_pct):
    print(f"  P{p:2d}: {v:.6e}")

total = len(k_all)
for thresh in [0.1, 0.01, 0.001, 0.0001]:
    cnt = np.sum(k_all < thresh)
    print(f"\nCells with k < {thresh}: {cnt} ({100*cnt/total:.2f}%)")

# Check non-zero k fraction
nonzero = np.sum(k_all > 1e-10)
print(f"Cells with k > 0: {nonzero} ({100*nonzero/total:.2f}%)")
