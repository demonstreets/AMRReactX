# 2026-07-23 H2 External Plume Dataset Ingestion Gate

## Scope

Engineering production-readiness blocker:
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

The existing H2 reference report correctly verified LEL/UEL threshold agreement
and AMR-vs-baseline consistency, but it had no machine-verifiable path for
case-matched external plume-shape data.

## Change

`tools/write_engineering_h2_reference_agreement_report.py` now accepts an
optional:

```text
--external-plume-dataset-json <path>
```

The optional dataset must satisfy all of the following before the report can
set `external_plume_shape_dataset_agreement = true`:

- `schema_version = 1`
- `dataset_type = external_h2_plume_shape_agreement`
- `case` exactly matches the underlying scout report case
- source metadata includes a title and either URL or DOI
- source type is one of:
  - `field_test`
  - `wind_tunnel`
  - `literature_digitized`
  - `validated_reference_model`
- at least two metrics are supplied
- every metric names an existing simulation/reference summary key
- every reference value is finite
- every metric defines at least one relative or absolute tolerance
- every metric passes its tolerance
- the dataset file is recorded in `evidence_files` with SHA-256

Without `--external-plume-dataset-json`, the official report remains a
threshold-only agreement report and does not clear the production blocker.

## Verification

Syntax and legacy-report verification:

- `python3 -m py_compile tools/write_engineering_h2_reference_agreement_report.py`
- `python3 tools/write_engineering_h2_reference_agreement_report.py --verify-json docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json`

Both passed.

Schema self-test evidence:

- dataset:
  `docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/external_plume_schema_selftest_20260723/selftest_dataset.json`
- generated report:
  `docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/external_plume_schema_selftest_20260723/selftest_reference_report.json`
- verifier:
  `VERIFY-PASS`

The self-test uses synthetic reference values copied from the current scout
summary only to exercise the validation path. It is not production external
evidence and is intentionally not written to the official reference report.

## Current Production Status

This change improves the production evidence pipeline but does not claim that
the external reference-data blocker is closed. A real external field-test,
wind-tunnel, or literature-digitized H2 plume-shape dataset still must be
matched to a corresponding simulation case and passed through this gate.
