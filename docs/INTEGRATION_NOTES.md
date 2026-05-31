# AMRReactX integration notes

Integration date: 2026-05-31
Correction update: 2026-05-31

## Canonical project folder

The consolidated AMRReactX project now lives at:

```text
C:\Users\demon\Documents\Codex\AMRReactX
```

## Sources reviewed

- `C:\Users\demon\Documents\Codex\2026-05-31\amrreactx-stage-1\work\AMRReactX`
  - Chosen as the canonical project source after the correction audit.
  - Despite the folder name, this is the newest development line and contains Stage 3.1/3.2/3.4 AMR hierarchy, tagging, maintained level-1 advance, and restriction-update work.
  - Its git HEAD at correction time was `5bc4421 Add AMR restriction consistency diagnostics`.
  - The source files, inputs, tools, top-level project files, and verification CSV histories were hash-checked against the consolidated project after synchronization.
- `C:\Users\demon\Documents\Codex\2026-05-31\amrreactx-cfd-plan-plan\work\AMRReactX`
  - Initially mistaken as the canonical project source.
  - This is an older Stage 2.4-era line and is superseded by the `amrreactx-stage-1` working tree.
- `C:\Users\demon\Documents\Codex\2026-05-31\amrreactx-cfd-plan-plan\outputs\amrreactx_stage2_4_progress.md`
  - Copied into `docs/amrreactx_stage2_4_progress.md`.
- `C:\Users\demon\Documents\Codex\2026-05-31\amrreactx-stage-1\outputs`
  - Copied into `docs/visual_outputs`.
- `C:\Users\demon\Documents\Codex\2026-05-31\soul-md\soul.md`
  - Copied into `soul.md` at the project root.
- `C:\Users\demon\Documents\Codex\2026-05-30\new-chat-2\AMRReactX`
  - Preserved as an early prototype under `legacy/2026-05-30-prototype`.
  - Its `build` directory and `plt_mini_leak` output were not copied.

## Integration policy

The `2026-05-31\amrreactx-stage-1\work\AMRReactX` version is treated as the active codebase. The `2026-05-30` version is kept only as a historical prototype because it is a smaller single-source-stage project and should not overwrite the newer modular architecture.

Build directories and AMReX plotfile outputs were intentionally excluded from the consolidated folder:

- `build`
- `build-stage1`
- `build-stage2-current`
- `plt_*`

These are generated artifacts and can be recreated from source and inputs. The lightweight verification history CSV files were retained because they are useful audit records.

## Current git status after integration

The copied repository preserves the working-tree state from the latest 2026-05-31 source. At correction time, these source changes were already present:

- Modified:
  - `README.md`
  - `src/AMR/Hierarchy.H`
  - `src/AMR/Hierarchy.cpp`
  - `src/Core/State.H`
  - `src/Core/ProblemSetup.cpp`
  - `src/IO/Diagnostics.H`
  - `src/IO/Diagnostics.cpp`
  - `src/main.cpp`
  - `tools/check_history.py`
  - `tools/run_stage3_verification.sh`
- Untracked:
  - `inputs/verify_level1_advance_3d.in`
  - `inputs/verify_level1_restriction_update_3d.in`

The integration itself added:

- `docs/`
- `legacy/`
- `soul.md`

No original source directories were deleted or modified during consolidation.
