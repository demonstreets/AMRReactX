#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

REQUIRED = {
    "nx", "ny", "nz", "time", "init_linf", "density_l1", "pressure_l1",
    "u_l1", "v_l1", "mass_rel", "entropy_linf"
}


def fail(message: str) -> None:
    raise SystemExit(f"pelec_isentropic_vortex_exact_convergence FAIL {message}")


def as_float(row: dict[str, str], name: str) -> float:
    try:
        value = float(row[name])
    except Exception as exc:
        fail(f"bad {name}: {exc}")
    if not math.isfinite(value):
        fail(f"nonfinite {name}")
    return value


def order(a: float, b: float) -> float:
    if a <= 0.0 or b <= 0.0:
        return float("nan")
    return math.log(a / b, 2.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--expected", default="16,32,64")
    ap.add_argument("--max-init-linf", type=float, default=1.0e-12)
    ap.add_argument("--max-mass-rel", type=float, default=1.0e-10)
    ap.add_argument("--min-density-order-32-64", type=float, default=1.5)
    ap.add_argument("--min-pressure-order-32-64", type=float, default=1.5)
    ap.add_argument("--min-velocity-order-32-64", type=float, default=1.5)
    ap.add_argument("--min-entropy-drop", type=float, default=10.0)
    ap.add_argument("--max-velocity-l1", type=float, default=5.0e-4)
    args = ap.parse_args()

    path = Path(args.summary)
    if not path.is_file():
        fail(f"missing summary {path}")
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if reader.fieldnames is None:
            fail("empty summary")
        missing = sorted(REQUIRED.difference(reader.fieldnames))
        if missing:
            fail("summary missing columns " + ",".join(missing))
        rows = list(reader)

    expected = [int(x) for x in args.expected.split(",") if x.strip()]
    if len(rows) != len(expected):
        fail(f"expected {len(expected)} rows, got {len(rows)}")

    parsed = []
    for row in rows:
        nx = int(row["nx"])
        ny = int(row["ny"])
        nz = int(row["nz"])
        if nx != ny or nz != 2:
            fail(f"unexpected grid {nx}x{ny}x{nz}")
        parsed.append({
            "nx": nx,
            "time": as_float(row, "time"),
            "init_linf": as_float(row, "init_linf"),
            "density_l1": as_float(row, "density_l1"),
            "pressure_l1": as_float(row, "pressure_l1"),
            "velocity_l1": max(as_float(row, "u_l1"), as_float(row, "v_l1")),
            "mass_rel": as_float(row, "mass_rel"),
            "entropy_linf": as_float(row, "entropy_linf"),
        })
    parsed.sort(key=lambda item: item["nx"])
    if [item["nx"] for item in parsed] != expected:
        fail(f"expected grids {expected}, got {[item['nx'] for item in parsed]}")

    for item in parsed:
        if item["init_linf"] > args.max_init_linf:
            fail(f"init_linf too large at nx={item['nx']}: {item['init_linf']:.8e}")
        if item["mass_rel"] > args.max_mass_rel:
            fail(f"mass_rel too large at nx={item['nx']}: {item['mass_rel']:.8e}")
        if item["velocity_l1"] > args.max_velocity_l1:
            fail(f"velocity_l1 too large at nx={item['nx']}: {item['velocity_l1']:.8e}")

    d16_32 = order(parsed[0]["density_l1"], parsed[1]["density_l1"])
    d32_64 = order(parsed[1]["density_l1"], parsed[2]["density_l1"])
    p16_32 = order(parsed[0]["pressure_l1"], parsed[1]["pressure_l1"])
    p32_64 = order(parsed[1]["pressure_l1"], parsed[2]["pressure_l1"])
    v16_32 = order(parsed[0]["velocity_l1"], parsed[1]["velocity_l1"])
    v32_64 = order(parsed[1]["velocity_l1"], parsed[2]["velocity_l1"])
    entropy_drop = parsed[0]["entropy_linf"] / parsed[2]["entropy_linf"]

    if d32_64 < args.min_density_order_32_64:
        fail(f"density 32/64 order too low: {d32_64:.3f}")
    if p32_64 < args.min_pressure_order_32_64:
        fail(f"pressure 32/64 order too low: {p32_64:.3f}")
    if v32_64 < args.min_velocity_order_32_64:
        fail(f"velocity 32/64 order too low: {v32_64:.3f}")
    if entropy_drop < args.min_entropy_drop:
        fail(f"entropy drop too low: {entropy_drop:.3f}")

    print(
        "pelec_isentropic_vortex_exact_convergence PASS "
        f"grids={','.join(str(item['nx']) for item in parsed)} time={parsed[0]['time']:.8e} "
        f"density_l1={','.join(f'{item['density_l1']:.8e}' for item in parsed)} "
        f"pressure_l1={','.join(f'{item['pressure_l1']:.8e}' for item in parsed)} "
        f"velocity_l1={','.join(f'{item['velocity_l1']:.8e}' for item in parsed)} "
        f"density_orders={d16_32:.3f},{d32_64:.3f} "
        f"pressure_orders={p16_32:.3f},{p32_64:.3f} "
        f"velocity_orders={v16_32:.3f},{v32_64:.3f} "
        f"entropy_drop={entropy_drop:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
