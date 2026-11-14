# H2 Fire Overpressure Reduced EXP002

- Status: `PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002`
- Dataset DOI: `doi:10.18710/X044QK`
- Source CSV: `Ign_pipe_geom_EXP_002.csv`
- CSV MD5 matches Dataverse: `True`
- Rows: `5000004`
- Time range ms: `-500.00202656` to `4500.00096082`
- Pressure channels: `4`
- Peak corrected overpressure bar: `0.027474030077501568`
- Ready for reduced validation case: `True`
- Strict fire calibration blocker cleared: `False`

## Pressure Channels

| Channel | Baseline V | Peak Corrected Bar | Peak Time ms |
|---:|---:|---:|---:|
| 2 | `-0.0006860907654372783` | `0.005112959234562722` | `2540.88896576` |
| 3 | `0.0016955959003005846` | `0.018787525900300587` | `2748.83696524` |
| 4 | `0.001988740077501568` | `0.027474030077501568` | `2744.80496525` |
| 5 | `0.003006231004515792` | `0.013993901004515792` | `2713.93696533` |

## Next Steps

- Map pressure channel positions from the associated experiment description or publication geometry.
- Build a reduced delayed-ignition H2 jet/pipe-obstacle validation case using EXP002 mass-flow, obstacle distance, release time, and ignition delay.
- Compare simulated peak overpressure and arrival time against the four baseline-corrected pressure channels.
