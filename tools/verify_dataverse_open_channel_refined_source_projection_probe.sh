#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root=${CODEX_DATAVERSE_REFINED_SOURCE_PROJECTION_ROOT:-docs/codex_audit/evidence/dataverse_refined_source_projection_probe_mpi_cuda_20260807}
report="$root/dataverse_refined_source_projection_probe_report.json"

if [[ ! -f "$report" ]]; then
  python3 tools/write_dataverse_open_channel_refined_source_projection_probe_report.py
fi

python3 tools/write_dataverse_open_channel_refined_source_projection_probe_report.py --verify-json "$report"

python3 - "$report" <<'PY'
import json
import sys
from pathlib import Path

report = Path(sys.argv[1])
data = json.loads(report.read_text(encoding="utf-8"))
summary = data["summary"]
assert data["status"] == "PASS-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA"
assert summary["mpi_rank_count"] == 2
assert summary["cuda_initialized"] is True
assert summary["run_log_has_no_abort_nan_or_cuda_error"] is True
assert all(abs(float(v) - 0.0125) <= 1.0e-12 for v in summary["dx_m"])
assert abs(float(summary["leak_radius_m"]) - 0.0023) <= 1.0e-15
assert summary["active_volume_equals_single_cell"] is True
assert float(summary["source_cfl"]) < 0.01
assert summary["production_agreement_completed"] is False
assert summary["clears_external_plume_reference_blocker"] is False
print("[dataverse-refined-source-projection-probe] PASS MPI+CUDA refined near-source source-projection screen")
PY
