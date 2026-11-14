"""Bounded same-state GPU partition comparison after an intentional saved stop."""
from pathlib import Path
import argparse
import subprocess
import json
import re
import shutil
import os
import hashlib
import sys
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
parser.add_argument('output',type=Path)
a=parser.parse_args()
r=Path('/home/cj/my-pele')
sys.path.insert(0,str(r/'tools'))
import amrex_reader
from read_native_spray import read_native_spray

source=a.source.resolve()
assert int((source/'exit_code').read_text())==6
assert json.loads((source/'stop_reason.json').read_text())['intentional_continuation']
checkpoint=sorted(q for q in source.glob('chk*') if (q/'Header').is_file())[-1]
step=int(checkpoint.name[3:]);initial=source/('plt'+checkpoint.name[3:])
start=amrex_reader.read_plotfile(str(initial))['time']
output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();env['LD_LIBRARY_PATH']='/home/cj/local/cuda-12.6/lib64:'+env.get('LD_LIBRARY_PATH','')
env['OMP_NUM_THREADS']='1'
exe=r/'examples/academic/spray_detonation/spatial_wd6_stoich_v12d.gnu.MPI.CUDA.ex'
results={}
for label,ranks,grid in [('one_gpu',1,'400 400'),('two_gpu_400',2,'400 400'),('two_gpu_100',2,'100 100')]:
    d=output/label;d.mkdir()
    for name in ['profile_SI.txt','droplets.dat']:shutil.copy2(source/name,d/name)
    (d/'bind_rank.sh').write_text('#!/bin/bash\nexport CUDA_VISIBLE_DEVICES="${OMPI_COMM_WORLD_LOCAL_RANK:-0}"\nexec "$@"\n')
    text=(source/'inputs').read_text()
    for key,new in [('max_step',str(step+20)),('stop_time',str(start+1e-6)),
                    ('prob.record_wave_history','0'),('amr.plot_per','1.e-3'),
                    ('amr.restart',str(checkpoint)),('amr.plotfile_on_restart','1'),
                    ('amr.regrid_on_restart','1'),('amr.max_grid_size',grid),
                    ('pelec.fixed_dt','2.e-9'),('pelec.profile_strang','1')]:
        pattern=r'^'+re.escape(key)+r'\s*=.*$'
        if re.search(pattern,text,re.M):text=re.sub(pattern,key+' = '+new,text,flags=re.M)
        else:text+='\n'+key+' = '+new+'\n'
    text=re.sub(r'^prob\.wave_history_interval\s*=.*\n','',text,flags=re.M)
    (d/'inputs').write_text(text)
    manifest=json.loads((source/'case.json').read_text())
    command=['mpirun','-np',str(ranks),'bash',str(d/'bind_rank.sh'),str(exe),'inputs']
    manifest.update(command=command,binary=str(exe),binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                    input_sha256=hashlib.sha256(text.encode()).hexdigest(),restart_from=str(checkpoint),
                    purpose='20 fixed steps from the same evolved state; GPU partition comparison, not a full propagation benchmark')
    (d/'case.json').write_text(json.dumps(manifest,indent=2))
    with (d/'run.log').open('w') as log:
        result=subprocess.run(command,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT)
    (d/'exit_code').write_text(str(result.returncode));assert result.returncode==0,(label,result.returncode)
    subprocess.run(['python3',str(r/'tools/validate_spray_restart.py'),str(initial),str(d/initial.name),
                    '--output',str(d/'restart_state_validation.json')],check=True)
    log=(d/'run.log').read_text()
    timing=[tuple(map(float,m)) for m in re.findall(r'STRANG_TIMING chemistry_1_s=(\S+) transport_s=(\S+) chemistry_2_s=(\S+)',log)]
    assert len(timing)==20,(label,len(timing))
    final=d/('plt'+format(step+20,'05d'));assert (final/'Header').is_file()
    results[label]={'ranks':ranks,'max_grid_size':grid,'median_step_s':float(np.median(np.sum(timing[2:],axis=1))),
                    'median_chemistry_s':float(np.median([v[0]+v[2] for v in timing[2:]])),
                    'final_plot':str(final),'timings_s':timing}
    print(label,json.dumps({k:v for k,v in results[label].items() if k!='timings_s'}),flush=True)

baseline=amrex_reader.read_plotfile(results['one_gpu']['final_plot'])
lp=read_native_spray(results['one_gpu']['final_plot']);li=np.lexsort(lp['identity_words'].T)
for label in ['two_gpu_400','two_gpu_100']:
    raw=amrex_reader.read_plotfile(results[label]['final_plot'])
    assert raw['time']==baseline['time']
    gas={k:float(np.max(np.abs(v-raw['fields'][k]))) for k,v in baseline['fields'].items()}
    species=[v for k,v in raw['fields'].items() if k.startswith('Y(')]
    raw_valid=all(np.isfinite(v).all() for v in raw['fields'].values())
    raw_valid=bool(raw_valid and min(v.min() for v in species)>=-1.e-12 and
        np.max(abs(sum(species)-1.))<1.e-9 and raw['fields']['density'].min()>0. and
        raw['fields']['pressure'].min()>0. and raw['fields']['Temp'].min()>0.)
    rp=read_native_spray(results[label]['final_plot']);ri=np.lexsort(rp['identity_words'].T)
    assert np.array_equal(lp['identity_words'][li],rp['identity_words'][ri])
    particle={k:float(np.max(abs(v[li]-rp['fields'][k][ri]))) for k,v in lp['fields'].items()}
    def mass(p):return np.sum(p['fields']['number_density']*p['fields']['diam']**3)
    mass_error=float(abs(mass(rp)-mass(lp))/mass(lp))
    integral_errors={k:float(abs(np.sum(raw['fields'][k])-np.sum(baseline['fields'][k]))/
                            max(np.sum(abs(baseline['fields'][k])),1.e-100)) for k in ['density','rho_E']}
    passed=bool(raw_valid and gas['Temp']<.01 and max(v for k,v in gas.items() if k.startswith('Y('))<1.e-6 and
                particle['temperature']<1.e-3 and particle['diam']<1.e-10 and
                mass_error<1.e-8 and max(integral_errors.values())<1.e-8)
    results[label].update(gas_maximum_absolute_differences=gas,particle_maximum_absolute_differences=particle,
        relative_total_liquid_mass_difference=mass_error,gas_integral_relative_differences=integral_errors,
        particle_count=lp['count'],raw_fields_admissible=raw_valid,passed=passed,
        speedup=results['one_gpu']['median_step_s']/results[label]['median_step_s'])
results.update(source=str(source),checkpoint=str(checkpoint),initial_plot=str(initial),
               same_final_time_s=baseline['time'],meaning='Same-physics partition sensitivity and measured timing on available GPUs')
(output/'comparison.json').write_text(json.dumps(results,indent=2))
print(json.dumps({k:{f:v for f,v in results[k].items() if f in ['passed','speedup','median_step_s','particle_count']}
                  for k in ['two_gpu_400','two_gpu_100']}),flush=True)
