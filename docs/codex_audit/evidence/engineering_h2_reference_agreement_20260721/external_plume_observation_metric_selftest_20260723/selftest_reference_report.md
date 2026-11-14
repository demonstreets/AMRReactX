# Engineering H2 Reference Threshold Agreement

Status: `PASS-REFERENCE-THRESHOLD-AGREEMENT`

Agreement tier: `external_plume_shape_dataset_agreement`
Threshold reference agreement: `True`
External plume-shape dataset agreement: `True`
External consequence dataset agreement: `False`
Field/wind-tunnel dataset agreement: `True`
Clears reference-data blocker: `True`

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
- `external_plume_metric_count`: `3`
- `external_plume_all_metrics_passed`: `True`

## Reference Sources

- NOAA CAMEO Chemicals HYDROGEN datasheet: https://cameochemicals.noaa.gov/chemical/8729 (H2 Lower Explosive Limit 4% and Upper Explosive Limit 75% by volume.)
- NOAA ORR Flammable Levels of Concern: https://response.restoration.noaa.gov/oil-and-chemical-spills/chemical-spills/resources/flammable-levels-concern.html (ALOHA default flammable LOCs: 60% LEL red zone and 10% LEL yellow zone.)
- NIST glossary: Flammable Limit: https://www.nist.gov/glossary-term/24026 (Flammable limits are expressed as fuel volume percent in air.)

## External Plume Shape Comparison

- Dataset: `observation metric ingestion selftest, not production evidence`
- Source type: `literature_digitized`
- Source: `Synthetic selftest values copied from observation report`

| Metric | Simulation | Reference | Rel. error | Passed |
| --- | ---: | ---: | ---: | --- |
| `max flammable x` | `0.984375` | `0.984375` | `0.0` | `True` |
| `max cloud volume` | `0.0382080078125` | `0.0382080078125` | `0.0` | `True` |
| `sensor peak` | `0.1405690665313` | `0.1405690665313` | `0.0` | `True` |

## Limitations

- This report includes external plume-shape metric agreement.
- It verifies H2 LEL/UEL thresholds, ALOHA-style LOC interpretation, positive flammable-cloud metrics, and AMR-vs-baseline drift on maintained large-grid evidence.
- It clears the reference-data blocker only for the external plume-shape metrics declared in the dataset; external consequence calibration remains separate.
