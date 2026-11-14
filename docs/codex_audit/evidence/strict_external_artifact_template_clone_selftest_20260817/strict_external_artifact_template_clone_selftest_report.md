# Strict External Artifact Template Clone Selftest

- Status: `PASS-STRICT-EXTERNAL-ARTIFACT-TEMPLATE-CLONE-SELFTEST`
- Clone cases: `14`
- Rejected clones: `14`
- Accepted clones: `0`
- Strict completion allowed: `False`

This negative selftest simulates every strict target artifact as a byte-for-byte copy of its template.
All such cases must be rejected and no target artifacts are created or copied by this selftest.

## Cases

- `external_plume` / `external_plume.baffle_geometry`: `REJECT` `target artifact bytes are identical to the verified template`
- `external_plume` / `external_plume.dataset_metadata`: `REJECT` `target artifact bytes are identical to the verified template`
- `external_plume` / `external_plume.digitization_uncertainty_record`: `REJECT` `target artifact bytes are identical to the verified template`
- `external_plume` / `external_plume.experimental_timeseries`: `REJECT` `target artifact bytes are identical to the verified template`
- `external_plume` / `external_plume.sensor_coordinates`: `REJECT` `target artifact bytes are identical to the verified template`
- `fire_calibration` / `fire_calibration.calibration_metadata`: `REJECT` `target artifact bytes are identical to the verified template`
- `fire_calibration` / `fire_calibration.fire_calibration_digitization_uncertainty`: `REJECT` `target artifact bytes are identical to the verified template`
- `fire_calibration` / `fire_calibration.fire_calibration_source_registry`: `REJECT` `target artifact bytes are identical to the verified template`
- `fire_calibration` / `fire_calibration.overpressure_metrics`: `REJECT` `target artifact bytes are identical to the verified template`
- `fire_calibration` / `fire_calibration.radiation_metrics`: `REJECT` `target artifact bytes are identical to the verified template`
- `real_cad` / `real_cad.real_cad_boundary_tags`: `REJECT` `target artifact bytes are identical to the verified template`
- `real_cad` / `real_cad.real_cad_cleanup_manifest`: `REJECT` `target artifact bytes are identical to the verified template`
- `real_cad` / `real_cad.real_cad_cleanup_quality_record`: `REJECT` `target artifact bytes are identical to the verified template`
- `real_cad` / `real_cad.real_cad_data_room_index`: `REJECT` `target artifact bytes are identical to the verified template`
