# Checkpoint - Engineering H2 leak open-domain release-rate sensitivity

> Date: 2026-07-17T16:24:22+08:00
> Agent: Codex
> Related items: ENG-06, ENG-10, ENG-11, QLT-03, QLT-04

## Summary

- Added a two-point open-domain H2 release-rate sensitivity gate that derives low/high leak-rate inputs, runs the maintained flammable-cloud chain for both, writes a summary CSV, and verifies mass scaling plus increased cloud species mass, peak mole fraction, and cloud volume for the stronger release.

## Changed Files / Modules

- tools/codex_smoke_engineering_h2_leak_open_domain_release_rate.sh
- docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md
- docs/codex_audit/SMOKE_MATRIX.md

## Verification

- CODEX_H2_LEAK_RELEASE_LOG_DIR=/tmp/codex_h2_leak_open_domain_release_rate_20260717 RUN_TIMEOUT=600 JOBS=4 tools/codex_smoke_engineering_h2_leak_open_domain_release_rate.sh -> PASS
- bash -n tools/codex_smoke_engineering_h2_leak_open_domain_release_rate.sh tools/codex_smoke_engineering_h2_leak_open_domain_sensitivity.sh tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh -> PASS
- python3 tools/check_machine_local_paths.py --strict -> PASS scanned_files=919
- SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh -> PASS warnings=3

## Evidence Paths

- /tmp/codex_h2_leak_open_domain_release_rate_20260717/release_rate_summary.csv
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/low_release/validation.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/low_release/profile_validation.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/low_release/hazard_summary.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/low_release/hazard_planes.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/low_release/hazard_timeseries.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/high_release/validation.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/high_release/profile_validation.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/high_release/hazard_summary.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/high_release/hazard_planes.log
- /tmp/codex_h2_leak_open_domain_release_rate_20260717/high_release/hazard_timeseries.log
- /tmp/codex_h2_open_domain_release_rate_bashn_20260717.log
- /tmp/codex_h2_open_domain_release_rate_path_audit_20260717.log
- /tmp/codex_h2_open_domain_release_rate_preflight_20260717.log

## Known Limitations

- Two-point release-rate smoke only; it does not vary leak radius, tank pressure/orifice model, crosswind, turbulence, geometry, ignition/fire coupling, or long-time stability.
- Open-domain cases remain coarse all-regular single-box plotfiles because the lightweight reader does not yet stitch multi-box 3D data.

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
... truncated after 120 entries
```
