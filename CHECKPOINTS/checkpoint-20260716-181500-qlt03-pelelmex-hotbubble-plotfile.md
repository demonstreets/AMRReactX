# Checkpoint: QLT-03 PeleLMeX HotBubble plotfile smoke

Date: 2026-07-16
Status: PASS-SMOKE / PARTIAL-QLT-03

## Summary

Added a targeted PeleLMeX HotBubble smoke for QLT-03 bubble-class coverage. The smoke builds/runs `external/PeleLMeX/Exec/RegTests/HotBubble` on a reduced 16x32 2D grid to `time = 0.002`, removes refinement-only and unused legacy keys for a clean strict input, enforces `amrex.abort_on_unused_inputs = 1`, writes initial/final plotfiles, and validates hot-bubble field structure plus short-time buoyancy response.

This is not a full Rayleigh-Taylor or quantitative bubble-rise benchmark; it is a reproducible solver-coupled plotfile sanity check that closes one more gap between raw startup and standard-case validation.

## Changed files / modules

- `tools/codex_smoke_engineering_pelelmex_hotbubble.sh`
- `tools/validate_pelelmex_hotbubble_plotfile.py`
- `docs/codex_audit/SMOKE_MATRIX.md`
- `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md`
- `CHECKPOINTS/checkpoint-20260716-181500-qlt03-pelelmex-hotbubble-plotfile.md`

## Verification

- `python3 -m py_compile tools/validate_pelelmex_hotbubble_plotfile.py`
- `bash -n tools/codex_smoke_engineering_pelelmex_hotbubble.sh`
- `CODEX_PELELMEX_HOTBUBBLE_LOG_DIR=/tmp/codex_pelelmex_hotbubble_20260716 JOBS=4 RUN_TIMEOUT=180 tools/codex_smoke_engineering_pelelmex_hotbubble.sh`

## Evidence

- `/tmp/codex_pelelmex_hotbubble_20260716/run.log`
- `/tmp/codex_pelelmex_hotbubble_20260716/validation.log`
- PASS line: `pelelmex_hotbubble_plotfile_validation PASS time=2.00000000e-03 temp0_range=3.00000000e+02:4.50000000e+02 temp1_range=3.00000000e+02:4.50000000e+02 rho0_range=7.81322661e-01:1.17198399e+00 rho1_range=7.81322658e-01:1.17198399e+00 velocity_linf=4.48502379e-03 vy_linf=4.48502379e-03 mass_rel=1.99502859e-07 hot_cells=32->32 hot_centroid_y=1.00000000e-02->1.00000000e-02 species_sum_err=4.44089210e-16`

## Known limitations

- Short-time small-grid sanity only; not a quantitative bubble-rise benchmark.
- Rayleigh-Taylor, double-Mach, MMS, exact/MMS PeleLMeX validation, mesh convergence, and long-time stability remain open.
- Kept out of the default quick gate because it builds a separate PeleLMeX RegTests executable.
