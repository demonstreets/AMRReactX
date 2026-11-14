# Engineering BFS k-epsilon Reference Validation

Status: `PASS-BFS-KEPSILON-REFERENCE`

## Summary

- Plotfile: `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/prodlim16_profile_exp020_4rank_5000_20260723/plt04309`
- Grid: `208 x 56`
- BFS validator: `PASS` rc `0`
- X_R/H: `5.944509505537611`
- Recirculation length/H: `5.741469816272965`
- Log-law validator rc: `1` linf `15.4519819`
- Preflight reports: `4` / `4` pass

## Blocking Gaps


## Diagnostic Gaps

- `bfs_loglaw_profile_plotfile_validation_failed`

## Preflight Reports

- `refined_208x56_lowcfl_5000step_reference_attempt`: `PASS-BFS-KEPSILON-PREFLIGHT` grid `208 x 56` H/dy `6.096000000000001` CFL `0.05` dt_shrink `0.001` NaN-risk `False`
- `base_104x28_current_input`: `PASS-BFS-KEPSILON-PREFLIGHT` grid `208 x 56` H/dy `6.096000000000001` CFL `0.05` dt_shrink `0.001` NaN-risk `False`
- `refined_208x56_default_cfl`: `PASS-BFS-KEPSILON-PREFLIGHT` grid `208 x 56` H/dy `6.096000000000001` CFL `0.05` dt_shrink `0.001` NaN-risk `False`
- `refined_208x56_lowcfl_500step`: `PASS-BFS-KEPSILON-PREFLIGHT` grid `208 x 56` H/dy `6.096000000000001` CFL `0.05` dt_shrink `0.001` NaN-risk `False`

## Sensitivity Cases

- `208x56_4rank_default_cfl`: `FAIL-NAN` step `0` time `0.0` X_R/H `None` recirc `None`
- `208x56_serial_cfl005_500step`: `COMPLETE-SCOUT` step `499` time `0.007105879625` X_R/H `1.261198811146003` recirc `1.1482939632545934`
