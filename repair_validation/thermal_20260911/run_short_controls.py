"""Run bounded, isolated controls after the baseline releases GPU 0.

The lower-open case changes gas and particle boundary physics. It is a
sensitivity experiment, not a repaired version of the original wall case.
The tighter-chemistry case changes only the active cell-chemistry tolerances.
"""
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
queue = b/'short_controls_queue_v1'
queue.mkdir(exist_ok=False)
(queue/'status.json').write_text(json.dumps({'state': 'waiting_for_baseline'}))
while not (source/'exit_code').exists():
    time.sleep(10)
assert int((source/'exit_code').read_text().strip()) == 0
source_manifest = json.loads((source/'case.json').read_text())
binary = Path(source_manifest['command'][-2])
assert hashlib.sha256(binary.read_bytes()).hexdigest() == source_manifest['executable_sha256']
candidates = []
for p in source.glob('chk*'):
    if (p/'Header').is_file():
        checkpoint_time = float((p/'Header').read_text().splitlines()[2])
        if 48e-6 <= checkpoint_time < 48.01e-6:
            candidates.append((p, checkpoint_time))
assert len(candidates) == 1, candidates
checkpoint, checkpoint_time = candidates[0]
original_text = (source/'inputs').read_text()
assert re.search(r'^pelec.lo_bc\s*=\s*FOExtrap SlipWall\s*$', original_text, re.M)
assert re.search(r'^pelec.cell_chemistry_rtol\s*=\s*0.0001\s*$', original_text, re.M)
jobs = [
    ('lower_open_from48_v1', {'pelec.lo_bc': 'FOExtrap FOExtrap'},
     'Lower-boundary sensitivity: gas outflow extrapolation and nonreflecting particle boundary from 48 us.'),
    ('tight_chemistry_from48_v1', {'pelec.cell_chemistry_rtol': '1e-6',
                                 'pelec.cell_chemistry_atol_y': '1e-15'},
     'Active WD6 cell chemistry tolerances tightened by 100 from the identical baseline 48-us checkpoint.')]
outcomes = []
for name, differences, purpose in jobs:
    # Budget covers initial and final full fields, CSV, and an explicit margin.
    if shutil.disk_usage(b).free < 3.5e9:
        raise RuntimeError('Insufficient free space for another bounded control; existing outputs preserved.')
    d = b/name
    d.mkdir(exist_ok=False)
    for filename in ['profile_SI.txt', 'droplets.dat']:
        (d/filename).symlink_to((source/filename).resolve())
    text = original_text
    updates = {'amr.restart': str(checkpoint), 'amr.plot_per': '2e-6',
               'amr.checkpoint_files_output': '0', **differences}
    for key, value in updates.items():
        text, count = re.subn(r'^'+re.escape(key)+r'\s*=.*$', key+' = '+value, text, flags=re.M)
        assert count == 1, (key, count)
    (d/'inputs').write_text(text)
    manifest = dict(source_manifest)
    manifest.update(restart_from=str(checkpoint), restart_time_s=checkpoint_time,
                    input_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    output_interval_s=2e-6, test_mode='short_control',
                    parameter_changes_from_baseline=updates, purpose=purpose)
    (d/'case.json').write_text(json.dumps(manifest, indent=2))
    env = dict(os.environ, OMP_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='0')
    env['LD_LIBRARY_PATH'] = '/home/cj/local/cuda-12.6/targets/x86_64-linux/lib:'+str(
        b.parent/'twophase_20260910/sundials_clean32_cuda_v2/install/lib')+':'+env.get('LD_LIBRARY_PATH', '')
    status = {'state': 'running', 'case': name, 'purpose': purpose, 'completed': outcomes}
    (queue/'status.json').write_text(json.dumps(status, indent=2))
    with (d/'run.log').open('w') as log:
        process = subprocess.Popen(manifest['command'], cwd=d, env=env,
                                   stdout=log, stderr=subprocess.STDOUT)
        (d/'launcher.json').write_text(json.dumps({'pid': process.pid, 'cuda_visible_devices': '0'}))
        code = process.wait()
    (d/'exit_code').write_text(str(code)+'\n')
    outcomes.append({'case': name, 'exit_code': code})
    assert code == 0, outcomes
(queue/'status.json').write_text(json.dumps({'state': 'complete', 'completed': outcomes}, indent=2))
