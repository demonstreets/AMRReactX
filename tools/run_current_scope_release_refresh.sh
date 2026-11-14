#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

log_dir="docs/codex_audit/evidence/current_scope_last_run_20260807"
mkdir -p "$log_dir"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
log="$log_dir/current_scope_verify_after_release_refresh_${stamp}.log"

set +e
bash tools/codex_verify_current_scope.sh > "$log" 2>&1
rc=$?
set -e
echo "CURRENT_SCOPE_RC=$rc" >> "$log"

if [ "$rc" -ne 0 ]; then
    tail -n 120 "$log"
    exit "$rc"
fi

python3 tools/write_current_scope_delivery_package_report.py
bash tools/verify_current_scope_delivery_package.sh
python3 tools/write_current_scope_final_handoff_note_report.py
bash tools/verify_current_scope_final_handoff_note.sh
python3 tools/write_current_operator_quickstart_smoke_report.py
bash tools/verify_current_operator_quickstart_smoke.sh
python3 tools/write_current_phase_closure_certificate_report.py
bash tools/verify_current_phase_closure_certificate.sh
python3 tools/write_strict_master_plan_closeout_action_pack_report.py
bash tools/verify_strict_master_plan_closeout_action_pack.sh
bash tools/run_strict_external_artifact_receiving_preflight.sh
python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py
bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh
python3 tools/write_current_worktree_hygiene_report.py
bash tools/verify_current_worktree_hygiene.sh
python3 tools/write_current_worktree_source_ledger_report.py
bash tools/verify_current_worktree_source_ledger.sh
python3 tools/write_current_case_output_cleanup_manifest_report.py
bash tools/verify_current_case_output_cleanup_manifest.sh
python3 tools/write_sundials_local_link_audit_report.py
bash tools/verify_sundials_local_link_audit.sh
python3 tools/write_current_worktree_review_queue_report.py
bash tools/verify_current_worktree_review_queue.sh
python3 tools/write_current_scope_operator_runbook_report.py
bash tools/verify_current_scope_operator_runbook.sh
python3 tools/write_master_plan_final_readiness_report.py
bash tools/verify_master_plan_final_readiness.sh
python3 tools/write_current_scope_delivery_package_report.py
bash tools/verify_current_scope_delivery_package.sh
python3 tools/write_current_scope_final_handoff_note_report.py
bash tools/verify_current_scope_final_handoff_note.sh
python3 tools/write_current_phase_final_delivery_index_report.py
bash tools/verify_current_phase_final_delivery_index.sh
python3 tools/write_current_worktree_hygiene_report.py
bash tools/verify_current_worktree_hygiene.sh
python3 tools/write_current_worktree_source_ledger_report.py
bash tools/verify_current_worktree_source_ledger.sh
python3 tools/write_current_case_output_cleanup_manifest_report.py
bash tools/verify_current_case_output_cleanup_manifest.sh
python3 tools/write_sundials_local_link_audit_report.py
bash tools/verify_sundials_local_link_audit.sh
python3 tools/write_current_worktree_review_queue_report.py
bash tools/verify_current_worktree_review_queue.sh
python3 tools/write_current_scope_release_refresh_entrypoint_report.py
bash tools/verify_current_scope_release_refresh_entrypoint.sh
python3 tools/write_current_phase_release_manifest_report.py
bash tools/verify_current_phase_release_manifest.sh
python3 tools/write_current_verification_chain_coverage_report.py
bash tools/verify_current_verification_chain_coverage.sh
python3 tools/write_current_scope_state_snapshot_report.py
bash tools/verify_current_scope_state_snapshot.sh
python3 tools/write_current_status_cli_report.py
bash tools/verify_current_status_cli.sh
python3 tools/write_current_report_hash_cycle_guard_report.py
bash tools/verify_current_report_hash_cycle_guard.sh
bash tools/verify_current_phase_release_manifest.sh
bash tools/verify_current_scope_delivery_package.sh
bash tools/verify_current_status_cli.sh
bash tools/verify_current_scope_state_snapshot.sh

printf 'current_scope_release_refresh PASS log=%s\n' "$log"
