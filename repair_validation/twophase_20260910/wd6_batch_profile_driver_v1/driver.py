import pathlib,subprocess,json,re,hashlib,os,shutil
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';ex=r/'examples/academic/spray_detonation';binary=ex/'spatial_wd6_tiled_v12d.gnu.MPI.CUDA.ex';source=b/'wd6_reg10_wet_2d_1400x400_gpu_probe_v1'
assert (b/'build_wd6_tiled_gpu_v1/exit_code').read_text().strip()=='0'
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='1',OMP_NUM_THREADS='1',LD_LIBRARY_PATH='/home/cj/local/cuda-12.6/lib64:'+env.get('LD_LIBRARY_PATH',''))
for tag,tile in [('full',None),('16x128',[16,128]),('32x128',[32,128])]:
 d=b/('wd6_chemistry_batch_'+tag+'_probe_v1');d.mkdir()
 for name in ['profile_SI.txt','droplets.dat']:shutil.copyfile(source/name,d/name)
 s=(source/'inputs').read_text();s=re.sub(r'^max_step\s*=.*$','max_step = 3',s,flags=re.M)
 s+='pelec.fixed_dt = 5.e-9\npelec.profile_strang = 1\n'
 s=re.sub(r'^ode.verbose\s*=.*$','ode.verbose = 2',s,flags=re.M)
 if tile:s+='pelec.chemistry_tile_size = '+' '.join(map(str,tile))+'\n'
 (d/'inputs').write_text(s);m=json.loads((source/'case.json').read_text());cmd=['mpirun','-np','1',str(binary),'inputs'];m.update(command=cmd,binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(s.encode()).hexdigest(),chemistry_tile_size=tile,trial='three fixed 5 ns steps, batch partition performance and field equivalence; not full propagation validation');(d/'case.json').write_text(json.dumps(m,indent=2))
 p=subprocess.run(cmd,cwd=d,env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT);(d/'exit_code').write_text(str(p.returncode));print(tag,p.returncode,flush=True)
 print('\n'.join(l for l in (d/'run.log').read_text().splitlines() if 'STRANG_TIMING' in l or 'Coarse TimeStep time' in l),flush=True)
 if p.returncode:break
