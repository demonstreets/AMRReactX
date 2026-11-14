# Checkpoint: engineering H2 acceptance matrix

Date: 2026-07-20

## Summary

Added a machine-readable engineering H2 acceptance matrix that maps the current engineering evidence into acceptance rows for H2 storage/pipeline leak dispersion, source physics, geometry/obstacles, AMR/MPI, production-mesh stability, ignition/fire screening, and scheduler-managed campaign handoff.

## Changes

- Added `tools/write_engineering_h2_acceptance_matrix.py`.
- Generated `docs/codex_audit/evidence/engineering_h2_acceptance_matrix_20260720/engineering_h2_acceptance_matrix.json` and `.md`.
- Updated `tools/write_engineering_production_scorecard.py` to include the acceptance matrix as hashed first-class evidence and expose its status in `summary`.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the matrix result.

## Matrix Result

- Status: `PARTIAL-PRODUCTION`
- Rows: `7`
- Pass-like rows: `6`
- Not-ready rows: `1`
- Not-ready row: `scheduler_managed_campaign`

The matrix confirms that the current internal engineering evidence covers dispersion core, source physics, geometry/obstacles, AMR/MPI smoke campaign, production-mesh AMR/MPI stability scout, and ignition/fire screening. It also keeps scheduler-managed production campaign handoff as an explicit blocker.

## Validation

- `python3 -m py_compile tools/write_engineering_h2_acceptance_matrix.py tools/write_engineering_production_scorecard.py`: PASS
- `python3 tools/write_engineering_h2_acceptance_matrix.py --verify-json ...engineering_h2_acceptance_matrix.json`: PASS
- `python3 tools/write_engineering_production_scorecard.py --verify-json ...engineering_production_scorecard.json`: PASS, `functional=90.6`, `production=70.0`
- Scorecard summary includes `engineering_h2_acceptance_matrix_status=PARTIAL-PRODUCTION`, `pass_like_rows=6`, `not_ready_rows=[scheduler_managed_campaign]`.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=966`
- `ctest --test-dir build-codex-smoke --output-on-failure`: PASS, `22/22`
