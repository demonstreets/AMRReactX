# Checkpoint: engineering BFS grid-sensitivity scouts

Date: 2026-07-22

## Summary

Extended the maintained BFS/k-epsilon reference report with two 208×56 grid-sensitivity scouts. The goal was to determine whether the strict EB-BFS reference failure is merely caused by the coarse 104×28 grid.

The answer is not yet favorable. A 4-rank/default-CFL 208×56 run aborts with NaNs immediately after startup. A serial 208×56 run with `cfl=0.05` and `dt_shrink=0.001` completes 500 steps without NaNs, but it only reaches `t=0.0071s`; the flow is far from developed and the extracted reattachment is `X_R/H=1.26`, with recirculation length `1.15H`.

## Changed Files / Modules

- `tools/write_engineering_bfs_kepsilon_reference_report.py`
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

- `python3 -m py_compile tools/write_engineering_bfs_kepsilon_reference_report.py`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py --verify-json docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `tools/run_engineering_h2_production_evidence_verification_archive.sh`

## Results

- Baseline EB-BFS reference report remains `NOT_READY-BFS-KEPSILON-REFERENCE`, `X_R/H=5.39`, recirculation length `4.92H`.
- 208×56 4-rank/default-CFL scout: `FAIL-NAN`.
- 208×56 serial low-CFL 500-step scout: `COMPLETE-SCOUT`, `t=0.007105879625`, `X_R/H=1.261198811146003`, recirculation length `1.1482939632545934`.
- Scorecard remains `NOT_PRODUCTION_READY`, `functional=93.4`, `production=73.5`, with `bfs_kepsilon_reference_validation_failed` retained.
- Full archive verification passed, including path audit and CTest `22/22 PASS`.

## Known Limitations

These are sensitivity scouts, not a completed refined BFS validation campaign. They show that a higher grid alone is not yet a turnkey fix: the default parallel refined run is unstable, while the stable low-CFL refined run is too short to evaluate the Driver-Seegmiller reattachment target.
