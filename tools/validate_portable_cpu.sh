#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
build=${1:-"${TMPDIR:-/tmp}/my-pele-portable-build"}
jobs=${JOBS:-4}
mkdir -p "$build/logs" "$build/runs/pelec" "$build/runs/pelelmex"
python3 "$root/tools/restore_portable_inputs.py" > "$build/logs/restore-inputs.log"
python3 "$root/tools/relocate_legacy_paths.py" --apply > "$build/logs/relocate.json"
cmake -S "$root" -B "$build/unit" -DMYPELE_ENABLE_UNIT_SMOKE=ON > "$build/logs/unit-config.log" 2>&1
cmake --build "$build/unit" -j "$jobs" > "$build/logs/unit-build.log" 2>&1
ctest --test-dir "$build/unit" --output-on-failure > "$build/logs/unit-test.log" 2>&1
for solver in PeleC PeleLMeX; do
  case $solver in
    PeleC) target=PeleC-Sod; case_dir=Sod; input=sod-1.inp; run=pelec ;;
    PeleLMeX) target=PeleLMeX-PeriodicCases; case_dir=PeriodicCases; input=covo-2d.inp; run=pelelmex ;;
  esac
  cmake -S "$root/external/$solver" -B "$build/$run" \
    -DPELE_DIM=2 -DPELE_ENABLE_MPI=OFF -DPELE_ENABLE_CUDA=OFF \
    -DPELE_ENABLE_PARTICLES=OFF -DCMAKE_BUILD_TYPE=Release > "$build/logs/$run-config.log" 2>&1
  cmake --build "$build/$run" --target "$target" -j "$jobs" > "$build/logs/$run-build.log" 2>&1
  exe="$build/$run/Exec/RegTests/$case_dir/$target"
  test -x "$exe"
  (cd "$build/runs/$run"; "$exe" "$root/external/$solver/Exec/RegTests/$case_dir/$input" \
      max_step=5 amr.max_step=5 amr.n_cell='32 32' amr.max_level=0 \
      amr.plot_int=-1 amr.check_int=-1) > "$build/logs/$run-run.log" 2>&1
done
python3 - "$build" <<'PY'
from pathlib import Path
import json,re,sys
r=Path(sys.argv[1]);result={}
for name in ['pelec','pelelmex']:
 text=(r/'logs'/f'{name}-run.log').read_text()
 if re.search(r'(?i)\b(?:nan|segmentation fault|sigsegv|amrex::abort|floating point exception)\b',text):
  raise SystemExit(f'{name}: fatal/nonfinite marker in log')
 result[name]={'process_exit':0,'fatal_marker_scan':'PASS','scope':'five-step nonreacting CPU smoke; not physical or reactive validation'}
(r/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
PY
