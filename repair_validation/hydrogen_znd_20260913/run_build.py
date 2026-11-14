from pathlib import Path
import json,subprocess,time
b=Path(__file__).resolve().parent
t=time.time()
with (b/'build.log').open('w') as f: code=subprocess.call(json.loads((b/'build_command.json').read_text()),cwd=b/'build_source',stdout=f,stderr=subprocess.STDOUT)
(b/'build_exit_code').write_text(str(code))
(b/'build_timing.json').write_text(json.dumps({'seconds':time.time()-t,'exit':code}))
