#!/usr/bin/env bash
set -euo pipefail
cd /home/cj/my-pele
outdir=docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720
mkdir -p "$outdir"
bootstrap_log="$outdir/full_verify_after_closure_manifest_bootstrap_20260724.log"
final_log="$outdir/full_verify_after_closure_manifest_final_20260724.log"
set +e
CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE bash tools/verify_engineering_h2_production_evidence.sh 2>&1 | tee "$bootstrap_log"
rc=${PIPESTATUS[0]}
printf 'CODEX_VERIFY_RC:%s\n' "$rc" | tee -a "$bootstrap_log"
set -e
if [ "$rc" -ne 0 ]; then
  exit "$rc"
fi
python3 tools/write_engineering_h2_production_evidence_verification_report.py --log "$bootstrap_log" --returncode "$rc"
python3 tools/write_engineering_h2_production_handoff_report.py
python3 tools/write_engineering_h2_master_plan_traceability_report.py
set +e
bash tools/verify_engineering_h2_production_evidence.sh 2>&1 | tee "$final_log"
rc=${PIPESTATUS[0]}
printf 'CODEX_VERIFY_RC:%s\n' "$rc" | tee -a "$final_log"
set -e
exit "$rc"