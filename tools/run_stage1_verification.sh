#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "tools/run_stage1_verification.sh is kept for compatibility."
echo "Forwarding to tools/run_stage2_verification.sh."

exec bash "${ROOT_DIR}/tools/run_stage2_verification.sh"
