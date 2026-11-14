"""Test whether front-location choices explain the measured speed deficit."""
from pathlib import Path
import sys,json
import numpy as np
b=Path(__file__).resolve().parent;root=b.parent
sys.path.insert(0,'/home/cj/my-pele/tools');import amrex_reader
meta=json.loads((root/'reference_v1/metadata.json').read_text())
def cross(x,y,level):
    i=np.flatnonzero((y[:-1]>=level)&(y[1:]<level))[-1]
    return float(x[i]+(level-y[i])*(x[i+1]-x[i])/(y[i+1]-y[i]))
records={}
for name in ['hydrogen_2400_cfl30_v1','hydrogen_4800_cfl30_v1','hydrogen_9600_cfl30_v1','hydrogen_4800_cfl15_v1']:
    s=json.loads((root/name/'analysis/summary.json').read_text());rows=[]
    for h in s['history']:
        q=amrex_reader.read_plotfile(h['plot']);x=q['x']*.01;f=q['fields'];p=f['pressure'].mean(axis=1)*.1;rho=f['density'].mean(axis=1)*1000
        dx=s['case']['dx_m'];xi=h['shock_m']-x;near=(xi>=3*dx)&(xi<=60e-6)
        adaptive=.5*(meta['upstream']['p']+np.median(p[near]))
        xp=.5*(x[:-1]+x[1:]);slope=-np.diff(p)/dx;candidate=np.flatnonzero(abs(xp-h['shock_m'])<1e-4);j=candidate[np.argmax(slope[candidate])]
        rows.append({'time_s':h['time_s'],'fixed_pressure':h['shock_m'],'adaptive_pressure':cross(x,p,adaptive),
                     'fixed_density':cross(x,rho,.5*(meta['upstream']['rho']+meta['von_neumann']['rho'])),
                     'maximum_front_gradient':float(xp[j])})
    t=np.array([r['time_s'] for r in rows]);keep=t>=2e-6
    fits={key:float(np.polyfit(t[keep],np.array([r[key] for r in rows])[keep],1)[0]) for key in rows[0] if key!='time_s'}
    records[name]={'fit_window_s':[2e-6,4e-6],'speeds_m_s':fits,'speed_spread_m_s':max(fits.values())-min(fits.values()),'history':rows}
(b/'shock_estimator_check.json').write_text(json.dumps(records,indent=2));print(json.dumps({n:{k:v for k,v in r.items() if k!='history'} for n,r in records.items()},indent=2))
