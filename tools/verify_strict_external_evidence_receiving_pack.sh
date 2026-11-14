#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/strict_external_evidence_receiving_pack_report.json}"
python3 tools/write_strict_external_evidence_receiving_pack_report.py --verify-json "$json"
echo "[strict-external-evidence-receiving-pack] PASS receiving pack"
