"""Compare completed dry/wet planar histories without claiming steady detonation."""
import argparse
import json
import hashlib
from pathlib import Path
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('dry_analysis', type=Path)
p.add_argument('wet_analysis', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
data, profiles, settings = {}, {}, {}
for name, folder in [('dry', a.dry_analysis), ('wet', a.wet_analysis)]:
    z = json.loads((folder/'analysis.json').read_text())
    if z['partial_analysis'] or not z['completed_requested_time'] or z['exit_code'] != 0 or not z['raw_fields_admissible']:
        raise ValueError(name+': completed admissible results required')
    data[name] = z
    profiles[name] = json.loads((folder/'mean_profiles.json').read_text())[-1]
    run = Path(z['run'])
    settings[name] = {'profile_sha256': hashlib.sha256((run/'profile_SI.txt').read_bytes()).hexdigest(),
                      'inputs': (run/'inputs').read_text()}
    if max(row['shock_transverse_span_mm'] for row in z['rows']) > 1.e-6:
        raise ValueError(name+': this plot is for planar propagation')

def value(text, key):
    matches = re.findall(r'^'+re.escape(key)+r'\s*=\s*([^#\n]+)', text, re.M)
    return matches[-1].split() if matches else None

def same_input(left, right):
    if left is None or right is None:
        return left == right
    try:
        return len(left) == len(right) and np.array_equal(np.asarray(left, dtype=float), np.asarray(right, dtype=float))
    except ValueError:
        return left == right

for key in ['geometry.prob_lo', 'geometry.prob_hi', 'amr.n_cell', 'prob.p0', 'prob.T0',
            'prob.front', 'prob.perturbation', 'prob.upstream_Y', 'pelec.lo_bc', 'pelec.hi_bc']:
    if not same_input(value(settings['dry']['inputs'], key), value(settings['wet']['inputs'], key)):
        raise ValueError('different physical initialization/grid: '+key)
if settings['dry']['profile_sha256'] != settings['wet']['profile_sha256']:
    raise ValueError('different gas reference profile')
if data['dry']['rows'][0]['liquid_mass_g'] != 0. or data['wet']['rows'][0]['liquid_mass_g'] <= 0.:
    raise ValueError('dry/wet labels do not match liquid loading')
if data['dry']['species_names'] != data['wet']['species_names']:
    raise ValueError('different chemistry')
end = data['dry']['rows'][-1]['time_s']
if abs(data['wet']['rows'][-1]['time_s']-end) > 1.e-12*end:
    raise ValueError('different final times')

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(3, 2, figsize=(12, 10), layout='constrained')
summary = {}
for name, z in data.items():
    rows = z['rows']; time = np.array([r['time_s'] for r in rows])
    position = np.array([r['shock_x_cm'] for r in rows])*.01
    color = '#b65c22' if name == 'dry' else '#1d6685'
    axes[0,0].plot(time*1.e6, position*1000., color=color, label=name)
    axes[1,0].plot(.5*(time[1:]+time[:-1])*1.e6, np.diff(position)/np.diff(time), color=color, label=name)
    axes[2,0].plot(time*1.e6, [r['positive_heat_release_centroid_gap_mm'] for r in rows], color=color, label=name)
    last = profiles[name]
    distance = (last['shock_x_cm']-np.asarray(last['x_cm']))*10.
    for axis, key, scale in zip(axes[:,1], ['pressure_Pa', 'gas_temperature_K', 'heat_release_W_m3'], [1.e-6, 1., 1.]):
        axis.plot(distance, np.asarray(last[key])*scale, color=color, label=name)
        axis.set_xlim(-3., 30.)
    mask = time >= .5*end
    summary[name] = {'analysis': str((a.dry_analysis if name == 'dry' else a.wet_analysis).resolve()),
        'common_late_speed_m_s': float(np.polyfit(time[mask], position[mask], 1)[0]),
        'fit_sample_window_s': [float(time[mask][0]), float(time[mask][-1])],
        'final': rows[-1],
        'numerical_settings': {key: value(settings[name]['inputs'], key) for key in
            ['pelec.cfl', 'cvode.rtol', 'cvode.atol', 'pelec.chemistry_transport_split']},
        'remaining_liquid_fraction': rows[-1]['liquid_mass_g']/rows[0]['liquid_mass_g'] if name == 'wet' else None}

for ax, label in zip(axes[:,0], ['Shock position (mm)', 'Interval shock speed (m/s)', 'Positive heat-release centroid gap (mm)']):
    ax.set(xlabel='Time (microseconds)', ylabel=label)
for ax, label in zip(axes[:,1], ['Pressure (MPa)', 'Gas temperature (K)', 'Heat release (W/m3)']):
    ax.set(xlabel='Distance behind leading shock (mm)', ylabel=label)
    ax.axvline(0., color='.6', lw=.7, ls='--')
for ax in axes.flat:
    ax.legend(); ax.grid(alpha=.15)
fig.suptitle(f'Planar dry / wet propagation; final profiles at {end*1.e6:.1f} microseconds')
a.output.mkdir(parents=True, exist_ok=False)
fig.savefig(a.output/'planar_dry_wet_comparison.png', dpi=170)
plt.close(fig)
result = {'requested_common_window_s': [.5*end, end], 'cases': summary,
    'wet_minus_dry_speed_relative_difference': summary['wet']['common_late_speed_m_s']/summary['dry']['common_late_speed_m_s']-1.,
    'interpretation': 'Finite-interval initial-value comparison. The initial wave is overdriven; interval speeds are output-to-output differences, not solver-step speeds. Similar average speeds do not establish steady wave/reaction coupling or spatial convergence.'}
(a.output/'comparison.json').write_text(json.dumps(result, indent=2))
print(json.dumps({'speed_relative_difference': result['wet_minus_dry_speed_relative_difference']}))
