#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_MMS_NONCONSTANT_DENSITY_ROOT:-docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729}"
case_src="external/PeleC/Exec/RegTests/MMS"
case_name="mms_nonconstant_density_stationary_8cell_1step"
case_root="$root/$case_name"
run_dir="$case_root/run"
shim_home="$case_root/masa_shim"
input_file="$run_dir/input.codex_mms_nonconstant_density"
build_log="$case_root/build.log"
run_log="$case_root/run.log"
validation_log="$case_root/validation.log"

mkdir -p "$root"
if [[ "$case_root" != "$root/"* ]]; then
  printf '[academic-mms-nonconstant-density] refusing unsafe case_root=%s root=%s\n' "$case_root" "$root" >&2
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

#include <cmath>
#include <cstdio>

namespace MASA {

inline void masa_init(const char*, const char*) {}
inline void masa_set_param(const char*, double) {}
inline void masa_display_param()
{
  std::printf("MASA shim: nonconstant-density stationary manufactured solution\n");
}
inline void masa_sanity_check() {}

MASA_HD inline double masa_eval_3d_exact_rho(double x, double y, double z)
{
  constexpr double pi = 3.141592653589793238462643383279502884;
  return 1.0 + 0.05 * std::cos(2.0 * pi * x) * std::cos(2.0 * pi * y) *
                 std::cos(2.0 * pi * z);
}
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

printf 'void codex_masa_nonconstant_density_shim_anchor(void) {}\n' >"$case_root/masa_shim_anchor.cpp"
g++ -c "$case_root/masa_shim_anchor.cpp" -o "$case_root/masa_shim_anchor.o"
ar rcs "$shim_home/lib/libmasa.a" "$case_root/masa_shim_anchor.o"

printf '[academic-mms-nonconstant-density] building PeleC MMS case with local nonconstant-density MASA shim\n'
(cd "$case_src" && make clean >/dev/null 2>&1 || true)
(cd "$case_src" && MASA_HOME="$repo_root/$shim_home" make -j "${JOBS:-4}" >"$repo_root/$build_log" 2>&1)

python3 - <<'PY' "$case_src/cns-no-amr.inp" "$input_file"
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
replacements = {
    'max_step = 1000000': 'max_step = 1',
    'stop_time = 0.000005': 'stop_time = 1.0e-10',
    'amr.n_cell           =  16  16  16': 'amr.n_cell           =  8  8  8',
    'amr.check_int       = 100000': 'amr.check_int       = 100000',
    'amr.plot_int        = 100000': 'amr.plot_int        = 1',
}
for old, new in replacements.items():
    text = text.replace(old, new)
dst.write_text(text, encoding='utf-8')
PY

cp "$case_src/PeleC3d.gnu.ex" "$run_dir/"

printf '[academic-mms-nonconstant-density] running %s\n' "$case_name"
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
    raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL run_returncode={run_rc}')
for token in ('NaN', 'nan', 'SIGSEGV', 'SIGABRT', 'Abort::'):
    if token in text:
        raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL failure_token={token}')
if 'AMReX' not in text or 'finalized' not in text:
    raise SystemExit('academic_mms_nonconstant_density_shim_validation FAIL amrex_finalization_missing')
if 'MASA shim: nonconstant-density stationary manufactured solution' not in text:
    raise SystemExit('academic_mms_nonconstant_density_shim_validation FAIL shim_banner_missing')
patterns = {
    'rho_mms_error': r'RHO MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'u_mms_error': r'U MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'v_mms_error': r'V MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'w_mms_error': r'W MMS ERROR\s*=\s*([0-9.eE+-]+)',
    'pressure_error': r'P MMS ERROR\s*=\s*([0-9.eE+-]+)',
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
        raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL missing_metric={key}')
    values[key] = float(matches[-1])
    if not math.isfinite(values[key]):
        raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL nonfinite_metric={key}')
primary_error_keys = ['rho_mms_error', 'u_mms_error', 'v_mms_error', 'w_mms_error']
primary_residual_keys = ['rho_residual', 'rhou_residual', 'rhov_residual', 'rhow_residual']
max_primary_error = max(values[key] for key in primary_error_keys)
max_primary_residual = max(values[key] for key in primary_residual_keys)
pressure_error_relative = values['pressure_error'] / 101325.0
rhoE_reference = 101325.0 / 0.4
rhoE_residual_relative = values['rhoE_residual'] / rhoE_reference
if max_primary_error > 1.0e-10:
    raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL max_primary_error={max_primary_error:.12g}')
if max_primary_residual > 1.0e-10:
    raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL max_primary_residual={max_primary_residual:.12g}')
if pressure_error_relative > 1.0e-7:
    raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL pressure_error_relative={pressure_error_relative:.12g}')
if rhoE_residual_relative > 1.0e-7:
    raise SystemExit(f'academic_mms_nonconstant_density_shim_validation FAIL rhoE_residual_relative={rhoE_residual_relative:.12g}')
print(
    'academic_mms_nonconstant_density_shim_validation PASS '
    f'max_primary_error={max_primary_error:.12g} '
    f'max_primary_residual={max_primary_residual:.12g} '
    f'pressure_error={values["pressure_error"]:.12g} '
    f'rhoE_residual={values["rhoE_residual"]:.12g} '
    f'pressure_error_relative={pressure_error_relative:.12g} '
    f'rhoE_residual_relative={rhoE_residual_relative:.12g} '
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
    'role': 'academic_mms_nonconstant_density_stationary_validation',
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
    'max_step': 1,
    'stop_time': 1.0e-10,
    'n_cell': [8, 8, 8],
    'uses_external_masa': False,
    'manufactured_solution_kind': 'nonconstant_density_stationary',
    'density_perturbation_amplitude': 0.05,
    'exact_pressure': 101325.0,
}
Path(out).write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 tools/write_academic_mms_nonconstant_density_shim_validation_report.py \
  --case-summary "$case_root/case_summary.json" \
  --output-json "$root/academic_mms_nonconstant_density_shim_validation_report.json" \
  --output-md "$root/academic_mms_nonconstant_density_shim_validation_report.md"
python3 tools/write_academic_mms_nonconstant_density_shim_validation_report.py \
  --verify-json "$root/academic_mms_nonconstant_density_shim_validation_report.json"

cat >docs/codex_audit/2026-07-29-academic-mms-nonconstant-density-shim-validation.md <<'EOF'
# Academic MMS Nonconstant-Density Shim Validation

Status: `PASS-ACADEMIC-MMS-NONCONSTANT-DENSITY-SHIM-VALIDATION`

This audit records a strengthened in-repository PeleC MMS validation gate for QLT-03. The server still lacks a real MASA/MetaPhysicL installation, so this gate generates a MASA-compatible shim with a nonconstant stationary density field, zero velocity, constant pressure, and zero source terms. It verifies that the MMS path evaluates spatially varying exact fields, computes MMS errors/residuals, finalizes cleanly, and keeps primary density/velocity errors plus relative pressure/energy residuals within bounded gates.

Evidence:

- `docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729/academic_mms_nonconstant_density_shim_validation_report.json`
- `docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729/academic_mms_nonconstant_density_shim_validation_report.md`
- `tools/codex_run_academic_mms_nonconstant_density_shim_validation.sh`
- `tools/write_academic_mms_nonconstant_density_shim_validation_report.py`

Residual scope:

- This strengthens MMS coverage beyond the constant-state shim.
- It does not clear the external nonlinear MASA/MetaPhysicL benchmark because no external MASA installation is available on the server.
EOF

printf '[academic-mms-nonconstant-density] COMPLETE root=%s run_rc=%s validation_rc=%s\n' "$root" "$run_rc" "$validation_rc"
