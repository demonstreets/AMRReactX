# Phase 1 — Tank Group Verification Report

## Overview

Verify the full STL → SDF → EB → BC Tags pipeline on a multi-cylinder tank
geometry.  Three vertical cylinders (radius 0.2, height 1.6) are arranged in a
triangular pattern inside a [-1,1]^3 domain with 32^3 cells.

## Cylinder Configuration

| Cylinder | Position (x, y) | Z-range | Radius |
|----------|-----------------|---------|--------|
| 1 | (-0.40, -0.23) | [-0.8, 0.8] | 0.2 |
| 2 | ( 0.40, -0.23) | [-0.8, 0.8] | 0.2 |
| 3 | ( 0.00,  0.46) | [-0.8, 0.8] | 0.2 |

## Pipeline

```
STL files (cyl1, cyl2, cyl3) ─→ (optional: STL→SDF)
                                        │
AMReX CylinderIF (GPUable) ─────────────┤
                                        │
                                        ▼
                          EB2::makeUnion(cyl1, cyl2, cyl3)
                                        │
                                        ▼
                          GeometryShop → EB2::Build → IndexSpace
                                        │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                     fillVolFrac    fillEBCellFlag   buildCellTags
                          │              │              │
                          ▼              ▼              ▼
                      MultiFab      EBCellFlagFab    iMultiFab
                                                   (FLUID/CUT/COVERED)
```

## Test Results

| Check | Result | Details |
|-------|--------|---------|
| EB level OK | PASS | |
| vfrac sum < total cells | PASS | 29727 < 32768 |
| FLUID cells exist | PASS | 28416 |
| CUT cells exist | PASS | 2368 |
| COVERED cells exist | PASS | 1984 |
| All cells tagged | PASS | 32768 = 32^3 |

## Gate Review Criteria

- [x] Multi-object union (3 cylinders) via `EB2::makeUnion`
- [x] EB construction succeeds with composite geometry
- [x] BC tags correctly classify FLUID/CUT/COVERED across all cylinders
- [x] AMR-ready: BC tags propagate with the IndexSpace hierarchy

## Files

| File | Purpose |
|------|---------|
| test/verification/tank_flow.cpp | Tank verification driver |
| src/geometry/bc_tags.H/.cpp | Cell type classification |
| src/geometry/eb2_factory.H | Implicit function factory |
