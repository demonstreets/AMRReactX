import pathlib,json,subprocess,shlex,os,time
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';ex=r/'examples/academic/spray_detonation'
deadline=time.monotonic()+3600
while not (b/'build_spatial_wd6_gpu_v2/exit_code').exists():
 if time.monotonic()>deadline:raise RuntimeError('prior GPU build timeout')
 time.sleep(5)
assert (b/'build_spatial_wd6_gpu_v2/exit_code').read_text().strip()=='0'
def build(kind):
 d=b/('build_spatial_wd6_'+kind+'_v3');d.mkdir()
 old=b/('build_spatial_wd6_'+kind+'_v2')
 a=json.loads((old/'command.json').read_text());a=[('EBASE=spatial_wd6_v3' if v.startswith('EBASE=') else v) for v in a]
 (d/'command.json').write_text(json.dumps(a));env=os.environ.copy();env['PATH']='/home/cj/local/cuda-12.6/bin:'+env['PATH']
 p=subprocess.run(a,cwd=ex,env=env,stdout=(d/'build.log').open('w'),stderr=subprocess.STDOUT)
 (d/'exit_code').write_text(str(p.returncode));print('BUILD',kind,p.returncode,flush=True);assert p.returncode==0
build('cpu')
for dry in [True,False]:
 d=b/('wd6_closed_'+('dry' if dry else 'wet')+'_cpu_v2')
 a=['python3',str(ex/'prepare_closed_case.py'),str(d),'--reference',str(b/'reference_wd6_v1'),'--binary',str(ex/'spatial_wd6_v32d.gnu.MPI.ex'),'--run']+(['--dry'] if dry else [])
 subprocess.run(a,check=True)
build('gpu')
print('DRIVER COMPLETE',flush=True)
