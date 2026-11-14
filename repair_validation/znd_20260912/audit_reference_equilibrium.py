"""Check whether thermodynamic CJ products are stationary under actual rates."""
from pathlib import Path
import json,numpy as np,cantera as ct
b=Path(__file__).resolve().parent
g=ct.Solution('/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml')
cj=json.loads((b/'reference_near_cj_v1/CJ.json').read_text())[0];g.TDY=cj['T_K'],cj['rho_kg_m3'],cj['Y'];dy=g.net_production_rates*g.molecular_weights/g.density
rec={'initial_max_abs_dY_dt_per_s':float(abs(dy).max()),'initial_species_l1_dY_dt_per_s':float(abs(dy).sum()),'initial_net_heat_release_W_m3':g.heat_release_rate,'initial_T_K':g.T,'initial_P_Pa':g.P,'initial_max_rate_species':g.species_names[int(np.argmax(abs(dy)))],'reversible_reactions':sum(rx.reversible for rx in g.reactions()),'reaction_count':g.n_reactions}
r=ct.IdealGasReactor(g,energy='on',clone=True);net=ct.ReactorNet([r]);net.rtol=1e-10;net.atol=1e-18;points=[]
for t in [1e-8,1e-7,1e-6,1e-5,1e-4,1e-3]:
 net.advance(t);points.append({'time_s':t,'T_K':r.T,'P_Pa':r.phase.P,'maximum_Y_change':float(np.max(abs(r.phase.Y-np.array(cj['Y']))))})
rec['constant_volume_relaxation']=points;(b/'kinetic_equilibrium_audit.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec,indent=2))

