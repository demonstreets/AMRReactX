# H2 Pipe-Rack Direct Reacting Single-CUDA Evidence

- Status: PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED
- Decision: direct_engineering_pipe_rack_leak_obstacle_reacting_ignition_single_gpu_pass
- Scope: engineering h2_leak_3d with cube/cylinder/pipe-rack STL obstacles, H2 leak source, initial flammable cloud, ignition hotspot, and ReactorCvode chemistry.
- Parallel path: singleton MPI launch on one CUDA device.
- Steps/plotfiles: 1000 steps; plt00000, plt00125, plt00250, plt00375, plt00500, plt00625, plt00750, plt00875, plt01000
- Plotfile time advanced: 0.0 -> 9.999999999999914e-06
- Reacting variables present: HeatRelease, I_R(H2), I_R(O2), Y(H2), Y(O2), Y(H2O).
- Sustained reaction outputs: 8 points; final Y(H2O)_max=0.1405349795432564

Limitation: this is a direct integrated CUDA sustained-fire gate, not a calibrated fire-spread certification.
