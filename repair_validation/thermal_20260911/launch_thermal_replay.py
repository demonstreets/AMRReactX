"""Launch isolated, bounded replays from the preserved 40 microsecond state."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess

p=argparse.ArgumentParser()
p.add_argument('mode',choices=['smoke','main'])
a=p.parse_args()
r=Path('/home/cj/my-pele')
old=r/'repair_validation/twophase_20260910'
b=r/'repair_validation/thermal_20260911'
source=old/'wd6_stoich_wet_2d_2800x800_two_gpu_continuation_v2'
checkpoint=source/'chk12551'
assert float((checkpoint/'Header').read_text().splitlines()[2])<40.01e-6
source_manifest=json.loads((source/'case.json').read_text())
original_binary=Path(source_manifest['command'][-2])
diagnostic_binary=r/'examples/academic/spray_detonation/spatial_wd6_thermal_v12d.gnu.MPI.CUDA.ex'
assert original_binary.is_file() and diagnostic_binary.is_file()
assert int((b/'build_diagnostics_gpu_v1/exit_code').read_text())==0
if a.mode=='main':
    assert json.loads((b/'diagnostic_observation_validation_v1.json').read_text())['passed']
    jobs=[('replay_cfl20_v1',diagnostic_binary,0,.2,True),('replay_cfl10_v1',diagnostic_binary,1,.1,True)]
else:
    jobs=[('observation_old_binary_v1',original_binary,0,.2,False),('observation_new_binary_v1',diagnostic_binary,1,.2,True)]

for name,binary,device,cfl,diagnostics in jobs:
    d=b/name;d.mkdir(exist_ok=False)
    for filename in ['profile_SI.txt','droplets.dat']:
        (d/filename).symlink_to(source/filename)
    text=(source/'inputs').read_text()
    updates={'amr.restart':str(checkpoint),'pelec.cfl':str(cfl),'amr.regrid_on_restart':'1',
             'amr.max_grid_size':'400 400','prob.record_wave_history':'0',
             'amr.checkpoint_files_output':'0' if a.mode=='smoke' else '1',
             'amr.check_per':'2e-6','amr.plot_per':'2e-6' if a.mode=='smoke' else '5e-7',
             'max_step':'12561' if a.mode=='smoke' else '100000'}
    for key,value in updates.items():
        text,count=re.subn(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+value,text,flags=re.M)
        assert count==1,(key,count)
    text=re.sub(r'^prob.wave_history_interval\s*=.*\n','',text,flags=re.M)
    if diagnostics:
        text+='\npelec.thermal_diagnostics = 1\npelec.thermal_diagnostic_interval_steps = 1\n'
        text+='pelec.thermal_diagnostic_upper_K = 5000\npelec.thermal_diagnostic_wall_band_cm = 0.05\n'
        text+='pelec.thermal_diagnostic_probe = 2444 1\n'
    (d/'inputs').write_text(text)
    command=['mpirun','-np','1',str(binary),'inputs']
    manifest=dict(source_manifest)
    manifest.update(command=command,restart_from=str(checkpoint),input_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),gpu_devices=[device],ranks=1,
                    device=device,cfl=cfl,diagnostics=diagnostics,output_interval_s=2e-6 if a.mode=='smoke' else 5e-7,
                    test_mode=a.mode,requested_time_s=50e-6,requested_max_step=12561 if a.mode=='smoke' else 100000,
                    purpose='Identical-state observation check' if a.mode=='smoke' else '40-to-50 microsecond time-step sensitivity and thermal-stage diagnostics')
    (d/'case.json').write_text(json.dumps(manifest,indent=2))
    env=dict(os.environ,OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES=str(device))
    env['LD_LIBRARY_PATH']='/home/cj/local/cuda-12.6/targets/x86_64-linux/lib:'+str(old/'sundials_clean32_cuda_v2/install/lib')+':'+env.get('LD_LIBRARY_PATH','')
    code='import subprocess,json;from pathlib import Path;d=Path('+repr(str(d))+');p=subprocess.run(json.loads((d/"case.json").read_text())["command"],cwd=d);(d/"exit_code").write_text(str(p.returncode)+"\\n")'
    proc=subprocess.Popen(['python3','-c',code],env=env,stdout=(d/'run.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
    (d/'launcher.json').write_text(json.dumps({'pid':proc.pid,'mode':a.mode,'cuda_visible_devices':str(device)}))
    print(json.dumps({'run':str(d),'pid':proc.pid,'device':device,'mode':a.mode}),flush=True)
