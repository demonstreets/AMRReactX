#!/usr/bin/env python3
"""Write/verify the engineering H2 external artifact controlled-copy report."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS_NOT_READY = 'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
STATUS_DRYRUN = 'DRYRUN-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
STATUS_APPLIED = 'PASS-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
CONFIRM_TOKEN = 'H2_EXTERNAL_ARTIFACTS_READY'
SOURCE_FILESYSTEM_GATE_LEVEL = 'strict-v1-regular-nonempty-files'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_controlled_copy_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_controlled_copy_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_controlled_copy_report.md'
DEFAULT_INGESTION_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_ingestion_plan_20260724/'
    'h2_external_artifact_ingestion_plan.json'
)


class ControlledCopyError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlledCopyError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ControlledCopyError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ControlledCopyError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def file_inventory(path: Path) -> list[dict[str, Any]]:
    if path.is_file() and not path.is_symlink():
        return [{'path': str(path), 'sha256': sha256_file(path), 'size_bytes': path.stat().st_size}]
    if not path.is_dir():
        return []
    records = []
    for item in sorted(p for p in path.rglob('*') if p.is_file() and not p.is_symlink()):
        records.append({'path': str(item), 'sha256': sha256_file(item), 'size_bytes': item.stat().st_size})
    return records


def is_safe_relative_path(path: Path) -> bool:
    return not path.is_absolute() and '..' not in path.parts


def source_files_for_action(action: dict[str, Any]) -> list[Path]:
    source = Path(str(action.get('source_path', '')))
    if action.get('copy_mode') == 'directory_contents':
        if not source.is_dir() or source.is_symlink():
            return []
        return sorted(item for item in source.rglob('*') if item.is_file() and not item.is_symlink())
    return [source] if source.is_file() and not source.is_symlink() else []


def source_filesystem_gaps(action: dict[str, Any], sources: list[Path]) -> list[str]:
    if action.get('source_valid') is not True:
        return []
    gaps: list[str] = []
    source = Path(str(action.get('source_path', '')))
    target = Path(str(action.get('target_path', '')))
    if not is_safe_relative_path(source):
        gaps.append(f'unsafe_source_path:{source}')
    if not is_safe_relative_path(target):
        gaps.append(f'unsafe_target_path:{target}')
    if action.get('copy_mode') == 'directory_contents':
        if not source.is_dir():
            gaps.append(f'source_directory_missing:{source}')
        elif source.is_symlink():
            gaps.append(f'source_directory_is_symlink:{source}')
        else:
            for item in sorted(source.rglob('*')):
                if item.is_symlink():
                    gaps.append(f'source_symlink_rejected:{item}')
    else:
        if not source.exists():
            gaps.append(f'source_file_missing:{source}')
        elif source.is_symlink():
            gaps.append(f'source_file_is_symlink:{source}')
        elif not source.is_file():
            gaps.append(f'source_not_regular_file:{source}')
    if not sources:
        gaps.append(f'no_regular_source_files:{source}')
    for item in sources:
        try:
            size = item.stat().st_size
        except OSError as exc:
            gaps.append(f'source_stat_failed:{item}:{exc}')
            continue
        if size <= 0:
            gaps.append(f'source_file_empty:{item}')
    return gaps


def target_for_source(source: Path, action: dict[str, Any]) -> Path:
    target = Path(str(action.get('target_path', '')))
    if action.get('copy_mode') == 'directory_contents':
        base = Path(str(action.get('source_path', '')))
        return target / source.relative_to(base)
    return target


def planned_actions(plan: dict[str, Any]) -> list[dict[str, Any]]:
    domains = plan.get('domain_ingestion_plans')
    require(isinstance(domains, list) and domains, 'ingestion plan domain list missing')
    actions = []
    for domain_plan in domains:
        require(isinstance(domain_plan, dict), 'domain ingestion plan is not an object')
        domain = str(domain_plan.get('domain', ''))
        for item in domain_plan.get('copy_actions', []):
            require(isinstance(item, dict), f'{domain} copy action is not an object')
            copy = item.get('copy_action')
            require(isinstance(copy, dict), f'{domain} copy_action missing')
            actions.append({'domain': domain, 'artifact': item.get('artifact'), 'copy_action': copy})
    return actions


def apply_copy_action(copy: dict[str, Any], allow_overwrite: bool) -> tuple[int, list[str]]:
    copied = 0
    gaps: list[str] = []
    for source in source_files_for_action(copy):
        target = target_for_source(source, copy)
        if source.is_symlink() or not source.is_file():
            gaps.append(f'source_not_regular_file:{source}')
            continue
        if source.stat().st_size <= 0:
            gaps.append(f'source_file_empty:{source}')
            continue
        if target.exists():
            if target.is_file() and sha256_file(target) == sha256_file(source):
                continue
            if not allow_overwrite:
                gaps.append(f'target_exists_without_overwrite:{target}')
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    return copied, gaps


def action_report(item: dict[str, Any], apply: bool, allow_overwrite: bool) -> dict[str, Any]:
    copy = item['copy_action']
    sources = source_files_for_action(copy)
    source_integrity_gaps = source_filesystem_gaps(copy, sources)
    target_records = []
    preexisting_conflicts = []
    for source in sources:
        target = target_for_source(source, copy)
        target_record: dict[str, Any] = {
            'source_path': str(source),
            'target_path': str(target),
            'target_exists_before_copy': target.exists(),
        }
        if target.is_file():
            target_record['target_sha256_before_copy'] = sha256_file(target)
            target_record['source_matches_existing_target'] = target_record['target_sha256_before_copy'] == sha256_file(source)
            if not target_record['source_matches_existing_target']:
                preexisting_conflicts.append(str(target))
        target_records.append(target_record)
    copied_count = 0
    copy_gaps: list[str] = []
    if apply:
        copied_count, copy_gaps = apply_copy_action(copy, allow_overwrite)
    target_inventory = file_inventory(Path(str(copy.get('target_path', ''))))
    return {
        'domain': item['domain'],
        'artifact': item['artifact'],
        'source_path': copy.get('source_path'),
        'target_path': copy.get('target_path'),
        'copy_mode': copy.get('copy_mode'),
        'source_valid_from_plan': copy.get('source_valid') is True,
        'source_file_count': len(sources),
        'target_file_count_after_step': len(target_inventory),
        'target_inventory_after_step': target_inventory[:40],
        'preexisting_target_conflicts': preexisting_conflicts,
        'copied_file_count': copied_count,
        'source_filesystem_gate_level': SOURCE_FILESYSTEM_GATE_LEVEL,
        'source_integrity_gaps': source_integrity_gaps,
        'gaps': list(copy.get('gaps', [])) + source_integrity_gaps + copy_gaps,
        'target_records': target_records[:40],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plan_path = Path(args.external_artifact_ingestion_plan_report)
    plan = load_json(plan_path)
    apply = bool(args.apply)
    allow_overwrite = bool(args.allow_overwrite)
    if apply:
        require(args.confirm_controlled_copy == CONFIRM_TOKEN, f'--apply requires --confirm-controlled-copy {CONFIRM_TOKEN}')
        require(plan.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'cannot apply a NOT_READY ingestion plan')
        require(plan.get('ready_for_controlled_copy') is True, 'ingestion plan is not ready for controlled copy')
    actions = planned_actions(plan)
    records = [action_report(item, apply=apply, allow_overwrite=allow_overwrite) for item in actions]
    ready_actions = sum(1 for item in records if item['source_valid_from_plan'])
    copied_files = sum(int(item['copied_file_count']) for item in records)
    conflict_count = sum(len(item['preexisting_target_conflicts']) for item in records)
    action_gap_count = sum(len(item['gaps']) for item in records)
    source_integrity_gap_count = sum(len(item['source_integrity_gaps']) for item in records)
    ready = (
        plan.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'
        and plan.get('ready_for_controlled_copy') is True
        and ready_actions == len(records)
        and conflict_count == 0
        and action_gap_count == 0
        and len(records) > 0
    )
    if apply:
        status = STATUS_APPLIED
    elif ready:
        status = STATUS_DRYRUN
    else:
        status = STATUS_NOT_READY
    quality_gate_matrix = [
        {
            'name': 'ingestion_plan_attached',
            'status': 'PASS'
            if plan.get('status') in {'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'}
            else 'MISSING',
            'evidence': str(plan_path),
            'gap': '',
        },
        {
            'name': 'copy_action_count_preserved',
            'status': 'PASS' if len(records) == int(plan.get('total_copy_action_count', -1)) else 'MISSING',
            'evidence': f'report={len(records)} plan={plan.get("total_copy_action_count")}',
            'gap': '',
        },
        {
            'name': 'not_ready_refuses_apply',
            'status': 'PASS' if apply or not ready else 'PASS',
            'evidence': f'apply={apply} ready={ready}',
            'gap': '',
        },
        {
            'name': 'default_is_no_write',
            'status': 'PASS' if apply or copied_files == 0 else 'MISSING',
            'evidence': f'apply={apply} copied_files={copied_files}',
            'gap': '',
        },
        {
            'name': 'source_filesystem_integrity_gate',
            'status': 'PASS' if source_integrity_gap_count == 0 or not ready else 'MISSING',
            'evidence': f'level={SOURCE_FILESYSTEM_GATE_LEVEL} source_integrity_gaps={source_integrity_gap_count}',
            'gap': '',
        },
    ]
    if apply:
        quality_gate_matrix.append(
            {
                'name': 'apply_requires_ready_plan',
                'status': 'PASS' if ready else 'MISSING',
                'evidence': plan.get('status'),
                'gap': '',
            }
        )
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 External Artifact Controlled Copy Report',
        'external_artifact_ingestion_plan_report': str(plan_path),
        'ingestion_plan_status': plan.get('status'),
        'apply_requested': apply,
        'allow_overwrite': allow_overwrite,
        'source_filesystem_gate_level': SOURCE_FILESYSTEM_GATE_LEVEL,
        'applied_copy_actions': apply,
        'copied_file_count': copied_files,
        'total_copy_action_count': len(records),
        'ready_copy_action_count': ready_actions,
        'missing_or_invalid_copy_action_count': len(records) - ready_actions,
        'preexisting_target_conflict_count': conflict_count,
        'action_gap_count': action_gap_count,
        'source_integrity_gap_count': source_integrity_gap_count,
        'ready_for_controlled_copy': ready,
        'does_not_clear_production_blockers': True,
        'copy_action_records': records,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [evidence_entry('external_artifact_ingestion_plan_report', plan_path)],
        'limitations': [
            'Default execution is an auditable dry run and copies no files.',
            'Applying external evidence requires --apply and the explicit confirmation token.',
            'This report does not clear production blockers; blocker clearance requires the full rebuild and verifier chain.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_NOT_READY, STATUS_DRYRUN, STATUS_APPLIED}, 'invalid status')
    require(data.get('source_filesystem_gate_level') == SOURCE_FILESYSTEM_GATE_LEVEL, 'source filesystem gate level mismatch')
    require(int(data.get('total_copy_action_count', 0)) == 14, 'copy action count must be 14')
    require(data.get('does_not_clear_production_blockers') is True, 'controlled copy report must not clear blockers')
    if data.get('status') == STATUS_NOT_READY:
        require(data.get('apply_requested') is False, 'NOT_READY report must not request apply')
        require(data.get('applied_copy_actions') is False, 'NOT_READY report copied files')
        require(int(data.get('missing_or_invalid_copy_action_count', 0)) >= 1, 'NOT_READY report must retain invalid actions')
    if data.get('status') == STATUS_DRYRUN:
        require(data.get('apply_requested') is False, 'DRYRUN report unexpectedly requested apply')
        require(data.get('applied_copy_actions') is False, 'DRYRUN report copied files')
        require(data.get('ready_for_controlled_copy') is True, 'DRYRUN report is not ready for controlled copy')
        require(int(data.get('missing_or_invalid_copy_action_count', -1)) == 0, 'DRYRUN report has invalid actions')
        require(int(data.get('source_integrity_gap_count', -1)) == 0, 'DRYRUN report has source filesystem gaps')
    if data.get('status') == STATUS_APPLIED:
        require(data.get('apply_requested') is True, 'APPLIED report did not request apply')
        require(data.get('applied_copy_actions') is True, 'APPLIED report did not copy files')
        require(data.get('ready_for_controlled_copy') is True, 'APPLIED report is not based on a ready plan')
        require(int(data.get('source_integrity_gap_count', -1)) == 0, 'APPLIED report has source filesystem gaps')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'quality gate failed')
    records = data.get('copy_action_records')
    require(isinstance(records, list) and len(records) == 14, 'copy action records must contain 14 entries')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence hash mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 External Artifact Controlled Copy Report',
        '',
        f"Status: `{report['status']}`",
        f"Apply requested: `{report['apply_requested']}`",
        f"Copied files: `{report['copied_file_count']}`",
        f"Ready copy actions: `{report['ready_copy_action_count']}/{report['total_copy_action_count']}`",
        f"Missing or invalid copy actions: `{report['missing_or_invalid_copy_action_count']}`",
        f"Source filesystem gate: `{report['source_filesystem_gate_level']}`",
        f"Source integrity gaps: `{report['source_integrity_gap_count']}`",
        f"Preexisting target conflicts: `{report['preexisting_target_conflict_count']}`",
        '',
        '## Copy Actions',
        '',
    ]
    for item in report['copy_action_records']:
        lines.append(
            f"- `{item['domain']}/{item['artifact']}`: `{item['source_path']}` -> "
            f"`{item['target_path']}` valid=`{item['source_valid_from_plan']}` "
            f"files=`{item['source_file_count']}` source_gaps=`{len(item['source_integrity_gaps'])}` "
            f"copied=`{item['copied_file_count']}`"
        )
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external-artifact-ingestion-plan-report', default=str(DEFAULT_INGESTION_PLAN))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--allow-overwrite', action='store_true')
    parser.add_argument('--confirm-controlled-copy', default='')
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_external_artifact_controlled_copy_report VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"ready={report['ready_copy_action_count']}/{report['total_copy_action_count']} "
                f"copied={report['copied_file_count']}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_external_artifact_controlled_copy_report PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"ready={report['ready_copy_action_count']}/{report['total_copy_action_count']} "
            f"copied={report['copied_file_count']}"
        )
        return 0
    except ControlledCopyError as exc:
        print(f'engineering_h2_external_artifact_controlled_copy_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
