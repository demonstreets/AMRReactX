# Academic Gas Detonation Archive Verifiability

Date: 2026-07-29

## Scope

This audit records the fix for the independent Type A review finding that the 2D, 3D, and detonation-front AMR gas-detonation reports were only directly verifiable on the original `/home/cj/my-pele` server path. The reports now resolve archived evidence paths through the active repository root and write repo-relative evidence paths when rebuilt.

## Changes

- `tools/write_academic_gas_2d_detonation_reference_report.py` now maps `/home/cj/my-pele/...` evidence references to the current repository root during verification and writes repo-relative evidence paths.
- `tools/write_academic_gas_3d_detonation_reference_report.py` now uses the same archive resolver and repo-relative evidence output.
- `tools/write_academic_gas_detonation_front_amr_validation_report.py` now uses the same archive resolver and repo-relative evidence output.
- `tools/write_academic_gas_detonation_readiness_report.py` now verifies embedded `evidence_files` hashes from the 2D, 3D, and detonation-front AMR subreports before it can regenerate readiness evidence.

## Verification Intent

The maintained solver gates remain separate from full academic certification. The reports can still pass their maintained readiness gates, but they continue to state that external literature/CJ/ZND agreement, full 3D cellular morphology, and GPU chemistry equivalence are deeper certification tasks unless separately proven.

## Evidence

- Local mirror verification of existing 2D detonation reference JSON passed after the resolver change.
- Local mirror verification of existing 3D detonation reference JSON passed after the resolver change.
- Local mirror verification of existing detonation-front AMR JSON passed after the resolver change.
- A regenerated readiness report includes `detonation_subreport_evidence_hashes_verified` with embedded counts for all three subreports.
