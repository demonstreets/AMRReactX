#!/usr/bin/env python3
"""Validate the parallel performance baseline summary."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

REQUIRED = {
    ("engineering", "serial"),
    ("engineering", "mpi"),
    ("engineering", "omp"),
    ("engineering", "hybrid"),
    ("academic", "serial"),
    ("academic", "mpi"),
    ("academic", "omp"),
    ("academic", "hybrid"),
}


def fail(message: str) -> None:
    raise SystemExit(f"parallel_perf_summary_validation FAIL {message}")


def parse_float(value: str, field: str, suite: str, mode: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{suite}/{mode} invalid {field}={value!r}")
    if not math.isfinite(parsed) or parsed <= 0.0:
        fail(f"{suite}/{mode} nonpositive {field}={value!r}")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    path = Path(args.summary)
    if not path.exists():
        fail(f"missing summary {path}")

    rows = list(csv.DictReader(path.open(newline=""), delimiter="\t"))
    if not rows:
        fail("empty summary")
    required_fields = {
        "suite",
        "mode",
        "solver",
        "ranks",
        "threads",
        "wall_elapsed_sec",
        "status",
        "warning",
        "log_dir",
        "run_log",
        "validation_log",
    }
    missing = required_fields.difference(rows[0])
    if missing:
        fail(f"missing fields={','.join(sorted(missing))}")

    seen: set[tuple[str, str]] = set()
    warnings: list[str] = []
    for row in rows:
        suite = row["suite"]
        mode = row["mode"]
        key = (suite, mode)
        if key in seen:
            fail(f"duplicate row {suite}/{mode}")
        seen.add(key)
        if row["status"] != "PASS":
            fail(f"{suite}/{mode} status={row['status']}")
        parse_float(row["wall_elapsed_sec"], "wall_elapsed_sec", suite, mode)
        run_log = Path(row["run_log"])
        if not run_log.exists() or run_log.stat().st_size == 0:
            fail(f"{suite}/{mode} missing/nonempty run_log={run_log}")
        text = run_log.read_text(errors="replace")
        if "AMReX" not in text or "finalized" not in text:
            fail(f"{suite}/{mode} run log missing AMReX finalization")
        if mode != "serial":
            validation_log = Path(row["validation_log"])
            if not validation_log.exists() or validation_log.stat().st_size == 0:
                fail(f"{suite}/{mode} missing validation_log={validation_log}")
            validation = validation_log.read_text(errors="replace")
            if "parallel_smoke_log_validation PASS" not in validation:
                fail(f"{suite}/{mode} missing parallel validation PASS")
        if row["warning"]:
            warnings.append(f"{suite}/{mode}:{row['warning']}")

    missing_keys = REQUIRED.difference(seen)
    if missing_keys:
        fail("missing cases=" + ",".join(f"{a}/{b}" for a, b in sorted(missing_keys)))

    print(
        "parallel_perf_summary_validation PASS "
        f"cases={len(rows)} warnings={len(warnings)} "
        f"warning_list={','.join(warnings) if warnings else 'none'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
