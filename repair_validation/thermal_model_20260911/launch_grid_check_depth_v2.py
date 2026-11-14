from pathlib import Path
import argparse, os, json, re, hashlib, subprocess
p=argparse.ArgumentParser();p.add_argument('mode',choices=['roundtrip','fine_smoke','fine_main']);a=p.parse_args()
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';old=r/'repair_validation/thermal_20260911/replay_cfl20_v1';scratch=Path('/dev/shm/my_pele_thermal_model_20260911')
binary=r/'examples/academic/spray_detonation/spatial_wd6_thermal_v12d.gnu.MPI.CUDA.ex'
if a.mode=='roundtrip': jobs=[('native_smoke_v1',old/'chk15119',1,'0'),('roundtrip_smoke_v1',scratch/'checkpoint_roundtrip_v1',1,'1')]
else: jobs=[(a.mode+'_depth_v2',scratch/'checkpoint_refined_depth_v2',2,'0,1')]
for name,checkpoint,ratio,devices in jobs:
 d=b/name;d.mkdir(exist_ok=False);out=scratch/name;out.mkdir(exist_ok=False)
 for f in ['profile_SI.txt','droplets.dat']:(d/f).symlink_to((old/f).resolve())
 text=(old/'inputs').read_text()
 updates={'amr.restart':str(checkpoint),'amr.n_cell':f'{2800*ratio} {800*ratio}','amr.regrid_on_restart':'1','amr.max_grid_size':'400 400','max_step':str(100000 if a.mode=='fine_main' else 15129 if ratio==1 else 15120),'stop_time':'50e-6','amr.checkpoint_files_output':'0','amr.plot_file':str(out/'plt'),'amr.plotfile_on_restart':'1','amr.plot_per':'5e-7','pelec.thermal_diagnostic_probe':f'{2444*ratio} {ratio}'}
 for k,v in updates.items():
  text,n=re.subn(r'^'+re.escape(k)+r'\s*=.*$',k+' = '+v,text,flags=re.M)
  if n==0:text+='\n'+k+' = '+v+'\n'
  assert n<=1,k
 (d/'inputs').write_text(text)
 cmd=['mpirun','-np',str(ratio),str(binary),'inputs']
 manifest={'command':cmd,'restart':str(checkpoint),'ratio':ratio,'gpu_devices':devices,'output':str(out),'input_sha256':hashlib.sha256(text.encode()).hexdigest(),'executable_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'scope':'Identical parcel identities and droplet intensive states; weights halved to preserve liquid loading per unit depth; conservative piecewise-constant gas-state refinement from 48 us; no prior fine-grid trajectory.'}
 (d/'case.json').write_text(json.dumps(manifest,indent=2))
 env=dict(os.environ,OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES=devices)
 env['LD_LIBRARY_PATH']='/home/cj/local/cuda-12.6/targets/x86_64-linux/lib:'+str(r/'repair_validation/twophase_20260910/sundials_clean32_cuda_v2/install/lib')+':'+env.get('LD_LIBRARY_PATH','')
 code='import subprocess,json;from pathlib import Path;d=Path('+repr(str(d))+');p=subprocess.run(json.loads((d/"case.json").read_text())["command"],cwd=d);(d/"exit_code").write_text(str(p.returncode)+"\\n")'
 proc=subprocess.Popen(['python3','-c',code],env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
 (d/'launcher.json').write_text(json.dumps({'pid':proc.pid}));print(name,proc.pid)
