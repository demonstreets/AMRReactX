#!/usr/bin/env python3
"""Read AMReX plotfile k-field statistics — correct FAB header parsing."""
import numpy as np
import sys, os

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
    line = f.readline().strip()
    parts_init = line.replace("(", "").split()
    nboxes = int(parts_init[0])
    for _ in range(nboxes):
        line = f.readline().strip()
        cleaned = line.replace("(", "").replace(")", "").replace(",", " ")
        parts = cleaned.split()
        lo = [int(parts[0]), int(parts[1]), int(parts[2])]
        hi = [int(parts[3]), int(parts[4]), int(parts[5])]
        boxes.append((lo, hi))
    f.readline()  # )
    n_on_disk = int(f.readline().strip())
    for _ in range(n_on_disk):
        line = f.readline().strip()
        parts = line.split()
        offsets.append(int(parts[-1]))

print(f"Boxes: {nboxes}, on_disk: {n_on_disk}")

# Read data
data_file = f"{plt_dir}/Level_0/Cell_D_00000"
with open(data_file, "rb") as f:
    all_k = []
    all_eps = []
    
    for idx, ((lo, hi), offset) in enumerate(zip(boxes, offsets)):
        nx = hi[0] - lo[0] + 1
        ny = hi[1] - lo[1] + 1
        nz = hi[2] - lo[2] + 1
        n_cells = nx * ny * nz
        
        f.seek(offset)
        # Find the newline that ends the ASCII FAB header
        header_bytes = bytearray()
        while True:
            b = f.read(1)
            if not b or b == b'\n':
                break
            header_bytes.extend(b)
        header_text = header_bytes.decode('ascii', errors='replace')
        
        # Now read binary data: n_cells * nvars doubles
        expected_size = n_cells * nvars * 8
        raw = f.read(expected_size)
        
        if len(raw) != expected_size:
            print(f"  Box {idx}: WARNING expected {expected_size} bytes, got {len(raw)}")
        
        data = np.frombuffer(raw, dtype=np.float64)
        data = data.reshape(nvars, n_cells)
        
        k_vals = data[k_idx, :]
        eps_vals = data[eps_idx, :]
        all_k.append(k_vals)
        all_eps.append(eps_vals)
        
        if idx == 0:
            print(f"  Box 0 header: '{header_text[:80]}...'")
            print(f"  Box 0: first k values: {k_vals[:5]}")
            print(f"  Box 0: first eps values: {eps_vals[:5]}")

k_all = np.concatenate(all_k)
eps_all = np.concatenate(all_eps)
k_all = np.maximum(k_all, 0.0)
eps_all = np.maximum(eps_all, 0.0)

# Stats
pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
k_pct = np.percentile(k_all, pcts)
eps_pct = np.percentile(eps_all, pcts)

print(f"\n===== k STATISTICS =====")
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
for thresh in [0.1, 0.01, 0.001]:
    cnt = np.sum(k_all < thresh)
    print(f"\nCells with k < {thresh}: {cnt} ({100*cnt/total:.2f}%)")

# Compare to inlet value: k_inlet = 1.5*(0.10*8)^2 = 0.96
# The "healthy" cells should have k reasonably close to 0.96
k_inlet_est = 1.5 * (0.10 * 8.0)**2
print(f"\nInlet k estimate: {k_inlet_est:.4f}")
print(f"Cells with k > 0.1: {np.sum(k_all > 0.1)}")
print(f"Cells with k > 0.5: {np.sum(k_all > 0.5)}")
print(f"Fraction k > 0.1: {100*np.sum(k_all > 0.1)/total:.2f}%")
print(f"Fraction k > 0.5: {100*np.sum(k_all > 0.5)/total:.2f}%")
