#!/usr/bin/env bash
set -uo pipefail
cd /home/cj/my-pele
base="docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/ebwall_cutcell_4rank_1000_20260723"
echo "START $(date -Is)" > "$base/status.txt"
(
  cd "$base"
  mpirun -np 4 /home/cj/my-pele/examples/engineering/backward_facing_step/codex_bfs_ebwall2d.gnu.MPI.ex /home/cj/my-pele/examples/engineering/backward_facing_step/input.yaml \
    amr.n_cell='208 56 1' \
    amr.max_level=0 \
    amr.max_grid_size='208 56 1' \
    amr.blocking_factor='8 8 1' \
    amr.plot_int=250 \
    amr.check_int=-1 \
    amr.max_step=1000 \
    amr.stop_time=0.15 \
    max_step=1000 \
    stop_time=0.15 \
    peleLM.cfl=0.05 \
    peleLM.init_shrink=0.001 \
    peleLM.dt_shrink=0.001 \
    amrex.abort_on_unused_inputs=0 \
    > run.log 2>&1
)
rc=$?
echo "$rc" > "$base/run.rc"
echo "RUN_RC $rc $(date -Is)" >> "$base/status.txt"
plot=$(find "$base" -maxdepth 1 -type d -name 'plt*' | sort | tail -1)
echo "PLOT $plot" >> "$base/status.txt"
if [ -n "$plot" ]; then
  python3 tools/validate_bfs.py "$plot" > "$base/validate_bfs.log" 2>&1
  vrc=$?
  echo "$vrc" > "$base/validate_bfs.rc"
  echo "VALIDATE_RC $vrc $(date -Is)" >> "$base/status.txt"
fi
