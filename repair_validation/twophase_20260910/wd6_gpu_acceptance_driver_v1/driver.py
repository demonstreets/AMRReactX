import pathlib,subprocess,json,os,shlex,re,hashlib
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';ex=r/'examples/academic/spray_detonation';binary=ex/'spatial_wd6_reg10_v12d.gnu.MPI.CUDA.ex'
assert (b/'build_spatial_wd6_reg10_gpu_v1/exit_code').read_text().strip()=='0'
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='1',OMP_NUM_THREADS='1',LD_LIBRARY_PATH='/home/cj/local/cuda-12.6/lib64:'+env.get('LD_LIBRARY_PATH',''))
for kind in ['dry','wet']:
 d=b/('wd6_reg10_closed_'+kind+'_gpu_v1')
 args=['python3',str(ex/'prepare_closed_case.py'),str(d),'--reference',str(b/'reference_wd6_v1'),'--binary',str(binary),'--wd6-regularization','1.e-10','--gpu','--device','1','--cuda-home','/home/cj/local/cuda-12.6','--linear-solver','custom_direct']+(['--dry'] if kind=='dry' else [])
 subprocess.run(args,check=True)
 cmd=json.loads((d/'case.json').read_text())['command']
 p=subprocess.run(cmd,cwd=d,env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT)
 (d/'exit_code').write_text(str(p.returncode));print(kind,p.returncode,flush=True);assert p.returncode==0
 args=['python3',str(r/'tools/validate_closed_spray.py'),str(d),'--output',str(b/(d.name+'_validation.json'))]+(['--cantera'] if kind=='dry' else [])
 subprocess.run(args,check=True)
d=b/'wd6_reg10_wet_2d_1400x400_gpu_probe_v1'
args=['python3',str(ex/'prepare_case.py'),str(d),'--reference',str(b/'reference_wd6_v1'),'--binary',str(binary),'--nx','1400','--ny','400','--length-cm','14','--height-cm','4','--front-cm','4','--end-time','5.e-5','--cfl','.1','--perturbation-cm','.08','--multimode','--walls','--gpu','--devices','1','--cuda-home','/home/cj/local/cuda-12.6','--linear-solver','custom_direct','--max-grid-size','400','400','--wave-history','--output-interval','2.e-6','--history-interval','1.e-6','--wd6-regularization','1.e-10']
subprocess.run(args,check=True)
p=d/'inputs';p.write_text(re.sub(r'^max_step\s*=.*$','max_step = 5',p.read_text(),flags=re.M))
m=json.loads((d/'case.json').read_text());m.update(input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),trial='five-step memory and timestep preflight; not full propagation validation');(d/'case.json').write_text(json.dumps(m,indent=2))
p=subprocess.run(m['command'],cwd=d,env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT)
(d/'exit_code').write_text(str(p.returncode));print('PROBE',p.returncode,flush=True)
