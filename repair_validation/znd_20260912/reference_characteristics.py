"""Interpolated reaction lengths and transparent residence-time diagnostics."""
from pathlib import Path
import json
import numpy as np
import cantera as ct
b=Path(__file__).resolve().parent;d=b/'reference_near_cj_v1';q=np.loadtxt(d/'profile_SI.txt');m=json.loads((d/'metadata.json').read_text());cj=json.loads((d/'CJ.json').read_text())[0]
species=m['species_names'];fuel=q[:,5+species.index('nc7h16')];w=m['D']-q[:,4]
tau=np.r_[0.,np.cumsum(.5*(1/w[1:]+1/w[:-1])*np.diff(q[:,0]))]
def first_cross(values,level,rising):
 ids=np.flatnonzero(((values[:-1]<level)&(values[1:]>=level)) if rising else ((values[:-1]>level)&(values[1:]<=level)))
 assert len(ids);i=int(ids[0]);f=(level-values[i])/(values[i+1]-values[i]);return {'distance_m':float(q[i,0]+f*(q[i+1,0]-q[i,0])),'estimated_residence_s':float(tau[i]+f*(tau[i+1]-tau[i]))}
lengths={str(v):first_cross(fuel,fuel[0]*(1-v),False) for v in [.1,.5,.9,.99]}
thermal_level=.5*(m['von_neumann']['T']+q[-1,3]);thermal=first_cross(q[:,3],thermal_level,True)
gas=ct.Solution('/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml');states=ct.SolutionArray(gas,shape=len(q));states.TDY=q[:,3],q[:,1],q[:,5:]
record={'fuel_conversion_interpolated':lengths,'thermal_half_level_K':thermal_level,'thermal_half':thermal,
 'residence_method':'Trapezoidal integral of dx/(D-u) over the exported reference; approximate diagnostic, not additional ODE solve.',
 'reference_end':{'x_m':float(q[-1,0]),'T_K':float(q[-1,3]),'p_Pa':float(q[-1,2]),'rho_kg_m3':float(q[-1,1])},
 'equilibrium_CJ':{k:cj[k] for k in ['T_K','p_Pa','rho_kg_m3','D_m_s']},
 'reversible_reactions':sum(rx.reversible for rx in gas.reactions()),'reaction_count':gas.n_reactions,
 'maximum_reference_lab_characteristic_m_s':float(np.max(abs(q[:,4])+states.sound_speed)),
 'minimum_common_thermo_temperature_K':gas.min_temp,'maximum_common_thermo_temperature_K':gas.max_temp}
(b/'reference_characteristics.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))

