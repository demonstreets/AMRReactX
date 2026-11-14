# DataverseNO AMR Source Projection Contract

Status: `PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-CONTRACT`

## Summary

- Contract ready: `True`
- Current projection: single-level cell-centered = `True`
- Experimental radius: `0.0023` m
- Current full-channel min dx: `0.024999999999999998` m
- Recommended refinement ratio from dx=0.025 m: `16`
- Recommended finest dx: `0.0015624999999999999` m
- Strict blocker cleared: `False`

## Required Acceptance

- `source_projected_only_on_finest_available_level`
- `coarse_cells_covered_by_fine_level_receive_zero_source`
- `sum_active_volume_over_all_levels_counts_each_physical_cell_once`
- `source_mass_integral_conserved_across_amr_regrid`
- `gpu_mpi_parity_for_projected_source_mass`
- `dataverse_agreement_not_cleared_by_contract_alone`

## Notes

- The current h2_leak_3d source uses cell-centered active volume on the GeometryData passed to modify_ext_sources.
- A strict AMR implementation must normalize over the finest uncovered cells only, avoiding coarse/fine double counting.
- The contract recommends at least 16x refinement from dx=0.025 m so the 2.3 mm Dataverse orifice radius is represented by at least one finest cell radius.
- Passing this contract is a precondition for a future longer Dataverse plume-shape agreement run; it does not clear the strict blocker by itself.
