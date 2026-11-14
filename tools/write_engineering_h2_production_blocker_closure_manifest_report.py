#!/usr/bin/env python3
"""Write/verify the engineering H2 production blocker closure manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_production_blocker_closure_manifest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_production_blocker_closure_manifest_report.md'
DEFAULT_DATA_ROOM = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724/'
    'h2_production_blocker_data_room_report.json'
)

TARGET_PATHS = {
    'real_cad_cleanup': {
        'real_cad_cleanup_manifest.json': (
            'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
            'package/real_cad_cleanup_manifest.json'
        ),
        'source_cad/*': (
            'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
            'package/source_cad/'
        ),
        'cleaned_geometry/*': (
            'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
            'package/cleaned_geometry/'
        ),
        'cleanup_quality_records': (
            'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
            'package/real_cad_cleanup_quality_record.csv'
        ),
        'real_cad_data_room_index.csv': (
            'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
            'package/real_cad_data_room_index.csv'
        ),
        'real_cad_cleanup_quality_record.csv': (
            'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
            'package/real_cad_cleanup_quality_record.csv'
        ),
    },
    'external_plume_shape_reference': {
        'dataset_metadata.json': (
            'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
            'dataset/dataset_metadata.json'
        ),
        'sensor_coordinates.csv': (
            'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
            'dataset/sensor_coordinates.csv'
        ),
        'baffle_geometry.csv': (
            'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
            'dataset/baffle_geometry.csv'
        ),
        'experimental_timeseries.csv': (
            'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
            'dataset/experimental_timeseries.csv'
        ),
    },
    'fire_consequence_calibration': {
        'calibration_metadata.json': (
            'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
            'dataset/calibration_metadata.json'
        ),
        'radiation_metrics.csv': (
            'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
            'dataset/radiation_metrics.csv'
        ),
        'overpressure_metrics.csv': (
            'docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/'
            'dataset/overpressure_metrics.csv'
        ),
        'calibrated_fire_consequence_report': (
            'docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/'
            'fire_consequence_metrics_report.json'
        ),
    },
}

COMMAND_SEQUENCES = {
    'real_cad_cleanup': [
        'python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py',
        'python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py',
        'python3 tools/write_engineering_production_scorecard.py',
        'python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py',
    ],
    'external_plume_shape_reference': [
        'python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py',
        'python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py',
        'python3 tools/write_engineering_h2_reference_agreement_report.py --external-plume-dataset-json <generated_external_plume_dataset_json>',
        'python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py',
        'python3 tools/write_engineering_production_scorecard.py',
        'python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py',
    ],
    'fire_consequence_calibration': [
        'python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py',
        'python3 tools/write_engineering_h2_fire_calibration_package_report.py',
        'python3 tools/write_engineering_h2_fire_calibration_dataset_report.py',
        'python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --calibration-dataset-json <generated_fire_calibration_dataset_json>',
        'python3 tools/write_engineering_production_scorecard.py',
        'python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py',
    ],
}

FINAL_COMMANDS = [
    'python3 tools/write_engineering_h2_production_blocker_data_room_report.py',
    'python3 tools/write_engineering_h2_production_blocker_closure_manifest_report.py',
    'python3 tools/write_engineering_h2_production_handoff_report.py',
    'python3 tools/write_engineering_h2_master_plan_traceability_report.py',
    'bash tools/verify_engineering_h2_production_evidence.sh',
]


class ClosureManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureManifestError(message)


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
        raise ClosureManifestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ClosureManifestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def artifact_record(domain: str, item: dict[str, Any]) -> dict[str, Any]:
    artifact = str(item.get('artifact', '')).strip()
    target = TARGET_PATHS.get(domain, {}).get(artifact)
    require(artifact, f'{domain} missing artifact name')
    require(target, f'{domain} artifact has no target path mapping: {artifact}')
    return {
        'artifact': artifact,
        'target_path': target,
        'required_action': item.get('required_action', ''),
        'closure_state': 'WAITING_FOR_EXTERNAL_DATA',
    }


def domain_closure_record(record: dict[str, Any]) -> dict[str, Any]:
    domain = str(record.get('domain', ''))
    require(domain in TARGET_PATHS, f'unknown domain: {domain}')
    missing = record.get('missing_artifacts')
    require(isinstance(missing, list), f'{domain} missing_artifacts is not a list')
    artifacts = [artifact_record(domain, item) for item in missing if isinstance(item, dict)]
    commands = COMMAND_SEQUENCES[domain]
    return {
        'domain': domain,
        'blocker': record.get('blocker'),
        'missing_artifact_count': len(artifacts),
        'artifact_records': artifacts,
        'domain_command_sequence': commands,
        'ready_for_execution': len(artifacts) == 0,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    data_room_path = Path(args.production_blocker_data_room_report)
    data_room = load_json(data_room_path)
    records = data_room.get('domain_records')
    require(isinstance(records, list) and records, 'data-room domain_records missing')
    closure_records = [domain_closure_record(item) for item in records if isinstance(item, dict)]
    total_missing = sum(int(item['missing_artifact_count']) for item in closure_records)
    quality_gate_matrix = [
        {
            'name': 'data_room_attached',
            'status': 'PASS' if data_room.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM' else 'MISSING',
            'evidence': str(data_room_path),
            'gap': '' if data_room.get('status') == 'PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM' else 'data-room report must PASS',
        },
        {
            'name': 'all_missing_artifacts_have_target_paths',
            'status': 'PASS',
            'evidence': f'{total_missing} artifact target mapping(s)',
            'gap': '',
        },
        {
            'name': 'all_domains_have_command_sequences',
            'status': 'PASS' if all(item['domain_command_sequence'] for item in closure_records) else 'MISSING',
            'evidence': 'domain closure commands are defined',
            'gap': '',
        },
        {
            'name': 'final_verifier_command_defined',
            'status': 'PASS' if FINAL_COMMANDS[-1] == 'bash tools/verify_engineering_h2_production_evidence.sh' else 'MISSING',
            'evidence': FINAL_COMMANDS[-1],
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Production Blocker Closure Manifest',
        'production_blocker_data_room_report': str(data_room_path),
        'ready_for_production_scorecard_clearance': data_room.get('ready_for_production_scorecard_clearance') is True,
        'remaining_blocker_count': data_room.get('remaining_blocker_count'),
        'total_missing_artifact_count': total_missing,
        'domain_closure_records': closure_records,
        'final_rebuild_command_sequence': FINAL_COMMANDS,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [evidence_entry('production_blocker_data_room_report', data_room_path)],
        'limitations': [
            'This manifest defines closure targets and command order; it does not provide missing external CAD, plume, or fire calibration data.',
            'A blocker is still open until its domain report, production scorecard, blocker preflight, and final verifier all pass.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    records = data.get('domain_closure_records')
    require(isinstance(records, list) and len(records) == 3, 'domain_closure_records must contain three domains')
    total_missing = int(data.get('total_missing_artifact_count', -1))
    require(total_missing >= 0, 'total_missing_artifact_count invalid')
    counted = 0
    for record in records:
        require(isinstance(record, dict), 'domain closure record is not an object')
        domain = str(record.get('domain', ''))
        require(domain in TARGET_PATHS, f'unknown closure domain: {domain}')
        artifacts = record.get('artifact_records')
        require(isinstance(artifacts, list), f'{domain} artifact_records missing')
        counted += len(artifacts)
        for item in artifacts:
            require(isinstance(item, dict), f'{domain} artifact record is not an object')
            require(str(item.get('target_path', '')).strip(), f'{domain} artifact missing target path')
            require(item.get('closure_state') == 'WAITING_FOR_EXTERNAL_DATA', f'{domain} invalid closure_state')
        commands = record.get('domain_command_sequence')
        require(isinstance(commands, list) and commands, f'{domain} command sequence missing')
    require(counted == total_missing, 'artifact count mismatch')
    final_commands = data.get('final_rebuild_command_sequence')
    require(isinstance(final_commands, list) and final_commands, 'final rebuild command sequence missing')
    require(final_commands[-1] == 'bash tools/verify_engineering_h2_production_evidence.sh', 'final verifier command mismatch')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'closure manifest quality gate failed')
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
        '# Engineering H2 Production Blocker Closure Manifest',
        '',
        f"Status: `{report['status']}`",
        f"Remaining blockers: `{report['remaining_blocker_count']}`",
        f"Total missing artifacts: `{report['total_missing_artifact_count']}`",
        '',
        '## Domain Closure Records',
        '',
    ]
    for record in report['domain_closure_records']:
        lines.append(f"### {record['domain']}")
        lines.append(f"- Blocker: `{record['blocker']}`")
        lines.append(f"- Missing artifact count: `{record['missing_artifact_count']}`")
        for artifact in record['artifact_records']:
            lines.append(f"- `{artifact['artifact']}` -> `{artifact['target_path']}`")
        lines.append('- Commands:')
        for command in record['domain_command_sequence']:
            lines.append(f"  - `{command}`")
        lines.append('')
    lines += ['## Final Rebuild Commands', '']
    for command in report['final_rebuild_command_sequence']:
        lines.append(f"- `{command}`")
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
    parser.add_argument('--production-blocker-data-room-report', default=str(DEFAULT_DATA_ROOM))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_production_blocker_closure_manifest VERIFY-PASS '
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
            'engineering_h2_production_blocker_closure_manifest PASS '
            f"json={out_json} md={out_md} missing_artifacts={report['total_missing_artifact_count']} "
            f"remaining={report['remaining_blocker_count']}"
        )
        return 0
    except ClosureManifestError as exc:
        print(f'engineering_h2_production_blocker_closure_manifest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
