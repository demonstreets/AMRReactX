# 2026-07-23 H2 External Plume Source Quality Gate

## Scope

The reference-agreement tool can now compare external datasets against plume
observation metrics. This created a new risk: a synthetic JSON with copied
simulation values and a placeholder URL could clear the external plume blocker.

## Change

`tools/write_engineering_h2_reference_agreement_report.py` now applies stricter
source-quality checks to external plume datasets by default:

- rejects synthetic/selftest/copied/not-production source metadata
- rejects reserved hosts such as `example.invalid`
- requires a real-looking DOI or public URL host
- requires `reference_basis` for every metric
- requires `digitization` metadata for `literature_digitized` datasets,
  including source figure/table and digitization method/operator/tool

Synthetic datasets are allowed only when the caller explicitly passes:

`--allow-synthetic-selftest`

That switch is for non-official validator selftests only.

## Verification

Official reference report still verifies and remains threshold-only:

- `external_plume_shape_dataset_agreement = false`
- `plume_observation_metric_count = 26`

Guard evidence:

- strict mode rejects a selftest dataset whose source uses synthetic wording
  and `example.invalid`
- selftest mode accepts the same dataset only with
  `--allow-synthetic-selftest`
- selftest mode still rejects a metric missing `reference_basis`

Evidence directory:

`docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/external_plume_source_quality_gate_20260723`

## Current Status

The external plume blocker remains open. This change makes the future blocker
closure harder to fake and more auditable.
