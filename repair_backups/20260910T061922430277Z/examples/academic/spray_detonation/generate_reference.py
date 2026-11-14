"""Independent Cantera equilibrium CJ and finite-rate ZND references (SI)."""
import argparse
import hashlib
import json
from pathlib import Path

import cantera as ct
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize_scalar

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("output", type=Path)
p.add_argument("--phi", type=float, default=.6)
p.add_argument("--pressure-Pa", type=float, default=50662.5)
p.add_argument("--temperature-K", type=float, default=300.)
p.add_argument("--speed-ratio", type=float, default=1.02)
args = p.parse_args()
if args.phi <= 0. or args.pressure_Pa <= 0. or args.temperature_K <= 0. or args.speed_ratio <= 1.:
    p.error("positive upstream values and a speed ratio strictly above one are required")
root = Path(__file__).resolve().parents[3]
mechanism = root/"external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml"
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)

def cj(phi):
    gas = ct.Solution(str(mechanism))
    gas.TPX = args.temperature_K, args.pressure_Pa, {"nc7h16": phi, "o2": 11., "n2": 41.36}
    y0, r0, e0 = gas.Y.copy(), gas.density, gas.int_energy_mass
    def hugoniot(compression, return_state=False):
        rho = compression*r0
        def residual(temp):
            gas.TDY = temp, rho, y0
            gas.equilibrate("TV", rtol=1.e-10, max_steps=2000)
            return gas.int_energy_mass-e0-.5*(gas.P+args.pressure_Pa)*(1/r0-1/rho)
        temp = brentq(residual, 500., 6000., xtol=1.e-7)
        residual(temp)
        speed = np.sqrt((gas.P-args.pressure_Pa)/(r0*(1-1/compression)))
        if return_state:
            return {"D_m_s": float(speed), "compression_ratio": float(compression),
                    "T_K": gas.T, "p_Pa": gas.P, "rho_kg_m3": gas.density,
                    "rho_upstream": r0, "Y": gas.Y.tolist(), "species_names": gas.species_names}
        return speed
    opt = minimize_scalar(hugoniot, bounds=(1.05, 4.), method="bounded", options={"xatol": 1.e-8})
    if not opt.success or not 1.0501 < opt.x < 3.9999:
        raise RuntimeError("CJ minimization did not find an interior equilibrium Hugoniot minimum")
    result = hugoniot(opt.x, True)
    result.update(phi=phi, upstream_pressure_Pa=args.pressure_Pa,
                  upstream_temperature_K=args.temperature_K,
                  method="minimum equilibrium Hugoniot detonation speed, independent Cantera EOS")
    return result

cj_states = [cj(args.phi)]
if abs(args.phi-1.) > 1.e-12:
    cj_states.append(cj(1.))
(out/"CJ.json").write_text(json.dumps(cj_states, indent=2))
g = ct.Solution(str(mechanism))
g.TPX = args.temperature_K, args.pressure_Pa, {"nc7h16": args.phi, "o2": 11., "n2": 41.36}
y0, rho0, p0, h0 = g.Y.copy(), g.density, g.P, g.enthalpy_mass
speed = cj_states[0]["D_m_s"]*args.speed_ratio
mass_flux = rho0*speed
momentum = p0+mass_flux*speed
energy = h0+.5*speed**2

def frozen_residual(rho):
    pressure = momentum-mass_flux**2/rho
    g.TDY = pressure/(rho*ct.gas_constant*np.sum(y0/g.molecular_weights)), rho, y0
    return g.enthalpy_mass+.5*(mass_flux/rho)**2-energy

grid = rho0*np.linspace(1.001, 15., 500)
brackets = [(a, z) for a, z in zip(grid[:-1], grid[1:])
            if frozen_residual(a)*frozen_residual(z) < 0.]
if not brackets:
    raise RuntimeError("no compressed frozen von Neumann state was found")
rho_vn = brentq(frozen_residual, *brackets[-1])
frozen_residual(rho_vn)
vn = {"rho": rho_vn, "p": g.P, "T": g.T, "u": speed-mass_flux/rho_vn}

def state(q):
    rho, y = q[0], q[1:-1]
    pressure = momentum-mass_flux**2/rho
    gas_constant = ct.gas_constant*np.sum(y/g.molecular_weights)
    g.TDY = pressure/(rho*gas_constant), rho, y
    return rho, mass_flux/rho, gas_constant

def rhs(time, q):
    rho, relative_speed, gas_constant = state(q)
    dy = g.net_production_rates*g.molecular_weights/rho
    gamma = g.cp_mass/g.cv_mass
    sound_squared = gamma*g.P/rho
    h = g.partial_molar_enthalpies/g.molecular_weights
    dgas_constant = ct.gas_constant*np.sum(dy/g.molecular_weights)
    drho = gamma*rho*(-gas_constant*np.dot(h, dy)/g.cp_mass+g.T*dgas_constant) / (
        relative_speed**2-sound_squared)
    return np.r_[drho, dy, relative_speed]

q0 = np.r_[rho_vn, y0, 0.]
sol = solve_ivp(rhs, [0., 1.e-4], q0, method="BDF", rtol=2.e-9,
                atol=np.r_[1.e-9, np.full(g.n_species, 1.e-16), 1.e-12],
                dense_output=True, max_step=1.e-6)
if not sol.success:
    raise RuntimeError(sol.message)
times = np.r_[0., np.geomspace(1.e-12, sol.t[-1], 5000)]
values = sol.sol(times)
raw_min = float(values[1:-1].min())
sum_error = float(np.max(abs(values[1:-1].sum(axis=0)-1.)))
if raw_min < -1.e-10 or sum_error > 1.e-9:
    raise RuntimeError("inadmissible finite-rate reference integration")
rows, residuals = [], []
for value in values.T:
    rho, relative_speed, _ = state(value)
    rows.append(np.r_[value[-1], rho, g.P, g.T, speed-relative_speed, g.Y])
    residuals.append(abs(g.enthalpy_mass+.5*relative_speed**2-energy)/max(abs(energy), 1.))
if max(residuals) > 1.e-6:
    raise RuntimeError("finite-rate reference failed its energy Hugoniot check")
table = np.asarray(rows)
np.savetxt(out/"profile_SI.txt", table,
           header="distance_behind_shock_m rho_kg_m3 p_Pa T_K u_m_s "+" ".join(g.species_names))
metadata = {"mechanism": "heptane_lu_88sk", "mechanism_sha256": hashlib.sha256(mechanism.read_bytes()).hexdigest(),
            "species_names": g.species_names, "D": speed, "CJ": cj_states[0]["D_m_s"],
            "overdrive_speed_ratio": args.speed_ratio,
            "upstream": {"rho": rho0, "p": p0, "T": args.temperature_K, "u": 0., "Y": y0.tolist()},
            "von_neumann": vn, "max_energy_relative_residual": max(residuals),
            "raw_min_species": raw_min, "max_species_sum_error": sum_error,
            "profile_export": "Cantera-normalized composition; raw BDF trace negativity is reported separately",
            "length_m": float(table[-1, 0]), "time_s": float(times[-1]),
            "evaluations": sol.nfev, "end_temperature": float(table[-1, 3]),
            "cantera_version": ct.__version__}
(out/"metadata.json").write_text(json.dumps(metadata, indent=2))
print(json.dumps(metadata))
