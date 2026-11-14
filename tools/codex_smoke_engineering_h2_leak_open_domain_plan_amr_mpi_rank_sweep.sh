#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_root="${CODEX_H2_LEAK_PLAN_AMR_MPI_RANK_SWEEP_LOG_DIR:-/tmp/codex_h2_leak_open_domain_plan_amr_mpi_rank_sweep_$(date -u +%Y%m%dT%H%M%SZ)}"
ranks_list="${CODEX_H2_LEAK_PLAN_AMR_MPI_RANK_SWEEP_RANKS:-2 4}"
summary_csv="$log_root/rank_sweep_summary.csv"

mkdir -p "$log_root"
: > "$log_root/rank_sweep_cases.tsv"

reuse_existing="${CODEX_H2_LEAK_PLAN_AMR_MPI_RANK_SWEEP_REUSE_EXISTING:-FALSE}"

for ranks in $ranks_list; do
  case_dir="$log_root/ranks_${ranks}"
  if [[ "$reuse_existing" == "TRUE" && -f "$case_dir/plan_amr_compare_summary.csv" && -f "$case_dir/amr_overhead_summary.csv" ]]; then
    printf '[codex-smoke] reusing h2_leak plan-AMR MPI rank case ranks=%s log_dir=%s\n' "$ranks" "$case_dir"
    printf 'ranks\t%s\t%s\n' "$ranks" "$case_dir" >> "$log_root/rank_sweep_cases.tsv"
    continue
  fi
  printf '[codex-smoke] running h2_leak plan-AMR MPI rank case ranks=%s log_dir=%s\n' "$ranks" "$case_dir"
  CODEX_H2_LEAK_PLAN_AMR_MPI_LOG_DIR="$case_dir" \
  CODEX_H2_LEAK_PLAN_AMR_MPI_RANKS="$ranks" \
  CODEX_H2_LEAK_PLAN_AMR_MAX_STEP="${CODEX_H2_LEAK_PLAN_AMR_RANK_SWEEP_MAX_STEP:-80}" \
  CODEX_H2_LEAK_PLAN_AMR_PLOT_INT="${CODEX_H2_LEAK_PLAN_AMR_RANK_SWEEP_PLOT_INT:-20}" \
  CODEX_H2_LEAK_PLAN_AMR_MIN_PLOTFILES="${CODEX_H2_LEAK_PLAN_AMR_RANK_SWEEP_MIN_PLOTFILES:-5}" \
  CODEX_H2_LEAK_PLAN_AMR_BASE_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_RANK_SWEEP_BASE_MAX_GRID_SIZE:-8}" \
  CODEX_H2_LEAK_PLAN_AMR_LEVEL1_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_RANK_SWEEP_LEVEL1_MAX_GRID_SIZE:-8}" \
  RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
  JOBS="${JOBS:-4}" \
    "$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi.sh"
  printf 'ranks\t%s\t%s\n' "$ranks" "$case_dir" >> "$log_root/rank_sweep_cases.tsv"
done

python3 - "$log_root" "$summary_csv" <<'PYCHECK'
import ast
import csv
import re
import sys
from pathlib import Path

log_root = Path(sys.argv[1])
summary_csv = Path(sys.argv[2])

patterns = ('FAIL', 'ERROR', 'Traceback', 'Abort', 'Backtrace', 'Unused ParmParse Variables')
hits = []
for p in sorted(log_root.rglob('*.log')):
    text = p.read_text(encoding='utf-8', errors='replace')
    for i, line in enumerate(text.splitlines(), 1):
        if any(marker in line for marker in patterns):
            hits.append((p, i, line[:240]))
if hits:
    for p, i, line in hits[:40]:
        print(f'{p}:{i}: {line}', file=sys.stderr)
    raise SystemExit(f'FAIL: rank sweep found {len(hits)} failure markers')


def read_single_row(path, case):
    with Path(path).open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    selected = [row for row in rows if row.get('case') == case]
    if len(selected) != 1:
        raise SystemExit(f'FAIL: expected one {case} row in {path}, got {len(selected)}')
    return selected[0]


def parse_validation(path):
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    m = re.search(r'h2_leak_open_domain_plan_amr_mpi_validation PASS .*?ranks=([0-9]+).*?baseline_fabs=(\[[^\]]+\]).*?amr_finest_level=([0-9]+).*?amr_fabs=(\[[^\n]+\])', text)
    if not m:
        raise SystemExit(f'FAIL: missing AMR MPI validation PASS line in {path}')
    return {
        'ranks': int(m.group(1)),
        'baseline_fabs': ast.literal_eval(m.group(2)),
        'amr_finest_level': int(m.group(3)),
        'amr_fabs': ast.literal_eval(m.group(4)),
    }


def rel_diff(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1.0e-30)

cases = []
for case_dir in sorted(log_root.glob('ranks_*')):
    if not case_dir.is_dir():
        continue
    ranks = int(case_dir.name.split('_', 1)[1])
    amr_row = read_single_row(case_dir / 'plan_amr_compare_summary.csv', 'amr')
    base_row = read_single_row(case_dir / 'plan_amr_compare_summary.csv', 'baseline')
    overhead = read_single_row(case_dir / 'amr_overhead_summary.csv', 'amr')
    validation_log = case_dir / 'rank_validation.log'
    # The wrapper prints the validation line to stdout, not a file. Reconstruct from plotfile checks.
    mpi_logs = [case_dir / 'baseline' / 'mpi_validation.log', case_dir / 'amr' / 'mpi_validation.log']
    for mpi_log in mpi_logs:
        text = mpi_log.read_text(encoding='utf-8', errors='replace')
        if f'mode=mpi ranks={ranks}' not in text or 'finalized=1' not in text:
            raise SystemExit(f'FAIL: weak MPI validation evidence in {mpi_log}')
    # Extract FAB counts directly from the PASS line saved in the top-level run output if present,
    # otherwise inspect the deterministic CSV/log evidence below.
    cases.append({
        'ranks': ranks,
        'baseline_cloud_volume': float(base_row['cloud_volume']),
        'amr_cloud_volume': float(amr_row['cloud_volume']),
        'amr_max_X': float(amr_row['max_X']),
        'amr_centroid_shift': float(amr_row['centroid_shift']),
        'amr_downstream_fraction': float(amr_row['downstream_fraction']),
        'amr_finest_level': int(amr_row['finest_level']),
        'amr_finest_fab_count': int(amr_row['finest_fab_count']),
        'amr_regrid_count': int(amr_row['regrid_count']),
        'mean_ncells_ratio': float(overhead['mean_ncells_ratio']),
        'advance_seconds_ratio': float(overhead['advance_seconds_ratio']),
        'final_plotfile_bytes_ratio': float(overhead['final_plotfile_bytes_ratio']),
        'log_dir': str(case_dir),
    })

if len(cases) < 2:
    raise SystemExit(f'FAIL: expected at least two rank cases, got {len(cases)}')
cases.sort(key=lambda row: row['ranks'])
for row in cases:
    if row['amr_finest_level'] < 1:
        raise SystemExit(f'FAIL: ranks={row["ranks"]} did not produce AMR level 1')
    if row['amr_finest_fab_count'] < row['ranks']:
        raise SystemExit(f'FAIL: ranks={row["ranks"]} AMR finest fabs {row["amr_finest_fab_count"]} < ranks')

ref = cases[0]
for row in cases[1:]:
    cloud_rel = rel_diff(ref['amr_cloud_volume'], row['amr_cloud_volume'])
    peak_rel = rel_diff(ref['amr_max_X'], row['amr_max_X'])
    centroid_abs = abs(ref['amr_centroid_shift'] - row['amr_centroid_shift'])
    downstream_abs = abs(ref['amr_downstream_fraction'] - row['amr_downstream_fraction'])
    row['cloud_rel_vs_ref'] = cloud_rel
    row['peak_rel_vs_ref'] = peak_rel
    row['centroid_abs_vs_ref'] = centroid_abs
    row['downstream_abs_vs_ref'] = downstream_abs
    if cloud_rel > 1.0e-10 or peak_rel > 1.0e-10 or centroid_abs > 1.0e-10 or downstream_abs > 1.0e-10:
        raise SystemExit('FAIL: rank sweep changed AMR hazard metrics beyond roundoff: ' + repr(row))
ref.update({
    'cloud_rel_vs_ref': 0.0,
    'peak_rel_vs_ref': 0.0,
    'centroid_abs_vs_ref': 0.0,
    'downstream_abs_vs_ref': 0.0,
})

fieldnames = [
    'ranks', 'log_dir', 'baseline_cloud_volume', 'amr_finest_level', 'amr_finest_fab_count', 'amr_regrid_count',
    'amr_cloud_volume', 'amr_max_X', 'amr_centroid_shift', 'amr_downstream_fraction',
    'mean_ncells_ratio', 'advance_seconds_ratio', 'final_plotfile_bytes_ratio',
    'cloud_rel_vs_ref', 'peak_rel_vs_ref', 'centroid_abs_vs_ref', 'downstream_abs_vs_ref',
]
with summary_csv.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    for row in cases:
        writer.writerow(row)

print('h2_leak_open_domain_plan_amr_mpi_rank_sweep PASS ' +
      f'cases={len(cases)} ranks={",".join(str(c["ranks"]) for c in cases)} ' +
      f'summary={summary_csv} log_files={len(list(log_root.rglob("*.log")))} ' +
      f'max_cloud_rel_vs_ref={max(c["cloud_rel_vs_ref"] for c in cases):.8e} ' +
      f'max_peak_rel_vs_ref={max(c["peak_rel_vs_ref"] for c in cases):.8e}')
PYCHECK

printf '[codex-smoke] PASS h2_leak open-domain plan-AMR MPI rank sweep log_root=%s summary=%s\n' "$log_root" "$summary_csv"
