# Checkpoint: Engineering H2 fire consequence screening metrics

Date: 2026-07-20 UTC
Repo: `${REPO_ROOT}`

## What changed

- Added `tools/write_engineering_h2_fire_consequence_metrics_report.py`.
- Generated a project-local H2 fire/radiation/overpressure screening report under `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/`.
- Connected the fire consequence screening report to `tools/write_engineering_production_scorecard.py` as first-class evidence for `ignition_fire_consequence_chain`.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the new scorecard numbers, evidence path, screening assumptions, and limitations.

## Evidence inputs

The screening report links existing verified evidence rather than reading raw plotfiles:

- Ignition report: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json`
- 8-rank AMR hazard summary: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/files/amr/hazard_summary.log`
- 8-rank AMR hazard time series: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/files/amr/hazard_timeseries.log`
- 8-rank AMR hazard planes: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/files/amr/hazard_planes.log`

Report:

- JSON: `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json`
- Markdown: `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.md`
- Status: `PASS-SCREENING`
- Scope: `engineering_screening_not_calibrated`

## Key metrics

- Flammable-cloud H2 mass: `2.23883994e-04 kg`
- Flammable-cloud volume: `2.46582031e-02 m^3`
- Inferred H2 mass rate: `2.000250508333333e-03 kg/s`
- Source-limited heat release: `2.40030061e+05 W`
- Flammable-cloud energy: `2.686607928e+04 J`
- Source-limited radiative power with `radiative_fraction=0.15`: `3.600450915e+04 W`
- TNT-equivalent screening mass with `blast_efficiency=0.03`: `1.9263441166347993e-04 kg`
- Max screening radiation flux: `2.86514780e+03 W/m^2`
- Max screening overpressure: `2.44388282e-01 kPa`

## Model limitations

- Radiation is an isotropic point-source screening metric, not a flame-shape/view-factor/wall/shielding/radiative-transfer model.
- Overpressure is TNT-equivalent screening, not a calibrated deflagration, congestion, ventilation, flame acceleration, or detonation model.
- Current values are smoke/scout-scale values from the maintained H2 production-mesh evidence and are not large-storage-tank accident magnitudes.
- This improves the reportable consequence chain, but does not close the `calibrated_fire_radiation_overpressure_metrics_missing` blocker.

## Scorecard

Regenerated scorecard:

- JSON: `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- Status: `NOT_PRODUCTION_READY`
- Engineering functional coverage: `89.3%`
- Engineering production credibility: `68.3%`

## Verification run

Commands and observed results:

- `python3 -m py_compile tools/write_engineering_h2_fire_consequence_metrics_report.py tools/write_engineering_production_scorecard.py`: silent success
- `python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --verify-json docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json`: `VERIFY-PASS ... status=PASS-SCREENING cloud_mass=2.23883994e-04 max_flux=2.86514780e+03 max_overpressure=2.44388282e-01`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`: `VERIFY-PASS ... functional=89.3 production=68.3`
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=964`
- `ctest --test-dir build-codex-smoke --output-on-failure`: `100% tests passed, 0 tests failed out of 22`

## Remaining production gaps

- Scheduler-managed H2 campaign outputs remain missing while SLURM control-plane probes are not producing a PASS run.
- Overnight/full-duration H2 leak stability remains missing.
- Full production-size hazardous-release campaigns remain missing.
- External plume/hazard/fire reference-data agreement remains missing.
- Real CAD cleanup and large-layout dynamic AMR campaigns remain missing.
- Calibrated fire radiation/overpressure metrics remain missing.
