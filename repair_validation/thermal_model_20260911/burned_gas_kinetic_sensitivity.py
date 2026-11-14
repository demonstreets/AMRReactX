"""Bounded burned-gas kinetic-network sensitivity, not a full fuel mechanism."""
from pathlib import Path
import json,time,hashlib,numpy as np,cantera as ct
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';base=b/'burned_gas_finite_rate_v3';out=b/'burned_gas_kinetic_sensitivity_v1';out.mkdir(exist_ok=False)
reference=ct.Solution(str(base/'burned_gas_gri_highT_trace_heptane.yaml'));lu_path=r/'external/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml';lu=ct.Solution(str(lu_path));prior=json.loads((base/'result.json').read_text())
common={n.lower() for n in reference.species_names}&set(lu.species_names);common.add('nc7h16_trace')
variants=[('gri_no_peroxides',reference,{n.lower() for n in reference.species_names}-{'ho2','h2o2'}),('gri_common_lu',reference,common),('lu_common_highT_thermo',lu,common)]
times=np.array([p['time_s'] for p in prior['samples'][0]['runs'][-1]['trajectory']]);all_results=[]
for name,source,allowed in variants:
 specs=[]
 for spec in reference.species():
  if spec.name.lower() in allowed:
   data=dict(spec.input_data);data['name']=spec.name.lower();specs.append(ct.Species.from_dict(data))
 gas=ct.Solution(thermo='ideal-gas',kinetics='gas',species=specs);indices=[]
 for i,rxn in enumerate(source.reactions()):
  if not {n.lower() for n in set(rxn.reactants)|set(rxn.products)}<=allowed:continue
  third=rxn.third_body
  if third is not None and third.name!='M' and third.name.lower() not in allowed:continue
  data=dict(rxn.input_data)
  if source is reference:
   import re
   # Lowercase species tokens; preserve pressure-dependent third-body M.
   data['equation']=re.sub(r'[A-Za-z][A-Za-z0-9_]*',lambda m:m.group(0) if m.group(0)=='M' else m.group(0).lower(),data['equation'])
  if 'efficiencies' in data:data['efficiencies']={k.lower():v for k,v in data['efficiencies'].items() if k.lower() in allowed}
  gas.add_reaction(ct.Reaction.from_dict(data,gas));indices.append(i)
 assert gas.n_reactions>0 and min(s.thermo.max_temp for s in gas.species())>=6000
 model=out/(name+'.yaml');gas.write_yaml(model);samples=[]
 for s in prior['samples']:
  source_sample=s['source_sample'];runs=[]
  for tol in [(1e-9,1e-18),(1e-11,1e-20)]:
   g=ct.Solution(str(model));Y={n:source_sample['Y']['Y('+('nc7h16' if n=='nc7h16_trace' else n)+')'] for n in ['nc7h16_trace','o2','co','h2o','co2','n2']}
   rho=source_sample['density_kg_m3'];u=source_sample['conserved_internal_energy_J_kg'];g.TDY=source_sample['T_K'],rho,Y;g.UV=u,1/rho
   elements=np.array([g.elemental_mass_fraction(n) for n in g.element_names]);reactor=ct.IdealGasReactor(g,energy='on',clone=False);net=ct.ReactorNet([reactor]);net.rtol,net.atol=tol;net.max_steps=200000;trajectory=[]
   for t in times:
    if t:net.advance(float(t))
    g=reactor.phase;err=float(np.max(abs(np.array([g.elemental_mass_fraction(n) for n in g.element_names])-elements)))
    point={'time_s':float(t),'T_K':g.T,'energy_error_J_kg':g.int_energy_mass-u,'element_error':err,'Ymin':float(g.Y.min())}
    assert 300<g.T<6000 and abs(point['energy_error_J_kg'])<.1 and err<1e-9 and point['Ymin']>-1e-12
    trajectory.append(point)
   runs.append({'rtol':tol[0],'atol':tol[1],'trajectory':trajectory})
  err=max(abs(x['T_K']-y['T_K']) for x,y in zip(runs[0]['trajectory'],runs[1]['trajectory']));assert err<.01
  samples.append({'sample_index':s['sample_index'],'max_tolerance_difference_K':err,'runs':runs})
 result={'name':name,'species_names':gas.species_names,'n_reactions':gas.n_reactions,'source_reaction_indices':indices,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'samples':samples};all_results.append(result)
 print(name,gas.n_species,gas.n_reactions,json.dumps([{'sample':s['sample_index'],'T0':s['runs'][-1]['trajectory'][0]['T_K'],'T2p5ns':s['runs'][-1]['trajectory'][4]['T_K'],'T100ns':s['runs'][-1]['trajectory'][9]['T_K'],'T2us':s['runs'][-1]['trajectory'][-1]['T_K']} for s in samples[-2:]]),flush=True)
(out/'result.json').write_text(json.dumps({'variants':all_results,'lu_source_sha256':hashlib.sha256(lu_path.read_bytes()).hexdigest(),'common_species':sorted(common),'scope':'Burned-gas network sensitivity with identical high-temperature thermodynamics and conserved input states. GRI and Lu common-network pair has identical species; rates and retained reactions differ. No-peroxide removal is a structural sensitivity. These derived subsets are not validated complete fuel mechanisms and do not establish kinetic accuracy at 5000 K or the sampled pressure.'},indent=2))
