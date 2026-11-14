#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report="docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"

if [[ ! -f "$report" ]]; then
  bash tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh
  python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py
fi

python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py --verify-json "$report"
echo "[engineering-liquefied-release-vaporization-source-model-cuda-smoke] PASS generated-input CUDA smoke report"
