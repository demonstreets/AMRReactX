# Checkpoint: Post Exact-Vortex Full Smoke Gate

Date: 2026-07-16
Scope: Repository-level regression check after QLT-03 PeleC exact isentropic-vortex initialization/reference updates.

## Verification

Command:

```bash
CODEX_SMOKE_LOG_DIR=/tmp/codex_smoke_all_post_exact_vortex_p1_beta5_20260716 JOBS=2 RUN_TIMEOUT=180 tools/codex_smoke_all.sh
```

Result: PASS.

Evidence directory:

- `/tmp/codex_smoke_all_post_exact_vortex_p1_beta5_20260716/`

Key evidence:

- `gpu_source_audit_rules PASS`
- `gpu_source_audit PASS profile=default roots=src/academic,src/engineering,src/common files=35 gpu_blocks=26 forbidden_findings=0`
- `gpu_source_audit PASS profile=extended roots=src/academic,src/engineering,src/common,examples/engineering/c3h8_gpu_test files=40 gpu_blocks=30 forbidden_findings=0`
- `100% tests passed, 0 tests failed out of 20` in `cmake_weno.log`
- Default smoke scripts passed for engineering PeleLMeX, generated-YAML PeleLMeX, H2 ignition plotfile/history/SDC compare, academic PeleC, detonation-wave, plan-AMR, and Sod plotfile.
- No `Unused ParmParse Variables` markers were found in top-level smoke logs.

## Interpretation

The default repository gate stayed green after the PeleC exact-vortex changes. This does not make the master plan complete, but it establishes that the QLT-03 exact-vortex work did not regress the maintained quick-check surface.
