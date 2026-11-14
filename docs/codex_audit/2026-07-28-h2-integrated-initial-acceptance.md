# 2026-07-28 H2 Integrated Initial Engineering Acceptance

The engineering acceptance boundary was clarified: the current integrated H2
engineering case can be considered initially acceptable if it demonstrates
leakage, dispersion, ignition, sustained reacting fire, physical conservation
sanity, and stable CPU/GPU/MPI execution in a complex-obstacle open-area scene.
Real CAD ingestion, exact external plume data, and calibrated fire/blast
consequence validation are explicitly deferred for later user-assisted work.

## Result

`tools/write_engineering_h2_integrated_initial_acceptance_report.py` now encodes
that initial acceptance boundary as a machine-checkable report.

Generated evidence:

- `docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728/h2_integrated_initial_acceptance_report.json`
- `docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728/h2_integrated_initial_acceptance_report.md`

Verified status:

- `PASS-H2-INTEGRATED-ENGINEERING-INITIAL-ACCEPTANCE`
- `clears_initial_integrated_engineering_goal = true`
- `clears_full_production_certification = false`

## Evidence Aggregated

- Complex obstacle leakage/dispersion/fire screening:
  `engineering_h2_pipe_rack_gpu_fire_obstacle_20260727`
- Large AMR engineering acceptance and conservation:
  `engineering_h2_large_acceptance_20260727`
- Single-GPU direct reacting fire, 2000 steps:
  `engineering_h2_pipe_rack_direct_reacting_cuda_2000step_20260727`
- 2-rank MPI+CUDA direct reacting fire, 2000 steps:
  `engineering_h2_pipe_rack_direct_reacting_mpi_cuda_2000step_20260727`
- Large-grid single-GPU and MPI+CUDA reacting checks:
  `engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_20260727`
  and `engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_20260727`
- MPI+CUDA checkpoint/restart reacting-fire continuity:
  `engineering_h2_pipe_rack_direct_reacting_mpi_cuda_restart_20260727`
- Fire consequence formula traceability:
  `engineering_h2_fire_consequence_traceability_20260727`

## Deferred

The report deliberately does not close:

- real plant CAD import, cleanup, and boundary tagging;
- external SBEPV5/field-test plume agreement;
- calibrated radiation/overpressure/fire consequence validation;
- production GPU scaling beyond the current 2-rank MPI+CUDA gates.
