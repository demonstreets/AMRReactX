"""Prepare the uniform periodic gas/liquid conservation and chemistry test."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import cantera as ct

here=Path(__file__).resolve().parent
root=here.parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('output',type=Path)
p.add_argument('--reference',type=Path,required=True)
p.add_argument('--binary',type=Path,required=True)
p.add_argument('--dt',type=float,default=1.e-7)
p.add_argument('--end-time',type=float,default=2.e-4)
p.add_argument('--dry',action='store_true')
p.add_argument('--nonreacting',action='store_true')
p.add_argument('--droplet-u-ms',type=float,default=0.)
p.add_argument('--gpu',action='store_true')
p.add_argument('--device',type=int,default=0)
p.add_argument('--cuda-home',type=Path)
p.add_argument('--linear-solver',choices=['denseAJ_direct','sparse_direct','custom_direct'])
p.add_argument('--wd6-regularization',type=float,default=0.)
p.add_argument('--cell-chemistry-integrator',choices=['cvode','wd6_extrapolated'],default='cvode')
p.add_argument('--cell-chemistry-rtol',type=float,default=1.e-6)
p.add_argument('--cell-chemistry-atol-y',type=float,default=1.e-13)
p.add_argument('--run',action='store_true')
a=p.parse_args()
if not all(math.isfinite(v) for v in [a.dt,a.end_time,a.droplet_u_ms]) or min(a.dt,a.end_time)<=0:
    p.error('time controls must be positive and all numeric values finite')
steps=round(a.end_time/a.dt)
if steps<1 or not math.isclose(steps*a.dt,a.end_time,rel_tol=1.e-12):
    p.error('end time must be an integer multiple of dt')
solver=a.linear_solver or ('sparse_direct' if a.gpu else 'denseAJ_direct')
if (not a.gpu and solver!='denseAJ_direct') or (a.gpu and solver=='denseAJ_direct'):
    p.error('solver selection does not match CPU/CUDA backend')
reference=a.reference.resolve();binary=a.binary.resolve()
meta=json.loads((reference/'metadata.json').read_text())
mechanism=meta['mechanism']
if mechanism not in ['heptane_lu_88sk','heptane_wd6']:p.error('unsupported mechanism')
if not all(math.isfinite(v) and v>0. for v in [a.cell_chemistry_rtol,a.cell_chemistry_atol_y]):
    p.error('cell chemistry tolerances must be finite and positive')
if a.cell_chemistry_integrator=='wd6_extrapolated' and (mechanism!='heptane_wd6' or not a.wd6_regularization>0.):
    p.error('wd6_extrapolated requires heptane_wd6 and positive regularization')
gas=ct.Solution(str(root/'external/PeleC/Submodules/PelePhysics/Mechanisms'/mechanism/'mechanism.yaml'))
if meta['species_names']!=gas.species_names:
    p.error('reference species ordering differs from the compiled mechanism')
gas.TPY=1400.,1.e5,meta['upstream']['Y']
phi=gas.equivalence_ratio('nc7h16',{'o2':1.,'n2':3.76})
if not math.isclose(phi,.6,rel_tol=1.e-10):p.error('this closed reference requires gas equivalence ratio 0.6')
if a.run and not binary.is_file():p.error('binary does not exist')
text=(here/'inputs.closed').read_text()
def set_input(key,value):
    global text
    text,count=re.subn(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+str(value),text,flags=re.M)
    if count!=1:raise ValueError('expected one input entry for '+key)
set_input('max_step',steps);set_input('stop_time',format(a.end_time,'.17g'))
set_input('pelec.fixed_dt',format(a.dt,'.17g'));set_input('amr.plot_int',max(1,steps//20))
set_input('pelec.do_react',int(not a.nonreacting));set_input('pelec.do_spray_particles',int(not a.dry))
set_input('cvode.solve_type',solver)
set_input('prob.upstream_Y',' '.join(format(v,'.17g') for v in gas.Y))
if a.gpu:set_input('amrex.the_arena_init_size',67108864)
if mechanism=='heptane_wd6':
    if not math.isfinite(a.wd6_regularization) or a.wd6_regularization<0.:p.error('invalid concentration epsilon')
    text+='prob.expected_wd6_regularization = '+format(a.wd6_regularization,'.17g')+'\n'
if a.dry:text='\n'.join(l for l in text.splitlines() if not l.startswith('particles.'))+'\n'
text+='pelec.cell_chemistry_integrator = '+a.cell_chemistry_integrator+'\n'
text+='pelec.cell_chemistry_rtol = '+format(a.cell_chemistry_rtol,'.17g')+'\n'
text+='pelec.cell_chemistry_atol_y = '+format(a.cell_chemistry_atol_y,'.17g')+'\n'
dx=.025;diameter=.001;rho_liquid=.6814
loading=gas.density*.001*gas.Y[gas.species_index('nc7h16')]*.4/.6
weight=loading*dx**3/(rho_liquid*math.pi*diameter**3/6.)
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
shutil.copyfile(reference/'profile_SI.txt',out/'profile_SI.txt')
(out/'inputs').write_text(text)
if not a.dry:
    rows=[]
    for j in range(4):
        for i in range(4):
            v=[(i+.5)*dx,(j+.5)*dx,a.droplet_u_ms*100.,0.,300.,diameter,1.,weight,weight,0.,0.,0.]
            rows.append(' '.join(format(x,'.17g') for x in v))
    (out/'droplets.dat').write_text('16\n'+'\n'.join(rows)+'\n')
command=['mpirun','-np','1',str(binary),'inputs']
manifest={'command':command,'mechanism':mechanism,'species_names':gas.species_names,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest() if binary.is_file() else None,
          'input_sha256':hashlib.sha256((out/'inputs').read_bytes()).hexdigest(),
          'dt_s':a.dt,'end_time_s':a.end_time,'gas_phi':phi,'liquid_phi':0. if a.dry else .4,
          'gas_temperature_K':1400.,'pressure_Pa':1.e5,'effective_depth_cm':dx,
          'droplet_u_ms':a.droplet_u_ms,'real_droplets_per_parcel':weight if not a.dry else 0.,
          'representation':'uniform periodic native gas plus Lagrangian droplets; hydro disabled',
          'chemistry_transport_split':'strang','linear_solver':solver,
          'cell_chemistry_integrator':a.cell_chemistry_integrator,
          'cell_chemistry_rtol':a.cell_chemistry_rtol,'cell_chemistry_atol_y':a.cell_chemistry_atol_y,
          'wd6_concentration_epsilon_mol_m3':a.wd6_regularization if mechanism=='heptane_wd6' else None}
(out/'case.json').write_text(json.dumps(manifest,indent=2))
if a.run:
    env=os.environ.copy();env['OMP_NUM_THREADS']='1'
    if a.gpu:
        env['CUDA_VISIBLE_DEVICES']=str(a.device)
        if a.cuda_home:env['LD_LIBRARY_PATH']=str(a.cuda_home.resolve()/'lib64')+':'+env.get('LD_LIBRARY_PATH','')
    process=subprocess.Popen(['bash','-c',shlex.join(command)+'; rc=$?; echo $rc > exit_code; exit $rc'],
        cwd=out,env=env,stdout=(out/'run.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
    print(json.dumps({'case':str(out),'pid':process.pid}))
else:print(json.dumps({'case':str(out),'command':command,'launched':False}))
