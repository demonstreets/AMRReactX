# Checkpoint: Engineering H2 Hybrid CFD Scout

Date: 2026-07-20
Generated UTC: 2026-07-20T08:12:10+00:00

## What changed

- Added and verified a real interactive H2 open-domain AMR hybrid MPI+OpenMP CFD scout wrapper: `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_hybrid.sh`.
- Fixed hybrid-capable H2 plume-history execution by assigning the generated PeleLMeX executable path before launch.
- Parameterized plan-AMR comparison plume-plane thresholds so the short hybrid scout can enforce a positive H2 cloud without inheriting long-smoke plane-count assumptions.
- Added `tools/write_engineering_h2_hybrid_cfd_scout_report.py` to package the hybrid CFD scout into project-local JSON/Markdown evidence with copied small logs/CSVs, input files, plot Header hashes, and verifier checks.
- Wired the hybrid CFD scout into `tools/write_engineering_production_scorecard.py` and `tools/verify_engineering_h2_production_evidence.sh`.
- Refreshed engineering readiness docs, smoke matrix, scorecard, and production evidence verification report.

## Main run

```bash
CODEX_H2_LEAK_PLAN_AMR_HYBRID_LOG_DIR=/tmp/codex_h2_leak_open_domain_plan_amr_hybrid_20260720_rerun5 CODEX_H2_LEAK_PLAN_AMR_HYBRID_RANKS=4 CODEX_H2_LEAK_PLAN_AMR_HYBRID_THREADS=2 CODEX_H2_LEAK_PLAN_AMR_MAX_STEP=40 CODEX_H2_LEAK_PLAN_AMR_PLOT_INT=20 CODEX_H2_LEAK_PLAN_AMR_MIN_PLOTFILES=3 CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES=3 OMP_PROC_BIND=spread OMP_PLACES=cores RUN_TIMEOUT=1200 JOBS=4 tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_hybrid.sh
```

Result: `PASS-HYBRID-CFD-SCOUT` with 4 MPI ranks x 2 OpenMP threads, `max_step=40`, baseline and AMR each writing 3 plotfiles, AMR finest level 1, 4 fine FABs, `cloud_rel_diff=4.46428599e-02`, `peak_rel_diff=4.55934286e-02`, `centroid_abs_diff=1.20702100e-04`, `downstream_abs_diff=8.84127700e-03`, `mean_ncells_ratio=1.4`, and `advance_seconds_ratio=1.57272302`.

The run is interactive `mpirun`, not scheduler-managed. The MPI implementation reports `mpi_thread_support_level_0`; this scout does not request MPI calls from multiple OpenMP threads, so the warning is tracked and accepted for this gate.

## Evidence

- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.md`
- `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`

## Verification

- `python3 -m py_compile tools/write_engineering_h2_hybrid_cfd_scout_report.py tools/write_engineering_production_scorecard.py`: PASS
- `bash -n tools/codex_smoke_engineering_h2_leak_plume_history.sh tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_hybrid.sh tools/verify_engineering_h2_production_evidence.sh`: PASS
- `python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json`: VERIFY-PASS
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`: VERIFY-PASS, `functional=92.1`, `production=71.7`, `status=NOT_PRODUCTION_READY`
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=970`
- `tools/verify_engineering_h2_production_evidence.sh`: PASS, CTest `22/22 PASS`
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE tools/verify_engineering_h2_production_evidence.sh`: PASS

## Current engineering status

Machine-checked engineering scorecard is now `functional=92.1%` and `production_credibility=71.7%`, still `NOT_PRODUCTION_READY`.

The remaining production blockers are unchanged in kind: completed scheduler-managed campaign evidence, larger/full-duration production-size campaigns, stronger hybrid scaling, real-CAD/industrial geometry campaigns, reference-data agreement, and calibrated fire/radiation/overpressure validation.
