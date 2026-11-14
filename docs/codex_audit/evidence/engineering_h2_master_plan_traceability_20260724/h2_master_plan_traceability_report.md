# Engineering H2 Master Plan Traceability Matrix

Status: `NOT_READY-H2-MASTER-PLAN-TRACEABILITY`
Master plan: `../pele_cfd_master_plan.md` sha256 `97d7f0529a0bd867`

## Current Scores

- `functional_coverage_percent`: `96.9`
- `production_credibility_percent`: `82.2`
- `ctest_tests`: `22`
- `ctest_passed`: `True`
- `scorecard_status`: `NOT_PRODUCTION_READY`
- `handoff_status`: `NOT_READY-H2-PRODUCTION-HANDOFF`
- `remaining_blocker_count`: `3`
- `academic_gas_detonation_readiness_status`: `PASS-ACADEMIC-GAS-DETONATION-READINESS`
- `academic_gas_foundation_ready`: `True`
- `academic_gas_short_2d_detonation_wave_validation_passed`: `True`
- `academic_gas_detonation_front_amr_validation_available`: `True`
- `academic_weno5_convergence_validation_status`: `PASS-ACADEMIC-WENO5-CONVERGENCE-VALIDATION`
- `academic_weno5_convergence_clears_acd_01`: `True`
- `academic_weno5_convergence_clears_qlt_03`: `True`
- `academic_weno5_convergence_pelec_p32_64`: `4.911286070252`
- `academic_weno5_convergence_pelec_p64_128`: `4.955275049333`
- `academic_weno5_convergence_error_ratio`: `8.268555361656759e-05`
- `academic_twophase_rayleigh_taylor_status`: `PASS-ACADEMIC-TWOPHASE-RAYLEIGH-TAYLOR-VALIDATION`
- `academic_twophase_rayleigh_taylor_clears_acd_04`: `True`
- `academic_twophase_interface_amr_available`: `False`
- `academic_twophase_interface_amr_validation_status`: `PASS-ACADEMIC-TWOPHASE-INTERFACE-AMR-VALIDATION`
- `academic_twophase_interface_amr_clears_acd_08`: `True`
- `academic_droplet_euler_lagrange_status`: `PASS-ACADEMIC-DROPLET-EULER-LAGRANGE-VALIDATION`
- `academic_droplet_euler_lagrange_clears_response_gate`: `True`
- `academic_droplet_euler_lagrange_clears_budget_gap`: `False`
- `academic_droplet_euler_lagrange_clears_external_reference_gap`: `False`
- `academic_droplet_euler_lagrange_clears_acd_05`: `False`
- `academic_droplet_euler_lagrange_particle_growth_factor`: `10.67`
- `academic_spray_detonation_status`: `PASS-ACADEMIC-SPRAY-DETONATION-VALIDATION`
- `academic_spray_detonation_clears_response_gate`: `True`
- `academic_spray_detonation_clears_budget_gap`: `False`
- `academic_spray_detonation_clears_cellular_detonation_gap`: `False`
- `academic_spray_detonation_clears_external_reference_gap`: `False`
- `academic_spray_detonation_clears_acd_07`: `False`
- `academic_spray_detonation_pressure_front_shift_cells`: `9.0`
- `academic_spray_detonation_source_budget_status`: `PASS-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION`
- `academic_spray_detonation_source_budget_clears_subgate`: `True`
- `academic_spray_detonation_source_budget_particle_mismatch`: `2.7182461588711962e-08`
- `academic_spray_detonation_source_budget_heat_release_absmax`: `11.110226624283513`
- `academic_spray_detonation_source_budget_pressure_front_shift_cells`: `3.0`
- `academic_spray_detonation_source_budget_clears_cellular_gap`: `False`
- `academic_spray_detonation_source_budget_clears_external_reference_gap`: `False`
- `academic_spray_detonation_source_budget_clears_broad_acd_07`: `False`
- `academic_spray_source_budget_validation_status`: `PASS-ACADEMIC-SPRAY-SOURCE-BUDGET-VALIDATION`
- `academic_spray_source_budget_clears_acd05_gas_source_history_budget`: `True`
- `academic_spray_source_budget_clears_acd05_full_gas_particle_budget`: `True`
- `academic_spray_source_budget_particle_mismatch`: `1.5138259899403366e-07`
- `academic_spray_source_budget_gas_mass_error`: `4.1546398406278134e-05`
- `academic_spray_source_budget_fuel_error`: `1.3841102017925978e-07`
- `academic_spray_source_budget_energy_error`: `6.173429543763765e-06`
- `academic_spray_source_budget_energy_residual`: `6.889820598158375e-09`
- `academic_spray_source_budget_max_abs_momentum_source_rate_integral`: `0.0`
- `academic_spray_source_budget_clears_acd07`: `False`
- `academic_droplet_spray_budget_preflight_status`: `PASS-ACADEMIC-DROPLET-SPRAY-PLOTFIELD-BUDGET-PREFLIGHT`
- `academic_droplet_spray_budget_preflight_clears_plotfield_gate`: `True`
- `academic_droplet_spray_budget_preflight_particle_binary_parser_ready`: `True`
- `academic_droplet_spray_budget_preflight_clears_full_budget_gap`: `False`
- `academic_spray_closed_particle_budget_status`: `PASS-ACADEMIC-SPRAY-CLOSED-PARTICLE-BUDGET`
- `academic_spray_closed_particle_budget_clears_fixed_particle_subgap`: `True`
- `academic_spray_closed_particle_budget_clears_full_acd05_budget`: `False`
- `academic_spray_closed_particle_budget_mass_rel_drift`: `0.0`
- `academic_spray_coupled_budget_residual_status`: `PASS-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL`
- `academic_spray_coupled_budget_residual_particle_plotfield_ready`: `True`
- `academic_spray_coupled_budget_residual_signs_consistent`: `True`
- `academic_spray_coupled_budget_residual_source_history_available`: `True`
- `academic_spray_coupled_budget_residual_clears_acd05`: `True`
- `academic_spray_coupled_budget_residual_clears_acd07`: `True`
- `academic_spray_coupled_budget_residual_max_mass_residual_over_particle_loss`: `9.239999997789152`
- `academic_gpu_environment_preflight_status`: `PASS-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT`
- `academic_gpu_environment_ready_for_acd_10`: `True`
- `academic_gpu_environment_ready_for_qlt_05`: `True`
- `academic_gpu_environment_blocking_reasons`: `[]`
- `academic_gas_double_mach_validation_status`: `PASS-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION`
- `academic_gas_double_mach_clears_qlt_03_gap`: `True`
- `academic_gas_double_mach_front_x`: `0.729167`
- `academic_twophase_bubble_rise_validation_status`: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION`
- `academic_twophase_bubble_rise_clears_short_time_response_gap`: `True`
- `academic_twophase_bubble_rise_clears_canonical_long_time_gap`: `False`
- `academic_twophase_bubble_rise_clears_qlt_03_gap`: `False`
- `academic_twophase_bubble_rise_centroid_rise`: `2.52982693127e-09`
- `academic_mms_shim_validation_status`: `PASS-ACADEMIC-MMS-SHIM-VALIDATION`
- `academic_mms_shim_clears_qlt_03_wiring_gap`: `True`
- `academic_mms_shim_clears_nonlinear_masa_benchmark`: `False`
- `academic_mms_shim_max_error`: `0.0`
- `academic_mms_nonconstant_density_shim_validation_status`: `PASS-ACADEMIC-MMS-NONCONSTANT-DENSITY-SHIM-VALIDATION`
- `academic_mms_nonconstant_density_shim_clears_qlt_03`: `True`
- `academic_mms_nonconstant_density_shim_clears_external_nonlinear_masa`: `False`
- `academic_mms_nonconstant_density_shim_pressure_error_relative`: `1.94159957562e-08`
- `real_cad_boundary_tag_contract_status`: `NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT`
- `real_cad_boundary_tag_ready_for_credit`: `False`
- `quality_review_coverage_status`: `PASS-H2-QUALITY-REVIEW-COVERAGE`
- `quality_review_ready_for_qlt01_credit`: `False`
- `quality_review_ready_for_qlt02_credit`: `False`

## Coverage Counts

- `DEFERRED`: `3`
- `NOT_READY`: `0`
- `PARTIAL`: `11`
- `PASS`: `15`

## Requirement Matrix

| ID | Requirement | Priority | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- |
| `ENG-01` | STL/STEP 几何文件读取 | `P0` | `PARTIAL` | geometry_pipeline_smoke; real_cad_cleanup_package_report | STL/synthetic geometry path exists, but production real-CAD/STEP cleanup evidence is still NOT_READY. |
| `ENG-02` | 自动网格生成 | `P0` | `PASS` | geometry_pipeline_smoke; production_mesh_scout_report | none |
| `ENG-03` | 网格自适应加密 (AMR) | `P0` | `PASS` | refinement_tags_smoke; production_mesh_8rank_scout_report | none |
| `ENG-04` | Embedded Boundary 障碍物表示 | `P0` | `PARTIAL` | geometry_pipeline_smoke; real_cad_cleanup_package_report | EB/STL pipeline is tested, but scorecard still blocks on synthetic geometry rather than real CAD cleanup. |
| `ENG-05` | 边界条件标签系统 | `P0` | `PARTIAL` | wall_functions_smoke; bfs_kepsilon_reference_report; real_cad_boundary_tag_contract_report | Boundary/wall-function evidence and a face-level BC tag contract exist, but real CAD boundary tags are not production-cleared. |
| `ENG-06` | 多组分气体扩散 | `P0` | `PASS` | engineering_h2_reference_agreement_report; production_mesh_8rank_scout_report | none |
| `ENG-07` | RANS k-ε 湍流模型 | `P0` | `PASS` | wall_functions_smoke; engineering_bfs_kepsilon_reference_report | none |
| `ENG-08` | 液体池蒸发源项 | `P1` | `PARTIAL` | evaporation_model_smoke; pool_vof_coupling_smoke | Evaporation/pool coupling smoke tests exist, but no production calibrated liquid-pool release validation is attached. |
| `ENG-09` | 风场边界条件 | `P1` | `PASS` | wind_profile_smoke | none |
| `ENG-10` | 着火/燃烧模拟 | `P1` | `PARTIAL` | ignition_consequence_report; fire_calibration_package_report | Ignition and screening fire metrics pass, but calibrated radiation/overpressure data are still missing. |
| `ENG-11` | 统一 YAML 输入文件 | `P0` | `PASS` | yaml_parser_smoke | none |
| `ENG-12` | 二阶精度格式 | `P0` | `PASS` | second_order_advection_smoke; isentropic_vortex_smoke | none |
| `ENG-13` | CPU 加速（近期） | `P0` | `PASS` | engineering_h2_mpi_scaling_report; hybrid_runtime_affinity_manifest | none |
| `ENG-14` | GPU 加速接口（后期） | `P2` | `DEFERRED` | academic_gpu_environment_preflight_report | GPU backend is a later-phase plan item; current GPU preflight is NOT_READY due NVIDIA driver/library mismatch and missing CUDA runtime libraries. |
| `ACD-01` | WENO5/WENO5-Z 高阶重构 | `P0` | `PASS` | weno5_smoke; pelec_weno_smoke; academic_weno5_convergence_validation_report | none |
| `ACD-02` | 多步化学反应机理读取 | `P0` | `PASS` | ignition_consequence_report; academic_gas_detonation_readiness_report | none |
| `ACD-03` | 气相爆轰模拟 | `P0` | `PASS` | sod_shock_tube_smoke; isentropic_vortex_smoke; pelec_weno_smoke; academic_gas_detonation_readiness_report | none |
| `ACD-04` | VOF 气液界面捕捉 | `P0` | `PASS` | vof_fct_smoke; vof_plic_smoke; twophase_eos_smoke; twophase_hllc_smoke; academic_twophase_rayleigh_taylor_validation_report | none |
| `ACD-05` | 欧拉-拉格朗日液滴追踪 | `P0` | `PARTIAL` | d2_law_smoke; academic_droplet_euler_lagrange_validation_report; academic_spray_source_budget_validation_report; academic_droplet_spray_budget_preflight_report; academic_spray_closed_particle_budget_report; academic_spray_coupled_budget_residual_report | D2-law, shock-droplet response, gas/spray plotfield budgets, native particle binary budgets, closed fixed-particle budget, gas mass/species/energy source-history budgets, particle/source mass closure, and momentum-source sanity pass, but broad evaporating spray momentum/total-energy state closure plus external breakup/reference validation remain open. |
| `ACD-06` | 表面张力模型 | `P1` | `PARTIAL` | csf_smoke; static_droplet_laplace_smoke | CSF normal/curvature/source-work smoke evidence exists, but coupled capillary-wave or solver-coupled static-droplet CFD benchmark validation is still open. |
| `ACD-07` | 气液两相爆轰 | `P1` | `PARTIAL` | academic_spray_detonation_validation_report; academic_spray_detonation_source_budget_validation_report; academic_droplet_spray_budget_preflight_report; academic_spray_coupled_budget_residual_report | Reacting spray shock/detonation-style response, source-field mapping, particle/source mass closure, gas/spray plotfield budgets, native particle binary budgets, and coupled-budget residual diagnostics pass, but full cellular gas-liquid detonation morphology and external reference agreement remain open. |
| `ACD-08` | 网格自适应 (AMR) | `P0` | `PASS` | refinement_tags_smoke; pelec_weno_smoke; academic_gas_detonation_readiness_report; academic_twophase_rayleigh_taylor_validation_report; academic_twophase_interface_amr_validation_report | none |
| `ACD-09` | CPU 加速（近期） | `P0` | `PASS` | engineering_h2_mpi_scaling_report; hybrid_runtime_affinity_manifest | none |
| `ACD-10` | GPU 加速（后期） | `P2` | `DEFERRED` | academic_gpu_environment_preflight_report | Academic GPU backend is not verified on the current server because the CUDA detonation smoke cannot load required NVIDIA/CUDA runtime libraries. |
| `QLT-01` | 单模块审查 | `` | `PARTIAL` | docs/codex_audit; quality_review_coverage_report | Audit records and a module coverage inventory exist, but independent Type A review-agent artifacts are not complete for every module. |
| `QLT-02` | 联调审查 | `` | `PARTIAL` | h2_blocker_clearance_preflight_report; production_evidence_verification_report; quality_review_coverage_report | Integration gates and a phase coverage inventory are machine-verified, but formal independent Type B review reports are not complete for every phase. |
| `QLT-03` | 验证算例 | `` | `PARTIAL` | ctest_22; sod_shock_tube_smoke; isentropic_vortex_smoke; academic_weno5_convergence_validation_report; academic_gas_double_mach_validation_report; academic_twophase_bubble_rise_validation_report; academic_mms_shim_validation_report; academic_mms_nonconstant_density_shim_validation_report | 22 smoke/verification tests plus WENO5 fifth-order convergence, Double-Mach, strengthened 6000-step low-CFL short-time bubble response, constant-state MMS wiring validation, and nonconstant-density MMS shim validation pass; external nonlinear MASA, canonical long physical-time bubble-rise stability, and experiment-grade comparisons remain incomplete. |
| `QLT-04` | 断点记录 | `` | `PASS` | docs/codex_audit; h2_production_handoff_report | none |
| `QLT-05` | GPU 合规性 | `` | `DEFERRED` | academic_gpu_environment_preflight_report | GPU compliance cannot receive credit until the NVIDIA driver/library mismatch and missing CUDA runtime libraries are repaired and the CUDA smoke gate passes. |

## Remaining Blockers

- `external_plume_shape_reference`: `reference_agreement_is_threshold_only_not_external_plume_shape_dataset` failed gates `case_package_runnable; dataset_metadata_available; exact_sensor_coordinates_available; exact_baffle_geometry_available; digitized_experimental_timeseries_available; external_dataset_json_written; reference_agreement_uses_external_shape_dataset`
- `real_cad_cleanup`: `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup` failed gates `manifest_present; provenance_complete; real_cad_source_classified; source_cad_hashes_verified; cleaned_geometry_hashes_verified; large_layout_coverage; bbox_non_degenerate_m; scorecard_blocker_clearance`
- `calibrated_fire_radiation_overpressure`: `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure` failed gates `ingestion_report_passed; metadata_available; case_alignment_complete; package_ready_for_dataset_builder`

## Evidence Files

- `master_plan`: `../pele_cfd_master_plan.md` sha256 `97d7f0529a0bd867`
- `production_evidence_verification_report`: `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json` sha256 `eebc2a5aa0d10b8c`
- `production_handoff_report`: `docs/codex_audit/evidence/engineering_h2_production_handoff_20260723/h2_production_handoff_report.json` sha256 `4a4ec7efeb8ce1e8`
- `blocker_clearance_preflight_report`: `docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/h2_blocker_clearance_preflight_report.json` sha256 `320fe14cf656f817`
- `engineering_production_scorecard`: `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json` sha256 `5d04d11b450a9b83`
- `academic_gas_detonation_readiness_report`: `docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/academic_gas_detonation_readiness_report.json` sha256 `e6c00594f975f42c`
- `academic_weno5_convergence_validation_report`: `docs/codex_audit/evidence/academic_weno5_convergence_validation_20260729/academic_weno5_convergence_validation_report.json` sha256 `891e66d88046819d`
- `academic_twophase_rayleigh_taylor_validation_report`: `docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/academic_twophase_rayleigh_taylor_validation_report.json` sha256 `fa7394d45d8f31fc`
- `academic_twophase_interface_amr_validation_report`: `docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/academic_twophase_interface_amr_validation_report.json` sha256 `c9f981226249383e`
- `academic_droplet_euler_lagrange_validation_report`: `docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/academic_droplet_euler_lagrange_validation_report.json` sha256 `8177b0a50a8cd0f8`
- `academic_spray_detonation_validation_report`: `docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/academic_spray_detonation_validation_report.json` sha256 `79f7546d6b8cce72`
- `academic_spray_detonation_source_budget_validation_report`: `docs/codex_audit/evidence/academic_spray_detonation_source_budget_validation_20260729/academic_spray_detonation_source_budget_validation_report.json` sha256 `e797a6800b0daf26`
- `academic_spray_source_budget_validation_report`: `docs/codex_audit/evidence/academic_spray_source_budget_validation_20260729/academic_spray_source_budget_validation_report.json` sha256 `82f57a030b8ffe81`
- `academic_droplet_spray_budget_preflight_report`: `docs/codex_audit/evidence/academic_droplet_spray_budget_preflight_20260729/academic_droplet_spray_budget_preflight_report.json` sha256 `12129cfa88698abd`
- `academic_spray_closed_particle_budget_report`: `docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/academic_spray_closed_particle_budget_report.json` sha256 `acebf474095c124d`
- `academic_spray_coupled_budget_residual_report`: `docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.json` sha256 `2140f4fe9b7fbf7d`
- `academic_gpu_environment_preflight_report`: `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/academic_gpu_environment_preflight_report.json` sha256 `2b1f2aa687e05321`
- `academic_gas_double_mach_validation_report`: `docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.json` sha256 `6db816f40a329734`
- `academic_twophase_bubble_rise_validation_report`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json` sha256 `c8fa8ab6bef801f8`
- `academic_mms_shim_validation_report`: `docs/codex_audit/evidence/academic_mms_shim_validation_20260728/academic_mms_shim_validation_report.json` sha256 `96dbb22787b5def5`
- `academic_mms_nonconstant_density_shim_validation_report`: `docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729/academic_mms_nonconstant_density_shim_validation_report.json` sha256 `85db805b16b3aea8`
- `real_cad_boundary_tag_contract_report`: `docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724/real_cad_boundary_tag_contract_report.json` sha256 `d88856f1bce57f1b`
- `quality_review_coverage_report`: `docs/codex_audit/evidence/engineering_h2_quality_review_coverage_20260724/h2_quality_review_coverage_report.json` sha256 `b9c294e90251afcf`

## Limitations

- This report traces master-plan requirements to current maintained evidence; it does not create new physical validation.
- PASS means evidence exists in the maintained verification chain, not external certification.
- PARTIAL and NOT_READY items require stronger validation or real external data before production readiness can be claimed.
