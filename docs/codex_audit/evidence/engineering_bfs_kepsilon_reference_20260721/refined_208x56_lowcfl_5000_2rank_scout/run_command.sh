#!/usr/bin/env bash
set -euo pipefail
cd /home/cj/my-pele/docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/refined_208x56_lowcfl_5000_2rank_scout
mpirun --oversubscribe -np 2 /home/cj/my-pele/examples/engineering/backward_facing_step/PeleLMeX2d.gnu.MPI.ex \
  /home/cj/my-pele/examples/engineering/backward_facing_step/input.yaml \
  amr.n_cell="208 56" \
  amr.max_grid_size=256 \
  amr.max_step=5000 \
  amr.stop_time=0.5 \
  amr.cfl=0.05 \
  amr.dt_shrink=0.001 \
  amr.plot_int=500 \
  amr.check_int=-1 \
  amr.plot_file=plt_ref \
  amr.check_file=chk_ref
