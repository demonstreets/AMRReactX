#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/bfs_kepsilon"
exe="$case_dir/codex_bfs_cpu2d.gnu.ex"

echo "[codex-smoke] building PeleLMeX bfs_kepsilon CPU baseline"
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_bfs_cpu

echo "[codex-smoke] running 1-step PeleLMeX bfs_kepsilon baseline"
cd "$case_dir"
timeout "${RUN_TIMEOUT:-120}" "$exe" input.codex_smoke
