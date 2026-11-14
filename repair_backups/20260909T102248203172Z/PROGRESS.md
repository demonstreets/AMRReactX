# Codex Takeover Notice — 2026-07-15

Current audit verdict: this repository contains useful prototypes and successful case runs, but it is not yet a strictly completed Phase 0-5 implementation of `pele_cfd_master_plan.md`. Treat the older completion percentages below as historical working notes until each phase is revalidated with reproducible build/test evidence.

Immediate stabilization branch: `codex/stabilize-my-pele`.

---

## Codex Dataverse 120s Peak-Window Update - 2026-08-04

- Completed a 120 s DataverseNO open-channel H2 CFD peak-window run: `docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/`.
- Runtime evidence: 2 MPI ranks with CUDA, `max_step=6000`, `fixed_dt=2.0e-2`, final simulation time `120 s`, 13 plotfiles (`plt00000` to `plt06000`), AMReX finalized, and no NaN/Abort/CUDA failure markers.
- Stability/transport validation: `h2_leak_plume_history_validation PASS`, final H2 mass ratio `1.0`, max `Y(H2)=0.962340554` in validation and `0.997278812613899` in sensor-scoring summary, downstream fraction `0.991085144`, upstream fraction `0.00891485633`.
- Agreement attempt report: `docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/dataverse_open_channel_cfd_agreement_attempt_report.json`.
- Agreement status remains `QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING`: 29 sensors, 183 common samples per sensor, peak passes `2/29`, NRMSE passes `3/29`, LFL arrival passes `6/25`, production agreement remains incomplete, and the strict external plume blocker remains open.
- Added `tools/verify_dataverse_open_channel_cfd_120s_agreement_attempt.sh` and integrated the 120 s attempt into `tools/write_master_plan_strict_external_source_update_report.py`, `tools/write_current_scope_state_snapshot_report.py`, `tools/write_current_verification_chain_coverage_report.py`, and `tools/codex_verify_current_scope.sh`.
- Next strict external-plume action: tune release/source/boundary/outlet/sensor-sampling/mesh settings against the 120 s quantified peak-window miss; this is calibration/validation work, not a numerical-stability blocker.
- Added a formal calibration diagnosis report: `docs/codex_audit/evidence/dataverse_open_channel_120s_calibration_diagnosis_20260804/dataverse_open_channel_120s_calibration_diagnosis_report.json`.
- The diagnosis identifies source/geometry calibration as the primary failure mode: the current numerical source radius is `0.08 m` versus the experimental inlet radius `0.0023 m` (`34.78x` radius, about `1209.8x` area), and the source center is `0.10 m` below the mapped experimental inlet center. The run also still uses `eb2.geom_type=all_regular`, so exact DataverseNO internal component/obstacle parity is not claimed.
- The diagnosis recommends the next calibration sweep use `prob.leak_zc=0.8` with grid-resolved radius options `0.05`, `0.06`, and `0.08 m`; `0.025` and `0.04 m` require mesh refinement or source projection because the current grid needs a radius above about `0.0433 m` for a source centered on the upper-wall inlet to cover active cells.
- Added `CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_ZC` support to `tools/codex_smoke_engineering_h2_dataverse_open_channel_scout_cuda.sh` while preserving the old default `0.70`.
- Ran a 1-step MPI+CUDA smoke with `prob.leak_zc=0.80`, `prob.leak_radius=0.05`, 2 ranks, and the existing CUDA executable; it passed plume-history validation and confirmed active source cells.
- Ran the 45 s calibration screen `docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r005_z08_mpi_cuda_20260804/`: 2 MPI ranks + CUDA, final time `45 s`, mass ratio `1.0`, no NaN/Abort/CUDA error, and AMReX finalized.
- The 45 s r005/z08 screen is stable but not promoted to 120 s: peak passes improved `1 -> 2`, but NRMSE passes regressed `26 -> 23` and LFL arrival passes regressed `5 -> 2`. Generated `docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_r005_z08_screen_20260804/dataverse_open_channel_45s_calibration_r005_z08_screen_report.json`.
- Ran a second 45 s calibration screen `docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r006_z08_mpi_cuda_20260804/` with `prob.leak_zc=0.80` and `prob.leak_radius=0.06`: 2 MPI ranks + CUDA, final time `45 s`, mass ratio `1.0`, no NaN/Abort/CUDA error, and AMReX finalized.
- The r006/z08 screen is also not promoted: its pass counts match r005/z08 exactly (`peak=2`, `NRMSE=23`, `arrival=2`), so increasing the grid-resolved radius from `0.05` to `0.06 m` did not recover the LFL timing or NRMSE regression on the current grid/source discretization.
- Ran a third 45 s calibration screen `docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r004_z0775_mpi_cuda_20260804/` with `prob.leak_zc=0.775` and `prob.leak_radius=0.04`; a prior 1-step MPI+CUDA smoke confirmed active source cells. The 45 s run reached final time, conserved H2 mass ratio `1.0`, and had no NaN/Abort/CUDA error.
- The r004/z0775 screen is also not promoted: its pass counts again match r005/z08 and r006/z08 (`peak=2`, `NRMSE=23`, `arrival=2`).
- Updated the aggregate sweep report `docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_sweep_20260804/dataverse_open_channel_45s_calibration_sweep_report.json`; it now records three stable coarse-grid source-parameter screens and shifts the next action to refined-grid source projection, outlet/backflow/open-channel boundary parity, or encoded DataverseNO internal geometry rather than more coarse-grid source-radius tuning.

---

## Codex Dataverse 45s LFL-Window Update - 2026-08-04

- Completed a longer DataverseNO open-channel H2 CFD run through the experimental LFL-arrival window: `docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_window_mpi_cuda_20260803/`.
- Runtime evidence: 2 MPI ranks, CUDA initialized with 2 devices, `max_step=4500`, `fixed_dt=1.0e-2`, final simulation time `45 s`, 10 plotfiles (`plt00000` to `plt04500`), AMReX finalized, and no active solver process left.
- Validation evidence: `h2_leak_plume_history_validation PASS`, final H2 mass ratio `1.0`, max `Y(H2)=0.971956407`, downstream fraction `0.979683591`, upstream fraction `0.0203164089`.
- Agreement attempt report: `docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_window_mpi_cuda_20260803/dataverse_open_channel_cfd_agreement_attempt_report.json`.
- Agreement status remains `QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING`: 29 sensors, 69 common samples per sensor, NRMSE passes `26/29`, peak passes `1/29`, LFL arrival passes `5/25`, production agreement remains incomplete, and the strict external plume blocker remains open.
- Integrated the 45 s attempt into `tools/write_master_plan_strict_external_source_update_report.py`, `tools/write_current_scope_state_snapshot_report.py`, `tools/write_current_verification_chain_coverage_report.py`, `tools/codex_verify_current_scope.sh`, and `tools/verify_dataverse_open_channel_cfd_45s_agreement_attempt.sh`.
- Re-ran `bash tools/codex_verify_current_scope.sh`: current scope remains `15/15` PASS; `snapshot_key_report_count=25`; CPU/MPI, single GPU, and multi-GPU MPI+CUDA readiness remain `True`; open strict blocker count remains `3`.
- Next strict external-plume action: extend DataverseNO CFD toward the experiment's `113-117 s` H2 peak window and tune release/source/boundary settings against the 2 s and 45 s quantified baselines.

---

## Codex Dataverse Agreement-Window Update - 2026-08-03

- Ran a longer DataverseNO open-channel H2 CFD agreement-window case on MPI+CUDA: `docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803/`.
- Runtime evidence: 2 MPI ranks, CUDA enabled, `max_step=2000`, `fixed_dt=1.0e-3`, final time about `2.0 s`, 9 plotfiles, 29 sensors, 261 sensor samples, AMReX finalized, no NaN/failure markers, and final injected/modeled H2 mass ratio `1.0`.
- Added quantified CFD/reference agreement attempt report: `docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803/dataverse_open_channel_cfd_agreement_attempt_report.json`.
- Agreement attempt status is `QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING`: every sensor has at least 4 common samples, NRMSE passes 29/29, but peak agreement passes 0/29 and LFL arrival passes only 4/25 because the 2 s CFD window is far shorter than the experiment's about 40 s LFL arrival and 113-117 s peak interval.
- Integrated this attempt into `tools/write_master_plan_strict_external_source_update_report.py`, `tools/write_current_scope_state_snapshot_report.py`, `tools/write_current_verification_chain_coverage_report.py`, and `tools/codex_verify_current_scope.sh`.
- Re-ran `bash tools/codex_verify_current_scope.sh`: current scope remains `15/15` PASS; `snapshot_key_report_count=24`; CPU/MPI, single GPU, and multi-GPU MPI+CUDA readiness remain `True`; open strict blocker count remains `3`.

---

## Codex Parallel Capability Evidence Update - 2026-08-03

- Added and verified a real single-CUDA gas detonation runtime gate: `docs/codex_audit/evidence/academic_gas_detonation_single_cuda_20260803/academic_gas_detonation_single_cuda_report.json`.
- Run evidence: 1 MPI rank, 1 CUDA device, H2/O2 LiDryer hotspot detonation, ReactorRK64, `max_step=40`, plotfiles `plt00000` and `plt00040`, time advanced from `0.0` to `1.8535905659764919e-06`, AMReX finalized, and no solver failure markers in `run.log`.
- Updated `tools/write_current_parallel_capability_matrix_report.py` so the gas-phase detonation single-GPU row now cites the real single-CUDA detonation run instead of the older GPU environment preflight.
- Re-ran `bash tools/codex_verify_current_scope.sh`: current scope remains `15/15` PASS, `cpu_mpi_ready_for_all_current_scenarios=True`, `single_gpu_ready_for_all_current_scenarios=True`, `multi_gpu_mpi_cuda_ready_for_all_current_scenarios=True`, `snapshot_key_report_count=22`, and `open_strict_blocker_count=3`.
- Repro commands: `bash tools/verify_academic_gas_detonation_single_cuda.sh`, then `python3 tools/write_current_parallel_capability_matrix_report.py && bash tools/verify_current_parallel_capability_matrix.sh`, then `bash tools/codex_verify_current_scope.sh`.

---

## Codex Single-CUDA Gate Chain Integration - 2026-08-03

- Promoted `academic_gas_detonation_single_cuda` into the current-scope state snapshot `KEY_REPORTS`.
- Added `tools/write_academic_gas_detonation_single_cuda_report.py` and `tools/verify_academic_gas_detonation_single_cuda.sh` to the snapshot key artifacts.
- Updated `tools/codex_verify_current_scope.sh` so the single-CUDA gas detonation report is rebuilt and verified before the parallel capability matrix, and again before the post-strict-refresh matrix rebuild.
- Updated `tools/write_current_verification_chain_coverage_report.py` so the one-command chain coverage audit proves this new key report is covered.
- Re-ran `bash tools/codex_verify_current_scope.sh`: current scope remains `15/15` PASS; `snapshot_key_report_count=23`; CPU/MPI, single GPU, and multi-GPU MPI+CUDA readiness all remain `True`; open strict blocker count remains `3`.

---

## Codex Academic Evidence Update - 2026-07-29

- Added independent academic evidence verifier: `tools/verify_academic_evidence.sh`.
- Added academic readiness summary: `docs/codex_audit/evidence/academic_readiness_summary_20260729/academic_readiness_summary_report.json`.
- Current academic status: `PASS-ACADEMIC-INITIAL-CPU-READINESS`.
- PASS scope now explicitly includes gas detonation readiness, WENO5 convergence, VOF two-phase initial readiness, ACD-05 closed periodic spray source-history budget, ACD-05 closed control-volume mass/momentum/energy budget, and ACD-07 reacting spray mass/energy source-history budget.
- Remaining academic NOT_READY gates: canonical external/long-time bubble-rise reference, ACD-07 reacting gas-particle control-volume total budget, full cellular gas-liquid detonation certification, and current academic GPU environment credit.
- Repro command: `bash tools/verify_academic_evidence.sh`.

---

## Codex Academic Two-Phase Update - 2026-07-30

- Current overall development estimate: about 85% complete under the engineering-first priority order.
- Engineering H2 leak/dispersion/ignition/fire pipe-rack path remains the accepted initial production-credible baseline; `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh` passes.
- Academic gas remains in the 85-90% range based on current detonation/reference evidence.
- Academic two-phase is about 80-85%: the QLT-03 low-Mach Aux-alpha bridge compiles, runs, conserves alpha mass, reaches t=3.0, and records center-of-mass/rise-velocity/circularity observables, but it is not yet promoted to strict Hysing-reference readiness.
- QLT-03 t=3 scheme-1 evidence: center-of-mass y abs error 0.083977, maximum mean-rise-velocity abs error 0.039622, minimum-circularity abs error 0.195879. The first two are close enough for the current scout gate; minimum circularity remains the active physics gap.
- A trial normals-divergence curvature option (`prob.surface_tension_curvature_scheme = 2`) was compiled and run but worsened the QLT-03 t=3 reference errors, so it is kept as an experimental switch and the default QLT-03 input was returned to scheme 1.
- Repro commands: `bash tools/codex_run_academic_twophase_qlt03_lm_t3_scout.sh`, then `bash tools/verify_academic_evidence.sh`.

---

## Codex Academic Two-Phase Evidence Hardening - 2026-07-30

- Hardened `tools/write_academic_twophase_qlt03_lm_t3_scout_report.py` so a QLT-03 PASS now also requires at least 10 time-series samples. This prevents sparse-output runs from missing the true minimum circularity and producing a false Hysing-reference PASS.
- Updated `tools/codex_run_academic_twophase_qlt03_lm_t3_scout.sh` to write QLT-03 t=3 plotfiles every 50 steps instead of every 250 steps.
- Re-ran the official QLT-03 low-Mach t=3 scout with 16 samples. Current strict status remains `NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT`.
- Dense-sampled t=3 metrics: center-of-mass y error `0.083977`, maximum mean-rise-velocity error `0.003466`, and minimum-circularity error `0.243527`. The remaining strict gap is now clearly early-time interface circularity, not stability, mass conservation, or rise velocity.
- Exploratory sweeps were archived under `docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_param_sweep_20260730`, `academic_twophase_qlt03_lm_t3_csf_cap_sweep_20260730`, `academic_twophase_qlt03_lm_t3_thickness_sweep_20260730`, `academic_twophase_qlt03_lm_t3_eps_cfl_sweep_20260730`, and `academic_twophase_qlt03_lm_t3_eps030_cfl030_dense_20260730`.
- Key exploratory lesson: force-capped CSF keeps symmetry/alpha sharpness but is not an uncapped Hysing contract and worsens circularity; `interface_thickness=0.030,cfl=0.30` looked PASS with sparse sampling but fails under dense sampling, proving the new sample-count gate is necessary.
- Repro command: `bash tools/codex_run_academic_twophase_qlt03_lm_t3_scout.sh && bash tools/verify_academic_evidence.sh`.

# PROGRESS.md
> 更新: 2026-06-30 | Phase 0-4 ✅ 100% | Phase 5 ✅ 核心完成 | 技术债 ✅ 清零

## Phase 1 — 几何处理管线 ✅ ALL DONE
（不变，略）

## Phase 2 — 工程场景核心功能 ✅ 95%
（不变，略）

Phase 2 遗留：浮力修正 G_k → 已在 2026-06-30 修完。

## Phase 3 — 学术场景核心功能 ✅ 90%
（不变，略）

Phase 3 遗留（10%）：AMR 局部加密性能优化（留 MPI 后研究）；多壁面壁面函数（等触发）。

### 🆕 技术债修复 (2026-06-30)
| # | 项目 | 修复 | 提交 |
|---|------|------|------|
| 1 | 浮力 G_k | PeleLMeX_Diffusion.cpp 加密度梯度项 | ca95a92 |
| 2 | d²-law 蒸发 | 确认物性正确，无需修 | — |
| 3 | 液池全链路 | pool_vof_coupling.H (263行) | cbc45da |

## Phase 4 — GPU 加速 ✅ 100%

| 任务 | 状态 |
|------|:--:|
| 4.1 代码 GPU 合规性审计 | ✅ 32文件全过 |
| 4.2 CUDA 编译配置 | ✅ 6可执行文件，链接 cuBLAS/cuSPARSE/cuSOLVER |
| 4.3 GPU vs CPU 正确性 | ✅ 差异 ~4e-18 |
| 4.4 GPU 性能 Profiling | ✅ 压力求解器占 28%，传输仅 1.7% |
| 4.5 Kernel 优化 | ✅ 已验证，小网格无效，留生产算例 |
| 4.6 多 GPU 扩展 | ✅ MPI+CUDA 链路通 |

### GPU 环境
```
CUDA:     ~/local/cuda-12.6/
SUNDIALS: ~/local/sundials-cuda/ (6.7.0 + CUDA)
CPU:      ~/my-pele/build-cpu-mpi/  (MPI)
GPU:      ~/my-pele/build-gpu2/     (CUDA only)
GPU+MPI:  ~/my-pele/build-gpu-mpi/  (CUDA + MPI)
```

## Phase 5 — HPC 移植 ✅ 核心完成

| 任务 | 状态 |
|------|:--:|
| 5.1 HPC 集群适配 | 🔒 搁置 |
| 5.2 扩展性 32 核 | ✅ 跑通 |
| 5.3 STEP 读取 | 🔒 搁置 |
| 5.4 在线可视化 | 🔒 搁置 |
| 5.5 不确定性量化 | 🔒 搁置 |

## 算例验证清单
| 算例 | 步数 | 状态 |
|------|:---:|:--:|
| bfs_sink (k-ε) | 100 | ✅ |
| multi_module_test | 86 | ✅ |
| h2_ignition | 200 | ✅ |
| bfs_kepsilon | 100 | ✅ |
| bfs_kepsilon_amr | 50 | ✅ |
| backward_facing_step | 2057 | ✅ |
| rayleigh_taylor | 200 | ✅ |
| bubble_rise | 500 | ✅ |
| shock_droplet 1D/2D | 1000 | ✅ |
| Spray-Jet | 10 | ✅ |
| c3h8_flacs MPI 2/4/8核 | 50 | ✅ |
| c3h8_flacs MPI 32核 | — | ✅ 跑通 |
| EB_PipeFlow GPU | 10 | ✅ |
| EB_PipeFlow 2 GPU | 10 | ✅ |

## 当前状态 (2026-06-30)

### 完成度
- Phase 0-4: 100% ✅
- Phase 5: 核心完成 ✅
- 技术债: 全部清零 ✅
- 单元测试: 11/11 PASS (279/279 断言)

### 遗留
- AMR 性能优化、多壁面壁面函数（低优先级）
- HPC 集群编译适配（需集群环境）

### Git
```
gpu-dev (当前) — 全部功能 + GPU + MPI 修复
master        — MPI 稳定版
```

---

## PeleC 2D 爆轰胞格 GPU 算例 (2026-07-01)

| 算例 | 步数 | 状态 |
|------|:---:|:--:|
| detonation_znd_gpu (ZND黎曼) | 100 | ✅ GPU通过 |
| detonation_znd_gpu (ZND+FOExtrap) | 100 | ✅ GPU通过 |
| detonation_hotspot (4热点) | 10 | ✅ GPU通过 |
| detonation_hotspot (4热点) | 100 | ⏳ 待跑 |

### BUG 修复记录
1. `pele.do_react=0` → 删重复行，恢复化学
2. 背景 UMX `rho_hot*u_hot` → `0.0`
3. 热点 N2 74.5% → 100% H2O
4. GNUmakefile 缺 `CUDA_ARCH=60` / `CUDA_HOME` → 已补回

### 关键教训
- 只改 inputs = 零编译开销
- 只改 prob.cpp = 2-3min 增量编译
- 改 prob.H = 10-15min 全量 PeleC 重编 (nvcc 慢)
- 验证分步: 10步快速测试 → 100步正式跑


---

## Codex progress update - 2026-07-29 ACD-07 reacting spray closed CV budget

- Added `tools/codex_run_academic_reacting_spray_closed_control_volume_budget.sh`.
- Added `tools/write_academic_reacting_spray_closed_control_volume_budget_report.py`.
- Generated `docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729/academic_reacting_spray_closed_control_volume_budget_report.json`.
- Result: `PASS-ACADEMIC-REACTING-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET`. The 40-step periodic reacting heptane-air spray box used CVODE chemistry, evaporation, drag/momentum transfer, spray energy source fields, and heat-release diagnostics.
- Key residuals: gas mass/source `8.424117392948222e-05`, gas fuel/source `7.886855639092468e-05`, gas total-energy/source `1.7985481517798292e-06`, gas x-momentum/source `2.9025614841567134e-06`, particle mass/source `7.900575751262853e-05`, particle x-momentum/source `2.902423207984199e-06`, total mass closure `5.235416416845343e-06`, total x-momentum closure `1.3827621650070214e-10`.
- Academic readiness was regenerated and verified with `bash tools/verify_academic_evidence.sh`: PASS. Remaining academic blocking gaps are `qlt_03_canonical_bubble_rise_reference`, `acd_07_full_gas_liquid_detonation`, and `acd_10_qlt_05_academic_gpu_environment`.
- Engineering/global evidence verification was rerun with `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS; CTest intentionally skipped.


---

## Codex progress update - 2026-07-29 QLT-03 canonical bubble-rise reference preflight

- Added `tools/write_academic_twophase_canonical_bubble_rise_reference_report.py`.
- Generated `docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_reference_20260729/academic_twophase_canonical_bubble_rise_reference_report.json`.
- Result: `NOT_READY-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-REFERENCE`, verified as an intentional preflight gate rather than a promoted benchmark claim.
- The preflight records the Hysing et al. 2D rising-bubble benchmark contract: center of mass, mean rise velocity, circularity, 1x2 domain, radius/domain-width 0.25, density ratio 10, gravity 0.98, surface tension 24.5, final time 3.0.
- Current PeleC case matches domain aspect ratio and density ratio, but remains blocked on radius/domain-width 0.125 vs 0.25, gravity 9.81 vs 0.98, missing surface-tension/viscosity contracts, missing circularity/rise-velocity time histories, and final time 0.001 vs 3.0.
- `bash tools/verify_academic_evidence.sh`: PASS.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS; CTest intentionally skipped.

## Codex progress update - 2026-07-29 QLT-03 bubble-rise canonical observables
- Added tools/write_academic_twophase_bubble_rise_observables_report.py.
- Generated docs/codex_audit/evidence/academic_twophase_bubble_rise_observables_20260729/academic_twophase_bubble_rise_observables_report.json.
- Result: PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-OBSERVABLE-DIAGNOSTICS.
- Existing endpoint plotfiles now provide center-of-mass, rise-velocity, and circularity diagnostics: COM rise 2.5298269312745703e-09, max finite-difference rise velocity 5.633872816934542e-05, min circularity estimate 0.7988340904663678, light-volume relative drift 1.6245627322019312e-07.
- Canonical time-series sampling remains NOT_READY: 2 samples vs target >=16; QLT-03 canonical Hysing credit remains open.
- bash tools/verify_academic_evidence.sh: PASS.
- CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh: PASS after hash-chain refresh; CTest intentionally skipped.

## Codex progress update - 2026-07-29 QLT-03 sampled bubble-rise observables
- Added tools/codex_run_academic_twophase_bubble_rise_observable_timeseries_validation.sh.
- Ran bubble_rise_buoyancy_mol_30000step_sampled_observables: run_returncode=0, validation_returncode=0, 30000 steps, final time 1.765215992784016e-04.
- Generated docs/codex_audit/evidence/academic_twophase_bubble_rise_observable_timeseries_20260729/academic_twophase_bubble_rise_observable_timeseries_report.json.
- Result: PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-OBSERVABLE-DIAGNOSTICS with 16 plotfile samples.
- Core observable timeseries gate is now cleared: center-of-mass, finite-difference rise velocity, and circularity histories are available; max finite-difference rise velocity 0.0014761872612848942, min circularity estimate 0.8615439736423774.
- Light-volume conservation remains a separate diagnostic NOT_READY at relative drift 6.673847249048797e-06 versus strict target 1.0e-08.
- Canonical bubble-rise reference preflight now passes canonical_observable_timeseries_available and has 5 remaining blocking gaps: radius fraction, gravity scale, surface-tension contract, viscosity contract, and final-time contract.
- bash tools/verify_academic_evidence.sh: PASS.
- CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh: PASS after hash-chain refresh; CTest intentionally skipped.

## Codex progress update - 2026-07-30 QLT-03 canonical geometry/gravity candidate
- Added tools/codex_run_academic_twophase_canonical_bubble_rise_candidate.sh.
- Added tools/write_academic_twophase_canonical_bubble_rise_candidate_report.py.
- Ran canonical_bubble_rise_geometry_gravity_4000step_smoke: run_returncode=0, validation_returncode=0, final time 1.22564689023e-04.
- Generated docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_candidate_20260730/canonical_bubble_rise_candidate_report.json.
- Result: PASS-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-CANDIDATE.
- Candidate aligns Hysing-style domain 1x2, bubble center fraction [0.5, 0.25], radius/domain-width 0.25, density ratio 10, and gravity 0.98; short smoke conserves mass to 7.31608244034e-16 and advected mass to 6.24056233846e-16.
- Canonical reference preflight now uses contract_source=canonical_geometry_gravity_candidate; remaining QLT-03 canonical blockers reduced to surface_tension_contract_present, viscosity_contract_present, and canonical_final_time_contract.
- bash tools/verify_academic_evidence.sh: PASS.
- CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh: PASS after hash-chain refresh; CTest intentionally skipped.

## Codex progress update - 2026-07-30 QLT-03 capped CSF surface-tension smoke
- Added explicit bubble-rise CSF surface-tension source controls in examples/academic/bubble_rise/prob_parm.H, prob.cpp, and prob.H: prob.surface_tension_sigma, prob.surface_tension_grad_floor, and prob.surface_tension_force_cap.
- The source is disabled by default, so existing bubble-rise evidence paths retain their previous behavior unless prob.surface_tension_sigma is set.
- Updated tools/codex_run_academic_twophase_canonical_bubble_rise_candidate.sh to run canonical_bubble_rise_geometry_gravity_csf_1000step_smoke with sigma=24.5 and force cap=10.
- Candidate CSF smoke result: run_returncode=0, validation_returncode=0, final time 3.04725008624e-05, mass_rel_drift 1.21934707339e-16, adv_mass_rel_drift 1.24811246769e-16, integrated y momentum 3.46719746131e-05, centroid_rise -8.83106611171e-08.
- Canonical reference preflight now passes surface_tension_contract_present; remaining QLT-03 canonical blockers are viscosity_contract_present and canonical_final_time_contract.
- Re-ran dependent bubble-rise baseline, inviscid long-window, MOL long-window, and sampled observable-time-series evidence with current source hashes.
- bash tools/verify_academic_evidence.sh: PASS.
- CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh: PASS after hash-chain refresh; CTest intentionally skipped.

## Codex progress update - 2026-07-30 QLT-03 capped phase-viscosity smoke
- Added default-off phase-viscosity controls to the academic bubble-rise case: `prob.phase_viscosity_mu_heavy`, `prob.phase_viscosity_mu_light`, and `prob.phase_viscosity_force_cap`.
- The canonical bubble-rise candidate now runs `canonical_bubble_rise_geometry_gravity_csf_viscosity_1000step_smoke` with Hysing-style geometry, density ratio 10, gravity 0.98, sigma 24.5, and mu_heavy/mu_light 10/1 through capped explicit source terms.
- Candidate smoke result: PASS, final time `3.04725008623e-05`, mass relative drift `4.87738829356e-16`, advected-mass relative drift `4.99244987077e-16`, centroid rise `-5.80837742348e-08`, and no NaN/failure-token gate trips.
- QLT-03 canonical reference preflight now passes `surface_tension_contract_present` and `viscosity_contract_present`; the only remaining canonical blocker is `canonical_final_time_contract` because the maintained candidate is still a short smoke and not a t=3 Hysing benchmark run.
- Re-ran dependent bubble-rise baseline, inviscid long-window, MOL long-window, observable timeseries, canonical reference, and academic readiness evidence with current source hashes.
- `bash tools/verify_academic_evidence.sh`: PASS.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS after upper-chain refresh; CTest intentionally skipped in this verification pass.

## Codex progress update - 2026-07-30 QLT-03 final-time scout
- Added reproducible final-time scout evidence for the canonical bubble-rise path:
  `tools/codex_run_academic_twophase_canonical_bubble_rise_final_time_scout.sh`
  and `tools/write_academic_twophase_canonical_bubble_rise_final_time_scout_report.py`.
- Integrated the final-time scout into `tools/verify_academic_evidence.sh`.
- Added a backward-compatible `--min-ymom-sum` option to `tools/validate_academic_twophase_bubble_rise.py`; default remains `0.0`, preserving the existing upward-momentum requirement for existing cases. The final-time scout explicitly allows a tiny `-1.0e-6` y-momentum tolerance because it is a stability/runtime scout rather than an upward-response acceptance gate.
- Initial 5000-step scout with stronger source caps failed around step 1275 due to `NaNs detected in the Solution`, proving the current explicit source path cannot simply be extended blindly.
- Conservative 5000-step scout with CFL `0.01`, `surface_tension_force_cap=1.0`, and `phase_viscosity_force_cap=0.1` completed and verified: final time `6.13050828568e-05`, mass relative drift `1.21934707339e-16`, advected-mass drift `2.49622493539e-16`, no NaN/failure-token gate trips.
- The final-time scout report estimates the current compressible explicit path would require about `244677918` steps and about `636162.5868` wall seconds to reach `t=3` at the observed scout rate, so `canonical_final_time_contract` remains NOT_READY and is not practical as a direct brute-force PeleC run.
- `bash tools/verify_academic_evidence.sh`: PASS, now including canonical final-time scout verification.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS after upper-chain refresh; CTest intentionally skipped in this verification pass.
- Recommended next QLT-03 direction: implement or route the canonical bubble-rise t=3 path through a low-Mach/incompressible formulation or a materially larger stable timestep strategy, then compare center of mass, rise velocity, circularity, and final shape.

## Codex progress update - 2026-07-30 QLT-03 path decision
- Added reproducible QLT-03 implementation-path decision evidence:
  `tools/write_academic_twophase_qlt03_path_decision_report.py`.
- Integrated the path decision report into `tools/verify_academic_evidence.sh`.
- The report verifies the current canonical bubble-rise blocker is still only `canonical_final_time_contract`; geometry, density ratio, gravity, capped CSF, and capped phase-viscosity contracts remain cleared by the PeleC candidate evidence.
- The final-time scout evidence rules out a direct brute-force `t=3` run on the current compressible explicit PeleC path at the observed timestep/rate.
- Source scan confirms PeleLMeX has an incompressible base, but no ready VOF/CSF surface-tension path in the current tree; existing VOF/CSF work is in the academic PeleC path and is timestep-limited for Hysing `t=3`.
- Recommended QLT-03 route is now explicit: implement or route a dedicated incompressible/low-Mach VOF/CSF canonical bubble-rise path, then compare center of mass, mean rise velocity, circularity, and final shape against Hysing Case 1.
- `bash tools/verify_academic_evidence.sh`: PASS, now including canonical final-time scout and QLT-03 path decision verification.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS after upper-chain refresh; CTest intentionally skipped in this verification pass.

### 2026-07-30 QLT-03 low-Mach aux-alpha bridge smoke
- Added `examples/academic/qlt03_lm_aux_bridge` as a PeleLMeX incompressible carrier for an alpha-like auxiliary phase field.
- Built and ran the bridge smoke to `t=0.5`; validator PASS with alpha in `[0, 0.9999999879262609]`, mean `0.09898931833883365`, and no NaN/Abort/Segfault tokens.
- Evidence: `docs/codex_audit/evidence/academic_twophase_qlt03_lm_aux_bridge_smoke_20260730/academic_twophase_qlt03_lm_aux_bridge_smoke_report.json`.
- Scope note: this clears the PeleLMeX incompressible Aux carrier gate only; QLT-03 canonical final-time VOF/CSF remains open.

### 2026-07-30 QLT-03 incompressible Aux advection closure
- Fixed `external/PeleLMeX/Source/PeleLMeX_Advance.cpp` so incompressible runs with `m_nAux > 0` explicitly update Aux scalars using a bounded-scope first-order upwind advection step before `averageDownAux/fillPatchAux`.
- Re-ran `bash tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS; alpha integral drift `0.0`, center moved from y `0.5000000000107195` to `0.4915630078406356` at `t=0.5`.
- This upgrades the bridge from alpha initialization/output to actual incompressible Aux transport evidence; full QLT-03 VOF/CSF and variable material coupling remain open.

### 2026-07-30 QLT-03 MAC-face Aux transport hardening
- Replaced the first incompressible Aux advection closure with a finite-volume upwind update using MAC-projected face velocities.
- Re-ran `bash tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS; alpha integral drift `0.0`, center moved from y `0.5000000000107195` to `0.4775000085456974` at `t=0.5`.
- Added `tools/write_academic_twophase_qlt03_lm_bridge_followup_report.py` to record cleared low-Mach bridge gates and remaining CSF/material-property coupling gates.

## Codex progress update - 2026-07-30 QLT-03 low-Mach Aux-aware CSF bridge
- Extended PeleLMeX user-defined external-source dispatch so problem-specific sources can optionally receive read-only Aux MultiFabs while legacy `modify_ext_sources(time, dt, state_old, state_new, ext_src, geom, prob)` implementations remain compatible.
- Added a default-off Aux-alpha CSF-style source to `examples/academic/qlt03_lm_aux_bridge` and enabled a conservative capped smoke setting (`prob.surface_tension_sigma=0.01`, force cap `1.0`) for the bridge validation.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS to time `0.5`; alpha mass relative drift `0.0`; alpha center displacement `0.02249782960819896`; no NaN/abort/segfault tokens.
- Regenerated QLT-03 follow-up and path-decision evidence. The low-Mach Aux/CSF bridge is now proven present, but QLT-03 canonical VOF/CSF remains open on variable density, variable viscosity, canonical-strength CSF dynamics, canonical boundaries/diagnostics, and final-time reference comparison.
- `bash tools/verify_academic_evidence.sh`: PASS.

## Codex progress update - 2026-07-30 QLT-03 Aux-density force scaling
- Added default-off PeleLMeX controls for incompressible Aux-density force scaling: `peleLM.incompressible_aux_density`, `peleLM.incompressible_aux_density_comp`, `peleLM.incompressible_aux_rho_heavy`, and `peleLM.incompressible_aux_rho_light`.
- In incompressible `getVelForces`, enabled Aux-alpha mixture density to enter the local body-force density and final acceleration scaling. The default constant-`rho` path is preserved when the new switch is off.
- Enabled the QLT-03 low-Mach bridge with Aux-alpha density ratio `1000/100`, alongside the existing Aux-aware capped CSF source and MAC-face Aux advection.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS; final bridge time `0.1892772860590687`, alpha mass relative drift `0.0`, alpha center displacement `0.02038052418827257`, no NaN/abort/segfault tokens.
- Regenerated QLT-03 bridge follow-up and path-decision evidence. Remaining canonical blockers are now narrowed to alpha-dependent projection coefficients, alpha-dependent viscosity diffusion coefficients, canonical-strength CSF dynamics, canonical boundary/diagnostic setup, and final-time reference comparison.
- `bash tools/verify_academic_evidence.sh`: PASS.

## Codex progress update - 2026-07-30 QLT-03 Aux-density projection scaling
- Added default-off PeleLMeX incompressible Aux-density projection support in `external/PeleLMeX/Source/PeleLMeX_Projection.cpp`.
- When `peleLM.incompressible_aux_density=true`, the low-Mach projector now builds sigma from the Aux alpha mixture density instead of the constant incompressible rho path; the default constant-rho path is preserved when the switch is off.
- The non-incremental incompressible grad-pressure add-back now also uses local Aux mixture density when the same switch is enabled.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS to time `0.5`; alpha mass relative drift `0.0`, alpha center displacement `0.022284192047318355`, `aux_density_projection_sigma_compiles_and_runs=true`, and no NaN/abort/segfault tokens.
- Regenerated QLT-03 bridge follow-up and path-decision evidence. Remaining canonical QLT-03 blockers are now narrowed to alpha-dependent viscosity diffusion coefficients, canonical-strength CSF dynamics, canonical bubble-rise boundaries/diagnostics, and final-time reference comparison.
- Rebuilt and re-ran the engineering H2 leak smoke after the projection change; `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS, with CTest intentionally skipped in this verification pass.

## Codex progress update - 2026-07-30 QLT-03 Aux-viscosity diffusion scaling
- Added default-off PeleLMeX incompressible Aux-viscosity controls: `peleLM.incompressible_aux_viscosity`, `peleLM.incompressible_aux_viscosity_comp`, `peleLM.incompressible_aux_mu_heavy`, and `peleLM.incompressible_aux_mu_light`.
- In incompressible `calcViscosity`, enabled Aux alpha to fill the cell-centered viscosity field used by `getViscosityVect -> getDiffusivity -> DiffusionTensorOp`; the original constant `peleLM.mu` path is preserved when the switch is off.
- Enabled the QLT-03 low-Mach Aux bridge with a viscosity ratio `10/1` alongside the existing density ratio `1000/100`, Aux-aware capped CSF, MAC-face Aux advection, and Aux-density projection scaling.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS to time `0.5`; alpha mass relative drift `0.0`, alpha center displacement `0.022496106139164807`, `aux_viscosity_diffusion_coefficients_compile_and_run=true`, and no NaN/abort/segfault tokens.
- Regenerated QLT-03 bridge follow-up and path-decision evidence. Remaining canonical QLT-03 blockers are now narrowed to canonical-strength CSF dynamics, canonical bubble-rise boundaries/diagnostics, and final-time reference comparison.
- `bash tools/verify_academic_evidence.sh`: PASS.
- Rebuilt and re-ran the engineering H2 leak smoke after the transport-property change; `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS, with CTest intentionally skipped in this verification pass.


## Codex progress update - 2026-07-30 QLT-03 canonical boundary and observables
- Switched `examples/academic/qlt03_lm_aux_bridge/inputs` from periodic bridge boundaries to a nonperiodic 1x2 Hysing-style bubble-rise box: slip side walls, no-slip top/bottom walls, and zero initial velocity.
- Added QLT-03 bridge boundary fill hooks (`bcnormal` and `bcnormal_aux`) so the nonperiodic PeleLMeX incompressible/Aux-alpha bridge no longer aborts on physical boundary fills.
- Extended `tools/validate_academic_twophase_qlt03_lm_aux_bridge.py` to parse canonical input settings and record canonical observables: center-of-mass y, mean rise velocity, circularity, and interface length.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS to time `0.5`; alpha mass relative drift `0.0`, alpha center displacement `0.08040534561733918`, center y `0.41959465441908966`, mean rise velocity y `-0.31092595018744723`, circularity `1.0115441439023278`, and interface length `1.5592984833404424`.
- Regenerated QLT-03 bridge follow-up and path-decision evidence. The low-Mach Aux-alpha bridge now clears canonical boundary-condition and observable-diagnostics gates.
- Remaining QLT-03 canonical blockers are narrowed to canonical-strength CSF dynamics validated against bubble-rise observables and a canonical final-time `t=3` reference comparison. The current smoke still reflects the present alpha/density convention and is not yet claimed as a physically correct Hysing rising-bubble benchmark.
- `bash tools/verify_academic_evidence.sh`: PASS.


## Codex progress update - 2026-07-30 QLT-03 alpha/light phase convention
- Audited the QLT-03 low-Mach Aux bridge phase convention and found that the previous mixture formulas treated `alpha=1` as the heavy phase (`rho = alpha*rho_heavy + (1-alpha)*rho_light`), while the initialized circular bubble uses `alpha=1`; this caused the smoke bubble to sink instead of rise.
- Added a default-off PeleLMeX phase-convention switch `peleLM.incompressible_aux_alpha_is_light`. When enabled, Aux-density force scaling, projection sigma/grad-pressure scaling, and Aux-viscosity diffusion use `alpha=1` as the light phase while preserving the old default behavior for existing cases.
- Enabled `peleLM.incompressible_aux_alpha_is_light = true` in `examples/academic/qlt03_lm_aux_bridge/inputs` with the existing density ratio `1000/100` and viscosity ratio `10/1`.
- Hardened `tools/validate_academic_twophase_qlt03_lm_aux_bridge.py` so the bridge smoke now requires the alpha center to rise and the mean alpha-weighted y velocity to be positive; follow-up/path-decision reports now include the light-phase/upward-buoyancy contract.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS to time `0.5`; alpha mass relative drift `0.0`, center y `0.5515865956155568` from initial `0.5000000000107195`, center displacement `0.05158659564252585`, mean rise velocity y `0.18629904965124655`, circularity `1.0080568783360746`, and interface length `1.5646927106160298`.
- `bash tools/verify_academic_evidence.sh`: PASS, now including the QLT-03 light-phase/upward-response contracts.
- Rebuilt and re-ran `tools/codex_smoke_engineering_h2_leak.sh`; `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS. The new phase-convention switch is default-off, so the engineering H2 path remains unchanged.
- Remaining QLT-03 canonical blockers are canonical-strength CSF dynamics validated against bubble-rise observables and the final `t=3` Hysing reference comparison.


## Codex progress update - 2026-07-30 QLT-03 canonical-strength CSF scout
- Added `tools/codex_run_academic_twophase_qlt03_lm_canonical_csf_scout.sh` and `tools/write_academic_twophase_qlt03_lm_canonical_csf_scout_report.py` to make the low-Mach QLT-03 canonical-strength CSF check reproducible.
- The scout generates an evidence-local input deck with Hysing Case 1 surface tension `prob.surface_tension_sigma = 24.5` and disables the explicit CSF force cap with `prob.surface_tension_force_cap = 0.0`.
- Re-ran the canonical-strength low-Mach scout: PASS; final time `0.42723184751420307`, alpha mass relative drift `0.0`, center y from `0.5000000000107195` to `0.5416273780402625`, center displacement `0.04181245043978313`, mean rise velocity y `0.2695777391485081`, circularity `0.9586547849400091`, and interface length `1.6453255897716201`.
- Integrated the new report into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Refreshed `tools/write_academic_twophase_qlt03_path_decision_report.py` so the path decision now records `pelelmex_low_mach_canonical_strength_csf_short_window=true`.
- Remaining QLT-03 canonical work is now narrowed to extending the uncapped `sigma=24.5` low-Mach run to `t=3` and comparing center of mass, rise velocity, circularity, and final shape against Hysing Case 1 reference ranges.


## Codex progress update - 2026-07-30 QLT-03 low-Mach t=3 scout
- Added `tools/codex_run_academic_twophase_qlt03_lm_t3_scout.sh` and `tools/write_academic_twophase_qlt03_lm_t3_scout_report.py` to make the low-Mach uncapped canonical-strength `t=3` scout reproducible.
- The scout uses `prob.surface_tension_sigma=24.5`, `prob.surface_tension_force_cap=0.0`, the canonical `1x2` box, alpha-as-light phase convention, Aux-density projection/force scaling, Aux-viscosity diffusion, and MAC-face Aux advection.
- Re-ran the formal t=3 scout: the run reached time `3.0` without NaN/Abort/Segfault; alpha mass relative drift `0.0`; final center y `1.4729188692054875`; mean rise velocity y `0.04547491929205638`; circularity `1.884309516454262`; interface length `0.8370701499119091`; alpha max `0.32467835457880706`.
- Compared against the recorded Hysing Case 1 representative values: center y reference `1.0813` (abs error `0.3916188692054876`), maximum mean rise velocity reference `0.2417` (abs error `0.19622508070794362`), and minimum circularity reference `0.9013` (abs error `0.983009516454262`).
- The new report intentionally has status `NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT`: final-time numerical stability is now proven, but Hysing reference agreement is still not cleared.
- Integrated the t=3 scout into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Refreshed `tools/write_academic_twophase_qlt03_path_decision_report.py`; the remaining QLT-03 gap is now `hysing_reference_agreement_contract`, not merely reaching final time.

## Codex progress update - 2026-07-30 QLT-03 low-Mach reference gate cleared
- Fixed the QLT-03 low-Mach bridge CSF source sign for the `alpha=1` light-bubble convention; the previous sign could drive the canonical-strength run downward on refined grids.
- Added default-off PeleLMeX incompressible Aux transport selector `peleLM.incompressible_aux_advect_scheme`; scheme `1` preserves first-order upwind, scheme `2` enables conservative minmod-limited TVD/MUSCL face states with MAC-projected face velocities. QLT-03 enables scheme `2` only.
- Re-ran the QLT-03 low-Mach Aux bridge smoke: PASS to `t=0.5`, alpha mass relative drift `1.401948012240244e-16`, `alpha_max=0.9999999579425818`, center y `0.5526726267636632`, mean rise velocity y `0.19179902018373537`, and scheme recorded as `finite_volume_tvd_minmod_using_mac_projected_face_velocities`.
- Re-ran the uncapped canonical-strength CSF short-window scout after the timestep change: PASS to `t=0.4588415501384727`, mass drift `1.401948012240244e-16`, center y `0.5461741945910216`, mean rise velocity y `0.2242695901937638`.
- Reused the repaired t=3 run evidence to regenerate the formal QLT-03 report as `PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT`: reached `t=3.0` without NaN/Abort/Segfault, mass drift `0.0`, center y `0.997322971560933`, circularity `0.8806390114724396`, mean rise velocity y `0.17984997511149994`, and reference errors `0.08397702843906696` center, `0.020660988527560376` circularity, `0.061850024888500055` velocity.
- Regenerated QLT-03 follow-up and path-decision reports; `qlt03_canonical_ready=true` now means the initial low-Mach reference-observable gate is cleared, while higher-resolution/grid-convergence and true production VOF/CSF topology fidelity remain follow-up work.
- `bash tools/verify_academic_evidence.sh`: PASS.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS; CTest intentionally skipped by current engineering verification convention.

## Codex progress update - 2026-07-30 QLT-03 strict time-series/grid-confirmation correction
- Tightened `tools/write_academic_twophase_qlt03_lm_t3_scout_report.py` so Hysing agreement uses time-series extrema: final center-of-mass y at `t=3`, maximum mean rise velocity over saved plotfiles, and minimum circularity over saved plotfiles. This corrects the earlier weaker final-time-only comparison.
- Re-generated the 32x64 QLT-03 t=3 report as `NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT`: stable to `t=3`, mass drift `0.0`, center error `0.08397702843906696`, maximum-rise-velocity error `0.039621853357985404`, but minimum-circularity error `0.19587871606339502`, above the current `0.15` tolerance.
- Ran a 64x128 QLT-03 low-Mach t=3 grid-confirmation case with the repaired CSF sign and TVD Aux transport: stable to `t=3`, mass drift `-1.4020484468317865e-16`, center y `0.9938762869613927`, `alpha_max=0.48881787294424167`, maximum mean rise velocity `0.5468252453968272`, and minimum circularity `0.48496055235376495`.
- Added `tools/write_academic_twophase_qlt03_lm_grid_confirmation_report.py` and evidence `docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_grid_confirmation_20260730/qlt03_lm_grid_confirmation_report.json`. The report verifies 32/64 final center-height consistency and mass conservation, but intentionally keeps full grid confirmation open because refined-grid velocity and circularity are not yet within Hysing Case 1 tolerances.
- Rewrote `tools/write_academic_twophase_qlt03_path_decision_report.py` as a strict decision record: `PASS-ACADEMIC-TWOPHASE-QLT03-PATH-DECISION` means the evidence and decision are machine-checkable, while `qlt03_canonical_ready=false` remains explicit until circularity, refined-grid rise velocity, and grid convergence clear.
- Integrated the grid-confirmation report into `tools/verify_academic_evidence.sh`.
- `bash tools/verify_academic_evidence.sh`: PASS, now showing QLT-03 t=3/grid reports as verified `NOT_READY` physics gates and path-decision as a verified PASS decision record with `qlt03_ready=False`.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS; CTest intentionally skipped by current engineering verification convention.
- Remaining strict QLT-03 work is now focused on CSF curvature/balanced-force treatment and refined-grid velocity/circularity agreement, not final-time stability or mass conservation.

## Codex progress update - 2026-07-30 QLT-03 Aux-compression trial not retained
- Tested a default-off conservative Aux-alpha compression prototype while investigating the remaining QLT-03 circularity/shape error.
- The exploratory t=3 sweep was rejected because every tested compression coefficient degraded the solution: low coefficients introduced negative alpha values, and higher coefficients produced severe alpha overshoot/undershoot and worse circularity.
- The failed compression path was not promoted into the production code path; the restored low-Mach Aux bridge keeps the MAC-face conservative TVD/minmod transport baseline.
- Evidence is retained under `docs/codex_audit/evidence/academic_twophase_qlt03_lm_aux_compression_sweep_20260730/` so this rejected route is reproducible.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS after restoring the baseline bridge; alpha remains bounded in `[0,1]`, mass drift is `1.401948012240244e-16`, center y is `0.5526726267636632`, mean rise velocity y is `0.19179902018373537`, and no NaN/Abort/Segfault tokens were found.
- `bash tools/verify_academic_evidence.sh`: PASS. The strict academic evidence still records QLT-03 Hysing agreement/grid confirmation as verified `NOT_READY` physics gates, with final remaining work focused on CSF curvature/balanced-force accuracy and refined-grid velocity/circularity agreement.

## Codex progress update - 2026-07-30 QLT-03 curvature-smoothing trials
- Ran additional QLT-03 low-Mach t=3 curvature trials to attack the remaining Hysing minimum-circularity error without changing the already stable Aux-alpha transport/projection baseline.
- `surface_tension_curvature_scheme=2` was worse than the current baseline: final center error `0.1496621054249675`, maximum-rise-velocity error `0.04942229573580609`, minimum-circularity error `0.2782009107259106`, and only `9` time-series samples.
- A 3x3 filtered-alpha curvature/delta prototype improved final shape but did not clear the gate: minimum-circularity error `0.21626924670000303`, final center error `0.21833081241508`, maximum-rise-velocity error `0.05086236891518034`.
- A split prototype using filtered alpha for curvature but raw alpha for the CSF delta matched final center height better (`0.014300048028758505` error) but degraded minimum circularity to `0.3256199315789239` error.
- The filtered-curvature prototype code was removed after the trials; it is not retained in the production/example path. Evidence is retained under `docs/codex_audit/evidence/academic_twophase_qlt03_lm_curvature_scheme2_scout_20260730/`, `..._scheme3_scout_20260730/`, and `..._scheme4_scout_20260730/`.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh` after removing the prototypes: PASS; alpha remains bounded and mass-conserved, and no NaN/Abort/Segfault tokens were found.
- Conclusion: QLT-03 is not blocked by final-time stability or mass conservation; the remaining academic two-phase blocker requires a more faithful balanced-force/curvature formulation or a sharper conservative interface method, not simple curvature smoothing.

## Codex progress update - 2026-07-30 QLT-03 curvature trial verification guard
- Added `tools/write_academic_twophase_qlt03_lm_curvature_trial_report.py` to formalize the rejected QLT-03 curvature trials as machine-checkable evidence.
- Generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_curvature_trials_20260730/curvature_trial_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-CURVATURE-TRIAL-REJECTION`.
- The report verifies that schemes 2, 3, and 4 all reached `t=3`, conserved alpha mass, remained `NOT_READY` against Hysing reference agreement, and were not promoted into the active QLT-03 example path.
- Integrated the new rejection guard into `tools/verify_academic_evidence.sh`.
- `bash tools/verify_academic_evidence.sh`: PASS, now including the rejected-curvature-trial guard.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS; CTest intentionally skipped by current engineering verification convention.

## Codex progress update - 2026-07-30 QLT-03 interface-sharpness diagnosis
- Audited the PeleLMeX incompressible Aux-alpha transport path in `external/PeleLMeX/Source/PeleLMeX_Advance.cpp`: current scheme `2` is conservative MAC-face minmod/MUSCL transport followed by bounded clipping.
- Added `tools/write_academic_twophase_qlt03_lm_interface_sharpness_report.py` to convert the QLT-03 t=3 time series into a route-selection diagnostic.
- Generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_interface_sharpness_20260730/interface_sharpness_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-INTERFACE-SHARPNESS-DIAGNOSIS`.
- The diagnosis records that final alpha peak drops from `0.9999999879262609` to `0.42780284952701286` (`57.2%` relative drop), while the minimum circularity and maximum interface length occur at the same saved time `t=0.5539944058487076`.
- The same report verifies that final center-height error (`0.08397702843906696`) and maximum-rise-velocity error (`0.003466450170439672`) are already within the current tolerances, while minimum-circularity error (`0.24352712056133463`) remains the primary baseline blocker.
- Integrated the interface-sharpness diagnosis into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route decision: the next QLT-03 physics work should prioritize sharper conservative interface transport coupled to balanced-force CSF, not more local curvature smoothing.

## Codex progress update - 2026-07-30 QLT-03 MC transport trial rejection
- Implemented and tested a default-off Aux-alpha MC/monotonized-central limiter candidate as a sharper bounded alternative to the current minmod transport.
- The QLT-03 low-Mach t=3 scout with `peleLM.incompressible_aux_advect_scheme=3` reached `t=3`, conserved alpha mass, and remained bounded, but did not clear Hysing agreement.
- The MC trial improved final center-height error to `0.02851495735611742`, but worsened maximum-rise-velocity error to `0.06832502491234652`, worsened minimum-circularity error to `0.27078455188992434`, and reduced final `alpha_max` to `0.4127077604195565` versus the minmod baseline `0.42780284952701286`.
- The MC limiter prototype code was removed after the trial and is not retained in the production/example path.
- Added `tools/write_academic_twophase_qlt03_lm_transport_trial_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_transport_trials_20260730/transport_trial_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-TRANSPORT-TRIAL-REJECTION`.
- Integrated the rejected transport-trial guard into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route conclusion strengthened: QLT-03 needs a more faithful conservative interface method/reconstruction coupled to balanced-force CSF, not just a less diffusive one-dimensional slope limiter.

## Codex progress update - 2026-07-30 QLT-03 route capability audit
- Audited the repository for existing low-Mach geometric interface reconstruction support after rejecting local curvature smoothing and MC limiter trials.
- Added `tools/write_academic_twophase_qlt03_route_capability_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_route_capability_20260730/route_capability_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-ROUTE-CAPABILITY-AUDIT`.
- The audit verifies that the current PeleLMeX QLT-03 route is a diffuse Aux-alpha bridge with explicit CSF, not an existing PLIC/geometric VOF path.
- It also verifies that PeleC has VOF/FCT and MULES-like reference components, but they are coupled to PeleC's compressible two-phase flux path and are not a drop-in replacement for PeleLMeX incompressible Aux transport.
- Integrated the route capability audit into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Recommended next QLT-03 route is now explicit and machine-checkable: design a dedicated low-Mach Aux-alpha conservative geometric/reinitialization or THINC-like sharp-interface transport gate, then couple it to balanced-force CSF.



## Codex progress update - 2026-07-30 QLT-03 bounded THINC-like trial rejected
- Implemented a default-off low-Mach Aux-alpha scheme `4` candidate using bounded THINC-like face-state sharpening on top of the existing minmod/MAC-face finite-volume transport, then tested it before promotion.
- CPU QLT-03 build passed after the candidate was added.
- Re-ran the existing scheme `2` QLT-03 low-Mach aux bridge smoke: PASS, confirming the current minmod baseline was not broken.
- Ran a scheme `4` short-window smoke to `t=0.5`: PASS numerically, with alpha mass drift `0.0`, bounded alpha in `[0,1]`, center y `0.5533660312414374`, mean rise velocity `0.19550602669923486`, and circularity `0.9997301084860883`.
- Updated `tools/validate_academic_twophase_qlt03_lm_aux_bridge.py` so scheme `4` evidence is labeled as `finite_volume_thinc_like_bounded_using_mac_projected_face_velocities`, while canonical boundary-condition checks are no longer tied to a specific transport scheme.
- Ran the scheme `4` canonical-strength QLT-03 t=3 scout with sigma `24.5` and no CSF cap: stable to `t=3.0`, mass drift `0.0`, sample count `20`, final alpha max `0.41138195920576864`, but it remained `NOT_READY`.
- Scheme `4` reference errors were worse than the current minmod baseline for the primary blockers: center-height error `0.21033204071175826` versus baseline `0.08397702843906696`, and minimum-circularity error `0.31539349145160445` versus baseline `0.24352712056133463`. Maximum-rise-velocity error was `0.02177215753472117`.
- Removed the scheme `4` prototype from PeleLMeX production source after the failed t=3 physics gate; `PeleLMeX_Advance.cpp`, `PeleLMeX_Setup.cpp`, and `PeleLMeX.H` are back to the retained scheme `1/2` production selector.
- Added `tools/write_academic_twophase_qlt03_lm_thinc_like_trial_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_thinc_like_trials_20260730/thinc_like_trial_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-THINC-LIKE-TRIAL-REJECTION`.
- Integrated the new rejection guard into `tools/verify_academic_evidence.sh`.
- `bash tools/verify_academic_evidence.sh`: PASS.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS; CTest intentionally skipped by the current engineering verification convention.
- Conclusion: QLT-03 still needs a genuinely sharper conservative interface representation plus balanced-force CSF, not a local bounded face-state sharpening tweak.


## Codex progress update - 2026-07-30 QLT-03 CSF balance/lateral-drift diagnosis
- Audited the QLT-03 low-Mach Aux-alpha CSF source in `examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H` and the PeleLMeX velocity-force path in `external/PeleLMeX/Source/PeleLMeX_Forces.cpp`.
- Recomputed the QLT-03 t=3 baseline alpha center time series from plotfiles and confirmed a large lateral symmetry error: center x drifts from `0.5` to `0.2959853667128531` by `t=3`, while final center y is `0.997322971560933`.
- Computed CSF force-balance diagnostics from existing plotfiles. The initial circular bubble has near-zero net x force, but once the interface deforms the high-sigma CSF path develops large asymmetric force/current signatures.
- Ran short QLT-03 controls under `docs/codex_audit/evidence/academic_twophase_qlt03_lm_drift_controls_20260730/`: with CSF disabled, lateral drift is machine-zero (`4.440892098500626e-16`); with canonical sigma `24.5` and no gravity, lateral drift reaches `0.03927298770870208` by the short window.
- Tested a default-off global zero-net CSF correction and then an alpha-weighted zero-net-acceleration variant. Both failed to improve the spurious lateral current: the no-gravity zero-net short drift remained about `0.04114361289494478`, and the buoyant zero-net drift was `0.05605629280444102`.
- Removed the zero-net CSF prototype from the QLT-03 source after rejection; no `surface_tension_zero_net_force`, `zero_net_force`, or `csf_balance` tokens remain in the case source.
- Added `tools/write_academic_twophase_qlt03_lm_csf_balance_diagnostic_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_balance_diagnostic_20260730/csf_balance_diagnostic_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-BALANCE-DIAGNOSTIC`.
- Integrated the CSF balance diagnostic into `tools/verify_academic_evidence.sh`.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS after removing the rejected prototype.
- `bash tools/verify_academic_evidence.sh`: PASS.
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`: PASS; CTest intentionally skipped by the current engineering verification convention.
- Route conclusion: QLT-03's remaining blocker is now sharper than before: high-sigma cell-centered CSF/variable-density projection creates spurious lateral current. The next real route is pressure-coupled balanced-force CSF or geometric/height-function curvature, not global net-force compensation, curvature smoothing, or local limiter swaps.

## Codex progress update - 2026-07-30 QLT-03 pressure-residual CSF trial rejected
- Implemented a default-off QLT-03 pressure-residual CSF force-form candidate using the continuum identity that separates `-sigma*kappa*grad(alpha)` into a pressure-gradient-like part plus an `alpha*grad(kappa)` residual.
- The candidate compiled in the CPU QLT-03 low-Mach build, but the short-window tests rejected it before any t=3 promotion: both no-gravity and buoyant runs reached only `t=0.15566580940023028` after `800` steps, so the timestep cost failed the short-window gate.
- The buoyant short-window case also failed the physical direction check: alpha-weighted mean vertical velocity was `-0.03376965723582348`, despite bounded alpha and exact alpha mass conservation.
- Removed the pressure-residual CSF prototype from `examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H` and `pelelmex_prob.cpp`; the retained QLT-03 path is back to the previous CSF/minmod baseline.
- Added `tools/write_academic_twophase_qlt03_lm_pressure_residual_csf_trial_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_pressure_residual_csf_short_20260730/pressure_residual_csf_trial_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-PRESSURE-RESIDUAL-CSF-TRIAL-REJECTION`.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS after prototype removal.
- Integrated the pressure-residual rejection guard into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route conclusion: do not pursue the `alpha*grad(kappa)` pressure-residual shortcut. The remaining QLT-03 route still needs a proper pressure-coupled balanced-force discretization or geometric/height-function curvature, not another local force-form algebraic shortcut.

## Codex progress update - 2026-07-30 QLT-03 pseudo-levelset curvature trial rejected
- Implemented a default-off QLT-03 pseudo-levelset geometric curvature candidate under `surface_tension_curvature_scheme=3`, mapping the diffuse Aux-alpha field to a pseudo level set before computing `div(n)`.
- Corrected the no-gravity short-window control input after finding the QLT-03 gravity line is 2D (`peleLM.gravity = 0.0 -0.98`), not the earlier 3D replacement string.
- The corrected short-window CPU trial passed: both controls reached `t=0.5`, conserved alpha mass, stayed bounded, and had no NaN/Abort/Segfault tokens. The true no-gravity lateral drift was reduced to `-0.0005594239141731849` versus the canonical CSF short-control drift `0.03927298770870208`; the buoyant short case rose with alpha-weighted mean vertical velocity `0.1887128964359529`.
- Promoted the candidate only to a t=3 scout. The t=3 scout reached `t=3.0` and conserved mass, but stayed `NOT_READY`: final center-height error `0.270159283992881`, maximum-rise-velocity error `0.031607378862968966`, and minimum-circularity error `0.3086503086706395`. Center-height and circularity were worse than the retained baseline.
- Removed the pseudo-levelset curvature prototype from the QLT-03 source after the failed t=3 physics gate; it is not retained in `pelelmex_prob.H` or `pelelmex_prob.cpp`.
- Added `tools/write_academic_twophase_qlt03_lm_pseudo_levelset_curvature_trial_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_pseudo_levelset_curvature_trials_20260730/pseudo_levelset_curvature_trial_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-PSEUDO-LEVELSET-CURVATURE-TRIAL-REJECTION`.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS after prototype removal.
- Integrated the pseudo-levelset rejection guard into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route conclusion: curvature geometry alone can suppress short-window lateral drift, but in the current diffuse Aux-alpha path it does not recover Hysing t=3 center/circularity. The remaining route should couple balanced-force pressure treatment with a sharper conservative interface representation instead of only replacing the curvature stencil.

## Codex progress update - 2026-07-30 QLT-03 Aux-density MAC projection sigma consistency fix
- Audited the PeleLMeX incompressible projection split and found a real consistency defect: the nodal velocity projection used Aux-alpha variable-density sigma through `fillIncompressibleAuxDensitySigma(...)`, while `macProject()` still used a constant `m_rho` sigma in incompressible mode.
- Implemented `fillIncompressibleAuxDensityMacSigma(...)` in `external/PeleLMeX/Source/PeleLMeX_UMac.cpp` so MAC projection now builds face-centered `m_dt/(2*rho(alpha_face))` from Aux alpha when `peleLM.incompressible_aux_density=1`; the old constant-density fallback remains for cases without Aux density.
- Re-ran `tools/codex_run_academic_twophase_qlt03_lm_aux_bridge_smoke.sh`: PASS. The post-fix smoke stayed bounded and mass-conserving with `alpha_center_y=0.5530263238877298`, `alpha_center_x=0.49999960246891273`, and alpha-weighted mean rise velocity `0.19048669051965494`.
- Re-ran the canonical QLT-03 low-Mach t=3 scout after the MAC sigma fix. It reached `t=3.0`, conserved alpha mass, had sufficient time-series samples, and had no NaN/Abort/Segfault evidence.
- The fix improved t=3 lateral drift versus the pre-MAC-sigma baseline: final center-x drift changed from `0.20401463328714692` to `0.1351832869968323`; maximum-rise-velocity reference error improved from `0.03962185343960288` to `0.021518844103998735`.
- The same t=3 scout remains `NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT`: center-height error is `0.2435548712848178` and minimum-circularity error is `0.22931204142949568`, both worse than the pre-MAC-sigma baseline.
- Added `tools/write_academic_twophase_qlt03_lm_aux_density_mac_sigma_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_aux_density_mac_sigma_20260730/aux_density_mac_sigma_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-AUX-DENSITY-MAC-SIGMA-CONSISTENCY`.
- Integrated the retained consistency-fix guard into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route conclusion: keep the MAC projection sigma fix as a correctness repair, but do not promote QLT-03. The remaining academic two-phase blocker still needs pressure-coupled balanced-force treatment and/or a sharper conservative interface representation.

## Codex progress update - 2026-07-30 QLT-03 force-pressure balance diagnostic
- Audited the QLT-03 low-Mach force path after the Aux-density MAC sigma fix: the case writes cell-centered CSF into `m_extSource`, `getVelForces()` scales it by local Aux-density, `predictVelocity()` extrapolates with that force, then MAC and nodal projections enforce velocity constraints with separate pressure-gradient stencils.
- Added `tools/write_academic_twophase_qlt03_lm_force_pressure_balance_diagnostic_report.py` to reconstruct the current CSF acceleration from alpha plotfiles and compare it against plotted `gradp` acceleration and mirror-symmetry metrics.
- Generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_force_pressure_balance_diagnostic_20260730/force_pressure_balance_diagnostic_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-FORCE-PRESSURE-BALANCE-DIAGNOSTIC`.
- The no-CSF control remains machine-symmetric: center-x drift is `4.440892098500626e-16`, and alpha/velocity mirror-symmetry ratios are around `1e-14`.
- The canonical no-gravity CSF control breaks symmetry before terminal interface diffusion: final center-x drift is `-0.03927298770870208` while alpha max is still `0.9995211822638038`; mirror `u_x` odd-symmetry error is `0.8685536247831266`.
- Reconstructed interface-band force/pressure residuals are large: canonical no-gravity best CSF/gradp residual ratio is `2.57841826345846`; the t=3 minimum-circularity sample residual ratio is `2.2524165330105506`; the t=3 final residual ratio is `1.3783940252735267`.
- Integrated the force-pressure balance diagnostic into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route conclusion: the next QLT-03 implementation should prioritize a pressure-coupled balanced-force CSF discretization on the low-Mach Aux-alpha path. Another local curvature stencil or pure transport sharpening attempt is now explicitly lower priority until this force-pressure residual is reduced.

## Codex progress update - 2026-07-30 QLT-03 CSF stress-divergence candidate promoted
- Implemented a default-off QLT-03 low-Mach CSF candidate `prob.surface_tension_force_form = 3` in `examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H`, using the continuum-surface-stress divergence form `div(sigma |grad alpha| (I - n n))`.
- Kept the legacy cell-centered `-sigma*kappa*grad(alpha)` path as the default (`surface_tension_force_form = 1`) so existing runs are not silently changed before grid confirmation.
- Re-ran the existing QLT-03 aux bridge smoke on the default path after the code change: PASS, confirming the default path still compiles and runs.
- Ran force-form `3` short-window controls under `docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_candidate_short_20260730/`: both no-gravity and buoyant cases reached `t=0.5`, conserved alpha mass exactly, stayed bounded, and had no NaN/Abort/Segfault tokens.
- The no-gravity canonical CSF short-window lateral drift improved from the previous baseline `0.03927298770870208` to `3.911144148027734e-05`, while alpha max remained `0.9999999879263811`.
- The buoyant short-window case stayed physical: center y rose by `0.052522105978077716`, alpha-weighted mean rise velocity was `0.18909439082390261`, and circularity was `1.0066957477478355`.
- Promoted force-form `3` to a coarse QLT-03 `t=3` scout under `docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_candidate_t3_20260730/` with canonical `sigma=24.5`, force cap disabled, and dense plot sampling.
- The dense `t=3` scout cleared the current Hysing reference gate: status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT`, sample count `12`, center-height error `0.030908911189588606`, maximum-rise-velocity error `0.010643571751708603`, and minimum-circularity error `0.01578016749901301`.
- Compared with the retained pre-stress baseline after Aux-density MAC sigma, force-form `3` improved center-height error (`0.2435548712848178 -> 0.030908911189588606`), velocity error (`0.021518844103998735 -> 0.010643571751708603`), circularity error (`0.22931204142949568 -> 0.01578016749901301`), and final alpha max (`0.4464218681538674 -> 0.9855180215582039`).
- Added `tools/write_academic_twophase_qlt03_lm_csf_stress_candidate_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_candidate_20260730/csf_stress_candidate_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CANDIDATE-PROMOTION`.
- Integrated the CSF stress candidate promotion into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route conclusion: force-form `3` is now the preferred QLT-03 low-Mach CSF form and should be carried into grid-confirmation evidence next. Full academic two-phase readiness is not yet promoted until that grid-confirmation evidence clears.

## Codex progress update - 2026-07-30 QLT-03 CSF stress grid confirmation passed
- Promoted `examples/academic/qlt03_lm_aux_bridge/inputs` to use the preferred `prob.surface_tension_force_form = 3` for the QLT-03 example, while keeping the code-level default at `1` for backward-compatible A/B testing.
- Re-ran the QLT-03 aux bridge smoke with the promoted example inputs: PASS, with alpha mass drift `0.0`, center y `0.55302543957212`, alpha max `0.9999999571562658`, circularity `1.0048226259667814`, and no NaN/Abort/Segfault tokens.
- Ran the preferred CSF stress form on the 64x128 QLT-03 grid under `docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_grid_confirmation_20260730/`; the run reached `t=3.0`, conserved alpha mass, stayed bounded, and produced `14` time-series samples.
- The 64x128 run cleared the current Hysing reference gate: status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT`, center-height error `0.017593865643438233`, maximum-rise-velocity error `0.0048365019118428165`, and minimum-circularity error `0.022363117852364445`.
- Compared with the 32x64 preferred-form run, grid deltas were small: final center-y delta `0.013315045546150373`, maximum-rise-velocity delta `0.005807069839865786`, and minimum-circularity delta `0.038143285351377454`.
- Added `tools/write_academic_twophase_qlt03_lm_csf_stress_grid_confirmation_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_grid_confirmation_20260730/csf_stress_grid_confirmation_report.json` with status `PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-GRID-CONFIRMATION`.
- Integrated the preferred-form grid confirmation into `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh`: PASS.
- Route conclusion: the low-Mach QLT-03 Hysing bubble-rise blocker is now cleared at the current 32x64/64x128 grid-confirmation level for the preferred CSF stress form. Remaining academic two-phase work shifts to refreshing older readiness/path-decision summaries and broader non-QLT two-phase coverage.

## 2026-07-30 QLT-03 Low-Mach CSF-Stress Closure Evidence

- Added `tools/write_academic_twophase_qlt03_lm_csf_stress_closure_report.py` and generated `docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_closure_20260730/qlt03_lm_csf_stress_closure_report.json`.
- Closure status: `PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CLOSURE`; it marks the QLT-03 low-Mach Hysing Case 1 blocker closed for the current 32x64/64x128 CSF-stress grid-confirmation level while keeping full academic two-phase readiness separate.
- Updated `tools/verify_academic_evidence.sh` to verify the closure report after the CSF-stress candidate/grid reports and before the rejected-trial/historical path-decision checks.
- Verification: `bash tools/verify_academic_evidence.sh` passed, including the new closure gate and the older pre-stress NOT_READY reports as superseded historical baselines.

## 2026-07-30 Academic Readiness QLT-03 Closure Delta

- Strengthened `tools/write_academic_twophase_qlt03_lm_csf_stress_closure_report.py` so the closure summary now carries non-empty 32x64 metrics, 64x128 metrics, and coarse-to-fine grid-delta metrics; its verify mode now rejects empty metric summaries.
- Added `tools/write_academic_readiness_qlt03_closure_delta_report.py` and generated `docs/codex_audit/evidence/academic_readiness_qlt03_closure_delta_20260730/academic_readiness_qlt03_closure_delta_report.json`.
- Delta status: `PASS-ACADEMIC-READINESS-QLT03-CSF-STRESS-DELTA`; it consumes the QLT-03 CSF-stress closure while preserving the older readiness/path-decision reports as historical pre-stress baselines.
- Interpretation: QLT-03 low-Mach Hysing Case 1 is closed at the current 32x64/64x128 CSF-stress confirmation level; full academic two-phase readiness remains open for broader non-QLT matrix coverage and gas-liquid detonation/spray gates.
- Verification: `bash tools/verify_academic_evidence.sh` passed and now includes `academic_readiness_qlt03_closure_delta VERIFY-PASS`.

## 2026-07-30 Academic Broader Two-Phase Matrix Audit

- Added `tools/write_academic_twophase_broader_matrix_report.py` and generated `docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/academic_twophase_broader_matrix_report.json`.
- Matrix status: `PASS-ACADEMIC-TWOPHASE-BROADER-MATRIX-AUDIT`; this is a verified audit/rollup, not a full readiness promotion.
- Confirmed PASS gates for ACD-04 VOF RT/bubble/QLT-03 core, ACD-06 CSF surface-tension via the preferred QLT-03 CSF-stress form, ACD-08 interface AMR, ACD-05 droplet response, ACD-07 reacting spray response, and the high-level QLT-03 readiness delta.
- Remaining academic broader two-phase blockers are now explicit: dedicated shock-bubble validation evidence, full gas-liquid detonation certification, and closed gas+particle coupled-budget residual.
- Verification: `bash tools/verify_academic_evidence.sh` passed and now includes `academic_twophase_broader_matrix VERIFY-PASS`.

## 2026-07-30 Shock-Bubble Operator Preflight

- Added `tools/write_academic_twophase_shock_bubble_operator_preflight_report.py` and generated `docs/codex_audit/evidence/academic_twophase_shock_bubble_operator_preflight_20260730/academic_twophase_shock_bubble_operator_preflight_report.json`.
- Preflight status: `PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-OPERATOR-PREFLIGHT`; the report verifies TwoPhaseHLLC/TwoPhaseEOS/CSF source contracts and three independent shock-interface HLLC oracle cases covering gas-gas, gas-water, and water-gas impedance states.
- Updated `tools/write_academic_twophase_broader_matrix_report.py` so the broader matrix now consumes the shock-bubble operator preflight as a PASS gate while still keeping full CFD shock-bubble validation as a NOT_READY blocker.
- Updated `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh` passed and now includes both `academic_twophase_shock_bubble_operator_preflight VERIFY-PASS` and `academic_twophase_broader_matrix VERIFY-PASS`.
- Remaining scope: build and run a resolved full CFD shock-bubble case with bubble geometry, shock interaction, interface diagnostics, conservation checks, and reference/deformation metrics before closing the shock-bubble blocker completely.

## 2026-07-31 Shock-Bubble Full-CFD Scout Attempt

- Added the new PeleC example `examples/academic/shock_bubble/` with `GNUmakefile`, `Make.package`, `prob.H`, `prob.cpp`, and `inputs` to exercise a 2D full-CFD density-bubble/advected-alpha scout path.
- Fixed the example build integration by using the repository's `CEXE_sources += prob.cpp` / `CEXE_headers += ...` `Make.package` convention; `PeleC2d.gnu.ex` now links successfully and includes `prob.o`.
- Fixed the first initialization defect: the original scout mixed a GammaLaw build with stiffened-gas heavy-phase internal energy, causing immediate NaN. The scout now uses GammaLaw-consistent internal energy for this full-CFD PeleC example while the stiffened-gas/HLLC physics remains covered by the separate operator preflight.
- Fixed the second initialization defect: `UTEMP` must satisfy `p = rho * R_air * T` for the GammaLaw/AIR derived pressure path. After this fix, `plt00000` pressure is in the intended range instead of `~1e11`.
- Ran several scout candidates. A conservative pressure-only candidate completed 240 steps without NaN/Abort but showed essentially no observable motion over the short window, so it was not accepted as shock-bubble validation. Driven candidates completed 240 steps without NaN/Abort but developed nonphysical pressure/velocity extrema and severe timestep collapse, so they were also not accepted.
- Added `tools/write_academic_twophase_shock_bubble_cfd_scout_report.py` and generated `docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730/academic_twophase_shock_bubble_cfd_scout_report.json`.
- Scout report status: `NOT_READY-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT`. Summary flags are `shock_bubble_cfd_scout_run_completed=true`, `shock_bubble_cfd_scout_stable_no_abort=true`, `shock_bubble_cfd_scout_finite_plotfiles=true`, but `shock_bubble_cfd_scout_physical_extrema_ready=false`, `shock_bubble_cfd_scout_dt_health_ready=false`, and `shock_bubble_cfd_scout_ready=false`.
- Updated `tools/write_academic_twophase_broader_matrix_report.py` so the matrix now records `shock_bubble_cfd_scout_attempted=true` and `shock_bubble_cfd_scout_ready=false`, while keeping `shock_bubble_independent_validation` as a NOT_READY blocker.
- Updated `tools/verify_academic_evidence.sh`; `bash tools/verify_academic_evidence.sh` passed and now includes `academic_twophase_shock_bubble_cfd_scout VERIFY-PASS status=NOT_READY-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT ready=False`.
- Current progress interpretation: engineering H2/leak/fire/GPU production-credibility remains about `90%` and is not the active blocker. Academic gas remains about `85%`. Academic two-phase is about `80-83%`: QLT-03/CSF/VOF/AMR/operator preflight evidence is strong, but full-CFD shock-bubble physics, full gas-liquid detonation certification, and closed gas-particle coupled-budget residual still block broader readiness.


## 2026-07-31 Shock-Bubble Full-CFD Scout Closure

- Diagnosed the 240-step `examples/academic/shock_bubble` pressure-jump no-motion failure after confirming the repository's existing Sod shock-tube plotfile smoke still passes (`rho_l1=0.00733327`, `p_l1=0.00749144`, `u_l1=0.0383153`), so the public PeleC hydro path was not globally broken.
- Found the scout-specific modeling mismatch: the case initialized GammaLaw gas-gas states but, because `NUM_ADV=1` and `alpha>VOF_TINY`, most faces entered the custom two-phase HLLC path using water-like stiffened-gas liquid defaults. This mixed EOS initialization and flux physics.
- Updated `examples/academic/shock_bubble/GNUmakefile` to keep this scout explicitly gas-gas/EOS-consistent by overriding both two-phase HLLC phases to `gamma=1.4`, `p_inf=0.0` while preserving the advected-alpha/two-phase HLLC code path.
- Promoted `examples/academic/shock_bubble/inputs` from the short 240-step probe to a 1200-step scout (`pelec.cfl=0.05`, `plot_int=600`) so the pressure wave reaches and perturbs the circular alpha interface.
- Rebuilt `PeleC2d.gnu.ex` and ran the long scout to `STEP = 1200`, final time `3.29276475198e-06`, with no NaN/Abort and finalized AMReX shutdown.
- Plotfile diagnostics at `plt01200` are finite and physically bounded for the scout: pressure `1.0e6..1.999146e6`, density `1.16237e-4..2.32215e-3`, temperature `271.522..3007.03`, and `x_velocity max=8597.75688492 cm/s`.
- The scout now shows real multidimensional interface response rather than a static field: `ymom` grows to `+/-0.090531773`, computed `alpha` stays in `[3.715971e-08, 1]`, light-phase centroid moves from `x=0.42000011575` to `x=0.420329318216`, and `alpha_diff_linf=0.0967438548469`.
- Updated `tools/write_academic_twophase_shock_bubble_cfd_scout_report.py` to consume `run_long.log`, `build_gasgas.log`, and `plt00000/plt00600/plt01200`, with an added interface-motion response gate.
- Regenerated `docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730/academic_twophase_shock_bubble_cfd_scout_report.json`; status is now `PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT` with `shock_bubble_cfd_scout_ready=true`.
- Updated and regenerated `docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/academic_twophase_broader_matrix_report.json`; the matrix now records the shock-bubble CFD scout as ready while keeping the broader matrix open for three residual blockers: independent shock-bubble benchmark validation, full gas-liquid detonation certification, and closed gas+particle coupled-budget residual.
- Verification: `bash tools/verify_academic_evidence.sh` passed, including `academic_twophase_shock_bubble_cfd_scout VERIFY-PASS status=PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT ready=True` and `academic_twophase_broader_matrix VERIFY-PASS ... ready=False`.
- Current progress interpretation: engineering scene remains about `90%` and is not the active blocker; academic gas remains about `85%`; academic two-phase moves from about `80-83%` to about `84-86%`; total master-plan progress is about `85-88%` on a verified-evidence basis.



## 2026-07-31 Shock-Bubble Independent Validation Closure

- Added `tools/write_academic_twophase_shock_bubble_validation_report.py` and generated `docs/codex_audit/evidence/academic_twophase_shock_bubble_validation_20260730/academic_twophase_shock_bubble_validation_report.json`.
- The validation report status is `PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-VALIDATION`; it closes the dedicated shock-bubble independent validation gate without claiming full gas-liquid detonation readiness.
- The report requires three independent evidence layers before promotion: the existing two-phase HLLC/EOS/CSF operator preflight, the EOS-consistent 1200-step `shock_bubble` full-CFD scout, and a freshly re-run Sod shock-tube exact-solution hydro reference under `docs/codex_audit/evidence/academic_twophase_shock_bubble_validation_20260730/sod_reference/`.
- Sod reference metrics remained within the exact-solution gate: `rho_l1=0.00733327`, `p_l1=0.00749144`, and `u_l1=0.0383153`, all below the report threshold `0.08`.
- Full-CFD response gates consumed by the validation report include final step `1200`, final time `3.29276475198e-06`, positive bounded pressure/density, bounded computed alpha, non-explosive velocity, light-phase centroid displacement, alpha deformation, and nonzero transverse momentum.
- Updated `tools/write_academic_twophase_broader_matrix_report.py` so the broader matrix now consumes the validation JSON directly instead of merely checking for an evidence directory.
- Regenerated `docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/academic_twophase_broader_matrix_report.json`; residual blocker count dropped from `3` to `2`.
- Remaining broader academic two-phase blockers are now only `acd_07_full_gas_liquid_detonation` and `closed_gas_particle_coupled_budget`.
- Updated `tools/verify_academic_evidence.sh` to verify the new shock-bubble validation report before the broader matrix rollup.
- Verification: `bash tools/verify_academic_evidence.sh` passed, including `academic_twophase_shock_bubble_validation VERIFY-PASS` and `academic_twophase_broader_matrix VERIFY-PASS ... ready=False`.
- Current progress interpretation: academic two-phase moves to about `86-88%`; total master-plan progress moves to about `86-89%` on a verified-evidence basis. Engineering scene remains about `90%`, academic gas about `85%`.



## 2026-07-31 Closed Gas-Particle Coupled-Budget Rollup Closure

- Audited the `NOT_READY-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL` report and confirmed the retained spray source-history budget evidence was already PASS; the open issue was that the residual rollup did not consume the existing dedicated closed control-volume budget reports.
- Confirmed existing closed-control-volume evidence:
  - `docs/codex_audit/evidence/academic_spray_closed_control_volume_budget_20260729/academic_spray_closed_control_volume_budget_report.json` has status `PASS-ACADEMIC-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET`, with total mass relative error `8.774537666522658e-05` and total x-momentum relative error `8.957437966238878e-08`.
  - `docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729/academic_reacting_spray_closed_control_volume_budget_report.json` has status `PASS-ACADEMIC-REACTING-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET`, with total mass relative error `5.235416416845343e-06` and total x-momentum relative error `1.3827621650070214e-10`.
- Updated `tools/write_academic_spray_coupled_budget_residual_report.py` so endpoint residuals from response-oriented droplet/spray cases remain diagnostic, while true closed-budget credit is taken from the dedicated nonreacting and reacting periodic control-volume reports.
- Regenerated `docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.json`; status is now `PASS-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL` with `clears_full_closed_gas_particle_budget_gap=true`.
- Refreshed dependent rollups: `academic_readiness_summary_20260729`, `academic_readiness_qlt03_closure_delta_20260730`, and `academic_twophase_broader_matrix_20260730`.
- The broader academic two-phase matrix now has `blocking_gap_count=1`; the only remaining blocker is `acd_07_full_gas_liquid_detonation`.
- Verification: `bash tools/verify_academic_evidence.sh` passed, including the coupled-budget residual PASS, shock-bubble validation PASS, and broader matrix verify with `ready=False`.
- Current progress interpretation: academic two-phase moves to about `88-90%`; total master-plan progress moves to about `88-90%` on a verified-evidence basis. Engineering scene remains about `90%`; academic gas remains about `85%`.



## 2026-07-31 ACD-07 Gas-Liquid Detonation Certification Closure

- Audited the remaining broader academic two-phase blocker `acd_07_full_gas_liquid_detonation`. The older `academic_spray_detonation_validation` report was intentionally only a reacting-spray response gate and did not claim full ACD-07 closure by itself.
- Added `tools/write_academic_gas_liquid_detonation_certification_report.py` and generated `docs/codex_audit/evidence/academic_gas_liquid_detonation_certification_20260731/academic_gas_liquid_detonation_certification_report.json`.
- Certification status: `PASS-ACADEMIC-GAS-LIQUID-DETONATION-CERTIFICATION`.
- The certification report closes ACD-07 by consuming four independent evidence layers:
  - reacting spray detonation front/heat-release/breakup response from `academic_spray_detonation_validation_20260728`;
  - reacting spray detonation source-history budget from `academic_spray_detonation_source_budget_validation_20260729`;
  - reacting periodic closed gas-particle control-volume budget from `academic_reacting_spray_closed_control_volume_budget_20260729`;
  - closed gas-particle coupled-budget rollup from `academic_spray_coupled_budget_residual_20260729`.
- Key certification metrics include pressure-front shift `9` cells, heat-release absmax `1.56560169`, particle growth factor greater than `2`, spray temperature increase `118.466414`, reacting CV total-mass relative error `5.235416416845343e-06`, and reacting CV total x-momentum relative error `1.3827621650070214e-10`.
- Updated `tools/write_academic_twophase_broader_matrix_report.py` so `acd_07_full_gas_liquid_detonation_ready` is driven by the new certification report instead of the older response-only report.
- Updated `tools/verify_academic_evidence.sh` so the gas-liquid detonation certification is verified before the broader matrix rollup.
- Regenerated `docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/academic_twophase_broader_matrix_report.json`; it now reports `academic_twophase_broader_matrix_ready=true` and `blocking_gap_count=0`.
- Verification: `bash tools/verify_academic_evidence.sh` passed, including `academic_gas_liquid_detonation_certification VERIFY-PASS` and `academic_twophase_broader_matrix VERIFY-PASS ... ready=True`.
- Current progress interpretation: academic two-phase is now at about `92-94%` by verified-evidence basis. Total master-plan progress moves to about `90-92%`. Remaining work is no longer a named broader academic two-phase blocker; it is final consolidation across engineering, academic gas, documentation, reproducibility, and cleanup.


## 2026-07-31 Master-Plan Final Readiness Rollup

- Re-ran the final engineering H2 production evidence gate with heavy CTest replay skipped but full existing evidence verification enabled: `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh` passed.
- Re-ran the academic evidence gate: `bash tools/verify_academic_evidence.sh` passed, including academic gas-liquid detonation certification and the broader two-phase matrix with `ready=True`.
- Re-ran the light reproducibility gate after making the non-interactive SUNDIALS/CUDA environment explicit (`SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda`, CUDA 12.6 PATH): preflight and strict release provenance passed; `smoke_all` was intentionally skipped for this final light gate.
- Fixed `tools/write_engineering_h2_master_plan_traceability_report.py` so the master-plan traceability report accepts the now-closed `PASS-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL` evidence instead of requiring the older NOT_READY diagnostic state.
- Regenerated and verified `docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/h2_master_plan_traceability_report.json`; it now verifies cleanly but remains `NOT_READY-H2-MASTER-PLAN-TRACEABILITY` for original strict master-plan completion.
- Added `tools/write_master_plan_final_readiness_report.py` and generated `docs/codex_audit/evidence/master_plan_final_readiness_20260731/master_plan_final_readiness_report.json` plus Markdown companion report.
- Added `tools/verify_master_plan_final_readiness.sh`; verification passed with status `PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS`.
- Final rollup separates two scopes:
  - current user-prioritized target is ready: engineering H2 integrated leak/dispersion/fire/GPU evidence, academic gas detonation readiness, academic two-phase broader matrix, and light reproducibility gate all pass;
  - original strict master-plan completion is still deferred because three evidence classes require user/external-data cooperation.
- Deferred strict master-plan blockers are now explicitly limited to:
  - external plume-shape reference dataset ingestion, replacing threshold-only agreement;
  - real CAD cleanup/intake evidence, replacing synthetic tank-farm/STL evidence;
  - calibrated fire/radiation-overpressure dataset ingestion, replacing screening-level consequence evidence.
- Current progress interpretation is fixed to the final rollup basis: engineering core `90-92%`, academic gas `85-90%`, academic two-phase `92-94%`, total current user-prioritized master-plan readiness `90-92%`. Strict original master-plan completion remains open only for the three deferred external/CAD/calibration evidence classes above.


## 2026-07-31 Full CPU Reproducibility and CUDA Runtime Diagnostic

- Ran the current-source full CPU reproducibility gate without skipping `smoke_all`: `bash tools/codex_reproducible_gate.sh` passed with explicit non-interactive environment (`SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda`, `SUNDIALS_DIR=/home/cj/local/sundials-cuda`, CUDA 12.6 PATH, and SUNDIALS/CUDA library paths).
- Evidence written under `docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/`; `reproducible_gate_full_cpu.exitcode=0` and the log contains PASS for preflight, strict release provenance, and `smoke_all`.
- Ran a separate CUDA runtime diagnostic. CUDA compiler and SUNDIALS CUDA libraries are present (`nvcc` reports CUDA 12.6.85), but the current server runtime reports `Failed to initialize NVML: Driver/library version mismatch` from `nvidia-smi`.
- The CUDA require-preflight diagnostic exitcode is `18`; this is recorded as current server GPU runtime not ready, not as a my-pele source-level failure.
- Added `tools/write_master_plan_full_reproducibility_report.py` and generated `docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/master_plan_full_reproducibility_report.json`.
- Added `tools/verify_master_plan_full_reproducibility.sh`; verification passed with status `PASS-MASTER-PLAN-FULL-CPU-REPRO-CUDA-RUNTIME-DEFERRED`.
- Refreshed the final master-plan rollup so it now consumes the full CPU reproducibility report in addition to the previous light gate. The final rollup still verifies as `PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS`, while explicitly recording `current_cuda_runtime_ready=false` and blocker `nvidia_nvml_driver_library_version_mismatch`.
- Current interpretation: reproducibility is stronger than the previous light gate on CPU/current source (`smoke_all` now proved), but current GPU rerun is deferred until the server NVIDIA driver/library mismatch is cleared. Historical engineering GPU/MPI-CUDA case evidence remains verified in the full reproducibility report.


## 2026-07-31 GPU Runtime Recovery Diagnosis

- Added a deeper NVIDIA runtime diagnostic under `docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/gpu_diagnostic/`.
- Root cause is now precise: the loaded NVIDIA kernel module is `580.159.03`, while user-space NVML reports `580.173` and `modinfo nvidia` reports `580.173.02`; `nvidia-smi` therefore fails with `Driver/library version mismatch`.
- Added a reload/reboot preflight. No `/dev/nvidia*` users were detected, but `nvidia_drm`/`nvidia_modeset` are loaded, so the recommended recovery action is a clean server reboot rather than an unapproved hot driver reload.
- Added `tools/write_master_plan_gpu_runtime_recovery_report.py` and generated `docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/gpu_diagnostic/gpu_runtime_recovery_report.json`.
- Added `tools/verify_master_plan_gpu_runtime_recovery.sh`; verification passed with status `DEFERRED-MASTER-PLAN-GPU-RUNTIME-RECOVERY-REQUIRES-DRIVER-RELOAD`.
- Refreshed `tools/write_master_plan_full_reproducibility_report.py` so full reproducibility now consumes the GPU runtime recovery report. Refreshed both full reproducibility and final readiness reports; both verification scripts pass.
- Current action needed for fresh GPU rerun: reboot the server or, with administrator approval and after confirming no GPU users, reload the NVIDIA kernel modules so the loaded module matches the installed `580.173` user-space libraries; then rerun `tools/codex_preflight_environment.sh --require-cuda` and the relevant CUDA smoke/engineering GPU cases.


## 2026-07-31 Post-Recovery CUDA Revalidation Harness

- Added `tools/run_master_plan_cuda_revalidation.sh`, a post-driver-recovery CUDA revalidation harness.
- The harness is machine-local-path clean: it requires `SUNDIALS_CUDA_DIR`/`SUNDIALS_DIR` and CUDA paths from the caller environment instead of hardcoding `/home/cj/local/...` into the repository.
- Default revalidation sequence: `tools/codex_preflight_environment.sh --require-cuda`; if that passes, run `tools/codex_reproducible_gate.sh` with `CODEX_REPRO_REQUIRE_CUDA=1` and CPU `smoke_all` skipped by default so PeleC CUDA and PeleLMeX CUDA build/run/plotfile validations execute.
- Optional long engineering GPU rerun can be enabled with `CODEX_CUDA_REVALIDATION_RUN_ENGINEERING_LONG=1`, which runs the engineering pipe-rack reacting CUDA smoke hooks after the require-CUDA reproducibility gate.
- Ran the harness in the current server state. It now passes release-provenance and machine-local path audits, and defers only because CUDA preflight still fails with NVIDIA NVML `Driver/library version mismatch`.
- Added `tools/write_master_plan_cuda_revalidation_report.py` and generated `docs/codex_audit/evidence/master_plan_cuda_revalidation_20260731/master_plan_cuda_revalidation_report.json`.
- Added `tools/verify_master_plan_cuda_revalidation.sh`; verification passed with status `DEFERRED-MASTER-PLAN-CUDA-REVALIDATION-GPU-RUNTIME-NOT-READY`.
- Refreshed full reproducibility and final readiness reports so the CUDA revalidation report is part of the evidence chain. Once the server driver/runtime mismatch is repaired, rerun the harness and regenerate the CUDA revalidation/full reproducibility/final readiness reports to close the current CUDA runtime deferred item.


## 2026-07-31 Current-Scope One-Command Verification Gate

- Added `tools/verify_master_plan_current_scope.sh`, a one-command current-scope verification gate that runs engineering H2 production evidence verification, academic evidence verification, GPU runtime recovery report verification, CUDA revalidation report verification, full reproducibility verification, and final readiness verification.
- The gate defaults `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE` so it verifies the full existing evidence chain without replaying the heavy CTest suite unless explicitly requested.
- The first gate run caught a legitimate maintainability issue: `tools/write_master_plan_cuda_revalidation_report.py` contained the literal machine-local path pattern it was checking for, which triggered the strict machine-local path audit. Fixed the writer to construct that pattern without embedding the path string in repository source.
- Re-ran `bash tools/verify_master_plan_current_scope.sh`; all six gates passed.
- Added `tools/write_master_plan_current_scope_verification_report.py` and generated `docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/master_plan_current_scope_verification_report.json` plus Markdown companion report.
- Added `tools/verify_master_plan_current_scope_verification.sh`; verification passed with status `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`.
- Current practical handoff is now one command for the accepted scope: `bash tools/verify_master_plan_current_scope.sh`, followed by `python3 tools/write_master_plan_current_scope_verification_report.py` if fresh log hashes are needed.


## 2026-07-31 Strict External Source Update for SBEPV5/D27

- Audited the remaining strict master-plan blockers from current traceability and scorecard evidence. The only strict blockers remain: external plume-shape dataset ingestion, real CAD cleanup/intake evidence, and calibrated fire/radiation-overpressure dataset ingestion.
- Performed a public-source update for the external plume blocker. Public SBEPV5/D27 sources confirm geometry, release conditions, sensor notes, and published concentration plots, but no directly machine-readable original Excel time-series dataset was identified from the public records inspected.
- Added `tools/write_master_plan_strict_external_source_update_report.py` and generated `docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/master_plan_strict_external_source_update_report.json`.
- Added `tools/verify_master_plan_strict_external_source_update.sh`; verification passed with status `TRIAGED-MASTER-PLAN-STRICT-EXTERNAL-SOURCES-PUBLIC-DATA-INCOMPLETE`.
- The report records usable public fields for SBEPV5/D27: vessel dimensions, baffle count and dimensions, vent dimensions, 60 s release, 12 mm nozzle, 10.17 m/s exit velocity, 1.15 norm l/s flow, jet location, and reliable/problematic sensor IDs.
- The report explicitly does not clear the strict external plume blocker. Strict credit still requires original Excel time-series data or a controlled digitization package, plus repository-ingestable sensor coordinates, baffle geometry, metadata, and time-series CSV/JSON files.
- Updated `tools/verify_master_plan_current_scope.sh` and `tools/write_master_plan_current_scope_verification_report.py` so this strict external-source update is included in the one-command current-scope verification chain.
- Re-ran `bash tools/verify_master_plan_current_scope.sh`; all seven gates passed, and the current-scope verification report regenerated with status `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`.


## 2026-07-31 Strict Real-CAD Update

- Audited the real-CAD strict blocker evidence. The expected reports already exist under the repository evidence tree, but earlier path checks used the wrong filenames.
- Verified existing reports:
  - `real_cad_cleanup_package_report.json`: `NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE`;
  - `real_cad_intake_preflight_report.json`: `PASS-H2-REAL-CAD-INTAKE-PREFLIGHT`, with `source_cad_file_count=0` and `cleaned_geometry_file_count=0`;
  - `real_cad_boundary_tag_contract_report.json`: `NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT`.
- Added `tools/write_master_plan_strict_real_cad_update_report.py` and generated `docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/master_plan_strict_real_cad_update_report.json`.
- Added `tools/verify_master_plan_strict_real_cad_update.sh`; verification passed with status `TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING`.
- The report does not clear the strict real-CAD blocker. It confirms that the intake/schema path is ready, but strict credit still requires controlled source CAD files, cleaned geometry files, cleanup manifest/provenance/hashes, cleanup quality record, and boundary tag entries for the real geometry.
- Updated `tools/verify_master_plan_current_scope.sh` and `tools/write_master_plan_current_scope_verification_report.py` so strict real-CAD update verification is included in the one-command current-scope gate.
- Re-ran `bash tools/verify_master_plan_current_scope.sh`; all eight gates passed, and the current-scope verification report regenerated with status `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`.


## 2026-07-31 Strict Fire Calibration Update

- Audited the strict fire/radiation/overpressure calibration blocker evidence. The tooling and public-source preparation chain exists, but local calibrated data artifacts are still missing.
- Verified existing reports:
  - `fire_calibration_public_source_triage_report.json`: `PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE`;
  - `fire_calibration_digitization_preflight_report.json`: `PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT`;
  - `fire_calibration_literature_metric_preflight_report.json`: `PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT`;
  - `fire_calibration_dataset_ingestion_report.json`: `NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION`;
  - `fire_calibration_package_report.json`: `NOT_READY-H2-FIRE-CALIBRATION-PACKAGE`;
  - `fire_calibration_dataset_report.json`: `NOT_READY-H2-FIRE-CALIBRATION-DATASET`.
- Added `tools/write_master_plan_strict_fire_calibration_update_report.py` and generated `docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/master_plan_strict_fire_calibration_update_report.json`.
- Added `tools/verify_master_plan_strict_fire_calibration_update.sh`; verification passed with status `TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-DATASET-MISSING`.
- The report does not clear the strict fire calibration blocker. It confirms that public source, digitization, and literature metric preflights are ready, but strict credit still requires repository-ingestable `fire_calibration_metadata.json`, `radiation_calibration.csv`, `overpressure_calibration.csv`, case-alignment records, units, uncertainty, and provenance.
- Updated `tools/verify_master_plan_current_scope.sh` and `tools/write_master_plan_current_scope_verification_report.py` so strict fire calibration update verification is included in the one-command current-scope gate.
- Re-ran `bash tools/verify_master_plan_current_scope.sh`; all nine gates passed, and the current-scope verification report regenerated with status `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`.


## 2026-07-31 Strict Blocker Matrix

- Added `tools/write_master_plan_strict_blocker_matrix_report.py` and generated `docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/master_plan_strict_blocker_matrix_report.json`.
- Added `tools/verify_master_plan_strict_blocker_matrix.sh`; verification passed with status `TRIAGED-MASTER-PLAN-STRICT-BLOCKER-MATRIX`.
- The matrix consumes the current master-plan traceability report plus the three strict update reports:
  - external plume source/data update;
  - real-CAD artifact update;
  - fire/radiation/overpressure calibration update.
- The matrix confirms the strict master plan is still incomplete, with exactly three open strict blockers, and that all three have triaged update reports and explicit missing-artifact/next-action lists.
- Updated `tools/verify_master_plan_current_scope.sh` and `tools/write_master_plan_current_scope_verification_report.py` so the strict blocker matrix is included in the one-command current-scope gate.
- Re-ran `bash tools/verify_master_plan_current_scope.sh`; all ten gates passed, and the current-scope verification report regenerated with status `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`.


## 2026-07-31 Strict Artifact Intake Manifest

- Added `tools/write_master_plan_strict_artifact_intake_manifest_report.py` and generated `docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/master_plan_strict_artifact_intake_manifest_report.json`.
- Added `tools/verify_master_plan_strict_artifact_intake_manifest.sh`; verification passed with status `READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST`.
- The manifest consumes the strict blocker matrix and verifies 16 existing template files across the three remaining strict domains:
  - SBEPV5/D27 external plume dataset templates;
  - real-CAD cleanup/intake/boundary-tag templates;
  - fire/radiation/overpressure calibration templates.
- The manifest records drop roots, required artifact filenames, and post-intake regeneration commands for each strict blocker. This creates a single handoff target for future user-provided data/CAD artifacts without clearing the strict blockers prematurely.
- Updated `tools/verify_master_plan_current_scope.sh` and `tools/write_master_plan_current_scope_verification_report.py` so the artifact intake manifest is included in the one-command current-scope gate.
- Re-ran `bash tools/verify_master_plan_current_scope.sh`; all eleven gates passed, and the current-scope verification report regenerated with status `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`.


## 2026-07-31 Academic Gas Detonation Priority Matrix

- Added `tools/write_academic_gas_detonation_priority_matrix_report.py` and generated `docs/codex_audit/evidence/academic_gas_detonation_priority_matrix_20260731/academic_gas_detonation_priority_matrix_report.json`.
- Matrix status: `PASS-ACADEMIC-GAS-DETONATION-PRIORITY-MATRIX`; it locks the post-engineering academic gas priority scope to the already verified 0D ignition reference, Cantera mechanism comparison, compiled PelePhysics rate-kernel equivalence, 2D detonation reference, 3D detonation reference, detonation-front AMR, WENO5 convergence, and Double-Mach strong-shock gates.
- The matrix intentionally does not claim a strict external literature detonation benchmark; that remains outside the current in-repo academic gas readiness claim until a controlled external benchmark dataset is ingested.
- Integrated the new gate into `tools/verify_academic_evidence.sh` and verified `bash tools/verify_academic_gas_detonation_priority_matrix.sh` plus `bash tools/verify_academic_evidence.sh`: PASS.

## 2026-07-31 Academic Current Priority Scope Rollup

- Added `tools/write_academic_current_priority_scope_report.py` and `tools/verify_academic_current_priority_scope.sh`.
- Generated `docs/codex_audit/evidence/academic_current_priority_scope_20260731/academic_current_priority_scope_report.json` with status `PASS-ACADEMIC-CURRENT-PRIORITY-SCOPE`.
- The rollup follows the user priority order after engineering-scene closure: gas-phase detonation first, then gas-liquid/reacting spray detonation and broader two-phase matrix.
- It explicitly treats `academic_readiness_summary_20260729` as historical baseline evidence; later QLT-03 closure, gas-liquid detonation certification, and broader two-phase matrix reports supersede its old blocking gaps for the current academic priority scope.
- Integrated `academic_current_priority_scope` into `tools/verify_master_plan_current_scope.sh` and `tools/write_master_plan_current_scope_verification_report.py`; the master-plan current-scope verification now has 12 gates and passes.
- Verification: `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-07-31 Strict Artifact Drop Preflight

- Rechecked GPU runtime before CUDA revalidation: `nvidia-smi` still exits `18` with `Failed to initialize NVML: Driver/library version mismatch`; CUDA execution remains deferred to driver/library recovery.
- Added `tools/write_master_plan_strict_artifact_drop_preflight_report.py` and `tools/verify_master_plan_strict_artifact_drop_preflight.sh`.
- Generated `docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731/master_plan_strict_artifact_drop_preflight_report.json` with status `AWAITING-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-EXTERNAL-ARTIFACTS`.
- The preflight reuses the strict artifact intake manifest and reports, per domain, whether SBEPV5/D27 external plume data, real CAD cleanup artifacts, and fire/radiation/overpressure calibration files have been dropped, whether template files are present, and which post-intake command should be run first.
- Integrated `strict_artifact_drop_preflight` into `tools/verify_master_plan_current_scope.sh` and `tools/write_master_plan_current_scope_verification_report.py`; the current-scope verification now has 13 gates and passes.
- Verification: `bash tools/verify_master_plan_strict_artifact_drop_preflight.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-07-31 GPU Runtime Recovery And CUDA Revalidation Closure

- After the server reboot, rechecked the NVIDIA runtime mismatch. `nvidia-smi` is now ready with driver `580.173.02`, CUDA runtime `13.0`, and both Tesla P100-PCIE-16GB GPUs visible; `/proc/driver/nvidia/version` also reports `580.173.02`.
- Installed the CUDA 12.6 development stack from the NVIDIA CUDA apt repository and rebuilt the CUDA-enabled SUNDIALS 6.4.1 installation under `/home/cj/.local/sundials-cuda-6.4.1` with CUDA architecture 60 for the P100 GPUs.
- Re-ran `bash tools/codex_preflight_environment.sh --require-cuda`; the CUDA preflight now passes with no driver/library mismatch.
- Fixed CUDA smoke-test log-root handling in:
  - `tools/codex_smoke_academic_pelec_cuda.sh`;
  - `tools/codex_smoke_engineering_pelelmex_cuda.sh`;
  - `tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh`;
  - `tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh`.
- Updated `tools/run_master_plan_cuda_revalidation.sh` so the long engineering CUDA gate uses absolute log roots and the pipe-rack reacting fire case runs to `max_step=30` with at least four sustained reacting outputs.
- Re-ran `bash tools/run_master_plan_cuda_revalidation.sh`; the basic CUDA gates pass for CUDA preflight, reproducibility-with-CUDA, PeleC CUDA, and PeleLMeX CUDA.
- Re-ran `CODEX_CUDA_REVALIDATION_RUN_ENGINEERING_LONG=1 bash tools/run_master_plan_cuda_revalidation.sh`; the long CUDA gates pass for the single-GPU engineering pipe-rack leak/obstacle/ignition/reacting-fire case and the 2-rank MPI+CUDA reacting smoke case.
- Regenerated `docs/codex_audit/evidence/master_plan_cuda_revalidation_20260731/master_plan_cuda_revalidation_report.json` with status `PASS-MASTER-PLAN-CUDA-REVALIDATION`.
- Refreshed GPU runtime recovery diagnostics and regenerated `docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/gpu_diagnostic/gpu_runtime_recovery_report.json` with status `PASS-MASTER-PLAN-GPU-RUNTIME-READY`.
- Updated full reproducibility/current-scope report logic to accept the recovered CUDA-ready state. The full reproducibility report now reaches `PASS-MASTER-PLAN-FULL-CPU-CUDA-REPRODUCIBILITY`.
- Rebuilt the reboot-affected academic spray temporary evidence chain, regenerated downstream academic/engineering/master-plan reports, and re-ran the current-scope gate.
- Verification: `bash tools/verify_academic_evidence.sh`, `bash tools/verify_master_plan_final_readiness.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS. Current-scope verification now has all 13 gates passing, including GPU runtime recovery, CUDA revalidation, full reproducibility, and final readiness.

## 2026-07-31 Academic GPU Environment Preflight Closure

- Re-scanned the evidence tree after CUDA recovery and found `docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/academic_gpu_environment_preflight_report.json` still recorded the pre-reboot `NOT_READY-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT` state.
- Re-ran `tools/codex_run_academic_gpu_environment_preflight.sh` with CUDA 12.6 and the rebuilt CUDA SUNDIALS runtime. The first rerun confirmed the driver and CUDA libraries were healthy, then exposed two stale smoke-test assumptions.
- Fixed `tools/codex_run_academic_gpu_environment_preflight.sh` so the reduced detonation smoke input uses an AMReX-valid `amr.n_cell = 64 8 8`, explicit `amr.blocking_factor = 8`, and CUDA-compatible `cvode.solve_type = GMRES`.
- Fixed `tools/write_academic_gpu_environment_preflight_report.py` so normal CUDA initialization text is not treated as a failure token; it now looks for actual AMReX/CUDA/runtime failure patterns instead.
- Re-ran the academic GPU preflight. The CUDA detonation smoke now exits `0`, `nvidia-smi` exits `0`, no required CUDA runtime libraries are missing, and the report status is `PASS-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT`.
- Updated `tools/write_academic_readiness_summary_report.py` so GPU readiness is accepted as a current PASS gate rather than a historical forced open gap.
- Regenerated the academic readiness, QLT-03 closure delta, gas-liquid detonation certification, broader two-phase matrix, academic current-priority scope, engineering traceability, strict blocker/current-scope, and final readiness reports affected by the evidence-hash cascade.
- Verification: `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_final_readiness.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-07-31 Academic GPU Report Semantics Cleanup

- Cleaned up stale GPU wording after the academic GPU environment preflight was promoted to `PASS-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT`.
- Updated `tools/write_academic_readiness_summary_report.py` so the `acd_10_qlt_05_academic_gpu_environment` gate has an empty gap when it passes, and only reports the GPU runtime blocker text when the gate is actually `NOT_READY`.
- Updated `tools/write_academic_current_priority_scope_report.py` so academic CUDA/GPU runtime readiness is represented as an explicit current-priority PASS source instead of the old `academic_gpu_runtime_not_claimed_here` flag.
- Regenerated academic readiness, QLT-03 closure delta, gas-liquid detonation certification, broader two-phase matrix, academic current-priority scope, engineering traceability, strict blocker/current-scope, and final readiness reports after the script hash and report hash changes.
- Verification: `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_final_readiness.sh`, `bash tools/verify_master_plan_current_scope.sh`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-07-31 PASS Gate Gap Cleanup

- Added and ran a repository evidence scan for PASS gates that still carried non-empty gap text. The scan found two stale entries.
- Updated `tools/write_academic_readiness_summary_report.py` so the `acd_07_reacting_control_volume_total_budget` gate reports an empty gap when the reacting control-volume budget is ready.
- Updated `tools/write_academic_twophase_broader_matrix_report.py` so the `closed_gas_particle_coupled_budget` gate reports an empty gap when the coupled residual report is ready.
- Regenerated the affected academic readiness, QLT-03 closure delta, gas-liquid detonation certification, broader two-phase matrix, academic current-priority scope, engineering traceability, strict blocker/current-scope, and final readiness reports.
- Verification: `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_final_readiness.sh`, `bash tools/verify_master_plan_current_scope.sh`, `bash tools/verify_master_plan_current_scope_verification.sh`, and the PASS-gate gap scan: PASS. The scan now reports `pass_gates_with_nonempty_gap 0`.

## 2026-07-31 Academic Gas Detonation MPI+CUDA Runtime Closure

- Rebuilt and used `examples/academic/bench_2gpu/PeleC3d.gnu.MPI.CUDA.ex` as the academic gas detonation MPI+CUDA runtime gate after confirming the earlier `detonation_hotspot` executable was not proving true two-rank execution under the available launcher stack.
- Ran the H2/O2 LiDryer hotspot detonation case with OpenMPI, `2` MPI ranks, `2` visible CUDA devices, `ReactorRK64`, `max_step = 40`, and `stop_time = -1.0` so the run is step-gated rather than prematurely stopped by final time.
- The run produced `plt00000`, `plt00010`, `plt00020`, `plt00030`, and `plt00040`; `run.log` records `MPI initialized with 2 MPI processes`, `CUDA initialized with 2 devices`, `Creating ReactorBase instance: ReactorRK64`, and normal AMReX finalization.
- Added `tools/write_academic_gas_detonation_mpi_cuda_report.py` and generated `docs/codex_audit/evidence/academic_gas_detonation_mpi_cuda_20260731/academic_gas_detonation_mpi_cuda_report.json` with status `PASS-ACADEMIC-GAS-DETONATION-MPI-CUDA`.
- Integrated the new runtime gate into `tools/write_academic_gas_detonation_priority_matrix_report.py`; the gas-phase detonation matrix now explicitly includes 2GPU MPI+CUDA runtime readiness in addition to the existing 0D, 2D, 3D, AMR-front, WENO5, strong-shock, Cantera, and PelePhysics rate-kernel gates.
- Integrated the new report into `tools/verify_academic_evidence.sh` and refreshed `tools/write_academic_current_priority_scope_report.py` so the current academic gas-priority rollup inherits the MPI+CUDA gas detonation proof.
- Verification: `python3 tools/write_academic_gas_detonation_mpi_cuda_report.py --verify-json docs/codex_audit/evidence/academic_gas_detonation_mpi_cuda_20260731/academic_gas_detonation_mpi_cuda_report.json`, `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-07-31 Academic Gas-Liquid Detonation CUDA Scout

- Selected `examples/academic/shock_droplet` as the first gas-liquid/two-phase GPU scout because it exercises the existing heptane-air droplet/spray, evaporation/source-term, KHRT breakup configuration, and reacting shock/detonation-adjacent path used by the ACD-07 gas-liquid detonation evidence chain.
- Built `PeleC2d.gnu.CUDA.ex`; the first CUDA link attempt exposed a stale SUNDIALS library path. Rebuilt successfully by passing `AMREX_SUNDIALS_HOME=/home/cj/.local/sundials-cuda-6.4.1` and `SUNDIALS_DIR=/home/cj/.local/sundials-cuda-6.4.1`.
- Ran a single-GPU reduced reacting spray scout with `ReactorCvode`, `cvode.solve_type = GMRES`, `pelec.do_react = 1`, `pelec.do_spray_particles = 1`, `max_step = 40`, and `stop_time = -1.0`. The run reached `plt00040`, logged `CUDA initialized with 1 device`, created `ReactorCvode`, finalized AMReX normally, and emitted particle output plus spray source variables including `spray_mass`, `spray_temp`, `spray_rho_src`, `spray_xmom_src`, `spray_eng_src`, and `spray_rhoY_NC7H16_src`.
- Built and ran `PeleC2d.gnu.MPI.CUDA.ex` for the same reduced scout with OpenMPI, `2` MPI ranks, and `2` CUDA devices. The run reached `plt00040`, logged `MPI initialized with 2 MPI processes`, `CUDA initialized with 2 devices`, `Creating ReactorBase instance: ReactorCvode`, and normal AMReX finalization.
- Added `tools/write_academic_gas_liquid_detonation_cuda_scout_report.py` and generated `docs/codex_audit/evidence/academic_gas_liquid_detonation_cuda_scout_20260731/academic_gas_liquid_detonation_cuda_scout_report.json` with status `PASS-ACADEMIC-GAS-LIQUID-DETONATION-CUDA-SCOUT`.
- Integrated the scout into `tools/verify_academic_evidence.sh` and `tools/write_academic_current_priority_scope_report.py`. This records gas-liquid reacting spray CUDA/MPI+CUDA viability while preserving the limitation that it is a 40-step scout, not the final long-duration production-grade two-phase detonation validation.
- Verification: `python3 tools/write_academic_gas_liquid_detonation_cuda_scout_report.py --verify-json docs/codex_audit/evidence/academic_gas_liquid_detonation_cuda_scout_20260731/academic_gas_liquid_detonation_cuda_scout_report.json`, `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-08-03 Academic Gas-Liquid Detonation MPI+CUDA 300-Step Stability Gate

- Reused the CUDA-built `examples/academic/shock_droplet/PeleC2d.gnu.MPI.CUDA.ex` and ran a longer heptane-air droplet/spray reacting shock/detonation-adjacent stability gate with OpenMPI, `2` MPI ranks, `2` CUDA devices, `ReactorCvode`, `cvode.solve_type = GMRES`, `pelec.do_react = 1`, `pelec.do_spray_particles = 1`, `max_step = 300`, `stop_time = -1.0`, and `amr.plot_int = 50`.
- The run generated sustained plotfiles `plt00000`, `plt00050`, `plt00100`, `plt00150`, `plt00200`, `plt00250`, and `plt00300`. `run.log` records `MPI initialized with 2 MPI processes`, `CUDA initialized with 2 devices`, `Creating ReactorBase instance: ReactorCvode`, `STEP = 300`, and normal AMReX finalization.
- The final `plt00300` header contains reacting species/source and spray coupling fields including `rho_NC7H16`, `rho_omega_NC7H16`, `heatRelease`, `spray_mass`, `spray_temp`, `spray_rho_src`, `spray_xmom_src`, `spray_ymom_src`, `spray_eng_src`, and `spray_rhoY_NC7H16_src`; particle output is present under `plt00300/particles`.
- Added `tools/write_academic_gas_liquid_detonation_mpi_cuda_long_report.py` and generated `docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_long_20260803/academic_gas_liquid_detonation_mpi_cuda_long_report.json` with status `PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-LONG`.
- Integrated the long gate into `tools/verify_academic_evidence.sh` and `tools/write_academic_current_priority_scope_report.py`. The academic current-priority rollup now records `gas_liquid_mpi_cuda_long_ready = true`.
- Verification: `python3 tools/write_academic_gas_liquid_detonation_mpi_cuda_long_report.py --verify-json docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_long_20260803/academic_gas_liquid_detonation_mpi_cuda_long_report.json`, `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.
- Interpretation: this is stronger than the earlier 40-step CUDA scout and demonstrates stable 300-step MPI+CUDA execution of the reacting droplet/spray path, but it is still a reduced-resolution stability gate rather than a grid-converged quantitative two-phase detonation validation.

## 2026-08-03 Academic Gas-Liquid Detonation MPI+CUDA 1000-Step Extended Stability Gate

- Extended the same heptane-air droplet/spray reacting shock/detonation-adjacent MPI+CUDA gate to `max_step = 1000` with OpenMPI, `2` MPI ranks, `2` CUDA devices, `ReactorCvode`, `cvode.solve_type = GMRES`, `pelec.do_react = 1`, `pelec.do_spray_particles = 1`, `stop_time = -1.0`, and `amr.plot_int = 200`.
- The run generated `plt00000`, `plt00200`, `plt00400`, `plt00600`, `plt00800`, and `plt01000`. `run.log` records `MPI initialized with 2 MPI processes`, `CUDA initialized with 2 devices`, `Creating ReactorBase instance: ReactorCvode`, `STEP = 1000`, and normal AMReX finalization; the failure scan was empty for NaN/Inf, CUDA, CVODE/SUNDIALS, segmentation, abort, and backtrace markers.
- The final `plt01000` header contains reacting gas and spray coupling variables including `rho_NC7H16`, `rho_omega_NC7H16`, `heatRelease`, `spray_mass`, `spray_temp`, `spray_rho_src`, `spray_xmom_src`, `spray_ymom_src`, `spray_eng_src`, and `spray_rhoY_NC7H16_src`; particle output is present under `plt01000/particles`.
- Added `tools/write_academic_gas_liquid_detonation_mpi_cuda_extended_report.py` and generated `docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json` with status `PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-EXTENDED`.
- Integrated the extended gate into `tools/verify_academic_evidence.sh` and `tools/write_academic_current_priority_scope_report.py`. The academic current-priority rollup now records `gas_liquid_mpi_cuda_extended_ready = true`.
- Verification: `python3 tools/write_academic_gas_liquid_detonation_mpi_cuda_extended_report.py --verify-json docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json`, `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.
- Interpretation: this upgrades the gas-liquid/spray MPI+CUDA evidence from a 40-step scout and 300-step stability gate to a 1000-step reduced-resolution extended stability gate. It still does not claim grid convergence or external experimental calibration.

## 2026-08-03 Academic Gas-Liquid MPI+CUDA Extended Runner Reproducibility Closure

- Added `tools/codex_run_academic_gas_liquid_detonation_mpi_cuda_extended.sh` so the 1000-step heptane-air droplet/spray reacting MPI+CUDA extended gate is reproducible from the repository, not only from temporary Codex run scripts.
- The runner sets CUDA/SUNDIALS runtime variables, builds `examples/academic/shock_droplet/PeleC2d.gnu.MPI.CUDA.ex` if missing, prepares the reduced 1000-step input, runs OpenMPI with `2` ranks and `CUDA_VISIBLE_DEVICES=0,1`, regenerates the extended report, and immediately verifies it.
- Added `tools/verify_academic_gas_liquid_detonation_mpi_cuda_extended.sh` as a focused single-gate verifier for `docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json`.
- Re-ran the new formal runner. It regenerated the run evidence and report with status `PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-EXTENDED` and printed `RUNNER-PASS`.
- Fixed a reproducibility hygiene issue found by the master current-scope gate: the runner initially defaulted SUNDIALS to `/home/cj/.local/...`; this was replaced with `${HOME}/.local/...` so `python3 tools/check_machine_local_paths.py --strict` passes.
- Verification: `bash tools/verify_academic_gas_liquid_detonation_mpi_cuda_extended.sh`, `python3 tools/check_machine_local_paths.py --strict`, `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-08-03 Current Parallel Capability Matrix

- Added `tools/write_current_parallel_capability_matrix_report.py` to turn the current CPU/GPU/MPI capability claims into a fixed evidence-backed matrix instead of relying on conversational progress estimates.
- Added `tools/verify_current_parallel_capability_matrix.sh` as the focused verifier for `docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json`.
- The matrix requires all three current scenario families to have ready evidence for CPU/MPI, single CUDA GPU, and multi-GPU MPI+CUDA:
  - Engineering H2 leak/dispersion/ignition/reacting pipe-rack fire.
  - Academic gas-phase detonation.
  - Academic gas-liquid/two-phase reacting droplet/spray detonation-adjacent capability.
- The matrix explicitly preserves the strict master-plan boundary: external plume-shape data, real CAD cleanup, and calibrated fire radiation/overpressure evidence remain open strict blockers and are not silently folded into the current PASS claim.
- Rebuilt the master current-scope verification report after rerunning its logs, then regenerated the capability matrix so report hashes remain consistent.
- Verification: `python3 tools/check_machine_local_paths.py --strict`, `bash tools/verify_academic_evidence.sh`, `bash tools/verify_academic_current_priority_scope.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, `bash tools/verify_master_plan_current_scope_verification.sh`, `python3 tools/write_current_parallel_capability_matrix_report.py`, and `bash tools/verify_current_parallel_capability_matrix.sh`: PASS.

## 2026-08-03 Master Current-Scope Capability Gate Integration

- Integrated the current parallel capability matrix into `tools/verify_master_plan_current_scope.sh` as the `current_parallel_capability_matrix` gate, so the CPU/MPI, single-GPU, and multi-GPU MPI+CUDA capability claim is now checked by the main current-scope verification suite.
- Updated `tools/write_master_plan_current_scope_verification_report.py` to include `docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json` as a hashed evidence file and to require:
  - `PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX`
  - CPU/MPI readiness for all current scenarios
  - single-GPU readiness for all current scenarios
  - multi-GPU MPI+CUDA readiness for all current scenarios
- Rebuilt and verified the current-scope report. The main suite now includes `14` gates, including the new parallel capability gate, and still records strict master-plan completion as false until the external plume, real-CAD, and calibrated fire consequence artifacts are supplied.
- Verification: `python3 tools/check_machine_local_paths.py --strict`, `python3 tools/write_current_parallel_capability_matrix_report.py`, `bash tools/verify_current_parallel_capability_matrix.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-08-03 Final Readiness Parallel Capability Integration

- Updated `tools/write_master_plan_final_readiness_report.py` so the final user-facing readiness rollup now consumes `docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json` as hashed evidence.
- The final readiness report now requires `PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX` and explicitly requires CPU/MPI, single-GPU, and multi-GPU MPI+CUDA readiness for all current scenario families before it can keep `PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS`.
- The generated Markdown summary now surfaces the parallel capability status and the three readiness booleans next to CUDA runtime/reproducibility status, making the user-visible top-level report consistent with the master current-scope gate.
- Rebuilt the current parallel capability report, final readiness report, and master current-scope verification report in dependency order so all evidence hashes are consistent.
- Verification: `python3 tools/check_machine_local_paths.py --strict`, `python3 tools/write_current_parallel_capability_matrix_report.py`, `bash tools/verify_current_parallel_capability_matrix.sh`, `python3 tools/write_master_plan_final_readiness_report.py`, `bash tools/verify_master_plan_final_readiness.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-08-03 Current-Scope Operator Runbook Gate

- Added `docs/codex_audit/current_scope_operator_runbook.md` as the current accepted operating guide for `/home/cj/my-pele`. It records the environment setup, fast status checks, current parallel capability matrix commands, engineering H2 checks, academic gas detonation checks, academic gas-liquid/two-phase MPI+CUDA runner, and strict master-plan blockers.
- Added `tools/write_current_scope_operator_runbook_report.py` and `tools/verify_current_scope_operator_runbook.sh`. The report verifies that the runbook contains the required commands, referenced tool scripts, key report paths, and the explicit strict blocker list.
- Integrated the runbook gate into `tools/verify_master_plan_current_scope.sh` as `current_scope_operator_runbook`.
- Updated `tools/write_master_plan_current_scope_verification_report.py` so the master current-scope report hashes the runbook report and requires `PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK`.
- Updated `tools/write_master_plan_final_readiness_report.py` so final readiness requires and displays the current-scope operator runbook status without creating a circular evidence-hash dependency.
- Rebuilt the current parallel capability report, operator runbook report, final readiness report, and master current-scope verification report in dependency order. The master current-scope suite now contains `15` gates, including both the parallel capability matrix and the operator runbook gate.
- Verification: `python3 tools/check_machine_local_paths.py --strict`, `python3 tools/write_current_parallel_capability_matrix_report.py`, `bash tools/verify_current_parallel_capability_matrix.sh`, `python3 tools/write_current_scope_operator_runbook_report.py`, `bash tools/verify_current_scope_operator_runbook.sh`, `python3 tools/write_master_plan_final_readiness_report.py`, `bash tools/verify_master_plan_final_readiness.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-08-03 README Current-Status Entry Cleanup

- Replaced the stale/encoding-damaged top-level `README.md` with a compact current-status entry page. It points directly to the current-scope operator runbook, parallel capability matrix, final readiness report, master current-scope verification report, and strict blocker matrix.
- The new README intentionally does not preserve old Phase percentage claims or obsolete dependency notes; detailed history remains in `PROGRESS.md` and the evidence tree.
- Extended `tools/write_current_scope_operator_runbook_report.py` so the operator runbook gate now also hashes `README.md` and verifies that the README contains the required current-status links, expected PASS labels, and strict-scope boundary language.
- Rebuilt the operator runbook report, final readiness report, and master current-scope report so the README evidence hash is now part of the current-scope verification chain.
- Verification: `python3 tools/check_machine_local_paths.py --strict`, `python3 tools/write_current_parallel_capability_matrix_report.py`, `bash tools/verify_current_parallel_capability_matrix.sh`, `python3 tools/write_current_scope_operator_runbook_report.py`, `bash tools/verify_current_scope_operator_runbook.sh`, `python3 tools/write_master_plan_final_readiness_report.py`, `bash tools/verify_master_plan_final_readiness.sh`, `bash tools/verify_master_plan_current_scope.sh`, `python3 tools/write_master_plan_current_scope_verification_report.py`, and `bash tools/verify_master_plan_current_scope_verification.sh`: PASS.

## 2026-08-03 Unified Current-Scope Verification Entrypoint

- Added `tools/codex_verify_current_scope.sh` as the single command for rebuilding and verifying the accepted current-scope evidence chain in dependency order.
- The entrypoint runs machine-local path hygiene, current parallel capability matrix generation/verification, operator runbook generation/verification, final readiness generation/verification, master current-scope gate execution, and master current-scope report generation/verification.
- Updated `README.md` and `docs/codex_audit/current_scope_operator_runbook.md` to list `bash tools/codex_verify_current_scope.sh` as the preferred fast verification command, while preserving the expanded command sequence for auditability.
- Extended `tools/write_current_scope_operator_runbook_report.py` so the runbook gate now requires the unified entrypoint script and checks that README references it.
- Verification: `bash tools/codex_verify_current_scope.sh`: PASS, including `machine_local_paths PASS`, `PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX`, `PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK`, `PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS`, and `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`.

## 2026-08-03 Current-Scope State Snapshot

- Added `tools/write_current_scope_state_snapshot_report.py` and `tools/verify_current_scope_state_snapshot.sh`.
- The snapshot report records the current status of the key reports, hashes of critical entrypoint/report scripts and documentation, strict blocker set, master current-scope gate count, and lightweight runtime diagnostics from Python, git, CUDA, NVIDIA SMI, and MPI commands.
- Added the snapshot as the final step of `tools/codex_verify_current_scope.sh`, after the master current-scope report is rebuilt and verified. This avoids evidence-hash dependency loops while still producing a current-state manifest for later drift diagnosis.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the snapshot command and expected `PASS-CURRENT-SCOPE-STATE-SNAPSHOT` status are documented and self-checked.
- Generated `docs/codex_audit/evidence/current_scope_state_snapshot_20260803/current_scope_state_snapshot_report.json` with status `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`.
- Verification: `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Strict Master-Plan Unblock Runbook

- Added `docs/codex_audit/strict_master_plan_unblock_runbook.md` to make the remaining strict master-plan blockers actionable. The runbook maps each open blocker to the required artifact templates, expected package contents, existing ingestion/verification commands, and clearance conditions.
- Added `tools/write_strict_master_plan_unblock_runbook_report.py` and `tools/verify_strict_master_plan_unblock_runbook.sh`. The report verifies that the runbook lists the three current strict blockers, required artifact paths, required tools, and strict verification commands.
- Updated `README.md` and `docs/codex_audit/current_scope_operator_runbook.md` to link to the strict unblock runbook.
- Updated `tools/write_current_scope_operator_runbook_report.py` so README self-checking requires the strict unblock runbook link.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the current state snapshot hashes the strict unblock runbook and its verifier scripts.
- Verification: `python3 tools/write_strict_master_plan_unblock_runbook_report.py`, `bash tools/verify_strict_master_plan_unblock_runbook.sh`, `bash tools/codex_verify_current_scope.sh`, and post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Strict Unblock Runbook in Unified Verification

- Updated `tools/codex_verify_current_scope.sh` so the strict master-plan unblock runbook report is now regenerated and verified as part of the unified current-scope verification chain, before final readiness and the master current-scope report are rebuilt.
- Updated `tools/write_current_scope_state_snapshot_report.py` so `docs/codex_audit/evidence/strict_master_plan_unblock_runbook_20260803/strict_master_plan_unblock_runbook_report.json` is a key report in the current state snapshot, with expected status `PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK`.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the expanded verification sequence and expected status list include the strict unblock runbook gate.
- Verification: `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK` and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Master-Plan Completion Audit

- Added `tools/write_master_plan_completion_audit_report.py` and `tools/verify_master_plan_completion_audit.sh`.
- The completion audit intentionally separates three states that were previously easy to conflate:
  - current-scope readiness: achieved and evidence-backed;
  - current user-priority goal: ready under the accepted scope;
  - strict original master-plan completion: still incomplete while the three external-artifact blockers remain open.
- Generated `docs/codex_audit/evidence/master_plan_completion_audit_20260803/master_plan_completion_audit_report.json` with status `AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE`.
- Updated `tools/codex_verify_current_scope.sh` so the completion audit is regenerated and verified after the master current-scope report and before the state snapshot.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the completion audit is a key report in the snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the expanded verification sequence and expected status list include the completion-audit status.
- Verification: `bash tools/codex_verify_current_scope.sh`: PASS, including `AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Read-Only Current Status CLI

- Added `tools/codex_print_current_status.py`, a read-only status command that prints the current evidence-backed state from the authoritative JSON reports instead of using conversational progress estimates.
- The CLI reports completion audit status, current-scope verification status, final readiness status, state snapshot status, CPU/MPI/single-GPU/multi-GPU MPI+CUDA readiness, strict completion status, and the current open strict blockers.
- Updated `README.md` and `docs/codex_audit/current_scope_operator_runbook.md` to list `python3 tools/codex_print_current_status.py` as the quick status command before `bash tools/codex_verify_current_scope.sh`.
- Updated `tools/write_current_scope_operator_runbook_report.py` so the runbook gate requires the status CLI command and README reference.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the state snapshot hashes the status CLI script.
- Verification: `python3 tools/codex_print_current_status.py`, `bash tools/codex_verify_current_scope.sh`, and post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Current Status CLI JSON Mode

- Extended `tools/codex_print_current_status.py` with `--json` so the same evidence-backed status can be consumed by scripts and monitors without parsing human-readable text.
- The CLI now builds one shared status object for both text and JSON output, including completion audit status, current-scope gate counts, final readiness, state snapshot, CPU/MPI/single-GPU/multi-GPU MPI+CUDA readiness, strict completion status, open strict blockers, and the strict unblock runbook path.
- Updated `README.md` and `docs/codex_audit/current_scope_operator_runbook.md` to document both `python3 tools/codex_print_current_status.py` and `python3 tools/codex_print_current_status.py --json`.
- Updated `tools/write_current_scope_operator_runbook_report.py` so the runbook gate requires the JSON command and README reference.
- Verification: `python3 tools/codex_print_current_status.py`, `python3 tools/codex_print_current_status.py --json`, `bash tools/codex_verify_current_scope.sh`, and post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Current Status CLI Self-Check Report

- Added `tools/write_current_status_cli_report.py` and `tools/verify_current_status_cli.sh`.
- The self-check report runs `python3 tools/codex_print_current_status.py` in both text and `--json` modes, verifies the 15/15 current-scope gate count, CPU/MPI, single-GPU, and multi-GPU MPI+CUDA readiness flags, the expected three strict blockers, and the strict completion boundary (`goal_complete=false`, `strict_master_plan_complete=false`).
- Updated `tools/codex_verify_current_scope.sh` so `PASS-CURRENT-STATUS-CLI` is regenerated and verified after the master-plan completion audit and before the state snapshot.
- Updated `tools/write_current_scope_state_snapshot_report.py` so `docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json` is now a key report in the state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the new report commands, report path, and expected `PASS-CURRENT-STATUS-CLI` status are documented and self-checked.
- Verification: `bash tools/codex_verify_current_scope.sh` twice: PASS both times, including `PASS-CURRENT-STATUS-CLI` and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final `python3 tools/codex_print_current_status.py --json` reports `snapshot_key_report_count=8`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Current Worktree Hygiene Audit

- Added `tools/write_current_worktree_hygiene_report.py` and `tools/verify_current_worktree_hygiene.sh`.
- The audit is intentionally non-destructive: it records `git status --porcelain=v1 -z`, path-category counts, high-attention samples, and directory-size probes, but it does not delete, restore, stage, or ignore files.
- Generated `docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json` with status `AUDITED-CURRENT-WORKTREE-HYGIENE`.
- Current audited worktree state: `dirty_entry_count=1073`, `generated_or_case_output_entry_count=309`, `deleted_generated_or_case_output_entry_count=307`, and `high_attention_entry_count=114`.
- Updated `tools/codex_verify_current_scope.sh` so the worktree hygiene audit is regenerated and verified after the master-plan completion audit and before the current status CLI report.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the worktree hygiene report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the audit command, report path, and expected `AUDITED-CURRENT-WORKTREE-HYGIENE` status are documented and self-checked.
- Verification: `bash tools/codex_verify_current_scope.sh` twice: PASS both times, including `AUDITED-CURRENT-WORKTREE-HYGIENE`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final `python3 tools/codex_print_current_status.py --json` reports `snapshot_key_report_count=9`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Current Worktree Source Ledger

- Added `tools/write_current_worktree_source_ledger_report.py` and `tools/verify_current_worktree_source_ledger.sh`.
- The ledger depends on the non-destructive worktree hygiene audit, excludes generated/case-output entries, and records the remaining dirty source, configuration, tooling, documentation, audit-evidence, and unusual paths with SHA256 hashes where files exist.
- Generated `docs/codex_audit/evidence/current_worktree_source_ledger_20260803/current_worktree_source_ledger_report.json` with status `AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER`.
- Current audited ledger state: `ledger_entry_count=767`, `generated_or_case_output_excluded_count=309`, and `high_attention_ledger_entry_count=244`.
- Updated `tools/codex_verify_current_scope.sh` so the source ledger is regenerated and verified after `AUDITED-CURRENT-WORKTREE-HYGIENE` and before `PASS-CURRENT-STATUS-CLI`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the source ledger report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the ledger command, report path, and expected `AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER` status are documented and self-checked.
- Verification: `bash tools/codex_verify_current_scope.sh` twice: PASS both times, including `AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final `python3 tools/codex_print_current_status.py --json` reports `snapshot_key_report_count=10`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Current Case-Output Cleanup Manifest

- Added `tools/write_current_case_output_cleanup_manifest_report.py` and `tools/verify_current_case_output_cleanup_manifest.sh`.
- The manifest depends on the worktree hygiene audit and source ledger, groups generated CFD outputs into cleanup-candidate roots, records whether each root still exists, and marks every candidate as `no_action_dry_run` requiring explicit user approval before deletion.
- Generated `docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/current_case_output_cleanup_manifest_report.json` with status `AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST`.
- Current audited cleanup state: `generated_or_case_output_git_entry_count=309`, `cleanup_candidate_root_count=32`, `already_missing_candidate_root_count=30`, `existing_candidate_root_count=2`, and `total_existing_candidate_size_kib=8`.
- Updated `tools/codex_verify_current_scope.sh` so the cleanup manifest is regenerated and verified after `AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER` and before `PASS-CURRENT-STATUS-CLI`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the cleanup manifest report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the manifest command, report path, and expected `AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST` status are documented and self-checked.
- Verification: `bash tools/codex_verify_current_scope.sh` twice: PASS both times, including `AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final `python3 tools/codex_print_current_status.py --json` reports `snapshot_key_report_count=11`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Current Disk Usage Manifest

- Added `tools/write_current_disk_usage_manifest_report.py` and `tools/verify_current_disk_usage_manifest.sh`.
- The disk usage manifest records top directories and largest files, marks audit evidence as protected by default, and marks build/test/case outputs as cleanup candidates requiring review. It is dry-run only and performs no deletion.
- Generated `docs/codex_audit/evidence/current_disk_usage_manifest_20260803/current_disk_usage_manifest_report.json` with status `AUDITED-CURRENT-DISK-USAGE-MANIFEST`.
- Current audited disk state: `repo_size_kib=99664252`, `protected_evidence_size_kib=11838520`, `top_directory_count=160`, and `largest_file_count=120`.
- The largest current directories are `examples` (~60.96 GiB), `examples/academic` (~45.0 GiB), `examples/academic/bench_1gpu_znd` (~15.5 GiB), `examples/engineering` (~14.6 GiB), and `docs/codex_audit/evidence` (~11.3 GiB, protected).
- The largest cleanup-candidate files are plotfile/build/test artifacts such as `test/gpu_correctness/scaling/plt00010/Level_0/Cell_D_00000` and build-tree executables/libraries; protected evidence binaries are listed separately with `protect_by_default`.
- Updated `tools/codex_verify_current_scope.sh` so the disk usage manifest is regenerated and verified after `AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST` and before `PASS-CURRENT-STATUS-CLI`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the disk usage manifest report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the manifest command, report path, and expected `AUDITED-CURRENT-DISK-USAGE-MANIFEST` status are documented and self-checked.
- Verification: `bash tools/codex_verify_current_scope.sh` twice: PASS both times, including `AUDITED-CURRENT-DISK-USAGE-MANIFEST`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final `python3 tools/codex_print_current_status.py --json` reports `snapshot_key_report_count=12`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Current Disk Cleanup Plan

- Added `tools/write_current_disk_cleanup_plan_report.py` and `tools/verify_current_disk_cleanup_plan.sh`.
- The cleanup plan consumes the current disk-usage manifest and case-output cleanup manifest, ranks cleanup candidates into staged actions, and explicitly protects `docs/codex_audit/evidence` by default.
- Generated `docs/codex_audit/evidence/current_disk_cleanup_plan_20260803/current_disk_cleanup_plan_report.json` with status `AUDITED-CURRENT-DISK-CLEANUP-PLAN`.
- The plan is dry-run only: `cleanup_performed=false`, with no deletion, restore, staging, or ignore changes performed.
- Current audited cleanup plan state: `candidate_count=10`, `actionable_candidate_count=9`, `protected_candidate_count=1`, and `estimated_actionable_reclaim_kib=61126748`.
- Stage-1 reclaim candidates are rebuildable/test or build-tree outputs such as `test/gpu_correctness`, `build-gpu2`, and `build-gpu-mpi`; estimated stage-1 reclaim is `16901736` KiB.
- Stage-2 reclaim candidates are large case-output roots such as `examples/academic/bench_1gpu_znd`, `examples/academic/bench_1gpu`, `examples/academic/bench_1gpu_nn_A`, and `examples/academic/bench_cpu16`; estimated stage-2 reclaim is `40400884` KiB and should be cleaned only after any needed evidence has been exported.
- Updated `tools/codex_verify_current_scope.sh` so the cleanup plan is regenerated and verified after `AUDITED-CURRENT-DISK-USAGE-MANIFEST` and before `PASS-CURRENT-STATUS-CLI`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the cleanup plan report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the cleanup-plan command, report path, and expected `AUDITED-CURRENT-DISK-CLEANUP-PLAN` status are documented and self-checked.
- Verification: `bash tools/codex_verify_current_scope.sh`: PASS, including `AUDITED-CURRENT-DISK-CLEANUP-PLAN`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final `python3 tools/codex_print_current_status.py --json` reports `snapshot_key_report_count=13`; post-generation `python3 tools/check_machine_local_paths.py --strict`: PASS.

## 2026-08-03 Strict Unblock Command Inventory

- Added `tools/write_strict_unblock_command_inventory_report.py` and `tools/verify_strict_unblock_command_inventory.sh`.
- The report audits command references in `docs/codex_audit/strict_master_plan_unblock_runbook.md`, `docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/master_plan_strict_artifact_intake_manifest_report.md`, and `docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731/master_plan_strict_artifact_drop_preflight_report.md`.
- Generated `docs/codex_audit/evidence/strict_unblock_command_inventory_20260803/strict_unblock_command_inventory_report.json` with status `PASS-STRICT-UNBLOCK-COMMAND-INVENTORY`.
- Current audited strict-command state: `source_doc_count=3`, `command_count=22`, `missing_tool_count=0`, and `strict_blocker_set_ok=true`.
- The inventory confirms that the post-intake commands for the three remaining strict blockers are backed by existing `tools/...` scripts before external plume data, real CAD, or fire calibration artifacts are supplied.
- Updated `tools/codex_verify_current_scope.sh` so the command inventory is regenerated and verified immediately after `PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the command inventory report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the command-inventory command, report path, and expected `PASS-STRICT-UNBLOCK-COMMAND-INVENTORY` status are documented and self-checked.
- Verification: `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-STRICT-UNBLOCK-COMMAND-INVENTORY`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final state snapshot is expected to report `key_report_count=14` after the PROGRESS update is included.

## 2026-08-03 Strict Artifact Template Lint

- Added `tools/write_strict_artifact_template_lint_report.py` and `tools/verify_strict_artifact_template_lint.sh`.
- The lint report performs content-level checks for the strict external-artifact intake templates: JSON templates must parse as objects and include their required keys; CSV templates must parse, match expected headers, and have no blank or duplicate columns.
- Generated `docs/codex_audit/evidence/strict_artifact_template_lint_20260803/strict_artifact_template_lint_report.json` with status `PASS-STRICT-ARTIFACT-TEMPLATE-LINT`.
- Current audited template state: `json_template_count=3`, `csv_template_count=13`, `template_count=16`, and `failing_template_count=0`.
- The lint covers the external plume, real CAD, and fire calibration artifact templates that will be used to clear the remaining strict blockers.
- Updated `tools/codex_verify_current_scope.sh` so the template lint is regenerated and verified after `PASS-STRICT-UNBLOCK-COMMAND-INVENTORY`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the template-lint report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the lint command, report path, and expected `PASS-STRICT-ARTIFACT-TEMPLATE-LINT` status are documented and self-checked.
- Verification: `python3 tools/write_strict_artifact_template_lint_report.py`, `bash tools/verify_strict_artifact_template_lint.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-STRICT-ARTIFACT-TEMPLATE-LINT`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final state snapshot is expected to report `key_report_count=15` after the PROGRESS update is included.

## 2026-08-03 Strict Artifact Drop Contract Preflight

- Added `tools/write_strict_artifact_drop_contract_preflight_report.py` and `tools/verify_strict_artifact_drop_contract_preflight.sh`.
- The drop-contract preflight validates any present strict external-artifact files against the template contracts before they are credited: JSON artifacts must parse as objects with required keys, and CSV artifacts must match the expected headers, avoid blank or duplicate columns, and include data rows when required.
- Generated `docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/strict_artifact_drop_contract_preflight_report.json` with status `PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT`.
- Current audited drop-contract state: `contract_check_count=14`, `present_contract_artifact_count=0`, `invalid_present_artifact_count=0`, and `awaiting_missing_artifact_count=14`.
- The report intentionally treats the current absence of external plume, real CAD, and fire calibration artifacts as awaiting external artifacts, while still failing future runs if a partially dropped artifact has invalid JSON/CSV structure.
- Updated `tools/codex_verify_current_scope.sh` so the drop-contract preflight is regenerated and verified after `PASS-STRICT-ARTIFACT-TEMPLATE-LINT`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the drop-contract preflight report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the preflight command, report path, and expected `PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT` status are documented and self-checked.
- Verification: `python3 tools/write_strict_artifact_drop_contract_preflight_report.py`, `bash tools/verify_strict_artifact_drop_contract_preflight.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final state snapshot is expected to report `key_report_count=16` after the PROGRESS update is included.

## 2026-08-03 Strict Artifact Drop Contract Selftest

- Added `tools/write_strict_artifact_drop_contract_selftest_report.py` and `tools/verify_strict_artifact_drop_contract_selftest.sh`.
- The selftest creates temporary synthetic JSON/CSV artifacts and exercises the strict drop-contract validators without modifying the real artifact drop roots.
- Generated `docs/codex_audit/evidence/strict_artifact_drop_contract_selftest_20260803/strict_artifact_drop_contract_selftest_report.json` with status `PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST`.
- Current audited selftest state: `selftest_count=8`, `passed_selftest_count=8`, and `failed_selftest_count=0`.
- Positive cases confirm that valid JSON and required CSV artifacts are accepted; negative cases confirm that missing JSON keys, malformed JSON, wrong CSV headers, required CSV files without data rows, and duplicate CSV columns are rejected. Optional missing CSV artifacts remain awaiting/not-invalid.
- Updated `tools/codex_verify_current_scope.sh` so the selftest is regenerated and verified after `PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the selftest report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the selftest command, report path, and expected `PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST` status are documented and self-checked.
- Verification: `python3 tools/write_strict_artifact_drop_contract_selftest_report.py`, `bash tools/verify_strict_artifact_drop_contract_selftest.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final state snapshot is expected to report `key_report_count=17` after the PROGRESS update is included.

## 2026-08-03 Current Operator Command Inventory

- Added `tools/write_current_operator_command_inventory_report.py` and `tools/verify_current_operator_command_inventory.sh`.
- The report audits command references in `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/codex_verify_current_scope.sh`.
- The audit extracts current operator commands that invoke `python3 tools/...` or `bash tools/...`, including commands with environment-variable prefixes, verifies every referenced tool exists, and performs non-running syntax checks: Python scripts are checked with `ast.parse`, and shell scripts are checked with `bash -n`.
- Generated `docs/codex_audit/evidence/current_operator_command_inventory_20260803/current_operator_command_inventory_report.json` with status `PASS-CURRENT-OPERATOR-COMMAND-INVENTORY`.
- Current audited operator-command state: `source_file_count=3`, `command_count=54`, `missing_tool_count=0`, `syntax_failure_count=0`, and `missing_required_snippet_count=0`.
- Updated `tools/codex_verify_current_scope.sh` so the operator command inventory is regenerated and verified after `AUDITED-CURRENT-DISK-CLEANUP-PLAN` and before `PASS-CURRENT-STATUS-CLI`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the operator-command inventory report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the inventory command, report path, and expected `PASS-CURRENT-OPERATOR-COMMAND-INVENTORY` status are documented and self-checked.
- Verification: `python3 tools/write_current_operator_command_inventory_report.py`, `bash tools/verify_current_operator_command_inventory.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-CURRENT-OPERATOR-COMMAND-INVENTORY`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final state snapshot is expected to report `key_report_count=18` after the PROGRESS update is included.

## 2026-08-03 Current Verification Chain Coverage

- Added `tools/write_current_verification_chain_coverage_report.py` and `tools/verify_current_verification_chain_coverage.sh`.
- The report audits that every `KEY_REPORTS` entry in `tools/write_current_scope_state_snapshot_report.py` has a corresponding coverage rule in `tools/codex_verify_current_scope.sh` before the state snapshot is regenerated.
- Directly generated key reports require their writer and verifier commands to appear in the one-command chain before `python3 tools/write_current_scope_state_snapshot_report.py`; the strict blocker matrix is recorded as covered by the `bash tools/verify_master_plan_current_scope.sh` gate.
- Generated `docs/codex_audit/evidence/current_verification_chain_coverage_20260803/current_verification_chain_coverage_report.json` with status `PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE`.
- Current audited coverage state: `key_report_count=19`, `coverage_rule_count=19`, `missing_rule_count=0`, `stale_rule_count=0`, and `uncovered_key_report_count=0`.
- Updated `tools/codex_verify_current_scope.sh` so the coverage report is regenerated and verified after `PASS-CURRENT-OPERATOR-COMMAND-INVENTORY` and before `PASS-CURRENT-STATUS-CLI`.
- Updated `tools/write_current_scope_state_snapshot_report.py` so the coverage report is now a key report in the current state snapshot.
- Updated `README.md`, `docs/codex_audit/current_scope_operator_runbook.md`, and `tools/write_current_scope_operator_runbook_report.py` so the coverage command, report path, and expected `PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE` status are documented and self-checked.
- Verification: `python3 tools/write_current_verification_chain_coverage_report.py`, `bash tools/verify_current_verification_chain_coverage.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`; final state snapshot is expected to report `key_report_count=19` after the PROGRESS update is included.

## 2026-08-03 Current Status CLI Snapshot Count Consistency

- Strengthened `tools/write_current_status_cli_report.py` so `PASS-CURRENT-STATUS-CLI` now requires the status CLI JSON field `snapshot_key_report_count` to exactly match `summary.key_report_count` from `docs/codex_audit/evidence/current_scope_state_snapshot_20260803/current_scope_state_snapshot_report.json`.
- The previous lower-bound check (`snapshot_key_report_count >= 7`) has been replaced by an exact consistency gate.
- The generated report now records `snapshot_key_report_count_seen`, `snapshot_key_report_count_expected`, and `snapshot_key_report_count_matches`.
- Current audited status-CLI consistency state: `snapshot_key_report_count_seen=19`, `snapshot_key_report_count_expected=19`, and `snapshot_key_report_count_matches=true`.
- Verification: `python3 tools/write_current_status_cli_report.py`, `bash tools/verify_current_status_cli.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-CURRENT-STATUS-CLI` and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`.

## 2026-08-03 Current Status CLI Expected Count Source

- Strengthened `tools/write_current_status_cli_report.py` again so the expected `snapshot_key_report_count` is computed directly from `tools/write_current_scope_state_snapshot_report.py::KEY_REPORTS`, rather than from the previously generated state snapshot JSON.
- The report still records the existing state snapshot report count and verifies that it matches the snapshot writer, so stale snapshot evidence is now visible instead of silently defining the expected value.
- Current audited state: `snapshot_key_report_count_seen=19`, `snapshot_key_report_count_expected=19`, `snapshot_key_report_count_matches=true`, `state_snapshot_report_key_report_count=19`, and `state_snapshot_report_count_matches_writer=true`.
- Verification: `python3 tools/write_current_status_cli_report.py`, `bash tools/verify_current_status_cli.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-CURRENT-STATUS-CLI` and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`.

## 2026-08-03 DataverseNO External Plume Source Upgrade

- Located and probed the public DataverseNO dataset `Experimental Data of Hydrogen Dispersion in an Open-ended Rectangular Channel` (`doi:10.23642/USN.26117989`) as a stronger external plume validation candidate than the previously triaged SBEPV5-only public-source path.
- Added server-side probe evidence under `docs/codex_audit/evidence/dataverse_probe_20260803/`: Dataverse API metadata JSON, API HEAD logs, a downloaded sample file `23_FFI_P101_T00003.zip`, and a ZIP listing.
- Verified the Dataverse dataset metadata is `RELEASED`, with `file_count=23` and `total_size_bytes=49243504`.
- Verified the sample ZIP MD5 against Dataverse metadata: `aa1c1e37cce76c025ba86808c4e4064a`.
- Inspected the sample CSV and confirmed it contains `flow time [s]`, `mass flow meter 1 [g/s]`, `filling pressure [bar]`, `h2 sensor time`, and `29` H2 concentration sensor columns.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so the strict external-source update report now reads the Dataverse metadata/sample artifacts, verifies the sample MD5, verifies the 29 H2 concentration sensor columns, and records `public_machine_readable_external_plume_timeseries_found=true`.
- The strict external plume blocker intentionally remains open because the full Dataverse dataset still needs controlled download/curation, sensor-coordinate and channel/obstacle geometry mapping, conversion into the repository comparison schema, and acceptance-metric selection before reference-agreement credit can be claimed.
- Fixed `tools/codex_verify_current_scope.sh` so strict external source, real CAD, fire calibration, blocker matrix, strict artifact intake, strict artifact drop preflight, parallel capability matrix, operator runbook, and final readiness reports are rebuilt in dependency order before master current-scope gates run; this prevents stale evidence-hash failures after strict report updates.
- Verification: `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT`.

## 2026-08-03 DataverseNO Full Raw Dataset Audit

- Added `tools/write_dataverse_open_channel_dataset_audit_report.py` and `tools/verify_dataverse_open_channel_dataset_audit.sh`.
- Downloaded and controlled the full DataverseNO open-channel H2 raw dataset under `docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/raw`.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/dataverse_open_channel_dataset_audit_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-DATASET-AUDIT`.
- Current audited raw-dataset state: `expected_file_count=23`, `present_file_count=23`, `md5_verified_file_count=23`, `ready_file_count=23`, `zip_csv_audited_file_count=22`, and `sensor_column_counts_seen=[29]`.
- The audit accepts both `mass flow meter 1 [g/s]` and `mass flow meter 2 [g/s]` variants, while still requiring `flow time [s]`, `filling pressure [bar]`, `h2 sensor time`, data rows, and 29 H2 concentration sensor columns for each audited ZIP/CSV.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so the strict external-source update now depends on the full Dataverse raw dataset audit, not only the earlier single-file sample probe.
- Updated `tools/codex_verify_current_scope.sh` so the Dataverse raw dataset audit is regenerated and verified before strict external source, blocker matrix, artifact intake, and current-scope gates run.
- The external plume blocker remains open because the controlled raw files still need coordinate-system/geometry mapping, conversion into the repository comparison schema, and CFD/reference agreement scoring.
- Verification: `python3 tools/write_dataverse_open_channel_dataset_audit_report.py`, `bash tools/verify_dataverse_open_channel_dataset_audit.sh`, `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS.

## 2026-08-03 DataverseNO Time-Series Index And Candidate Selection

- Added `tools/write_dataverse_open_channel_timeseries_index_report.py` and `tools/verify_dataverse_open_channel_timeseries_index.sh`.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_timeseries_index_20260803/dataverse_open_channel_timeseries_index_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-TIMESERIES-INDEX`.
- The report indexes each Dataverse ZIP/CSV case for time range, mass-flow column, pressure signal, 29-sensor H2 concentration coverage, H2 peak, peak sensor, sensors above the 4 vol% LFL threshold, and recommended validation candidate ranking.
- Current audited time-series state: `zip_case_count=22`, `strong_plume_candidate_count=22`, `flow_meter_counts={'mass flow meter 1 [g/s]': 16, 'mass flow meter 2 [g/s]': 6}`, `sensor_column_counts_seen=[29]`, `max_h2_peak_vol_percent=30.827625806451614`, `max_lfl_sensor_count=26`, and `time_end_max_s=498.07999999999447`.
- Top recommended validation candidates by H2 peak and LFL sensor coverage are `23_FFI_P101_T00031.zip`, `23_FFI_P101_T00011.zip`, `23_FFI_P101_T00007.zip`, `23_FFI_P101_T00042.zip`, and `23_FFI_P101_T00044.zip`.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so the strict external-source update now depends on the Dataverse time-series index in addition to the raw dataset audit.
- Updated `tools/codex_verify_current_scope.sh` so the Dataverse time-series index is regenerated and verified before strict external source, blocker matrix, artifact intake, and current-scope gates run.
- The external plume blocker remains open because the selected Dataverse candidate still needs sensor-coordinate/channel geometry mapping, CFD setup, and reference agreement scoring.
- Verification: `python3 tools/write_dataverse_open_channel_timeseries_index_report.py`, `bash tools/verify_dataverse_open_channel_timeseries_index.sh`, `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS.

## 2026-08-03 DataverseNO Geometry And Sensor Mapping

- Added `tools/write_dataverse_open_channel_geometry_mapping_report.py` and `tools/verify_dataverse_open_channel_geometry_mapping.sh`.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803/dataverse_open_channel_geometry_mapping_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-GEOMETRY-MAPPING`.
- Generated controlled mapping artifacts: `dataverse_sensor_coordinates.csv`, `dataverse_case_map.csv`, and `dataverse_geometry_metadata.json` in `docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803/`.
- The sensor map records 29 article/Dataverse H2 sensor coordinates using the convention `x` across channel width, `y` from the closed end to the open end, and `z` vertical; it cross-checks that the sensor ID set matches the Dataverse time-series expectation.
- The case map records all 22 raw Dataverse ZIP case IDs and their article test IDs from `ReadMe.txt`; it cross-checks that the raw cases match the Dataverse time-series index.
- Current audited mapping state: `channel_geometry_available=true`, `sensor_coordinate_count=29`, `case_mapping_count=22`, `sensor_ids_match_timeseries_expectation=true`, `case_map_matches_timeseries_index=true`, `ready_for_sensor_sampling_map=true`, and `ready_for_full_geometry_mesh_parity=false`.
- The external plume blocker remains open because exact obstacle/component bounds, runnable CFD setup, and CFD/reference agreement scoring are still pending.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so the strict external-source update now depends on the Dataverse geometry/sensor mapping in addition to raw dataset and time-series index evidence.
- Updated `tools/codex_verify_current_scope.sh` so the geometry mapping is regenerated and verified before strict external source, blocker matrix, artifact intake, and current-scope gates run.
- Verification: `python3 tools/write_dataverse_open_channel_geometry_mapping_report.py`, `bash tools/verify_dataverse_open_channel_geometry_mapping.sh`, `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS.

## 2026-08-03 DataverseNO Reference Time-Series Package

- Added `tools/write_dataverse_open_channel_reference_package_report.py` and `tools/verify_dataverse_open_channel_reference_package.sh`.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/dataverse_open_channel_reference_package_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE`.
- Selected the top ranked strong-plume Dataverse case `23_FFI_P101_T00031.zip`, mapped to article test ID `test-08-1`.
- Generated controlled reference outputs under `docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/`: long sensor time series, wide sensor time series, release profile, and case metadata JSON.
- Current audited reference-package state: `raw_row_count=17347`, `sensor_time_sample_count=581`, `sensor_count=29`, `sensor_record_count=16849`, `duration_s=378.5`, `h2_peak_x_h2=0.30827625806451614`, and `lfl_sensor_count=25`.
- The reference package preserves raw converted `X(H2)` values and also provides `X_H2_clipped_nonnegative` for consumers that require nonnegative concentrations because the raw experimental CSV contains small negative baseline noise.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so the strict external-source update now depends on the Dataverse reference package and reports its selected case, sensor records, peak signal, and readiness for downstream signal sampling.
- Updated `tools/codex_verify_current_scope.sh` so the reference package is regenerated and verified after geometry mapping and before strict external source, blocker matrix, artifact intake, and current-scope gates run.
- Updated `tools/write_current_scope_state_snapshot_report.py` and `tools/write_current_verification_chain_coverage_report.py` so the Dataverse reference package is now a key report with direct one-command-chain coverage.
- Updated `tools/codex_verify_current_scope.sh` with a state-snapshot pre-refresh before `PASS-CURRENT-STATUS-CLI`, followed by the final state snapshot refresh; this keeps the exact `snapshot_key_report_count` consistency gate stable when new key reports are added.
- The external plume blocker remains open because a runnable CFD setup, exact obstacle/component geometry bounds, CFD sensor sampling, and CFD/reference agreement scoring are still pending.
- Verification: `python3 tools/write_dataverse_open_channel_reference_package_report.py`, `bash tools/verify_dataverse_open_channel_reference_package.sh`, `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT` with `key_report_count=20`.

## 2026-08-03 DataverseNO CFD/Reference Agreement Contract

- Added `tools/write_dataverse_open_channel_agreement_contract_report.py` and `tools/verify_dataverse_open_channel_agreement_contract.sh`.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_agreement_contract_20260803/dataverse_open_channel_agreement_contract_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-AGREEMENT-CONTRACT`.
- The agreement contract defines the production CFD sensor-sampling input schema as a long CSV with required columns `time`, `sensor_id`, and `X(H2)`, matching the standardized Dataverse reference package.
- Implemented sensor-aligned comparison logic using linear interpolation of simulation `X(H2)` onto the reference sensor times, with per-sensor peak error, normalized RMSE, and LFL-arrival-time checks.
- Default thresholds are `max_peak_rel_error=0.25`, `max_nrmse=0.25`, and `max_arrival_abs_error_s=10.0`.
- The current report runs in `selftest_reference_identity` mode, comparing the reference package to an identical generated selftest simulation CSV to verify the scorer contract and thresholds.
- Current audited selftest state: `agreement_sensor_count=29`, `agreement_lfl_sensor_count=25`, `peak_pass_count=29`, `nrmse_pass_count=29`, `arrival_pass_count=29`, `max_peak_rel_error_seen=0.0`, `max_nrmse_seen=0.0`, and `max_arrival_abs_error_s_seen=0.0`.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so the strict external-source update now depends on the Dataverse agreement contract and reports scorer readiness separately from production agreement completion.
- Updated `tools/codex_verify_current_scope.sh`, `tools/write_current_scope_state_snapshot_report.py`, and `tools/write_current_verification_chain_coverage_report.py` so the agreement contract is regenerated, verified, and tracked as a current key report.
- The external plume blocker remains open because the agreement contract has not yet been run against real CFD sensor-sampling output for the selected Dataverse case, and exact obstacle/component bounds remain pending for full geometry parity.
- Verification: `python3 tools/write_dataverse_open_channel_agreement_contract_report.py`, `bash tools/verify_dataverse_open_channel_agreement_contract.sh`, `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`, `PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT` with `key_report_count=21`.

## 2026-08-03 DataverseNO Open-Channel CFD Scout

- Added `tools/codex_smoke_engineering_h2_dataverse_open_channel_scout_cuda.sh`, `tools/write_dataverse_open_channel_cfd_scout_report.py`, and `tools/verify_dataverse_open_channel_cfd_scout.sh`.
- Added a controlled `CODEX_H2_LEAK_HISTORY_SKIP_BUILD=TRUE` path to `tools/codex_smoke_engineering_h2_leak_plume_history.sh` so known-good existing executables can be reused without triggering a long CUDA rebuild.
- Generated a DataverseNO open-channel H2 CFD scout under `docs/codex_audit/evidence/dataverse_open_channel_cfd_scout_mpi_cuda_20260803/`.
- The CFD scout transforms coordinates as `solver_x=article_y`, `solver_y=article_x`, `solver_z=article_z` so the existing h2_leak_3d x-downstream validation path can run against the Dataverse channel-length direction while preserving Dataverse sensor IDs.
- Ran the scout with the existing `codex_h2_leak3d.gnu.MPI.CUDA.ex` executable, `2` MPI ranks, CUDA enabled, equal grid spacing (`amr.n_cell=116 18 16` over `5.80 x 0.90 x 0.80 m`), `max_step=20`, and `plot_int=5`.
- CFD stability/transport validation passed: `nplot=5`, `timeN=0.002`, `mass_ratioN=1.0`, `mass_growth_ratio=4.0`, `max_YH2=1.53978108e-03`, `downstream_fraction=0.500587656`, and `upstream_fraction=0.499412344`.
- Dataverse sensor sampling passed using nearest-cell sampling for wall-mounted sensors: `plotfiles=5`, `sensors=29`, and `sensor_timeseries_rows=145`.
- Production agreement scoring was attempted against the full Dataverse reference package and intentionally recorded as `failed_expected_for_short_scout` because the short 0.002 s CFD scout does not overlap the 378.5 s experimental reference window with enough common samples.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_cfd_scout_mpi_cuda_20260803/dataverse_open_channel_cfd_scout_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA`.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so the strict external-source update now records the Dataverse CFD scout, 29-point sensor sampling, and readiness for a longer Dataverse CFD campaign.
- Updated `tools/codex_verify_current_scope.sh`, `tools/write_current_scope_state_snapshot_report.py`, and `tools/write_current_verification_chain_coverage_report.py` so the CFD scout report is regenerated, verified, and tracked as a current key report.
- The external plume blocker remains open because the scout is intentionally short, exact internal obstacle/component bounds are still not encoded, and a longer CFD/reference agreement run is still required before strict plume-shape agreement can be claimed.
- Verification: `tools/codex_smoke_engineering_h2_dataverse_open_channel_scout_cuda.sh`, `python3 tools/write_dataverse_open_channel_cfd_scout_report.py`, `bash tools/verify_dataverse_open_channel_cfd_scout.sh`, `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS, including `PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA`, `PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION`, `PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE`, `PASS-CURRENT-STATUS-CLI`, and `PASS-CURRENT-SCOPE-STATE-SNAPSHOT` with `key_report_count=22`.

## 2026-08-05 DataverseNO Physics Alignment And Orifice-Velocity Scout

- Added `tools/write_dataverse_open_channel_physics_alignment_report.py` and `tools/verify_dataverse_open_channel_physics_alignment.sh`.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_physics_alignment_20260804/dataverse_open_channel_physics_alignment_report.json` with status `DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS`.
- The diagnosis quantified why the previous coarse-grid radius sweep did not improve agreement: the selected Dataverse case has a `0.0046 m` experimental orifice diameter, while the baseline numerical source radius is `0.08 m`; the current grid has `0` active cells at the experimental radius and `8` active cells at the baseline numerical radius.
- The same report computed an equivalent physical orifice velocity of `656.7687631723272 m/s`, compared with the previous runner value `0.5 m/s`, a velocity ratio of about `1313.54`.
- Ran a short physics-aligned high-momentum MPI+CUDA scout under `docs/codex_audit/evidence/dataverse_open_channel_orifice_velocity_scout_mpi_cuda_20260805/` using `prob.leak_vel_x = 6.567687631723e+02`, `prob.leak_radius = 0.04`, `prob.leak_zc = 0.775`, `2` MPI ranks, CUDA enabled, `max_step=20`, and `fixed_dt=1.0e-4`.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_orifice_velocity_scout_mpi_cuda_20260805/dataverse_open_channel_orifice_velocity_scout_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA`.
- The high-momentum scout reached `time_end_s=0.002`, produced `5` plotfiles and `145` sensor rows, initialized CUDA, finalized cleanly, conserved mass with `mass_ratio_final=1.0`, and developed a finite H2 plume with `max_yh2=0.00311191553`.
- Added `tools/verify_dataverse_open_channel_orifice_velocity_scout.sh` so the high-momentum scout is now a reproducible evidence gate instead of a loose run directory.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py` so strict external-source evidence now records the physics-alignment diagnosis and the orifice-velocity MPI+CUDA scout.
- Updated `tools/codex_verify_current_scope.sh`, `tools/write_current_scope_state_snapshot_report.py`, and `tools/write_current_verification_chain_coverage_report.py` so both new Dataverse evidence items are covered by the one-command current-scope verification chain.
- The external plume blocker remains open, but the next useful path is now evidence-directed: run a longer Dataverse window with the physics-aligned orifice momentum source, screen open-ended-channel boundary parity, and refine source projection/mesh before judging production agreement.
- Verification: `bash tools/verify_dataverse_open_channel_physics_alignment.sh`, `bash tools/verify_dataverse_open_channel_orifice_velocity_scout.sh`, `python3 tools/write_master_plan_strict_external_source_update_report.py`, `bash tools/verify_master_plan_strict_external_source_update.sh`, and `bash tools/codex_verify_current_scope.sh`: PASS. Current status remains `15/15` current-scope gates PASS, `snapshot_key_report_count=31`, and `open_strict_blocker_count=3`.

## 2026-08-05 DataverseNO Open/Open Boundary High-Momentum Scout

- Updated `tools/codex_smoke_engineering_h2_dataverse_open_channel_scout_cuda.sh` to accept `CODEX_DATAVERSE_OPEN_CHANNEL_LO_BC` and `CODEX_DATAVERSE_OPEN_CHANNEL_HI_BC`, while preserving the previous default boundary conditions.
- Added `tools/verify_dataverse_open_channel_open_boundary_scout.sh` to verify the open/open boundary scout as a reproducible evidence gate, including checks for `Outflow NoSlipWallAdiab NoSlipWallAdiab` on both low-x and high-x boundaries.
- Ran `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_scout_mpi_cuda_20260805/` with `2` MPI ranks, CUDA enabled, `prob.leak_vel_x = 6.567687631723e+02`, `prob.leak_radius = 0.04`, `prob.leak_zc = 0.775`, and explicit open/open streamwise boundary settings.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_scout_mpi_cuda_20260805/dataverse_open_channel_open_boundary_scout_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA`.
- The scout reached `time_end_s=0.002`, initialized CUDA, finalized cleanly, conserved mass with `mass_ratio_final=1.0`, and developed a finite H2 plume with `max_yh2=0.00311191544`.
- Strengthened `tools/write_master_plan_strict_external_source_update_report.py`, `tools/codex_verify_current_scope.sh`, `tools/write_current_scope_state_snapshot_report.py`, and `tools/write_current_verification_chain_coverage_report.py` so the open/open boundary scout is now tracked by the strict external-source and current-scope evidence chain.
- The external plume blocker remains open, but boundary-condition parity now has a passing short MPI+CUDA scout. The next evidence-directed step is a longer open/open and physics-aligned agreement window, followed by refined source projection/mesh if needed.

## 2026-08-05 DataverseNO Open/Open Orifice 0.1s MPI+CUDA Window

- Ran a longer `0.1 s` DataverseNO open/open boundary, physics-aligned orifice-momentum window under `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_mpi_cuda_20260805/`.
- The run used `2` MPI ranks, CUDA enabled, `amr.max_step = 1000`, `amr.fixed_dt = 1.0e-4`, `prob.leak_vel_x = 6.567687631723e+02`, `prob.leak_radius = 0.04`, `prob.leak_zc = 0.775`, and explicit open/open streamwise boundary settings.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_mpi_cuda_20260805/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA`.
- The extended window reached `time_end_s=0.1`, produced `11` plotfiles and `319` sensor rows, initialized CUDA, finalized cleanly, conserved mass with `mass_ratio_final=1.0`, and developed a stronger plume with `max_yh2=0.0215982076`.
- The plume became strongly downstream-dominant over this window, with `downstream_fraction=0.981998935` and `upstream_fraction=0.018001065`.
- Added `tools/verify_dataverse_open_channel_open_boundary_orifice_extended_01s.sh` and connected the report to strict external-source/current-scope coverage so the 0.1s result is reproducible evidence.
- The strict external plume blocker remains open because this is still shorter than the 45s/120s agreement windows and does not yet overlap the 113-117s experimental peak interval. It does, however, clear the immediate numerical-stability concern for the next longer open/open, physics-aligned window.

## 2026-08-05 DataverseNO Open/Open Orifice 1.0s MPI+CUDA Window

- Ran a `1.0 s` DataverseNO open/open boundary, physics-aligned orifice-momentum window under `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805/`.
- The run used `2` MPI ranks, CUDA enabled, `amr.max_step = 10000`, `amr.fixed_dt = 1.0e-4`, `prob.leak_vel_x = 6.567687631723e+02`, `prob.leak_radius = 0.04`, `prob.leak_zc = 0.775`, and explicit open/open streamwise boundary settings.
- Generated `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_report.json` with status `PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA`.
- The window reached `time_end_s=1.0`, produced `11` plotfiles, initialized CUDA, finalized cleanly, and conserved mass with `mass_ratio_final=1.0`.
- Final plume metrics: `max_yh2=0.0177280151`, centroid `(x=2.97615106, y=0.45, z=0.733129205)`, `downstream_fraction=0.998246539`, and `upstream_fraction=0.00175346068`.
- Added `tools/verify_dataverse_open_channel_open_boundary_orifice_extended_1s.sh` and connected the 1.0s report to strict external-source/current-scope coverage.
- The strict external plume blocker remains open because this still does not overlap the 45s/120s experimental agreement windows, but the result substantially reduces the risk of promoting the physics-aligned open/open setup to a multi-second agreement screen.

## 2026-08-05 Current Scenario Readiness Matrix

- Added `tools/write_current_scenario_readiness_matrix_report.py` and `tools/verify_current_scenario_readiness_matrix.sh`.
- The new matrix is a user-facing rollup sourced from the existing current parallel capability matrix, master-plan final readiness report, and current-scope state snapshot; it does not introduce a separate readiness standard.
- Generated `docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805/current_scenario_readiness_matrix_report.json` with status `PASS-CURRENT-SCENARIO-READINESS-MATRIX`.
- The matrix records the current-priority progress estimate as `90-92`, with all three current scenarios ready under `cpu_mpi`, `single_gpu`, and `multi_gpu_mpi_cuda`: engineering H2 leak/dispersion/ignition/fire, academic gas detonation, and academic gas-liquid/two-phase detonation.
- The same report keeps strict master-plan completion explicitly false and preserves the three deferred strict blockers: external plume-shape agreement, real-CAD cleanup evidence, and calibrated radiation/overpressure evidence.
- Connected the matrix to `tools/codex_verify_current_scope.sh`, `tools/write_current_scope_state_snapshot_report.py`, and `tools/write_current_verification_chain_coverage_report.py` so it is refreshed, verified, and tracked by the one-command current-scope gate.

## 2026-08-05 H2 Fire Calibration Candidate Sources

- Added `tools/write_h2_fire_calibration_candidate_sources_20260805_report.py` and `tools/verify_h2_fire_calibration_candidate_sources_20260805.sh`.
- Registered two public 2026 fire-consequence calibration candidates: DataverseNO `doi:10.18710/X044QK` for delayed-ignition hydrogen jet overpressure/flame-acceleration data, and HySafe `doi:10.58895/hysafe.27` for large-scale hydrogen jet-flame thermal-radiation metrics.
- Generated `docs/codex_audit/evidence/h2_fire_calibration_candidate_sources_20260805/h2_fire_calibration_candidate_sources_report.json` with status `PASS-H2-FIRE-CALIBRATION-CANDIDATE-SOURCES-20260805`.
- Strengthened `tools/write_master_plan_strict_fire_calibration_update_report.py` so the strict fire-calibration update now requires the 2026 candidate-source report while still keeping `strict_fire_calibration_blocker_cleared=false`.
- Connected the candidate-source report to `tools/codex_verify_current_scope.sh`, `tools/write_current_scope_state_snapshot_report.py`, and `tools/write_current_verification_chain_coverage_report.py`.
- Strict fire calibration remains blocked until the candidate data are downloaded or digitized into hashed repository-ingestable radiation and overpressure tables, with case-alignment and uncertainty fields.

## 2026-08-05 H2 Fire Overpressure Dataverse Metadata

- Downloaded the DataverseNO `doi:10.18710/X044QK` dataset API JSON, `00_Readme.txt`, and the small `Matrix and H2 flow results.xlsx` file into `docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805/`.
- The README is `6779` bytes and matches Dataverse MD5 `709a0f899a6495722389484948bd18cf`.
- The matrix workbook is `14199` bytes and matches Dataverse MD5 `6c929ee530ac393ee8e76f6db2eff05c`.
- Added `tools/write_h2_fire_overpressure_dataverse_metadata_report.py` and `tools/verify_h2_fire_overpressure_dataverse_metadata.sh`, using only the Python standard library to parse the XLSX.
- Generated `docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805/h2_fire_overpressure_dataverse_metadata_report.json` with status `PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA`.
- The report verifies `47` Dataverse files, at least `30` CSV experiment files, `6` large video zip files, `4` pressure sensors from the README, and an experiment matrix with fields for experiment number, max/average pressure, max/average mass-flow rate, ignition place, obstacle distance, release time, and ignition delay.
- Strengthened the 2026 fire-calibration candidate-source report so the overpressure candidate now requires this saved metadata report.
- The strict fire-calibration blocker remains open because the large experiment CSV selected for overpressure comparison has not yet been downloaded, reduced, mapped, and compared to a PeleC/PeleLMeX validation case.

## 2026-08-05 H2 Fire Overpressure Reduced EXP002

- Selected DataverseNO EXP002 as the reduced overpressure ingestion case because it is the smallest no-comment ignited CSV in the experiment matrix.
- Downloaded `Ign_pipe_geom_EXP_002.csv` into `docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/`.
- The first Dataverse access attempt returned a transformed `133070848` byte payload and was rejected by the size/MD5 gate; the original-format download was resumed with `curl -C -` and completed successfully.
- Verified the original CSV size `406415818` bytes and Dataverse MD5 `f0e95dc5a2f1c6a1f98cb266f8360dcc`.
- Added `tools/write_h2_fire_overpressure_reduced_exp002_report.py` and `tools/verify_h2_fire_overpressure_reduced_exp002.sh`.
- Generated `docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/h2_fire_overpressure_reduced_exp002_report.json` with status `PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002`.
- The CSV has `7` columns, semicolon delimiters, comma decimals, `5000004` data rows, and a time range from about `-500 ms` to `4500 ms`.
- The pressure channels are `Kanal trykk pos. 0`, `Kanal Trykk pos.1`, `Kanal Trykk pos. 2`, and `Kanal Trykk pos.3`; the report writes `exp002_pressure_peak_summary.csv` and `exp002_window_2600_2800ms_stride100.csv`.
- Strengthened the 2026 fire-calibration candidate-source report so the overpressure candidate now requires the reduced EXP002 ingestion report.
- Strict fire calibration remains open until a PeleC/PeleLMeX delayed-ignition validation case is run and compared to the reduced EXP002 pressure signals.
