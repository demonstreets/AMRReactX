# Checkpoint: engineering H2 leak multi-box plotfile reader

Date: 2026-07-18

## User priority

Engineering scenarios remain the active priority. Static droplet / CSF / deeper gas-liquid work is low priority until the tank/pipeline leak, fire, and detonation-risk engineering path is production-grade.

## This slice

Closed the current engineering blocker where `tools/amrex_reader.py` could only read single-box 3D plotfiles. That limitation forced the open-domain H2 leak smoke to stay at `amr.max_grid_size=32`, which is not representative of larger engineering domains that are naturally tiled into multiple AMReX boxes.

## Code changes

- `tools/amrex_reader.py`
  - Reads `FabOnDisk` offsets from `Level_0/Cell_H` and seeks to the correct offset before parsing each FAB header/data block.
  - Stitches multi-box 3D Level 0 plotfiles by placing each FAB at its integer index-space offset.
  - Retains 2D multi-box support but now uses the same index-space placement style instead of assuming simple x-concatenation.
  - Adds overlap and uncovered-cell guards for both 2D and 3D multi-box plotfiles.
  - Generates cell-center `x/y/z` coordinate arrays using global box lower indices, not only `prob_lo` and array length.
- `tools/test_amrex_reader_multibox.py`
  - Adds synthetic 2D/3D AMReX-like plotfile fixtures.
  - Verifies 3D two-box stitching, 2D two-box stitching, exact component values, coordinate arrays, gap detection, and overlap detection.
- `CMakeLists.txt`
  - Registers `amrex_reader_multibox_smoke` under `MYPELE_ENABLE_UNIT_SMOKE` when Python3 is available.
- `examples/engineering/h2_leak_3d/input.codex_open_domain_multibox_smoke`
  - Adds an open-domain H2 leak input with `amr.max_grid_size=16` to force a two-box Level 0 plotfile on the smoke mesh.
- `tools/codex_smoke_engineering_h2_leak_open_domain_multibox.sh`
  - Reuses the maintained open-domain plume/hazard chain with the multi-box input.
  - Verifies the final `plt00100/Level_0/Cell_H` has at least two `FabOnDisk` entries.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`
  - Record the new evidence and move the old multi-box reader gap to the narrower residual risk: AMR multi-level overlay and production-scale multi-box campaigns remain open.

## Verification evidence

- `python3 -m py_compile tools/amrex_reader.py tools/test_amrex_reader_multibox.py`: PASS.
- `python3 tools/test_amrex_reader_multibox.py`: PASS, `amrex_reader_multibox_smoke PASS dims=2,3 gap_guard=1 overlap_guard=1`.
- `cmake -S . -B build-codex-smoke`: PASS.
- `ctest --test-dir build-codex-smoke -R amrex_reader_multibox_smoke --output-on-failure`: PASS, 1/1.
- `ctest --test-dir build-codex-smoke --output-on-failure`: PASS, 22/22.
- `CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR=/tmp/codex_h2_leak_open_domain_multibox_post_reader_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain_multibox.sh`: PASS.
  - `validation.log`: `timeN=0.1`, `massN=2.00000000e-04`, `injectedN=2.00000000e-04`, `mass_ratioN=1.00000000e+00`, `downstream_fraction=8.49997579e-01`.
  - `profile_validation.log`: `centroid_shift=1.01245408e-01`, `y_l1=z_l1=2.61092816e-01`.
  - `hazard_summary.log`: `cloud_volume=2.14843750e-02`, `cloud_species_mass=1.81033585e-04`, `max_X=1.61483568e-01`.
  - `hazard_planes.log`: `active_planes=4`, `flammable_planes=2`.
  - `hazard_timeseries.log`: `plotfiles=6`, `final_cloud_volume=2.14843750e-02`, `final_flammable_planes=2`.
  - wrapper final check: `final_plot=plt00100 fab_count=2`.
- Log hygiene: no `Unused ParmParse Variables`, `RuntimeWarning`, `nan`, or `inf` markers in the new multi-box run logs.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=940`.
- `git diff --check` on touched files: PASS.

## Residual risks

- Current lightweight reader still reads Level 0 only. It does not overlay AMR fine/coarse levels or validate multi-level AMR plotfiles.
- The multi-box H2 case is still a coarse all-regular smoke with two boxes, not a production-size MPI/multi-rank campaign.
- Engineering leak model still lacks full real-gas EOS tables, thermal cooldown/Joule-Thomson effects, distributed pipe-network waves, complex branch/valve topology, sonic-jet resolution, and two-phase flashing.
- Dispersion/hazard metrics are still smoke-scale and synthetic; reference-quality experimental/literature plume benchmarks and long-time stability campaigns remain open.
- Industrial geometry coverage has STL/tank-farm plumbing smokes, but not real CAD cleanup, broad bad-mesh QA, per-file transforms, or larger obstacle-layout validation.

## Progress estimate

Engineering production path: about 78% of the current staged stabilization/audit plan. The strongest remaining blockers are reference-quality plume/fire validation, AMR multi-level and production-scale campaigns, distributed network/thermal real-gas physics, and real CAD geometry robustness.
