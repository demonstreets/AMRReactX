#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/detonation_2D"
exe="$case_dir/codex_deton2d_cpu2d.gnu.ex"
root="${CODEX_2D_DETONATION_REFERENCE_ROOT:-$repo_root/docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728}"
run_root="$root/runs"
manifest="$root/case_manifest.json"
max_step="${CODEX_2D_DETONATION_REFERENCE_MAX_STEP:-200}"
stop_time="${CODEX_2D_DETONATION_REFERENCE_STOP_TIME:-1.35e-7}"
run_timeout="${RUN_TIMEOUT:-300}"

mkdir -p "$run_root"

printf '[academic-2d-detonation-reference] building detonation_2D executable\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_deton2d_cpu

for spec in "coarse_64x32:64:32" "medium_96x48:96:48" "fine_128x64:128:64"; do
  IFS=: read -r name nx ny <<<"$spec"
  run_dir="$run_root/$name"
  input_file="$run_dir/inputs"
  run_log="$run_dir/run.log"
  validation_log="$run_dir/validation.log"
  mkdir -p "$run_dir"
  rm -rf "$run_dir"/plt* "$run_log" "$validation_log" "$input_file"
  python3 - "$case_dir/inputs.codex_wave_smoke" "$input_file" "$nx" "$ny" "$max_step" "$stop_time" <<'PY'
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
nx = int(sys.argv[3])
ny = int(sys.argv[4])
max_step = int(sys.argv[5])
stop_time = sys.argv[6]
text = src.read_text(encoding='utf-8')
replacements = {
    r'^max_step\s*=.*$': f'max_step = {max_step}',
    r'^stop_time\s*=.*$': f'stop_time = {stop_time}',
    r'^amr\.n_cell\s*=.*$': f'amr.n_cell = {nx} {ny} 1',
    r'^amr\.blocking_factor\s*=.*$': 'amr.blocking_factor = 16',
    r'^amr\.plot_int\s*=.*$': f'amr.plot_int = {max_step}',
}
for pattern, replacement in replacements.items():
    text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f'failed to replace {pattern}')
dst.write_text(text, encoding='utf-8')
PY
  printf '[academic-2d-detonation-reference] running %s n_cell=%sx%s max_step=%s\n' "$name" "$nx" "$ny" "$max_step"
  (
    cd "$run_dir"
    timeout "$run_timeout" "$exe" "$input_file" > "$run_log" 2>&1
  )
  grep -q 'AMReX .* finalized' "$run_log"
  if grep -q 'Unused ParmParse Variables' "$run_log"; then
    echo "[academic-2d-detonation-reference] $name left unused ParmParse variables" >&2
    exit 1
  fi
  final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt[0-9][0-9][0-9][0-9][0-9]' -printf '%f\n' | sort | tail -1)
  if [[ -z "$final_plot" || "$final_plot" == "plt00000" ]]; then
    echo "[academic-2d-detonation-reference] $name did not produce a final plotfile" >&2
    exit 1
  fi
  python3 "$repo_root/tools/validate_detonation_wave.py" \
    --initial "$run_dir/plt00000" \
    --final "$run_dir/$final_plot" \
    --min-temp-rise 1.0 | tee "$validation_log"
done

python3 - "$manifest" "$run_root" "$max_step" <<'PY'
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
run_root = Path(sys.argv[2])
max_step = int(sys.argv[3])
cases = [
    {'name': 'coarse_64x32', 'n_cell': [64, 32, 1]},
    {'name': 'medium_96x48', 'n_cell': [96, 48, 1]},
    {'name': 'fine_128x64', 'n_cell': [128, 64, 1]},
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
    case['prob_lo'] = [0.0, 0.0, 0.0]
    case['prob_hi'] = [5.0, 2.5, 0.01]
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({'cases': cases}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 "$repo_root/tools/write_academic_gas_2d_detonation_reference_report.py" \
  --manifest "$manifest"
python3 "$repo_root/tools/write_academic_gas_2d_detonation_reference_report.py" \
  --verify-json "$root/academic_gas_2d_detonation_reference_report.json"

printf '[academic-2d-detonation-reference] PASS root=%s\n' "$root"
