# Checkpoint: engineering BFS strict reference tolerance

Date: 2026-07-21

## Summary

Re-audited the BFS/k-epsilon reference evidence after finding that `examples/engineering/bfs_kepsilon/plt00100` is a straight-channel smoke, not a true backward-facing-step geometry. The maintained BFS reference report now targets the real EB backward-facing-step output `examples/engineering/backward_facing_step/plt02057`.

The true EB-BFS case is useful but still not production-ready under the master-plan requirement. It has `ke_wall_functions=1`, grid `104 x 28`, `U_ref=13.47 m/s`, `H=0.0381 m`, and a detected recirculation zone of `4.92H`; however, strict reattachment accuracy fails because `X_R/H=5.39` is outside `6.26 ± 10%`.

## Changed Files / Modules

- `tools/validate_bfs.py`
- `tools/write_engineering_bfs_kepsilon_reference_report.py`
- `tools/write_engineering_production_scorecard.py`
- `tools/write_engineering_h2_production_evidence_verification_report.py`
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
- `python3 tools/validate_bfs.py examples/engineering/backward_facing_step/plt02057`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py --verify-json docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `tools/run_engineering_h2_production_evidence_verification_archive.sh`

## Results

- Strict BFS validator: `VERDICT: FAIL`, `X_R/H=5.39`, reference window `6.26 ± 0.63`, recirculation length `4.92H`.
- BFS/k-epsilon report: `NOT_READY-BFS-KEPSILON-REFERENCE`, `bfs_rc=1`.
- Scorecard remains `NOT_PRODUCTION_READY`, `functional=93.4`, `production=73.5`, with `bfs_kepsilon_reference_validation_failed` retained.
- Full archive verification passed, including CTest `22/22 PASS`.

## Known Limitations

This checkpoint does not tune or improve k-epsilon physics. It replaces misleading channel-smoke evidence with the real EB-BFS output and aligns the acceptance criterion with the master-plan ±10% reference requirement. Closing this blocker still needs a refined/tuned BFS or another accepted turbulent reference campaign.
