import pathlib, json, shutil, subprocess, shlex, os, hashlib, argparse, re
import cantera as ct
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910'
p=argparse.ArgumentParser()
p.add_argument('name');p.add_argument('--nx',type=int,default=240);p.add_argument('--ny',type=int,default=80)
p.add_argument('--lx',type=float,default=12.);p.add_argument('--ly',type=float,default=4.)
p.add_argument('--time',type=float,default=4.e-5);p.add_argument('--ranks',type=int,default=16)
p.add_argument('--gpu',action='store_true');p.add_argument('--dry',action='store_true')
p.add_argument('--multimode',action='store_true');p.add_argument('--prepare-only',action='store_true')
p.add_argument('--cfl',type=float,default=.1);p.add_argument('--perturbation',type=float,default=.04)
args=p.parse_args()
if '/' in args.name or '\\' in args.name or args.name in ['.','..']:raise ValueError('simple case name required')
dx=args.lx/args.nx;dy=args.ly/args.ny
if abs(dx-dy)>1e-12:raise ValueError('square cells required for the 2D spray effective-depth convention')
exe=r/('examples/academic/spray_detonation/spatial_gpu32_202609102d.gnu.MPI.CUDA.ex' if args.gpu else
       'examples/academic/spray_detonation/spatial_diagnostic_202609102d.gnu.MPI.ex')
if not exe.exists():raise FileNotFoundError(exe)
meta=json.loads((b/'reference_znd_v1/metadata.json').read_text())
d=b/args.name;d.mkdir(exist_ok=False)
shutil.copy(b/'reference_znd_v1/profile_SI.txt',d/'profile_SI.txt')
text=(b/'detonation_dry_1d_300_v2/inputs').read_text()
def replace(key,value):
    global text
    text,n=re.subn(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+str(value),text,flags=re.M)
    if n!=1:raise ValueError((key,n))
replace('max_step',20000);replace('stop_time',format(args.time,'.17g'))
replace('geometry.prob_hi',f'{args.lx} {args.ly}');replace('amr.n_cell',f'{args.nx} {args.ny}')
replace('amr.max_grid_size','128 32' if args.gpu else '32 16')
replace('pelec.cfl',args.cfl);replace('pelec.do_spray_particles',int(not args.dry))
replace('amr.checkpoint_files_output',1);text+='amr.check_per = 1.e-5\n'
replace('amr.plot_per','5.e-7');replace('prob.perturbation',args.perturbation)
if args.multimode:text+='prob.perturbation_mode = 2\n'
if args.gpu:
    replace('cvode.solve_type','sparse_direct')
    text+='amrex.the_arena_init_size = 268435456\n'
gas=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml'))
gas.TPY=300,50662.5,meta['upstream']['Y'];rhog=gas.density*.001
liquid_mass_density=rhog*gas.Y[gas.species_index('nc7h16')]*(.4/.6)
particle_rows=[];rho_l=.6814;diam=.001
single_mass=rho_l*3.14159265358979323846/6*diam**3
represented_number=liquid_mass_density*dx*dy*dx/single_mass
if not args.dry:
    base=(b/'spray_budget_wet_inert_v4/inputs').read_text()
    text+='\n'+'\n'.join(l for l in base.splitlines() if l.startswith('particles.'))+'\n'
    # Seed liquid only in undisturbed gas, beyond the largest initial front displacement.
    for j in range(args.ny):
        for i in range(args.nx):
            x=(i+.5)*dx;y=(j+.5)*dy
            if x<=2.+abs(args.perturbation):continue
            row=[x,y,0.,0.,300.,diam,1.,represented_number,represented_number,0.,0.,0.]
            particle_rows.append(' '.join(format(v,'.17g') for v in row))
    (d/'droplets.dat').write_text(str(len(particle_rows))+'\n'+'\n'.join(particle_rows)+'\n')
(d/'inputs').write_text(text)
cmd=['mpirun','-np',str(args.ranks),str(exe),'inputs']
env=os.environ.copy();env['OMP_NUM_THREADS']='1'
if args.gpu:
    env['LD_LIBRARY_PATH']='/home/cj/local/cuda-12.6/lib64:'+env.get('LD_LIBRARY_PATH','')
    if args.ranks>1:
        binding=d/'bind_rank.sh'
        binding.write_text('#!/bin/bash\nexport CUDA_VISIBLE_DEVICES=${OMPI_COMM_WORLD_LOCAL_RANK}\nexec "$@"\n')
        cmd=['mpirun','-np',str(args.ranks),'bash',str(binding),str(exe),'inputs']
    else:env['CUDA_VISIBLE_DEVICES']='0'
(d/'command.json').write_text(json.dumps({'command':cmd,'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
    'gas_phi':.6,'liquid_phi':0 if args.dry else .4,'liquid_mass_density_g_cm3':0 if args.dry else liquid_mass_density,
    'parcel_count':len(particle_rows),'real_droplets_per_parcel':represented_number,
    'effective_depth_cm':dx,'diameter_cm':diam,'reference':str(b/'reference_znd_v1'),
    'initialization':'finite-rate ZND gas wave plus cold liquid in undisturbed gas; no subsequent imposed front speed'},indent=2))
if not args.prepare_only:
    q=subprocess.Popen(['bash','-c',shlex.join(cmd)+'; rc=$?; echo $rc > exit_code; exit $rc'],cwd=d,env=env,
                       stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
    print(json.dumps({'run':str(d),'pid':q.pid,'ranks':args.ranks,'parcels':len(particle_rows)}))
else:print(json.dumps({'prepared':str(d)}))
