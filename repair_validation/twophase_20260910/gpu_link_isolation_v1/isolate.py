import pathlib,subprocess,json,shlex
b=pathlib.Path('/home/cj/my-pele/repair_validation/twophase_20260910');d=b/'gpu_link_isolation_v1'
a=shlex.split((b/'gpu_link_diagnostic_v1/nvlink.opt').read_text())
objs=[v for v in a if v.endswith('.o')]
r=[]
for n,p in enumerate(objs):
 q=subprocess.run(['/home/cj/local/cuda-12.6/bin/nvlink','-arch','sm_60',p,'-o',str(d/'test.cubin')],capture_output=True,text=True)
 r.append({'object':p,'returncode':q.returncode,'stderr':q.stderr[-300:]})
 (d/'results.json').write_text(json.dumps(r,indent=2))
print('objects',len(r),'fpe',[x['object'] for x in r if x['returncode']==-8])
