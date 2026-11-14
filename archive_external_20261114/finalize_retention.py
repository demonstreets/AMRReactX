from pathlib import Path
import json,time,os
b=Path('/home/cj/my-pele/archive_external_20261114')
while not (b/'COMPLETE.json').exists():
 if (b/'FAILED.json').exists():raise RuntimeError('Archive failed; no deletion performed')
 time.sleep(15)
rows=json.loads((b/'retention_omissions.json').read_text()); allowed=[Path('/dev/shm/my_pele_hydrogen_znd_20260913'),Path('/dev/shm/my_pele_znd_20260912'),Path('/dev/shm/my_pele_thermal_model_20260911'),Path('/run/user/1001/amrreactx_hydrogen_verification_20260914')]
report=b/'03_review_results'/'retention_report.md'
report.write_text('# Result retention\n\nFull preserved-file verification completed before deletion.\nSupported overdriven 4 us case: keep first and last native plotfiles.\nNear-CJ waveframe v1/v2: validation not achieved; keep configuration, logs and analyses, omit native failed fields.\nNonzero-exit cases: execution failed; keep original exit codes and logs.\nUnclassified cases: preserved without assuming physical PASS.\n\nSee retention_omissions.json for every omitted source field.\n')
removed=[]
for row in rows:
 p=Path(row['source'])
 if not any(r in p.parents for r in allowed):raise RuntimeError('Outside authorized roots')
 if p.is_symlink():continue
 if p.is_file():
  n=p.stat().st_size;p.unlink();removed.append({'path':str(p),'bytes':n,'reason':row['reason']})
(b/'deletion_receipt.json').write_text(json.dumps({'removed_files':len(removed),'removed_bytes':sum(x['bytes'] for x in removed),'files':removed},indent=2))
(b/'RETENTION_COMPLETE.json').write_text(json.dumps({'status':'complete','removed_files':len(removed)}))
