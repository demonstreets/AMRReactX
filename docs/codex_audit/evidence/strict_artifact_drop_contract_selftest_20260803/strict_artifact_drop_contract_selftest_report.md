# Strict Artifact Drop Contract Selftest

- Status: `PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST`
- Selftests: `8/8`
- Failed selftests: `0`

## Tests

- `valid_json_accepts_required_keys` expected_ready=`True` observed_ready=`True` passed=`True`
- `missing_json_keys_rejected` expected_ready=`False` observed_ready=`False` passed=`True`
- `malformed_json_rejected` expected_ready=`False` observed_ready=`False` passed=`True`
- `valid_required_csv_accepts_header_and_data` expected_ready=`True` observed_ready=`True` passed=`True`
- `wrong_csv_header_rejected` expected_ready=`False` observed_ready=`False` passed=`True`
- `required_csv_without_data_rows_rejected` expected_ready=`False` observed_ready=`False` passed=`True`
- `duplicate_csv_columns_rejected` expected_ready=`False` observed_ready=`False` passed=`True`
- `absent_optional_csv_is_awaiting_not_invalid` expected_ready=`True` observed_ready=`True` passed=`True`
