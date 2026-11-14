#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REPORT="docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/h2_fire_plotfile_sensor_sampling_negative_selftest_report.json"

python3 tools/write_h2_fire_plotfile_sensor_sampling_negative_selftest_report.py --verify-json "$REPORT"

echo "[h2-fire-plotfile-sensor-sampling-negative-selftest] PASS negative selftest report"
