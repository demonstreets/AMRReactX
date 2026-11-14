# H2 Fire MDPI Radiation Integrated CFD Proxy

- Status: `PASS-H2-FIRE-MDPI-RADIATION-INTEGRATED-CFD-PROXY`
- Plotfiles integrated: `11`
- MDPI radiation metrics: `4`
- Radiative fraction: `0.2`
- Peak integrated radiative proxy power: `114444.30181986034` W
- Peak plotfile: `docs/codex_audit/evidence/engineering_h2_pipe_rack_mpi_cuda_long_revalidation_20260731/run_root/run/plt00200`
- Virtual radiometer flux generated: `True`
- Agreement pass/fail: `0/4`
- Strict fire calibration blocker cleared: `False`

## Limitations

- Uses positive HeatRelease volume integral with an assumed radiative fraction.
- Does not model flame surface, gas radiation, wall/obstruction view factors, absorption, soot, or radiometer orientation.
- Uses MDPI distance anchors only; it is not case-aligned to a full experiment setup.
- Does not clear strict calibrated radiation or overpressure credit.

## Evidence

- `radiation_table`: `docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/h2_fire_mdpi_radiation_calibration_table_report.json`
- `radiation_metrics_csv`: `docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/radiation_metrics.csv`
- `history_csv`: `docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/integrated_heat_release_history.csv`
- `comparison_csv`: `docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/integrated_radiation_proxy_comparison.csv`
- `peak_plotfile_header`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_mpi_cuda_long_revalidation_20260731/run_root/run/plt00200/Header`
- `peak_plotfile_cell_h`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_mpi_cuda_long_revalidation_20260731/run_root/run/plt00200/Level_0/Cell_H`
