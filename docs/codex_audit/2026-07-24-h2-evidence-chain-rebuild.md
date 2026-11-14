# Engineering H2 Evidence Chain Rebuild

Date: 2026-07-24

## Scope

Added `tools/rebuild_engineering_h2_evidence_chain.sh` to rebuild the engineering H2 evidence reports in dependency order. This reduces hash-cascade failures when an upstream evidence report is regenerated.

## Rebuild Order

The script rebuilds:

- real-CAD cleanup and intake reports
- SBEPV5 dataset, digitization, literature anchor, external dataset, and case-package reports
- fire calibration ingestion, digitization, literature anchor, package, and dataset reports
- reference agreement and external plume readiness
- production scorecard
- blocker preflight, data-room, closure manifest, external evidence intake kit, handoff, and master-plan traceability

By default it then runs a two-stage `tools/verify_engineering_h2_production_evidence.sh` pass and regenerates the final production evidence verification report from the final log.

## Usage

```bash
bash tools/rebuild_engineering_h2_evidence_chain.sh
```

For a faster local evidence-only refresh:

```bash
bash tools/rebuild_engineering_h2_evidence_chain.sh --skip-full-verify
```

For environments without a CTest build directory:

```bash
bash tools/rebuild_engineering_h2_evidence_chain.sh --skip-ctest
```

## Limitations

This script fixes reproducibility of the evidence ledger. It does not provide missing external CAD, SBEPV5 plume data, or calibrated fire consequence data, and it does not clear production blockers by itself.
