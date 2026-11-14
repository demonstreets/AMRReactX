#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader


def fail(message: str) -> None:
    raise SystemExit(f"pelelmex_hotbubble_plotfile_validation FAIL {message}")


def field(data: dict, name: str) -> np.ndarray:
    fields = data["fields"]
    if name not in fields:
        fail(f"missing field {name}")
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        fail(f"nonfinite field {name}")
    return arr


def total_mass(data: dict) -> float:
    density = field(data, "density")
    dx = data.get("dx") or data.get("grid", {}).get("dx")
    if not dx:
        fail("missing plotfile spacing")
    dv = float(np.prod(dx[: density.ndim]))
    return float(np.sum(density) * dv)


def hot_centroid_y(data: dict, threshold: float) -> float:
    temp = field(data, "temp")
    y = np.asarray(data.get("y"), dtype=float)
    if y.ndim != 1 or y.size != temp.shape[1]:
        fail("missing/inconsistent y coordinates")
    hot = temp > threshold
    if not np.any(hot):
        fail(f"no hot cells above {threshold}")
    _, yy = np.meshgrid(np.arange(temp.shape[0]), y, indexing="ij")
    return float(np.mean(yy[hot]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--initial", required=True)
    ap.add_argument("--final", required=True)
    ap.add_argument("--expected-time", type=float, default=0.002)
    ap.add_argument("--time-tol", type=float, default=1.0e-12)
    ap.add_argument("--hot-threshold", type=float, default=350.0)
    ap.add_argument("--min-final-velocity", type=float, default=1.0e-4)
    ap.add_argument("--max-mass-rel", type=float, default=1.0e-6)
    args = ap.parse_args()

    initial = amrex_reader.read_plotfile(args.initial)
    final = amrex_reader.read_plotfile(args.final)
    if abs(float(initial["time"])) > args.time_tol:
        fail(f"initial time is not zero: {initial['time']}")
    if abs(float(final["time"]) - args.expected_time) > args.time_tol:
        fail(f"final time {final['time']} != expected {args.expected_time}")

    temp0 = field(initial, "temp")
    temp1 = field(final, "temp")
    rho0 = field(initial, "density")
    rho1 = field(final, "density")
    vx0 = field(initial, "x_velocity")
    vy0 = field(initial, "y_velocity")
    vx1 = field(final, "x_velocity")
    vy1 = field(final, "y_velocity")

    if temp0.shape != temp1.shape:
        fail(f"shape changed {temp0.shape} -> {temp1.shape}")
    if temp0.min() < 299.0 or temp0.max() < 440.0:
        fail(f"initial hot bubble missing temp_range={temp0.min()}:{temp0.max()}")
    if rho0.min() <= 0.0 or rho1.min() <= 0.0:
        fail("nonpositive density")
    hot_idx = np.unravel_index(int(np.argmax(temp0)), temp0.shape)
    if not (rho0[hot_idx] < rho0.mean()):
        fail("hot cell is not lighter than domain mean")
    if max(float(np.max(np.abs(vx0))), float(np.max(np.abs(vy0)))) > 1.0e-14:
        fail("initial velocity is not zero")
    velocity_linf = max(float(np.max(np.abs(vx1))), float(np.max(np.abs(vy1))))
    if velocity_linf < args.min_final_velocity:
        fail(f"final velocity too small: {velocity_linf}")

    species_sum_err = None
    if "Y(O2)" in final["fields"] and "Y(N2)" in final["fields"]:
        ysum = field(final, "Y(O2)") + field(final, "Y(N2)")
        species_sum_err = float(np.max(np.abs(ysum - 1.0)))
        if species_sum_err > 1.0e-12:
            fail(f"species mass fractions do not close: {species_sum_err}")

    mass0 = total_mass(initial)
    mass1 = total_mass(final)
    mass_rel = abs(mass1 - mass0) / max(abs(mass0), 1.0e-300)
    if mass_rel > args.max_mass_rel:
        fail(f"mass drift too large: {mass_rel}")

    hot0 = int(np.count_nonzero(temp0 > args.hot_threshold))
    hot1 = int(np.count_nonzero(temp1 > args.hot_threshold))
    cy0 = hot_centroid_y(initial, args.hot_threshold)
    cy1 = hot_centroid_y(final, args.hot_threshold)
    if hot0 <= 0 or hot1 <= 0:
        fail("hot bubble disappeared")

    pieces = [
        "pelelmex_hotbubble_plotfile_validation PASS",
        f"time={float(final['time']):.8e}",
        f"temp0_range={float(temp0.min()):.8e}:{float(temp0.max()):.8e}",
        f"temp1_range={float(temp1.min()):.8e}:{float(temp1.max()):.8e}",
        f"rho0_range={float(rho0.min()):.8e}:{float(rho0.max()):.8e}",
        f"rho1_range={float(rho1.min()):.8e}:{float(rho1.max()):.8e}",
        f"velocity_linf={velocity_linf:.8e}",
        f"vy_linf={float(np.max(np.abs(vy1))):.8e}",
        f"mass_rel={mass_rel:.8e}",
        f"hot_cells={hot0}->{hot1}",
        f"hot_centroid_y={cy0:.8e}->{cy1:.8e}",
    ]
    if species_sum_err is not None:
        pieces.append(f"species_sum_err={species_sum_err:.8e}")
    print(" ".join(pieces))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
