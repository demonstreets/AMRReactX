"""Inspect recorded thermal hotspots without changing any flow state."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p = argparse.ArgumentParser()
p.add_argument('plots', nargs='+', type=Path)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--tools', type=Path, default=Path('/home/cj/my-pele/tools'))
p.add_argument('--compare-first', action='store_true', help='Require equal times and compare fields to the first plot')
a = p.parse_args()
sys.path.insert(0, str(a.tools))
import amrex_reader
a.output.mkdir(exist_ok=False, parents=True)
fig, axes = plt.subplots(len(a.plots), 3, figsize=(15, 3.4*len(a.plots)),
                         squeeze=False, constrained_layout=True)
results = []
reference = None
for row, plot in enumerate(a.plots):
    label_run = {'wd6_stoich_wet_2d_2800x800_two_gpu_continuation_v2': 'Original fine-grid run',
                 'replay_cfl20_v1': 'Replay CFL 0.2',
                 'replay_cfl10_v1': 'Replay CFL 0.1',
                 'lower_open_from48_v1': 'Lower boundary open from 48 us',
                 'tight_chemistry_from48_v1': '100x chemistry (interrupted)',
                 'chemistry10_from48_v1': '10x tighter chemistry from 48 us',
                 'replay_coarse_cfl20_v1': 'Coarse-grid replay 0.1 mm'}.get(plot.parent.name, plot.parent.name)
    d = amrex_reader.read_plotfile(str(plot))
    f = d['fields']
    x = np.asarray(d['x'])*10.
    y = np.asarray(d['y'])*10.
    T = f['Temp']
    i, j = np.unravel_index(np.argmax(T), T.shape)
    rho = f['density']*1000.
    pressure = f['pressure']*.1
    u = f['x_velocity']*.01
    v = f['y_velocity']*.01
    specific_energy = f['rho_E']*.1/rho - .5*(u*u + v*v)
    hot = T > 5000.
    positive_hrr = np.maximum(f['heatRelease'], 0.)
    input_text = (plot.parent/'inputs').read_text()
    p0 = float(re.findall(r'^prob.p0\s*=\s*([^#\n]+)', input_text, re.M)[-1])*.1
    front = []
    for column in pressure.T:
        ids = np.flatnonzero(column > 3.*p0)
        if not len(ids) or ids[-1] == len(x)-1:
            raise ValueError('Leading pressure front is absent or touches outlet')
        last = ids[-1]
        front.append(x[last] + (3.*p0-column[last])/(column[last+1]-column[last])*(x[last+1]-x[last]))
    front = np.asarray(front)
    dy = float(d['dx'][1])*10.
    lower = np.broadcast_to(y[None, :] <= y[0]-dy/2.+.5, T.shape)
    upper = np.broadcast_to(y[None, :] >= y[-1]+dy/2.-.5, T.shape)
    interior = ~(lower | upper)
    summary = {'plot': str(plot), 'time_s': d['time'], 'cell_count': T.size,
        'analysis_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'plot_header_sha256': hashlib.sha256((plot/'Header').read_bytes()).hexdigest(),
        'Tmax_K': float(T[i, j]), 'peak_index': [int(i), int(j)],
        'peak_xy_mm': [float(x[i]), float(y[j])],
        'peak_pressure_Pa': float(pressure[i, j]),
        'peak_density_kg_m3': float(rho[i, j]),
        'peak_internal_energy_J_kg': float(specific_energy[i, j]),
        'peak_velocity_m_s': [float(u[i, j]), float(v[i, j])],
        'peak_Y': {k: float(f[k][i, j]) for k in f if k.startswith('Y(')},
        'cells_above_5000_K': int(hot.sum()), 'hot_volume_fraction': float(hot.mean()),
        'hot_positive_hrr_fraction': float(positive_hrr[hot].sum()/positive_hrr.sum())
                                     if positive_hrr.sum() else None,
        'regional_Tmax_K': {k: float(T[mask].max()) for k, mask in
                           [('lower_0p5mm', lower), ('upper_0p5mm', upper), ('interior', interior)]},
        'domain_pressure_max_Pa': float(pressure.max()),
        'front_definition': 'Most downstream 3*p0 pressure crossing in each transverse column',
        'mean_front_mm': float(front.mean()),
        'front_rms_mm': float(front.std()),
        'front_span_mm': float(np.ptp(front)),
        'hot_cells': [{'index': [int(ii), int(jj)], 'xy_mm': [float(x[ii]), float(y[jj])],
                       'T_K': float(T[ii, jj]), 'p_Pa': float(pressure[ii, jj]),
                       'e_J_kg': float(specific_energy[ii, jj])}
                      for ii, jj in zip(*np.nonzero(hot))]}
    if a.compare_first:
        if reference is None:
            reference = {'T': T.copy(), 'p': pressure.copy(), 'time': d['time'], 'plot': str(plot)}
        assert abs(d['time']-reference['time']) < 1e-12
        assert reference['T'].shape == T.shape
        summary['comparison_to_first'] = {'plot': reference['plot'], **{
            label: {'maximum_absolute_difference': float(np.max(abs(values-reference[key]))),
                    'mean_absolute_difference': float(np.mean(abs(values-reference[key]))),
                    'rms_difference': float(np.sqrt(np.mean((values-reference[key])**2))),
                    'units': units}
            for key, values, label, units in [('T', T, 'temperature', 'K'), ('p', pressure, 'pressure', 'Pa')]}}
    results.append(summary)
    # Identical physical window makes the preserved near-wall event comparable.
    ix = (x >= 115.) & (x <= 128.)
    iy = y <= 3.
    for col, (values, label, limits, cmap) in enumerate([
            (T, 'Temperature (K)', (300, 5500), 'inferno'),
            (pressure/1e6, 'Pressure (MPa)', (0, 10), 'viridis'),
            (v, 'Wall-normal velocity (m/s)', (-1000, 1000), 'coolwarm')]):
        ax = axes[row, col]
        region = values[np.ix_(ix, iy)].T
        im = ax.pcolormesh(x[ix], y[iy], region, shading='nearest', cmap=cmap,
                           vmin=limits[0], vmax=limits[1], rasterized=True)
        if np.any(hot[np.ix_(ix, iy)]):
            ax.contour(x[ix], y[iy], T[np.ix_(ix, iy)].T, levels=[5000.],
                       colors='cyan', linewidths=.8)
        ax.set(xlabel='x (mm)', ylabel='y (mm)')
        ax.set_title(f'{label_run}\n{d["time"]*1e6:.4f} us; {label}', fontsize=10)
        fig.colorbar(im, ax=ax, shrink=.8)
fig.suptitle('Preserved lower-wall region; cyan contour: 5000 K')
fig.savefig(a.output/'near_wall_fields.png', dpi=170)
(a.output/'summary.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
