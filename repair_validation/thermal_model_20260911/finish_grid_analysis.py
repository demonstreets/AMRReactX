"""Bounded postprocessing for the one explicitly launched diagnostic trial."""
from pathlib import Path
import time,json,subprocess,hashlib
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';d=b/'fine_main_depth_v2';scratch=Path('/dev/shm/my_pele_thermal_model_20260911/fine_main_depth_v2');deadline=time.monotonic()+7200
while not (d/'exit_code').exists():
 if time.monotonic()>deadline:raise TimeoutError('Postprocessing wait exceeded 2 hours; no solver action taken')
 time.sleep(30)
assert int((d/'exit_code').read_text())==0
p=subprocess.run(['python3',str(b/'analyze_grid_histories.py')],capture_output=True,text=True);(b/'grid_history_final_v1.log').write_text(p.stdout+p.stderr);assert p.returncode==0
plots=sorted(scratch.glob('plt[0-9]*'));assert len(plots)>=2
last=plots[-1];lines=(last/'Header').read_text().splitlines();n=int(lines[1]);assert abs(float(lines[3+n])-5e-5)<1e-14
if not (scratch/'inputs').exists():(scratch/'inputs').symlink_to(d/'inputs')
source=r/'repair_validation/thermal_20260911/replay_cfl20_v1';coarse=sorted(source.glob('plt[0-9]*'))[-1]
script=(r/'repair_validation/thermal_20260911/analyze_hotspot_fields.py').read_text().replace("'Replay CFL 0.2'","'Reference 0.05 mm'").replace("'replay_cfl10_v1':", "'fine_main_depth_v2': 'Refined 0.025 mm', 'replay_cfl10_v1':")
custom=b/'analyze_grid_final_fields.py';custom.write_text(script)
p=subprocess.run(['python3',str(custom),str(coarse),str(last),'--output',str(b/'grid_final_fields_v1')],capture_output=True,text=True);(b/'grid_final_fields_v1.log').write_text(p.stdout+p.stderr);assert p.returncode==0
manifest=[]
for plot in plots:
 for p in sorted(plot.rglob('*')):
  if p.is_file():
   h=hashlib.sha256()
   with p.open('rb') as f:
    while chunk:=f.read(8*1024*1024):h.update(chunk)
   manifest.append({'path':str(p.relative_to(scratch)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
(b/'fine_native_plot_manifest.json').write_text(json.dumps(manifest,indent=2));(b/'grid_postprocessing_status.json').write_text(json.dumps({'state':'complete','final_plot':str(last),'plot_count':len(plots),'raw_files':len(manifest)},indent=2));print('complete',last,flush=True)
