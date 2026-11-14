import subprocess,json,time,os
from pathlib import Path
d=Path(__file__).resolve().parent
case=json.loads((d/'case.json').read_text());start=time.time()
with (d/'run.log').open('w') as log:
 p=subprocess.Popen(case['command'],cwd=d,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1'))
 (d/'solver_pid').write_text(str(p.pid));code=p.wait()
(d/'exit_code').write_text(str(code));(d/'timing.json').write_text(json.dumps({'wall_seconds':time.time()-start,'exit_code':code}))
