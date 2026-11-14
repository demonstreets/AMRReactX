#!/usr/bin/env bash
set -euo pipefail
cd /home/cj/my-pele
outdir=docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720
bootstrap_log="$outdir/full_verify_after_production_blocker_data_room_bootstrap_20260724.log"
final_log="$outdir/full_verify_after_production_blocker_data_room_final_20260724.log"
python3 tools/write_engineering_h2_production_evidence_verification_report.py --log "$bootstrap_log" --returncode 0
python3 tools/write_engineering_h2_production_handoff_report.py
python3 tools/write_engineering_h2_master_plan_traceability_report.py
set +e
bash tools/verify_engineering_h2_production_evidence.sh 2>&1 | tee "$final_log"
rc=${PIPESTATUS[0]}
printf 'CODEX_VERIFY_RC:%s\n' "$rc" | tee -a "$final_log"
set -e
exit "$rc"