# Result retention

Full preserved-file verification completed before deletion.
Supported overdriven 4 us case: keep first and last native plotfiles.
Near-CJ waveframe v1/v2: validation not achieved; keep configuration, logs and analyses, omit native failed fields.
Nonzero-exit cases: execution failed; keep original exit codes and logs.
Unclassified cases: preserved without assuming physical PASS.

See retention_omissions.json for every omitted source field.
