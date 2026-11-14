# Academic Gas Double-Mach Reflection Validation

Status: `PASS-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION`

## Scope

PeleC inviscid GammaLaw Double-Mach reflection strong-shock gate: front advancement, Rankine-Hugoniot plateau states, positive density/pressure, finite fields, and clean AMReX finalization

## Key Metrics

- Time: `0.000991338878532`
- Grid: `96x24`
- Density range: `1.37778` to `8.01314`
- Pressure range: `0.976611` to `117.66`
- Front x: `0.729167` minimum expected `0.278926`

## Quality Gates

- `run_finalized_without_failure_tokens`: `PASS`
- `positive_finite_density_pressure`: `PASS`
- `rankine_hugoniot_plateau_states`: `PASS`
- `shock_front_advancement`: `PASS`

## Evidence Files

- `case_summary`: `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/double_mach_reflection_8step/case_summary.json` sha256 `2956e9ea569e0c47`
- `input_file`: `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/double_mach_reflection_8step/run/input.codex_smoke` sha256 `b0ad78e61f1e9812`
- `run_log`: `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/double_mach_reflection_8step/run.log` sha256 `6173097c61c1e6f9`
- `runner_log`: `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/double_mach_reflection_8step/runner.log` sha256 `54501ebf5f791dca`
- `validation_log`: `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/double_mach_reflection_8step/validation.log` sha256 `6ed516ac9bcacbfa`
- `runner`: `tools/codex_run_academic_gas_double_mach_validation.sh` sha256 `3fdb1d8cecd14d8b`
- `smoke_runner`: `tools/codex_smoke_academic_double_mach.sh` sha256 `05720f1979a7a50e`
- `validator`: `tools/validate_double_mach_plotfile.py` sha256 `11e1e186357f1720`
- `report_writer`: `tools/write_academic_gas_double_mach_validation_report.py` sha256 `cf99b101f3c83c6c`

## Limitations

- This is an in-repository short Double-Mach reflection gate, not a full external literature benchmark.
- The gate strengthens QLT-03 standard validation coverage but does not by itself clear MMS or bubble-rise gaps.
