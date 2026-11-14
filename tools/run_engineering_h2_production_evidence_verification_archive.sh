#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

out_dir="${CODEX_ENGINEERING_H2_VERIFY_ARCHIVE_DIR:-docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720}"
log_path="$out_dir/verification.log"
raw_log_path="$out_dir/verification.raw.log"
report_json="$out_dir/production_evidence_verification_report.json"
report_md="$out_dir/production_evidence_verification_report.md"
mkdir -p "$out_dir"

set +e
CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE \
  tools/verify_engineering_h2_production_evidence.sh 2>&1 | tee "$raw_log_path"
verify_rc=${PIPESTATUS[0]}
set -e

python3 - "$repo_root" "$raw_log_path" "$log_path" "$verify_rc" <<'PYSANITIZE'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1]).resolve()
raw_log = Path(sys.argv[2])
log_path = Path(sys.argv[3])
verify_rc = sys.argv[4]
text = raw_log.read_text(encoding='utf-8', errors='replace')
text = text.replace(str(repo_root), '${REPO_ROOT}')
text = text.replace(str(Path.home()), '${USER_HOME}')
if not text.endswith('\n'):
    text += '\n'
text += f'CODEX_VERIFY_RC:{verify_rc}\n'
log_path.write_text(text, encoding='utf-8')
PYSANITIZE
rm -f "$raw_log_path"

if [[ "$verify_rc" -ne 0 ]]; then
  printf '[engineering-h2-archive] FAIL verifier returned %s; sanitized log=%s\n' "$verify_rc" "$log_path" >&2
  exit "$verify_rc"
fi

report_args=(
  --log "$log_path"
  --returncode "$verify_rc"
  --output-json "$report_json"
  --output-md "$report_md"
)
if [[ "${CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST:-${CODEX_ENGINEERING_VERIFY_SKIP_CTEST:-FALSE}}" == TRUE ]]; then
  report_args+=(--no-require-ctest)
fi
python3 tools/write_engineering_h2_production_evidence_verification_report.py "${report_args[@]}"
python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json "$report_json"

printf '[engineering-h2-archive] PASS log=%s report=%s\n' "$log_path" "$report_json"
