# DataverseNO AMR Source Projection Implementation

Status: `PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION`

## Summary

- Implementation ready: `True`
- Framework owner mask: `True`
- Coarse covered-cell user delta removed: `True`
- Non-user external sources preserved: `True`
- MPI CPU build verified: `True`
- MPI CUDA source compile verified: `True`
- MPI CUDA linked executable: `True`
- MPI CUDA reproducible build entrypoint: `True`
- MPI CUDA build uses CUDA 12.6: `True`
- MPI CUDA build uses local SUNDIALS CUDA: `True`
- MPI CUDA rebuild blocked by toolkit version: `False`
- MPI CUDA rebuild blocked by missing SUNDIALS: `False`
- Strict external plume blocker cleared: `False`

## Checks

- `user_source_hook_present`: `True`
- `coarse_level_guard_present`: `True`
- `pre_user_source_snapshot_present`: `True`
- `fine_mask_constructed`: `True`
- `fine_mask_uses_next_level_grids`: `True`
- `fine_mask_uses_ref_ratio`: `True`
- `mask_has_owner_semantics`: `True`
- `restores_non_user_sources_on_fine_covered_coarse_cells`: `True`
- `gpu_parallel_restore_present`: `True`
- `restore_synchronized`: `True`

## Notes

- User-defined external sources are still authored through the problem hook.
- For coarse levels covered by a finer AMR level, the framework snapshots ext_src before the user hook and restores those cells after the hook.
- This preserves pre-existing non-user external sources while preventing user source double counting across coarse/fine overlap.
- This implementation satisfies the AMR projection precondition, but a longer DataverseNO plume agreement run is still required for strict external-source credit.
