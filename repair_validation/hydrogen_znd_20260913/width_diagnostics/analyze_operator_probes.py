"""Verify the isolated native hydro shock and CVODE chemistry against Cantera."""
from pathlib import Path
import json,sys
import numpy as np
import cantera as ct
from scipy.optimize import brentq
b=Path(__file__).resolve().parent;root=b.parent
sys.path.insert(0,'/home/cj/my-pele/tools');import amrex_reader
meta=json.loads((root/'reference_v1/metadata.json').read_text());wcomp=json.loads((b/'width_comparison.json').read_text())
mechanism='/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/LiDryer/mechanism.yaml'
gas=ct.Solution(mechanism);Y0=meta['upstream']['Y']
results={}
for name in ['hydro_only_2400_v2','hydro_only_9600_v2','chemistry_only_v1']:
    d=b/name;assert int((d/'exit_code').read_text())==0,name
    case=json.loads((d/'case.json').read_text());rows=[]
    if name.startswith('chemistry'):
        gas.TPY=meta['von_neumann']['T'],meta['von_neumann']['p'],Y0
        reactor=ct.IdealGasReactor(gas,clone=True);net=ct.ReactorNet([reactor]);net.rtol=1e-11;net.atol=1e-20
    for plot in sorted(Path(case['plot_root']).glob('plt*')):
        q=amrex_reader.read_plotfile(str(plot));f=q['fields'];mean=lambda k:f[k].mean(axis=1)
        T=mean('Temp');p=mean('pressure')*.1;x=q['x']*.01
        row={'time_s':q['time'],'T_min_K':float(T.min()),'T_max_K':float(T.max())}
        if name.startswith('hydro'):
            level=.5*(meta['upstream']['p']+meta['von_neumann']['p'])
            ids=np.flatnonzero((p[:-1]>=level)&(p[1:]<level));assert len(ids)==1
            j=ids[0];front=float(x[j]+(level-p[j])*(x[j+1]-x[j])/(p[j+1]-p[j]))
            row['shock_m']=front
        else:
            if q['time']>0:net.advance(q['time'])
            species=np.array([mean('Y('+s+')') for s in gas.species_names]).T
            row.update(native_T_K=float(T.mean()),Cantera_T_K=reactor.T,
                       temperature_error_K=float(T.mean()-reactor.T),
                       species_max_abs_error=float(np.max(abs(species-reactor.phase.Y))),
                       spatial_T_spread_K=float(T.max()-T.min()))
        rows.append(row)
    assert abs(rows[-1]['time_s']-case['stop_time_s'])<1e-14
    if name.startswith('hydro'):
        t=np.array([r['time_s'] for r in rows]);x=np.array([r['shock_m'] for r in rows]);keep=t>=.2e-6
        fit=np.polyfit(t[keep],x[keep],1);detail={'speed_m_s':float(fit[0]),'relative_error_percent':float(100*(fit[0]/meta['D']-1)),
                                             'position_fit_rms_m':float(np.sqrt(np.mean((x[keep]-np.polyval(fit,t[keep]))**2)))}
    else:detail={'max_abs_temperature_error_K':max(abs(r['temperature_error_K']) for r in rows),
                 'max_abs_species_error':max(r['species_max_abs_error'] for r in rows)}
    results[name]={'exit_code':0,'history':rows,**detail}

def frozen(speed):
    gas.TPY=300,101325,Y0;rho0=gas.density;h0=gas.enthalpy_mass;m=rho0*speed;mom=101325+rho0*speed**2
    def residual(rho):
        pressure=mom-m*m/rho
        gas.DPY=rho,pressure,Y0
        return gas.enthalpy_mass+.5*(m/rho)**2-h0-.5*speed**2
    grid=rho0*np.linspace(1.001,10,150);brackets=[(x,y) for x,y in zip(grid[:-1],grid[1:]) if residual(x)*residual(y)<0]
    rho=brentq(residual,*brackets[-1]);residual(rho)
    return {'T_K':gas.T,'p_Pa':gas.P,'rho_kg_m3':gas.density}
fine=wcomp['cases']['hydrogen_9600_cfl30_v1']['history']
shock_consistency=[]
for h in fine:
    pred=frozen(h['local_speed_m_s'])
    shock_consistency.append({'time_s':h['time_s'],'local_speed_m_s':h['local_speed_m_s'],'frozen_jump_at_local_speed':pred,
                              'observed_T_K':h['near_shock_T_K'],'observed_p_Pa':h['near_shock_p_Pa']})
delay=[]
for label,T,p in [('reference_VN',meta['von_neumann']['T'],meta['von_neumann']['p']),
                  ('fine_final_postshock',fine[-1]['near_shock_T_K'],fine[-1]['near_shock_p_Pa'])]:
    gas.TPY=T,p,Y0;r=ct.IdealGasReactor(gas,clone=True);net=ct.ReactorNet([r]);net.rtol=1e-10;net.atol=1e-19
    previous_t=0;previous_T=T
    while r.T<T+400 and net.time<1e-3:
        previous_t=net.time;previous_T=r.T;net.step()
    reached=r.T>=T+400
    time400=previous_t+(T+400-previous_T)/(r.T-previous_T)*(net.time-previous_t) if reached else None
    delay.append({'label':label,'initial_T_K':T,'initial_p_Pa':p,'fresh_composition':True,'temperature_rise_K':400,
                  'delay_s':time400,'reached':reached,'integration_end_s':net.time})
record={'probes':results,'fine_shock_consistency':shock_consistency,'Cantera_UV_temperature_sensitivity':delay,
        'limits':['Pure hydro and pure chemistry probes isolate basic operators, not their coupled stability.',
                  'UV +400 K delay measures thermochemical sensitivity at fresh composition; it is neither ZND induction time nor a CFD material-particle trajectory.',
                  'A changing wave speed and multiple heat-release peaks do not alone distinguish physical instability from numerical triggering or amplification.']}
(b/'operator_probe_results.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'probes':{k:{j:v for j,v in q.items() if j!='history'} for k,q in results.items()},'Cantera_UV_temperature_sensitivity':delay,'final_shock_consistency':shock_consistency[-1]},indent=2))
