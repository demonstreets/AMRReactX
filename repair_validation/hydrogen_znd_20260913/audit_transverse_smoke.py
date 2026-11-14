from pathlib import Path
import re,json,sys,numpy as np
b=Path('/home/cj/my-pele/repair_validation/hydrogen_znd_20260913');sys.path.insert(0,'/home/cj/my-pele/tools');import amrex_reader
qs=[]
for name in ['smoke_2400_v1','smoke_2400_ny4_v1']:
 d=b/name;assert int((d/'exit_code').read_text())==0;q=sorted(Path(json.loads((d/'case.json').read_text())['plot_root']).glob('plt*'))[-1];qs.append(amrex_reader.read_plotfile(str(q)))
q1,q2=qs;errors={k:float(np.max(abs(q1['fields'][k].mean(axis=1)-q2['fields'][k].mean(axis=1)))/max(float(np.max(abs(q1['fields'][k]))),1e-10)) for k in q1['fields']};record={'time_2rows_s':q1['time'],'time_4rows_s':q2['time'],'time_difference_s':q2['time']-q1['time'],'maximum_relative_difference':max(errors.values()),'per_field_relative_difference':errors};(b/'transverse_smoke_comparison.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))