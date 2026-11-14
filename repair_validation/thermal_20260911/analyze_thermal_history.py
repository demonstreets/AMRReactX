"""Analyze immutable snapshots of opt-in Strang diagnostics.

The global maximum may move between stages. Only the fixed probe permits
same-cell operator increments. Stage time labels are the enclosing step end,
not physical times assigned to the split operators.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

parser = argparse.ArgumentParser()
parser.add_argument('cases', nargs='+', type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--plot-start-us', type=float)
args = parser.parse_args()
args.output.mkdir(exist_ok=False, parents=True)
stages = ['before', 'chemistry_1', 'transport_and_spray', 'chemistry_2']
summaries = {}
fig, axes = plt.subplots(3, 2, figsize=(14, 12), constrained_layout=True)
for case_index, case in enumerate(args.cases):
    color = plt.get_cmap('tab10')(case_index)
    case_label = {'replay_cfl20_v1': 'Baseline CFL 0.2', 'replay_cfl10_v1': 'Half-step CFL 0.1',
                  'lower_open_from48_v1': 'Lower boundary open',
                  'tight_chemistry_from48_v1': '100x chemistry (interrupted)',
                  'chemistry10_from48_v1': '10x tighter chemistry',
                  'replay_coarse_cfl20_v1': 'Coarse grid 0.1 mm'}.get(case.name, case.name)
    raw = (case / 'thermal_stages.csv').read_bytes()
    # The writer can be active. Snapshot only newline-terminated CSV records.
    raw = raw[:raw.rfind(b'\n') + 1]
    (args.output / (case.name + '_snapshot.csv')).write_bytes(raw)
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    data = []
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            continue
        data.append({k: v if k in ['stage', 'point'] else float(v) for k, v in row.items()})
    groups = {}
    for row in data:
        groups.setdefault(int(row['step']), {})[(row['stage'], row['point'])] = row
    complete = {k: v for k, v in groups.items()
                if all((s, p) in v for s in stages for p in ['maximum', 'fixed_probe'])}
    if not complete:
        summaries[case.name] = {'complete_steps': 0}
        continue
    accepted = [row for k, group in complete.items() for row in group.values()]
    end = [group[('chemistry_2', 'maximum')] for group in complete.values()]
    peak = max(accepted, key=lambda x: x['T_K'])
    crossing = next((row for row in accepted if row['cells_above_fit_upper'] > 0), None)
    increments = []
    for step, group in complete.items():
        for previous, stage in zip(stages, stages[1:]):
            prior = group[(previous, 'fixed_probe')]
            curr = group[(stage, 'fixed_probe')]
            increments.append({'step': step, 'stage': stage,
                'time_step_end_us': (curr['time_start_s'] + curr['dt_s']) * 1e6,
                **{'delta_' + field: curr[field] - prior[field]
                   for field in ['T_K', 'e_internal_J_kg', 'rho_kg_m3', 'u_m_s', 'v_m_s']}})
    with (args.output / (case.name + '_probe_increments.csv')).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=increments[0].keys())
        writer.writeheader()
        writer.writerows(increments)
    exit_path = case / 'exit_code'
    summary = {'case': str(case), 'snapshot_sha256': hashlib.sha256(raw).hexdigest(),
        'analysis_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'case_input_sha256': hashlib.sha256((case/'inputs').read_bytes()).hexdigest(),
        'complete_steps': len(complete), 'partial_steps_excluded': len(groups) - len(complete),
        'first_time_us': end[0]['time_start_s'] * 1e6,
        'last_time_us': (end[-1]['time_start_s'] + end[-1]['dt_s']) * 1e6,
        'solver_exit_code': int(exit_path.read_text().strip()) if exit_path.exists() else None,
        'maximum_over_recorded_operator_stages': peak,
        'first_step_with_cell_above_fit_upper': crossing,
        'max_nonfinite_cell_count': max(row['cells_nonfinite_T'] for row in accepted),
        'max_recorded_internal_energy_disagreement_J_kg': max(
            abs(row['e_internal_J_kg']-row['stored_e_internal_J_kg']) for row in accepted),
        'final_complete_step': end[-1],
        'fixed_probe_largest_temperature_increase_by_operator': {
            stage: max((x for x in increments if x['stage'] == stage), key=lambda x: x['delta_T_K'])
            for stage in stages[1:]},
        'interpretation': 'Moving global maxima are extrema, not same-cell operator histories; '
                          'fixed-probe increments refer to one Eulerian cell. '
                          'Intermediate stages are labeled by enclosing step end only.'}
    window_end = [row for row in end if row['time_start_s']+row['dt_s'] > 48e-6]
    if window_end:
        cell_shape = re.findall(r'^amr.n_cell\s*=\s*([^#\n]+)', (case/'inputs').read_text(), re.M)[-1]
        cell_count = int(np.prod([int(x) for x in cell_shape.split()]))
        durations = np.array([row['time_start_s']+row['dt_s']-max(row['time_start_s'], 48e-6)
                              for row in window_end])
        counts = np.array([row['cells_above_fit_upper'] for row in window_end])
        summary['window_from_48us'] = {
            'duration_us': float(durations.sum()*1e6),
            'max_complete_step_T_K': max(row['T_K'] for row in window_end),
            'max_complete_step_hot_cell_count': int(counts.max()),
            'duration_with_any_hot_cell_us': float(durations[counts>0].sum()*1e6),
            'hot_cell_space_time_fraction': float(np.dot(durations, counts)/durations.sum()/cell_count),
            'max_regional_complete_step_T_K': {key: max(row[key] for row in window_end)
                 for key in ['lower_band_Tmax_K', 'upper_band_Tmax_K', 'interior_Tmax_K']},
            'quadrature': 'Step-end rectangle rule, clipped at the 48-us lower window edge.'}
        budget_steps = [step for step, group in complete.items()
                        if group[('before', 'fixed_probe')]['time_start_s'] >= 48e-6]
        if budget_steps:
            first = complete[budget_steps[0]][('before', 'fixed_probe')]
            last = complete[budget_steps[-1]][('chemistry_2', 'fixed_probe')]
            budget_step_set = set(budget_steps)
            budget_increments = [item for item in increments if item['step'] in budget_step_set]
            budget = {'start_time_us': first['time_start_s']*1e6,
                      'end_time_us': (last['time_start_s']+last['dt_s'])*1e6,
                      'probe_xy_mm': [first['x_mm'], first['y_mm']],
                      'initial_T_K': first['T_K'], 'final_T_K': last['T_K'],
                      'interpretation': 'Eulerian fixed-cell split-operator accounting, '
                          'not a Lagrangian heat budget or a unique thermodynamic decomposition.'}
            budget_fig, budget_axes = plt.subplots(1, 2, figsize=(13, 4.7), constrained_layout=True)
            for axis, field, units in zip(budget_axes, ['T_K', 'e_internal_J_kg'], ['K', 'J/kg']):
                totals = {stage: sum(item['delta_'+field] for item in budget_increments if item['stage'] == stage)
                          for stage in stages[1:]}
                actual_change = last[field]-first[field]
                budget[field] = {'change_by_operator': totals, 'total_change': actual_change,
                                 'unattributed_inter_step_change': actual_change-sum(totals.values())}
                for stage in stages[1:]:
                    points = [item for item in budget_increments if item['stage'] == stage]
                    axis.plot([item['time_step_end_us'] for item in points],
                              np.cumsum([item['delta_'+field] for item in points]), label=stage)
                actual_rows = [complete[step][('chemistry_2', 'fixed_probe')] for step in budget_steps]
                axis.plot([(item['time_start_s']+item['dt_s'])*1e6 for item in actual_rows],
                          [item[field]-first[field] for item in actual_rows], 'k--', label='Actual net change')
                axis.set(xlabel='Step-end time (microseconds)', ylabel='Cumulative change ('+units+')',
                         title='Fixed-cell '+('temperature' if field == 'T_K' else 'internal energy'))
                axis.grid(alpha=.25)
                axis.legend(fontsize=8)
            budget_fig.suptitle(case_label+': fixed Eulerian probe; operator increments since 48 us')
            budget_fig.savefig(args.output/(case.name+'_probe_operator_budget.png'), dpi=160)
            plt.close(budget_fig)
            summary['probe_operator_budget_since_48us'] = budget
    summaries[case.name] = summary
    t = np.array([(row['time_start_s'] + row['dt_s']) * 1e6 for row in end])
    axes[0, 0].plot(t, [row['T_K'] for row in end], color=color, label=case_label)
    for key, style, label in [('lower_band_Tmax_K', '-', 'lower wall'),
                              ('upper_band_Tmax_K', '--', 'upper wall'),
                              ('interior_Tmax_K', ':', 'interior')]:
        axes[0, 1].plot(t, [row[key] for row in end], style, color=color, label=case_label + ': ' + label)
    axes[1, 0].plot(t, [row['cells_above_fit_upper'] for row in end], color=color, label=case_label)
    probe = [group[('chemistry_2', 'fixed_probe')] for group in complete.values()]
    axes[1, 1].plot(t, [row['T_K'] for row in probe], color=color, label=case_label)
    axes[2, 0].plot(t, [row['e_internal_J_kg'] / 1e6 for row in probe], color=color, label=case_label)
    axes[2, 1].plot(t, [row['dt_s'] * 1e9 for row in end], color=color, label=case_label)
for ax, title, ylabel in zip(axes.flat,
    ['Complete-step domain maximum', 'Complete-step regional maxima',
     'Complete-step cells above 5000 K', 'Fixed Eulerian probe temperature',
     'Fixed Eulerian probe internal energy', 'Hydrodynamic time step'],
    ['T (K)', 'T (K)', 'Cell count', 'T (K)', 'e (MJ/kg)', 'dt (ns)']):
    ax.set(title=title, xlabel='Step-end time (microseconds)', ylabel=ylabel)
    ax.grid(alpha=.25)
    ax.legend(fontsize=7)
    if args.plot_start_us is not None:
        ax.set_xlim(left=args.plot_start_us)
axes[1, 0].set_ylim(bottom=0.)
axes[1, 0].yaxis.set_major_locator(MaxNLocator(integer=True))
for ax in [axes[0, 0], axes[0, 1], axes[1, 1]]:
    ax.axhline(5000, color='gray', linestyle='--', linewidth=1)
fig.suptitle('Thermal control histories; complete Strang steps only')
fig.savefig(args.output / 'thermal_history.png', dpi=160)
(args.output / 'summary.json').write_text(json.dumps(summaries, indent=2))
print(json.dumps(summaries, indent=2))
