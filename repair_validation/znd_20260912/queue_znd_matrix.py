"""Run the two remaining bounded checks after their prerequisite cases finish."""
from pathlib import Path
import argparse,json,subprocess,time
p=argparse.ArgumentParser();p.add_argument('slot',choices=['fine','time']);a=p.parse_args()
b=Path('/home/cj/my-pele/repair_validation/znd_20260912')
pre='planar_600_cfl20_v1' if a.slot=='fine' else 'planar_1200_cfl20_v1'
name='planar_2400_cfl20_v1' if a.slot=='fine' else 'planar_1200_cfl10_v1'
state=b/('queue_'+a.slot+'.json');deadline=time.monotonic()+3*3600
while not (b/pre/'exit_code').exists():
 assert time.monotonic()<deadline
 state.write_text(json.dumps({'state':'waiting','prerequisite':pre,'next':name}))
 time.sleep(30)
assert int((b/pre/'exit_code').read_text())==0
cmd=['python3',str(b/'launch_znd_case.py'),name,'--nx','2400' if a.slot=='fine' else '1200','--ny','2','--time','12.e-6','--mapping','ROUNDROBIN','--cfl','.2' if a.slot=='fine' else '.1']
subprocess.run(cmd,check=True)
state.write_text(json.dumps({'state':'launched','prerequisite':pre,'next':name,'command':cmd}))

