from pathlib import Path
import os,tarfile,hashlib,json,time,shutil
base=Path('/home/cj/my-pele/archive_external_20261114')
roots=[Path('/dev/shm/my_pele_hydrogen_znd_20260913'),Path('/dev/shm/my_pele_znd_20260912'),Path('/dev/shm/my_pele_thermal_model_20260911'),Path('/run/user/1001/amrreactx_hydrogen_verification_20260914')]
def digest(f):
 h=hashlib.sha256()
 while True:
  b=f.read(4*1024*1024)
  if not b:break
  h.update(b)
 return h.hexdigest()
def category(p):
 parts=[x.lower() for x in p.parts]
 if any(x in ('analysis','analysis_partial','results','results_partial','figures','evidence') for x in parts):return '03_review_results'
 if any(x.startswith(('build','source_snapshot','pelec_')) or x in ('vendor','dependencies','frame_build_source','delivery_patch') for x in parts):return '01_program_sources_and_builds'
 if p.suffix.lower() in ('.py','.sh','.h','.cpp','.c','.cmake') or p.name in ('GNUmakefile','Make.package'):return '01_program_sources_and_builds'
 return '02_test_cases'
try:
 manifest=[]; counts={}; links=[]; omissions=[]
 for root in roots:
  label=root.name+('_run' if str(root).startswith('/run') else '_shm')
  groups={}
  for dp,ds,fs in os.walk(root,followlinks=False):
   for n in list(ds):
    if (Path(dp)/n).is_symlink(): fs.append(n);ds.remove(n)
   for n in fs:
    p=Path(dp)/n;rel=p.relative_to(root);groups.setdefault(category(rel),[]).append((p,rel))
  # Retention decisions only for explicitly reviewed cases or nonzero exits.
  rejected=set(); passed=set(); fieldsets={}
  for dp,ds,fs in os.walk(root,followlinks=False):
   d=Path(dp)
   if 'exit_code' in fs:
    try:
     if int((d/'exit_code').read_text().strip())!=0:rejected.add(d)
    except ValueError:pass
   if d.name in ('cj_znd_waveframe_40mm_v2','cj_znd_waveframe_40mm_v1'):rejected.add(d)
   if d.name=='supported_overdrive_1p2_fixedbc_4us_v1':passed.add(d)
   plots=sorted([d/x for x in ds if x.startswith('plt') and (d/x/'Header').is_file()])
   if plots:fieldsets[d]=plots
  excluded=[]
  for d,plots in fieldsets.items():
   owner=next((c for c in rejected|passed if d==c or c in d.parents),None)
   if owner in rejected:excluded+=plots
   elif owner in passed:excluded+=plots[1:-1]
  excluded=set(excluded)
  for cat in groups:
   kept=[]
   for p,rel in groups[cat]:
    reason=next((x for x in p.parents if x in excluded),None)
    if reason:omissions.append({'source':str(p),'reason':'failed case field' if any(c==reason or c in reason.parents for c in rejected) else 'passed case intermediate field'})
    else:kept.append((p,rel))
   groups[cat]=kept
  (base/'retention_omissions.json').write_text(json.dumps(omissions,indent=2))
  for cat,items in groups.items():
   out=base/cat;out.mkdir(exist_ok=True)
   target=out/(label+'.tar.gz'); expected={}
   print('COPY',label,cat,len(items),flush=True)
   with tarfile.open(target,'w:gz',compresslevel=1,dereference=False) as tar:
    for p,rel in items:
     if shutil.disk_usage(base).free<3*1024**3:raise RuntimeError('Less than 3 GiB free; stopped safely')
     st=p.lstat();row={'source':str(p),'archive':str(target.relative_to(base)),'member':str(rel),'bytes':st.st_size}
     if p.is_symlink():row['link']=os.readlink(p);links.append(row)
     elif p.is_file():
      with p.open('rb') as f:row['sha256']=digest(f)
      expected[str(rel)]=row['sha256']
     else:row['skipped']='non-regular';manifest.append(row);continue
     tar.add(p,arcname=str(rel),recursive=False)
     if p.lstat().st_mtime_ns!=st.st_mtime_ns:raise RuntimeError('Source changed: '+str(p))
     manifest.append(row)
   print('VERIFY',target,flush=True)
   with tarfile.open(target,'r:gz') as tar:
    for m in tar:
     if m.isfile():
      assert digest(tar.extractfile(m))==expected.pop(m.name),m.name
   assert not expected
   counts[str(target.relative_to(base))]={'files':len(items),'archive_bytes':target.stat().st_size,'verified':True}
   (base/'manifest.json').write_text(json.dumps(manifest,indent=2))
   (base/'progress.json').write_text(json.dumps(counts,indent=2))
 # Explicit project files in home; exclude account/configuration files.
 dest=base/'04_project_plan_and_home_records';dest.mkdir(exist_ok=True)
 for p in Path('/home/cj').iterdir():
  if p.is_file() and (p.name=='pele_cfd_master_plan.md' or p.name.startswith(('codewhale_','codex_run_h2_','patch_cold_cell','fix_make','fix_cmake','patch_build_cmake','run_cc','run_dc','task_p')) or p.name in ('k_epsilon_fix.png','k_epsilon_decay.png','znd_detonation.png','PASS_FAIL','test_rnnlib.cpp')):
   shutil.copy2(p,dest/p.name)
   with p.open('rb') as f:a=digest(f)
   with (dest/p.name).open('rb') as f:assert digest(f)==a
   manifest.append({'source':str(p),'copy':str((dest/p.name).relative_to(base)),'sha256':a})
 (base/'manifest.json').write_text(json.dumps(manifest,indent=2))
 (base/'symlinks.json').write_text(json.dumps(links,indent=2))
 (base/'README.md').write_text('''# External project archive — 2026-11-14

01_program_sources_and_builds: program sources, build snapshots and analysis tools.
02_test_cases: inputs, references, native fields, logs and runtime records.
03_review_results: analyses, figures and review evidence; preservation does not imply physical validation.
04_project_plan_and_home_records: master plan and project-specific home records.

Original files remain in place. Archive member paths are relative to the source root recorded in manifest.json. Extract all category archives for the same source into one chosen restore directory to reconstruct it. Original symbolic links are preserved and inventoried in symlinks.json; absolute links require remapping when restoring elsewhere. Original inputs/scripts also retain source paths. This is an evidence archive, not a portable rebuilt release.

The active main program remains in /home/cj/my-pele/src and external/{PeleC,PeleLMeX,PelePhysics}. Existing tests remain in examples and repair_validation. This archive adds external material without replacing the active program.

Every regular archived file was SHA256 checked against the original by rereading the compressed archive. See manifest.json and progress.json.
''')
 (base/'COMPLETE.json').write_text(json.dumps({'status':'complete','entries':len(manifest),'archives':counts,'completed_epoch':time.time()},indent=2))
 print('COMPLETE',len(manifest),flush=True)
except Exception as e:
 (base/'FAILED.json').write_text(json.dumps({'error':repr(e)}));raise
