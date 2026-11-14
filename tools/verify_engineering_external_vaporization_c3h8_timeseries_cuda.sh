#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report="docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/engineering_external_vaporization_c3h8_timeseries_cuda_report.json"

if [[ ! -f "$report" ]]; then
  python3 tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py
fi

python3 tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py --verify-json "$report"
