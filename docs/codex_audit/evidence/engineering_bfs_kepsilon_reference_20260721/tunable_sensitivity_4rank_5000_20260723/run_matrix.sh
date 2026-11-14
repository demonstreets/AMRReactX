#!/usr/bin/env bash
set -uo pipefail
cd /home/cj/my-pele
base="docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/tunable_sensitivity_4rank_5000_20260723"
exe="examples/engineering/backward_facing_step/codex_bfs_tunable2d.gnu.MPI.ex"
inputs="examples/engineering/backward_facing_step/input.yaml"
validator="tools/validate_bfs.py"
summary="$base/summary.tsv"
status="$base/status.txt"
printf 'case\tTI\tL\trc\treattach_x_h\trecirc_h\tverdict\tplot\n' > "$summary"
echo "START $(date -Is)" > "$status"
run_case() {
  local name="$1" ti="$2" len="$3"
  local run_dir="$base/$name"
  case "$run_dir" in
    docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/tunable_sensitivity_4rank_5000_20260723/*) ;;
    *) echo "unsafe run_dir $run_dir" >&2; exit 2;;
  esac
  rm -rf "$run_dir"
  mkdir -p "$run_dir"
  echo "RUN $name TI=$ti L=$len $(date -Is)" >> "$status"
  (
    cd "$run_dir"
    mpirun -np 4 ../../../../../../examples/engineering/backward_facing_step/codex_bfs_tunable2d.gnu.MPI.ex ../../../../../../examples/engineering/backward_facing_step/input.yaml \
      amr.n_cell='208 56 1' \
      amr.max_level=0 \
      amr.max_grid_size='208 56 1' \
      amr.blocking_factor='8 8 1' \
      amr.plot_int=500 \
      amr.check_int=-1 \
      max_step=5000 \
      stop_time=1.0 \
      peleLM.cfl=0.05 \
      peleLM.init_shrink=0.001 \
      peleLM.dt_shrink=0.001 \
      peleLM.ke_inlet_TI="$ti" \
      peleLM.ke_inlet_L="$len" \
      amrex.abort_on_unused_inputs=0 \
      > run.log 2>&1
  )
  local rc=$?
  echo "$rc" > "$run_dir/run.rc"
  local plot=""
  plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt_ref*' | sort | tail -1)
  local bx="NA" br="NA" verdict="NO_PLOT"
  if [ -n "$plot" ]; then
    python3 "$validator" "$plot" > "$run_dir/validate_bfs.log" 2>&1
    local vrc=$?
    verdict="FAIL"
    if [ "$vrc" = "0" ]; then verdict="PASS"; fi
    bx=$(python3 - "$run_dir/validate_bfs.log" <<'PY'
import json, re, sys, pathlib
text=pathlib.Path(sys.argv[1]).read_text(errors='replace')
vals=re.findall(r'\{[\s\S]*?\}', text)
if vals:
    d=json.loads(vals[-1]); print(d.get('reattachment_x_h','NA'))
else: print('NA')
PY
)
    br=$(python3 - "$run_dir/validate_bfs.log" <<'PY'
import json, re, sys, pathlib
text=pathlib.Path(sys.argv[1]).read_text(errors='replace')
vals=re.findall(r'\{[\s\S]*?\}', text)
if vals:
    d=json.loads(vals[-1]); print(d.get('recirculation_length_h','NA'))
else: print('NA')
PY
)
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$ti" "$len" "$rc" "$bx" "$br" "$verdict" "$plot" >> "$summary"
  echo "DONE $name rc=$rc XRH=$bx recirc=$br verdict=$verdict $(date -Is)" >> "$status"
}
run_case baseline_TI005_L1H 0.05 0.0381
run_case lowTI001_L1H 0.01 0.0381
run_case lowTI0005_L1H 0.005 0.0381
run_case TI001_L4H 0.01 0.1524
echo "END $(date -Is)" >> "$status"
