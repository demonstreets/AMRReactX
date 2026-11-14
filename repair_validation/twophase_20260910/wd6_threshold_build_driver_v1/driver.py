import pathlib,json,subprocess,os,time
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';ex=r/'examples/academic/spray_detonation'
deadline=time.monotonic()+1800
def active_make():
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   argv=(p/'cmdline').read_bytes().split(b'\0')
   if argv and pathlib.Path(argv[0].decode()).name=='make' and pathlib.Path(os.readlink(p/'cwd'))==ex:return True
  except (OSError,UnicodeDecodeError):pass
 return False
while active_make():
 if time.monotonic()>deadline:raise RuntimeError('prior make timeout')
 time.sleep(5)
for suffix,eps in [('reg8','1.e-8'),('reg10','1.e-10')]:
 d=b/('build_spatial_wd6_'+suffix+'_cpu_v1');d.mkdir()
 args=json.loads((b/'build_spatial_wd6_cpu_v2/command.json').read_text())
 args=[('EBASE=spatial_wd6_'+suffix+'_v1' if x.startswith('EBASE=') else x) for x in args]
 args+=['WD6_REGULARIZATION='+eps,'-W',str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_wd6/mechanism.H')]
 (d/'command.json').write_text(json.dumps(args));q=subprocess.run(args,cwd=ex,stdout=(d/'build.log').open('w'),stderr=subprocess.STDOUT)
 (d/'exit_code').write_text(str(q.returncode));print('BUILD',suffix,q.returncode,flush=True);assert q.returncode==0
 for dry in [True,False]:
  args=['python3',str(ex/'prepare_closed_case.py'),str(b/('wd6_'+suffix+'_closed_'+('dry' if dry else 'wet')+'_cpu_v1')),'--reference',str(b/'reference_wd6_v1'),'--binary',str(ex/('spatial_wd6_'+suffix+'_v12d.gnu.MPI.ex')),'--wd6-regularization',eps,'--run']+(['--dry'] if dry else [])
  subprocess.run(args,check=True)
print('DONE',flush=True)
