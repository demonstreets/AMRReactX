"""Compare four completed dry/wet and coarse/fine propagation analyses.

Reports observed sensitivity without assigning a universal convergence pass.
Cellular waves can shift phase on refinement, so front fits, time windows and
pressure-trace repeat distances remain separate observables.
"""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from scipy.signal import find_peaks
import amrex_reader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser(description=__doc__)
for name in ['dry-coarse','dry-fine','wet-coarse','wet-fine']:
    p.add_argument('--'+name,type=Path,required=True,help='completed analysis directory')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
records={}
inputs={}
manifests={}
for name in ['dry_coarse','dry_fine','wet_coarse','wet_fine']:
    folder=getattr(a,name)
    z=json.loads((folder/'analysis.json').read_text())
    if z['partial_analysis'] or not z['completed_requested_time'] or not z['raw_fields_admissible'] or z['exit_code']!=0:
        raise ValueError(f'{name}: complete, successful and admissible analysis required')
    records[name]=z
    inputs[name]=(Path(z['run'])/'inputs').read_text()
    manifests[name]=json.loads((Path(z['run'])/'case.json').read_text())

def value(text,key):
    return re.findall(r'^'+re.escape(key)+r'\s*=\s*([^#\n]+)',text,re.M)[-1].split()

for key in ['geometry.prob_lo','geometry.prob_hi','prob.p0','prob.T0','prob.front',
            'prob.perturbation','prob.perturbation_mode','prob.upstream_Y',
            'pelec.lo_bc','pelec.hi_bc','prob.expected_wd6_regularization']:
    values=[value(s,key) for s in inputs.values()]
    if any(v!=values[0] for v in values):
        raise ValueError('inconsistent physical comparison parameter: '+key)
if any(z['species_names']!=records['dry_coarse']['species_names'] for z in records.values()):
    raise ValueError('mechanisms/species differ across the comparison')
for kind in ['dry','wet']:
    for key in ['liquid_phi','diameter_um','liquid_mass_density_g_cm3','gas_phi','profile_sha256']:
        if manifests[kind+'_coarse'][key]!=manifests[kind+'_fine'][key]:
            raise ValueError(f'{kind}: resolution changes physical parameter {key}')
for name,m in manifests.items():
    if (name.startswith('dry') and m['liquid_phi']!=0.) or (name.startswith('wet') and m['liquid_phi']<=0.):
        raise ValueError('dry/wet liquid loading does not match the comparison label')

common_end=min(z['rows'][-1]['time_s'] for z in records.values())
window_start=0.5*common_end

def fit(t,x,lo,hi):
    mask=(t>=lo)&(t<=hi)
    if mask.sum()<4: raise ValueError('insufficient common-window samples')
    coeff=np.polyfit(t[mask],x[mask],1)
    return {'speed_m_s':float(coeff[0]),'points':int(mask.sum()),
            'sampled_time_s':[float(t[mask][0]),float(t[mask][-1])],
            'position_residual_rms_m':float(np.sqrt(np.mean((x[mask]-np.polyval(coeff,t[mask]))**2)))}

summary={}
first_extrapolated_times = [r['time_s'] for z in records.values() for r in z['rows']
    if r.get('cells_below_thermo_temperature_range', 0) or r.get('cells_above_thermo_temperature_range', 0)]
earlier_fit_end = None
if first_extrapolated_times:
    first_bad = min(first_extrapolated_times)
    earlier_last = max(r['time_s'] for z in records.values() for r in z['rows'] if r['time_s']<first_bad)
    earlier_fit_end = .5*(earlier_last+first_bad)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for name,z in records.items():
    rows=z['rows'];t=np.array([r['time_s'] for r in rows]);x=np.array([r['shock_x_cm'] for r in rows])*.01
    mask=(t>=window_start)&(t<=common_end)
    item={'run':z['run'],'analysis':str(getattr(a,name).resolve()),
          'common_late_fit':fit(t,x,window_start,common_end),
          'early_late_fit':fit(t,x,window_start,.75*common_end),
          'late_late_fit':fit(t,x,.75*common_end,common_end),
          'pressure_trace_repeats':z.get('pressure_trace_repeats'),
          'thermodynamic_extrapolation_in_saved_fields': z.get('thermodynamic_extrapolation_in_saved_fields'),
          'thermodynamic_temperature_range_K': z.get('thermodynamic_temperature_range_K'),
          'extrapolating_saved_states': [{k:r[k] for k in ['time_s','temperature_max_K',
              'cells_below_thermo_temperature_range','cells_above_thermo_temperature_range']}
              for r in rows if r.get('cells_below_thermo_temperature_range',0) or r.get('cells_above_thermo_temperature_range',0)],
          'late_sample_count':int(mask.sum())}
    if earlier_fit_end is not None and earlier_fit_end>window_start:
        item['fit_excluding_first_and_later_extrapolating_saved_states'] = fit(t,x,window_start,earlier_fit_end)
    for key in ['shock_transverse_rms_mm','shock_transverse_span_mm',
                'heat_release_peak_gap_mm','positive_heat_release_centroid_gap_mm']:
        q=np.array([r[key] if r[key] is not None else np.nan for r in rows])[mask]
        item[key]={'minimum':float(np.nanmin(q)),'median':float(np.nanmedian(q)),
                   'maximum':float(np.nanmax(q)),
                   'meaning':'range of saved-time samples, not a statistical confidence interval'}
    if rows[0]['liquid_mass_g']>0.:
        item['remaining_liquid_fraction']=rows[-1]['liquid_mass_g']/rows[0]['liquid_mass_g']
    summary[name]=item
    label=name.replace('_',' ');color='#1d6685' if name.startswith('wet') else '#b65c22'
    style='-' if name.endswith('fine') else '--'
    axes[0,0].plot(t*1e6,x*1000.,style,color=color,label=label)
    axes[0,1].plot(t*1e6,[r['shock_transverse_rms_mm'] for r in rows],style,color=color,label=label)
    axes[1,0].plot(t*1e6,[r['positive_heat_release_centroid_gap_mm'] for r in rows],style,color=color,label=label)
    if rows[0]['liquid_mass_g']>0.:
        axes[1,1].plot(t*1e6,[r['liquid_mass_g']/rows[0]['liquid_mass_g'] for r in rows],style,color=color,label=label)

sensitivities={}
for kind in ['dry','wet']:
    c=summary[kind+'_coarse']['common_late_fit']['speed_m_s']
    f=summary[kind+'_fine']['common_late_fit']['speed_m_s']
    sensitivities[kind+'_speed_coarse_to_fine_relative_difference']=(c-f)/f
for grid in ['coarse','fine']:
    d=summary['dry_'+grid]['common_late_fit']['speed_m_s']
    w=summary['wet_'+grid]['common_late_fit']['speed_m_s']
    sensitivities[grid+'_speed_wet_to_dry_relative_difference']=(w-d)/d

# Compare pressure tracks only where every recorder contains the entire
# passage of the front. Recorder restart times differ across the four runs.
trace_windows=[z.get('pressure_trace_repeats',{}).get('crop_x_cm') for z in records.values()]
common_trace={'status':'no common complete pressure-trace window'}
trace_figure=None
if all(w is not None for w in trace_windows):
    left=max(w[0] for w in trace_windows)
    right=min(w[1] for w in trace_windows)
    if right>left:
        trace_arrays={}
        common_trace={'status':'evaluated','requested_x_cm':[left,right],'cases':{},
            'meaning':'Same physical region after all recorder restarts; repeat distances are not a converged cell-size distribution.'}
        for name,z in records.items():
            foil=amrex_reader.read_plotfile(str(Path(z['run'])/z['soot_foil']['plot']))
            x=np.asarray(foil['x'])
            mask=(x>=left)&(x<=right)
            values=foil['fields']['maximum_pressure'][mask]
            if values.shape[0]<12 or values.shape[1]<12:
                raise ValueError('common pressure-trace crop is too small to analyze')
            dx=foil['dx'];offset=x[mask][0]-.5*dx[0]
            trace_arrays[name]=(values,dx,offset)
            demeaned=values-values.mean(axis=1,keepdims=True)
            item={'sampled_x_centers_cm':[float(x[mask][0]),float(x[mask][-1])],
                  'shape':list(values.shape),
                  'history_start_time_s':z['soot_foil']['sampling_start_time_s'],
                  'history_end_time_s':float(foil['time'])}
            for axis,axis_name in [(0,'x'),(1,'y')]:
                count=values.shape[axis];lags=np.arange(1,count//2)
                spectrum=np.fft.rfft(demeaned,n=2*count,axis=axis)
                products=np.fft.irfft(spectrum.conj()*spectrum,n=2*count,axis=axis)
                numerator=np.sum(products,axis=1-axis)[lags]
                squared=np.sum(demeaned*demeaned,axis=1-axis)
                cumulative=np.r_[0.,np.cumsum(squared)]
                suffix=np.r_[np.cumsum(squared[::-1])[::-1],0.]
                denominator=np.sqrt(cumulative[count-lags]*suffix[lags])
                corr=np.divide(numerator,denominator,out=np.zeros_like(numerator),where=denominator>0.)
                peaks,_=find_peaks(corr,height=.1,prominence=.05)
                item[axis_name]={'lags_mm':(lags*dx[axis]*10.).tolist(),
                    'correlation':corr.tolist(),
                    'positive_repeat_distances_mm':((peaks+1)*dx[axis]*10.).tolist()}
            common_trace['cases'][name]=item
        trace_figure,trace_axes=plt.subplots(2,2,figsize=(10,8),layout='constrained')
        vmax=max(float(v[0].max()) for v in trace_arrays.values())*1.e-7
        for axis,(name,(values,dx,offset)) in zip(trace_axes.flat,trace_arrays.items()):
            extent=[offset*10.,(offset+len(values)*dx[0])*10.,0.,values.shape[1]*dx[1]*10.]
            im=axis.imshow((values*1.e-7).T,origin='lower',extent=extent,
                           aspect='equal',cmap='magma',vmin=0.,vmax=vmax)
            axis.set(xlabel='x (mm)',ylabel='y (mm)',title=name.replace('_',' '))
        trace_figure.colorbar(im,ax=trace_axes.ravel().tolist(),label='Maximum pressure (MPa)',shrink=.8)
        trace_figure.suptitle('Pressure tracks in the common region with complete front passage')
for ax,title,ylabel in zip(axes.flat,
        ['A  Measured leading-shock motion','B  Transverse shock structure',
         'C  Heat-release location relative to mean shock','D  Total liquid remaining'],
        ['Mean shock position (mm)','Front RMS displacement (mm)',
         'Positive heat-release centroid gap (mm)','Liquid mass / initial liquid mass']):
    ax.set(xlabel='Time (microseconds)',ylabel=ylabel,title=title)
    ax.legend(fontsize=8)
    ax.axvspan(window_start*1e6,common_end*1e6,color='.8',alpha=.15,zorder=-1)
fig.suptitle('Dry / wet propagation and spatial refinement; shaded common fitting window')
a.output.mkdir(parents=True,exist_ok=False)
fig.savefig(a.output/'grid_and_coupling_comparison.png',dpi=170)
plt.close(fig)
if trace_figure is not None:
    trace_figure.savefig(a.output/'common_pressure_tracks.png',dpi=170)
    plt.close(trace_figure)
result={'common_window_s':[window_start,common_end],'cases':summary,'observed_sensitivities':sensitivities,
        'any_thermodynamic_extrapolation_in_saved_fields':bool(first_extrapolated_times),
        'earlier_fit_requested_end_s':earlier_fit_end,
        'earlier_fit_meaning':'Sensitivity using saved states before the first recorded thermal-range exceedance. No assertion about unsaved solver steps or unaffected subsequent dynamics.',
        'common_pressure_trace':common_trace,
        'interpretation':'Numerical sensitivities and pressure-pattern distances only. Raw finite-state admissibility does not imply thermodynamic fit-range validity. Assess cellular structure visually and against the physical observation window; no universal PASS threshold is imposed.'}
(a.output/'comparison.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'common_window_s':result['common_window_s'],'observed_sensitivities':sensitivities}))
