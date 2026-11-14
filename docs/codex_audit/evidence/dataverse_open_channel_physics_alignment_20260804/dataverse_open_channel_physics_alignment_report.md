# DataverseNO Open-Channel H2 Physics Alignment Diagnosis

- Status: `DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS`
- Experimental orifice diameter: `0.0046` m
- Baseline numerical source radius: `0.08` m
- Radius ratio baseline/experiment: `34.78260869565217`
- Area ratio baseline/experiment: `1209.8298676748582`
- Equivalent physical orifice velocity: `656.7687631723272` m/s
- Baseline numerical source velocity: `0.5` m/s
- Velocity ratio equivalent/baseline: `1313.5375263446545`
- Current grid cell size: `[0.049999999999999996, 0.05, 0.05]` m
- Active cells at experimental radius on current grid: `0`
- Active cells at baseline radius on current grid: `8`
- Recommended orifice-velocity scout: `656.7687631723272` m/s
- Strict external plume blocker cleared: `False`

## Interpretation

- The current coarse-grid source conserves injected mass but cannot directly represent the 4.6 mm experimental orifice radius with cell-centered spherical support.
- The current Dataverse runner injects the measured mass flow with a low 0.5 m/s momentum velocity; the equivalent physical orifice velocity is orders of magnitude larger.
- The previous radius sweep was stable but insensitive, so the next useful screen should vary momentum/BC/source projection rather than only coarse numerical radius.

## Recommended Next Screens

- `orifice_velocity_short_mpi_cuda_scout`: prove whether a momentum-aligned source remains stable before any long 45-120 s campaign
- `open_end_boundary_parity_screen`: separate boundary-condition bias from source calibration bias for the open-ended channel
- `refined_source_projection_screen`: reduce the radius/grid mismatch before judging peak and arrival-time agreement
