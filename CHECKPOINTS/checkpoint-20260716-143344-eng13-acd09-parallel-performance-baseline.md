# Checkpoint - ENG-13 ACD-09 parallel performance baseline

> Date: 2026-07-16T14:33:44+08:00
> Agent: Codex
> Related items: ENG-13, ACD-09

## Summary

- Added a targeted parallel performance/stability baseline that runs engineering PeleLMeX and academic PeleC serial, MPI, OpenMP, and hybrid smokes.
- Added a summary validator that requires all eight cases, positive wall-clock timings, AMReX finalization, per-mode validation logs, and explicit preservation of MPI thread-support warnings.
- Recorded current tiny-case wall times and kept the result as baseline evidence rather than a speedup/scaling claim.

## Changed Files / Modules

- tools/codex_smoke_parallel_perf_baseline.sh
- tools/validate_parallel_perf_summary.py
- docs/codex_audit/MASTER_PLAN_TRACEABILITY.md
- docs/codex_audit/SMOKE_MATRIX.md

## Verification

- python3 -m py_compile tools/validate_parallel_perf_summary.py
- bash -n tools/codex_smoke_parallel_perf_baseline.sh
- CODEX_PARALLEL_PERF_LOG_DIR=/tmp/codex_parallel_perf_baseline_20260716 JOBS=2 RUN_TIMEOUT=240 tools/codex_smoke_parallel_perf_baseline.sh

## Evidence Paths

- /tmp/codex_parallel_perf_baseline_20260716/summary.tsv
- /tmp/codex_parallel_perf_baseline_20260716/validation.log
- /tmp/codex_parallel_perf_baseline_20260716/engineering_mpi/validation.log
- /tmp/codex_parallel_perf_baseline_20260716/engineering_hybrid/validation.log
- /tmp/codex_parallel_perf_baseline_20260716/academic_mpi/validation.log
- /tmp/codex_parallel_perf_baseline_20260716/academic_hybrid/validation.log

## Known Limitations

- Tiny-case elapsed times are overhead-dominated and do not prove useful speedup or production scaling.
- MPI and hybrid modes still report mpi_thread_support_level_0; a policy/acceptance decision, scheduler/affinity guidance, production-size scaling curves, and longer stability runs remain open.

## Git Status Snapshot

```text
 M AGENTS.md
 M PROGRESS.md
 M examples/academic/detonation_2D/GNUmakefile
 M examples/academic/vof_advection_1D/prob.H
 M examples/engineering/bfs_kepsilon/pelelmex_prob.H
 M examples/engineering/bfs_kepsilon/pelelmex_prob.cpp
 M examples/engineering/c3h8_gpu_test/pelelmex_prob.H
 M examples/engineering/h2_ignition/GNUmakefile
 M examples/engineering/h2_ignition/pelelmex_prob.cpp
 M examples/engineering/h2_leak_3d/GNUmakefile
 M examples/engineering/h2_leak_3d/pelelmex_prob.H
 M external/PeleC/Exec/Make.PeleC
 M external/PeleC/Source/Hydro.cpp
 M external/PeleC/Source/PeleC.cpp
 M external/PeleC/Source/Tagging.H
 M external/PeleC/Source/Tagging.cpp
 M external/PeleC/Source/WENO.H
 M external/PeleLMeX/CMake/BuildPelePhysicsLib.cmake
 M external/PeleLMeX/Exec/Make.PeleLMeX
 M external/PeleLMeX/Exec/RegTests/CMakeLists.txt
 M external/PeleLMeX/Source/PeleLMeX.H
 M external/PeleLMeX/Source/PeleLMeX.cpp
 M external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp
 M external/PeleLMeX/Source/PeleLMeX_Setup.cpp
 M external/PeleLMeX/Source/PeleLMeX_Tagging.cpp
 M external/PelePhysics/Source/Reactions/Make.package
 M external/PelePhysics/Source/Reactions/ReactorCvode.cpp
 D external/PelePhysics/Submodules/sundials
 M external/PelePhysics/Testing/Exec/Make.PelePhysics
 M external/amrex/Src/Extern/SUNDIALS/AMReX_Sundials_Core.cpp
 M src/academic/twophase/CSF.H
 M src/academic/twophase/TwoPhaseEOS.H
 M src/academic/vof/VOF_FCT.H
 M src/academic/vof/vof_modules.H
 M src/common/input_parser/yaml_parser.cpp
 M src/common/input_parser/yaml_schema.H
 M src/engineering/evaporation/evaporation_model.H
 M src/engineering/evaporation/pool_evaporation.H
 M src/engineering/evaporation/pool_vof_coupling.H
 M src/engineering/my_pele_modules.H
 M src/engineering/turbulence/wall_functions.H
 M src/engineering/turbulence/wall_functions.cpp
 M src/engineering/wind/wind_profile.H
 M src/geometry/bc_tags.H
 M src/geometry/bc_tags.cpp
 M src/geometry/eb2_factory.H
 M src/geometry/eb2_factory.cpp
 M src/geometry/stl_parser.cpp
 M test/unit/test_csf.cpp
 M test/unit/test_full.yaml
 M test/unit/test_twophase_eos.cpp
 M test/unit/test_twophase_hllc.cpp
 M test/unit/test_vof_fct.cpp
 M test/unit/test_wall_functions.cpp
 M test/unit/test_yaml_parser.cpp
 M tools/__pycache__/amrex_reader.cpython-312.pyc
 M tools/amrex_reader.py
?? .gitmodules
?? CHECKPOINTS/checkpoint-20260716-120912-codex-gpu-source-audit-second-order-numerics.md
?? CHECKPOINTS/checkpoint-20260716-123526-eng01-geometry-step-guard.md
?? CHECKPOINTS/checkpoint-20260716-124028-acd03-detonation-speed-species.md
?? CHECKPOINTS/checkpoint-20260716-125452-acd07-shock-droplet-spray.md
?? CHECKPOINTS/checkpoint-20260716-131314-eng14-acd10-pelec-cuda-p100-smoke.md
?? CHECKPOINTS/checkpoint-20260716-141753-eng14-acd10-pelelmex-cuda-p100-smoke.md
?? CHECKPOINTS/checkpoint-20260716-142320-qlt05-eng14-extended-gpu-source-audit.md
?? CMakeLists.txt
?? case_test_records/
?? docs/codex_audit/
?? examples/academic/bench_1gpu/
?? examples/academic/bench_1gpu_h2o2/
?? examples/academic/bench_1gpu_nn_A/
?? examples/academic/bench_1gpu_ppm1_test/
?? examples/academic/bench_1gpu_znd/
?? examples/academic/bench_2gpu/
?? examples/academic/bench_cpu16/
?? examples/academic/d2_law/input.codex_long_slope_smoke
?? examples/academic/d2_law/input.codex_smoke
?? examples/academic/d2_law/input.codex_trend_smoke
?? examples/academic/deton_cpu_build/
?? examples/academic/detonation_2D/inputs.codex_plan_amr_smoke
?? examples/academic/detonation_2D/inputs.codex_smoke
?? examples/academic/detonation_2D/inputs.codex_wave_smoke
?? examples/academic/detonation_hotspot/
?? examples/academic/detonation_znd_gpu/
?? examples/academic/shock_droplet/input.codex_sod_smoke
?? examples/academic/shock_droplet/input.codex_spray_smoke
?? examples/academic/vof_advection_1D/input.codex_smoke
?? examples/engineering/bfs_kepsilon/input.codex_smoke
?? examples/engineering/bfs_kepsilon/input.codex_yaml_profile_smoke.yaml
?? examples/engineering/bfs_kepsilon/input.codex_yaml_smoke.yaml
?? examples/engineering/c3h8_flacs/AMReX_buildInfo.cpp
?? examples/engineering/c3h8_gpu_test/input.codex_cuda_smoke
?? examples/engineering/counterflow_c12h23_gpu/
?? examples/engineering/counterflow_c12h23_v2/
?? examples/engineering/ecn_spray_a_gpu/
?? examples/engineering/h2_ignition/input.codex_history_sdc2_smoke
?? examples/engineering/h2_ignition/input.codex_history_smoke
?? examples/engineering/h2_ignition/input.codex_plot_smoke
?? examples/engineering/h2_ignition/input.codex_smoke
?? examples/engineering/h2_leak_3d/input.codex_plume_history_smoke
?? examples/engineering/h2_leak_3d/input.codex_plume_smoke
?? examples/engineering/h2_leak_3d/input.codex_smoke
?? examples/engineering/jet_flame_c12h23/
?? examples/engineering/spray_combust_3d/
?? examples/engineering/spray_heptane_1gpu/
?? external/PeleLMeX/Exec/RegTests/EB_EnclosedFlame/AMReX_buildInfo.cpp
?? external/PeleLMeX/Exec/RegTests/EB_FlowPastCylinder/input.codex_amr_smoke
?? external/PeleLMeX/Exec/RegTests/EB_FlowPastCylinder/input.codex_plan_amr_smoke
?? external/PeleLMeX/Exec/RegTests/EB_FlowPastCylinder/input.codex_smoke
?? external/PeleLMeX/Exec/RegTests/H2_HotBubble/
?? external/PeleLMeX_BAK_20260708/
?? external/PelePhysics/Mechanisms/C12H23/
?? external/PelePhysics/Mechanisms/h2o2/
?? external/PelePhysics/Source/Reactions/ReactorNN.H
?? external/PelePhysics/Source/Reactions/ReactorNN.H.nullbak
?? external/PelePhysics/Source/Reactions/ReactorNN.H.shell
?? external/PelePhysics/Source/Reactions/ReactorNN.H_BAK_20260712
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp.bak2
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp.bak_codex_v41_forward
... truncated after 120 entries
```
