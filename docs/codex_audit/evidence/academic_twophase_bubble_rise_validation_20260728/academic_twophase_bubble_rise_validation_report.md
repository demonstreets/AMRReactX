# Academic Two-Phase Bubble-Rise Validation

Status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION`

## Key Metrics

- Clears QLT-03 short-time bubble-response gap: `True`
- Clears QLT-03 canonical long-time bubble-rise gap: `False`
- Clears broad QLT-03 bubble-rise gap: `False`
- Blocking reasons: `[]`
- Time: `0.0` to `4.49038700993e-05`
- Grid: `32x64`
- Alpha range: `-6.5160458e-49` to `1.0`
- Mass relative drift: `3.39080707901e-14`
- Advected-scalar relative drift: `3.39964084494e-14`
- Light centroid y: `0.1` to `0.10000000253`
- Integrated y momentum: `3.33512289701e-07`

## Evidence Files

- `case_summary`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/bubble_rise_buoyancy_6000step_low_cfl/case_summary.json` sha256 `65dba52bdcf73838`
- `input_file`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/bubble_rise_buoyancy_6000step_low_cfl/run/input.codex_bubble_rise` sha256 `701d96a08912328f`
- `build_log`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/bubble_rise_buoyancy_6000step_low_cfl/build.log` sha256 `57bf3bb7a9c1658c`
- `run_log`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/bubble_rise_buoyancy_6000step_low_cfl/run.log` sha256 `fa76b51d1ce0515d`
- `validation_log`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/bubble_rise_buoyancy_6000step_low_cfl/validation.log` sha256 `110a5d0f726a2881`
- `runner`: `tools/codex_run_academic_twophase_bubble_rise_validation.sh` sha256 `2e1ada977e242a75`
- `validator`: `tools/validate_academic_twophase_bubble_rise.py` sha256 `85b7ffa62d71c62c`
- `report_writer`: `tools/write_academic_twophase_bubble_rise_validation_report.py` sha256 `dc156465325bf18c`
- `long_window_probe_gate_report`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/long_window_probe_gate_20260729/bubble_rise_long_window_probe_gate_report.json` sha256 `41ecda042662aee7`
- `inviscid_long_window_report`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_inviscid_long_window_validation_20260729/academic_twophase_bubble_rise_inviscid_long_window_validation_report.json` sha256 `5dc0f00f0ab96655`
- `mol_long_window_report`: `docs/codex_audit/evidence/academic_twophase_bubble_rise_mol_long_window_validation_20260729/academic_twophase_bubble_rise_mol_long_window_validation_report.json` sha256 `5408bd970570e996`
- `prob_H`: `examples/academic/bubble_rise/prob.H` sha256 `696e5bead6f342f0`
- `prob_cpp`: `examples/academic/bubble_rise/prob.cpp` sha256 `e400cbbd6d9dce3c`
- `prob_parm_H`: `examples/academic/bubble_rise/prob_parm.H` sha256 `6c0c1fc3213544f1`

## Limitations

- This is a maintained in-repository strengthened short-time, low-CFL buoyancy-response stability gate, not an external benchmark of a canonical long-time bubble-rise experiment.
- The 6000-step low-CFL gate proves positive finite state, conservation, bounded alpha, and a measurable upward light-phase response.
- Phase-consistent smooth-interface inviscid and do_mol=1 30000-step long-window gates are now attached; external canonical long-time bubble deformation remains a follow-up rather than being claimed by this report.
- The gate clears only the short-time buoyancy-response component of QLT-03; canonical long-time bubble-rise validation remains open.
