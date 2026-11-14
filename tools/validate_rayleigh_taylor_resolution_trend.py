#!/usr/bin/env python3
"""Validate a multi-resolution Rayleigh-Taylor growth trend smoke."""
import argparse
import math
import re
from pathlib import Path

LINE_RE = re.compile(
    r"rayleigh_taylor_growth_validation PASS .*?"
    r"time=(?P<time>[-+0-9.eE]+)\s+"
    r"grid=\((?P<nx>\d+),\s*(?P<ny>\d+)\)\s+"
    r"mode=(?P<mode>\d+)\s+"
    r"initial_amp=(?P<initial_amp>[-+0-9.eE]+)\s+"
    r"final_amp=(?P<final_amp>[-+0-9.eE]+)\s+"
    r"growth_ratio=(?P<growth_ratio>[-+0-9.eE]+)\s+"
    r"growth_rate=(?P<growth_rate>[-+0-9.eE]+)\s+"
    r"mass_rel=(?P<mass_rel>[-+0-9.eE]+)\s+"
    r"vof_mass_rel=(?P<vof_mass_rel>[-+0-9.eE]+)"
)


def parse_log(path):
    text = Path(path).read_text()
    match = LINE_RE.search(text)
    if not match:
        raise SystemExit(f"FAIL: could not parse RT growth metrics from {path}")
    values = match.groupdict()
    out = {"path": str(path)}
    for key in ("nx", "ny", "mode"):
        out[key] = int(values[key])
    for key in (
        "time", "initial_amp", "final_amp", "growth_ratio", "growth_rate",
        "mass_rel", "vof_mass_rel"):
        out[key] = float(values[key])
    return out


def relerr(value, reference):
    return abs(value - reference) / max(abs(reference), 1.0e-300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("growth_logs", nargs="+", help="growth.log files to compare")
    ap.add_argument("--expected-amp", type=float, default=0.05)
    ap.add_argument("--min-growth-ratio", type=float, default=1.02)
    ap.add_argument("--mass-rtol", type=float, default=2.0e-5)
    ap.add_argument("--time-rtol", type=float, default=1.0e-8)
    ap.add_argument("--max-rate-spread", type=float, default=0.60,
                    help="max relative spread of growth rates about their mean")
    ap.add_argument("--max-initial-amp-relerr", type=float, default=0.06)
    args = ap.parse_args()

    cases = sorted((parse_log(path) for path in args.growth_logs), key=lambda c: c["nx"])
    if len(cases) < 3:
        raise SystemExit("FAIL: at least three RT resolutions are required")
    if len({c["nx"] for c in cases}) != len(cases):
        raise SystemExit("FAIL: duplicate RT nx resolutions in trend logs")
    if len({c["mode"] for c in cases}) != 1:
        raise SystemExit("FAIL: mixed RT perturbation modes in trend logs")

    times = [c["time"] for c in cases]
    t_mean = sum(times) / len(times)
    for c in cases:
        if not math.isfinite(c["time"]) or relerr(c["time"], t_mean) > args.time_rtol:
            raise SystemExit(
                f"FAIL: final times are not aligned case={c['nx']}x{c['ny']} "
                f"time={c['time']:.12g} mean={t_mean:.12g}")
        if c["ny"] != 2 * c["nx"]:
            raise SystemExit(f"FAIL: unexpected RT aspect grid {c['nx']}x{c['ny']}")
        if c["mass_rel"] > args.mass_rtol or c["vof_mass_rel"] > args.mass_rtol:
            raise SystemExit(
                f"FAIL: mass drift at {c['nx']}x{c['ny']} "
                f"rho={c['mass_rel']:.6g} rho_adv_0={c['vof_mass_rel']:.6g}")
        if c["growth_ratio"] < args.min_growth_ratio:
            raise SystemExit(
                f"FAIL: insufficient RT growth at {c['nx']}x{c['ny']} "
                f"ratio={c['growth_ratio']:.6g}")
        if not math.isfinite(c["growth_rate"]) or c["growth_rate"] <= 0.0:
            raise SystemExit(
                f"FAIL: non-positive RT growth rate at {c['nx']}x{c['ny']} "
                f"rate={c['growth_rate']:.6g}")
        amp_err = relerr(c["initial_amp"], args.expected_amp)
        if amp_err > args.max_initial_amp_relerr:
            raise SystemExit(
                f"FAIL: initial mode amplitude at {c['nx']}x{c['ny']} "
                f"is not close to seed {args.expected_amp}: "
                f"amp={c['initial_amp']:.8g} relerr={amp_err:.6g}")

    amp_errors = [relerr(c["initial_amp"], args.expected_amp) for c in cases]
    if amp_errors[-1] > amp_errors[0]:
        raise SystemExit(
            "FAIL: finest-grid initial interface projection is farther from "
            f"the seeded amplitude than the coarsest grid: {amp_errors[-1]:.6g} "
            f"> {amp_errors[0]:.6g}")

    rates = [c["growth_rate"] for c in cases]
    rate_mean = sum(rates) / len(rates)
    rate_spread = (max(rates) - min(rates)) / max(abs(rate_mean), 1.0e-300)
    if rate_spread > args.max_rate_spread:
        raise SystemExit(
            f"FAIL: RT growth-rate spread is too large: {rate_spread:.6g} "
            f"> {args.max_rate_spread:.6g} rates={','.join(f'{r:.8g}' for r in rates)}")

    grids = ",".join(f"{c['nx']}x{c['ny']}" for c in cases)
    ratios = ",".join(f"{c['growth_ratio']:.8g}" for c in cases)
    rates_s = ",".join(f"{c['growth_rate']:.8g}" for c in cases)
    amps = ",".join(f"{c['initial_amp']:.8g}->{c['final_amp']:.8g}" for c in cases)
    print(
        "rayleigh_taylor_resolution_trend PASS "
        f"grids={grids} time={t_mean:.12g} mode={cases[0]['mode']} "
        f"amp={amps} growth_ratios={ratios} growth_rates={rates_s} "
        f"rate_spread={rate_spread:.6g} "
        f"mass_max={max(c['mass_rel'] for c in cases):.6g} "
        f"vof_mass_max={max(c['vof_mass_rel'] for c in cases):.6g}")


if __name__ == "__main__":
    main()
