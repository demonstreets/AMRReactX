#!/usr/bin/env python3
"""Write/verify the engineering H2 production blocker data-room report."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM'

DEFAULT_OUTPUT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / 'h2_production_blocker_data_room_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / 'h2_production_blocker_data_room_report.md'
DEFAULT_REAL_CAD_INTAKE = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/'
    'real_cad_intake_preflight_report.json'
)
DEFAULT_SBEPV5_DIGITIZATION = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724/'
    'sbepv5_d27_digitization_preflight_report.json'
)
DEFAULT_FIRE_DIGITIZATION = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/'
    'fire_calibration_digitization_preflight_report.json'
)
DEFAULT_BLOCKER_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/'
    'h2_blocker_clearance_preflight_report.json'
)

DOMAIN_CONFIG = {
    'real_cad_cleanup': {
        'blocker': 'geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup',
        'expected_status': 'PASS-H2-REAL-CAD-INTAKE-PREFLIGHT',
        'ready_key': 'cleanup_package_clears_blocker',
    },
    'external_plume_shape_reference': {
        'blocker': 'reference_agreement_is_threshold_only_not_external_plume_shape_dataset',
        'expected_status': 'PASS-SBEPV5-D27-DIGITIZATION-PREFLIGHT',
        'ready_key': 'ready_for_dataset_ingestion',
    },
    'fire_consequence_calibration': {
        'blocker': 'fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure',
        'expected_status': 'PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT',
        'ready_key': 'ready_for_dataset_ingestion',
    },
}


class DataRoomError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DataRoomError(message)


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
        raise DataRoomError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise DataRoomError(f'invalid JSON evidence {path}: {exc}') from exc
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


def domain_record(domain: str, report: dict[str, Any], path: Path) -> dict[str, Any]:
    config = DOMAIN_CONFIG[domain]
    summary = report.get('summary') if isinstance(report.get('summary'), dict) else {}
    missing = report.get('missing_artifacts') if isinstance(report.get('missing_artifacts'), list) else []
    preflight_passed = report.get('status') == config['expected_status']
    ready = summary.get(config['ready_key']) is True or report.get(config['ready_key']) is True
    return {
        'domain': domain,
        'blocker': config['blocker'],
        'preflight_report': str(path),
        'preflight_status': report.get('status'),
        'preflight_passed': preflight_passed,
        'ready_for_blocker_clearance': ready,
        'missing_artifact_count': len(missing),
        'missing_artifacts': missing,
        'summary': summary,
    }


def gate_row(name: str, passed: bool, evidence: str, gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else '',
        'gap': '' if passed else gap,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    real_path = Path(args.real_cad_intake_preflight_report)
    plume_path = Path(args.sbepv5_digitization_preflight_report)
    fire_path = Path(args.fire_calibration_digitization_preflight_report)
    blocker_path = Path(args.blocker_clearance_preflight_report)
    blocker = load_json(blocker_path)
    records = [
        domain_record('real_cad_cleanup', load_json(real_path), real_path),
        domain_record('external_plume_shape_reference', load_json(plume_path), plume_path),
        domain_record('fire_consequence_calibration', load_json(fire_path), fire_path),
    ]
    total_missing = sum(int(item['missing_artifact_count']) for item in records)
    ready_domains = [item for item in records if item['ready_for_blocker_clearance']]
    remaining_count = int(blocker.get('remaining_blocker_count', -1))
    ready_for_clearance = remaining_count == 0 and len(ready_domains) == len(records)
    quality_gate_matrix = [
        gate_row(
            'all_domain_preflights_pass',
            all(item['preflight_passed'] for item in records),
            'real-CAD, external plume, and fire calibration preflight reports pass',
            'Each production blocker must have a passing intake/digitization preflight report.',
        ),
        gate_row(
            'blocker_preflight_attached',
            blocker.get('status') in {
                'PASS-H2-BLOCKER-CLEARANCE-PREFLIGHT',
                'NOT_READY-H2-BLOCKER-CLEARANCE-PREFLIGHT',
            },
            str(blocker_path),
            'Attach a valid blocker clearance preflight report.',
        ),
        gate_row(
            'missing_artifacts_retained_until_ready',
            ready_for_clearance or total_missing >= 3,
            f'total_missing_artifacts={total_missing}',
            'A not-ready data room must retain missing artifacts instead of claiming readiness.',
        ),
        gate_row(
            'scorecard_clearance_consistency',
            ready_for_clearance == bool(blocker.get('ready_for_production_scorecard_clearance')),
            'data-room readiness matches blocker preflight readiness',
            'Data-room readiness and blocker preflight readiness disagree.',
        ),
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Production Blocker Data Room',
        'ready_for_production_scorecard_clearance': ready_for_clearance,
        'remaining_blocker_count': remaining_count,
        'ready_domain_count': len(ready_domains),
        'domain_count': len(records),
        'total_missing_artifact_count': total_missing,
        'domain_records': records,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('real_cad_intake_preflight_report', real_path),
            evidence_entry('sbepv5_digitization_preflight_report', plume_path),
            evidence_entry('fire_calibration_digitization_preflight_report', fire_path),
            evidence_entry('blocker_clearance_preflight_report', blocker_path),
        ],
        'limitations': [
            'This report is a consolidated production data-room intake ledger; it does not supply missing external evidence.',
            'Production readiness still requires each domain report to pass its full ingestion/build/agreement path and the blocker preflight to clear.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    records = data.get('domain_records')
    require(isinstance(records, list) and len(records) == 3, 'domain_records must contain three production blockers')
    domains = {str(item.get('domain')) for item in records if isinstance(item, dict)}
    require(set(DOMAIN_CONFIG) == domains, 'domain_records do not match required production blockers')
    require(all(item.get('preflight_passed') is True for item in records if isinstance(item, dict)), 'domain preflight not passed')
    total_missing = int(data.get('total_missing_artifact_count', -1))
    require(total_missing >= 0, 'total_missing_artifact_count invalid')
    if data.get('ready_for_production_scorecard_clearance') is True:
        require(total_missing == 0, 'ready data room still has missing artifacts')
        require(int(data.get('remaining_blocker_count', -1)) == 0, 'ready data room still has blockers')
    else:
        require(total_missing >= 1, 'not-ready data room must retain missing artifacts')
        require(int(data.get('remaining_blocker_count', 0)) >= 1, 'not-ready data room must retain blockers')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
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
        '# Engineering H2 Production Blocker Data Room',
        '',
        f"Status: `{report['status']}`",
        f"Ready for production scorecard clearance: `{report['ready_for_production_scorecard_clearance']}`",
        f"Remaining blockers: `{report['remaining_blocker_count']}`",
        f"Total missing artifacts: `{report['total_missing_artifact_count']}`",
        '',
        '## Domains',
        '',
    ]
    for record in report['domain_records']:
        lines.append(f"### {record['domain']}")
        lines.append(f"- Blocker: `{record['blocker']}`")
        lines.append(f"- Preflight status: `{record['preflight_status']}`")
        lines.append(f"- Ready for blocker clearance: `{record['ready_for_blocker_clearance']}`")
        lines.append(f"- Missing artifact count: `{record['missing_artifact_count']}`")
        for item in record['missing_artifacts']:
            lines.append(f"  - `{item['artifact']}`: {item['required_action']}")
        lines.append('')
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['gap'] or 'none'} |")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
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
    parser.add_argument('--real-cad-intake-preflight-report', default=str(DEFAULT_REAL_CAD_INTAKE))
    parser.add_argument('--sbepv5-digitization-preflight-report', default=str(DEFAULT_SBEPV5_DIGITIZATION))
    parser.add_argument('--fire-calibration-digitization-preflight-report', default=str(DEFAULT_FIRE_DIGITIZATION))
    parser.add_argument('--blocker-clearance-preflight-report', default=str(DEFAULT_BLOCKER_PREFLIGHT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_production_blocker_data_room VERIFY-PASS '
                f"json={args.verify_json} missing_artifacts={report['total_missing_artifact_count']} "
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
            'engineering_h2_production_blocker_data_room PASS '
            f"json={out_json} md={out_md} missing_artifacts={report['total_missing_artifact_count']} "
            f"remaining={report['remaining_blocker_count']}"
        )
        return 0
    except DataRoomError as exc:
        print(f'engineering_h2_production_blocker_data_room FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
