# Engineering CH4 Pipe-Rack Delayed-Ignition MPI+CUDA 500-Step Probe

- Status: `PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP`
- Decision: `ch4_rank_mapped_mpi_cuda_longer_sustained_fire_window_pass`
- Chemistry model: `CH4_lean`
- MPI ranks/CUDA devices: `2` / `2`
- Rank GPU bindings: `{'0': '0', '1': '1'}`
- Steps/final time: `500` / `4.999999999999962e-06`
- Sustained outputs: `10`
- Late reactive outputs: `6`
- Peak Y(H2O) max: `0.0003198202199495681`
- Final Y(H2O) max: `6.322977979580781e-05`
- Final heat release abs: `3198864.2986795595`
- Final I_R(CH4) abs: `0.11287264590845858`

## Limitations

- This 500-step probe is longer than the ignition smoke tests, but it is still not a calibrated full-duration natural-gas production campaign.
- The late window is a decaying but still reactive hot plume; production qualification still needs scenario-specific duration and acceptance thresholds.
- The geometry is synthetic cube/cylinder/pipe-rack STL, not a real cleaned plant CAD import.
- Radiation, overpressure, LNG vaporization, and multi-component natural-gas composition validation are outside this probe.
