"""One-shot comparison after the existing fine-wet completion analysis."""
from pathlib import Path
import json
import subprocess
import time

r = Path('/home/cj/my-pele')
b = r/'repair_validation/twophase_20260910'
status = b/'four_case_completion_queue_v1.json'
assert not status.exists()
deadline = time.monotonic()+8*3600
while True:
    marker = b/'fine_wet_completion_queue_v2.json'
    state = json.loads(marker.read_text()) if marker.is_file() else {}
    fine = state.get('wet_fine', {})
    if fine.get('status') == 'analysis failed' or fine.get('solver_exit', 0) != 0:
        raise RuntimeError(fine)
    if fine.get('analysis_exit') == 0 and 'reaction_exit' in fine:
        assert fine['reaction_exit'] == 0, fine
        break
    if time.monotonic()>deadline:
        raise TimeoutError('Fine-wet completion evidence was not ready within eight hours')
    time.sleep(30)
command = ['python3', str(r/'tools/compare_spray_detonation.py'),
           '--dry-coarse', str(b/'wd6_cell_dry_coarse_final_analysis_v2'),
           '--dry-fine', str(b/'dry_fine_completed_analysis_v3'),
           '--wet-coarse', str(b/'wet_coarse_completed_analysis_v3'),
           '--wet-fine', str(b/'wet_fine_completed_analysis_v4'),
           '--output', str(b/'wd6_four_case_comparison_v1')]
state = {'status': 'running comparison', 'command': command}
status.write_text(json.dumps(state, indent=2))
with (b/'wd6_four_case_comparison_v1.log').open('w') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
state.update(status='finished', exit_code=result.returncode)
status.write_text(json.dumps(state, indent=2))
print(json.dumps(state), flush=True)
raise SystemExit(result.returncode)
