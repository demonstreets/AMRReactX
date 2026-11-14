#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
exe="$case_dir/codex_h2_leak3d.gnu.ex"
log_dir="${CODEX_H2_LEAK_STL_BAD_MESH_LOG_DIR:-/tmp/codex_h2_leak_stl_bad_mesh_guard_$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$log_dir/run"
run_log="$log_dir/run.log"
input_src="$case_dir/input.codex_stl_obstacle_smoke"
input_dst="$run_dir/input.codex_stl_bad_mesh_guard"
bad_stl="$run_dir/codex_degenerate_triangle.stl"

mkdir -p "$run_dir"
rm -rf "$run_dir"/plt* "$run_log"

printf '[codex-smoke] building PeleLMeX h2_leak_3d STL bad-mesh guard\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_h2_leak USE_MPI=FALSE USE_EB=TRUE

cp "$exe" "$run_dir/"
cat > "$bad_stl" <<'EOFSTL'
solid codex_degenerate_triangle
  facet normal 0 0 1
    outer loop
      vertex 0 0 0
      vertex 0 0 0
      vertex 0 0 0
    endloop
  endfacet
endsolid codex_degenerate_triangle
EOFSTL
python3 - "$input_src" "$input_dst" <<'PYINPUT'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text()
text = text.replace('prob.obstacle_stl_file = cube_obstacle.stl',
                    'prob.obstacle_stl_file = codex_degenerate_triangle.stl')
dst.write_text(text)
PYINPUT

printf '[codex-smoke] running expected-fail STL bad-mesh guard\n'
cd "$run_dir"
set +e
timeout "${RUN_TIMEOUT:-120}" "./$(basename "$exe")" "$(basename "$input_dst")" > "$run_log" 2>&1
rc=$?
set -e

if [ "$rc" -eq 0 ]; then
  echo '[codex-smoke] FAIL: degenerate STL case unexpectedly succeeded' >&2
  exit 1
fi
if [ "$rc" -eq 124 ]; then
  echo '[codex-smoke] FAIL: degenerate STL guard timed out instead of aborting clearly' >&2
  exit 1
fi
if ! grep -q "buildFromSTL: encountered degenerate STL triangle in 'codex_degenerate_triangle.stl'" "$run_log"; then
  echo '[codex-smoke] FAIL: missing explicit degenerate STL triangle diagnostic' >&2
  tail -80 "$run_log" >&2
  exit 1
fi
if grep -q 'Writing plotfile' "$run_log"; then
  echo '[codex-smoke] FAIL: degenerate STL guard advanced far enough to write a plotfile' >&2
  tail -80 "$run_log" >&2
  exit 1
fi

printf '[codex-smoke] PASS h2_leak STL bad-mesh guard log_dir=%s rc=%s\n' "$log_dir" "$rc"
