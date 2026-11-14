from pathlib import Path
import json,numpy as np,cantera as ct
b=Path('/home/cj/my-pele/repair_validation/thermal_model_20260911');d=b/'burned_gas_finite_rate_v3';data=json.loads((d/'result.json').read_text());g=ct.Solution(str(d/'burned_gas_gri_highT_trace_heptane.yaml'))
nu=g.product_stoich_coeffs-g.reactant_stoich_coeffs
out=[]
for s in data['samples']:
 points=[]
 for q in s['runs'][-1]['trajectory']:
  g.TDY=q['T_K'],s['source_sample']['density_kg_m3'],q['Y']
  du=g.partial_molar_int_energies@nu
  # Species molar energy [J/kmol] and net progress [kmol/m3/s].
  contribution=-du*g.net_rates_of_progress/(g.density*g.cv_mass)
  identity=-np.dot(g.partial_molar_int_energies,g.net_production_rates)/(g.density*g.cv_mass)
  assert abs(contribution.sum()-identity)<max(1e-3,abs(identity)*1e-12)
  top=np.argsort(abs(contribution))[-6:][::-1]
  points.append({'time_s':q['time_s'],'T_K':g.T,'p_Pa':g.P,'dTdt_K_s':float(identity),'dominant_reactions':[{'index':int(i),'equation':g.reaction(i).equation,'net_progress_kmol_m3_s':float(g.net_rates_of_progress[i]),'dTdt_K_s':float(contribution[i])} for i in top],'radical_mass_fractions':{n:float(g[n].Y[0]) for n in ['H','O','OH','NO','CO','H2']}})
 out.append({'sample':s['sample_index'],'points':points})
result={'samples':out,'scope':'Instantaneous fixed-density temperature-rate decomposition along the verified finite-rate trajectories. Reaction contributions can change sign over time and are not integrated heat fractions or flow compression budgets.'}
(d/'reaction_channel_diagnostics.json').write_text(json.dumps(result,indent=2));print(json.dumps([{'sample':v['sample'],'initial':v['points'][0],'at_2p5ns':v['points'][4]} for v in out[-2:]],indent=2))
