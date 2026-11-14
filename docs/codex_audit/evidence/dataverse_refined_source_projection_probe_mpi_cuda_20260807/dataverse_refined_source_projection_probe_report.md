# DataverseNO Refined Source Projection Probe

- Status: `PASS-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA`
- MPI ranks: `2`
- CUDA initialized: `True`
- Grid: `[32, 16, 8]`
- dx: `[0.012499999999999999, 0.0125, 0.012500000000000011]` m
- Leak radius: `0.0023` m
- Active volume: `1.953125e-06` m3
- Single-cell volume: `1.9531250000000017e-06` m3
- Source CFL: `0.0052541501053784`
- Time end: `9.999999999999999e-05` s
- Max Y(H2): `0.0505563747`
- Clears strict external plume blocker: `False`

## Limitations

- This is a near-source refined projection stability probe, not a full-channel Dataverse plume-shape agreement case.
- The experimental 2.3 mm radius is represented by one cell-centered source cell at dx=0.0125 m; longer full-domain refinement or source projection is still required for production agreement.
- This evidence reduces the source/grid mismatch risk but does not clear the strict external plume-shape blocker.
