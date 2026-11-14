# Engineering CH4 Cold-Plume CPU, MPI, And CUDA Probe

- Status: `PASS-ENGINEERING-CH4-COLD-PLUME-CPU-MPI-CUDA-PROBE`
- Species: `CH4`
- Chemistry model: `CH4_lean`
- CPU probe passed: `True`
- CPU/MPI probe passed: `True`
- MPI rank count: `2`
- Single CUDA probe passed: `True`
- Production ready: `False`
- Plotfiles: `6`
- Final time s: `5e-05`
- Final mass/injected ratio: `1.0`
- Max Y(CH4): `3.12047166e-08`

## Limitations

- This is a short CPU, 2-rank CPU/MPI, and single-CUDA cold-plume probe for CH4 source injection and passive dispersion.
- It does not validate CH4 ignition, flame propagation, fire consequences, MPI+CUDA, or multi-GPU execution.
- It is not a natural-gas mixture or LNG vaporization validation.
