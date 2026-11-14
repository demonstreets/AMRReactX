from pathlib import Path
import subprocess,json,re,shutil,os,hashlib,sys
import numpy as np
r=Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910'
sys.path.insert(0,str(r/'tools'))
import amrex_reader
from read_native_spray import read_native_spray
source=b/'wd6_cell_wet_2d_1400x400_cfl20_tol4_gpu_v2'
checkpoint=source/'chk01226';initial=source/'plt01226'
start=amrex_reader.read_plotfile(str(initial))['time']
output=b/'wd6_stoich_native_comparison_v1'
output.mkdir(exist_ok=False)
env=os.environ.copy();env['LD_LIBRARY_PATH']='/home/cj/local/cuda-12.6/lib64:'+env.get('LD_LIBRARY_PATH','')
results={}
for label,binary in [('full','spatial_wd6_cell_v22d.gnu.MPI.CUDA.ex'),('reduced','spatial_wd6_stoich_v12d.gnu.MPI.CUDA.ex')]:
    d=output/label;d.mkdir()
    for n in ['profile_SI.txt','droplets.dat','bind_rank.sh']:shutil.copy2(source/n,d/n)
    text=(source/'inputs').read_text()
    for key,new in [('max_step','1246'),('stop_time',str(start+1e-6)),('prob.record_wave_history','0'),('amr.plot_per','1.e-3')]:
        text,n=re.subn(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+new,text,flags=re.M);assert n==1,key
    text=re.sub(r'^prob\.wave_history_interval\s*=.*\n','',text,flags=re.M)
    text+='\namr.restart = '+str(checkpoint)+'\namr.plotfile_on_restart = 1\npelec.fixed_dt = 2.e-9\npelec.profile_strang = 1\n'
    (d/'inputs').write_text(text)
    exe=r/'examples/academic/spray_detonation'/binary
    manifest=json.loads((source/'case.json').read_text())
    command=['mpirun','-np','1','bash',str(d/'bind_rank.sh'),str(exe),'inputs']
    manifest.update(command=command,binary=str(exe),binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                    input_sha256=hashlib.sha256(text.encode()).hexdigest(),wd6_linear_algebra=label,
                    purpose='20-step fixed-dt restart equivalence and timing; not a completed propagation benchmark')
    (d/'case.json').write_text(json.dumps(manifest,indent=2))
    with (d/'run.log').open('w') as f:p=subprocess.run(command,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT)
    (d/'exit_code').write_text(str(p.returncode));assert p.returncode==0,(label,p.returncode)
    subprocess.run(['python3',str(r/'tools/validate_spray_restart.py'),str(initial),str(d/'plt01226'),
                    '--output',str(d/'restart_state_validation.json')],check=True)
    log=(d/'run.log').read_text()
    timings=[tuple(map(float,m)) for m in re.findall(r'STRANG_TIMING chemistry_1_s=(\S+) transport_s=(\S+) chemistry_2_s=(\S+)',log)]
    plots=sorted(p for p in d.glob('plt*') if (p/'Header').is_file())
    assert len(timings)==20 and plots[-1].name=='plt01246',(label,len(timings),plots)
    results[label]={'median_step_s':float(np.median(np.sum(timings[2:],axis=1))),
                    'median_chemistry_s':float(np.median([x[0]+x[2] for x in timings[2:]])),
                    'timings_s':timings,'final_plot':str(plots[-1])}
    print(label,json.dumps({k:v for k,v in results[label].items() if k!='timings_s'}),flush=True)

left=amrex_reader.read_plotfile(results['full']['final_plot']);right=amrex_reader.read_plotfile(results['reduced']['final_plot'])
assert abs(left['time']-right['time'])<1e-17
gas={}
for k,v in left['fields'].items():
    err=float(np.max(abs(v-right['fields'][k])))
    gas[k]={'maximum_absolute_difference':err,'maximum_scaled_difference':err/max(float(np.max(abs(v))),1e-30)}
lp=read_native_spray(results['full']['final_plot']);rp=read_native_spray(results['reduced']['final_plot'])
li=np.lexsort(lp['identity_words'].T);ri=np.lexsort(rp['identity_words'].T)
assert np.array_equal(lp['identity_words'][li],rp['identity_words'][ri])
particles={k:float(np.max(abs(v[li]-rp['fields'][k][ri]))) for k,v in lp['fields'].items()}
passed=gas['Temp']['maximum_absolute_difference']<.01 and max(v['maximum_absolute_difference'] for k,v in gas.items() if k.startswith('Y('))<1e-6
results.update(gas_field_differences=gas,particle_absolute_differences=particles,passed=bool(passed),
               full_to_reduced_median_time_ratio=results['full']['median_step_s']/results['reduced']['median_step_s'])
(output/'comparison.json').write_text(json.dumps(results,indent=2))
print('RESULT',passed,'ratio',results['full_to_reduced_median_time_ratio'],'temperature',gas['Temp'],flush=True)
assert passed

