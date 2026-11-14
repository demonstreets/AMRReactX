#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_STRICT_ARTIFACT_DROP_CONTRACT_SELFTEST_REPORT:-docs/codex_audit/evidence/strict_artifact_drop_contract_selftest_20260803/strict_artifact_drop_contract_selftest_report.json}

python3 tools/write_strict_artifact_drop_contract_selftest_report.py --verify-json "$report"
