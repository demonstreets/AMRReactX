#!/usr/bin/env python3
"""Write/verify the engineering H2 external evidence operations dashboard."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_READY = 'PASS-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD'
STATUS_NOT_READY = 'NOT_READY-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_evidence_operations_dashboard.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_evidence_operations_dashboard.md'
DEFAULT_SCORECARD = Path(
    'docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json'
)
DEFAULT_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/'
    'h2_blocker_clearance_preflight_report.json'
)
DEFAULT_DATA_ROOM = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724/'
    'h2_production_blocker_data_room_report.json'
)
DEFAULT_CLOSURE = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_DROP = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
    'h2_external_artifact_drop_validator_report.json'
)
DEFAULT_INGESTION_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_ingestion_plan_20260724/'
    'h2_external_artifact_ingestion_plan.json'
)
DEFAULT_CONTROLLED_COPY = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_controlled_copy_20260724/'
    'h2_external_artifact_controlled_copy_report.json'
)


class DashboardError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DashboardError(message)


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
        raise DashboardError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise DashboardError(f'invalid JSON evidence {path}: {exc}') from exc
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


def domain_artifact_summary(
    closure: dict[str, Any],
    drop: dict[str, Any],
    ingestion_plan: dict[str, Any],
    controlled_copy: dict[str, Any],
) -> list[dict[str, Any]]:
    closure_domains = {
        str(item.get('domain')): item
        for item in closure.get('domain_closure_records', [])
        if isinstance(item, dict)
    }
    drop_domains = {
        str(item.get('domain')): item
        for item in drop.get('domain_records', [])
        if isinstance(item, dict)
    }
    plan_domains = {
        str(item.get('domain')): item
        for item in ingestion_plan.get('domain_ingestion_plans', [])
        if isinstance(item, dict)
    }
    copy_records: dict[str, list[dict[str, Any]]] = {}
    for item in controlled_copy.get('copy_action_records', []):
        if isinstance(item, dict):
            copy_records.setdefault(str(item.get('domain')), []).append(item)

    records = []
    for domain, closure_record in sorted(closure_domains.items()):
        artifacts = closure_record.get('artifact_records', [])
        artifact_count = len(artifacts) if isinstance(artifacts, list) else 0
        drop_record = drop_domains.get(domain, {})
        plan_record = plan_domains.get(domain, {})
        records.append(
            {
                'domain': domain,
                'blocker': closure_record.get('blocker'),
                'expected_artifact_count': artifact_count,
                'missing_artifact_count': closure_record.get('missing_artifact_count'),
                'drop_valid_artifact_count': drop_record.get('valid_artifact_count'),
                'drop_missing_or_invalid_artifact_count': drop_record.get('missing_or_invalid_artifact_count'),
                'ingestion_ready_copy_action_count': plan_record.get('ready_copy_action_count'),
                'ingestion_missing_or_invalid_action_count': plan_record.get('missing_or_invalid_action_count'),
                'controlled_copy_ready_action_count': sum(
                    1 for item in copy_records.get(domain, []) if item.get('source_valid_from_plan') is True
                ),
                'controlled_copy_copied_file_count': sum(
                    int(item.get('copied_file_count', 0)) for item in copy_records.get(domain, [])
                ),
                'ready_for_domain_controlled_copy': (
                    int(plan_record.get('ready_copy_action_count', 0)) == artifact_count and artifact_count > 0
                ),
            }
        )
    return records


def next_operator_commands() -> list[dict[str, str]]:
    return [
        {
            'step': 'stage_external_artifacts',
            'command': 'place supplier/lab files under docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/drop/',
            'purpose': 'Populate the real-CAD, SBEPV5, and fire-calibration drop folders without touching controlled evidence.',
        },
        {
            'step': 'validate_drop',
            'command': 'python3 tools/write_engineering_h2_external_artifact_drop_validator.py',
            'purpose': 'Validate file presence, schemas, columns, counts, and domain-specific identifiers.',
        },
        {
            'step': 'plan_ingestion',
            'command': 'python3 tools/write_engineering_h2_external_artifact_ingestion_plan.py',
            'purpose': 'Regenerate controlled-copy source/target mapping from validated drop evidence.',
        },
        {
            'step': 'dry_run_controlled_copy',
            'command': 'python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
            'purpose': 'Inspect target conflicts and copy readiness without writing evidence files.',
        },
        {
            'step': 'apply_controlled_copy',
            'command': 'python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py --apply --confirm-controlled-copy H2_EXTERNAL_ARTIFACTS_READY',
            'purpose': 'Copy only after every external artifact gate is PASS and the operator explicitly confirms.',
        },
        {
            'step': 'rebuild_and_verify',
            'command': 'bash tools/rebuild_engineering_h2_evidence_chain.sh',
            'purpose': 'Rebuild all dependent evidence, run the verifier, and update the production-readiness ledger.',
        },
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    scorecard_path = Path(args.scorecard)
    preflight_path = Path(args.blocker_clearance_preflight_report)
    data_room_path = Path(args.production_blocker_data_room_report)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    drop_path = Path(args.external_artifact_drop_validator_report)
    ingestion_path = Path(args.external_artifact_ingestion_plan_report)
    controlled_copy_path = Path(args.external_artifact_controlled_copy_report)

    scorecard = load_json(scorecard_path)
    preflight = load_json(preflight_path)
    data_room = load_json(data_room_path)
    closure = load_json(closure_path)
    drop = load_json(drop_path)
    ingestion_plan = load_json(ingestion_path)
    controlled_copy = load_json(controlled_copy_path)

    total_expected = int(drop.get('total_expected_artifact_count', 0))
    valid_artifacts = int(drop.get('valid_artifact_count', 0))
    ready_actions = int(ingestion_plan.get('ready_copy_action_count', 0))
    copied_files = int(controlled_copy.get('copied_file_count', 0))
    remaining_blockers = int(preflight.get('remaining_blocker_count', 0))
    missing_artifacts = int(data_room.get('missing_artifact_count', closure.get('total_missing_artifact_count', 0)))
    ready = (
        remaining_blockers == 0
        and total_expected == 14
        and valid_artifacts == total_expected
        and ready_actions == total_expected
        and controlled_copy.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
        and controlled_copy.get('applied_copy_actions') is True
    )
    status = STATUS_READY if ready else STATUS_NOT_READY
    domains = domain_artifact_summary(closure, drop, ingestion_plan, controlled_copy)
    quality_gate_matrix = [
        {
            'name': 'scorecard_attached',
            'status': 'PASS' if scorecard.get('status') in {'PRODUCTION_READY', 'NOT_PRODUCTION_READY'} else 'MISSING',
            'evidence': str(scorecard_path),
            'gap': '',
        },
        {
            'name': 'blocker_preflight_attached',
            'status': 'PASS'
            if preflight.get('status') in {'PASS-H2-BLOCKER-CLEARANCE-PREFLIGHT', 'NOT_READY-H2-BLOCKER-CLEARANCE-PREFLIGHT'}
            else 'MISSING',
            'evidence': str(preflight_path),
            'gap': '',
        },
        {
            'name': 'drop_ingestion_controlled_copy_counts_match',
            'status': 'PASS'
            if total_expected == int(ingestion_plan.get('total_copy_action_count', -1)) == int(controlled_copy.get('total_copy_action_count', -2))
            else 'MISSING',
            'evidence': f'drop={total_expected} ingestion={ingestion_plan.get("total_copy_action_count")} controlled_copy={controlled_copy.get("total_copy_action_count")}',
            'gap': '',
        },
        {
            'name': 'not_ready_preserves_blockers',
            'status': 'PASS' if ready or remaining_blockers >= 1 else 'MISSING',
            'evidence': f'remaining_blockers={remaining_blockers}',
            'gap': '',
        },
        {
            'name': 'controlled_copy_does_not_clear_blockers',
            'status': 'PASS' if controlled_copy.get('does_not_clear_production_blockers') is True else 'MISSING',
            'evidence': str(controlled_copy_path),
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 External Evidence Operations Dashboard',
        'scorecard_report': str(scorecard_path),
        'blocker_clearance_preflight_report': str(preflight_path),
        'production_blocker_data_room_report': str(data_room_path),
        'production_blocker_closure_manifest_report': str(closure_path),
        'external_artifact_drop_validator_report': str(drop_path),
        'external_artifact_ingestion_plan_report': str(ingestion_path),
        'external_artifact_controlled_copy_report': str(controlled_copy_path),
        'current_status': {
            'scorecard_status': scorecard.get('status'),
            'functional_coverage_percent': scorecard.get('functional_coverage_percent'),
            'production_credibility_percent': scorecard.get('production_credibility_percent'),
            'remaining_blocker_count': remaining_blockers,
            'missing_external_artifact_count': missing_artifacts,
            'total_expected_external_artifact_count': total_expected,
            'drop_status': drop.get('status'),
            'drop_valid_artifact_count': valid_artifacts,
            'ingestion_plan_status': ingestion_plan.get('status'),
            'ingestion_ready_copy_action_count': ready_actions,
            'controlled_copy_status': controlled_copy.get('status'),
            'controlled_copy_ready_action_count': controlled_copy.get('ready_copy_action_count'),
            'controlled_copy_copied_file_count': copied_files,
            'controlled_copy_apply_requested': controlled_copy.get('apply_requested'),
            'ready_for_production_blocker_clearance': ready,
        },
        'domain_artifact_status': domains,
        'next_operator_commands': next_operator_commands(),
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_production_scorecard', scorecard_path),
            evidence_entry('engineering_h2_blocker_clearance_preflight_report', preflight_path),
            evidence_entry('engineering_h2_production_blocker_data_room_report', data_room_path),
            evidence_entry('engineering_h2_production_blocker_closure_manifest_report', closure_path),
            evidence_entry('engineering_h2_external_artifact_drop_validator_report', drop_path),
            evidence_entry('engineering_h2_external_artifact_ingestion_plan_report', ingestion_path),
            evidence_entry('engineering_h2_external_artifact_controlled_copy_report', controlled_copy_path),
        ],
        'limitations': [
            'This dashboard summarizes authoritative evidence reports; it does not launch CFD cases.',
            'It does not copy external artifacts and does not clear production blockers.',
            'Production readiness can only change after controlled evidence is copied, dependent reports are rebuilt, and the full verifier passes.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    status = data.get('current_status')
    require(isinstance(status, dict), 'current_status missing')
    require(int(status.get('total_expected_external_artifact_count', 0)) == 14, 'expected external artifact count must be 14')
    require(status.get('drop_status') in {'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'}, 'invalid drop status')
    require(
        status.get('ingestion_plan_status')
        in {'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'},
        'invalid ingestion plan status',
    )
    require(
        status.get('controlled_copy_status')
        in {
            'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY',
            'DRYRUN-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY',
            'PASS-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY',
        },
        'invalid controlled-copy status',
    )
    require(data.get('does_not_clear_production_blockers') is True, 'dashboard must not clear blockers')
    domains = data.get('domain_artifact_status')
    require(isinstance(domains, list) and len(domains) == 3, 'domain_artifact_status must contain three domains')
    commands = data.get('next_operator_commands')
    require(isinstance(commands, list) and len(commands) >= 6, 'next_operator_commands incomplete')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'quality gate failed')
    if data.get('status') == STATUS_READY:
        require(status.get('ready_for_production_blocker_clearance') is True, 'PASS dashboard is not ready for clearance')
        require(int(status.get('remaining_blocker_count', -1)) == 0, 'PASS dashboard has remaining blockers')
        require(int(status.get('missing_external_artifact_count', -1)) == 0, 'PASS dashboard has missing artifacts')
    else:
        require(status.get('ready_for_production_blocker_clearance') is False, 'NOT_READY dashboard marked ready')
        require(int(status.get('remaining_blocker_count', 0)) >= 1, 'NOT_READY dashboard must retain blockers')
        require(int(status.get('missing_external_artifact_count', 0)) >= 1, 'NOT_READY dashboard must retain missing artifacts')
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
        '# Engineering H2 External Evidence Operations Dashboard',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Current Status',
        '',
    ]
    for key, value in report['current_status'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Domain Artifact Status', '']
    for item in report['domain_artifact_status']:
        lines.append(
            f"- `{item['domain']}`: drop `{item['drop_valid_artifact_count']}/{item['expected_artifact_count']}`, "
            f"ingestion `{item['ingestion_ready_copy_action_count']}/{item['expected_artifact_count']}`, "
            f"copied files `{item['controlled_copy_copied_file_count']}`"
        )
    lines += ['', '## Next Operator Commands', '']
    for item in report['next_operator_commands']:
        lines.append(f"- `{item['step']}`: `{item['command']}`")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
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
    parser.add_argument('--scorecard', default=str(DEFAULT_SCORECARD))
    parser.add_argument('--blocker-clearance-preflight-report', default=str(DEFAULT_PREFLIGHT))
    parser.add_argument('--production-blocker-data-room-report', default=str(DEFAULT_DATA_ROOM))
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE))
    parser.add_argument('--external-artifact-drop-validator-report', default=str(DEFAULT_DROP))
    parser.add_argument('--external-artifact-ingestion-plan-report', default=str(DEFAULT_INGESTION_PLAN))
    parser.add_argument('--external-artifact-controlled-copy-report', default=str(DEFAULT_CONTROLLED_COPY))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            status = report['current_status']
            print(
                'engineering_h2_external_evidence_operations_dashboard VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"drop={status['drop_valid_artifact_count']}/{status['total_expected_external_artifact_count']} "
                f"remaining={status['remaining_blocker_count']}"
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
        status = report['current_status']
        print(
            'engineering_h2_external_evidence_operations_dashboard PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"drop={status['drop_valid_artifact_count']}/{status['total_expected_external_artifact_count']} "
            f"remaining={status['remaining_blocker_count']}"
        )
        return 0
    except DashboardError as exc:
        print(f'engineering_h2_external_evidence_operations_dashboard FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
