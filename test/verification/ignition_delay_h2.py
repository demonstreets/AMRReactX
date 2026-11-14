#!/usr/bin/env python3
"""
Phase 0.4 — Cantera H2/air 0D constant-volume ignition delay verification.

Computes ignition delay at T=1200 K, P=1 atm, phi=1 (H2/air).
Uses the Burke et al. H2/O2 mechanism (h2o2.yaml) from Cantera.

Usage:
    python3 ignition_delay_h2.py
"""

import cantera as ct
import numpy as np
import sys
import time

# ---------- Parameters ----------
T_init = 1200.0       # K
P_init = 101325.0     # Pa (1 atm)
phi = 1.0
mechanism = "h2o2.yaml"  # Burke et al. H2/O2 mechanism

# ---------- Setup ----------
gas = ct.Solution(mechanism)
print(f"Mechanism: {mechanism}")
print(f"  Species: {gas.n_species}, Reactions: {gas.n_reactions}")

# H2/air mixture at phi=1
# H2 + 0.5*(O2 + 3.76 N2) -> phi=1 means fuel_air_ratio = 1
gas.set_equivalence_ratio(phi, "H2", "O2:1.0, N2:3.76")
gas.TP = T_init, P_init

print(f"\nInitial conditions:")
print(f"  T = {gas.T:.1f} K, P = {gas.P / 101325:.2f} atm, phi = {phi}")
print(f"  X_H2  = {gas.X[gas.species_index('H2')]:.4f}")
print(f"  X_O2  = {gas.X[gas.species_index('O2')]:.4f}")
print(f"  X_N2  = {gas.X[gas.species_index('N2')]:.4f}")

# ---------- Constant-volume reactor ----------
reactor = ct.IdealGasReactor(gas)
sim = ct.ReactorNet([reactor])
sim.rtol = 1.0e-12
sim.atol = 1.0e-15

# Time-integrate
states = ct.SolutionArray(gas, extra=["t"])
t_start = time.time()

t = 0.0
dt = 1.0e-12  # small initial timestep for output
t_end = 1.0   # max simulation time (s)

step = 0
T_max_recorded = T_init

print(f"\nIntegrating...")
print(f"{'Step':>6} {'Time (s)':>12} {'T (K)':>10} {'dT/dt (K/s)':>14}")

while t < t_end:
    t = sim.step()
    states.append(gas.state, t=t)
    T = gas.T
    if T > T_max_recorded:
        T_max_recorded = T
    dTdt = (states.T[-1] - states.T[-2]) / (t - states.t[-2]) if len(states.T) > 1 else 0
    
    if step % 50 == 0 or T > T_init + 50:
        print(f"{step:6d} {t:12.6e} {T:10.2f} {dTdt:14.2e}")
    
    # Check for ignition: max temperature rise rate
    if T > T_init + 400 and dTdt > 1.0e8:
        print(f"{step:6d} {t:12.6e} {T:10.2f} {dTdt:14.2e}  <-- ignition detected")
        break
    
    step += 1

t_end_wall = time.time()

# ---------- Compute ignition delay ----------
# Ignition delay: time when temperature derivative is maximal
if len(states.T) > 10:
    dT = np.diff(states.T)
    dt_arr = np.diff(states.t)
    dTdt_arr = np.zeros_like(states.t)
    dTdt_arr[1:] = dT / dt_arr
    i_ign = np.argmax(dTdt_arr)
else:
    i_ign = -1

if i_ign > 0:
    tau_ign = states.t[i_ign]
    T_ign = states.T[i_ign]
else:
    tau_ign = t
    T_ign = gas.T

print(f"\n{'='*60}")
print(f"RESULTS:")
print(f"  Ignition delay (max dT/dt): tau = {tau_ign:.6e} s ({tau_ign*1e6:.2f} us)")
print(f"  Ignition temperature:       T   = {T_ign:.1f} K")
print(f"  Peak temperature:           T   = {T_max_recorded:.1f} K")
print(f"  Wall-clock time:            {t_end_wall - t_start:.2f} s")
print(f"  Time steps:                 {step}")
print(f"{'='*60}")

# ---------- Save results ----------
output_file = "ignition_delay_h2_results.csv"
# Save key timesteps
with open(output_file, "w") as f:
    f.write("t,T,P,rho\n")
    n_out = min(len(states.t), 1000)
    idx = np.linspace(0, len(states.t)-1, n_out, dtype=int)
    for i in idx:
        f.write(f"{states.t[i]:.12e},{states.T[i]:.6e},{states.P[i]:.6e},{states.density[i]:.6e}\n")

print(f"\nResults saved to {output_file}")

# Also print the mechanism info for report
print(f"\nMechanism summary: {gas.n_species} species, {gas.n_reactions} reactions")
print(f"  Species list: {', '.join(gas.species_names[:10])}...")
