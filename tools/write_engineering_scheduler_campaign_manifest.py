#!/usr/bin/env python3
"""Write a scheduler-ready engineering H2 campaign manifest and SLURM script."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SchedulerManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SchedulerManifestError(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sanitize_text(text: str, replacements: list[tuple[str, str]]) -> str:
    out = text
    for old, new in replacements:
        if old:
            out = out.replace(old, new)
    return out


def marker_values() -> list[str]:
    values = [str(Path.home()), os.environ.get('HOME', '')]
    for key, value in os.environ.items():
        upper_key = key.upper()
        if any(token in upper_key for token in ('PASS', 'PASSWORD', 'SECRET', 'TOKEN')):
            values.append(value)
    return sorted({value for value in values if value and len(value) > 3})


def no_private_markers(text: str) -> bool:
    return not any(marker in text for marker in marker_values())


def run_probe(command: list[str], timeout_s: int, replacements: list[tuple[str, str]], cwd: Path | None = None) -> dict[str, Any]:
    executable = shutil.which(command[0])
    record: dict[str, Any] = {
        'command': command,
        'executable': executable or '',
        'available': bool(executable),
        'timeout_s': timeout_s,
        'timed_out': False,
        'returncode': None,
        'stdout': '',
        'stderr': '',
    }
    if not executable:
        return record
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout_s, check=False, cwd=cwd)
        record.update({
            'returncode': proc.returncode,
            'stdout': sanitize_text(proc.stdout, replacements).strip(),
            'stderr': sanitize_text(proc.stderr, replacements).strip(),
        })
    except subprocess.TimeoutExpired as exc:
        record.update({
            'timed_out': True,
            'stdout': sanitize_text(exc.stdout or '', replacements).strip(),
            'stderr': sanitize_text(exc.stderr or '', replacements).strip(),
        })
    return record


def repo_metadata(repo: Path) -> dict[str, Any]:
    def git(args: list[str]) -> str:
        try:
            return subprocess.check_output(['git', *args], cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ''

    return {
        'branch': git(['rev-parse', '--abbrev-ref', 'HEAD']),
        'commit': git(['rev-parse', 'HEAD']),
        'dirty_short': git(['status', '--short']),
    }


def script_relative_repo_up(script_path: Path, repo: Path) -> str:
    try:
        rel_parent = script_path.resolve().parent.relative_to(repo.resolve())
    except ValueError as exc:
        raise SchedulerManifestError('script output must be inside the repository') from exc
    depth = len(rel_parent.parts)
    if depth == 0:
        return '.'
    return '/'.join(['..'] * depth)


def slurm_line(option: str, value: str | None) -> list[str]:
    if value:
        return [f'#SBATCH {option}={value}']
    return []


def build_slurm_script(args: argparse.Namespace, script_path: Path, repo: Path) -> str:
    repo_up = script_relative_repo_up(script_path, repo)
    job_name = args.job_name
    campaign_root = f"docs/codex_audit/evidence/{args.evidence_dir}/campaign_run"
    affinity_json = f"docs/codex_audit/evidence/{args.evidence_dir}/runtime_affinity_manifest.json"
    affinity_md = f"docs/codex_audit/evidence/{args.evidence_dir}/runtime_affinity_manifest.md"
    summary_json = f"docs/codex_audit/evidence/{args.evidence_dir}/campaign_run_summary.json"
    summary_md = f"docs/codex_audit/evidence/{args.evidence_dir}/campaign_run_summary.md"
    run_report_json = f"docs/codex_audit/evidence/{args.evidence_dir}/scheduler_run_report.json"
    run_report_md = f"docs/codex_audit/evidence/{args.evidence_dir}/scheduler_run_report.md"
    stdout_path = f"docs/codex_audit/evidence/{args.evidence_dir}/slurm-%j.out"

    lines: list[str] = [
        '#!/usr/bin/env bash',
        f'#SBATCH --job-name={job_name}',
        f'#SBATCH --nodes={args.nodes}',
        f'#SBATCH --ntasks={args.ranks}',
        f'#SBATCH --cpus-per-task={args.threads}',
        f'#SBATCH --time={args.time_limit}',
        f'#SBATCH --output={stdout_path}',
        *slurm_line('--partition', args.partition),
        *slurm_line('--account', args.account),
        '',
        'set -euo pipefail',
        'script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)',
        f'repo_root=$(cd "$script_dir/{repo_up}" && pwd)',
        'cd "$repo_root"',
        '',
        f'export OMP_NUM_THREADS="${{OMP_NUM_THREADS:-{args.threads}}}"',
        f'export OMP_PROC_BIND="${{OMP_PROC_BIND:-{args.omp_proc_bind}}}"',
        f'export OMP_PLACES="${{OMP_PLACES:-{args.omp_places}}}"',
        f'export JOBS="${{JOBS:-{args.jobs}}}"',
        f'export RUN_TIMEOUT="${{RUN_TIMEOUT:-{args.run_timeout_s}}}"',
        f'export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS="${{CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_RANKS:-{args.ranks}}}"',
        f'export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP="${{CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MAX_STEP:-{args.max_step}}}"',
        f'export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT="${{CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_PLOT_INT:-{args.plot_int}}}"',
        f'export CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES="${{CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_PLOTFILES:-{args.min_plotfiles}}}"',
        '',
        f'mkdir -p "docs/codex_audit/evidence/{args.evidence_dir}"',
        'finalize_scheduler_report() {',
        '  rc=$?',
        f'  python3 tools/sanitize_engineering_scheduler_evidence.py docs/codex_audit/evidence/{args.evidence_dir} || rc=$?',
        '  if [[ $rc -eq 0 ]]; then',
        '    python3 tools/verify_engineering_scheduler_run.py \\',
        f'      --evidence-dir {args.evidence_dir} \\',
        f'      --output-json {run_report_json} \\',
        f'      --output-md {run_report_md} || rc=$?',
        '  else',
        '    python3 tools/verify_engineering_scheduler_run.py \\',
        f'      --evidence-dir {args.evidence_dir} \\',
        f'      --output-json {run_report_json} \\',
        f'      --output-md {run_report_md} \\',
        '      --allow-incomplete || true',
        '  fi',
        '  exit $rc',
        '}',
        'trap finalize_scheduler_report EXIT',
        '',
        'python3 tools/write_engineering_runtime_affinity_manifest.py \\',
        f'  --ranks {args.ranks} \\',
        f'  --threads {args.threads} \\',
        f'  --output-json {affinity_json} \\',
        f'  --output-md {affinity_md}',
        '',
        'python3 tools/run_engineering_h2_campaign.py \\',
        f'  --campaign {args.campaign} \\',
        f'  --suite {args.suite} \\',
        f'  --jobs {args.jobs} \\',
        f'  --run-timeout-s {args.run_timeout_s} \\',
        f'  --case-timeout-s {args.case_timeout_s} \\',
        f'  --output-root {campaign_root} \\',
        f'  --output-json {summary_json} \\',
        f'  --output-md {summary_md}',
        '',
        f'python3 tools/write_engineering_scheduler_campaign_manifest.py --verify-json docs/codex_audit/evidence/{args.evidence_dir}/scheduler_campaign_manifest.json',
    ]
    return '\n'.join(lines)


def build_execution_plan(args: argparse.Namespace, evidence_dir: str) -> dict[str, Any]:
    campaign_root = f"docs/codex_audit/evidence/{evidence_dir}/campaign_run"
    return {
        'plan_tier': 'scheduler_managed_production_scout_candidate',
        'run_mode': 'slurm_batch',
        'suite': args.suite,
        'campaign': args.campaign,
        'resume_policy': {
            'wrapper_reuse_existing_enabled': False,
            'scheduler_rerun_safe': True,
            'rerun_instruction': (
                'Regenerate the manifest, submit the hashed SLURM script, then verify '
                'scheduler_run_report.json after the job exits.'
            ),
        },
        'expected_outputs': {
            'evidence_root': f"docs/codex_audit/evidence/{evidence_dir}",
            'campaign_run_root': campaign_root,
            'runtime_affinity_manifest': f"docs/codex_audit/evidence/{evidence_dir}/runtime_affinity_manifest.json",
            'campaign_run_summary': f"docs/codex_audit/evidence/{evidence_dir}/campaign_run_summary.json",
            'scheduler_run_report': f"docs/codex_audit/evidence/{evidence_dir}/scheduler_run_report.json",
            'sanitized_slurm_stdout_glob': f"docs/codex_audit/evidence/{evidence_dir}/slurm-*.out",
        },
        'closure_criteria': [
            'scheduler_submit_attempt.status == SUBMITTED',
            'runtime_affinity_manifest.status == PASS',
            'campaign_run_summary.status == PASS',
            'verify_engineering_scheduler_run.py status == PASS',
            'scheduler logs contain no failure markers, nonfinite tokens, private markers, or unsanitized machine-local paths',
        ],
        'production_limitations': [
            'This plan remains a production-scout candidate until the scheduler controller accepts and completes the job.',
            'Full production readiness still requires production-size/full-duration campaign evidence and external reference agreement.',
        ],
    }


def build_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        f"# Engineering Scheduler Campaign Manifest: {manifest['campaign']}",
        '',
        f"Status: `{manifest['status']}`",
        f"Suite: `{manifest['suite']}`",
        f"Generated UTC: `{manifest['generated_at_utc']}`",
        f"Scheduler: `{manifest['scheduler']['kind']}`",
        f"Script: `{manifest['script']['path']}`",
        f"Script SHA-256: `{manifest['script']['sha256']}`",
        '',
        '## Requested Resources',
        '',
    ]
    for key, value in manifest['resources'].items():
        lines.append(f'- {key}: `{value}`')
    lines.extend(['', '## Scheduler Probes', ''])
    for name, probe in manifest['scheduler']['probes'].items():
        state = 'timeout' if probe['timed_out'] else ('available' if probe['available'] else 'missing')
        lines.append(f"- {name}: `{state}`, returncode=`{probe['returncode']}`")
    plan = manifest.get('execution_plan', {})
    lines.extend(['', '## Execution Plan', ''])
    if isinstance(plan, dict):
        lines.append(f"- Plan tier: `{plan.get('plan_tier', '')}`")
        lines.append(f"- Run mode: `{plan.get('run_mode', '')}`")
        outputs = plan.get('expected_outputs', {})
        if isinstance(outputs, dict):
            for key, value in outputs.items():
                lines.append(f"- {key}: `{value}`")
        criteria = plan.get('closure_criteria', [])
        if isinstance(criteria, list):
            lines.extend(['', '### Closure Criteria', ''])
            for item in criteria:
                lines.append(f'- {item}')
    lines.extend(['', '## Commands', ''])
    for command in manifest['commands']:
        lines.append(f"- `{command}`")
    lines.extend(['', '## Warnings', ''])
    for warning in manifest['warnings']:
        lines.append(f'- {warning}')
    lines.extend(['', '## Limitations', ''])
    for item in manifest['limitations']:
        lines.append(f'- {item}')
    lines.append('')
    return '\n'.join(lines)


def verify_manifest(path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing manifest: {path}')
    raw = path.read_text(encoding='utf-8')
    require(no_private_markers(raw), 'manifest contains machine-local/private strings')
    manifest = json.loads(raw)
    require(manifest.get('schema_version') == 1, 'schema_version is not 1')
    require(manifest.get('status') in {'READY', 'READY_WITH_WARNINGS'}, 'unexpected status')
    resources = manifest.get('resources', {})
    require(int(resources.get('ranks', 0)) >= 1, 'invalid ranks')
    require(int(resources.get('threads_per_rank', 0)) >= 1, 'invalid threads_per_rank')
    require(manifest.get('suite'), 'missing suite')
    plan = manifest.get('execution_plan')
    require(isinstance(plan, dict), 'missing execution_plan')
    require(plan.get('plan_tier') == 'scheduler_managed_production_scout_candidate', 'unexpected execution_plan.plan_tier')
    require(plan.get('run_mode') == 'slurm_batch', 'unexpected execution_plan.run_mode')
    outputs = plan.get('expected_outputs')
    require(isinstance(outputs, dict), 'missing execution_plan.expected_outputs')
    for key in ('evidence_root', 'campaign_run_root', 'runtime_affinity_manifest', 'campaign_run_summary', 'scheduler_run_report'):
        require(outputs.get(key), f'execution_plan expected output missing {key}')
    closure = plan.get('closure_criteria')
    require(isinstance(closure, list) and len(closure) >= 4, 'execution_plan closure criteria incomplete')
    script = manifest.get('script', {})
    script_path = Path(script.get('path', ''))
    require(script_path.is_file(), f'missing generated script: {script_path}')
    script_text = script_path.read_text(encoding='utf-8')
    require(no_private_markers(script_text), 'generated script contains machine-local/private strings')
    require(sha256_text(script_text) == script.get('sha256'), 'generated script sha256 mismatch')
    required_tokens = [
        '#SBATCH --ntasks=',
        '#SBATCH --cpus-per-task=',
        'write_engineering_runtime_affinity_manifest.py',
        'run_engineering_h2_campaign.py',
        'sanitize_engineering_scheduler_evidence.py', 'verify_engineering_scheduler_run.py',
        'OMP_PROC_BIND',
        'OMP_PLACES',
    ]
    for token in required_tokens:
        require(token in script_text, f'generated script missing {token}')
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-json', type=Path, help='Verify an existing scheduler campaign manifest')
    parser.add_argument('--campaign', default='engineering-h2-production-scheduler-readiness')
    parser.add_argument('--suite', default='h2-production-scout')
    parser.add_argument('--evidence-dir', default=f"engineering_scheduler_h2_{datetime.now(timezone.utc).strftime('%Y%m%d')}")
    parser.add_argument('--job-name', default='eng-h2-prod-scout')
    parser.add_argument('--scheduler', choices=('slurm',), default='slurm')
    parser.add_argument('--nodes', type=int, default=1)
    parser.add_argument('--ranks', type=int, default=4)
    parser.add_argument('--threads', type=int, default=1)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--max-step', type=int, default=200)
    parser.add_argument('--plot-int', type=int, default=20)
    parser.add_argument('--min-plotfiles', type=int, default=11)
    parser.add_argument('--time-limit', default='02:00:00')
    parser.add_argument('--partition', default='')
    parser.add_argument('--account', default='')
    parser.add_argument('--omp-proc-bind', default='close')
    parser.add_argument('--omp-places', default='cores')
    parser.add_argument('--run-timeout-s', type=int, default=2400)
    parser.add_argument('--case-timeout-s', type=int, default=4200)
    parser.add_argument('--probe-timeout-s', type=int, default=5)
    parser.add_argument('--sbatch-test-only', action='store_true', help='Run sbatch --test-only on the generated script without submitting')
    parser.add_argument('--output-json', type=Path)
    parser.add_argument('--output-md', type=Path)
    parser.add_argument('--script-output', type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.verify_json:
            manifest = verify_manifest(args.verify_json)
            print(
                'engineering_scheduler_campaign_manifest VERIFY-PASS ' +
                f"suite={manifest['suite']} ranks={manifest['resources']['ranks']} " +
                f"threads={manifest['resources']['threads_per_rank']} json={args.verify_json}"
            )
            return 0

        require(args.nodes >= 1, 'nodes must be >= 1')
        require(args.ranks >= 1, 'ranks must be >= 1')
        require(args.threads >= 1, 'threads must be >= 1')
        require(args.max_step >= 1, 'max-step must be >= 1')
        require(args.plot_int >= 1, 'plot-int must be >= 1')
        require(args.min_plotfiles >= 1, 'min-plotfiles must be >= 1')

        repo = repo_root()
        evidence_root = repo / 'docs' / 'codex_audit' / 'evidence' / args.evidence_dir
        output_json = args.output_json or evidence_root / 'scheduler_campaign_manifest.json'
        output_md = args.output_md or evidence_root / 'scheduler_campaign_manifest.md'
        script_output = args.script_output or evidence_root / 'run_engineering_h2_slurm.sh'
        if not output_json.is_absolute():
            output_json = repo / output_json
        if not output_md.is_absolute():
            output_md = repo / output_md
        if not script_output.is_absolute():
            script_output = repo / script_output
        evidence_root.mkdir(parents=True, exist_ok=True)

        replacements = [(str(repo), '${REPO_ROOT}'), (str(Path.home()), '${USER_HOME}'), (os.environ.get('HOME', ''), '${USER_HOME}')]
        probes = {
            'sbatch_version': run_probe(['sbatch', '--version'], args.probe_timeout_s, replacements),
            'sinfo': run_probe(['sinfo', '-h', '-o', '%P|%D|%t|%c|%m|%G'], args.probe_timeout_s, replacements),
            'squeue_user': run_probe(['squeue', '-h', '-u', os.environ.get('USER', ''), '-o', '%i|%T|%j|%D|%C|%M|%R'], args.probe_timeout_s, replacements),
            'scontrol_ping': run_probe(['scontrol', 'ping'], args.probe_timeout_s, replacements),
        }

        script_text = build_slurm_script(args, script_output, repo)
        require(no_private_markers(script_text), 'generated script contains machine-local/private strings')
        script_output.write_text(script_text, encoding='utf-8')
        script_output.chmod(0o755)

        if args.sbatch_test_only:
            rel_script = str(script_output.relative_to(repo))
            probes['sbatch_test_only'] = run_probe(['sbatch', '--test-only', rel_script], args.probe_timeout_s, replacements, cwd=repo)

        warnings: list[str] = []
        if not probes['sbatch_version']['available']:
            warnings.append('sbatch_not_available')
        for name in ('sinfo', 'squeue_user', 'scontrol_ping', 'sbatch_test_only'):
            if name not in probes:
                continue
            if probes[name]['timed_out']:
                warnings.append(f'{name}_timed_out')
            elif probes[name]['available'] and probes[name]['returncode'] not in (0, None):
                warnings.append(f'{name}_returncode_{probes[name]["returncode"]}')
        if args.threads > 1:
            warnings.append('hybrid_threaded_mpi_requires_thread_support_policy_review')

        manifest: dict[str, Any] = {
            'schema_version': 1,
            'status': 'READY_WITH_WARNINGS' if warnings else 'READY',
            'generated_at_utc': utc_now(),
            'campaign': args.campaign,
            'suite': args.suite,
            'repo': repo_metadata(repo),
            'host': platform.node(),
            'python': sys.version.split()[0],
            'scheduler': {
                'kind': args.scheduler,
                'probes': probes,
            },
            'resources': {
                'nodes': args.nodes,
                'ranks': args.ranks,
                'threads_per_rank': args.threads,
                'jobs': args.jobs,
                'max_step': args.max_step,
                'plot_int': args.plot_int,
                'min_plotfiles': args.min_plotfiles,
                'time_limit': args.time_limit,
                'partition': args.partition,
                'account': args.account,
                'omp_proc_bind': args.omp_proc_bind,
                'omp_places': args.omp_places,
                'run_timeout_s': args.run_timeout_s,
                'case_timeout_s': args.case_timeout_s,
            },
            'script': {
                'path': str(script_output.relative_to(repo)),
                'sha256': sha256_text(script_text),
                'mode': '0755',
            },
            'execution_plan': build_execution_plan(args, args.evidence_dir),
            'commands': [
                f'bash {script_output.relative_to(repo)}',
                f'sbatch {script_output.relative_to(repo)}',
                f'python3 tools/submit_engineering_scheduler_job.py {script_output.relative_to(repo)} --output-json {evidence_root.relative_to(repo)}/scheduler_submit_attempt.json --output-md {evidence_root.relative_to(repo)}/scheduler_submit_attempt.md --allow-non-submitted',
                f'python3 tools/write_engineering_scheduler_campaign_manifest.py --verify-json {output_json.relative_to(repo)}',
            ],
            'warnings': warnings,
            'limitations': [
                'This manifest prepares a scheduler-managed engineering H2 campaign but does not submit a job by itself.',
                'A PASS manifest proves reproducible scheduler script generation, client probing, resource capture, optional sbatch test-only probing, script hash verification, and automatic scheduler-run report generation after successful or failed scheduled execution.',
                'Production readiness still requires a completed scheduler-managed run with runtime-affinity evidence, campaign summary, sanitized logs, and long-duration stability metrics.',
            ],
        }
        raw = json.dumps(manifest, indent=2, sort_keys=True) + '\n'
        require(no_private_markers(raw), 'manifest contains machine-local/private strings')
        output_json.write_text(raw, encoding='utf-8')
        output_md.write_text(build_markdown(manifest), encoding='utf-8')
        verify_manifest(output_json)
        print(
            'engineering_scheduler_campaign_manifest PASS ' +
            f"status={manifest['status']} suite={args.suite} ranks={args.ranks} threads={args.threads} " +
            f"warnings={len(warnings)} json={output_json} md={output_md} script={script_output}"
        )
        return 0
    except SchedulerManifestError as exc:
        print(f'engineering_scheduler_campaign_manifest FAIL {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
