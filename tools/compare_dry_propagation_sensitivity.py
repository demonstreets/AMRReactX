"""Compare two complete dry propagation runs with identical physical initialization.

Reports full-interval numerical sensitivity, including same-time final fields.
It does not assign a universal acceptable error for detonation calculations.
"""
import argparse
import json
from pathlib import Path
import re

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import amrex_reader

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('baseline',type=Path,help='complete analysis directory')
p.add_argument('candidate',type=Path,help='complete analysis directory')
p.add_argument('output',type=Path)
a=p.parse_args()
analyses=[]
texts=[]
for folder in [a.baseline,a.candidate]:
    z=json.loads((folder/'analysis.json').read_text())
    if (z['partial_analysis'] or not z['completed_requested_time'] or
        not z['raw_fields_admissible'] or z['exit_code']!=0):
        raise ValueError('requires complete, successful, admissible propagation analyses')
    if any(row['parcel_count'] or row['liquid_mass_g'] for row in z['rows']):
        raise ValueError('this sensitivity tool requires dry gas in both cases')
    analyses.append(z)
    texts.append((Path(z['run'])/'inputs').read_text())

def value(text,key,required=True):
    entries=re.findall(r'^'+re.escape(key)+r'\s*=\s*([^#\n]+)',text,re.M)
    if not entries:
        if required:raise ValueError('missing input '+key)
        return None
    return entries[-1].split()

for key in ['geometry.prob_lo','geometry.prob_hi','geometry.is_periodic',
            'amr.n_cell','amr.max_level','prob.p0','prob.T0','prob.front',
            'prob.perturbation','prob.upstream_Y','pelec.lo_bc','pelec.hi_bc',
            'pelec.chemistry_transport_split']:
    if value(texts[0],key)!=value(texts[1],key):
        raise ValueError('physical discretization or initialization differs: '+key)
if analyses[0]['species_names']!=analyses[1]['species_names']:
    raise ValueError('species differ')
profiles=[(Path(z['run'])/'profile_SI.txt').read_bytes() for z in analyses]
if profiles[0]!=profiles[1]:raise ValueError('reference profiles differ')
final_time=[z['rows'][-1]['time_s'] for z in analyses]
if final_time[0]!=final_time[1]:raise ValueError('final physical times differ')
final_fields=[]
for z in analyses:
    row=z['rows'][-1]
    final_fields.append(amrex_reader.read_plotfile(str(Path(row['source_run'])/row['plot'])))
if not np.array_equal(final_fields[0]['x'],final_fields[1]['x']):
    raise ValueError('final grids differ')

differences={}
names=['density','rho_E','pressure','Temp','x_velocity']+['Y('+n+')' for n in analyses[0]['species_names']]
for name in names:
    b=final_fields[0]['fields'][name];c=final_fields[1]['fields'][name]
    if b.shape!=c.shape:raise ValueError('field shapes differ')
    error=np.abs(c-b)
    differences[name]={'maximum_absolute_difference_native_units':float(error.max()),
        'mean_absolute_difference_native_units':float(error.mean()),
        'maximum_difference_over_baseline_maximum':float(error.max()/max(np.abs(b).max(),1.e-100))}

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
history=[]
for idx,(z,raw) in enumerate(zip(analyses,final_fields)):
    t=np.array([row['time_s'] for row in z['rows']]);x=np.array([row['shock_x_cm'] for row in z['rows']])*.01
    mask=t>=.5*final_time[0]
    fit=np.polyfit(t[mask],x[mask],1)
    history.append({'speed_m_s':float(fit[0]),'sampled_window_s':[float(t[mask][0]),float(t[mask][-1])],
                    'fit_rms_m':float(np.sqrt(np.mean((x[mask]-np.polyval(fit,t[mask]))**2)))})
    label='Baseline' if idx==0 else 'Candidate';style='-' if idx==0 else '--'
    axes[0,0].plot(t*1e6,x*1000.,style,label=label)
    for axis,key,scale in [(axes[0,1],'pressure',1.e-7),(axes[1,0],'Temp',1.),(axes[1,1],'Y(nc7h16)',1.)]:
        axis.plot(np.asarray(raw['x'])*10.,raw['fields'][key].mean(axis=1)*scale,style,label=label)
for axis,title,xlabel,ylabel in zip(axes.flat,
    ['Shock propagation','Final pressure','Final gas temperature','Final gas fuel'],
    ['Time (microseconds)','x (mm)','x (mm)','x (mm)'],
    ['Shock position (mm)','Pressure (MPa)','Temperature (K)','Fuel mass fraction']):
    axis.set(title=title,xlabel=xlabel,ylabel=ylabel);axis.legend()
fig.suptitle('Complete dry propagation numerical sensitivity')
a.output.mkdir(parents=True,exist_ok=False)
fig.savefig(a.output/'dry_propagation_sensitivity.png',dpi=170);plt.close(fig)
result={'baseline_analysis':str(a.baseline.resolve()),'candidate_analysis':str(a.candidate.resolve()),
        'final_time_s':final_time[0],'late_half_fits':history,
        'relative_speed_difference':(history[1]['speed_m_s']-history[0]['speed_m_s'])/history[0]['speed_m_s'],
        'final_front_difference_mm':10.*(analyses[1]['rows'][-1]['shock_x_cm']-analyses[0]['rows'][-1]['shock_x_cm']),
        'maximum_temperature_difference_K':differences['Temp']['maximum_absolute_difference_native_units'],
        'maximum_mass_fraction_difference':max(v['maximum_absolute_difference_native_units'] for k,v in differences.items() if k.startswith('Y(')),
        'numerical_settings':[{k:value(text,k,False) for k in ['pelec.cfl','ode.rtol','ode.atol','cvode.solve_type']} for text in texts],
        'final_field_differences':differences,
        'interpretation':'Observed numerical sensitivity of matching complete dry runs; final fields share the same physical time and grid.'}
(a.output/'comparison.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='final_field_differences'}))
