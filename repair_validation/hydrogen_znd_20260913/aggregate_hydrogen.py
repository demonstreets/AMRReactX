"""Build reproducible ZND comparison figures and machine-readable assessment."""
from pathlib import Path
import argparse,json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=Path(__file__).resolve().parent)
p.add_argument('--partial',action='store_true');a=p.parse_args();b=a.base
out=b/('results_partial' if a.partial else 'results');out.mkdir(exist_ok=True)
names=['hydrogen_2400_cfl30_v1','hydrogen_4800_cfl30_v1','hydrogen_9600_cfl30_v1','hydrogen_4800_cfl15_v1']
refdir=b/'reference_v1';meta=json.loads((refdir/'metadata.json').read_text());audit=json.loads((refdir/'reference_audit.json').read_text())
ref=np.loadtxt(refdir/'profile_SI.txt');species=meta['species_names'];D=meta['CJ']
characteristics=json.loads((b/'reference_quality.json').read_text());Lhalf=characteristics['reference_fuel_half']['x_m']
data=[];rows=[]
for name in names:
 path=b/name/'analysis/summary.json'
 if not path.exists():
  if a.partial:continue
  raise FileNotFoundError(path)
 s=json.loads(path.read_text());q=np.load(path.parent/'final_profile.npz');h=s['history'][-1];err=h['errors_0p05_to_3_mm'];fit=s['wave_speed_fits']['2e-06'];case=s['case']
 label=f"{case['nx']} cells, CFL {case['cfl']:g}"
 row={'name':name,'nx':case['nx'],'dx_mm':case['dx_m']*1e3,'cfl':case['cfl'],'end_time_us':s['end_time_s']*1e6,
  'speed_m_s':fit['speed_m_s'],'speed_error_percent':100*fit['relative_error_vs_CJ'],
  'speed_3_4_m_s':s['wave_speed_fits']['3e-06']['speed_m_s'],
  'position_fit_rms_um':fit['rms_position_residual_m']*1e6,
  'fuel_half_mm':h['fuel_half_distance_m']*1e3 if h['fuel_half_distance_m'] else None,
  'fuel_half_error_percent':100*(h['fuel_half_distance_m']/Lhalf-1) if h['fuel_half_distance_m'] else None,
  'thermal_half_mm':h['thermal_half_distance_m']*1e3,
  'thermal_half_error_percent':100*(h['thermal_half_distance_m']/characteristics['reference_thermal_half']['x_m']-1),
  'frozen_peak_error_percent':100*(h['frozen_peak_pressure_Pa']/meta['von_neumann']['p']-1),
  'Tmax_K':h['Tmax_K'],
  **{k+'_L1_percent':100*err[k]['normalized_L1'] for k in ['p','T','rho','u']},
  **{k+'_MAE':err[k]['mean_absolute'] for k in ['Y_fuel','Y_o2','Y_oh','Y_h2o']},
  **{k+'_core_L1_percent':100*h['supplemental_core_errors_0p05_to_0p5_mm'][k]['normalized_L1'] for k in ['p','T','rho','u']},
  'mass_balance_relative':s['boundary_balance']['mass']['relative_to_initial_inventory'],
  'energy_balance_relative':s['boundary_balance']['energy']['relative_to_initial_inventory'],
  'max_species_sum_error':s['maximum_species_sum_error'],'nonfinite':s['max_nonfinite'],
  'transverse_relative_spread':s['max_transverse_relative_spread'],'exit_code':s['exit_code']}
 rows.append(row);data.append((label,s,q))
assert rows
with (out/'metrics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.22,'figure.dpi':140,'savefig.dpi':180})
colors=['#1677b8','#e58323','#2b994f','#9257ac'];styles=['-','-','-','--']
fig,axs=plt.subplots(2,2,figsize=(11,7),sharex=True)
for ax,key,col,factor,title in zip(axs.flat,['p','T','rho','u'],[2,3,1,4],[1e-6,1,1,1],['Pressure (MPa)','Temperature (K)','Density (kg/m3)','Lab velocity (m/s)']):
 ax.plot(ref[:,0]*1e3,ref[:,col]*factor,'k-',lw=2,label='Independent near-CJ ZND')
 for (label,s,q),color,style in zip(data,colors,styles):ax.plot(q['xi_m']*1e3,q[key]*factor,color=color,ls=style,lw=1.2,label=label)
 ax.set(xlim=(-.025,3),ylabel=title,xlabel='Distance behind numerical shock (mm)')
axs[0,0].legend(fontsize=8);fig.suptitle('Freely propagating planar wave at 4 microseconds')
fig.tight_layout();fig.savefig(out/'znd_structure.png')
for ax in axs.flat: ax.set_xlim(-.025,.8)
fig.savefig(out/'znd_structure_reaction_zone.png');plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(11,7),sharex=True)
for ax,key,sp in zip(axs.flat,['Y_fuel','Y_o2','Y_oh','Y_h2o'],['H2','O2','OH','H2O']):
 ax.plot(ref[:,0]*1e3,ref[:,5+species.index(sp)],'k-',lw=2,label='Independent near-CJ ZND')
 for (label,s,q),color,style in zip(data,colors,styles):ax.plot(q['xi_m']*1e3,q[key],color=color,ls=style,lw=1.2,label=label)
 ax.set(xlim=(0,0.8),ylabel=sp+' mass fraction',xlabel='Distance behind numerical shock (mm)')
axs[0,0].axvline(Lhalf*1e3,color='gray',ls=':',label='ZND fuel half-consumption');handles, labels = axs[0,0].get_legend_handles_labels(); fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5,.95), ncol=3, fontsize=8)
fig.suptitle('Species profiles: reaction timing is assessed separately from wave speed')
fig.tight_layout(rect=[0,0,1,.85]);fig.savefig(out/'znd_species.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4))
for (label,s,q),color,style in zip(data,colors,styles):
 h=s['history'];t=np.array([v['time_s'] for v in h])*1e6
 axs[0].plot(t,np.array([v['shock_minus_expected_m'] for v in h])*1e3,color=color,ls=style,marker='.',label=label)
 axs[1].plot(t,[v['fuel_half_distance_m']*1e3 if v['fuel_half_distance_m'] else np.nan for v in h],color=color,ls=style,marker='.',label=label)
axs[0].set(xlabel='Time (microseconds)',ylabel='Front minus initial CJ trajectory (mm)');axs[0].legend(fontsize=8)
axs[1].axhline(Lhalf*1e3,color='k',ls=':',label='ZND');axs[1].set(xlabel='Time (microseconds)',ylabel='Fuel half-consumption length (mm)');axs[1].legend(fontsize=8)
fig.tight_layout();fig.savefig(out/'znd_history.png');plt.close(fig)
assessment={'reference':audit,'reference_characteristics':characteristics,'rows':rows,'status':'incomplete' if a.partial else 'assessed',
 'scope':'Short-duration planar reactive-Euler consistency check using native CPU LiDryer H2-air; not a long-time stability, GPU, other chemical mechanisms, spray, diffusion or AMR validation.'}
if len(rows)==4:
 fine=rows[2];scope=json.loads((b/'validation_scope.json').read_text());limits=scope['targets']
 checks={'CJ_sonic':audit['CJ_sonic_relative_error']<1e-6,
 'reference_energy':audit['max_energy_relative_residual']<1e-7,
 'fine_wave_speed':abs(fine['speed_error_percent'])<100*limits['fine_mean_speed_relative_error'],
 'fine_flow_profile':all(fine[k+'_L1_percent']<100*limits['fine_flow_normalized_L1'] for k in ['p','T','rho','u']),
 'fine_major_species':all(fine[k+'_MAE']<limits['fine_species_mean_abs_Y_error'] for k in ['Y_fuel','Y_o2','Y_oh','Y_h2o']),
 'fine_fuel_half_length':fine['fuel_half_error_percent'] is not None and abs(fine['fuel_half_error_percent'])<100*limits['fine_fuel_half_relative_error'],
 'fine_thermal_half_length':abs(fine['thermal_half_error_percent'])<100*limits['fine_thermal_half_relative_error'],
 'all_cases_finite':all(v['nonfinite']==0 for v in rows),
 'all_cases_species_sum':all(v['max_species_sum_error']<limits['max_species_sum_error'] for v in rows),
 'all_cases_exit_zero':all(v['exit_code']==0 and abs(v['end_time_us']-4)<1e-10 for v in rows)}
 assessment['checks']=checks;assessment['all_preregistered_targets_met']=all(checks.values())
 assessment['spatial_error_trends']={k:[v[k] for v in rows[:3]] for k in ['speed_error_percent','fuel_half_error_percent','p_L1_percent','T_L1_percent','rho_L1_percent','u_L1_percent','Y_fuel_MAE']}
 assessment['temporal_metric_differences_CFL015_minus_030']={k:rows[3][k]-rows[1][k] for k in ['speed_m_s','fuel_half_mm','p_L1_percent','T_L1_percent','rho_L1_percent','u_L1_percent','Y_fuel_MAE']}
 q1=data[1][2];q2=data[3][2];xi=np.linspace(.00005,.003,1181)
 # Both shock-relative coordinates descend with increasing lab x.
 assessment['temporal_profile_MAE_same_window']={k:float(np.mean(abs(np.interp(xi,q2['xi_m'][::-1],q2[k][::-1])-np.interp(xi,q1['xi_m'][::-1],q1[k][::-1])))) for k in ['p','T','rho','u','Y_fuel','Y_o2','Y_oh','Y_h2o']}
(out/'assessment.json').write_text(json.dumps(assessment,indent=2))
print(json.dumps({'output':str(out),'rows':rows,'checks':assessment.get('checks')},indent=2))
