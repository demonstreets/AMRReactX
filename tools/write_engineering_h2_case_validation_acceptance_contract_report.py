#!/usr/bin/env python3
"""Write/verify the engineering H2 case-validation acceptance contract report."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-CASE-VALIDATION-ACCEPTANCE-CONTRACT'
VALID_COMPARATORS = {'==', '>=', '<=', 'count>=', 'contains_any', 'contains_all'}

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_contract_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_acceptance_contract_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_acceptance_contract_report.md'
DEFAULT_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/'
    'h2_external_evidence_case_validation_plan.json'
)

EXPECTED_CAMPAIGN_MIN_METRICS = {
    'real_cad_large_layout_leak_dispersion': 10,
    'sbepv5_d27_external_plume_validation': 12,
    'calibrated_fire_consequence_validation': 11,
    'integrated_engineering_production_replay': 10,
}


class AcceptanceContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceContractError(message)


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
        raise AcceptanceContractError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise AcceptanceContractError(f'invalid JSON evidence {path}: {exc}') from exc
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


def is_quantitative(metric: dict[str, Any]) -> bool:
    threshold = metric.get('threshold')
    return isinstance(threshold, (int, float)) and not isinstance(threshold, bool)


def validate_metric(campaign_id: str, metric: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    for key in ('metric_id', 'source_report', 'source_field', 'comparator', 'threshold', 'description'):
        if key not in metric:
            gaps.append(f'missing_{key}')
    if metric.get('comparator') not in VALID_COMPARATORS:
        gaps.append(f'unsupported_comparator:{metric.get("comparator")}')
    if metric.get('required_for_production_credit') is not True:
        gaps.append('not_required_for_production_credit')
    if not str(metric.get('metric_id', '')).strip():
        gaps.append('blank_metric_id')
    if not str(metric.get('source_report', '')).strip():
        gaps.append('blank_source_report')
    if not str(metric.get('source_field', '')).strip():
        gaps.append('blank_source_field')
    if not str(metric.get('description', '')).strip():
        gaps.append('blank_description')
    comparator = metric.get('comparator')
    threshold = metric.get('threshold')
    if comparator in {'>=', '<=', 'count>='} and not is_quantitative(metric):
        gaps.append(f'{comparator}_requires_numeric_threshold')
    if comparator in {'contains_any', 'contains_all'} and not (
        isinstance(threshold, list) and all(str(item).strip() for item in threshold)
    ):
        gaps.append(f'{comparator}_requires_nonempty_list_threshold')
    if comparator == '==' and threshold is None:
        gaps.append('equals_requires_nonnull_threshold')
    return [f'{campaign_id}:{metric.get("metric_id", "<unknown>")}:{gap}' for gap in gaps]


def campaign_contract_records(plan: dict[str, Any]) -> list[dict[str, Any]]:
    campaigns = plan.get('case_validation_campaigns')
    require(isinstance(campaigns, list) and campaigns, 'case_validation_campaigns missing')
    records: list[dict[str, Any]] = []
    for campaign in campaigns:
        require(isinstance(campaign, dict), 'campaign is not an object')
        campaign_id = str(campaign.get('campaign_id', '')).strip()
        contract = campaign.get('acceptance_contract')
        require(campaign_id, 'campaign_id missing')
        require(isinstance(contract, list) and contract, f'{campaign_id} acceptance_contract missing')
        gaps = [gap for metric in contract if isinstance(metric, dict) for gap in validate_metric(campaign_id, metric)]
        non_object_count = sum(1 for metric in contract if not isinstance(metric, dict))
        if non_object_count:
            gaps.append(f'{campaign_id}:non_object_metric_count:{non_object_count}')
        metric_ids = [str(metric.get('metric_id', '')) for metric in contract if isinstance(metric, dict)]
        duplicate_metric_ids = sorted({item for item in metric_ids if metric_ids.count(item) > 1})
        for item in duplicate_metric_ids:
            gaps.append(f'{campaign_id}:{item}:duplicate_metric_id')
        min_metrics = EXPECTED_CAMPAIGN_MIN_METRICS.get(campaign_id, 0)
        if len(contract) < min_metrics:
            gaps.append(f'{campaign_id}:metric_count:{len(contract)}<{min_metrics}')
        source_reports = sorted({str(metric.get('source_report', '')) for metric in contract if isinstance(metric, dict)})
        records.append(
            {
                'campaign_id': campaign_id,
                'metric_count': len(contract),
                'quantitative_metric_count': sum(1 for metric in contract if isinstance(metric, dict) and is_quantitative(metric)),
                'boolean_or_status_metric_count': sum(
                    1 for metric in contract if isinstance(metric, dict) and not is_quantitative(metric)
                ),
                'source_reports': source_reports,
                'duplicate_metric_ids': duplicate_metric_ids,
                'status': 'PASS' if not gaps else 'FAIL',
                'gaps': gaps,
            }
        )
    return records


def negative_contract_selftest(plan: dict[str, Any]) -> dict[str, Any]:
    fixture = copy.deepcopy(plan)
    campaigns = fixture.get('case_validation_campaigns')
    require(isinstance(campaigns, list) and campaigns, 'negative fixture campaigns missing')
    first = campaigns[0]
    require(isinstance(first, dict), 'negative fixture first campaign invalid')
    contract = first.get('acceptance_contract')
    require(isinstance(contract, list) and contract, 'negative fixture contract missing')
    first_metric = contract[0]
    require(isinstance(first_metric, dict), 'negative fixture first metric invalid')
    first_metric.pop('threshold', None)
    records = campaign_contract_records(fixture)
    refused = any(record['status'] == 'FAIL' for record in records)
    return {
        'negative_selftest_only': True,
        'mutation': 'removed threshold from first acceptance metric',
        'refused': refused,
        'failed_campaign_count': sum(1 for record in records if record['status'] == 'FAIL'),
        'gaps': [gap for record in records for gap in record['gaps']],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plan_path = Path(args.case_validation_plan_report)
    plan = load_json(plan_path)
    require(plan.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN', 'case validation plan did not PASS')
    records = campaign_contract_records(plan)
    failed_records = [record for record in records if record['status'] != 'PASS']
    total_metric_count = sum(int(record['metric_count']) for record in records)
    quantitative_metric_count = sum(int(record['quantitative_metric_count']) for record in records)
    source_reports = sorted({source for record in records for source in record['source_reports']})
    negative = negative_contract_selftest(plan)
    require(negative['refused'] is True, 'negative contract selftest was not refused')
    quality_gate_matrix = [
        {
            'name': 'all_campaigns_have_acceptance_contracts',
            'status': 'PASS' if len(records) == 4 and not failed_records else 'FAIL',
            'evidence': f'campaigns={len(records)} failed={len(failed_records)}',
            'gap': '; '.join(gap for record in failed_records for gap in record['gaps']),
        },
        {
            'name': 'contract_metric_count_is_production_sized',
            'status': 'PASS' if total_metric_count >= 35 and quantitative_metric_count >= 12 else 'FAIL',
            'evidence': f'total={total_metric_count} quantitative={quantitative_metric_count}',
            'gap': '',
        },
        {
            'name': 'contract_sources_cover_domain_and_final_reports',
            'status': 'PASS'
            if {
                'real_cad_intake_preflight_report',
                'h2_reference_agreement_report',
                'fire_consequence_metrics_report',
                'case_validation_runner_ledger',
                'production_evidence_verification_report',
            } <= set(source_reports)
            else 'FAIL',
            'evidence': ','.join(source_reports),
            'gap': '',
        },
        {
            'name': 'negative_selftest_refuses_missing_threshold',
            'status': 'PASS' if negative['refused'] is True else 'FAIL',
            'evidence': f"failed_campaigns={negative['failed_campaign_count']}",
            'gap': '; '.join(negative['gaps']),
        },
        {
            'name': 'contract_report_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'acceptance contract is a future-real-data gate only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Case Validation Acceptance Contract',
        'case_validation_plan_report': str(plan_path),
        'summary': {
            'campaign_count': len(records),
            'acceptance_contract_metric_count': total_metric_count,
            'quantitative_metric_count': quantitative_metric_count,
            'failed_contract_campaign_count': len(failed_records),
            'source_report_count': len(source_reports),
            'negative_missing_threshold_refused': negative['refused'],
        },
        'campaign_contract_records': records,
        'source_reports': source_reports,
        'negative_contract_selftest': negative,
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_h2_external_evidence_case_validation_plan_report', plan_path),
        ],
        'limitations': [
            'This report audits structured acceptance contracts only; it does not execute CFD validation campaigns.',
            'Production credit still requires accepted external data, campaign execution, metric comparison, and the full verifier passing.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'report must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('campaign_count', 0)) == 4, 'campaign count mismatch')
    require(int(summary.get('acceptance_contract_metric_count', 0)) >= 35, 'acceptance contract metric count too small')
    require(int(summary.get('quantitative_metric_count', 0)) >= 12, 'quantitative metric count too small')
    require(int(summary.get('failed_contract_campaign_count', -1)) == 0, 'failed contract campaigns remain')
    require(summary.get('negative_missing_threshold_refused') is True, 'negative threshold selftest was not refused')
    records = data.get('campaign_contract_records')
    require(isinstance(records, list) and len(records) == 4, 'campaign_contract_records mismatch')
    require(all(record.get('status') == 'PASS' for record in records if isinstance(record, dict)), 'failed campaign contract')
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
        '# Engineering H2 Case Validation Acceptance Contract',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Campaign Contracts', '']
    for record in report['campaign_contract_records']:
        lines.append(
            f"- `{record['campaign_id']}`: `{record['status']}`, "
            f"metrics `{record['metric_count']}`, quantitative `{record['quantitative_metric_count']}`"
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
    parser.add_argument('--case-validation-plan-report', default=str(DEFAULT_PLAN))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_case_validation_acceptance_contract VERIFY-PASS '
                f"json={args.verify_json} metrics={summary['acceptance_contract_metric_count']} "
                f"quantitative={summary['quantitative_metric_count']}"
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
            'engineering_h2_case_validation_acceptance_contract PASS '
            f"json={out_json} md={out_md} metrics={report['summary']['acceptance_contract_metric_count']} "
            f"quantitative={report['summary']['quantitative_metric_count']}"
        )
        return 0
    except AcceptanceContractError as exc:
        print(f'engineering_h2_case_validation_acceptance_contract FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
