#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_root="${CODEX_H2_LEAK_PLAN_AMR_SWEEP_LOG_DIR:-/tmp/codex_h2_leak_open_domain_plan_amr_sweep_$(date -u +%Y%m%dT%H%M%SZ)}"
thresholds="${CODEX_H2_LEAK_PLAN_AMR_SWEEP_THRESHOLDS:-1.0e-2 4.0e-2}"
max_step="${CODEX_H2_LEAK_PLAN_AMR_SWEEP_MAX_STEP:-80}"
plot_int="${CODEX_H2_LEAK_PLAN_AMR_SWEEP_PLOT_INT:-20}"
min_plotfiles="${CODEX_H2_LEAK_PLAN_AMR_SWEEP_MIN_PLOTFILES:-5}"
min_mass_growth_ratio="${CODEX_H2_LEAK_PLAN_AMR_SWEEP_MIN_MASS_GROWTH_RATIO:-3.5}"
summary_csv="$log_root/plan_amr_sweep_summary.csv"
case_index="$log_root/plan_amr_sweep_cases.tsv"

mkdir -p "$log_root"
: > "$case_index"
printf '[codex-smoke] h2_leak plan-AMR sweep log_root=%s thresholds="%s" max_step=%s plot_int=%s min_plotfiles=%s min_mass_growth_ratio=%s\n' \
  "$log_root" "$thresholds" "$max_step" "$plot_int" "$min_plotfiles" "$min_mass_growth_ratio"

for grad in $thresholds; do
  slug=$(python3 - "$grad" <<'PYSLUG'
import re
import sys
print(re.sub(r'[^0-9A-Za-z]+', '_', sys.argv[1]).strip('_'))
PYSLUG
)
  case_root="$log_root/gradient_${slug}"
  mkdir -p "$case_root"
  printf '%s\t%s\n' "$grad" "$case_root" >> "$case_index"
  printf '[codex-smoke] running plan-AMR threshold=%s case_root=%s\n' "$grad" "$case_root"
  if ! CODEX_H2_LEAK_PLAN_AMR_COMPARE_LOG_DIR="$case_root" \
       CODEX_H2_LEAK_PLAN_AMR_SPECIES_GRADIENT="$grad" \
       CODEX_H2_LEAK_PLAN_AMR_MAX_STEP="$max_step" \
       CODEX_H2_LEAK_PLAN_AMR_PLOT_INT="$plot_int" \
       CODEX_H2_LEAK_PLAN_AMR_MIN_PLOTFILES="$min_plotfiles" \
       CODEX_H2_LEAK_PLAN_AMR_MIN_MASS_GROWTH_RATIO="$min_mass_growth_ratio" \
       RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
       JOBS="${JOBS:-4}" \
       "$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh" \
       2>&1 | tee "$case_root/sweep_stdout.log"; then
    printf '[codex-smoke] FAIL plan-AMR threshold=%s case_root=%s\n' "$grad" "$case_root" >&2
    exit 1
  fi
done

python3 - "$case_index" "$summary_csv" <<'PYSWEEP'
import csv
import os
import sys
from pathlib import Path

case_index = Path(sys.argv[1])
summary = Path(sys.argv[2])
max_cloud_rel = float(os.environ.get('CODEX_H2_LEAK_PLAN_AMR_SWEEP_MAX_CLOUD_REL_DIFF', '0.45'))
max_peak_rel = float(os.environ.get('CODEX_H2_LEAK_PLAN_AMR_SWEEP_MAX_PEAK_REL_DIFF', '0.50'))
max_centroid_abs = float(os.environ.get('CODEX_H2_LEAK_PLAN_AMR_SWEEP_MAX_CENTROID_ABS_DIFF', '0.08'))
max_downstream_abs = float(os.environ.get('CODEX_H2_LEAK_PLAN_AMR_SWEEP_MAX_DOWNSTREAM_ABS_DIFF', '0.15'))
max_mean_cells_ratio = float(os.environ.get('CODEX_H2_LEAK_PLAN_AMR_SWEEP_MAX_MEAN_NCELLS_RATIO', '10.0'))
max_advance_ratio = float(os.environ.get('CODEX_H2_LEAK_PLAN_AMR_SWEEP_MAX_ADVANCE_SECONDS_RATIO', '25.0'))
min_overhead_spread = float(os.environ.get('CODEX_H2_LEAK_PLAN_AMR_SWEEP_MIN_MEAN_NCELLS_RATIO_SPREAD', '0.02'))

entries = []
for raw in case_index.read_text(encoding='utf-8').splitlines():
    if not raw.strip():
        continue
    grad_text, case_root_text = raw.split('\t', 1)
    case_root = Path(case_root_text)
    compare_csv = case_root / 'plan_amr_compare_summary.csv'
    overhead_csv = case_root / 'amr_overhead_summary.csv'
    if not compare_csv.is_file():
        raise SystemExit(f'FAIL: missing compare summary for threshold {grad_text}: {compare_csv}')
    if not overhead_csv.is_file():
        raise SystemExit(f'FAIL: missing overhead summary for threshold {grad_text}: {overhead_csv}')
    compare_rows = list(csv.DictReader(compare_csv.open(newline='', encoding='utf-8')))
    overhead_rows = list(csv.DictReader(overhead_csv.open(newline='', encoding='utf-8')))
    amr = next((row for row in compare_rows if row.get('case') == 'amr'), None)
    overhead = next((row for row in overhead_rows if row.get('case') == 'amr'), None)
    if amr is None or overhead is None:
        raise SystemExit(f'FAIL: missing amr rows for threshold {grad_text}')
    entry = {
        'plan_species_gradient': grad_text,
        'case_root': str(case_root),
        'amr_finest_level': int(amr['finest_level']),
        'amr_finest_fabs': int(amr['finest_fab_count']),
        'regrid_count': int(amr['regrid_count']),
        'made_level1': int(amr['made_level1']),
        'mass_ratio': float(amr['mass_ratio']),
        'mass_ratioN': float(amr['mass_ratioN']),
        'cloud_rel_diff': float(amr['cloud_rel_diff']),
        'peak_rel_diff': float(amr['peak_rel_diff']),
        'centroid_abs_diff': float(amr['centroid_abs_diff']),
        'downstream_abs_diff': float(amr['downstream_abs_diff']),
        'cloud_volume': float(amr['cloud_volume']),
        'max_X': float(amr['max_X']),
        'active_planes': int(amr['active_planes']),
        'flammable_planes': int(amr['flammable_planes']),
        'mean_ncells_ratio': float(overhead['mean_ncells_ratio']),
        'max_ncells_ratio': float(overhead['max_ncells_ratio']),
        'advance_seconds_ratio': float(overhead['advance_seconds_ratio']),
        'final_plotfile_bytes_ratio': float(overhead['final_plotfile_bytes_ratio']),
    }
    if entry['amr_finest_level'] < 1 or entry['amr_finest_fabs'] <= 0 or entry['made_level1'] != 1:
        raise SystemExit(f'FAIL: threshold {grad_text} did not dynamically create populated Level 1: {entry}')
    if not (0.90 <= entry['mass_ratio'] <= 1.10 and 0.90 <= entry['mass_ratioN'] <= 1.10):
        raise SystemExit(f'FAIL: threshold {grad_text} mass ratio out of range: {entry}')
    if entry['cloud_rel_diff'] > max_cloud_rel:
        raise SystemExit(f'FAIL: threshold {grad_text} cloud drift too large: {entry}')
    if entry['peak_rel_diff'] > max_peak_rel:
        raise SystemExit(f'FAIL: threshold {grad_text} peak drift too large: {entry}')
    if entry['centroid_abs_diff'] > max_centroid_abs:
        raise SystemExit(f'FAIL: threshold {grad_text} centroid drift too large: {entry}')
    if entry['downstream_abs_diff'] > max_downstream_abs:
        raise SystemExit(f'FAIL: threshold {grad_text} downstream drift too large: {entry}')
    if entry['mean_ncells_ratio'] > max_mean_cells_ratio or entry['advance_seconds_ratio'] > max_advance_ratio:
        raise SystemExit(f'FAIL: threshold {grad_text} AMR overhead too large: {entry}')
    entries.append(entry)

if len(entries) < 2:
    raise SystemExit('FAIL: plan-AMR sweep requires at least two thresholds')
entries.sort(key=lambda row: float(row['plan_species_gradient']))
mean_ratios = [row['mean_ncells_ratio'] for row in entries]
spread = max(mean_ratios) - min(mean_ratios)
if spread < min_overhead_spread:
    raise SystemExit(
        f'FAIL: plan-AMR thresholds did not change mean cell overhead enough: spread={spread:.8e}')
for lo, hi in zip(entries, entries[1:]):
    if lo['mean_ncells_ratio'] + 0.05 < hi['mean_ncells_ratio']:
        raise SystemExit(
            'FAIL: looser species-gradient threshold increased mean cell overhead: '
            f'{lo["plan_species_gradient"]}->{lo["mean_ncells_ratio"]:.8e}, '
            f'{hi["plan_species_gradient"]}->{hi["mean_ncells_ratio"]:.8e}')

summary.parent.mkdir(parents=True, exist_ok=True)
fieldnames = list(entries[0].keys())
with summary.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(entries)
print('h2_leak_open_domain_plan_amr_sweep PASS ' +
      f'output={summary} thresholds={len(entries)} ' +
      f'mean_ncells_ratio_min={min(mean_ratios):.8e} ' +
      f'mean_ncells_ratio_max={max(mean_ratios):.8e} ' +
      f'mean_ncells_ratio_spread={spread:.8e} ' +
      'max_cloud_rel_diff=' + f'{max(row["cloud_rel_diff"] for row in entries):.8e} ' +
      'max_peak_rel_diff=' + f'{max(row["peak_rel_diff"] for row in entries):.8e}')
PYSWEEP

printf '[codex-smoke] PASS h2_leak open-domain plan-AMR sweep log_root=%s summary=%s\n' "$log_root" "$summary_csv"
