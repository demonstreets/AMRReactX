# Checkpoint: Engineering H2 MPI Link-Shim Verifier

Date: 2026-07-21

## What changed

- Promoted the project-local MPI link shim from an ad hoc build workaround to a first-class engineering evidence gate.
- `tools/verify_engineering_h2_production_evidence.sh` now runs `verify_mpi_link_shim` before validating the packaged engineering evidence.
- `tools/write_engineering_h2_production_evidence_verification_report.py` now records `mpi_link_shim_pass`, requires it during report verification, bumps the report schema to version 4, and hashes `tools/prepare_mpi_link_shims.sh` as evidence.

## Evidence

- `verify_mpi_link_shim` reports `MPI link shim PASS` for `.codex/lib/mpi-link`.
- Required symlinks are checked for `libmpi_cxx.so`, `libopen-rte.so`, `libopen-pal.so`, `libhwloc.so`, `libevent_core.so`, and `libevent_pthreads.so`.
- The refreshed archive report verifies with `engineering_h2_production_evidence_verification_report VERIFY-PASS`, `status=PASS`, `score=92.8/72.7`, and `ctest=22`.
- Full archive command passed: `tools/run_engineering_h2_production_evidence_verification_archive.sh`.

## Scope

This closes a reproducibility blind spot for non-interactive MPI relinks on the current server. It does not clear the remaining production blockers: scheduler-managed campaign outputs, full production-size/overnight evidence, real CAD/reference data, and calibrated fire/radiation/overpressure validation.
