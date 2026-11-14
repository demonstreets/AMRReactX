from pathlib import Path
import time,subprocess,json
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';d=b/'fine_main_depth_v2';out=b/'fine_hot_chemistry_final_v1';deadline=time.monotonic()+7200
while not (d/'exit_code').exists():
 if time.monotonic()>deadline:raise TimeoutError('No completed refined run within 2 hours')
 time.sleep(30)
assert int((d/'exit_code').read_text())==0
cmd=['python3',str(r/'repair_validation/thermal_20260911/validate_hot_cell_chemistry.py'),str(d),'--output',str(out)]
p=subprocess.run(cmd,capture_output=True,text=True);(b/'fine_hot_chemistry_final_v1.log').write_text(p.stdout+p.stderr);assert p.returncode==0
q=json.loads((out/'validation.json').read_text());summary={'samples':[],'source_method':'Independent two-extent Radau with the active WD6 thermodynamics and native temperature inversion convention.'}
for name,result in q['results'].items():
 run=next(z for z in result['native_runs'] if z['rtol']==1e-5)
 point={'name':name,'reference_convergence':result['reference_convergence'],'default_native':run,'failed_tolerances':[z['rtol'] for z in result['native_runs'] if not z['success']]}
 if run['success']:point['recorded_flow_minus_reference_K']=run['T_difference_from_reference_K']-run['T_difference_from_recorded_flow_stage_K']
 summary['samples'].append(point)
summary['passed_default']=bool(summary['samples'] and all(s['default_native']['success'] and abs(s['default_native']['T_difference_from_reference_K'])<.05 and abs(s['recorded_flow_minus_reference_K'])<.05 for s in summary['samples']))
summary['sample_count']=len(summary['samples']);summary['max_default_native_T_error_K']=max(abs(s['default_native'].get('T_difference_from_reference_K',float('inf'))) for s in summary['samples']);summary['max_recorded_flow_T_error_K']=max(abs(s.get('recorded_flow_minus_reference_K',float('inf'))) for s in summary['samples'])
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
