# Checkpoint: Full reproducible wrapper gate

Date: 2026-07-16
Status: PASS-SMOKE / full default reproducibility gate

## Summary

Ran `tools/codex_reproducible_gate.sh` without `CODEX_REPRO_SKIP_SMOKE_ALL`, proving that the composed gate now passes preflight, release provenance strict, and the full default `tools/codex_smoke_all.sh` path in one command. This upgrades the previous wrapper-only evidence into a full default reproducibility-gate run.

## Verification

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_full_default_20260716 \
  JOBS=2 RUN_TIMEOUT=180 \
  tools/codex_reproducible_gate.sh
```

Additional audit commands:

```bash
grep -n "SUMMARY PASS\|PASS warnings=0\|all smoke checks passed" /tmp/codex_reproducible_gate_full_default_20260716/preflight.log /tmp/codex_reproducible_gate_full_default_20260716/release_provenance_strict.log /tmp/codex_reproducible_gate_full_default_20260716/smoke_all.log
```

## Evidence

- `/tmp/codex_reproducible_gate_full_default_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_default_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all.log`: `[codex-smoke-all] all smoke checks passed`.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all/academic_detonation_wave/validation.log`: detonation-wave validation PASS.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all/academic_pelec_plan_amr/validation.log`: PeleC plan-AMR validation PASS.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all/academic_sod_plotfile/validation.log`: Sod plotfile validation PASS.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all/engineering_h2_ignition_plotfile/validation.log`: H2 ignition plotfile validation PASS.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all/engineering_h2_ignition_history/validation.log`: H2 ignition history validation PASS.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all/engineering_h2_ignition_sdc_compare/sdc_compare.log`: H2 ignition SDC comparison PASS.

## Remaining limitations

- This full wrapper run did not set `CODEX_REPRO_REQUIRE_CUDA=1`; PeleC/PeleLMeX CUDA wrapper branches remain covered by `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716`.
- A release candidate should still run the full wrapper with CUDA enabled if GPU deliverables are in scope.
- Physics-validation gaps remain: MMS, double-Mach, Rayleigh-Taylor, longer stability, production scaling, and broader reference benchmarks are not closed by this gate.
