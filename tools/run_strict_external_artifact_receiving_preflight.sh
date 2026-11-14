#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

log_dir="docs/codex_audit/evidence/strict_external_artifact_receiving_preflight_20260820"
mkdir -p "$log_dir"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
log="$log_dir/strict_external_artifact_receiving_preflight_${stamp}.log"

set +e
(
    set -e
    echo "[strict-external-artifact-receiving-preflight] START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    python3 tools/codex_print_strict_external_artifact_drop_index.py
    python3 tools/write_master_plan_strict_artifact_intake_manifest_report.py
    bash tools/verify_master_plan_strict_artifact_intake_manifest.sh
    python3 tools/write_master_plan_strict_artifact_drop_preflight_report.py
    bash tools/verify_master_plan_strict_artifact_drop_preflight.sh
    python3 tools/write_strict_artifact_drop_contract_preflight_report.py
    bash tools/verify_strict_artifact_drop_contract_preflight.sh
    python3 tools/write_strict_external_artifact_drop_index_report.py
    bash tools/verify_strict_external_artifact_drop_index.sh
    python3 tools/write_strict_external_artifact_drop_checklist_report.py
    bash tools/verify_strict_external_artifact_drop_checklist.sh
    python3 tools/write_strict_external_evidence_receiving_pack_report.py
    bash tools/verify_strict_external_evidence_receiving_pack.sh
    python3 tools/write_strict_external_artifact_cn_handoff_report.py
    bash tools/verify_strict_external_artifact_cn_handoff.sh
    python3 tools/write_strict_master_plan_closeout_action_pack_report.py
    bash tools/verify_strict_master_plan_closeout_action_pack.sh
    python3 tools/write_current_status_cli_report.py
    bash tools/verify_current_status_cli.sh
) > "$log" 2>&1
rc=$?
set -e
echo "STRICT_EXTERNAL_ARTIFACT_RECEIVING_PREFLIGHT_RC=$rc" >> "$log"

if [ "$rc" -ne 0 ]; then
    tail -n 120 "$log"
    exit "$rc"
fi

tail -n 80 "$log"
printf 'strict_external_artifact_receiving_preflight PASS log=%s\n' "$log"
