# Academic Gas Double-Mach Reflection Validation

Status: `PASS-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION`

This audit records the maintained PeleC Double-Mach reflection strong-shock validation gate for QLT-03 standard validation coverage. The case exercises inviscid GammaLaw shock reflection with positive density/pressure checks, finite-field checks, Rankine-Hugoniot plateau-state checks, shock-front advancement, and clean AMReX finalization.

Evidence:

- `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.json`
- `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.md`
- `tools/codex_run_academic_gas_double_mach_validation.sh`
- `tools/write_academic_gas_double_mach_validation_report.py`

Residual scope:

- This clears the Double-Mach component of QLT-03.
- MMS, bubble-rise, and external experiment-grade comparisons remain separate QLT-03 gaps.
