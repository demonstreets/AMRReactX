#!/usr/bin/env python3
"""Submit an engineering scheduler script and write a sanitized attempt report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SubmitError(RuntimeError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def marker_values() -> list[str]:
    values = [str(Path.home()), os.environ.get('HOME', '')]
    for key, value in os.environ.items():
        upper_key = key.upper()
        if any(token in upper_key for token in ('PASS', 'PASSWORD', 'SECRET', 'TOKEN')):
            values.append(value)
    return sorted({value for value in values if value and len(value) > 3})


def sanitize_text(text: str, replacements: list[tuple[str, str]]) -> str:
    out = text
    for old, new in replacements:
        if old:
            out = out.replace(old, new)
    return out


def no_private_markers(text: str) -> bool:
    return not any(marker in text for marker in marker_values())


def classify_attempt(returncode: int | None, timed_out: bool, stderr: str, stdout: str) -> tuple[str, str]:
    text = f'{stdout}\n{stderr}'.lower()
    if timed_out:
        return 'CONTROLLER_UNAVAILABLE', 'sbatch command timed out before returning a job id'
    if returncode == 0 and stdout.strip():
        return 'SUBMITTED', 'sbatch returned a job id'
    controller_markers = [
        'unable to contact slurm controller',
        'slurm_receive_msg',
        'socket timed out',
        'connect failure',
        'connection refused',
    ]
    if any(marker in text for marker in controller_markers):
        return 'CONTROLLER_UNAVAILABLE', 'sbatch could not contact the SLURM controller'
    if 'invalid account' in text or 'invalid partition' in text:
        return 'POLICY_REJECTED', 'scheduler rejected account or partition settings'
    if returncode is None:
        return 'NOT_RUN', 'sbatch was not executed'
    return 'SUBMIT_FAILED', f'sbatch returncode={returncode}'


def parse_job_id(stdout: str) -> str:
    first = stdout.strip().splitlines()[0].strip() if stdout.strip() else ''
    match = re.match(r'([0-9]+)', first)
    return match.group(1) if match else ''


def run_submit(script: Path, timeout_s: int, replacements: list[tuple[str, str]]) -> dict[str, Any]:
    sbatch = shutil.which('sbatch')
    command = ['sbatch', '--parsable', str(script)]
    sanitized_command = [sanitize_text(str(item), replacements) for item in command]
    record: dict[str, Any] = {
        'command': sanitized_command,
        'executable': sbatch or '',
        'available': bool(sbatch),
        'timeout_s': timeout_s,
        'timed_out': False,
        'returncode': None,
        'stdout': '',
        'stderr': '',
        'duration_s': 0.0,
    }
    if not sbatch:
        record['status'] = 'SBATCH_MISSING'
        record['detail'] = 'sbatch executable was not found in PATH'
        return record
    start = time.monotonic()
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout_s, check=False)
        record['returncode'] = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        record['timed_out'] = True
        stdout = exc.stdout or ''
        stderr = exc.stderr or ''
    record['duration_s'] = time.monotonic() - start
    stdout = sanitize_text(stdout, replacements).strip()
    stderr = sanitize_text(stderr, replacements).strip()
    record['stdout'] = stdout
    record['stderr'] = stderr
    record['stdout_sha256'] = sha256_text(stdout)
    record['stderr_sha256'] = sha256_text(stderr)
    status, detail = classify_attempt(record['returncode'], bool(record['timed_out']), stderr, stdout)
    record['status'] = status
    record['detail'] = detail
    record['job_id'] = parse_job_id(stdout) if status == 'SUBMITTED' else ''
    return record


def write_markdown(report: dict[str, Any], path: Path) -> None:
    attempt = report['attempt']
    lines = [
        '# Engineering Scheduler Submit Attempt',
        '',
        f"Status: `{report['status']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        f"Script: `{report['script']}`",
        f"sbatch available: `{attempt['available']}`",
        f"Return code: `{attempt['returncode']}`",
        f"Timed out: `{attempt['timed_out']}`",
        f"Job id: `{attempt.get('job_id', '')}`",
        '',
        '## Detail',
        '',
        attempt.get('detail', ''),
        '',
        '## Stderr',
        '',
        '```text',
        attempt.get('stderr', ''),
        '```',
        '',
    ]
    path.write_text('\n'.join(lines), encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script', type=Path)
    parser.add_argument('--timeout-s', type=int, default=45)
    parser.add_argument('--output-json', type=Path, required=True)
    parser.add_argument('--output-md', type=Path, required=True)
    parser.add_argument('--allow-non-submitted', action='store_true')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repo_root()
    script = args.script
    if not script.is_absolute():
        script = repo / script
    if not script.is_file():
        print(f'engineering_scheduler_submit_attempt FAIL missing script: {script}', file=sys.stderr)
        return 2
    replacements = [(str(repo), '${REPO_ROOT}'), (str(Path.home()), '${USER_HOME}'), (os.environ.get('HOME', ''), '${USER_HOME}')]
    attempt = run_submit(script, args.timeout_s, replacements)
    report = {
        'schema_version': 1,
        'status': attempt['status'],
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'script': str(script.relative_to(repo)),
        'attempt': attempt,
        'limitations': [
            'SUBMITTED only proves that the scheduler accepted the job; completed scheduler-run evidence still requires runtime-affinity and campaign summary outputs.',
            'CONTROLLER_UNAVAILABLE documents a scheduler control-plane failure and does not satisfy the production scheduler gate.',
        ],
    }
    raw = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if not no_private_markers(raw):
        print('engineering_scheduler_submit_attempt FAIL report contains private markers', file=sys.stderr)
        return 2
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(raw, encoding='utf-8')
    write_markdown(report, args.output_md)
    print(
        'engineering_scheduler_submit_attempt ' + report['status'] + ' ' +
        f"returncode={attempt['returncode']} timed_out={attempt['timed_out']} " +
        f"job_id={attempt.get('job_id', '')} json={args.output_json} md={args.output_md}"
    )
    if report['status'] == 'SUBMITTED' or args.allow_non_submitted:
        return 0
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
