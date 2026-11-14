from pathlib import Path
import json,time,subprocess,traceback
b=Path(__file__).resolve().parent
names=['hydrogen_2400_cfl30_v1','hydrogen_4800_cfl30_v1','hydrogen_9600_cfl30_v1','hydrogen_4800_cfl15_v1']
def state(stage,**kw):(b/'finalizer_status.json').write_text(json.dumps({'stage':stage,**kw},indent=2))
try:
 state('waiting_for_cases')
 while not all((b/n/'exit_code').exists() for n in names):time.sleep(10)
 assert all(int((b/n/'exit_code').read_text())==0 for n in names)
 for n in names:
  state('analyze',case=n);subprocess.run(['python3',str(b/'analyze_hydrogen_case.py'),n],check=True)
 for script in ['aggregate_hydrogen.py','audit_boundary_reach.py','write_hydrogen_report.py','package_hydrogen_evidence.py']:
  state('run',script=script);subprocess.run(['python3',str(b/script)],check=True)
 state('complete')
except Exception as exc:
 state('failed',error=str(exc),traceback=traceback.format_exc());raise
