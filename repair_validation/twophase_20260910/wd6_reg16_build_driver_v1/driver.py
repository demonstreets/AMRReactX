import pathlib,json,subprocess,os,time
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';ex=r/'examples/academic/spray_detonation'
deadline=time.monotonic()+1800
def active_old_make():
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   argv=(p/'cmdline').read_bytes().split(b'\0')
   if argv and pathlib.Path(argv[0].decode()).name=='make' and b'EBASE=spatial_wd6_v3' in argv:return True
  except (OSError,UnicodeDecodeError):pass
 return False
while active_old_make():
 if time.monotonic()>deadline:raise RuntimeError('prior make timeout')
 time.sleep(5)
for backend in ['cpu','gpu']:
 d=b/('build_spatial_wd6_reg16_'+backend+'_v1');d.mkdir()
 a=json.loads((b/('build_spatial_wd6_'+backend+'_v2')/'command.json').read_text())
 a=[('EBASE=spatial_wd6_reg16_v1' if x.startswith('EBASE=') else x) for x in a]
 a+=['WD6_REGULARIZATION=1.e-16','-W',str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_wd6/mechanism.H')]
 (d/'command.json').write_text(json.dumps(a));env=os.environ.copy();env['PATH']='/home/cj/local/cuda-12.6/bin:'+env['PATH']
 q=subprocess.run(a,cwd=ex,env=env,stdout=(d/'build.log').open('w'),stderr=subprocess.STDOUT)
 (d/'exit_code').write_text(str(q.returncode));print('BUILD',backend,q.returncode,flush=True);assert q.returncode==0
 if backend=='cpu':
  for dry in [True,False]:
   args=['python3',str(ex/'prepare_closed_case.py'),str(b/('wd6_reg16_closed_'+('dry' if dry else 'wet')+'_cpu_v1')),'--reference',str(b/'reference_wd6_v1'),'--binary',str(ex/'spatial_wd6_reg16_v12d.gnu.MPI.ex'),'--wd6-regularization','1.e-16','--run']+(['--dry'] if dry else [])
   subprocess.run(args,check=True)
print('DONE',flush=True)
