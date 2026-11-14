#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/h2_fire_exp002_pressure_cfd_proxy_report.json}"
python3 tools/write_h2_fire_exp002_pressure_cfd_proxy_report.py --verify-json "$json"
