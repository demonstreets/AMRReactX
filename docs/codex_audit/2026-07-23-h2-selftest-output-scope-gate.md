# 2026-07-23 H2 Selftest Output Scope Gate

## Scope

`--allow-synthetic-selftest` is required for validator selftests that use
synthetic copied values. Without an output-scope guard, that switch could be
misused to write synthetic evidence into the official reference report path.

## Change

`tools/write_engineering_h2_reference_agreement_report.py` now rejects
`--allow-synthetic-selftest` unless:

- the output JSON is not the official reference JSON path
- the output Markdown is not the official reference Markdown path
- the output paths are isolated under a path containing `selftest`

## Verification

- Official threshold-only report generation still passes.
- `--allow-synthetic-selftest` with the official reference output path fails.
- `--allow-synthetic-selftest` under the selftest evidence directory passes.
- The official report remains `reference_threshold_agreement` and does not set
  external plume agreement.

## Status

This is a guardrail improvement. It does not clear the external plume blocker,
but it prevents test-mode evidence from contaminating official production
readiness reports.
