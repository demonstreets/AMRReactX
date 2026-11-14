# Engineering H2 Production-Mesh MPI Scaling Scout

Status: `PASS-SCALING-SCOUT`
Rank series: `[4, 8, 16]`
Generated UTC: `2026-07-20T07:23:36+00:00`
Base cells: `65536`
AMR equivalent fine cells: `524288`
Max step: `120`
Cloud rel diff spread: `0.00000000e+00`
Peak rel diff spread: `0.00000000e+00`
Max AMR advance seconds ratio: `1.83771921e+00`
Baseline speedup 4-to-16: `1.82066093e+00`
AMR speedup 4-to-16: `1.82631363e+00`
16-rank AMR finest FAB count: `73`

## Rank Rows

| Ranks | Baseline s | AMR s | AMR/baseline | Cloud rel | Peak rel | AMR FABs | Baseline speedup | AMR speedup |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 68.926661 | 119.957525 | 1.740365 | 3.80952381e-02 | 4.31073584e-02 | 12 | 1.000000 | 1.000000 |
| 8 | 40.216922 | 73.907411 | 1.837719 | 3.80952381e-02 | 4.31073584e-02 | 12 | 1.713872 | 1.623078 |
| 16 | 37.858044 | 65.682872 | 1.734978 | 3.80952381e-02 | 4.31073584e-02 | 73 | 1.820661 | 1.826314 |

## Evidence Files

- `production_mesh_4rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json` sha256 `ea806a6dd56bb0ed`
- `production_mesh_8rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json` sha256 `6b4c05d1d48a0205`
- `production_mesh_16rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json` sha256 `976464cb31a86f6c`
- `production_mesh_4rank_case_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/files/engineering_case_report.json` sha256 `87e92bde8929c2bb`
- `production_mesh_8rank_case_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/files/engineering_case_report.json` sha256 `8f7a51aaf6440aca`
- `production_mesh_16rank_case_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/files/engineering_case_report.json` sha256 `b690854ed0bf4157`

## Limitations

- This is a short interactive production-mesh scaling scout, not a scheduler-managed performance study.
- It verifies rank consistency, bounded AMR-vs-baseline hazard drift, FAB distribution, and runtime improvement from 4 to 16 ranks on one synthetic H2 leak case.
- It does not prove production-size scaling, queue/affinity behavior, hybrid MPI/OpenMP safety, overnight stability, real-CAD geometry, or external reference-data agreement.
