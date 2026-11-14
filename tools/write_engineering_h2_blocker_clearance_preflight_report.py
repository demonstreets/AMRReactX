#!/usr/bin/env python3
"""Write/verify the engineering H2 production blocker-clearance preflight report."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_READY = 'PASS-H2-BLOCKER-CLEARANCE-PREFLIGHT'
STATUS_NOT_READY = 'NOT_READY-H2-BLOCKER-CLEARANCE-PREFLIGHT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_blocker_clearance_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_blocker_clearance_preflight_report.md'
DEFAULT_SCORECARD = Path(
    'docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json'
)
DEFAULT_REAL_CAD = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
    'real_cad_cleanup_package_report.json'
)
DEFAULT_FIRE = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_package_20260723/'
    'fire_calibration_package_report.json'
)
DEFAULT_EXTERNAL_PLUME = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_readiness_20260723/'
    'external_plume_benchmark_readiness_report.json'
)

BLOCKER_TO_REPORT = {
    'reference_agreement_is_threshold_only_not_external_plume_shape_dataset': {
        'domain': 'external_plume_shape_reference',
        'path_attr': 'external_plume_readiness_report',
        'clear_key': 'clears_reference_data_blocker',
        'ready_status': 'PASS-EXTERNAL-PLUME-BENCHMARK',
        'not_ready_status': 'NOT_READY-EXTERNAL-PLUME-BENCHMARK',
    },
    'geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup': {
        'domain': 'real_cad_cleanup',
        'path_attr': 'real_cad_cleanup_package_report',
        'clear_key': 'clears_real_cad_cleanup_blocker',
        'ready_status': 'PASS-H2-REAL-CAD-CLEANUP-PACKAGE',
        'not_ready_status': 'NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE',
    },
    'fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure': {
        'domain': 'calibrated_fire_radiation_overpressure',
        'path_attr': 'fire_calibration_package_report',
        'clear_key': 'clears_fire_consequence_blocker',
        'ready_status': 'PASS-H2-FIRE-CALIBRATION-PACKAGE',
        'not_ready_status': 'NOT_READY-H2-FIRE-CALIBRATION-PACKAGE',
    },
}


class BlockerPreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BlockerPreflightError(message)


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
        raise BlockerPreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise BlockerPreflightError(f'invalid JSON in {path}: {exc}') from exc
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


def failed_quality_gates(report: dict[str, Any]) -> list[str]:
    matrix = report.get('quality_gate_matrix')
    if not isinstance(matrix, list):
        return ['quality_gate_matrix_missing']
    failed: list[str] = []
    for item in matrix:
        if isinstance(item, dict) and item.get('status') != 'PASS':
            failed.append(str(item.get('name', 'unnamed_gate')))
    return failed


def blocker_record(
    blocker: str,
    report: dict[str, Any],
    report_path: Path,
    mapping: dict[str, str],
    scorecard_current_blocker: bool,
) -> dict[str, Any]:
    gaps = report.get('blocking_gaps')
    if not isinstance(gaps, list):
        gaps = ['report_blocking_gaps_missing']
    failed = failed_quality_gates(report)
    clears = report.get(mapping['clear_key']) is True and not failed and report.get('status') == mapping['ready_status']
    return {
        'blocker': blocker,
        'domain': mapping['domain'],
        'status': 'CLEARED' if clears else 'NOT_READY',
        'scorecard_current_blocker': scorecard_current_blocker,
        'gate_report': str(report_path),
        'gate_report_status': report.get('status'),
        'clears_blocker': clears,
        'clear_key': mapping['clear_key'],
        'failed_quality_gates': failed,
        'blocking_gaps': gaps,
        'required_next_artifacts': report.get('next_required_artifacts', []),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    scorecard_path = Path(args.scorecard)
    real_cad_path = Path(args.real_cad_cleanup_package_report)
    fire_path = Path(args.fire_calibration_package_report)
    plume_path = Path(args.external_plume_readiness_report)
    scorecard = load_json(scorecard_path)
    reports = {
        'real_cad_cleanup_package_report': (load_json(real_cad_path), real_cad_path),
        'fire_calibration_package_report': (load_json(fire_path), fire_path),
        'external_plume_readiness_report': (load_json(plume_path), plume_path),
    }
    blockers = scorecard.get('blocking_gaps')
    require(isinstance(blockers, list), 'scorecard blocking_gaps missing')
    blocker_set = set(map(str, blockers))
    records = []
    uncovered = [str(blocker) for blocker in blockers if str(blocker) not in BLOCKER_TO_REPORT]
    for blocker, mapping in BLOCKER_TO_REPORT.items():
        report, report_path = reports[mapping['path_attr']]
        records.append(blocker_record(blocker, report, report_path, mapping, blocker in blocker_set))
    missing_expected: list[str] = []
    cleared_records = [item for item in records if item['clears_blocker'] and not item['scorecard_current_blocker']]
    remaining_records = [
        item for item in records
        if item['scorecard_current_blocker'] or not item['clears_blocker']
    ]
    all_scorecard_clear = scorecard.get('status') == 'PRODUCTION_READY' and not blockers
    ready = all_scorecard_clear and not uncovered and not missing_expected and not remaining_records
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 Production Blocker Clearance Preflight',
        'scorecard': str(scorecard_path),
        'scorecard_status': scorecard.get('status'),
        'scorecard_blocking_gaps': blockers,
        'scorecard_scores': scorecard.get('scores', {}),
        'blocker_records': records,
        'uncovered_scorecard_blockers': uncovered,
        'expected_blockers_not_currently_in_scorecard': missing_expected,
        'cleared_blocker_count': len(cleared_records),
        'remaining_blocker_count': len(remaining_records) + len(uncovered),
        'ready_for_production_scorecard_clearance': ready,
        'evidence_files': [
            evidence_entry('engineering_production_scorecard', scorecard_path),
            evidence_entry('real_cad_cleanup_package_report', real_cad_path),
            evidence_entry('fire_calibration_package_report', fire_path),
            evidence_entry('external_plume_readiness_report', plume_path),
        ],
        'limitations': [
            'This preflight report coordinates blocker-clearance evidence; it does not run CFD and does not clear a blocker by itself.',
            'A blocker is only considered cleared when its domain report reaches its PASS status and the production scorecard removes that blocker.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('scorecard_status') in {'NOT_PRODUCTION_READY', 'PRODUCTION_READY'}, 'invalid scorecard status')
    blockers = data.get('scorecard_blocking_gaps')
    require(isinstance(blockers, list), 'scorecard_blocking_gaps missing')
    records = data.get('blocker_records')
    require(isinstance(records, list), 'blocker_records missing')
    uncovered = data.get('uncovered_scorecard_blockers')
    require(isinstance(uncovered, list), 'uncovered_scorecard_blockers missing')
    for item in records:
        require(isinstance(item, dict), 'blocker record is not an object')
        require(str(item.get('blocker', '')) in BLOCKER_TO_REPORT, 'unknown mapped blocker')
        require(item.get('status') in {'CLEARED', 'NOT_READY'}, 'invalid blocker record status')
        require(isinstance(item.get('scorecard_current_blocker'), bool), 'scorecard_current_blocker missing')
        require(isinstance(item.get('failed_quality_gates'), list), 'failed_quality_gates missing')
        if item.get('status') == 'CLEARED':
            require(item.get('clears_blocker') is True, 'CLEARED record does not clear blocker')
            require(not item.get('failed_quality_gates'), 'CLEARED record has failed quality gates')
        else:
            require(item.get('clears_blocker') is False, 'NOT_READY record cannot clear blocker')
    if data.get('status') == STATUS_READY:
        require(data.get('scorecard_status') == 'PRODUCTION_READY', 'READY preflight requires production-ready scorecard')
        require(not blockers, 'READY preflight has scorecard blockers')
        require(not uncovered, 'READY preflight has uncovered blockers')
        require(data.get('ready_for_production_scorecard_clearance') is True, 'READY preflight not marked ready')
    else:
        require(data.get('ready_for_production_scorecard_clearance') is False, 'NOT_READY preflight cannot be ready')
        require(bool(blockers) or bool(uncovered), 'NOT_READY preflight must have blockers or uncovered gaps')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            p = Path(str(item.get('path', '')))
            require(p.is_file(), f'missing evidence file: {p}')
            require(sha256_file(p) == item.get('sha256'), f'evidence sha256 mismatch: {p}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Production Blocker Clearance Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Scorecard status: `{report['scorecard_status']}`",
        f"Ready for production scorecard clearance: `{report['ready_for_production_scorecard_clearance']}`",
        '',
        '## Blocker Records',
        '',
        '| Blocker | Domain | Status | Failed quality gates | Blocking gaps |',
        '| --- | --- | --- | --- | --- |',
    ]
    for item in report['blocker_records']:
        failed = '; '.join(item['failed_quality_gates']) or 'none'
        gaps = '; '.join(str(gap) for gap in item['blocking_gaps']) or 'none'
        lines.append(
            f"| `{item['blocker']}` | `{item['domain']}` | `{item['status']}`"
            f" scorecard_current={item['scorecard_current_blocker']} | {failed} | {gaps} |"
        )
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scorecard', default=str(DEFAULT_SCORECARD))
    parser.add_argument('--real-cad-cleanup-package-report', default=str(DEFAULT_REAL_CAD))
    parser.add_argument('--fire-calibration-package-report', default=str(DEFAULT_FIRE))
    parser.add_argument('--external-plume-readiness-report', default=str(DEFAULT_EXTERNAL_PLUME))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_blocker_clearance_preflight VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"remaining={report['remaining_blocker_count']}"
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
            'engineering_h2_blocker_clearance_preflight PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"remaining={report['remaining_blocker_count']}"
        )
        return 0
    except BlockerPreflightError as exc:
        print(f'engineering_h2_blocker_clearance_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
