# Checkpoint: Engineering H2 Hybrid Production-Mesh Scout

Date: 2026-07-20
Generated UTC: 2026-07-20T08:29:19+00:00

## What changed

- Ran a real 4 MPI x 2 OpenMP H2 open-domain dynamic plan-AMR PeleLMeX CFD scout on the production-mesh scout grid.
- Fixed `tools/write_engineering_h2_hybrid_cfd_scout_report.py` so `--output-json` no longer writes packaged `files/` into the default short-scout evidence root unless `--evidence-root` is explicitly set.
- Regenerated both the 40-step short hybrid CFD scout report and the new 120-step hybrid production-mesh report with independent evidence roots and hash-consistent packaged files.
- Added the hybrid production-mesh report to `tools/write_engineering_production_scorecard.py` and `tools/verify_engineering_h2_production_evidence.sh`.
- Refreshed engineering scorecard, production-evidence verification report, readiness docs, and smoke matrix.

## Main run

```bash
CODEX_H2_LEAK_PLAN_AMR_HYBRID_LOG_DIR=/tmp/codex_h2_leak_open_domain_plan_amr_hybrid_prodmesh_20260720 CODEX_H2_LEAK_PLAN_AMR_HYBRID_RANKS=4 CODEX_H2_LEAK_PLAN_AMR_HYBRID_THREADS=2 CODEX_H2_LEAK_PLAN_AMR_N_CELL="64 32 32" CODEX_H2_LEAK_PLAN_AMR_MAX_STEP=120 CODEX_H2_LEAK_PLAN_AMR_PLOT_INT=30 CODEX_H2_LEAK_PLAN_AMR_MIN_PLOTFILES=5 CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES=5 OMP_PROC_BIND=spread OMP_PLACES=cores RUN_TIMEOUT=1800 JOBS=4 tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_hybrid.sh
```

## Result

- Wrapper result: `PASS h2_leak open-domain plan-AMR hybrid validation`.
- Parallel mode: 4 MPI ranks x 2 OpenMP threads.
- Baseline grid: `64x32x32`, `65536` cells.
- AMR equivalent fine grid: `128x64x64`, `524288` cells.
- Plotfiles: 5 baseline and 5 AMR.
- AMR finest level: 1.
- AMR finest FAB count: 12.
- Regrid count: 59.
- `cloud_rel_diff=3.80952381e-02`.
- `peak_rel_diff=4.31073584e-02`.
- `centroid_abs_diff=3.15499000e-04`.
- `downstream_abs_diff=2.60922300e-03`.
- `mean_ncells_ratio=1.41002604`.
- `advance_seconds_ratio=1.61148722`.

## Evidence

- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/hybrid_production_mesh_scout_report.json`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/hybrid_production_mesh_scout_report.md`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json`
- `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`

## Verification

- `python3 -m py_compile tools/write_engineering_h2_hybrid_cfd_scout_report.py tools/write_engineering_production_scorecard.py`: PASS
- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_hybrid.sh tools/verify_engineering_h2_production_evidence.sh`: PASS
- Short hybrid CFD report: VERIFY-PASS, 4x2, `cloud_rel_diff=4.46428599e-02`, `peak_rel_diff=4.55934286e-02`
- Hybrid production-mesh report: VERIFY-PASS, 4x2, `cloud_rel_diff=3.80952381e-02`, `peak_rel_diff=4.31073584e-02`
- `python3 tools/write_engineering_production_scorecard.py --verify-json ...`: VERIFY-PASS, `functional=92.4`, `production=72.1`, `status=NOT_PRODUCTION_READY`
- `tools/verify_engineering_h2_production_evidence.sh`: PASS, CTest `22/22 PASS`
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE tools/verify_engineering_h2_production_evidence.sh`: PASS
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=970`

## Current engineering status

Machine-checked engineering scorecard is now `functional=92.4%` and `production_credibility=72.1%`, still `NOT_PRODUCTION_READY`.

The new evidence strengthens interactive hybrid MPI/OpenMP production-mesh confidence. It still does not clear the remaining production blockers: completed scheduler-managed campaign evidence, full production-size/full-duration campaigns, larger hybrid scaling, real CAD/industrial geometry campaigns, reference-data agreement, and calibrated fire/radiation/overpressure validation.
