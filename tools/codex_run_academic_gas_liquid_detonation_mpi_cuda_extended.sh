#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

export PATH=/usr/local/cuda-12.6/bin:$PATH
export SUNDIALS_CUDA_DIR="${SUNDIALS_CUDA_DIR:-${HOME}/.local/sundials-cuda-6.4.1}"
export SUNDIALS_DIR="${SUNDIALS_DIR:-$SUNDIALS_CUDA_DIR}"
export AMREX_SUNDIALS_HOME="${AMREX_SUNDIALS_HOME:-$SUNDIALS_CUDA_DIR}"
export LD_LIBRARY_PATH="$SUNDIALS_CUDA_DIR/lib:/usr/local/cuda-12.6/lib64:${LD_LIBRARY_PATH:-}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1}"

root="docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803"
case_src="examples/academic/shock_droplet"
exe="$case_src/PeleC2d.gnu.MPI.CUDA.ex"
run_dir="$root/mpi_cuda_reacting_spray_detonation_1000step"
input="$run_dir/inputs"
launcher="${MPI_LAUNCHER:-$(command -v mpirun.openmpi || command -v mpirun)}"
jobs="${JOBS:-4}"
run_timeout="${RUN_TIMEOUT:-3600}"

mkdir -p "$root"

if [[ ! -x "$exe" ]]; then
  {
    printf 'UTC build start: '
    date -u
    make -C "$case_src" -j "$jobs" \
      DIM=2 USE_MPI=TRUE USE_OMP=FALSE USE_CUDA=TRUE \
      AMREX_SUNDIALS_HOME="$AMREX_SUNDIALS_HOME" \
      SUNDIALS_DIR="$SUNDIALS_DIR"
  } > "$root/build_mpi_cuda_extended.log" 2>&1
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$exe" "$run_dir/"
cp "$case_src"/initspraydata*.dat "$run_dir"/
cp "$case_src/inputs" "$input"

python3 - "$input" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(errors="replace")
replacements = {
    "max_step": "1000",
    "stop_time": "-1.0",
    "geometry.prob_hi": "50.0 2.0",
    "amr.n_cell": "128 32",
    "amr.blocking_factor": "16 16",
    "amr.max_grid_size": "64 32",
    "pelec.do_react": "1",
    "pelec.chem_integrator": '"ReactorCvode"',
    "cvode.solve_type": "GMRES",
    "cvode.rtol": "1e-6",
    "cvode.atol": "1e-10",
    "amr.checkpoint_files_output": "0",
    "amr.check_int": "-1",
    "amr.plot_files_output": "1",
    "amr.plot_int": "200",
    "pelec.plot_massfrac": "1",
    "pelec.plot_rhoy": "1",
    "particles.plot_src": "1",
    "amr.derive_plot_vars": "x_velocity y_velocity pressure",
    "pelec.sum_interval": "-1",
    "amr.v": "1",
    "pelec.v": "0",
    "prob.Y_NC7H16": "0.0621",
    "prob.Y_O2": "0.2186",
    "prob.Y_N2": "0.7193",
    "prob.p_left": "1.8e7",
    "prob.T_left": "2200.0",
    "prob.p_right": "1.013e6",
    "prob.T_right": "300.0",
}
lines = []
seen = set()
for raw in text.splitlines():
    stripped = raw.split("#", 1)[0].strip()
    if stripped and "=" in stripped:
        key = stripped.split("=", 1)[0].strip()
        if key == "amr.plot_per":
            continue
        if key in replacements:
            lines.append(f"{key} = {replacements[key]}")
            seen.add(key)
            continue
    lines.append(raw)
for key, value in replacements.items():
    if key not in seen:
        lines.append(f"{key} = {value}")
path.write_text("\n".join(lines) + "\n")
PY

{
  printf 'UTC start: '
  date -u
  printf 'CUDA_VISIBLE_DEVICES=%s\n' "$CUDA_VISIBLE_DEVICES"
  "$launcher" --version 2>&1 | sed -n '1,8p' || true
  nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader
  ldd "$exe" | grep -Ei 'not found|sundials|cuda|mpi' || true
} > "$root/mpi_cuda_launcher.log" 2>&1

if grep -q 'not found' "$root/mpi_cuda_launcher.log"; then
  cat "$root/mpi_cuda_launcher.log" >&2
  exit 2
fi

(
  cd "$run_dir"
  timeout "$run_timeout" "$launcher" --oversubscribe -np 2 "./$(basename "$exe")" "$(basename "$input")" > run.log 2>&1
)

{
  printf 'UTC end: '
  date -u
  nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader
} >> "$root/mpi_cuda_launcher.log" 2>&1

python3 tools/write_academic_gas_liquid_detonation_mpi_cuda_extended_report.py
python3 tools/write_academic_gas_liquid_detonation_mpi_cuda_extended_report.py \
  --verify-json "$root/academic_gas_liquid_detonation_mpi_cuda_extended_report.json"

printf 'academic_gas_liquid_detonation_mpi_cuda_extended RUNNER-PASS root=%s run_dir=%s\n' "$root" "$run_dir"
