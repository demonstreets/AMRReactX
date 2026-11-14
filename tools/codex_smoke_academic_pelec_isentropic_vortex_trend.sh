#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/external/PeleC/Exec/RegTests/IsentropicVortex"
exe="$case_dir/codex_isentropic_vortex3d.gnu.ex"
log_dir=${CODEX_ISENTROPIC_VORTEX_TREND_LOG_DIR:-/tmp/codex_pelec_isentropic_vortex_trend_$(date -u +%Y%m%dT%H%M%SZ)}
resolutions=${CODEX_ISENTROPIC_VORTEX_RESOLUTIONS:-"16 32 64"}
summary="$log_dir/summary.tsv"
trend_stop_time=${CODEX_VORTEX_STOP_TIME:-0.003}
trend_max_step=${CODEX_VORTEX_MAX_STEP:-30}
trend_cfl=${CODEX_VORTEX_CFL:-0.5}
trend_exact=${CODEX_VORTEX_EXACT:-0}
trend_beta=${CODEX_VORTEX_BETA:-5.0}
trend_p_bg=${CODEX_VORTEX_P_BG:-}
trend_rho_bg=${CODEX_VORTEX_RHO_BG:-}
trend_u_bg=${CODEX_VORTEX_U_BG:-}
trend_v_bg=${CODEX_VORTEX_V_BG:-}
mkdir -p "$log_dir"

if [[ "${CODEX_SKIP_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-isentropic-vortex-trend] building PeleC IsentropicVortex"
  make -C "$case_dir" -j "${JOBS:-2}" EBASE=codex_isentropic_vortex >"$log_dir/build.log" 2>&1
else
  echo "[codex-isentropic-vortex-trend] reusing existing executable: $exe"
fi

printf 'case\tnx\tny\tnz\ttime\tinit_linf\tdensity_l1\tpressure_l1\tu_l1\tv_l1\tmass_rel\tentropy_linf\ttemp_min\ttemp_max\n' >"$summary"

for n in $resolutions; do
  case_log_dir="$log_dir/n${n}"
  run_dir="$case_log_dir/run"
  rm -rf "$case_log_dir"
  mkdir -p "$run_dir"
  cp "$exe" "$run_dir/"

  python3 - "$case_dir/input.codex_smoke" "$run_dir/input.codex_trend" "$n" "$trend_stop_time" "$trend_max_step" "$trend_cfl" "$trend_exact" "$trend_beta" "$trend_p_bg" "$trend_rho_bg" "$trend_u_bg" "$trend_v_bg" <<'PY'
from __future__ import annotations
import re
import sys

src, dst, n_s, stop_time, max_step, cfl, exact, beta, p_bg, rho_bg, u_bg, v_bg = sys.argv[1:13]
n = int(n_s)
replacements = {
    "max_step": f"max_step = {max_step}",
    "stop_time": f"stop_time = {stop_time}",
    "pelec.cfl": f"pelec.cfl = {cfl}",
    "amr.n_cell": f"amr.n_cell = {n} {n} 2",
    "amr.max_grid_size": f"amr.max_grid_size = {n}",
    "amr.plot_int": "amr.plot_int = 1",
    "prob.exact_vortex": f"prob.exact_vortex = {exact}",
    "prob.vortex_beta": f"prob.vortex_beta = {beta}",
}
optional = {
    "prob.p_bg": p_bg,
    "prob.rho_bg": rho_bg,
    "prob.u_bg": u_bg,
    "prob.v_bg": v_bg,
}
for key, value in optional.items():
    if value != "":
        replacements[key] = f"{key} = {value}"
seen = set()
with open(src, "r", encoding="utf-8") as fh:
    lines = fh.readlines()
new_lines = []
for line in lines:
    stripped = line.strip()
    replaced = False
    for key, value in replacements.items():
        if re.match(rf"^\s*{re.escape(key)}\s*=", line):
            new_lines.append(value + "\n")
            seen.add(key)
            replaced = True
            break
    if not replaced:
        new_lines.append(line)
for key, value in replacements.items():
    if key not in seen:
        new_lines.append(value + "\n")
with open(dst, "w", encoding="utf-8") as fh:
    fh.writelines(new_lines)
PY

  echo "[codex-isentropic-vortex-trend] running nx=$n stop_time=$trend_stop_time cfl=$trend_cfl exact=$trend_exact beta=$trend_beta p_bg=${trend_p_bg:-base}"
  (
    cd "$run_dir"
    timeout "${RUN_TIMEOUT:-240}" ./codex_isentropic_vortex3d.gnu.ex input.codex_trend
  ) >"$case_log_dir/run.log" 2>&1

  grep -q "PLOTFILE: file = plt00000" "$case_log_dir/run.log"
  grep -q "AMReX .* finalized" "$case_log_dir/run.log"
  if grep -Eq "Unused ParmParse Variables|Backtrace|SIGABRT|Abort::" "$case_log_dir/run.log"; then
    echo "[codex-isentropic-vortex-trend] nx=$n run log contains abort/unused/backtrace marker" >&2
    exit 1
  fi

  final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt*' | sort | tail -n 1)
  if [[ -z "$final_plot" || "$(basename "$final_plot")" == "plt00000" ]]; then
    echo "[codex-isentropic-vortex-trend] nx=$n missing final plotfile" >&2
    exit 1
  fi

  python3 "$repo_root/tools/validate_pelec_isentropic_vortex.py" \
    --initial "$run_dir/plt00000" \
    --final "$final_plot" \
    --run-log "$case_log_dir/run.log" \
    --input "$run_dir/input.codex_trend" \
    --max-final-density-l1 "${CODEX_VORTEX_MAX_DENSITY_L1:-2.0e-3}" \
    --max-final-pressure-l1 "${CODEX_VORTEX_MAX_PRESSURE_L1:-2.0e-3}" \
    --max-final-velocity-l1 "${CODEX_VORTEX_MAX_VELOCITY_L1:-1.0e-2}" \
    | tee "$case_log_dir/validation.log"

  python3 - "$case_log_dir/validation.log" "$summary" "n${n}" <<'PY'
from __future__ import annotations
import re
import sys

log_path, summary_path, case_name = sys.argv[1:4]
text = open(log_path, "r", encoding="utf-8").read()
if "pelec_isentropic_vortex_validation PASS" not in text:
    raise SystemExit("validation log missing PASS line")
fields = dict(re.findall(r"(time|nx|ny|nz|init_linf|density_l1|pressure_l1|u_l1|v_l1|mass_rel|entropy_linf|temp_min|temp_max)=([-+0-9.eE]+)", text))
required = ["nx", "ny", "nz", "time", "init_linf", "density_l1", "pressure_l1", "u_l1", "v_l1", "mass_rel", "entropy_linf", "temp_min", "temp_max"]
missing = [name for name in required if name not in fields]
if missing:
    raise SystemExit("missing metrics: " + ",".join(missing))
with open(summary_path, "a", encoding="utf-8") as fh:
    fh.write(case_name + "\t" + "\t".join(fields[name] for name in required) + "\n")
PY
done

python3 "$repo_root/tools/validate_pelec_isentropic_vortex_trend.py" \
  --summary "$summary" \
  --max-velocity-l1 "${CODEX_VORTEX_TREND_MAX_VELOCITY_L1:-2.0e-4}" \
  --min-density-drop "${CODEX_VORTEX_TREND_MIN_DENSITY_DROP:-1.15}" \
  --min-pressure-drop "${CODEX_VORTEX_TREND_MIN_PRESSURE_DROP:-1.15}" \
  --min-entropy-drop "${CODEX_VORTEX_TREND_MIN_ENTROPY_DROP:-10.0}" \
  | tee "$log_dir/trend_validation.log"

echo "[codex-isentropic-vortex-trend] PASS; logs: $log_dir"
