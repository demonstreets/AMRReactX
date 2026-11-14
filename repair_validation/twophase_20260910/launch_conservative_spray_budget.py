import pathlib,json,subprocess,shlex,shutil,hashlib,os,re
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910'
exe=r/'examples/academic/spray_detonation/spatial_clean32_202609102d.gnu.MPI.ex'
meta=json.loads((b/'reference_znd_v1/metadata.json').read_text())
for version,dt,steps in [('v4',1.e-8,20000),('v5',5.e-9,40000)]:
    for label in ['wet_inert','wet_reactive','dry_reactive']:
        old=b/('spray_budget_'+label+'_v3');d=b/('spray_budget_'+label+'_'+version);d.mkdir(exist_ok=False)
        for p in old.iterdir():
            if p.name.startswith('initspray') or p.name in ['droplets.dat','initial_budget.json','budget.json']:shutil.copy(p,d/p.name)
        shutil.copy(b/'reference_znd_v1/profile_SI.txt',d/'profile_SI.txt')
        text='\n'.join(l for l in (old/'inputs').read_text().splitlines() if not l.startswith('prob.') and not l.startswith('#'))+'\n'
        def replace(key,value):
            global text
            text=re.sub(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+str(value),text,flags=re.M)
        replace('max_step',steps);replace('pelec.fixed_dt',format(dt,'.17g'));replace('amr.plot_int',steps//20)
        replace('cvode.solve_type','denseAJ_direct');replace('ode.atol','1.e-18')
        replace('amr.derive_plot_vars','pressure x_velocity y_velocity')
        text+='''# Uniform upstream state: the profile front lies outside the domain.
prob.profile = profile_SI.txt
prob.front = -1
prob.perturbation = 0
prob.p0 = 1.e6
prob.T0 = 1400
prob.upstream_Y = '''+' '.join(format(y,'.17g') for y in meta['upstream']['Y'])+'\n'
        (d/'inputs').write_text(text)
        cmd=['mpirun','-np','1',str(exe),'inputs'];(d/'command.json').write_text(json.dumps({'command':cmd,'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'dt':dt,'end_time':steps*dt},indent=2))
        env=os.environ.copy();env['OMP_NUM_THREADS']='1'
        p=subprocess.Popen(['bash','-c',shlex.join(cmd)+'; rc=$?; echo $rc > exit_code; exit $rc'],cwd=d,env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
        print(json.dumps({'run':str(d),'pid':p.pid}))
