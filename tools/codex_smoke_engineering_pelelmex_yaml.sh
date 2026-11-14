#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/bfs_kepsilon"
build_dir="$repo_root/build-codex-smoke"
converter="$build_dir/my_pele_yaml_to_parmparse"
input_yaml="$case_dir/input.codex_yaml_smoke.yaml"
profile_yaml="$case_dir/input.codex_yaml_profile_smoke.yaml"
generated_input="${CODEX_GENERATED_INPUT:-/tmp/codex_bfs_from_yaml.inputs}"
profile_input="${CODEX_PROFILE_INPUT:-/tmp/codex_bfs_profile_from_yaml.inputs}"
exe="$case_dir/codex_bfs_cpu2d.gnu.ex"

echo "[codex-smoke-yaml] configuring converter"
cmake -S "$repo_root" -B "$build_dir" -DMYPELE_ENABLE_UNIT_SMOKE=ON >/dev/null
cmake --build "$build_dir" --target my_pele_yaml_to_parmparse -j "${JOBS:-4}" >/dev/null

echo "[codex-smoke-yaml] generating ParmParse input from true YAML"
"$converter" "$input_yaml" "$generated_input" --dim 2 --solver-only

grep -q '^geometry.prob_lo = 0 0$' "$generated_input"
grep -q '^amr.n_cell = 80 8$' "$generated_input"
grep -q '^peleLM.les_model = kepsilon$' "$generated_input"
grep -q '^peleLM.lo_bc = Inflow NoSlipWallAdiab$' "$generated_input"
grep -q '^peleLM.hi_bc = Outflow SlipWallAdiab$' "$generated_input"
grep -q '^prob.meanFlowMag = 2$' "$generated_input"
grep -q '^prob.windProfileType = 0$' "$generated_input"

echo "[codex-smoke-yaml] generating log-law wind-profile input from true YAML"
"$converter" "$profile_yaml" "$profile_input" --dim 2 --solver-only
grep -q '^prob.meanFlowMag = 2$' "$profile_input"
grep -q '^prob.windProfileType = 1$' "$profile_input"
grep -q '^prob.windRefHeight = 10$' "$profile_input"
grep -q '^prob.windRoughnessLength = 0.029999999999999999$' "$profile_input"

echo "[codex-smoke-yaml] building PeleLMeX bfs_kepsilon CPU baseline"
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_bfs_cpu >/dev/null

echo "[codex-smoke-yaml] running generated-input PeleLMeX bfs_kepsilon baseline"
cd "$case_dir"
run_log="${CODEX_RUN_LOG:-/tmp/codex_bfs_from_yaml_run.log}"
timeout "${RUN_TIMEOUT:-120}" "$exe" "$generated_input" | tee "$run_log"
grep -q "Velocity: 2 0" "$run_log"
if grep -q "Unused ParmParse Variables" "$run_log"; then
  echo "[codex-smoke-yaml] generated input left unused ParmParse variables" >&2
  exit 1
fi

echo "[codex-smoke-yaml] running log-law wind-profile PeleLMeX bfs_kepsilon baseline"
profile_run_log="${CODEX_PROFILE_RUN_LOG:-/tmp/codex_bfs_profile_from_yaml_run.log}"
timeout "${RUN_TIMEOUT:-120}" "$exe" "$profile_input" | tee "$profile_run_log"
grep -q "Velocity: 0.3922899764 0" "$profile_run_log"
if grep -q "Unused ParmParse Variables" "$profile_run_log"; then
  echo "[codex-smoke-yaml] generated wind-profile input left unused ParmParse variables" >&2
  exit 1
fi
