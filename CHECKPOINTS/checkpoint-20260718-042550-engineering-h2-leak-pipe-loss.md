# Engineering H2 Leak Pipe-Loss Checkpoint

Date (UTC): 20260718-042550

## What changed

- Added steady equivalent pipe/valve loss inputs to the pressure-orifice H2 leak source: `prob.leak_line_diameter`, `prob.leak_line_length`, `prob.leak_line_friction_factor`, and `prob.leak_line_loss_coeff`.
- The source now solves an effective orifice-upstream pressure from `K = K_minor + f L / D`, reducing mdot relative to the no-loss orifice formula while preserving the default no-loss behavior when the new fields are zero.
- Added `examples/engineering/h2_leak_3d/input.codex_pipe_loss_smoke` and `tools/codex_smoke_engineering_h2_leak_pipe_loss.sh`.
- Extended `leak_source_smoke` with equivalent-loss pressure/mdot checks and tank-blowdown-with-line-loss interval coverage.
- Updated engineering readiness and smoke-matrix audit docs with pipe-loss evidence and residual limitations.

## Verification evidence

- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`: PASS. Log: `/tmp/codex_pipe_loss_ctest_leak_source_20260718.log`.
- Pipe-loss 3D H2 leak smoke: PASS. Log dir: `/tmp/codex_h2_leak_pipe_loss_20260718`. Validation: `massN=6.62820318e-05`, `injectedN=6.62820318e-05`, `mass_ratioN=1.00000000e+00`, `mass_growth_ratio=5.00000000e+00`, downstream/upstream `7.16962501e-01/2.83037499e-01`. Wrapper: `mdot=1.32564063e-03`, `no_loss_mdot=1.74271791e-03`, `reduction=7.60674246e-01`, `effective_pressure=3.80337123e+05`, `supply_pressure=5.00000000e+05`, `line_loss_total=4.40000000e+01`, `mass_ratioN=1.00000000e+00`.
- Accidental duplicate pipe-loss rerun caused by an unquoted checkpoint heredoc also passed at `/tmp/codex_h2_leak_pipe_loss_20260718T042552Z`; it is not the primary evidence but confirms repeatability of the same smoke.
- No-loss pressure-orifice regression: PASS. Log dir: `/tmp/codex_h2_leak_pressure_orifice_post_pipe_loss_20260718`; wrapper rel error `2.353e-10`.
- Tank-blowdown regression: PASS. Log dir: `/tmp/codex_h2_leak_tank_blowdown_post_pipe_loss_20260718`; wrapper `pressure_drop=2.11027122e+04`, `mdot_drop=7.20811300e-05`, `mass_ratioN=1.00000000e+00`.
- Fixed-rate plume-history regression: PASS. Log dir: `/tmp/codex_h2_leak_plume_history_post_pipe_loss_20260718`; `mass_ratioN=1.00000000e+00`.
- Hygiene: bash syntax PASS, Python compile PASS, targeted `git diff --check` PASS for changed source/docs, path audit PASS (`scanned_files=931`), preflight PASS with 3 optional CUDA SUNDIALS warnings, and no `Unused ParmParse Variables` or `RuntimeWarning` in new/regression logs.

## Residual risk

- This is a steady 1D equivalent-loss model only. It is useful for engineering screening of line/valve restrictions, but it is not a distributed unsteady pipe-network model.
- Still missing production-grade real-gas compressibility, thermal cooldown, linepack, valve opening/closing transients, multi-hole releases, sonic jet resolution, fire coupling, long-time campaigns, and reference/literature validation.
- Current evidence remains smoke-scale; it improves source physics coverage but does not make the full code production-grade yet.

## Recommended next slice

Engineering priority remains gas leak production readiness. Highest-value next options: add real-gas/thermal-cooldown discharge corrections, multi-hole source layout support, distributed pipe-network/linepack scaffolding, or strengthen CAD/STL geometry QA and longer open-domain campaigns.
