# Current Worktree Review Queue

- Status: `PASS-CURRENT-WORKTREE-REVIEW-QUEUE`
- Ready: `True`
- Policy: `non-destructive; review classification only; no cleanup/stage/restore/ignore`
- Ledger entries: `1111`
- High-attention entries: `255`
- Generated/case-output entries excluded: `309`
- Cleanup candidate roots: `32`
- Existing cleanup candidate roots: `2`
- External dependency link drifts: `1`
- SUNDIALS local link audit: `PASS-SUNDIALS-LOCAL-LINK-AUDIT`
- SUNDIALS local link drift present: `True`
- SUNDIALS current link kind: `directory`
- SUNDIALS safe to auto-restore: `False`
- Review required before packaging: `True`

## Priority Counts

- `P0`: `1`
- `P1`: `154`
- `P4`: `100`

## Domain Counts

- `academic_examples`: `36`
- `engineering_examples`: `77`
- `external_dependency_or_mirror`: `76`
- `other`: `66`

## Risk Reasons

- `external_dependency_or_mirror_change`: `75`
- `p4_review_item`: `100`
- `source_or_input_change_requires_review`: `79`
- `tracked_symlink_deleted_but_replacement_directory_present`: `1`

## Top Churn Entries

- `P1` `engineering_examples` ` M` churn=`671` reason=`source_or_input_change_requires_review` `examples/engineering/h2_leak_3d/pelelmex_prob.H`
- `P1` `other` ` M` churn=`619` reason=`source_or_input_change_requires_review` `test/unit/test_vof_fct.cpp`
- `P1` `other` ` M` churn=`601` reason=`source_or_input_change_requires_review` `src/geometry/eb2_factory.cpp`
- `P1` `engineering_examples` ` M` churn=`431` reason=`source_or_input_change_requires_review` `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
- `P1` `other` ` M` churn=`370` reason=`source_or_input_change_requires_review` `test/unit/test_csf.cpp`
- `P1` `academic_examples` ` M` churn=`310` reason=`source_or_input_change_requires_review` `examples/academic/bubble_rise/prob.H`
- `P1` `other` ` M` churn=`273` reason=`source_or_input_change_requires_review` `test/unit/test_twophase_eos.cpp`
- `P1` `external_dependency_or_mirror` ` M` churn=`209` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Source/PeleLMeX_Advance.cpp`
- `P1` `external_dependency_or_mirror` ` M` churn=`194` reason=`external_dependency_or_mirror_change` `external/PeleC/Source/PeleC.cpp`
- `P1` `external_dependency_or_mirror` ` M` churn=`172` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Source/PeleLMeX_Projection.cpp`
- `P1` `external_dependency_or_mirror` ` M` churn=`166` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp`
- `P1` `external_dependency_or_mirror` ` M` churn=`136` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Source/PeleLMeX_UMac.cpp`
- `P1` `other` ` M` churn=`123` reason=`source_or_input_change_requires_review` `test/unit/test_yaml_parser.cpp`
- `P1` `external_dependency_or_mirror` ` M` churn=`122` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Source/PeleLMeX_Tagging.cpp`
- `P1` `external_dependency_or_mirror` ` M` churn=`120` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Exec/Make.PeleLMeX`
- `P1` `other` ` M` churn=`111` reason=`source_or_input_change_requires_review` `src/geometry/stl_parser.cpp`
- `P1` `other` ` M` churn=`110` reason=`source_or_input_change_requires_review` `src/engineering/evaporation/pool_vof_coupling.H`
- `P1` `other` ` M` churn=`108` reason=`source_or_input_change_requires_review` `test/unit/test_twophase_hllc.cpp`
- `P1` `engineering_examples` ` M` churn=`104` reason=`source_or_input_change_requires_review` `examples/engineering/backward_facing_step/pelelmex_prob.H`
- `P1` `other` ` M` churn=`98` reason=`source_or_input_change_requires_review` `src/academic/twophase/CSF.H`
- `P1` `external_dependency_or_mirror` ` M` churn=`90` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Source/PeleLMeX_ProblemSpecificFunctions.H`
- `P1` `external_dependency_or_mirror` ` M` churn=`83` reason=`external_dependency_or_mirror_change` `external/PeleLMeX/Source/PeleLMeX_Forces.cpp`
- `P1` `other` ` M` churn=`67` reason=`source_or_input_change_requires_review` `src/engineering/wind/wind_profile.H`
- `P1` `other` ` M` churn=`62` reason=`source_or_input_change_requires_review` `src/geometry/eb2_factory.H`
- `P1` `other` ` M` churn=`59` reason=`source_or_input_change_requires_review` `src/common/input_parser/yaml_parser.cpp`

## Operator Guidance

- Review P0/P1 entries before packaging or handing off source changes.
- Treat generated/case-output cleanup candidates separately from source review.
- Do not delete, restore, stage, or ignore files from this report alone.
- Run the source ledger and cleanup manifest again after any manual cleanup.
