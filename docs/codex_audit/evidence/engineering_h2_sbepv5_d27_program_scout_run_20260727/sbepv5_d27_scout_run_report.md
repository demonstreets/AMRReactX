# HySafe SBEPV5 D27 Program-Side Scout Run

- Status: `PASS-SBEPV5-D27-PROGRAM-SCOUT-RUN`
- Run root: `/tmp/codex_h2_sbepv5_d27_scout_cuda_20260727_200step_baffle_clearance_plume_threshold`
- Grid/steps: `48 8 36`; `200` steps
- Plotfiles: `5`
- Sensors/rows: `12` sensors; `60` rows
- Max X(H2): `0.0049255823912365505`
- Plume threshold: `1e-08` to `1.0` mole fraction
- Max threshold-cloud x/z: `0.13749999999999998`, `0.21250000000000002`

Limitations:
- This is a program-side SBEPV5 D27 scout using public geometry/release facts and approximate baffle/sensor placement.
- The plume observation threshold is configured for low-concentration plume detection, not for claiming a flammable cloud.
- It is not an external experimental agreement claim because exact baffle bounds, exact sensor coordinates, and original/digitized Gas01..Gas12 histories are not ingested.
