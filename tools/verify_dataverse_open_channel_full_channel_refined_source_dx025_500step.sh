#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_500step_mpi_cuda_20260807/dataverse_full_channel_refined_source_dx025_500step_report.json

if [[ ! -f "$report" ]]; then
  python3 tools/write_dataverse_open_channel_full_channel_refined_source_dx025_500step_report.py
fi

python3 tools/write_dataverse_open_channel_full_channel_refined_source_dx025_500step_report.py --verify-json "$report"

python3 - "$report" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
s = data["summary"]
assert data["status"] == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-500STEP-MPI-CUDA"
assert s["full_dataverse_domain"] is True
assert s["mpi_rank_count"] == 2
assert s["cuda_initialized"] is True
assert s["run_log_has_no_abort_nan_or_cuda_error"] is True
assert int(s["max_step"]) == 500
assert s["clears_external_plume_reference_blocker"] is False
print("[dataverse-full-channel-refined-source-dx025-500step] PASS MPI+CUDA full-channel refined-source 500-step screen")
PY
