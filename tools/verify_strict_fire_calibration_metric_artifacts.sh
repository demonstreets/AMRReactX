#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/strict_fire_calibration_metric_artifacts_20260817/strict_fire_calibration_metric_artifacts_report.json}
python3 tools/write_strict_fire_calibration_metric_artifacts_report.py --verify-json "$json"
echo "[strict-fire-calibration-metric-artifacts] PASS metric artifacts"
