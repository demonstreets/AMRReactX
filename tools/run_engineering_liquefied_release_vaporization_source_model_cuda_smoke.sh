#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root=${CODEX_LIQUEFIED_RELEASE_SOURCE_MODEL_CUDA_SMOKE_ROOT:-docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807}
case_dir=examples/engineering/h2_leak_3d
stl_src=docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_cuda_20260806/runtime_evidence/codex_merged_pipe_rack_obstacles.stl

rm -rf "$root"
mkdir -p "$root"/{lng_ch4,lpg_c3h8}

export CUDA_HOME=/usr/local/cuda-12.6
export CUDA_PATH=/usr/local/cuda-12.6
export SUNDIALS_HOME="${SUNDIALS_HOME:-$HOME/.local/sundials-cuda-6.4.1}"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$SUNDIALS_HOME/lib:$SUNDIALS_HOME/lib64:$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"

{
  echo "--- env ---"
  nvcc --version
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  echo "CUDA_HOME=$CUDA_HOME"
  echo "SUNDIALS_HOME=$SUNDIALS_HOME"
} > "$root/environment.log" 2>&1

python3 tools/write_engineering_liquefied_release_vaporization_source_model_report.py > "$root/source_model_refresh.log" 2>&1

run_case() {
  local label=$1
  local input_src=$2
  local input_name=$3
  local exe_name=$4
  local out_dir="$root/$label"

  cp "$input_src" "$out_dir/$input_name"
  cp "$stl_src" "$out_dir/codex_merged_pipe_rack_obstacles.stl"
  {
    echo "exe=$case_dir/$exe_name"
    ls -lh "$case_dir/$exe_name"
    ldd "$case_dir/$exe_name" | grep -E 'sundials|cuda|curand|cusparse|cusolver' || true
  } > "$out_dir/executable.log" 2>&1

  pushd "$out_dir" > /dev/null
  set +e
  "$repo_root/$case_dir/$exe_name" "$input_name" \
    amr.max_step=6 \
    amr.plot_int=6 \
    amr.checkpoint_files_output=0 \
    amr.plot_files_output=0 \
    > "$repo_root/$out_dir/run.log" 2>&1
  local rc=$?
  set -e
  popd > /dev/null
  echo "run_rc=$rc" > "$out_dir/run.status"
  return "$rc"
}

run_case \
  lng_ch4 \
  docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/lng_ch4_screening_release/input.lng_ch4_screening_release.generated \
  input.lng_ch4_screening_release.generated \
  codex_ch4_timeseries_probe3d.gnu.CUDA.ex

run_case \
  lpg_c3h8 \
  docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/lpg_c3h8_screening_release/input.lpg_c3h8_screening_release.generated \
  input.lpg_c3h8_screening_release.generated \
  codex_c3h8_timeseries_probe3d.gnu.CUDA.ex
