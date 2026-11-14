# Checkpoint: engineering H2 production-mesh 1200-step stability scout

Date: 2026-07-20

## Summary

Completed a 4-rank MPI H2 open-domain production-mesh 1200-step stability scout for the engineering leak-dispersion chain. The baseline and AMR solver runs reached final time 1.2 and wrote 11 plotfiles each. The AMR run used a base grid of 64x32x32 with an AMR-equivalent fine grid of 128x64x64.

## Key Evidence

- Scout root: `${SCOUT_ROOT}` = `codex_h2_leak_production_mesh_1200step_stability_scout_20260720`
- Evidence report: `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json`
- Status: `PASS-STABILITY`
- MPI ranks: `4`
- Max step: `1200`
- Plotfiles: baseline `11`, AMR `11`
- AMR finest level: `1`
- Cloud relative difference: `2.99314337e-02`
- Peak-X relative difference: `3.58285346e-02`
- Mean Ncells ratio: `2.33083984`
- Advance-seconds ratio: `2.53215280`

## Scorecard Update

Updated `tools/write_engineering_production_scorecard.py` to include the new 1200-step stability report as first-class evidence. The latest scorecard now verifies with:

- Engineering functional coverage: `90.6%`
- Engineering production credibility: `70.0%`
- Status: `NOT_PRODUCTION_READY`

The score remains blocked by scheduler-managed run outputs, full production-size campaigns, overnight/full-duration stability, reference-data agreement, real-CAD cleanup, and calibrated fire metrics.

## Validation

- `python3 -m py_compile tools/validate_h2_leak_plume_history.py tools/write_engineering_production_scorecard.py tools/write_engineering_h2_production_scale_scout_report.py`: PASS
- `bash -n tools/codex_smoke_engineering_h2_leak_plume_history.sh`: PASS
- `python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json ...1200step...json`: PASS
- `python3 tools/write_engineering_production_scorecard.py --verify-json ...scorecard.json`: PASS, `functional=90.6`, `production=70.0`
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=965`
- `ctest --test-dir build-codex-smoke --output-on-failure`: PASS, `22/22`
