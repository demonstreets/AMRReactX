#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

evidence_root=${CODEX_ACADEMIC_WENO5_CONVERGENCE_LOG_DIR:-docs/codex_audit/evidence/academic_weno5_convergence_validation_20260729}
build_dir=${CODEX_ACADEMIC_WENO5_CONVERGENCE_BUILD_DIR:-build-codex-smoke}
jobs=${JOBS:-4}

mkdir -p "$evidence_root"

cmake_log="$evidence_root/cmake.log"
build_log="$evidence_root/build.log"
ctest_list_log="$evidence_root/ctest_list.log"
ctest_log="$evidence_root/ctest_weno_verbose.log"
case_summary="$evidence_root/case_summary.json"

cmake -S . -B "$build_dir" -DMYPELE_ENABLE_UNIT_SMOKE=ON >"$cmake_log" 2>&1
cmake --build "$build_dir" -j "$jobs" >"$build_log" 2>&1
ctest --test-dir "$build_dir" -N >"$ctest_list_log" 2>&1

set +e
ctest --test-dir "$build_dir" -V -R 'weno5_smoke|pelec_weno_smoke' >"$ctest_log" 2>&1
ctest_rc=$?
set -e

python3 - "$case_summary" "$cmake_log" "$build_log" "$ctest_list_log" "$ctest_log" "$ctest_rc" "$build_dir" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

out, cmake_log, build_log, ctest_list_log, ctest_log, ctest_rc, build_dir = sys.argv[1:]
data = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "build_dir": build_dir,
    "cmake_log": cmake_log,
    "build_log": build_log,
    "ctest_list_log": ctest_list_log,
    "ctest_log": ctest_log,
    "ctest_returncode": int(ctest_rc),
    "required_tests": ["weno5_smoke", "pelec_weno_smoke"],
}
Path(out).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

python3 tools/write_academic_weno5_convergence_validation_report.py \
  --case-summary "$case_summary"
python3 tools/write_academic_weno5_convergence_validation_report.py \
  --verify-json "$evidence_root/academic_weno5_convergence_validation_report.json"

if [[ "$ctest_rc" -ne 0 ]]; then
  echo "[academic-weno5-convergence] FAIL ctest returncode=$ctest_rc; see $ctest_log" >&2
  exit "$ctest_rc"
fi

echo "[academic-weno5-convergence] PASS; evidence: $evidence_root"
