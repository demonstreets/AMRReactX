# 当前两相求解与验证入口

2026-09-10 新实现及验证采用以下两个入口。它们使用不同的液体表示，不能将同一份液体质量同时计入体积分数与液滴粒子。

| 任务 | 运行与模型说明 | 已实现的主推进 |
|---|---|---|
| 解析气液界面 | [resolved_twophase](examples/academic/resolved_twophase/README.md) | 独立相质量、气相组分质量、共同压力与速度、两相温度的混合物热力学闭合；声学压力推进及守恒几何 PLIC 重映射 |
| 稀疏液滴与反应流 | [spray_detonation](examples/academic/spray_detonation/README.md) | 原生 PeleC 流动、有限速率气相化学及液滴质量／动量／能量交换；传播、反应序列和每步压力轨迹诊断 |

解析界面入口已完成平移、混合声波、双 EOS 激波管及 CPU/MPI/GPU/重启的定量验证，具体数值和模型限制见其 README。它采用声学松弛通量，并非 HLLC；当前为无黏、无相变的均匀网格模型。液滴入口的封闭系统守恒与化学参考对照已经完成，二维传播和网格比较仍在验证中；不能将正在运行的算例写为完成认证。

原有旧状态定义下的实验性 VOF 路径不等同于上述新解析界面求解器。旧 PASS 汇总不能替代新入口的实测结果。[2026-09-09 修复说明](docs/codex_audit/repair_20260909.md)保留其历史审查含义。本轮明确不包含真实 CAD 接入及实际三维泄漏／火灾验证。

---

> **2026-09-09 审查修正：旧 PASS 不代表当前物理验收。** 7–8 月的汇总、认证与并行能力报告保留为历史记录；其中冷流热点、零反应机理和缺失全场数据的结论已被独立审查否定或降级。当前依据为 [修复说明与复验方法](docs/codex_audit/repair_20260909.md)。本轮不开展真实 CAD 接入及实际三维泄漏/火灾算例验证。VOF 混合物闭合、PLIC 主推进和气液爆轰完整认证仍不完备。

# my-pele 历史状态入口（以下为审查前记录）

This repository is the current `/home/cj/my-pele` working tree for the PeleC/PeleLMeX
CFD program. Older README content was replaced because it contained stale progress
claims, obsolete dependency notes, and encoding damage. Detailed history remains in
`PROGRESS.md` and the evidence reports under `docs/codex_audit/evidence/`.

## 历史入口：不得替代 2026-09-09 的复验结论

Operator runbook:

```text
docs/codex_audit/current_scope_operator_runbook.md
```

Current CPU/GPU/MPI capability matrix:

```text
docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json
```

Top-level current-scope readiness reports:

```text
docs/codex_audit/evidence/master_plan_final_readiness_20260731/master_plan_final_readiness_report.json
docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/master_plan_current_scope_verification_report.json
```

Strict blocker matrix:

```text
docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/master_plan_strict_blocker_matrix_report.json
```

Strict master-plan unblock runbook:

```text
docs/codex_audit/strict_master_plan_unblock_runbook.md
```

Dataverse AMR source projection and long-window reconciliation:

```text
docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/dataverse_open_channel_amr_source_projection_implementation_report.json
docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/dataverse_open_channel_long_window_reconciliation_report.json
```

Current status CLI self-check:

```text
docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json
```

Current-scope release candidate handoff:

```text
docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json
```

Project Closeout Forecast:

```text
docs/codex_audit/evidence/project_closeout_forecast_20260812/project_closeout_forecast_report.json
```

Strict Master-Plan Completion Gate:

```text
docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/strict_master_plan_completion_gate_report.json
```

Strict External Artifact Drop Index:

```text
docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/strict_external_artifact_drop_index_report.json
```

Strict External Artifact Drop Checklist:

```text
docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/strict_external_artifact_drop_checklist_report.json
```

Strict External Artifact Chinese Handoff:

```text
docs/user_guides/真实资料投递清单_按文件路径.md
docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/strict_external_artifact_cn_handoff_report.json
```

Strict External Artifact Progress Selftest:

```text
docs/codex_audit/evidence/strict_external_artifact_progress_selftest_20260812/strict_external_artifact_progress_selftest_report.json
```

Strict Master-Plan Closeout Action Pack:

```text
docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.json
```

Project Closeout Acceptance Gate:

```text
docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/project_closeout_acceptance_gate_report.json
```

Current-Scope Delivery Package:

```text
docs/codex_audit/evidence/current_scope_delivery_package_20260812/current_scope_delivery_package_report.json
```

Complete Walkthrough Guide:

```text
docs/user_guides/从目录到排错_完整运行教程.md
docs/codex_audit/evidence/complete_walkthrough_guide_20260818/complete_walkthrough_guide_report.json
```

Current-Scope Final Handoff Note:

```text
docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/current_scope_final_handoff_note_report.json
```

Current Operator Quickstart Smoke:

```text
docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/current_operator_quickstart_smoke_report.json
```

Current Phase Closure Certificate:

```text
docs/codex_audit/evidence/current_phase_closure_certificate_20260812/current_phase_closure_certificate_report.json
```

Current Phase Release Manifest:

```text
docs/codex_audit/evidence/current_phase_release_manifest_20260812/current_phase_release_manifest_report.json
```

Current Phase Final Delivery Index:

```text
docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/current_phase_final_delivery_index_report.json
```

Current worktree hygiene audit:

```text
docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json
```

Current worktree source/tooling ledger:

```text
docs/codex_audit/evidence/current_worktree_source_ledger_20260803/current_worktree_source_ledger_report.json
```

Current worktree review queue:

```text
docs/codex_audit/evidence/current_worktree_review_queue_20260820/current_worktree_review_queue_report.json
```

Current generated case-output cleanup manifest:

```text
docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/current_case_output_cleanup_manifest_report.json
```

Current disk usage manifest:

```text
docs/codex_audit/evidence/current_disk_usage_manifest_20260803/current_disk_usage_manifest_report.json
```

Current dry-run disk cleanup plan:

```text
docs/codex_audit/evidence/current_disk_cleanup_plan_20260803/current_disk_cleanup_plan_report.json
```

Current operator command inventory:

```text
docs/codex_audit/evidence/current_operator_command_inventory_20260803/current_operator_command_inventory_report.json
```

Current verification chain coverage:

```text
docs/codex_audit/evidence/current_verification_chain_coverage_20260803/current_verification_chain_coverage_report.json
```

Strict unblock command inventory:

```text
docs/codex_audit/evidence/strict_unblock_command_inventory_20260803/strict_unblock_command_inventory_report.json
```

Strict artifact template lint:

```text
docs/codex_audit/evidence/strict_artifact_template_lint_20260803/strict_artifact_template_lint_report.json
```

Strict artifact drop contract preflight:

```text
docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/strict_artifact_drop_contract_preflight_report.json
```

Strict artifact drop contract selftest:

```text
docs/codex_audit/evidence/strict_artifact_drop_contract_selftest_20260803/strict_artifact_drop_contract_selftest_report.json
```

## Fast Verification

Run from the repository root:

```bash
cd /home/cj/my-pele
python3 tools/codex_print_current_status.py
python3 tools/codex_print_current_status.py --json
bash tools/verify_complete_walkthrough_guide.sh
bash tools/codex_verify_current_scope.sh
```

To run a full verification and then refresh the delivery/final handoff reports so
they point at that latest passing log:

```bash
bash tools/run_current_scope_release_refresh.sh
```

Equivalent expanded sequence:

```bash
python3 tools/check_machine_local_paths.py --strict
python3 tools/codex_print_current_status.py
python3 tools/codex_print_current_status.py --json
python3 tools/write_current_scope_operator_runbook_report.py
bash tools/verify_current_scope_operator_runbook.sh
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
python3 tools/write_current_parallel_capability_matrix_report.py
bash tools/verify_current_parallel_capability_matrix.sh
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
```

Expected current statuses:

```text
PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK
PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK
PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX
PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS
PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION
PASS-CURRENT-STATUS-CLI
AUDITED-CURRENT-WORKTREE-HYGIENE
AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER
PASS-CURRENT-WORKTREE-REVIEW-QUEUE
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
PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK
PASS-CURRENT-SCOPE-STATE-SNAPSHOT
AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE
```

## Current Capability Claim

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
docs/codex_audit/evidence/project_closeout_forecast_20260812/project_closeout_forecast_report.json
docs/codex_audit/evidence/current_scope_delivery_package_20260812/current_scope_delivery_package_report.json
docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/current_scope_final_handoff_note_report.json
docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/current_operator_quickstart_smoke_report.json
docs/codex_audit/evidence/current_phase_closure_certificate_20260812/current_phase_closure_certificate_report.json
docs/codex_audit/evidence/current_phase_release_manifest_20260812/current_phase_release_manifest_report.json
docs/user_guides/真实资料投递清单_按文件路径.md
docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/strict_external_artifact_cn_handoff_report.json
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

Use this wrapper when you want one command to run the full current-scope chain, save a
timestamped log, and then refresh the delivery package, final handoff note, state
snapshot, and status CLI against that latest passing log:

```bash
bash tools/run_current_scope_release_refresh.sh
python3 tools/write_current_phase_final_delivery_index_report.py
bash tools/verify_current_phase_final_delivery_index.sh
python3 tools/write_current_scope_release_refresh_entrypoint_report.py
bash tools/verify_current_scope_release_refresh_entrypoint.sh
```

Report:

```text
docs/codex_audit/evidence/current_scope_release_refresh_entrypoint_20260812/current_scope_release_refresh_entrypoint_report.json
docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/current_phase_final_delivery_index_report.json
```

The current-scope evidence supports CPU/MPI, single CUDA GPU, and multi-GPU MPI+CUDA
readiness for these scenario families:

- Engineering H2 leak, dispersion, ignition, and reacting pipe-rack fire.
- Engineering multi-fuel gas-source, gasified LNG/LPG surrogate, and screening
  external-vaporization workflows.
- Academic gas-phase detonation.
- Academic gas-liquid/two-phase reacting droplet/spray detonation-adjacent capability.

## Current-Scope Release Candidate Handoff

The current user-priority scope is packaged as a release-candidate handoff, with
strict master-plan completion still explicitly false:

```text
docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json
```

Use these status lines as the quick boundary:

```text
release-candidate handoff ready: yes
release-candidate usable for current priority scope: yes
release-candidate is full strict master-plan completion: no
```

## Fuel And Liquefied-Gas Boundary

Use the status CLI to inspect the evidence-backed fuel boundary before changing
engineering release cases:

```bash
python3 tools/codex_print_current_status.py
python3 tools/codex_print_current_status.py --json
```

Current gas-source evidence supports:

- H2 as the primary engineering current scope.
- CH4 gas/fire probes.
- C3H8 gas/fire probes.
- Multi-fuel input-template catalog checks.
- gasified LNG surrogate boundaries.
- gasified LPG surrogate boundaries.
- Multi-fuel external vaporization CUDA inputs.
- Liquefied-release source-model CUDA smoke checks.
- Liquefied-release source balance checks.
- Liquefied-release source balance negative selftest guards.
- Liquefied-release thermal plausibility checks.
- Liquefied LNG/LPG breach-to-gas-source contract checks.
- Operator-editable LNG/LPG breach preset JSONs under
  `examples/engineering/h2_leak_3d/liquefied_breach_presets/`.
- Liquefied phase-change overclaim guard.

Authoritative evidence:

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
```

Engineering Multifuel And Liquefied-Gas User Answer:

```text
can_compute_liquefied_tank_breach_vaporization
```

Boundary claim:

```text
liquefied release source balance negative cases rejected: 5/5
multi-fuel template catalog ready: yes
liquefied release source guard phase-change overclaim: yes
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

Use the operator runbook for the exact verification and reproduction commands.

## External Plume Reference Boundary

Use the status CLI and strict external-source report before claiming external
plume-shape agreement:

```bash
python3 tools/codex_print_current_status.py
bash tools/codex_build_h2_leak_mpi_cuda_repro.sh
python3 tools/write_dataverse_open_channel_amr_source_projection_implementation_report.py
bash tools/verify_dataverse_open_channel_amr_source_projection_implementation.sh
python3 tools/write_dataverse_open_channel_long_window_reconciliation_report.py
bash tools/verify_dataverse_open_channel_long_window_reconciliation.sh
python3 tools/write_master_plan_strict_external_source_update_report.py
bash tools/verify_master_plan_strict_external_source_update.sh
```

Authoritative external-reference evidence:

```text
docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/master_plan_strict_external_source_update_report.json
docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/dataverse_open_channel_amr_source_projection_implementation_report.json
docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/dataverse_open_channel_long_window_reconciliation_report.json
```

Current external-reference boundary claim:

```text
external plume blocker cleared: no
Dataverse agreement sensor count: 29
Dataverse 120s agreement attempt status: QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING
Dataverse long-window reconciliation: TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP
Dataverse existing 120s reaches experimental peak interval: yes
Dataverse existing 120s all sensors passed: no
Dataverse current refined-source steps to 113s: 22600000
Dataverse AMR MPI+CUDA reproducible build uses CUDA 12.6: yes
Dataverse geometry ready for full mesh parity: no
```

## Real CAD Boundary

Use the status CLI and strict real-CAD report before claiming real CAD cleanup or
boundary-tag credit:

```bash
python3 tools/codex_print_current_status.py
python3 tools/write_engineering_h2_real_cad_negative_selftest_report.py
bash tools/verify_engineering_h2_real_cad_negative_selftest.sh
python3 tools/write_master_plan_strict_real_cad_update_report.py
bash tools/verify_master_plan_strict_real_cad_update.sh
```

Authoritative real-CAD evidence:

```text
docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/master_plan_strict_real_cad_update_report.json
docs/codex_audit/evidence/engineering_h2_real_cad_guard_negative_selftest_20260807/real_cad_guard_negative_selftest_report.json
```

Current real-CAD boundary claim:

```text
real CAD handoff contract ready: yes
real CAD source CAD files: 0
real CAD negative cases rejected: 8/8
real CAD guard boundary missing required role: yes
real CAD boundary contract ready for credit: no
```

## Fire Consequence Calibration Boundary

Use the status CLI and strict fire calibration report before claiming radiation
or overpressure validation:

```bash
python3 tools/codex_print_current_status.py
python3 tools/write_h2_fire_calibration_residual_budget_report.py
bash tools/verify_h2_fire_calibration_residual_budget.sh
python3 tools/write_master_plan_strict_fire_calibration_update_report.py
bash tools/verify_master_plan_strict_fire_calibration_update.sh
```

Authoritative fire-consequence calibration-boundary evidence:

```text
docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/master_plan_strict_fire_calibration_update_report.json
docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/h2_fire_overpressure_reduced_exp002_report.json
docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/h2_fire_exp002_pressure_cfd_proxy_report.json
docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/h2_fire_plotfile_sensor_sampling_contract_report.json
docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json
docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/h2_fire_calibration_residual_budget_report.json
```

Current fire boundary claim:

```text
fire calibration blocker cleared: no
fire calibration residual budget ready: yes
fire calibration residual budget clears blocker: no
EXP002 pressure CFD proxy CPU/GPU parity: yes
MDPI CFD outputs sufficient for radiation agreement: no
```

## Strict Scope Boundary

Current-scope PASS does not claim strict completion of:

- External plume-shape benchmark data ingestion and agreement.
- Real CAD cleanup/intake evidence.
- Calibrated fire radiation and overpressure evidence.

Those items remain explicit strict blockers until controlled external artifacts are
provided and ingested through the existing strict evidence workflows.

Use `docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/current_phase_final_delivery_index_report.md`
as the single-page current handoff index. Use `docs/codex_audit/strict_master_plan_unblock_runbook.md` for the exact artifact
templates and commands needed to clear those strict blockers. Use
`docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.md`
for the current machine-checked 14-item done/missing action list.
