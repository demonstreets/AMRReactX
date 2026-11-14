# Engineering H2 Full-Duration Candidate

Status: `PASS-FULL-DURATION-EXECUTED`
Candidate tier: `full_duration_execution_candidate`
Executed: `True`
Clears stability-duration blocker: `True`

## Target

- Ranks: `4`
- Max step: `7200`
- Plot interval: `240`
- Expected plotfiles per case: `31`
- Expected simulation time: `7.2` s

## Resource Preflight

- Free GB: `162.41`
- Required free GB: `20.0`
- Disk preflight passed: `True`

## Blocking Gaps

- none

## Command

```bash
env CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS=4 CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP=7200 CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT=240 CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES=31 RUN_TIMEOUT=43200 JOBS=8 CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LOG_DIR=docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run bash tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh
```

## Executed Evidence

- Run root: `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run`
- Summary CSV: `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run/reduced_long_summary.csv`
- Engineering case report: `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run/engineering_case_report.json`
