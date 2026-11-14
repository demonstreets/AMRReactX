# H2 Real-CAD Data-Room Index Validation

Date: 2026-07-24

## Purpose

Strengthen the real-CAD production blocker path by validating controlled data-room CSVs, not
only the cleanup manifest. This allows owner/operator CAD intake evidence to be checked as soon
as real files are staged.

## Updated Gate

- `tools/write_engineering_h2_real_cad_intake_preflight_report.py`

## New Checked Artifacts

- `real_cad_data_room_index.csv`
- `real_cad_cleanup_quality_record.csv`

## Rules

`real_cad_data_room_index.csv` must include source and cleaned geometry rows with:

- file role,
- label,
- relative path,
- SHA-256,
- source type,
- revision,
- owner or supplier.

At least three labels must have both `source_cad` and `cleaned_geometry` rows.

`real_cad_cleanup_quality_record.csv` must include at least three geometry records with true
cleanup checks, bounding-box fields, tool or method, and reviewer.

## Production Rule

This change does not clear `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`.
It makes the real-CAD intake gate stricter and more reproducible once actual controlled CAD
artifacts are supplied.
