"""Archive final evidence with native plotfile hashes; preserve previous archive."""
from pathlib import Path
import hashlib,json,platform,subprocess,zipfile
import cantera,numpy,scipy
b=Path(__file__).resolve().parent;scratch=Path('/dev/shm/my_pele_znd_20260912');archive=scratch/'znd_evidence_final_v2.zip'
names=['planar_600_cfl20_v1','planar_1200_cfl20_v1','planar_2400_cfl20_v1','planar_1200_cfl10_v1']
records=[]
for name in names:
 assert int((b/name/'exit_code').read_text())==0
 for p in sorted((scratch/name).rglob('*')):
  if p.is_file():records.append({'path':str(Path('native_plotfiles')/name/p.relative_to(scratch/name)),'source':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(b/'native_plotfile_manifest.json').write_text(json.dumps(records,indent=2))
(b/'runtime_versions.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'cantera':cantera.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__,'MPI':subprocess.check_output(['mpirun','--version'],text=True).strip()},indent=2))
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(b.rglob('*')):
  if p.is_file() and not any(v in p.parts for v in ['analysis_partial','results_partial','__pycache__']) and p.name not in ['finalizer_status.json','archive_info.json']:
   z.write(p,str(Path('evidence')/p.relative_to(b)))
 for record in records:z.write(record['source'],record['path'])
with zipfile.ZipFile(archive) as z:
 bad=z.testzip();assert bad is None,bad;count=len(z.infolist());assert len(set(z.namelist()))==count
info={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'entries':count,'native_files':len(records),'CRC_check':'passed','report':'evidence/ZND验证报告.md','result':'Completed short-duration verification; fuel half-consumption length criterion failed. Other reported targets met; no claim of full solver validation.'}
(b/'archive_info.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))

