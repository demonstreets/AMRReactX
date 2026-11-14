# Environment preflight

Updated: 2026-07-16

This note records the maintained environment preflight for the current `/home/cj/my-pele` worktree. It is a fast reproducibility gate to run before expensive smoke tests or before claiming that another machine can reproduce the current server state.

## Command

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  tools/codex_preflight_environment.sh --require-cuda
```

For CPU-only machines, omit `--require-cuda`, but `SUNDIALS_CUDA_DIR` or `SUNDIALS_DIR` must still point to the SUNDIALS install used by the current build configuration.

## What It Checks

- Core tools: `git`, `cmake`, `make`, `python3`, `c++`, and `cc`.
- Release provenance strict gate: `python3 tools/check_release_provenance.py --strict`.
- Dependency layout from `docs/codex_audit/DEPENDENCY_PROVENANCE.tsv`.
- Relative symlinks for local AMReX/PelePhysics sharing.
- SUNDIALS include/lib directories, version header, CPU libraries, and CUDA libraries.
- CUDA tools and GPU visibility when `--require-cuda` is used.
- Machine-local path audit: `python3 tools/check_machine_local_paths.py --strict`, covering maintained source/script/input roots while excluding generated build/plot/checkpoint artifacts.

## Current Evidence

- `/tmp/codex_preflight_environment_cuda_20260716_final.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_preflight_release_provenance.log`: release provenance strict sub-check produced by the preflight script.
- `/tmp/codex_preflight_environment_strict_sundials64_20260716.log`: intentional negative check showing `--strict-sundials-6.4` fails because the validated server SUNDIALS is `6.7.0`.


Machine-local path audit evidence after the 2026-07-16 cleanup:

- `/tmp/codex_machine_local_paths_final_strict_20260716.log`: `machine_local_paths PASS scanned_files=893`.
- `/tmp/codex_preflight_machine_paths_20260716.log`: preflight includes the strict machine-local path audit and reports `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_geometry_eb2_stl_machine_paths_20260716.log`: EB2/STL geometry smoke PASS after replacing unit-test `/tmp/test_*` literals with system temporary paths.
- `/tmp/codex_geometry_amrex_domain_machine_paths_20260716_rerun.log`: AMReX domain smoke PASS after replacing stale user-home CMake-package sanitization with a generic pattern.

## Version Note

The master plan says to lock SUNDIALS 6.4 because bundled 7.x was risky. The currently verified server configuration uses:

- SUNDIALS `6.7.0`
- CUDA toolkit `12.6.85`
- Tesla P100 compute capability `6.0`

This is a documented plan deviation. Current evidence supports the SUNDIALS 6.x line on this server, specifically 6.7.0, not a strict 6.4-only claim. Use `tools/codex_preflight_environment.sh --strict-sundials-6.4` when an experiment needs to enforce the original master-plan value; it currently fails on this server by design.

## Release Boundary

Preflight passing means the current machine is suitable for the maintained smoke gates. It does not replace a dependency bootstrap script, release commit, tag, or full physics validation matrix.

## Reproducible Gate Wrapper

`tools/codex_reproducible_gate.sh` wraps the environment preflight, release provenance strict check, existing default smoke gate, and optional CUDA smokes.

Full CPU-oriented reproducibility gate:

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_<timestamp> \
  JOBS=2 RUN_TIMEOUT=180 \
  tools/codex_reproducible_gate.sh
```

Full CUDA-inclusive gate:

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_REQUIRE_CUDA=1 \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_cuda_<timestamp> \
  JOBS=2 RUN_TIMEOUT=240 \
  tools/codex_reproducible_gate.sh
```

Fast wrapper validation can set `CODEX_REPRO_SKIP_SMOKE_ALL=1`; this validates preflight/provenance and, when requested, the CUDA smokes without rerunning the long default gate.

Current wrapper evidence:

- `/tmp/codex_reproducible_gate_preflight_only_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_preflight_only_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/pelec_cuda/validation.log`: PeleC CUDA smoke PASS.
- `/tmp/codex_reproducible_gate_cuda_skip_smoke_all_20260716/pelelmex_cuda/validation.log`: PeleLMeX CUDA smoke PASS.

## Full Wrapper Evidence

The full default wrapper gate has now been run without `CODEX_REPRO_SKIP_SMOKE_ALL`:

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_full_default_20260716 \
  JOBS=2 RUN_TIMEOUT=180 \
  tools/codex_reproducible_gate.sh
```

Evidence:

- `/tmp/codex_reproducible_gate_full_default_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_default_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all.log`: `[codex-smoke-all] all smoke checks passed`.
- Detailed default-gate logs live under `/tmp/codex_reproducible_gate_full_default_20260716/smoke_all/`.

## Full CUDA-Inclusive Wrapper Evidence

The full CUDA-inclusive wrapper gate has now been run without `CODEX_REPRO_SKIP_SMOKE_ALL` and with `CODEX_REPRO_REQUIRE_CUDA=1`:

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_REQUIRE_CUDA=1 \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_full_cuda_20260716 \
  JOBS=1 RUN_TIMEOUT=240 \
  tools/codex_reproducible_gate.sh
```

Evidence:

- `/tmp/codex_reproducible_gate_full_cuda_20260716/preflight.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/smoke_all.log`: `[codex-smoke-all] all smoke checks passed`.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/pelec_cuda/validation.log`: PeleC CUDA smoke validation PASS.
- `/tmp/codex_reproducible_gate_full_cuda_20260716/pelelmex_cuda/validation.log`: PeleLMeX CUDA smoke validation PASS.
- Failure-keyword scan over top-level, CUDA, and nested smoke logs found no `Unused ParmParse Variables`, `Backtrace`, `Segfault`, `CUDA error`, or `FAIL` markers.

## Machine-Path Cleanup Wrapper Evidence

After adding `tools/check_machine_local_paths.py` to preflight and removing maintained `/home/cj`, stale `/home/demon...`, and direct unit-test `/tmp/test_*` dependencies, the non-skipped CUDA-inclusive wrapper was rerun:

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_REQUIRE_CUDA=1 \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716 \
  JOBS=1 RUN_TIMEOUT=240 \
  tools/codex_reproducible_gate.sh
```

Evidence:

- `/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716.log`: wrapper reports all requested checks passed.
- `/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716/preflight.log`: includes machine-local path audit and reports `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716/release_provenance_strict.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716/smoke_all.log`: `[codex-smoke-all] all smoke checks passed`.
- `/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716/pelec_cuda/validation.log`: PeleC CUDA smoke PASS.
- `/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716/pelelmex_cuda/validation.log`: PeleLMeX CUDA smoke PASS.
- `/tmp/codex_reproducible_gate_full_cuda_machine_paths_failure_scan_20260716.log`: failure-keyword scan found no matches.

## H2 Ignition-Delay Wrapper Evidence

After adding the H2/O2 0D ignition-delay convergence smoke to `tools/codex_smoke_all.sh`, the full CUDA-inclusive reproducibility wrapper was rerun:

```bash
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda \
  CODEX_REPRO_REQUIRE_CUDA=1 \
  CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_full_cuda_h2_ignition_delay_20260716 \
  JOBS=1 RUN_TIMEOUT=240 \
  tools/codex_reproducible_gate.sh
```

Evidence:

- `/tmp/codex_reproducible_gate_full_cuda_h2_ignition_delay_20260716.log`: preflight, release provenance strict, updated smoke_all, PeleC CUDA, and PeleLMeX CUDA all PASS.
- `/tmp/codex_reproducible_gate_full_cuda_h2_ignition_delay_20260716/smoke_all/engineering_h2_ignition_delay/validation.log`: `h2_ignition_delay_validation PASS threshold_rise=400 mid_fine_rel=5.32379232e-04`.
- `/tmp/codex_reproducible_gate_full_cuda_h2_ignition_delay_failure_scan_20260716.log`: failure-keyword scan found no matches.
