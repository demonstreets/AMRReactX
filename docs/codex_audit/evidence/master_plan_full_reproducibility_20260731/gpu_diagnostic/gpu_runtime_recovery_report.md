# GPU Runtime Recovery Report

- Status: `PASS-MASTER-PLAN-GPU-RUNTIME-READY`
- Current CUDA runtime ready: `True`
- CUDA require-preflight exitcode: `0`
- Kernel module version: `580.173.02`
- NVML user-space version: `580.173.02`
- `modinfo nvidia` version: `580.173.02`
- Device users detected: `True`
- Recommended action: `no_reload_required_runtime_versions_match`

Reboot the server or, with administrator approval and after confirming no GPU users, reload the NVIDIA kernel modules so the loaded kernel module matches the 580.173 user-space NVML libraries. After recovery, rerun tools/codex_preflight_environment.sh --require-cuda and the relevant CUDA smoke/engineering GPU cases.

GPU device users were detected; do not hot reload until those jobs are stopped.
