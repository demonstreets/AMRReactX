from pathlib import Path
import json,hashlib,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
b=Path('/home/cj/my-pele/repair_validation/thermal_model_20260911');base=json.loads((b/'burned_gas_finite_rate_v3/result.json').read_text());more=json.loads((b/'burned_gas_kinetic_sensitivity_v1/result.json').read_text());out=b/'kinetic_comparison_v1';out.mkdir(exist_ok=False)
models=[('GRI subset: 17 species',base['samples']),('GRI subset: no peroxides',more['variants'][0]['samples']),('GRI common subset: 12 species',more['variants'][1]['samples']),('Lu common subset: 12 species',more['variants'][2]['samples'])]
fig,axes=plt.subplots(1,2,figsize=(13,5.4),constrained_layout=True);table=[]
for ax,i,title in zip(axes,[3,4],['Saved-field peak state','Transient stage peak state']):
 native=[p for p in base['native_results'] if p['sample']==i and p['success']]
 ax.semilogx([p['time_s']*1e9 for p in native],[p['T_K'] for p in native],'k-',label='Active WD6',lw=1.8)
 for j,(label,samples) in enumerate(models):
  s=next(q for q in samples if q['sample_index']==i);t=s['runs'][-1]['trajectory'];positive=[q for q in t if q['time_s']>0]
  ax.semilogx([q['time_s']*1e9 for q in positive],[q['T_K'] for q in positive],['-','--',':','-.'][j],label=label,lw=1.8)
  below=next(q['time_s']*1e9 for q in t if q['T_K']<5000)
  previous=max(q['time_s']*1e9 for q in t if q['time_s']*1e9<below)
  table.append({'sample':i,'model':label,'initial_T_K':t[0]['T_K'],'T_at_2p5ns_K':t[4]['T_K'],'T_at_100ns_K':t[9]['T_K'],'T_at_2us_K':t[-1]['T_K'],'first_sampled_crossing_5000_bracket_ns':[previous,below],'maximum_tolerance_difference_K':s.get('maximum_T_difference_on_tightening_K',s.get('max_tolerance_difference_K'))})
 ax.axhline(5000,color='gray',ls='--',lw=.8);ax.set(title=title,xlabel='Closed fixed-density relaxation time (ns)',ylabel='Temperature (K)',ylim=(3750,5500));ax.grid(alpha=.25)
axes[0].legend(fontsize=8,loc='lower left');fig.suptitle('Burned-gas kinetic sensitivity at the same conserved energy\nDerived subsets; high-temperature kinetics remain unvalidated')
fig.savefig(out/'kinetic_sensitivity.png',dpi=180)
(out/'summary.json').write_text(json.dumps({'results':table,'scope':more['scope'],'all_models_match_initial_conserved_state':True},indent=2));print(json.dumps(table,indent=2))
