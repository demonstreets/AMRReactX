# Checkpoint - Machine-local path audit and cleanup

> Date: 2026-07-16T16:57:37+08:00
> Agent: Codex
> Related items: QLT-04 checkpoint records, Release/reproducibility portability

## Summary

- Added strict machine-local path audit for maintained source/script/input roots and integrated it into preflight.
- Removed maintained /home/cj, stale /home/demon..., and direct unit-test /tmp/test_* path dependencies; ReactorNN model paths are now runtime-configurable.
- Full CUDA-inclusive reproducible wrapper gate still passes after the cleanup.

## Changed Files / Modules

- tools/check_machine_local_paths.py
- tools/codex_preflight_environment.sh
- tools/codex_smoke_geometry_amrex_domain.sh
- external/PelePhysics/Source/Reactions/ReactorNN.cpp
- test/unit/test_stl_parser.cpp
- test/unit/test_yaml_parser.cpp
- examples/academic/*/GNUmakefile* and examples/engineering/*/GNUmakefile* with machine-local path cleanup
- docs/codex_audit/ENVIRONMENT_PREFLIGHT.md
- docs/codex_audit/SMOKE_MATRIX.md
- docs/codex_audit/MASTER_PLAN_TRACEABILITY.md

## Verification

- python3 tools/check_machine_local_paths.py --strict -> PASS scanned_files=893
- SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda tools/codex_preflight_environment.sh --require-cuda -> PASS warnings=0
- tools/codex_smoke_geometry_eb2_stl.sh -> PASS
- tools/codex_smoke_geometry_amrex_domain.sh -> PASS
- SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda CODEX_REPRO_REQUIRE_CUDA=1 CODEX_REPRO_LOG_DIR=/tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716 JOBS=1 RUN_TIMEOUT=240 tools/codex_reproducible_gate.sh -> PASS

## Evidence Paths

- /tmp/codex_machine_local_paths_final_strict_20260716.log
- /tmp/codex_preflight_machine_paths_20260716.log
- /tmp/codex_geometry_eb2_stl_machine_paths_20260716.log
- /tmp/codex_geometry_amrex_domain_machine_paths_20260716_rerun.log
- /tmp/codex_reproducible_gate_full_cuda_machine_paths_20260716.log
- /tmp/codex_reproducible_gate_full_cuda_machine_paths_failure_scan_20260716.log

## Known Limitations

- Generated build products, plotfiles, checkpoint directories, and generated AMReX_buildInfo.cpp are intentionally excluded from the path audit.
- This portability gate does not prove full dependency bootstrap, release tagging, or the remaining master-plan physics validation matrix.

## Git Status Snapshot

```text
 M AGENTS.md
 M PROGRESS.md
 M examples/academic/detonation_2D/GNUmakefile
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
 M external/PeleC/Source/Hydro.cpp
 M external/PeleC/Source/PeleC.cpp
 M external/PeleC/Source/Tagging.H
 M external/PeleC/Source/Tagging.cpp
 M external/PeleC/Source/WENO.H
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
?? CHECKPOINTS/checkpoint-20260716-170000-post-exact-vortex-full-gate.md
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
... truncated after 120 entries
```
