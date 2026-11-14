"""Supplemental domain-of-dependence and localized fuel-deficit diagnostics."""
from pathlib import Path
import sys,json
import numpy as np
import cantera as ct
b=Path(__file__).resolve().parent;r=Path('/home/cj/my-pele');sys.path.insert(0,str(r/'tools'));import amrex_reader
ref=np.loadtxt(b/'reference_near_cj_v1/profile_SI.txt');m=json.loads((b/'reference_near_cj_v1/metadata.json').read_text());sp=m['species_names'];j=sp.index('nc7h16')
gas=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml'));records={}
for d in sorted(b.glob('planar_*')):
 path=d/'analysis/summary.json'
 if not path.exists():continue
 s=json.loads(path.read_text());hist=[];amax=0.
 for row in s['history']:
  q=amrex_reader.read_plotfile(row['plot']);f=q['fields'];x=q['x']*.01;xi=row['shock_m']-x
  y=np.array([f['Y('+name+')'].mean(axis=1) for name in sp]).T;rho=f['density'].mean(axis=1)*1000.;T=f['Temp'].mean(axis=1);u=f['x_velocity'].mean(axis=1)*.01
  states=ct.SolutionArray(gas,shape=len(x));states.TDY=T,rho,y;cmax=float(np.max(abs(u)+states.sound_speed));amax=max(amax,cmax)
  mask=(xi>=.0005)&(xi<=.007);ids=np.flatnonzero(mask);deficit=y[:,j]-np.interp(xi,ref[:,0],ref[:,5+j]);k=int(ids[np.argmin(deficit[mask])])
  hist.append({'time_s':row['time_s'],'fuel_deficit_location_behind_shock_m':float(xi[k]),'fuel_deficit_Y':float(deficit[k]),'frozen_material_estimate_behind_shock_m':float(row['shock_m']-(.04+m['von_neumann']['u']*row['time_s'])),'max_abs_u_plus_frozen_c_m_s':cmax})
 width= s['history'][-1]['shock_m']-.030;travel=amax*s['end_time_s']
 records[d.name]={'max_characteristic_all_saved_plots_m_s':amax,'sampled_characteristic_bound_travel_m':travel,'left_edge_of_final_wide_comparison_m':width,'left_boundary_cannot_reach_wide_comparison_under_sampled_bound':travel<width,'note':'Uses the largest frozen characteristic over saved plots, not a strict bound over every unsaved time step. Fuel-deficit advection estimate is a diagnostic hypothesis, not a material tracer or root-cause proof.','history':hist}
(b/'profile_diagnostics.json').write_text(json.dumps(records,indent=2));print(json.dumps({k:{z:v for z,v in v.items() if z!='history'} for k,v in records.items()},indent=2))

