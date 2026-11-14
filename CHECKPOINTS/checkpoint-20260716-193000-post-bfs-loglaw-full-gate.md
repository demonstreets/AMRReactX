# Checkpoint: Post ENG-09 BFS log-law full gate

Date: 2026-07-16
Status: PASS-GATE / PARTIAL-MASTER-PLAN

## Summary

After fixing the BFS k-epsilon log-law setup so the same wind-profile helper initializes the velocity field and inflow boundary, the default `tools/codex_smoke_all.sh` gate was rerun. The gate stayed green, including the generated-YAML PeleLMeX path whose log-law typical velocity now reflects the profile value rather than the old uniform reference speed.

This checkpoint proves the ENG-09 fix did not regress the maintained default CPU/GPU-static/plotfile validation gate. It does not claim full master-plan completion.

## Changed files / modules

- `examples/engineering/bfs_kepsilon/pelelmex_prob.H`
- `tools/codex_smoke_engineering_pelelmex_yaml.sh`
- `tools/codex_smoke_engineering_bfs_loglaw_profile_plotfile.sh`
- `tools/validate_bfs_loglaw_profile_plotfile.py`
- `docs/codex_audit/SMOKE_MATRIX.md`
- `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md`
- `CHECKPOINTS/checkpoint-20260716-190000-eng09-bfs-loglaw-plotfile.md`
- `CHECKPOINTS/checkpoint-20260716-193000-post-bfs-loglaw-full-gate.md`

## Verification

- `CODEX_SMOKE_LOG_DIR=/tmp/codex_smoke_all_post_bfs_loglaw_profile_20260716 JOBS=2 RUN_TIMEOUT=180 tools/codex_smoke_all.sh`
- `CODEX_RUN_LOG=/tmp/codex_bfs_from_yaml_post_loglaw_init_20260716.log CODEX_PROFILE_RUN_LOG=/tmp/codex_bfs_profile_from_yaml_post_loglaw_init_20260716.log JOBS=4 RUN_TIMEOUT=120 tools/codex_smoke_engineering_pelelmex_yaml.sh`
- `python3 -m py_compile tools/validate_bfs_loglaw_profile_plotfile.py`
- `bash -n tools/codex_smoke_engineering_bfs_loglaw_profile_plotfile.sh`
- `bash -n tools/codex_smoke_engineering_pelelmex_yaml.sh`

## Evidence

- `/tmp/codex_smoke_all_post_bfs_loglaw_profile_20260716/gate.log`
- `/tmp/codex_smoke_all_post_bfs_loglaw_profile_20260716/`
- `/tmp/codex_bfs_loglaw_profile_plotfile_20260716/validation.log`
- `/tmp/codex_bfs_profile_from_yaml_post_loglaw_init_20260716.log`
- Full-gate PASS line: `[codex-smoke-all] all smoke checks passed`
- Log-law plotfile PASS line: `bfs_loglaw_profile_plotfile_validation PASS time=0.00000000e+00 nx=80 ny=8 u_min=0.00000000e+00 u_max=3.92289976e-01 expected_min=0.00000000e+00 expected_max=3.92289976e-01 profile_linf=1.11022302e-16 v_linf=0.00000000e+00 shear=3.92289976e-01`

## Known limitations

- The full gate is still a smoke gate, not a complete master-plan validation campaign.
- ENG-09 still needs evolved ABL, wind-tunnel/open-terrain, turbulence-model, and EB-wall/y+ validation.
- QLT-03 still needs MMS, double-Mach, Rayleigh-Taylor, quantitative bubble-rise reference validation, and additional plan-specific reference tolerances.
