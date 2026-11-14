#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_CUDA_REVALIDATION_REPORT:-docs/codex_audit/evidence/master_plan_cuda_revalidation_20260731/master_plan_cuda_revalidation_report.json}

python3 tools/write_master_plan_cuda_revalidation_report.py --verify-json "$report"
echo "[master-plan-cuda-revalidation] PASS CUDA revalidation report verification"
