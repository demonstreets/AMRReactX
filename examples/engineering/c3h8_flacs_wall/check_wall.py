#!/usr/bin/env python3
"""Check k/epsilon at y_lo wall (y-index 0) in plt00050."""
import numpy as np
import sys

plt_dir = sys.argv[1] if len(sys.argv) > 1 else "plt00050"

# Read Header
with open(f"{plt_dir}/Header") as f:
    lines = f.readlines()
nvars = int(lines[1].strip())
comp_names = [lines[i].strip() for i in range(2, 2+nvars)]
k_idx = comp_names.index("k")
eps_idx = comp_names.index("epsilon")
print(f"Variables: {comp_names}")
print(f"k_idx={k_idx}, eps_idx={eps_idx}")

# Read Cell_H
offsets = []
boxes = []
with open(f"{plt_dir}/Level_0/Cell_H") as f:
    _ = f.readline()  # version
    _ = f.readline()
    ncomp_h = int(f.readline().strip())
    _ = f.readline()  # ngrow
    box_header = f.readline().strip()
    nboxes = int(box_header.strip("() ").split()[0])
    
    for _ in range(nboxes):
        line = f.readline().strip()
        cleaned = line.replace("(", "").replace(")", "").replace(",", " ")
        parts = cleaned.split()
        lo = [int(parts[0]), int(parts[1]), int(parts[2])]
        hi = [int(parts[3]), int(parts[4]), int(parts[5])]
        boxes.append((lo, hi))
    
    _ = f.readline()  # ")"
    
    n_on_disk = int(f.readline().strip())
    for _ in range(n_on_disk):
        line = f.readline().strip()
        parts = line.split()
        offsets.append(int(parts[-1]))

print(f"nboxes={nboxes}, n_on_disk={n_on_disk}")

# Find boxes touching y=0 lo boundary
ylo_boxes = [(i, lo, hi) for i, (lo, hi) in enumerate(boxes) if lo[1] == 0]
print(f"Boxes touching y_lo (lo[1]==0): {len(ylo_boxes)}")
for idx, lo, hi in ylo_boxes:
    print(f"  Box {idx}: lo={lo}, hi={hi} (nx={hi[0]-lo[0]+1}, ny={hi[1]-lo[1]+1}, nz={hi[2]-lo[2]+1})")

# Read data for y_lo boxes from Cell_D_00000 binary
data_file = f"{plt_dir}/Level_0/Cell_D_00000"
all_k_wall = []
all_eps_wall = []

with open(data_file, "rb") as f:
    for idx, lo, hi in ylo_boxes:
        nx = hi[0] - lo[0] + 1
        ny = hi[1] - lo[1] + 1
        nz = hi[2] - lo[2] + 1
        n_cells = nx * ny * nz
        expected_bytes = n_cells * nvars * 8
        
        f.seek(offsets[idx])
        # Skip FAB header until newline
        while True:
            b = f.read(1)
            if not b or b == b'\n':
                break
        
        raw = f.read(expected_bytes)
        actual = len(raw)
        if actual != expected_bytes:
            print(f"  Box {idx}: WARNING expected {expected_bytes}, got {actual}")
            if actual < expected_bytes:
                continue
        
        data = np.frombuffer(raw, dtype=np.float64).reshape(nvars, n_cells)
        
        # y=0 cells: for each z-slice, the first nx cells
        for z_local in range(nz):
            z_offset = z_local * nx * ny
            all_k_wall.append(data[k_idx, z_offset:z_offset + nx])
            all_eps_wall.append(data[eps_idx, z_offset:z_offset + nx])

if all_k_wall:
    k_wall = np.concatenate(all_k_wall)
    eps_wall = np.concatenate(all_eps_wall)
    k_wall_pos = np.maximum(k_wall, 0.0)
    eps_wall_pos = np.maximum(eps_wall, 0.0)
    
    print(f"\n===== y_lo WALL SUMMARY (k/eps at first cell off wall) =====")
    print(f"Total wall cells: {len(k_wall)}")
    print(f"k:  min={k_wall_pos.min():.6e}  max={k_wall_pos.max():.6e}  mean={k_wall_pos.mean():.6e}")
    print(f"eps: min={eps_wall_pos.min():.6e}  max={eps_wall_pos.max():.6e}  mean={eps_wall_pos.mean():.6e}")
    
    for thresh in [0, 1e-10, 1e-6, 1e-3, 0.01, 0.1, 0.3]:
        cnt_k = np.sum(k_wall_pos > thresh)
        cnt_eps = np.sum(eps_wall_pos > thresh)
        print(f"  k > {thresh:.0e}: {cnt_k}/{len(k_wall)} ({100*cnt_k/len(k_wall):.1f}%)"
              f"  |  eps > {thresh:.0e}: {cnt_eps}/{len(k_wall)} ({100*cnt_eps/len(k_wall):.1f}%)")
else:
    print("\nNo wall cells found!")
