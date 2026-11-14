"""Rebase legacy runtime paths after copying the package. Default is dry-run.

Run python3 tools/relocate_legacy_paths.py --apply from any working directory.
Only known package-root prefixes are rewritten; scientific settings and evidence
documents are not rewritten. External datasets/toolchains remain explicit inputs.
"""
import argparse
import json
from pathlib import Path
import re

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    state=root/'.portable-root.json'
    previous=json.loads(state.read_text())['root'] if state.exists() else '/home/cj/my-pele'
    old_roots=sorted(set([previous,'/home/cj/my-pele']),key=len,reverse=True)
    changes=[]; external=[]
    exts={'.py','.sh','.cmake','.inp','.yaml','.yml','.toml'}
    # Evidence/report trees retain the exact historic paths for provenance.
    for base in ['tools','scripts','examples','cases','test','src','cmake']:
        for p in (root/base).rglob('*'):
            if not p.is_file() or p.is_symlink() or p==Path(__file__).resolve():continue
            if p.stat().st_size>2_000_000:continue
            if p.suffix not in exts and p.name not in {'GNUmakefile','Makefile','CMakeLists.txt'} and not p.name.startswith(('inputs','input.')):continue
            try:text=p.read_text(encoding='utf-8')
            except UnicodeError:continue
            updated=text
            for old in old_roots:
                if old!=str(root):
                    updated=re.sub(re.escape(old)+r'(?=/|[\s\"\'\)]|$)',lambda _:str(root),updated)
            if updated!=text:
                changes.append(str(p.relative_to(root)))
                if args.apply:p.write_text(updated,encoding='utf-8')
            for value in re.findall(r'/(?:home|dev/shm|run/user|opt)/[^\s\"\'<>;,)]+',updated):
                if not value.startswith(str(root)+'/') and value!=str(root):
                    external.append({'file':str(p.relative_to(root)),'reference':value})
    report={'root':str(root),'previous_root':previous,'applied':args.apply,'changed_files':changes,'external_references':external}
    if args.apply:
        state.write_text(json.dumps({'root':str(root)},indent=2))
        (root/'docs/portability/legacy_path_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'applied':args.apply,'changed_files':len(changes),'external_references':len(external)}))

if __name__=='__main__':main()
