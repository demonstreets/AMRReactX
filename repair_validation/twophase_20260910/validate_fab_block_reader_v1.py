from pathlib import Path
import sys,importlib.util,time,json,numpy as np
r=Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';sys.path.insert(0,str(r/'tools'));import amrex_reader as old
spec=importlib.util.spec_from_file_location('block_reader',b/'amrex_reader_block_v1.py');new=importlib.util.module_from_spec(spec);spec.loader.exec_module(new)
out=b/'fab_reader_validation_v1';out.mkdir(exist_ok=False);result=[]
for nz in [1,2]:
 arr=np.arange(24*nz,dtype=np.float64);header=b'FAB ((8,(64 11 52 0 1 12 0 1023)),(8,(64 11 52 0 1 12 0 1023)))((0,0,0)(2,3,1)(0,0,0)) 2\n';block=header+arr.tobytes();p=out/('multi_'+str(nz));p.write_bytes(block+block)
 for offset in [0,len(block)]:assert np.array_equal(old._read_fab_data(p,2,3,4,nz,offset),new._read_fab_data(p,2,3,4,nz,offset))
result.append({'synthetic_2D_and_3D_multi_FAB_offsets':True})
plots=[b/'native88_dry_1d_600_tol6_control_v1/plt04286',b/'wd6_stoich_wet_2d_2800x800_continuation_v1/plt07600',b/'wd6_fine_wet_gpu_partition_comparison_v1/two_gpu_100/plt07620']
for p in plots:
 t=time.monotonic();left=old.read_plotfile(str(p));told=time.monotonic()-t;t=time.monotonic();right=new.read_plotfile(str(p));tnew=time.monotonic()-t
 assert left['time']==right['time'] and np.array_equal(left['x'],right['x']) and np.array_equal(left['dx'],right['dx'])
 assert left['fields'].keys()==right['fields'].keys() and all(np.array_equal(left['fields'][k],right['fields'][k]) for k in left['fields'])
 item={'plot':str(p),'all_values_bitwise_equal':True,'old_seconds':told,'new_seconds':tnew};result.append(item);print(json.dumps(item),flush=True)
(out/'validation.json').write_text(json.dumps(result,indent=2))
