#!/usr/bin/env python3
"""Write/verify the engineering H2 real-CAD intake preflight report."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from write_engineering_campaign_manifest import (
    CAD_FILE_EXTENSIONS,
    ManifestError,
    validate_real_cad_cleanup_manifest,
)

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-REAL-CAD-INTAKE-PREFLIGHT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724')
DEFAULT_PACKAGE_ROOT = Path('docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package')
DEFAULT_MANIFEST = DEFAULT_PACKAGE_ROOT / 'real_cad_cleanup_manifest.json'
DEFAULT_DATA_ROOM_INDEX = DEFAULT_PACKAGE_ROOT / 'real_cad_data_room_index.csv'
DEFAULT_CLEANUP_QUALITY_RECORD = DEFAULT_PACKAGE_ROOT / 'real_cad_cleanup_quality_record.csv'
DEFAULT_CLEANUP_PACKAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
    'real_cad_cleanup_package_report.json'
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'real_cad_intake_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'real_cad_intake_preflight_report.md'


class RealCadIntakePreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RealCadIntakePreflightError(message)


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
        raise RealCadIntakePreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RealCadIntakePreflightError(f'invalid JSON evidence {path}: {exc}') from exc
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


def gate_row(name: str, passed: bool, evidence: str | list[str], gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else [],
        'gap': '' if passed else gap,
    }


def write_intake_templates(package_root: Path) -> list[Path]:
    package_root.mkdir(parents=True, exist_ok=True)
    index_path = package_root / 'real_cad_data_room_index_template.csv'
    cleanup_path = package_root / 'real_cad_cleanup_quality_record_template.csv'
    index_rows = [
        ['file_role', 'label', 'relative_path', 'sha256', 'source_type', 'revision', 'owner_or_supplier', 'notes'],
        ['source_cad', 'tank_001', 'source_cad/tank_001.step', '<64 hex>', 'owner_operator_cad', '<rev>', '<owner>', 'controlled source geometry'],
        ['cleaned_geometry', 'tank_001', 'cleaned_geometry/tank_001.stl', '<64 hex>', 'derived_cleanup', '<rev>', '<owner>', 'simulation-ready geometry'],
    ]
    cleanup_rows = [
        [
            'label',
            'units_declared',
            'watertight_or_closed_surface',
            'nondegenerate_elements',
            'positive_volume_or_area',
            'bbox_min_m',
            'bbox_max_m',
            'tool_or_method',
            'reviewer',
        ],
        ['tank_001', 'true', 'true', 'true', 'true', '[0,0,0]', '[1,1,1]', '<mesh cleanup tool/version>', '<reviewer>'],
    ]
    index_path.write_text('\n'.join(','.join(row) for row in index_rows) + '\n', encoding='utf-8')
    cleanup_path.write_text('\n'.join(','.join(row) for row in cleanup_rows) + '\n', encoding='utf-8')
    return [index_path, cleanup_path]


def cad_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.rglob('*') if path.is_file() and path.suffix.lower() in CAD_FILE_EXTENSIONS)


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline='', encoding='utf-8') as fh:
            return [dict(row) for row in csv.DictReader(fh)]
    except OSError as exc:
        raise RealCadIntakePreflightError(f'failed reading CSV {path}: {exc}') from exc


def csv_has_columns(rows: list[dict[str, str]], columns: tuple[str, ...]) -> bool:
    if not rows:
        return False
    present = set(rows[0].keys())
    return all(column in present for column in columns)


def valid_sha256(value: str) -> bool:
    text = str(value).strip().lower()
    return len(text) == 64 and all(ch in '0123456789abcdef' for ch in text)


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == 'true'


def validate_data_room_index(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    rows = read_csv_dicts(path)
    required = ('file_role', 'label', 'relative_path', 'sha256', 'source_type', 'revision', 'owner_or_supplier')
    require(csv_has_columns(rows, required), f'{path} missing required columns: {required}')
    role_counts = {'source_cad': 0, 'cleaned_geometry': 0}
    labels_by_role = {'source_cad': set(), 'cleaned_geometry': set()}
    for idx, row in enumerate(rows, 1):
        role = str(row.get('file_role', '')).strip()
        label = str(row.get('label', '')).strip()
        rel = str(row.get('relative_path', '')).strip()
        require(role in role_counts, f'{path} row {idx} invalid file_role: {role}')
        require(label, f'{path} row {idx} missing label')
        require(rel, f'{path} row {idx} missing relative_path')
        require(valid_sha256(row.get('sha256', '')), f'{path} row {idx} invalid sha256')
        require(str(row.get('source_type', '')).strip(), f'{path} row {idx} missing source_type')
        require(str(row.get('revision', '')).strip(), f'{path} row {idx} missing revision')
        require(str(row.get('owner_or_supplier', '')).strip(), f'{path} row {idx} missing owner_or_supplier')
        role_counts[role] += 1
        labels_by_role[role].add(label)
    paired_labels = labels_by_role['source_cad'] & labels_by_role['cleaned_geometry']
    require(len(paired_labels) >= 3, f'{path} requires at least three labels with both source_cad and cleaned_geometry rows')
    return {
        'path': str(path),
        'sha256': sha256_file(path),
        'row_count': len(rows),
        'source_cad_rows': role_counts['source_cad'],
        'cleaned_geometry_rows': role_counts['cleaned_geometry'],
        'paired_label_count': len(paired_labels),
        'paired_labels': sorted(paired_labels),
    }


def validate_cleanup_quality_record(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    rows = read_csv_dicts(path)
    required = (
        'label',
        'units_declared',
        'watertight_or_closed_surface',
        'nondegenerate_elements',
        'positive_volume_or_area',
        'bbox_min_m',
        'bbox_max_m',
        'tool_or_method',
        'reviewer',
    )
    require(csv_has_columns(rows, required), f'{path} missing required columns: {required}')
    labels = set()
    for idx, row in enumerate(rows, 1):
        label = str(row.get('label', '')).strip()
        require(label, f'{path} row {idx} missing label')
        require(label not in labels, f'{path} duplicate label: {label}')
        labels.add(label)
        for key in ('units_declared', 'watertight_or_closed_surface', 'nondegenerate_elements', 'positive_volume_or_area'):
            require(parse_bool(row.get(key, '')), f'{path} row {idx} cleanup check must be true: {key}')
        require(str(row.get('bbox_min_m', '')).strip(), f'{path} row {idx} missing bbox_min_m')
        require(str(row.get('bbox_max_m', '')).strip(), f'{path} row {idx} missing bbox_max_m')
        require(str(row.get('tool_or_method', '')).strip(), f'{path} row {idx} missing tool_or_method')
        require(str(row.get('reviewer', '')).strip(), f'{path} row {idx} missing reviewer')
    require(len(labels) >= 3, f'{path} requires at least three cleanup quality records')
    return {
        'path': str(path),
        'sha256': sha256_file(path),
        'row_count': len(rows),
        'labels': sorted(labels),
    }


def build_missing_artifacts(
    manifest_present: bool,
    source_count: int,
    cleaned_count: int,
    validation: dict[str, Any] | None,
    data_room_index: dict[str, Any] | None,
    cleanup_quality_record: dict[str, Any] | None,
) -> list[dict[str, str]]:
    missing = []
    if not manifest_present:
        missing.append(
            {
                'artifact': 'real_cad_cleanup_manifest.json',
                'required_action': 'fill the package manifest from the template with controlled provenance and exact file hashes',
            }
        )
    if source_count < 3:
        missing.append(
            {
                'artifact': 'source_cad/*',
                'required_action': 'stage at least three real source CAD files for a tank/pipe large-layout campaign',
            }
        )
    if cleaned_count < 3:
        missing.append(
            {
                'artifact': 'cleaned_geometry/*',
                'required_action': 'stage at least three cleaned simulation geometries derived from the source CAD files',
            }
        )
    if not validation:
        missing.append(
            {
                'artifact': 'cleanup_quality_records',
                'required_action': 'record units, watertightness, degeneracy, positive volume/area, and meter-space bounding boxes per geometry',
            }
        )
    if not data_room_index:
        missing.append(
            {
                'artifact': 'real_cad_data_room_index.csv',
                'required_action': 'provide a controlled data-room index with source/cleaned file roles, labels, relative paths, hashes, source type, revision, and owner/supplier',
            }
        )
    if not cleanup_quality_record:
        missing.append(
            {
                'artifact': 'real_cad_cleanup_quality_record.csv',
                'required_action': 'provide cleanup quality records for at least three geometries with true cleanup checks, bbox fields, tool/method, and reviewer',
            }
        )
    return missing


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    package_root = Path(args.package_root)
    manifest_path = Path(args.real_cad_cleanup_manifest)
    data_room_index_path = Path(args.data_room_index)
    cleanup_quality_record_path = Path(args.cleanup_quality_record)
    cleanup_package_path = Path(args.real_cad_cleanup_package_report)
    template_files = write_intake_templates(package_root)

    source_dir = package_root / 'source_cad'
    cleaned_dir = package_root / 'cleaned_geometry'
    source_files = cad_files(source_dir)
    cleaned_files = cad_files(cleaned_dir)
    manifest_present = manifest_path.is_file()
    cleanup_package = load_json(cleanup_package_path)
    validation: dict[str, Any] | None = None
    data_room_index: dict[str, Any] | None = None
    cleanup_quality_record: dict[str, Any] | None = None
    manifest_error = ''
    data_room_index_error = ''
    cleanup_quality_record_error = ''
    if manifest_present:
        try:
            validation = validate_real_cad_cleanup_manifest(manifest_path, args.campaign)
        except (ManifestError, json.JSONDecodeError, OSError) as exc:
            manifest_error = str(exc)
    if data_room_index_path.is_file():
        try:
            data_room_index = validate_data_room_index(data_room_index_path)
        except RealCadIntakePreflightError as exc:
            data_room_index_error = str(exc)
    if cleanup_quality_record_path.is_file():
        try:
            cleanup_quality_record = validate_cleanup_quality_record(cleanup_quality_record_path)
        except RealCadIntakePreflightError as exc:
            cleanup_quality_record_error = str(exc)

    cleanup_clears = cleanup_package.get('clears_real_cad_cleanup_blocker') is True
    large_layout_valid = bool(
        validation
        and validation.get('large_layout_campaign') is True
        and int(validation.get('geometry_count', 0)) >= 3
    )
    ready_for_cleanup_gate = large_layout_valid and cleanup_clears
    missing_artifacts = build_missing_artifacts(
        manifest_present,
        len(source_files),
        len(cleaned_files),
        validation,
        data_room_index,
        cleanup_quality_record,
    )
    if manifest_error:
        missing_artifacts.append(
            {
                'artifact': 'valid_real_cad_cleanup_manifest',
                'required_action': f'fix manifest validation error: {manifest_error[:240]}',
            }
        )
    if data_room_index_error:
        missing_artifacts.append(
            {
                'artifact': 'valid_real_cad_data_room_index',
                'required_action': f'fix data-room index validation error: {data_room_index_error[:240]}',
            }
        )
    if cleanup_quality_record_error:
        missing_artifacts.append(
            {
                'artifact': 'valid_real_cad_cleanup_quality_record',
                'required_action': f'fix cleanup quality record validation error: {cleanup_quality_record_error[:240]}',
            }
        )

    quality_gate_matrix = [
        gate_row(
            'package_scaffold_available',
            package_root.is_dir() and source_dir.is_dir() and cleaned_dir.is_dir(),
            str(package_root),
            'Run the real-CAD cleanup package report to create package/source_cad/cleaned_geometry staging dirs.',
        ),
        gate_row(
            'data_room_templates_available',
            all(path.is_file() for path in template_files),
            [str(path) for path in template_files],
            'Create the CAD data-room index and cleanup quality record templates.',
        ),
        gate_row(
            'controlled_data_room_index_present',
            data_room_index_path.is_file(),
            str(data_room_index_path),
            'Provide real_cad_data_room_index.csv in the package root.',
        ),
        gate_row(
            'controlled_data_room_index_validates',
            data_room_index is not None,
            str(data_room_index_path),
            data_room_index_error or 'Data-room index must have at least three paired source/cleaned labels with valid hashes and provenance columns.',
        ),
        gate_row(
            'cleanup_quality_record_present',
            cleanup_quality_record_path.is_file(),
            str(cleanup_quality_record_path),
            'Provide real_cad_cleanup_quality_record.csv in the package root.',
        ),
        gate_row(
            'cleanup_quality_record_validates',
            cleanup_quality_record is not None,
            str(cleanup_quality_record_path),
            cleanup_quality_record_error or 'Cleanup quality record must include at least three labels with true checks, bbox fields, tool/method, and reviewer.',
        ),
        gate_row(
            'source_cad_large_layout_files_local',
            len(source_files) >= 3,
            [str(path) for path in source_files],
            'Provide at least three real source CAD files for large-layout evidence.',
        ),
        gate_row(
            'cleaned_geometry_large_layout_files_local',
            len(cleaned_files) >= 3,
            [str(path) for path in cleaned_files],
            'Provide at least three cleaned geometry files for large-layout evidence.',
        ),
        gate_row(
            'controlled_manifest_present',
            manifest_present,
            str(manifest_path),
            'Provide real_cad_cleanup_manifest.json in the package root.',
        ),
        gate_row(
            'controlled_manifest_validates',
            validation is not None,
            str(manifest_path),
            manifest_error or 'Manifest must pass campaign, provenance, hash, cleanup, bbox, and large-layout checks.',
        ),
        gate_row(
            'large_layout_real_cad_coverage',
            large_layout_valid,
            f"{validation.get('geometry_count')} geometries" if validation else '',
            'The validated manifest must declare large_layout_campaign=true and include at least three real geometries.',
        ),
        gate_row(
            'cleanup_package_blocks_or_clears_consistently',
            cleanup_package.get('status') in {
                'PASS-H2-REAL-CAD-CLEANUP-PACKAGE',
                'NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE',
            },
            str(cleanup_package_path),
            'Attach a valid real-CAD cleanup package report.',
        ),
        gate_row(
            'ready_for_scorecard_blocker_clearance',
            ready_for_cleanup_gate,
            'validated manifest and cleanup package clear real-CAD blocker',
            'The scorecard blocker stays open until the cleanup package clears a validated large-layout real-CAD manifest.',
        ),
    ]

    evidence_files = [
        evidence_entry('real_cad_cleanup_package_report', cleanup_package_path),
        evidence_entry('real_cad_data_room_index_template', template_files[0]),
        evidence_entry('real_cad_cleanup_quality_record_template', template_files[1]),
    ]
    if manifest_present:
        evidence_files.append(evidence_entry('real_cad_cleanup_manifest', manifest_path))
    if data_room_index_path.is_file():
        evidence_files.append(evidence_entry('real_cad_data_room_index', data_room_index_path))
    if cleanup_quality_record_path.is_file():
        evidence_files.append(evidence_entry('real_cad_cleanup_quality_record', cleanup_quality_record_path))

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Real-CAD Intake Preflight',
        'campaign': args.campaign,
        'package_root': str(package_root),
        'real_cad_cleanup_manifest': str(manifest_path),
        'clears_real_cad_cleanup_blocker': False,
        'ready_for_cleanup_package_gate': ready_for_cleanup_gate,
        'manifest_validation_error': manifest_error,
        'data_room_index_validation_error': data_room_index_error,
        'cleanup_quality_record_validation_error': cleanup_quality_record_error,
        'missing_artifacts': missing_artifacts,
        'summary': {
            'package_scaffold_available': package_root.is_dir() and source_dir.is_dir() and cleaned_dir.is_dir(),
            'data_room_templates_available': all(path.is_file() for path in template_files),
            'manifest_present': manifest_present,
            'data_room_index_present': data_room_index_path.is_file(),
            'data_room_index_validates': data_room_index is not None,
            'data_room_index_row_count': data_room_index.get('row_count') if data_room_index else 0,
            'data_room_index_paired_label_count': data_room_index.get('paired_label_count') if data_room_index else 0,
            'cleanup_quality_record_present': cleanup_quality_record_path.is_file(),
            'cleanup_quality_record_validates': cleanup_quality_record is not None,
            'cleanup_quality_record_row_count': cleanup_quality_record.get('row_count') if cleanup_quality_record else 0,
            'source_cad_file_count': len(source_files),
            'cleaned_geometry_file_count': len(cleaned_files),
            'manifest_validates': validation is not None,
            'large_layout_valid': large_layout_valid,
            'cleanup_package_status': cleanup_package.get('status'),
            'cleanup_package_clears_blocker': cleanup_clears,
            'missing_artifact_count': len(missing_artifacts),
        },
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': evidence_files,
        'limitations': [
            'This report is an intake preflight; it does not fabricate real CAD or clear the production blocker by itself.',
            'Production credit requires controlled source CAD, cleaned simulation geometry, exact hashes, provenance, and cleanup checks.',
            'The real-CAD blocker remains open until the cleanup package report validates a large-layout non-synthetic manifest.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('clears_real_cad_cleanup_blocker') is False, 'intake preflight cannot clear blocker directly')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('package_scaffold_available') is True, 'package scaffold missing')
    require(summary.get('data_room_templates_available') is True, 'data-room templates missing')
    require(isinstance(summary.get('data_room_index_present'), bool), 'data-room index presence missing')
    require(isinstance(summary.get('data_room_index_validates'), bool), 'data-room index validity missing')
    require(isinstance(summary.get('cleanup_quality_record_present'), bool), 'cleanup quality record presence missing')
    require(isinstance(summary.get('cleanup_quality_record_validates'), bool), 'cleanup quality record validity missing')
    require(isinstance(summary.get('source_cad_file_count'), int), 'source CAD count missing')
    require(isinstance(summary.get('cleaned_geometry_file_count'), int), 'cleaned geometry count missing')
    require(summary.get('cleanup_package_status') in {
        'PASS-H2-REAL-CAD-CLEANUP-PACKAGE',
        'NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE',
    }, 'invalid cleanup package status')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality gate matrix missing')
    if summary.get('cleanup_package_clears_blocker') is not True:
        require(any(item.get('status') == 'MISSING' for item in matrix if isinstance(item, dict)), 'open blocker must retain missing gates')
        missing = data.get('missing_artifacts')
        require(isinstance(missing, list) and missing, 'open blocker must list missing artifacts')
        missing_names = {str(item.get('artifact')) for item in missing if isinstance(item, dict)}
        if summary.get('data_room_index_validates') is not True:
            require('real_cad_data_room_index.csv' in missing_names or 'valid_real_cad_data_room_index' in missing_names, 'open data-room index gap must be listed')
        if summary.get('cleanup_quality_record_validates') is not True:
            require('real_cad_cleanup_quality_record.csv' in missing_names or 'valid_real_cad_cleanup_quality_record' in missing_names, 'open cleanup quality record gap must be listed')
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
        '# Engineering H2 Real-CAD Intake Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Campaign: `{report['campaign']}`",
        f"Package root: `{report['package_root']}`",
        f"Ready for cleanup package gate: `{report['ready_for_cleanup_package_gate']}`",
        f"Clears real-CAD blocker directly: `{report['clears_real_cad_cleanup_blocker']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Missing Artifacts', '']
    for item in report['missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
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
    parser.add_argument('--campaign', default='engineering-h2-production-full')
    parser.add_argument('--package-root', default=str(DEFAULT_PACKAGE_ROOT))
    parser.add_argument('--real-cad-cleanup-manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--data-room-index', default=str(DEFAULT_DATA_ROOM_INDEX))
    parser.add_argument('--cleanup-quality-record', default=str(DEFAULT_CLEANUP_QUALITY_RECORD))
    parser.add_argument('--real-cad-cleanup-package-report', default=str(DEFAULT_CLEANUP_PACKAGE_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_real_cad_intake_preflight VERIFY-PASS '
                f"json={args.verify_json} missing_artifacts={report['summary']['missing_artifact_count']} "
                f"source_cad={report['summary']['source_cad_file_count']} "
                f"cleaned_geometry={report['summary']['cleaned_geometry_file_count']}"
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
            'engineering_h2_real_cad_intake_preflight PASS '
            f"json={out_json} md={out_md} missing_artifacts={report['summary']['missing_artifact_count']}"
        )
        return 0
    except RealCadIntakePreflightError as exc:
        print(f'engineering_h2_real_cad_intake_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
