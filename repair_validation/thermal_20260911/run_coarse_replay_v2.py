"""Record the preserved coarse trajectory after the short controls release GPU 0."""
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
old = b.parent/'twophase_20260910'
source = old/'wd6_stoich_wet_2d_1400x400_continuation_v1'
checkpoint = source/'chk06107'
binary = r/'examples/academic/spray_detonation/spatial_wd6_thermal_v12d.gnu.MPI.CUDA.ex'
status_file = b/'coarse_replay_queue_v2.status.json'
assert not status_file.exists()
status_file.write_text(json.dumps({'state': 'waiting_for_short_controls'}))
assert int((source/'exit_code').read_text().strip()) == 0
checkpoint_time = float((checkpoint/'Header').read_text().splitlines()[2])
assert 40e-6 <= checkpoint_time < 40.01e-6
while not (b/'chemistry10_from48_v1/exit_code').exists():
    time.sleep(10)
assert int((b/'chemistry10_from48_v1/exit_code').read_text().strip()) == 0
assert shutil.disk_usage(b).free > 3.5e9
d = b/'replay_coarse_cfl20_v1'
d.mkdir(exist_ok=False)
for name in ['profile_SI.txt', 'droplets.dat']:
    (d/name).symlink_to((source/name).resolve())
text = (source/'inputs').read_text()
updates = {'amr.restart': str(checkpoint), 'amr.checkpoint_files_output': '0',
           'amr.plot_per': '2e-6', 'prob.record_wave_history': '0'}
for key, value in updates.items():
    text, count = re.subn(r'^'+re.escape(key)+r'\s*=.*$', key+' = '+value, text, flags=re.M)
    assert count == 1, (key, count)
text = re.sub(r'^prob.wave_history_interval\s*=.*\n', '', text, flags=re.M)
assert 'amr.regrid_on_restart' not in text
text += '\namr.regrid_on_restart = 1\npelec.thermal_diagnostics = 1\n'
text += 'pelec.thermal_diagnostic_interval_steps = 1\npelec.thermal_diagnostic_upper_K = 5000\n'
text += 'pelec.thermal_diagnostic_wall_band_cm = 0.05\npelec.thermal_diagnostic_probe = 1222 0\n'
(d/'inputs').write_text(text)
command = ['mpirun', '-np', '1', str(binary), 'inputs']
binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
manifest = json.loads((source/'case.json').read_text())
manifest.update(command=command, binary=str(binary), binary_sha256=binary_hash,
                executable_sha256=binary_hash, input_sha256=hashlib.sha256(text.encode()).hexdigest(),
                restart_from=str(checkpoint), previous_run=str(source), restart_time_s=checkpoint_time,
                gpu_devices=[0], device=0, ranks=1, cfl=.2, diagnostics=True,
                output_interval_s=2e-6, history_output_interval_s=None,
                history_scope='Full operator-stage thermal records over the coarse 40-to-50-us replay.',
                test_mode='coarse_replay', requested_time_s=50e-6,
                purpose='Mesh and parcel-resolution sensitivity using the separately evolved coarse checkpoint; no fine-to-coarse state remapping.')
(d/'case.json').write_text(json.dumps(manifest, indent=2))
env = dict(os.environ, OMP_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='0')
env['LD_LIBRARY_PATH'] = '/home/cj/local/cuda-12.6/targets/x86_64-linux/lib:'+str(
    old/'sundials_clean32_cuda_v2/install/lib')+':'+env.get('LD_LIBRARY_PATH', '')
status_file.write_text(json.dumps({'state': 'running', 'case': d.name}))
with (d/'run.log').open('w') as log:
    process = subprocess.Popen(command, cwd=d, env=env, stdout=log, stderr=subprocess.STDOUT)
    (d/'launcher.json').write_text(json.dumps({'pid': process.pid, 'cuda_visible_devices': '0'}))
    code = process.wait()
(d/'exit_code').write_text(str(code)+'\n')
status_file.write_text(json.dumps({'state': 'complete' if code == 0 else 'failed', 'exit_code': code}))
raise SystemExit(code)
