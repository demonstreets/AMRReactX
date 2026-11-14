#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_VERIFICATION_CHAIN_COVERAGE_REPORT:-docs/codex_audit/evidence/current_verification_chain_coverage_20260803/current_verification_chain_coverage_report.json}

python3 tools/write_current_verification_chain_coverage_report.py --verify-json "$report"
