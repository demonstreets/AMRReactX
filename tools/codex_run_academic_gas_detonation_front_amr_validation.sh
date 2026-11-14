#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/detonation_znd_gpu"
exe="$case_dir/codex_deton3d_znd_amr_cpu3d.gnu.MPI.ex"
root="${CODEX_DETONATION_FRONT_AMR_ROOT:-$repo_root/docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728}"
run_root="$root/runs"
manifest="$root/case_manifest.json"
max_step="${CODEX_DETONATION_FRONT_AMR_MAX_STEP:-80}"
stop_time="${CODEX_DETONATION_FRONT_AMR_STOP_TIME:-5.0e-7}"
mpi_ranks="${CODEX_DETONATION_FRONT_AMR_MPI_RANKS:-2}"
run_timeout="${RUN_TIMEOUT:-600}"

mkdir -p "$run_root"

printf '[academic-detonation-front-amr] building detonation_znd CPU/MPI executable\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_deton3d_znd_amr_cpu \
  USE_MPI=TRUE USE_CUDA=FALSE USE_EXPLICIT_REACT=FALSE > "$root/build.log" 2>&1

run_case() {
  local name="$1"
  local role="$2"
  local nx="$3"
  local ny="$4"
  local nz="$5"
  local max_level="$6"
  local expect_amr="$7"
  local run_dir="$run_root/$name"
  local input_file="$run_dir/inputs"
  local run_log="$run_dir/run.log"
  local validation_log="$run_dir/validation.log"
  mkdir -p "$run_dir"
  rm -rf "$run_dir"/plt* "$run_dir"/chk* "$run_log" "$validation_log" "$input_file"
  cp "$exe" "$run_dir/"
  python3 - "$case_dir/inputs" "$input_file" "$nx" "$ny" "$nz" "$max_level" "$max_step" "$stop_time" <<'PY'
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
nx = int(sys.argv[3])
ny = int(sys.argv[4])
nz = int(sys.argv[5])
max_level = int(sys.argv[6])
max_step = int(sys.argv[7])
stop_time = sys.argv[8]
text = src.read_text(encoding='utf-8')
replacements = {
    r'^max_step\s*=.*$': f'max_step = {max_step}',
    r'^stop_time\s*=.*$': f'stop_time = {stop_time}',
    r'^amr\.n_cell\s*=.*$': f'amr.n_cell = {nx} {ny} {nz}',
    r'^amr\.max_level\s*=.*$': f'amr.max_level = {max_level}',
    r'^amr\.ref_ratio\s*=.*$': 'amr.ref_ratio = 2',
    r'^amr\.regrid_int\s*=.*$': 'amr.regrid_int = 2',
    r'^amr\.blocking_factor\s*=.*$': 'amr.blocking_factor = 4',
    r'^amr\.max_grid_size\s*=.*$': 'amr.max_grid_size = 64',
    r'^amr\.n_error_buf\s*=.*$': 'amr.n_error_buf = 2 2 2 2',
    r'^tagging\.dengrad\s*=.*$': 'tagging.dengrad = 0.05',
    r'^tagging\.max_dengrad_lev\s*=.*$': 'tagging.max_dengrad_lev = 1',
    r'^tagging\.pressgrad\s*=.*$': 'tagging.pressgrad = 0.25',
    r'^tagging\.max_pressgrad_lev\s*=.*$': 'tagging.max_pressgrad_lev = 1',
    r'^tagging\.tempgrad\s*=.*$': 'tagging.tempgrad = 50',
    r'^tagging\.max_tempgrad_lev\s*=.*$': 'tagging.max_tempgrad_lev = 1',
    r'^amr\.plot_int\s*=.*$': f'amr.plot_int = {max_step}',
    r'^amr\.check_int\s*=.*$': 'amr.check_int = -1',
}
for pattern, replacement in replacements.items():
    text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f'failed to replace {pattern}')
dst.write_text(text, encoding='utf-8')
PY
  printf '[academic-detonation-front-amr] running %s role=%s n_cell=%sx%sx%s max_level=%s ranks=%s\n' \
    "$name" "$role" "$nx" "$ny" "$nz" "$max_level" "$mpi_ranks"
  (
    cd "$run_dir"
    timeout "$run_timeout" mpirun --oversubscribe -np "$mpi_ranks" \
      "./$(basename "$exe")" "$(basename "$input_file")" > "$run_log" 2>&1
  )
  grep -q 'AMReX .* finalized' "$run_log"
  if grep -qiE 'nan|inf|SIGSEGV|Segmentation|Backtrace|Abort|Simulation stopped early' "$run_log"; then
    echo "[academic-detonation-front-amr] $name failure marker in run log" >&2
    exit 1
  fi
  final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt[0-9][0-9][0-9][0-9][0-9]' -printf '%f\n' | sort | tail -1)
  if [[ -z "$final_plot" || "$final_plot" == "plt00000" ]]; then
    echo "[academic-detonation-front-amr] $name did not produce a final plotfile" >&2
    exit 1
  fi
  validator_args=(
    "$repo_root/tools/validate_academic_gas_detonation_front_amr.py"
    --initial "$run_dir/plt00000"
    --final "$run_dir/$final_plot"
  )
  if [[ "$expect_amr" == TRUE ]]; then
    validator_args+=(--expect-amr)
  fi
  python3 "${validator_args[@]}" | tee "$validation_log"
}

run_case amr_96x4x4_l1 amr_front 96 4 4 1 TRUE
run_case uniform_fine_192x8x8 uniform_fine_reference 192 8 8 0 FALSE

python3 - "$manifest" "$run_root" "$max_step" <<'PY'
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
run_root = Path(sys.argv[2])
max_step = int(sys.argv[3])
cases = [
    {'name': 'amr_96x4x4_l1', 'role': 'amr_front', 'amr_enabled': True, 'n_cell': [96, 4, 4], 'max_level': 1, 'ref_ratio': 2},
    {'name': 'uniform_fine_192x8x8', 'role': 'uniform_fine_reference', 'amr_enabled': False, 'n_cell': [192, 8, 8], 'max_level': 0, 'ref_ratio': 1},
]
for case in cases:
    run_dir = run_root / case['name']
    plotfiles = sorted(p.name for p in run_dir.glob('plt[0-9][0-9][0-9][0-9][0-9]') if p.name != 'plt00000')
    if not plotfiles:
        raise SystemExit(f'{case["name"]} has no final plotfile')
    case['run_dir'] = str(run_dir)
    case['input_file'] = str(run_dir / 'inputs')
    case['run_log'] = str(run_dir / 'run.log')
    case['validation_log'] = str(run_dir / 'validation.log')
    case['plotfile_initial'] = str(run_dir / 'plt00000')
    case['plotfile_final'] = str(run_dir / plotfiles[-1])
    case['max_step'] = max_step
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({'cases': cases}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 "$repo_root/tools/write_academic_gas_detonation_front_amr_validation_report.py" \
  --manifest "$manifest"
python3 "$repo_root/tools/write_academic_gas_detonation_front_amr_validation_report.py" \
  --verify-json "$root/academic_gas_detonation_front_amr_validation_report.json"

printf '[academic-detonation-front-amr] PASS root=%s\n' "$root"
