"""Analyze completed thermal controls; preserve original runs and failed trials."""
from pathlib import Path
import hashlib
import json
import subprocess
import time

b = Path('/home/cj/my-pele/repair_validation/thermal_20260911')
names = ['replay_cfl20_v1', 'replay_cfl10_v1', 'chemistry10_from48_v1',
         'lower_open_from48_v1', 'replay_coarse_cfl20_v1']
status = b/'final_analysis_status_v1.json'
while True:
    codes = {n: int((b/n/'exit_code').read_text()) if (b/n/'exit_code').exists() else None for n in names}
    status.write_text(json.dumps({'state': 'waiting', 'exit_codes': codes}, indent=2))
    assert all(x in [None, 0] for x in codes.values()), codes
    if all(x == 0 for x in codes.values()):
        break
    time.sleep(20)

def run(label, command):
    status.write_text(json.dumps({'state': 'analyzing', 'operation': label}))
    proc = subprocess.run(command, capture_output=True, text=True)
    (b/(label+'.log')).write_text(proc.stdout+proc.stderr)
    assert proc.returncode == 0, (label, proc.stderr[-2000:])

run('normalize_completed_metadata_v1', ['python3', str(b/'normalize_case_metadata.py'),
                                      *[str(b/n) for n in names]])
groups = {'numerical_controls_final_v1': names[:3],
          'boundary_control_final_v1': [names[0], names[3]],
          'mesh_control_final_v1': [names[0], names[4]]}
combined = {}
for output, group in groups.items():
    run(output, ['python3', str(b/'analyze_thermal_history.py'), *[str(b/n) for n in group],
                 '--output', str(b/output), '--plot-start-us', '48'])
    combined.update(json.loads((b/output/'summary.json').read_text()))
(b/'final_history_summary_v1.json').write_text(json.dumps(combined, indent=2))

plots = {n: sorted(p for p in (b/n).glob('plt*') if (p/'Header').exists())[-1] for n in names}
run('final_fine_fields_v1', ['python3', str(b/'analyze_hotspot_fields.py'),
                           *[str(plots[n]) for n in names[:4]], '--compare-first',
                           '--output', str(b/'final_fine_fields_v1')])
run('final_mesh_fields_v1', ['python3', str(b/'analyze_hotspot_fields.py'),
                           str(plots[names[0]]), str(plots[names[4]]),
                           '--output', str(b/'final_mesh_fields_v1')])
for n, entry in combined.items():
    assert entry['solver_exit_code'] == 0 and abs(entry['last_time_us']-50) < 1e-7
    assert entry['partial_steps_excluded'] == 0
    assert entry['max_nonfinite_cell_count'] == 0
status.write_text(json.dumps({'state': 'complete', 'exit_codes': codes,
                             'case_count': len(names),
                             'summary_sha256': hashlib.sha256((b/'final_history_summary_v1.json').read_bytes()).hexdigest()}, indent=2))
print(status.read_text())
