# Checkpoint: Engineering H2 production-mesh scout

Date: 2026-07-20 UTC
Repo: `${REPO_ROOT}`

## What changed

- Fixed an AMReX FAB binary-reader edge case in `tools/amrex_reader.py`: FAB header parsing now treats only spaces/tabs as optional header whitespace so a binary payload that begins with newline byte `0x0a` is not consumed as text whitespace.
- Added/extended `tools/test_amrex_reader_multibox.py` coverage for the newline-leading binary payload case. The smoke now reports `newline_payload=1`.
- Packaged the new H2 production-mesh scout under `docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/`.
- Updated `tools/write_engineering_production_scorecard.py` to ingest the production-mesh scout as first-class evidence.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` so the progress numbers and limitations match the current evidence.

## New H2 production-mesh scout evidence

Command family: `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh` with 4 MPI ranks, `max_step=120`, `plot_int=30`, and `CODEX_H2_LEAK_PLAN_AMR_N_CELL="64 32 32"`.

Report: `docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json`

Key metrics:

- Status: `PASS-SCOUT`
- Ranks: `4`
- Baseline grid: `64x32x32`, `65536` cells
- AMR equivalent fine grid: `128x64x64`, `524288` cells
- Plotfiles: `5` baseline, `5` AMR
- AMR finest level: `1`
- AMR FABs: `[(0, 16), (1, 12)]`
- `cloud_rel_diff=3.80952381e-02`
- `peak_rel_diff=4.31073584e-02`
- `mean_ncells_ratio=1.41002604`
- `advance_seconds_ratio=1.74036467`

This is stronger than the earlier `48x24x24` production-scale scout, but remains a scout rather than a full production-size/reference-data/scheduler-managed campaign.

## Scorecard

Regenerated scorecard:

- JSON: `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- Status: `NOT_PRODUCTION_READY`
- Engineering functional coverage: `88.6%`
- Engineering production credibility: `66.6%`

Interpretation: the H2 engineering leak/AMR function path is now quite broad, but production credibility is intentionally capped by missing scheduler-run outputs, full production-size campaigns, overnight/full-duration stability, external reference-data agreement, real-CAD cleanup, and calibrated fire/radiation/overpressure metrics.

## Verification run

Commands and observed results:

- `python3 -m py_compile tools/amrex_reader.py tools/write_engineering_h2_production_scale_scout_report.py tools/write_engineering_production_scorecard.py`: silent success
- `python3 tools/test_amrex_reader_multibox.py`: `amrex_reader_multibox_smoke PASS ... newline_payload=1`
- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh`: silent success
- `python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json`: `VERIFY-PASS ... status=PASS-SCOUT ranks=4 base_cells=65536 fine_cells=524288`
- `python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/long_stability_scout_report.json`: `VERIFY-PASS ... status=PASS-STABILITY ranks=4 base_cells=27648 fine_cells=221184`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`: `VERIFY-PASS ... functional=88.6 production=66.6`
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=963`
- `ctest --test-dir build-codex-smoke --output-on-failure`: `100% tests passed, 0 tests failed out of 22`

## Remaining engineering-production gaps

- Full scheduler-managed SLURM campaign still not proven in the current control-plane state.
- Overnight/full-duration H2 leak stability remains missing; current long-stability evidence is 300-step scout only.
- Larger MPI/rank scaling and memory-pressure sweeps remain open.
- External reference-data plume/hazard agreement remains missing.
- Real CAD cleanup and large tank-farm dynamic AMR campaigns remain open.
- Fire/radiation/overpressure calibrated consequence metrics remain open.
