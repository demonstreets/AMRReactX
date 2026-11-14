# Two Phase Foundation Type A Review

Review ID: `two_phase_foundation`
Coverage Type: `type_a_module_review`
Independent reviewer: Averroes, independent read-only subagent review on 2026-07-29.
Reviewer source review ID: `TYPE-A-TWOPHASE-ACD04-08-QLT03-20260729`
Verdict: `CHANGES_REQUESTED`

## Scope

This Type A review covers the academic two-phase and gas-liquid foundation implementation and evidence for ACD-04, ACD-05, ACD-06, ACD-07, ACD-08, and the two-phase portion of QLT-03. The review was performed against `remote_sync/home/cj/my-pele` without modifying files.

## Critical Issues

1. ACD-06 CSF coupled energy consistency is not demonstrated and appears incomplete in the coupled PeleC source path reviewed. The CSF force path adds momentum source terms, while an equivalent total-energy work term was not demonstrated in that path. The standalone CSF unit smoke verifies basic normals, curvature, and zero-force behavior, but not coupled total-energy consistency, capillary-wave behavior, or static-droplet pressure balance.

2. QLT-03 bubble-rise is over-cleared by the current report language. The maintained gate supports only short-time, low-CFL buoyancy-response stability. Longer-window probes in the same evidence package show negative internal energy or non-finite-cell failures, so this should not be called full bubble-rise validation.

3. Several `clears_acd_*` flags exceed the demonstrated physics. ACD-05 and ACD-07 are supported by short shock-droplet/spray cases with particle growth, surface-area response, finite derived fields, and species closure, but not by a closed gas+particle mass/energy budget or external/reference validation. The ACD-07 case is detonation-style, not a full cellular gas-liquid detonation validation.

## Warnings

- Rayleigh-Taylor evidence supports bounded alpha, mass conservation, and growth response, but does not yet prove full PLIC geometric interface transport accuracy in the integrated solver path.
- The current two-phase EOS uses simplified liquid-dominated interface-cell closure and pressure/sound-speed clamps. This is a stabilization scaffold rather than proof of thermodynamically consistent mixed-cell EOS.
- The HLLC path needs stronger positivity/robustness evidence for strong-shock gas-liquid cases.
- Some evidence manifests include machine-local absolute paths; archive-relative provenance would be stronger.

## Evidence Checked

- `tools/write_academic_twophase_rayleigh_taylor_validation_report.py`
- `tools/write_academic_twophase_interface_amr_validation_report.py`
- `tools/write_academic_droplet_euler_lagrange_validation_report.py`
- `tools/write_academic_spray_detonation_validation_report.py`
- `tools/write_academic_twophase_bubble_rise_validation_report.py`
- JSON and log evidence under `docs/codex_audit/evidence/academic_twophase_*`
- JSON and log evidence under `docs/codex_audit/evidence/academic_droplet_*`
- JSON and log evidence under `docs/codex_audit/evidence/academic_spray_*`
- `src/academic/twophase/*`
- `src/academic/vof/*`
- `examples/academic/bubble_rise/*`
- `examples/academic/rayleigh_taylor/*`
- `examples/academic/shock_droplet/*`
- `external/PeleC/Source/Godunov.H`
- `external/PeleC/Source/MOL.cpp`
- `external/PeleC/Source/PeleCUtilities.H`
- `external/PeleC/Source/Hydro.cpp`

## Residual Gaps

- Coupled CSF energy-budget test and capillary/static-droplet CFD benchmark.
- Long-time positive/finite bubble-rise validation.
- Gas+particle conservative mass, momentum, and energy budget for ACD-05 and ACD-07.
- External or MMS/reference validation for Rayleigh-Taylor, bubble rise, spray breakup, and spray detonation.
- Demonstrated PLIC reconstruction in the full solver update path, not only helper/unit coverage.
