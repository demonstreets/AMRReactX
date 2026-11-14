import pathlib,subprocess,shlex,json,math
b=pathlib.Path('/home/cj/my-pele/repair_validation/twophase_20260910');d=b/'gpu_link_minimize_v1'
xs=[x for x in shlex.split((b/'gpu_link_diagnostic_v1/nvlink.opt').read_text()) if x.endswith('.o')]
def fails(ys):
 q=subprocess.run(['/home/cj/local/cuda-12.6/bin/nvlink','-arch','sm_60',*ys,'-o',str(d/'test.cubin')],capture_output=True,timeout=60)
 with (d/'trials.jsonl').open('a') as f: f.write(json.dumps({'objects':ys,'rc':q.returncode})+'\n')
 return q.returncode==-8
n=2
while len(xs)>=2:
 size=math.ceil(len(xs)/n);changed=False
 for i in range(0,len(xs),size):
  ys=xs[:i]+xs[i+size:]
  if ys and fails(ys):
   xs=ys;n=max(n-1,2);changed=True;break
 if not changed:
  if n>=len(xs):break
  n=min(len(xs),n*2)
 (d/'minimal.json').write_text(json.dumps(xs,indent=2))
 print('remaining',len(xs),flush=True)
print(xs)
