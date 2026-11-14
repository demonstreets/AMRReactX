# Engineering CH4 Pipe-Rack Delayed-Ignition MPI+CUDA Probe

- Status: `PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA`
- Decision: `ch4_delayed_ignition_leak_obstacle_reacting_rank_mapped_mpi_cuda_pass`
- Chemistry model: `CH4_lean`
- MPI ranks/CUDA devices: `2` / `2`
- Rank GPU bindings: `{'0': '0', '1': '1'}`
- Steps/final time: `120` / `1.1999999999999985e-06`
- Sustained outputs: `9`
- Max temperature: `2938.763590332824`
- Final Y(H2O) max: `0.000317720435104595`
- Final Y(CO2) max: `1.0067499803796316e-08`

## Limitations

- This is a reduced CH4 rank-mapped MPI+CUDA fire probe, not a calibrated natural-gas/LNG production validation.
- Longer production-duration CH4/natural-gas fire campaigns and fuel-specific LFL/UFL acceptance thresholds remain required before a broad natural-gas production claim.
- The geometry is synthetic cube/cylinder/pipe-rack STL, not a real cleaned plant CAD import.
- Radiation, overpressure, and LNG vaporization/phase-change consequences are outside this probe.
