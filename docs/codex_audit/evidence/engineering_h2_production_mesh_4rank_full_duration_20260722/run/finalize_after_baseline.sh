#!/usr/bin/env bash
set -euo pipefail
cd /home/cj/my-pele
RUN_DIR=docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run
EVID_DIR=docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722
CAMPAIGN_DIR=docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722
CANDIDATE_DIR=docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722
MATRIX_DIR=docs/codex_audit/evidence/engineering_h2_acceptance_matrix_20260720
SCORECARD_DIR=docs/codex_audit/evidence/engineering_production_scorecard_20260720
pid_file="$RUN_DIR/baseline_repair.pid"
echo "[$(date -u +%FT%TZ)] finalize waiting for baseline repair pid_file=$pid_file"
while true; do
  pid=$(cat "$pid_file" 2>/dev/null || true)
  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    break
  fi
  last_step=$(grep 'STEP \[' "$RUN_DIR/baseline/run.log" 2>/dev/null | tail -n 1 | sed -E 's/.*STEP \[([0-9]+)\].*/\1/' || true)
  plots=$(find "$RUN_DIR/baseline/run" -maxdepth 1 -type d -name 'plt*' 2>/dev/null | wc -l)
  echo "[$(date -u +%FT%TZ)] baseline_repair_running pid=$pid step=${last_step:-unknown} plotfiles=$plots"
  sleep 60
done
echo "[$(date -u +%FT%TZ)] baseline repair process ended; checking evidence"
for d in baseline amr; do
  plots=$(find "$RUN_DIR/$d/run" -maxdepth 1 -type d -name 'plt*' 2>/dev/null | wc -l)
  echo "$d plotfiles=$plots"
  test "$plots" -ge 31
  test -d "$RUN_DIR/$d/run/plt07200"
  grep -q 'Final simulation time: 7.2' "$RUN_DIR/$d/run.log"
  grep -q 'AMReX .* finalized' "$RUN_DIR/$d/run.log"
  grep -q 'PASS' "$RUN_DIR/$d/validation.log"
  grep -q 'PASS' "$RUN_DIR/$d/profile_validation.log"
  grep -q 'PASS' "$RUN_DIR/$d/hazard_summary.log"
  grep -q 'PASS' "$RUN_DIR/$d/hazard_planes.log"
  grep -q 'PASS' "$RUN_DIR/$d/hazard_timeseries.log"
done
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_REUSE_EXISTING=TRUE
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS=4
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP=7200
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT=240
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES=31
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LOG_DIR="$RUN_DIR"
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLANE_MASS_FRACTION=0.01
export CODEX_H2_LEAK_PLAN_AMR_N_CELL="64 32 32"
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_BASE_MAX_GRID_SIZE=16
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LEVEL1_MAX_GRID_SIZE=16
export RUN_TIMEOUT=43200
export JOBS=8
bash tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh
python3 tools/write_engineering_h2_production_scale_scout_report.py \
  --source-root "$RUN_DIR" \
  --evidence-root "$EVID_DIR" \
  --case-name h2-open-domain-plan-amr-mpi-production-mesh-4rank-7200step-full-duration \
  --title H2-Production-Mesh-4Rank-7200-Step-Full-Duration-Report \
  --status PASS-STABILITY \
  --min-ranks 4 \
  --min-max-step 7200 \
  --min-base-cells 65536 \
  --min-equivalent-fine-cells 524288 \
  --min-plotfiles 31 \
  --max-cloud-rel-diff 0.25 \
  --max-peak-rel-diff 0.25 \
  --max-mean-ncells-ratio 10.0 \
  --max-advance-seconds-ratio 25.0 \
  --output-json "$EVID_DIR/production_mesh_4rank_full_duration_report.json" \
  --output-md "$EVID_DIR/production_mesh_4rank_full_duration_report.md"
python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json "$EVID_DIR/production_mesh_4rank_full_duration_report.json"
python3 tools/write_engineering_h2_production_mesh_campaign_report.py \
  --output-json "$CAMPAIGN_DIR/production_mesh_campaign_report.json" \
  --output-md "$CAMPAIGN_DIR/production_mesh_campaign_report.md"
python3 tools/write_engineering_h2_production_mesh_campaign_report.py --verify-json "$CAMPAIGN_DIR/production_mesh_campaign_report.json"
python3 tools/write_engineering_h2_full_duration_candidate_report.py \
  --output-json "$CANDIDATE_DIR/full_duration_candidate_report.json" \
  --output-md "$CANDIDATE_DIR/full_duration_candidate_report.md"
python3 tools/write_engineering_h2_full_duration_candidate_report.py --verify-json "$CANDIDATE_DIR/full_duration_candidate_report.json"
python3 tools/write_engineering_h2_acceptance_matrix.py \
  --output-json "$MATRIX_DIR/engineering_h2_acceptance_matrix.json" \
  --output-md "$MATRIX_DIR/engineering_h2_acceptance_matrix.md"
python3 tools/write_engineering_h2_acceptance_matrix.py --verify-json "$MATRIX_DIR/engineering_h2_acceptance_matrix.json"
python3 tools/write_engineering_production_scorecard.py \
  --output-json "$SCORECARD_DIR/engineering_production_scorecard.json" \
  --output-md "$SCORECARD_DIR/engineering_production_scorecard.md"
python3 tools/write_engineering_production_scorecard.py --verify-json "$SCORECARD_DIR/engineering_production_scorecard.json"
CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/run_engineering_h2_production_evidence_verification_archive.sh
echo "[$(date -u +%FT%TZ)] FINALIZE_PASS"
python3 - <<'PY'
import json, pathlib
p=pathlib.Path('docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json')
j=json.loads(p.read_text())
print('scorecard_status', j.get('status'))
print('functional_score', j.get('functional_score'))
print('production_score', j.get('production_score'))
print('blockers', j.get('blockers'))
PY