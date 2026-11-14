# 2026-07-28 Academic two-phase interface AMR validation

## Scope

This audit records the ACD-08 two-phase interface-AMR validation gate and the follow-up AMR stability hardening added after the engineering H2 initial acceptance work. The gate is based on the academic Rayleigh-Taylor two-fluid setup and checks that AMR refinement follows the gas-liquid interface while conservation, boundedness, finite-state constraints, and post-regrid stability remain valid.

## Evidence

- Report root: `docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728`
- Report JSON: `academic_twophase_interface_amr_validation_report.json`
- Report markdown: `academic_twophase_interface_amr_validation_report.md`
- Runner: `tools/codex_run_academic_twophase_interface_amr_validation.sh`
- Rayleigh-Taylor default input: `examples/academic/rayleigh_taylor/inputs`
- Plotfile reader fix: `tools/amrex_reader.py`
- Validators: `tools/validate_academic_twophase_interface_amr.py`, `tools/validate_rayleigh_taylor_plotfile.py`, `tools/validate_rayleigh_taylor_growth.py`
- Total verifier: `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`

## Result

Status: `PASS-ACADEMIC-TWOPHASE-INTERFACE-AMR-VALIDATION`

The maintained gate now uses a 64x128 base AMR case with one refined level, `amr.n_error_buf = 4 4`, and a 128x256 uniform-fine reference. The AMR case ran 3500 steps to time `0.00877437412363`, including the post-step-3000 regrid; the uniform reference ran 3500 steps to time `0.00443816671238`. The final report self-verified and the full production evidence verifier returned `VERIFY_RC=0` with CTest intentionally skipped.

Key AMR metrics:

- finest level: `1`
- composite grid: `128 x 256`
- interface cells: `328`
- interface refined cells: `328`
- interface refined fraction: `1.0`
- refined box count: `4`
- refined cell fraction: `0.5`
- growth ratio: `1.0609263`
- growth rate: `6.7403544`
- mass relative drift: `0.0`
- VOF mass relative drift: `0.0`
- alpha range: `-1.86645926e-66` to `1.0`

Uniform reference metrics:

- grid: `128 x 256`
- growth ratio: `1.0253621`
- growth rate: `5.6432846`
- mass relative drift: `1.4803e-16`
- VOF mass relative drift: `2.22045e-16`

The AMR/reference growth-rate relative difference is `0.1944027065372531`, within the maintained gate threshold. ACD-08 remains `PASS` in the master-plan traceability report with stronger evidence than the previous 48x96/96x192 3000-step window.

## Fixes

`tools/amrex_reader.py` was corrected to parse structured AMReX Header files instead of treating the first numeric two-column step/time line as mesh spacing. The old parser could infer an invalid refinement ratio for 2D AMR plotfiles and attempt an enormous allocation.

The interface-AMR runner now uses the normal Rayleigh-Taylor input template rather than the growth-specific template that enabled dual-energy overrides. The dual-energy overrides caused the 128x256 uniform reference to trigger a step-1 NaN stop, while the normal RT template runs the 128x256 reference cleanly.

The AMR gate now injects `amr.n_error_buf = 4 4`. Diagnostics showed that unbuffered 64x128 AMR with frequent regridding produced NaNs along the Level_1 lower coarse-fine boundary. Buffer values 2 and 4 passed the 80-step frequent-regrid sweep; 4 was selected for the maintained gate. The buffered 64x128 AMR case also passed the 3500-step formal run and advanced past the step-3000 regrid that previously exposed a NaN.

The Rayleigh-Taylor plot and growth validators accept `--alpha-tol`. The interface-AMR gate uses `2.0e-6`, which tolerates roundoff-scale VOF undershoots/overshoots while still rejecting meaningful boundedness failures.

## Limitations And Follow-Up

This validates two-phase interface AMR on a maintained Rayleigh-Taylor case; it is not yet a gas-liquid detonation, spray-combustion, or external literature benchmark.

The unbuffered AMR failure remains documented as a coarse-fine-boundary instability mode. The maintained gate avoids it with a small AMR error buffer, but a deeper solver-level hardening item remains: two-phase HLLC/VOF fluxes and AMR fill/regrid handling should eventually be audited so the code is robust even when a user chooses a minimal buffer.
