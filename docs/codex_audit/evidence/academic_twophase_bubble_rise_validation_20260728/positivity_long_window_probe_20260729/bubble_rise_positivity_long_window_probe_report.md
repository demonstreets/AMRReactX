# Bubble-Rise Positivity Long-Window Probe

Status: NOT_READY-ACADEMIC-TWOPHASE-BUBBLE-RISE-POSITIVITY-LONG-WINDOW-PROBE

Case count: 17
Passing case count: 1

Post-timestep rho_e/Temp positivity protection prevents several negative-energy terminal states, but long-window cases still fail canonical bubble-rise motion or viscous NaN stability; source sign and source magnitude probes do not clear the gap.

## Cases
- positivity_mol_ramp5e5_terminal0015_30000: run_rc=1 validation_rc=2 nan=True
- positivity_nomol_ramp5e5_terminal0015_30000: run_rc=0 validation_rc=1 nan=False
- positivity_nomol_noterminal_30000: run_rc=0 validation_rc=1 nan=False
- positivity_nomol_ramp5e5_noterminal_30000: run_rc=0 validation_rc=1 nan=False
- positivity_nomol_ramp5e5_terminal005_30000: run_rc=0 validation_rc=1 nan=False
- positivity_nomol_ramp5e5_terminal01_30000: run_rc=0 validation_rc=1 nan=False
- floor25_mol_terminal0015: run_rc=1 validation_rc=2 nan=True
- floor25_nomol_noterminal: run_rc=0 validation_rc=1 nan=False
- floor25_nomol_terminal0015: run_rc=0 validation_rc=1 nan=False
- cfl005_30000: run_rc=None validation_rc=None nan=None
- cfl010_30000: run_rc=None validation_rc=None nan=None
- accel981: run_rc=None validation_rc=None nan=None
- accel98p1: run_rc=None validation_rc=None nan=None
- accel_neg981: run_rc=None validation_rc=None nan=None
- accel_neg98p1: run_rc=None validation_rc=None nan=None
- accel_neg_6000: run_rc=None validation_rc=None nan=None
- accel_pos_6000: run_rc=None validation_rc=None nan=None
