"""Reconcile inherited case metadata with actual immutable inputs and command.

Preserves the original manifest. Does not change inputs, command, executable,
solver outputs, or any running process.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re

p = argparse.ArgumentParser()
p.add_argument('cases', nargs='+', type=Path)
a = p.parse_args()
b = Path('/home/cj/my-pele/repair_validation/thermal_20260911').resolve()
audits = []
for case in a.cases:
    case = case.resolve()
    assert case.parent == b
    assert int((case/'exit_code').read_text().strip()) == 0
    manifest_path = case/'case.json'
    original_bytes = manifest_path.read_bytes()
    original = json.loads(original_bytes)
    assert not original.get('metadata_reconciled_from_actual_inputs')
    raw = (case/'inputs').read_bytes()
    text = raw.decode()
    input_hash = hashlib.sha256(raw).hexdigest()
    assert original['input_sha256'] == input_hash
    def value(key):
        values = re.findall(r'^'+re.escape(key)+r'\s*=\s*([^#\n]+)', text, re.M)
        assert len(values) == 1, (key, values)
        return values[0].strip()
    binary = Path(original['command'][-2])
    assert original['command'][-1] == 'inputs' and binary.is_file()
    binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert original.get('executable_sha256', binary_hash) == binary_hash
    restart = Path(value('amr.restart'))
    lo, hi = value('pelec.lo_bc').split(), value('pelec.hi_bc').split()
    corrected = dict(original)
    corrected.update(binary=str(binary), binary_sha256=binary_hash,
        executable_sha256=binary_hash, cfl=float(value('pelec.cfl')),
        cell_chemistry_integrator=value('pelec.cell_chemistry_integrator'),
        cell_chemistry_rtol=float(value('pelec.cell_chemistry_rtol')),
        cell_chemistry_atol_y=float(value('pelec.cell_chemistry_atol_y')),
        boundary_conditions={'lower': lo, 'upper': hi},
        transverse_boundary='lower y: '+lo[1]+'; upper y: '+hi[1],
        restart_from=str(restart), previous_run=str(restart.parent),
        output_interval_s=float(value('amr.plot_per')),
        history_output_interval_s=None,
        history_scope='thermal_stages.csv records the four split-operator stages; the legacy wave-history writer is disabled.',
        diagnostics=bool(int(value('pelec.thermal_diagnostics'))),
        thermal_probe_index=[int(x) for x in value('pelec.thermal_diagnostic_probe').split()],
        cell_shape=[int(x) for x in value('amr.n_cell').split()],
        metadata_reconciled_from_actual_inputs=True)
    assert value('prob.record_wave_history') == '0'
    backup = b/'metadata_history'/case.name/'case_before_normalization_v1.json'
    backup.parent.mkdir(parents=True, exist_ok=True)
    assert not backup.exists()
    backup.write_bytes(original_bytes)
    changes = {key: {'before': original.get(key), 'after': val}
               for key, val in corrected.items() if original.get(key) != val}
    manifest_path.write_text(json.dumps(corrected, indent=2))
    audit = {'case': str(case), 'captured_utc': datetime.now(timezone.utc).isoformat(),
             'original_manifest_backup': str(backup),
             'original_manifest_sha256': hashlib.sha256(original_bytes).hexdigest(),
             'new_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
             'unchanged_input_sha256': input_hash, 'changes': changes}
    (backup.parent/'normalization_audit.json').write_text(json.dumps(audit, indent=2))
    audits.append(audit)
print(json.dumps(audits, indent=2))
