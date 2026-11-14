#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

json="docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805/engineering_h2_pipe_rack_delayed_ignition_cuda_report.json"

python3 tools/write_engineering_h2_pipe_rack_delayed_ignition_cuda_report.py --verify-json "$json"
