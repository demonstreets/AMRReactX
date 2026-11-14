# Checkpoint: Engineering BFS k-epsilon Preflight Evidence

Date: 2026-07-22

## Scope

- Added `tools/check_engineering_bfs_kepsilon_case.py`.
- Integrated BFS/k-epsilon preflight evidence into `tools/write_engineering_bfs_kepsilon_reference_report.py`.
- Generated three preflight evidence reports for the current base input and two refined-grid sensitivity configurations.

## Evidence

- `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_preflight_base_report.json`
  - status: `NOT_READY-BFS-KEPSILON-PREFLIGHT`
  - grid: `104 x 28`
  - blocking gaps:
    - `bfs_step_height_resolution_below_engineering_minimum`
    - `bfs_grid_below_engineering_minimum`
    - `bfs_cfl_above_refined_grid_stability_limit`
    - `bfs_dt_shrink_above_refined_grid_stability_limit`

- `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_preflight_208_default_report.json`
  - status: `NOT_READY-BFS-KEPSILON-PREFLIGHT`
  - grid: `208 x 56`
  - blocking gaps:
    - `bfs_cfl_above_refined_grid_stability_limit`
    - `bfs_dt_shrink_above_refined_grid_stability_limit`
  - diagnostic gap:
    - `bfs_refined_grid_high_nan_risk_from_cfl_or_dt_shrink`

- `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_preflight_208_lowcfl_report.json`
  - status: `NOT_READY-BFS-KEPSILON-PREFLIGHT`
  - grid: `208 x 56`
  - blocking gaps:
    - `bfs_stop_time_below_reference_duration`
    - `bfs_max_step_below_reference_duration`

## Result

- BFS reference report remains `NOT_READY-BFS-KEPSILON-REFERENCE`.
- Engineering production scorecard remains `NOT_PRODUCTION_READY`.
- Scores remain unchanged: functional `93.4`, production credibility `73.5`.
- Full archive verification passed after refreshing scorecard hashes.
- CTest: `22/22` passed.
- Path audit: `machine_local_paths PASS scanned_files=978`.

## Remaining BFS Blocker

The current evidence proves the BFS/k-epsilon chain is explicit and reproducible, but not production-ready. The next real closure step is a stable refined-grid run with conservative CFL/dt-shrink and sufficient duration, followed by reattachment/recirculation agreement against the reference threshold.
