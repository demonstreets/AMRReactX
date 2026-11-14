# Strict External Artifact Receiving Preflight Entrypoint Report

- Status: `PASS-STRICT-EXTERNAL-ARTIFACT-RECEIVING-PREFLIGHT-ENTRYPOINT`
- Ready: `True`
- Wrapper: `tools/run_strict_external_artifact_receiving_preflight.sh`
- Latest passing log: `docs/codex_audit/evidence/strict_external_artifact_receiving_preflight_20260820/strict_external_artifact_receiving_preflight_20260820T101157Z.log`
- Required files: `14`
- Present files: `5`
- Missing files: `9`
- Open strict blockers: `3`
- Strict completion allowed: `False`
- File presence is strict completion: `False`
- Fire production calibration claim allowed: `False`
- Fire pressure agreement ready: `False`
- Fire radiation agreement ready: `False`

## File Presence vs Strict Credit

The receiving preflight distinguishes filesystem presence from strict production credit. A file can exist and pass schema checks while the strict blocker remains open if the artifact does not yet prove case-aligned physics agreement.

For the fire consequence blocker, current residuals are:

- Pressure missing artifact count: `3`
- Radiation missing artifact count: `3`
- Residual budget clears strict blocker: `False`

## Commands

```bash
bash tools/run_strict_external_artifact_receiving_preflight.sh
python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py
bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh
```
