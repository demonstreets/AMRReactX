import pathlib, sys, subprocess, json
import numpy as np
import cantera as ct
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910'
data={v:json.loads(subprocess.check_output([sys.executable,str(b/'analyze_spray_budget_v6.py'),v],text=True)) for v in ['v4','v5']}
for v in data:
    if any(a['exit']!=0 for a in data[v].values()):raise ValueError('all closed runs must complete')
code=(b/'analyze_spray_budget_v6.py').read_text().replace("['wet_inert','wet_reactive','dry_reactive']","['wet_inert']")
moving={v:json.loads(subprocess.check_output([sys.executable,'-c',code,v],text=True))['wet_inert'] for v in ['v6','v7']}
gas=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml'))
meta=json.loads((b/'reference_znd_v1/metadata.json').read_text());gas.TPY=1400,1e5,meta['upstream']['Y']
reactor=ct.IdealGasReactor(gas,energy='on',clone=False);net=ct.ReactorNet([reactor]);net.rtol=1e-10;net.atol=1e-20
reference=[]
for t in np.linspace(0,2e-4,201):
    if t>0:net.advance(t)
    reference.append({'time':float(t),'T':reactor.T,'Y':reactor.phase.Y.tolist()})
comparison={}
for label in ['wet_inert','wet_reactive','dry_reactive']:
    a=data['v4'][label]['rows'];z=data['v5'][label]['rows']
    if len(a)!=len(z):raise ValueError('matching sample times required')
    comparison[label]={'max_temperature_difference_K':max(abs(x['Tmax']-y['Tmax']) for x,y in zip(a,z)),
        'max_relative_liquid_mass_difference':max(abs(x['liquid_mass']-y['liquid_mass'])/max(a[0]['liquid_mass'],1e-100) for x,y in zip(a,z)),
        'max_relative_combined_fuel_difference':max(abs(x['fuel_mass']+x['liquid_mass']-y['fuel_mass']-y['liquid_mass'])/(a[0]['fuel_mass']+a[0]['liquid_mass']) for x,y in zip(a,z))}
tr=np.array([q['time'] for q in reference]);Tr=np.array([q['T'] for q in reference])
for v in data:
    a=data[v]['dry_reactive']['rows'];Tref=np.interp([q['time'] for q in a],tr,Tr)
    comparison['cantera_'+v]={'max_temperature_difference_K':float(np.max(abs(Tref-[q['Tmax'] for q in a]))),
        'max_relative_temperature_difference':float(np.max(abs(Tref-[q['Tmax'] for q in a])/Tref))}
out={'closed':data,'moving':moving,'cantera_reference':reference,'comparison':comparison,
     'note':'Closed, uniform, constant-volume gas-plus-liquid verification; this is not a spatial detonation result.'}
dest=b/'closed_coupling_verified_v1.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,2,figsize=(11,8),layout='constrained')
colors={'dry_reactive':'#b65c22','wet_reactive':'#176685','wet_inert':'#668765'}
labels={'dry_reactive':'Reactive gas, no liquid','wet_reactive':'Reactive gas + liquid','wet_inert':'Nonreacting gas + liquid'}
for k in labels:
    rows=data['v4'][k]['rows'];t=np.array([q['time'] for q in rows])*1e6
    ax[0,0].plot(t,[q['Tmax'] for q in rows],color=colors[k],label=labels[k])
    if rows[0]['liquid_mass']:
        ax[0,1].plot(t,[q['liquid_mass']/rows[0]['liquid_mass'] for q in rows],color=colors[k],label=labels[k])
    initial=rows[0];den=abs(initial['gas_energy'])+abs(initial['liquid_model_energy'])
    ax[1,0].plot(t,[(q['combined_model_energy']-initial['combined_model_energy'])/den*1e12 for q in rows],color=colors[k],label=labels[k])
ax[0,0].plot(tr*1e6,Tr,ls='--',color='.25',lw=1,label='Independent Cantera gas reactor')
ax[0,0].set(title='A  Thermal response and ignition',xlabel='Time (microseconds)',ylabel='Gas temperature (K)')
ax[0,0].legend(fontsize=8)
ax[0,1].set(title='B  Liquid evaporation',xlabel='Time (microseconds)',ylabel='Remaining liquid / initial liquid',ylim=(0,1.03))
ax[0,1].legend(fontsize=8)
ax[1,0].set(title='C  Closed total-energy balance',xlabel='Time (microseconds)',ylabel='Relative energy error x 1e12')
ax[1,0].legend(fontsize=8)
rows=moving['v6']['rows'];t=np.array([q['time'] for q in rows])*1e6;initial=rows[0]['combined_momentum'][0]
ax[1,1].plot(t,[q['gas_momentum'][0]/initial for q in rows],color='#176685',label='Gas momentum')
ax[1,1].plot(t,[q['liquid_momentum'][0]/initial for q in rows],color='#b65c22',label='Liquid momentum')
ax[1,1].plot(t,[q['combined_momentum'][0]/initial for q in rows],'--',color='.25',label='Combined momentum')
ax[1,1].set(title='D  Nonzero-slip momentum exchange',xlabel='Time (microseconds)',ylabel='x momentum / initial total')
ax[1,1].legend(fontsize=8)
fig.suptitle('Closed gas-liquid coupling: mass, energy, momentum and finite-rate chemistry',fontsize=13)
fig.savefig(b/'closed_coupling_verified_v1.png',dpi=160)
print(json.dumps({'comparison':comparison,'json':str(dest),'figure':str(b/'closed_coupling_verified_v1.png')}))
