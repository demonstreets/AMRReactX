# Case inventory

Updated: 2026-07-15

This inventory distinguishes maintained smoke baselines from stale or experimental case directories. It is not a full benchmark catalog.

## Maintained quick smoke baselines

| Area | Case | Entry point | Status |
| --- | --- | --- | --- |
| CMake/WENO | `test/unit/test_weno5.cpp` via top-level CMake | `tools/codex_smoke_all.sh` | Passing smoke. |
| PeleLMeX engineering | `examples/engineering/bfs_kepsilon` | `tools/codex_smoke_engineering_pelelmex.sh` | Builds GNU CPU and runs one step with `input.codex_smoke`. |
| PeleC academic | `examples/academic/detonation_2D` | `tools/codex_smoke_academic_pelec.sh` | Builds GNU CPU and runs one reacting CVODE step with `inputs.codex_smoke`. |

## Stale / do not auto-discover

| Path | Reason | Action before use |
| --- | --- | --- |
| `examples/academic/deton_cpu_build` | Broken `GNUmakefile -> GNUmakefile.cpu`; contains stale `3d.gnu.MPI.CUDA.EXE` object/config output and no source/input files. | Repair as a real case or remove. Do not include in automated build discovery. |
| `external/PeleLMeX_BAK_20260708` | Backup tree under `external`, not a live dependency. | Keep out of dependency/build discovery. |

## Experimental / not yet smoke-gated

The following areas remain outside the maintained quick gate until they have explicit inputs, build commands, and pass/fail evidence:

- GPU PeleC/PeleLMeX cases.
- Multi-rank MPI cases.
- Spray combustion examples.
- VOF/two-phase examples.
- C12H23 and ReactorNN examples.
- Long-running production or benchmark cases.
