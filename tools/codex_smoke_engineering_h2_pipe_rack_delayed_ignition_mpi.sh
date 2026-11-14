#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
ebase="${CODEX_PIPE_RACK_DELAYED_MPI_EBASE:-codex_h2_leak_delayed_ignition_pipe_rack}"
exe="$case_dir/${ebase}3d.gnu.MPI.ex"
log_root="${CODEX_PIPE_RACK_DELAYED_MPI_LOG_ROOT:-/tmp/codex_h2_pipe_rack_delayed_ignition_mpi_$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$log_root"
log_root=$(cd "$log_root" && pwd)
run_dir="$log_root/run"
input_file="$run_dir/input.codex_pipe_rack_delayed_ignition_mpi"
summary_json="$log_root/summary.json"
run_log="$log_root/run.log"
build_log="$log_root/build.log"
max_step="${CODEX_PIPE_RACK_DELAYED_MPI_MAX_STEP:-120}"
plot_int="${CODEX_PIPE_RACK_DELAYED_MPI_PLOT_INT:-10}"
mpi_ranks="${CODEX_PIPE_RACK_DELAYED_MPI_RANKS:-2}"
n_cell="${CODEX_PIPE_RACK_DELAYED_MPI_N_CELL:-32 16 16}"
max_grid_size="${CODEX_PIPE_RACK_DELAYED_MPI_MAX_GRID_SIZE:-16}"
ignition_start_time="${CODEX_PIPE_RACK_DELAYED_MPI_IGNITION_START_TIME:-2.0e-7}"
ignition_duration="${CODEX_PIPE_RACK_DELAYED_MPI_IGNITION_DURATION:-1.5e-7}"
ignition_power="${CODEX_PIPE_RACK_DELAYED_MPI_IGNITION_POWER:-1.0e10}"

rm -rf "$run_dir" "$run_log" "$summary_json"
mkdir -p "$run_dir"

python3 - "$run_dir" <<'PYGEN'
import math
import struct
import sys
from pathlib import Path

out = Path(sys.argv[1])


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(v):
    m = math.sqrt(sum(x * x for x in v))
    return (0.0, 0.0, 0.0) if m == 0.0 else tuple(x / m for x in v)


def tri_normal(tri):
    return norm(cross(sub(tri[1], tri[0]), sub(tri[2], tri[0])))


def write_stl(path, triangles, name):
    with path.open("wb") as fh:
        fh.write(name.encode("ascii", errors="ignore")[:80].ljust(80, b" "))
        fh.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            fh.write(struct.pack("<12fH", *(tri_normal(tri) + tri[0] + tri[1] + tri[2]), 0))


def cube(center, size):
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
    tris = []
    for a, b, c, d in [
        ("000", "010", "110", "100"),
        ("001", "101", "111", "011"),
        ("000", "100", "101", "001"),
        ("010", "011", "111", "110"),
        ("000", "001", "011", "010"),
        ("100", "110", "111", "101"),
    ]:
        tris.append((p[a], p[b], p[c]))
        tris.append((p[a], p[c], p[d]))
    return tris


def add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def scale(s, a):
    return tuple(s * x for x in a)


def basis(p0, p1):
    axis = norm(sub(p1, p0))
    helper = (0.0, 0.0, 1.0)
    if abs(sum(axis[i] * helper[i] for i in range(3))) > 0.9:
        helper = (0.0, 1.0, 0.0)
    u = norm(cross(axis, helper))
    v = norm(cross(axis, u))
    return u, v


def cylinder(p0, p1, radius, segments=16):
    u, v = basis(p0, p1)
    r0, r1 = [], []
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        radial = add(scale(math.cos(t) * radius, u), scale(math.sin(t) * radius, v))
        r0.append(add(p0, radial))
        r1.append(add(p1, radial))
    tris = []
    for i in range(segments):
        j = (i + 1) % segments
        tris.extend([(r0[i], r0[j], r1[j]), (r0[i], r1[j], r1[i]), (p0, r0[i], r0[j]), (p1, r1[j], r1[i])])
    return tris


pipe = []
for x in (1.28, 1.62):
    for y in (0.32, 0.68):
        pipe.extend(cylinder((x, y, 0.18), (x, y, 0.82), 0.035, 16))
for y in (0.38, 0.50, 0.62):
    for z in (0.34, 0.56, 0.76):
        pipe.extend(cylinder((1.18, y, z), (1.72, y, z), 0.025, 16))

cube_tris = cube((0.86, 0.36, 0.48), (0.18, 0.22, 0.30))
cylinder_tris = cylinder((1.05, 0.68, 0.18), (1.05, 0.68, 0.82), 0.075, 24)
write_stl(out / "codex_cube_block.stl", cube_tris, "codex cube block")
write_stl(out / "codex_vertical_cylinder.stl", cylinder_tris, "codex vertical cylinder")
write_stl(out / "codex_pipe_rack.stl", pipe, "codex pipe rack")
write_stl(out / "codex_premerged_pipe_rack_obstacles.stl", cube_tris + cylinder_tris + pipe, "codex premerged pipe rack")
PYGEN

cat > "$input_file" <<EOF_INPUT
# Codex 3D H2 pipe-rack delayed ignition smoke, CPU MPI.
geometry.is_periodic = 0 0 0
geometry.coord_sys   = 0
geometry.prob_lo     = 0.0 0.0 0.0
geometry.prob_hi     = 2.0 1.0 1.0

peleLM.lo_bc = Inflow SlipWallAdiab SlipWallAdiab
peleLM.hi_bc = Outflow SlipWallAdiab SlipWallAdiab
peleLM.v = 1
peleLM.incompressible = 0
peleLM.sdc_iterMax = 1
peleLM.num_init_iter = 1
peleLM.floor_species = 1
peleLM.user_defined_ext_sources = 1
peleLM.advection_scheme = Godunov_PLM
peleLM.do_react = 1
peleLM.chem_integrator = ReactorCvode

amr.n_cell = $n_cell
amr.v = 1
amr.max_level = 0
amr.blocking_factor = 4
amr.max_grid_size = $max_grid_size
amr.max_step = $max_step
amr.stop_time = -1.0
amr.fixed_dt = 1.0e-8
amr.cfl = 0.25
amr.plot_int = $plot_int
amr.check_int = -1
amr.derive_plot_vars = mass_fractions avg_pressure

prob.P_mean = 101325.0
prob.T_mean = 300.0
prob.wind_u = 0.50
prob.wind_v = 0.0
prob.leak_xc = 0.55
prob.leak_yc = 0.50
prob.leak_zc = 0.50
prob.leak_rate = 5.0e-4
prob.leak_radius = 0.10
prob.leak_vel_x = 0.50
prob.leak_vel_y = 0.0
prob.leak_vel_z = 0.0
prob.leak_T = 300.0

prob.initial_flammable_cloud = 1
prob.cloud_xc = 1.25
prob.cloud_yc = 0.50
prob.cloud_zc = 0.50
prob.cloud_rx = 0.34
prob.cloud_ry = 0.18
prob.cloud_rz = 0.18
prob.cloud_T = 300.0
prob.cloud_YH2 = 0.0283
prob.cloud_YO2 = 0.2264
prob.cloud_YN2 = 0.7453
prob.ignition_hotspot = 0
prob.ignition_xc = 1.25
prob.ignition_yc = 0.50
prob.ignition_zc = 0.50
prob.ignition_radius = 0.08
prob.ignition_T = 2000.0
prob.ignition_source = 1
prob.ignition_start_time = $ignition_start_time
prob.ignition_duration = $ignition_duration
prob.ignition_power = $ignition_power

eb2.geom_type = UserDefined
eb2.cover_multiple_cuts = 1
prob.obstacle_geometry = stl
prob.obstacle_stl_file = codex_premerged_pipe_rack_obstacles.stl
prob.obstacle_stl_merged_file = codex_premerged_pipe_rack_obstacles.stl
prob.obstacle_stl_scale = 1.0
prob.obstacle_stl_xc = 0.0
prob.obstacle_stl_yc = 0.0
prob.obstacle_stl_zc = 0.0
prob.obstacle_stl_reverse_normal = 0
prob.obstacle_stl_ngrow = 4

cvode.solve_type = GMRES
cvode.max_order = 4
mac_proj.verbose = 0
nodal_proj.verbose = 0
EOF_INPUT

if [[ "${CODEX_PIPE_RACK_DELAYED_MPI_CLEAN_BUILD:-AUTO}" == "TRUE" || ! -x "$exe" ]]; then
  rm -rf "$case_dir/tmp_build_dir" "$exe" "$case_dir/PeleLMeX3d.gnu.MPI.ex"
fi
source "$repo_root/tools/prepare_mpi_link_shims.sh"
make -C "$case_dir" -j "${JOBS:-4}" EBASE="$ebase" USE_MPI=TRUE USE_EB=TRUE > "$build_log" 2>&1
cp "$exe" "$run_dir/"

(
  cd "$run_dir"
  mpirun --oversubscribe -np "$mpi_ranks" "./$(basename "$exe")" "$(basename "$input_file")" > "$run_log" 2>&1
)

python3 - "$log_root" "$summary_json" "$max_step" "$mpi_ranks" <<'PYCHECK'
import hashlib
import json
import os
import re
import sys
from pathlib import Path

log_root = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
max_step = int(sys.argv[3])
mpi_ranks = int(sys.argv[4])
run_dir = log_root / "run"
run_log = log_root / "run.log"
input_path = run_dir / "input.codex_pipe_rack_delayed_ignition_mpi"
text = run_log.read_text(errors="replace")


def fail(msg):
    raise SystemExit(f"pipe_rack_delayed_ignition_mpi FAIL {msg}")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


for needle in [
    f"MPI initialized with {mpi_ranks} MPI processes",
    "Creating ReactorBase instance: ReactorCvode",
    "Initializing CVODE:",
    "H2 leak UserDefined EB STL: file=codex_premerged_pipe_rack_obstacles.stl",
    "Applying H2 leak source:",
    "H2 delayed ignition source: enabled=1",
    f"STEP [{max_step - 1}]",
]:
    if needle not in text:
        fail(f"missing marker: {needle}")
if "CUDA initialized" in text:
    fail("CPU/MPI run unexpectedly initialized CUDA")
if "AMReX" not in text or "finalized" not in text.lower():
    fail("AMReX did not finalize")
bad = [
    line.strip()
    for line in text.splitlines()
    if re.search(
        r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Segmentation|SIGSEGV|CUDA error|"
        r"Abort|Backtrace|Wrong solve_type|CVODE solve failed|reactor failed|deltaT_iters not converged",
        line,
        re.I,
    )
]
if bad:
    fail(f"failure markers: {bad[:5]}")


def parse_header(plot_name):
    lines = (run_dir / plot_name / "Header").read_text(errors="replace").splitlines()
    nvars = int(lines[1])
    variables = lines[2 : 2 + nvars]
    time_value = float(lines[2 + nvars + 1])
    return variables, time_value


def parse_cell_h(plot_name):
    lines = (run_dir / plot_name / "Level_0" / "Cell_H").read_text(errors="replace").splitlines()
    records = []
    i = 0
    while i < len(lines):
        m = re.match(r"^\s*([0-9]+),([0-9]+)\s*$", lines[i])
        if m:
            nrows = int(m.group(1))
            ncols = int(m.group(2))
            block = []
            for row_idx in range(nrows):
                vals = [float(x) for x in lines[i + 1 + row_idx].strip().rstrip(",").split(",") if x]
                if len(vals) != ncols:
                    fail(f"bad min/max row length in {plot_name}")
                block.append(vals)
            records.append(block)
            i += 1 + nrows
            continue
        i += 1
    if len(records) < 2:
        fail(f"cannot parse Cell_H records in {plot_name}")
    mins = [min(row[col] for row in records[0]) for col in range(len(records[0][0]))]
    maxs = [max(row[col] for row in records[1]) for col in range(len(records[1][0]))]
    return mins, maxs


plots = sorted(p.name for p in run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
if "plt00000" not in plots or f"plt{max_step:05d}" not in plots:
    fail(f"missing required plotfiles: {plots}")
required_vars = {"Y(H2)", "Y(O2)", "Y(H2O)", "temp", "HeatRelease", "I_R(H2)", "I_R(O2)"}
history = []
for plot in plots:
    variables, time_value = parse_header(plot)
    missing = sorted(required_vars - set(variables))
    if missing:
        fail(f"missing variables in {plot}: {missing}")
    mins, maxs = parse_cell_h(plot)
    def extrema(name):
        idx = variables.index(name)
        return mins[idx], maxs[idx]
    heat_min, heat_max = extrema("HeatRelease")
    ir_h2_min, ir_h2_max = extrema("I_R(H2)")
    _, yh2o_max = extrema("Y(H2O)")
    _, temp_max = extrema("temp")
    history.append({
        "plotfile": plot,
        "time": time_value,
        "temp_max": temp_max,
        "heat_release_abs_max": max(abs(heat_min), abs(heat_max)),
        "ir_h2_abs_max": max(abs(ir_h2_min), abs(ir_h2_max)),
        "y_h2o_max": yh2o_max,
    })

initial_h2o = history[0]["y_h2o_max"]
final_h2o = history[-1]["y_h2o_max"]
sustained_rows = [
    row for row in history[1:]
    if row["heat_release_abs_max"] >= float(os.environ.get("CODEX_PIPE_RACK_DELAYED_MPI_MIN_HEAT_RELEASE_ABS", "1000.0"))
    and row["ir_h2_abs_max"] >= float(os.environ.get("CODEX_PIPE_RACK_DELAYED_MPI_MIN_IR_H2_ABS", "1.0e-3"))
    and row["y_h2o_max"] > initial_h2o + float(os.environ.get("CODEX_PIPE_RACK_DELAYED_MPI_MIN_H2O_GROWTH", "1.0e-7"))
]
min_outputs = int(os.environ.get("CODEX_PIPE_RACK_DELAYED_MPI_MIN_SUSTAINED_OUTPUTS", "5"))
if len(sustained_rows) < min_outputs:
    fail(f"insufficient sustained reaction outputs: {len(sustained_rows)} < {min_outputs}")
if final_h2o <= initial_h2o + 1.0e-7:
    fail(f"H2O did not grow enough: initial={initial_h2o} final={final_h2o}")
if history[-1]["time"] <= history[0]["time"]:
    fail("plotfile time did not advance")

summary = {
    "schema_version": 1,
    "status": "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-MPI",
    "run_root": str(log_root),
    "run_dir": str(run_dir),
    "mpi_ranks": mpi_ranks,
    "cuda_devices": 0,
    "max_step": max_step,
    "plotfiles": plots,
    "reaction_history": history,
    "sustained_reaction_checks": {
        "min_sustained_outputs": min_outputs,
        "sustained_output_count": len(sustained_rows),
        "initial_y_h2o_max": initial_h2o,
        "final_y_h2o_max": final_h2o,
        "final_time": history[-1]["time"],
    },
    "validated_capabilities": {
        "cpu_mpi_parallel": True,
        "h2_leak_source": True,
        "pipe_rack_stl_obstacles": True,
        "initial_flammable_cloud": True,
        "delayed_ignition_timed_energy_source": True,
        "initial_hotspot_not_used": True,
        "reactor_cvode": True,
        "cvode_gmres": True,
        "sustained_post_ignition_fire_development": True,
    },
    "evidence_files": [
        {"label": "run_log", "path": str(run_log), "sha256": sha(run_log)},
        {"label": "input", "path": str(input_path), "sha256": sha(input_path)},
        {"label": "final_plot_header", "path": str(run_dir / f"plt{max_step:05d}" / "Header"), "sha256": sha(run_dir / f"plt{max_step:05d}" / "Header")},
    ],
}
summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(
    "pipe_rack_delayed_ignition_mpi PASS "
    f"log_root={log_root} max_step={max_step} mpi_ranks={mpi_ranks} "
    f"sustained_outputs={len(sustained_rows)} final_y_h2o={final_h2o:.8e}"
)
PYCHECK
