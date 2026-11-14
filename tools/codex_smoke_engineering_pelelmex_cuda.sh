#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/c3h8_gpu_test"
exe="$case_dir/PeleLMeX3d.gnu.CUDA.ex"
input="$case_dir/input.codex_cuda_smoke"
log_dir="${CODEX_PELELMEX_CUDA_LOG_DIR:-/tmp/codex_pelelmex_cuda_smoke_$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$log_dir"
log_dir=$(cd "$log_dir" && pwd)
run_dir="$log_dir/run"
build_log="$log_dir/build.log"
run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
env_log="$log_dir/environment.log"
sundials_cuda_dir="${SUNDIALS_CUDA_DIR:-${SUNDIALS_DIR:-}}"
if [ -z "$sundials_cuda_dir" ]; then
  echo "[codex-smoke] set SUNDIALS_CUDA_DIR or SUNDIALS_DIR to a CUDA-capable SUNDIALS install" >&2
  exit 2
fi
if [ ! -d "$sundials_cuda_dir/include" ] || [ ! -d "$sundials_cuda_dir/lib" ]; then
  echo "[codex-smoke] invalid SUNDIALS CUDA install: $sundials_cuda_dir" >&2
  exit 2
fi
export SUNDIALS_CUDA_DIR="$sundials_cuda_dir"
export SUNDIALS_DIR="$sundials_cuda_dir"
cuda_bin=$(command -v nvcc || true)
if [ -n "$cuda_bin" ]; then
  cuda_root=$(cd "$(dirname "$cuda_bin")/.." && pwd)
  export LD_LIBRARY_PATH="$cuda_root/lib64:$cuda_root/targets/x86_64-linux/lib:$sundials_cuda_dir/lib:${LD_LIBRARY_PATH:-}"
else
  export LD_LIBRARY_PATH="$sundials_cuda_dir/lib:${LD_LIBRARY_PATH:-}"
fi

mkdir -p "$run_dir"
rm -rf "$run_dir"/plt* "$run_dir"/chk* "$run_dir"/Backtrace.* "$build_log" "$run_log" "$validation_log" "$env_log"

{
  date -u
  which nvidia-smi || true
  nvidia-smi || true
  which nvcc || true
  nvcc --version || true
  printf 'LD_LIBRARY_PATH=%s
' "${LD_LIBRARY_PATH:-}"
} > "$env_log" 2>&1

printf '[codex-smoke] building PeleLMeX CUDA executable
'
make -C "$case_dir" -j "${JOBS:-1}" > "$build_log" 2>&1

test -x "$exe"

printf '[codex-smoke] running 1-step PeleLMeX CUDA smoke
'
cd "$run_dir"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" timeout "${RUN_TIMEOUT:-180}" "$exe" "$input" > "$run_log" 2>&1

grep -q 'CUDA initialized with' "$run_log"
grep -q 'STEP \[0\]' "$run_log"
grep -q 'Writing plotfile: plt00001' "$run_log"
grep -q 'AMReX .* finalized' "$run_log"
if grep -q 'Unused ParmParse Variables' "$run_log"; then
  echo '[codex-smoke] PeleLMeX CUDA run left unused ParmParse variables' >&2
  exit 1
fi
if grep -q 'Backtrace\|Segfault\|CUDA error' "$run_log"; then
  echo '[codex-smoke] PeleLMeX CUDA run emitted failure diagnostics' >&2
  exit 1
fi
if [ ! -d "$run_dir/plt00001" ]; then
  echo '[codex-smoke] missing PeleLMeX CUDA plotfile plt00001' >&2
  exit 1
fi

python3 "$repo_root/tools/validate_pelelmex_cuda_smoke.py" --plotfile "$run_dir/plt00001" | tee "$validation_log"

printf '[codex-smoke] PASS PeleLMeX CUDA build=%s run=%s validation=%s env=%s
'   "$build_log" "$run_log" "$validation_log" "$env_log"
