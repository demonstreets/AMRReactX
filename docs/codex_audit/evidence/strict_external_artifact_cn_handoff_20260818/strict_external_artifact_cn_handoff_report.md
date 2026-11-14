# Strict External Artifact Chinese Handoff Report

- Status: `PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF`
- Guide: `docs/user_guides/真实资料投递清单_按文件路径.md`
- Domains: `3`
- Required files: `14`
- Present files: `5`
- Missing files: `9`
- Strict completion allowed: `False`

## Commands

```bash
bash tools/run_strict_external_artifact_receiving_preflight.sh
python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py
bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh
python3 tools/write_strict_external_artifact_cn_handoff_report.py
bash tools/verify_strict_external_artifact_cn_handoff.sh
bash tools/run_current_scope_release_refresh.sh
```

## Domains

- `external_plume` `外部泄漏/扩散 plume 数据` required=5 present=0 missing=5
- `fire_calibration` `火灾、热辐射、过压标定数据` required=5 present=5 missing=0
- `real_cad` `真实 CAD、清理几何与边界标签` required=4 present=0 missing=4
