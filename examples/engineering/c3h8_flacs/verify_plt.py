#!/usr/bin/env python3
"""Verify cylinder volFrac pattern and k z-symmetry in plt00100."""
import numpy as np
import sys

plt_dir = sys.argv[1] if len(sys.argv) > 1 else "plt00100"

# Read Header
with open(f"{plt_dir}/Header") as f:
    lines = f.readlines()
nvars = int(lines[1].strip())
comp_names = [lines[i].strip() for i in range(2, 2+nvars)]
k_idx = comp_names.index("k")
vf_idx = comp_names.index("volFrac")
print(f"k={k_idx}, volFrac={vf_idx}")

# Read Cell_H
offsets = []
boxes = []
with open(f"{plt_dir}/Level_0/Cell_H") as f:
    f.readline(); f.readline()
    ncomp_h = int(f.readline().strip())
    f.readline()
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
    f.readline()
    n_on_disk = int(f.readline().strip())
    for _ in range(n_on_disk):
        line = f.readline().strip()
        offsets.append(int(line.split()[-1]))

print(f"Boxes: {nboxes}")

# Domain info from header
# prob_lo = (0,0,0), prob_hi = (80,50,40), n_cell = 160,100,80
# dx = 0.5, dy = 0.5, dz = 0.5
dx, dy, dz = 0.5, 0.5, 0.5

# Read data
data_file = f"{plt_dir}/Level_0/Cell_D_00000"
with open(data_file, "rb") as f:
    all_data = []
    for idx, ((lo, hi), offset) in enumerate(zip(boxes, offsets)):
        nx = hi[0] - lo[0] + 1
        ny = hi[1] - lo[1] + 1
        nz = hi[2] - lo[2] + 1
        n_cells = nx * ny * nz
        
        f.seek(offset)
        header_bytes = bytearray()
        while True:
            b = f.read(1)
            if not b or b == b'\n':
                break
            header_bytes.extend(b)
        
        expected_size = n_cells * nvars * 8
        raw = f.read(expected_size)
        data = np.frombuffer(raw, dtype=np.float64).reshape(nvars, n_cells)
        
        # Extract coordinates
        xs = np.zeros(n_cells)
        ys = np.zeros(n_cells)
        zs = np.zeros(n_cells)
        idx = 0
        for k in range(lo[2], hi[2]+1):
            z = (k + 0.5) * dz
            for j in range(lo[1], hi[1]+1):
                y = (j + 0.5) * dy
                for i in range(lo[0], hi[0]+1):
                    x = (i + 0.5) * dx
                    xs[idx] = x
                    ys[idx] = y
                    zs[idx] = z
                    idx += 1
        
        all_data.append({
            'lo': lo, 'hi': hi,
            'x': xs, 'y': ys, 'z': zs,
            'k': data[k_idx, :],
            'volFrac': data[vf_idx, :]
        })

# Combine all
x_all = np.concatenate([d['x'] for d in all_data])
y_all = np.concatenate([d['y'] for d in all_data])
z_all = np.concatenate([d['z'] for d in all_data])
k_all = np.concatenate([d['k'] for d in all_data])
vf_all = np.concatenate([d['volFrac'] for d in all_data])

# ============================================
# 1. Check volFrac - find cells with volFrac < 1.0 (partially covered by EB)
# ============================================
eb_cells = vf_all < 0.99
n_eb = np.sum(eb_cells)
print(f"\n===== volFrac ANALYSIS =====")
print(f"Total cells: {len(vf_all):,}")
print(f"EB cells (volFrac<0.99): {n_eb} ({100*n_eb/len(vf_all):.2f}%)")

# Get x,y positions of EB cells (z-midplane: 18.5 < z < 21.5, near z=20)
mid_z = (z_all > 18.5) & (z_all < 21.5)
eb_mid = eb_cells & mid_z
eb_x = x_all[eb_mid]
eb_y = y_all[eb_mid]

print(f"EB cells near z-midplane (18.5-21.5): {np.sum(eb_mid)}")

# Check for cylinders at expected positions:
# c1: (20, 25, 20), c2: (35, 17.5, 20), c3: (35, 32.5, 20), radius=5
def check_cylinder(cx, cy, label):
    near = (eb_x > cx-6) & (eb_x < cx+6) & (eb_y > cy-6) & (eb_y < cy+6)
    cnt = np.sum(near)
    if cnt > 0:
        print(f"  {label} at ({cx},{cy}): {cnt} EB cells found ✓")
    else:
        print(f"  {label} at ({cx},{cy}): NO EB cells ✗")

check_cylinder(20, 25, "c1(前)")
check_cylinder(35, 17.5, "c2(后左)")
check_cylinder(35, 32.5, "c3(后右)")

# Check spacing
# c2-c3 y-distance should be 32.5-17.5 = 15m
# c1-c2 distance = sqrt((35-20)^2 + (17.5-25)^2) = sqrt(225 + 56.25) = sqrt(281.25) ≈ 16.77m
print(f"\nCylinder spacing:")
print(f"  c2-c3 y-distance: 32.5-17.5 = 15.0 m (target: 15m)")

# ============================================
# 2. Check k z-symmetry at upper/lower boundaries
# ============================================
print(f"\n===== k BOUNDARY SYMMETRY =====")

# z-lo boundary: z < 1.0 (first 2 cells from z=0)
# z-hi boundary: z > 39.0 (last 2 cells from z=40)
z_lo = z_all < 1.0
z_hi = z_all > 39.0

# Get x-y cross sections near boundaries (away from cylinders)
# Use x in [60, 70], y in [10, 40] (well downstream, away from cylinders)
far_field = (x_all > 60) & (x_all < 70) & (y_all > 10) & (y_all < 40)

k_lo = k_all[z_lo & far_field]
k_hi = k_all[z_hi & far_field]

print(f"Far-field k at z-lo boundary: mean={k_lo.mean():.6f}, min={k_lo.min():.6e}, max={k_lo.max():.6e}")
print(f"Far-field k at z-hi boundary: mean={k_hi.mean():.6f}, min={k_hi.min():.6e}, max={k_hi.max():.6e}")

if len(k_lo) > 0 and len(k_hi) > 0:
    diff = abs(k_lo.mean() - k_hi.mean())
    if diff < 1e-8:
        print("  k symmetry: IDENTICAL ✓")
    elif diff < 1e-4:
        print(f"  k symmetry: near-identical (diff={diff:.2e}) ✓")
    else:
        print(f"  k symmetry: DIFFERENT (diff={diff:.2e}) - may need investigation")

# Also check across entire boundary
k_lo_all = k_all[z_lo]
k_hi_all = k_all[z_hi]
print(f"\nEntire boundary region:")
print(f"  z-lo: cells={len(k_lo_all)}, mean k={k_lo_all.mean():.6f}")
print(f"  z-hi: cells={len(k_hi_all)}, mean k={k_hi_all.mean():.6f}")
if abs(k_lo_all.mean() - k_hi_all.mean()) < 1e-6:
    print("  Entire boundary k: SYMMETRIC ✓")
else:
    print(f"  Entire boundary k diff: {abs(k_lo_all.mean()-k_hi_all.mean()):.2e}")

# Check for any NaN/Inf
print(f"\nk NaN count: {np.sum(np.isnan(k_all))}")
print(f"k Inf count: {np.sum(np.isinf(k_all))}")
print(f"k negative count: {np.sum(k_all < 0)}")
