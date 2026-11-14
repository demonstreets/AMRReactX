# 2026-07-27 H2 SBEPV5 D27 Program Scout Run

This pass moved the external-plume benchmark chain from a paper/spec scaffold to
a runnable program-side CUDA scout for the selected HySafe SBEPV5 / GexCon D27
style case.

## What Changed

- Added parameter controls to `tools/codex_smoke_engineering_h2_sbepv5_d27_scout_cuda.sh` for release rate, source radius, source velocity, baffle enablement, and plume-detection thresholds.
- Added one-cell z-wall clearance to the four approximate scout baffles. The previous upper/lower baffles touched the coarse-domain z walls and produced first-step NaNs in the EB path.
- Kept the scout deliberately conservative: public D27 geometry/release facts are recorded, while the numeric source center/velocity and approximate baffle/sensor locations remain marked as program-scout assumptions.
- Updated `tools/write_engineering_h2_sbepv5_d27_scout_run_report.py` so lightweight evidence files are copied into the audit evidence directory instead of depending on `/tmp`.
- Updated `tools/write_engineering_h2_external_plume_benchmark_readiness.py` to consume the D27 program-scout report as a distinct current output without clearing the external-reference blocker.

## Evidence

- `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_program_scout_run_20260727/sbepv5_d27_scout_run_report.json`
- `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_program_scout_run_20260727/sbepv5_d27_scout_run_report.md`
- The report directory includes copied `run_log`, `validation_log`, input, sensor JSON, plume observation JSON, plume extents CSV, and sensor time-series CSV.

The accepted scout run used:

- Single CUDA run
- Domain `1.20 x 0.20 x 0.90 m`
- Grid `48 8 36`
- `200` steps, `fixed_dt = 1.0e-5 s`, final time `0.002 s`
- Four approximate STL baffles
- Twelve approximate Gas01..Gas12 sensor probes
- H2 mass conservation ratio `1.00001210`
- Max `X(H2) = 0.0049255823912365505`

## Current Status

`PASS-SBEPV5-D27-PROGRAM-SCOUT-RUN` is a program-side execution and observability
pass. It proves that the D27-style small-domain/baffle/sensor/CUDA path can run
stably and produce plume and sensor outputs.

It does not prove external experimental agreement. The production blocker remains
open until exact or accepted digitized SBEPV5 D27 baffle geometry, sensor
coordinates, and Gas01..Gas12 concentration histories are ingested and compared
with case-specific tolerances.
