#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/external/PeleLMeX/Exec/RegTests/HotBubble"
exe="$case_dir/codex_hotbubble2d.gnu.ex"
log_dir=${CODEX_PELELMEX_HOTBUBBLE_LOG_DIR:-/tmp/codex_pelelmex_hotbubble_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir="$log_dir/run"
mkdir -p "$run_dir"

if [[ "${CODEX_SKIP_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-pelelmex-hotbubble] building PeleLMeX HotBubble"
  make -C "$case_dir" -j "${JOBS:-4}" USE_MPI=FALSE EBASE=codex_hotbubble >"$log_dir/build.log" 2>&1
else
  echo "[codex-pelelmex-hotbubble] reusing executable: $exe"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$exe" "$run_dir/"
python3 - "$case_dir/input.2d-regt" "$run_dir/input.codex_hotbubble" <<'PY'
from __future__ import annotations
from pathlib import Path
import sys

src, dst = sys.argv[1:3]
skip_keys = {
    "amr.ref_ratio",
    "amr.regrid_int",
    "amr.refinement_indicators",
    "cvode.solve_type",
    "ode.analytical_jacobian",
}
replacements = {
    "amr.n_cell": "amr.n_cell = 16 32",
    "amr.max_level": "amr.max_level = 0",
    "amr.max_grid_size": "amr.max_grid_size = 32",
    "amr.blocking_factor": "amr.blocking_factor = 8",
    "amr.plot_int": "amr.plot_int = 1",
    "amr.max_step": "amr.max_step = 10",
    "amr.stop_time": "amr.stop_time = 0.002",
    "amr.cfl": "amr.cfl = 0.5",
    "amr.derive_plot_vars": "amr.derive_plot_vars = avg_pressure mag_vort mass_fractions",
}
lines = []
seen = set()
for line in Path(src).read_text(encoding="utf-8").splitlines(True):
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        lines.append(line)
        continue
    key = stripped.split("=", 1)[0].strip() if "=" in stripped else None
    if key in skip_keys or key.startswith("amr.temp.") or key.startswith("amr.gtemp."):
        continue
    if key in replacements:
        lines.append(replacements[key] + "\n")
        seen.add(key)
        continue
    lines.append(line)
for key, value in replacements.items():
    if key not in seen:
        lines.append(value + "\n")
lines.append("amrex.abort_on_unused_inputs = 1\n")
Path(dst).write_text("".join(lines), encoding="utf-8")
PY

(
  cd "$run_dir"
  timeout "${RUN_TIMEOUT:-180}" ./codex_hotbubble2d.gnu.ex input.codex_hotbubble
) >"$log_dir/run.log" 2>&1

grep -q "Final simulation time: 0.002" "$log_dir/run.log"
grep -q "AMReX .* finalized" "$log_dir/run.log"
if grep -Eq "Unused ParmParse Variables|Backtrace|SIGABRT|Abort::" "$log_dir/run.log"; then
  echo "[codex-pelelmex-hotbubble] run log contains abort/unused/backtrace marker" >&2
  exit 1
fi

initial_plot="$run_dir/plt00000"
final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt*' | sort | tail -n 1)
if [[ -z "$final_plot" || "$final_plot" == "$initial_plot" ]]; then
  echo "[codex-pelelmex-hotbubble] missing final plotfile" >&2
  exit 1
fi

python3 "$repo_root/tools/validate_pelelmex_hotbubble_plotfile.py" \
  --initial "$initial_plot" \
  --final "$final_plot" \
  --expected-time 0.002 \
  | tee "$log_dir/validation.log"

echo "[codex-pelelmex-hotbubble] PASS; logs: $log_dir"
