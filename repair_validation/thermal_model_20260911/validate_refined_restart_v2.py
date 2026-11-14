from pathlib import Path
import sys,json,numpy as np
r=Path('/home/cj/my-pele');sys.path.insert(0,str(r/'tools'))
import amrex_reader
from read_native_spray import read_native_spray
b=r/'repair_validation/thermal_model_20260911';s=Path('/dev/shm/my_pele_thermal_model_20260911')
src=s/'native_smoke_v1/plt15119';dst=s/'fine_smoke_v1/plt15119'
left=amrex_reader.read_plotfile(str(src));right=amrex_reader.read_plotfile(str(dst));assert left['time']==right['time']
assert np.allclose(np.array(left['dx'])/2,right['dx'],rtol=0,atol=1e-15)
gas={};derived={}
for k,v in left['fields'].items():
 if not (k in ['density','rho_E','Temp','pressure','x_velocity','y_velocity','z_velocity','heatRelease'] or k.startswith('rho_') or k.startswith('Y(')):
  derived[k]={'source_sum':float(np.sum(v)),'refined_sum':float(np.sum(right['fields'][k]))};continue
 q=right['fields'][k];assert q.shape==(v.shape[0]*2,v.shape[1]*2)
 error=max(float(np.max(abs(q[j::2,i::2]-v))) for i in range(2) for j in range(2))
 gas[k]={'maximum_absolute_difference':error,'maximum_scaled_difference':error/max(float(np.max(abs(v))),1e-30)}
lp=read_native_spray(src);rp=read_native_spray(dst);li=np.lexsort(lp['identity_words'].T);ri=np.lexsort(rp['identity_words'].T)
assert np.array_equal(lp['identity_words'][li],rp['identity_words'][ri])
particles={k:float(np.max(abs(v[li]-rp['fields'][k][ri]))) for k,v in lp['fields'].items()}
assert derived['num_parcels']['source_sum']==derived['num_parcels']['refined_sum']==lp['count']
result={'time_s':left['time'],'particle_counts':[lp['count'],rp['count']],'identity_words_equal':True,'gas':gas,'particle_max_absolute_errors':particles,'mesh_dependent_particle_deposition':derived,'passed':bool(all(v['maximum_scaled_difference']<1e-12 for v in gas.values()) and max(particles.values())==0),'scope':'Every gas child cell compared with its parent; all evolved liquid states and identity words checked. Cell-local particle diameters and parcel counts are redeposited on the new mesh, and cannot equal parent-cell values. Total deposited parcel count is conserved.'}
(b/'fine_restart_acceptance_v2.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['passed']
