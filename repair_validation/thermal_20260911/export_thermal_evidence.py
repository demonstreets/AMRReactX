"""Create a compact, hash-audited evidence archive after completed analyses."""
from pathlib import Path
import hashlib
import json
import zipfile

b = Path('/home/cj/my-pele/repair_validation/thermal_20260911')
r = b.parent.parent
assert json.loads((b/'final_analysis_status_v1.json').read_text())['state'] == 'complete'
selected = {}
def add(path, name=None):
    assert path.is_file(), path
    selected[name or str(path.relative_to(b))] = path.read_bytes()

directories = ['numerical_controls_final_v1', 'boundary_control_final_v1', 'mesh_control_final_v1',
               'final_fine_fields_v1', 'final_mesh_fields_v1',
               'baseline_first_event_v1', 'half_first_event_v1',
               'baseline_peak_thermodynamics_v2', 'hot_cell_chemistry_validation_v3',
               'original_baseline_final_comparison_v1', 'metadata_history']
for dirname in directories:
    for p in (b/dirname).rglob('*'):
        if p.is_file() and p.suffix in ['.json', '.png', '.yaml', '.csv', '.txt', '.log']:
            if not p.name.endswith('_snapshot.csv'):
                add(p)
files = ['final_history_summary_v1.json', 'final_analysis_status_v1.json',
         'diagnostic_observation_acceptance_v1.json', 'diagnostic_observation_validation_v1.json',
         'observation_old_repeat_tolerance_validation_v1.json',
         'observation_new_on_off_tolerance_validation_v1.json',
         'observation_old_new_tolerance_validation_v1.json',
         'original_replay_42us_comparison.json',
         'thermodynamic_inverse_source_evidence.json',
         'conservative_original_and_baseline_peak_states_v2.json',
         'baseline_first_crossing_steps_v1.json',
         'build_diagnostics_gpu_v1/command.json', 'build_diagnostics_gpu_v1/exit_code',
         'short_controls_queue_v1.exit_code', 'short_controls_queue_v1.log',
         'coarse_replay_queue_v1.exit_code', 'coarse_replay_queue_v1.log',
         'coarse_replay_queue_v2.status.json', 'coarse_replay_queue_v2.log']
for n in files:
    add(b/n)
names = ['replay_cfl20_v1', 'replay_cfl10_v1', 'chemistry10_from48_v1',
         'lower_open_from48_v1', 'replay_coarse_cfl20_v1', 'tight_chemistry_from48_v1']
for n in names:
    for filename in ['inputs', 'case.json', 'launcher.json', 'exit_code', 'thermal_stages.csv', 'run.log']:
        add(b/n/filename)
    if (b/n/'termination_record.json').exists():
        add(b/n/'termination_record.json')
for p in b.glob('*.py'):
    add(p, 'reproduction_scripts/'+p.name)
add(b/'probe_thermal_chemistry.cpp', 'reproduction_scripts/probe_thermal_chemistry.cpp')
for name in ['external/PeleC/Source/Advance.cpp', 'external/PeleC/Source/StrangThermalDiagnostics.H',
             'src/academic/chemistry/Wd6Rosenbrock.H',
             'external/PelePhysics/Mechanisms/heptane_wd6/mechanism.yaml',
             'external/PelePhysics/Mechanisms/heptane_wd6/mechanism.H']:
    add(r/name, 'source/'+name)
manifest = {'remote_root': str(b), 'scope': 'Completed thermal controls and explicit failed/interrupted trial records; full AMReX fields and executable remain on server.',
            'files': {n: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                      for n, raw in sorted(selected.items())}}
(b/'evidence_manifest.json').write_text(json.dumps(manifest, indent=2))
archive = b/'thermal_evidence_v1.zip'
assert not archive.exists()
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for n, raw in selected.items():
        z.writestr(n, raw)
    z.writestr('evidence_manifest.json', json.dumps(manifest, indent=2))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(json.dumps({'archive': str(archive), 'file_count': len(selected), 'bytes': archive.stat().st_size,
                  'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2))
