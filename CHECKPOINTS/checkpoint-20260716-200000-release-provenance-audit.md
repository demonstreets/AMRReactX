# Checkpoint: Release provenance audit

Date: 2026-07-16
Status: PASS-WARN / RELEASE-BLOCKER

## Summary

Added a release-provenance audit for dependency paths and submodule/symlink portability. The audit confirms the current server state remains runnable, but release packaging is not clean: several tracked dependency paths are absolute symlinks, `.gitmodules` is incomplete, and the current SUNDIALS CUDA shim hard-codes `/home/cj/local/sundials-cuda`.

This is now explicit evidence instead of an implicit dirty-worktree surprise.

## Changed files / modules

- `tools/check_release_provenance.py`
- `docs/codex_audit/RELEASE_PROVENANCE.md`
- `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md`
- `docs/codex_audit/SMOKE_MATRIX.md`
- `CHECKPOINTS/checkpoint-20260716-200000-release-provenance-audit.md`

## Verification

- `python3 -m py_compile tools/check_release_provenance.py`
- `python3 tools/check_release_provenance.py | tee /tmp/codex_release_provenance_20260716.log`
- `python3 tools/check_release_provenance.py --strict > /tmp/codex_release_provenance_strict_20260716.log 2>&1; echo strict_rc=$?`

## Evidence

- `/tmp/codex_release_provenance_20260716.log`
- `/tmp/codex_release_provenance_strict_20260716.log`
- Non-strict result: `release_provenance PASS-WARN warnings=11`
- Strict result: `strict_rc=1`

## Known limitations

- This checkpoint does not fix the provenance problems; it makes them mechanically visible.
- Current smoke gates remain valid for this server, but release-ready packaging remains blocked until strict provenance passes.
