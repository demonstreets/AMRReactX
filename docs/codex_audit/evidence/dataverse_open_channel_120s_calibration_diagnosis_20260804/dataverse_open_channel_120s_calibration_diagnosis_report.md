# DataverseNO 120s Calibration Diagnosis

- Status: `DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-120S-CALIBRATION-GAPS`
- 120 s agreement status: `QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING`
- Source radius ratio vs experiment: `34.78260869565217`
- Source area ratio vs experiment: `1209.8298676748582`
- Source center z offset: `-0.10000000000000009` m
- Minimum active radius at reference source on current grid: `0.04330127018922188` m
- Severe peak errors: `20`
- Severe over/under prediction: `12` / `8`
- Infinite LFL arrival errors: `5`
- Strict external plume blocker cleared: `False`

## Next Calibration Inputs

- `prob.leak_zc`: `0.8`
- `minimum_active_radius_at_reference_source_on_current_grid_m`: `0.04330127018922188`
- `prob.leak_radius_options_m_current_grid`: `[0.05, 0.06, 0.08]`
- `prob.leak_radius_options_m_requires_refinement_or_cell_projection`: `[0.025, 0.04]`
- `prob.leak_rate`: `0.0009152681907312`
- `amr.n_cell_options`: `['232 36 32', '174 27 24']`
- `geometry_required_change`: `replace eb2.geom_type=all_regular with encoded DataverseNO internal component/obstacle bounds before strict geometry parity`
- `scoring_policy`: `re-run 45 s first for LFL timing, then 120 s for peak-window agreement after source-height/radius changes`
