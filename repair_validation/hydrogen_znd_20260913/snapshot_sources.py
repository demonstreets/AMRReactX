from pathlib import Path
import shutil,hashlib,json,subprocess
r=Path('/home/cj/my-pele');b=r/'repair_validation/hydrogen_znd_20260913';out=b/'source_snapshot';out.mkdir(exist_ok=True)
paths=[r/'tools/amrex_reader.py',r/'external/PeleC/Source/Advance.cpp',r/'external/PeleC/Source/React.cpp']
for root in [r/'external/PeleC/Submodules/PelePhysics/Mechanisms/LiDryer',r/'external/PeleC/Submodules/PelePhysics/Source/Reactions',r/'src/academic/chemistry']:
 paths.extend(p for p in root.rglob('*') if p.is_file() and p.suffix in ['.H','.cpp','.yaml','.h','.mk'])
records=[]
for p in paths:
 if not p.is_file():continue
 rel=p.relative_to(r);q=out/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);records.append({'path':str(rel),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(b/'source_manifest.json').write_text(json.dumps(records,indent=2));print('source files',len(records),'bytes',sum(x['bytes'] for x in records))
rev={}
for name,path in [('my-pele',r),('PeleC',r/'external/PeleC'),('PelePhysics',r/'external/PeleC/Submodules/PelePhysics'),('AMReX',r/'external/PeleC/Submodules/PelePhysics/Submodules/amrex')]:
 q=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],capture_output=True,text=True);rev[name]={'HEAD':q.stdout.strip(),'exit':q.returncode};d=subprocess.run(['git','-C',str(path),'status','--short','--untracked-files=no'],capture_output=True,text=True);rev[name]['tracked_status']=d.stdout
(b/'git_revisions.json').write_text(json.dumps(rev,indent=2));print(json.dumps(rev,indent=2)[:4000])