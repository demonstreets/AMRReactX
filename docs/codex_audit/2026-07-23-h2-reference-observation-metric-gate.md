# 2026-07-23 H2 Reference Observation Metric Gate

## Scope

The external H2 plume blocker requires case-matched field, wind-tunnel, or
literature-digitized plume evidence. The code already produced plume
observation outputs, but the official reference-agreement gate could only
compare coarse summary metrics. That was too weak for benchmark datasets based
on sensor histories or flammable-cloud extents.

## Change

`tools/write_engineering_h2_reference_agreement_report.py` now reads the
official plume observation report when present and exposes machine-comparable
`observation_*` metric keys for external datasets, including:

- global flammable cloud extent and volume metrics
- per-sensor peak H2 mole fraction
- per-sensor final H2 mole fraction
- per-sensor LFL arrival time when present

The external dataset validator now also checks that a metric key is compatible
with its declared `metric_type`. Examples:

- `plume_extent` must use flammable-cloud extent/location observation keys.
- `sensor_concentration` / `concentration_peak` must use sensor concentration
  keys.
- `arrival_time` must use sensor arrival-time keys.
- `flammable_cloud_volume` must use cloud-volume keys.

This prevents a dataset from passing by declaring a shape metric while actually
comparing an unrelated scalar.

## Verification

Official reference report was regenerated and still remains:

`agreement_tier = reference_threshold_agreement`

`external_plume_shape_dataset_agreement = false`

It now records `plume_observation_metric_count = 26`.

Self-test evidence was generated under:

`docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/external_plume_observation_metric_selftest_20260723`

The self-test external dataset uses synthetic values copied from the current
observation report only to exercise the gate. It is not production external
evidence and is not written to the official report.

Guard verification rejects a dataset where
`observation_max_flammable_x` is declared as `arrival_time`.

## Current Status

This makes the external-plume blocker more actionable, but it still does not
clear it. The remaining requirement is a real case-matched external plume
dataset.
