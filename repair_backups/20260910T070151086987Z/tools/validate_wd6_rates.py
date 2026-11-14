"""Compare the native WD6 chemistry probe with independent Cantera rates."""
import argparse
import json
from pathlib import Path
import subprocess

import cantera as ct
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("probe", type=Path, help="compiled test/unit/probe_wd6_chemistry.cpp")
p.add_argument("output", type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
gas = ct.Solution(str(root / "external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_wd6/mechanism.yaml"))
rng = np.random.default_rng(1937)
states = [(float(T), float(P), rng.dirichlet(np.ones(6)*2))
          for T in [500, 1000, 1600, 2300, 3000]
          for P in [50662.5, 100000, 1000000] for _ in range(3)]
states += [(1400., 1.e5, np.array([.04, .2, 0, 0, 0, .76])),
           (2500., 1.e5, np.array([0, .1, .1, .2, .1, .5])),
           (300., 1.e5, np.array([0, 0, 0, 0, 0, 1.]))]
input_text = "".join(" ".join(format(v, ".17g") for v in [T, P*10, *X])+"\n"
                     for T, P, X in states)
result = subprocess.run([str(a.probe.resolve())], input=input_text, text=True,
                        capture_output=True, check=True)
values = np.array([[float(v) for v in line.split()] for line in result.stdout.splitlines()])
if values.shape != (len(states), 56) or not np.isfinite(values).all():
    raise ValueError("native probe must return one finite density/rate/Jacobian row per state")

def rhs(T, concentrations):
    rho = np.dot(concentrations, gas.molecular_weights)*.001
    Y = concentrations*gas.molecular_weights/(rho*1000.)
    gas.TDY = T, rho, Y
    production = gas.net_production_rates*1000.
    cv = (gas.standard_cp_R-1)*ct.gas_constant*.001
    dT = -np.dot(production, gas.partial_molar_int_energies*.001)/np.dot(concentrations, cv)
    return np.r_[production, dT]

errors = dict(density=0., rates=0., jacobian=0., states=len(states))
for idx, ((T, P, X), row) in enumerate(zip(states, values)):
    gas.TPX = T, P, X
    rho, rates, c = gas.density*.001, gas.net_production_rates*.001, gas.concentrations*1000.
    errors["density"] = max(errors["density"], abs(row[0]-rho)/rho)
    errors["rates"] = max(errors["rates"], float(np.max(abs(row[1:7]-rates)))/max(float(np.max(abs(rates))), 1.e-30))
    jac = row[7:].reshape((7, 7), order="F")
    if idx >= 45:
        continue  # Fractional-order derivatives at zero have no finite classical limit.
    fd = np.empty((7, 7))
    for j in range(7):
        plus, minus = c.copy(), c.copy()
        h = (T if j == 6 else c[j])*1.e-5
        if j == 6 and T == 1000.:
            # Cantera and generated NASA routines can select different values
            # exactly at a polynomial switch. Differentiate the high-T branch
            # from its interior, extrapolating to the branch endpoint.
            fd[:, j] = (-5*rhs(T+h, c)+8*rhs(T+2*h, c)-3*rhs(T+3*h, c))/(2*h)
        elif j == 6:
            fd[:, j] = (rhs(T+h, c)-rhs(T-h, c))/(2*h)
        else:
            plus[j] += h
            minus[j] -= h
            fd[:, j] = (rhs(T, plus)-rhs(T, minus))/(2*h)
    errors["jacobian"] = max(errors["jacobian"], float(np.max(abs(jac-fd))/max(np.max(abs(fd)), 1.)))
errors["thresholds"] = dict(density=1.e-12, rates=1.e-11, jacobian=1.e-5)
errors["passed"] = all(errors[k] < v for k, v in errors["thresholds"].items())
errors["derivative_scope"] = "45 positive-composition states; high-side derivative at 1000 K; three zero-species states checked for finite native output and accurate rates"
with a.output.open("x") as f:
    json.dump(errors, f, indent=2)
print(json.dumps(errors))
raise SystemExit(0 if errors["passed"] else 2)
