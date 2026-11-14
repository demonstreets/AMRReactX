# Academic GPU Environment Preflight

Date: 2026-07-28

Status: `NOT_READY-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT`

Evidence root:

- `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728`

## Scope

This audit records the current GPU runtime state for the academic CUDA detonation path. It is attached to the ACD-10 and QLT-05 later-phase GPU items so those items have reproducible diagnostic evidence instead of an informal "not tested" status.

## Result

The preflight does not grant GPU credit.

- `nvidia-smi` return code: `18`
- Driver/library mismatch detected: `true`
- CUDA detonation smoke return code: `127`
- Smoke finalized with AMReX: `false`
- Missing CUDA runtime/math libraries from the current loader path/cache:
  - `libcurand.so.10`
  - `libcusolver.so.11`
  - `libcusparse.so.12`

The smoke also sees missing GPU-linked SUNDIALS/CUDA libraries before the executable can start the physics solve.

## Evidence

- Runner: `tools/codex_run_academic_gpu_environment_preflight.sh`
- Report writer: `tools/write_academic_gpu_environment_preflight_report.py`
- Report JSON: `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/academic_gpu_environment_preflight_report.json`
- Driver log: `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/nvidia_smi.log`
- Linker log: `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/ldd_cuda_exe.log`
- CUDA library search log: `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/cuda_library_search.log`
- Smoke log: `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/cuda_detonation_smoke/run.log`

## Impact

ACD-10 and QLT-05 remain deferred/not creditable on the current server state. The CPU/MPI academic and engineering evidence remains valid; this preflight only blocks CUDA/GPU credit.

## Recovery

After repairing the NVIDIA driver/library mismatch and installing or exposing the required CUDA runtime libraries, rerun:

```bash
bash tools/codex_run_academic_gpu_environment_preflight.sh
```

Only a `PASS-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT` report should be used to clear ACD-10/QLT-05 GPU credit.
