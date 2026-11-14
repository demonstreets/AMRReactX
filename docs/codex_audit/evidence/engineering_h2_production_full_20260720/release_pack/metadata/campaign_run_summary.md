# Engineering H2 Campaign: engineering-h2-production-full-20260720

Status: `PASS`
Suite: `engineering-h2-production`
Generated UTC: `2026-07-20T02:30:02+00:00`
Output root: `/tmp/codex_engineering_h2_campaign_full_20260720`
Host: `xiaochun-4028`
Repo commit: `0ec1056ff13bba9ee4062713938d55a75efc93dd`
Case count: `16`

## Cases

| Case | Suite | Status | Duration s | Root |
| --- | --- | --- | ---: | --- |
| `open-domain` | `h2-core` | `PASS` | 26.29 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/open-domain` |
| `release-rate` | `h2-core` | `PASS` | 52.41 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/release-rate` |
| `crosswind` | `h2-core` | `PASS` | 53.36 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/crosswind` |
| `low-wind` | `h2-core` | `PASS` | 52.51 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/low-wind` |
| `pressure-orifice` | `h2-source-physics` | `PASS` | 14.50 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/pressure-orifice` |
| `real-gas-orifice` | `h2-source-physics` | `PASS` | 14.50 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/real-gas-orifice` |
| `tank-blowdown` | `h2-source-physics` | `PASS` | 14.30 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/tank-blowdown` |
| `real-gas-tank-blowdown` | `h2-source-physics` | `PASS` | 14.15 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/real-gas-tank-blowdown` |
| `pipe-loss` | `h2-source-physics` | `PASS` | 14.35 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/pipe-loss` |
| `linepack-blowdown` | `h2-source-physics` | `PASS` | 15.35 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/linepack-blowdown` |
| `linepack-valve-schedule` | `h2-source-physics` | `PASS` | 14.85 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/linepack-valve-schedule` |
| `tank-farm` | `h2-geometry` | `PASS` | 65.24 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/tank-farm` |
| `stl-multifile` | `h2-geometry` | `PASS` | 51.25 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/stl-multifile` |
| `stl-perfile-transform` | `h2-geometry` | `PASS` | 50.60 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/stl-perfile-transform` |
| `plan-amr-mpi-rank-sweep` | `h2-amr-mpi` | `PASS` | 116.30 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-rank-sweep` |
| `plan-amr-mpi-reduced-long` | `h2-production-scout` | `PASS` | 108.40 | `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-reduced-long` |

## Limitations

- Campaign runner proves orchestration, logging, return-code capture, and required-output collection for selected engineering H2 cases.
- It does not by itself prove production-scale CFD accuracy, real CAD cleanup, scheduler affinity, overnight stability, fire heat-release validation, or reference-data agreement.
