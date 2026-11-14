#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/bfs_kepsilon"
build_dir="$repo_root/build-codex-smoke"
converter="$build_dir/my_pele_yaml_to_parmparse"
profile_yaml="$case_dir/input.codex_yaml_profile_smoke.yaml"
exe="$case_dir/codex_bfs_cpu2d.gnu.ex"
log_dir=${CODEX_BFS_LOGLAW_PROFILE_LOG_DIR:-/tmp/codex_bfs_loglaw_profile_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir="$log_dir/run"
generated_input="$log_dir/input.codex_bfs_loglaw_profile"
mkdir -p "$run_dir"

if [[ "${CODEX_SKIP_CONVERTER:-0}" != "1" || ! -x "$converter" ]]; then
  echo "[codex-bfs-loglaw] configuring/building YAML converter"
  cmake -S "$repo_root" -B "$build_dir" -DMYPELE_ENABLE_UNIT_SMOKE=ON >"$log_dir/cmake.log" 2>&1
  cmake --build "$build_dir" --target my_pele_yaml_to_parmparse -j "${JOBS:-4}" >"$log_dir/converter_build.log" 2>&1
fi

"$converter" "$profile_yaml" "$generated_input" --dim 2 --solver-only
python3 - "$generated_input" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
replacements = {
    "amr.plot_int": "amr.plot_int = 1",
    "amr.max_step": "amr.max_step = 1",
    "amr.stop_time": "amr.stop_time = -1.0",
}
lines = []
seen = set()
for line in path.read_text().splitlines(True):
    key = line.strip().split("=", 1)[0].strip() if "=" in line else None
    if key in replacements:
        lines.append(replacements[key] + "\n")
        seen.add(key)
    else:
        lines.append(line)
for key, value in replacements.items():
    if key not in seen:
        lines.append(value + "\n")
lines.append("amrex.abort_on_unused_inputs = 1\n")
path.write_text("".join(lines))
PY

grep -q '^prob.windProfileType = 1$' "$generated_input"
grep -q '^prob.windRefHeight = 10$' "$generated_input"
grep -q '^prob.windRoughnessLength = 0.029999999999999999$' "$generated_input"
grep -q '^amr.plot_int = 1$' "$generated_input"

if [[ "${CODEX_SKIP_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-bfs-loglaw] building PeleLMeX BFS"
  make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_bfs_cpu >"$log_dir/build.log" 2>&1
fi

(
  cd "$run_dir"
  timeout "${RUN_TIMEOUT:-120}" "$exe" "$generated_input"
) >"$log_dir/run.log" 2>&1

grep -q "AMReX .* finalized" "$log_dir/run.log"
if grep -Eq "Unused ParmParse Variables|Backtrace|SIGABRT|Abort::" "$log_dir/run.log"; then
  echo "[codex-bfs-loglaw] run log contains abort/unused/backtrace marker" >&2
  exit 1
fi
if [[ ! -d "$run_dir/plt00000" ]]; then
  echo "[codex-bfs-loglaw] missing initial plotfile" >&2
  exit 1
fi

python3 "$repo_root/tools/validate_bfs_loglaw_profile_plotfile.py" \
  --plotfile "$run_dir/plt00000" \
  --uref 2.0 \
  --zref 10.0 \
  --z0 0.03 \
  | tee "$log_dir/validation.log"

echo "[codex-bfs-loglaw] PASS; logs: $log_dir"
