#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root=${CODEX_EXTERNAL_VAPORIZATION_CH4_TIMESERIES_CUDA_ROOT:-docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda}
case_dir=examples/engineering/h2_leak_3d
input_src=docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/input.codex_ch4_external_vaporization_timeseries
input_name=input.codex_ch4_external_vaporization_timeseries
exe_name=codex_ch4_timeseries_probe3d.gnu.CUDA.ex
stl_src=docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_cuda_20260806/runtime_evidence/codex_merged_pipe_rack_obstacles.stl
pipe_stl_src=docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_cuda_20260806/runtime_evidence/codex_pipe_rack.stl

rm -rf "$root"
mkdir -p "$root/run"

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

python3 tools/write_engineering_external_vaporization_multifuel_source_matrix_report.py > "$root/source_matrix_refresh.log" 2>&1
cp "$input_src" "$root/run/$input_name"
cp "$stl_src" "$root/run/codex_merged_pipe_rack_obstacles.stl"
cp "$pipe_stl_src" "$root/run/codex_pipe_rack.stl"

pushd "$case_dir" > /dev/null
{
  echo "--- env ---"
  nvcc --version
  echo "CUDA_HOME=$CUDA_HOME"
  echo "SUNDIALS_HOME=$SUNDIALS_HOME"
  echo "--- make ---"
  make -j"${CODEX_BUILD_JOBS:-8}" \
    USE_CUDA=TRUE \
    USE_MPI=FALSE \
    Chemistry_Model=CH4_lean \
    Eos_Model=Fuego \
    Transport_Model=Simple \
    EBASE=codex_ch4_timeseries_probe \
    TMP_BUILD_DIR=tmp_build_dir/codex_ch4_timeseries
  echo "--- executable ---"
  ls -lh "$exe_name"
  ldd "$exe_name" | grep -E 'sundials|cuda|curand|cusparse|cusolver' || true
  echo "CH4 TIMESERIES CUDA BUILD PASS"
} > "$repo_root/$root/build.log" 2>&1
popd > /dev/null

pushd "$root/run" > /dev/null
set +e
"$repo_root/$case_dir/$exe_name" "$input_name" \
  amr.max_step=6 \
  amr.plot_int=6 \
  amr.checkpoint_files_output=0 \
  amr.plot_files_output=0 \
  > "$repo_root/$root/run.log" 2>&1
rc=$?
set -e
popd > /dev/null

echo "run_rc=$rc" > "$root/run.status"
exit "$rc"
