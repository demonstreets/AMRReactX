# 2026-07-23 Real CAD Cleanup Gate

## Scope

Engineering production readiness still contained the blocker:

```text
geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup
```

The existing campaign manifest correctly identified the current geometry
coverage as synthetic tank-farm/STL regression evidence, but there was no strict
input path for real plant/vendor/as-built CAD cleanup evidence.

## Change

`tools/write_engineering_campaign_manifest.py` now accepts:

```text
--real-cad-cleanup-manifest <json>
```

The optional manifest is validated before it can upgrade geometry evidence from
`synthetic_obstacle_regression` to `real_cad_cleanup`.

Required real-CAD evidence fields:

- `schema_version = 1`
- `dataset_type = engineering_real_cad_cleanup_evidence`
- Matching `campaign`
- `status = PASS`
- `synthetic = false`
- `cad_source_is_real = true`
- `source_type` in `owner_operator_cad`, `as_built_cad`, `vendor_cad`, or
  `plant_cad`
- Provenance with `title` and `owner_or_supplier`
- At least one geometry with source CAD and cleaned geometry file hashes
- Cleanup checks for declared units, closed/watertight surface,
  nondegenerate elements, positive volume/area, and finite bounding boxes

To clear the production blocker, the evidence must also be marked as a
large-layout campaign and include at least three real CAD geometries.

## Verification

Isolated schema self-test directory:

```text
docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_schema_20260723
```

Positive/default checks:

```text
CAD_GATE_OK default_no_cad_campaign_manifest.json clears= False tier= synthetic_obstacle_regression count= 0
CAD_GATE_OK selftest_real_cad_campaign_manifest.json clears= True tier= real_cad_cleanup count= 3
```

Negative guards:

```text
CAD_GUARD_OK synthetic manifest rejected
CAD_GUARD_OK large-layout geometry-count guard rejected
```

The self-test STL/CAD files are synthetic and exist only to prove the schema and
guard behavior. They are not production evidence and are not wired into the
official campaign manifest.

## Current Production Meaning

The official campaign manifest still correctly reports:

- `geometry_evidence_tier = synthetic_obstacle_regression`
- `synthetic_tank_farm_evidence = true`
- `synthetic_stl_pipeline_evidence = true`
- `clears_real_cad_cleanup_blocker = false`

This change adds a strict, reproducible path to clear the CAD blocker when real
plant/vendor/as-built CAD cleanup evidence is available.
