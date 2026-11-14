import pathlib,sys,json,numpy as np,cantera as ct
r=pathlib.Path('/home/cj/my-pele');sys.path.insert(0,str(r/'tools'))
import amrex_reader
from read_native_spray import read_native_spray
base=r/'repair_validation/twophase_20260910'
gas=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml'))
fuel='nc7h16';gas.TPX=300,1.e5,{fuel:1};h_ref=gas.enthalpy_mass*1.e4
cp=2.2483e7;latent=3.63e9;rho_l=.6814
version=sys.argv[1] if len(sys.argv)>1 else 'v3'
result={}
for label in ['wet_inert','wet_reactive','dry_reactive']:
    d=base/('spray_budget_'+label+'_'+version)
    code=int((d/'exit_code').read_text()) if (d/'exit_code').exists() else None
    out={'exit':code,'running':code is None,'rows':[]}
    if code:out['log_tail']=(d/'run.log').read_text()[-2000:];result[label]=out;continue
    for plot in sorted(d.glob('plt*')):
        if not (plot/'Header').exists():continue
        a=amrex_reader.read_plotfile(str(plot));f=a['fields'];cell_volume=float(np.prod(a['dx'][:a['ndim']]))
        depth=a['dx'][0] if a['ndim']==2 else 1
        mg=float(f['density'].sum()*cell_volume*depth);eg=float(f['rho_E'].sum()*cell_volume*depth)
        row={'time':a['time'],'gas_mass':mg,'gas_energy':eg,'Tmin':float(f['Temp'].min()),'Tmax':float(f['Temp'].max()),
            'fuel_mass':float(f['rho_nc7h16'].sum()*cell_volume*depth),'water_mass':float(f['rho_h2o'].sum()*cell_volume*depth),
            'pressure_min':float(f['pressure'].min()),'pressure_max':float(f['pressure'].max()),'thickness_cm':depth,
            'nonfinite_fields':sum(int((~np.isfinite(v)).sum()) for v in f.values())}
        row['gas_momentum']=[float(np.sum(f['density']*f[k])*cell_volume*depth) for k in ['x_velocity','y_velocity']]
        row['liquid_momentum']=[0.,0.]
        if (plot/'particles/Header').exists():
            p=read_native_spray(plot);pf=p['fields'];m=pf['number_density']*rho_l*np.pi/6*pf['diam']**3
            ep=m*(h_ref-latent+cp*(pf['temperature']-300)+.5*(pf['xvel']**2+pf['yvel']**2))
            row['liquid_momentum']=[float(np.sum(m*pf[k])) for k in ['xvel','yvel']]
            row.update(liquid_mass=float(m.sum()),liquid_model_energy=float(ep.sum()),particle_count=p['count'],
                drop_Tmin=float(pf['temperature'].min()) if p['count'] else None,drop_Tmax=float(pf['temperature'].max()) if p['count'] else None,
                drop_dmin=float(pf['diam'].min()) if p['count'] else None,drop_dmax=float(pf['diam'].max()) if p['count'] else None,
                invalid_particles=int(((pf['number_density']<0)|(pf['diam']<=0)|(pf['temperature']<=0)).sum()))
        else:row.update(liquid_mass=0.,liquid_model_energy=0.,particle_count=0,invalid_particles=0)
        row['combined_momentum']=(np.array(row['gas_momentum'])+row['liquid_momentum']).tolist()
        row['combined_mass']=row['gas_mass']+row['liquid_mass'];row['combined_model_energy']=row['gas_energy']+row['liquid_model_energy']
        ynames=[k for k in f if k.startswith('Y(') or k.startswith('Y_')]
        row['Y_names_sample']=ynames[:3]
        if ynames:
            row['Ymin']=min(float(f[k].min()) for k in ynames);row['Ysum_error']=float(np.max(np.abs(sum(f[k] for k in ynames)-1)))
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
    result[label]=out
print(json.dumps(result))
