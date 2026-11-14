# Engineering CH4 Pipe-Rack Delayed-Ignition CPU/MPI Probe

- Status: `PASS-CH4-PIPE-RACK-DELAYED-IGNITION-CPU-MPI`
- Decision: `ch4_delayed_ignition_leak_obstacle_reacting_cpu_mpi_pass`
- Chemistry model: `CH4_lean`
- MPI ranks/CUDA devices: `2` / `0`
- Steps/final time: `120` / `1.1999999999999985e-06`
- Sustained outputs: `9`
- Max temperature: `2938.763580096761`
- Final Y(H2O) max: `0.0003096467000807105`
- Final Y(CO2) max: `9.600636125732245e-09`

## Limitations

- This is a reduced CH4 CPU/MPI fire probe, not a calibrated natural-gas/LNG production validation.
- Single-CUDA CH4 fire has a separate report; MPI+CUDA and multi-GPU CH4 fire campaigns remain required before a broad CH4 production claim.
- The geometry is synthetic cube/cylinder/pipe-rack STL, not a real cleaned plant CAD import.
- Radiation, overpressure, and LNG vaporization/phase-change consequences are outside this probe.
