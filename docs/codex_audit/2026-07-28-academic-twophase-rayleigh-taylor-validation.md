# Academic Two-Phase Rayleigh-Taylor Validation

Date: 2026-07-28

## Scope

This audit records the academic two-phase Rayleigh-Taylor validation added for the gas-liquid/two-phase academic track after the engineering H2 integrated acceptance work was closed to the agreed initial production-credibility standard.

## Evidence

- Runner: `tools/codex_run_academic_twophase_rayleigh_taylor_validation.sh`
- Report writer: `tools/write_academic_twophase_rayleigh_taylor_validation_report.py`
- Evidence root: `docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728`
- Report: `docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/academic_twophase_rayleigh_taylor_validation_report.json`

## Result

Status: `PASS-ACADEMIC-TWOPHASE-RAYLEIGH-TAYLOR-VALIDATION`

The validation ran three uniform-grid Rayleigh-Taylor cases:

- `32x64`: initial amplitude `0.052679652`, final amplitude `0.060459554`, growth ratio `1.1476832`, growth rate `8.6090837`, mass drift `0`, VOF mass drift `0`
- `64x128`: initial amplitude `0.049804063`, final amplitude `0.055259745`, growth ratio `1.1095429`, growth rate `6.4967595`, mass drift `0`, VOF mass drift `0`
- `96x192`: initial amplitude `0.049685331`, final amplitude `0.053936113`, growth ratio `1.0855541`, growth rate `5.1306571`, mass drift `2.63164e-16`, VOF mass drift `3.94746e-16`

The cross-resolution trend remained bounded with growth-rate spread `0.515666`, maximum total-mass drift `2.63164e-16`, and maximum VOF-mass drift `3.94746e-16`.

## Master Plan Impact

- `ACD-04` is now covered as `PASS` by maintained two-phase validation evidence.
- `ACD-08` remains `PARTIAL`: gas detonation-front AMR and uniform-grid two-phase Rayleigh-Taylor validation are evidenced, but two-phase interface-specific AMR validation is still not complete.

## Verification

The engineering/academic evidence chain was regenerated and verified with:

`CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`

The command returned `VERIFY_RC=0` and the final line was `PASS engineering H2 production evidence verification`.
