"""Run the revised tenfold-tighter full-field control in a new directory."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

r = Path('/home/cj/my-pele')
b = r/'repair_validation/thermal_20260911'
source = b/'replay_cfl20_v1'
assert (b/'tight_chemistry_from48_v1/termination_record.json').is_file()
while not (b/'short_controls_queue_v1.exit_code').exists():
    time.sleep(2)
assert int((b/'short_controls_queue_v1.exit_code').read_text().strip()) != 0
assert shutil.disk_usage(b).free > 3.5e9
checkpoints = [p for p in source.glob('chk*') if (p/'Header').is_file()
               and 48e-6 <= float((p/'Header').read_text().splitlines()[2]) < 48.01e-6]
assert len(checkpoints) == 1
checkpoint = checkpoints[0]
binary = r/'examples/academic/spray_detonation/spatial_wd6_thermal_v12d.gnu.MPI.CUDA.ex'
d = b/'chemistry10_from48_v1'
d.mkdir(exist_ok=False)
for name in ['profile_SI.txt', 'droplets.dat']:
    (d/name).symlink_to((source/name).resolve())
text = (source/'inputs').read_text()
updates = {'amr.restart': str(checkpoint), 'amr.checkpoint_files_output': '0',
           'amr.plot_per': '2e-6', 'pelec.cell_chemistry_rtol': '1e-5',
           'pelec.cell_chemistry_atol_y': '1e-14'}
for key, value in updates.items():
    text, count = re.subn(r'^'+re.escape(key)+r'\s*=.*$', key+' = '+value, text, flags=re.M)
    assert count == 1, (key, count)
(d/'inputs').write_text(text)
manifest = json.loads((source/'case.json').read_text())
binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
manifest.update(command=['mpirun', '-np', '1', str(binary), 'inputs'],
                binary=str(binary), binary_sha256=binary_hash, executable_sha256=binary_hash,
                input_sha256=hashlib.sha256(text.encode()).hexdigest(),
                previous_run=str(source), restart_from=str(checkpoint),
                output_interval_s=2e-6, history_output_interval_s=None,
                cell_chemistry_rtol=1e-5, cell_chemistry_atol_y=1e-14,
                parameter_changes_from_baseline=updates, test_mode='short_control',
                purpose='Tenfold tighter full-domain chemistry tolerance, supplemented by stricter local-state verification; replaces intentionally interrupted 100x full-domain trial.')
(d/'case.json').write_text(json.dumps(manifest, indent=2))
env = dict(os.environ, OMP_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='0')
env['LD_LIBRARY_PATH'] = '/home/cj/local/cuda-12.6/targets/x86_64-linux/lib:'+str(
    b.parent/'twophase_20260910/sundials_clean32_cuda_v2/install/lib')+':'+env.get('LD_LIBRARY_PATH', '')
with (d/'run.log').open('w') as log:
    process = subprocess.Popen(manifest['command'], cwd=d, env=env, stdout=log, stderr=subprocess.STDOUT)
    (d/'launcher.json').write_text(json.dumps({'pid': process.pid, 'cuda_visible_devices': '0'}))
    code = process.wait()
(d/'exit_code').write_text(str(code)+'\n')
raise SystemExit(code)
