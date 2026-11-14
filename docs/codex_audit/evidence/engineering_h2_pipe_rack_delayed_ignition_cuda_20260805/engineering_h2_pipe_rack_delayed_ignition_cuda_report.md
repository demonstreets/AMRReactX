# H2 Pipe-Rack Delayed-Ignition Single-CUDA Evidence

- Status: PASS-H2-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA
- Decision: delayed_ignition_leak_obstacle_reacting_single_gpu_pass
- Scope: H2 leak + initial flammable cloud + STL cube/cylinder/pipe-rack obstacles + delayed timed ignition source + ReactorCvode chemistry.
- Parallel path: single CUDA device through the MPI CUDA executable path.
- Steps/final time: 120 steps; final_time=1.1999999999999985e-06
- Sustained post-ignition outputs: 7
- Final Y(H2O)_max: 1.385375798968195e-06
- Initial hot spot was disabled; ignition came from the timed energy source.

Limitation: this strengthens the engineering fire stability gate but does not clear calibrated overpressure/radiation validation.
