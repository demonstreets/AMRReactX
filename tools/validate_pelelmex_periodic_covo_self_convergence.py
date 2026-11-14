#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader

FIELDS = ("x_velocity", "y_velocity")


def fail(message: str) -> None:
    raise SystemExit(f"pelelmex_periodic_covo_self_convergence FAIL {message}")


def restrict2(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 3:
        nx, ny, nz = arr.shape
        if nx % 2 or ny % 2:
            fail(f"cannot restrict odd grid shape {arr.shape}")
        return arr.reshape(nx // 2, 2, ny // 2, 2, nz).mean(axis=(1, 3))
    if arr.ndim == 2:
        nx, ny = arr.shape
        if nx % 2 or ny % 2:
            fail(f"cannot restrict odd grid shape {arr.shape}")
        return arr.reshape(nx // 2, 2, ny // 2, 2).mean(axis=(1, 3))
    fail(f"unsupported field rank {arr.ndim}")


def l1(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        fail(f"shape mismatch {a.shape} vs {b.shape}")
    value = float(np.mean(np.abs(a - b)))
    if not math.isfinite(value):
        fail("nonfinite L1 difference")
    return value


def read_case(spec: str) -> tuple[int, dict]:
    if "=" not in spec:
        fail(f"case spec must be NX=plotfile, got {spec}")
    n_s, path_s = spec.split("=", 1)
    try:
        n = int(n_s)
    except ValueError:
        fail(f"bad grid size in {spec}")
    path = Path(path_s)
    if not path.is_dir():
        fail(f"missing plotfile {path}")
    return n, amrex_reader.read_plotfile(str(path))


def order(coarse_fine: float, fine_finest: float) -> float:
    if coarse_fine <= 0.0 or fine_finest <= 0.0:
        return float("nan")
    return math.log(coarse_fine / fine_finest, 2.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", action="append", required=True)
    ap.add_argument("--min-order", type=float, default=1.0)
    ap.add_argument("--max-time-spread", type=float, default=1.0e-12)
    args = ap.parse_args()

    cases = dict(read_case(spec) for spec in args.case)
    grids = sorted(cases)
    if len(grids) != 3 or grids[1] != 2 * grids[0] or grids[2] != 2 * grids[1]:
        fail(f"expected three 2x-refined grids, got {grids}")
    times = [float(cases[n]["time"]) for n in grids]
    if max(times) - min(times) > args.max_time_spread:
        fail(f"final times differ too much: {times}")

    metrics = {}
    for name in FIELDS:
        arrays = []
        for n in grids:
            fields = cases[n]["fields"]
            if name not in fields:
                fail(f"missing field {name} for nx={n}")
            arr = np.asarray(fields[name], dtype=float)
            if not np.all(np.isfinite(arr)):
                fail(f"nonfinite field {name} for nx={n}")
            arrays.append(arr)
        e16_32 = l1(arrays[0], restrict2(arrays[1]))
        e32_64 = l1(arrays[1], restrict2(arrays[2]))
        p = order(e16_32, e32_64)
        if not math.isfinite(p) or p < args.min_order:
            fail(f"{name} order={p:.3f} e16_32={e16_32:.8e} e32_64={e32_64:.8e}")
        metrics[name] = (e16_32, e32_64, p)

    pieces = [
        "pelelmex_periodic_covo_self_convergence PASS",
        f"grids={','.join(str(n) for n in grids)}",
        f"time={times[0]:.8e}",
    ]
    for name in FIELDS:
        e16_32, e32_64, p = metrics[name]
        pieces.append(f"{name}_e16_32={e16_32:.8e}")
        pieces.append(f"{name}_e32_64={e32_64:.8e}")
        pieces.append(f"{name}_order={p:.3f}")
    print(" ".join(pieces))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
