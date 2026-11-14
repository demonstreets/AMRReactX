#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export CODEX_H2_LEAK_PROFILE_INPUT="${CODEX_H2_LEAK_PROFILE_INPUT:-input.codex_open_domain_multibox_smoke}"
export CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR="${CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR:-/tmp/codex_h2_leak_open_domain_multibox_$(date -u +%Y%m%dT%H%M%SZ)}"

"$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain.sh"

input_base=$(basename "$CODEX_H2_LEAK_PROFILE_INPUT")
input_file="$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR/run/$input_base"
max_step=$(awk '$1 == "amr.max_step" {print $3}' "$input_file")
printf -v final_plot 'plt%05d' "$max_step"
cell_h="$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR/run/$final_plot/Level_0/Cell_H"
fab_count=$(grep -c '^FabOnDisk:' "$cell_h")
if [ "$fab_count" -lt 2 ]; then
  printf '[codex-smoke] FAIL h2_leak open-domain multibox expected >=2 FabOnDisk entries, got %s in %s
' "$fab_count" "$cell_h" >&2
  exit 1
fi

printf '[codex-smoke] PASS h2_leak open-domain multibox validation log_dir=%s final_plot=%s fab_count=%s
' "$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR" "$final_plot" "$fab_count"
