#!/usr/bin/env python3
"""Write/verify the engineering H2 case-validation failure attribution report."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-CASE-VALIDATION-FAILURE-ATTRIBUTION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_failure_attribution_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_failure_attribution_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_failure_attribution_report.md'
DEFAULT_EVALUATION = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_evaluation_20260724/'
    'h2_case_validation_acceptance_evaluation_report.json'
)
DEFAULT_WORKSHEET = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724/'
    'h2_external_evidence_acceptance_worksheet.json'
)
DEFAULT_DASHBOARD = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724/'
    'h2_external_evidence_operations_dashboard.json'
)
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)

CAMPAIGN_DOMAIN_HINTS = {
    'real_cad_large_layout_leak_dispersion': ['real_cad_cleanup'],
    'sbepv5_d27_external_plume_validation': ['external_plume_shape_reference'],
    'calibrated_fire_consequence_validation': ['fire_consequence_calibration'],
    'integrated_engineering_production_replay': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
}

SOURCE_REPORT_DOMAIN_HINTS = {
    'real_cad_intake_preflight_report': ['real_cad_cleanup'],
    'real_cad_cleanup_package_report': ['real_cad_cleanup'],
    'sbepv5_d27_dataset_ingestion_report': ['external_plume_shape_reference'],
    'h2_reference_agreement_report': ['external_plume_shape_reference'],
    'fire_calibration_dataset_ingestion_report': ['fire_consequence_calibration'],
    'fire_calibration_dataset_report': ['fire_consequence_calibration'],
    'fire_consequence_metrics_report': ['fire_consequence_calibration'],
    'h2_external_artifact_drop_validator_report': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
    'h2_external_artifact_controlled_copy_report': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
    'h2_blocker_clearance_preflight_report': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
    'engineering_production_scorecard': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
    'case_validation_runner_ledger': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
    'production_evidence_verification_report': [
        'real_cad_cleanup',
        'external_plume_shape_reference',
        'fire_consequence_calibration',
    ],
}


class FailureAttributionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FailureAttributionError(message)


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
        raise FailureAttributionError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise FailureAttributionError(f'invalid JSON evidence {path}: {exc}') from exc
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


def worksheet_rows_by_domain(worksheet: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows = worksheet.get('worksheet_rows')
    require(isinstance(rows, list) and rows, 'worksheet_rows missing')
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        require(isinstance(row, dict), 'worksheet row is not an object')
        domain = str(row.get('domain', '')).strip()
        require(domain, 'worksheet row missing domain')
        grouped[domain].append(
            {
                'domain': domain,
                'artifact': row.get('artifact'),
                'drop_path': row.get('drop_path'),
                'target_path': row.get('target_path'),
                'current_present': row.get('current_present'),
                'current_valid': row.get('current_valid'),
                'current_gaps': row.get('current_gaps', []),
                'required_action': row.get('required_action'),
            }
        )
    return dict(grouped)


def failed_and_deferred_metrics(evaluation: dict[str, Any]) -> list[dict[str, Any]]:
    campaigns = evaluation.get('campaign_evaluations')
    require(isinstance(campaigns, list) and campaigns, 'campaign_evaluations missing')
    metrics: list[dict[str, Any]] = []
    for campaign in campaigns:
        require(isinstance(campaign, dict), 'campaign evaluation is not an object')
        campaign_id = str(campaign.get('campaign_id', '')).strip()
        items = campaign.get('metric_evaluations')
        require(isinstance(items, list), f'{campaign_id} metric_evaluations missing')
        for item in items:
            require(isinstance(item, dict), f'{campaign_id} metric item is not an object')
            if item.get('status') in {'FAIL', 'DEFERRED'}:
                record = dict(item)
                record['campaign_id'] = campaign_id
                record['campaign_title'] = campaign.get('title')
                metrics.append(record)
    return metrics


def domains_for_metric(metric: dict[str, Any]) -> list[str]:
    source_domains = SOURCE_REPORT_DOMAIN_HINTS.get(str(metric.get('source_report', '')))
    if source_domains:
        return source_domains
    campaign_domains = CAMPAIGN_DOMAIN_HINTS.get(str(metric.get('campaign_id', '')))
    return campaign_domains or []


def attribution_record(metric: dict[str, Any], worksheet_by_domain: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    domains = domains_for_metric(metric)
    worksheet_rows = [row for domain in domains for row in worksheet_by_domain.get(domain, [])]
    status = str(metric.get('status'))
    return {
        'campaign_id': metric.get('campaign_id'),
        'metric_id': metric.get('metric_id'),
        'metric_status': status,
        'source_report': metric.get('source_report'),
        'source_field': metric.get('source_field'),
        'gap': metric.get('gap', ''),
        'attributed_domains': domains,
        'artifact_row_count': len(worksheet_rows),
        'artifact_rows': worksheet_rows,
        'operator_action_class': 'rerun_final_verifier_after_all_domains_pass' if status == 'DEFERRED' else 'supply_or_fix_external_artifacts',
    }


def action_groups(records: list[dict[str, Any]], dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        domains = record.get('attributed_domains')
        key = 'final_verifier_deferred' if record.get('metric_status') == 'DEFERRED' else '+'.join(domains or ['unattributed'])
        grouped[key].append(record)
    next_commands = dashboard.get('next_operator_commands') if isinstance(dashboard.get('next_operator_commands'), list) else []
    groups: list[dict[str, Any]] = []
    for key, items in sorted(grouped.items(), key=lambda pair: pair[0]):
        artifact_rows = []
        seen_artifacts = set()
        for item in items:
            for row in item.get('artifact_rows', []):
                row_key = (row.get('domain'), row.get('artifact'), row.get('drop_path'))
                if row_key not in seen_artifacts:
                    seen_artifacts.add(row_key)
                    artifact_rows.append(row)
        groups.append(
            {
                'action_group_id': key,
                'metric_count': len(items),
                'failed_metric_count': sum(1 for item in items if item.get('metric_status') == 'FAIL'),
                'deferred_metric_count': sum(1 for item in items if item.get('metric_status') == 'DEFERRED'),
                'artifact_row_count': len(artifact_rows),
                'artifact_rows': artifact_rows,
                'next_operator_commands': next_commands,
            }
        )
    return groups


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    evaluation_path = Path(args.acceptance_evaluation_report)
    worksheet_path = Path(args.external_evidence_acceptance_worksheet_report)
    dashboard_path = Path(args.external_evidence_operations_dashboard_report)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    evaluation = load_json(evaluation_path)
    worksheet = load_json(worksheet_path)
    dashboard = load_json(dashboard_path)
    closure = load_json(closure_path)
    require(
        evaluation.get('status') in {
            'PASS-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION',
            'NOT_READY-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION',
        },
        'acceptance evaluation status invalid',
    )
    require(worksheet.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-ACCEPTANCE-WORKSHEET', 'worksheet did not PASS')
    require(
        dashboard.get('status') in {
            'PASS-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
            'NOT_READY-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
        },
        'operations dashboard status invalid',
    )
    require(closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST', 'closure manifest did not PASS')
    worksheet_by_domain = worksheet_rows_by_domain(worksheet)
    metrics = failed_and_deferred_metrics(evaluation)
    records = [attribution_record(metric, worksheet_by_domain) for metric in metrics]
    groups = action_groups(records, dashboard)
    summary = evaluation.get('summary') if isinstance(evaluation.get('summary'), dict) else {}
    failed = sum(1 for item in records if item['metric_status'] == 'FAIL')
    deferred = sum(1 for item in records if item['metric_status'] == 'DEFERRED')
    unattributed = [item for item in records if not item['attributed_domains']]
    quality_gate_matrix = [
        {
            'name': 'evaluation_attached',
            'status': 'PASS',
            'evidence': str(evaluation_path),
            'gap': '',
        },
        {
            'name': 'failed_and_deferred_metrics_match_evaluation',
            'status': 'PASS'
            if failed == int(summary.get('failed_metric_count', -1))
            and deferred == int(summary.get('deferred_metric_count', -1))
            else 'FAIL',
            'evidence': f'failed={failed} deferred={deferred}',
            'gap': '',
        },
        {
            'name': 'all_problem_metrics_are_attributed',
            'status': 'PASS' if not unattributed else 'FAIL',
            'evidence': f'unattributed={len(unattributed)}',
            'gap': ','.join(str(item.get('metric_id')) for item in unattributed),
        },
        {
            'name': 'current_not_ready_state_has_actionable_artifacts',
            'status': 'PASS'
            if evaluation.get('status') != 'NOT_READY-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION'
            or any(group.get('artifact_row_count', 0) > 0 for group in groups)
            else 'FAIL',
            'evidence': f'action_groups={len(groups)}',
            'gap': '',
        },
        {
            'name': 'failure_attribution_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'attribution is operator guidance only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Case Validation Failure Attribution',
        'acceptance_evaluation_report': str(evaluation_path),
        'external_evidence_acceptance_worksheet_report': str(worksheet_path),
        'external_evidence_operations_dashboard_report': str(dashboard_path),
        'production_blocker_closure_manifest_report': str(closure_path),
        'summary': {
            'evaluation_status': evaluation.get('status'),
            'evaluation_acceptance_metric_count': summary.get('acceptance_metric_count'),
            'failed_metric_count': failed,
            'deferred_metric_count': deferred,
            'attributed_problem_metric_count': len(records) - len(unattributed),
            'unattributed_problem_metric_count': len(unattributed),
            'action_group_count': len(groups),
            'external_artifact_row_count': int(worksheet.get('summary', {}).get('worksheet_row_count', 0))
            if isinstance(worksheet.get('summary'), dict)
            else None,
            'missing_or_invalid_artifact_row_count': int(
                worksheet.get('summary', {}).get('missing_or_invalid_artifact_row_count', 0)
            )
            if isinstance(worksheet.get('summary'), dict)
            else None,
        },
        'metric_attributions': records,
        'action_groups': groups,
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_h2_case_validation_acceptance_evaluation_report', evaluation_path),
            evidence_entry('engineering_h2_external_evidence_acceptance_worksheet_report', worksheet_path),
            evidence_entry('engineering_h2_external_evidence_operations_dashboard_report', dashboard_path),
            evidence_entry('engineering_h2_production_blocker_closure_manifest_report', closure_path),
        ],
        'limitations': [
            'This report attributes failed or deferred acceptance metrics to operator actions; it does not supply external data or run CFD campaigns.',
            'Production credit still requires all attributed artifacts to pass the strict intake gates, campaign execution, and final verifier pass.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'report must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('evaluation_acceptance_metric_count', 0)) >= 35, 'evaluation metric count too small')
    require(int(summary.get('unattributed_problem_metric_count', -1)) == 0, 'unattributed problem metrics remain')
    if summary.get('evaluation_status') == 'NOT_READY-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION':
        require(int(summary.get('failed_metric_count', 0)) >= 1, 'NOT_READY attribution must retain failed metrics')
        require(int(summary.get('action_group_count', 0)) >= 1, 'NOT_READY attribution must have action groups')
        require(int(summary.get('missing_or_invalid_artifact_row_count', 0)) >= 1, 'NOT_READY attribution must retain missing artifacts')
    records = data.get('metric_attributions')
    require(isinstance(records, list), 'metric_attributions missing')
    groups = data.get('action_groups')
    require(isinstance(groups, list) and groups, 'action_groups missing')
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
        '# Engineering H2 Case Validation Failure Attribution',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Action Groups', '']
    for group in report['action_groups']:
        lines.append(
            f"- `{group['action_group_id']}`: metrics `{group['metric_count']}`, "
            f"failed `{group['failed_metric_count']}`, deferred `{group['deferred_metric_count']}`, "
            f"artifacts `{group['artifact_row_count']}`"
        )
    lines += ['', '## Quality Gates', '']
    for item in report['quality_gate_matrix']:
        lines.append(f"- `{item['name']}`: `{item['status']}`")
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
    parser.add_argument('--acceptance-evaluation-report', default=str(DEFAULT_EVALUATION))
    parser.add_argument('--external-evidence-acceptance-worksheet-report', default=str(DEFAULT_WORKSHEET))
    parser.add_argument('--external-evidence-operations-dashboard-report', default=str(DEFAULT_DASHBOARD))
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_case_validation_failure_attribution VERIFY-PASS '
                f"json={args.verify_json} failed={summary['failed_metric_count']} "
                f"groups={summary['action_group_count']}"
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
            'engineering_h2_case_validation_failure_attribution PASS '
            f"json={out_json} md={out_md} failed={report['summary']['failed_metric_count']} "
            f"groups={report['summary']['action_group_count']}"
        )
        return 0
    except FailureAttributionError as exc:
        print(f'engineering_h2_case_validation_failure_attribution FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
