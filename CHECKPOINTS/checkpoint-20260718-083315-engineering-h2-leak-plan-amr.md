# Checkpoint: engineering H2 leak dynamic plan-AMR gate

Date: 2026-07-18 08:33:15 UTC

## Scope

Priority remains engineering production-readiness for large-scale gas leak / fire / detonation-adjacent workflows. This slice focused on moving the H2 leak AMR evidence beyond static near-field refinement into a first dynamic plan-AMR comparison driven by H2 species gradients.

## Changes

- Added `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh`.
- Hardened `tools/validate_h2_leak_plume_history.py` so dynamic AMR histories may legitimately report changing composite grid shapes over time.
- Hardened `tools/amrex_reader.py` for sparse fine-patch AMR composite overlays while preserving single-level uncovered-cell rejection.
- Fixed 3D FAB singleton-dimension squeezing in `tools/amrex_reader.py`.
- Added sparse-AMR and 3D singleton-dimension coverage to `tools/test_amrex_reader_multibox.py`.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`.

## Evidence

- Dynamic open-domain H2 plan-AMR comparison: `/tmp/codex_h2_leak_open_domain_plan_amr_sparse_20260718/plan_amr_compare_summary.csv`.
- PASS metrics: `plan_species_gradient=2.0e-2`, `amr_finest_level=1`, `amr_finest_fabs=16`, `regrid_count=49`, `cloud_rel_diff=7.85340319e-02`, `peak_rel_diff=4.21517687e-02`, `centroid_abs_diff=3.27653000e-04`, `downstream_abs_diff=5.61330700e-03`.
- Dynamic AMR history: `grid_shapes=[(32, 16, 16), (64, 32, 32)]`, `mass_ratioN=1.00000057e+00`.
- AMR overhead: `/tmp/codex_h2_leak_open_domain_plan_amr_sparse_20260718/amr_overhead_summary.csv`, PASS with `mean_ncells_ratio=1.68921875e+00`, `advance_seconds_ratio=2.28212692e+00`, `final_plotfile_bytes_ratio=2.11514628e+00`.
- Log scan over `/tmp/codex_h2_leak_open_domain_plan_amr_sparse_20260718`: zero failure markers across 12 log files.
- Syntax regression: `python3 -m py_compile tools/amrex_reader.py tools/validate_h2_leak_plume_history.py tools/summarize_h2_leak_amr_overhead.py tools/test_amrex_reader_multibox.py` PASS.
- Reader regression: `python3 tools/test_amrex_reader_multibox.py` PASS with `sparse_amr=1`.
- Path audit: `python3 tools/check_machine_local_paths.py --strict` PASS, `scanned_files=948`.
- CTest: `ctest --test-dir build-codex-smoke --output-on-failure` PASS, 22/22.

## Remaining engineering gaps

- Dynamic AMR has one H2 species-gradient threshold smoke only; threshold sweeps, refinement efficiency, convergence, and production scaling remain open.
- Real CAD / large-layout tank-farm dynamic AMR campaigns remain open.
- Long-time production-size leak/fire campaigns and reference-data validation remain open.
- Full real-gas EOS, thermal cooldown, distributed pipe-network waves, and complex valve-network transients remain incomplete.
