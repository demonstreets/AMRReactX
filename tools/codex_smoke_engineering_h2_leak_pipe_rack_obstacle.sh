#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_PIPE_RACK_LOG_DIR:-/tmp/codex_h2_leak_pipe_rack_obstacle_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_dir/inputs"
asset_dir="$log_dir/assets"
summary_csv="$log_dir/pipe_rack_obstacle_summary.csv"
input_file="$input_dir/input.codex_pipe_rack_obstacle_smoke"
base_input="$repo_root/examples/engineering/h2_leak_3d/input.codex_stl_obstacle_smoke"

mkdir -p "$input_dir" "$asset_dir"

python3 - "$base_input" "$input_file" "$asset_dir" <<'PYGEN'
import math
import struct
import sys
from pathlib import Path

base = Path(sys.argv[1])
out = Path(sys.argv[2])
asset_dir = Path(sys.argv[3])


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vec_norm(v):
    mag = math.sqrt(sum(x * x for x in v))
    if mag == 0.0:
        return (0.0, 0.0, 0.0)
    return tuple(x / mag for x in v)


def tri_normal(tri):
    return vec_norm(vec_cross(vec_sub(tri[1], tri[0]), vec_sub(tri[2], tri[0])))


def write_binary_stl(path, triangles, name):
    header = (name[:80]).encode("ascii", errors="ignore").ljust(80, b" ")
    with path.open("wb") as fh:
        fh.write(header)
        fh.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            n = tri_normal(tri)
            fh.write(struct.pack("<12fH", *(n + tri[0] + tri[1] + tri[2]), 0))


def cube_triangles(center, size):
    cx, cy, cz = center
    sx, sy, sz = (0.5 * s for s in size)
    p = {
        "000": (cx - sx, cy - sy, cz - sz),
        "100": (cx + sx, cy - sy, cz - sz),
        "110": (cx + sx, cy + sy, cz - sz),
        "010": (cx - sx, cy + sy, cz - sz),
        "001": (cx - sx, cy - sy, cz + sz),
        "101": (cx + sx, cy - sy, cz + sz),
        "111": (cx + sx, cy + sy, cz + sz),
        "011": (cx - sx, cy + sy, cz + sz),
    }
    faces = [
        ("000", "010", "110", "100"),
        ("001", "101", "111", "011"),
        ("000", "100", "101", "001"),
        ("010", "011", "111", "110"),
        ("000", "001", "011", "010"),
        ("100", "110", "111", "101"),
    ]
    tris = []
    for a, b, c, d in faces:
        tris.append((p[a], p[b], p[c]))
        tris.append((p[a], p[c], p[d]))
    return tris


def axis_basis(p0, p1):
    axis = vec_norm(vec_sub(p1, p0))
    helper = (0.0, 0.0, 1.0)
    if abs(sum(axis[i] * helper[i] for i in range(3))) > 0.9:
        helper = (0.0, 1.0, 0.0)
    u = vec_norm(vec_cross(axis, helper))
    v = vec_norm(vec_cross(axis, u))
    return axis, u, v


def add_vec(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale_vec(s, a):
    return (s * a[0], s * a[1], s * a[2])


def cylinder_triangles(p0, p1, radius, segments=24):
    _, u, v = axis_basis(p0, p1)
    ring0 = []
    ring1 = []
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        radial = add_vec(scale_vec(math.cos(t) * radius, u), scale_vec(math.sin(t) * radius, v))
        ring0.append(add_vec(p0, radial))
        ring1.append(add_vec(p1, radial))
    tris = []
    for i in range(segments):
        j = (i + 1) % segments
        tris.append((ring0[i], ring0[j], ring1[j]))
        tris.append((ring0[i], ring1[j], ring1[i]))
        tris.append((p0, ring0[i], ring0[j]))
        tris.append((p1, ring1[j], ring1[i]))
    return tris


def pipe_rack_triangles():
    tris = []
    # Four posts.
    for x in (1.28, 1.62):
        for y in (0.32, 0.68):
            tris.extend(cylinder_triangles((x, y, 0.18), (x, y, 0.82), 0.035, 20))
    # Long pipe runs.
    for y in (0.38, 0.50, 0.62):
        for z in (0.34, 0.56, 0.76):
            tris.extend(cylinder_triangles((1.18, y, z), (1.72, y, z), 0.025, 20))
    # Cross members.
    for x in (1.28, 1.62):
        for z in (0.42, 0.70):
            tris.extend(cylinder_triangles((x, 0.28, z), (x, 0.72, z), 0.018, 16))
    return tris


write_binary_stl(asset_dir / "codex_cube_block.stl", cube_triangles((0.86, 0.36, 0.48), (0.18, 0.22, 0.30)), "codex cube block")
write_binary_stl(
    asset_dir / "codex_vertical_cylinder.stl",
    cylinder_triangles((1.05, 0.68, 0.18), (1.05, 0.68, 0.82), 0.075, 28),
    "codex vertical cylinder",
)
write_binary_stl(asset_dir / "codex_pipe_rack.stl", pipe_rack_triangles(), "codex pipe rack")

skip_prefixes = (
    "prob.obstacle_geometry",
    "prob.obstacle_stl_file",
    "prob.obstacle_stl_files",
    "prob.obstacle_stl_merged_file",
    "prob.obstacle_stl_scale",
    "prob.obstacle_stl_xc",
    "prob.obstacle_stl_yc",
    "prob.obstacle_stl_zc",
    "prob.obstacle_stl_reverse_normal",
    "prob.obstacle_stl_ngrow",
    "prob.obstacle_xc",
    "prob.obstacle_yc",
    "prob.obstacle_zc",
)
kept = [line for line in base.read_text(encoding="utf-8").splitlines() if not line.strip().startswith(skip_prefixes)]
kept.extend([
    "",
    "# Codex pipe-rack obstacle engineering geometry.",
    "prob.obstacle_geometry = stl",
    "prob.obstacle_stl_files = codex_cube_block.stl codex_vertical_cylinder.stl codex_pipe_rack.stl",
    "prob.obstacle_stl_merged_file = codex_merged_pipe_rack_obstacles.stl",
    "prob.obstacle_stl_scale = 1.0",
    "prob.obstacle_stl_xc = 0.0",
    "prob.obstacle_stl_yc = 0.0",
    "prob.obstacle_stl_zc = 0.0",
    "prob.obstacle_stl_reverse_normal = 0",
    "prob.obstacle_stl_ngrow = 4",
    "eb2.cover_multiple_cuts = 1",
    "prob.obstacle_xc = 0.0",
    "prob.obstacle_yc = 0.0",
    "prob.obstacle_zc = 0.0",
])
out.write_text("\n".join(kept) + "\n", encoding="utf-8")
PYGEN

CODEX_H2_LEAK_PROFILE_INPUT="$input_file" \
CODEX_H2_LEAK_HISTORY_EXTRA_FILES="$asset_dir/codex_cube_block.stl $asset_dir/codex_vertical_cylinder.stl $asset_dir/codex_pipe_rack.stl" \
CODEX_H2_LEAK_STL_LOG_DIR="$log_dir" \
RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh"

python3 - "$log_dir/stl_obstacle_summary.csv" "$summary_csv" "$log_dir/run.log" <<'PYCHECK'
import csv
import sys
from pathlib import Path

source = Path(sys.argv[1])
out = Path(sys.argv[2])
run_log = Path(sys.argv[3]).read_text(encoding="utf-8", errors="replace")
rows = list(csv.DictReader(source.open(newline="", encoding="utf-8")))
if len(rows) != 1:
    raise SystemExit(f"FAIL: expected one pipe-rack STL summary row, got {len(rows)}")
row = rows[0]
expected = "codex_cube_block.stl;codex_vertical_cylinder.stl;codex_pipe_rack.stl"
if row.get("stl_source_files") != expected:
    raise SystemExit(f"FAIL: unexpected obstacle source list: {row.get('stl_source_files')}")
if row.get("stl_file") != "codex_merged_pipe_rack_obstacles.stl":
    raise SystemExit(f"FAIL: unexpected merged STL file: {row.get('stl_file')}")
if int(row.get("stl_vertices", "0")) < 1000:
    raise SystemExit(f"FAIL: pipe-rack STL vertex count too small: {row.get('stl_vertices')}")
for needle in [
    ("Engineering leak UserDefined EB STL files: count=3", "H2 leak UserDefined EB STL files: count=3"),
    "stl_file[0]=codex_cube_block.stl",
    "stl_file[1]=codex_vertical_cylinder.stl",
    "stl_file[2]=codex_pipe_rack.stl",
    "buildFromSTL QA: file=codex_merged_pipe_rack_obstacles.stl",
    "Resetting fine-covered cells mask",
]:
    if isinstance(needle, tuple):
        ok = any(item in run_log for item in needle)
    else:
        ok = needle in run_log
    if not ok:
        raise SystemExit(f"FAIL: missing pipe-rack obstacle log marker: {needle}")
if not (0.95 <= float(row["mass_ratio"]) <= 1.05):
    raise SystemExit(f"FAIL: pipe-rack mass ratio out of range: {row['mass_ratio']}")
if float(row["cloud_volume"]) <= 0.0:
    raise SystemExit("FAIL: pipe-rack obstacle case did not produce a flammable cloud")
if int(row["active_planes"]) < 3 or int(row["flammable_planes"]) < 1:
    raise SystemExit(
        f"FAIL: insufficient hazard planes: active={row['active_planes']} flammable={row['flammable_planes']}"
    )
row["case"] = "pipe_rack_cube_cylinder_pipes"
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
    writer.writeheader()
    writer.writerow(row)
print(
    "h2_leak_pipe_rack_obstacle PASS "
    f"output={out} mass_ratio={float(row['mass_ratio']):.8e} "
    f"cloud_volume={float(row['cloud_volume']):.8e} "
    f"active_planes={row['active_planes']} flammable_planes={row['flammable_planes']} "
    f"vertices={row['stl_vertices']}"
)
PYCHECK

printf '[codex-smoke] PASS h2_leak pipe-rack cube/cylinder/pipes obstacle validation log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
