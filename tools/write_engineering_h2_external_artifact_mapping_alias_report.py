#!/usr/bin/env python3
"""Write/verify the engineering H2 external artifact mapping alias report."""
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
STATUS = 'PASS-H2-EXTERNAL-ARTIFACT-MAPPING-ALIAS'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_mapping_alias_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_mapping_alias_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_mapping_alias_report.md'
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_DROP_VALIDATOR = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
    'h2_external_artifact_drop_validator_report.json'
)
DEFAULT_ACCEPTANCE_WORKSHEET = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724/'
    'h2_external_evidence_acceptance_worksheet.json'
)
DEFAULT_INGESTION_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_ingestion_plan_20260724/'
    'h2_external_artifact_ingestion_plan.json'
)

ALLOWED_ALIAS_GROUPS = [
    {
        'alias_group_id': 'real_cad_cleanup_quality_record_legacy_alias',
        'domain': 'real_cad_cleanup',
        'target_path': (
            'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
            'package/real_cad_cleanup_quality_record.csv'
        ),
        'drop_path': (
            'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
            'drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv'
        ),
        'artifacts': ['cleanup_quality_records', 'real_cad_cleanup_quality_record.csv'],
        'canonical_artifact': 'real_cad_cleanup_quality_record.csv',
        'reason': (
            'cleanup_quality_records is a legacy requirement label for the same quality-record CSV; '
            'the concrete file artifact remains real_cad_cleanup_quality_record.csv.'
        ),
    },
]


class MappingAliasError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MappingAliasError(message)


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
        raise MappingAliasError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise MappingAliasError(f'invalid JSON evidence {path}: {exc}') from exc
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


def alias_key(domain: str, artifacts: list[str], path: str) -> tuple[str, tuple[str, ...], str]:
    return (domain, tuple(sorted(artifacts)), path)


def allowed_target_alias_keys() -> set[tuple[str, tuple[str, ...], str]]:
    return {
        alias_key(str(item['domain']), list(item['artifacts']), str(item['target_path']))
        for item in ALLOWED_ALIAS_GROUPS
    }


def allowed_drop_alias_keys() -> set[tuple[str, tuple[str, ...], str]]:
    return {
        alias_key(str(item['domain']), list(item['artifacts']), str(item['drop_path']))
        for item in ALLOWED_ALIAS_GROUPS
    }


def collect_closure_rows(closure: dict[str, Any]) -> list[dict[str, str]]:
    records = closure.get('domain_closure_records')
    require(isinstance(records, list) and records, 'closure domain records missing')
    rows: list[dict[str, str]] = []
    for record in records:
        require(isinstance(record, dict), 'closure domain record is not an object')
        domain = str(record.get('domain', '')).strip()
        require(domain, 'closure domain missing')
        artifacts = record.get('artifact_records')
        require(isinstance(artifacts, list), f'{domain} artifact_records missing')
        for item in artifacts:
            require(isinstance(item, dict), f'{domain} artifact record is not an object')
            artifact = str(item.get('artifact', '')).strip()
            target_path = str(item.get('target_path', '')).strip()
            require(artifact, f'{domain} artifact missing')
            require(target_path, f'{domain}/{artifact} target_path missing')
            rows.append({'domain': domain, 'artifact': artifact, 'target_path': target_path})
    return rows


def collect_drop_paths(drop: dict[str, Any]) -> dict[tuple[str, str], str]:
    records = drop.get('domain_records')
    require(isinstance(records, list) and records, 'drop validator domain records missing')
    result: dict[tuple[str, str], str] = {}
    for record in records:
        require(isinstance(record, dict), 'drop domain record is not an object')
        domain = str(record.get('domain', '')).strip()
        validations = record.get('artifact_validations')
        require(isinstance(validations, list), f'{domain} artifact_validations missing')
        for item in validations:
            require(isinstance(item, dict), f'{domain} drop artifact validation is not an object')
            artifact = str(item.get('artifact', '')).strip()
            validation = item.get('drop_validation')
            require(isinstance(validation, dict), f'{domain}/{artifact} drop_validation missing')
            drop_path = str(validation.get('path', '')).strip()
            require(drop_path, f'{domain}/{artifact} drop path missing')
            result[(domain, artifact)] = drop_path
    return result


def collect_worksheet_rows(worksheet: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    rows = worksheet.get('worksheet_rows')
    require(isinstance(rows, list) and rows, 'worksheet_rows missing')
    result: dict[tuple[str, str], dict[str, str]] = {}
    for item in rows:
        require(isinstance(item, dict), 'worksheet row is not an object')
        domain = str(item.get('domain', '')).strip()
        artifact = str(item.get('artifact', '')).strip()
        result[(domain, artifact)] = {
            'target_path': str(item.get('target_path', '')).strip(),
            'drop_path': str(item.get('drop_path', '')).strip(),
        }
    return result


def duplicate_groups(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row['domain'], row[field])].append(row)
    groups: list[dict[str, Any]] = []
    for (domain, path), items in sorted(grouped.items(), key=lambda pair: (pair[0][0], pair[0][1])):
        if len(items) > 1:
            artifacts = sorted(item['artifact'] for item in items)
            groups.append(
                {
                    'domain': domain,
                    field: path,
                    'artifacts': artifacts,
                    'artifact_count': len(artifacts),
                }
            )
    return groups


def unexpected_alias_groups(groups: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    allowed = allowed_target_alias_keys() if field == 'target_path' else allowed_drop_alias_keys()
    unexpected: list[dict[str, Any]] = []
    for group in groups:
        key = alias_key(str(group['domain']), list(group['artifacts']), str(group[field]))
        if key not in allowed:
            unexpected.append(group)
    return unexpected


def merged_rows(
    closure_rows: list[dict[str, str]],
    drop_paths: dict[tuple[str, str], str],
    worksheet_rows: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in closure_rows:
        key = (row['domain'], row['artifact'])
        worksheet = worksheet_rows.get(key, {})
        drop_path = drop_paths.get(key, '')
        worksheet_target = worksheet.get('target_path', '')
        worksheet_drop = worksheet.get('drop_path', '')
        out.append(
            {
                'domain': row['domain'],
                'artifact': row['artifact'],
                'target_path': row['target_path'],
                'drop_path': drop_path,
                'worksheet_target_path': worksheet_target,
                'worksheet_drop_path': worksheet_drop,
                'target_path_matches_worksheet': worksheet_target == row['target_path'],
                'drop_path_matches_worksheet': worksheet_drop == drop_path,
            }
        )
    return out


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    closure_path = Path(args.production_blocker_closure_manifest_report)
    drop_path = Path(args.external_artifact_drop_validator_report)
    worksheet_path = Path(args.external_evidence_acceptance_worksheet_report)
    ingestion_path = Path(args.external_artifact_ingestion_plan_report)

    closure = load_json(closure_path)
    drop = load_json(drop_path)
    worksheet = load_json(worksheet_path)
    ingestion = load_json(ingestion_path)

    require(closure.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST', 'closure manifest did not PASS')
    require(drop.get('status') in {'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'}, 'drop validator status invalid')
    require(
        worksheet.get('status') == 'PASS-H2-EXTERNAL-EVIDENCE-ACCEPTANCE-WORKSHEET',
        'acceptance worksheet did not PASS',
    )
    require(ingestion.get('status') in {'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'}, 'ingestion plan status invalid')

    closure_rows = collect_closure_rows(closure)
    rows = merged_rows(closure_rows, collect_drop_paths(drop), collect_worksheet_rows(worksheet))
    target_duplicate_groups = duplicate_groups(rows, 'target_path')
    drop_duplicate_groups = duplicate_groups(rows, 'drop_path')
    unexpected_target_groups = unexpected_alias_groups(target_duplicate_groups, 'target_path')
    unexpected_drop_groups = unexpected_alias_groups(drop_duplicate_groups, 'drop_path')
    worksheet_target_mismatches = [row for row in rows if not row['target_path_matches_worksheet']]
    worksheet_drop_mismatches = [row for row in rows if not row['drop_path_matches_worksheet']]
    alias_group_ids = sorted(item['alias_group_id'] for item in ALLOWED_ALIAS_GROUPS)
    allowed_target_group_keys = allowed_target_alias_keys()
    observed_target_group_keys = {
        alias_key(str(item['domain']), list(item['artifacts']), str(item['target_path']))
        for item in target_duplicate_groups
    }
    observed_allowed_alias_group_count = len(allowed_target_group_keys & observed_target_group_keys)
    quality_gate_matrix = [
        {
            'name': 'all_artifact_rows_are_cross_referenced',
            'status': 'PASS' if not worksheet_target_mismatches and not worksheet_drop_mismatches else 'FAIL',
            'evidence': f'rows={len(rows)}',
            'gap': '; '.join(
                f"{row['domain']}/{row['artifact']}"
                for row in worksheet_target_mismatches + worksheet_drop_mismatches
            ),
        },
        {
            'name': 'duplicate_target_paths_are_declared_aliases',
            'status': 'PASS' if not unexpected_target_groups else 'FAIL',
            'evidence': f'duplicate_target_groups={len(target_duplicate_groups)} allowed={observed_allowed_alias_group_count}',
            'gap': '; '.join(str(group) for group in unexpected_target_groups),
        },
        {
            'name': 'duplicate_drop_paths_are_declared_aliases',
            'status': 'PASS' if not unexpected_drop_groups else 'FAIL',
            'evidence': f'duplicate_drop_groups={len(drop_duplicate_groups)} allowed={observed_allowed_alias_group_count}',
            'gap': '; '.join(str(group) for group in unexpected_drop_groups),
        },
        {
            'name': 'alias_audit_does_not_clear_blockers',
            'status': 'PASS',
            'evidence': 'mapping alias audit is bookkeeping evidence only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Artifact Mapping Alias Report',
        'production_blocker_closure_manifest_report': str(closure_path),
        'external_artifact_drop_validator_report': str(drop_path),
        'external_evidence_acceptance_worksheet_report': str(worksheet_path),
        'external_artifact_ingestion_plan_report': str(ingestion_path),
        'summary': {
            'domain_count': len({row['domain'] for row in rows}),
            'artifact_row_count': len(rows),
            'alias_group_count': len(ALLOWED_ALIAS_GROUPS),
            'observed_allowed_alias_group_count': observed_allowed_alias_group_count,
            'duplicate_target_group_count': len(target_duplicate_groups),
            'duplicate_drop_group_count': len(drop_duplicate_groups),
            'unexpected_duplicate_target_group_count': len(unexpected_target_groups),
            'unexpected_duplicate_drop_group_count': len(unexpected_drop_groups),
            'worksheet_target_mismatch_count': len(worksheet_target_mismatches),
            'worksheet_drop_mismatch_count': len(worksheet_drop_mismatches),
        },
        'allowed_alias_groups': ALLOWED_ALIAS_GROUPS,
        'target_path_duplicate_groups': target_duplicate_groups,
        'drop_path_duplicate_groups': drop_duplicate_groups,
        'unexpected_target_path_duplicate_groups': unexpected_target_groups,
        'unexpected_drop_path_duplicate_groups': unexpected_drop_groups,
        'artifact_mapping_rows': rows,
        'quality_gate_matrix': quality_gate_matrix,
        'does_not_clear_production_blockers': True,
        'operator_note': (
            'Only one real cleanup-quality CSV should be staged for the allowed real-CAD alias group; '
            'both artifact labels intentionally resolve to that same file and must pass the same validator.'
        ),
        'evidence_files': [
            evidence_entry('engineering_h2_production_blocker_closure_manifest_report', closure_path),
            evidence_entry('engineering_h2_external_artifact_drop_validator_report', drop_path),
            evidence_entry('engineering_h2_external_evidence_acceptance_worksheet_report', worksheet_path),
            evidence_entry('engineering_h2_external_artifact_ingestion_plan_report', ingestion_path),
        ],
        'limitations': [
            'This report audits external artifact target/drop path aliasing only.',
            'It does not supply external CAD, plume-reference, or calibrated fire data and cannot clear production blockers.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'report must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(int(summary.get('domain_count', 0)) == 3, 'domain count mismatch')
    require(int(summary.get('artifact_row_count', 0)) == 14, 'artifact row count mismatch')
    require(int(summary.get('alias_group_count', 0)) == 1, 'alias group count mismatch')
    require(int(summary.get('observed_allowed_alias_group_count', 0)) == 1, 'allowed alias group not observed')
    require(int(summary.get('duplicate_target_group_count', 0)) == 1, 'duplicate target group count mismatch')
    require(int(summary.get('duplicate_drop_group_count', 0)) == 1, 'duplicate drop group count mismatch')
    require(int(summary.get('unexpected_duplicate_target_group_count', -1)) == 0, 'unexpected target aliases remain')
    require(int(summary.get('unexpected_duplicate_drop_group_count', -1)) == 0, 'unexpected drop aliases remain')
    require(int(summary.get('worksheet_target_mismatch_count', -1)) == 0, 'worksheet target mismatches remain')
    require(int(summary.get('worksheet_drop_mismatch_count', -1)) == 0, 'worksheet drop mismatches remain')
    allowed = data.get('allowed_alias_groups')
    require(isinstance(allowed, list) and len(allowed) == 1, 'allowed_alias_groups mismatch')
    require(allowed[0].get('canonical_artifact') == 'real_cad_cleanup_quality_record.csv', 'canonical alias mismatch')
    rows = data.get('artifact_mapping_rows')
    require(isinstance(rows, list) and len(rows) == 14, 'artifact_mapping_rows mismatch')
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
        '# Engineering H2 External Artifact Mapping Alias Report',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Allowed Alias Groups', '']
    for item in report['allowed_alias_groups']:
        lines.append(
            f"- `{item['alias_group_id']}`: `{item['domain']}` "
            f"`{', '.join(item['artifacts'])}` -> `{item['target_path']}`"
        )
    lines += ['', '## Duplicate Target Groups', '']
    for item in report['target_path_duplicate_groups']:
        lines.append(f"- `{item['domain']}` `{item['target_path']}` artifacts=`{', '.join(item['artifacts'])}`")
    lines += ['', '## Duplicate Drop Groups', '']
    for item in report['drop_path_duplicate_groups']:
        lines.append(f"- `{item['domain']}` `{item['drop_path']}` artifacts=`{', '.join(item['artifacts'])}`")
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
    parser.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_CLOSURE_MANIFEST))
    parser.add_argument('--external-artifact-drop-validator-report', default=str(DEFAULT_DROP_VALIDATOR))
    parser.add_argument('--external-evidence-acceptance-worksheet-report', default=str(DEFAULT_ACCEPTANCE_WORKSHEET))
    parser.add_argument('--external-artifact-ingestion-plan-report', default=str(DEFAULT_INGESTION_PLAN))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_artifact_mapping_alias VERIFY-PASS '
                f"json={args.verify_json} aliases={summary['alias_group_count']} "
                f"unexpected_targets={summary['unexpected_duplicate_target_group_count']}"
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
            'engineering_h2_external_artifact_mapping_alias PASS '
            f"json={out_json} md={out_md} aliases={report['summary']['alias_group_count']} "
            f"unexpected_targets={report['summary']['unexpected_duplicate_target_group_count']}"
        )
        return 0
    except MappingAliasError as exc:
        print(f'engineering_h2_external_artifact_mapping_alias FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
