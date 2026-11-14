#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
exe="$case_dir/codex_h2_leak3d.gnu.ex"
log_dir="${CODEX_H2_LEAK_STL_GUARD_LOG_DIR:-/tmp/codex_h2_leak_stl_geometry_guard_$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$log_dir/run"
run_log="$log_dir/run.log"
input_src="$case_dir/input.codex_stl_obstacle_smoke"
input_dst="$run_dir/input.codex_stl_outside_domain_guard"

mkdir -p "$run_dir"
rm -rf "$run_dir"/plt* "$run_log"

printf '[codex-smoke] building PeleLMeX h2_leak_3d STL geometry guard\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_h2_leak USE_MPI=FALSE USE_EB=TRUE

cp "$exe" "$run_dir/"
cp "$case_dir/cube_obstacle.stl" "$run_dir/"
python3 - "$input_src" "$input_dst" <<'PYINPUT'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text()
text = text.replace('prob.obstacle_stl_xc = 1.0', 'prob.obstacle_stl_xc = 9.0')
text = text.replace('prob.obstacle_xc = 1.0', 'prob.obstacle_xc = 9.0')
dst.write_text(text)
PYINPUT

printf '[codex-smoke] running expected-fail STL outside-domain guard\n'
cd "$run_dir"
set +e
timeout "${RUN_TIMEOUT:-120}" "./$(basename "$exe")" "$(basename "$input_dst")" > "$run_log" 2>&1
rc=$?
set -e

if [ "$rc" -eq 0 ]; then
  echo '[codex-smoke] FAIL: outside-domain STL case unexpectedly succeeded' >&2
  exit 1
fi
if [ "$rc" -eq 124 ]; then
  echo '[codex-smoke] FAIL: outside-domain STL guard timed out instead of aborting clearly' >&2
  exit 1
fi
if ! grep -q 'buildFromSTL: scaled STL bounds do not intersect the computational domain' "$run_log"; then
  echo '[codex-smoke] FAIL: missing explicit outside-domain STL bounds diagnostic' >&2
  tail -80 "$run_log" >&2
  exit 1
fi
if ! grep -q 'bounds=\[(8.9,0.4,0.4),(9.1,0.6,0.6)\]' "$run_log"; then
  echo '[codex-smoke] FAIL: missing scaled STL bounds in guard diagnostic' >&2
  tail -80 "$run_log" >&2
  exit 1
fi
if ! grep -q 'domain=\[(0,0,0),(2,1,1)\]' "$run_log"; then
  echo '[codex-smoke] FAIL: missing domain bounds in guard diagnostic' >&2
  tail -80 "$run_log" >&2
  exit 1
fi

printf '[codex-smoke] PASS h2_leak STL geometry guard log_dir=%s rc=%s\n' "$log_dir" "$rc"
