#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mpi_ranks="${CODEX_H2_LEAK_PLAN_AMR_MPI_RANKS:-${MPI_RANKS:-2}}"
log_root="${CODEX_H2_LEAK_PLAN_AMR_MPI_LOG_DIR:-/tmp/codex_h2_leak_open_domain_plan_amr_mpi_$(date -u +%Y%m%dT%H%M%SZ)}"

export MPI_RANKS="$mpi_ranks"
export CODEX_H2_LEAK_HISTORY_MPI_RANKS="$mpi_ranks"
export CODEX_H2_LEAK_HISTORY_USE_MPI=TRUE
export CODEX_H2_LEAK_HISTORY_EBASE="${CODEX_H2_LEAK_HISTORY_EBASE:-codex_h2_leak_plan_amr_mpi}"
export CODEX_H2_LEAK_PLAN_AMR_COMPARE_LOG_DIR="$log_root"
export CODEX_H2_LEAK_PLAN_AMR_COMPARE_REUSE_EXISTING="${CODEX_H2_LEAK_PLAN_AMR_MPI_REUSE_EXISTING:-FALSE}"
export CODEX_H2_LEAK_PLAN_AMR_LEVEL1_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_LEVEL1_MAX_GRID_SIZE:-16}"
export CODEX_H2_LEAK_PLAN_AMR_BASE_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_BASE_MAX_GRID_SIZE:-32}"

"$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh"

for case_name in baseline amr; do
  run_log="$log_root/$case_name/run.log"
  python3 "$repo_root/tools/validate_parallel_smoke_log.py"     --log "$run_log"     --mode mpi     --solver pelelmex     --expected-ranks "$mpi_ranks"     --require-final-time | tee "$log_root/$case_name/mpi_validation.log"
done

python3 - "$repo_root" "$log_root" "$mpi_ranks" <<'PYCHECK'
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
log_root = Path(sys.argv[2])
mpi_ranks = int(sys.argv[3])
sys.path.insert(0, str(repo / 'tools'))
import amrex_reader  # noqa: E402


def grab(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return m.group(1)


def read_text(path):
    return Path(path).read_text(encoding='utf-8', errors='replace')


def inspect_case(case_name, expected_min_level):
    case_dir = log_root / case_name
    run_dir = case_dir / 'run'
    inputs = sorted(p for p in run_dir.iterdir() if p.name.startswith('input.codex_open_domain_plan_amr_'))
    if len(inputs) != 1:
        raise SystemExit(f'FAIL: expected one generated input for {case_name}, found {len(inputs)} in {run_dir}')
    input_text = read_text(inputs[0])
    max_step = int(grab(r'amr\.max_step\s*=\s*([0-9]+)', input_text, f'{case_name} amr.max_step'))
    plot = run_dir / f'plt{max_step:05d}'
    if not plot.is_dir():
        raise SystemExit(f'FAIL: missing final plotfile for {case_name}: {plot}')
    meta = amrex_reader._parse_header(str(plot / 'Header'))
    if meta['finest_level'] < expected_min_level:
        raise SystemExit(f'FAIL: {case_name} finest_level={meta["finest_level"]}, expected >= {expected_min_level}')
    levels = []
    for level in range(meta['finest_level'] + 1):
        cell_h = plot / f'Level_{level}' / 'Cell_H'
        if not cell_h.is_file():
            raise SystemExit(f'FAIL: missing Cell_H for {case_name} level {level}: {cell_h}')
        fab_count = sum(1 for line in read_text(cell_h).splitlines() if line.strip().startswith('FabOnDisk:'))
        if fab_count <= 0:
            raise SystemExit(f'FAIL: no FabOnDisk entries for {case_name} level {level}: {cell_h}')
        levels.append((level, fab_count))
    if case_name == 'baseline' and levels[0][1] < mpi_ranks:
        raise SystemExit(f'FAIL: baseline Level_0 fab_count={levels[0][1]} < mpi_ranks={mpi_ranks}')
    if case_name == 'amr':
        finest_fabs = levels[-1][1]
        if finest_fabs < mpi_ranks:
            raise SystemExit(f'FAIL: AMR finest level fab_count={finest_fabs} < mpi_ranks={mpi_ranks}')
        run_log = read_text(case_dir / 'run.log')
        for marker in ('Making new level 1', 'Regridding'):
            if marker not in run_log:
                raise SystemExit(f'FAIL: missing {marker!r} in AMR MPI run log')
    return meta['finest_level'], levels

base_level, base_levels = inspect_case('baseline', 0)
amr_level, amr_levels = inspect_case('amr', 1)
summary = read_text(log_root / 'plan_amr_compare_summary.csv')
if 'cloud_rel_diff' not in summary or 'peak_rel_diff' not in summary:
    raise SystemExit('FAIL: missing plan-AMR comparison metrics in summary CSV')
print('h2_leak_open_domain_plan_amr_mpi_validation PASS ' +
      f'log_root={log_root} ranks={mpi_ranks} baseline_finest_level={base_level} ' +
      f'baseline_fabs={base_levels} amr_finest_level={amr_level} amr_fabs={amr_levels}')
PYCHECK

printf '[codex-smoke] PASS h2_leak open-domain plan-AMR MPI validation log_root=%s ranks=%s
' "$log_root" "$mpi_ranks"
