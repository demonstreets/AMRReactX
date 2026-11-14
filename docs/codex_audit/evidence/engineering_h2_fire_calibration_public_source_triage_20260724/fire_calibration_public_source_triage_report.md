# Engineering H2 Fire Calibration Public Source Triage

Status: `PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE`
Clears fire-consequence blocker: `False`

## Radiation Candidates

- `mdpi_jet_fire_2024`: https://www.mdpi.com/2076-3417/14/16/7098
- `sandia_cryogenic_h2_jet_fire_2019`: https://doi.org/10.1016/j.ijhydene.2018.08.107
- `bam_large_scale_h2_jet_flames_2025`: https://hysafejournal.org/en/articles/10.58895/hysafe.27

## Overpressure Candidates

- `hyindoor_low_strength_enclosure_2017`: https://h2tools.org/bibcite/reference/3540
- `container_deflagration_2020`: https://doi.org/10.1016/j.ijhydene.2020.04.036

## Missing Artifacts

- `calibration_metadata.json`: select one radiation source and one overpressure source, record URL/DOI, source hashes, and case-alignment booleans
- `radiation_metrics.csv`: digitize or obtain heat-flux measurements with distance, tolerance, and source basis
- `overpressure_metrics.csv`: digitize or obtain peak overpressure measurements with distance, tolerance, and source basis
- `calibrated_fire_consequence_report`: run the official fire consequence report against a generated calibration dataset JSON

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `radiation_public_source_candidates_available` | `PASS` | none |
| `overpressure_public_source_candidates_available` | `PASS` | none |
| `calibration_metadata_local` | `MISSING` | No production calibration_metadata.json with source hashes and case-alignment booleans is local. |
| `radiation_metrics_local` | `MISSING` | No local radiation_metrics.csv has been ingested. |
| `overpressure_metrics_local` | `MISSING` | No local overpressure_metrics.csv has been ingested. |
| `calibrated_consequence_report` | `MISSING` | Official fire consequence report has not been rerun with a calibration dataset JSON. |

## Limitations

- This report identifies candidate public calibration sources only; it does not digitize or ingest calibration data.
- Radiation and overpressure data families may come from different experiments, but production credit requires explicit case-alignment metadata.
- The fire-consequence blocker remains until calibrated radiation and overpressure agreement reports pass.
