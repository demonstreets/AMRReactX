#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_root="${CODEX_SBEPV5_D27_SCOUT_LOG_ROOT:-/tmp/codex_h2_sbepv5_d27_scout_cuda_$(date -u +%Y%m%dT%H%M%SZ)}"
asset_dir="$log_root/assets"
run_dir="$log_root/run"
input_file="$log_root/input.sbepv5_d27_scout_h2_leak_3d"
sensors_json="$log_root/sensors.sbepv5_d27_approx.json"
run_log="$log_root/run.log"
plume_json="$log_root/h2_plume_observation_report.json"
plume_md="$log_root/h2_plume_observation_report.md"
plume_extents_csv="$log_root/plume_extents.csv"
sensor_timeseries_csv="$log_root/sensor_timeseries.csv"

max_step="${CODEX_SBEPV5_D27_SCOUT_MAX_STEP:-250}"
plot_int="${CODEX_SBEPV5_D27_SCOUT_PLOT_INT:-50}"
fixed_dt="${CODEX_SBEPV5_D27_SCOUT_FIXED_DT:-1.0e-4}"
mpi_ranks="${CODEX_SBEPV5_D27_SCOUT_MPI_RANKS:-1}"
use_cuda="${CODEX_SBEPV5_D27_SCOUT_USE_CUDA:-TRUE}"
leak_rate="${CODEX_SBEPV5_D27_SCOUT_LEAK_RATE:-1.034e-4}"
leak_radius="${CODEX_SBEPV5_D27_SCOUT_LEAK_RADIUS:-0.050}"
leak_vel_x="${CODEX_SBEPV5_D27_SCOUT_LEAK_VEL_X:-1.0}"
use_baffles="${CODEX_SBEPV5_D27_SCOUT_USE_BAFFLES:-TRUE}"
plume_lfl="${CODEX_SBEPV5_D27_SCOUT_PLUME_LFL:-1.0e-8}"
plume_ufl="${CODEX_SBEPV5_D27_SCOUT_PLUME_UFL:-1.0}"
use_mpi=FALSE
if [ "$mpi_ranks" -gt 1 ]; then
  use_mpi=TRUE
fi

mkdir -p "$asset_dir" "$run_dir"

python3 - "$asset_dir" "$input_file" "$sensors_json" "$max_step" "$plot_int" "$fixed_dt" "$leak_rate" "$leak_radius" "$leak_vel_x" "$use_baffles" <<'PYGEN'
import json
import math
import struct
import sys
from pathlib import Path

asset_dir = Path(sys.argv[1])
input_file = Path(sys.argv[2])
sensors_json = Path(sys.argv[3])
max_step = int(sys.argv[4])
plot_int = int(sys.argv[5])
fixed_dt = float(sys.argv[6])
leak_rate = float(sys.argv[7])
leak_radius = float(sys.argv[8])
leak_vel_x = float(sys.argv[9])
use_baffles = sys.argv[10].strip().upper() == "TRUE"


def normal(tri):
    ax, ay, az = (tri[1][i] - tri[0][i] for i in range(3))
    bx, by, bz = (tri[2][i] - tri[0][i] for i in range(3))
    nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
    mag = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (0.0, 0.0, 0.0) if mag == 0.0 else (nx / mag, ny / mag, nz / mag)


def box_triangles(center, size):
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


def write_stl(path, triangles, name):
    header = name.encode("ascii", errors="ignore")[:80].ljust(80, b" ")
    with path.open("wb") as fh:
        fh.write(header)
        fh.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            fh.write(struct.pack("<12fH", *(normal(tri) + tri[0] + tri[1] + tri[2]), 0))


# D27 public facts give four baffles, each 0.30 m high by 0.20 m deep.
# Exact x/z placement still requires source-figure digitization, so this scout
# uses a documented alternating upper/lower layout only for program-side runs.
# Keep a one-cell clearance from z walls in this coarse scout mesh. The public
# D27 benchmark used baffles in the vessel, but exact wall attachment/clearance
# requires original geometry tables; touching coarse STL plates can create EB
# sliver states that dominate this code-path test.
baffles = [
    ("sbepv5_baffle_1_upper.stl", (0.30, 0.10, 0.725), (0.010, 0.180, 0.300)),
    ("sbepv5_baffle_2_lower.stl", (0.50, 0.10, 0.175), (0.010, 0.180, 0.300)),
    ("sbepv5_baffle_3_upper.stl", (0.70, 0.10, 0.725), (0.010, 0.180, 0.300)),
    ("sbepv5_baffle_4_lower.stl", (0.90, 0.10, 0.175), (0.010, 0.180, 0.300)),
]
for name, center, size in baffles:
    write_stl(asset_dir / name, box_triangles(center, size), name)

sensors = []
xs = [0.15, 0.45, 0.75, 1.05]
zs = [0.15, 0.45, 0.75]
reliable = {1, 2, 5, 7, 8, 9, 10, 12}
for sid in range(1, 13):
    row = (sid - 1) // 4
    col = (sid - 1) % 4
    sensors.append({
        "id": f"Gas{sid:02d}",
        "x": xs[col],
        "y": 0.18,
        "z": zs[row],
        "reliability": "reliable" if sid in reliable else "unreliable",
        "source_basis": "approximate_compartment_centerline_for_program_scout_not_external_agreement",
    })
sensors_json.write_text(json.dumps({
    "schema_version": 1,
    "sensor_basis": "SBEPV5 D27 approximate rear-wall compartment centers; exact coordinates require digitization/original table",
    "benchmark_id": "hysafe_sbepv5_d27",
    "sensors": sensors,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

baffle_input = ""
if use_baffles:
    baffle_input = f"""
eb2.geom_type = UserDefined
eb2.cover_multiple_cuts = 1
prob.obstacle_geometry = stl
prob.obstacle_stl_files = {' '.join(name for name, _, _ in baffles)}
prob.obstacle_stl_merged_file = sbepv5_d27_merged_baffles.stl
prob.obstacle_stl_scale = 1.0
prob.obstacle_stl_xc = 0.0
prob.obstacle_stl_yc = 0.0
prob.obstacle_stl_zc = 0.0
prob.obstacle_stl_reverse_normal = 0
prob.obstacle_stl_ngrow = 2
prob.obstacle_xc = 0.0
prob.obstacle_yc = 0.0
prob.obstacle_zc = 0.0
""".lstrip()
else:
    baffle_input = """
eb2.geom_type = all_regular
""".lstrip()

input_file.write_text(f"""
# HySafe SBEPV5 D27 style h2_leak_3d CUDA scout.
# Public facts used: 1.20 x 0.20 x 0.90 m vessel, 12 mm nozzle,
# 10.17 m/s H2 exit velocity, 1.15 Nl/s release, x/y/z jet =
# 0.03/0.10/0.145 m. The numeric source center is shifted to x=0.075 m
# and numeric source velocity is configurable so the regularized
# low-Mach scout remains stable on this coarse finite-volume mesh.
# Baffle and sensor positions are approximate program-scout placeholders
# until exact figure/table digitization is local.

geometry.is_periodic = 0 0 0
geometry.coord_sys   = 0
geometry.prob_lo     = 0.0 0.0 0.0
geometry.prob_hi     = 1.20 0.20 0.90

peleLM.lo_bc = Inflow NoSlipWallAdiab NoSlipWallAdiab
peleLM.hi_bc = Outflow NoSlipWallAdiab NoSlipWallAdiab
peleLM.v = 1
peleLM.incompressible = 0
peleLM.sdc_iterMax = 1
peleLM.num_init_iter = 1
peleLM.floor_species = 1
peleLM.user_defined_ext_sources = 1
peleLM.advection_scheme = Godunov_PLM
peleLM.do_react = 1
peleLM.chem_integrator = ReactorNull

amr.n_cell = 48 8 36
amr.v = 1
amr.max_level = 0
amr.blocking_factor = 4
amr.max_grid_size = 16
amr.max_step = {max_step}
amr.stop_time = -1.0
amr.fixed_dt = {fixed_dt:.12e}
amr.cfl = 0.5
amr.plot_int = {plot_int}
amr.check_int = -1
amr.derive_plot_vars = mass_fractions avg_pressure

prob.P_mean = 101325.0
prob.T_mean = 293.0
prob.wind_u = 0.0
prob.wind_v = 0.0
prob.leak_xc = 0.075
prob.leak_yc = 0.10
prob.leak_zc = 0.145
prob.leak_rate = {leak_rate:.12e}
prob.leak_radius = {leak_radius:.12e}
prob.leak_vel_x = {leak_vel_x:.12e}
prob.leak_vel_y = 0.0
prob.leak_vel_z = 0.0
prob.leak_T = 293.0

{baffle_input}
""".lstrip(), encoding="utf-8")
PYGEN

extra_files=""
if [[ "$use_baffles" == "TRUE" ]]; then
  extra_files="$asset_dir/sbepv5_baffle_1_upper.stl $asset_dir/sbepv5_baffle_2_lower.stl $asset_dir/sbepv5_baffle_3_upper.stl $asset_dir/sbepv5_baffle_4_lower.stl"
fi

CODEX_H2_LEAK_HISTORY_INPUT="$input_file" \
CODEX_H2_LEAK_HISTORY_EXTRA_FILES="$extra_files" \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_root" \
CODEX_H2_LEAK_HISTORY_USE_CUDA="$use_cuda" \
CODEX_H2_LEAK_HISTORY_USE_MPI="$use_mpi" \
CODEX_H2_LEAK_HISTORY_MPI_RANKS="$mpi_ranks" \
CODEX_H2_LEAK_HISTORY_EBASE="${CODEX_SBEPV5_D27_SCOUT_EBASE:-codex_h2_leak_sbepv5_d27_scout}" \
CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES="$((max_step / plot_int + 1))" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_SBEPV5_D27_SCOUT_MIN_MASS_GROWTH_RATIO:-1.5}" \
CODEX_H2_LEAK_HISTORY_MIN_DOWNSTREAM_FRACTION="${CODEX_SBEPV5_D27_SCOUT_MIN_DOWNSTREAM_FRACTION:-0.05}" \
CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION="${CODEX_SBEPV5_D27_SCOUT_MIN_UPSTREAM_FRACTION:-0.0}" \
RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

python3 "$repo_root/tools/write_engineering_h2_plume_observation_report.py" \
  --run-dir "$run_dir" \
  --sensors-json "$sensors_json" \
  --lfl "$plume_lfl" \
  --ufl "$plume_ufl" \
  --min-plotfiles "$((max_step / plot_int + 1))" \
  --min-sensors 8 \
  --sensor-sampling trilinear \
  --output-json "$plume_json" \
  --output-md "$plume_md" \
  --extents-csv "$plume_extents_csv" \
  --sensors-csv "$sensor_timeseries_csv"

python3 "$repo_root/tools/write_engineering_h2_plume_observation_report.py" --verify-json "$plume_json"

printf 'sbepv5_d27_scout_cuda PASS log_root=%s max_step=%s mpi_ranks=%s cuda=%s plume=%s\n' \
  "$log_root" "$max_step" "$mpi_ranks" "$use_cuda" "$plume_json"
