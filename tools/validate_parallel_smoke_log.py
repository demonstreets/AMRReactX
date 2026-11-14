#!/usr/bin/env python3
"""Validate AMReX/PeleC/PeleLMeX MPI/OpenMP smoke logs."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"parallel_smoke_log_validation FAIL {message}")


def find_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text)
    if match is None:
        return None
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, help="run.log to validate")
    parser.add_argument("--mode", choices=("mpi", "omp", "hybrid"), required=True)
    parser.add_argument("--solver", choices=("pelelmex", "pelec"), required=True)
    parser.add_argument("--expected-ranks", type=int, default=None)
    parser.add_argument("--expected-threads", type=int, default=None)
    parser.add_argument("--require-step", default=None, help="literal step marker to require")
    parser.add_argument("--require-final-time", action="store_true")
    parser.add_argument("--allow-thread-support-zero", action="store_true")
    args = parser.parse_args()

    log_path = Path(args.log)
    text = log_path.read_text(errors="replace")

    ranks = find_int(r"MPI initialized with\s+(\d+)\s+MPI processes", text)
    threads = find_int(r"OMP initialized with\s+(\d+)\s+OMP threads", text)
    thread_level = find_int(r"MPI initialized with thread support level\s+(\d+)", text)
    final_time = re.search(r"Final simulation time:\s*([^\s]+)", text)
    finalized = re.search(r"AMReX .* finalized", text) is not None

    if args.mode in ("mpi", "hybrid"):
        require(ranks is not None, "missing MPI initialization line")
        if args.expected_ranks is not None:
            require(ranks == args.expected_ranks, f"expected_ranks={args.expected_ranks} observed={ranks}")
    else:
        require(ranks is None or ranks == 1, f"unexpected MPI rank count in OMP mode observed={ranks}")

    if args.mode in ("omp", "hybrid"):
        require(threads is not None, "missing OpenMP initialization line")
        if args.expected_threads is not None:
            require(threads == args.expected_threads, f"expected_threads={args.expected_threads} observed={threads}")
    else:
        require(threads is None or threads == 1, f"unexpected OMP thread count in MPI mode observed={threads}")

    if args.mode == "hybrid":
        if thread_level == 0 and not args.allow_thread_support_zero:
            require(False, "MPI thread support level is 0")

    if args.require_final_time:
        require(final_time is not None, "missing final simulation time")
    if args.require_step is not None:
        require(args.require_step in text, f"missing required step marker {args.require_step!r}")
    require(finalized, "missing AMReX finalized marker")

    warning = ""
    if thread_level == 0:
        warning = " warning=mpi_thread_support_level_0"
    elif thread_level is not None:
        warning = f" thread_support_level={thread_level}"

    print(
        "parallel_smoke_log_validation PASS "
        f"solver={args.solver} mode={args.mode} ranks={ranks if ranks is not None else 'na'} "
        f"threads={threads if threads is not None else 'na'} "
        f"final_time={final_time.group(1) if final_time else 'na'} finalized=1{warning}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
