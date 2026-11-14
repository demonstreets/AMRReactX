import pathlib,json,shutil,subprocess,shlex,hashlib,os
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910'
ref=b/'reference_znd_v1';meta=json.loads((ref/'metadata.json').read_text())
exe=r/'examples/academic/spray_detonation/spatial_clean32_202609102d.gnu.MPI.ex'
for nx,np in [(300,4),(600,8)]:
    d=b/f'detonation_dry_1d_{nx}_v2';d.mkdir(exist_ok=False)
    shutil.copy(ref/'profile_SI.txt',d/'profile_SI.txt')
    text=f'''# Finite-rate n-heptane/air freely evolving ZND wave; CGS.
max_step = 4000
stop_time = 4.e-5
geometry.coord_sys = 0
geometry.prob_lo = 0 0
geometry.prob_hi = 12 {48/nx:.16g}
geometry.is_periodic = 0 1
amr.n_cell = {nx} 4
amr.max_level = 0
amr.blocking_factor = 4
amr.max_grid_size = 32 4
pelec.lo_bc = FOExtrap Interior
pelec.hi_bc = FOExtrap Interior
pelec.do_hydro = 1
pelec.do_react = 1
pelec.do_spray_particles = 0
pelec.diffuse_vel = 0
pelec.diffuse_temp = 0
pelec.diffuse_spec = 0
pelec.chem_integrator = ReactorCvode
cvode.solve_type = denseAJ_direct
ode.rtol = 1.e-8
ode.atol = 1.e-18
pelec.allow_negative_energy = 1
pelec.cfl = 0.3
pelec.init_shrink = 0.2
pelec.change_max = 1.1
pelec.dt_cutoff = 1.e-15
pelec.v = 0
amr.v = 1
amr.checkpoint_files_output = 0
amr.plot_per = 1.e-6
amr.plot_vars = density Temp rho_E rho_nc7h16 rho_o2 rho_h2o rho_co2 heatRelease
amr.derive_plot_vars = pressure x_velocity y_velocity
pelec.plot_massfrac = 1
prob.profile = profile_SI.txt
prob.front = 2
prob.perturbation = 0
prob.p0 = 506625
prob.T0 = 300
prob.upstream_Y = {' '.join(format(x,'.17g') for x in meta['upstream']['Y'])}
amrex.abort_on_unused_inputs = 1
'''
    (d/'inputs').write_text(text)
    cmd=['mpirun','-np',str(np),str(exe),'inputs']
    (d/'command.json').write_text(json.dumps({'command':cmd,'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'initialization_reference':str(ref)},indent=2))
    env=os.environ.copy();env['OMP_NUM_THREADS']='1'
    p=subprocess.Popen(['bash','-c',shlex.join(cmd)+'; rc=$?; echo $rc > exit_code; exit $rc'],cwd=d,env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
    print(json.dumps({'run':str(d),'pid':p.pid,'ranks':np}))
