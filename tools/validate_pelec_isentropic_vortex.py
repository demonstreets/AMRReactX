#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader

GAMMA = 1.4


def fail(message: str) -> None:
    raise SystemExit(f"pelec_isentropic_vortex_validation FAIL {message}")


def parse_log_value(name: str, text: str) -> float:
    m = re.search(rf"\b{name}\s*=\s*([-+0-9.eE]+)", text)
    if not m:
        fail(f"missing {name} in run log")
    return float(m.group(1))


def parse_input_value(path: str, key: str, default: float) -> float:
    if not path:
        return default
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*([-+0-9.eE]+)")
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            m = pattern.search(line)
            if m:
                return float(m.group(1))
    return default


def periodic_delta(coord: np.ndarray, center: float, period: float) -> np.ndarray:
    return coord - center - period * np.floor((coord - center) / period + 0.5)


def reference(x: np.ndarray, y: np.ndarray, time: float, params: dict[str, float]) -> dict[str, np.ndarray]:
    lx = params["domain_x"]
    ly = params["domain_y"]
    cx = (params["center_x"] + params["u_bg"] * time) % lx
    cy = (params["center_y"] + params["v_bg"] * time) % ly
    dx = periodic_delta(x, cx, lx)
    dy = periodic_delta(y, cy, ly)
    rv = params["vortex_R"]
    dxn = dx / rv
    dyn = dy / rv
    r2 = dxn * dxn + dyn * dyn
    if params.get("exact_vortex", 0.0) != 0.0:
        beta = params["vortex_beta"]
        e = np.exp(0.5 * (1.0 - r2))
        theta = 1.0 - (GAMMA - 1.0) * beta * beta / (8.0 * GAMMA * math.pi * math.pi) * np.exp(1.0 - r2)
        u = params["u_bg"] - beta / (2.0 * math.pi) * e * dyn
        v = params["v_bg"] + beta / (2.0 * math.pi) * e * dxn
        temp = params["T_bg"] * theta
    else:
        eps = params["vortex_eps"]
        e = np.exp(-r2 / 2.0)
        du = -eps * dyn * e
        dv = eps * dxn * e
        u = params["u_bg"] + du
        v = params["v_bg"] + dv
        u2 = u * u + v * v
        u2_bg = params["u_bg"] ** 2 + params["v_bg"] ** 2
        temp = params["T_bg"] - (u2 - u2_bg) / (2.0 * params["cp_bg"])
    rho = params["rho_bg"] * (temp / params["T_bg"]) ** (1.0 / (GAMMA - 1.0))
    pressure = params["p_bg"] * (rho / params["rho_bg"]) ** GAMMA
    return {"density": rho, "Temp": temp, "pressure": pressure, "x_velocity": u, "y_velocity": v}


def l1(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a - b)))


def linf(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.max(np.abs(a - b)))


def read_xy_mesh(pf: dict) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(pf["x"])
    y = np.asarray(pf["y"])
    xx, yy = np.meshgrid(x, y, indexing="ij")
    sample = next(iter(pf["fields"].values()))
    if sample.ndim == 3:
        xx = xx[:, :, None] + np.zeros(sample.shape)
        yy = yy[:, :, None] + np.zeros(sample.shape)
    return xx, yy


def field(pf: dict, name: str) -> np.ndarray:
    fields = pf["fields"]
    if name not in fields:
        fail(f"missing field {name}")
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        fail(f"nonfinite field {name}")
    return arr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--initial", required=True)
    ap.add_argument("--final", required=True)
    ap.add_argument("--run-log", required=True)
    ap.add_argument("--input", default="")
    ap.add_argument("--max-init-linf", type=float, default=2.0e-8)
    ap.add_argument("--max-final-density-l1", type=float, default=3.0e-4)
    ap.add_argument("--max-final-pressure-l1", type=float, default=3.0e-4)
    ap.add_argument("--max-final-velocity-l1", type=float, default=3.0e-3)
    ap.add_argument("--max-mass-rel", type=float, default=1.0e-10)
    args = ap.parse_args()

    log_text = open(args.run_log, "r", encoding="utf-8", errors="replace").read()
    if "AMReX" not in log_text or "finalized" not in log_text:
        fail("run log missing AMReX finalization")
    if "Unused ParmParse Variables" in log_text or "Backtrace" in log_text or "SIGABRT" in log_text:
        fail("run log contains abort/unused/backtrace marker")

    init = amrex_reader.read_plotfile(args.initial)
    final = amrex_reader.read_plotfile(args.final)
    params = {
        "vortex_eps": parse_input_value(args.input, "prob.vortex_eps", 0.5),
        "vortex_beta": parse_input_value(args.input, "prob.vortex_beta", 5.0),
        "exact_vortex": parse_input_value(args.input, "prob.exact_vortex", 0.0),
        "vortex_R": parse_input_value(args.input, "prob.vortex_R", 1.0),
        "center_x": parse_input_value(args.input, "prob.center_x", 5.0),
        "center_y": parse_input_value(args.input, "prob.center_y", 5.0),
        "rho_bg": parse_input_value(args.input, "prob.rho_bg", 1.0),
        "u_bg": parse_input_value(args.input, "prob.u_bg", 1.0),
        "v_bg": parse_input_value(args.input, "prob.v_bg", 1.0),
        "p_bg": parse_input_value(args.input, "prob.p_bg", 0.714285714),
        "T_bg": parse_log_value("T_bg", log_text),
        "cp_bg": parse_log_value("cp_bg", log_text),
        "domain_x": float(init["prob_hi"][0] - init["prob_lo"][0]),
        "domain_y": float(init["prob_hi"][1] - init["prob_lo"][1]),
    }

    init_x, init_y = read_xy_mesh(init)
    final_x, final_y = read_xy_mesh(final)
    ref0 = reference(init_x, init_y, 0.0, params)
    reff = reference(final_x, final_y, float(final["time"]), params)

    init_linf = max(linf(field(init, name), ref0[name]) for name in ref0)
    if init_linf > args.max_init_linf:
        fail(f"initial reference mismatch linf={init_linf:.8e}")

    rho0 = field(init, "density")
    rhof = field(final, "density")
    pressuref = field(final, "pressure")
    tempf = field(final, "Temp")
    uf = field(final, "x_velocity")
    vf = field(final, "y_velocity")
    zf = field(final, "z_velocity")
    if not (float(rhof.min()) > 0.0 and float(pressuref.min()) > 0.0 and float(tempf.min()) > 0.0):
        fail("nonpositive thermodynamic field")
    if float(np.max(np.abs(zf))) > 1.0e-12:
        fail(f"z velocity drift {np.max(np.abs(zf)):.6e}")

    rho_l1 = l1(rhof, reff["density"])
    p_l1 = l1(pressuref, reff["pressure"])
    u_l1 = l1(uf, reff["x_velocity"])
    v_l1 = l1(vf, reff["y_velocity"])
    if rho_l1 > args.max_final_density_l1:
        fail(f"density_l1={rho_l1:.8e}")
    if p_l1 > args.max_final_pressure_l1:
        fail(f"pressure_l1={p_l1:.8e}")
    if max(u_l1, v_l1) > args.max_final_velocity_l1:
        fail(f"velocity_l1={max(u_l1, v_l1):.8e}")

    cell_vol = float(np.prod(final["dx"]))
    mass0 = float(np.sum(rho0) * cell_vol)
    massf = float(np.sum(rhof) * cell_vol)
    mass_rel = abs(massf - mass0) / max(abs(mass0), 1.0e-300)
    if mass_rel > args.max_mass_rel:
        fail(f"mass_rel={mass_rel:.8e}")

    entropy = pressuref / np.power(rhof, GAMMA)
    entropy_linf = float(np.max(np.abs(entropy - params["p_bg"] / params["rho_bg"] ** GAMMA)))

    print(
        "pelec_isentropic_vortex_validation PASS "
        f"time={float(final['time']):.8e} nx={final['grid']['nx']} ny={final['grid']['ny']} nz={final['grid'].get('nz', 1)} "
        f"init_linf={init_linf:.8e} density_l1={rho_l1:.8e} pressure_l1={p_l1:.8e} "
        f"u_l1={u_l1:.8e} v_l1={v_l1:.8e} mass_rel={mass_rel:.8e} "
        f"entropy_linf={entropy_linf:.8e} temp_min={float(tempf.min()):.8e} temp_max={float(tempf.max()):.8e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
