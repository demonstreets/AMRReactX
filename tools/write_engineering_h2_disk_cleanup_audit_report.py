#!/usr/bin/env python3
"""Write/verify a read-only disk cleanup audit for H2 full-duration runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PASS_STATUS = 'PASS-DISK-CLEANUP-AUDIT'
NOT_READY_STATUS = 'NOT_READY-DISK-CLEANUP-AUDIT'

DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/'
    'disk_cleanup_audit_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/'
    'disk_cleanup_audit_report.md'
)


class ReportError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def du_bytes(path: Path) -> int:
    try:
        out = subprocess.check_output(['du', '-sb', str(path)], text=True, stderr=subprocess.DEVNULL)
        return int(out.split()[0])
    except Exception:
        total = 0
        if path.is_file():
            return path.stat().st_size
        for root, _, files in os.walk(path):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    pass
        return total


def repo_label(path: Path, repo: Path) -> str:
    return str(path.relative_to(repo))


def tmp_label(path: Path) -> str:
    return '${TMPDIR}/' + path.name


def item(path: Path, label: str, category: str, cleanup_class: str, now: float) -> dict[str, Any]:
    try:
        stat = path.stat()
        age_days = max(0.0, (now - stat.st_mtime) / 86400.0)
    except OSError:
        age_days = None
    size = du_bytes(path)
    return {
        'label': label,
        'category': category,
        'cleanup_class': cleanup_class,
        'size_bytes': size,
        'size_gb': size / 1024**3,
        'age_days': age_days,
        'requires_manual_confirmation': True,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path('.').resolve()
    now = time.time()
    required = int(args.min_required_free_gb * 1024**3)
    free = shutil.disk_usage(repo).free
    deficit = max(0, required - free)

    repo_candidates: list[dict[str, Any]] = []
    for child in sorted(repo.iterdir()):
        if child.name in {'.git', '.codex'}:
            cleanup_class = 'keep_required_repository_metadata'
        elif child.name.startswith('build') or child.name in {'PASS', '.pytest_cache', 'backups'}:
            cleanup_class = 'review_generated_or_cache_directory'
        elif child.name in {'examples', 'test'}:
            cleanup_class = 'review_large_case_or_test_data_before_cleanup'
        else:
            cleanup_class = 'keep_or_low_priority_review'
        if child.is_dir():
            repo_candidates.append(item(child, repo_label(child, repo), 'repo_top_level', cleanup_class, now))

    tmp_candidates: list[dict[str, Any]] = []
    for path in sorted(Path('/tmp').glob('codex*')):
        if path.exists():
            tmp_candidates.append(item(path, tmp_label(path), 'tmp_codex_artifact', 'review_tmp_codex_artifact', now))

    repo_candidates.sort(key=lambda x: int(x['size_bytes']), reverse=True)
    tmp_candidates.sort(key=lambda x: int(x['size_bytes']), reverse=True)
    review_candidates = [
        entry for entry in repo_candidates
        if entry['cleanup_class'] in {
            'review_generated_or_cache_directory',
            'review_large_case_or_test_data_before_cleanup',
        }
    ][: args.max_repo_candidates]
    review_candidates += tmp_candidates[: args.max_tmp_candidates]
    reclaimable_review_bytes = sum(int(entry['size_bytes']) for entry in review_candidates)

    blockers: list[str] = []
    if free < required:
        blockers.append('free_disk_below_full_duration_candidate_requirement')
    if deficit > 0 and reclaimable_review_bytes < deficit:
        blockers.append('review_candidates_do_not_cover_disk_deficit')

    status = PASS_STATUS if not blockers else NOT_READY_STATUS
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 Disk Cleanup Audit',
        'audit_scope': 'read_only_disk_usage_and_cleanup_candidates',
        'destructive_actions_performed': False,
        'full_duration_disk_requirement': {
            'min_required_free_gb': args.min_required_free_gb,
            'min_required_free_bytes': required,
            'current_free_bytes': free,
            'current_free_gb': free / 1024**3,
            'deficit_bytes': deficit,
            'deficit_gb': deficit / 1024**3,
            'passes_requirement': free >= required,
        },
        'summary': {
            'repo_top_level_entries_scanned': len(repo_candidates),
            'tmp_codex_entries_scanned': len(tmp_candidates),
            'review_candidate_count': len(review_candidates),
            'review_candidate_bytes': reclaimable_review_bytes,
            'review_candidate_gb': reclaimable_review_bytes / 1024**3,
            'review_candidates_cover_deficit': deficit == 0 or reclaimable_review_bytes >= deficit,
            'largest_repo_entries': repo_candidates[:10],
            'largest_tmp_codex_entries': tmp_candidates[:10],
        },
        'cleanup_review_candidates': review_candidates,
        'blocking_gaps': blockers,
        'limitations': [
            'This audit is read-only and does not delete files.',
            'Cleanup candidates require human confirmation because some generated data may still be useful evidence or case history.',
            'Repository paths are recorded as relative labels, and tmp artifacts are recorded with ${TMPDIR} labels to avoid machine-local path leakage.',
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    req = report['full_duration_disk_requirement']
    summary = report['summary']
    lines = [
        '# Engineering H2 Disk Cleanup Audit',
        '',
        f"Status: `{report['status']}`",
        f"Destructive actions performed: `{report['destructive_actions_performed']}`",
        '',
        '## Disk Requirement',
        '',
        f"- Current free GB: `{req['current_free_gb']:.2f}`",
        f"- Required free GB: `{req['min_required_free_gb']:.2f}`",
        f"- Deficit GB: `{req['deficit_gb']:.2f}`",
        f"- Requirement passed: `{req['passes_requirement']}`",
        '',
        '## Cleanup Review Candidates',
        '',
        f"- Candidate count: `{summary['review_candidate_count']}`",
        f"- Candidate total GB: `{summary['review_candidate_gb']:.2f}`",
        f"- Candidates cover deficit: `{summary['review_candidates_cover_deficit']}`",
        '',
        '| Label | Class | Size GB | Age days |',
        '| --- | --- | ---: | ---: |',
    ]
    for entry in report['cleanup_review_candidates']:
        age = entry['age_days']
        age_text = '' if age is None else f'{age:.1f}'
        lines.append(
            f"| `{entry['label']}` | `{entry['cleanup_class']}` | "
            f"{entry['size_gb']:.2f} | {age_text} |"
        )
    lines.extend(['', '## Blocking Gaps', ''])
    if report['blocking_gaps']:
        for gap in report['blocking_gaps']:
            lines.append(f'- `{gap}`')
    else:
        lines.append('- none')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ReportError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {PASS_STATUS, NOT_READY_STATUS}, 'invalid status')
    require(data.get('destructive_actions_performed') is False, 'audit must be read-only')
    req = data.get('full_duration_disk_requirement', {})
    require(isinstance(req, dict), 'missing full_duration_disk_requirement')
    require(float(req.get('min_required_free_gb', 0.0)) > 0.0, 'invalid disk requirement')
    require(isinstance(data.get('cleanup_review_candidates'), list), 'missing cleanup_review_candidates')
    for entry in data.get('cleanup_review_candidates', []):
        label = str(entry.get('label', ''))
        home_marker = '/' + 'home/'
        require(home_marker not in label, f'machine-local home path leaked: {label}')
        require(not label.startswith('/tmp/'), f'raw tmp path leaked: {label}')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--min-required-free-gb', type=float, default=20.0)
    ap.add_argument('--max-repo-candidates', type=int, default=12)
    ap.add_argument('--max-tmp-candidates', type=int, default=30)
    ap.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)

    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            req = data['full_duration_disk_requirement']
            print(
                'engineering_h2_disk_cleanup_audit_report VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"free_gb={req['current_free_gb']:.2f} required_gb={req['min_required_free_gb']:.2f}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        req = report['full_duration_disk_requirement']
        print(
            'engineering_h2_disk_cleanup_audit_report PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"free_gb={req['current_free_gb']:.2f} required_gb={req['min_required_free_gb']:.2f}"
        )
        return 0
    except ReportError as exc:
        print(f'engineering_h2_disk_cleanup_audit_report FAIL {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
