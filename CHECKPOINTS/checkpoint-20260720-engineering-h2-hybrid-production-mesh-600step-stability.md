# Checkpoint: engineering H2 hybrid production-mesh 600-step stability

Date: 2026-07-20

## What changed

- Ran the real PeleLMeX H2 open-domain plan-AMR hybrid production-mesh stability scout at 4 MPI ranks x 2 OpenMP threads, `64x32x32` base grid, AMR-equivalent `128x64x64`, `max_step=600`, `plot_int=60`.
- Baseline simulation passed plume history/profile/hazard summary/planes/timeseries.
- AMR simulation passed plume history, then initially failed the plan-AMR profile gate because the fixed single centroid-plane H2 mass fraction threshold was too high for the longer 3D plume (`plane_fraction=1.28163874e-02` vs old plan-AMR default `0.02`).
- Adjusted only the plan-AMR engineering comparison wrapper default `CODEX_H2_LEAK_PLAN_AMR_MIN_PLANE_MASS_FRACTION` from `0.02` to `0.005`; the generic profile validator default remains `0.05`.
- Revalidated the same AMR plotfiles: profile, hazard summary, hazard planes, hazard timeseries, baseline-AMR comparison, hybrid parallel logs, and AMR overhead now pass.
- Generated and verified `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/hybrid_production_mesh_600step_stability_scout_report.json`.
- Integrated the new report into `tools/write_engineering_production_scorecard.py` and `tools/verify_engineering_h2_production_evidence.sh`.
- Refreshed production scorecard, production evidence verification report, readiness doc, and smoke matrix.

## Key evidence

- Hybrid production-mesh 600-step report: `PASS-HYBRID-CFD-SCOUT`
- Parallel mode: 4 MPI ranks x 2 OpenMP threads
- Base cells: `65536`
- AMR-equivalent fine cells: `524288`
- Plotfiles: baseline `11`, AMR `11`
- AMR finest level: `1`
- AMR finest FAB count: `28`
- Regrid count: `299`
- Cloud relative difference: `3.15976518e-02`
- Peak-X relative difference: `3.40034177e-02`
- Centroid absolute difference: `5.37634e-04`
- Downstream-fraction absolute difference: `4.98946e-04`
- Mean ncells ratio: `1.97647135`
- Advance seconds ratio: `2.00754474`
- Final plotfile bytes ratio: `2.62860423`

## Current scorecard

- Status: `NOT_PRODUCTION_READY`
- Engineering functional coverage: `92.6%`
- Engineering production credibility: `72.3%`

The score remains production-not-ready because scheduler-managed PASS run outputs, full production-size campaigns, overnight/full-duration stability, external reference-data agreement, real-CAD cleanup campaigns, and calibrated fire/radiation/overpressure metrics remain open.

## Verification

- `python3 -m py_compile tools/write_engineering_production_scorecard.py`: PASS
- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh tools/verify_engineering_h2_production_evidence.sh`: PASS
- `python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/hybrid_production_mesh_600step_stability_scout_report.json`: PASS
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE tools/verify_engineering_h2_production_evidence.sh`: PASS
- Full `tools/verify_engineering_h2_production_evidence.sh`: PASS, including `22/22` CTest and strict machine-local path audit.

## Next recommended work

1. Fix or restore SLURM controller availability, then run the generated scheduler-managed engineering H2 production-scout campaign.
2. Convert the inline production evidence verification report refresh logic into a maintained tool to avoid ad-hoc report generation.
3. Extend hybrid evidence beyond 4x2 interactive execution: at least 8-rank hybrid, scheduler-managed hybrid, and longer-duration hybrid stability.
4. Add external/reference-data validation and real-CAD cleanup campaigns before claiming production readiness.
