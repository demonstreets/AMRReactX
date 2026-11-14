# Checkpoint - RT input-name sensitivity fixed by absolute input normalization

> Date: 2026-07-17T10:59:46+08:00
> Agent: Codex
> Related items: QLT-03, ACD-04

## Summary

- Fixed the PeleC launch path by normalizing a relative argv[1] inputs filename to an absolute path before amrex::Initialize, eliminating the RT high-resolution failure triggered by long dotted relative input names.
- Converted the RT input-name diagnostic from an expected-failure reproducer into a regression that requires both inputs_safe and the formerly failing input.codex_high to PASS.
- Updated RT highres and resolution-trend wrappers to intentionally use long dotted input.codex_* relative filenames, so maintained guardrails exercise the fixed path instead of avoiding it.

## Changed Files / Modules

- external/PeleC/Source/main.cpp
- tools/codex_diagnose_rayleigh_taylor_input_name_sensitivity.sh
- tools/codex_smoke_academic_rayleigh_taylor_highres_probe.sh
- tools/codex_smoke_academic_rayleigh_taylor_resolution_trend.sh
- docs/codex_audit/SMOKE_MATRIX.md
- docs/codex_audit/MASTER_PLAN_TRACEABILITY.md

## Verification

- make -j 4 DIM=2 EBASE=codex_rayleigh_taylor USE_MPI=FALSE USE_OMP=FALSE: PASS
- CODEX_RAYLEIGH_TAYLOR_NAME_LOG_DIR=/tmp/codex_rt_input_name_fixed_20260717 bash tools/codex_diagnose_rayleigh_taylor_input_name_sensitivity.sh: PASS
- CODEX_RAYLEIGH_TAYLOR_HIGHRES_LOG_DIR=/tmp/codex_rt_highres_input_abs_fix_20260717 bash tools/codex_smoke_academic_rayleigh_taylor_highres_probe.sh: PASS
- CODEX_RAYLEIGH_TAYLOR_TREND_LOG_DIR=/tmp/codex_rt_trend_input_abs_fix_20260717 bash tools/codex_smoke_academic_rayleigh_taylor_resolution_trend.sh: PASS
- SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh: PASS (warnings=3 optional CUDA SUNDIALS libs missing)

## Evidence Paths

- /tmp/codex_rt_input_abs_fix_matrix_20260717_105347/summary.tsv: all six relative/absolute/dir-name cases PASS
- /tmp/codex_rt_input_name_fixed_20260717/summary.tsv: inputs_safe PASS; input.codex_high PASS
- /tmp/codex_rt_highres_input_abs_fix_20260717/growth.log: 128x256 growth ratio 1.0326368, zero mass/VOF drift
- /tmp/codex_rt_trend_input_abs_fix_20260717/resolution_trend.log: 32x64/64x128/96x192 trend PASS, rate_spread=0.521898
- /tmp/codex_rt_input_abs_fix_preflight_20260717.log: preflight SUMMARY PASS warnings=3; machine-local path audit strict PASS

## Known Limitations

- This fixes the launch/input-name sensitivity but does not resolve the separate low-pressure p0=10,cfl=0.05 128x256 RT robustness loss around steps 85-92.
- RT still needs published/reference growth-rate, capillary/static-droplet, bubble-rise, and longer-time two-phase stability validation before QLT-03/ACD-04 can be marked complete.

## Git Status Snapshot

```text
 M AGENTS.md
 M PROGRESS.md
 M examples/academic/detonation_2D/GNUmakefile
 M examples/academic/rayleigh_taylor/GNUmakefile
 M examples/academic/rayleigh_taylor/inputs
 M examples/academic/rayleigh_taylor/prob.H
 M examples/academic/rayleigh_taylor/prob.cpp
 M examples/academic/rayleigh_taylor/prob_parm.H
 M examples/academic/vof_advection_1D/prob.H
 M examples/engineering/bfs_kepsilon/pelelmex_prob.H
 M examples/engineering/bfs_kepsilon/pelelmex_prob.cpp
 M examples/engineering/c3h8_flacs/GNUmakefile
 M examples/engineering/c3h8_flacs_amr/GNUmakefile
 M examples/engineering/c3h8_flacs_ke_wall_test/GNUmakefile
 M examples/engineering/c3h8_flacs_mpi/GNUmakefile
 M examples/engineering/c3h8_flacs_mpi/GNUmakefile.full
 M examples/engineering/c3h8_flacs_mpi/GNUmakefile.mpi
 M examples/engineering/c3h8_flacs_wall/GNUmakefile
 M examples/engineering/c3h8_gpu_test/GNUmakefile
 M examples/engineering/c3h8_gpu_test/pelelmex_prob.H
 M examples/engineering/h2_ignition/GNUmakefile
 M examples/engineering/h2_ignition/pelelmex_prob.cpp
 M examples/engineering/h2_leak_3cyl/GNUmakefile.abs
 M examples/engineering/h2_leak_3cyl_kepsilon/GNUmakefile
 M examples/engineering/h2_leak_3d/GNUmakefile
 M examples/engineering/h2_leak_3d/pelelmex_prob.H
 M examples/engineering/test_c3h8/GNUmakefile
 M examples/engineering/triangle_cyl/GNUmakefile
 M external/PeleC/Exec/Make.PeleC
 M external/PeleC/Exec/RegTests/IsentropicVortex/prob.H
 M external/PeleC/Exec/RegTests/IsentropicVortex/prob.cpp
 M external/PeleC/Exec/RegTests/IsentropicVortex/prob_parm.H
 M external/PeleC/Source/Godunov.H
 M external/PeleC/Source/Hydro.cpp
 M external/PeleC/Source/MOL.cpp
 M external/PeleC/Source/PeleC.cpp
 M external/PeleC/Source/PeleCUtilities.H
 M external/PeleC/Source/Tagging.H
 M external/PeleC/Source/Tagging.cpp
 M external/PeleC/Source/WENO.H
 M external/PeleC/Source/main.cpp
 M external/PeleC/Submodules/PelePhysics
 M external/PeleLMeX/CMake/BuildPelePhysicsLib.cmake
 M external/PeleLMeX/Exec/Make.PeleLMeX
 M external/PeleLMeX/Exec/RegTests/CMakeLists.txt
 M external/PeleLMeX/Source/PeleLMeX.H
 M external/PeleLMeX/Source/PeleLMeX.cpp
 M external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp
 M external/PeleLMeX/Source/PeleLMeX_Setup.cpp
 M external/PeleLMeX/Source/PeleLMeX_Tagging.cpp
 M external/PeleLMeX/Submodules/PelePhysics
 M external/PelePhysics/Source/Reactions/Make.package
 M external/PelePhysics/Source/Reactions/ReactorCvode.cpp
 M external/PelePhysics/Submodules/amrex
 D external/PelePhysics/Submodules/sundials
 M external/PelePhysics/Testing/Exec/IgnitionDelay/GPU_misc.H
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
 M test/unit/test_stl_parser.cpp
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
?? CHECKPOINTS/checkpoint-20260716-143344-eng13-acd09-parallel-performance-baseline.md
?? CHECKPOINTS/checkpoint-20260716-143825-qlt03-isentropic-vortex-reference.md
?? CHECKPOINTS/checkpoint-20260716-144627-qlt03-pelec-isentropic-vortex-solver-smoke.md
?? CHECKPOINTS/checkpoint-20260716-150000-qlt03-pelec-isentropic-vortex-resolution-trend.md
?? CHECKPOINTS/checkpoint-20260716-153000-qlt03-pelec-isentropic-vortex-self-convergence.md
?? CHECKPOINTS/checkpoint-20260716-160000-qlt03-pelec-exact-isentropic-vortex-convergence.md
?? CHECKPOINTS/checkpoint-20260716-163000-qlt03-pelec-exact-vortex-pressure-normalization.md
?? CHECKPOINTS/checkpoint-20260716-165737-machine-local-path-audit.md
?? CHECKPOINTS/checkpoint-20260716-170000-post-exact-vortex-full-gate.md
?? CHECKPOINTS/checkpoint-20260716-170717-eng10-h2-ignition-delay.md
?? CHECKPOINTS/checkpoint-20260716-171951-qlt03-double-mach-smoke.md
?? CHECKPOINTS/checkpoint-20260716-173000-qlt03-pelelmex-periodic-covo-self-convergence.md
?? CHECKPOINTS/checkpoint-20260716-181500-qlt03-pelelmex-hotbubble-plotfile.md
?? CHECKPOINTS/checkpoint-20260716-190000-eng09-bfs-loglaw-plotfile.md
?? CHECKPOINTS/checkpoint-20260716-193000-post-bfs-loglaw-full-gate.md
?? CHECKPOINTS/checkpoint-20260716-200000-release-provenance-audit.md
?? CHECKPOINTS/checkpoint-20260716-203000-release-provenance-relative-symlinks.md
?? CHECKPOINTS/checkpoint-20260716-211500-release-provenance-strict-pass.md
?? CHECKPOINTS/checkpoint-20260716-214500-environment-preflight.md
?? CHECKPOINTS/checkpoint-20260716-221500-reproducible-wrapper-gate.md
?? CHECKPOINTS/checkpoint-20260716-223000-full-reproducible-wrapper-gate.md
?? CHECKPOINTS/checkpoint-20260716-224500-full-cuda-reproducible-wrapper-gate.md
?? CHECKPOINTS/checkpoint-20260717-093452-checkpoint-20260717-rt-vof-eos-smoke.md
?? CHECKPOINTS/checkpoint-20260717-095838-rt-two-phase-growth-gate-20260717.md
?? CHECKPOINTS/checkpoint-20260717-101815-rt-resolution-trend-guardrail-20260717.md
?? CHECKPOINTS/checkpoint-20260717-103913-rt-highres-probe-input-name-guard-20260717.md
?? CHECKPOINTS/checkpoint-20260717-104812-rt-input-name-sensitivity-diagnostic-20260717.md
?? CHECKPOINTS/checkpoint-20260717-105946-rt-input-name-absolute-normalization-20260717.md
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
?? examples/academic/rayleigh_taylor/input.codex_growth
?? examples/academic/rayleigh_taylor/input.codex_smoke
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
?? external/PeleC/Exec/RegTests/DoubleMachReflection/input.codex_smoke
?? external/PeleC/Exec/RegTests/IsentropicVortex/input.codex_smoke
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
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp.bak_codex_v4_ooddiag
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp.nullbak
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp.planb
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp.shell
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp.stage4a_bak
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp_BAK_20260712
?? external/PelePhysics/Source/Reactions/ReactorNN.cpp_BAK_planA_pre_20260712_115348
?? external/PelePhysics/Testing/Exec/IgnitionDelay/inputs/inputs.codex_h2_firstpass
?? external/PelePhysics/Testing/Exec/ReactEval/inputs.nn_test
?? external/amrex/Src/Extern/SUNDIALS/arkode
?? external/amrex/Src/Extern/SUNDIALS/cvode
?? external/amrex/Src/Extern/SUNDIALS/nvector
?? external/amrex/Src/Extern/SUNDIALS/sunadaptcontroller
?? external/amrex/Src/Extern/SUNDIALS/sunadjointcheckpointscheme
?? external/amrex/Src/Extern/SUNDIALS/sundials
?? external/amrex/Src/Extern/SUNDIALS/sundomeigest
?? external/amrex/Src/Extern/SUNDIALS/sunlinsol
?? external/amrex/Src/Extern/SUNDIALS/sunmatrix
?? external/amrex/Src/Extern/SUNDIALS/sunmemory
?? external/amrex/Src/Extern/SUNDIALS/sunnonlinsol
?? src/academic/droplet/
?? src/academic/twophase/TwoPhaseParams.H
?? src/academic/validation/
?? src/academic/vof/PLIC.H
?? src/common/input_parser/parmparse_writer.H
?? src/common/input_parser/parmparse_writer.cpp
?? src/engineering/amr/
?? src/engineering/dispersion/
?? src/engineering/leak_source/
?? src/engineering/numerics/
?? src/geometry/domain_builder.H
?? test/unit/AMReX_Config.H.in
?? test/unit/mechanism.H
?? test/unit/test_amrex_domain_builder.cpp
?? test/unit/test_d2_law.cpp
?? test/unit/test_evaporation_model.cpp
?? test/unit/test_gaussian_plume.cpp
?? test/unit/test_geometry_pipeline.cpp
?? test/unit/test_isentropic_vortex.cpp
?? test/unit/test_leak_source.cpp
?? test/unit/test_pelec_weno.cpp
?? test/unit/test_pool_vof_coupling.cpp
?? test/unit/test_refinement_tags.cpp
?? test/unit/test_second_order_advection.cpp
?? test/unit/test_sod_shock_tube.cpp
?? test/unit/test_vof_plic.cpp
?? test/unit/test_wind_profile.cpp
?? tools/__pycache__/check_gpu_source_audit.cpython-312.pyc
?? tools/__pycache__/check_machine_local_paths.cpython-312.pyc
?? tools/__pycache__/check_release_provenance.cpython-312.pyc
?? tools/__pycache__/validate_bfs_loglaw_profile_plotfile.cpython-312.pyc
?? tools/__pycache__/validate_d2_fresh_history.cpython-312.pyc
?? tools/__pycache__/validate_detonation_wave.cpython-312.pyc
?? tools/__pycache__/validate_double_mach_plotfile.cpython-312.pyc
?? tools/__pycache__/validate_h2_ignition_delay.cpython-312.pyc
?? tools/__pycache__/validate_h2_leak_plume.cpython-312.pyc
?? tools/__pycache__/validate_parallel_perf_summary.cpython-312.pyc
?? tools/__pycache__/validate_parallel_smoke_log.cpython-312.pyc
?? tools/__pycache__/validate_pelec_cuda_smoke.cpython-312.pyc
?? tools/__pycache__/validate_pelec_isentropic_vortex.cpython-312.pyc
?? tools/__pycache__/validate_pelec_isentropic_vortex_exact_convergence.cpython-312.pyc
?? tools/__pycache__/validate_pelec_isentropic_vortex_self_convergence.cpython-312.pyc
?? tools/__pycache__/validate_pelec_isentropic_vortex_trend.cpython-312.pyc
?? tools/__pycache__/validate_pelelmex_cuda_smoke.cpython-312.pyc
?? tools/__pycache__/validate_pelelmex_hotbubble_plotfile.cpython-312.pyc
?? tools/__pycache__/validate_pelelmex_periodic_covo_self_convergence.cpython-312.pyc
?? tools/__pycache__/validate_rayleigh_taylor_growth.cpython-312.pyc
?? tools/__pycache__/validate_rayleigh_taylor_plotfile.cpython-312.pyc
?? tools/__pycache__/validate_rayleigh_taylor_resolution_trend.cpython-312.pyc
?? tools/__pycache__/validate_shock_droplet_spray.cpython-312.pyc
?? tools/__pycache__/validate_sod_plotfile.cpython-312.pyc
?? tools/__pycache__/write_codex_checkpoint.cpython-312.pyc
?? tools/check_gpu_source_audit.py
?? tools/check_machine_local_paths.py
?? tools/check_release_provenance.py
?? tools/codex_audit_dependencies.sh
?? tools/codex_diagnose_rayleigh_taylor_input_name_sensitivity.sh
?? tools/codex_preflight_environment.sh
?? tools/codex_reproducible_gate.sh
?? tools/codex_smoke_academic_d2_law.sh
?? tools/codex_smoke_academic_detonation_wave.sh
?? tools/codex_smoke_academic_double_mach.sh
?? tools/codex_smoke_academic_pelec.sh
?? tools/codex_smoke_academic_pelec_cuda.sh
?? tools/codex_smoke_academic_pelec_hybrid.sh
?? tools/codex_smoke_academic_pelec_isentropic_vortex.sh
?? tools/codex_smoke_academic_pelec_isentropic_vortex_exact_convergence.sh
?? tools/codex_smoke_academic_pelec_isentropic_vortex_self_convergence.sh
?? tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh
?? tools/codex_smoke_academic_pelec_mpi.sh
?? tools/codex_smoke_academic_pelec_omp.sh
?? tools/codex_smoke_academic_pelec_plan_amr.sh
?? tools/codex_smoke_academic_rayleigh_taylor.sh
?? tools/codex_smoke_academic_rayleigh_taylor_growth.sh
?? tools/codex_smoke_academic_rayleigh_taylor_highres_probe.sh
?? tools/codex_smoke_academic_rayleigh_taylor_resolution_trend.sh
?? tools/codex_smoke_academic_shock_droplet_spray.sh
?? tools/codex_smoke_academic_sod_plotfile.sh
?? tools/codex_smoke_academic_vof_advection.sh
?? tools/codex_smoke_all.sh
?? tools/codex_smoke_engineering_bfs_loglaw_profile_plotfile.sh
?? tools/codex_smoke_engineering_h2_ignition.sh
?? tools/codex_smoke_engineering_h2_ignition_delay.sh
?? tools/codex_smoke_engineering_h2_ignition_history.sh
?? tools/codex_smoke_engineering_h2_ignition_plotfile.sh
?? tools/codex_smoke_engineering_h2_ignition_sdc_compare.sh
?? tools/codex_smoke_engineering_h2_leak.sh
?? tools/codex_smoke_engineering_h2_leak_plume_history.sh
?? tools/codex_smoke_engineering_pelelmex.sh
?? tools/codex_smoke_engineering_pelelmex_amr.sh
?? tools/codex_smoke_engineering_pelelmex_cuda.sh
?? tools/codex_smoke_engineering_pelelmex_eb.sh
?? tools/codex_smoke_engineering_pelelmex_hotbubble.sh
?? tools/codex_smoke_engineering_pelelmex_hybrid.sh
?? tools/codex_smoke_engineering_pelelmex_mpi.sh
?? tools/codex_smoke_engineering_pelelmex_omp.sh
?? tools/codex_smoke_engineering_pelelmex_periodic_covo.sh
?? tools/codex_smoke_engineering_pelelmex_yaml.sh
?? tools/codex_smoke_geometry_amrex_domain.sh
?? tools/codex_smoke_geometry_eb2_stl.sh
?? tools/codex_smoke_parallel_perf_baseline.sh
?? tools/codex_yaml_to_parmparse.cpp
?? tools/test_gpu_source_audit_rules.sh
?? tools/validate_bfs_loglaw_profile_plotfile.py
?? tools/validate_d2_fresh_history.py
?? tools/validate_detonation_wave.py
?? tools/validate_double_mach_plotfile.py
?? tools/validate_h2_ignition_delay.py
?? tools/validate_h2_ignition_history.py
?? tools/validate_h2_ignition_plotfile.py
?? tools/validate_h2_ignition_sdc_compare.py
?? tools/validate_h2_leak_plume.py
?? tools/validate_h2_leak_plume_history.py
?? tools/validate_parallel_perf_summary.py
?? tools/validate_parallel_smoke_log.py
?? tools/validate_pelec_cuda_smoke.py
?? tools/validate_pelec_isentropic_vortex.py
?? tools/validate_pelec_isentropic_vortex_exact_convergence.py
?? tools/validate_pelec_isentropic_vortex_self_convergence.py
?? tools/validate_pelec_isentropic_vortex_trend.py
?? tools/validate_pelec_plan_amr.py
?? tools/validate_pelelmex_cuda_smoke.py
?? tools/validate_pelelmex_hotbubble_plotfile.py
?? tools/validate_pelelmex_periodic_covo_self_convergence.py
?? tools/validate_rayleigh_taylor_growth.py
?? tools/validate_rayleigh_taylor_plotfile.py
?? tools/validate_rayleigh_taylor_resolution_trend.py
?? tools/validate_shock_droplet_spray.py
?? tools/validate_sod_plotfile.py
?? tools/write_codex_checkpoint.py
```
