#!/usr/bin/env python3
"""
Constant-volume autoignition simulation for H2/air mixture.

Calculates ignition delay time using Cantera.
Conditions: H2/air, phi=1.0, T=1200K, P=1atm, constant volume.
"""

import cantera as ct
import numpy as np

def run_ignition_delay():
    # Conditions
    T0 = 1200.0          # K
    P0 = 101325.0         # Pa (1 atm)
    phi = 1.0             # equivalence ratio
    
    # H2/air mechanism - use GRI 3.0 (includes H2 subset)
    gas = ct.Solution('h2o2.yaml')
    
    # Set stoichiometric H2/air mixture at phi=1
    gas.set_equivalence_ratio(phi, 'H2', 'O2:1.0, N2:3.76')
    gas.TP = T0, P0
    
    print(f"Initial conditions:")
    print(f"  Temperature: {T0} K")
    print(f"  Pressure:    {P0/101325:.4f} atm")
    print(f"  phi:         {phi}")
    print(f"  H2 mole fraction:  {gas.X[gas.species_index('H2')]:.4f}")
    print(f"  O2 mole fraction:  {gas.X[gas.species_index('O2')]:.4f}")
    print(f"  N2 mole fraction:  {gas.X[gas.species_index('N2')]:.4f}")
    print(f"  Density: {gas.density:.4f} kg/m3")
    print()
    
    # Constant volume reactor
    r = ct.IdealGasReactor(gas)
    net = ct.ReactorNet([r])
    
    # Track state
    times = []
    temperatures = []
    max_steps = 50000
    
    print("Running constant-volume autoignition...")
    
    for i in range(max_steps):
        net.step()
        times.append(net.time)
        temperatures.append(r.T)
        
        # Ignition detected when temperature rises significantly
        # Use criterion: T > T0 + 400 K (typical OH-radical based ignition)
        if r.T > T0 + 400:
            # Linear interpolation to find exact ignition delay
            # Find when dT/dt is maximum (more precise than fixed threshold)
            break
    
    # Compute ignition delay time using max dT/dt criterion
    temps = np.array(temperatures)
    times_arr = np.array(times)
    
    # Find point of maximum temperature derivative
    dTdt = np.gradient(temps, times_arr)
    idx_max = np.argmax(dTdt)
    t_ign = times_arr[idx_max]
    
    # Also report using fixed threshold T0+400
    idx_thresh = np.argmax(temps > T0 + 400)
    t_ign_thresh = times_arr[idx_thresh] if idx_thresh > 0 else float('inf')
    
    print("\nResults:")
    print(f"  Simulation time range: {times[0]:.6e} - {times[-1]:.6e} s")
    print(f"  Max temperature:        {max(temperatures):.1f} K")
    print(f"  Peak dT/dt:            {max(dTdt):.1f} K/s")
    print(f"  Ignition delay (max dT/dt):  {t_ign:.6e} s")
    print(f"  Ignition delay (T0+400K):    {t_ign_thresh:.6e} s")
    
    return t_ign

if __name__ == '__main__':
    t_ign = run_ignition_delay()
