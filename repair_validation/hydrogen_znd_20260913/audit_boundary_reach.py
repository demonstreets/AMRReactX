"""Estimate boundary reach from frozen acoustic speeds in saved native fields."""
from pathlib import Path
import json,sys
import numpy as np,cantera as ct
b=Path(__file__).resolve().parent;r=Path('/home/cj/my-pele');sys.path.insert(0,str(r/'tools'));import amrex_reader
names=['hydrogen_2400_cfl30_v1','hydrogen_4800_cfl30_v1','hydrogen_9600_cfl30_v1','hydrogen_4800_cfl15_v1'];records=[]
g=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/LiDryer/mechanism.yaml'))
for name in names:
 p=b/name/'analysis/summary.json'
 if not p.exists():continue
 s=json.loads(p.read_text());speeds=[]
 for h in s['history']:
  q=amrex_reader.read_plotfile(h['plot']);f=q['fields'];mean=lambda key:f[key].mean(axis=1)
  gas=ct.SolutionArray(g,len(q['x']));Y=np.array([mean('Y('+sp+')') for sp in g.species_names]).T;gas.TPY=mean('Temp'),mean('pressure')*.1,Y
  u=mean('x_velocity')*.01;speeds.append(float(np.max(abs(u)+gas.sound_speed)))
 vmax=max(speeds);t=s['end_time_s'];front=s['history'][-1]['shock_m'];gap=front-.003-vmax*t
 records.append({'name':name,'max_saved_abs_u_plus_frozen_c_m_s':vmax,'estimated_left_boundary_reach_m':vmax*t,'final_comparison_window_left_m':front-.003,'estimated_margin_m':gap,'final_front_m':front,'right_boundary_m':s['case']['length_m'],'left_reach_outside_window':gap>0,'front_inside_domain':front<s['case']['length_m']})
record={'method':'Use maximum |u|+c across all saved cells and times, multiply by final time; compare with left edge of final shock-aligned window. Saved-output estimate, not a continuous-time proof. Frozen sound speed from the same LiDryer thermo.','cases':records}
(b/'boundary_reach.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
