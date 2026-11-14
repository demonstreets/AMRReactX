"""Restore large losslessly compressed case inputs and verify content hashes."""
from pathlib import Path
import gzip,hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
for entry in json.loads((R/'docs/portability/compressed_inputs.json').read_text()):
    dest=R/entry['path'];src=R/entry['gzip']
    assert dest.resolve().is_relative_to(R)
    if dest.exists() and hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()==entry['sha256']:continue
    temp=dest.with_name(dest.name+'.restoring')
    with gzip.open(src,'rb') as inp,temp.open('wb') as out:shutil.copyfileobj(inp,out)
    with temp.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==entry['sha256']
    temp.replace(dest)
print('PASS: portable input files restored and verified')
