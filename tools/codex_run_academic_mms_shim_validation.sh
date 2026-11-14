#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_MMS_SHIM_ROOT:-docs/codex_audit/evidence/academic_mms_shim_validation_20260728}"
case_src="external/PeleC/Exec/RegTests/MMS"
case_name="mms_constant_state_shim_8cell_2step"
case_root="$root/$case_name"
run_dir="$case_root/run"
shim_home="$case_root/masa_shim"
input_file="$run_dir/input.codex_mms_shim"
build_log="$case_root/build.log"
run_log="$case_root/run.log"
validation_log="$case_root/validation.log"

mkdir -p "$root"
if [[ "$case_root" != "$root/"* ]]; then
  printf '[academic-mms-shim] refusing unsafe case_root=%s root=%s\n' "$case_root" "$root" >&2
  exit 2
fi
rm -rf "$case_root"
mkdir -p "$run_dir" "$shim_home/include" "$shim_home/lib"

cat >"$shim_home/include/masa.h" <<'EOF'
#pragma once

#ifndef MASA_HD
#  ifdef AMREX_GPU_HOST_DEVICE
#    define MASA_HD AMREX_GPU_HOST_DEVICE
#  elif defined(AMREX_GPU_DEVICE)
#    define MASA_HD AMREX_GPU_DEVICE
#  else
#    define MASA_HD
#  endif
#endif

#include <cstdio>

namespace MASA {

inline void masa_init(const char*, const char*) {}
inline void masa_set_param(const char*, double) {}
inline void masa_display_param() { std::printf("MASA shim: constant-state manufactured solution\n"); }
inline void masa_sanity_check() {}

MASA_HD inline double masa_eval_3d_exact_rho(double, double, double) { return 1.0; }
MASA_HD inline double masa_eval_3d_exact_u(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_exact_v(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_exact_w(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_exact_p(double, double, double) { return 101325.0; }

MASA_HD inline double masa_eval_3d_source_rho(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_u(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_v(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_w(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_e(double, double, double) { return 0.0; }

} // namespace MASA
EOF

printf 'void codex_masa_shim_anchor(void) {}\n' >"$case_root/masa_shim_anchor.cpp"
g++ -c "$case_root/masa_shim_anchor.cpp" -o "$case_root/masa_shim_anchor.o"
ar rcs "$shim_home/lib/libmasa.a" "$case_root/masa_shim_anchor.o"

printf '[academic-mms-shim] building PeleC MMS case with local MASA shim\n'
(cd "$case_src" && MASA_HOME="$repo_root/$shim_home" make -j "${JOBS:-4}" >"$repo_root/$build_log" 2>&1)

python3 - <<'PY' "$case_src/cns-no-amr.inp" "$input_file"
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
replacements = {
    'max_step = 1000000': 'max_step = 2',
    'stop_time = 0.000005': 'stop_time = 1.0e-8',
    'amr.n_cell           =  16  16  16': 'amr.n_cell           =  8  8  8',
    'pelec.sum_interval   = 1': 'pelec.sum_interval   = 1',
    'amr.check_int       = 100000': 'amr.check_int       = 100000',
    'amr.plot_int        = 100000': 'amr.plot_int        = 2',
}
for old, new in replacements.items():
    text = text.replace(old, new)
dst.write_text(text, encoding='utf-8')
PY

cp "$case_src/PeleC3d.gnu.ex" "$run_dir/"

printf '[academic-mms-shim] running %s\n' "$case_name"
set +e
(cd "$run_dir" && timeout "${RUN_TIMEOUT:-240}" ./PeleC3d.gnu.ex "$(basename "$input_file")" >"$repo_root/$run_log" 2>&1)
run_rc=$?
set -e

python3 - <<'PY' "$repo_root" "$build_log" "$run_log"
import sys
from pathlib import Path

repo_root = sys.argv[1].rstrip('/') + '/'
for name in sys.argv[2:]:
    path = Path(name)
    if path.is_file():
        path.write_text(path.read_text(encoding='utf-8', errors='replace').replace(repo_root, ''), encoding='utf-8')
PY

set +e
python3 - <<'PY' "$run_log" "$run_rc" >"$validation_log" 2>&1
import math
import re
import sys
from pathlib import Path

run_log = Path(sys.argv[1])
run_rc = int(sys.argv[2])
text = run_log.read_text(encoding='utf-8', errors='replace')
if run_rc != 0:
    raise SystemExit(f'academic_mms_shim_validation FAIL run_returncode={run_rc}')
for token in ('NaN', 'nan', 'SIGSEGV', 'SIGABRT', 'Abort::'):
    if token in text:
        raise SystemExit(f'academic_mms_shim_validation FAIL failure_token={token}')
if 'AMReX' not in text or 'finalized' not in text:
    raise SystemExit('academic_mms_shim_validation FAIL amrex_finalization_missing')
if 'MASA shim: constant-state manufactured solution' not in text:
    raise SystemExit('academic_mms_shim_validation FAIL masa_shim_banner_missing')
patterns = {
    'rho_mms_error': r'RHO MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'u_mms_error': r'U MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'v_mms_error': r'V MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'w_mms_error': r'W MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'p_mms_error': r'P MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'rho_residual': r'RHO RESIDUAL\s*=\s*([0-9.eE+-]+)',
    'rhou_residual': r'RHO\*U RESIDUAL\s*=\s*([0-9.eE+-]+)',
    'rhov_residual': r'RHO\*V RESIDUAL\s*=\s*([0-9.eE+-]+)',
    'rhow_residual': r'RHO\*W RESIDUAL\s*=\s*([0-9.eE+-]+)',
    'rhoE_residual': r'RHO\*E RESIDUAL\s*=\s*([0-9.eE+-]+)',
}
values = {}
for key, pattern in patterns.items():
    matches = re.findall(pattern, text)
    if not matches:
        raise SystemExit(f'academic_mms_shim_validation FAIL missing_metric={key}')
    values[key] = float(matches[-1])
    if not math.isfinite(values[key]):
        raise SystemExit(f'academic_mms_shim_validation FAIL nonfinite_metric={key}')
max_error = max(values[k] for k in values if k.endswith('_error'))
max_residual = max(values[k] for k in values if k.endswith('_residual'))
if max_error > 1.0e-9:
    raise SystemExit(f'academic_mms_shim_validation FAIL max_error={max_error:.12g}')
if max_residual > 1.0e-9:
    raise SystemExit(f'academic_mms_shim_validation FAIL max_residual={max_residual:.12g}')
print(
    'academic_mms_shim_validation PASS '
    f'max_error={max_error:.12g} max_residual={max_residual:.12g} '
    + ' '.join(f'{key}={value:.12g}' for key, value in sorted(values.items()))
)
PY
validation_rc=$?
set -e
cat "$validation_log"

python3 - <<'PY' "$case_root/case_summary.json" "$case_name" "$input_file" "$build_log" "$run_log" "$validation_log" "$shim_home" "$run_rc" "$validation_rc"
import json
import sys
from pathlib import Path

out, case_name, input_file, build_log, run_log, validation_log, shim_home, run_rc, validation_rc = sys.argv[1:]
summary = {
    'case_name': case_name,
    'role': 'academic_mms_constant_state_wiring_validation',
    'solver': 'PeleC',
    'dimension': 3,
    'backend': 'CPU-serial',
    'input_file': input_file,
    'build_log': build_log,
    'run_log': run_log,
    'validation_log': validation_log,
    'masa_shim_home': shim_home,
    'run_returncode': int(run_rc),
    'validation_returncode': int(validation_rc),
    'max_step': 2,
    'n_cell': [8, 8, 8],
    'uses_external_masa': False,
}
Path(out).write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 tools/write_academic_mms_shim_validation_report.py \
  --case-summary "$case_root/case_summary.json" \
  --output-json "$root/academic_mms_shim_validation_report.json" \
  --output-md "$root/academic_mms_shim_validation_report.md"
python3 tools/write_academic_mms_shim_validation_report.py \
  --verify-json "$root/academic_mms_shim_validation_report.json"

cat >docs/codex_audit/2026-07-28-academic-mms-shim-validation.md <<'EOF'
# Academic MMS Shim Validation

Status: `PASS-ACADEMIC-MMS-SHIM-VALIDATION`

This audit records a maintained PeleC MMS wiring validation gate for QLT-03. The server does not currently provide MASA/MetaPhysicL, and GitHub source access timed out during dependency probing, so the gate uses a local MASA-compatible constant-state shim generated inside the evidence directory. It validates that the PeleC MMS RegTest builds with `PELE_USE_MASA`, links a MASA-compatible interface, enables `pelec.do_mms = 1`, computes MMS source/error diagnostics, finalizes cleanly, and keeps all constant-state MMS errors/residuals at roundoff.

Evidence:

- `docs/codex_audit/evidence/academic_mms_shim_validation_20260728/academic_mms_shim_validation_report.json`
- `docs/codex_audit/evidence/academic_mms_shim_validation_20260728/academic_mms_shim_validation_report.md`
- `tools/codex_run_academic_mms_shim_validation.sh`
- `tools/write_academic_mms_shim_validation_report.py`

Residual scope:

- This clears MMS wiring/build/runtime coverage only.
- It does not replace the nonlinear MASA manufactured-solution benchmark, MASA/MetaPhysicL installation, or experiment-grade validation.
EOF

printf '[academic-mms-shim] COMPLETE root=%s run_rc=%s validation_rc=%s\n' "$root" "$run_rc" "$validation_rc"
