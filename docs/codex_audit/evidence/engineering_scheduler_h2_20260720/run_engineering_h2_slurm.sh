#!/usr/bin/env bash
#SBATCH --job-name=eng-h2-prod-scout
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00
#SBATCH --output=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/slurm-%j.out

set -euo pipefail
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/../../../.." && pwd)
cd "$repo_root"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OMP_PROC_BIND="${OMP_PROC_BIND:-close}"
export OMP_PLACES="${OMP_PLACES:-cores}"
export JOBS="${JOBS:-4}"
export RUN_TIMEOUT="${RUN_TIMEOUT:-2400}"
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS:-4}"
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP:-200}"
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT:-20}"
export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES="${CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES:-11}"

mkdir -p "docs/codex_audit/evidence/engineering_scheduler_h2_20260720"
finalize_scheduler_report() {
  rc=$?
  python3 tools/sanitize_engineering_scheduler_evidence.py docs/codex_audit/evidence/engineering_scheduler_h2_20260720 || rc=$?
  if [[ $rc -eq 0 ]]; then
    python3 tools/verify_engineering_scheduler_run.py \
      --evidence-dir engineering_scheduler_h2_20260720 \
      --output-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json \
      --output-md docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.md || rc=$?
  else
    python3 tools/verify_engineering_scheduler_run.py \
      --evidence-dir engineering_scheduler_h2_20260720 \
      --output-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json \
      --output-md docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.md \
      --allow-incomplete || true
  fi
  exit $rc
}
trap finalize_scheduler_report EXIT

python3 tools/write_engineering_runtime_affinity_manifest.py \
  --ranks 4 \
  --threads 1 \
  --output-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/runtime_affinity_manifest.json \
  --output-md docs/codex_audit/evidence/engineering_scheduler_h2_20260720/runtime_affinity_manifest.md

python3 tools/run_engineering_h2_campaign.py \
  --campaign engineering-h2-production-scheduler-readiness \
  --suite h2-production-scout \
  --jobs 4 \
  --run-timeout-s 2400 \
  --case-timeout-s 4200 \
  --output-root docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run \
  --output-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run_summary.json \
  --output-md docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run_summary.md

python3 tools/write_engineering_scheduler_campaign_manifest.py --verify-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json