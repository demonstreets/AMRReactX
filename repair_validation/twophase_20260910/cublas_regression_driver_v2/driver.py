import json,pathlib,subprocess,os
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='1',LD_LIBRARY_PATH='/home/cj/local/cuda-12.6/lib64:'+env.get('LD_LIBRARY_PATH',''))
for p in json.loads(pathlib.Path('plans.json').read_text()):
 d=pathlib.Path(p['cwd']);print('START',d,flush=True)
 with (d/'run.log').open('w') as log: rc=subprocess.call(p['command'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT)
 (d/'exit_code').write_text(str(rc)+'\n');print('END',d,rc,flush=True)
 if rc: raise SystemExit(rc)
