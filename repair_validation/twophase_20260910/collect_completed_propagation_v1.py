"""Finite postprocessing queue for the already launched validation campaign."""
from pathlib import Path
import json
import subprocess
import time

root = Path('/home/cj/my-pele')
base = root/'repair_validation/twophase_20260910'
jobs = [
    ('wet_coarse', 'wd6_stoich_wet_2d_1400x400_continuation_v1',
     ['wd6_cell_wet_2d_1400x400_cfl20_tol4_gpu_v2']),
    ('dry_fine', 'wd6_stoich_dry_2d_2800x800_continuation_v1',
     ['wd6_cell_dry_2d_2800x800_cfl20_tol4_gpu_v2']),
    ('wet_fine', 'wd6_stoich_wet_2d_2800x800_continuation_v1',
     ['wd6_cell_wet_2d_2800x800_cfl20_tol4_gpu_v2']),
    ('native88_dry_tol6', 'native88_dry_1d_600_tol6_control_v1', []),
    ('native88_wet', 'detonation_wet_1d_600_tol6_continuation_v3', [
        'detonation_wet_1d_600_cublas_cfl10_v1',
        'detonation_wet_1d_600_cpu_continuation_v1',
        'detonation_wet_1d_600_cpu24_continuation_v2']),
]
state = {}
status_file = base/'completed_propagation_queue_v1.json'
if status_file.exists():
    raise RuntimeError('This queue already has an execution record')

def save():
    status_file.write_text(json.dumps(state, indent=2))

while len(state) < len(jobs):
    for key, name, previous in jobs:
        if key in state:
            continue
        run = base/name
        marker = run/'exit_code'
        if not marker.is_file():
            continue
        exit_code = int(marker.read_text())
        state[key] = {'run': str(run), 'solver_exit': exit_code}
        if exit_code != 0:
            state[key]['status'] = 'solver did not complete successfully'
            save()
            continue
        out = base/(key+'_completed_analysis_v3')
        command = ['python3', str(root/'tools/analyze_spray_detonation.py'),
                   str(run), str(out)]
        for old in previous:
            command += ['--previous-run', str(base/old)]
        state[key].update(status='analyzing', output=str(out), command=command)
        save()
        with (base/(key+'_completed_analysis_v3.log')).open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        state[key]['analysis_exit'] = result.returncode
        state[key]['status'] = 'analysis finished' if result.returncode == 0 else 'analysis failed'
        if result.returncode == 0 and not key.startswith('native88'):
            plot = sorted(p.name for p in run.glob('plt*') if (p/'Header').is_file())[-1]
            reaction_out = base/(key+'_completed_reaction_v3')
            command = ['python3', str(root/'tools/analyze_wd6_reaction_sequence.py'),
                       str(run), plot, str(reaction_out)]
            with (base/(key+'_completed_reaction_v3.log')).open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            state[key].update(reaction_exit=result.returncode, reaction_output=str(reaction_out))
        save()
    if len(state) < len(jobs):
        time.sleep(30)
print(json.dumps(state), flush=True)
