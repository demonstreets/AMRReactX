# Academic Two-Phase CSF and Bubble-Rise Review Fixes

Date: 2026-07-29

## Scope

This audit records follow-up work from the independent Type A two-phase review. The review found that CSF source coupling lacked demonstrated total-energy consistency and that the bubble-rise report over-cleared the broad QLT-03 bubble-rise gap using only a short-time low-CFL run.

## Changes

- `src/academic/twophase/CSF.H` now exposes `csf_force_work`, a device-safe helper for the total-energy source contribution `F dot u`.
- `external/PeleC/Source/Hydro.cpp` now adds the CSF work term to `UEDEN` whenever the CSF momentum source is added.
- `test/unit/test_csf.cpp` now checks the CSF source-work helper in the maintained `csf_smoke` unit test.
- `tools/write_academic_twophase_bubble_rise_validation_report.py` now separates:
  - `clears_qlt_03_short_time_bubble_response_gap`
  - `clears_qlt_03_canonical_long_time_bubble_rise_gap`
  - `clears_qlt_03_bubble_rise_gap`
- `tools/write_engineering_h2_master_plan_traceability_report.py` now treats ACD-06 as `PARTIAL` until a coupled capillary/static-droplet CFD benchmark exists, and treats bubble-rise as short-time evidence only.

## Verification Intent

The short-time bubble-rise gate can still pass as a stability and buoyancy-response smoke/validation gate. It must not be used as proof of canonical long-time bubble-rise behavior because longer probes have shown non-finite or negative-internal-energy failures.

## Remaining Gaps

- Coupled capillary-wave or solver-coupled static-droplet validation for CSF.
- Long-time positive/finite bubble-rise validation.
- External or MMS/reference validation for two-phase interface dynamics.
