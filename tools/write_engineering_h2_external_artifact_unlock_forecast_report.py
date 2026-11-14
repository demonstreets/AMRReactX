#!/usr/bin/env python3
"""Write/verify the engineering H2 external-artifact unlock forecast report."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-EXTERNAL-ARTIFACT-UNLOCK-FORECAST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_unlock_forecast_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_unlock_forecast_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_unlock_forecast_report.md'
DEFAULT_SCORECARD = Path(
    'docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json'
)
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_CLOSURE_MATRIX = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_closure_matrix_20260724/'
    'h2_case_validation_closure_matrix_report.json'
)
DEFAULT_DASHBOARD = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724/'
    'h2_external_evidence_operations_dashboard.json'
)

PRODUCTION_READY_TARGET_PERCENT = 90.0
DOMAIN_PRIORITY = {
    'real_cad_cleanup': 10,
    'external_plume_shape_reference': 20,
    'fire_consequence_calibration': 30,
}
DOMAIN_SCORECARD_GATES = {
    'real_cad_cleanup': [
        'obstacle_geometry_and_stl_pipeline',
        'long_duration_stability',
    ],
    'external_plume_shape_reference': [
        'h2_dispersion_and_hazard_outputs',
        'production_scale_and_reference_accuracy',
        'long_duration_stability',
    ],
    'fire_consequence_calibration': [
        'ignition_fire_consequence_chain',
    ],
}


class UnlockForecastError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UnlockForecastError(message)


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
        raise UnlockForecastError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise UnlockForecastError(f'invalid JSON evidence {path}: {exc}') from exc
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


def scores(scorecard: dict[str, Any]) -> dict[str, Any]:
    value = scorecard.get('scores')
    require(isinstance(value, dict), 'scorecard scores missing')
    return value


def scorecard_gate_map(scorecard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    gates = scorecard.get('gates')
    require(isinstance(gates, list) and gates, 'scorecard gates missing')
    return {str(gate.get('name')): gate for gate in gates if isinstance(gate, dict)}


def closure_domain_map(closure: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = closure.get('domain_closure_records')
    require(isinstance(records, list) and records, 'closure manifest domain records missing')
    return {str(item.get('domain')): item for item in records if isinstance(item, dict)}


def matrix_domain_map(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = matrix.get('domain_records')
    require(isinstance(records, list) and records, 'closure matrix domain_records missing')
    return {str(item.get('domain')): item for item in records if isinstance(item, dict)}


def dashboard_commands(dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    commands = dashboard.get('next_operator_commands')
    require(isinstance(commands, list) and len(commands) >= 6, 'dashboard operator command sequence incomplete')
    return [item for item in commands if isinstance(item, dict)]


def blocker_to_domain(blocker: str, domains: dict[str, dict[str, Any]]) -> str | None:
    for domain, record in domains.items():
        if record.get('blocker') == blocker:
            return domain
    return None


def gate_records_for_domain(domain: str, gate_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for gate_name in DOMAIN_SCORECARD_GATES.get(domain, []):
        gate = gate_map.get(gate_name)
        if not gate:
            continue
        records.append(
            {
                'name': gate.get('name'),
                'status': gate.get('status'),
                'production_points': gate.get('production_points'),
                'production_weight': gate.get('production_weight'),
                'gaps': gate.get('gaps', []),
            }
        )
    return records


def build_domain_unlock_record(
    domain: str,
    closure_record: dict[str, Any],
    matrix_record: dict[str, Any],
    gate_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    artifacts = closure_record.get('artifact_records')
    require(isinstance(artifacts, list) and artifacts, f'{domain} artifact records missing')
    command_sequence = closure_record.get('domain_command_sequence')
    require(isinstance(command_sequence, list) and command_sequence, f'{domain} command sequence missing')
    blocking_artifacts = matrix_record.get('blocking_artifacts')
    require(isinstance(blocking_artifacts, list), f'{domain} matrix blocking artifacts missing')
    return {
        'domain': domain,
        'priority': DOMAIN_PRIORITY.get(domain, 99),
        'blocker': closure_record.get('blocker'),
        'current_ready_for_execution': closure_record.get('ready_for_execution') is True,
        'artifact_count': len(artifacts),
        'valid_artifact_count': matrix_record.get('valid_artifact_count'),
        'missing_or_invalid_artifact_count': matrix_record.get('missing_or_invalid_artifact_count'),
        'problem_metric_count': matrix_record.get('problem_metric_count'),
        'failed_metric_count': matrix_record.get('failed_metric_count'),
        'deferred_metric_count': matrix_record.get('deferred_metric_count'),
        'scorecard_gates_affected': gate_records_for_domain(domain, gate_map),
        'artifact_unlock_requirements': blocking_artifacts,
        'domain_rebuild_command_sequence_after_controlled_copy': command_sequence,
        'unlock_completion_criteria': [
            'all listed artifacts are present under the external drop root and pass the strict drop validator',
            'operator receipt is present and valid',
            'controlled copy is applied with the explicit confirmation token',
            'domain reports and scorecard are rebuilt',
            'case-validation acceptance evaluation passes or no longer reports domain-linked failures',
            'full engineering H2 production verifier passes',
        ],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    scorecard_path = Path(args.scorecard)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    matrix_path = Path(args.case_validation_closure_matrix_report)
    dashboard_path = Path(args.external_evidence_operations_dashboard_report)
    scorecard = load_json(scorecard_path)
    closure = load_json(closure_path)
    matrix = load_json(matrix_path)
    dashboard = load_json(dashboard_path)

    require(scorecard.get('status') in {'PRODUCTION_READY', 'NOT_PRODUCTION_READY'}, 'scorecard status invalid')
    require(closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST', 'closure manifest did not PASS')
    require(matrix.get('status') == 'PASS-H2-CASE-VALIDATION-CLOSURE-MATRIX', 'closure matrix did not PASS')
    require(
        dashboard.get('status') in {
            'PASS-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
            'NOT_READY-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
        },
        'dashboard status invalid',
    )

    score_values = scores(scorecard)
    production_percent = float(score_values.get('engineering_production_credibility_percent', 0.0))
    functional_percent = float(score_values.get('engineering_functional_coverage_percent', 0.0))
    blocker_domains = closure_domain_map(closure)
    matrix_domains = matrix_domain_map(matrix)
    gate_map = scorecard_gate_map(scorecard)
    blocking_gaps = scorecard.get('blocking_gaps')
    require(isinstance(blocking_gaps, list), 'scorecard blocking gaps missing')
    domain_records = [
        build_domain_unlock_record(domain, closure_record, matrix_domains.get(domain, {}), gate_map)
        for domain, closure_record in sorted(blocker_domains.items(), key=lambda item: DOMAIN_PRIORITY.get(item[0], 99))
    ]
    blocker_map = [
        {
            'blocker': blocker,
            'domain': blocker_to_domain(str(blocker), blocker_domains),
        }
        for blocker in blocking_gaps
    ]
    unmapped_blockers = [item for item in blocker_map if not item['domain']]
    total_artifacts = sum(int(item['artifact_count']) for item in domain_records)
    missing_artifacts = sum(int(item.get('missing_or_invalid_artifact_count') or 0) for item in domain_records)
    mapped_metric_ids = int(matrix.get('summary', {}).get('mapped_problem_metric_count', 0)) if isinstance(matrix.get('summary'), dict) else 0
    problem_metric_count = int(matrix.get('summary', {}).get('problem_metric_count', 0)) if isinstance(matrix.get('summary'), dict) else 0
    quality_gate_matrix = [
        {
            'name': 'scorecard_attached',
            'status': 'PASS',
            'evidence': str(scorecard_path),
            'gap': '',
        },
        {
            'name': 'all_scorecard_blockers_mapped_to_domains',
            'status': 'PASS' if not unmapped_blockers and len(blocker_map) == 3 else 'FAIL',
            'evidence': f'blockers={len(blocker_map)} unmapped={len(unmapped_blockers)}',
            'gap': ','.join(str(item['blocker']) for item in unmapped_blockers),
        },
        {
            'name': 'artifact_unlock_inventory_complete',
            'status': 'PASS' if total_artifacts == 14 and missing_artifacts >= 1 else 'FAIL',
            'evidence': f'artifacts={total_artifacts} missing={missing_artifacts}',
            'gap': '',
        },
        {
            'name': 'case_validation_metrics_mapped',
            'status': 'PASS' if problem_metric_count == mapped_metric_ids and problem_metric_count >= 35 else 'FAIL',
            'evidence': f'mapped={mapped_metric_ids} problem={problem_metric_count}',
            'gap': '',
        },
        {
            'name': 'production_credit_not_forecast_as_cleared',
            'status': 'PASS' if production_percent < PRODUCTION_READY_TARGET_PERCENT and scorecard.get('status') == 'NOT_PRODUCTION_READY' else 'FAIL',
            'evidence': f'production={production_percent:.1f} target={PRODUCTION_READY_TARGET_PERCENT:.1f}',
            'gap': '',
        },
        {
            'name': 'operator_command_sequence_available',
            'status': 'PASS' if len(dashboard_commands(dashboard)) >= 6 else 'FAIL',
            'evidence': f'commands={len(dashboard_commands(dashboard))}',
            'gap': '',
        },
        {
            'name': 'unlock_forecast_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'forecast is planning/traceability evidence only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Artifact Unlock Forecast',
        'scorecard_report': str(scorecard_path),
        'production_blocker_closure_manifest_report': str(closure_path),
        'case_validation_closure_matrix_report': str(matrix_path),
        'external_evidence_operations_dashboard_report': str(dashboard_path),
        'summary': {
            'scorecard_status': scorecard.get('status'),
            'functional_coverage_percent': functional_percent,
            'production_credibility_percent': production_percent,
            'production_ready_target_percent': PRODUCTION_READY_TARGET_PERCENT,
            'production_credibility_gap_to_target_percent': round(
                max(PRODUCTION_READY_TARGET_PERCENT - production_percent, 0.0),
                1,
            ),
            'unresolved_blocker_count': len(blocking_gaps),
            'unmapped_blocker_count': len(unmapped_blockers),
            'domain_unlock_count': len(domain_records),
            'artifact_unlock_requirement_count': total_artifacts,
            'missing_or_invalid_artifact_count': missing_artifacts,
            'case_validation_problem_metric_count': problem_metric_count,
            'case_validation_mapped_problem_metric_count': mapped_metric_ids,
            'ready_for_controlled_copy': missing_artifacts == 0,
            'ready_for_production_blocker_clearance': False,
        },
        'blocker_domain_map': blocker_map,
        'domain_unlock_records': domain_records,
        'operator_execution_order': dashboard_commands(dashboard),
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'limitations': [
            'This forecast orders and traces the remaining external-artifact work; it does not supply real data or change scorecard credit.',
            'Projected readiness remains unclaimed until strict artifact gates, controlled copy, case-validation campaigns, and final production verification all pass.',
        ],
        'evidence_files': [
            evidence_entry('engineering_production_scorecard', scorecard_path),
            evidence_entry('engineering_h2_production_blocker_closure_manifest_report', closure_path),
            evidence_entry('engineering_h2_case_validation_closure_matrix_report', matrix_path),
            evidence_entry('engineering_h2_external_evidence_operations_dashboard_report', dashboard_path),
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'forecast must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('unresolved_blocker_count', 0)) == 3, 'unresolved blocker count must be 3')
    require(int(summary.get('unmapped_blocker_count', -1)) == 0, 'unmapped blockers remain')
    require(int(summary.get('domain_unlock_count', 0)) == 3, 'domain unlock count must be 3')
    require(int(summary.get('artifact_unlock_requirement_count', 0)) == 14, 'artifact unlock count must be 14')
    require(int(summary.get('missing_or_invalid_artifact_count', 0)) >= 1, 'current state must retain missing artifacts')
    require(
        int(summary.get('case_validation_mapped_problem_metric_count', -1))
        == int(summary.get('case_validation_problem_metric_count', -2)),
        'case-validation problem metrics are not fully mapped',
    )
    require(float(summary.get('production_credibility_percent', 100.0)) < PRODUCTION_READY_TARGET_PERCENT, 'forecast overclaims production readiness')
    require(summary.get('ready_for_production_blocker_clearance') is False, 'forecast cannot mark blocker clearance ready')
    domain_records = data.get('domain_unlock_records')
    require(isinstance(domain_records, list) and len(domain_records) == 3, 'domain unlock records must contain three domains')
    for record in domain_records:
        require(isinstance(record, dict), 'domain unlock record is not an object')
        require(str(record.get('domain', '')).strip(), 'domain unlock record missing domain')
        require(str(record.get('blocker', '')).strip(), f"{record.get('domain')} missing blocker")
        require(int(record.get('artifact_count', 0)) >= 1, f"{record.get('domain')} missing artifacts")
        require(int(record.get('problem_metric_count', 0)) >= 1, f"{record.get('domain')} missing metrics")
        require(isinstance(record.get('scorecard_gates_affected'), list), f"{record.get('domain')} gates missing")
        require(
            isinstance(record.get('domain_rebuild_command_sequence_after_controlled_copy'), list)
            and record['domain_rebuild_command_sequence_after_controlled_copy'],
            f"{record.get('domain')} rebuild commands missing",
        )
    commands = data.get('operator_execution_order')
    require(isinstance(commands, list) and len(commands) >= 6, 'operator execution order incomplete')
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list) and gates, 'quality gate matrix missing')
    require(all(item.get('status') == 'PASS' for item in gates if isinstance(item, dict)), 'quality gate failed')
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
        '# Engineering H2 External Artifact Unlock Forecast',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Domain Unlocks', '']
    for record in report['domain_unlock_records']:
        gates = ', '.join(str(item.get('name')) for item in record['scorecard_gates_affected'])
        lines.append(
            f"- `{record['domain']}`: artifacts `{record['valid_artifact_count']}/{record['artifact_count']}`, "
            f"metrics `{record['problem_metric_count']}`, blocker `{record['blocker']}`, gates `{gates}`"
        )
    lines += ['', '## Operator Execution Order', '']
    for item in report['operator_execution_order']:
        lines.append(f"- `{item.get('step')}`: `{item.get('command')}`")
    lines += ['', '## Quality Gates', '']
    for gate in report['quality_gate_matrix']:
        lines.append(f"- `{gate['name']}`: `{gate['status']}`")
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
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--case-validation-closure-matrix-report', default=str(DEFAULT_CLOSURE_MATRIX))
    parser.add_argument('--external-evidence-operations-dashboard-report', default=str(DEFAULT_DASHBOARD))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_artifact_unlock_forecast VERIFY-PASS '
                f"json={args.verify_json} blockers={summary['unresolved_blocker_count']} "
                f"artifacts={summary['artifact_unlock_requirement_count']} "
                f"metrics={summary['case_validation_mapped_problem_metric_count']}/"
                f"{summary['case_validation_problem_metric_count']}"
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
            'engineering_h2_external_artifact_unlock_forecast PASS '
            f"json={out_json} md={out_md} blockers={report['summary']['unresolved_blocker_count']} "
            f"artifacts={report['summary']['artifact_unlock_requirement_count']} "
            f"metrics={report['summary']['case_validation_mapped_problem_metric_count']}/"
            f"{report['summary']['case_validation_problem_metric_count']}"
        )
        return 0
    except UnlockForecastError as exc:
        print(f'engineering_h2_external_artifact_unlock_forecast FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
