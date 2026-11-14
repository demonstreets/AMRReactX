import pathlib,subprocess,json,os,shutil,hashlib,re
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';ex=r/'examples/academic/spray_detonation';binary=ex/'spatial_wd6_cell_v12d.gnu.MPI.ex'
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='1',OMP_NUM_THREADS='1',LD_LIBRARY_PATH='/home/cj/local/cuda-12.6/lib64:'+env.get('LD_LIBRARY_PATH',''))
for kind in ['dry','wet']:
 source=b/('wd6_reg10_closed_'+kind+'_gpu_v1' if kind!='propagation' else 'wd6_chemistry_batch_full_probe_v1')
 d=b/('wd6_cell_'+kind+'_cpu_v1');d.mkdir()
 for name in ['profile_SI.txt','droplets.dat']:
  if (source/name).exists():shutil.copyfile(source/name,d/name)
 s=(source/'inputs').read_text()+'\npelec.cell_chemistry_integrator = wd6_extrapolated\npelec.cell_chemistry_rtol = 1.e-6\npelec.cell_chemistry_atol_y = 1.e-13\n'
 s=re.sub(r'^cvode.solve_type\s*=.*$','cvode.solve_type = denseAJ_direct',s,flags=re.M)
 (d/'inputs').write_text(s);m=json.loads((source/'case.json').read_text());cmd=['mpirun','-np','1',str(binary),'inputs'];m.update(command=cmd,binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(s.encode()).hexdigest(),cell_chemistry_integrator='wd6_extrapolated',cell_chemistry_rtol=1.e-6,cell_chemistry_atol_y=1.e-13);(d/'case.json').write_text(json.dumps(m,indent=2))
 p=subprocess.run(cmd,cwd=d,env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT);(d/'exit_code').write_text(str(p.returncode));print(kind,p.returncode,flush=True)
 if p.returncode:break
 if kind!='propagation':
  a=['python3',str(r/'tools/validate_closed_spray.py'),str(d),'--output',str(b/(d.name+'_validation.json'))]+(['--cantera'] if kind=='dry' else [])
  v=subprocess.run(a);print('validation',v.returncode,flush=True)
 else:print('\n'.join(l for l in (d/'run.log').read_text().splitlines() if 'STRANG_TIMING' in l or 'Coarse TimeStep time' in l),flush=True)
