#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/backward_facing_step"
exe="$case_dir/PeleLMeX2d.gnu.MPI.ex"
input="$case_dir/input.yaml"

case1_dir="${CODEX_BFS_208_DEFAULT_DIR:-/tmp/codex_bfs_refine_208x56_4rank_20260721}"
case2_dir="${CODEX_BFS_208_LOWCFL_DIR:-/tmp/codex_bfs_refine_208x56_serial_cfl005_20260721}"
summary="${CODEX_BFS_SENSITIVITY_SUMMARY:-/tmp/codex_bfs_kepsilon_sensitivity_summary_20260722.tsv}"

run_case() {
  local label="$1"
  local run_dir="$2"
  shift 2
  mkdir -p "$run_dir"
  find "$run_dir" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  (
    cd "$run_dir"
    set +e
    "$@" > run.log 2>&1
    printf '%s\n' "$?" > run.rc
    set -e
    local last_plot
    last_plot=$(find . -maxdepth 1 -type d -name 'plt_ref*' -printf '%f\n' | sort | tail -1 || true)
    if [[ -n "$last_plot" ]]; then
      set +e
      python3 "$repo_root/tools/validate_bfs.py" "$last_plot" > validate_bfs.log 2>&1
      printf '%s\n' "$?" > validate_bfs.rc
      set -e
    fi
  )
}

summarize_case() {
  local label="$1"
  local run_dir="$2"
  python3 - "$repo_root" "$label" "$run_dir" <<'PYSUM'
import contextlib
import io
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
label = sys.argv[2]
run_dir = Path(sys.argv[3])
sys.path.insert(0, str(repo / 'tools'))
import validate_bfs  # noqa: E402

def read(path):
    return Path(path).read_text(encoding='utf-8', errors='replace') if Path(path).is_file() else ''

run_log = read(run_dir / 'run.log')
run_rc = read(run_dir / 'run.rc').strip() or 'missing'
steps = [int(m.group(1)) for m in re.finditer(r'STEP \[(\d+)\]', run_log)]
times = [float(m.group(1)) for m in re.finditer(r'Time: ([0-9.eE+-]+), dt', run_log)]
plots = sorted(p for p in run_dir.glob('plt_ref*') if (p / 'Header').is_file())

status = 'INCOMPLETE'
if 'NaNs detected' in run_log:
    status = 'FAIL-NAN'
elif 'AMReX (26.05) finalized' in run_log or 'AMReX finalized' in run_log:
    status = 'COMPLETE-SCOUT'

xrh = ''
recirc = ''
validator_rc = ''
if plots:
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            result = validate_bfs.validate(str(plots[-1]))
        validator_rc = '0' if result.get('verdict') == 'PASS' else '1'
        if result.get('xr_h') == result.get('xr_h'):
            xrh = f"{float(result['xr_h']):.12g}"
        if result.get('recirc_length_h') == result.get('recirc_length_h'):
            recirc = f"{float(result['recirc_length_h']):.12g}"
    except Exception as exc:
        validator_rc = f'error:{type(exc).__name__}'

print('\t'.join([
    label,
    status,
    str(run_dir),
    run_rc,
    str(max(steps) if steps else ''),
    f"{times[-1]:.12g}" if times else '',
    plots[-1].name if plots else '',
    validator_rc,
    xrh,
    recirc,
]))
PYSUM
}

if [[ ! -x "$exe" ]]; then
  printf 'FAIL missing executable: %s\n' "$exe" >&2
  exit 2
fi

run_case \
  208x56_4rank_default_cfl \
  "$case1_dir" \
  mpirun -np 4 "$exe" "$input" \
  amr.n_cell="208 56" \
  amr.max_grid_size=64 \
  amr.max_step=5000 \
  amr.stop_time=0.5 \
  amr.plot_int=500 \
  amr.check_int=-1 \
  amr.plot_file=plt_ref \
  amr.check_file=chk_ref

run_case \
  208x56_serial_cfl005_500step \
  "$case2_dir" \
  "$exe" "$input" \
  amr.n_cell="208 56" \
  amr.max_grid_size=64 \
  amr.max_step=500 \
  amr.stop_time=0.05 \
  amr.cfl=0.05 \
  amr.dt_shrink=0.001 \
  amr.plot_int=250 \
  amr.check_int=-1 \
  amr.plot_file=plt_ref \
  amr.check_file=chk_ref

{
  printf 'label\tstatus\trun_dir\trun_rc\tmax_step_seen\tlast_time_seen\tlatest_plotfile\tvalidate_rc\txr_h\trecirc_h\n'
  summarize_case 208x56_4rank_default_cfl "$case1_dir"
  summarize_case 208x56_serial_cfl005_500step "$case2_dir"
} > "$summary"

cat "$summary"
if ! grep -q $'208x56_4rank_default_cfl\tFAIL-NAN' "$summary"; then
  printf 'FAIL expected 208x56_4rank_default_cfl to reproduce FAIL-NAN\n' >&2
  exit 1
fi
if ! grep -q $'208x56_serial_cfl005_500step\tCOMPLETE-SCOUT' "$summary"; then
  printf 'FAIL expected 208x56_serial_cfl005_500step to complete\n' >&2
  exit 1
fi
printf '[codex-scout] PASS bfs k-epsilon sensitivity summary=%s\n' "$summary"
