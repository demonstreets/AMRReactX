# Academic Gas Detonation Type A Review

Review ID: `academic_gas_detonation`
Coverage Type: `type_a_module_review`
Independent reviewer: Halley, independent read-only subagent review on 2026-07-29.
Reviewer source review ID: `TYPEA-ACD-GAS-DETONATION-LOCAL-20260729`
Verdict: `CHANGES_REQUESTED`

## Scope

This Type A review covers the academic gas detonation implementation and evidence for ACD-01, ACD-02, ACD-03, ACD-08, and the gas-detonation portion of QLT-03. The review was performed against the local archived tree under `remote_sync/home/cj/my-pele` without modifying files.

## Critical Issues

1. The 2D, 3D, and detonation-front AMR subreports are not fully locally re-verifiable from the archived mirror. Their JSON evidence paths point to `/home/cj/my-pele/...`; parent readiness verification checks subreport JSON files but does not recursively verify referenced manifests, run logs, validation logs, input decks, or plotfile evidence.

2. Some rerun-critical source/input artifacts are not complete in the local archive. The runners depend on detonation case directories and WENO implementation files that were not all visible in the mirror checked by the reviewer, which blocks independent reconstruction from the archive alone.

3. The current detonation reference claims remain smoke/self-consistency level, not full physical reference validation. Existing validators check finite fields, positive density/temperature, front motion, broad speed windows, mass/species closure, and H2O response, but do not yet check CJ/ZND speed, induction length, reaction-zone resolution, cell size, literature/experimental benchmark agreement, or fully cellular 3D detonation structure.

4. QLT-03 gas-detonation review coverage is now documented by this review, but the review verdict is not a closure verdict. The remaining gaps must stay visible in traceability.

## Warnings

- WENO5 evidence is useful for ACD-01 and QLT-03, but it mainly covers scalar/cell-average reconstruction. It does not yet cover full PeleC characteristic projection, reacting detonation shocks, WENO-vs-PPM solution comparison, AMR coarse-fine boundaries, or GPU execution paths.
- Chemistry evidence is stronger than the detonation-physics evidence, but the compiled rate-kernel equivalence report is limited to the CPU LiDryer path; GPU source-rate equivalence remains open.
- AMR front validation demonstrates refinement coverage of the thermal front, but does not yet prove detonation reaction-zone error control or robust tagging efficiency.
- The 2D front-speed spread gate is broad enough for a smoke/self-consistency gate, not a strict convergence claim.

## Evidence Checked

- `tools/write_academic_gas_detonation_readiness_report.py`
- `tools/write_academic_weno5_convergence_validation_report.py`
- `tools/write_academic_gas_2d_detonation_reference_report.py`
- `tools/write_academic_gas_3d_detonation_reference_report.py`
- `tools/write_academic_gas_detonation_front_amr_validation_report.py`
- JSON and Markdown evidence under `docs/codex_audit/evidence/academic_gas_*`
- `test/unit/test_pelec_weno.cpp`
- `external/PeleC/Source/Hydro.cpp`
- `external/PeleC/Source/MOL.cpp`
- `external/PeleC/Source/Godunov.H`

## Residual Gaps

- Archive-relative, locally verifiable evidence paths for all detonation subreports.
- Complete archival of detonation case directories, input decks, build metadata, and WENO implementation files needed for independent reruns.
- CJ/ZND or literature benchmark checks with explicit tolerances.
- Full-flow WENO detonation comparisons and AMR coarse-fine/front-tagging accuracy tests.
- GPU chemistry/source-rate equivalence if GPU detonation readiness is later claimed.
