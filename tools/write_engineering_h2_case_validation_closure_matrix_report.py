#!/usr/bin/env python3
"""Write/verify the engineering H2 case-validation closure matrix report."""
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
STATUS = 'PASS-H2-CASE-VALIDATION-CLOSURE-MATRIX'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_case_validation_closure_matrix_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_case_validation_closure_matrix_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_case_validation_closure_matrix_report.md'
DEFAULT_FAILURE_ATTRIBUTION = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_failure_attribution_20260724/'
    'h2_case_validation_failure_attribution_report.json'
)
DEFAULT_WORKSHEET = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724/'
    'h2_external_evidence_acceptance_worksheet.json'
)
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_DASHBOARD = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724/'
    'h2_external_evidence_operations_dashboard.json'
)


class ClosureMatrixError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureMatrixError(message)


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
        raise ClosureMatrixError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ClosureMatrixError(f'invalid JSON evidence {path}: {exc}') from exc
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


def artifact_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get('domain', '')).strip(),
        str(row.get('artifact', '')).strip(),
        str(row.get('drop_path', '')).strip(),
    )


def worksheet_artifacts(worksheet: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    rows = worksheet.get('worksheet_rows')
    require(isinstance(rows, list) and rows, 'worksheet_rows missing')
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        require(isinstance(row, dict), 'worksheet row is not an object')
        key = artifact_key(row)
        require(all(key), f'worksheet row has incomplete artifact key: {key}')
        out[key] = {
            'domain': key[0],
            'artifact': key[1],
            'drop_path': key[2],
            'target_path': row.get('target_path'),
            'blocker': row.get('blocker'),
            'required_action': row.get('required_action'),
            'current_present': row.get('current_present'),
            'current_valid': row.get('current_valid'),
            'current_gaps': row.get('current_gaps', []),
            'validation_command': row.get('validation_command'),
            'controlled_copy_command_after_all_rows_valid': row.get('controlled_copy_command_after_all_rows_valid'),
            'domain_rebuild_commands_after_copy': row.get('domain_rebuild_commands_after_copy', []),
            'final_rebuild_command': row.get('final_rebuild_command'),
            'acceptance_criteria': row.get('acceptance_criteria', []),
        }
    return out


def closure_artifact_count(closure: dict[str, Any]) -> int:
    records = closure.get('domain_closure_records')
    require(isinstance(records, list) and records, 'closure manifest domain records missing')
    total = 0
    for record in records:
        if isinstance(record, dict) and isinstance(record.get('artifact_records'), list):
            total += len(record['artifact_records'])
    return total


def metric_problem_count(failure_attribution: dict[str, Any]) -> int:
    records = failure_attribution.get('metric_attributions')
    require(isinstance(records, list), 'metric_attributions missing')
    return len(records)


def metric_signature(record: dict[str, Any]) -> dict[str, Any]:
    return {
        'campaign_id': record.get('campaign_id'),
        'metric_id': record.get('metric_id'),
        'metric_status': record.get('metric_status'),
        'source_report': record.get('source_report'),
        'source_field': record.get('source_field'),
        'gap': record.get('gap', ''),
        'operator_action_class': record.get('operator_action_class'),
    }


def build_artifact_matrix(
    worksheet_by_artifact: dict[tuple[str, str, str], dict[str, Any]],
    failure_attribution: dict[str, Any],
) -> list[dict[str, Any]]:
    by_artifact: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    metric_records = failure_attribution.get('metric_attributions')
    require(isinstance(metric_records, list), 'metric_attributions missing')
    for record in metric_records:
        require(isinstance(record, dict), 'metric attribution is not an object')
        rows = record.get('artifact_rows')
        require(isinstance(rows, list), f"{record.get('metric_id')} artifact_rows missing")
        for row in rows:
            require(isinstance(row, dict), f"{record.get('metric_id')} artifact row is not an object")
            key = artifact_key(row)
            if all(key):
                by_artifact[key].append(metric_signature(record))

    matrix = []
    for key, artifact in sorted(worksheet_by_artifact.items()):
        metrics = by_artifact.get(key, [])
        metric_ids = sorted({str(item.get('metric_id')) for item in metrics if item.get('metric_id')})
        failed_metrics = [item for item in metrics if item.get('metric_status') == 'FAIL']
        deferred_metrics = [item for item in metrics if item.get('metric_status') == 'DEFERRED']
        matrix.append(
            {
                **artifact,
                'problem_metric_count': len(metric_ids),
                'failed_metric_count': len({str(item.get('metric_id')) for item in failed_metrics}),
                'deferred_metric_count': len({str(item.get('metric_id')) for item in deferred_metrics}),
                'problem_metric_ids': metric_ids,
                'problem_metrics': sorted(metrics, key=lambda item: (str(item.get('campaign_id')), str(item.get('metric_id')))),
                'ready_to_attempt_copy': artifact.get('current_valid') is True,
                'blocking_state': 'WAITING_FOR_VALID_EXTERNAL_ARTIFACT'
                if artifact.get('current_valid') is not True
                else 'READY_FOR_CONTROLLED_COPY',
            }
        )
    return matrix


def build_domain_records(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in matrix:
        grouped[str(item['domain'])].append(item)
    records = []
    for domain, rows in sorted(grouped.items()):
        metric_ids = {metric_id for row in rows for metric_id in row.get('problem_metric_ids', [])}
        failed_metric_ids = {
            metric['metric_id']
            for row in rows
            for metric in row.get('problem_metrics', [])
            if metric.get('metric_status') == 'FAIL'
        }
        deferred_metric_ids = {
            metric['metric_id']
            for row in rows
            for metric in row.get('problem_metrics', [])
            if metric.get('metric_status') == 'DEFERRED'
        }
        records.append(
            {
                'domain': domain,
                'artifact_count': len(rows),
                'valid_artifact_count': sum(1 for row in rows if row.get('current_valid') is True),
                'missing_or_invalid_artifact_count': sum(1 for row in rows if row.get('current_valid') is not True),
                'problem_metric_count': len(metric_ids),
                'failed_metric_count': len(failed_metric_ids),
                'deferred_metric_count': len(deferred_metric_ids),
                'blocking_artifacts': [
                    {
                        'artifact': row.get('artifact'),
                        'drop_path': row.get('drop_path'),
                        'target_path': row.get('target_path'),
                        'required_action': row.get('required_action'),
                        'problem_metric_count': row.get('problem_metric_count'),
                    }
                    for row in rows
                    if row.get('current_valid') is not True
                ],
            }
        )
    return records


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    failure_path = Path(args.case_validation_failure_attribution_report)
    worksheet_path = Path(args.external_evidence_acceptance_worksheet_report)
    closure_path = Path(args.production_blocker_closure_manifest_report)
    dashboard_path = Path(args.external_evidence_operations_dashboard_report)
    failure = load_json(failure_path)
    worksheet = load_json(worksheet_path)
    closure = load_json(closure_path)
    dashboard = load_json(dashboard_path)

    require(failure.get('status') == 'PASS-H2-CASE-VALIDATION-FAILURE-ATTRIBUTION', 'failure attribution did not PASS')
    require(worksheet.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-ACCEPTANCE-WORKSHEET', 'worksheet did not PASS')
    require(closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST', 'closure manifest did not PASS')
    require(
        dashboard.get('status') in {
            'PASS-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
            'NOT_READY-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
        },
        'operations dashboard status invalid',
    )

    artifacts = worksheet_artifacts(worksheet)
    matrix = build_artifact_matrix(artifacts, failure)
    domain_records = build_domain_records(matrix)
    problem_metric_ids = {
        metric_id
        for row in matrix
        for metric_id in row.get('problem_metric_ids', [])
    }
    problem_metrics = metric_problem_count(failure)
    rows_without_metrics = [row for row in matrix if int(row.get('problem_metric_count', 0)) == 0]
    valid_artifacts = sum(1 for row in matrix if row.get('current_valid') is True)
    missing_or_invalid = len(matrix) - valid_artifacts
    current_status = dashboard.get('current_status') if isinstance(dashboard.get('current_status'), dict) else {}
    quality_gate_matrix = [
        {
            'name': 'failure_attribution_attached',
            'status': 'PASS',
            'evidence': str(failure_path),
            'gap': '',
        },
        {
            'name': 'artifact_rows_match_closure_manifest',
            'status': 'PASS' if len(matrix) == closure_artifact_count(closure) == 14 else 'FAIL',
            'evidence': f'matrix={len(matrix)} closure={closure_artifact_count(closure)}',
            'gap': '',
        },
        {
            'name': 'all_problem_metrics_mapped_to_artifacts',
            'status': 'PASS' if len(problem_metric_ids) == problem_metrics else 'FAIL',
            'evidence': f'mapped={len(problem_metric_ids)} problem={problem_metrics}',
            'gap': '',
        },
        {
            'name': 'every_artifact_has_metric_closure_context',
            'status': 'PASS' if not rows_without_metrics else 'FAIL',
            'evidence': f'rows_without_metrics={len(rows_without_metrics)}',
            'gap': ','.join(f"{row['domain']}/{row['artifact']}" for row in rows_without_metrics),
        },
        {
            'name': 'current_not_ready_state_preserved',
            'status': 'PASS'
            if current_status.get('ready_for_production_blocker_clearance') is False and missing_or_invalid >= 1
            else 'FAIL',
            'evidence': f'missing_or_invalid={missing_or_invalid}',
            'gap': '',
        },
        {
            'name': 'closure_matrix_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'matrix is planning/traceability evidence only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Case Validation Closure Matrix',
        'case_validation_failure_attribution_report': str(failure_path),
        'external_evidence_acceptance_worksheet_report': str(worksheet_path),
        'production_blocker_closure_manifest_report': str(closure_path),
        'external_evidence_operations_dashboard_report': str(dashboard_path),
        'summary': {
            'artifact_row_count': len(matrix),
            'valid_artifact_row_count': valid_artifacts,
            'missing_or_invalid_artifact_row_count': missing_or_invalid,
            'problem_metric_count': problem_metrics,
            'mapped_problem_metric_count': len(problem_metric_ids),
            'unmapped_problem_metric_count': max(problem_metrics - len(problem_metric_ids), 0),
            'artifact_rows_without_metric_context_count': len(rows_without_metrics),
            'domain_count': len(domain_records),
            'ready_for_controlled_copy': missing_or_invalid == 0,
            'ready_for_production_blocker_clearance': False,
        },
        'domain_records': domain_records,
        'artifact_closure_matrix': matrix,
        'operator_execution_order': dashboard.get('next_operator_commands', []),
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'evidence_files': [
            evidence_entry('engineering_h2_case_validation_failure_attribution_report', failure_path),
            evidence_entry('engineering_h2_external_evidence_acceptance_worksheet_report', worksheet_path),
            evidence_entry('engineering_h2_production_blocker_closure_manifest_report', closure_path),
            evidence_entry('engineering_h2_external_evidence_operations_dashboard_report', dashboard_path),
        ],
        'limitations': [
            'This matrix links missing external artifacts to failed/deferred acceptance metrics; it does not supply external data.',
            'Production credit can only change after all artifacts pass the strict drop gate, controlled copy is applied, campaigns are rebuilt, and the final verifier passes.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'closure matrix must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('artifact_row_count', 0)) == 14, 'artifact row count must be 14')
    require(int(summary.get('problem_metric_count', 0)) >= 35, 'problem metric count too small')
    require(
        int(summary.get('mapped_problem_metric_count', -1)) == int(summary.get('problem_metric_count', -2)),
        'not all problem metrics mapped',
    )
    require(int(summary.get('unmapped_problem_metric_count', -1)) == 0, 'unmapped problem metrics remain')
    require(
        int(summary.get('artifact_rows_without_metric_context_count', -1)) == 0,
        'artifact rows without metric context remain',
    )
    require(int(summary.get('domain_count', 0)) == 3, 'domain count must be 3')
    require(summary.get('ready_for_production_blocker_clearance') is False, 'closure matrix must not mark production ready')
    matrix = data.get('artifact_closure_matrix')
    require(isinstance(matrix, list) and len(matrix) == 14, 'artifact closure matrix must contain 14 rows')
    for row in matrix:
        require(isinstance(row, dict), 'matrix row is not an object')
        require(str(row.get('domain', '')).strip(), 'matrix row missing domain')
        require(str(row.get('artifact', '')).strip(), 'matrix row missing artifact')
        require(str(row.get('drop_path', '')).strip(), 'matrix row missing drop_path')
        require(str(row.get('target_path', '')).strip(), 'matrix row missing target_path')
        require(int(row.get('problem_metric_count', 0)) >= 1, f"{row.get('domain')}/{row.get('artifact')} has no metrics")
        require(isinstance(row.get('problem_metrics'), list) and row['problem_metrics'], 'problem_metrics missing')
    domains = data.get('domain_records')
    require(isinstance(domains, list) and len(domains) == 3, 'domain_records must contain three domains')
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
        '# Engineering H2 Case Validation Closure Matrix',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Domain Records', '']
    for domain in report['domain_records']:
        lines.append(
            f"- `{domain['domain']}`: artifacts `{domain['valid_artifact_count']}/{domain['artifact_count']}`, "
            f"problem metrics `{domain['problem_metric_count']}`, failed `{domain['failed_metric_count']}`, "
            f"deferred `{domain['deferred_metric_count']}`"
        )
    lines += ['', '## Artifact Matrix', '']
    for row in report['artifact_closure_matrix']:
        lines.append(
            f"- `{row['domain']}/{row['artifact']}`: valid=`{row['current_valid']}` "
            f"metrics=`{row['problem_metric_count']}` target=`{row['target_path']}`"
        )
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
    parser.add_argument('--case-validation-failure-attribution-report', default=str(DEFAULT_FAILURE_ATTRIBUTION))
    parser.add_argument('--external-evidence-acceptance-worksheet-report', default=str(DEFAULT_WORKSHEET))
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
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
                'engineering_h2_case_validation_closure_matrix VERIFY-PASS '
                f"json={args.verify_json} artifacts={summary['artifact_row_count']} "
                f"metrics={summary['mapped_problem_metric_count']}/{summary['problem_metric_count']}"
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
            'engineering_h2_case_validation_closure_matrix PASS '
            f"json={out_json} md={out_md} artifacts={report['summary']['artifact_row_count']} "
            f"metrics={report['summary']['mapped_problem_metric_count']}/{report['summary']['problem_metric_count']}"
        )
        return 0
    except ClosureMatrixError as exc:
        print(f'engineering_h2_case_validation_closure_matrix FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
