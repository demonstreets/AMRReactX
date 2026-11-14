#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/external/PeleLMeX/Exec/RegTests/PeriodicCases"
exe="$case_dir/codex_periodic_covo2d.gnu.ex"
log_dir=${CODEX_PELELMEX_COVO_LOG_DIR:-/tmp/codex_pelelmex_periodic_covo_$(date -u +%Y%m%dT%H%M%SZ)}
resolutions=${CODEX_PELELMEX_COVO_RESOLUTIONS:-"16 32 64"}
mkdir -p "$log_dir"

if [[ "${CODEX_SKIP_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-pelelmex-covo] building PeleLMeX PeriodicCases CoVo"
  make -C "$case_dir" -j "${JOBS:-4}" USE_MPI=FALSE EBASE=codex_periodic_covo >"$log_dir/build.log" 2>&1
else
  echo "[codex-pelelmex-covo] reusing executable: $exe"
fi

cases=()
for n in $resolutions; do
  case_log_dir="$log_dir/n${n}"
  run_dir="$case_log_dir/run"
  rm -rf "$case_log_dir"
  mkdir -p "$run_dir"
  cp "$exe" "$run_dir/"
  python3 - "$case_dir/input.2d_CoVo" "$run_dir/input.codex_covo" "$n" <<'PY'
from __future__ import annotations
from pathlib import Path
import re
import sys

src, dst, n_s = sys.argv[1:4]
n = int(n_s)
skip_keys = {
    "amr.ref_ratio",
    "amr.regrid_int",
    "godunov.use_ppm",
    "peleLM.rho",
    "peleLM.mu",
}
replacements = {
    "amr.n_cell": f"amr.n_cell = {n} {n}",
    "amr.max_grid_size": f"amr.max_grid_size = {n}",
    "amr.blocking_factor": f"amr.blocking_factor = {max(4, min(16, n))}",
    "amr.max_step": "amr.max_step = 500",
    "amr.stop_time": "amr.stop_time = 0.02",
    "amr.cfl": "amr.cfl = 0.5",
    "amr.plot_int": "amr.plot_int = 1",
    "amr.derive_plot_vars": "amr.derive_plot_vars = avg_pressure mag_vort mass_fractions",
}
lines = Path(src).read_text(encoding="utf-8").splitlines(True)
out = []
seen = set()
for line in lines:
    if any(re.match(rf"^\s*{re.escape(key)}\s*=", line) for key in skip_keys):
        continue
    done = False
    for key, value in replacements.items():
        if re.match(rf"^\s*{re.escape(key)}\s*=", line):
            out.append(value + "\n")
            seen.add(key)
            done = True
            break
    if not done:
        out.append(line)
for key, value in replacements.items():
    if key not in seen:
        out.append(value + "\n")
out.append("amrex.abort_on_unused_inputs = 1\n")
Path(dst).write_text("".join(out), encoding="utf-8")
PY

  echo "[codex-pelelmex-covo] running nx=$n"
  (
    cd "$run_dir"
    timeout "${RUN_TIMEOUT:-240}" ./codex_periodic_covo2d.gnu.ex input.codex_covo
  ) >"$case_log_dir/run.log" 2>&1

  grep -q "Final simulation time: 0.02" "$case_log_dir/run.log"
  grep -q "AMReX .* finalized" "$case_log_dir/run.log"
  if grep -Eq "Unused ParmParse Variables|Backtrace|SIGABRT|Abort::" "$case_log_dir/run.log"; then
    echo "[codex-pelelmex-covo] nx=$n run log contains abort/unused/backtrace marker" >&2
    exit 1
  fi
  final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt*' | sort | tail -n 1)
  if [[ -z "$final_plot" || "$(basename "$final_plot")" == "plt00000" ]]; then
    echo "[codex-pelelmex-covo] nx=$n missing final plotfile" >&2
    exit 1
  fi
  cases+=("--case" "${n}=${final_plot}")
done

python3 "$repo_root/tools/validate_pelelmex_periodic_covo_self_convergence.py" \
  "${cases[@]}" \
  --min-order "${CODEX_PELELMEX_COVO_MIN_ORDER:-1.0}" \
  | tee "$log_dir/validation.log"

echo "[codex-pelelmex-covo] PASS; logs: $log_dir"
