#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/strict_external_plume_source_separation_audit_20260817/strict_external_plume_source_separation_audit_report.json}

python3 tools/write_strict_external_plume_source_separation_audit_report.py --verify-json "$json"
echo "[strict-external-plume-source-separation-audit] PASS source separation audit"
