#!/usr/bin/env python3
"""Validate a Rayleigh-Taylor run and measure the seeded interface mode."""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader


def load(path, alpha_tol):
    plot = amrex_reader.read_plotfile(path)
    required = ("density", "rho_e", "Temp", "rho_adv_0")
    missing = [name for name in required if name not in plot["fields"]]
    if missing:
        raise SystemExit(f"FAIL: {path} missing fields {missing}")
    rho = np.asarray(plot["fields"]["density"])
    rho_e = np.asarray(plot["fields"]["rho_e"])
    temp = np.asarray(plot["fields"]["Temp"])
    adv = np.asarray(plot["fields"]["rho_adv_0"])
    for name, arr in (("density", rho), ("rho_e", rho_e), ("Temp", temp),
                      ("rho_adv_0", adv)):
        if not np.isfinite(arr).all():
            raise SystemExit(f"FAIL: non-finite {path} field {name}")
    if float(rho.min()) <= 0 or float(rho_e.min()) <= 0 or float(temp.min()) <= 0:
        raise SystemExit(
            f"FAIL: nonphysical {path} state rho_min={rho.min():.6g} "
            f"rho_e_min={rho_e.min():.6g} T_min={temp.min():.6g}")
    alpha = adv / rho
    if float(alpha.min()) < -alpha_tol or float(alpha.max()) > 1.0 + alpha_tol:
        raise SystemExit(
            f"FAIL: alpha out of bounds {path} "
            f"range={alpha.min():.6g}:{alpha.max():.6g}")
    return plot, rho, alpha


def interface_mode(plot, alpha, mode):
    nx = round((plot["prob_hi"][0] - plot["prob_lo"][0]) / plot["dx"][0])
    ny = round((plot["prob_hi"][1] - plot["prob_lo"][1]) / plot["dx"][1])
    if alpha.shape != (nx, ny):
        raise SystemExit(
            f"FAIL: reader/grid mismatch shape={alpha.shape} expected={(nx, ny)}")
    # Heavy fluid occupies y above the interface, so its column volume gives
    # y_interface = y_hi - integral(alpha dy), including mixed cells.
    y_interface = plot["prob_hi"][1] - alpha.sum(axis=1) * plot["dx"][1]
    x = plot["prob_lo"][0] + (np.arange(nx) + 0.5) * plot["dx"][0]
    phase = 2.0 * np.pi * mode * (x - plot["prob_lo"][0]) / (
        plot["prob_hi"][0] - plot["prob_lo"][0])
    coefficient = 2.0 / nx * np.sum((y_interface - y_interface.mean()) * np.cos(phase))
    return float(coefficient), float(y_interface.min()), float(y_interface.max())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--initial", required=True)
    ap.add_argument("--final", required=True)
    ap.add_argument("--mode", type=int, default=2)
    ap.add_argument("--min-growth-ratio", type=float, default=1.02)
    ap.add_argument("--mass-rtol", type=float, default=2.0e-5)
    ap.add_argument("--alpha-tol", type=float, default=1.0e-8)
    args = ap.parse_args()

    initial, rho0, alpha0 = load(args.initial, args.alpha_tol)
    final, rhof, alphaf = load(args.final, args.alpha_tol)
    if float(alpha0.min()) >= 0.5 or float(alpha0.max()) <= 0.5:
        raise SystemExit("FAIL: initial field does not contain both RT phases")

    mass_rel = abs(float(rhof.sum()) - float(rho0.sum())) / max(float(abs(rho0.sum())), 1.0)
    vof0 = float((rho0 * alpha0).sum())
    voff = float((rhof * alphaf).sum())
    vof_mass_rel = abs(voff - vof0) / max(abs(vof0), 1.0)
    if mass_rel > args.mass_rtol or vof_mass_rel > args.mass_rtol:
        raise SystemExit(
            f"FAIL: conserved mass drift rho={mass_rel:.6g} "
            f"rho_adv_0={vof_mass_rel:.6g}")

    a0, y0_min, y0_max = interface_mode(initial, alpha0, args.mode)
    af, yf_min, yf_max = interface_mode(final, alphaf, args.mode)
    initial_amp = abs(a0)
    final_amp = abs(af)
    if initial_amp <= 1.0e-12:
        raise SystemExit(f"FAIL: seeded mode amplitude is too small: {a0:.6g}")
    ratio = final_amp / initial_amp
    if ratio < args.min_growth_ratio:
        raise SystemExit(
            f"FAIL: RT mode did not grow enough ratio={ratio:.6g} "
            f"required={args.min_growth_ratio:.6g}")

    final_ymom = final["fields"].get("ymom")
    if final_ymom is None or not np.isfinite(final_ymom).all():
        raise SystemExit("FAIL: missing/non-finite final ymom")
    if float(np.max(np.abs(final_ymom))) <= 0:
        raise SystemExit("FAIL: gravity produced no measurable momentum response")
    dt = float(final["time"] - initial["time"])
    rate = np.log(ratio) / dt if dt > 0 else float("nan")
    print(
        "rayleigh_taylor_growth_validation PASS "
        f"time={final['time']:.12g} grid={alpha0.shape} mode={args.mode} "
        f"initial_amp={initial_amp:.8g} final_amp={final_amp:.8g} "
        f"growth_ratio={ratio:.8g} growth_rate={rate:.8g} "
        f"mass_rel={mass_rel:.6g} vof_mass_rel={vof_mass_rel:.6g} "
        f"initial_y={y0_min:.6g}:{y0_max:.6g} "
        f"final_y={yf_min:.6g}:{yf_max:.6g}")


if __name__ == "__main__":
    main()
