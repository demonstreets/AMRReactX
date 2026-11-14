# Checkpoint: engineering H2 release evidence pack

Date: 2026-07-20 UTC
Scope: durable project-local evidence packaging for the full engineering H2 production smoke campaign.

## Context

The full `engineering-h2-production` smoke-scale campaign had already passed with 16/16 cases and a compact project-local campaign manifest. The remaining reproducibility gap was that the original runner summary, case logs, and required output files were still primarily rooted in `/tmp`. This checkpoint records a durable release evidence pack that preserves the runner-declared evidence inside the repository audit tree and can be verified later without re-reading the original `/tmp` case output tree.

## Tool added

Added:

```text
tools/package_engineering_h2_release_evidence.py
```

The tool supports:

```bash
python3 tools/package_engineering_h2_release_evidence.py package ...
python3 tools/package_engineering_h2_release_evidence.py verify ...
```

Package mode verifies/copies:

- campaign runner summary JSON/Markdown;
- campaign manifest JSON/Markdown;
- every case `campaign_case.log`;
- every runner-declared required output file;
- required-output SHA-256 integrity during copy;
- wrapper-script SHA-256 values from the current repository;
- unique case names, PASS status, zero return codes, no missing required files, and no runner-detected failure markers.

Verify mode revalidates the project-local pack manifest and all packed files by SHA-256. It does not require the original `/tmp` source files, but it still checks wrapper-script hashes against the current repository state. Text files are sanitized during packaging by replacing the absolute repository root and user-home prefix with `${REPO_ROOT}` and `${USER_HOME}` while preserving source SHA-256 values separately from packed SHA-256 values.

## Pack command

```bash
python3 tools/package_engineering_h2_release_evidence.py package \
  --run-summary /tmp/codex_engineering_h2_campaign_full_20260720/campaign_run_summary.json \
  --campaign-manifest /tmp/codex_engineering_h2_campaign_full_20260720/campaign_manifest.json \
  --output-root docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack
```

Result:

```text
engineering_h2_release_evidence_pack PASS cases=16 output=docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack manifest=docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json
```

## Verify command

```bash
python3 tools/package_engineering_h2_release_evidence.py verify \
  --pack-manifest docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json
```

Result:

```text
engineering_h2_release_evidence_pack VERIFY-PASS cases=16 manifest=docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json
```

## Pack spot-check

```text
pack PASS 16 5 files 44 bytes 732880
pack_sha 0737ac2c6baa710b
readme_sha c3b257a1b247dce9
source_summary 7a4c5fea708e4f77
first_case open-domain 5 92d4222737eafb17 sanitized=True
last_case plan-amr-mpi-reduced-long 3 4166ac92139e9683,c90c9b7877eacf7f,f0bc45cc80939b17
suites h2-core,h2-source-physics,h2-geometry,h2-amr-mpi,h2-production-scout
```

The pack contains 44 sanitized project-local files under:

```text
docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack
```

## Documentation updated

Updated:

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

The audit now states that the full 16-case `engineering-h2-production` smoke-scale campaign is not only PASS, but also preserved as a project-local release evidence pack with offline verification.

## Limitations

This pack improves reproducibility and handoff, but it remains evidence packaging for smoke-scale runs. It does not include full AMReX plotfile directories and does not close production-size meshes, overnight stability, scheduler/affinity validation, fire heat-release validation, real CAD cleanup, reference-data agreement, detonation parity, or non-H2 engineering scenario parity.
