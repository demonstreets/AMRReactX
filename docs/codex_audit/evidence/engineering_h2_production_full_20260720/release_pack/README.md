# Engineering H2 Production Release Evidence Pack

Status: `PASS`
Campaign: `engineering-h2-production-full-20260720`
Suite: `engineering-h2-production`
Generated UTC: `2026-07-23T02:12:23+00:00`
Case count: `16`
Suites: `h2-core, h2-source-physics, h2-geometry, h2-amr-mpi, h2-production-scout`

## Source Files

- `campaign_run_summary_json`: `metadata/campaign_run_summary.json` sha256 `7a4c5fea708e4f77`
- `campaign_run_summary_md`: `metadata/campaign_run_summary.md` sha256 `9e6fccc59cf91335`
- `campaign_manifest_json`: `metadata/campaign_manifest.json` sha256 `b42719b95f920174`
- `campaign_manifest_md`: `metadata/campaign_manifest.md` sha256 `e8b3e79cb930942b`

## Cases

### open-domain

- Suite: `h2-core`
- Duration seconds: `26.29`
- Script: `tools/codex_smoke_engineering_h2_leak_open_domain.sh`
- Script SHA-256: `48a7432fdb66b15c`
- Case log sanitized: `True`
- Required files: `5`
- Required SHA-256 prefixes: `18d8c109035843c8, 967a00cf3d2d645a, a5f8e50037f049ca, bd719f3055c884f0, 3ca5aee1813fe085`

### release-rate

- Suite: `h2-core`
- Duration seconds: `52.41`
- Script: `tools/codex_smoke_engineering_h2_leak_open_domain_release_rate.sh`
- Script SHA-256: `b4a74a936c741e0f`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `aec5656d84f2cf1c`

### crosswind

- Suite: `h2-core`
- Duration seconds: `53.36`
- Script: `tools/codex_smoke_engineering_h2_leak_open_domain_crosswind.sh`
- Script SHA-256: `0dc71dcdfd7b2c13`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `2a86d4dff9f2455a`

### low-wind

- Suite: `h2-core`
- Duration seconds: `52.51`
- Script: `tools/codex_smoke_engineering_h2_leak_open_domain_low_wind.sh`
- Script SHA-256: `8c3e9a9ab1aa6e51`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `d9fe423b3037f931`

### pressure-orifice

- Suite: `h2-source-physics`
- Duration seconds: `14.50`
- Script: `tools/codex_smoke_engineering_h2_leak_pressure_orifice.sh`
- Script SHA-256: `cc2fcfa40143114f`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `6870743ae13b6841`

### real-gas-orifice

- Suite: `h2-source-physics`
- Duration seconds: `14.50`
- Script: `tools/codex_smoke_engineering_h2_leak_real_gas_orifice.sh`
- Script SHA-256: `4cebd1f06c3f9a94`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `ba9b0135e4930140`

### tank-blowdown

- Suite: `h2-source-physics`
- Duration seconds: `14.30`
- Script: `tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh`
- Script SHA-256: `ccd1d6798e38fd89`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `49d4b7d71032b726`

### real-gas-tank-blowdown

- Suite: `h2-source-physics`
- Duration seconds: `14.15`
- Script: `tools/codex_smoke_engineering_h2_leak_real_gas_tank_blowdown.sh`
- Script SHA-256: `fd1002a6293036aa`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `f3783cc5c09db9a6`

### pipe-loss

- Suite: `h2-source-physics`
- Duration seconds: `14.35`
- Script: `tools/codex_smoke_engineering_h2_leak_pipe_loss.sh`
- Script SHA-256: `1c85ab6bdfa1d53c`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `cf59117e435c14be`

### linepack-blowdown

- Suite: `h2-source-physics`
- Duration seconds: `15.35`
- Script: `tools/codex_smoke_engineering_h2_leak_linepack_blowdown.sh`
- Script SHA-256: `6b90aad9ca33bc9b`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `5b2190d73cc08348`

### linepack-valve-schedule

- Suite: `h2-source-physics`
- Duration seconds: `14.85`
- Script: `tools/codex_smoke_engineering_h2_leak_linepack_valve_schedule.sh`
- Script SHA-256: `40fdec70122f724e`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `674bcffed1a16c6e`

### tank-farm

- Suite: `h2-geometry`
- Duration seconds: `65.24`
- Script: `tools/codex_smoke_engineering_h2_leak_tank_farm.sh`
- Script SHA-256: `a63ac2acb05cf895`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `d1fde805798ba16d`

### stl-multifile

- Suite: `h2-geometry`
- Duration seconds: `51.25`
- Script: `tools/codex_smoke_engineering_h2_leak_stl_multifile_obstacle.sh`
- Script SHA-256: `5f31f54ea00426af`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `c86da1e5209ade2d`

### stl-perfile-transform

- Suite: `h2-geometry`
- Duration seconds: `50.60`
- Script: `tools/codex_smoke_engineering_h2_leak_stl_perfile_transform.sh`
- Script SHA-256: `2f111bd7df792b77`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `853c049d0e3353d2`

### plan-amr-mpi-rank-sweep

- Suite: `h2-amr-mpi`
- Duration seconds: `116.30`
- Script: `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_rank_sweep.sh`
- Script SHA-256: `b5664c13be8b0b76`
- Case log sanitized: `True`
- Required files: `1`
- Required SHA-256 prefixes: `82524eb74f6afcaa`

### plan-amr-mpi-reduced-long

- Suite: `h2-production-scout`
- Duration seconds: `108.40`
- Script: `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh`
- Script SHA-256: `e26bddf6ce6743ab`
- Case log sanitized: `True`
- Required files: `3`
- Required SHA-256 prefixes: `4166ac92139e9683, c90c9b7877eacf7f, f0bc45cc80939b17`

## Limitations

- This pack preserves runner summaries, case logs, required output files, and SHA-256 hashes for the smoke-scale engineering H2 production campaign.
- It does not include full AMReX plotfile directories or prove production-size accuracy, scheduler affinity, overnight stability, fire heat-release validation, or reference-data agreement.
