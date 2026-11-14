#!/usr/bin/env python3
"""Write/verify the engineering H2 synthetic self-test isolation guard report."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-SYNTHETIC-SELFTEST-ISOLATION-GUARD'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_synthetic_selftest_isolation_guard_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_synthetic_selftest_isolation_guard_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_synthetic_selftest_isolation_guard_report.md'
DEFAULT_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/'
    'h2_external_artifact_gate_selftest_report.json'
)

DEFAULT_SCANNED_REPORTS = [
    Path('docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json'),
    Path(
        'docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/'
        'h2_blocker_clearance_preflight_report.json'
    ),
    Path(
        'docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724/'
        'h2_production_blocker_data_room_report.json'
    ),
    Path(
        'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
        'h2_production_blocker_closure_manifest_report.json'
    ),
    Path(
        'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
        'h2_external_artifact_drop_validator_report.json'
    ),
    Path(
        'docs/codex_audit/evidence/engineering_h2_external_artifact_ingestion_plan_20260724/'
        'h2_external_artifact_ingestion_plan.json'
    ),
    Path(
        'docs/codex_audit/evidence/engineering_h2_external_artifact_controlled_copy_20260724/'
        'h2_external_artifact_controlled_copy_report.json'
    ),
    Path(
        'docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724/'
        'h2_external_evidence_operations_dashboard.json'
    ),
]


class IsolationGuardError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IsolationGuardError(message)


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
        raise IsolationGuardError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise IsolationGuardError(f'invalid JSON evidence {path}: {exc}') from exc
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


def summary(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get('summary', {})
    return value if isinstance(value, dict) else {}


def current_status(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get('current_status', {})
    return value if isinstance(value, dict) else {}


def fragments_from_selftest(selftest: dict[str, Any]) -> list[str]:
    fragments = [
        'synthetic_selftest',
        'synthetic_fixture',
        'synthetic-selftest',
        str(selftest.get('synthetic_drop_root', '')),
        str(selftest.get('synthetic_controlled_target_root', '')),
    ]
    reports = selftest.get('synthetic_reports', {})
    if isinstance(reports, dict):
        fragments.extend(str(item) for item in reports.values())
    return sorted({item.replace('\\', '/') for item in fragments if item})


def scan_report(path: Path, forbidden_fragments: list[str]) -> dict[str, Any]:
    text = path.read_text(encoding='utf-8', errors='replace').replace('\\', '/')
    hits = [item for item in forbidden_fragments if item in text]
    return {
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
        'forbidden_hit_count': len(hits),
        'forbidden_hits': hits,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    selftest_path = Path(args.external_artifact_gate_selftest_report)
    selftest = load_json(selftest_path)
    scanned_paths = [Path(item) for item in args.scanned_report]
    for path in scanned_paths:
        require(path.is_file(), f'missing scanned production report: {path}')
    forbidden_fragments = fragments_from_selftest(selftest)
    scan_records = [scan_report(path, forbidden_fragments) for path in scanned_paths]

    scorecard = load_json(scanned_paths[0])
    preflight = load_json(scanned_paths[1])
    data_room = load_json(scanned_paths[2])
    drop = load_json(scanned_paths[4])
    ingestion = load_json(scanned_paths[5])
    controlled_copy = load_json(scanned_paths[6])
    dashboard = load_json(scanned_paths[7])

    score_summary = summary(scorecard)
    dashboard_status = current_status(dashboard)
    forbidden_hits = sum(int(item['forbidden_hit_count']) for item in scan_records)
    remaining_blockers = int(preflight.get('remaining_blocker_count', 0))
    production_status = scorecard.get('status')
    not_ready_with_blockers = production_status == 'NOT_PRODUCTION_READY' and remaining_blockers >= 1
    synthetic_not_in_real_drop = int(drop.get('valid_artifact_count', -1)) != 14 or drop.get('drop_root') != selftest.get('synthetic_drop_root')
    real_controlled_copy_not_applied = controlled_copy.get('applied_copy_actions') is False
    quality_gate_matrix = [
        {
            'name': 'selftest_passes_but_is_synthetic_only',
            'status': 'PASS'
            if selftest.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-GATE-SELFTEST'
            and selftest.get('synthetic_selftest_only') is True
            and selftest.get('does_not_clear_production_blockers') is True
            else 'MISSING',
            'evidence': str(selftest_path),
            'gap': '',
        },
        {
            'name': 'production_reports_do_not_reference_selftest_artifacts',
            'status': 'PASS' if forbidden_hits == 0 else 'MISSING',
            'evidence': f'scanned_reports={len(scan_records)} forbidden_hits={forbidden_hits}',
            'gap': '; '.join(hit for record in scan_records for hit in record['forbidden_hits']),
        },
        {
            'name': 'scorecard_not_ready_while_real_blockers_remain',
            'status': 'PASS' if remaining_blockers == 0 or not_ready_with_blockers else 'MISSING',
            'evidence': f'scorecard={production_status} remaining_blockers={remaining_blockers}',
            'gap': '',
        },
        {
            'name': 'real_drop_is_separate_from_synthetic_fixture',
            'status': 'PASS' if synthetic_not_in_real_drop else 'MISSING',
            'evidence': f"real_drop_root={drop.get('drop_root')} synthetic_drop_root={selftest.get('synthetic_drop_root')}",
            'gap': '',
        },
        {
            'name': 'real_controlled_copy_has_not_been_satisfied_by_selftest',
            'status': 'PASS' if real_controlled_copy_not_applied else 'MISSING',
            'evidence': f"applied_copy_actions={controlled_copy.get('applied_copy_actions')}",
            'gap': '',
        },
        {
            'name': 'dashboard_still_reports_real_missing_artifacts',
            'status': 'PASS'
            if remaining_blockers == 0
            or int(dashboard_status.get('missing_external_artifact_count', 0)) >= 1
            else 'MISSING',
            'evidence': f"dashboard_missing={dashboard_status.get('missing_external_artifact_count')}",
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Synthetic Self-Test Isolation Guard',
        'external_artifact_gate_selftest_report': str(selftest_path),
        'synthetic_selftest_only': True,
        'does_not_clear_production_blockers': True,
        'forbidden_fragments': forbidden_fragments,
        'scanned_report_count': len(scan_records),
        'forbidden_hit_count': forbidden_hits,
        'current_status': {
            'scorecard_status': production_status,
            'functional_coverage_percent': score_summary.get('functional_percent')
            or scorecard.get('functional_coverage_percent'),
            'production_credibility_percent': score_summary.get('production_credibility_percent')
            or scorecard.get('production_credibility_percent'),
            'remaining_blocker_count': remaining_blockers,
            'data_room_missing_artifact_count': data_room.get('missing_artifact_count'),
            'real_drop_status': drop.get('status'),
            'real_drop_valid_artifact_count': drop.get('valid_artifact_count'),
            'real_ingestion_status': ingestion.get('status'),
            'real_ingestion_ready_copy_action_count': ingestion.get('ready_copy_action_count'),
            'real_controlled_copy_status': controlled_copy.get('status'),
            'real_controlled_copy_copied_file_count': controlled_copy.get('copied_file_count'),
            'dashboard_missing_external_artifact_count': dashboard_status.get('missing_external_artifact_count'),
        },
        'scan_records': scan_records,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('engineering_h2_external_artifact_gate_selftest_report', selftest_path),
            *[
                evidence_entry(f'scanned_production_report_{idx:02d}', path)
                for idx, path in enumerate(scanned_paths, start=1)
            ],
        ],
        'limitations': [
            'This guard checks evidence wiring and isolation; it does not validate physical fidelity.',
            'Synthetic self-test evidence is allowed only as a verifier self-test and must not appear in production input reports.',
            'When real external evidence is supplied, this guard should continue to pass as long as production reports do not reference the synthetic self-test fixture.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('synthetic_selftest_only') is True, 'guard must mark self-test as synthetic')
    require(data.get('does_not_clear_production_blockers') is True, 'guard must not clear blockers')
    require(int(data.get('scanned_report_count', 0)) >= 8, 'too few production reports scanned')
    require(int(data.get('forbidden_hit_count', -1)) == 0, 'synthetic self-test fragments found in production reports')
    status = data.get('current_status')
    require(isinstance(status, dict), 'current_status missing')
    if int(status.get('remaining_blocker_count', 0)) >= 1:
        require(status.get('scorecard_status') == 'NOT_PRODUCTION_READY', 'scorecard ready while blockers remain')
        require(int(status.get('dashboard_missing_external_artifact_count', 0)) >= 1, 'dashboard missing artifacts not retained')
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
        '# Engineering H2 Synthetic Self-Test Isolation Guard',
        '',
        f"Status: `{report['status']}`",
        f"Scanned reports: `{report['scanned_report_count']}`",
        f"Forbidden hits: `{report['forbidden_hit_count']}`",
        '',
        '## Current Status',
        '',
    ]
    for key, value in report['current_status'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Quality Gates', '']
    for item in report['quality_gate_matrix']:
        lines.append(f"- `{item['name']}`: `{item['status']}`")
    lines += ['', '## Scanned Reports', '']
    for item in report['scan_records']:
        lines.append(f"- `{item['path']}` hits=`{item['forbidden_hit_count']}`")
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
    parser.add_argument('--external-artifact-gate-selftest-report', default=str(DEFAULT_SELFTEST))
    parser.add_argument('--scanned-report', action='append', default=[str(item) for item in DEFAULT_SCANNED_REPORTS])
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_synthetic_selftest_isolation_guard VERIFY-PASS '
                f"json={args.verify_json} scanned={report['scanned_report_count']} hits={report['forbidden_hit_count']}"
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
            'engineering_h2_synthetic_selftest_isolation_guard PASS '
            f"json={out_json} md={out_md} scanned={report['scanned_report_count']} hits={report['forbidden_hit_count']}"
        )
        return 0
    except IsolationGuardError as exc:
        print(f'engineering_h2_synthetic_selftest_isolation_guard FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
