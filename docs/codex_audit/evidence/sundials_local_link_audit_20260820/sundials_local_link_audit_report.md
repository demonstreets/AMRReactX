# SUNDIALS Local Link Audit

- Status: `PASS-SUNDIALS-LOCAL-LINK-AUDIT`
- Audit ready: `True`
- Cleanup performed: `False`
- Tracked mode: `120000`
- Tracked target: `/tmp/sundials-6.7.0`
- Current replacement kind: `directory`
- Current Git XY: ` D`
- Local link drift present: `True`
- Expected target exists: `False`
- CUDA SUNDIALS ready candidates: `2`
- Safe to auto-restore: `False`
- Restore requires explicit operator review: `True`

## CUDA SUNDIALS Candidates

- `/home/cj/local/sundials-cuda` kind=`directory` exists=`True` ready=`True`
- `/home/cj/.local/sundials-cuda-6.4.1` kind=`directory` exists=`True` ready=`True`
- `/tmp/sundials-6.7.0` kind=`missing` exists=`False` ready=`False`

## Operator Guidance

- Do not delete or replace external/PelePhysics/Submodules/sundials from this report alone.
- If packaging source, resolve the tracked symlink versus replacement directory deliberately.
- CUDA smoke scripts may still pass when SUNDIALS_CUDA_DIR points to a separate ready install.
- After manual dependency repair, rerun this audit and the current worktree review queue.
