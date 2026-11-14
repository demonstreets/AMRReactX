#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root=${CODEX_DATAVERSE_OPEN_CHANNEL_OPEN_BOUNDARY_ORIFICE_EXTENDED_2S_ROOT:-docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807}
report="$root/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_screen_report.json"

if [[ ! -f "$report" ]]; then
  python3 tools/write_dataverse_open_channel_open_boundary_orifice_extended_2s_report.py
fi

python3 tools/write_dataverse_open_channel_open_boundary_orifice_extended_2s_report.py --verify-json "$report"

python3 - "$report" <<'PY'
import json
import sys
from pathlib import Path

report = Path(sys.argv[1])
data = json.loads(report.read_text(encoding="utf-8"))
summary = data["summary"]
assert data["status"] == "PASS-DATAVERSE-OPEN-CHANNEL-OPEN-BOUNDARY-ORIFICE-EXTENDED-2S-MPI-CUDA"
assert summary["mpi_rank_count"] == 2
assert summary["cuda_initialized"] is True
assert summary["plotfile_count"] >= 21
assert summary["sensor_count"] == 29
assert summary["sensor_timeseries_rows"] >= 600
assert abs(float(summary["time_end_s"]) - 2.0) <= 1.0e-12
assert 0.75 <= float(summary["mass_ratio_final"]) <= 1.05
assert float(summary["max_yh2"]) > 0.015
assert float(summary["downstream_fraction"]) > 0.99
assert summary["production_agreement_completed"] is False
assert summary["clears_external_plume_reference_blocker"] is False
print("[dataverse-open-channel-open-boundary-orifice-extended-2s] PASS MPI+CUDA 2.0s open-boundary stability/agreement-screen")
PY
