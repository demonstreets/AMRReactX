# Checkpoint: engineering H2 case report packaging

Date: 2026-07-20

## Context

User priority is engineering production readiness first. The reduced-long H2 open-domain plan-AMR MPI gate produced useful evidence, but the artifacts were still scattered across logs and CSVs. Production handoff needs one validated report artifact that records the case, core metrics, limitations, and hashes for reproducibility.

## Changes

- Added `tools/write_engineering_h2_case_report.py`.
- The tool validates an evidence root containing `reduced_long_summary.csv`, `plan_amr_compare_summary.csv`, `amr_overhead_summary.csv`, generated inputs, baseline/AMR MPI logs, and plume/profile/hazard logs.
- It fails on missing files, missing `PASS` lines, nonfinite metrics, weak final hazard metrics, missing dynamic AMR evidence, or run-log failure markers.
- It writes `engineering_case_report.json` and `engineering_case_report.md` with run summary, hazard metrics, AMR overhead, limitations, and SHA-256 hashes for generated inputs and summary CSVs.
- Integrated the report generator into `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh`, so the reduced-long gate now emits report artifacts automatically.

## Evidence

Evidence root: `/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720`.

Integrated gate result:

```text
engineering_h2_case_report PASS case=h2-open-domain-plan-amr-mpi-reduced-long root=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720 json=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720/engineering_case_report.json md=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720/engineering_case_report.md
[codex-smoke] PASS h2_leak open-domain plan-AMR MPI reduced-long root=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720 summary=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720/reduced_long_summary.csv report_json=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720/engineering_case_report.json report_md=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720/engineering_case_report.md
```

JSON spot-check:

```text
status=PASS
case=h2-open-domain-plan-amr-mpi-reduced-long
ranks=4
max_step=200
amr_final_cloud=0.0382080078125
cloud_rel_diff=0.130990415
inputs=2
evidence_files=amr_overhead_summary.csv,plan_amr_compare_summary.csv,reduced_long_summary.csv
```

Markdown spot-check confirms the report includes run summary, hazard metrics, AMR overhead ratios, evidence hashes, and limitations.

## Verification

- `python3 -m py_compile tools/write_engineering_h2_case_report.py`
- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh`
- `CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_REUSE_EXISTING=TRUE CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_LOG_DIR=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720 bash tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh`
- JSON field spot-check via Python
- Markdown first 80 lines inspected
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=954`
- `ctest --test-dir build-codex-smoke --output-on-failure`: `100% tests passed, 0 tests failed out of 22`

## Remaining risk

This improves engineering evidence packaging, not the physical model itself. It does not prove production-size releases, real CAD/tank-farm layouts, scheduler/affinity behavior, overnight stability, fire heat-release validation, or reference-data accuracy.
