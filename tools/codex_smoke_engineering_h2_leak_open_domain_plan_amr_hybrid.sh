#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mpi_ranks="${CODEX_H2_LEAK_PLAN_AMR_HYBRID_RANKS:-${MPI_RANKS:-4}}"
omp_threads="${CODEX_H2_LEAK_PLAN_AMR_HYBRID_THREADS:-${OMP_NUM_THREADS:-2}}"
log_root="${CODEX_H2_LEAK_PLAN_AMR_HYBRID_LOG_DIR:-/tmp/codex_h2_leak_open_domain_plan_amr_hybrid_$(date -u +%Y%m%dT%H%M%SZ)}"

export MPI_RANKS="$mpi_ranks"
export OMP_NUM_THREADS="$omp_threads"
export OMP_PROC_BIND="${OMP_PROC_BIND:-spread}"
export OMP_PLACES="${OMP_PLACES:-cores}"
export CODEX_H2_LEAK_HISTORY_MPI_RANKS="$mpi_ranks"
export CODEX_H2_LEAK_HISTORY_USE_MPI=TRUE
export CODEX_H2_LEAK_HISTORY_USE_OMP=TRUE
export CODEX_H2_LEAK_HISTORY_EBASE="${CODEX_H2_LEAK_HISTORY_EBASE:-codex_h2_leak_plan_amr_hybrid}"
export CODEX_H2_LEAK_PLAN_AMR_COMPARE_LOG_DIR="$log_root"
export CODEX_H2_LEAK_PLAN_AMR_LEVEL1_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_LEVEL1_MAX_GRID_SIZE:-16}"
export CODEX_H2_LEAK_PLAN_AMR_BASE_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_BASE_MAX_GRID_SIZE:-32}"
export CODEX_H2_LEAK_PLAN_AMR_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_PLAN_AMR_MIN_MASS_GROWTH_RATIO:-1.5}"
export CODEX_H2_LEAK_PLAN_AMR_MIN_ACTIVE_PLANES="${CODEX_H2_LEAK_PLAN_AMR_MIN_ACTIVE_PLANES:-2}"
export CODEX_H2_LEAK_PLAN_AMR_MIN_FLAMMABLE_PLANES="${CODEX_H2_LEAK_PLAN_AMR_MIN_FLAMMABLE_PLANES:-0}"

"$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh"

for case_name in baseline amr; do
  run_log="$log_root/$case_name/run.log"
  python3 "$repo_root/tools/validate_parallel_smoke_log.py" \
    --log "$run_log" \
    --mode hybrid \
    --solver pelelmex \
    --expected-ranks "$mpi_ranks" \
    --expected-threads "$omp_threads" \
    --require-final-time \
    --allow-thread-support-zero | tee "$log_root/$case_name/hybrid_validation.log"
done

python3 - "$repo_root" "$log_root" "$mpi_ranks" "$omp_threads" <<'PYCHECK'
import csv
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
log_root = Path(sys.argv[2])
mpi_ranks = int(sys.argv[3])
omp_threads = int(sys.argv[4])
sys.path.insert(0, str(repo / 'tools'))
import amrex_reader  # noqa: E402

FAIL_MARKERS = (
    'Traceback',
    'RuntimeError',
    'Segmentation fault',
    'SIGSEGV',
    'Backtrace',
    'Unused ParmParse Variables',
)

def read_text(path):
    return Path(path).read_text(encoding='utf-8', errors='replace')

def grab(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return m.group(1)

def inspect_case(case_name, expected_min_level):
    case_dir = log_root / case_name
    run_dir = case_dir / 'run'
    run_log = read_text(case_dir / 'run.log')
    for marker in FAIL_MARKERS:
        if marker in run_log:
            raise SystemExit(f'FAIL: {marker} in {case_name} run log')
    if f'MPI initialized with {mpi_ranks} MPI processes' not in run_log:
        raise SystemExit(f'FAIL: {case_name} missing MPI rank initialization')
    if f'OMP initialized with {omp_threads} OMP threads' not in run_log:
        raise SystemExit(f'FAIL: {case_name} missing OMP thread initialization')
    validation = read_text(case_dir / 'hybrid_validation.log')
    for token in (f'mode=hybrid', f'ranks={mpi_ranks}', f'threads={omp_threads}', 'finalized=1'):
        if token not in validation:
            raise SystemExit(f'FAIL: {case_name} hybrid validation missing {token}')
    inputs = sorted(p for p in run_dir.iterdir() if p.name.startswith('input.codex_open_domain_plan_amr_'))
    if len(inputs) != 1:
        raise SystemExit(f'FAIL: expected one generated input for {case_name}, found {len(inputs)}')
    max_step = int(grab(r'amr\.max_step\s*=\s*([0-9]+)', read_text(inputs[0]), f'{case_name} amr.max_step'))
    plot = run_dir / f'plt{max_step:05d}'
    if not plot.is_dir():
        raise SystemExit(f'FAIL: missing final plotfile for {case_name}: {plot}')
    meta = amrex_reader._parse_header(str(plot / 'Header'))
    if meta['finest_level'] < expected_min_level:
        raise SystemExit(f'FAIL: {case_name} finest_level={meta["finest_level"]}, expected >= {expected_min_level}')
    levels = []
    for level in range(meta['finest_level'] + 1):
        cell_h = plot / f'Level_{level}' / 'Cell_H'
        fab_count = sum(1 for line in read_text(cell_h).splitlines() if line.strip().startswith('FabOnDisk:'))
        if fab_count <= 0:
            raise SystemExit(f'FAIL: no FabOnDisk entries for {case_name} level {level}')
        levels.append((level, fab_count))
    if levels[-1][1] < mpi_ranks:
        raise SystemExit(f'FAIL: {case_name} finest fab_count={levels[-1][1]} < mpi_ranks={mpi_ranks}')
    hazard = read_text(case_dir / 'hazard_timeseries.log')
    plotfiles = int(grab(r'plotfiles=([0-9]+)', hazard, f'{case_name} plotfiles'))
    final_cloud = float(grab(r'final_cloud_volume=([0-9.eE+-]+)', hazard, f'{case_name} final_cloud'))
    final_peak = float(grab(r'final_peak_X=([0-9.eE+-]+)', hazard, f'{case_name} final_peak'))
    if plotfiles < 3 or final_cloud <= 0.0 or final_peak <= 0.0:
        raise SystemExit(f'FAIL: weak hybrid hazard series for {case_name}')
    return {'case': case_name, 'max_step': max_step, 'finest_level': meta['finest_level'], 'fabs': levels, 'plotfiles': plotfiles, 'final_cloud_volume': final_cloud, 'final_peak_X': final_peak}

base = inspect_case('baseline', 0)
amr = inspect_case('amr', 1)
summary_path = log_root / 'plan_amr_compare_summary.csv'
with summary_path.open(newline='', encoding='utf-8') as fh:
    rows = list(csv.DictReader(fh))
if len(rows) < 2:
    raise SystemExit('FAIL: missing plan-AMR compare rows')
amr_row = rows[-1]
cloud_rel = float(amr_row['cloud_rel_diff'])
peak_rel = float(amr_row['peak_rel_diff'])
if cloud_rel > 0.45 or peak_rel > 0.50:
    raise SystemExit(f'FAIL: hybrid plan-AMR drift too large cloud={cloud_rel} peak={peak_rel}')
print('h2_leak_open_domain_plan_amr_hybrid_validation PASS ' +
      f'log_root={log_root} ranks={mpi_ranks} threads={omp_threads} ' +
      f'baseline_fabs={base["fabs"]} amr_fabs={amr["fabs"]} ' +
      f'cloud_rel_diff={cloud_rel:.8e} peak_rel_diff={peak_rel:.8e}')
PYCHECK

printf '[codex-smoke] PASS h2_leak open-domain plan-AMR hybrid validation log_root=%s ranks=%s threads=%s\n' "$log_root" "$mpi_ranks" "$omp_threads"
