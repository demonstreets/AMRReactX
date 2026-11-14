"""Common Cantera thermicity definitions for ZND reference and saved CFD states."""
from pathlib import Path
import json, sys, csv
import cantera as ct
import numpy as np
from scipy.signal import find_peaks

b = Path(__file__).resolve().parent
root = b.parent
sys.path.insert(0, '/home/cj/my-pele/tools')
import amrex_reader
mechanism = '/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/LiDryer/mechanism.yaml'
gas = ct.Solution(mechanism)
meta = json.loads((root/'reference_v1/metadata.json').read_text())
names = ['hydrogen_2400_cfl30_v1', 'hydrogen_4800_cfl30_v1', 'hydrogen_9600_cfl30_v1', 'hydrogen_4800_cfl15_v1']

def thermo(T, p, Y):
    states = ct.SolutionArray(gas, len(T))
    states.TPY = T, p, Y
    wdot = states.net_production_rates
    dydt = wdot * gas.molecular_weights / states.density[:, None]
    hs = states.partial_molar_enthalpies / gas.molecular_weights
    sigma = np.sum((states.mean_molecular_weight[:, None]/gas.molecular_weights - hs/(states.cp_mass*T)[:, None])*dydt, axis=1)
    qdot = -np.sum(states.partial_molar_enthalpies * wdot, axis=1)
    return sigma, qdot, states.int_energy_mass, states.density

def peak_record(x, rate, n):
    peak = float(rate[n]); half = .5*peak
    left = n
    while left > 0 and rate[left-1] >= half: left -= 1
    right = n
    while right < len(x)-1 and rate[right+1] >= half: right += 1
    lo = None if left == 0 else float(np.interp(half, rate[left-1:left+1], x[left-1:left+1]))
    hi = None if right == len(x)-1 else float(np.interp(half, rate[right:right+2][::-1], x[right:right+2][::-1]))
    return {'peak_distance_m':float(x[n]), 'peak_rate_s_inv':peak, 'half_rise_m':lo, 'half_fall_m':hi,
            'fwhm_m':None if lo is None or hi is None else hi-lo,
            'cells_above_half':int(right-left+1)}

def widths(x, sigma):
    keep = (x >= 0) & (x <= .003)
    x, s = x[keep], sigma[keep]
    n = int(np.argmax(s))
    assert s[n] > 0
    main = peak_record(x, s, n)
    # Only report local peaks with at least 10% of the global peak prominence.
    # This is a multi-peak diagnostic, not a different acceptance definition.
    peaks, _ = find_peaks(s, prominence=.1*s[n])
    main['significant_peak_count'] = len(peaks)
    main['significant_peaks'] = [peak_record(x, s, int(j)) for j in peaks]
    main['global_peak_at_window_edge'] = n in [0, len(x)-1]
    return main

references = {}
for folder in ['reference_v1', 'reference_tight_v1']:
    q = np.loadtxt(root/folder/'profile_SI.txt')
    sigma, qdot, e, rho = thermo(q[:,3], q[:,2], q[:,5:])
    r = widths(q[:,0], sigma)
    r['density_EOS_max_relative_difference'] = float(np.max(abs(rho/q[:,1]-1)))
    references[folder] = r
    np.savez_compressed(b/(folder+'_thermicity.npz'), xi_m=q[:,0], thermicity_s_inv=sigma, heat_release_W_m3=qdot)
reference = references['reference_v1']
all_cases = {}
table = []
profiles = {}
for name in names:
    summary = json.loads((root/name/'analysis/summary.json').read_text())
    case = summary['case']; dx = case['dx_m']
    hist = summary['history']; times = np.array([h['time_s'] for h in hist]); shock = np.array([h['shock_m'] for h in hist])
    speed = np.gradient(shock, times, edge_order=2)
    entries = []
    for k, h in enumerate(hist):
        q = amrex_reader.read_plotfile(h['plot']); f = q['fields']; mean = lambda key:f[key].mean(axis=1)
        x = q['x']*.01; xi = h['shock_m']-x
        p = mean('pressure')*.1; T = mean('Temp'); u = mean('x_velocity')*.01
        Y = np.array([mean('Y('+s+')') for s in gas.species_names]).T
        sigma, qdot, eint, eosrho = thermo(T, p, Y)
        order = np.argsort(xi)
        result = widths(xi[order], sigma[order])
        result.update(time_s=h['time_s'], local_speed_m_s=float(speed[k]),
                      induction_error_percent=100*(result['peak_distance_m']/reference['peak_distance_m']-1),
                      reaction_width_error_percent=None if result['fwhm_m'] is None else 100*(result['fwhm_m']/reference['fwhm_m']-1),
                      reaction_fwhm_cells=None if result['fwhm_m'] is None else result['fwhm_m']/dx)
        # State just behind the shock, outside its first three cells and before nominal induction.
        near = (xi >= 3*dx) & (xi <= 60e-6)
        result.update(near_shock_T_K=float(np.median(T[near])), near_shock_p_Pa=float(np.median(p[near])),
                      near_shock_YH2=float(np.median(Y[near,0])), near_shock_u_m_s=float(np.median(u[near])))
        density = mean('density')*1000; energy = mean('rho_E')*.1
        result['EOS_density_max_relative_error'] = float(np.max(abs(eosrho/density-1)))
        result['EOS_energy_max_scaled_error'] = float(np.max(abs(energy-density*(eint+.5*u*u)))/np.max(abs(energy)))
        if k == 0:
            ref = np.loadtxt(root/'reference_v1/profile_SI.txt')
            keep = (xi >= 0) & (xi <= .003)
            result['initialization_max_abs_difference'] = {label:float(np.max(abs(values[keep]-np.interp(xi[keep],ref[:,0],ref[:,col])))) for label,values,col in [('p_Pa',p,2),('T_K',T,3),('u_m_s',u,4)]}
        if k in [0, 2, 4, 6, 8, 12, len(hist)-1]:
            np.savez_compressed(b/f'{name}_t{k:02d}.npz', xi_m=xi[order], thermicity_s_inv=sigma[order], heat_release_W_m3=qdot[order], T_K=T[order], p_Pa=p[order], Y=Y[order], u_m_s=u[order])
        entries.append(result)
        table.append({'case':name,'dx_um':dx*1e6,'CFL':case['cfl'],'time_us':h['time_s']*1e6,
                      'local_speed_m_s':result['local_speed_m_s'],'induction_um':result['peak_distance_m']*1e6,
                      'reaction_fwhm_um':None if result['fwhm_m'] is None else result['fwhm_m']*1e6,
                      'induction_error_percent':result['induction_error_percent'],'reaction_width_error_percent':result['reaction_width_error_percent'],
                      'significant_peak_count':result['significant_peak_count'],'reaction_fwhm_cells':result['reaction_fwhm_cells'],
                      'near_shock_T_K':result['near_shock_T_K'],'near_shock_p_MPa':result['near_shock_p_Pa']*1e-6})
    all_cases[name] = {'case':case,'mean_speed_2_to_4us_m_s':summary['wave_speed_fits']['2e-06']['speed_m_s'],
                       'reference_reaction_width_in_cells':reference['fwhm_m']/dx,'history':entries}
    print(name, json.dumps(entries[-1]), flush=True)
out = {'definition':json.loads((b/'definition_source.json').read_text()), 'reference':references,
       'window_m':[0,.003], 'cases':all_cases,
       'caveats':['Global thermicity peak on the fixed 0–3 mm window. FWHM refers to its connected peak, not the full span of all pulses.',
                  'Peak position uses resolved sample maximum. Half-height crossings use linear interpolation. No smoothing.',
                  'The 4-us CFD fields are unsteady; these are instantaneous apparent lengths, not established steady ZND parameters.',
                  'Local shock speed is a derivative of output positions at about 0.25 us intervals, not a step-resolved velocity.']}
(b/'width_comparison.json').write_text(json.dumps(out,indent=2))
with (b/'width_history.csv').open('w',newline='') as f:
    w = csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
print('REFERENCE',json.dumps(references,indent=2))
