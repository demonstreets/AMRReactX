#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_GPU_RUNTIME_RECOVERY_REPORT:-docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/gpu_diagnostic/gpu_runtime_recovery_report.json}

python3 tools/write_master_plan_gpu_runtime_recovery_report.py --verify-json "$report"
echo "[master-plan-gpu-runtime] PASS GPU runtime recovery report verification"
