# Engineering H2 Reference Threshold Agreement

Status: `PASS-REFERENCE-THRESHOLD-AGREEMENT`

Agreement tier: `reference_threshold_agreement`
Threshold reference agreement: `True`
External plume-shape dataset agreement: `False`
External consequence dataset agreement: `False`
Field/wind-tunnel dataset agreement: `False`
Clears reference-data blocker: `False`

## Summary

- `ranks`: `8`
- `threads_per_rank`: `2`
- `max_step`: `120`
- `base_cell_count`: `221184`
- `amr_equivalent_fine_cell_count`: `1769472`
- `cloud_rel_diff`: `0.0159761211`
- `peak_rel_diff`: `0.00155533247`
- `baseline_peak_x`: `0.186721493`
- `amr_peak_x`: `0.186431079`
- `baseline_lel_cloud_volume`: `0.0257523148`
- `amr_lel_cloud_volume`: `0.0253408927`
- `amr_final_flammable_planes`: `14`
- `plume_observation_metric_count`: `26`
- `all_threshold_checks_passed`: `True`
- `external_plume_metric_count`: `0`
- `external_plume_all_metrics_passed`: `False`

## Reference Sources

- NOAA CAMEO Chemicals HYDROGEN datasheet: https://cameochemicals.noaa.gov/chemical/8729 (H2 Lower Explosive Limit 4% and Upper Explosive Limit 75% by volume.)
- NOAA ORR Flammable Levels of Concern: https://response.restoration.noaa.gov/oil-and-chemical-spills/chemical-spills/resources/flammable-levels-concern.html (ALOHA default flammable LOCs: 60% LEL red zone and 10% LEL yellow zone.)
- NIST glossary: Flammable Limit: https://www.nist.gov/glossary-term/24026 (Flammable limits are expressed as fuel volume percent in air.)

## Limitations

- This is an engineering threshold-agreement report, not external field-test or wind-tunnel plume validation.
- It verifies H2 LEL/UEL thresholds, ALOHA-style LOC interpretation, positive flammable-cloud metrics, and AMR-vs-baseline drift on maintained large-grid evidence.
- It does not clear the reference-data blocker by itself; experimental/literature plume-shape and consequence comparisons remain required.
