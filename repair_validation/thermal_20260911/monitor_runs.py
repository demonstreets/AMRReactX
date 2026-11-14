"""Read-only compact status for the four isolated thermal controls."""
from pathlib import Path
import csv
import io
import json
import re
import shutil
from datetime import datetime, timezone

b = Path('/home/cj/my-pele/repair_validation/thermal_20260911')
out = {'captured_utc': datetime.now(timezone.utc).isoformat(), 'cases': {}}
for name in ['replay_cfl20_v1', 'replay_cfl10_v1', 'replay_coarse_cfl20_v1',
             'lower_open_from48_v1', 'tight_chemistry_from48_v1', 'chemistry10_from48_v1']:
    p = b/name
    if not p.is_dir():
        continue
    entry = {'exit_code': int((p/'exit_code').read_text().strip()) if (p/'exit_code').exists() else None}
    if (p/'termination_record.json').exists():
        entry['intentionally_interrupted']=True
    if (p/'thermal_stages.csv').exists():
        raw = (p/'thermal_stages.csv').read_text()
        raw = raw[:raw.rfind('\n')+1]
        rows = [r for r in csv.DictReader(io.StringIO(raw))
                if r.get('Y_n2') is not None and r['point'] == 'maximum']
        ends = [r for r in rows if r['stage'] == 'chemistry_2']
        if ends:
            last = ends[-1]
            peak = max(rows, key=lambda x: float(x['T_K']))
            first_hot = next((r for r in rows if float(r['cells_above_fit_upper']) > 0), None)
            entry.update(time_us=(float(last['time_start_s'])+float(last['dt_s']))*1e6,
                         dt_ns=float(last['dt_s'])*1e9,
                         Tmax_K=float(last['T_K']),
                         history_peak_K=float(peak['T_K']),
                         history_peak_stage=peak['stage'],
                         history_peak_xy_mm=[float(peak['x_mm']), float(peak['y_mm'])],
                         hot_count=int(last['cells_above_fit_upper']),
                         max_nonfinite_count=max(int(r['cells_nonfinite_T']) for r in rows),
                         first_hot=first_hot)
            with (p/'run.log').open('rb') as f:
                f.seek(max(0, (p/'run.log').stat().st_size-20000))
                tail = f.read().decode(errors='replace')
            timings = [float(x) for x in re.findall(r'Coarse TimeStep time:\s*([\d.eE+-]+)', tail)][-20:]
            if timings and entry['exit_code'] is None:
                entry['estimated_remaining_minutes_at_current_rate'] = (
                    (50.-entry['time_us'])*1000./entry['dt_ns']*sum(timings)/len(timings)/60.)
    out['cases'][name] = entry
out['free_GB'] = shutil.disk_usage(b).free/1e9
if (b/'short_controls_queue_v1/status.json').exists():
    out['controls'] = json.loads((b/'short_controls_queue_v1/status.json').read_text())
if (b/'short_controls_queue_v1.exit_code').exists():
    out['controls_exit_code'] = int((b/'short_controls_queue_v1.exit_code').read_text().strip())
if (b/'coarse_replay_queue_v1.status.json').exists():
    out['coarse_replay_queue'] = json.loads((b/'coarse_replay_queue_v1.status.json').read_text())
if (b/'coarse_replay_queue_v2.status.json').exists():
    out['coarse_replay_queue_v2'] = json.loads((b/'coarse_replay_queue_v2.status.json').read_text())
print(json.dumps(out, indent=2))
