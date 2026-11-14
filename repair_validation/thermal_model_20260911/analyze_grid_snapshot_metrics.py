from pathlib import Path
import sys,json,csv,hashlib,re,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';sys.path.insert(0,str(r/'tools'))
import amrex_reader
from read_native_spray import read_native_spray
out=b/'grid_snapshot_metrics_v1';out.mkdir(exist_ok=False);rows=[];start=4.80012635646224e-5
cases=[(r/'repair_validation/thermal_20260911/replay_cfl20_v1','Reference 0.05 mm'),(Path('/dev/shm/my_pele_thermal_model_20260911/fine_main_depth_v2'),'Refined 0.025 mm')]
for root,label in cases:
 input_text=(root/'inputs').read_text();p0=float(re.findall(r'^prob.p0\s*=\s*([^#\n]+)',input_text,re.M)[-1])*.1;threshold=3*p0
 for p in sorted(root.glob('plt[0-9]*')):
  lines=(p/'Header').read_text().splitlines();time_s=float(lines[3+int(lines[1])])
  if time_s<start-1e-14:continue
  data=amrex_reader.read_plotfile(str(p));f=data['fields'];dx,dy=data['dx'];depth_cm=dx;T=f['Temp'];P=f['pressure']*.1;x=data['x']*10.;y=data['y']*10.
  front=[]
  for column in P.T:
   ids=np.flatnonzero(column>threshold)
   assert len(ids) and ids[-1]<len(x)-1
   i=ids[-1];front.append(x[i]+(threshold-column[i])/(column[i+1]-column[i])*(x[i+1]-x[i]))
  lp=read_native_spray(p);fields=lp['fields'];assert float(f['num_parcels'].sum())==lp['count']
  liquid_mass_g=float(np.sum(fields['number_density']*np.pi/6*.6814*fields['diam']**3))
  row={'case':label,'plot':str(p),'time_us':time_s*1e6,'spacing_mm':dx*10,'Tmax_K':float(T.max()),'lower_0p5mm_Tmax_K':float(T[:,y<=.5].max()),'hot_area_mm2':float(np.sum(T>5000)*dx*dy*100),'mean_front_mm':float(np.mean(front)),'front_rms_mm':float(np.std(front)),'front_span_mm':float(np.ptp(front)),'gas_mass_per_depth_kg_m':float(np.sum(f['density'])*dx*dy*.1),'liquid_mass_per_depth_kg_m':liquid_mass_g/depth_cm*.1,'represented_droplets_per_m':float(np.sum(fields['number_density'])/depth_cm*100),'parcel_count':lp['count'],'plot_header_sha256':hashlib.sha256((p/'Header').read_bytes()).hexdigest()};rows.append(row)
  print(label,row['time_us'],row['Tmax_K'],row['mean_front_mm'],flush=True)
with (out/'metrics.csv').open('w',newline='') as file:
 w=csv.DictWriter(file,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
fig,axes=plt.subplots(2,2,figsize=(11,7.5),constrained_layout=True)
for root,label in cases:
 selected=[q for q in rows if q['case']==label]
 for ax,key in zip(axes.flat,['mean_front_mm','front_rms_mm','liquid_mass_per_depth_kg_m','Tmax_K']):ax.plot([q['time_us'] for q in selected],[q[key] for q in selected],'o-',label=label,markersize=4)
for ax,title,unit in zip(axes.flat,['Mean leading pressure front','Transverse front variation','Liquid mass per unit depth','Saved-field maximum temperature'],['Position (mm)','RMS (mm)','Mass per depth (kg/m)','Temperature (K)']):
 ax.set(title=title,xlabel='Actual snapshot time (microseconds)',ylabel=unit);ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('Short-interval grid sensitivity with identical initial liquid loading\nFront: most downstream 3 p0 pressure crossing; open-domain masses need not be constant')
fig.savefig(out/'grid_snapshot_metrics.png',dpi=170)
(out/'summary.json').write_text(json.dumps({'rows':rows,'scope':'Actual snapshot times are retained; masses are normalized by the library depth Lz=dx. These are open-domain inventories, not mass conservation residuals. Finer-grid initialization is a conservative remap of the coarse trajectory at 48 us.'},indent=2))
