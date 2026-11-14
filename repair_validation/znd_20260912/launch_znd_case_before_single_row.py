"""Bounded planar reactive-Euler verification using the existing native solver."""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('name');p.add_argument('--nx',type=int,required=True)
p.add_argument('--cfl',type=float,default=.2);p.add_argument('--time',type=float,default=20.e-6)
p.add_argument('--ranks',type=int,default=24);p.add_argument('--steps',type=int,default=100000)
p.add_argument('--rtol',type=float,default=1.e-7);p.add_argument('--atol',type=float,default=1.e-14)
p.add_argument('--reference',default='reference_near_cj_v1')
a=p.parse_args();assert re.fullmatch(r'[a-zA-Z0-9_]+',a.name)
r=Path('/home/cj/my-pele');b=r/'repair_validation/znd_20260912'
ref=b/a.reference;meta=json.loads((ref/'metadata.json').read_text())
assert json.loads((ref/'reference_audit.json').read_text())['CJ_sonic_relative_error']<1.e-4
exe=r/'examples/academic/spray_detonation/spatial_final_cleanup_v12d.gnu.MPI.ex'
d=b/a.name;d.mkdir(exist_ok=False)
scratch=Path('/dev/shm/my_pele_znd_20260912')/a.name;scratch.mkdir(parents=True,exist_ok=False)
text=(r/'repair_validation/twophase_20260910/detonation_dry_1d_600_strang_cfl30_v1/inputs').read_text()
replacements={'max_step':a.steps,'stop_time':format(a.time,'.17g'),
 'geometry.prob_hi':'12 0.08','amr.n_cell':f'{a.nx} 4','amr.max_grid_size':'16 4',
 'pelec.cfl':a.cfl,'amr.checkpoint_files_output':0,'amr.plot_per':'1.e-6',
 'prob.profile':str(ref/'profile_SI.txt'),'prob.front':4,'prob.perturbation':0,
 'amr.plot_vars':'density Temp rho_E heatRelease',
 'prob.upstream_Y':' '.join(format(v,'.17g') for v in meta['upstream']['Y'])}
for key,value in replacements.items():
 text,n=re.subn(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+str(value),text,flags=re.M);assert n==1,(key,n)
text+='\n'+f'''amr.plot_file = {scratch}/plt
pelec.sdc_iters = 1
pelec.cell_chemistry_integrator = cvode
pelec.cell_chemistry_rtol = {a.rtol:.17g}
pelec.cell_chemistry_atol_y = {a.atol:.17g}
'''
(d/'inputs').write_text(text)
cmd=['mpirun','-np',str(a.ranks),str(exe),'inputs'];env=os.environ.copy();env['OMP_NUM_THREADS']='1'
case={'command':cmd,'binary':str(exe),'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
 'reference':str(ref),'profile_sha256':hashlib.sha256((ref/'profile_SI.txt').read_bytes()).hexdigest(),
 'input_sha256':hashlib.sha256(text.encode()).hexdigest(),'nx':a.nx,'ny':4,'dx_m':.12/a.nx,
 'cfl':a.cfl,'rtol':a.rtol,'atol_y':a.atol,'stop_time_s':a.time,'plot_root':str(scratch),
 'physical_model':'Single-phase inviscid reactive Euler, heptane_lu_88sk, transverse uniform periodic strip; no droplets, diffusion or transverse perturbation.',
 'initialization':'Near-CJ finite-rate ZND at 1.00001 D_CJ; no forcing or imposed wave speed after initialization.'}
(d/'case.json').write_text(json.dumps(case,indent=2))
runner='''import subprocess,json,time,os
from pathlib import Path
d=Path(__file__).resolve().parent
case=json.loads((d/'case.json').read_text());start=time.time()
with (d/'run.log').open('w') as log:
 p=subprocess.Popen(case['command'],cwd=d,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1'))
 (d/'solver_pid').write_text(str(p.pid));code=p.wait()
(d/'exit_code').write_text(str(code));(d/'timing.json').write_text(json.dumps({'wall_seconds':time.time()-start,'exit_code':code}))
'''
(d/'run_case.py').write_text(runner)
q=subprocess.Popen(['python3',str(d/'run_case.py')],cwd=d,env=env,stdout=(d/'launcher.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
(d/'launcher.json').write_text(json.dumps({'pid':q.pid}));print(json.dumps({'case':str(d),'pid':q.pid,'nx':a.nx}))

