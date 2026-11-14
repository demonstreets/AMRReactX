#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
use_mpi="${CODEX_H2_LEAK_HISTORY_USE_MPI:-FALSE}"
use_omp="${CODEX_H2_LEAK_HISTORY_USE_OMP:-FALSE}"
use_cuda="${CODEX_H2_LEAK_HISTORY_USE_CUDA:-FALSE}"
ebase="${CODEX_H2_LEAK_HISTORY_EBASE:-codex_h2_leak}"
clean_build="${CODEX_H2_LEAK_HISTORY_CLEAN_BUILD:-AUTO}"
exe_suffix="gnu.ex"
if [[ "$use_cuda" == "TRUE" && "$use_mpi" == "TRUE" ]]; then
  exe_suffix="gnu.MPI.CUDA.ex"
elif [[ "$use_cuda" == "TRUE" ]]; then
  exe_suffix="gnu.CUDA.ex"
elif [[ "$use_mpi" == "TRUE" && "$use_omp" == "TRUE" ]]; then
  exe_suffix="gnu.MPI.OMP.ex"
elif [[ "$use_mpi" == "TRUE" ]]; then
  exe_suffix="gnu.MPI.ex"
elif [[ "$use_omp" == "TRUE" ]]; then
  exe_suffix="gnu.OMP.ex"
fi
input_name="${CODEX_H2_LEAK_HISTORY_INPUT:-input.codex_plume_history_smoke}"
exe="$case_dir/${ebase}3d.${exe_suffix}"
log_dir="${CODEX_H2_LEAK_HISTORY_LOG_DIR:-/tmp/codex_h2_leak_plume_history_$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$log_dir/run"
run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"

mkdir -p "$run_dir"
rm -rf "$run_dir"/plt* "$run_log" "$validation_log"

printf '[codex-smoke] building PeleLMeX h2_leak_3d plume-history validation USE_MPI=%s USE_OMP=%s EBASE=%s\n' "$use_mpi" "$use_omp" "$ebase"
if [[ "$use_cuda" == "TRUE" ]]; then
  cuda_bin=$(command -v nvcc || true)
  if [ -z "$cuda_bin" ] && [ -x /usr/local/cuda/bin/nvcc ]; then
    cuda_bin=/usr/local/cuda/bin/nvcc
    export PATH="/usr/local/cuda/bin:$PATH"
  fi
  if [ -z "$cuda_bin" ]; then
    for candidate in "${HOME}"/local/cuda-*/bin/nvcc /usr/local/cuda-*/bin/nvcc; do
      if [ -x "$candidate" ]; then
        cuda_bin="$candidate"
        export PATH="$(dirname "$candidate"):$PATH"
        break
      fi
    done
  fi
  if [ -z "$cuda_bin" ]; then
    echo "[codex-smoke] nvcc not found for h2_leak CUDA run" >&2
    exit 127
  fi
  cuda_root=$(cd "$(dirname "$cuda_bin")/.." && pwd)
  if [ -z "${AMREX_CUDA_ARCH:-}" ]; then
    cuda_arch=""
    device_query="$cuda_root/extras/demo_suite/deviceQuery"
    if [ -x "$device_query" ]; then
      cuda_arch=$("$device_query" 2>/dev/null \
        | awk -F: '/CUDA Capability Major\/Minor version number/ {gsub(/[[:space:]]/, "", $2); split($2, a, "."); print a[1] a[2]; exit}' \
        || true)
    fi
    if [ -z "$cuda_arch" ] && command -v nvidia-smi >/dev/null 2>&1; then
      cuda_arch=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null \
        | awk 'NR == 1 {gsub(/[.[:space:]]/, ""); print}' || true)
    fi
    if [ -n "$cuda_arch" ]; then
      export AMREX_CUDA_ARCH="$cuda_arch"
      printf '[codex-smoke] detected AMREX_CUDA_ARCH=%s for h2_leak CUDA run\n' "$AMREX_CUDA_ARCH"
    fi
  fi
  export LIBRARY_PATH="$cuda_root/lib64:$cuda_root/targets/x86_64-linux/lib:${LIBRARY_PATH:-}"
  export LD_LIBRARY_PATH="$cuda_root/lib64:$cuda_root/targets/x86_64-linux/lib:${LD_LIBRARY_PATH:-}"
  sundials_search_roots=(
    "${SUNDIALS_CUDA_DIR:-}"
    "${SUNDIALS_DIR:-}"
    "$HOME/local/sundials-cuda"
    "$repo_root/external/PeleLMeX/Submodules/PelePhysics/ThirdParty/INSTALL/gnu.CUDA"
    "$repo_root/external/PeleLMeX/Submodules/PelePhysics/Submodules/sundials"
    "$repo_root/external/PeleLMeX/build/Submodules/PelePhysics/Submodules/sundials"
    "$repo_root/build-gpu2/Submodules/PelePhysics/Submodules/sundials"
    "$repo_root/build-gpu-mpi/Submodules/PelePhysics/Submodules/sundials"
    "$repo_root/external/PelePhysics/ThirdParty/INSTALL/gnu.CUDA"
    "$repo_root/external/PelePhysics/Submodules/sundials"
  )
  sundials_lib_dirs=()
  for sundials_root in "${sundials_search_roots[@]}"; do
    if [ -d "$sundials_root" ]; then
      while IFS= read -r lib_dir; do
        sundials_lib_dirs+=("$lib_dir")
      done < <(find "$sundials_root" -type f \( -name 'libsundials_*.so' -o -name 'libsundials_*.a' \) -printf '%h\n' | sort -u)
    fi
  done
  if [ "${#sundials_lib_dirs[@]}" -gt 0 ]; then
    sundials_path=$(IFS=:; printf '%s' "${sundials_lib_dirs[*]}")
    export LIBRARY_PATH="$sundials_path${LIBRARY_PATH:+:$LIBRARY_PATH}"
    export LD_LIBRARY_PATH="$sundials_path:$LD_LIBRARY_PATH"
    printf '[codex-smoke] SUNDIALS CUDA library search path: %s\n' "$sundials_path"
  else
    echo '[codex-smoke] no SUNDIALS CUDA libraries found for h2_leak CUDA run' >&2
    exit 127
  fi
fi
if [[ "$use_mpi" == "TRUE" ]] && ! command -v mpirun >/dev/null 2>&1; then
  echo "[codex-smoke] mpirun not found for h2_leak plume-history MPI run" >&2
  exit 127
fi
if [[ "$use_mpi" == "TRUE" ]]; then
  # Some deployment images provide OpenMPI runtime libraries without the
  # unversioned development symlinks emitted by mpicxx --showme:link.
  # Prepare project-local shims so smoke builds are reproducible without root.
  # shellcheck source=/dev/null
  source "$repo_root/tools/prepare_mpi_link_shims.sh"
fi
mpi_show=""
mpi_run_version=""
if [[ "$use_mpi" == "TRUE" ]]; then
  mpi_show="$(mpicxx -show 2>/dev/null || mpicxx --showme 2>/dev/null || true)"
  mpi_run_version="$(mpirun --version 2>/dev/null | head -n 1 || true)"
fi
if [[ "$clean_build" == "AUTO" ]]; then
  clean_build=FALSE
  if [ ! -x "$exe" ]; then
    clean_build=TRUE
  elif [[ "$use_mpi" == "TRUE" ]]; then
    if printf '%s\n%s\n' "$mpi_show" "$mpi_run_version" | grep -qi openmpi; then
      if grep -RIl '/usr/lib/x86_64-linux-gnu/mpich/include' "$case_dir/tmp_build_dir" >/dev/null 2>&1; then
        clean_build=TRUE
      fi
    elif printf '%s\n%s\n' "$mpi_show" "$mpi_run_version" | grep -qi mpich; then
      if grep -RIl '/usr/lib/x86_64-linux-gnu/openmpi/include' "$case_dir/tmp_build_dir" >/dev/null 2>&1; then
        clean_build=TRUE
      fi
    fi
  fi
fi
if [[ "$clean_build" == "TRUE" && "${CODEX_H2_LEAK_HISTORY_SKIP_BUILD:-FALSE}" != "TRUE" ]]; then
  printf '[codex-smoke] clean rebuild for h2_leak_3d EBASE=%s USE_MPI=%s USE_OMP=%s USE_CUDA=%s\n' "$ebase" "$use_mpi" "$use_omp" "$use_cuda"
  rm -rf "$case_dir/tmp_build_dir" "$exe" "$case_dir/PeleLMeX3d.${exe_suffix}"
fi
if [[ "${CODEX_H2_LEAK_HISTORY_SKIP_BUILD:-FALSE}" == "TRUE" ]]; then
  if [ ! -x "$exe" ]; then
    echo "[codex-smoke] requested skip build but executable is missing: $exe" >&2
    exit 1
  fi
  printf '[codex-smoke] skipping h2_leak_3d build and reusing executable=%s\n' "$exe"
else
  make -C "$case_dir" -j "${JOBS:-4}" EBASE="$ebase" USE_MPI="$use_mpi" USE_OMP="$use_omp" USE_CUDA="$use_cuda" USE_EB=TRUE
fi
if [[ "$use_mpi" == "TRUE" ]]; then
  printf '[codex-smoke] MPI wrapper: %s\n' "$mpi_show"
  printf '[codex-smoke] MPI launcher: %s\n' "$mpi_run_version"
  if printf '%s\n%s\n' "$mpi_show" "$mpi_run_version" | grep -qi openmpi; then
    if grep -RIl '/usr/lib/x86_64-linux-gnu/mpich/include' "$case_dir/tmp_build_dir" >/dev/null 2>&1; then
      echo '[codex-smoke] mixed MPI build detected: OpenMPI launcher/wrapper with MPICH dependency records' >&2
      exit 1
    fi
  fi
fi

if [[ "$input_name" = /* ]]; then
  input_src="$input_name"
else
  input_src="$case_dir/$input_name"
fi
input_base=$(basename "$input_src")
cp "$input_src" "$run_dir/"
cp "$exe" "$run_dir/"
if [ -n "${CODEX_H2_LEAK_HISTORY_EXTRA_FILES:-}" ]; then
  for extra_file in $CODEX_H2_LEAK_HISTORY_EXTRA_FILES; do
    if [[ "$extra_file" = /* ]]; then
      extra_src="$extra_file"
    else
      extra_src="$case_dir/$extra_file"
    fi
    if [ ! -f "$extra_src" ]; then
      echo "[codex-smoke] missing extra h2 leak input asset: $extra_src" >&2
      exit 1
    fi
    cp "$extra_src" "$run_dir/"
  done
fi

max_step=$(awk '$1 == "amr.max_step" {print $3}' "$run_dir/$input_base")
plot_int=$(awk '$1 == "amr.plot_int" {print $3}' "$run_dir/$input_base")
if [ -z "$max_step" ] || [ -z "$plot_int" ]; then
  echo '[codex-smoke] unable to parse amr.max_step/amr.plot_int from input' >&2
  exit 1
fi
if [ "$max_step" -lt 1 ] || [ "$plot_int" -lt 1 ]; then
  echo '[codex-smoke] invalid amr.max_step/amr.plot_int in input' >&2
  exit 1
fi
final_step=$max_step
last_logged_step=$((max_step - 1))
printf -v final_plot 'plt%05d' "$final_step"
min_plotfiles=$((max_step / plot_int + 1))

printf '[codex-smoke] running PeleLMeX h2_leak_3d plume-history validation input=%s max_step=%s plot_int=%s USE_MPI=%s USE_OMP=%s USE_CUDA=%s OMP_NUM_THREADS=%s\n' "$input_base" "$max_step" "$plot_int" "$use_mpi" "$use_omp" "$use_cuda" "${OMP_NUM_THREADS:-1}"
cd "$run_dir"
if [[ "$use_mpi" == "TRUE" ]]; then
  mpi_ranks="${CODEX_H2_LEAK_HISTORY_MPI_RANKS:-${MPI_RANKS:-2}}"
  OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" timeout "${RUN_TIMEOUT:-180}" mpirun --oversubscribe -np "$mpi_ranks" "./$(basename "$exe")" "$input_base" > "$run_log" 2>&1
else
  OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" timeout "${RUN_TIMEOUT:-180}" "./$(basename "$exe")" "$input_base" > "$run_log" 2>&1
fi

if [[ "$use_mpi" == "TRUE" ]]; then
  grep -q "MPI initialized with ${CODEX_H2_LEAK_HISTORY_MPI_RANKS:-${MPI_RANKS:-2}} MPI processes" "$run_log"
fi
if [[ "$use_cuda" == "TRUE" ]]; then
  grep -q 'CUDA initialized with' "$run_log"
fi
if [[ "$use_omp" == "TRUE" ]]; then
  grep -q "OMP initialized with ${OMP_NUM_THREADS:-1} OMP threads" "$run_log"
fi
grep -q 'Applying H2 leak source:' "$run_log"
grep -q 'H2 leak discrete active volume=' "$run_log"
grep -q 'mdot_vol=' "$run_log"
grep -q 'Creating ReactorBase instance: ReactorNull' "$run_log"
grep -q "STEP \[$last_logged_step\]" "$run_log"
grep -q 'AMReX .* finalized' "$run_log"
if grep -q 'Unused ParmParse Variables' "$run_log"; then
  echo '[codex-smoke] h2_leak_3d plume-history run left unused ParmParse variables' >&2
  exit 1
fi
if [ ! -d "$run_dir/plt00000" ] || [ ! -d "$run_dir/$final_plot" ]; then
  echo "[codex-smoke] missing h2 leak plume-history plotfiles plt00000/$final_plot" >&2
  exit 1
fi

python3 "$repo_root/tools/validate_h2_leak_plume_history.py" \
  --run-dir "$run_dir" \
  --input "$run_dir/$input_base" \
  --log "$run_log" \
  --min-plotfiles "${CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES:-$min_plotfiles}" \
  --min-mass-growth-ratio "${CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO:-4.0}" \
  --max-mass-drop-ratio "${CODEX_H2_LEAK_HISTORY_MAX_MASS_DROP_RATIO:-1.0e-6}" \
  --min-final-mass-ratio "${CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO:-0.80}" \
  --max-final-mass-ratio "${CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO:-1.50}" \
  --max-center-offset "${CODEX_H2_LEAK_HISTORY_MAX_CENTER_OFFSET:-0.10}" \
  --min-downstream-fraction "${CODEX_H2_LEAK_HISTORY_MIN_DOWNSTREAM_FRACTION:-0.30}" \
  --min-upstream-fraction "${CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION:-0.20}" | tee "$validation_log"

printf '[codex-smoke] PASS h2_leak plume-history validation log=%s validation=%s\n' "$run_log" "$validation_log"
