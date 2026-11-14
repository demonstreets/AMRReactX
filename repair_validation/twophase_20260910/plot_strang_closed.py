import pathlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
b=pathlib.Path('/home/cj/my-pele/repair_validation/twophase_20260910')
d=json.loads((b/'strang_all_closed_comparison_v2.json').read_text())['runs']
ref=json.loads((b/'closed_coupling_verified_v1.json').read_text())['cantera_reference']
tr=np.array([v['time'] for v in ref]);Tr=np.array([v['T'] for v in ref])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,2,figsize=(11,8),layout='constrained')
colors={'dry_reactive':'#b65c22','wet_reactive':'#176685'}
comparison={}
for kind,color in colors.items():
    for version,style in [('v1','-'),('v2','--')]:
        rows=d[version][kind]['rows'];t=np.array([v['time'] for v in rows]);initial=rows[0]
        label=('Gas only' if kind=='dry_reactive' else 'Gas + droplets')+(' (dt=100 ns)' if version=='v1' else ' (dt=50 ns)')
        if version=='v1':
            ax[0,0].plot(t*1e6,[v['Tmax'] for v in rows],marker='o',ms=4,ls='none',color=color,label=label)
        if kind=='wet_reactive':
            ax[0,1].plot(t*1e6,[v['liquid_mass']/initial['liquid_mass'] for v in rows],style,color=color,label=label)
        den=abs(initial['gas_energy'])+abs(initial['liquid_model_energy'])
        ax[1,0].plot(t*1e6,[(v['combined_model_energy']-initial['combined_model_energy'])/den*1e12 for v in rows],style,color=color,label=label)
        if kind=='dry_reactive':
            comparison[version+'_cantera_max_temperature_error_K']=float(max(abs(np.interp(t,tr,Tr)-[v['Tmax'] for v in rows])))
    a=d['v1'][kind]['rows'];z=d['v2'][kind]['rows']
    tx=np.array([v['time'] for v in a]);tz=np.array([v['time'] for v in z]);diff=np.array([v['Tmax'] for v in z])-np.interp(tz,tx,[v['Tmax'] for v in a])
    ax[1,1].plot(tz*1e6,diff,color=color,label='Gas only' if kind=='dry_reactive' else 'Gas + droplets')
    comparison[kind+'_dt_refinement_max_temperature_difference_K']=float(max(abs(diff)))
ax[0,0].plot(tr*1e6,Tr,color='.25',lw=1.,label='Independent Cantera, gas only')
ax[0,0].set(title='A  Ignition and thermal response',ylabel='Gas temperature (K)')
ax[0,1].set(title='B  Complete liquid evaporation',ylabel='Liquid mass / initial liquid mass',ylim=(0,1.04))
ax[1,0].set(title='C  Closed combined-energy conservation',ylabel='Relative energy drift x 1e12')
ax[1,1].set(title='D  Time-step refinement',ylabel='T(50 ns) - T(100 ns) (K)')
for a in ax.flat:a.set_xlabel('Time (microseconds)');a.legend(fontsize=8)
fig.suptitle('Strang-coupled native gas/liquid reactor: 88 species, no hydrodynamic transport',fontsize=12)
fig.savefig(b/'strang_closed_verified_v1.png',dpi=170)
(b/'strang_closed_verified_v1_summary.json').write_text(json.dumps(comparison,indent=2))
print(json.dumps(comparison))

