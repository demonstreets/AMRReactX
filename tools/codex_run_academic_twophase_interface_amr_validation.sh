#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/rayleigh_taylor"
exe="$case_dir/codex_rayleigh_taylor2d.gnu.ex"
root="${CODEX_TWOPHASE_INTERFACE_AMR_ROOT:-$repo_root/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728}"
run_root="$root/runs"
manifest="$root/case_manifest.json"

jobs="${JOBS:-4}"
run_timeout="${RUN_TIMEOUT:-1200}"
stop_time="${CODEX_TWOPHASE_INTERFACE_AMR_STOP_TIME:-1.6e-2}"
max_step="${CODEX_TWOPHASE_INTERFACE_AMR_MAX_STEP:-3500}"
base_nx="${CODEX_TWOPHASE_INTERFACE_AMR_BASE_NX:-64}"
base_ny=$((2 * base_nx))
fine_nx=$((2 * base_nx))
fine_ny=$((2 * base_ny))
p0="${CODEX_TWOPHASE_INTERFACE_AMR_P0:-50.0}"
cfl="${CODEX_TWOPHASE_INTERFACE_AMR_CFL:-0.005}"
error_buf="${CODEX_TWOPHASE_INTERFACE_AMR_ERROR_BUF:-4}"

rm -rf "$run_root"
mkdir -p "$run_root"

echo "[academic-twophase-interface-amr] build case=$case_dir jobs=$jobs"
pushd "$case_dir" >/dev/null
make -j "$jobs" DIM=2 EBASE=codex_rayleigh_taylor USE_MPI=FALSE USE_OMP=FALSE >"$run_root/build.log" 2>&1
popd >/dev/null
test -x "$exe"

make_input() {
  local src="$1"
  local dst="$2"
  local nx="$3"
  local ny="$4"
  local max_level="$5"
  python3 - "$src" "$dst" "$nx" "$ny" "$stop_time" "$max_step" "$p0" "$cfl" "$max_level" "$error_buf" <<'PY'
import re
import sys
from pathlib import Path

src, dst, nx, ny, stop_time, max_step, p0, cfl, max_level, error_buf = sys.argv[1:]
text = Path(src).read_text()
replacements = {
    r'^max_step\s*=.*$': f'max_step = {max_step}',
    r'^stop_time\s*=.*$': f'stop_time = {stop_time}',
    r'^amr\.n_cell\s*=.*$': f'amr.n_cell = {nx} {ny} 1',
    r'^amr\.plot_int\s*=.*$': f'amr.plot_int = {max_step}',
    r'^amr\.max_level\s*=.*$': f'amr.max_level = {max_level}',
    r'^pelec\.cfl\s*=.*$': f'pelec.cfl = {cfl}',
    r'^pelec\.init_shrink\s*=.*$': 'pelec.init_shrink = 0.01',
    r'^prob\.p0\s*=.*$': f'prob.p0 = {p0}',
    r'^pelec\.sum_interval\s*=.*$': 'pelec.sum_interval = 1000',
    r'^tagging\.dengrad\s*=.*$': 'tagging.dengrad = 0.005',
}
for pattern, value in replacements.items():
    text, count = re.subn(pattern, value, text, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f'FAIL: expected one replacement for {pattern}, got {count}')
if max_level != '0' and 'amr.regrid_int' not in text:
    text = text.replace('amr.max_grid_size = 64\n', 'amr.max_grid_size = 64\namr.regrid_int = 1000\n')
if max_level != '0':
    value = f'amr.n_error_buf = {error_buf} {error_buf}'
    if re.search(r'^amr\.n_error_buf\s*=.*$', text, flags=re.MULTILINE):
        text = re.sub(r'^amr\.n_error_buf\s*=.*$', value, text, flags=re.MULTILINE)
    else:
        text = text.replace('amr.blocking_factor = 16\n', f'amr.blocking_factor = 16\n{value}\n')
Path(dst).write_text(text)
PY
}

run_case() {
  local name="$1"
  local role="$2"
  local nx="$3"
  local ny="$4"
  local max_level="$5"
  local run_dir="$run_root/$name"
  local input_name="input.$name"
  mkdir -p "$run_dir"
  make_input "$case_dir/inputs" "$run_dir/$input_name" "$nx" "$ny" "$max_level"
  echo "[academic-twophase-interface-amr] running $name role=$role n_cell=${nx}x${ny} max_level=$max_level"
  pushd "$run_dir" >/dev/null
  timeout "$run_timeout" "$exe" "$input_name" >"$run_root/$name.log" 2>&1
  popd >/dev/null
  grep -q "AMReX (.*) finalized" "$run_root/$name.log"
  test -d "$run_dir/plt00000"
  final_plot="$(find "$run_dir" -maxdepth 1 -type d -name 'plt[0-9][0-9][0-9][0-9][0-9]' | sort | tail -1)"
  test -n "$final_plot"
  python3 "$repo_root/tools/validate_rayleigh_taylor_plotfile.py" \
    --initial "$run_dir/plt00000" --final "$final_plot" --alpha-tol 2.0e-6 >"$run_root/conservation_$name.log"
  python3 "$repo_root/tools/validate_rayleigh_taylor_growth.py" \
    --initial "$run_dir/plt00000" --final "$final_plot" --alpha-tol 2.0e-6 >"$run_root/growth_$name.log"
  if [[ "$max_level" != "0" ]]; then
    python3 "$repo_root/tools/validate_academic_twophase_interface_amr.py" \
      --initial "$run_dir/plt00000" --final "$final_plot" --alpha-tol 2.0e-6 >"$run_root/interface_amr_$name.log"
    cat "$run_root/interface_amr_$name.log"
  fi
  cat "$run_root/growth_$name.log"
}

run_case "amr_${base_nx}x${base_ny}_l1" "amr_interface" "$base_nx" "$base_ny" 1
run_case "uniform_fine_${fine_nx}x${fine_ny}" "uniform_fine_reference" "$fine_nx" "$fine_ny" 0

python3 - "$manifest" "$run_root" "$base_nx" "$base_ny" "$fine_nx" "$fine_ny" <<'PY'
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
run_root = Path(sys.argv[2])
base_nx, base_ny, fine_nx, fine_ny = [int(v) for v in sys.argv[3:]]
cases = []
for name, role, nx, ny, amr_enabled in [
    (f'amr_{base_nx}x{base_ny}_l1', 'amr_interface', base_nx, base_ny, True),
    (f'uniform_fine_{fine_nx}x{fine_ny}', 'uniform_fine_reference', fine_nx, fine_ny, False),
]:
    run_dir = run_root / name
    plotfiles = sorted(p.name for p in run_dir.glob('plt[0-9][0-9][0-9][0-9][0-9]') if p.name != 'plt00000')
    if not plotfiles:
        raise SystemExit(f'{run_dir} has no final plotfile')
    item = {
        'name': name,
        'role': role,
        'amr_enabled': amr_enabled,
        'n_cell': [nx, ny, 1],
        'run_dir': str(run_dir),
        'input_file': str(run_dir / f'input.{name}'),
        'run_log': str(run_root / f'{name}.log'),
        'conservation_log': str(run_root / f'conservation_{name}.log'),
        'growth_log': str(run_root / f'growth_{name}.log'),
        'plotfile_initial': str(run_dir / 'plt00000'),
        'plotfile_final': str(run_dir / plotfiles[-1]),
    }
    if amr_enabled:
        item['interface_amr_log'] = str(run_root / f'interface_amr_{name}.log')
    cases.append(item)
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({'build_log': str(run_root / 'build.log'), 'cases': cases}, indent=2, sort_keys=True) + '\n')
PY

python3 "$repo_root/tools/write_academic_twophase_interface_amr_validation_report.py" \
  --manifest "$manifest"
python3 "$repo_root/tools/write_academic_twophase_interface_amr_validation_report.py" \
  --verify-json "$root/academic_twophase_interface_amr_validation_report.json"

printf '[academic-twophase-interface-amr] PASS root=%s\n' "$root"
