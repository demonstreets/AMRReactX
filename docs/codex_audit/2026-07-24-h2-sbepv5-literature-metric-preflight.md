# H2 SBEPV5 Literature Metric Preflight

Date: 2026-07-24

## Purpose

Add a machine-checkable preflight for SBEPV5 D27 literature-level response metrics. This
records public-paper metric anchors that are useful for later reference-agreement checks, while
preserving the production blocker until local experimental coordinates, baffle geometry, and
time-series data are ingested.

## Added Evidence

- `tools/write_engineering_h2_sbepv5_literature_metric_preflight_report.py`
- `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_literature_metric_preflight_20260724/sbepv5_d27_literature_metric_preflight_report.json`
- `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_literature_metric_preflight_20260724/sbepv5_d27_literature_metric_preflight_report.md`

## Metric Anchors

- Gas09 time to 15 vol% H2: 16-19 s
- Gas10 time to 15 vol% H2: 17-20 s
- Gas12 later rise than Gas09/Gas10
- Gas09/Gas10 marked as priority sensors for buoyant jet and baffle interaction

## Production Rule

This report must not clear `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.
It is an intermediate evidence layer. Production clearance still requires:

- original or reviewed digitized Gas01..Gas12 concentration histories,
- exact Gas01..Gas12 coordinates,
- exact baffle geometry,
- generated external plume dataset JSON,
- official `h2_reference_agreement_report` with external plume-shape agreement.
