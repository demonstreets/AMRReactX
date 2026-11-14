# Current Disk Cleanup Plan

- Status: `AUDITED-CURRENT-DISK-CLEANUP-PLAN`
- Candidate count: `10`
- Actionable candidates: `9`
- Protected candidates: `1`
- Estimated actionable reclaim KiB: `63889240`
- Stage 1 reclaim KiB: `16901736`
- Stage 2 reclaim KiB: `40400884`
- Cleanup performed: `False`

## Candidates

- `test/gpu_correctness` size_mib=`10385.08` stage=`stage_1_lowest_risk_after_rebuild_checks` risk=`low_to_medium`
- `build-gpu2` size_mib=`4440.1` stage=`stage_1_lowest_risk_after_rebuild_checks` risk=`low_to_medium`
- `build-gpu-mpi` size_mib=`1680.42` stage=`stage_1_lowest_risk_after_rebuild_checks` risk=`low_to_medium`
- `examples/academic/bench_1gpu_znd` size_mib=`15910.21` stage=`stage_2_case_output_after_evidence_export` risk=`medium`
- `examples/academic/bench_1gpu` size_mib=`9946.81` stage=`stage_2_case_output_after_evidence_export` risk=`medium`
- `examples/academic/bench_1gpu_nn_A` size_mib=`9533.97` stage=`stage_2_case_output_after_evidence_export` risk=`medium`
- `examples/academic/bench_cpu16` size_mib=`4062.99` stage=`stage_2_case_output_after_evidence_export` risk=`medium`
- `examples/engineering/h2_leak_3d` size_mib=`4704.43` stage=`review_only` risk=`unknown_review_required`
- `examples/academic/detonation_znd_gpu` size_mib=`1727.82` stage=`review_only` risk=`unknown_review_required`
- `docs/codex_audit/evidence` size_mib=`19350.18` stage=`protect` risk=`protected_do_not_delete`

## Required Before Any Cleanup

- obtain explicit user approval for concrete paths
- run bash tools/codex_verify_current_scope.sh immediately before cleanup
- stop active CFD jobs that may write candidate paths
- preserve audit evidence and current input decks needed for reproducibility
- after cleanup, regenerate disk usage, cleanup plan, state snapshot, and PROGRESS evidence
