#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_GAS_DOUBLE_MACH_ROOT:-docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728}"
case_name="double_mach_reflection_8step"
case_root="$root/$case_name"
runner_log="$case_root/runner.log"
input_file="$case_root/run/input.codex_smoke"
run_log="$case_root/run.log"
build_log="$case_root/build.log"
validation_log="$case_root/validation.log"
final_plot="$case_root/run/plt00008"

mkdir -p "$root"
if [[ "$case_root" != "$root/"* ]]; then
  printf '[academic-gas-double-mach] refusing unsafe case_root=%s root=%s\n' "$case_root" "$root" >&2
  exit 2
fi
rm -rf "$case_root"
mkdir -p "$case_root"

printf '[academic-gas-double-mach] running maintained Double-Mach smoke case\n'
CODEX_DOUBLE_MACH_LOG_DIR="$case_root" \
CODEX_DOUBLE_MACH_INPUT=input.codex_smoke \
CODEX_DOUBLE_MACH_EXPECT_STEP=8 \
RUN_TIMEOUT="${RUN_TIMEOUT:-240}" \
JOBS="${JOBS:-4}" \
  bash tools/codex_smoke_academic_double_mach.sh >"$runner_log" 2>&1
python3 - <<'PY' "$repo_root" "$runner_log" "$build_log" "$run_log" "$validation_log"
import sys
from pathlib import Path

repo_root = sys.argv[1].rstrip('/') + '/'
for name in sys.argv[2:]:
    path = Path(name)
    if path.is_file():
        text = path.read_text(encoding='utf-8', errors='replace')
        path.write_text(text.replace(repo_root, ''), encoding='utf-8')
PY
cat "$runner_log"

python3 - <<'PY' "$case_root/case_summary.json" "$case_name" "$input_file" "$build_log" "$run_log" "$runner_log" "$validation_log" "$final_plot"
import json
import sys
from pathlib import Path

out, case_name, input_file, build_log, run_log, runner_log, validation_log, final_plot = sys.argv[1:]
summary = {
    'case_name': case_name,
    'role': 'academic_gas_double_mach_reflection_strong_shock_validation',
    'solver': 'PeleC',
    'dimension': 3,
    'backend': 'CPU-serial',
    'input_file': input_file,
    'build_log': build_log,
    'run_log': run_log,
    'runner_log': runner_log,
    'validation_log': validation_log,
    'final_plot': final_plot,
    'max_step': 8,
    'chemistry_model': 'Null',
    'eos_model': 'GammaLaw',
}
Path(out).write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 tools/write_academic_gas_double_mach_validation_report.py \
  --case-summary "$case_root/case_summary.json" \
  --output-json "$root/academic_gas_double_mach_validation_report.json" \
  --output-md "$root/academic_gas_double_mach_validation_report.md"
python3 tools/write_academic_gas_double_mach_validation_report.py \
  --verify-json "$root/academic_gas_double_mach_validation_report.json"

cat >docs/codex_audit/2026-07-28-academic-gas-double-mach-validation.md <<'EOF'
# Academic Gas Double-Mach Reflection Validation

Status: `PASS-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION`

This audit records the maintained PeleC Double-Mach reflection strong-shock validation gate for QLT-03 standard validation coverage. The case exercises inviscid GammaLaw shock reflection with positive density/pressure checks, finite-field checks, Rankine-Hugoniot plateau-state checks, shock-front advancement, and clean AMReX finalization.

Evidence:

- `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.json`
- `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.md`
- `tools/codex_run_academic_gas_double_mach_validation.sh`
- `tools/write_academic_gas_double_mach_validation_report.py`

Residual scope:

- This clears the Double-Mach component of QLT-03.
- MMS, bubble-rise, and external experiment-grade comparisons remain separate QLT-03 gaps.
EOF

printf '[academic-gas-double-mach] PASS root=%s\n' "$root"
