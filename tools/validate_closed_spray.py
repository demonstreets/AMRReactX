"""Validate raw closed native gas/liquid budgets in CGS units."""
import argparse,json,pathlib,re,sys
import numpy as np
import cantera as ct
import amrex_reader
from read_native_spray import read_native_spray

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('run',type=pathlib.Path)
p.add_argument('--output',type=pathlib.Path,required=True)
p.add_argument('--partial',action='store_true')
p.add_argument('--cantera',action='store_true',help='independent constant-volume gas-only reaction reference')
args=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[1]
d=args.run.resolve()
def inp(key,default=None):
    values=re.findall(r'^'+re.escape(key)+r'\s*=\s*(.*?)\s*(?:#.*)?$',(d/'inputs').read_text(),re.M)
    return values[-1].strip().strip('"') if values else default
if inp('geometry.is_periodic')!='1 1' or inp('pelec.do_hydro')!='0':
    raise ValueError('this validator requires the uniform 2D periodic closed test with hydro disabled')
species=(d/'profile_SI.txt').open().readline().split()[6:]
matches=[]
for mechanism in ['heptane_lu_88sk','heptane_wd6']:
    candidate=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms'/mechanism/'mechanism.yaml'))
    if candidate.species_names==species:matches.append(candidate)
if len(matches)!=1:raise ValueError('reference must identify exactly one supported mechanism species order')
gas=matches[0]
fuel='nc7h16';gas.TPX=300.,1.e5,{fuel:1.};h_ref=gas.enthalpy_mass*1.e4
cp=float(inp('particles.NC7H16_cp','2.2483e7'))
latent=float(inp('particles.NC7H16_latent','3.63e9'))
rho_l=float(inp('particles.NC7H16_rho','.6814'))
def analyze(d):
    code=int((d/'exit_code').read_text()) if (d/'exit_code').exists() else None
    out={'exit':code,'running':code is None,'rows':[]}
    if code is not None and code != 0 and not args.partial:
        raise ValueError('solver did not exit successfully')
    for plot in sorted(d.glob('plt*')):
        if not (plot/'Header').exists():continue
        a=amrex_reader.read_plotfile(str(plot));f=a['fields'];cell_volume=float(np.prod(a['dx'][:a['ndim']]))
        depth=a['dx'][0] if a['ndim']==2 else 1
        mg=float(f['density'].sum()*cell_volume*depth);eg=float(f['rho_E'].sum()*cell_volume*depth)
        row={'time':a['time'],'gas_mass':mg,'gas_energy':eg,'Tmin':float(f['Temp'].min()),'Tmax':float(f['Temp'].max()),
            'fuel_mass':float((f['density']*f['Y(nc7h16)']).sum()*cell_volume*depth),'water_mass':float((f['density']*f['Y(h2o)']).sum()*cell_volume*depth),
            'pressure_min':float(f['pressure'].min()),'pressure_max':float(f['pressure'].max()),'thickness_cm':depth,
            'nonfinite_fields':sum(int((~np.isfinite(v)).sum()) for v in f.values())}
        row['density_min']=float(f['density'].min())
        if args.cantera:
            row['mean_mass_fractions']=[float(np.mean(f['Y('+name+')'])) for name in gas.species_names]
        row['gas_momentum']=[float(np.sum(f['density']*f[k])*cell_volume*depth) for k in ['x_velocity','y_velocity']]
        row['liquid_momentum']=[0.,0.]
        if (plot/'particles/Header').exists():
            p=read_native_spray(plot);pf=p['fields'];m=pf['number_density']*rho_l*np.pi/6*pf['diam']**3
            ep=m*(h_ref-latent+cp*(pf['temperature']-300)+.5*(pf['xvel']**2+pf['yvel']**2))
            row['liquid_momentum']=[float(np.sum(m*pf[k])) for k in ['xvel','yvel']]
            invalid_finite=np.any(np.array([~np.isfinite(v) for v in pf.values()]),axis=0)
            row.update(liquid_mass=float(m.sum()),liquid_model_energy=float(ep.sum()),particle_count=p['count'],
                drop_Tmin=float(pf['temperature'].min()) if p['count'] else None,drop_Tmax=float(pf['temperature'].max()) if p['count'] else None,
                drop_dmin=float(pf['diam'].min()) if p['count'] else None,drop_dmax=float(pf['diam'].max()) if p['count'] else None,
                invalid_particles=int(((pf['number_density']<0)|(pf['diam']<=0)|(pf['temperature']<=0)|invalid_finite).sum()))
        else:row.update(liquid_mass=0.,liquid_model_energy=0.,particle_count=0,invalid_particles=0)
        row['combined_momentum']=(np.array(row['gas_momentum'])+row['liquid_momentum']).tolist()
        row['combined_mass']=row['gas_mass']+row['liquid_mass'];row['combined_model_energy']=row['gas_energy']+row['liquid_model_energy']
        ynames=[k for k in f if k.startswith('Y(') or k.startswith('Y_')]
        row['Y_names_sample']=ynames[:3]
        if ynames:
            row['Ymax']=max(float(f[k].max()) for k in ynames);row['Ymin']=min(float(f[k].min()) for k in ynames);row['Ysum_error']=float(np.max(np.abs(sum(f[k] for k in ynames)-1)))
            species_fields={k[2:-1] if k.startswith('Y(') else k[2:]:f[k] for k in ynames}
            if set(species_fields)!=set(gas.species_names):raise ValueError('incomplete species fields')
            masses=np.array([float(np.sum(f['density']*species_fields[s])*cell_volume*depth) for s in gas.species_names])
            masses[gas.species_index(fuel)]+=row['liquid_mass']
            row['element_masses']={element:float(sum(masses[n]*gas.n_atoms(n,element)*gas.atomic_weight(element)/gas.molecular_weights[n] for n in range(gas.n_species))) for element in gas.element_names}
        out['rows'].append(row)
    if out['rows']:
        first,last=out['rows'][0],out['rows'][-1]
        out['momentum_absolute_error']=(np.array(last['combined_momentum'])-first['combined_momentum']).tolist()
        out['mass_rel_error']=(last['combined_mass']-first['combined_mass'])/first['combined_mass']
        out['energy_rel_error']=(last['combined_model_energy']-first['combined_model_energy'])/(abs(first['gas_energy'])+abs(first['liquid_model_energy']))
        out['fuel_consumed_fraction']=1-(last['fuel_mass']+last['liquid_mass'])/(first['fuel_mass']+first['liquid_mass'])
        out['liquid_evaporated_fraction']=1-last['liquid_mass']/first['liquid_mass'] if first['liquid_mass'] else None
        out['element_relative_errors']={k:abs(last['element_masses'][k]-v)/max(abs(v),1.e-100) for k,v in first['element_masses'].items()}
        trace=out['rows'];times=np.array([v['time'] for v in trace]);temp=np.array([v['Tmax'] for v in trace])
        out['max_temperature_rise_rate_time']=float(times[np.argmax(np.gradient(temp,times))])
    return out

result=analyze(d)
rows=result['rows']
if not rows: raise ValueError('no complete raw plotfiles')
initial=rows[0]
mass0=initial['combined_mass']
energy_scale=abs(initial['gas_energy'])+abs(initial['liquid_model_energy'])
mass_error=max(abs(v['combined_mass']-mass0)/mass0 for v in rows)
energy_error=max(abs(v['combined_model_energy']-initial['combined_model_energy'])/energy_scale for v in rows)
element_error=max(abs(v['element_masses'][k]-value)/max(abs(value),1.e-100)
                  for v in rows for k,value in initial['element_masses'].items())
momentum_scale=max(mass0,sum(abs(x) for x in initial['gas_momentum'])+sum(abs(x) for x in initial['liquid_momentum']))
momentum_error=float(max(max(abs(np.array(v['combined_momentum'])-initial['combined_momentum']))/momentum_scale for v in rows))
valid=all(v['density_min']>0. and v['Tmin']>0. and v['pressure_min']>0. and
          v['nonfinite_fields']==0 and v['invalid_particles']==0 and
          v.get('Ymin',-1.)>=-1.e-12 and v.get('Ymax',2.)<=1.+1.e-12 and
          v.get('Ysum_error',1.)<=1.e-8 for v in rows)
requested=float(inp('stop_time','-1'))
if requested<=0.:requested=float(inp('max_step'))*float(inp('pelec.fixed_dt'))
completed=result['exit']==0 and rows[-1]['time']>=requested*(1.-1.e-9)
passed=bool(valid and completed and max(mass_error,energy_error,element_error,momentum_error)<=1.e-8)
result.update(raw_fields_admissible=valid,completed_requested_time=completed,passed=passed,
              partial_analysis=args.partial,run=str(d),requested_time_s=requested,
              maximum_mass_relative_drift=mass_error,maximum_total_energy_relative_drift=energy_error,
              maximum_element_relative_drift=element_error,maximum_scaled_momentum_drift=momentum_error,
              units='CGS; gas and liquid integrated with the native 2D depth dx',
              liquid_energy_reference='h_vapor(300 K) - latent + cp*(T-300 K) + kinetic energy')
if args.cantera:
    if any(v['liquid_mass']>0. for v in rows) or inp('pelec.do_react')!='1':
        raise ValueError('Cantera reference requires a reactive gas-only closed case')
    gas.TPY=initial['Tmax'],initial['pressure_max']*.1,initial['mean_mass_fractions']
    reactor=ct.IdealGasReactor(gas,energy='on',clone=False)
    net=ct.ReactorNet([reactor]);net.rtol=1.e-10;net.atol=1.e-20
    reference=[]
    for v in rows:
        elapsed=v['time']-initial['time']
        if elapsed>0.:net.advance(elapsed)
        reference.append({'time_s':v['time'],'temperature_K':reactor.T,
                          'mass_fractions':reactor.phase.Y.tolist()})
    terr=max(abs(v['Tmax']-q['temperature_K']) for v,q in zip(rows,reference))
    yerr=max(float(np.max(abs(np.array(v['mean_mass_fractions'])-q['mass_fractions']))) for v,q in zip(rows,reference))
    reference_pass=terr<=1. and yerr<=1.e-3
    result['cantera_reference']={'version':ct.__version__,'maximum_temperature_difference_K':terr,
        'maximum_absolute_mass_fraction_difference':yerr,'passed':reference_pass,'samples':reference,
        'acceptance':'maximum sampled temperature difference <= 1 K and absolute mass-fraction difference <= 0.001'}
    result['passed']=result['passed'] and reference_pass
args.output.parent.mkdir(parents=True,exist_ok=True)
if args.output.exists():raise FileExistsError(args.output)
args.output.write_text(json.dumps(result,indent=2))
brief={k:v for k,v in result.items() if k not in ['rows','cantera_reference']}
if args.cantera:brief['cantera_reference']={k:v for k,v in result['cantera_reference'].items() if k!='samples'}
print(json.dumps(brief))
if not valid or max(mass_error,energy_error,element_error,momentum_error)>1.e-8:raise SystemExit(2)
if not args.partial and not completed:raise SystemExit(3)
if args.cantera and not reference_pass:raise SystemExit(4)
