#!/usr/bin/env python3
"""Write/verify the engineering H2 post-intake case validation plan."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS = 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_evidence_case_validation_plan.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_evidence_case_validation_plan.md'
DEFAULT_ACCEPTANCE_WORKSHEET = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724/'
    'h2_external_evidence_acceptance_worksheet.json'
)

EXPECTED_DOMAINS = {
    'real_cad_cleanup',
    'external_plume_shape_reference',
    'fire_consequence_calibration',
}


class CaseValidationPlanError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CaseValidationPlanError(message)


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
        raise CaseValidationPlanError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise CaseValidationPlanError(f'invalid JSON evidence {path}: {exc}') from exc
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
    require(isinstance(rows, list), 'acceptance worksheet rows missing')
    by_domain: dict[str, list[dict[str, Any]]] = {domain: [] for domain in EXPECTED_DOMAINS}
    for row in rows:
        if not isinstance(row, dict):
            continue
        domain = str(row.get('domain', ''))
        require(domain in EXPECTED_DOMAINS, f'unexpected worksheet domain: {domain}')
        by_domain.setdefault(domain, []).append(row)
    return by_domain


def domain_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = sum(1 for row in rows if row.get('current_valid') is True)
    return {
        'artifact_row_count': len(rows),
        'valid_artifact_row_count': valid,
        'missing_or_invalid_artifact_row_count': len(rows) - valid,
        'all_artifacts_valid': len(rows) > 0 and valid == len(rows),
    }


def metric(
    metric_id: str,
    source_report: str,
    source_field: str,
    comparator: str,
    threshold: Any,
    units: str,
    description: str,
) -> dict[str, Any]:
    return {
        'metric_id': metric_id,
        'source_report': source_report,
        'source_field': source_field,
        'comparator': comparator,
        'threshold': threshold,
        'units': units,
        'description': description,
        'required_for_production_credit': True,
    }


def acceptance_contract(campaign_id: str) -> list[dict[str, Any]]:
    runner_contract = [
        metric(
            f'{campaign_id}_runner_ledger_pass',
            'case_validation_runner_ledger',
            'status',
            '==',
            'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER',
            'status',
            'The guarded external-evidence case runner must record a successful execution ledger.',
        ),
        metric(
            f'{campaign_id}_runner_command_recorded',
            'case_validation_runner_ledger',
            'command_results.campaign_id',
            'contains_any',
            [campaign_id],
            'campaign_ids',
            'The runner ledger must include executed command records for this campaign.',
        ),
    ]
    contracts = {
        'real_cad_large_layout_leak_dispersion': [
            metric('real_cad_source_file_count', 'real_cad_intake_preflight_report', 'summary.source_cad_file_count', '>=', 3, 'files', 'At least three real source CAD files must be staged.'),
            metric('real_cad_cleaned_geometry_count', 'real_cad_intake_preflight_report', 'summary.cleaned_geometry_file_count', '>=', 3, 'files', 'At least three cleaned simulation geometries must be paired with source CAD.'),
            metric('real_cad_paired_label_count', 'real_cad_intake_preflight_report', 'summary.data_room_index_paired_label_count', '>=', 3, 'labels', 'The data-room index must pair source and cleaned geometry labels.'),
            metric('real_cad_cleanup_quality_rows', 'real_cad_intake_preflight_report', 'summary.cleanup_quality_record_row_count', '>=', 3, 'rows', 'Cleanup quality records must cover each real geometry.'),
            metric('real_cad_manifest_validates', 'real_cad_intake_preflight_report', 'summary.manifest_validates', '==', True, 'boolean', 'Manifest provenance, hashes, cleanup, bbox, and campaign declarations must validate.'),
            metric('real_cad_large_layout_valid', 'real_cad_intake_preflight_report', 'summary.large_layout_valid', '==', True, 'boolean', 'The accepted geometry package must declare and validate a large-layout campaign.'),
            metric('real_cad_cleanup_blocker_cleared', 'real_cad_cleanup_package_report', 'clears_real_cad_cleanup_blocker', '==', True, 'boolean', 'The real-CAD cleanup blocker must be cleared by the domain package report.'),
            metric('real_cad_rebuild_verifier_pass', 'production_evidence_verification_report', 'status', '==', 'PASS', 'status', 'The full production verifier must pass after rebuilding with the accepted CAD evidence.'),
        ],
        'sbepv5_d27_external_plume_validation': [
            metric('sbepv5_dataset_ingestion_ready', 'sbepv5_d27_dataset_ingestion_report', 'status', '==', 'PASS-SBEPV5-D27-DATASET-INGESTION', 'status', 'The SBEPV5 D27 external dataset ingestion must pass.'),
            metric('sbepv5_exact_sensor_coordinates', 'sbepv5_d27_dataset_ingestion_report', 'current_inputs.exact_sensor_coordinates_available', '==', True, 'boolean', 'Gas01..Gas12 sensor coordinates must be accepted with required uncertainty metadata.'),
            metric('sbepv5_exact_baffle_geometry', 'sbepv5_d27_dataset_ingestion_report', 'current_inputs.exact_baffle_geometry_available', '==', True, 'boolean', 'Baffle bounds must be accepted with required uncertainty metadata.'),
            metric('sbepv5_experimental_timeseries', 'sbepv5_d27_dataset_ingestion_report', 'current_inputs.experimental_timeseries_available', '==', True, 'boolean', 'Experimental concentration histories must be present.'),
            metric('sbepv5_sensor_count', 'sbepv5_d27_dataset_ingestion_report', 'sensor_coordinate_summary.sensor_ids', 'count>=', 12, 'sensors', 'All expected Gas01..Gas12 sensors must be represented.'),
            metric('sbepv5_baffle_count', 'sbepv5_d27_dataset_ingestion_report', 'baffle_geometry_summary.baffle_ids', 'count>=', 4, 'baffles', 'All four baffles must be represented.'),
            metric('sbepv5_timeseries_duration', 'sbepv5_d27_dataset_ingestion_report', 'timeseries_summary.max_time_s', '>=', 120.0, 's', 'Reference time histories must cover at least 120 seconds.'),
            metric('external_plume_metric_count', 'h2_reference_agreement_report', 'summary.external_plume_metric_count', '>=', 2, 'metrics', 'External plume comparison must include at least two declared metrics.'),
            metric('external_plume_shape_metric_present', 'h2_reference_agreement_report', 'external_plume_shape_comparison.metric_types', 'contains_any', ['plume_extent', 'sensor_concentration', 'arrival_time'], 'metric_types', 'At least one accepted metric must be a plume-shape metric.'),
            metric('external_plume_all_metrics_passed', 'h2_reference_agreement_report', 'summary.external_plume_all_metrics_passed', '==', True, 'boolean', 'All accepted external plume metrics must pass declared tolerances.'),
            metric('external_plume_reference_blocker_cleared', 'h2_reference_agreement_report', 'clears_reference_data_blocker', '==', True, 'boolean', 'External plume agreement must clear the reference-data blocker.'),
        ],
        'calibrated_fire_consequence_validation': [
            metric('fire_calibration_ingestion_ready', 'fire_calibration_dataset_ingestion_report', 'status', '==', 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION', 'status', 'Fire calibration dataset ingestion must pass.'),
            metric('fire_radiation_metric_count', 'fire_calibration_dataset_ingestion_report', 'radiation_metrics_summary.row_count', '>=', 1, 'metrics', 'At least one radiation calibration metric must be accepted.'),
            metric('fire_overpressure_metric_count', 'fire_calibration_dataset_ingestion_report', 'overpressure_metrics_summary.row_count', '>=', 1, 'metrics', 'At least one overpressure calibration metric must be accepted.'),
            metric('fire_calibration_dataset_ready', 'fire_calibration_dataset_report', 'status', '==', 'PASS-H2-FIRE-CALIBRATION-DATASET', 'status', 'The generated calibration dataset JSON must pass.'),
            metric('fire_calibration_metric_families', 'fire_calibration_dataset_report', 'dataset.metrics.family', 'contains_all', ['radiation', 'overpressure'], 'families', 'The calibration dataset must include both radiation and overpressure families.'),
            metric('fire_consequence_calibrated_status', 'fire_consequence_metrics_report', 'status', '==', 'PASS-CALIBRATED-CONSEQUENCE-AGREEMENT', 'status', 'The consequence report must be upgraded from screening to calibrated agreement.'),
            metric('fire_radiation_model_calibrated', 'fire_consequence_metrics_report', 'radiation_model_calibrated', '==', True, 'boolean', 'Radiation model calibration must pass accepted metrics.'),
            metric('fire_overpressure_model_calibrated', 'fire_consequence_metrics_report', 'overpressure_model_calibrated', '==', True, 'boolean', 'Overpressure model calibration must pass accepted metrics.'),
            metric('fire_consequence_blocker_cleared', 'fire_consequence_metrics_report', 'clears_calibrated_fire_consequence_blocker', '==', True, 'boolean', 'The calibrated fire consequence blocker must be cleared.'),
        ],
        'integrated_engineering_production_replay': [
            metric('external_artifact_drop_ready', 'h2_external_artifact_drop_validator_report', 'status', '==', 'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'status', 'All 14 external artifact rows must pass the strict drop validator.'),
            metric('external_artifact_drop_valid_count', 'h2_external_artifact_drop_validator_report', 'valid_artifact_count', '==', 14, 'artifacts', 'The drop validator must accept every expected external artifact row.'),
            metric('controlled_copy_applied', 'h2_external_artifact_controlled_copy_report', 'controlled_copy_applied', '==', True, 'boolean', 'Validated external evidence must be copied with explicit operator confirmation.'),
            metric('controlled_copy_ready_count', 'h2_external_artifact_controlled_copy_report', 'ready_copy_action_count', '==', 14, 'actions', 'All external artifact copy actions must be ready.'),
            metric('blocker_clearance_zero_remaining', 'h2_blocker_clearance_preflight_report', 'remaining_blocker_count', '==', 0, 'blockers', 'No production blocker may remain before scorecard clearance.'),
            metric('scorecard_production_ready', 'engineering_production_scorecard', 'status', '==', 'PRODUCTION_READY', 'status', 'The engineering scorecard must be production-ready after real-data rebuild.'),
            metric('production_verifier_pass', 'production_evidence_verification_report', 'status', '==', 'PASS', 'status', 'The top-level production evidence verifier must pass.'),
            metric('production_verifier_ctest_count', 'production_evidence_verification_report', 'summary.ctest_tests', '==', 22, 'tests', 'The smoke-test suite must still pass during final verification.'),
        ],
    }
    require(campaign_id in contracts, f'unknown campaign acceptance contract: {campaign_id}')
    return contracts[campaign_id] + runner_contract


def campaign(
    campaign_id: str,
    title: str,
    required_domains: list[str],
    domain_summaries: dict[str, dict[str, Any]],
    commands: list[str],
    acceptance_metrics: list[str],
    expected_evidence: list[str],
) -> dict[str, Any]:
    ready = all(domain_summaries[domain]['all_artifacts_valid'] for domain in required_domains)
    gaps = [
        f'{domain}:missing_or_invalid={domain_summaries[domain]["missing_or_invalid_artifact_row_count"]}'
        for domain in required_domains
        if not domain_summaries[domain]['all_artifacts_valid']
    ]
    return {
        'campaign_id': campaign_id,
        'title': title,
        'required_domains': required_domains,
        'ready_to_execute_after_controlled_copy': ready,
        'blocking_gaps': gaps,
        'commands_after_external_artifacts_pass': commands,
        'acceptance_metrics': acceptance_metrics,
        'acceptance_contract': acceptance_contract(campaign_id),
        'expected_evidence_outputs': expected_evidence,
        'does_not_clear_production_blockers': True,
    }


def build_campaigns(domain_summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        campaign(
            'real_cad_large_layout_leak_dispersion',
            'Real-CAD tank/pipe large-layout H2 leak dispersion validation',
            ['real_cad_cleanup'],
            domain_summaries,
            [
                'python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py',
                'python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py',
                'bash tools/rebuild_engineering_h2_evidence_chain.sh',
            ],
            [
                'real CAD package PASS and clears_real_cad_cleanup_blocker true',
                'large_layout_campaign true',
                'at least three source CAD files paired with cleaned simulation geometries',
                'full production verifier PASS after rebuild',
            ],
            [
                'engineering_h2_real_cad_intake_preflight_report',
                'engineering_h2_real_cad_cleanup_package_report',
                'engineering_h2_production_evidence_verification_report',
            ],
        ),
        campaign(
            'sbepv5_d27_external_plume_validation',
            'HySafe SBEPV5 D27 external plume-shape validation',
            ['external_plume_shape_reference'],
            domain_summaries,
            [
                'python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py',
                'python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py',
                'python3 tools/write_engineering_h2_reference_agreement_report.py --external-plume-dataset-json <generated_external_plume_dataset_json>',
                'python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py',
                'bash tools/rebuild_engineering_h2_evidence_chain.sh',
            ],
            [
                'SBEPV5 dataset ingestion PASS',
                'external plume dataset JSON written',
                'sensor concentration histories cover at least 120 s',
                'case-specific plume-shape agreement replaces threshold-only reference evidence',
            ],
            [
                'sbepv5_d27_dataset_ingestion_report',
                'sbepv5_d27_external_dataset_report',
                'h2_reference_agreement_report',
                'external_plume_benchmark_readiness_report',
            ],
        ),
        campaign(
            'calibrated_fire_consequence_validation',
            'Calibrated fire radiation and overpressure consequence validation',
            ['fire_consequence_calibration'],
            domain_summaries,
            [
                'python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py',
                'python3 tools/write_engineering_h2_fire_calibration_package_report.py',
                'python3 tools/write_engineering_h2_fire_calibration_dataset_report.py',
                'python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --calibration-dataset-json <generated_fire_calibration_dataset_json>',
                'bash tools/rebuild_engineering_h2_evidence_chain.sh',
            ],
            [
                'fire calibration package PASS and clears fire consequence blocker',
                'radiation metrics calibrated against accepted source data',
                'overpressure metrics calibrated against accepted source data',
                'screening-only fire consequence status replaced by calibrated evidence tier',
            ],
            [
                'fire_calibration_dataset_ingestion_report',
                'fire_calibration_package_report',
                'fire_calibration_dataset_report',
                'fire_consequence_metrics_report',
            ],
        ),
        campaign(
            'integrated_engineering_production_replay',
            'Integrated production replay after all real external evidence is accepted',
            ['real_cad_cleanup', 'external_plume_shape_reference', 'fire_consequence_calibration'],
            domain_summaries,
            [
                'python3 tools/write_engineering_h2_external_artifact_drop_validator.py',
                'python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py --apply --confirm-controlled-copy H2_EXTERNAL_ARTIFACTS_READY',
                'bash tools/rebuild_engineering_h2_evidence_chain.sh',
                'bash tools/verify_engineering_h2_production_evidence.sh',
            ],
            [
                'external artifact drop PASS 14/14',
                'controlled copy PASS and applied',
                'blocker clearance preflight PASS with zero remaining blockers',
                'engineering production scorecard PRODUCTION_READY',
                'top-level production evidence verifier PASS',
            ],
            [
                'h2_external_artifact_drop_validator_report',
                'h2_external_artifact_controlled_copy_report',
                'h2_blocker_clearance_preflight_report',
                'engineering_production_scorecard',
                'production_evidence_verification_report',
            ],
        ),
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    worksheet_path = Path(args.external_evidence_acceptance_worksheet_report)
    worksheet = load_json(worksheet_path)
    by_domain = worksheet_rows_by_domain(worksheet)
    summaries = {domain: domain_status(rows) for domain, rows in by_domain.items()}
    campaigns = build_campaigns(summaries)
    ready_count = sum(1 for item in campaigns if item['ready_to_execute_after_controlled_copy'] is True)
    contract_metric_count = sum(len(item['acceptance_contract']) for item in campaigns)
    worksheet_summary = worksheet.get('summary') if isinstance(worksheet.get('summary'), dict) else {}
    quality_gate_matrix = [
        {
            'name': 'acceptance_worksheet_attached',
            'status': 'PASS' if worksheet.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-ACCEPTANCE-WORKSHEET' else 'MISSING',
            'evidence': str(worksheet_path),
            'gap': '',
        },
        {
            'name': 'campaign_plan_complete',
            'status': 'PASS' if len(campaigns) == 4 else 'MISSING',
            'evidence': f'campaigns={len(campaigns)}',
            'gap': '',
        },
        {
            'name': 'campaigns_do_not_clear_blockers',
            'status': 'PASS' if all(item['does_not_clear_production_blockers'] for item in campaigns) else 'MISSING',
            'evidence': 'case validation plan is planning evidence only',
            'gap': '',
        },
        {
            'name': 'campaign_acceptance_contracts_are_structured',
            'status': 'PASS' if contract_metric_count >= 32 else 'MISSING',
            'evidence': f'contract_metrics={contract_metric_count}',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Evidence Case Validation Plan',
        'external_evidence_acceptance_worksheet_report': str(worksheet_path),
        'summary': {
            'worksheet_row_count': worksheet_summary.get('worksheet_row_count'),
            'worksheet_valid_artifact_row_count': worksheet_summary.get('valid_artifact_row_count'),
            'worksheet_missing_or_invalid_artifact_row_count': worksheet_summary.get('missing_or_invalid_artifact_row_count'),
            'worksheet_ready_for_external_evidence_acceptance': worksheet_summary.get('ready_for_external_evidence_acceptance'),
            'domain_count': len(summaries),
            'case_validation_campaign_count': len(campaigns),
            'ready_case_validation_campaign_count': ready_count,
            'integrated_replay_ready': campaigns[-1]['ready_to_execute_after_controlled_copy'],
            'acceptance_contract_metric_count': contract_metric_count,
        },
        'domain_readiness': summaries,
        'case_validation_campaigns': campaigns,
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_h2_external_evidence_acceptance_worksheet_report', worksheet_path),
        ],
        'limitations': [
            'This plan converts accepted external evidence into explicit validation campaigns; it does not launch long CFD runs.',
            'No validation campaign may clear production blockers until its commands run on accepted controlled evidence and the full verifier passes.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'plan must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('worksheet_row_count', 0)) == 14, 'worksheet row count mismatch')
    require(int(summary.get('domain_count', 0)) == 3, 'domain count mismatch')
    require(int(summary.get('case_validation_campaign_count', 0)) == 4, 'campaign count mismatch')
    require(int(summary.get('acceptance_contract_metric_count', 0)) >= 32, 'acceptance contract metric count too small')
    domains = data.get('domain_readiness')
    require(isinstance(domains, dict), 'domain_readiness missing')
    require(set(domains) == EXPECTED_DOMAINS, 'domain_readiness domains mismatch')
    campaigns = data.get('case_validation_campaigns')
    require(isinstance(campaigns, list) and len(campaigns) == 4, 'case_validation_campaigns mismatch')
    require(
        all(isinstance(item.get('commands_after_external_artifacts_pass'), list) and item['commands_after_external_artifacts_pass'] for item in campaigns),
        'campaign commands missing',
    )
    require(
        all(isinstance(item.get('acceptance_metrics'), list) and len(item['acceptance_metrics']) >= 4 for item in campaigns),
        'campaign acceptance metrics incomplete',
    )
    for item in campaigns:
        contract = item.get('acceptance_contract')
        require(isinstance(contract, list) and len(contract) >= 8, f"{item.get('campaign_id')} acceptance contract incomplete")
        for metric_item in contract:
            require(isinstance(metric_item, dict), f"{item.get('campaign_id')} contract metric is not an object")
            for key in ('metric_id', 'source_report', 'source_field', 'comparator', 'threshold', 'description'):
                require(key in metric_item, f"{item.get('campaign_id')} contract metric missing {key}")
            require(
                metric_item.get('comparator') in {'==', '>=', '<=', 'count>=', 'contains_any', 'contains_all'},
                f"{item.get('campaign_id')} unsupported comparator {metric_item.get('comparator')}",
            )
            require(
                metric_item.get('required_for_production_credit') is True,
                f"{item.get('campaign_id')} metric not required for production credit",
            )
    require(all(item.get('does_not_clear_production_blockers') is True for item in campaigns), 'campaign clears blockers')
    if int(summary.get('worksheet_missing_or_invalid_artifact_row_count', 0)) >= 1:
        require(summary.get('integrated_replay_ready') is False, 'integrated replay marked ready with missing artifacts')
        require(int(summary.get('ready_case_validation_campaign_count', -1)) == 0, 'campaigns marked ready with missing artifacts')
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
        '# Engineering H2 External Evidence Case Validation Plan',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Domain Readiness', '']
    for domain, info in sorted(report['domain_readiness'].items()):
        lines.append(
            f"- `{domain}`: valid `{info['valid_artifact_row_count']}/{info['artifact_row_count']}`, "
            f"ready `{info['all_artifacts_valid']}`"
        )
    lines += ['', '## Case Validation Campaigns', '']
    for item in report['case_validation_campaigns']:
        lines.append(f"- `{item['campaign_id']}`: ready `{item['ready_to_execute_after_controlled_copy']}`")
        lines.append(f"  commands: `{'; '.join(item['commands_after_external_artifacts_pass'])}`")
        lines.append(f"  acceptance contract metrics: `{len(item['acceptance_contract'])}`")
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
    parser.add_argument('--external-evidence-acceptance-worksheet-report', default=str(DEFAULT_ACCEPTANCE_WORKSHEET))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_evidence_case_validation_plan VERIFY-PASS '
                f"json={args.verify_json} campaigns={summary['case_validation_campaign_count']} "
                f"ready={summary['ready_case_validation_campaign_count']}"
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
            'engineering_h2_external_evidence_case_validation_plan PASS '
            f"json={out_json} md={out_md} campaigns={report['summary']['case_validation_campaign_count']} "
            f"ready={report['summary']['ready_case_validation_campaign_count']}"
        )
        return 0
    except CaseValidationPlanError as exc:
        print(f'engineering_h2_external_evidence_case_validation_plan FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
