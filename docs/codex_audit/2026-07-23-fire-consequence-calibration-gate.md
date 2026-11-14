# 2026-07-23 Fire Consequence Calibration Gate

## Scope

Engineering priority work continued on the H2 tank/pipe leak, ignition, fire,
radiation, and overpressure consequence chain. The existing fire consequence
report was intentionally screening-only, which is correct for weak evidence but
left no strict path for upgrading to production-grade calibrated evidence.

## Change

`tools/write_engineering_h2_fire_consequence_metrics_report.py` now accepts an
optional `--calibration-dataset-json` input. The default report remains
screening-only unless an external calibration dataset is supplied and passes all
gate checks.

The calibration dataset must provide:

- `schema_version = 1`
- `dataset_type = h2_fire_consequence_calibration_agreement`
- A matching `case`
- Source metadata with `title` and either `url` or `doi`
- `source_type` in `field_test`, `wind_tunnel`, `literature_digitized`, or
  `validated_reference_model`
- At least two metric comparisons
- Both `radiation` and `overpressure` metric families to clear the production
  blocker
- Positive absolute or relative tolerance on every metric
- Passing reference agreement on every metric

Only `field_test`, `wind_tunnel`, or `literature_digitized` sources can clear
`clears_calibrated_fire_consequence_blocker`. A
`validated_reference_model` dataset can be recorded but cannot clear the
production blocker by itself.

## Verification

Existing official screening report still verifies:

```text
engineering_h2_fire_consequence_metrics VERIFY-PASS
status=PASS-SCREENING
```

Positive schema self-test:

```text
engineering_h2_fire_consequence_metrics VERIFY-PASS
status=PASS-CALIBRATED-CONSEQUENCE-AGREEMENT
SELFTEST_CLEARS True
SELFTEST_FAMILIES overpressure,radiation
```

Negative guard tests:

```text
GUARD_OK guard_validated_reference_model_report.json PASS-SCREENING False
GUARD_OK guard_radiation_only_report.json PASS-SCREENING False
```

The self-test values are synthetic and copied from the current screening report.
They prove the schema and verifier path only; they are not production evidence.

## Current Production Meaning

This change improves the engineering consequence chain by adding the missing
strict data-ingestion path for real calibration evidence. It does not by itself
clear the production blocker. The official report remains:

- `status = PASS-SCREENING`
- `clears_calibrated_fire_consequence_blocker = false`

The remaining work is to run or digitize a real H2 fire/radiation/overpressure
reference case with matching scenario metadata, then feed it through this gate.
