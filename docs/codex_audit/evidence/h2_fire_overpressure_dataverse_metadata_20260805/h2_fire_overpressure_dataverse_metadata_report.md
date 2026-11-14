# H2 Fire Overpressure Dataverse Metadata

- Status: `PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA`
- Dataset DOI: `doi:10.18710/X044QK`
- File count: `47`
- CSV file count: `39`
- Large zip file count: `6`
- README MD5 matches Dataverse: `True`
- Matrix XLSX MD5 matches Dataverse: `True`
- Experiment matrix rows: `40`
- Pressure sensors detected in README: `4`
- Strict fire calibration blocker cleared: `False`

## Matrix Header

`EXP Number`, `Max Pressure [bar]`, `Max MFR [kg/s]`, `Avg Pressure [bar]`, `Avg MFR [kg/s]`, `Ignition place`, `Obstacle distance from the nozzle [cm]`, `H2 release time [s]`, `Ignition delay time [s]`, `comments`

## Next Steps

- Select one ignited experiment with no exclusion comment and a small CSV size for a reduced overpressure calibration scout.
- Download only the selected CSV into a dedicated evidence directory with MD5 verification.
- Extract pressure-sensor time-series columns, pressure conversion, ignition delay, obstacle distance, and mass-flow metadata.
- Build a reduced PeleC/PeleLMeX delayed-ignition validation case and compare peak overpressure/time-of-arrival against the selected experiment.
