# AMRReactX Stage 2.4 Progress

Working copy:
`C:\Users\demon\Documents\Codex\2026-05-31\amrreactx-cfd-plan-plan\work\AMRReactX`

Completed in this pass:

- Reviewed the stored AMRReactX CFD development plan and target architecture.
- Copied the latest Stage 2.3 working tree into this session's workspace.
- Added `source_total_rate` as an optional engineering source parameter.
- Preserved backward compatibility: negative `source_total_rate` keeps the old `source_strength` behavior.
- Normalized `box` and `gaussian` source strengths during parameter parsing.
- Added `inputs/verify_source_total_rate_3d.in`.
- Extended `tools/run_stage1_verification.sh` and `tools/check_history.py`.
- Updated README and local AMRReactX memory notes.

Verification:

Command:

```bash
BUILD_DIR=build-stage2-current NP=2 bash tools/run_stage1_verification.sh
```

Result: full Stage 1/2 verification suite passed under WSL Ubuntu-24.04 with AMReX 26.05 and 2 MPI ranks.

New verification case:

- `source_total_rate = 0.2`
- final time `t = 0.4`
- final `source_rate = 0.2`
- final `mass = 0.08`
- final `injected = 0.08`
- final `balance_error = -1.679212325e-15`
