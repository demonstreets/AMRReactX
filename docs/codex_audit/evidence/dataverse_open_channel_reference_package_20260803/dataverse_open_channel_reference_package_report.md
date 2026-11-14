# DataverseNO Open-Channel H2 Reference Package

- Status: `PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE`
- Selected case: `23_FFI_P101_T00031.zip` / `test-08-1`
- Raw rows: `17347`
- Sensor time samples: `581`
- Sensor records: `16849`
- Duration s: `378.5`
- Peak H2 vol percent: `30.827625806451614` at sensor `20`
- LFL sensor count: `25`
- Ready for reference signal sampling: `True`
- Ready for CFD/reference agreement scoring: `False`
- Clears external plume blocker: `False`

## Outputs

- long_timeseries_csv: `docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/dataverse_reference_timeseries_long.csv`
- wide_timeseries_csv: `docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/dataverse_reference_timeseries_wide.csv`
- release_profile_csv: `docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/dataverse_reference_release_profile.csv`
- case_metadata_json: `docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/dataverse_reference_case_metadata.json`

## Limitations

- This report proves reference signal packaging, not CFD validation agreement.
- The raw experimental CSV contains small negative concentration readings from measurement noise; X(H2) preserves the raw converted signal and X_H2_clipped_nonnegative is provided for nonnegative-only consumers.
- The strict external plume blocker remains open until CFD sensor samples are compared against this reference package with accepted metrics.
