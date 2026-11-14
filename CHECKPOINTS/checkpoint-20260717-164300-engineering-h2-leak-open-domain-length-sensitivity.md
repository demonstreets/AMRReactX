# Checkpoint - Engineering H2 leak open-domain length sensitivity

> Date: 2026-07-17T16:43:00+08:00
> Agent: Codex
> Related items: ENG-06, ENG-09, ENG-10, ENG-11, QLT-03, QLT-04

## Summary

- Added a two-point open-domain H2 domain-length/outlet-margin gate that keeps grid spacing fixed, runs the maintained flammable-cloud chain on base and longer x domains, and verifies the flammable cloud and active H2 field are not outlet-clipped.
- Updated the production-readiness audit and smoke matrix to reflect the new outlet-margin evidence while preserving the verdict `NOT PRODUCTION READY`.

## Changed Files / Modules

- tools/codex_smoke_engineering_h2_leak_open_domain_length.sh
- docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md
- docs/codex_audit/SMOKE_MATRIX.md

## Verification

- CODEX_H2_LEAK_LENGTH_LOG_DIR=/tmp/codex_h2_leak_open_domain_length_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain_length.sh -> PASS
- bash -n tools/codex_smoke_engineering_h2_leak_open_domain_length.sh tools/codex_smoke_engineering_h2_leak_open_domain_radius.sh tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh -> PASS
- python3 tools/check_machine_local_paths.py --strict -> PASS scanned_files=921
- SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh -> PASS warnings=3

## Evidence Paths

- /tmp/codex_h2_leak_open_domain_length_20260717/length_summary.csv
- /tmp/codex_h2_leak_open_domain_length_20260717/base_domain/validation.log
- /tmp/codex_h2_leak_open_domain_length_20260717/base_domain/profile_validation.log
- /tmp/codex_h2_leak_open_domain_length_20260717/base_domain/hazard_summary.log
- /tmp/codex_h2_leak_open_domain_length_20260717/base_domain/hazard_planes.log
- /tmp/codex_h2_leak_open_domain_length_20260717/base_domain/hazard_timeseries.log
- /tmp/codex_h2_leak_open_domain_length_20260717/long_domain/validation.log
- /tmp/codex_h2_leak_open_domain_length_20260717/long_domain/profile_validation.log
- /tmp/codex_h2_leak_open_domain_length_20260717/long_domain/hazard_summary.log
- /tmp/codex_h2_leak_open_domain_length_20260717/long_domain/hazard_planes.log
- /tmp/codex_h2_leak_open_domain_length_20260717/long_domain/hazard_timeseries.log
- /tmp/codex_h2_open_domain_length_bashn_20260717.log
- /tmp/codex_h2_open_domain_length_path_audit_20260717.log
- /tmp/codex_h2_open_domain_length_preflight_20260717.log

## Key Metrics

- Base domain: `x_hi=2.0`, `nx=32`, `cloud_face_margin=1.18750000e+00`, `active_face_margin=1.06250000e+00`, `cloud_volume=2.14843750e-02`, `max_X=1.61483568e-01`.
- Long domain: `x_hi=2.5`, `nx=40`, `cloud_face_margin=1.68750000e+00`, `active_face_margin=1.56250000e+00`, `cloud_volume=2.14843750e-02`, `max_X=1.61483568e-01`.

## Known Limitations

- Coarse all-regular single-box smoke only; it is not a full inlet/outlet, atmospheric-boundary-layer, terrain, obstacle/tank-farm, or production-scale mesh campaign.
- Open-domain cases remain single-box because the lightweight reader does not yet stitch multi-box 3D plotfiles.
- The outlet-margin check covers this one wind/source setup; crosswind, calm release, orifice/tank-pressure, ignition/fire coupling, and long-time stability remain open.

## Git Status Snapshot

```text
?? docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md
?? docs/codex_audit/SMOKE_MATRIX.md
?? tools/codex_smoke_engineering_h2_leak_open_domain_length.sh
```
