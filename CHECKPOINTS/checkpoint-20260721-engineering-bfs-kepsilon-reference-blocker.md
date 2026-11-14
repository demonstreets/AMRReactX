# Checkpoint: engineering BFS/k-epsilon reference blocker

Date: 2026-07-21

## Summary

Audited the existing `examples/engineering/bfs_kepsilon/plt00100` evidence against the maintained BFS validator. The plotfile does not show BFS reattachment or recirculation, and the log-law profile validator also fails. Tightened the validator semantics so `PASS WITH NOTES` can no longer be treated as a successful CLI result, then added a maintained machine-readable report that records the current BFS/k-epsilon reference state as `NOT_READY-BFS-KEPSILON-REFERENCE`.

## Changed Files / Modules

- `tools/validate_bfs.py`
- `tools/write_engineering_bfs_kepsilon_reference_report.py`
- `tools/write_engineering_production_scorecard.py`
- `tools/write_engineering_h2_production_evidence_verification_report.py`
- `tools/verify_engineering_h2_production_evidence.sh`
- `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json`
- `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.md`
- `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md`
- `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/verification.log`
- `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`
- `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.md`
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

## Verification

- `python3 -m py_compile tools/validate_bfs.py tools/write_engineering_bfs_kepsilon_reference_report.py tools/write_engineering_production_scorecard.py tools/write_engineering_h2_production_evidence_verification_report.py`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py --verify-json docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json`
- `python3 tools/write_engineering_production_scorecard.py --output-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json --output-md docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `tools/run_engineering_h2_production_evidence_verification_archive.sh`

## Results

- BFS/k-epsilon report: `NOT_READY-BFS-KEPSILON-REFERENCE`, `bfs_rc=1`, `loglaw_rc=1`, grid `80 x 8`.
- Scorecard remains `NOT_PRODUCTION_READY`, `functional=93.4`, `production=73.5`.
- Full archive verification passed, including `machine_local_paths PASS scanned_files=976` and CTest `22/22 PASS`.

## Known Limitations

This checkpoint does not improve the k-epsilon physical model or produce a reference-quality BFS run. It prevents a false-positive turbulence validation result and makes the failed BFS/reference state explicit in the production blocker ledger. Production-grade turbulence validation still needs an adequate-grid BFS, flat-plate, or cylinder reference campaign with reattachment, recirculation, wall/log-law, and grid-sensitivity evidence.
