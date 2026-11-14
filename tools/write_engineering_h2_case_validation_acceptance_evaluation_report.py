#!/usr/bin/env python3
"""Write/verify the engineering H2 case-validation acceptance evaluation report."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_READY = 'PASS-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION'
STATUS_NOT_READY = 'NOT_READY-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_evaluation_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_acceptance_evaluation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_acceptance_evaluation_report.md'
DEFAULT_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/'
    'h2_external_evidence_case_validation_plan.json'
)
DEFAULT_CONTRACT = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_contract_20260724/'
    'h2_case_validation_acceptance_contract_report.json'
)

SOURCE_REPORTS = {
    'real_cad_intake_preflight_report': Path(
        'docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/'
        'real_cad_intake_preflight_report.json'
    ),
    'real_cad_cleanup_package_report': Path(
        'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
        'real_cad_cleanup_package_report.json'
    ),
    'sbepv5_d27_dataset_ingestion_report': Path(
        'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
        'sbepv5_d27_dataset_ingestion_report.json'
    ),
    'h2_reference_agreement_report': Path(
        'docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/'
        'h2_reference_agreement_report.json'
    ),
    'fire_calibration_dataset_ingestion_report': Path(
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
        'fire_calibration_dataset_ingestion_report.json'
    ),
    'fire_calibration_dataset_report': Path(
        'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/'
        'fire_calibration_dataset_report.json'
    ),
    'fire_consequence_metrics_report': Path(
        'docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/'
        'fire_consequence_metrics_report.json'
    ),
    'h2_external_artifact_drop_validator_report': Path(
        'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
        'h2_external_artifact_drop_validator_report.json'
    ),
    'h2_external_artifact_controlled_copy_report': Path(
        'docs/codex_audit/evidence/engineering_h2_external_artifact_controlled_copy_20260724/'
        'h2_external_artifact_controlled_copy_report.json'
    ),
    'h2_blocker_clearance_preflight_report': Path(
        'docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/'
        'h2_blocker_clearance_preflight_report.json'
    ),
    'engineering_production_scorecard': Path(
        'docs/codex_audit/evidence/engineering_production_scorecard_20260720/'
        'engineering_production_scorecard.json'
    ),
    'case_validation_runner_ledger': Path(
        'docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724/'
        'h2_case_validation_runner_ledger.json'
    ),
}

DEFERRED_SOURCE_REPORTS = {
    'production_evidence_verification_report': 'final verifier is generated after this evaluation in the rebuild cycle',
}


class AcceptanceEvaluationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceEvaluationError(message)


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
        raise AcceptanceEvaluationError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise AcceptanceEvaluationError(f'invalid JSON evidence {path}: {exc}') from exc
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


def flatten_values(value: Any, segments: list[str]) -> Any:
    if not segments:
        return value
    head, tail = segments[0], segments[1:]
    if isinstance(value, dict):
        require(head in value, f'missing field segment: {head}')
        return flatten_values(value[head], tail)
    if isinstance(value, list):
        out = []
        for item in value:
            try:
                out.append(flatten_values(item, segments))
            except AcceptanceEvaluationError:
                continue
        require(out, f'no list entries contain field segment: {head}')
        return out
    raise AcceptanceEvaluationError(f'cannot descend through non-container at segment: {head}')


def extract_field(data: dict[str, Any], field: str) -> Any:
    return flatten_values(data, [part for part in field.split('.') if part])


def numeric(value: Any) -> float:
    if isinstance(value, bool):
        raise AcceptanceEvaluationError('boolean is not numeric')
    out = float(value)
    require(math.isfinite(out), 'non-finite numeric value')
    return out


def compare(value: Any, comparator: str, threshold: Any) -> bool:
    if comparator == '==':
        return value == threshold
    if comparator == '>=':
        return numeric(value) >= numeric(threshold)
    if comparator == '<=':
        return numeric(value) <= numeric(threshold)
    if comparator == 'count>=':
        require(isinstance(value, list), 'count>= requires list value')
        return len(value) >= int(threshold)
    if comparator == 'contains_any':
        require(isinstance(value, list) and isinstance(threshold, list), 'contains_any requires list values')
        return bool({str(item) for item in value} & {str(item) for item in threshold})
    if comparator == 'contains_all':
        require(isinstance(value, list) and isinstance(threshold, list), 'contains_all requires list values')
        return {str(item) for item in threshold} <= {str(item) for item in value}
    raise AcceptanceEvaluationError(f'unsupported comparator: {comparator}')


def comparator_selftest() -> dict[str, Any]:
    cases = [
        ('eq_positive', 2, '==', 2, True),
        ('eq_negative', 2, '==', 3, False),
        ('ge_positive', 3, '>=', 2, True),
        ('ge_negative', 1, '>=', 2, False),
        ('count_positive', ['a', 'b'], 'count>=', 2, True),
        ('count_negative', ['a'], 'count>=', 2, False),
        ('contains_any_positive', ['plume_extent'], 'contains_any', ['arrival_time', 'plume_extent'], True),
        ('contains_any_negative', ['metadata'], 'contains_any', ['arrival_time', 'plume_extent'], False),
        ('contains_all_positive', ['radiation', 'overpressure'], 'contains_all', ['radiation', 'overpressure'], True),
        ('contains_all_negative', ['radiation'], 'contains_all', ['radiation', 'overpressure'], False),
    ]
    records = []
    for name, value, comparator, threshold, expected in cases:
        passed = compare(value, comparator, threshold)
        records.append(
            {
                'case': name,
                'value': value,
                'comparator': comparator,
                'threshold': threshold,
                'expected': expected,
                'actual': passed,
                'status': 'PASS' if passed is expected else 'FAIL',
            }
        )
    return {
        'case_count': len(records),
        'passed_case_count': sum(1 for item in records if item['status'] == 'PASS'),
        'all_cases_passed': all(item['status'] == 'PASS' for item in records),
        'cases': records,
    }


def evaluate_metric(metric: dict[str, Any], sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_report = str(metric.get('source_report', ''))
    metric_id = str(metric.get('metric_id', ''))
    if source_report in DEFERRED_SOURCE_REPORTS:
        return {
            'metric_id': metric_id,
            'source_report': source_report,
            'source_field': metric.get('source_field'),
            'comparator': metric.get('comparator'),
            'threshold': metric.get('threshold'),
            'actual_value': None,
            'status': 'DEFERRED',
            'gap': DEFERRED_SOURCE_REPORTS[source_report],
        }
    if source_report not in sources:
        return {
            'metric_id': metric_id,
            'source_report': source_report,
            'source_field': metric.get('source_field'),
            'comparator': metric.get('comparator'),
            'threshold': metric.get('threshold'),
            'actual_value': None,
            'status': 'FAIL',
            'gap': f'missing source report mapping: {source_report}',
        }
    try:
        value = extract_field(sources[source_report], str(metric.get('source_field', '')))
        passed = compare(value, str(metric.get('comparator')), metric.get('threshold'))
    except (AcceptanceEvaluationError, ValueError, TypeError) as exc:
        return {
            'metric_id': metric_id,
            'source_report': source_report,
            'source_field': metric.get('source_field'),
            'comparator': metric.get('comparator'),
            'threshold': metric.get('threshold'),
            'actual_value': None,
            'status': 'FAIL',
            'gap': str(exc),
        }
    return {
        'metric_id': metric_id,
        'source_report': source_report,
        'source_field': metric.get('source_field'),
        'comparator': metric.get('comparator'),
        'threshold': metric.get('threshold'),
        'actual_value': value,
        'status': 'PASS' if passed else 'FAIL',
        'gap': '' if passed else f'actual value did not satisfy {metric.get("comparator")} {metric.get("threshold")}',
    }


def load_sources() -> dict[str, dict[str, Any]]:
    return {label: load_json(path) for label, path in SOURCE_REPORTS.items()}


def campaign_evaluations(plan: dict[str, Any], sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    campaigns = plan.get('case_validation_campaigns')
    require(isinstance(campaigns, list) and campaigns, 'case_validation_campaigns missing')
    out: list[dict[str, Any]] = []
    for campaign in campaigns:
        require(isinstance(campaign, dict), 'campaign is not an object')
        campaign_id = str(campaign.get('campaign_id', ''))
        contract = campaign.get('acceptance_contract')
        require(isinstance(contract, list) and contract, f'{campaign_id} acceptance_contract missing')
        metrics = [evaluate_metric(metric, sources) for metric in contract if isinstance(metric, dict)]
        passed = sum(1 for item in metrics if item['status'] == 'PASS')
        failed = sum(1 for item in metrics if item['status'] == 'FAIL')
        deferred = sum(1 for item in metrics if item['status'] == 'DEFERRED')
        ready = bool(metrics) and failed == 0 and deferred == 0
        out.append(
            {
                'campaign_id': campaign_id,
                'title': campaign.get('title'),
                'required_domains': campaign.get('required_domains', []),
                'metric_count': len(metrics),
                'passed_metric_count': passed,
                'failed_metric_count': failed,
                'deferred_metric_count': deferred,
                'ready_for_production_credit': ready,
                'metric_evaluations': metrics,
            }
        )
    return out


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plan_path = Path(args.case_validation_plan_report)
    contract_path = Path(args.acceptance_contract_report)
    plan = load_json(plan_path)
    contract = load_json(contract_path)
    require(plan.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN', 'case validation plan did not PASS')
    require(
        contract.get('status') == 'PASS-H2-CASE-VALIDATION-ACCEPTANCE-CONTRACT',
        'acceptance contract report did not PASS',
    )
    sources = load_sources()
    campaigns = campaign_evaluations(plan, sources)
    total_metrics = sum(int(item['metric_count']) for item in campaigns)
    passed_metrics = sum(int(item['passed_metric_count']) for item in campaigns)
    failed_metrics = sum(int(item['failed_metric_count']) for item in campaigns)
    deferred_metrics = sum(int(item['deferred_metric_count']) for item in campaigns)
    ready_campaigns = sum(1 for item in campaigns if item['ready_for_production_credit'])
    ready = ready_campaigns == len(campaigns) and failed_metrics == 0 and deferred_metrics == 0
    selftest = comparator_selftest()
    require(selftest['all_cases_passed'] is True, 'comparator selftest failed')
    quality_gate_matrix = [
        {
            'name': 'acceptance_contract_attached',
            'status': 'PASS',
            'evidence': str(contract_path),
            'gap': '',
        },
        {
            'name': 'all_contract_metrics_evaluated_or_deferred',
            'status': 'PASS' if total_metrics >= 35 else 'FAIL',
            'evidence': f'total={total_metrics} passed={passed_metrics} failed={failed_metrics} deferred={deferred_metrics}',
            'gap': '',
        },
        {
            'name': 'current_state_retains_unmet_real_data_metrics',
            'status': 'PASS' if failed_metrics >= 1 else 'FAIL',
            'evidence': f'failed_metrics={failed_metrics}',
            'gap': '',
        },
        {
            'name': 'final_verifier_metrics_are_deferred_to_avoid_hash_cycle',
            'status': 'PASS' if deferred_metrics >= 1 else 'FAIL',
            'evidence': f'deferred_metrics={deferred_metrics}',
            'gap': '',
        },
        {
            'name': 'comparator_selftest_passed',
            'status': 'PASS' if selftest['all_cases_passed'] else 'FAIL',
            'evidence': f"{selftest['passed_case_count']}/{selftest['case_count']}",
            'gap': '',
        },
        {
            'name': 'evaluation_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'evaluation is a current-state gate only',
            'gap': '',
        },
    ]
    status = STATUS_READY if ready else STATUS_NOT_READY
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 Case Validation Acceptance Evaluation',
        'case_validation_plan_report': str(plan_path),
        'acceptance_contract_report': str(contract_path),
        'summary': {
            'campaign_count': len(campaigns),
            'ready_campaign_count': ready_campaigns,
            'acceptance_metric_count': total_metrics,
            'passed_metric_count': passed_metrics,
            'failed_metric_count': failed_metrics,
            'deferred_metric_count': deferred_metrics,
            'ready_for_production_credit': ready,
            'comparator_selftest_case_count': selftest['case_count'],
            'comparator_selftest_passed': selftest['all_cases_passed'],
        },
        'campaign_evaluations': campaigns,
        'source_report_paths': {label: str(path) for label, path in SOURCE_REPORTS.items()},
        'deferred_source_reports': DEFERRED_SOURCE_REPORTS,
        'comparator_selftest': selftest,
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_h2_external_evidence_case_validation_plan_report', plan_path),
            evidence_entry('engineering_h2_case_validation_acceptance_contract_report', contract_path),
        ]
        + [evidence_entry(label, path) for label, path in SOURCE_REPORTS.items()],
        'limitations': [
            'This report evaluates acceptance contracts against the current evidence JSON files; it does not run CFD campaigns.',
            'Final production-verifier metrics are intentionally deferred here to avoid a circular evidence hash dependency.',
            'Production credit still requires accepted external data, campaign execution, zero failed metrics, and the final verifier passing.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'report must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('campaign_count', 0)) == 4, 'campaign count mismatch')
    require(int(summary.get('acceptance_metric_count', 0)) >= 35, 'acceptance metric count too small')
    require(summary.get('comparator_selftest_passed') is True, 'comparator selftest did not pass')
    require(int(summary.get('comparator_selftest_case_count', 0)) == 10, 'comparator selftest count mismatch')
    if data.get('status') == STATUS_READY:
        require(int(summary.get('failed_metric_count', -1)) == 0, 'READY evaluation has failed metrics')
        require(int(summary.get('deferred_metric_count', -1)) == 0, 'READY evaluation has deferred metrics')
        require(summary.get('ready_for_production_credit') is True, 'READY evaluation not marked ready')
    else:
        require(
            int(summary.get('failed_metric_count', 0)) >= 1 or int(summary.get('deferred_metric_count', 0)) >= 1,
            'NOT_READY evaluation must retain failed or deferred metrics',
        )
        require(summary.get('ready_for_production_credit') is False, 'NOT_READY evaluation marked ready')
    campaigns = data.get('campaign_evaluations')
    require(isinstance(campaigns, list) and len(campaigns) == 4, 'campaign_evaluations mismatch')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'quality gate failed')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and len(entries) >= 10, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence hash mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Case Validation Acceptance Evaluation',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Campaigns', '']
    for item in report['campaign_evaluations']:
        lines.append(
            f"- `{item['campaign_id']}`: ready `{item['ready_for_production_credit']}`, "
            f"pass/fail/deferred `{item['passed_metric_count']}/{item['failed_metric_count']}/{item['deferred_metric_count']}`"
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
    parser.add_argument('--acceptance-contract-report', default=str(DEFAULT_CONTRACT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_case_validation_acceptance_evaluation VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"failed={summary['failed_metric_count']} deferred={summary['deferred_metric_count']}"
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
            'engineering_h2_case_validation_acceptance_evaluation PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"failed={report['summary']['failed_metric_count']} deferred={report['summary']['deferred_metric_count']}"
        )
        return 0
    except AcceptanceEvaluationError as exc:
        print(f'engineering_h2_case_validation_acceptance_evaluation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
