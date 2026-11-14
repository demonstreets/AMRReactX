#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_cuda_20260807/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_report.json

if [[ ! -f "$report" ]]; then
  python3 tools/write_dataverse_open_channel_full_channel_refined_source_dx025_1000step_dt5em6_report.py
fi

python3 tools/write_dataverse_open_channel_full_channel_refined_source_dx025_1000step_dt5em6_report.py --verify-json "$report"

python3 - "$report" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
s = data["summary"]
assert data["status"] == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA"
assert s["full_dataverse_domain"] is True
assert s["mpi_rank_count"] == 2
assert s["cuda_initialized"] is True
assert s["run_log_has_no_abort_nan_or_cuda_error"] is True
assert int(s["max_step"]) == 1000
assert abs(float(s["time_end_s"]) - 0.005) <= 1.0e-12
assert s["clears_external_plume_reference_blocker"] is False
print("[dataverse-full-channel-refined-source-dx025-1000step-dt5em6] PASS MPI+CUDA full-channel refined-source 1000-step dt=5e-6 screen")
PY
