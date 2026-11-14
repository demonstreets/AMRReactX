#!/usr/bin/env bash
set -euo pipefail

root=${CODEX_DATAVERSE_OPEN_CHANNEL_OPEN_BOUNDARY_ORIFICE_EXTENDED_01S_ROOT:-docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_mpi_cuda_20260805}
report="$root/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_report.json"

python3 tools/write_dataverse_open_channel_cfd_scout_report.py \
  --run-log "$root/run.log" \
  --validation-log "$root/validation.log" \
  --plume-report "$root/h2_plume_observation_report.json" \
  --agreement-attempt "$root/agreement_attempt_status.json" \
  --input "$root/input.dataverse_open_channel_h2_scout_3d" \
  --sensors "$root/sensors.dataverse_open_channel_solver_coords.json" \
  --output-json "$report" \
  --output-md "$root/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_report.md"

python3 tools/write_dataverse_open_channel_cfd_scout_report.py --verify-json "$report"

python3 - "$root" "$report" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
report = Path(sys.argv[2])
data = json.loads(report.read_text(encoding="utf-8"))
summary = data["summary"]
input_text = (root / "input.dataverse_open_channel_h2_scout_3d").read_text(encoding="utf-8")
assert data["status"] == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA"
assert summary["mpi_rank_count"] == 2
assert summary["cuda_initialized"] is True
assert summary["plotfile_count"] >= 11
assert summary["sensor_count"] == 29
assert summary["sensor_timeseries_rows"] >= 319
assert abs(float(summary["time_end_s"]) - 0.1) <= 1.0e-12
assert abs(float(summary["mass_ratio_final"]) - 1.0) <= 1.0e-12
assert float(summary["max_yh2"]) > 0.02
assert float(summary["downstream_fraction"]) > 0.95
assert summary["agreement_attempt_status"] == "failed_expected_for_short_scout"
assert "peleLM.lo_bc = Outflow NoSlipWallAdiab NoSlipWallAdiab" in input_text
assert "peleLM.hi_bc = Outflow NoSlipWallAdiab NoSlipWallAdiab" in input_text
assert "amr.max_step = 1000" in input_text
assert "amr.fixed_dt = 1.000000000000e-04" in input_text
assert "prob.leak_vel_x = 6.567687631723e+02" in input_text
print("[dataverse-open-channel-open-boundary-orifice-extended-01s] PASS MPI+CUDA 0.1s high-momentum stability window")
PY
