#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir=${CODEX_PARALLEL_PERF_LOG_DIR:-/tmp/codex_parallel_perf_baseline_$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$log_dir"
summary="$log_dir/summary.tsv"

printf 'suite\tmode\tsolver\tranks\tthreads\twall_elapsed_sec\tstatus\twarning\tlog_dir\trun_log\tvalidation_log\n' > "$summary"

now_ns() {
  python3 - <<'PY'
import time
print(time.time_ns())
PY
}

elapsed_sec() {
  python3 - "$1" "$2" <<'PY'
import sys
start = int(sys.argv[1])
end = int(sys.argv[2])
print(f"{(end-start)/1.0e9:.6f}")
PY
}

record_case() {
  local suite=$1 mode=$2 solver=$3 ranks=$4 threads=$5 case_log_dir=$6 validation_log=$7 warning=$8 elapsed=$9
  local run_log="$case_log_dir/run.log"
  if [[ "$mode" == "serial" ]]; then
    run_log="$case_log_dir/tool.log"
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\tPASS\t%s\t%s\t%s\t%s\n' \
    "$suite" "$mode" "$solver" "$ranks" "$threads" "$elapsed" "$warning" "$case_log_dir" "$run_log" "$validation_log" >> "$summary"
}

run_wrapped() {
  local suite=$1 mode=$2 solver=$3 ranks=$4 threads=$5 script=$6
  local case_log_dir="$log_dir/${suite}_${mode}"
  mkdir -p "$case_log_dir"
  echo "[codex-parallel-perf] START ${suite}/${mode}"
  local start end elapsed warning validation_log
  start=$(now_ns)
  case "$mode" in
    serial)
      (cd "$repo_root" && JOBS="${JOBS:-2}" RUN_TIMEOUT="${RUN_TIMEOUT:-240}" "$script") >"$case_log_dir/tool.log" 2>&1
      validation_log=""
      ;;
    mpi)
      (cd "$repo_root" && CODEX_SMOKE_LOG_DIR="$case_log_dir" JOBS="${JOBS:-2}" RUN_TIMEOUT="${RUN_TIMEOUT:-240}" MPI_RANKS="$ranks" "$script") >"$case_log_dir/tool.log" 2>&1
      validation_log="$case_log_dir/validation.log"
      ;;
    omp)
      (cd "$repo_root" && CODEX_SMOKE_LOG_DIR="$case_log_dir" JOBS="${JOBS:-2}" RUN_TIMEOUT="${RUN_TIMEOUT:-240}" OMP_NUM_THREADS="$threads" "$script") >"$case_log_dir/tool.log" 2>&1
      validation_log="$case_log_dir/validation.log"
      ;;
    hybrid)
      (cd "$repo_root" && CODEX_SMOKE_LOG_DIR="$case_log_dir" JOBS="${JOBS:-2}" RUN_TIMEOUT="${RUN_TIMEOUT:-300}" MPI_RANKS="$ranks" OMP_NUM_THREADS="$threads" "$script") >"$case_log_dir/tool.log" 2>&1
      validation_log="$case_log_dir/validation.log"
      ;;
    *)
      echo "unknown mode $mode" >&2
      exit 2
      ;;
  esac
  end=$(now_ns)
  elapsed=$(elapsed_sec "$start" "$end")
  warning=""
  if [[ -n "$validation_log" && -f "$validation_log" ]] && grep -q 'warning=mpi_thread_support_level_0' "$validation_log"; then
    warning="mpi_thread_support_level_0"
  fi
  record_case "$suite" "$mode" "$solver" "$ranks" "$threads" "$case_log_dir" "$validation_log" "$warning" "$elapsed"
  echo "[codex-parallel-perf] PASS ${suite}/${mode} elapsed=${elapsed}s warning=${warning:-none}"
}

run_wrapped engineering serial pelelmex 1 1 tools/codex_smoke_engineering_pelelmex.sh
run_wrapped engineering mpi pelelmex "${MPI_RANKS:-2}" 1 tools/codex_smoke_engineering_pelelmex_mpi.sh
run_wrapped engineering omp pelelmex 1 "${OMP_NUM_THREADS:-2}" tools/codex_smoke_engineering_pelelmex_omp.sh
run_wrapped engineering hybrid pelelmex "${MPI_RANKS:-2}" "${OMP_NUM_THREADS:-2}" tools/codex_smoke_engineering_pelelmex_hybrid.sh
run_wrapped academic serial pelec 1 1 tools/codex_smoke_academic_pelec.sh
run_wrapped academic mpi pelec "${MPI_RANKS:-2}" 1 tools/codex_smoke_academic_pelec_mpi.sh
run_wrapped academic omp pelec 1 "${OMP_NUM_THREADS:-2}" tools/codex_smoke_academic_pelec_omp.sh
run_wrapped academic hybrid pelec "${MPI_RANKS:-2}" "${OMP_NUM_THREADS:-2}" tools/codex_smoke_academic_pelec_hybrid.sh

python3 "$repo_root/tools/validate_parallel_perf_summary.py" --summary "$summary" | tee "$log_dir/validation.log"

echo "[codex-parallel-perf] PASS; logs: $log_dir"
