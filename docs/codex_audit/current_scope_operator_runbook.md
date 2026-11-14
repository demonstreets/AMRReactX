> **2026-09-09 审查修正：旧 PASS 不代表当前物理验收。** 7–8 月的汇总、认证与并行能力报告保留为历史记录；其中冷流热点、零反应机理和缺失全场数据的结论已被独立审查否定或降级。当前依据为 [修复说明与复验方法](repair_20260909.md)。本轮不开展真实 CAD 接入及实际三维泄漏/火灾算例验证。VOF 混合物闭合、PLIC 主推进和气液爆轰完整认证仍不完备。

# Current-Scope Operator Runbook

This runbook records the current evidence-backed operating path for `/home/cj/my-pele`.
It is intentionally narrower than the original strict master plan: it covers the current
engineering and academic scope that has reproducible evidence on this server, while
keeping strict external-artifact blockers explicit.

## Runtime Environment

Run commands from the repository root:

```bash
cd /home/cj/my-pele
```

For CUDA/SUNDIALS runs, use the recovered CUDA runtime:

```bash
export PATH=/usr/local/cuda-12.6/bin:$PATH
export SUNDIALS_CUDA_DIR="${SUNDIALS_CUDA_DIR:-${HOME}/.local/sundials-cuda-6.4.1}"
export SUNDIALS_DIR="$SUNDIALS_CUDA_DIR"
export AMREX_SUNDIALS_HOME="$SUNDIALS_CUDA_DIR"
export LD_LIBRARY_PATH="$SUNDIALS_CUDA_DIR/lib:/usr/local/cuda-12.6/lib64:${LD_LIBRARY_PATH:-}"
```

## Fast Status Checks

Use these checks when you want to confirm the current accepted state without rerunning
the expensive CFD cases:

```bash
python3 tools/codex_print_current_status.py
python3 tools/codex_print_current_status.py --json
bash tools/codex_verify_current_scope.sh
```

Use this wrapper when you want to run full verification and refresh the delivery
handoff reports against that new passing log:

```bash
bash tools/run_current_scope_release_refresh.sh
```

Expanded dependency order:

```bash
python3 tools/check_machine_local_paths.py --strict
python3 tools/codex_print_current_status.py
python3 tools/codex_print_current_status.py --json
python3 tools/write_current_parallel_capability_matrix_report.py
bash tools/verify_current_parallel_capability_matrix.sh
python3 tools/write_strict_master_plan_unblock_runbook_report.py
bash tools/verify_strict_master_plan_unblock_runbook.sh
python3 tools/write_strict_unblock_command_inventory_report.py
bash tools/verify_strict_unblock_command_inventory.sh
python3 tools/write_strict_artifact_template_lint_report.py
bash tools/verify_strict_artifact_template_lint.sh
python3 tools/write_strict_artifact_drop_contract_preflight_report.py
bash tools/verify_strict_artifact_drop_contract_preflight.sh
python3 tools/write_strict_artifact_drop_contract_selftest_report.py
bash tools/verify_strict_artifact_drop_contract_selftest.sh
python3 tools/write_master_plan_final_readiness_report.py
bash tools/verify_master_plan_final_readiness.sh
bash tools/verify_master_plan_current_scope.sh
python3 tools/write_master_plan_current_scope_verification_report.py
bash tools/verify_master_plan_current_scope_verification.sh
python3 tools/write_master_plan_completion_audit_report.py
bash tools/verify_master_plan_completion_audit.sh
python3 tools/write_current_worktree_hygiene_report.py
bash tools/verify_current_worktree_hygiene.sh
python3 tools/write_current_worktree_source_ledger_report.py
bash tools/verify_current_worktree_source_ledger.sh
python3 tools/write_current_worktree_review_queue_report.py
bash tools/verify_current_worktree_review_queue.sh
python3 tools/write_current_case_output_cleanup_manifest_report.py
bash tools/verify_current_case_output_cleanup_manifest.sh
python3 tools/write_current_disk_usage_manifest_report.py
bash tools/verify_current_disk_usage_manifest.sh
python3 tools/write_current_disk_cleanup_plan_report.py
bash tools/verify_current_disk_cleanup_plan.sh
python3 tools/write_current_operator_command_inventory_report.py
bash tools/verify_current_operator_command_inventory.sh
python3 tools/write_current_scope_release_candidate_handoff_report.py
bash tools/verify_current_scope_release_candidate_handoff.sh
python3 tools/write_project_closeout_forecast_report.py
bash tools/verify_project_closeout_forecast.sh
python3 tools/write_strict_master_plan_completion_gate_report.py
bash tools/verify_strict_master_plan_completion_gate.sh
python3 tools/write_strict_external_artifact_drop_index_report.py
bash tools/verify_strict_external_artifact_drop_index.sh
python3 tools/codex_print_strict_external_artifact_drop_index.py
python3 tools/codex_print_strict_external_artifact_drop_index.py --json
python3 tools/write_strict_external_artifact_drop_index_cli_report.py
bash tools/verify_strict_external_artifact_drop_index_cli.sh
python3 tools/write_strict_external_artifact_drop_checklist_report.py
bash tools/verify_strict_external_artifact_drop_checklist.sh
python3 tools/write_strict_external_artifact_cn_handoff_report.py
bash tools/verify_strict_external_artifact_cn_handoff.sh
python3 tools/write_strict_external_artifact_progress_selftest_report.py
bash tools/verify_strict_external_artifact_progress_selftest.sh
python3 tools/write_strict_master_plan_closeout_action_pack_report.py
bash tools/verify_strict_master_plan_closeout_action_pack.sh
python3 tools/write_complete_walkthrough_guide_report.py
bash tools/verify_complete_walkthrough_guide.sh
python3 tools/write_current_scope_delivery_package_report.py
bash tools/verify_current_scope_delivery_package.sh
python3 tools/write_project_closeout_acceptance_gate_report.py
bash tools/verify_project_closeout_acceptance_gate.sh
python3 tools/write_current_scope_final_handoff_note_report.py
bash tools/verify_current_scope_final_handoff_note.sh
python3 tools/write_current_operator_quickstart_smoke_report.py
bash tools/verify_current_operator_quickstart_smoke.sh
python3 tools/write_current_phase_closure_certificate_report.py
bash tools/verify_current_phase_closure_certificate.sh
python3 tools/write_current_worktree_hygiene_report.py
bash tools/verify_current_worktree_hygiene.sh
python3 tools/write_current_phase_release_manifest_report.py
bash tools/verify_current_phase_release_manifest.sh
python3 tools/write_current_scope_release_refresh_entrypoint_report.py
bash tools/verify_current_scope_release_refresh_entrypoint.sh
python3 tools/write_current_verification_chain_coverage_report.py
bash tools/verify_current_verification_chain_coverage.sh
python3 tools/write_current_status_cli_report.py
bash tools/verify_current_status_cli.sh
python3 tools/write_current_scope_state_snapshot_report.py
bash tools/verify_current_scope_state_snapshot.sh
python3 tools/write_current_report_hash_cycle_guard_report.py
bash tools/verify_current_report_hash_cycle_guard.sh
```

Expected current-scope result:

```text
PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX
PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK
PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS
PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION
PASS-CURRENT-STATUS-CLI
AUDITED-CURRENT-WORKTREE-HYGIENE
AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER
AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST
AUDITED-CURRENT-DISK-USAGE-MANIFEST
AUDITED-CURRENT-DISK-CLEANUP-PLAN
PASS-CURRENT-OPERATOR-COMMAND-INVENTORY
PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF
PASS-PROJECT-CLOSEOUT-FORECAST
PASS-CURRENT-SCOPE-DELIVERY-PACKAGE
PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE
PASS-CURRENT-SCOPE-RELEASE-REFRESH-ENTRYPOINT
PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE
PASS-STRICT-UNBLOCK-COMMAND-INVENTORY
PASS-STRICT-ARTIFACT-TEMPLATE-LINT
PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT
PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST
PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF
PASS-CURRENT-SCOPE-STATE-SNAPSHOT
AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE
```

## Capability Matrix

The current capability matrix is the authoritative CPU/GPU/MPI status summary:

```bash
python3 tools/write_current_parallel_capability_matrix_report.py
bash tools/verify_current_parallel_capability_matrix.sh
```

Report:

```text
docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json
docs/codex_audit/evidence/master_plan_final_readiness_20260731/master_plan_final_readiness_report.json
docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/master_plan_current_scope_verification_report.json
docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json
docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json
docs/codex_audit/evidence/current_worktree_source_ledger_20260803/current_worktree_source_ledger_report.json
docs/codex_audit/evidence/current_worktree_review_queue_20260820/current_worktree_review_queue_report.json
docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/current_case_output_cleanup_manifest_report.json
docs/codex_audit/evidence/current_disk_usage_manifest_20260803/current_disk_usage_manifest_report.json
docs/codex_audit/evidence/current_disk_cleanup_plan_20260803/current_disk_cleanup_plan_report.json
docs/codex_audit/evidence/current_operator_command_inventory_20260803/current_operator_command_inventory_report.json
docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json
docs/codex_audit/evidence/current_verification_chain_coverage_20260803/current_verification_chain_coverage_report.json
docs/codex_audit/evidence/strict_unblock_command_inventory_20260803/strict_unblock_command_inventory_report.json
docs/codex_audit/evidence/strict_artifact_template_lint_20260803/strict_artifact_template_lint_report.json
docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/strict_artifact_drop_contract_preflight_report.json
docs/codex_audit/evidence/strict_artifact_drop_contract_selftest_20260803/strict_artifact_drop_contract_selftest_report.json
docs/codex_audit/evidence/current_scope_state_snapshot_20260803/current_scope_state_snapshot_report.json
```

The matrix requires all current scenario families to be ready for:

- CPU/MPI
- Single CUDA GPU
- Multi-GPU MPI+CUDA

Current scenario families:

- Engineering H2 leak, dispersion, ignition, and reacting pipe-rack fire.
- Engineering multi-fuel gas-source, gasified LNG/LPG surrogate, and screening
  external-vaporization workflows.
- Academic gas-phase detonation.
- Academic gas-liquid/two-phase reacting droplet/spray detonation-adjacent capability.

## Current-Scope Release Candidate Handoff

Use this report when handing the current priority scope to an operator:

```bash
python3 tools/write_current_scope_release_candidate_handoff_report.py
bash tools/verify_current_scope_release_candidate_handoff.sh
```

Report:

```text
docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json
```

Boundary:

```text
release-candidate handoff ready: yes
release-candidate usable for current priority scope: yes
release-candidate is full strict master-plan completion: no
```

## Current-Scope Final Handoff Note

Use these reports when handing the current usable scope to an operator:

```bash
python3 tools/write_project_closeout_forecast_report.py
bash tools/verify_project_closeout_forecast.sh
python3 tools/write_strict_master_plan_completion_gate_report.py
bash tools/verify_strict_master_plan_completion_gate.sh
python3 tools/write_strict_external_artifact_drop_index_report.py
bash tools/verify_strict_external_artifact_drop_index.sh
python3 tools/codex_print_strict_external_artifact_drop_index.py
python3 tools/codex_print_strict_external_artifact_drop_index.py --json
python3 tools/write_strict_external_artifact_drop_index_cli_report.py
bash tools/verify_strict_external_artifact_drop_index_cli.sh
python3 tools/write_strict_external_artifact_drop_checklist_report.py
bash tools/verify_strict_external_artifact_drop_checklist.sh
python3 tools/write_strict_external_artifact_cn_handoff_report.py
bash tools/verify_strict_external_artifact_cn_handoff.sh
python3 tools/write_strict_external_artifact_progress_selftest_report.py
bash tools/verify_strict_external_artifact_progress_selftest.sh
python3 tools/write_strict_master_plan_closeout_action_pack_report.py
bash tools/verify_strict_master_plan_closeout_action_pack.sh
python3 tools/write_current_scope_delivery_package_report.py
bash tools/verify_current_scope_delivery_package.sh
python3 tools/write_project_closeout_acceptance_gate_report.py
bash tools/verify_project_closeout_acceptance_gate.sh
python3 tools/write_current_scope_final_handoff_note_report.py
bash tools/verify_current_scope_final_handoff_note.sh
python3 tools/write_current_operator_quickstart_smoke_report.py
bash tools/verify_current_operator_quickstart_smoke.sh
python3 tools/write_current_phase_closure_certificate_report.py
bash tools/verify_current_phase_closure_certificate.sh
python3 tools/write_current_worktree_hygiene_report.py
bash tools/verify_current_worktree_hygiene.sh
python3 tools/write_current_phase_release_manifest_report.py
bash tools/verify_current_phase_release_manifest.sh
```

Reports:

```text
Project Closeout Forecast
Strict Master-Plan Completion Gate
Strict External Artifact Drop Index
Strict External Artifact Drop Checklist
Strict External Artifact Chinese Handoff
Strict External Artifact Progress Selftest
Strict Master-Plan Closeout Action Pack
Project Closeout Acceptance Gate
Current-Scope Delivery Package
Current Operator Quickstart Smoke
Current Phase Closure Certificate
Current Phase Release Manifest
Current Phase Final Delivery Index
docs/codex_audit/evidence/project_closeout_forecast_20260812/project_closeout_forecast_report.json
docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/strict_master_plan_completion_gate_report.json
docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/strict_external_artifact_drop_index_report.json
docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/strict_external_artifact_drop_checklist_report.json
docs/user_guides/真实资料投递清单_按文件路径.md
docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/strict_external_artifact_cn_handoff_report.json
docs/codex_audit/evidence/strict_external_artifact_progress_selftest_20260812/strict_external_artifact_progress_selftest_report.json
docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.json
docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/project_closeout_acceptance_gate_report.json
docs/codex_audit/evidence/current_scope_delivery_package_20260812/current_scope_delivery_package_report.json
docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/current_operator_quickstart_smoke_report.json
docs/codex_audit/evidence/current_phase_closure_certificate_20260812/current_phase_closure_certificate_report.json
docs/codex_audit/evidence/current_phase_release_manifest_20260812/current_phase_release_manifest_report.json
docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/current_phase_final_delivery_index_report.json
docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/current_scope_final_handoff_note_report.json
```

Boundary:

```text
current scope can be closed now: yes
strict master-plan can be closed now: no
strict completion allowed: no
strict closeout requires external artifacts: yes
真实资料投递清单_按文件路径
strict external artifact Chinese handoff ready: yes
```

## Current-Scope Release Refresh

Use this wrapper to run the full current-scope chain, save a timestamped log, and
refresh the delivery package, final handoff note, state snapshot, and status CLI
against that latest passing log:

```bash
bash tools/run_current_scope_release_refresh.sh
python3 tools/write_current_scope_release_refresh_entrypoint_report.py
bash tools/verify_current_scope_release_refresh_entrypoint.sh
```

Report:

```text
docs/codex_audit/evidence/current_scope_release_refresh_entrypoint_20260812/current_scope_release_refresh_entrypoint_report.json
```

## Fuel And Liquefied-Gas Boundary

Use the status CLI before changing fuel species, LNG/LPG surrogate inputs, or
external vaporization schedules:

```bash
python3 tools/codex_print_current_status.py
python3 tools/codex_print_current_status.py --json
python3 tools/write_current_status_cli_report.py
bash tools/verify_current_status_cli.sh
```

Focused multi-fuel and liquefied-source evidence rebuilds:

```bash
python3 tools/write_engineering_multi_fuel_capability_boundary_report.py
bash tools/verify_engineering_multi_fuel_capability_boundary.sh
python3 tools/write_engineering_multi_fuel_operator_runbook_report.py
bash tools/verify_engineering_multi_fuel_operator_runbook.sh
python3 tools/write_engineering_multi_fuel_template_catalog_report.py
bash tools/verify_engineering_multi_fuel_template_catalog.sh
bash tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh
python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py
bash tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh
python3 tools/write_engineering_liquefied_release_source_balance_report.py
bash tools/verify_engineering_liquefied_release_source_balance.sh
python3 tools/write_engineering_liquefied_release_source_balance_negative_selftest_report.py
bash tools/verify_engineering_liquefied_release_source_balance_negative_selftest.sh
python3 tools/write_engineering_liquefied_release_thermal_plausibility_report.py
bash tools/verify_engineering_liquefied_release_thermal_plausibility.sh
python3 tools/write_engineering_liquefied_breach_source_contract_report.py
bash tools/verify_engineering_liquefied_breach_source_contract.sh
python3 tools/write_engineering_liquefied_breach_preset_templates_report.py
bash tools/verify_engineering_liquefied_breach_preset_templates.sh
python3 tools/write_engineering_multifuel_liquefied_user_answer_report.py
bash tools/verify_engineering_multifuel_liquefied_user_answer.sh
python3 tools/write_engineering_liquefied_phase_change_overclaim_guard_report.py
bash tools/verify_engineering_liquefied_phase_change_overclaim_guard.sh
```

Authoritative reports:

```text
docs/codex_audit/engineering_multi_fuel_operator_runbook.md
docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json
docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806/engineering_multi_fuel_operator_runbook_report.json
docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/engineering_multi_fuel_template_catalog_report.json
docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json
docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/engineering_liquefied_release_source_balance_report.json
docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/engineering_liquefied_release_source_balance_negative_selftest_report.json
docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/engineering_liquefied_release_thermal_plausibility_report.json
docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/engineering_liquefied_breach_source_contract_report.json
docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/engineering_liquefied_breach_preset_templates_report.json
docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811/engineering_multifuel_liquefied_user_answer_report.json
docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811/engineering_liquefied_phase_change_overclaim_guard_report.json
docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json
```

Engineering Multifuel And Liquefied-Gas User Answer:

```text
can_compute_liquefied_tank_breach_vaporization
```

Current supported gas-source boundary:

- H2 remains the primary engineering current-scope fuel.
- CH4 gas/fire probes are evidence-backed.
- C3H8 gas/fire probes are evidence-backed.
- Multi-fuel input templates are cataloged and self-checked.
- Gasified LNG surrogate boundaries are evidence-backed.
- Gasified LPG surrogate boundaries are evidence-backed.
- Multi-fuel external vaporization CUDA inputs are evidence-backed.
- Liquefied-release source-model CUDA smoke checks are evidence-backed.
- Liquefied-release source balance checks are evidence-backed.
- Liquefied-release source balance negative selftest guards are evidence-backed.
- Liquefied-release thermal plausibility checks are evidence-backed.
- Liquefied LNG/LPG breach-to-gas-source contracts are evidence-backed.
- Operator-editable LNG/LPG breach preset JSONs are evidence-backed:
  `examples/engineering/h2_leak_3d/liquefied_breach_presets/`.
- Liquefied phase-change overclaim guard is evidence-backed.

Current explicit non-claims:

```text
liquefied release source balance negative cases rejected: 5/5
liquefied release source guard negative mdot: yes
liquefied release source guard species drift: yes
liquefied release source guard schedule mismatch: yes
liquefied release source guard phase-change overclaim: yes
liquefied release source guard generated-input species mismatch: yes
liquefied release thermal plausibility ready: yes
liquefied release vaporized fraction formula: yes
liquefied release heat loads positive: yes
liquefied breach source contract ready: yes
liquefied breach source contract generates external gas source: yes
liquefied breach preset templates ready: yes
liquefied breach preset templates generate CFD CSV: yes
liquefied phase-change overclaim guard ready: yes
liquefied production phase-change claim allowed: no
liquefied CFD solves liquid phase-change: no
liquefied CFD solves flashing discharge: no
internal liquid phase-change CFD: no
multi-fuel production-ready claim: no
overclaim guard: yes
```

## External Plume Reference Boundary

Use these focused rebuilds before interpreting external plume-shape agreement:

```bash
bash tools/codex_build_h2_leak_mpi_cuda_repro.sh
python3 tools/write_dataverse_open_channel_amr_source_projection_implementation_report.py
bash tools/verify_dataverse_open_channel_amr_source_projection_implementation.sh
python3 tools/write_dataverse_open_channel_long_window_reconciliation_report.py
bash tools/verify_dataverse_open_channel_long_window_reconciliation.sh
python3 tools/write_master_plan_strict_external_source_update_report.py
bash tools/verify_master_plan_strict_external_source_update.sh
```

Authoritative external-reference report:

```text
docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/master_plan_strict_external_source_update_report.json
docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/dataverse_open_channel_amr_source_projection_implementation_report.json
docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/dataverse_open_channel_long_window_reconciliation_report.json
```

Current external-reference boundary:

```text
external plume blocker cleared: no
Dataverse agreement sensor count: 29
Dataverse 45s agreement attempt status: QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING
Dataverse 120s agreement attempt status: QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING
Dataverse long-window reconciliation: TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP
Dataverse existing 120s reaches experimental peak interval: yes
Dataverse existing 120s all sensors passed: no
Dataverse current refined-source time end s: 0.005
Dataverse current refined-source steps to 113s: 22600000
Dataverse AMR current projection single-level: no
Dataverse AMR lacks level-aware mask: no
Dataverse AMR MPI+CUDA reproducible build uses CUDA 12.6: yes
Dataverse geometry ready for full mesh parity: no
Dataverse obstacle exact bounds available: no
```

## Real CAD Boundary

Use these focused rebuilds before interpreting real-CAD cleanup or boundary-tag
credit:

```bash
python3 tools/write_engineering_h2_real_cad_negative_selftest_report.py
bash tools/verify_engineering_h2_real_cad_negative_selftest.sh
python3 tools/write_master_plan_strict_real_cad_update_report.py
bash tools/verify_master_plan_strict_real_cad_update.sh
```

Authoritative real-CAD report:

```text
docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/master_plan_strict_real_cad_update_report.json
docs/codex_audit/evidence/engineering_h2_real_cad_guard_negative_selftest_20260807/real_cad_guard_negative_selftest_report.json
```

Current real-CAD boundary:

```text
real CAD handoff contract ready: yes
real CAD source CAD files: 0
real CAD cleaned geometry files: 0
real CAD negative cases rejected: 8/8
real CAD guard synthetic manifest: yes
real CAD guard source hash mismatch: yes
real CAD guard boundary missing required role: yes
real CAD boundary contract ready for credit: no
```

## Fire Consequence Calibration Boundary

Use these focused rebuilds before interpreting H2 radiation or overpressure
consequence evidence:

```bash
python3 tools/write_h2_fire_overpressure_reduced_exp002_report.py
bash tools/verify_h2_fire_overpressure_reduced_exp002.sh
python3 tools/write_h2_fire_exp002_pressure_cfd_proxy_report.py
bash tools/verify_h2_fire_exp002_pressure_cfd_proxy.sh
python3 tools/write_h2_fire_plotfile_sensor_sampling_contract_report.py
bash tools/verify_h2_fire_plotfile_sensor_sampling_contract.sh
python3 tools/write_h2_fire_plotfile_sensor_sampling_negative_selftest_report.py
bash tools/verify_h2_fire_plotfile_sensor_sampling_negative_selftest.sh
python3 tools/write_h2_fire_mdpi_radiation_integrated_cfd_proxy_report.py
bash tools/verify_h2_fire_mdpi_radiation_integrated_cfd_proxy.sh
python3 tools/write_h2_fire_calibration_residual_budget_report.py
bash tools/verify_h2_fire_calibration_residual_budget.sh
python3 tools/write_master_plan_strict_fire_calibration_update_report.py
bash tools/verify_master_plan_strict_fire_calibration_update.sh
```

Authoritative fire-boundary reports:

```text
docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/master_plan_strict_fire_calibration_update_report.json
docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/h2_fire_overpressure_reduced_exp002_report.json
docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/h2_fire_exp002_pressure_cfd_proxy_report.json
docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/h2_fire_plotfile_sensor_sampling_contract_report.json
docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/h2_fire_plotfile_sensor_sampling_negative_selftest_report.json
docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json
docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/h2_fire_calibration_residual_budget_report.json
```

Current fire calibration boundary:

```text
fire calibration blocker cleared: no
fire calibration residual budget ready: yes
fire calibration residual budget clears blocker: no
EXP002 pressure CFD proxy CPU/GPU parity: yes
EXP002 CFD outputs sufficient for pressure agreement: no
plotfile sensor sampling negative cases rejected: 8/8
MDPI integrated radiation CFD proxy extracted: yes
MDPI CFD outputs sufficient for radiation agreement: no
```

## Worktree Hygiene

Use this non-destructive audit before cleanup, packaging, staging, or handoff:

```bash
python3 tools/write_current_worktree_hygiene_report.py
bash tools/verify_current_worktree_hygiene.sh
python3 tools/write_current_worktree_source_ledger_report.py
bash tools/verify_current_worktree_source_ledger.sh
python3 tools/write_current_worktree_review_queue_report.py
bash tools/verify_current_worktree_review_queue.sh
python3 tools/write_current_case_output_cleanup_manifest_report.py
bash tools/verify_current_case_output_cleanup_manifest.sh
python3 tools/write_current_disk_usage_manifest_report.py
bash tools/verify_current_disk_usage_manifest.sh
python3 tools/write_current_disk_cleanup_plan_report.py
bash tools/verify_current_disk_cleanup_plan.sh
python3 tools/write_current_operator_command_inventory_report.py
bash tools/verify_current_operator_command_inventory.sh
python3 tools/write_current_verification_chain_coverage_report.py
bash tools/verify_current_verification_chain_coverage.sh
```

The report classifies dirty worktree entries into generated/case output, audit
evidence, tooling, documentation, example source/config, and high-attention samples.
It does not delete, restore, stage, or ignore files.
The source/tooling ledger then excludes generated/case output and records the remaining
dirty source, configuration, tooling, documentation, audit-evidence, and unusual paths
with file hashes where available.
The worktree review queue converts the high-attention source ledger entries into
domain and priority groups for handoff review. It is a review aid only: it does not
delete, restore, stage, or ignore files.
The case-output cleanup manifest groups generated CFD outputs into dry-run cleanup
candidates, records whether each root still exists, and requires explicit user approval
before any deletion.
The disk usage manifest records the largest directories and files across the current
repository, marks audit evidence as protected by default, and marks build/test/case
outputs as cleanup candidates requiring review.
The disk cleanup plan converts those manifests into a dry-run decision plan with
candidate roots, risk levels, estimated reclaim sizes, and preconditions. It still
does not delete files and every cleanup candidate requires explicit user approval.

## Engineering H2 Current Scope

Quick evidence verification:

```bash
CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh
```

Useful focused smoke/runtime entry points:

```bash
bash tools/codex_smoke_engineering_h2_leak_pipe_rack_obstacle.sh
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh
bash tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh
```

Accepted engineering evidence includes leak, dispersion, obstacles, ignition, reacting
fire propagation, CPU/MPI execution, single-GPU CUDA execution, and multi-GPU MPI+CUDA
execution in the current user-priority scope.

## Academic Gas Detonation

Quick evidence verification:

```bash
bash tools/verify_academic_evidence.sh
bash tools/verify_academic_current_priority_scope.sh
```

Useful focused entry points:

```bash
bash tools/codex_run_academic_gpu_environment_preflight.sh
bash tools/codex_run_academic_gas_2d_detonation_reference.sh
bash tools/codex_run_academic_gas_3d_detonation_reference.sh
bash tools/codex_run_academic_gas_detonation_front_amr_validation.sh
```

The gas detonation MPI+CUDA evidence is recorded in:

```text
docs/codex_audit/evidence/academic_gas_detonation_mpi_cuda_20260731/academic_gas_detonation_mpi_cuda_report.json
```

## Academic Gas-Liquid / Two-Phase Detonation

Quick evidence verification:

```bash
bash tools/verify_academic_evidence.sh
bash tools/verify_academic_current_priority_scope.sh
```

Reproducible 1000-step reacting spray MPI+CUDA runner:

```bash
bash tools/codex_run_academic_gas_liquid_detonation_mpi_cuda_extended.sh
bash tools/verify_academic_gas_liquid_detonation_mpi_cuda_extended.sh
```

Report:

```text
docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json
```

This is a reduced-resolution stability proof for reacting spray coupling on 2 MPI
ranks and 2 CUDA devices. It does not replace case-specific grid convergence or
external quantitative validation for a publication or accident-forensics claim.

## Strict Master-Plan Blockers

The following blockers remain intentionally open. They do not invalidate the current
user-scope CPU/GPU/MPI capability claim, but they prevent strict completion of the
original full master plan:

- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`

Relevant strict reports:

```text
docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/master_plan_strict_blocker_matrix_report.json
docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/master_plan_strict_external_source_update_report.json
docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/master_plan_strict_real_cad_update_report.json
docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/master_plan_strict_fire_calibration_update_report.json
docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.json
```

Strict unblock instructions:

```text
docs/codex_audit/strict_master_plan_unblock_runbook.md
docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/current_phase_final_delivery_index_report.md
docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.md
```

## Interpreting PASS

`PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION` means the current engineering-first
scope is reproducible and evidence-backed on this server.

It does not mean:

- Real CAD import/cleanup has been credited with production evidence.
- External plume-shape benchmark data have been ingested and matched.
- Fire radiation or overpressure metrics have been calibrated against external data.
- Every possible user mechanism, geometry, mesh, or accident scenario is grid-converged.

Use the strict blocker reports before claiming strict master-plan completion.
