# HySafe SBEPV5 D27 Literature Metric Preflight

Status: `PASS-SBEPV5-D27-LITERATURE-METRIC-PREFLIGHT`
Clears reference-data blocker: `False`
Ready for reference agreement consumption: `False`

## Metric Anchors

- `gas09_time_to_15pct_h2_s`: `[16.0, 19.0]`
- `gas10_time_to_15pct_h2_s`: `[17.0, 20.0]`
- `gas12_late_rise_qualitative`: `Gas12 begins to rise much later than Gas09 and Gas10`
- `gas09_gas10_sensitive_buoyant_jet_region`: `Gas09 and Gas10 are the most sensitive positions for the baffle-split buoyant jet`

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `public_source_triage_ready` | `PASS` | docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/external_plume_public_source_triage_report.json |
| `digitization_preflight_ready` | `PASS` | docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724/sbepv5_d27_digitization_preflight_report.json |
| `gas09_arrival_metric_available` | `PASS` | reported interval 16-19 s to 15 vol% H2 |
| `gas10_arrival_metric_available` | `PASS` | reported interval 17-20 s to 15 vol% H2 |
| `full_timeseries_still_missing` | `MISSING` | Original Excel or accepted digitized Gas01..Gas12 concentration time series is still required. |

## Missing Artifacts

- `experimental_timeseries.csv`: ingest original Excel or reviewed digitized curves for Gas01..Gas12 through at least 120 s
- `literature_metric_acceptance_overlay.json`: after program sensor probes exist, compare Gas09/Gas10 arrival-time metrics to reported intervals

## Limitations

- The metric anchors are literature-level checks, not a replacement for local experimental time series.
- This report cannot clear the external plume-shape blocker without ingested coordinates, baffle geometry, and sensor histories.
