# H2 Pipe-Rack Direct Reacting Single-CUDA Evidence

- Status: PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED
- Decision: direct_engineering_pipe_rack_leak_obstacle_reacting_ignition_single_gpu_pass
- Scope: engineering h2_leak_3d with cube/cylinder/pipe-rack STL obstacles, H2 leak source, initial flammable cloud, ignition hotspot, and ReactorCvode chemistry.
- Parallel path: singleton MPI launch on one CUDA device.
- Steps/plotfiles: 2000 steps; plt00000, plt00250, plt00500, plt00750, plt01000, plt01250, plt01500, plt01750, plt02000
- Plotfile time advanced: 0.0 -> 2.000000000000062e-05
- Reacting variables present: HeatRelease, I_R(H2), I_R(O2), Y(H2), Y(O2), Y(H2O).
- Sustained reaction outputs: 8 points; final Y(H2O)_max=0.1502349990492146

Limitation: this is a direct integrated CUDA sustained-fire gate, not a calibrated fire-spread certification.
