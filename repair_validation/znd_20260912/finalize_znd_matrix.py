"""Analyze completed bounded cases, preserve evidence, and exit."""
from pathlib import Path
import json,subprocess,time,shutil,hashlib,zipfile
b=Path(__file__).resolve().parent;r=Path('/home/cj/my-pele')
names=['planar_600_cfl20_v1','planar_1200_cfl20_v1','planar_2400_cfl20_v1','planar_1200_cfl10_v1']
done=set();deadline=time.monotonic()+3*3600
while len(done)<len(names):
 assert time.monotonic()<deadline,'deadline exceeded'
 for name in names:
  if name in done or not (b/name/'exit_code').exists():continue
  code=int((b/name/'exit_code').read_text());assert code==0,(name,code)
  subprocess.run(['python3',str(b/'analyze_znd_case.py'),name],check=True)
  done.add(name)
 (b/'finalizer_status.json').write_text(json.dumps({'state':'analyzing','completed':sorted(done)}))
 if len(done)<len(names):time.sleep(30)
subprocess.run(['python3',str(b/'aggregate_znd.py')],check=True)
sourcefiles=['examples/academic/spray_detonation/prob.H','examples/academic/spray_detonation/prob.cpp','examples/academic/spray_detonation/prob_parm.H','external/PeleC/Source/Advance.cpp','external/PeleC/Source/React.cpp','external/PeleC/Source/Setup.cpp','external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.H','external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml','tools/amrex_reader.py']
records=[]
for file in sourcefiles:
 src=r/file;dst=b/'source_snapshot'/file;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 records.append({'path':file,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'bytes':src.stat().st_size})
(b/'source_snapshot/manifest.json').write_text(json.dumps(records,indent=2))
scratch=Path('/dev/shm/my_pele_znd_20260912');archive=scratch/'znd_evidence_v1.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(b.rglob('*')):
  if p.is_file() and not any(v in p.parts for v in ['analysis_partial','results_partial','__pycache__']) and p.name not in ['finalizer_status.json','finalizer.log']:
   z.write(p,str(Path('evidence')/p.relative_to(b)))
 for name in names:
  for p in sorted((scratch/name).rglob('*')):
   if p.is_file():z.write(p,str(Path('native_plotfiles')/name/p.relative_to(scratch/name)))
record={'state':'complete','cases':names,'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(b/'finalizer_status.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)

