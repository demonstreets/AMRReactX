#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root=${CODEX_DATAVERSE_REFINED_SOURCE_PROJECTION_ROOT:-docs/codex_audit/evidence/dataverse_refined_source_projection_probe_mpi_cuda_20260807}
input_name=input.dataverse_refined_source_projection_probe_3d

rm -rf "$root"
mkdir -p "$root"
cp "examples/engineering/h2_leak_3d/$input_name" "$root/"

set +e
CODEX_H2_LEAK_HISTORY_USE_MPI=TRUE \
CODEX_H2_LEAK_HISTORY_USE_CUDA=TRUE \
CODEX_H2_LEAK_HISTORY_EBASE=codex_h2_leak_dataverse_open_channel_scout \
CODEX_H2_LEAK_HISTORY_SKIP_BUILD=TRUE \
CODEX_H2_LEAK_HISTORY_INPUT="$input_name" \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$repo_root/$root" \
CODEX_H2_LEAK_HISTORY_MPI_RANKS=2 \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO=0.0 \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO=2.0 \
CODEX_H2_LEAK_HISTORY_MAX_MASS_DROP_RATIO=1.0 \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO=0.01 \
CODEX_H2_LEAK_HISTORY_MAX_CENTER_OFFSET=1.0 \
CODEX_H2_LEAK_HISTORY_MIN_DOWNSTREAM_FRACTION=0.0 \
CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION=0.0 \
RUN_TIMEOUT=240 \
bash tools/codex_smoke_engineering_h2_leak_plume_history.sh > "$root/background.log" 2>&1
rc=$?
set -e

echo "run_rc=$rc" > "$root/run.status"
if [[ "$rc" -eq 0 ]]; then
  echo DONE > "$root/status.txt"
else
  echo FAILED > "$root/status.txt"
fi

exit "$rc"
