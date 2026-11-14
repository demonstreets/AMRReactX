# 2026-07-28 Integrated Acceptance Scorecard Closure

## Scope

Codex aligned the engineering H2 evidence ledger with the user-approved
initial integrated acceptance criterion:

- complex obstacle open-area H2 leak, dispersion, ignition, and reacting fire;
- stable CPU, single-CUDA, and MPI+CUDA execution evidence;
- sustained stiff reacting flame development without NaN/Inf or runtime failure;
- conservation and physical sanity checks carried by the referenced reports;
- real CAD import, external plume dataset agreement, calibrated radiation, and
  calibrated overpressure remain deferred full-production certification items.

## Changes

- Updated `tools/write_engineering_production_scorecard.py` so the default
  direct reacting fire evidence points to the 2000-step sustained single-CUDA
  and MPI+CUDA reports.
- Added the integrated initial acceptance report to scorecard evidence hashing,
  summary fields, and markdown output.
- Added the new 2026-07-28 scorecard to
  `tools/verify_engineering_h2_production_evidence.sh`.
- Regenerated downstream blocker/data-room/closure/external-evidence audit
  indexes after upstream hashes changed.
- Removed hard-coded `/home/cj` CUDA/SUNDIALS paths from smoke scripts, replacing
  them with `${HOME}`-based defaults while preserving `CUDA_NVCC` and
  `SUNDIALS_CUDA_DIR` overrides.

## Evidence

- `docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728/h2_integrated_initial_acceptance_report.json`
- `docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.json`
- `docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.md`

Key scorecard fields:

- `engineering_functional_coverage_percent`: `96.9`
- `engineering_production_credibility_percent`: `82.2`
- `engineering_initial_integrated_acceptance`: `true`
- `engineering_h2_integrated_initial_acceptance_status`:
  `PASS-H2-INTEGRATED-ENGINEERING-INITIAL-ACCEPTANCE`
- full production certification remains blocked by real CAD, external plume
  shape/reference data, and calibrated fire-consequence evidence.

## Verification

Server directory: `/home/cj/my-pele`

Commands passed:

```bash
python3 -m py_compile tools/write_engineering_production_scorecard.py
python3 tools/write_engineering_production_scorecard.py \
  --output-json docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.json \
  --output-md docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.md
python3 tools/write_engineering_production_scorecard.py \
  --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.json
bash -n tools/verify_engineering_h2_production_evidence.sh
python3 tools/check_machine_local_paths.py --strict
CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE \
  bash tools/verify_engineering_h2_production_evidence.sh
```

Final unified verification output:

```text
machine_local_paths PASS scanned_files=1052
100% tests passed, 0 tests failed out of 22
[engineering-h2-verify] PASS engineering H2 production evidence verification
```
