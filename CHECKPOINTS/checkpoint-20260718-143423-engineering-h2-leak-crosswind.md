# Checkpoint: engineering H2 leak crosswind response gate

Date: 2026-07-18

## User priority

Engineering production scenarios remain first priority. This slice targets large-scale leak/dispersion readiness by adding evidence that the maintained open-domain H2 workflow responds to lateral wind/source direction, not only streamwise wind.

## This slice

Added a maintained open-domain H2 crosswind-response smoke. The new gate compares a baseline case with `prob.wind_v = 0.0` against a crosswind case with `prob.wind_v = 1.5` and matching `prob.leak_vel_y = 1.5`, then verifies that the plume/hazard post-processing chain remains healthy and that the H2 centroid moves laterally by a measurable amount.

## Code changes

- `tools/codex_smoke_engineering_h2_leak_plume_history.sh`
  - Added `CODEX_H2_LEAK_HISTORY_MAX_CENTER_OFFSET` so crosswind or other lateral-response cases can relax the default no-lateral-motion guard without changing the default behavior.
- `tools/codex_smoke_engineering_h2_leak_plume_profile.sh`
  - Exposed existing `validate_h2_leak_plume_profile.py` thresholds through environment variables: y/z L1 bounds, centroid shift, downstream fraction, lateral offset, plane mass fraction, and final mass-ratio bounds.
  - Defaults preserve the previous no-crosswind behavior.
- `tools/codex_smoke_engineering_h2_leak_open_domain_crosswind.sh`
  - Generates two temporary inputs from `input.codex_open_domain_flammable_smoke`.
  - Runs the full flammable-cloud chain for baseline and crosswind cases.
  - Writes `crosswind_summary.csv` and fails unless crosswind y-shift separates from baseline, downstream mass remains strong, and flammable-cloud volume remains nonzero and bounded.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`
  - Added the new crosswind evidence and narrowed the remaining boundary-condition gap to broader/low-wind/inlet/terrain validation.

## Verification evidence

- `bash -n tools/codex_smoke_engineering_h2_leak_plume_history.sh tools/codex_smoke_engineering_h2_leak_plume_profile.sh tools/codex_smoke_engineering_h2_leak_open_domain_crosswind.sh`: PASS.
- First calibration run with `wind_v=1.0` failed only the summary threshold: `crosswind plume y shift too small: 0.02175563` in `/tmp/codex_h2_leak_open_domain_crosswind_20260718`; the solver and plume/hazard subchecks were otherwise healthy. The maintained gate was then strengthened to `wind_v=1.5` instead of weakening the `2.5e-2` y-shift requirement.
- `CODEX_H2_LEAK_CROSSWIND_LOG_DIR=/tmp/codex_h2_leak_open_domain_crosswind_20260718_v15 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain_crosswind.sh`: PASS.
  - `crosswind_summary.csv`: `baseline_y_shift=0.00000000e+00`, `crosswind_y_shift=3.20681320e-02`, `baseline_downstream=8.49997579e-01`, `crosswind_downstream=8.86249988e-01`, `baseline_cloud=2.14843750e-02`, `crosswind_cloud=2.39257812e-02`.
  - Crosswind `validation.log`: `massN=2.00008692e-04`, `injectedN=2.00000000e-04`, `mass_ratioN=1.00004346e+00`, `lateral_offset=3.20681323e-02`, `downstream_fraction=8.86249988e-01`.
  - Crosswind `profile_validation.log`: `centroid=(6.45262904e-01,5.32068132e-01,5.00000000e-01)`, `centroid_shift=1.45262904e-01`, `y_l1=3.43491203e-01`, `z_l1=2.52044810e-01`.
  - Crosswind `hazard_summary.log`: `cloud_volume=2.39257812e-02`, `cloud_species_mass=1.68731740e-04`, `max_X=1.43484754e-01`.
  - Crosswind `hazard_planes.log`: `active_planes=6`, `flammable_planes=3`.
  - Crosswind `hazard_timeseries.log`: `plotfiles=6`, `final_cloud_volume=2.39257812e-02`, `final_flammable_planes=3`.
- Default open-domain regression after parameterizing wrappers: `CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR=/tmp/codex_h2_leak_open_domain_post_crosswind_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain.sh`: PASS.
- Log hygiene:
  - No `Unused ParmParse Variables`, `RuntimeWarning`, `nan`, `inf`, or `FAIL` markers in `/tmp/codex_h2_leak_open_domain_crosswind_20260718_v15/{baseline,crosswind}/*.log`.
  - No such markers in `/tmp/codex_h2_leak_open_domain_post_crosswind_20260718/*.log`.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=941`.
- `ctest --test-dir build-codex-smoke --output-on-failure`: PASS, 22/22.
- Touched-file whitespace/final-newline check: PASS before writing this checkpoint.

## Residual risks

- This is a two-point uniform crosswind smoke, not a full boundary-condition campaign.
- The crosswind case intentionally matches leak jet y-velocity to `wind_v`; separate crosswind-only ambient wind, oblique jet, calm wind, and low-wind cases remain open.
- It does not validate atmospheric boundary-layer evolution, terrain, obstacle/tank-farm crosswind interaction, turbulence-model accuracy, or experimental/literature plume data.
- Production-scale long-time and MPI/multi-node crosswind campaigns remain open.

## Progress estimate

Engineering production path is now about 79%. This slice closes the first lateral wind-response gate; the main remaining production blockers are still reference-quality plume/fire validation, low-wind/inlet/terrain campaigns, AMR multi-level and production-scale campaigns, distributed real-gas/thermal pipe-network physics, and real CAD geometry robustness.
