import pathlib, sys, json, argparse
import numpy as np
r=pathlib.Path('/home/cj/my-pele')
sys.path.insert(0,str(r/'tools'))
import amrex_reader

parser=argparse.ArgumentParser()
parser.add_argument('run',type=pathlib.Path)
parser.add_argument('--output',type=pathlib.Path)
args=parser.parse_args()
rows=[]
for p in sorted(args.run.glob('plt*')):
    if not (p/'Header').exists():continue
    a=amrex_reader.read_plotfile(str(p));f=a['fields'];x=np.asarray(a['x'])
    pressure=f['pressure'].mean(axis=tuple(range(1,f['pressure'].ndim)))
    p0=float(pressure[-1]);threshold=3*p0
    active=np.flatnonzero(pressure>threshold)
    if not len(active) or active[-1]>=len(x)-1:
        raise ValueError('leading shock cannot be isolated from the right boundary')
    i=active[-1]
    shock=x[i]+(threshold-pressure[i])/(pressure[i+1]-pressure[i])*(x[i+1]-x[i])
    row={'plot':p.name,'time_s':a['time'],'shock_x_cm':float(shock),
         'shock_threshold_dyn_cm2':threshold,'pressure_max_dyn_cm2':float(f['pressure'].max()),
         'Tmin_K':float(f['Temp'].min()),'Tmax_K':float(f['Temp'].max()),
         'nonfinite_fields':sum(int((~np.isfinite(v)).sum()) for v in f.values())}
    ynames=[k for k in f if k.startswith('Y(')]
    if not ynames:raise ValueError('all gas mass fractions must be saved')
    row['Ymin']=min(float(f[k].min()) for k in ynames)
    row['Ysum_error']=float(np.max(np.abs(sum(f[k] for k in ynames)-1)))
    if 'heatRelease' in f:
        heat=f['heatRelease'].mean(axis=tuple(range(1,f['heatRelease'].ndim)))
        mask=(x<shock)&(x>shock-3.)
        ids=np.flatnonzero(mask)
        ih=ids[np.argmax(heat[mask])]
        row.update(heat_release_peak_x_cm=float(x[ih]),
                   heat_release_peak=float(heat[ih]),
                   shock_heat_release_separation_cm=float(shock-x[ih]))
    rows.append(row)
out={'run':str(args.run),'exit':int((args.run/'exit_code').read_text()) if (args.run/'exit_code').exists() else None,
     'rows':rows,'front_definition':'rightmost transverse-mean pressure crossing of three times the undisturbed right-boundary pressure'}
if len(rows)>=4:
    tail=[v for v in rows if v['time_s']>=.5*rows[-1]['time_s']]
    t=np.array([v['time_s'] for v in tail]);x=np.array([v['shock_x_cm'] for v in tail])*.01
    fit=np.polyfit(t,x,1);res=x-np.polyval(fit,t)
    out['late_half_fit']={'speed_m_s':float(fit[0]),'position_rms_residual_m':float(np.sqrt(np.mean(res**2))),
                          'start_s':float(t[0]),'end_s':float(t[-1]),'points':len(tail)}
    out['raw_fields_admissible']=all(v['nonfinite_fields']==0 and v['Tmin_K']>0 and v['Ymin']>=-1e-12 and v['Ysum_error']<1e-8 for v in rows)
if args.output:
    if args.output.exists():raise ValueError('refusing to overwrite prior evidence')
    args.output.write_text(json.dumps(out,indent=2))
print(json.dumps(out))
