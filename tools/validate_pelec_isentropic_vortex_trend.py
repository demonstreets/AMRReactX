#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

REQUIRED_COLUMNS = {
    "nx",
    "ny",
    "nz",
    "time",
    "init_linf",
    "density_l1",
    "pressure_l1",
    "u_l1",
    "v_l1",
    "mass_rel",
    "entropy_linf",
}


def fail(message: str) -> None:
    raise SystemExit(f"pelec_isentropic_vortex_trend_validation FAIL {message}")


def as_float(row: dict[str, str], name: str) -> float:
    try:
        value = float(row[name])
    except Exception as exc:
        fail(f"bad {name} for nx={row.get('nx', '?')}: {exc}")
    if not math.isfinite(value):
        fail(f"nonfinite {name} for nx={row.get('nx', '?')}")
    return value


def observed_order(coarse: float, fine: float) -> float:
    if coarse <= 0.0 or fine <= 0.0:
        return float("nan")
    return math.log(coarse / fine, 2.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--expected", default="16,32,64")
    ap.add_argument("--max-init-linf", type=float, default=2.0e-8)
    ap.add_argument("--max-mass-rel", type=float, default=1.0e-10)
    ap.add_argument("--max-time-spread", type=float, default=1.0e-12)
    ap.add_argument("--min-density-drop", type=float, default=1.15)
    ap.add_argument("--min-pressure-drop", type=float, default=1.15)
    ap.add_argument("--min-velocity-drop", type=float, default=1.0)
    ap.add_argument("--max-velocity-l1", type=float, default=2.0e-4)
    ap.add_argument("--min-entropy-drop", type=float, default=10.0)
    args = ap.parse_args()

    path = Path(args.summary)
    if not path.is_file():
        fail(f"missing summary {path}")
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if reader.fieldnames is None:
            fail("empty summary")
        missing = sorted(REQUIRED_COLUMNS.difference(reader.fieldnames))
        if missing:
            fail("summary missing columns " + ",".join(missing))
        rows = list(reader)

    expected = [int(x) for x in args.expected.split(",") if x.strip()]
    if len(rows) != len(expected):
        fail(f"expected {len(expected)} cases, got {len(rows)}")

    parsed: list[dict[str, float]] = []
    for row in rows:
        nx = int(row["nx"])
        ny = int(row["ny"])
        nz = int(row["nz"])
        if nx != ny or nz != 2:
            fail(f"unexpected grid {nx}x{ny}x{nz}")
        parsed.append({
            "nx": float(nx),
            "time": as_float(row, "time"),
            "init_linf": as_float(row, "init_linf"),
            "density_l1": as_float(row, "density_l1"),
            "pressure_l1": as_float(row, "pressure_l1"),
            "velocity_l1": max(as_float(row, "u_l1"), as_float(row, "v_l1")),
            "mass_rel": as_float(row, "mass_rel"),
            "entropy_linf": as_float(row, "entropy_linf"),
        })

    parsed.sort(key=lambda item: item["nx"])
    got = [int(item["nx"]) for item in parsed]
    if got != expected:
        fail(f"expected grids {expected}, got {got}")

    times = [item["time"] for item in parsed]
    if max(times) - min(times) > args.max_time_spread:
        fail(f"final times differ too much: {times}")
    for item in parsed:
        if item["init_linf"] > args.max_init_linf:
            fail(f"init_linf too large at nx={int(item['nx'])}: {item['init_linf']:.8e}")
        if item["mass_rel"] > args.max_mass_rel:
            fail(f"mass_rel too large at nx={int(item['nx'])}: {item['mass_rel']:.8e}")

    density_drop = parsed[0]["density_l1"] / parsed[-1]["density_l1"]
    pressure_drop = parsed[0]["pressure_l1"] / parsed[-1]["pressure_l1"]
    velocity_drop = parsed[0]["velocity_l1"] / parsed[-1]["velocity_l1"]
    entropy_drop = parsed[0]["entropy_linf"] / parsed[-1]["entropy_linf"]
    max_velocity_l1 = max(item["velocity_l1"] for item in parsed)
    if density_drop < args.min_density_drop:
        fail(f"density error did not drop enough coarse/fine={density_drop:.3f}")
    if pressure_drop < args.min_pressure_drop:
        fail(f"pressure error did not drop enough coarse/fine={pressure_drop:.3f}")
    if entropy_drop < args.min_entropy_drop:
        fail(f"entropy error did not drop enough coarse/fine={entropy_drop:.3f}")
    if velocity_drop < args.min_velocity_drop:
        fail(f"velocity error regressed coarse/fine={velocity_drop:.3f}")
    if max_velocity_l1 > args.max_velocity_l1:
        fail(f"velocity_l1 exceeds bound max={max_velocity_l1:.8e}")

    d_orders = [observed_order(parsed[i]["density_l1"], parsed[i + 1]["density_l1"]) for i in range(len(parsed) - 1)]
    p_orders = [observed_order(parsed[i]["pressure_l1"], parsed[i + 1]["pressure_l1"]) for i in range(len(parsed) - 1)]
    v_orders = [observed_order(parsed[i]["velocity_l1"], parsed[i + 1]["velocity_l1"]) for i in range(len(parsed) - 1)]

    print(
        "pelec_isentropic_vortex_trend_validation PASS "
        f"cases={len(parsed)} grids={','.join(str(int(item['nx'])) for item in parsed)} "
        f"time={times[0]:.8e} "
        f"density_l1={','.join(f'{item['density_l1']:.8e}' for item in parsed)} "
        f"pressure_l1={','.join(f'{item['pressure_l1']:.8e}' for item in parsed)} "
        f"velocity_l1={','.join(f'{item['velocity_l1']:.8e}' for item in parsed)} "
        f"entropy_drop={entropy_drop:.3f} max_velocity_l1={max_velocity_l1:.8e} "
        f"density_orders={','.join(f'{x:.3f}' for x in d_orders)} "
        f"pressure_orders={','.join(f'{x:.3f}' for x in p_orders)} "
        f"velocity_orders={','.join(f'{x:.3f}' for x in v_orders)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
