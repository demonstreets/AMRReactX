#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mpi_ranks="${CODEX_H2_LEAK_OPEN_DOMAIN_MPI_RANKS:-${MPI_RANKS:-2}}"
export MPI_RANKS="$mpi_ranks"
export CODEX_H2_LEAK_HISTORY_MPI_RANKS="$mpi_ranks"
export CODEX_H2_LEAK_HISTORY_USE_MPI=TRUE
export CODEX_H2_LEAK_HISTORY_EBASE="${CODEX_H2_LEAK_HISTORY_EBASE:-codex_h2_leak_mpi}"
export CODEX_H2_LEAK_PROFILE_INPUT="${CODEX_H2_LEAK_PROFILE_INPUT:-input.codex_open_domain_flammable_smoke}"
export CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR="${CODEX_H2_LEAK_OPEN_DOMAIN_MPI_LOG_DIR:-/tmp/codex_h2_leak_open_domain_mpi_$(date -u +%Y%m%dT%H%M%SZ)}"

"$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain.sh"

run_log="$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR/run.log"
python3 "$repo_root/tools/validate_parallel_smoke_log.py" \
  --log "$run_log" \
  --mode mpi \
  --solver pelelmex \
  --expected-ranks "$mpi_ranks" \
  --require-final-time | tee "$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR/mpi_validation.log"

input_base=$(basename "$CODEX_H2_LEAK_PROFILE_INPUT")
input_file="$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR/run/$input_base"
max_step=$(awk '$1 == "amr.max_step" {print $3}' "$input_file")
printf -v final_plot 'plt%05d' "$max_step"
cell_h="$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR/run/$final_plot/Level_0/Cell_H"
fab_count=$(grep -c '^FabOnDisk:' "$cell_h")
if [ "$fab_count" -lt "$mpi_ranks" ]; then
  printf '[codex-smoke] FAIL h2_leak open-domain MPI expected at least %s FabOnDisk entries, got %s in %s
' "$mpi_ranks" "$fab_count" "$cell_h" >&2
  exit 1
fi

printf '[codex-smoke] PASS h2_leak open-domain MPI validation log_dir=%s ranks=%s final_plot=%s fab_count=%s
' "$CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR" "$mpi_ranks" "$final_plot" "$fab_count"
