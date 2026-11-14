#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_CH4_COLD_PLUME_CPU_PROBE_REPORT:-docs/codex_audit/evidence/engineering_ch4_cold_plume_cpu_probe_20260806/engineering_ch4_cold_plume_cpu_probe_report.json}

python3 tools/write_engineering_ch4_cold_plume_cpu_probe_report.py --verify-json "$report"
echo "[engineering-ch4-cold-plume-cpu-probe] PASS CH4 cold plume CPU/MPI/CUDA probe report"
