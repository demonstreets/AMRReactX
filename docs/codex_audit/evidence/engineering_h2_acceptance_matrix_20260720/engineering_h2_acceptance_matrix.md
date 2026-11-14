# Engineering H2 Acceptance Matrix

Status: `PASS-PRODUCTION-MATRIX`

## Summary

- Rows: `7`
- Pass-like rows: `7`
- Not-ready rows: `[]`

## Matrix

| Row | Status | Evidence level | Main gaps |
| --- | --- | --- | --- |
| `dispersion_core` | `PASS-SMOKE` | `smoke_campaign` | smoke-scale internal campaign only; external reference-data agreement and production-size case matrix remain open |
| `source_physics` | `PASS-SMOKE` | `smoke_campaign` | smoke-scale internal campaign only; external reference-data agreement and production-size case matrix remain open |
| `geometry_obstacles` | `PASS-SMOKE` | `smoke_campaign` | smoke-scale internal campaign only; external reference-data agreement and production-size case matrix remain open |
| `amr_mpi_smoke` | `PASS-SMOKE` | `smoke_campaign` | smoke-scale internal campaign only; external reference-data agreement and production-size case matrix remain open |
| `production_mesh_amr_mpi_stability` | `PASS-SCOUT` | `production_mesh_scout` | 1200-step production-mesh, 8-rank/600-step stability, and 16-rank short scouts exist; scheduler-managed overnight/full-duration production campaigns remain open |
| `ignition_fire_consequence_screening` | `PASS-SCREENING` | `screening_not_calibrated` | screening consequence metrics exist; calibrated radiation, overpressure, flame-speed, and reference fire validation remain open |
| `scheduler_managed_campaign` | `PASS` | `scheduler_allocation` | none recorded |

## Evidence Files

- `release_pack`: `docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json` sha256 `012adc15d0dff150`
- `production_mesh_1200step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json` sha256 `1d0f9891d1ef7700`
- `production_mesh_8rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json` sha256 `6b4c05d1d48a0205`
- `production_mesh_16rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json` sha256 `976464cb31a86f6c`
- `production_mesh_8rank_600step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json` sha256 `76cf3ad46f4f9720`
- `ignition_consequence_report`: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json` sha256 `3f1eb940bc75c59e`
- `fire_consequence_metrics_report`: `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json` sha256 `f1e4bb21fb6166d3`
- `scheduler_run_report`: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json` sha256 `262da4919c55fc24`
