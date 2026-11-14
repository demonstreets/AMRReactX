"""Compare native chemistry with an independent two-extent Radau calculation.

Both solve the active regularized WD6 model, including its extrapolated
thermodynamics. This verifies numerical integration, not high-T model validity.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import subprocess
import time
import numpy as np
import cantera as ct
from scipy.integrate import solve_ivp

r=Path('/home/cj/my-pele')
b=r/'repair_validation/thermal_20260911'
parser=argparse.ArgumentParser()
parser.add_argument('cases',nargs='*',type=Path,default=[b/'replay_cfl20_v1'])
parser.add_argument('--output',type=Path,default=b/'hot_cell_chemistry_validation_v3')
args=parser.parse_args()
out=args.output
out.mkdir(exist_ok=False)
command=json.loads((b.parent/'twophase_20260910/wd6_rosenbrock_probe_v1/command.json').read_text())
command=[str(b/'probe_thermal_chemistry.cpp') if x.endswith('/probe_wd6_rosenbrock.cpp') else x for x in command]
command[command.index('-o')+1]=str(out/'probe')
command.append('-DMY_PELE_WD6_STOICH_SOLVE')
(out/'build_command.json').write_text(json.dumps(command,indent=2))
build=subprocess.run(command,cwd=r/'examples/engineering/h2_leak_3d',capture_output=True,text=True)
(out/'build.log').write_text(build.stdout+build.stderr)
assert build.returncode==0,build.stderr

names=['nc7h16','o2','co','h2o','co2','n2']
mechanism=r/'external/PelePhysics/Mechanisms/heptane_wd6/mechanism.yaml'
gas=ct.Solution(str(mechanism))
mw=gas.molecular_weights
coefficients=np.array([gas.species(n).thermo.coeffs for n in names])
assert coefficients.shape==(6,15)
R=8.31446261815324
nu=np.array([[-1.,0.],[-7.5,-.5],[7.,-1.],[8.,0.],[0.,1.],[0.,0.]])
eps=1e-10
def caloric(T):
    a=np.where((T>=coefficients[:,0])[:,None],coefficients[:,1:8],coefficients[:,8:15])
    u=R*((a[:,0]-1.)*T+a[:,1]*T*T/2.+a[:,2]*T**3/3.+a[:,3]*T**4/4.+a[:,4]*T**5/5.+a[:,5])
    cv=R*(a[:,0]-1.+a[:,1]*T+a[:,2]*T*T+a[:,3]*T**3+a[:,4]*T**4)
    return u,cv
def invert(c,target,guess):
    T=guess
    for _ in range(40):
        u,cv=caloric(T)
        residual=float(c@u-target)
        scale=max(float(abs(c*u).sum()+abs(target)),1.)
        if abs(residual)<=1e-13*scale:return T
        capacity=float(c@cv)
        assert capacity>0 and np.isfinite(capacity)
        T-=residual/capacity
        assert 90<T<10000,T
    raise RuntimeError('Independent caloric inversion did not converge')
def fraction(c,exponent):
    return c*(max(c,0.)+eps)**(exponent-1.)
def rates(c,T):
    q1=19922349.2590608*np.exp(-15096.586004963/T)*fraction(c[0],.25)*max(c[1],0.)**1.5
    q2=12589254117.9417*np.exp(-20128.7813399506/T)*c[2]*fraction(c[1],.25)*fraction(c[3],.5)
    q3=5e8*np.exp(-20128.7813399506/T)*c[4]
    return np.array([q1,q2-q3])

samples={}
sources=[]
def add(step,prior,after):
    before,following=groups[step][prior],groups[step][after]
    if (before['i'],before['j'])!=(following['i'],following['j']):return
    samples[f'{case.name}__{step}_{after}']={'case':str(case),'before':before,
                                          'recorded_after':following,'duration_s':before['dt_s']/2.}
for case in args.cases:
    assert int((case/'exit_code').read_text().strip())==0
    raw=(case/'thermal_stages.csv').read_bytes()
    sources.append({'case':str(case),'csv_sha256':hashlib.sha256(raw).hexdigest()})
    rows=[{k:v if k in ['stage','point'] else float(v) for k,v in row.items()}
          for row in csv.DictReader(raw.decode().splitlines()) if row['point']=='maximum']
    groups={}
    for row in rows:groups.setdefault(int(row['step']),{})[row['stage']]=row
    first=next((row for row in rows if row['cells_above_fit_upper']>0),None)
    peak=max(rows,key=lambda x:x['T_K'])
    selected_steps=[int(peak['step']),max(groups)]
    if first:selected_steps.append(int(first['step']))
    for step in selected_steps:
        add(step,'before','chemistry_1');add(step,'transport_and_spray','chemistry_2')
    for prior,after in [('before','chemistry_1'),('transport_and_spray','chemistry_2')]:
        candidates=[step for step,g in groups.items() if g[prior]['time_start_s']>=48e-6
                    and g[after]['T_K']>4500 and (g[prior]['i'],g[prior]['j'])==(g[after]['i'],g[after]['j'])]
        if candidates:
            step=max(candidates,key=lambda s:groups[s][after]['T_K']-groups[s][prior]['T_K'])
            add(step,prior,after)
(out/'sampled_states.json').write_text(json.dumps(samples,indent=2))
levels=[(1e-4,1e-13),(1e-5,1e-14),(1e-6,1e-15),(1e-8,1e-17)]
input_lines=[]
for ident,sample in samples.items():
    row=sample['before']
    for rtol,atol in levels:
        values=[row['T_K'],row['rho_kg_m3'],row['e_internal_J_kg'],sample['duration_s'],rtol,atol,
                *[row['Y_'+n] for n in names]]
        input_lines.append(ident+' '+' '.join(format(x,'.17g') for x in values))
native_input='\n'.join(input_lines)+'\n'
(out/'native_inputs.txt').write_text(native_input)
native=subprocess.run([str(out/'probe')],input=native_input,capture_output=True,text=True,timeout=60)
(out/'native_outputs.txt').write_text(native.stdout)
(out/'native_stderr.txt').write_text(native.stderr)
assert native.returncode==0,native.stderr
native_results={}
for line in native.stdout.splitlines():
    parts=line.split();numbers=list(map(float,parts[1:]));assert len(numbers)==15,numbers
    native_results.setdefault(parts[0],[]).append({'rtol':numbers[0],'atol_y':numbers[1],
        'success':bool(numbers[2]),'T_polynomial_K':numbers[3],'T_flow_inverse_K':numbers[4],
        'Y':numbers[5:11],'energy_residual_J_m3':numbers[11],
        'accepted_steps':int(numbers[12]),'rejected_steps':int(numbers[13]),'flow_inverse_range_flag':int(numbers[14])})

results={}
for ident,sample in samples.items():
    row=sample['before'];mass=row['rho_kg_m3']*1000.;target=row['rho_kg_m3']*row['e_internal_J_kg']
    initial_Y=np.array([row['Y_'+n] for n in names]);c0=mass*initial_Y/mw
    def rhs(t,extent):
        c=c0+nu@extent;T=invert(c,target,row['T_K']);return rates(c,T)
    references=[]
    for rtol,atol in [(1e-10,1e-14),(1e-12,1e-16)]:
        start=time.monotonic()
        solution=solve_ivp(rhs,(0.,sample['duration_s']),np.zeros(2),method='Radau',rtol=rtol,atol=atol,
                           first_step=sample['duration_s']/1000.,max_step=sample['duration_s']/4.)
        assert solution.success,solution.message
        c=c0+nu@solution.y[:,-1];T=invert(c,target,row['T_K']);Y=c*mw/mass
        u_edge,cv_edge=caloric(5000.)
        T_flow=5000.+(target-c@u_edge)/(c@cv_edge) if target>c@u_edge else T
        references.append({'rtol':rtol,'atol_extent_mol_m3':atol,'T_polynomial_K':T,
            'T_flow_inverse_K':float(T_flow),'Y':Y.tolist(),'minimum_Y':float(Y.min()),
            'mass_fraction_sum_error':float(Y.sum()-1.),'nfev':solution.nfev,
            'elapsed_s':time.monotonic()-start})
    reference=references[-1]
    convergence={'temperature_difference_K':abs(reference['T_flow_inverse_K']-references[0]['T_flow_inverse_K']),
        'max_Y_difference':float(np.max(abs(np.array(reference['Y'])-references[0]['Y'])))}
    assert convergence['temperature_difference_K']<.01 and convergence['max_Y_difference']<1e-8,convergence
    assert reference['minimum_Y']>=-1e-12 and abs(reference['mass_fraction_sum_error'])<1e-9,reference
    for result in native_results[ident]:
        if not result['success']:
            result['endpoint_accuracy_not_evaluated']='Native integration did not complete; state is partial.'
            continue
        result['T_difference_from_reference_K']=result['T_flow_inverse_K']-reference['T_flow_inverse_K']
        result['max_Y_difference_from_reference']=float(np.max(abs(np.array(result['Y'])-reference['Y'])))
        result['T_difference_from_recorded_flow_stage_K']=result['T_flow_inverse_K']-sample['recorded_after']['T_K']
    results[ident]={'reference_runs':references,'reference_convergence':convergence,'native_runs':native_results[ident]}
summary={'reference_method':'Independent SciPy Radau integration of two stoichiometric extents; NASA7 caloric inversion implemented separately from native C++.',
    'mechanism_sha256':hashlib.sha256(mechanism.read_bytes()).hexdigest(),
    'sources':sources,
    'probe_source_sha256':hashlib.sha256((b/'probe_thermal_chemistry.cpp').read_bytes()).hexdigest(),
    'probe_binary_sha256':hashlib.sha256((out/'probe').read_bytes()).hexdigest(),
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'species':names,'concentration_regularization_mol_m3':eps,'results':results,
    'interpretation':'Numerical chemistry verification at recorded high-temperature states of the active WD6 model. Does not validate extrapolated thermodynamics, high-temperature kinetic completeness, wall physics, or the full coupled trajectory.'}
(out/'validation.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
