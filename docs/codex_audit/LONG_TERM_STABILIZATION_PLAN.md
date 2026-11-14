# Long-term stabilization plan

Owner: Codex takeover branch `codex/stabilize-my-pele`
Date: 2026-07-15

## North star

Turn `my-pele` from an exploratory PeleC/PeleLMeX experiment tree into a reproducible CFD platform whose claims are backed by build logs, short smoke cases, and physics validation reports.

A feature is not considered complete because a progress note says it is complete. It is complete only when the repository contains:

1. a documented build path,
2. a minimal smoke test or short solver run,
3. a validation or limitation note tied to the master plan requirement,
4. a clean enough git/dependency state for someone else to reproduce it.

## Stage A — repository and build hygiene

Goal: make the repository understandable and buildable without personal shell state.

- Preserve takeover snapshots and do not delete existing user results.
- Restore submodule metadata and dependency provenance.
- Keep standard make/CMake build paths usable outside CodeWhale.
- Add top-level smoke tests for standalone modules.
- Separate generated case outputs from source and document what is intentionally retained.

Exit criteria:

- `git submodule status --recursive` exits successfully.
- Top-level CMake smoke tests pass.
- At least one PeleLMeX example and one PeleC example have documented short rebuild/run probes.

## Stage B — engineering/PeleLMeX stabilization

Goal: make the engineering leakage/dispersion path reliable before adding more physics.

Priority fixes:

- k-epsilon source terms: boundary-safe gradients, ghost-cell policy, EB cut-cell handling.
- k-epsilon wall functions: EB wall distance, wall normal, y-plus diagnostics.
- leakage source accounting: mass/species/energy conservation and CSV diagnostics.
- C3H8/H2 leakage smoke cases: short CPU run, optional GPU run, NaN/mass checks.

Exit criteria:

- Short PeleLMeX nonreacting leakage case runs from a documented command.
- k/epsilon remain finite and positive.
- injected mass and domain inventory agree within a documented tolerance.

## Stage C — reacting engineering cases

Goal: enable combustion only after nonreacting transport is stable.

Priority fixes:

- Mechanism provenance and unit checks.
- Reactor choice matrix: RK64/CVODE/NN only with clear support status.
- Small H2/C3H8 ignition/flame smoke cases.
- GPU memory and NaN failure modes documented.

Exit criteria:

- One short reacting PeleLMeX case completes without NaN.
- Chemistry mechanism and units are documented.

## Stage D — academic/PeleC stabilization

Goal: distinguish working PeleC shock/detonation capabilities from WENO/VOF prototypes.

Priority fixes:

- WENO: document current scalar primitive reconstruction; do not claim characteristic WENO until implemented.
- PeleC detonation: short GPU and CPU-capable probes with clear solver settings.
- VOF/two-phase: isolate as experimental until PLIC, EOS, HLLC, CSF, and conservation tests are mature.

Exit criteria:

- PeleC Sod or ZND short case has a documented reproducible command.
- WENO smoke test passes and limitations are documented.
- VOF/two-phase claims are downgraded or backed by tests.

## Stage E — qualification and release

Goal: converge to a usable research release.

- Master-plan requirement matrix regenerated from evidence.
- Known limitations page kept current.
- Build/run scripts are idempotent.
- Long-running production cases separated from quick CI smoke cases.

## Current Stage A status

Updated 2026-07-15:
- DONE: top-level CMake smoke target exists and `weno5_smoke` passes.
- DONE: repository submodule status no longer fails immediately due to missing `.gitmodules` entry for AMReX-Hydro.
- DONE: `/home/cj/bin/make` no longer blocks normal builds by default.
- DONE: `examples/engineering/bfs_kepsilon` builds with GNU CPU and completes a 1-step smoke run.
- DONE: `examples/academic/detonation_2D` builds from repository-local PeleC sources and completes a 1-step CPU reacting smoke run via `tools/codex_smoke_academic_pelec.sh`.
- DONE: `tools/codex_smoke_all.sh` now runs the current quick gate across CMake/WENO, PeleLMeX engineering CPU, and PeleC academic CPU baselines.
- DONE: current quick smoke inputs no longer emit `Unused ParmParse` warnings.
- PARTIAL: academic PeleC GPU dry-run for `examples/academic/detonation_znd_gpu` parses successfully, but full build/run remains unverified.
- PARTIAL: `examples/academic/deton_cpu_build` is marked stale in-place and recorded in `docs/codex_audit/CASE_INVENTORY.md`; it still needs repair or removal before release.
- PARTIAL: dependency provenance is documented in `docs/codex_audit/DEPENDENCY_AUDIT.md`, but external symlink/shared-worktree layout is still not release-grade.

