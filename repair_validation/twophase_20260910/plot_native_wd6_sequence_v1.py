from pathlib import Path
import subprocess,json
import numpy as np
import cantera as ct
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910'
d=b/'wd6_native_temporal_sequence_v1';d.mkdir(exist_ok=False)
probe=b/'wd6_stoich_probe_v1/probe'
initial=[1400.,1.4e7,.6,11.,0.,0.,0.,41.36,1e-5,1e-8,1e-6]
p=subprocess.run([str(probe)],input=' '.join(map(str,initial))+'\n',capture_output=True,text=True,check=True)
(d/'native_trace.txt').write_text(p.stdout)
v=np.loadtxt(p.stdout.splitlines());g=ct.Solution(str(r/'external/PelePhysics/Mechanisms/heptane_wd6/mechanism.yaml'))
g.TPY=1400.,1.4e6,v[0,2:8];react=ct.IdealGasReactor(g,clone=True);net=ct.ReactorNet([react]);net.rtol=1e-10;net.atol=1e-14
ref=[]
for row in v:
    net.advance(row[0]);ref.append([react.T,*react.phase.Y])
ref=np.array(ref);terr=float(np.max(abs(v[:,1]-ref[:,0])));yerr=float(np.max(abs(v[:,2:8]-ref[:,1:])))
assert terr<.01 and yerr<1e-5,(terr,yerr)
t=v[:,0];fuel=v[:,2];co=v[:,4];co2=v[:,6]
def first_crossing(values,target):
    ids=np.flatnonzero((values-target)*(values[0]-target)<=0.)
    if not len(ids):return None
    i=int(ids[0])
    if i==0:return float(t[0])
    return float(t[i-1]+(target-values[i-1])/(values[i]-values[i-1])*(t[i]-t[i-1]))
result={'initial_temperature_K':1400.,'initial_pressure_Pa':1.4e6,'gas_phi':.6,
        'native_probe':str(probe),'native_input':initial,'native_integrator_rtol':1e-6,
        'concentration_epsilon_mol_m3':1e-10,'cantera_rtol':1e-10,'cantera_atol':1e-14,
        'maximum_cantera_temperature_difference_K':terr,'maximum_cantera_mass_fraction_difference':yerr,
        'fuel_half_consumption_time_s':first_crossing(fuel,.5*fuel[0]),
        'CO_peak_time_s':float(t[np.argmax(co)]),'CO_peak_mass_fraction':float(np.max(co)),
        'CO2_half_final_formation_time_s':first_crossing(co2,.5*(co2[0]+co2[-1])),
        'interpretation':'Temporal reaction sequence in a homogeneous constant-volume native WD6 reactor. These are not detonation residence times and do not identify fuel origin in a spray.'}
(d/'sequence.json').write_text(json.dumps(result,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,1,figsize=(10,7),layout='constrained',sharex=True)
for name,col,color in [('n-heptane',2,'#1d6685'),('CO',4,'#b65c22'),('CO2',6,'#30875c')]:
    ax[0].plot(t*1e6,v[:,col],color=color,label='Native '+name)
    ax[0].plot(t[::20]*1e6,ref[::20,col-1],ls='none',marker='o',mfc='none',ms=4,color=color,label='Cantera '+name)
ax[0].set(ylabel='Gas mass fraction',title='Fuel consumption and carbon-oxide intermediate')
ax[0].legend(ncol=2,fontsize=9)
ax[1].plot(t*1e6,v[:,1],color='#b65c22',label='Native energy-constrained reactor')
ax[1].plot(t[::20]*1e6,ref[::20,0],ls='none',marker='o',mfc='none',ms=4,color='.3',label='Independent Cantera')
ax[1].set(xlabel='Time (microseconds)',ylabel='Gas temperature (K)',title='Constant-volume thermal response')
ax[1].legend(fontsize=9)
fig.suptitle('WD6 temporal sequence: 1400 K, 1.4 MPa, gas equivalence ratio 0.6')
fig.savefig(d/'temporal_sequence.png',dpi=170)
plt.close(fig)
print(json.dumps(result))

