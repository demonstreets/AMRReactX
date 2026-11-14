#!/usr/bin/env python3
"""Write/verify the engineering H2 external artifact ingestion plan."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS_READY = 'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'
STATUS_NOT_READY = 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_ingestion_plan_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_ingestion_plan.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_ingestion_plan.md'
DEFAULT_DROP_VALIDATOR = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
    'h2_external_artifact_drop_validator_report.json'
)
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)

DOMAIN_REBUILD_COMMANDS = {
    'real_cad_cleanup': [
        'python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py',
        'python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py',
    ],
    'external_plume_shape_reference': [
        'python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py',
        'python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py',
        'python3 tools/write_engineering_h2_reference_agreement_report.py --external-plume-dataset-json <generated_external_plume_dataset_json>',
        'python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py',
    ],
    'fire_consequence_calibration': [
        'python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py',
        'python3 tools/write_engineering_h2_fire_calibration_package_report.py',
        'python3 tools/write_engineering_h2_fire_calibration_dataset_report.py',
        'python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --calibration-dataset-json <generated_fire_calibration_dataset_json>',
    ],
}

FINAL_REBUILD_COMMANDS = [
    'python3 tools/write_engineering_production_scorecard.py --output-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json --output-md docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md',
    'python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py',
    'python3 tools/write_engineering_h2_production_blocker_data_room_report.py',
    'python3 tools/write_engineering_h2_production_blocker_closure_manifest_report.py',
    'python3 tools/write_engineering_h2_external_evidence_intake_kit_manifest.py',
    'python3 tools/write_engineering_h2_external_artifact_drop_validator.py',
    'python3 tools/write_engineering_h2_external_artifact_ingestion_plan.py',
    'python3 tools/write_engineering_h2_production_handoff_report.py',
    'python3 tools/write_engineering_h2_master_plan_traceability_report.py',
    'bash tools/rebuild_engineering_h2_evidence_chain.sh',
]


class IngestionPlanError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IngestionPlanError(message)


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
        raise IngestionPlanError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise IngestionPlanError(f'invalid JSON evidence {path}: {exc}') from exc
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


def closure_domain_map(closure: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = closure.get('domain_closure_records')
    require(isinstance(records, list) and records, 'closure manifest domain records missing')
    return {str(item.get('domain')): item for item in records if isinstance(item, dict)}


def target_path_for(closure_domains: dict[str, dict[str, Any]], domain: str, artifact: str) -> str:
    record = closure_domains.get(domain, {})
    artifacts = record.get('artifact_records')
    require(isinstance(artifacts, list), f'{domain} closure artifacts missing')
    for item in artifacts:
        if isinstance(item, dict) and item.get('artifact') == artifact:
            return str(item.get('target_path', ''))
    raise IngestionPlanError(f'{domain} artifact target missing: {artifact}')


def copy_action(drop_validation: dict[str, Any], target_path: str, domain_quality_gaps: list[str]) -> dict[str, Any]:
    source_path = str(drop_validation.get('path', ''))
    target_is_directory = target_path.endswith('/') or '*' in source_path
    gaps = list(drop_validation.get('gaps', []))
    if domain_quality_gaps:
        gaps.extend(f'domain_quality_gap:{gap}' for gap in domain_quality_gaps[:20])
    return {
        'source_path': source_path,
        'target_path': target_path,
        'target_is_directory': target_is_directory,
        'copy_mode': 'directory_contents' if target_is_directory else 'single_file',
        'source_valid': drop_validation.get('valid') is True and not domain_quality_gaps,
        'source_sha256': drop_validation.get('sha256'),
        'source_size_bytes': drop_validation.get('size_bytes'),
        'gaps': gaps,
    }


def domain_plan(drop_domain: dict[str, Any], closure_domains: dict[str, dict[str, Any]]) -> dict[str, Any]:
    domain = str(drop_domain.get('domain', ''))
    validations = drop_domain.get('artifact_validations')
    require(isinstance(validations, list), f'{domain} artifact validations missing')
    raw_domain_quality_gaps = drop_domain.get('domain_quality_gaps', [])
    domain_quality_gaps = [str(item) for item in raw_domain_quality_gaps] if isinstance(raw_domain_quality_gaps, list) else []
    actions = []
    for item in validations:
        require(isinstance(item, dict), f'{domain} validation item is not an object')
        artifact = str(item.get('artifact', ''))
        drop_validation = item.get('drop_validation')
        require(isinstance(drop_validation, dict), f'{domain} {artifact} drop_validation missing')
        target = target_path_for(closure_domains, domain, artifact)
        actions.append(
            {
                'artifact': artifact,
                'copy_action': copy_action(drop_validation, target, domain_quality_gaps),
            }
        )
    ready_actions = [item for item in actions if item['copy_action']['source_valid']]
    return {
        'domain': domain,
        'blocker': drop_domain.get('blocker'),
        'artifact_count': len(actions),
        'ready_copy_action_count': len(ready_actions),
        'missing_or_invalid_action_count': len(actions) - len(ready_actions),
        'domain_quality_gap_count': len(domain_quality_gaps),
        'domain_quality_gaps': domain_quality_gaps,
        'ready_for_domain_ingestion': len(actions) == len(ready_actions) and not domain_quality_gaps,
        'copy_actions': actions,
        'domain_rebuild_command_sequence': DOMAIN_REBUILD_COMMANDS.get(domain, []),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    drop_path = Path(args.external_artifact_drop_validator_report)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    drop = load_json(drop_path)
    closure = load_json(closure_path)
    closure_domains = closure_domain_map(closure)
    drop_domains = drop.get('domain_records')
    require(isinstance(drop_domains, list) and drop_domains, 'drop validator domain_records missing')
    plans = [domain_plan(item, closure_domains) for item in drop_domains if isinstance(item, dict)]
    total_actions = sum(int(item['artifact_count']) for item in plans)
    ready_actions = sum(int(item['ready_copy_action_count']) for item in plans)
    missing_actions = total_actions - ready_actions
    ready = (
        total_actions > 0
        and ready_actions == total_actions
        and drop.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-DROP'
        and drop.get('ready_for_controlled_ingestion') is True
    )
    status = STATUS_READY if ready else STATUS_NOT_READY
    quality_gate_matrix = [
        {
            'name': 'drop_validator_attached',
            'status': 'PASS'
            if drop.get('status') in {'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'}
            else 'MISSING',
            'evidence': str(drop_path),
            'gap': '',
        },
        {
            'name': 'closure_manifest_attached',
            'status': 'PASS' if closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST' else 'MISSING',
            'evidence': str(closure_path),
            'gap': '',
        },
        {
            'name': 'copy_action_count_matches_drop_artifact_count',
            'status': 'PASS' if total_actions == int(drop.get('total_expected_artifact_count', -1)) else 'MISSING',
            'evidence': f'plan={total_actions} drop={drop.get("total_expected_artifact_count")}',
            'gap': '',
        },
        {
            'name': 'not_ready_preserves_invalid_actions',
            'status': 'PASS' if ready or missing_actions >= 1 else 'MISSING',
            'evidence': f'missing_or_invalid_actions={missing_actions}',
            'gap': '',
        },
        {
            'name': 'does_not_apply_copy_actions',
            'status': 'PASS',
            'evidence': 'plan-only report; no files are copied',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 External Artifact Ingestion Plan',
        'external_artifact_drop_validator_report': str(drop_path),
        'production_blocker_closure_manifest_report': str(closure_path),
        'total_copy_action_count': total_actions,
        'ready_copy_action_count': ready_actions,
        'missing_or_invalid_copy_action_count': missing_actions,
        'ready_for_controlled_copy': ready,
        'ready_for_domain_ingestion': ready,
        'remaining_blocker_count': closure.get('remaining_blocker_count'),
        'does_not_apply_copy_actions': True,
        'does_not_clear_production_blockers': True,
        'domain_ingestion_plans': plans,
        'final_rebuild_command_sequence_after_copy': FINAL_REBUILD_COMMANDS,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('external_artifact_drop_validator_report', drop_path),
            evidence_entry('production_blocker_closure_manifest_report', closure_path),
        ],
        'limitations': [
            'This plan records copy targets and rebuild commands only; it does not copy external artifacts.',
            'Production readiness can only change after a PASS drop is copied into controlled paths and the full rebuild/verifier chain passes.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(int(data.get('total_copy_action_count', 0)) == 14, 'copy action count must be 14')
    require(data.get('does_not_apply_copy_actions') is True, 'ingestion plan must not apply copy actions')
    require(data.get('does_not_clear_production_blockers') is True, 'ingestion plan must not clear blockers')
    if data.get('status') == STATUS_READY:
        require(data.get('ready_for_controlled_copy') is True, 'PASS plan is not ready for copy')
        require(int(data.get('missing_or_invalid_copy_action_count', -1)) == 0, 'PASS plan has invalid copy actions')
    else:
        require(data.get('ready_for_controlled_copy') is False, 'NOT_READY plan marked ready')
        require(int(data.get('missing_or_invalid_copy_action_count', 0)) >= 1, 'NOT_READY plan must retain invalid actions')
    plans = data.get('domain_ingestion_plans')
    require(isinstance(plans, list) and len(plans) == 3, 'domain ingestion plans must contain three domains')
    for plan in plans:
        require(isinstance(plan, dict), 'domain plan is not an object')
        commands = plan.get('domain_rebuild_command_sequence')
        require(isinstance(commands, list) and commands, f"{plan.get('domain')} rebuild command sequence missing")
        actions = plan.get('copy_actions')
        require(isinstance(actions, list) and actions, f"{plan.get('domain')} copy actions missing")
        for action in actions:
            require(isinstance(action, dict), 'copy action is not an object')
            copy = action.get('copy_action')
            require(isinstance(copy, dict), 'copy_action missing')
            require(str(copy.get('source_path', '')).strip(), 'copy action missing source path')
            require(str(copy.get('target_path', '')).strip(), 'copy action missing target path')
    final_commands = data.get('final_rebuild_command_sequence_after_copy')
    require(isinstance(final_commands, list) and final_commands, 'final rebuild commands missing')
    require(final_commands[-1] == 'bash tools/rebuild_engineering_h2_evidence_chain.sh', 'final rebuild command mismatch')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'quality gate failed')
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
        '# Engineering H2 External Artifact Ingestion Plan',
        '',
        f"Status: `{report['status']}`",
        f"Total copy actions: `{report['total_copy_action_count']}`",
        f"Ready copy actions: `{report['ready_copy_action_count']}`",
        f"Missing or invalid copy actions: `{report['missing_or_invalid_copy_action_count']}`",
        f"Ready for controlled copy: `{report['ready_for_controlled_copy']}`",
        '',
        '## Domain Plans',
        '',
    ]
    for plan in report['domain_ingestion_plans']:
        lines.append(f"### {plan['domain']}")
        lines.append(f"- Copy actions: `{plan['ready_copy_action_count']}/{plan['artifact_count']}`")
        lines.append(f"- Ready: `{plan['ready_for_domain_ingestion']}`")
        for action in plan['copy_actions']:
            copy = action['copy_action']
            lines.append(f"- `{action['artifact']}`: `{copy['source_path']}` -> `{copy['target_path']}` valid=`{copy['source_valid']}`")
        lines.append('')
    lines += ['## Final Rebuild Commands After Copy', '']
    for command in report['final_rebuild_command_sequence_after_copy']:
        lines.append(f'- `{command}`')
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
    parser.add_argument('--external-artifact-drop-validator-report', default=str(DEFAULT_DROP_VALIDATOR))
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_external_artifact_ingestion_plan VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"ready={report['ready_copy_action_count']}/{report['total_copy_action_count']}"
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
            'engineering_h2_external_artifact_ingestion_plan PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"ready={report['ready_copy_action_count']}/{report['total_copy_action_count']}"
        )
        return 0
    except IngestionPlanError as exc:
        print(f'engineering_h2_external_artifact_ingestion_plan FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
