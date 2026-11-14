from pathlib import Path
import hashlib,json,zipfile,sys,platform
import cantera,numpy,scipy,matplotlib
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';prior=r/'repair_validation/thermal_20260911'
assert int((b/'fine_main_depth_v2/exit_code').read_text())==0
assert json.loads((b/'fine_native_archive_v1.json').read_text())['state']=='verified'
assert (b/'grid_final_fields_v1/global_peaks.png').is_file()
assert (b/'fine_hot_chemistry_final_v1/summary.json').is_file()
selected={}
def add(p,name=None):
 assert p.is_file(),p
 selected[name or str(p.relative_to(b))]=p.read_bytes()
folders=['burned_gas_finite_rate_v3','burned_gas_kinetic_sensitivity_v1','kinetic_comparison_v1','external_mechanism_screen_v1','fine_first_chemistry_validation_v1','fine_hot_chemistry_final_v1','grid_history_final_v1','grid_final_fields_v1','grid_snapshot_metrics_v1','tool_history']
for folder in folders:
 for p in sorted((b/folder).rglob('*')):
  if p.is_file() and (p.suffix in ['.json','.yaml','.csv','.png','.txt','.log','.py']):add(p)
for folder in ['native_smoke_v1','roundtrip_smoke_v1','fine_smoke_v1','fine_smoke_depth_v2','fine_main_v1','fine_main_depth_v2']:
 for name in ['inputs','case.json','launcher.json','exit_code','termination.json','thermal_stages.csv','run.log']:
  p=b/folder/name
  if p.is_file():add(p)
for p in sorted(b.iterdir()):
 if p.is_file() and p.suffix in ['.py','.cpp','.json','.log','.exit_code'] and p.name not in ['evidence_manifest.json','native_archive_progress.json']:
  add(p,('reproduction_scripts/' if p.suffix in ['.py','.cpp'] else '')+p.name)
for name in ['inputs','case.json','launcher.json','exit_code','thermal_stages.csv','run.log']:
 add(prior/'replay_cfl20_v1'/name,'reference/replay_cfl20_v1/'+name)
for name in ['conservative_original_and_baseline_peak_states_v2.json','probe_thermal_chemistry.cpp','validate_hot_cell_chemistry.py']:
 add(prior/name,'reference/'+name)
for name in ['external/PeleC/Source/Advance.cpp','external/PeleC/Source/StrangThermalDiagnostics.H','src/academic/chemistry/Wd6Rosenbrock.H','external/PeleC/Submodules/PelePhysics/Source/Spray/SprayParticles.cpp','external/PeleC/Submodules/PelePhysics/Source/Spray/SprayDerive.cpp','external/PeleC/Submodules/PelePhysics/Source/Spray/SprayIO.cpp']:
 add(r/name,'source/'+name)
for mechanism in ['heptane_wd6','heptane_lu_88sk','heptane_fc']:
 add(r/'external/PelePhysics/Mechanisms'/mechanism/'mechanism.yaml','source/mechanisms/'+mechanism+'.yaml')
for name in ['gri30_highT.yaml','nasa_gas.yaml']:
 p=next(Path(folder)/name for folder in cantera.get_data_directories() if (Path(folder)/name).is_file());add(p,'source/cantera/'+name)
runtime={'python':sys.version,'platform':platform.platform(),'cantera':cantera.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}
selected['runtime_versions.json']=json.dumps(runtime,indent=2).encode()
manifest={'remote_root':str(b),'scope':'Completed corrected-depth short-interval refinement, burned-gas network sensitivity, first-crossing independent integration, and explicitly invalidated early trials. Large native fields are kept in the separate verified native archive.','files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sorted(selected.items())}}
(b/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2));archive=b/'model_evidence_v1.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,data in sorted(selected.items()):z.writestr(name,data)
 z.writestr('evidence_manifest.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,data in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==data['sha256']
print(json.dumps({'archive':str(archive),'files':len(selected),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))
