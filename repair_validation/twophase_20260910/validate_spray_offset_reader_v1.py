from pathlib import Path
import sys,importlib.util,time,json,numpy as np
r=Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';sys.path.insert(0,str(r/'tools'));from read_native_spray import read_native_spray as old
spec=importlib.util.spec_from_file_location('new_reader',b/'read_native_spray_offset_v1.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=b/'wd6_stoich_wet_2d_2800x800_continuation_v1';plots=[sorted(source.glob('plt*'))[-1]]
other=b/'wd6_fine_wet_gpu_partition_comparison_v1/two_gpu_100'
if (other/'exit_code').exists() and (other/'exit_code').read_text().strip()=='0':plots.append(sorted(other.glob('plt*'))[-1])
result=[]
for p in plots:
 t=time.monotonic();left=old(p);told=time.monotonic()-t;t=time.monotonic();right=m.read_native_spray(p);tnew=time.monotonic()-t
 assert left['count']==right['count'] and np.array_equal(left['identity_words'],right['identity_words'])
 assert left['fields'].keys()==right['fields'].keys() and all(np.array_equal(left['fields'][k],right['fields'][k]) for k in left['fields'])
 result.append({'plot':str(p),'count':left['count'],'all_values_bitwise_equal':True,'old_seconds':told,'new_seconds':tnew})
(b/'spray_offset_reader_validation_v1.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
