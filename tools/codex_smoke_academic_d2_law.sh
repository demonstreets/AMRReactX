#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT/examples/academic/d2_law"
EXE="$CASE_DIR/PeleC2d.gnu.ex"
INPUT_NAME="${CODEX_D2_LAW_INPUT:-input.codex_smoke}"
INPUT="$CASE_DIR/$INPUT_NAME"
INIT="$CASE_DIR/initsprayfile.dat"
EXPECTED_STEP="${CODEX_D2_LAW_EXPECT_STEP:-2}"
CHECK_TREND="${CODEX_D2_LAW_CHECK_TREND:-0}"
LOG_DIR="${CODEX_D2_LAW_LOG_DIR:-/tmp/codex_d2_law_smoke_$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$LOG_DIR"
RUN_DIR="$(mktemp -d "$LOG_DIR/run.XXXXXX")"
LOG="$LOG_DIR/run.log"

cp "$INPUT" "$RUN_DIR/$INPUT_NAME"
cp "$INIT" "$RUN_DIR/initsprayfile.dat"

if [[ ! -x "$EXE" ]]; then
  echo "[codex-d2-law] missing executable: $EXE" >&2
  echo "[codex-d2-law] build it in $CASE_DIR with: make -j ${JOBS:-2}" >&2
  exit 2
fi

(
  cd "$RUN_DIR"
  "$EXE" "$INPUT_NAME"
) | tee "$LOG"

grep -q "STEP = $EXPECTED_STEP" "$LOG"
grep -q "AMReX .* finalized" "$LOG"
if grep -q "Unused ParmParse Variables" "$LOG"; then
  echo "[codex-d2-law] unexpected unused ParmParse variables" >&2
  exit 3
fi

latest_plot="$(find "$RUN_DIR" -maxdepth 1 -type d -name 'plt*' | sort | tail -1)"
if [[ -z "$latest_plot" ]]; then
  echo "[codex-d2-law] no plotfile was produced" >&2
  exit 4
fi
if [[ ! -f "$latest_plot/particles/Level_0/Particle_H" ]]; then
  echo "[codex-d2-law] plotfile missing particle header: $latest_plot" >&2
  exit 5
fi

latest_ascii="$(find "$RUN_DIR" -maxdepth 1 -type f -name 'spray*.p3d' | sort | tail -1)"
if [[ -z "$latest_ascii" ]]; then
  echo "[codex-d2-law] no spray ASCII file was produced" >&2
  exit 6
fi
awk 'NR==6 { if (NF < 12 || $5 <= 0 || $6 <= 0 || $12 <= 0 || $12 > 1.000001) exit 1 }' "$latest_ascii"

if [[ "$CHECK_TREND" == "1" ]]; then
  first_ascii="$(find "$RUN_DIR" -maxdepth 1 -type f -name 'spray*.p3d' | sort | head -1)"
  python3 - "$first_ascii" "$latest_ascii" <<'PYTREND'
import sys


def record(path):
    vals = open(path, encoding="utf-8").read().strip().splitlines()[-1].split()
    if len(vals) < 12:
        raise SystemExit(f"bad particle line in {path}")
    return float(vals[4]), float(vals[11])


t0, y0 = record(sys.argv[1])
t1, y1 = record(sys.argv[2])
if not (t1 > t0 and y1 < y0 and 0.0 < y1 <= 1.0):
    raise SystemExit(f"D2 trend check failed: T {t0}->{t1}, Y {y0}->{y1}")
print(f"[codex-d2-law] trend T={t0:.12g}->{t1:.12g} Y={y0:.12g}->{y1:.12g}")
PYTREND
fi

echo "[codex-d2-law] PASS log=$LOG run=$(basename "$RUN_DIR") plot=$(basename "$latest_plot") ascii=$(basename "$latest_ascii") step=$EXPECTED_STEP input=$INPUT_NAME"
