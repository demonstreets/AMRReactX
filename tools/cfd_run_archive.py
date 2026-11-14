#!/usr/bin/env python3
"""Archive complete CFD evidence and fingerprint actual source trees.

No cleanup or overwrite mode is provided. Hash verification and physical
validation are separate: an intact archive is not a physically valid run.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import platform
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_child(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'path escapes artifact root: {relative}')
    return path


def binary_references(header):
    header = Path(header)
    refs = re.findall(r'FabOnDisk:\s+(\S+)\s+(\d+)', header.read_text(errors='strict'))
    if not refs:
        raise ValueError(f'no binary FAB references in {header}')
    files = []
    for name, offset in refs:
        path = safe_child(header.parent, name)
        if not path.is_file() or path.stat().st_size <= int(offset):
            raise ValueError(f'missing/truncated FAB payload: {path} offset={offset}')
        files.append(path)
    return files


def check_plotfile(plot):
    import amrex_reader
    import numpy as np
    plot = Path(plot)
    header = plot / 'Header'
    lines = [line.strip() for line in header.read_text().splitlines() if line.strip()]
    ncomp = int(lines[1])
    ndim, time, finest = int(lines[ncomp + 2]), float(lines[ncomp + 3]), int(lines[ncomp + 4])
    if ncomp <= 0 or ndim not in (1, 2, 3) or finest < 0 or not math.isfinite(time):
        raise ValueError(f'invalid plot header: {header}')
    required = {f'Level_{lev}/Cell' for lev in range(finest + 1)}
    if not required.issubset(set(lines)):
        raise ValueError(f'missing level references in {header}')
    payloads = []
    for prefix in sorted(required):
        payloads.extend(binary_references(safe_child(plot, prefix + '_H')))
    meta = amrex_reader._parse_header_structured(str(header))
    nonfinite = 0
    for level in range(finest + 1):
        # Decode payload sizes without imposing a physical PASS on the fields.
        data, grid = amrex_reader._read_level(str(plot), level, ncomp, meta['dx'][level])
        coverage = grid.get('coverage')
        stored = data[coverage] if coverage is not None else data
        nonfinite += int(np.count_nonzero(~np.isfinite(stored)))
    return {'time': time, 'ndim': ndim, 'levels': finest + 1,
            'payload_count': len(set(payloads)), 'nonfinite_stored_values': nonfinite,
            'physical_validation': 'not_performed'}


def git_metadata(path, repo):
    def query(*args):
        try:
            p = subprocess.run(['git', '-C', str(path), *args], capture_output=True, text=True)
        except OSError:
            return None
        return p.stdout.strip() if p.returncode == 0 else None
    top = query('rev-parse', '--show-toplevel')
    return {'repository_root': top, 'parent_commit': query('rev-parse', 'HEAD'),
            'source_kind': 'vendored_in_parent_repository' if top and Path(top).resolve() == repo
                           else 'independent_repository' if top else 'unversioned_source',
            'upstream_commit_verified': False}


def source_fingerprint(repo, roots):
    repo = Path(repo).resolve()
    result = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'repository': str(repo), 'source_trees': []}
    for relative in roots:
        root = safe_child(repo, relative)
        if not root.exists():
            raise ValueError(f'missing source root: {root}')
        paths = [root] if root.is_file() else sorted(root.rglob('*'))
        entries = []
        for p in paths:
            if any(part in ('.git', '__pycache__', 'tmp_build_dir') or part.startswith('build-')
                   for part in p.relative_to(root.parent).parts):
                continue
            if p.is_symlink():
                raise ValueError(f'source snapshot requires explicit resolved roots, not symlinks: {p}')
            if p.is_file() and p.suffix not in ('.o', '.a', '.so', '.ex', '.pyc', '.log'):
                entries.append({'path': p.relative_to(repo).as_posix(),
                                'size_bytes': p.stat().st_size, 'sha256': sha256(p)})
        digest = hashlib.sha256(''.join(item['path'] + '\0' + item['sha256'] + '\n'
                                        for item in entries).encode()).hexdigest()
        result['source_trees'].append({'path': str(relative), 'tree_sha256': digest,
                                      'files': entries, 'version': git_metadata(root if root.is_dir() else root.parent, repo)})
    return result


def verify_archive(directory):
    directory = Path(directory).resolve()
    report = json.loads((directory / 'archive_manifest.json').read_text())
    for item in report['files']:
        p = safe_child(directory, item['path'])
        if not p.is_file() or p.stat().st_size != item['size_bytes'] or sha256(p) != item['sha256']:
            raise ValueError(f'archive integrity mismatch: {p}')
    for relative in report['plotfiles']:
        check_plotfile(safe_child(directory, relative))
    return report


def archive_run(run, output, repo, executable, source_manifest=None):
    run, output, repo, executable = (Path(p).resolve() for p in (run, output, repo, executable))
    if output.exists() or output.is_relative_to(run):
        raise ValueError('archive output must be new and outside the run directory')
    plots = sorted(p for p in run.iterdir() if p.is_dir() and re.fullmatch(r'plt\d+', p.name))
    if not plots:
        raise ValueError('run has no plotfiles to archive')
    checked = {p.name: check_plotfile(p) for p in plots}
    # Check every checkpoint FAB header too; do not archive Header-only checkpoints.
    for checkpoint in run.glob('chk[0-9]*'):
        headers = list(checkpoint.glob('Level_*/*_H'))
        if checkpoint.is_dir() and not headers:
            raise ValueError(f'checkpoint has no binary FAB headers: {checkpoint}')
        for header in headers:
            binary_references(header)
    if not executable.is_file():
        raise ValueError(f'executable missing: {executable}')
    before = {p.relative_to(run).as_posix(): sha256(p) for p in run.rglob('*') if p.is_file()}
    if any(p.is_symlink() for p in run.rglob('*')):
        raise ValueError('portable run archive cannot contain symlinks')
    expected_sources = None
    if source_manifest:
        expected_sources = json.loads(Path(source_manifest).read_text())
        for tree in expected_sources['source_trees']:
            for item in tree['files']:
                p = safe_child(repo, item['path'])
                if not p.is_file() or sha256(p) != item['sha256']:
                    raise ValueError(f'source changed since pre-build manifest: {p}')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(run, output / 'run')
    (output / 'binary').mkdir()
    shutil.copy2(executable, output / 'binary' / executable.name)
    for name, digest in before.items():
        if sha256(safe_child(output / 'run', name)) != digest or sha256(safe_child(run, name)) != digest:
            raise ValueError(f'run changed during archive: {name}; incomplete archive retained at {output}')
    if expected_sources:
        for tree in expected_sources['source_trees']:
            for item in tree['files']:
                destination = safe_child(output / 'source_snapshot', item['path'])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(safe_child(repo, item['path']), destination)
                if sha256(destination) != item['sha256']:
                    raise ValueError(f'source changed during archive: {item["path"]}')
        (output / 'source_manifest.json').write_text(json.dumps(expected_sources, indent=2))
    files = [{'path': p.relative_to(output).as_posix(), 'size_bytes': p.stat().st_size,
              'sha256': sha256(p)} for p in sorted(output.rglob('*')) if p.is_file()]
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'platform': platform.platform(), 'source_run': str(run),
              'executable_sha256': sha256(executable), 'files': files,
              'plotfiles': {'run/' + name: info for name, info in checked.items()},
              'source_snapshot_present': expected_sources is not None,
              'physical_acceptance': 'not_granted_by_archive_integrity'}
    (output / 'archive_manifest.json').write_text(json.dumps(report, indent=2))
    verify_archive(output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    source = sub.add_parser('sources')
    source.add_argument('--repo', type=Path, required=True)
    source.add_argument('--source-root', action='append', required=True)
    source.add_argument('--output', type=Path, required=True)
    archive = sub.add_parser('archive')
    for name in ('run', 'output', 'repo', 'executable'):
        archive.add_argument('--' + name, type=Path, required=True)
    archive.add_argument('--source-manifest', type=Path)
    verify = sub.add_parser('verify')
    verify.add_argument('directory', type=Path)
    args = parser.parse_args()
    if args.action == 'sources':
        report = source_fingerprint(args.repo, args.source_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2)
    elif args.action == 'archive':
        archive_run(args.run, args.output, args.repo, args.executable, args.source_manifest)
    else:
        verify_archive(args.directory)
    print('PASS archive/source integrity only; physical acceptance requires separate validation')


if __name__ == '__main__':
    main()
