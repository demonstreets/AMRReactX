"""Finite-rate relaxation of recorded burned-gas hotspots, not a spray replacement.

GRI-Mech high-T is used only for burned gases with negligible remaining heptane.
Trace heptane is retained as an inert species to preserve the input composition.
This does not establish high-pressure/high-T kinetic accuracy or a coupled-flow fix.
"""
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import time
import numpy as np
import cantera as ct
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

r = Path('/home/cj/my-pele')
prior = r/'repair_validation/thermal_20260911'
b = r/'repair_validation/thermal_model_20260911'
out = b/'burned_gas_finite_rate_v2'
out.mkdir(parents=True, exist_ok=False)
source = prior/'conservative_original_and_baseline_peak_states_v2.json'
all_samples = json.loads(source.read_text())['hot_cells']
assert len(all_samples) == 7
samples = [s for s in all_samples if s['Y']['Y(nc7h16)'] < 1e-30]
excluded_samples = [s for s in all_samples if s['Y']['Y(nc7h16)'] >= 1e-30]
assert len(samples) == 5
assert max(s['Y']['Y(nc7h16)'] for s in samples) < 1e-30
reference = ct.Solution('gri30_highT.yaml')
nasa = {s.name: s for s in ct.Species.list_from_file('nasa_gas.yaml')}
fuel = ct.Species('NC7H16_TRACE', {'C': 7, 'H': 16})
fuel.thermo = nasa['C7H16,n-heptane'].thermo
model = ct.Solution(thermo='ideal-gas', kinetics='gas',
                    species=reference.species()+[fuel], reactions=reference.reactions())
model.write_yaml(out/'burned_gas_gri_highT_trace_heptane.yaml')
assert min(s.thermo.max_temp for s in model.species()) >= 6000
mapping = {'nc7h16': 'NC7H16_TRACE', 'o2': 'O2', 'co': 'CO', 'h2o': 'H2O', 'co2': 'CO2', 'n2': 'N2'}
species = list(mapping)
times = np.array([0., .1, .5, 1., 2.5, 5., 10., 25., 50., 100., 250., 500., 1000., 2000.])*1e-9
rows = []
results = []
native_input = []
for i, sample in enumerate(samples):
    T, rho, energy = sample['T_K'], sample['density_kg_m3'], sample['conserved_internal_energy_J_kg']
    Y = {mapping[n]: sample['Y']['Y('+n+')'] for n in species}
    initial_Y = np.array([sample['Y']['Y('+n+')'] for n in species])
    trajectories = []
    for rtol, atol in [(1e-9, 1e-18), (1e-11, 1e-20)]:
        gas = ct.Solution(str(out/'burned_gas_gri_highT_trace_heptane.yaml'))
        gas.TDY = T, rho, Y
        gas.UV = energy, 1./rho
        initial_T = gas.T
        elements = np.array([gas.elemental_mass_fraction(n) for n in gas.element_names])
        reactor = ct.IdealGasReactor(gas, energy='on', clone=False)
        network = ct.ReactorNet([reactor])
        network.rtol, network.atol = rtol, atol
        network.max_steps = 200000
        trajectory = []
        start = time.monotonic()
        for t in times:
            if t:
                network.advance(float(t))
            state = reactor.phase
            element_error = float(np.max(abs(np.array([state.elemental_mass_fraction(n) for n in state.element_names])-elements)))
            point = {'time_s': float(t), 'T_K': state.T, 'p_Pa': state.P,
                     'energy_error_J_kg': state.int_energy_mass-energy,
                     'relative_density_error': state.density/rho-1,
                     'element_mass_fraction_error': element_error,
                     'Y_min': float(state.Y.min()), 'Y_sum_error': float(state.Y.sum()-1),
                     'Y': state.Y.tolist()}
            assert state.T <= 6000 and state.T >= 300
            assert abs(point['energy_error_J_kg']) < .1 and element_error < 1e-9
            assert point['Y_min'] > -1e-12 and abs(point['Y_sum_error']) < 1e-9
            trajectory.append(point)
        trajectories.append({'rtol': rtol, 'atol': atol, 'elapsed_s': time.monotonic()-start,
                             'initial_T_at_same_conserved_energy_K': initial_T,
                             'trajectory': trajectory})
    terr = max(abs(a['T_K']-c['T_K']) for a,c in zip(trajectories[0]['trajectory'],trajectories[1]['trajectory']))
    assert terr < .01, terr
    result = {'sample_index': i, 'source_sample': sample,
              'maximum_T_difference_on_tightening_K': terr, 'runs': trajectories}
    results.append(result)
    for point in trajectories[-1]['trajectory']:
        rows.append({'sample': i, 'model': 'Burned gas GRI high-T', 'time_ns': point['time_s']*1e9,
                     'T_K': point['T_K'], 'p_Pa': point['p_Pa']})
    for j,t in enumerate(times[1:]):
        native_input.append(f'{i}_{j} '+' '.join(format(x,'.17g') for x in
            [T,rho,energy,t,1e-5,1e-14,*initial_Y]))

raw_input = '\n'.join(native_input)+'\n'
(out/'native_wd6_inputs.txt').write_text(raw_input)
probe = prior/'hot_cell_chemistry_validation_v3/probe'
native = subprocess.run([str(probe)], input=raw_input, capture_output=True, text=True, timeout=90)
(out/'native_wd6_outputs.txt').write_text(native.stdout)
(out/'native_wd6_stderr.txt').write_text(native.stderr)
assert native.returncode == 0, native.stderr
native_results = []
for line in native.stdout.splitlines():
    parts = line.split()
    i,j = map(int,parts[0].split('_'))
    values = list(map(float,parts[1:]))
    native_results.append({'sample': i, 'time_s': float(times[j+1]),
                           'success': bool(values[2]), 'T_K': values[4],
                           'energy_error_J_m3': values[11],
                           'accepted_steps': int(values[12]), 'rejected_steps': int(values[13])})
    if values[2]:
        rows.append({'sample': i, 'model': 'Active WD6', 'time_ns': times[j+1]*1e9,
                     'T_K': values[4], 'p_Pa': None})
assert len(native_results) == len(samples)*(len(times)-1)
with (out/'relaxation_history.csv').open('w',newline='') as f:
    writer = csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
fig,axes = plt.subplots(1,2,figsize=(13,4.8),constrained_layout=True)
peak_indices = [max(range(len(samples)-1), key=lambda i:samples[i]['T_K']), len(samples)-1]
for ax,i,title in zip(axes,peak_indices,['50-us saved-field peak','Transient operator-stage peak']):
    for name,style in [('Active WD6','o-'),('Burned gas GRI high-T','s-')]:
        selected = [p for p in rows if p['sample']==i and p['model']==name and p['time_ns']>0]
        ax.semilogx([p['time_ns'] for p in selected],[p['T_K'] for p in selected],style,label=name,markersize=3)
    ax.axhline(5000,color='gray',linestyle='--',linewidth=.8)
    ax.set(title=title,xlabel='Closed, fixed-density relaxation time (ns)',ylabel='Temperature (K)')
    ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('Finite-rate burned-gas sensitivity; no transport or continued compression')
fig.savefig(out/'burned_gas_relaxation.png',dpi=170)
result = {'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'model_sha256': hashlib.sha256((out/'burned_gas_gri_highT_trace_heptane.yaml').read_bytes()).hexdigest(),
          'native_probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'species_names': model.species_names, 'reference_header': reference.input_header,
          'trace_fuel_max_mass_fraction': max(s['Y']['Y(nc7h16)'] for s in samples),
          'samples': results, 'native_results': native_results,
          'excluded_samples_with_non_negligible_fuel': excluded_samples,
          'scope': 'Finite-rate burned-gas model sensitivity at the same recorded density, composition and conserved internal energy. GRI-Mech high-T does not model fresh n-heptane spray oxidation; trace heptane is inert. Thermodynamic fit coverage does not validate high-pressure kinetic extrapolation. Closed relaxation is not the coupled flow trajectory.'}
(out/'result.json').write_text(json.dumps(result,indent=2))
summary = {'sample_count': len(samples), 'native_requested': len(native_results),
           'native_completed': sum(x['success'] for x in native_results),
           'peaks': [{'sample':i,'original_T_K':samples[i]['T_K'],
                     'expanded_initial_T_K':results[i]['runs'][-1]['trajectory'][0]['T_K'],
                     'expanded_T_at_2p5ns_K':results[i]['runs'][-1]['trajectory'][4]['T_K'],
                     'expanded_T_at_100ns_K':results[i]['runs'][-1]['trajectory'][9]['T_K'],
                     'expanded_T_at_2us_K':results[i]['runs'][-1]['trajectory'][-1]['T_K']}
                     for i in peak_indices], 'scope':result['scope']}
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
