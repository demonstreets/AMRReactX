# Checkpoint: engineering BFS sensitivity scout script

Date: 2026-07-22

## Summary

Added `tools/codex_scout_engineering_bfs_kepsilon_sensitivity.sh` so the 208×56 BFS/k-epsilon sensitivity evidence can be reproduced without reconstructing ad hoc commands. The script runs two maintained scouts:

- `208x56_4rank_default_cfl`: expected current result `FAIL-NAN`.
- `208x56_serial_cfl005_500step`: expected current result `COMPLETE-SCOUT`, `t=0.007105879625`, `X_R/H=1.26119881115`, recirculation `1.14829396325H`.

The BFS reference report now includes the script as a hashed evidence file.

## Changed Files / Modules

- `tools/codex_scout_engineering_bfs_kepsilon_sensitivity.sh`
- `tools/write_engineering_bfs_kepsilon_reference_report.py`
- `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json`
- `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.md`
- `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

## Verification

- `tools/codex_scout_engineering_bfs_kepsilon_sensitivity.sh`
- `python3 -m py_compile tools/write_engineering_bfs_kepsilon_reference_report.py`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py --verify-json docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json`
- `tools/run_engineering_h2_production_evidence_verification_archive.sh`

## Results

- Sensitivity script passed and wrote `/tmp/codex_bfs_kepsilon_sensitivity_summary_20260722.tsv`.
- BFS report remains `NOT_READY-BFS-KEPSILON-REFERENCE`.
- Scorecard remains `NOT_PRODUCTION_READY`, `functional=93.4`, `production=73.5`.
- Full archive verification passed, path audit scanned 977 files, and CTest passed 22/22.

## Known Limitations

This script makes the current blocker reproducible; it does not fix the default refined-grid NaN or produce a developed refined BFS reference result.
