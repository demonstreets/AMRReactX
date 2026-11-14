# Engineering H2 Production Mesh Campaign Scout

Status: `PASS-PRODUCTION-MESH-FULL-DURATION-CAMPAIGN`
Campaign scale: `engineering_production_mesh_full_duration_campaign`
Production-size mesh campaign: `True`
Full-duration campaign: `True`

## Summary

- Cases: `7` / `7` pass
- Ranks covered: `[4, 8, 16]`
- Max step: `7200`
- Max base cells: `65536`
- Max AMR-equivalent fine cells: `524288`
- Max cloud relative difference: `0.0380952381`
- Max peak relative difference: `0.0431073584`

## Cases

| Case | Status | Ranks | Steps | Base cells | Fine cells | Cloud rel | Peak rel |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `production_mesh_4rank_120step` | `PASS-SCOUT` | 4 | 120 | 65536 | 524288 | 0.0380952381 | 0.0431073584 |
| `production_mesh_8rank_120step` | `PASS-SCOUT` | 8 | 120 | 65536 | 524288 | 0.0380952381 | 0.0431073584 |
| `production_mesh_16rank_120step` | `PASS-SCOUT` | 16 | 120 | 65536 | 524288 | 0.0380952381 | 0.0431073584 |
| `production_mesh_4rank_600step` | `PASS-STABILITY` | 4 | 600 | 65536 | 524288 | 0.0315976518 | 0.0340034177 |
| `production_mesh_8rank_600step` | `PASS-STABILITY` | 8 | 600 | 65536 | 524288 | 0.0315976518 | 0.0340034177 |
| `production_mesh_4rank_1200step` | `PASS-STABILITY` | 4 | 1200 | 65536 | 524288 | 0.0299314337 | 0.0358285346 |
| `production_mesh_4rank_7200step_full_duration` | `PASS-FULL-DURATION` | 4 | 7200 | 65536 | 524288 | 0.0280126911 | 0.0345775965 |

## Blocking Gaps

- none
