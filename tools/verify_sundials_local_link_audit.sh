#!/usr/bin/env bash
set -euo pipefail

json="${1:-docs/codex_audit/evidence/sundials_local_link_audit_20260820/sundials_local_link_audit_report.json}"
python3 tools/write_sundials_local_link_audit_report.py --verify-json "$json"
echo "[sundials-local-link-audit] PASS"
