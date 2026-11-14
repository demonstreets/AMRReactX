from pathlib import Path
import subprocess,time,json
b=Path(__file__).resolve().parent
for previous,name,cfl in [('hydrogen_2400_cfl30_v1','hydrogen_4800_cfl30_v1','.3'),('hydrogen_4800_cfl30_v1','hydrogen_4800_cfl15_v1','.15')]:
 while not (b/previous/'exit_code').exists():time.sleep(10)
 assert int((b/previous/'exit_code').read_text())==0
 subprocess.run(['python3',str(b/'launch_hydrogen_case.py'),name,'--nx','4800','--cfl',cfl],check=True)
 (b/'queue_status.json').write_text(json.dumps({'launched':name}))
