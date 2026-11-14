"""Extract the first recorded threshold crossing and valid same-cell increments."""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json

p = argparse.ArgumentParser()
p.add_argument('cases', nargs='+', type=Path)
p.add_argument('--output', required=True, type=Path)
a = p.parse_args()
a.output.mkdir(exist_ok=False, parents=True)
stages = ['before', 'chemistry_1', 'transport_and_spray', 'chemistry_2']
results = {}
for case in a.cases:
    raw = (case/'thermal_stages.csv').read_text()
    raw = raw[:raw.rfind('\n')+1]
    rows = [{k: v if k in ['stage', 'point'] else float(v) for k, v in row.items()}
            for row in csv.DictReader(io.StringIO(raw))
            if row.get('Y_n2') is not None and row['point'] == 'maximum']
    first = next((row for row in rows if row['cells_above_fit_upper'] > 0), None)
    summary = {'case': str(case), 'first_crossing': first,
               'analysis_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if first:
        group = {row['stage']: row for row in rows if row['step'] == first['step']}
        summary['operator_stages'] = group
        summary['step_start_us'] = first['time_start_s']*1e6
        summary['step_end_us'] = (first['time_start_s']+first['dt_s'])*1e6
        same_location = len(group) == 4 and len({(row['i'], row['j']) for row in group.values()}) == 1
        summary['same_maximum_cell_at_all_four_stages'] = same_location
        increments = []
        for previous, stage in zip(stages, stages[1:]):
            if previous not in group or stage not in group:
                continue
            before, after = group[previous], group[stage]
            if (before['i'], before['j']) != (after['i'], after['j']):
                continue
            increments.append({'operator': stage, 'cell_index': [after['i'], after['j']],
                **{'delta_'+key: after[key]-before[key] for key in
                   ['T_K', 'p_Pa', 'rho_kg_m3', 'e_internal_J_kg', 'u_m_s', 'v_m_s']}})
        summary['valid_same_cell_operator_increments'] = increments
        if same_location:
            summary['net_temperature_change_K'] = group['chemistry_2']['T_K']-group['before']['T_K']
            summary['accounting_residual_K'] = summary['net_temperature_change_K']-sum(
                item['delta_T_K'] for item in increments)
        summary['interpretation'] = ('First threshold crossing in the recorded interval, not the cause of all prior heating. '
            'Increments are reported only when consecutive recorded maxima occupy the same Eulerian cell. '
            'Transport and spray are combined; their increment is not a separated compression-work measurement.')
    results[case.name] = summary
(a.output/'event_summary.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
