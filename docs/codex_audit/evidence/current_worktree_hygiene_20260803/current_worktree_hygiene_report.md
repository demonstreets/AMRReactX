# Current Worktree Hygiene Audit

- Status: `AUDITED-CURRENT-WORKTREE-HYGIENE`
- Dirty entries: `1420`
- Generated/case-output entries: `309`
- Deleted generated/case-output entries: `307`
- High-attention entries: `114`
- Cleanup performed: `False`
- Current-scope gates: `15/15`
- Completion audit: `AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE`

## Category Counts

- `documentation`: `145`
- `example_source_or_config`: `32`
- `generated_or_case_output`: `309`
- `other`: `142`
- `source_or_config`: `81`
- `tooling`: `711`

## Recommendations

- Do not run destructive cleanup from automation while the worktree carries user and audit changes.
- Treat generated_or_case_output entries as cleanup candidates only after preserving required evidence reports and logs.
- Review high_attention_samples before staging, reverting, or packaging source/config changes.
