"""Inspect native planar fields and compare the freely moving wave with ZND."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np

p=argparse.ArgumentParser(description=__doc__);p.add_argument('name');p.add_argument('--partial',action='store_true');a=p.parse_args()
r=Path('/home/cj/my-pele');b=r/'repair_validation/znd_20260912';d=b/a.name
sys.path.insert(0,str(r/'tools'));import amrex_reader
case=json.loads((d/'case.json').read_text());ref=Path(case['reference']);meta=json.loads((ref/'metadata.json').read_text())
table=np.loadtxt(ref/'profile_SI.txt');species=meta['species_names'];D=meta['D'];p0=meta['upstream']['p'];rho0=meta['upstream']['rho'];Y0=np.array(meta['upstream']['Y']);dx=case['dx_m']
code=int((d/'exit_code').read_text()) if (d/'exit_code').exists() else None
if not a.partial:assert code==0,code
out=d/('analysis_partial' if a.partial else 'analysis');out.mkdir(exist_ok=True)
threshold=.5*(p0+meta['von_neumann']['p']);hist=[];last=None

def crossing(x,y,level):
 indices=np.flatnonzero((y[:-1]>=level)&(y[1:]<level))
 if not len(indices):return None
 i=indices[-1];return float(x[i]+(level-y[i])*(x[i+1]-x[i])/(y[i+1]-y[i]))

for plot in sorted(Path(case['plot_root']).glob('plt[0-9]*')):
 if not (plot/'Header').exists():continue
 try:q=amrex_reader.read_plotfile(str(plot))
 except Exception:
  if a.partial:continue
  raise
 f=q['fields'];x=q['x']*.01;mean=lambda k:f[k].mean(axis=1)
 density=mean('density')*1000.;pressure=mean('pressure')*.1;temperature=mean('Temp');u=mean('x_velocity')*.01;energy=mean('rho_E')*.1
 y=np.array([mean('Y('+s+')') for s in species]).T
 nonfinite=sum(int(np.count_nonzero(~np.isfinite(v))) for v in f.values())
 transverse=max(float(np.max(abs(v-v.mean(axis=1)[:,None])))/max(float(np.max(abs(v))),1.e-10) for v in f.values())
 shock=crossing(x,pressure,threshold);assert shock is not None
 xi=shock-x;mask=(xi>=.001)&(xi<=.015);assert mask.sum()>5
 actual={'rho':density,'p':pressure,'T':temperature,'u':u,'Y_fuel':y[:,species.index('nc7h16')],'Y_o2':y[:,species.index('o2')],'Y_co2':y[:,species.index('co2')],'Y_h2o':y[:,species.index('h2o')]}
 refcols={'rho':1,'p':2,'T':3,'u':4,**{'Y_'+label:5+species.index(s) for label,s in [('fuel','nc7h16'),('o2','o2'),('co2','co2'),('h2o','h2o')]}}
 scales={'rho':meta['von_neumann']['rho']-rho0,'p':meta['von_neumann']['p']-p0,'T':table[:,3].max()-300.,'u':D}
 errors={}
 for name,values in actual.items():
  expected=np.interp(xi,table[:,0],table[:,refcols[name]])
  errors[name]={'mean_absolute':float(np.mean(abs(values[mask]-expected[mask]))),'max_absolute':float(np.max(abs(values[mask]-expected[mask])))}
  if name in scales:errors[name]['normalized_L1']=errors[name]['mean_absolute']/scales[name]
 # Supplemental wider interval includes the principal temperature-rise region.
 # Preserve the original 1--15 mm targets separately; do not replace their metrics.
 wide=(xi>=.001)&(xi<=.030);wide_errors={}
 for name,values in actual.items():
  expected=np.interp(xi,table[:,0],table[:,refcols[name]])
  wide_errors[name]={'mean_absolute':float(np.mean(abs(values[wide]-expected[wide]))),'max_absolute':float(np.max(abs(values[wide]-expected[wide])))}
  if name in scales:wide_errors[name]['normalized_L1']=wide_errors[name]['mean_absolute']/scales[name]
 # Find the first fuel half-consumption crossing when moving downstream from the shock.
 ids=np.flatnonzero((xi>=0)&(xi<=.03))[::-1];fuel=actual['Y_fuel'];half=None
 for i,j in zip(ids[:-1],ids[1:]):
  if fuel[i]>=.5*Y0[species.index('nc7h16')] and fuel[j]<.5*Y0[species.index('nc7h16')]:
   level=.5*Y0[species.index('nc7h16')];half=float(xi[i]+(level-fuel[i])*(xi[j]-xi[i])/(fuel[j]-fuel[i]));break
 thermal_level=.5*(meta['von_neumann']['T']+table[-1,3]);thermal_half=None
 for i,j in zip(ids[:-1],ids[1:]):
  if temperature[i]<thermal_level<=temperature[j]:
   thermal_half=float(xi[i]+(thermal_level-temperature[i])*(xi[j]-xi[i])/(temperature[j]-temperature[i]));break
 near=(xi>=-2*dx)&(xi<=.001)
 row={'time_s':q['time'],'plot':str(plot),'shock_m':shock,'shock_minus_expected_m':shock-(.04+D*q['time']),
  'Tmin_K':float(temperature.min()),'Tmax_K':float(temperature.max()),'pmax_Pa':float(pressure.max()),
  'frozen_peak_pressure_Pa':float(pressure[near].max()),'fuel_half_distance_m':half,'thermal_half_distance_m':thermal_half,'thermal_half_level_K':thermal_level,'errors_1_to_15_mm':errors,'supplemental_errors_1_to_30_mm':wide_errors,
  'nonfinite_fields':nonfinite,'transverse_relative_spread':transverse,'min_Y':float(y.min()),'max_species_sum_error':float(np.max(abs(y.sum(axis=1)-1))),
  'mass_per_area_kg_m2':float(density.sum()*dx),'total_energy_per_area_J_m2':float(energy.sum()*dx),
  'net_mass_influx_kg_m2_s':float(density[0]*u[0]-density[-1]*u[-1]),
  'net_energy_influx_W_m2':float((energy[0]+pressure[0])*u[0]-(energy[-1]+pressure[-1])*u[-1])}
 hist.append(row);last=(x,xi,actual,energy,y)
assert hist
hist.sort(key=lambda z:z['time_s']);times=np.array([z['time_s'] for z in hist]);shocks=np.array([z['shock_m'] for z in hist])
fits={}
for lower in [0.,4.e-6,8.e-6]:
 keep=times>=lower
 if keep.sum()>=3:
  coeff=np.polyfit(times[keep],shocks[keep],1);res=shocks[keep]-np.polyval(coeff,times[keep]);fits[str(lower)]={'speed_m_s':float(coeff[0]),'relative_error_vs_CJ':float(coeff[0]/meta['CJ']-1),'rms_position_residual_m':float(np.sqrt(np.mean(res**2)))}
balance={}
for quantity,flux,label in [('mass_per_area_kg_m2','net_mass_influx_kg_m2_s','mass'),('total_energy_per_area_J_m2','net_energy_influx_W_m2','energy')]:
 change=hist[-1][quantity]-hist[0][quantity];integral=float(np.trapz([z[flux] for z in hist],times));balance[label]={'inventory_change':change,'integrated_boundary_influx':integral,'residual':change-integral,'relative_to_initial_inventory':abs(change-integral)/max(abs(hist[0][quantity]),1.e-30)}
summary={'case':case,'exit_code':code,'partial':a.partial,'end_time_s':float(times[-1]),'CJ_m_s':meta['CJ'],'initial_ZND_speed_m_s':D,'front_threshold_Pa':threshold,
 'comparison_window_m':[.001,.015],'comparison_method':'Shock-aligned cell-center samples; errors normalized by fixed reference jumps, same physical window at every resolution.',
 'wave_speed_fits':fits,'boundary_balance':balance,'history':hist,'max_nonfinite':max(z['nonfinite_fields'] for z in hist),
 'max_transverse_relative_spread':max(z['transverse_relative_spread'] for z in hist),'minimum_Y_all_plots':min(z['min_Y'] for z in hist),'maximum_species_sum_error':max(z['max_species_sum_error'] for z in hist)}
if not a.partial:assert abs(times[-1]-case['stop_time_s'])<1.e-14
assert summary['max_nonfinite']==0
(out/'summary.json').write_text(json.dumps(summary,indent=2))
x,xi,actual,energy,y=last
np.savez_compressed(out/'final_profile.npz',x_m=x,xi_m=xi,**actual,rho_E_J_m3=energy,Y=y)
np.savetxt(out/'front_history.csv',np.array([[z['time_s'],z['shock_m'],z['Tmax_K'],z['pmax_Pa']] for z in hist]),delimiter=',',header='time_s,shock_m,Tmax_K,pmax_Pa',comments='')
print(json.dumps({k:v for k,v in summary.items() if k not in ['case','history']},indent=2))

