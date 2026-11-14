#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/spray_test"
evidence_root="$repo_root/docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729"
run_root="${CODEX_SPRAY_CLOSED_BUDGET_RUN_ROOT:-/tmp/codex_academic_spray_closed_particle_budget_20260729}"
max_step="${CODEX_SPRAY_CLOSED_BUDGET_MAX_STEP:-50}"
plot_int="${CODEX_SPRAY_CLOSED_BUDGET_PLOT_INT:-50}"
run_timeout="${CODEX_SPRAY_CLOSED_BUDGET_TIMEOUT:-300}"

mkdir -p "$evidence_root" "$run_root"
run_dir=$(mktemp -d "$run_root/run.XXXXXX")
input_file="$run_dir/input.spray_closed_particle_budget"
run_log="$evidence_root/spray_closed_particle_budget.log"
validation_log="$evidence_root/validation_spray_closed_particle_budget.log"
exe="$case_dir/PeleC2d.gnu.ex"

if [[ ! -x "$exe" ]]; then
  printf '[academic-spray-closed-budget] missing executable: %s\n' "$exe" >&2
  printf '[academic-spray-closed-budget] build with: make -C %s -j ${JOBS:-4}\n' "$case_dir" >&2
  exit 2
fi

python3 - "$case_dir/inputs_spray_test" "$input_file" "$max_step" "$plot_int" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
max_step = sys.argv[3]
plot_int = sys.argv[4]
text = src.read_text()
replacements = {
    r'^max_step\s*=.*$': f'max_step = {max_step}',
    r'^amr\.plot_files_output\s*=.*$': 'amr.plot_files_output = 1',
    r'^amr\.max_grid_size\s*=.*$': 'amr.max_grid_size = 256',
}
for pattern, repl in replacements.items():
    text = re.sub(pattern, repl, text, flags=re.MULTILINE)
if not re.search(r'^amr\.plot_file\s*=', text, flags=re.MULTILINE):
    text += '\namr.plot_file = plt\n'
if not re.search(r'^amr\.plot_int\s*=', text, flags=re.MULTILINE):
    text += f'amr.plot_int = {plot_int}\n'
else:
    text = re.sub(r'^amr\.plot_int\s*=.*$', f'amr.plot_int = {plot_int}', text, flags=re.MULTILINE)
if not re.search(r'^amr\.checkpoint_files_output\s*=', text, flags=re.MULTILINE):
    text += 'amr.checkpoint_files_output = 0\n'
dst.write_text(text)
PY

(
  cd "$run_dir"
  timeout "$run_timeout" "$exe" "$(basename "$input_file")"
) 2>&1 | tee "$run_log"

initial="$run_dir/plt00000"
final="$run_dir/plt$(printf '%05d' "$max_step")"
if [[ ! -d "$initial" || ! -d "$final" ]]; then
  printf '[academic-spray-closed-budget] missing expected plotfiles initial=%s final=%s\n' "$initial" "$final" >&2
  exit 3
fi

python3 "$repo_root/tools/validate_academic_spray_closed_particle_budget.py" \
  --input "$input_file" \
  --run-log "$run_log" \
  --initial "$initial" \
  --final "$final" \
  --expected-step "$max_step" \
  | tee "$validation_log"

case_dir_out="$evidence_root/spray_closed_particle_budget"
rm -rf "$case_dir_out"
mkdir -p "$case_dir_out"
cp "$input_file" "$case_dir_out/input.spray_closed_particle_budget"
cp -a "$initial" "$case_dir_out/plt00000"
cp -a "$final" "$case_dir_out/plt$(printf '%05d' "$max_step")"
cat > "$evidence_root/case_manifest.json" <<JSON
{
  "cases": [
    {
      "name": "spray_closed_particle_budget",
      "role": "closed_fixed_particle_binary_budget",
      "input_file": "docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/spray_closed_particle_budget/input.spray_closed_particle_budget",
      "run_log": "docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/spray_closed_particle_budget.log",
      "validation_log": "docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/validation_spray_closed_particle_budget.log",
      "plotfile_initial": "docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/spray_closed_particle_budget/plt00000",
      "plotfile_final": "docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/spray_closed_particle_budget/plt$(printf '%05d' "$max_step")",
      "max_step": $max_step
    }
  ]
}
JSON

printf '[academic-spray-closed-budget] PASS evidence=%s run_dir=%s\n' "$evidence_root" "$run_dir"
