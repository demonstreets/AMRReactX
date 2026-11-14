# Checkpoint: Reproducible wrapper gate

Date: 2026-07-16
Status: PASS-SMOKE / gate orchestration

## Summary

Added `tools/codex_reproducible_gate.sh`, a release-oriented wrapper that composes the environment preflight, release provenance strict check, default `tools/codex_smoke_all.sh`, and optional PeleC/PeleLMeX CUDA smokes. The wrapper keeps the existing default quick gate unchanged while providing a single command for reproducibility-oriented runs.

## Changed files / modules

- `tools/codex_reproducible_gate.sh`
- `docs/codex_audit/ENVIRONMENT_PREFLIGHT.md`
- `docs/codex_audit/SMOKE_MATRIX.md`
- `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md`

## Verification

```bash
bash -n tools/codex_reproducible_gate.sh
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda CODEX_REPRO_SKIP_SMOKE_ALL=1 CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_preflight_only_20260716 tools/codex_reproducible_gate.sh
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda CODEX_REPRO_REQUIRE_CUDA=1 CODEX_REPRO_SKIP_SMOKE_ALL=1 CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716 JOBS=1 RUN_TIMEOUT=240 tools/codex_reproducible_gate.sh
```

## Evidence

- `/tmp/codex_reproducible_gate_preflight_only_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_preflight_only_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/pelec_cuda/validation.log`: PeleC CUDA smoke PASS.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/pelelmex_cuda/validation.log`: PeleLMeX CUDA smoke PASS.

## Remaining limitations

- This checkpoint validates wrapper orchestration and CUDA branches with `CODEX_REPRO_SKIP_SMOKE_ALL=1`; it does not rerun the full default `smoke_all` gate.
- Before a release candidate, run the wrapper without `CODEX_REPRO_SKIP_SMOKE_ALL`.
- The wrapper does not solve remaining physics-validation gaps such as MMS, double-Mach, Rayleigh-Taylor, long-time stability, or production scaling.
