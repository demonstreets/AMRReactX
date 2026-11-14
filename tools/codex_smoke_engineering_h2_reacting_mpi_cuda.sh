#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="${CODEX_REACTING_MPI_CUDA_CASE_DIR:-$repo_root/examples/academic/bench_2gpu}"
exe="${CODEX_REACTING_MPI_CUDA_EXE:-$case_dir/PeleC3d.gnu.MPI.CUDA.ex}"
log_dir="${CODEX_REACTING_MPI_CUDA_LOG_DIR:-/tmp/codex_pelec_h2_reacting_ignition_openmpi_cuda_2rank_$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$log_dir"
log_dir=$(cd "$log_dir" && pwd)
input_file="$log_dir/input.codex_mpi_cuda_react_smoke"
summary_json="$log_dir/reacting_mpi_cuda_summary.json"
run_log="$log_dir/run.log"
launcher_log="$log_dir/launcher.log"

mkdir -p "$log_dir"

cat > "$input_file" <<'EOF_INPUT'
# Codex PeleC 2-rank MPI+CUDA H2/O2 reacting smoke.
max_step = 5
stop_time = 1.0e-7

geometry.is_periodic = 0 0 1
geometry.coord_sys = 0
geometry.prob_lo = 0.0 0.0 0.0
geometry.prob_hi = 3.0 2.0 0.16
amr.n_cell = 48 16 4

pelec.lo_bc = "NoSlipWall" "NoSlipWall" "Interior"
pelec.hi_bc = "FOExtrap"     "NoSlipWall" "Interior"

pelec.do_hydro = 1
pelec.do_react = 1
pelec.chem_integrator = "ReactorRK64"
pelec.allow_negative_energy = 1
pelec.ppm_type = 0
pelec.weno_scheme = 1
pelec.cfl = 0.05
pelec.plm_iorder = 2
pelec.use_flattening = 1

amrex.the_arena_init_size = 0
amr.max_level = 0
amr.blocking_factor = 4
amr.max_grid_size = 32
amr.checkpoint_files_output = 0
amr.plot_int = 1
amr.plot_vars = density Temp pressure rho_H2 rho_O2 rho_H2O rho_H rho_O rho_OH rho_HO2 rho_H2O2 rho_N2
amr.derive_plot_vars = x_velocity y_velocity z_velocity
pelec.plot_massfrac = 1

prob.p_0 = 2.0e5
prob.T_0 = 300.0
prob.T_hot = 2214.0
prob.p_hot = 1.8e7
prob.r_hot = 0.55
prob.u_hot = 2.84e5

amrex.abort_on_unused_inputs = 1
EOF_INPUT

find_cuda_root() {
  if [ -x "${HOME}/local/cuda-12.6/bin/nvcc" ]; then
    printf '%s\n' "${HOME}/local/cuda-12.6"
    return 0
  fi
  if command -v nvcc >/dev/null 2>&1; then
    dirname "$(dirname "$(command -v nvcc)")"
    return 0
  fi
  if [ -d /usr/local/cuda ]; then
    printf '%s\n' /usr/local/cuda
    return 0
  fi
  return 1
}

cuda_root=$(find_cuda_root)
sundials_cuda_dir="${SUNDIALS_CUDA_DIR:-${HOME}/local/sundials-cuda}"
cuda_libs=(
  "$cuda_root/targets/x86_64-linux/lib"
  "$cuda_root/lib64"
  "/usr/local/cuda/lib64"
)
sundials_libs=(
  "$sundials_cuda_dir/lib"
  "$repo_root/external/PeleC/Submodules/PelePhysics/ThirdParty/INSTALL/gnu.CUDA/lib"
)
export LD_LIBRARY_PATH="$(IFS=:; printf '%s' "${sundials_libs[*]}:${cuda_libs[*]}:${LD_LIBRARY_PATH:-}")"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export AMREX_CUDA_ARCH="${AMREX_CUDA_ARCH:-60}"

if [ ! -x "$exe" ]; then
  echo "reacting_mpi_cuda_smoke FAIL missing executable: $exe" >&2
  exit 2
fi

launcher="${CODEX_REACTING_MPI_CUDA_LAUNCHER:-}"
if [ -z "$launcher" ]; then
  launcher=$(command -v mpirun || command -v mpirun.openmpi)
fi
if [ -z "$launcher" ] || ! "$launcher" --version 2>&1 | grep -Eqi 'Open MPI|OpenRTE'; then
  echo "reacting_mpi_cuda_smoke FAIL this PeleC build must be launched with OpenMPI mpirun" >&2
  exit 2
fi

{
  printf 'launcher=%s\n' "$launcher"
  "$launcher" --version 2>&1 | sed -n '1,6p'
  printf 'exe=%s\n' "$exe"
  printf 'LD_LIBRARY_PATH=%s\n' "$LD_LIBRARY_PATH"
  ldd "$exe" | grep -Ei 'not found|sundials|cuda|mpi' || true
} > "$launcher_log"
if grep -q 'not found' "$launcher_log"; then
  echo "reacting_mpi_cuda_smoke FAIL unresolved dynamic libraries" >&2
  cat "$launcher_log" >&2
  exit 2
fi

(
  cd "$log_dir"
  "$launcher" -np "${CODEX_REACTING_MPI_CUDA_RANKS:-2}" "$exe" "$input_file" > "$run_log" 2>&1
)

python3 - "$log_dir" "$summary_json" <<'PYCHECK'
import hashlib
import json
import math
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
summary_json = Path(sys.argv[2])
run_log_path = log_dir / "run.log"
input_path = log_dir / "input.codex_mpi_cuda_react_smoke"
ic_path = log_dir / "ic.txt"
job_info_path = log_dir / "plt00005" / "job_info"
header0_path = log_dir / "plt00000" / "Header"
header5_path = log_dir / "plt00005" / "Header"
launcher_log_path = log_dir / "launcher.log"

def fail(msg):
    raise SystemExit(f"reacting_mpi_cuda_smoke FAIL {msg}")

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

for path in [run_log_path, input_path, ic_path, job_info_path, header0_path, header5_path, launcher_log_path]:
    if not path.is_file():
        fail(f"missing evidence file: {path}")

run_log = run_log_path.read_text(errors="replace")
input_text = input_path.read_text(errors="replace")
job_info = job_info_path.read_text(errors="replace")
ic_text = ic_path.read_text(errors="replace")
failure_re = re.compile(
    r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|"
    r"CUDA error|GPU last error|Abort|FAIL|error while loading",
    re.I,
)
hits = [line.strip() for line in run_log.splitlines() if failure_re.search(line)]
if hits:
    fail(f"solver failure markers found: {hits[:3]}")
for needle in [
    "MPI initialized with 2 MPI processes",
    "CUDA initialized with 2 devices",
    "Creating ReactorBase instance: ReactorRK64",
]:
    if needle not in run_log:
        fail(f"missing run marker: {needle}")
if "AMReX" not in run_log or "finalized" not in run_log.lower():
    fail("AMReX did not finalize")
if "number of MPI processes: 2" not in job_info:
    fail("plotfile job_info does not prove two MPI ranks")
if "pelec.do_react = 1" not in input_text:
    fail("input does not enable reactions")
if 'pelec.chem_integrator = "ReactorRK64"' not in input_text:
    fail("input does not select ReactorRK64")

def parse_header(path):
    lines = path.read_text(errors="replace").splitlines()
    nvars = int(lines[1].strip())
    variables = [lines[i].strip() for i in range(2, 2 + nvars)]
    time_value = float(lines[2 + nvars + 1].strip())
    return variables, time_value

vars0, time0 = parse_header(header0_path)
vars5, time5 = parse_header(header5_path)
needed = {"density", "Temp", "rho_H2", "rho_O2", "rho_H2O"}
if not needed <= set(vars5):
    fail(f"missing reacting variables: {sorted(needed - set(vars5))}")
if not (math.isfinite(time0) and math.isfinite(time5) and time5 > time0):
    fail("plotfile time did not advance")

m = re.search(
    r"Hotspot:\s+p=([0-9.eE+-]+)\s+T=([0-9.eE+-]+)\s+rho=([0-9.eE+-]+)\s+"
    r"r=([0-9.eE+-]+)\s+cm\s+u=([0-9.eE+-]+)",
    ic_text,
)
if not m:
    fail("hotspot IC line missing")
hotspot = {
    "pressure": float(m.group(1)),
    "temperature": float(m.group(2)),
    "density": float(m.group(3)),
    "radius_cm": float(m.group(4)),
    "velocity_cm_s": float(m.group(5)),
}
if hotspot["temperature"] < 1000.0:
    fail("hotspot temperature too low")

summary = {
    "schema_version": 1,
    "status": "PASS-PELEC-H2-REACTING-MPI-CUDA-SMOKE",
    "case": "pelec_lidryer_h2_o2_hotspot_reacting_smoke",
    "run_dir": str(log_dir),
    "mpi_launcher": "OpenMPI mpirun",
    "mpi_ranks": 2,
    "cuda_devices": 2,
    "max_step": 5,
    "do_react": True,
    "chem_integrator": "ReactorRK64",
    "plotfiles": ["plt00000", "plt00005"],
    "initial_time": time0,
    "final_time": time5,
    "hotspot": hotspot,
    "validated_capabilities": {
        "pelec_reacting_solver": True,
        "h2_o2_lidryer_mechanism": True,
        "mpi_parallel": True,
        "cuda_parallel": True,
        "mpi_cuda_2rank_2device": True,
        "direct_engineering_obstacle_fire_propagation": False,
    },
    "evidence_files": [
        {"label": "run_log", "path": str(run_log_path), "sha256": sha(run_log_path)},
        {"label": "launcher_log", "path": str(launcher_log_path), "sha256": sha(launcher_log_path)},
        {"label": "input", "path": str(input_path), "sha256": sha(input_path)},
        {"label": "initial_condition_summary", "path": str(ic_path), "sha256": sha(ic_path)},
        {"label": "plt00005_job_info", "path": str(job_info_path), "sha256": sha(job_info_path)},
        {"label": "plt00000_header", "path": str(header0_path), "sha256": sha(header0_path)},
        {"label": "plt00005_header", "path": str(header5_path), "sha256": sha(header5_path)},
    ],
}
summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(
    "reacting_mpi_cuda_smoke PASS "
    f"log_dir={log_dir} mpi_ranks=2 cuda_devices=2 final_time={time5:.8e}"
)
PYCHECK
