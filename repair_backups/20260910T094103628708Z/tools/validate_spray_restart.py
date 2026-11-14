"""Compare gas and individual evolved droplets at a checkpoint restart time.

Use the source plotfile at the checkpoint time and the restart plotfile written
with amr.plotfile_on_restart=1. Particle ordering may change across MPI ranks;
their stored identity words provide the correspondence. Fresh init_file data
must not replace checkpoint droplets. Per-step spray source buffers are not
conservative state and are reported separately from the acceptance decision.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import amrex_reader
from read_native_spray import read_native_spray

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("source",type=Path)
p.add_argument("restart",type=Path)
p.add_argument("--output",type=Path,required=True)
p.add_argument("--rtol",type=float,default=1.e-12)
a=p.parse_args()
left=amrex_reader.read_plotfile(str(a.source))
right=amrex_reader.read_plotfile(str(a.restart))
lf,rf=left["fields"],right["fields"]
if not np.array_equal(left["x"],right["x"]) or not np.array_equal(left["dx"],right["dx"]):
    raise ValueError("restart changed physical cell coordinates or spacing")
required=[k for k in lf if k in ["density","rho_E","Temp","pressure","x_velocity","y_velocity","z_velocity"] or
          k.startswith("rho_") or k.startswith("Y(")]
if set(required)-set(rf): raise ValueError("restart plotfile omits gas state fields")
gas={}
for k in required:
    if lf[k].shape!=rf[k].shape: raise ValueError("restart changed the physical mesh resolution")
    scale=max(float(np.max(abs(lf[k]))),1.e-30)
    error=float(np.max(abs(lf[k]-rf[k])))
    gas[k]={"maximum_absolute_difference":error,"maximum_scaled_difference":error/scale}
lp=read_native_spray(a.source)
rp=read_native_spray(a.restart)
li=np.lexsort(lp["identity_words"].T)
ri=np.lexsort(rp["identity_words"].T)
identity_equal=np.array_equal(lp["identity_words"][li],rp["identity_words"][ri])
unique_ids=len(np.unique(lp["identity_words"],axis=0))==lp["count"]
particle={}
if identity_equal:
    if set(lp["fields"])!=set(rp["fields"]): raise ValueError("particle real components changed")
    for k,v in lp["fields"].items():
        error=float(np.max(abs(v[li]-rp["fields"][k][ri]))) if len(v) else 0.
        scale=max(float(np.max(abs(v))),1.e-30) if len(v) else 1.
        particle[k]={"maximum_absolute_difference":error,"maximum_scaled_difference":error/scale}
source_buffers={k:float(np.max(abs(v-rf[k]))) for k,v in lf.items() if k.startswith("spray_") and k.endswith("_src") and k in rf}
passed=bool(left["time"]==right["time"] and identity_equal and unique_ids and
            all(v["maximum_scaled_difference"]<=a.rtol for v in gas.values()) and
            all(v["maximum_scaled_difference"]<=a.rtol for v in particle.values()))
result={"source":str(a.source.resolve()),"restart":str(a.restart.resolve()),
        "times_s":[left["time"],right["time"]],"particle_counts":[lp["count"],rp["count"]],
        "identity_words_equal":bool(identity_equal),"source_particle_identities_unique":bool(unique_ids),
        "gas_state":gas,"particle_state":particle,"nonstate_spray_source_buffer_differences":source_buffers,
        "relative_tolerance":a.rtol,"passed":passed}
a.output.write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ["gas_state","particle_state","nonstate_spray_source_buffer_differences"]}))
raise SystemExit(0 if passed else 2)
