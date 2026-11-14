# Engineering H2 Fire EXP002 Delayed-Ignition Bridge

- status: `PASS-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE`
- decision: `delayed_ignition_energy_conserved_and_exp002_mapping_ready`
- strict fire calibration blocker cleared: `False`
- CUDA ignition energy relative error: `0.000e+00`
- CPU/MPI ignition energy relative error: `0.000e+00`
- EXP002 peak corrected overpressure: `0.027474030077501568` bar
- EXP002 ignition delay: `2.5` s

## Limitations

- This bridge proves energy-source accounting and EXP002 target availability; it is not calibrated CFD overpressure agreement.
- The current delayed-ignition run is a stiff reduced window, not the full 3 s EXP002 release and 2.5 s ignition delay.
- The current geometry remains synthetic cube/cylinder/pipe-rack STL, not the EXP002 pipe geometry or a cleaned plant CAD import.
