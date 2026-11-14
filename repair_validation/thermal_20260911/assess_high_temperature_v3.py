"""Independent thermodynamic checks at the recorded high-temperature states.

No production mechanism is modified. Equilibrium is a limiting diagnostic,
not a finite-rate flow prediction or an alternative measured temperature.
"""
from pathlib import Path
import argparse
import hashlib
import json
import cantera as ct
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

r=Path('/home/cj/my-pele')
old=r/'repair_validation/twophase_20260910'
b=r/'repair_validation/thermal_20260911'
parser=argparse.ArgumentParser()
parser.add_argument('--hot-cell-file',type=Path,default=old/'wet_fine_thermal_extrapolation_v1.json')
parser.add_argument('--output',type=Path,default=b/'independent_thermodynamics_v2')
args=parser.parse_args()
out=args.output
out.mkdir(exist_ok=False)
mechanism=r/'external/PelePhysics/Mechanisms/heptane_wd6/mechanism.yaml'
original=ct.Solution(str(mechanism))
nasa_path=next(Path(p)/'nasa_gas.yaml' for p in ct.get_data_directories() if (Path(p)/'nasa_gas.yaml').is_file())
database={s.name:s for s in ct.Species.list_from_file(str(nasa_path))}
mapping={'nc7h16':'C7H16,n-heptane','o2':'O2','co':'CO','h2o':'H2O','co2':'CO2','n2':'N2'}
def renamed(source,name):
    data=dict(database[source].input_data)
    data['name']=name
    return ct.Species.from_dict(data)
reference_species=[renamed(mapping[n],n) for n in original.species_names]
reference=ct.Solution(thermo='ideal-gas',species=reference_species)
extra=['H2','H','O','OH','HO2','H2O2','N','NO','NO2','N2O']
expanded=ct.Solution(thermo='ideal-gas',species=reference_species+[renamed(n,n.lower()) for n in extra])
reference.write_yaml(str(out/'six_species_nasa_reference.yaml'))
expanded.write_yaml(str(out/'expanded_nasa_equilibrium_reference.yaml'))
hot=json.loads(args.hot_cell_file.read_text())
results=[]
for point in hot['hot_cells']:
    y={n:point['Y']['Y('+n+')'] for n in original.species_names}
    T=point['T_K'];rho=point['density_kg_m3']
    original.TDY=T,rho,y
    original_inferred_u=original.int_energy_mass
    target_u=point.get('conserved_internal_energy_J_kg',original_inferred_u)
    reference.TDY=T,rho,y
    cp_ratio=reference.cp_mass/original.cp_mass-1.
    cv_ratio=reference.cv_mass/original.cv_mass-1.
    du=reference.int_energy_mass-target_u
    reference.UV=target_u,1./rho
    fixed={'T_K':reference.T,'p_Pa':reference.P,'energy_residual_J_kg':reference.int_energy_mass-target_u}
    reference.equilibrate('UV',solver='auto',max_steps=3000)
    restricted={'T_K':reference.T,'p_Pa':reference.P,'Y':dict(zip(reference.species_names,reference.Y.tolist())),
                'energy_residual_J_kg':reference.int_energy_mass-target_u}
    expanded.TDY=T,rho,y
    expanded.UV=target_u,1./rho
    expanded.equilibrate('UV',solver='auto',max_steps=3000)
    full={'T_K':expanded.T,'p_Pa':expanded.P,'Y':dict(zip(expanded.species_names,expanded.Y.tolist())),
          'energy_residual_J_kg':expanded.int_energy_mass-target_u}
    results.append({'i':point['i'],'j':point['j'],'original_T_K':T,'target_internal_energy_J_kg':target_u,
        'source':point.get('source',{'input_file':str(args.hot_cell_file)}),
        'original_EOS_minus_conserved_internal_energy_J_kg':original_inferred_u-target_u,
        'independent_cp_relative_difference_at_original_T':cp_ratio,
        'independent_cv_relative_difference_at_original_T':cv_ratio,
        'independent_internal_energy_difference_at_original_T_J_kg':du,
        'independent_fixed_composition_UV':fixed,'independent_six_species_equilibrium_UV':restricted,
        'independent_expanded_equilibrium_UV':full})

maximum=max(hot['hot_cells'],key=lambda p:p['T_K'])
y={n:maximum['Y']['Y('+n+')'] for n in original.species_names}
rows=[]
for T in np.linspace(300.,6000.,115):
    original.TDY=T,maximum['density_kg_m3'],y
    reference.TDY=T,maximum['density_kg_m3'],y
    rows.append({'T_K':float(T),'original_cp_J_kg_K':original.cp_mass,'reference_cp_J_kg_K':reference.cp_mass,
        'original_cv_J_kg_K':original.cv_mass,'reference_cv_J_kg_K':reference.cv_mass,
        'original_u_J_kg':original.int_energy_mass,'reference_u_J_kg':reference.int_energy_mass})
result={'original_mechanism':str(mechanism),'original_mechanism_sha256':hashlib.sha256(mechanism.read_bytes()).hexdigest(),
    'input_hot_cell_file':str(args.hot_cell_file),'input_hot_cell_sha256':hashlib.sha256(args.hot_cell_file.read_bytes()).hexdigest(),
    'analysis_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'reference_database':str(nasa_path),'reference_database_sha256':hashlib.sha256(nasa_path.read_bytes()).hexdigest(),
    'reference_source_url':'https://github.com/Cantera/cantera/blob/main/data/nasa_gas.yaml',
    'nasa_report_url':'https://ntrs.nasa.gov/citations/19940013151',
    'related_nasa_glenn_2002_report':'https://ntrs.nasa.gov/citations/20020085330',
    'database_description_header':nasa_path.read_text().split('species:')[0],
    'cantera_version':ct.__version__,'original_fit_range_K':[original.min_temp,original.max_temp],
    'reference_fit_range_K':[reference.min_temp,reference.max_temp],
    'expanded_reference_fit_range_K':[expanded.min_temp,expanded.max_temp],
    'reference_species_mapping':mapping,'expanded_species':expanded.species_names,
    'hot_cells':results,'fixed_peak_composition_temperature_sweep':rows,
    'interpretation':'Fixed-composition UV compares caloric thermodynamics at the same conserved density, composition and energy. Equilibrium UV changes composition and is only a limiting sensitivity; it does not establish the local relaxation rate, shock cause, or actual flow temperature.'}
(out/'assessment.json').write_text(json.dumps(result,indent=2))
fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for name,label in [('original','Current WD6 thermodynamics'),('reference','Independent NASA database')]:
    axes[0].plot([q['T_K'] for q in rows],[q[name+'_cv_J_kg_K'] for q in rows],label=label)
axes[0].axvline(5000,color='.4',ls='--',label='Current fit upper limit')
axes[0].set(xlabel='Temperature (K)',ylabel='Mixture cv (J/kg/K)',title='Peak-cell fixed-composition heat capacity')
axes[0].legend(fontsize=8)
labels=['Recorded','Independent\nfixed composition','Independent\n6-species equilibrium','Independent\nexpanded equilibrium']
q=max(results,key=lambda p:p['original_T_K'])
vals=[q['original_T_K'],q['independent_fixed_composition_UV']['T_K'],q['independent_six_species_equilibrium_UV']['T_K'],q['independent_expanded_equilibrium_UV']['T_K']]
axes[1].bar(range(4),vals,color=['#94603b','#397998','#799f72','#8c88a2'])
axes[1].set(xticks=range(4),xticklabels=labels,ylabel='Temperature (K)',title='Same density and total internal energy')
axes[1].tick_params(axis='x',labelsize=8)
for i,v in enumerate(vals):axes[1].text(i,v+30,f'{v:.1f}',ha='center',fontsize=9)
fig.suptitle('Independent thermodynamics and equilibrium limits; no production model change')
fig.savefig(out/'thermodynamic_comparison.png',dpi=170)
print(json.dumps({'output':str(out),'peak_cell':q,'reference_fit_range_K':result['reference_fit_range_K']}))
