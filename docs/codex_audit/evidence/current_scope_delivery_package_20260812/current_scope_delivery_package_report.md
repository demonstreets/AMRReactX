# Current-Scope Delivery Package

- Status: `PASS-CURRENT-SCOPE-DELIVERY-PACKAGE`
- Delivery package ready: `True`
- Current scope can be closed now: `True`
- Current scope closeout estimate: `0.5-1 day for final handoff notes and optional fresh smoke reruns`
- Strict master-plan complete: `False`
- Strict completion gate: `AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS`
- Strict completion allowed: `False`
- Strict external artifact drop index: `PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX`
- Strict external artifact drop checklist: `PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST`
- Strict closeout requires external artifacts: `True`
- Open strict blockers: `3`
- Last full current-scope log passed: `True`

## Entrypoints

- `readme`: `README.md`
- `operator_runbook`: `docs/codex_audit/current_scope_operator_runbook.md`
- `user_guides_index`: `docs/user_guides/README.md`
- `user_guides_index_report`: `docs/codex_audit/evidence/user_guides_index_20260818/user_guides_index_report.json`
- `user_guides_index_verify`: `bash tools/verify_user_guides_index.sh`
- `complete_walkthrough_guide`: `docs/user_guides/从目录到排错_完整运行教程.md`
- `real_case_intake_guide`: `docs/user_guides/真实工程资料交付与复验清单.md`
- `strict_external_artifact_cn_handoff_guide`: `docs/user_guides/真实资料投递清单_按文件路径.md`
- `strict_external_artifact_cn_handoff_report`: `docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/strict_external_artifact_cn_handoff_report.json`
- `strict_external_artifact_cn_handoff_verify`: `bash tools/verify_strict_external_artifact_cn_handoff.sh`
- `status_cli_text`: `python3 tools/codex_print_current_status.py`
- `status_cli_json`: `python3 tools/codex_print_current_status.py --json`
- `full_current_scope_verification`: `bash tools/codex_verify_current_scope.sh`

## Required Commands

- `bash tools/codex_verify_current_scope.sh`
- `python3 tools/codex_print_current_status.py`
- `python3 tools/codex_print_current_status.py --json`
- `python3 tools/write_current_scope_release_candidate_handoff_report.py`
- `bash tools/verify_current_scope_release_candidate_handoff.sh`
- `python3 tools/write_project_closeout_forecast_report.py`
- `bash tools/verify_project_closeout_forecast.sh`
- `python3 tools/write_strict_master_plan_completion_gate_report.py`
- `bash tools/verify_strict_master_plan_completion_gate.sh`
- `python3 tools/write_strict_external_artifact_drop_index_report.py`
- `bash tools/verify_strict_external_artifact_drop_index.sh`
- `python3 tools/write_strict_external_artifact_drop_checklist_report.py`
- `bash tools/verify_strict_external_artifact_drop_checklist.sh`
- `python3 tools/write_strict_external_artifact_cn_handoff_report.py`
- `bash tools/verify_strict_external_artifact_cn_handoff.sh`
- `python3 tools/write_user_guides_index_report.py`
- `bash tools/verify_user_guides_index.sh`
- `python3 tools/write_current_scope_delivery_package_report.py`
- `bash tools/verify_current_scope_delivery_package.sh`

## Can Claim For Current Scope

- current engineering and academic priority scenarios are verified by the current-scope chain
- CPU/MPI, single GPU, and MPI+CUDA readiness are represented in the current parallel matrix
- H2, CH4, and C3H8 gas-source workflows are represented by current templates
- LNG_CH4 and LPG_C3H8 liquefied release workflows are screening/external-source ready

## Do Not Claim

- full strict master-plan completion
- production CFD-internal liquid flashing or pool evaporation
- calibrated fire radiation/overpressure consequence prediction
- validated real-CAD cleanup and boundary tagging on user-provided plant geometry
- external plume-shape agreement against a passing public dataset
