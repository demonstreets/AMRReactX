from pathlib import Path
import json,shutil,sys,hashlib,numpy as np
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';s=Path('/dev/shm/my_pele_thermal_model_20260911');sys.path.insert(0,str(r/'tools'))
from read_native_spray import read_native_spray
src=s/'checkpoint_refined_v1';dst=s/'checkpoint_refined_depth_v2';assert not dst.exists();shutil.copytree(src,dst)
root=dst/'particles';lines=iter((root/'Header').read_text().splitlines());assert next(lines)=='Version_Two_Dot_One_double'
dim=int(next(lines));nr=int(next(lines));names=[next(lines) for _ in range(nr)];ni=int(next(lines));ints=[next(lines) for _ in range(ni)];assert int(next(lines))==1
count=int(next(lines));nextid=int(next(lines));finest=int(next(lines));assert finest==0 and dim==2
ngrid=[int(next(lines)) for _ in range(finest+1)];factor=.5;changed=[]
for lev,nboxes in enumerate(ngrid):
 for _ in range(nboxes):
  fileno,n,offset=map(int,next(lines).split())
  if n==0:continue
  p=root/f'Level_{lev}'/f'DATA_{fileno:05d}';values=np.memmap(p,mode='r+',dtype='<f8',offset=offset+n*(2+ni)*4,shape=(n,dim+nr))
  for name in ['number_density','num_dens0']:values[:,dim+names.index(name)]*=factor
  values.flush();del values;changed.append({'file':str(p),'particles':n,'offset':offset})
left=read_native_spray(src);right=read_native_spray(dst);assert np.array_equal(left['identity_words'],right['identity_words'])
errors={}
for k,v in left['fields'].items():
 expected=v*factor if k in ['number_density','num_dens0'] else v
 errors[k]=float(np.max(abs(expected-right['fields'][k])));assert errors[k]==0
audit={'source':str(src),'destination':str(dst),'coarse_depth_cm':.005,'fine_depth_cm':.0025,'weight_factor':factor,'count':count,'scaled_components':['number_density','num_dens0'],'expected_state_max_errors':errors,'unit_depth_weight_error':float(np.max(abs(left['fields']['number_density']/.005-right['fields']['number_density']/.0025))),'identity_words_unchanged':True,'physical_interpretation':'The library enforces Lz=dx. Halving parcel represented droplet counts preserves liquid number, mass, momentum and energy per unit out-of-plane depth. Physical droplet diameter, velocity, temperature and position are unchanged.','supersedes':'The unchanged-depth statement in checkpoint_refined_v1_audit.json was incorrect. fine_main_v1 is invalidated and terminated; do not use as a grid-only comparison.'}
assert audit['unit_depth_weight_error']==0
(b/'checkpoint_refined_depth_v2_audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
