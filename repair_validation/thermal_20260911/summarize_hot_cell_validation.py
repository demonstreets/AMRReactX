"""Report completed integrations separately from native attempt-limit failures."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser()
parser.add_argument('directory',nargs='?',type=Path,default=Path('/home/cj/my-pele/repair_validation/thermal_20260911/hot_cell_chemistry_validation_v2'))
d=parser.parse_args().directory
source=d/'validation.json'
data=json.loads(source.read_text())
levels=[]
failures=[]
for rtol in [1e-4,1e-5,1e-6,1e-8]:
    entries=[(name,x) for name,result in data['results'].items() for x in result['native_runs'] if x['rtol']==rtol]
    completed=[x for _,x in entries if x['success']]
    levels.append({'rtol':rtol,'completed':len(completed),'requested':len(entries),
        'maximum_temperature_error_K':max(abs(x['T_difference_from_reference_K']) for x in completed),
        'maximum_mass_fraction_error':max(x['max_Y_difference_from_reference'] for x in completed),
        'maximum_difference_from_recorded_flow_stage_K':max(abs(x['T_difference_from_recorded_flow_stage_K']) for x in completed)})
    for name,x in entries:
        if not x['success']:
            failures.append({'sample':name,'rtol':rtol,'accepted_steps':x['accepted_steps'],
                'rejected_steps':x['rejected_steps'],
                'reason':'Native integrate returned false; total attempted substeps reached 20000.' if
                         x['accepted_steps']+x['rejected_steps']>=20000 else 'Native integrate returned false.',
                'interpretation':'Partial state is not a completed endpoint; excluded from accuracy statistics.'})
summary={'raw_validation_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'sample_count':len(data['results']),'levels':levels,'incomplete_runs':failures,
    'all_requested_native_integrations_completed':not failures,
    'reference_self_comparison_max_temperature_difference_K':max(x['reference_convergence']['temperature_difference_K'] for x in data['results'].values()),
    'reference_self_comparison_max_mass_fraction_difference':max(x['reference_convergence']['max_Y_difference'] for x in data['results'].values()),
    'interpretation':data['interpretation']}
(d/'validation_summary.json').write_text(json.dumps(summary,indent=2))
common=[row for row in levels if row['completed']==row['requested']]
fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
labels=[f"{row['rtol']:.0e}" for row in common]
for ax,key,title in zip(axes,['maximum_temperature_error_K','maximum_mass_fraction_error'],
        ['Maximum temperature error (K)','Maximum mass-fraction error']):
    values=[row[key] for row in common]
    bars=ax.bar(labels,values,color=['#4c78a8','#f58518','#54a24b'])
    ax.set_yscale('log');ax.set(xlabel='Native relative tolerance',ylabel=title,title=title)
    ax.grid(axis='y',alpha=.2)
    for bar,value in zip(bars,values):
        ax.annotate(f'{value:.3g}',(bar.get_x()+bar.get_width()/2,value),xytext=(0,4),
                    textcoords='offset points',ha='center',fontsize=9)
fig.suptitle(f'Independent Radau comparison: all {summary["sample_count"]} sampled chemical half-steps completed at shown tolerances')
fig.text(.5,-.02,f'The 1e-8 tolerance is excluded: {levels[-1]["requested"]-levels[-1]["completed"]} of {levels[-1]["requested"]} native integrations did not complete.',ha='center',fontsize=9)
fig.savefig(d/'chemical_tolerance_comparison.png',dpi=170,bbox_inches='tight')
print(json.dumps(summary,indent=2))
