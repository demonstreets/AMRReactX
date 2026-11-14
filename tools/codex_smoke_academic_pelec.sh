#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/detonation_2D"
exe="$case_dir/codex_deton2d_cpu2d.gnu.ex"

echo "[codex-smoke] building PeleC detonation_2D CPU baseline"
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_deton2d_cpu

echo "[codex-smoke] running 1-step PeleC detonation_2D baseline"
cd "$case_dir"
timeout "${RUN_TIMEOUT:-120}" "$exe" inputs.codex_smoke
