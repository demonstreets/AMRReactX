#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/external/PelePhysics/Testing/Exec/IgnitionDelay"
exe="$case_dir/codex_h2_ign_delay2d.gnu.ex"
log_dir="${CODEX_H2_IGNITION_DELAY_LOG_DIR:-/tmp/codex_h2_ignition_delay_$(date -u +%Y%m%dT%H%M%SZ)}"
log_dir=$(mkdir -p "$log_dir" && cd "$log_dir" && pwd)
validation_log="$log_dir/validation.log"

mkdir -p "$log_dir"
rm -rf "$log_dir"/n* "$validation_log"

printf '[codex-smoke] building PelePhysics H2/O2 ignition-delay driver\n'
make -C "$case_dir" -j "${JOBS:-4}" Chemistry_Model=h2o2 EBASE=codex_h2_ign_delay USE_MPI=FALSE > "$log_dir/build.log" 2>&1

generate_input() {
  local ndt=$1
  local input=$2
  cat > "$input" <<EOF
ncells = 1 1 1
max_grid_size  = 1
fuel_name = H2
reactFormat = Array4
chem_integrator = "ReactorCvode"

ode.dt  = 0.01
ode.ndt = $ndt
ode.ode_ncells = 1
ode.reactor_type  = 2 # 1=full e, 2=full h
ode.verbose = 0
ode.use_typ_vals = 0
ode.rtol = 1e-10
ode.atol = 1e-12

cvode.solve_type = dense_direct
cvode.precond_type = dense_simplified_AJacobian
cvode.max_order = 4

amrex.fpe_trap_invalid = 1
amrex.fpe_trap_zero = 1
amrex.fpe_trap_overflow = 1

# 1 atm in CGS barye.
hr.press = 1013250.0
hr.t0 = 1200
hr.equiv_ratio = 1.0
hr.outputFolderHR = ./
EOF
}

validation_args=()
for ndt in 2500 5000 10000; do
  run_dir="$log_dir/n$ndt"
  mkdir -p "$run_dir"
  input="$run_dir/inputs.h2_ignition_delay"
  generate_input "$ndt" "$input"
  printf '[codex-smoke] running H2 ignition-delay ndt=%s\n' "$ndt"
  (cd "$run_dir" && timeout "${RUN_TIMEOUT:-180}" "$exe" "$input" > run.log 2>&1)
  grep -q 'Creating ReactorBase instance: ReactorCvode' "$run_dir/run.log"
  grep -q 'Fuel: H2, Oxy: O2' "$run_dir/run.log"
  grep -q 'AMReX .* finalized' "$run_dir/run.log"
  if grep -q 'Unused ParmParse Variables' "$run_dir/run.log"; then
    echo "[codex-smoke] H2 ignition-delay ndt=$ndt left unused ParmParse variables" >&2
    exit 1
  fi
  test -s "$run_dir/PPreaction.txt"
  validation_args+=(--case "n$ndt" "$run_dir/PPreaction.txt")
done

python3 "$repo_root/tools/validate_h2_ignition_delay.py" \
  "${validation_args[@]}" \
  --require-converging | tee "$validation_log"

printf '[codex-smoke] PASS H2/O2 ignition-delay validation logs=%s validation=%s\n' "$log_dir" "$validation_log"
