#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mpi_ranks="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS:-${MPI_RANKS:-4}}"
max_step="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP:-200}"
plot_int="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT:-20}"
min_plotfiles="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES:-11}"
min_mass_growth_ratio="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_MASS_GROWTH_RATIO:-3.0}"
max_mass_drop_ratio="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_MASS_DROP_RATIO:-5.0e-3}"
min_final_mass_ratio="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_FINAL_MASS_RATIO:-0.05}"
max_final_mass_ratio="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_FINAL_MASS_RATIO:-1.20}"
min_plane_mass_fraction="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLANE_MASS_FRACTION:-0.02}"
log_root="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LOG_DIR:-/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ "$log_root" != /* ]]; then
  log_root="$repo_root/$log_root"
fi
reuse_existing="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_REUSE_EXISTING:-FALSE}"
summary_csv="$log_root/reduced_long_summary.csv"
report_json="$log_root/engineering_case_report.json"
report_md="$log_root/engineering_case_report.md"

mkdir -p "$log_root"

if [[ "$reuse_existing" != TRUE || ! -f "$log_root/plan_amr_compare_summary.csv" ]]; then
  CODEX_H2_LEAK_PLAN_AMR_MPI_RANKS="$mpi_ranks" \
  CODEX_H2_LEAK_PLAN_AMR_MPI_LOG_DIR="$log_root" \
  CODEX_H2_LEAK_PLAN_AMR_MPI_REUSE_EXISTING="$reuse_existing" \
  CODEX_H2_LEAK_PLAN_AMR_MAX_STEP="$max_step" \
  CODEX_H2_LEAK_PLAN_AMR_PLOT_INT="$plot_int" \
  CODEX_H2_LEAK_PLAN_AMR_MIN_PLOTFILES="$min_plotfiles" \
  CODEX_H2_LEAK_PLAN_AMR_MIN_MASS_GROWTH_RATIO="$min_mass_growth_ratio" \
  CODEX_H2_LEAK_PLAN_AMR_MAX_MASS_DROP_RATIO="$max_mass_drop_ratio" \
  CODEX_H2_LEAK_PLAN_AMR_MIN_FINAL_MASS_RATIO="$min_final_mass_ratio" \
  CODEX_H2_LEAK_PLAN_AMR_MAX_FINAL_MASS_RATIO="$max_final_mass_ratio" \
  CODEX_H2_LEAK_PLAN_AMR_MIN_PLANE_MASS_FRACTION="$min_plane_mass_fraction" \
  CODEX_H2_LEAK_PLAN_AMR_BASE_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_BASE_MAX_GRID_SIZE:-8}" \
  CODEX_H2_LEAK_PLAN_AMR_LEVEL1_MAX_GRID_SIZE="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LEVEL1_MAX_GRID_SIZE:-8}" \
  RUN_TIMEOUT="${RUN_TIMEOUT:-1800}" \
  JOBS="${JOBS:-4}" \
    "$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi.sh"
else
  printf '[codex-smoke] reusing existing reduced-long plan-AMR MPI root=%s\n' "$log_root"
fi

python3 - "$repo_root" "$log_root" "$summary_csv" "$mpi_ranks" "$max_step" "$plot_int" "$min_plotfiles" <<'PYCHECK'
import csv
import math
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
log_root = Path(sys.argv[2])
summary_csv = Path(sys.argv[3])
mpi_ranks = int(sys.argv[4])
max_step = int(sys.argv[5])
plot_int = int(sys.argv[6])
min_plotfiles = int(sys.argv[7])
sys.path.insert(0, str(repo / 'tools'))
import amrex_reader  # noqa: E402

FAIL_MARKERS = (
    'FAIL',
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
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f'FAIL: missing {label}')
    return match.group(1)


def finite_float(value, label):
    number = float(value)
    if not math.isfinite(number):
        raise SystemExit(f'FAIL: nonfinite {label}={value!r}')
    return number


def scan_logs():
    hits = []
    logs = []
    for case_name in ('baseline', 'amr'):
        case_dir = log_root / case_name
        if case_dir.is_dir():
            logs.extend(sorted(case_dir.rglob('*.log')))
    for log in logs:
        text = read_text(log)
        rel = log.relative_to(log_root)
        for marker in FAIL_MARKERS:
            if marker in text:
                hits.append(f'{rel}:{marker}')
        if re.search(r'(?<![A-Za-z0-9_])(?:nan|inf)(?![A-Za-z0-9_])', text, re.IGNORECASE):
            hits.append(f'{rel}:nonfinite-token')
    if hits:
        raise SystemExit('FAIL: failure markers in logs: ' + '; '.join(hits[:20]))
    return len(logs)


def inspect_plot(case_name):
    run_dir = log_root / case_name / 'run'
    plot = run_dir / f'plt{max_step:05d}'
    if not plot.is_dir():
        raise SystemExit(f'FAIL: missing final plotfile {plot}')
    meta = amrex_reader._parse_header(str(plot / 'Header'))
    levels = []
    for level in range(meta['finest_level'] + 1):
        cell_h = plot / f'Level_{level}' / 'Cell_H'
        if not cell_h.is_file():
            raise SystemExit(f'FAIL: missing {case_name} Level_{level}/Cell_H')
        fabs = sum(1 for line in read_text(cell_h).splitlines() if line.strip().startswith('FabOnDisk:'))
        if fabs <= 0:
            raise SystemExit(f'FAIL: empty FAB list for {case_name} level {level}')
        levels.append((level, fabs))
    if case_name == 'baseline' and meta['finest_level'] != 0:
        raise SystemExit(f'FAIL: baseline finest_level={meta["finest_level"]}, expected 0')
    if case_name == 'amr' and meta['finest_level'] < 1:
        raise SystemExit(f'FAIL: AMR finest_level={meta["finest_level"]}, expected >=1')
    if levels[-1][1] < mpi_ranks:
        raise SystemExit(f'FAIL: {case_name} final finest FABs {levels[-1][1]} < mpi ranks {mpi_ranks}')
    return meta['finest_level'], levels


def inspect_timeseries(case_name):
    path = log_root / case_name / 'hazard_timeseries.csv'
    if not path.is_file():
        raise SystemExit(f'FAIL: missing {path}')
    with path.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < min_plotfiles:
        raise SystemExit(f'FAIL: {case_name} plotfiles={len(rows)} < {min_plotfiles}')
    if int(rows[-1]['step']) != max_step:
        raise SystemExit(f'FAIL: {case_name} final step {rows[-1]["step"]} != {max_step}')
    previous_step = -1
    previous_time = -1.0
    max_cloud = 0.0
    max_peak = 0.0
    max_flammable_planes = 0
    masses = []
    for idx, row in enumerate(rows):
        step = int(row['step'])
        time = finite_float(row['time'], f'{case_name} time row {idx}')
        if step <= previous_step or time < previous_time:
            raise SystemExit(f'FAIL: nonmonotone step/time in {case_name} row {idx}')
        previous_step = step
        previous_time = time
        for key in ('total_species_mass', 'total_cloud_species_mass', 'total_cloud_volume', 'peak_X', 'peak_Y', 'max_plane_cloud_volume'):
            value = finite_float(row[key], f'{case_name} {key} row {idx}')
            if value < -1.0e-14:
                raise SystemExit(f'FAIL: negative {case_name} {key} row {idx}: {value}')
        mass = finite_float(row['total_species_mass'], f'{case_name} total_species_mass row {idx}')
        masses.append(mass)
        cloud = finite_float(row['total_cloud_volume'], f'{case_name} total_cloud_volume row {idx}')
        peak = finite_float(row['peak_X'], f'{case_name} peak_X row {idx}')
        max_cloud = max(max_cloud, cloud)
        max_peak = max(max_peak, peak)
        max_flammable_planes = max(max_flammable_planes, int(row['flammable_planes']))
    final = rows[-1]
    final_mass = finite_float(final['total_species_mass'], f'{case_name} final mass')
    final_cloud = finite_float(final['total_cloud_volume'], f'{case_name} final cloud')
    final_peak = finite_float(final['peak_X'], f'{case_name} final peak_X')
    final_flammable_planes = int(final['flammable_planes'])
    if final_mass <= 0.0 or final_mass < 0.75 * max(masses):
        raise SystemExit(f'FAIL: weak final retained mass in {case_name}: final={final_mass:.8e} max={max(masses):.8e}')
    if max_cloud <= 0.0 or max_peak <= 0.0 or max_flammable_planes < 1:
        raise SystemExit(f'FAIL: missing sustained hazard in {case_name}: max_cloud={max_cloud:.8e} max_peak={max_peak:.8e} max_flammable_planes={max_flammable_planes}')
    if final_cloud <= 0.0 or final_peak <= 0.0 or final_flammable_planes < 1:
        raise SystemExit(f'FAIL: weak final hazard in {case_name}: final_cloud={final_cloud:.8e} final_peak={final_peak:.8e} final_flammable_planes={final_flammable_planes}')
    return {
        'case': case_name,
        'plotfiles': len(rows),
        'final_step': int(final['step']),
        'final_time': finite_float(final['time'], f'{case_name} final time'),
        'final_mass': final_mass,
        'final_cloud_volume': final_cloud,
        'final_peak_X': final_peak,
        'final_flammable_planes': final_flammable_planes,
        'max_cloud_volume': max_cloud,
        'max_peak_X': max_peak,
        'max_flammable_planes': max_flammable_planes,
    }


def inspect_mpi(case_name):
    path = log_root / case_name / 'mpi_validation.log'
    text = read_text(path)
    ranks = int(grab(r'ranks=([0-9]+)', text, f'{case_name} mpi ranks'))
    final_time = finite_float(grab(r'final_time=([0-9.eE+-]+)', text, f'{case_name} final_time'), f'{case_name} final_time')
    finalized = int(grab(r'finalized=([0-9]+)', text, f'{case_name} finalized'))
    if ranks != mpi_ranks or finalized != 1:
        raise SystemExit(f'FAIL: bad MPI validation for {case_name}: ranks={ranks} finalized={finalized}')
    expected_time = max_step * 1.0e-3
    if abs(final_time - expected_time) > max(1.0e-12, expected_time * 1.0e-10):
        raise SystemExit(f'FAIL: {case_name} final_time={final_time:.12e}, expected {expected_time:.12e}')
    return final_time


def read_compare_metrics():
    path = log_root / 'plan_amr_compare_summary.csv'
    with path.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < 2:
        raise SystemExit('FAIL: plan_amr_compare_summary.csv has too few rows')
    amr = rows[-1]
    metrics = {key: finite_float(amr[key], key) for key in ('cloud_rel_diff', 'peak_rel_diff', 'centroid_abs_diff', 'downstream_abs_diff')}
    if metrics['cloud_rel_diff'] > 0.50 or metrics['peak_rel_diff'] > 0.55:
        raise SystemExit(f'FAIL: long plan-AMR hazard drift too large: {metrics}')
    return metrics


log_count = scan_logs()
base_level, base_fabs = inspect_plot('baseline')
amr_level, amr_fabs = inspect_plot('amr')
base_ts = inspect_timeseries('baseline')
amr_ts = inspect_timeseries('amr')
base_time = inspect_mpi('baseline')
amr_time = inspect_mpi('amr')
metrics = read_compare_metrics()

summary_csv.parent.mkdir(parents=True, exist_ok=True)
fieldnames = [
    'case', 'ranks', 'max_step', 'plot_int', 'plotfiles', 'final_step', 'final_time',
    'finest_level', 'fabs', 'final_mass', 'final_cloud_volume', 'final_peak_X',
    'final_flammable_planes', 'max_cloud_volume', 'max_peak_X', 'max_flammable_planes',
    'cloud_rel_diff', 'peak_rel_diff', 'centroid_abs_diff', 'downstream_abs_diff', 'log_files',
]
with summary_csv.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    for ts, level, fabs, final_time in ((base_ts, base_level, base_fabs, base_time), (amr_ts, amr_level, amr_fabs, amr_time)):
        row = {
            **ts,
            'ranks': mpi_ranks,
            'max_step': max_step,
            'plot_int': plot_int,
            'final_time': f'{final_time:.12e}',
            'finest_level': level,
            'fabs': repr(fabs),
            'cloud_rel_diff': '',
            'peak_rel_diff': '',
            'centroid_abs_diff': '',
            'downstream_abs_diff': '',
            'log_files': log_count,
        }
        if ts['case'] == 'amr':
            row.update({key: f'{value:.8e}' for key, value in metrics.items()})
        writer.writerow(row)

print('h2_leak_open_domain_plan_amr_mpi_reduced_long PASS ' +
      f'root={log_root} ranks={mpi_ranks} max_step={max_step} plotfiles={base_ts["plotfiles"]}/{amr_ts["plotfiles"]} ' +
      f'baseline_final_cloud={base_ts["final_cloud_volume"]:.8e} amr_final_cloud={amr_ts["final_cloud_volume"]:.8e} ' +
      f'amr_finest_level={amr_level} amr_fabs={amr_fabs} cloud_rel_diff={metrics["cloud_rel_diff"]:.8e} ' +
      f'peak_rel_diff={metrics["peak_rel_diff"]:.8e} log_files={log_count}')
PYCHECK

python3 "$repo_root/tools/write_engineering_h2_case_report.py" \
  --case h2-open-domain-plan-amr-mpi-reduced-long \
  --root "$log_root" \
  --output-json "$report_json" \
  --output-md "$report_md"

printf '[codex-smoke] PASS h2_leak open-domain plan-AMR MPI reduced-long root=%s summary=%s report_json=%s report_md=%s\n' "$log_root" "$summary_csv" "$report_json" "$report_md"
