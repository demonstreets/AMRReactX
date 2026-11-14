# Academic Two-Phase Bubble-Rise Validation

Status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION`

This audit records the maintained PeleC two-phase bubble-rise validation gate for QLT-03 standard validation coverage. The bubble-rise case now uses a problem-specific external buoyancy source rather than an unused `pelec.gravity` input alone. The 6000-step low-CFL gate proves a strengthened short-time buoyancy response with bounded alpha and strong conservation over many stable source-coupled updates.

Evidence:

- `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json`
- `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.md`
- `tools/codex_run_academic_twophase_bubble_rise_validation.sh`
- `tools/validate_academic_twophase_bubble_rise.py`
- `tools/write_academic_twophase_bubble_rise_validation_report.py`

Residual scope:

- This clears the strengthened short-time, low-CFL bubble-rise stability component of QLT-03.
- Longer 8000-30000 step probes with several CFL/source/pressure variants still reached non-finite or negative-internal-energy states, so canonical long physical-time bubble-rise deformation/stability remains a separate QLT-03 gap.
- MMS nonlinear MASA and external experiment-grade validation remain separate QLT-03 gaps.
