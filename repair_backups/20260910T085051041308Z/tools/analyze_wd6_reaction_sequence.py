"""Shock-aligned WD6 reaction/evaporation diagnostics from a native plotfile.

All rates are evaluated in individual cells before transverse averaging.
The explicit WD6 formulas match the compiled three-reaction mechanism,
including its recorded concentration regularization. This diagnostic does not
interpret an ordered set of peaks as proof of a separate relay detonation.
"""
import argparse
import json
from pathlib import Path
import re

import cantera as ct
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import amrex_reader

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("run", type=Path)
p.add_argument("plot", help="name of one completed plotfile in the run")
p.add_argument("output", type=Path)
p.add_argument("--behind-mm", type=float, default=30.)
a = p.parse_args()
run = a.run.resolve()
manifest = json.loads((run/"case.json").read_text())
if manifest["mechanism"] != "heptane_wd6":
    p.error("this model-specific diagnostic requires heptane_wd6")
text = (run/"inputs").read_text()
def inp(name):
    return float(re.findall(r"^"+re.escape(name)+r"\s*=\s*([^#\n]+)", text, re.M)[-1])
p0 = inp("prob.p0")
eps = inp("prob.expected_wd6_regularization")
data = amrex_reader.read_plotfile(str(run/a.plot))
f = data["fields"]
x = np.asarray(data["x"])
T = f["Temp"]
if T.ndim != 2 or a.behind_mm <= 0.:
    p.error("requires a 2D plotfile and positive analysis distance")
root = Path(__file__).resolve().parents[1]
g = ct.Solution(str(root/"external/PelePhysics/Mechanisms/heptane_wd6/mechanism.yaml"))
names = ["nc7h16", "o2", "co", "h2o", "co2", "n2"]
assert g.species_names == names
Y = np.stack([f["Y("+n+")"] for n in names], axis=-1)
if not np.all(np.isfinite(Y)) or Y.min() < -1.e-12 or np.max(abs(Y.sum(axis=-1)-1.)) > 1.e-8:
    raise ValueError("raw mass fractions failed admissibility checks")
c = f["density"][...,None]*1.e6*Y/g.molecular_weights
def fractional(v, exponent):
    return v*(np.maximum(v,0.)+eps)**(exponent-1.) if eps>0. else np.maximum(v,0.)**exponent
q1 = 19922349.2590608*np.exp(-15096.586004963/T)*fractional(c[...,0],.25)*np.maximum(c[...,1],0.)**1.5
q2 = 12589254117.9417*np.exp(-20128.7813399506/T)*fractional(c[...,1],.25)*c[...,2]*fractional(c[...,3],.5)
q3 = 500000000.*np.exp(-20128.7813399506/T)*c[...,4]
# Ideal-gas species enthalpies depend on temperature alone. Chunk the
# independent thermodynamic evaluation to bound Cantera's working memory.
h1 = np.empty_like(T)
h2 = np.empty_like(T)
for first in range(0,T.shape[0],64):
    sl = slice(first,first+64)
    temps = T[sl].reshape(-1)
    states = ct.SolutionArray(g,len(temps))
    states.TP = temps,1.e5
    h = states.partial_molar_enthalpies/1000.  # J/mol
    h1[sl] = (-h[:,0]-7.5*h[:,1]+7.*h[:,2]+8.*h[:,3]).reshape(T[sl].shape)
    h2[sl] = (-h[:,2]-.5*h[:,1]+h[:,4]).reshape(T[sl].shape)
power1 = -q1*h1
power2 = -(q2-q3)*h2
native_hrr = f["heatRelease"]*.1
reconstructed = power1+power2
hrr_error = float(np.max(abs(reconstructed-native_hrr))/max(float(np.max(abs(native_hrr))),1.e-30))
if hrr_error > 1.e-7:
    raise ValueError(f"reconstructed reaction heat release differs from native field: {hrr_error}")
front = []
for column in f["pressure"].T:
    ids = np.flatnonzero(column>3.*p0)
    if not len(ids) or ids[-1]==len(x)-1:
        raise ValueError("leading shock is absent or reaches the outlet")
    i = ids[-1]
    front.append(x[i]+(3.*p0-column[i])/(column[i+1]-column[i])*(x[i+1]-x[i]))
front = np.asarray(front)
# Positive distance is behind each local shock, not behind the mean front.
distance = np.arange(0.,a.behind_mm+data["dx"][0]*5.,data["dx"][0]*10.)
coverage = np.zeros(len(distance),dtype=int)
fields = {"pressure_Pa":f["pressure"]*.1,"gas_temperature_K":T,
          "fuel_oxidation_mol_m3_s":q1,"CO_oxidation_net_mol_m3_s":q2-q3,
          "fuel_stage_power_W_m3":power1,"CO_stage_net_power_W_m3":power2,
          "total_heat_release_W_m3":native_hrr}
for n in names: fields["Y_"+n] = f["Y("+n+")"]
if "spray_rho_src" in f:
    fields["evaporation_kg_m3_s"] = f["spray_rho_src"]*1000.
    fields["liquid_density_kg_m3"] = f["spray_density"]*1000.
profiles = {name:np.zeros(len(distance)) for name in fields}
for j in range(T.shape[1]):
    behind = (front[j]-x[::-1])*10.
    valid = (distance>=behind[0]) & (distance<=behind[-1])
    coverage[valid] += 1
    for name,values in fields.items():
        profiles[name][valid] += np.interp(distance[valid],behind,values[::-1,j])
if np.any(coverage==0):
    raise ValueError("analysis window extends beyond available shock-aligned data")
profiles = {name:values/coverage for name,values in profiles.items()}
metrics = {}
for name in ["fuel_stage_power_W_m3","CO_stage_net_power_W_m3","total_heat_release_W_m3","evaporation_kg_m3_s"]:
    if name not in profiles: continue
    v = profiles[name]
    positive = np.maximum(v,0.)
    metrics[name] = {"positive_peak_gap_mm":float(distance[np.argmax(v)]) if v.max()>0. else None,
                     "positive_centroid_gap_mm":float(np.dot(distance,positive)/positive.sum()) if positive.sum()>0. else None,
                     "positive_fraction_within_5_mm":float(positive[distance<=5.].sum()/positive.sum()) if positive.sum()>0. else None}
result = {"run":str(run),"plot":a.plot,"time_s":data["time"],"mechanism":"heptane_wd6",
          "concentration_regularization_mol_m3":eps,"native_hrr_max_scaled_difference":hrr_error,
          "coordinate":"positive distance behind the local 3*p0 leading pressure crossing, column by column",
          "reaction_1":"nc7h16 + 7.5 o2 -> 7 co + 8 h2o",
          "reaction_2_net":"co + 0.5 o2 <-> co2, forward minus dissociation rate",
          "interpretation":"Spatial source ordering and shock proximity; not a Lagrangian residence time or proof of relay detonation.",
          "metrics":metrics,"distance_behind_local_shock_mm":distance.tolist(),
          "transverse_columns_per_bin":coverage.tolist(),"profiles":{k:v.tolist() for k,v in profiles.items()}}
a.output.mkdir(parents=True,exist_ok=False)
(a.output/"reaction_sequence.json").write_text(json.dumps(result,indent=2))
fig,axs = plt.subplots(3,1,figsize=(10,9),layout="constrained",sharex=True)
axs[0].plot(distance,profiles["fuel_stage_power_W_m3"],label="Fuel to CO/H2O")
axs[0].plot(distance,profiles["CO_stage_net_power_W_m3"],label="CO to CO2, net")
axs[0].plot(distance,profiles["total_heat_release_W_m3"],label="Total",ls="--")
axs[0].set(ylabel="Chemical power (W/m3)")
for n in ["nc7h16","co","co2","h2o"]: axs[1].plot(distance,profiles["Y_"+n],label=n)
axs[1].set(ylabel="Gas mass fraction")
if "evaporation_kg_m3_s" in profiles:
    axs[2].plot(distance,profiles["evaporation_kg_m3_s"],label="Evaporation")
    axs[2].set(ylabel="Mass source (kg/m3/s)")
else:
    axs[2].plot(distance,profiles["pressure_Pa"]*1.e-6,label="Gas pressure")
    axs[2].set(ylabel="Pressure (MPa)")
for ax in axs: ax.legend();ax.grid(alpha=.2)
axs[2].set(xlabel="Distance behind local leading shock (mm)")
fig.suptitle(f"Shock-aligned local reaction sources, t = {data['time']*1.e6:.3f} microseconds")
fig.savefig(a.output/"reaction_sequence.png",dpi=170)
plt.close(fig)
print(json.dumps({k:v for k,v in result.items() if k not in ["profiles","distance_behind_local_shock_mm","transverse_columns_per_bin"]}))
