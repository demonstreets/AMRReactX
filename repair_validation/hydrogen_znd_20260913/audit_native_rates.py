"""Compare the compiled native LiDryer thermochemistry with Cantera on ZND states."""
from pathlib import Path
import json,subprocess
import cantera as ct,numpy as np
b=Path(__file__).resolve().parent
ref=np.loadtxt(b/'reference_v1/profile_SI.txt');ids=np.unique(np.r_[np.arange(0,801,4),np.arange(801,len(ref),40),len(ref)-1])
g=ct.Solution('/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/LiDryer/mechanism.yaml')
inputs=[];expected=[]
for i in ids:
 q=ref[i];g.TPY=q[3],q[2],q[5:];inputs.append(' '.join(map(str,np.r_[q[2],q[3],q[5:]])));expected.append(np.r_[g.cp_mass,g.int_energy_mass,g.net_production_rates])
r=subprocess.run(['/dev/shm/my_pele_hydrogen_znd_20260913/native_rates'],input='\n'.join(inputs)+'\n',capture_output=True,text=True,check=True)
actual=np.array([list(map(float,line.split())) for line in r.stdout.splitlines()]);expected=np.array(expected);diff=abs(actual-expected)
record={'sample_count':len(ids),'sample_distance_range_m':[float(ref[ids[0],0]),float(ref[ids[-1],0])],'cp_max_abs_J_kg_K':float(diff[:,0].max()),'internal_energy_max_abs_J_kg':float(diff[:,1].max()),'molar_rate_max_abs_kmol_m3_s':float(diff[:,2:].max()),'molar_rate_max_difference_over_global_peak':float(diff[:,2:].max()/abs(expected[:,2:]).max()),'molar_rate_max_row_scaled_difference':float(np.max(np.max(diff[:,2:],axis=1)/np.maximum(np.max(abs(expected[:,2:]),axis=1),1e-8))),'rate_unit_conversion':'CKWYP uses mol/cm3/s; multiply by 1000 to compare with Cantera kmol/m3/s.'}
np.savez_compressed(b/'native_rates_comparison.npz',reference_row_ids=ids,expected=expected,actual=actual)
(b/'native_rates_comparison.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
