"""Archive diagnostics, exact input/log evidence and all new probe plotfiles."""
from pathlib import Path
import json,hashlib,zipfile
b=Path(__file__).resolve().parent;root=b.parent
scratch=Path('/dev/shm/my_pele_hydrogen_znd_20260913/width_diagnostics')
archive=scratch/'hydrogen_width_diagnostics_v1.zip'
for name in ['hydro_only_2400_v2','hydro_only_9600_v2','chemistry_only_v1']:
    assert int((b/name/'exit_code').read_text())==0
source={'original_ZND_evidence_archive':json.loads((root/'archive_info.json').read_text()),
        'original_case_input_hashes':{p.parent.name:json.loads(p.read_text())['input_sha256'] for p in root.glob('hydrogen_*/case.json')},
        'note':'The four original 4-us reacting CFD plotfile sets are preserved in the original archive; this addendum includes their extracted profiles plus all new isolated-probe plotfiles.'}
(b/'source_evidence.json').write_text(json.dumps(source,indent=2))
records=[]
for folder in sorted(scratch.iterdir()):
    if not folder.is_dir():continue
    for p in sorted(folder.rglob('*')):
        if p.is_file():records.append({'path':str(Path('native_probe_plotfiles')/p.relative_to(scratch)),
                                       'source':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(b/'native_probe_manifest.json').write_text(json.dumps(records,indent=2))
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(b.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.name!='archive_info.json':z.write(p,str(Path('evidence')/p.relative_to(b)))
    for r in records:z.write(r['source'],r['path'])
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    count=len(z.infolist());assert len(set(z.namelist()))==count
info={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
      'entries':count,'native_probe_files':len(records),'CRC_check':'passed'}
(b/'archive_info.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
