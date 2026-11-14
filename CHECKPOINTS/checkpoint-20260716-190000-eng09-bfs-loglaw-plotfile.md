# Checkpoint: ENG-09 BFS log-law plotfile profile

Date: 2026-07-16
Status: PASS-SMOKE / PARTIAL-ENG-09

## Summary

Fixed the BFS k-epsilon problem setup so the log-law wind profile is applied consistently to both the initial velocity field and inflow boundary state. Added a targeted smoke that generates the log-law BFS input from YAML, runs PeleLMeX with plot output, and validates the initial `x_velocity(y)` field against the log-law formula in the plotfile.

This moves ENG-09 from input/boundary-state evidence toward solver-output evidence. It is still an initial-profile smoke, not an evolved atmospheric-boundary-layer or wind-tunnel benchmark.

## Changed files / modules

- `examples/engineering/bfs_kepsilon/pelelmex_prob.H`
- `tools/codex_smoke_engineering_bfs_loglaw_profile_plotfile.sh`
- `tools/validate_bfs_loglaw_profile_plotfile.py`
- `docs/codex_audit/SMOKE_MATRIX.md`
- `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md`
- `CHECKPOINTS/checkpoint-20260716-190000-eng09-bfs-loglaw-plotfile.md`

## Verification

- `make -C examples/engineering/bfs_kepsilon -j 4 EBASE=codex_bfs_cpu`
- `python3 -m py_compile tools/validate_bfs_loglaw_profile_plotfile.py`
- `bash -n tools/codex_smoke_engineering_bfs_loglaw_profile_plotfile.sh`
- `CODEX_BFS_LOGLAW_PROFILE_LOG_DIR=/tmp/codex_bfs_loglaw_profile_plotfile_20260716 JOBS=4 RUN_TIMEOUT=120 tools/codex_smoke_engineering_bfs_loglaw_profile_plotfile.sh`
- `CODEX_RUN_LOG=/tmp/codex_bfs_from_yaml_post_loglaw_init_20260716.log CODEX_PROFILE_RUN_LOG=/tmp/codex_bfs_profile_from_yaml_post_loglaw_init_20260716.log JOBS=4 RUN_TIMEOUT=120 tools/codex_smoke_engineering_pelelmex_yaml.sh`

## Evidence

- `/tmp/codex_bfs_loglaw_profile_plotfile_20260716/input.codex_bfs_loglaw_profile`
- `/tmp/codex_bfs_loglaw_profile_plotfile_20260716/run.log`
- `/tmp/codex_bfs_loglaw_profile_plotfile_20260716/validation.log`
- `/tmp/codex_bfs_from_yaml_post_loglaw_init_20260716.log`
- `/tmp/codex_bfs_profile_from_yaml_post_loglaw_init_20260716.log`
- PASS line: `bfs_loglaw_profile_plotfile_validation PASS time=0.00000000e+00 nx=80 ny=8 u_min=0.00000000e+00 u_max=3.92289976e-01 expected_min=0.00000000e+00 expected_max=3.92289976e-01 profile_linf=1.11022302e-16 v_linf=0.00000000e+00 shear=3.92289976e-01`

## Known limitations

- Initial-profile smoke only; it does not validate an evolved neutral ABL.
- No wind-tunnel/open-terrain reference comparison yet.
- EB-wall wind/y+ diagnostics and turbulence-model validation remain open.
