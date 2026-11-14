#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/strict_fire_calibration_source_registry_artifact_20260817/strict_fire_calibration_source_registry_artifact_report.json}

python3 tools/write_strict_fire_calibration_source_registry_artifact_report.py --verify-json "$json"
echo "[strict-fire-calibration-source-registry-artifact] PASS source registry artifact"
