# Checkpoint: Full CUDA-inclusive reproducible wrapper gate

Date: 2026-07-16
Status: PASS-SMOKE / strongest current reproducibility gate

## Summary

Ran `tools/codex_reproducible_gate.sh` with `CODEX_REPRO_REQUIRE_CUDA=1` and without `CODEX_REPRO_SKIP_SMOKE_ALL`. This proves the composed gate passes environment preflight, release provenance strict, the full default `tools/codex_smoke_all.sh`, PeleC CUDA, and PeleLMeX CUDA in one command.

## Verification

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_REQUIRE_CUDA=1 \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_full_cuda_20260716 \
  JOBS=1 RUN_TIMEOUT=240 \
  tools/codex_reproducible_gate.sh
```

Failure-keyword audit:

```bash
grep -R "Unused ParmParse Variables\|Backtrace\|Segfault\|CUDA error\| FAIL\|FAIL " -n /tmp/codex_reproducible_gate_full_cuda_20260716/*.log /tmp/codex_reproducible_gate_full_cuda_20260716/*/*.log /tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/*.log /tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/*/*.log
```

The failure-keyword audit produced no output.

## Evidence

- `/tmp/codex_reproducible_gate_full_cuda_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all.log`: `[codex-smoke-all] all smoke checks passed`.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/pelec_cuda/validation.log`: PeleC CUDA smoke validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/pelelmex_cuda/validation.log`: PeleLMeX CUDA smoke validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/academic_detonation_wave/validation.log`: detonation-wave validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/academic_pelec_plan_amr/validation.log`: PeleC plan-AMR validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/academic_sod_plotfile/validation.log`: Sod plotfile validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/engineering_h2_ignition_plotfile/validation.log`: H2 ignition plotfile validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/engineering_h2_ignition_history/validation.log`: H2 ignition history validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all/engineering_h2_ignition_sdc_compare/sdc_compare.log`: H2 ignition SDC comparison PASS.

## Remaining limitations

- This is the strongest current smoke/reproducibility gate, but it is not full master-plan completion.
- It does not close MMS, double-Mach, Rayleigh-Taylor, long-stability, production scaling, or quantitative reference benchmark gaps.
- Final release still needs commit/tag discipline and dependency bootstrap/lock documentation.
