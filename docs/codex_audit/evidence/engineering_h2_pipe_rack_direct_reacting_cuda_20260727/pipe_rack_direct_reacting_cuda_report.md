# H2 Pipe-Rack Direct Reacting Single-CUDA Evidence

- Status: PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED
- Decision: direct_engineering_pipe_rack_leak_obstacle_reacting_ignition_single_gpu_pass
- Scope: engineering h2_leak_3d with cube/cylinder/pipe-rack STL obstacles, H2 leak source, initial flammable cloud, ignition hotspot, and ReactorCvode chemistry.
- Parallel path: singleton MPI launch on one CUDA device.
- Steps/plotfiles: 500 steps; plt00000, plt00100, plt00200, plt00300, plt00400, plt00500
- Plotfile time advanced: 0.0 -> 4.999999999999962e-06
- Reacting variables present: HeatRelease, I_R(H2), I_R(O2), Y(H2), Y(O2), Y(H2O).
- Sustained reaction outputs: 5 points; final Y(H2O)_max=0.13230707374199105

Limitation: this is a direct integrated CUDA sustained-fire gate, not a calibrated fire-spread certification.
