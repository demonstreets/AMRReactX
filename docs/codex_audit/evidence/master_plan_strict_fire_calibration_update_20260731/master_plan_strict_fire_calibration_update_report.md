# Strict Fire Calibration Update

- Status: `TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-PARTIAL-DATA-BRIDGED`
- Public-source triage: `PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE`
- Digitization preflight: `PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT`
- Literature metric preflight: `PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT`
- 2026 candidate sources: `PASS-H2-FIRE-CALIBRATION-CANDIDATE-SOURCES-20260805`
- EXP002 reduced overpressure: `PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002`
- EXP002 delayed-ignition bridge: `PASS-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE`
- EXP002 peak corrected overpressure: `0.027474030077501568` bar
- EXP002 bridge energy conservation ready: `True`
- EXP002 bridge CPU/GPU parity ready: `True`
- EXP002 overpressure calibration table: `PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE`
- EXP002 overpressure metric count: `4`
- EXP002 pressure comparison contract: `PASS-H2-FIRE-EXP002-PRESSURE-COMPARISON-CONTRACT`
- EXP002 CFD pressure comparison executed: `False`
- EXP002 pressure CFD proxy: `PASS-H2-FIRE-EXP002-PRESSURE-CFD-PROXY`
- EXP002 pressure CFD proxy CPU/GPU parity: `True`
- Plotfile sensor sampling contract: `PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-CONTRACT`
- Plotfile pressure time-series path ready: `True`
- Plotfile sensor sampling uses synthetic coordinates: `True`
- Plotfile sensor sampling mode: `linear`
- Plotfile sensor sampling linear interpolation: `True`
- Plotfile sensor sampling non-cell-center coordinates: `True`
- Plotfile sensor sampling negative selftest: `PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-NEGATIVE-SELFTEST`
- Plotfile sensor sampling negative cases refused: `8/8`
- MDPI radiation calibration table: `PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE`
- MDPI radiation metric count: `4`
- MDPI radiation comparison contract: `PASS-H2-FIRE-MDPI-RADIATION-COMPARISON-CONTRACT`
- MDPI CFD radiation comparison executed: `False`
- MDPI radiation screening comparison: `QUANTIFIED-H2-FIRE-MDPI-RADIATION-SCREENING-NOT-PASSING`
- MDPI radiation screening pass/fail: `0/4`
- MDPI radiation CFD proxy: `PASS-H2-FIRE-MDPI-RADIATION-CFD-PROXY`
- MDPI radiation CFD proxy CPU/GPU parity: `True`
- MDPI integrated radiation CFD proxy: `PASS-H2-FIRE-MDPI-RADIATION-INTEGRATED-CFD-PROXY`
- MDPI integrated radiation plotfiles: `11`
- MDPI integrated radiation virtual flux generated: `True`
- Dataset ingestion: `NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION`
- Package: `NOT_READY-H2-FIRE-CALIBRATION-PACKAGE`
- Dataset: `NOT_READY-H2-FIRE-CALIBRATION-DATASET`
- Strict fire calibration blocker cleared: `False`

## Missing For Strict Credit

- CFD radiation comparison against MDPI heat-flux targets
- exact EXP002 sensor coordinates plus CFD pressure-sensor comparison against EXP002 peak overpressure and arrival time
- case alignment records linking measurements to simulated engineering scenarios
- uncertainty/provenance fields sufficient for calibrated radiation and overpressure agreement

## Next Actions

- Replace the synthetic plotfile sensor-sampling CSV with exact EXP002 sensor coordinates once available.
- Run a case-aligned CFD radiation comparison against the MDPI radiation target table.
- Run an EXP002-aligned CFD pressure-sensor comparison and require peak overpressure plus arrival-time acceptance before clearing strict fire credit.
- Run the existing dataset ingestion, package, dataset builder, production scorecard, and master-plan traceability reports after calibrated tables exist.
