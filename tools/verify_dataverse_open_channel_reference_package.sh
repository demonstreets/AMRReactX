#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

python3 tools/write_dataverse_open_channel_reference_package_report.py \
  --verify-json docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/dataverse_open_channel_reference_package_report.json
