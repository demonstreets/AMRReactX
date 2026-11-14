#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REPORT="docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json"

python3 tools/write_h2_fire_mdpi_radiation_integrated_cfd_proxy_report.py --verify-json "$REPORT"

echo "[h2-fire-mdpi-radiation-integrated-cfd-proxy] PASS integrated radiation proxy report"
