#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader


def fail(message: str) -> None:
    raise SystemExit(f"bfs_loglaw_profile_plotfile_validation FAIL {message}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plotfile", required=True)
    ap.add_argument("--uref", type=float, default=2.0)
    ap.add_argument("--zref", type=float, default=10.0)
    ap.add_argument("--z0", type=float, default=0.03)
    ap.add_argument("--tol", type=float, default=2.0e-12)
    ap.add_argument("--min-shear", type=float, default=0.03)
    args = ap.parse_args()

    data = amrex_reader.read_plotfile(args.plotfile)
    fields = data["fields"]
    for name in ("x_velocity", "y_velocity"):
        if name not in fields:
            fail(f"missing field {name}")
    u = np.asarray(fields["x_velocity"], dtype=float)
    v = np.asarray(fields["y_velocity"], dtype=float)
    y = np.asarray(data.get("y"), dtype=float)
    if u.ndim != 2 or y.ndim != 1 or u.shape[1] != y.size:
        fail(f"unexpected shapes u={u.shape} y={y.shape}")
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        fail("nonfinite velocity field")
    if args.z0 <= 0.0 or args.zref <= args.z0:
        fail("invalid log-law parameters")

    sample_y = np.maximum(y, args.z0)
    expected = args.uref * np.log(sample_y / args.z0) / np.log(args.zref / args.z0)
    err = np.abs(u - expected[np.newaxis, :])
    linf = float(np.max(err))
    if linf > args.tol:
        fail(f"x_velocity profile mismatch linf={linf:.8e}")
    v_linf = float(np.max(np.abs(v)))
    if v_linf > args.tol:
        fail(f"nonzero y_velocity linf={v_linf:.8e}")
    shear = float(expected[-1] - expected[0])
    if shear < args.min_shear:
        fail(f"log-law shear too small: {shear:.8e}")
    if not np.all(np.diff(expected) >= -1.0e-15):
        fail("expected profile is not monotone")

    print(
        "bfs_loglaw_profile_plotfile_validation PASS "
        f"time={float(data['time']):.8e} nx={u.shape[0]} ny={u.shape[1]} "
        f"u_min={float(u.min()):.8e} u_max={float(u.max()):.8e} "
        f"expected_min={float(expected.min()):.8e} expected_max={float(expected.max()):.8e} "
        f"profile_linf={linf:.8e} v_linf={v_linf:.8e} shear={shear:.8e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
