from pathlib import Path
import subprocess,json,re,shutil,os,hashlib,sys
import numpy as np
r=Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910'
sys.path.insert(0,str(r/'tools'))
import amrex_reader
env=os.environ.copy();env['OMP_NUM_THREADS']='1'
binary=r/'examples/academic/spray_detonation/spatial_regrid_v22d.gnu.MPI.ex'
def tolerance_inputs(d):
    text=(d/'inputs').read_text()
    for key,new in [('ode.rtol','1.e-6'),('ode.atol','1.e-16')]:
        text,n=re.subn(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+new,text,flags=re.M);assert n==1,key
    (d/'inputs').write_text(text)
    m=json.loads((d/'case.json').read_text());m.update(ode_rtol=1e-6,ode_atol=1e-16,input_sha256=hashlib.sha256(text.encode()).hexdigest())
    (d/'case.json').write_text(json.dumps(m,indent=2))
def run(d,cmd):
    with (d/'run.log').open('w') as f:p=subprocess.run(cmd,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT)
    (d/'exit_code').write_text(str(p.returncode));assert p.returncode==0,(d,p.returncode)
for kind in ['dry','wet']:
    d=b/f'native88_tol6_{kind}_closed_cpu_v1'
    cmd=['python3',str(r/'examples/academic/spray_detonation/prepare_closed_case.py'),str(d),
         '--reference',str(b/'reference_znd_v1'),'--binary',str(binary)]
    if kind=='dry':cmd+=['--dry']
    subprocess.run(cmd,check=True)
    tolerance_inputs(d);run(d,json.loads((d/'case.json').read_text())['command'])
    cmd=['python3',str(r/'tools/validate_closed_spray.py'),str(d),'--output',str(d/'validation.json')]
    if kind=='dry':cmd+=['--cantera']
    subprocess.run(cmd,check=True)
    print('CLOSED',kind,'complete',flush=True)

source=b/'native88_cpu_partition_probe_v1';d=b/'native88_tol6_partition_probe_v1';d.mkdir(exist_ok=False)
for name in ['inputs','case.json','profile_SI.txt','droplets.dat']:shutil.copy2(source/name,d/name)
tolerance_inputs(d)
text=(d/'inputs').read_text()+'\npelec.profile_strang = 1\n';(d/'inputs').write_text(text)
cmd=['mpirun','-np','8',str(binary),'inputs'];m=json.loads((d/'case.json').read_text());m.update(command=cmd,input_sha256=hashlib.sha256(text.encode()).hexdigest());(d/'case.json').write_text(json.dumps(m,indent=2))
run(d,cmd)
subprocess.run(['python3',str(r/'tools/validate_spray_restart.py'),str(source/'plt03171'),str(d/'plt03171'),
                '--output',str(d/'restart_state_validation.json')],check=True)
left=amrex_reader.read_plotfile(str(source/'plt03191'));right=amrex_reader.read_plotfile(str(d/'plt03191'))
gas={k:float(np.max(abs(v-right['fields'][k]))) for k,v in left['fields'].items()}
log=(d/'run.log').read_text();steps=list(map(float,re.findall(r'Coarse TimeStep time: (\S+)',log)))
passed=abs(left['time']-right['time'])<1e-11 and gas['Temp']<.1 and max(v for k,v in gas.items() if k.startswith('Y('))<1e-5
result={'times_s':[left['time'],right['time']],'gas_maximum_absolute_differences':gas,
        'median_step_s':float(np.median(steps[2:])),
        'profile':re.findall(r'STRANG_TIMING.*',log)[-5:],'passed':bool(passed),
        'interpretation':'Short evolving-state sensitivity, with independent closed reactor checks; full propagation sensitivity remains to be assessed.'}
(d/'comparison.json').write_text(json.dumps(result,indent=2));print('PROBE',json.dumps(result),flush=True);assert passed

