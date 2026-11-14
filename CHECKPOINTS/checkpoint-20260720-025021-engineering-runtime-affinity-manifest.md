# Checkpoint: engineering runtime affinity manifest

Timestamp: 2026-07-20 02:50:21 UTC
Scope: engineering production-readiness, runtime/MPI/OpenMP affinity evidence.

## Context

The previous engineering H2 leak campaign and release packaging evidence showed deterministic small-case execution, summaries, hashes, and packaged release artifacts. The remaining production-readiness gap here was not chemistry or case setup; it was whether the current server runtime can be described and checked for MPI launch, CPU topology, and affinity policy before larger engineering campaigns.

This checkpoint adds an interactive runtime-affinity preflight. It is intentionally lightweight and does not run a large CFD case.

## Added tool

- `tools/write_engineering_runtime_affinity_manifest.py`

The tool records sanitized CPU topology, `uname`, host metadata, selected scheduler and OpenMP environment variables, MPI launcher/version metadata, and a Python-based MPI probe that does not require `mpi4py`. The probe validates rank count, contiguous unique ranks, nonempty CPU affinity masks, and the explicit `OMP_NUM_THREADS` setting. It can also verify a stored JSON manifest with `--verify-json`.

## Evidence generated

Command:

```bash
python3 tools/write_engineering_runtime_affinity_manifest.py \
  --ranks 4 \
  --threads 1 \
  --output-json docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json \
  --output-md docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.md
```

Result:

```text
engineering_runtime_affinity_manifest PASS ranks=4 threads=1 warnings=3 json=docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json md=docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.md
```

Verification:

```bash
python3 tools/write_engineering_runtime_affinity_manifest.py --verify-json docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json
```

Result:

```text
engineering_runtime_affinity_manifest VERIFY-PASS ranks=4 threads=1 warnings=3 json=docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json
```

Spot-check summary:

```text
manifest PASS {'ranks': 4, 'threads_per_rank': 1} warnings= ['no_scheduler_environment_detected', 'OMP_PROC_BIND_unset', 'OMP_PLACES_unset']
sha 8baa9ff21cf2694e
md_sha 79b8ab76e27ff744
cpu 56 {'Architecture': 'x86_64', 'CPU max MHz': '3300.0000', 'CPU min MHz': '1200.0000', 'CPU(s)': '56', 'Core(s) per socket': '14', 'Model name': 'Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz', 'NUMA node(s)': '2', 'Socket(s)': '2', 'Thread(s) per core': '2'}
launcher /usr/bin/mpirun 0
probe_rc 0 rows 4 stdout_sha ac00ad760f283aa0
rank 0 host xiaochun-4028 affinity_count 28 omp 1 affinity_head [0, 1, 2, 3, 4, 5, 6, 7]
rank 1 host xiaochun-4028 affinity_count 28 omp 1 affinity_head [14, 15, 16, 17, 18, 19, 20, 21]
rank 2 host xiaochun-4028 affinity_count 28 omp 1 affinity_head [0, 1, 2, 3, 4, 5, 6, 7]
rank 3 host xiaochun-4028 affinity_count 28 omp 1 affinity_head [14, 15, 16, 17, 18, 19, 20, 21]
```

Private-path check:

The generated runtime-affinity evidence directory was checked for machine-local path and credential markers. No matches were reported.

## Docs updated

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

The docs now distinguish the new interactive runtime-affinity preflight from still-open production gaps.

## Remaining limitations

- No batch scheduler environment was present in this interactive shell.
- `OMP_PROC_BIND` and `OMP_PLACES` were unset, so binding policy is recorded as missing rather than proven production-safe.
- This does not prove production MPI scaling, hybrid MPI/OpenMP safety, CFD performance scaling, or overnight stability.
- A scheduler-managed long engineering campaign is still required before claiming production-grade large-scale engineering readiness.

## Final verification

- Python compile passed for the runtime-affinity manifest tool and the engineering H2 campaign/package helpers.
- `--verify-json` passed on the generated runtime-affinity manifest.
- The first path audit found a hard-coded machine-local marker in the new verifier source; that source check was replaced with dynamic HOME/credential-environment marker checks.
- `python3 tools/check_machine_local_paths.py --strict` then passed with `machine_local_paths PASS scanned_files=958`.
- `ctest --test-dir build-codex-smoke --output-on-failure` passed 22/22 tests.
