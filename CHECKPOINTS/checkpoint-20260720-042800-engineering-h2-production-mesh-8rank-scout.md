# Checkpoint: Engineering H2 production-mesh 8-rank scout

Date: 2026-07-20 UTC
Repo: `${REPO_ROOT}`

## What changed

- Ran the maintained H2 open-domain dynamic plan-AMR/MPI production-mesh scout at 8 MPI ranks.
- Packaged sanitized evidence under `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/`.
- Updated `tools/write_engineering_production_scorecard.py` so the 8-rank scout is first-class evidence for the `engineering_amr_mpi_efficiency` gate.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` to distinguish 4-rank and 8-rank production-mesh scout evidence.

## New 8-rank scout evidence

Command family: `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh` with 8 MPI ranks, `max_step=120`, `plot_int=30`, and `CODEX_H2_LEAK_PLAN_AMR_N_CELL="64 32 32"`.

Report: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json`

Key metrics:

- Status: `PASS-SCOUT`
- Ranks: `8`
- Baseline grid: `64x32x32`, `65536` cells
- AMR equivalent fine grid: `128x64x64`, `524288` cells
- Plotfiles: `5` baseline, `5` AMR
- AMR finest level: `1`
- AMR FABs: `[(0, 16), (1, 12)]`
- `cloud_rel_diff=3.80952381e-02`
- `peak_rel_diff=4.31073584e-02`
- `mean_ncells_ratio=1.41002604`
- `advance_seconds_ratio=1.83771921`

The 8-rank result matches the 4-rank production-mesh hazard deltas and keeps AMR overhead within the existing scout thresholds. It improves MPI/AMR confidence but is still not a full production scaling curve or scheduler-managed allocation proof.

## Scorecard

Regenerated scorecard:

- JSON: `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- Status: `NOT_PRODUCTION_READY`
- Engineering functional coverage: `89.0%`
- Engineering production credibility: `67.5%`

The status remains blocked from production-ready because scheduler-run outputs, full production-size campaigns, overnight/full-duration stability, external reference-data agreement, real-CAD cleanup, and calibrated fire/radiation/overpressure metrics are still missing.

## Verification to run/record after this checkpoint

- `python3 -m py_compile tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `python3 tools/check_machine_local_paths.py --strict`
- `ctest --test-dir build-codex-smoke --output-on-failure`
