from pathlib import Path
import csv,io,json,hashlib,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';out=b/'grid_history_final_v1';out.mkdir(exist_ok=False);start=4.80012635646224e-5
cases=[(r/'repair_validation/thermal_20260911/replay_cfl20_v1','0.05 mm reference',.05),(b/'fine_main_depth_v2','0.025 mm refined',.025)]
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True);results={}
for case,label,h in cases:
 assert int((case/'exit_code').read_text())==0
 raw=(case/'thermal_stages.csv').read_bytes();rows=[{k:v if k in ['stage','point'] else float(v) for k,v in q.items()} for q in csv.DictReader(io.StringIO(raw.decode()))]
 rows=[q for q in rows if q['time_start_s']>=start-1e-14];maximum=[q for q in rows if q['point']=='maximum'];end=[q for q in maximum if q['stage']=='chemistry_2'];assert end and abs(end[-1]['time_start_s']+end[-1]['dt_s']-5e-5)<1e-14
 groups={}
 for q in rows:groups.setdefault(q['step'],set()).add((q['stage'],q['point']))
 assert all(len(v)==8 for v in groups.values())
 peak=max(maximum,key=lambda q:q['T_K']);first=next((q for q in maximum if q['cells_above_fit_upper']>0),None);times=np.array([(q['time_start_s']+q['dt_s'])*1e6 for q in end]);area=np.array([q['cells_above_fit_upper']*h*h for q in end]);dt=np.array([q['dt_s'] for q in end]);duration=sum(dt)
 results[case.name]={'case':str(case),'label':label,'cell_spacing_mm':h,'effective_depth_mm':h,'start_time_s':start,'end_time_s':end[-1]['time_start_s']+end[-1]['dt_s'],'complete_steps':len(end),'peak_all_stages':peak,'first_above_5000':first,'final':end[-1],'nonfinite_max':max(q['cells_nonfinite_T'] for q in maximum),'final_hot_area_mm2':float(area[-1]),'max_endstep_hot_area_mm2':float(max(area)),'time_average_hot_area_mm2':float(np.dot(area,dt)/duration),'quadrature':'End-of-step rectangular rule; dt-weighted over common restart interval','dt_range_ns':[float(min(dt)*1e9),float(max(dt)*1e9)],'csv_sha256':hashlib.sha256(raw).hexdigest(),'input_sha256':hashlib.sha256((case/'inputs').read_bytes()).hexdigest()}
 axes[0,0].plot(times,[q['T_K'] for q in end],label=label);axes[0,1].plot(times,[q['lower_band_Tmax_K'] for q in end],label=label);axes[1,0].plot(times,area,label=label);axes[1,1].plot(times,dt*1e9,label=label)
for ax,title,units in zip(axes.flat,['Domain maximum after full step','Lower 0.5 mm wall band maximum','Area above 5000 K after full step','Time step at CFL = 0.2'],['Temperature (K)','Temperature (K)','Area per unit depth (mm$^2$)','Time step (ns)']):
 ax.set(title=title,xlabel='Time (microseconds)',ylabel=units,xlim=(start*1e6,50));ax.grid(alpha=.25);ax.legend(fontsize=9)
for ax in axes[0]:ax.axhline(5000,color='gray',ls='--',lw=.8)
axes[1,0].set_ylim(bottom=0);fig.suptitle('Same 48-us gas state, same droplet identities and liquid loading per unit depth\nShort-interval refinement sensitivity; no claim of full-trajectory grid convergence')
fig.savefig(out/'grid_history.png',dpi=170);(out/'summary.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
