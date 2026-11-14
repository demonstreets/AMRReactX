"""Finish bounded snapshot diagnostics and preserve native outputs after the run."""
from pathlib import Path
import time,subprocess,tarfile,hashlib,json,shutil
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';scratch=Path('/dev/shm/my_pele_thermal_model_20260911/fine_main_depth_v2');deadline=time.monotonic()+7200
state=b/'native_archive_progress.json'
def status(phase,**extra):state.write_text(json.dumps({'phase':phase,**extra},indent=2))
status('waiting_for_grid_postprocessing')
while not (b/'grid_postprocessing_status.json').exists():
 if time.monotonic()>deadline:raise TimeoutError('No completed grid postprocessing within 2 hours; no solver action taken')
 time.sleep(30)
assert json.loads((b/'grid_postprocessing_status.json').read_text())['state']=='complete'
status('snapshot_metrics')
p=subprocess.run(['python3',str(b/'analyze_grid_snapshot_metrics.py')],capture_output=True,text=True);(b/'grid_snapshot_metrics_v1.log').write_text(p.stdout+p.stderr);assert p.returncode==0
archive=scratch.parent/'fine_main_depth_v2_native_v1.tar.gz';assert not archive.exists();manifest=json.loads((b/'fine_native_plot_manifest.json').read_text());expected={q['path']:q['sha256'] for q in manifest}
status('compressing_native_outputs',raw_bytes=sum(q['bytes'] for q in manifest))
with tarfile.open(archive,'w:gz',compresslevel=3) as tar:
 for p in sorted(scratch.glob('plt[0-9]*')):tar.add(p,arcname=p.name)
 tar.add(b/'fine_native_plot_manifest.json',arcname='native_manifest.json');tar.add(b/'fine_main_depth_v2/inputs',arcname='inputs')
status('verifying_archive_contents',archive_bytes=archive.stat().st_size)
checked=[]
with tarfile.open(archive,'r:gz') as tar:
 for member in tar:
  if not member.isfile() or member.name not in expected:continue
  h=hashlib.sha256();f=tar.extractfile(member)
  while chunk:=f.read(8*1024*1024):h.update(chunk)
  assert h.hexdigest()==expected[member.name],member.name;checked.append(member.name)
assert set(checked)==set(expected)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while chunk:=f.read(8*1024*1024):h.update(chunk)
 return h.hexdigest()
sha=digest(archive);free=shutil.disk_usage(b).free;persistent=None
if free>archive.stat().st_size+512*1024*1024:
 target=b/archive.name;assert not target.exists();status('copying_to_persistent_disk',archive_bytes=archive.stat().st_size)
 shutil.copyfile(archive,target);assert digest(target)==sha;persistent=str(target)
result={'state':'verified','archive_sha256':sha,'archive_bytes':archive.stat().st_size,'verified_native_files':len(checked),'persistent_archive':persistent,'ram_archive':str(archive),'persistent_free_bytes_before_copy':free,'scope':'All saved native gas and particle plotfiles from the corrected-depth refined run. The restart checkpoint can be recreated from the preserved coarse checkpoint and audited refinement scripts.'}
(b/'fine_native_archive_v1.json').write_text(json.dumps(result,indent=2));status('complete',**result);print(json.dumps(result,indent=2),flush=True)
