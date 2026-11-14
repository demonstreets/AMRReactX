#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/strict_external_artifact_cross_benchmark_alias_selftest_20260817/strict_external_artifact_cross_benchmark_alias_selftest_report.json}

python3 tools/write_strict_external_artifact_cross_benchmark_alias_selftest_report.py --verify-json "$json"
echo "[strict-external-artifact-cross-benchmark-alias-selftest] PASS cross-benchmark alias selftest"
