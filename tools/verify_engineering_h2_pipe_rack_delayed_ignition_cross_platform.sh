#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

json="docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805/engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json"

python3 tools/write_engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.py --verify-json "$json"
