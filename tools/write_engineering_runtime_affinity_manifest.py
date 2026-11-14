#!/usr/bin/env python3
"""Write a lightweight engineering runtime/MPI affinity manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RuntimeManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeManifestError(message)


def sanitize_text(text: str, replacements: list[tuple[str, str]]) -> str:
    out = text
    for old, new in replacements:
        if old:
            out = out.replace(old, new)
    return out


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def run_command(argv: list[str], timeout_s: int, replacements: list[tuple[str, str]]) -> dict[str, Any]:
    start = time.monotonic()
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout_s)
        returncode = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = -1
        stdout = exc.stdout or ''
        stderr = exc.stderr or ''
        timed_out = True
    duration_s = time.monotonic() - start
    stdout = sanitize_text(stdout, replacements)
    stderr = sanitize_text(stderr, replacements)
    return {
        'argv': [sanitize_text(str(item), replacements) for item in argv],
        'returncode': returncode,
        'duration_s': duration_s,
        'timed_out': timed_out,
        'stdout': stdout,
        'stderr': stderr,
        'stdout_sha256': sha256_text(stdout),
        'stderr_sha256': sha256_text(stderr),
    }


def cpu_topology(replacements: list[tuple[str, str]]) -> dict[str, Any]:
    lscpu = shutil.which('lscpu')
    nproc = os.cpu_count() or 0
    topo: dict[str, Any] = {'python_os_cpu_count': nproc}
    if lscpu:
        result = run_command([lscpu], 15, replacements)
        topo['lscpu'] = result
        fields = {}
        for line in result['stdout'].splitlines():
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key in {
                'Architecture',
                'CPU(s)',
                'Thread(s) per core',
                'Core(s) per socket',
                'Socket(s)',
                'NUMA node(s)',
                'Model name',
                'CPU max MHz',
                'CPU min MHz',
            }:
                fields[key] = value
        topo['summary'] = fields
        parsed_cpus = fields.get('CPU(s)')
        if parsed_cpus and parsed_cpus.isdigit():
            topo['logical_cpus'] = int(parsed_cpus)
        else:
            topo['logical_cpus'] = nproc
    else:
        topo['logical_cpus'] = nproc
        topo['lscpu'] = {'returncode': 127, 'stdout': '', 'stderr': 'lscpu not found'}
        topo['summary'] = {}
    return topo


def selected_environment() -> dict[str, str]:
    keys = [
        'OMP_NUM_THREADS',
        'OMP_PROC_BIND',
        'OMP_PLACES',
        'SLURM_JOB_ID',
        'SLURM_NTASKS',
        'SLURM_CPUS_PER_TASK',
        'PBS_JOBID',
        'LSB_JOBID',
        'PMI_SIZE',
        'OMPI_COMM_WORLD_SIZE',
    ]
    return {key: os.environ[key] for key in keys if key in os.environ}


def find_launcher() -> str:
    for name in ('mpirun', 'mpiexec'):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeManifestError('missing mpirun/mpiexec launcher')


def mpi_probe_code() -> str:
    return (
        "import json, os, socket; "
        "rank = os.environ.get('OMPI_COMM_WORLD_RANK') or os.environ.get('PMI_RANK') or os.environ.get('PMIX_RANK') or os.environ.get('MPI_LOCALRANKID') or '0'; "
        "local_rank = os.environ.get('OMPI_COMM_WORLD_LOCAL_RANK') or os.environ.get('MPI_LOCALRANKID') or os.environ.get('PMI_LOCAL_RANK') or ''; "
        "size = os.environ.get('OMPI_COMM_WORLD_SIZE') or os.environ.get('PMI_SIZE') or os.environ.get('PMIX_SIZE') or ''; "
        "aff = sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else []; "
        "print(json.dumps({'rank': int(rank), 'local_rank': local_rank, 'size': size, 'hostname': socket.gethostname(), 'pid': os.getpid(), 'affinity': aff, 'affinity_count': len(aff), 'omp_num_threads': os.environ.get('OMP_NUM_THREADS', '')}, sort_keys=True))"
    )


def parse_probe_stdout(stdout: str) -> list[dict[str, Any]]:
    rows = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith('{'):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.sort(key=lambda item: int(item.get('rank', -1)))
    return rows


def run_mpi_probe(launcher: str, ranks: int, threads: int, replacements: list[tuple[str, str]], timeout_s: int) -> dict[str, Any]:
    env = os.environ.copy()
    env['OMP_NUM_THREADS'] = str(threads)
    code = mpi_probe_code()
    argv = [launcher, '-np', str(ranks), sys.executable, '-c', code]
    start = time.monotonic()
    proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout_s, env=env)
    duration_s = time.monotonic() - start
    stdout = sanitize_text(proc.stdout, replacements)
    stderr = sanitize_text(proc.stderr, replacements)
    rows = parse_probe_stdout(stdout)
    return {
        'argv': [sanitize_text(str(item), replacements) for item in argv[:4]] + ['<python-affinity-probe>'],
        'returncode': proc.returncode,
        'duration_s': duration_s,
        'stdout': stdout,
        'stderr': stderr,
        'stdout_sha256': sha256_text(stdout),
        'stderr_sha256': sha256_text(stderr),
        'rows': rows,
    }


def validate_probe(probe: dict[str, Any], ranks: int, threads: int, logical_cpus: int) -> list[str]:
    warnings: list[str] = []
    require(probe['returncode'] == 0, f'MPI probe returncode={probe["returncode"]}')
    rows = probe['rows']
    require(len(rows) == ranks, f'MPI probe rows={len(rows)} expected={ranks}')
    observed_ranks = [int(row['rank']) for row in rows]
    require(observed_ranks == list(range(ranks)), f'MPI probe ranks={observed_ranks} expected={list(range(ranks))}')
    for row in rows:
        require(int(row.get('affinity_count', 0)) > 0, f'rank {row.get("rank")} has empty CPU affinity')
        if str(row.get('omp_num_threads', '')) != str(threads):
            warnings.append(f'rank{row.get("rank")}:omp_num_threads={row.get("omp_num_threads")}')
    if logical_cpus and ranks * threads > logical_cpus:
        warnings.append(f'oversubscription:ranks_x_threads={ranks * threads}>logical_cpus={logical_cpus}')
    affinity_sets = {tuple(row.get('affinity', [])) for row in rows}
    if len(affinity_sets) == 1:
        warnings.append('all_mpi_ranks_share_same_affinity_mask')
    return warnings


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path.cwd().resolve()
    replacements = [(str(repo_root), '${REPO_ROOT}'), (str(repo_root.parent), '${USER_HOME}')]
    ranks = args.ranks
    threads = args.threads
    require(ranks >= 1, 'ranks must be positive')
    require(threads >= 1, 'threads must be positive')
    topology = cpu_topology(replacements)
    logical_cpus = int(topology.get('logical_cpus', 0) or 0)
    launcher = find_launcher()
    launcher_version = run_command([launcher, '--version'], 15, replacements)
    if launcher_version['returncode'] != 0:
        launcher_version = run_command([launcher, '-version'], 15, replacements)
    hostname = socket.gethostname()
    uname = run_command(['uname', '-a'], 15, replacements)
    scheduler_env = selected_environment()
    probe = run_mpi_probe(launcher, ranks, threads, replacements, args.timeout_s)
    warnings = validate_probe(probe, ranks, threads, logical_cpus)
    if not scheduler_env:
        warnings.append('no_scheduler_environment_detected')
    if 'OMP_PROC_BIND' not in scheduler_env:
        warnings.append('OMP_PROC_BIND_unset')
    if 'OMP_PLACES' not in scheduler_env:
        warnings.append('OMP_PLACES_unset')
    status = 'PASS'
    return {
        'schema_version': 1,
        'status': status,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'host': hostname,
        'requested': {'ranks': ranks, 'threads_per_rank': threads},
        'topology': topology,
        'launcher': {'path': sanitize_text(launcher, replacements), 'version': launcher_version},
        'uname': uname,
        'scheduler_environment': scheduler_env,
        'mpi_probe': probe,
        'warnings': warnings,
        'recommended_policy': {
            'mpi': 'Use scheduler-native launch when available; otherwise record mpirun/mpiexec command and rank count.',
            'openmp': 'Set OMP_NUM_THREADS explicitly. For hybrid runs, set OMP_PROC_BIND=spread and OMP_PLACES=cores unless the site scheduler provides a stronger binding policy.',
            'evidence': 'Preserve this manifest next to campaign summaries for production handoff.',
        },
        'limitations': [
            'This is a runtime/affinity preflight and does not prove CFD numerical accuracy.',
            'The MPI probe is a lightweight Python launch; it does not replace production-size CFD scaling, scheduler allocation testing, or overnight stability.',
            'Absence of scheduler environment variables means this evidence was collected from an interactive shell rather than a managed batch allocation.',
        ],
    }


def write_markdown(manifest: dict[str, Any], path: Path) -> None:
    topo = manifest['topology'].get('summary', {})
    probe_rows = manifest['mpi_probe']['rows']
    lines = [
        '# Engineering Runtime Affinity Manifest',
        '',
        f"Status: `{manifest['status']}`",
        f"Generated UTC: `{manifest['generated_at_utc']}`",
        f"Host: `{manifest['host']}`",
        f"Requested ranks x threads: `{manifest['requested']['ranks']}` x `{manifest['requested']['threads_per_rank']}`",
        f"Logical CPUs: `{manifest['topology'].get('logical_cpus', 'unknown')}`",
        f"MPI launcher: `{manifest['launcher']['path']}`",
        '',
        '## CPU Summary',
        '',
    ]
    for key, value in topo.items():
        lines.append(f'- {key}: `{value}`')
    lines.extend(['', '## MPI Probe', ''])
    for row in probe_rows:
        aff = row.get('affinity', [])
        preview = ','.join(str(v) for v in aff[:8])
        if len(aff) > 8:
            preview += ',...'
        lines.append(f"- rank `{row['rank']}` host `{row['hostname']}` affinity_count `{row['affinity_count']}` affinity `{preview}`")
    lines.extend(['', '## Warnings', ''])
    if manifest['warnings']:
        for item in manifest['warnings']:
            lines.append(f'- `{item}`')
    else:
        lines.append('- none')
    lines.extend(['', '## Recommended Policy', ''])
    for key, value in manifest['recommended_policy'].items():
        lines.append(f'- {key}: {value}')
    lines.extend(['', '## Limitations', ''])
    for item in manifest['limitations']:
        lines.append(f'- {item}')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def verify_manifest(path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing manifest: {path}')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    require(manifest.get('schema_version') == 1, 'schema_version is not 1')
    require(manifest.get('status') == 'PASS', 'status is not PASS')
    requested = manifest.get('requested', {})
    ranks = int(requested.get('ranks', 0))
    threads = int(requested.get('threads_per_rank', 0))
    require(ranks >= 1 and threads >= 1, 'invalid requested ranks/threads')
    topology = manifest.get('topology', {})
    logical_cpus = int(topology.get('logical_cpus', 0) or 0)
    require(logical_cpus >= ranks, f'logical_cpus={logical_cpus} smaller than ranks={ranks}')
    probe = manifest.get('mpi_probe', {})
    require(probe.get('returncode') == 0, 'MPI probe returncode is not zero')
    rows = probe.get('rows', [])
    require(isinstance(rows, list) and len(rows) == ranks, f'MPI probe row count mismatch rows={len(rows)} ranks={ranks}')
    observed = sorted(int(row.get('rank', -1)) for row in rows)
    require(observed == list(range(ranks)), f'MPI ranks mismatch observed={observed}')
    for row in rows:
        require(int(row.get('affinity_count', 0)) > 0, f'rank {row.get("rank")} has empty affinity')
        require(str(row.get('omp_num_threads', '')) == str(threads), f'rank {row.get("rank")} omp_num_threads mismatch')
    raw = path.read_text(encoding='utf-8')
    marker_values = [str(Path.home()), os.environ.get('HOME', '')]
    for key, value in os.environ.items():
        upper_key = key.upper()
        if any(token in upper_key for token in ('PASS', 'PASSWORD', 'SECRET', 'TOKEN')):
            marker_values.append(value)
    markers = sorted({value for value in marker_values if value and len(value) > 3})
    leaked = [marker for marker in markers if marker in raw]
    require(not leaked, 'manifest contains machine-local/private strings')
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-json', type=Path, help='Verify an existing runtime affinity manifest JSON')
    parser.add_argument('--ranks', type=int, default=4, help='MPI ranks for the lightweight probe')
    parser.add_argument('--threads', type=int, default=1, help='OMP_NUM_THREADS to export during the MPI probe')
    parser.add_argument('--timeout-s', type=int, default=60, help='Command timeout')
    parser.add_argument('--output-json', type=Path, help='Output manifest JSON')
    parser.add_argument('--output-md', type=Path, help='Output manifest Markdown')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.verify_json:
            manifest = verify_manifest(args.verify_json)
            print(
                'engineering_runtime_affinity_manifest VERIFY-PASS '
                f'ranks={manifest["requested"]["ranks"]} threads={manifest["requested"]["threads_per_rank"]} '
                f'warnings={len(manifest["warnings"])} json={args.verify_json}'
            )
            return 0
        require(args.output_json is not None, '--output-json is required unless --verify-json is used')
        require(args.output_md is not None, '--output-md is required unless --verify-json is used')
        manifest = build_manifest(args)
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(manifest, args.output_md)
    except (RuntimeManifestError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f'engineering_runtime_affinity_manifest FAIL {exc}') from exc
    print(
        'engineering_runtime_affinity_manifest PASS '
        f'ranks={manifest["requested"]["ranks"]} threads={manifest["requested"]["threads_per_rank"]} '
        f'warnings={len(manifest["warnings"])} json={args.output_json} md={args.output_md}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
