#!/usr/bin/env python3
"""Package and verify durable engineering H2 campaign release evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvidencePackError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidencePackError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_bytes(raw: bytes, replacements: list[tuple[str, str]]) -> tuple[bytes, bool]:
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw, False
    original = text
    for old, new in replacements:
        if old:
            text = text.replace(old, new)
    if text == original:
        return raw, False
    return text.encode('utf-8'), True


def copy_checked(
    src: Path,
    dst: Path,
    expected_sha256: str | None = None,
    replacements: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    require(src.is_file(), f'missing source file: {src}')
    raw = src.read_bytes()
    src_sha = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None:
        require(src_sha == expected_sha256, f'source hash mismatch for {src}')
    packed_raw, sanitized = sanitize_bytes(raw, replacements or [])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(packed_raw)
    dst_sha = sha256_file(dst)
    return {
        'source_path': str(src),
        'source_sha256': src_sha,
        'path': str(dst),
        'relative_path': str(dst),
        'sha256': dst_sha,
        'size_bytes': dst.stat().st_size,
        'sanitized': sanitized,
    }


def read_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing JSON file: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def compact_repo_metadata(repo: dict[str, Any]) -> dict[str, Any]:
    dirty_short = str(repo.get('dirty_short', ''))
    compact = {
        'branch': repo.get('branch'),
        'commit': repo.get('commit'),
        'dirty': bool(dirty_short.strip()),
        'dirty_short_line_count': len([line for line in dirty_short.splitlines() if line.strip()]),
    }
    if dirty_short:
        compact['dirty_short_sha256'] = hashlib.sha256(dirty_short.encode('utf-8')).hexdigest()
    return compact


def rel_record(record: dict[str, Any], output_root: Path) -> dict[str, Any]:
    packed = Path(record['path'])
    record = dict(record)
    record['relative_path'] = packed.relative_to(output_root).as_posix()
    record['path'] = record['relative_path']
    return record


def validate_summary(summary: dict[str, Any], summary_path: Path) -> None:
    require(summary.get('schema_version') == 1, f'{summary_path} schema_version is not 1')
    require(summary.get('status') == 'PASS', f'{summary_path} status is not PASS')
    require(summary.get('suite') == 'engineering-h2-production', f'{summary_path} is not engineering-h2-production')
    cases = summary.get('cases')
    require(isinstance(cases, list) and cases, f'{summary_path} missing cases')
    require(int(summary.get('case_count', -1)) == len(cases), f'{summary_path} case_count mismatch')


def package_evidence(args: argparse.Namespace) -> dict[str, Any]:
    summary_path = args.run_summary.resolve()
    summary_md_path = summary_path.with_suffix('.md')
    manifest_path = args.campaign_manifest.resolve() if args.campaign_manifest else summary_path.with_name('campaign_manifest.json')
    manifest_md_path = manifest_path.with_suffix('.md')
    output_root = args.output_root.resolve()
    repo_root = Path.cwd().resolve()
    replacements = [
        (str(repo_root), '${REPO_ROOT}'),
        (str(repo_root.parent), '${USER_HOME}'),
    ]

    summary = read_json(summary_path)
    validate_summary(summary, summary_path)
    require(summary_md_path.is_file(), f'missing run summary Markdown: {summary_md_path}')
    require(manifest_path.is_file(), f'missing campaign manifest: {manifest_path}')
    require(manifest_md_path.is_file(), f'missing campaign manifest Markdown: {manifest_md_path}')

    if output_root.exists() and any(output_root.iterdir()) and not args.force:
        raise EvidencePackError(f'output root is not empty, use --force to replace: {output_root}')
    output_root.mkdir(parents=True, exist_ok=True)

    metadata_root = output_root / 'metadata'
    source_files = {
        'campaign_run_summary_json': rel_record(copy_checked(summary_path, metadata_root / 'campaign_run_summary.json', replacements=replacements), output_root),
        'campaign_run_summary_md': rel_record(copy_checked(summary_md_path, metadata_root / 'campaign_run_summary.md', replacements=replacements), output_root),
        'campaign_manifest_json': rel_record(copy_checked(manifest_path, metadata_root / 'campaign_manifest.json', replacements=replacements), output_root),
        'campaign_manifest_md': rel_record(copy_checked(manifest_md_path, metadata_root / 'campaign_manifest.md', replacements=replacements), output_root),
    }

    cases = []
    seen_names = set()
    suites = []
    for raw_case in summary['cases']:
        name = str(raw_case.get('name', ''))
        require(name, 'case missing name')
        require(name not in seen_names, f'duplicate case name: {name}')
        seen_names.add(name)
        suite = str(raw_case.get('suite', ''))
        if suite not in suites:
            suites.append(suite)
        require(raw_case.get('status') == 'PASS', f'{name} status is not PASS')
        require(int(raw_case.get('returncode', -1)) == 0, f'{name} returncode is not zero')
        require(not raw_case.get('missing_required_files'), f'{name} has missing required files')
        require(not raw_case.get('log_failure_markers'), f'{name} has failure markers')

        case_root = output_root / 'cases' / name
        case_log = rel_record(copy_checked(Path(raw_case['case_log']), case_root / 'campaign_case.log', replacements=replacements), output_root)
        required_files = raw_case.get('required_files')
        hashes = raw_case.get('required_file_hashes')
        require(isinstance(required_files, list) and required_files, f'{name} missing required_files')
        require(isinstance(hashes, list), f'{name} missing required_file_hashes')
        require(len(required_files) == len(hashes), f'{name} required hash count mismatch')

        packed_required = []
        seen_required = set()
        for item in hashes:
            src = Path(str(item.get('path', '')))
            dst = case_root / src.name
            packed = copy_checked(src, dst, str(item.get('sha256', '')), replacements=replacements)
            packed_required.append(rel_record(packed, output_root))
            seen_required.add(src.name)
        require(seen_required == set(required_files), f'{name} required file names do not match hashed files')

        script_path = Path(str(raw_case.get('script', '')))
        require(script_path.is_file(), f'{name} missing wrapper script: {script_path}')
        cases.append({
            'name': name,
            'suite': suite,
            'status': 'PASS',
            'script_path': str(script_path),
            'script_sha256': sha256_file(script_path),
            'command': raw_case.get('command', []),
            'duration_s': float(raw_case.get('duration_s', 0.0)),
            'timeout_s': int(raw_case.get('timeout_s', 0)),
            'started_at_utc': raw_case.get('started_at_utc'),
            'finished_at_utc': raw_case.get('finished_at_utc'),
            'description': raw_case.get('description', ''),
            'case_log': case_log,
            'required_files': packed_required,
        })

    pack = {
        'schema_version': 1,
        'status': 'PASS',
        'pack_type': 'engineering-h2-production-release-evidence',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'source_run_summary': str(summary_path),
        'source_output_root': summary.get('output_root'),
        'sanitization': {
            'enabled': True,
            'replacement_labels': [
                {'from': 'absolute_repo_root', 'to': '${REPO_ROOT}'},
                {'from': 'absolute_user_home', 'to': '${USER_HOME}'},
            ],
        },
        'campaign': summary.get('campaign'),
        'suite': summary.get('suite'),
        'case_count': len(cases),
        'suite_count': len(suites),
        'suites': suites,
        'source_files': source_files,
        'repo': compact_repo_metadata(summary.get('repo', {})),
        'host': summary.get('host', {}),
        'cases': cases,
        'limitations': [
            'This pack preserves runner summaries, case logs, required output files, and SHA-256 hashes for the smoke-scale engineering H2 production campaign.',
            'It does not include full AMReX plotfile directories or prove production-size accuracy, scheduler affinity, overnight stability, fire heat-release validation, or reference-data agreement.',
        ],
    }
    pack_path = output_root / 'evidence_pack_manifest.json'
    pack_path.write_text(json.dumps(pack, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    verify_pack(pack_path)
    write_markdown(pack, output_root / 'README.md')
    return pack


def verify_file_record(record: dict[str, Any], output_root: Path, label: str) -> None:
    path = output_root / str(record['path'])
    require(path.is_file(), f'missing packed {label}: {path}')
    actual = sha256_file(path)
    require(actual == record['sha256'], f'packed {label} hash mismatch: {path}')
    require(path.stat().st_size == int(record['size_bytes']), f'packed {label} size mismatch: {path}')


def verify_pack(pack_path: Path) -> dict[str, Any]:
    pack_path = pack_path.resolve()
    pack = read_json(pack_path)
    output_root = pack_path.parent
    require(pack.get('schema_version') == 1, f'{pack_path} schema_version is not 1')
    require(pack.get('status') == 'PASS', f'{pack_path} status is not PASS')
    require(pack.get('pack_type') == 'engineering-h2-production-release-evidence', f'{pack_path} unexpected pack_type')
    cases = pack.get('cases')
    require(isinstance(cases, list) and cases, f'{pack_path} missing cases')
    require(int(pack.get('case_count', -1)) == len(cases), f'{pack_path} case_count mismatch')
    for name, record in pack.get('source_files', {}).items():
        verify_file_record(record, output_root, name)
    seen_names = set()
    for case in cases:
        name = case.get('name')
        require(name and name not in seen_names, f'duplicate or missing case name: {name}')
        seen_names.add(name)
        require(case.get('status') == 'PASS', f'{name} status is not PASS')
        verify_file_record(case['case_log'], output_root, f'{name} case log')
        required = case.get('required_files')
        require(isinstance(required, list) and required, f'{name} missing packed required files')
        for item in required:
            verify_file_record(item, output_root, f'{name} required file')
        script_path = Path(str(case.get('script_path', '')))
        require(script_path.is_file(), f'{name} missing repo wrapper script: {script_path}')
        require(sha256_file(script_path) == case.get('script_sha256'), f'{name} wrapper script hash mismatch')
    return pack


def write_markdown(pack: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Production Release Evidence Pack',
        '',
        f"Status: `{pack['status']}`",
        f"Campaign: `{pack['campaign']}`",
        f"Suite: `{pack['suite']}`",
        f"Generated UTC: `{pack['generated_at_utc']}`",
        f"Case count: `{pack['case_count']}`",
        f"Suites: `{', '.join(pack['suites'])}`",
        '',
        '## Source Files',
        '',
    ]
    for name, record in pack['source_files'].items():
        sanitized = ' sanitized' if record.get('sanitized') else ''
        lines.append(f"- `{name}`: `{record['path']}` sha256 `{record['sha256'][:16]}`{sanitized}")
    lines.extend(['', '## Cases', ''])
    for case in pack['cases']:
        req = ', '.join(item['sha256'][:16] for item in case['required_files'])
        lines.extend([
            f"### {case['name']}",
            '',
            f"- Suite: `{case['suite']}`",
            f"- Duration seconds: `{case['duration_s']:.2f}`",
            f"- Script: `{case['script_path']}`",
            f"- Script SHA-256: `{case['script_sha256'][:16]}`",
            f"- Case log sanitized: `{case['case_log'].get('sanitized', False)}`",
            f"- Required files: `{len(case['required_files'])}`",
            f"- Required SHA-256 prefixes: `{req}`",
            '',
        ])
    lines.extend(['## Limitations', ''])
    for item in pack['limitations']:
        lines.append(f'- {item}')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    package = sub.add_parser('package', help='Create a durable release evidence pack from a campaign run summary')
    package.add_argument('--run-summary', required=True, type=Path, help='Campaign runner summary JSON')
    package.add_argument('--campaign-manifest', type=Path, help='Campaign manifest JSON; defaults next to run summary')
    package.add_argument('--output-root', required=True, type=Path, help='Output evidence pack directory')
    package.add_argument('--force', action='store_true', help='Allow writing into a non-empty output directory')
    verify = sub.add_parser('verify', help='Verify an existing evidence pack manifest')
    verify.add_argument('--pack-manifest', required=True, type=Path, help='Packed evidence_pack_manifest.json')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == 'package':
            pack = package_evidence(args)
            print(
                'engineering_h2_release_evidence_pack PASS '
                f'cases={pack["case_count"]} output={args.output_root} manifest={args.output_root / "evidence_pack_manifest.json"}'
            )
        elif args.command == 'verify':
            pack = verify_pack(args.pack_manifest)
            print(
                'engineering_h2_release_evidence_pack VERIFY-PASS '
                f'cases={pack["case_count"]} manifest={args.pack_manifest}'
            )
        else:
            raise EvidencePackError(f'unknown command: {args.command}')
    except EvidencePackError as exc:
        raise SystemExit(f'engineering_h2_release_evidence_pack FAIL {exc}') from exc
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
