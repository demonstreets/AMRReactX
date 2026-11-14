#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_DATAVERSE_OPEN_CHANNEL_PHYSICS_ALIGNMENT_REPORT:-docs/codex_audit/evidence/dataverse_open_channel_physics_alignment_20260804/dataverse_open_channel_physics_alignment_report.json}

python3 tools/write_dataverse_open_channel_physics_alignment_report.py
python3 tools/write_dataverse_open_channel_physics_alignment_report.py --verify-json "$report"

python3 - "$report" <<'PY'
import json
import sys
from pathlib import Path

report = Path(sys.argv[1])
data = json.loads(report.read_text(encoding="utf-8"))
summary = data["summary"]
assert data["status"] == "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS"
assert summary["ready_for_orifice_velocity_scout"] is True
assert summary["ready_for_refined_source_projection"] is True
assert summary["strict_external_plume_blocker_cleared"] is False
assert summary["current_grid_active_cell_count_for_experimental_radius"] == 0
assert summary["current_grid_active_cell_count_for_baseline_radius"] > 0
print("[dataverse-open-channel-physics-alignment] PASS physics alignment diagnosis")
PY
