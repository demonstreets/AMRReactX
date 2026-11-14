#!/usr/bin/env python3
"""Write and verify the engineering H2 real-CAD cleanup package report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from write_engineering_campaign_manifest import (
    ManifestError,
    REAL_CAD_DATASET_TYPE,
    REAL_CAD_SOURCE_TYPES,
    REQUIRED_REAL_CAD_PROVENANCE_FIELDS,
    validate_real_cad_cleanup_manifest,
)

SCHEMA_VERSION = 2
STATUS_READY = 'PASS-H2-REAL-CAD-CLEANUP-PACKAGE'
STATUS_NOT_READY = 'NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE'
DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723')
DEFAULT_PACKAGE_ROOT = DEFAULT_ROOT / 'package'
DEFAULT_MANIFEST = DEFAULT_PACKAGE_ROOT / 'real_cad_cleanup_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'real_cad_cleanup_package_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'real_cad_cleanup_package_report.md'


class RealCadPackageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RealCadPackageError(message)


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
        raise RealCadPackageError(f'missing JSON: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RealCadPackageError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def safe_gap(text: str) -> str:
    text = re.sub(r'\s+', '_', text.strip())
    text = re.sub(r'[^A-Za-z0-9_.:/=-]+', '_', text)
    return text[:240]


def manifest_template(campaign: str) -> dict[str, Any]:
    return {
        'schema_version': 1,
        'dataset_type': REAL_CAD_DATASET_TYPE,
        'campaign': campaign,
        'status': 'PASS',
        'synthetic': False,
        'cad_source_is_real': True,
        'source_type': 'owner_operator_cad',
        'large_layout_campaign': True,
        'provenance': {
            'title': 'Replace with plant/tank farm CAD package title',
            'owner_or_supplier': 'Replace with owner/operator/vendor name',
            'drawing_or_package_id': 'Replace with controlled drawing/package id',
            'revision': 'Replace with revision',
            'received_at_utc': 'YYYY-MM-DDTHH:MM:SSZ',
            'confidentiality': 'internal_or_owner_provided',
        },
        'geometries': [
            {
                'label': label,
                'source_cad': {
                    'path': f'{DEFAULT_PACKAGE_ROOT}/source_cad/{label}.step',
                    'sha256': '<64 hex sha256 of source CAD>',
                },
                'cleaned_geometry': {
                    'path': f'{DEFAULT_PACKAGE_ROOT}/cleaned_geometry/{label}.stl',
                    'sha256': '<64 hex sha256 of cleaned geometry>',
                },
                'cleanup_checks': {
                    'units_declared': True,
                    'watertight_or_closed_surface': True,
                    'nondegenerate_elements': True,
                    'positive_volume_or_area': True,
                    'bbox_min_m': [0.0, 0.0, 0.0],
                    'bbox_max_m': [1.0, 1.0, 1.0],
                    'notes': 'Replace bbox and checks with measured cleanup output.',
                },
            }
            for label in ('tank_001', 'pipe_rack_001', 'bund_wall_001')
        ],
    }


def intake_checklist_lines() -> list[str]:
    rows = [
        ['item', 'required_evidence', 'production_rule'],
        ['provenance.title', 'controlled CAD/package title', 'non-empty'],
        ['provenance.owner_or_supplier', 'owner/operator/vendor name', 'non-empty'],
        ['provenance.drawing_or_package_id', 'drawing or CAD package id', 'non-empty'],
        ['provenance.revision', 'controlled revision', 'non-empty'],
        ['provenance.received_at_utc', 'UTC receipt timestamp', 'YYYY-MM-DDTHH:MM:SSZ'],
        ['provenance.confidentiality', 'data handling category', 'non-empty'],
        ['source_type', 'source classification', '|'.join(sorted(REAL_CAD_SOURCE_TYPES))],
        ['geometries[].source_cad', 'source CAD file and SHA-256', 'supported CAD/geometry extension and exact hash'],
        ['geometries[].cleaned_geometry', 'cleaned simulation geometry and SHA-256', 'supported CAD/geometry extension and exact hash'],
        ['cleanup_checks.units_declared', 'declared geometry units', 'true'],
        ['cleanup_checks.watertight_or_closed_surface', 'closed/watertight cleanup result', 'true'],
        ['cleanup_checks.nondegenerate_elements', 'degenerate element check result', 'true'],
        ['cleanup_checks.positive_volume_or_area', 'positive volume/area check result', 'true'],
        ['cleanup_checks.bbox_min_m/max_m', 'meter-space bounding box', 'finite 3D min/max with max greater than min'],
        ['large_layout_campaign', 'multi-object tank/pipe layout declaration', 'true with at least three geometries for blocker clearance'],
    ]
    return [','.join(f'"{cell}"' for cell in row) for row in rows]


def write_package_templates(package_root: Path, campaign: str) -> list[Path]:
    source_dir = package_root / 'source_cad'
    cleaned_dir = package_root / 'cleaned_geometry'
    source_dir.mkdir(parents=True, exist_ok=True)
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    template_path = package_root / 'real_cad_cleanup_manifest_template.json'
    checklist_path = package_root / 'real_cad_intake_checklist.csv'
    readme_path = package_root / 'README.md'
    source_readme = source_dir / 'README.md'
    cleaned_readme = cleaned_dir / 'README.md'
    template_path.write_text(
        json.dumps(manifest_template(campaign), indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    readme_path.write_text(
        '\n'.join(
            [
                '# Engineering H2 Real-CAD Cleanup Package',
                '',
                'Fill `real_cad_cleanup_manifest.json` from the template after source CAD and cleaned geometry files are staged.',
                '',
                'Production credit requires:',
                '- `synthetic: false` and `cad_source_is_real: true`',
                f"- `source_type` in `{sorted(REAL_CAD_SOURCE_TYPES)}`",
                '- at least three geometries for a large-layout campaign',
                '- source and cleaned geometry files with exact SHA-256 hashes',
                '- cleanup checks proving declared units, closed/watertight surfaces, nondegenerate elements, positive volume/area, and meter bounding boxes',
                '- all intake checklist rows in `real_cad_intake_checklist.csv` satisfied by controlled evidence',
                '',
                'This package is a data-ingestion gate. It does not claim CFD accuracy by itself.',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    source_readme.write_text(
        'Place owner/operator, as-built, vendor, or plant CAD files here. Supported extensions: .stl, .step, .stp, .iges, .igs, .brep, .obj.\n',
        encoding='utf-8',
    )
    cleaned_readme.write_text(
        'Place cleaned simulation geometry here after scale, watertightness, degeneracy, and bbox checks are complete.\n',
        encoding='utf-8',
    )
    checklist_path.write_text('\n'.join(intake_checklist_lines()) + '\n', encoding='utf-8')
    return [template_path, checklist_path, readme_path, source_readme, cleaned_readme]


def gate_row(name: str, passed: bool, evidence: str, gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else '',
        'gap': '' if passed else gap,
    }


def build_quality_gate_matrix(
    manifest_present: bool,
    validation: dict[str, Any] | None,
    clears_blocker: bool,
) -> list[dict[str, Any]]:
    provenance = validation.get('provenance', {}) if validation else {}
    provenance_complete = bool(
        validation
        and isinstance(provenance, dict)
        and all(str(provenance.get(key, '')).strip() for key in REQUIRED_REAL_CAD_PROVENANCE_FIELDS)
    )
    source_files = validation.get('source_cad_files', []) if validation else []
    cleaned_files = validation.get('cleaned_geometry_files', []) if validation else []
    bbox = validation.get('bbox_union_m', {}) if validation else {}
    extents = bbox.get('extent', []) if isinstance(bbox, dict) else []
    bbox_ok = bool(validation and isinstance(extents, list) and sum(1 for value in extents if float(value) > 0.0) >= 2)
    geometry_count = int(validation.get('geometry_count', 0)) if validation else 0
    large_layout = bool(validation and validation.get('large_layout_campaign') is True)
    return [
        gate_row(
            'manifest_present',
            manifest_present,
            'real_cad_cleanup_manifest.json exists',
            'Provide real_cad_cleanup_manifest.json in the package root.',
        ),
        gate_row(
            'provenance_complete',
            provenance_complete,
            'required provenance fields are populated',
            'Populate title, owner_or_supplier, drawing_or_package_id, revision, received_at_utc, and confidentiality.',
        ),
        gate_row(
            'real_cad_source_classified',
            bool(validation and validation.get('source_type') in REAL_CAD_SOURCE_TYPES),
            str(validation.get('source_type')) if validation else '',
            'Set source_type to an accepted real-CAD source classification.',
        ),
        gate_row(
            'source_cad_hashes_verified',
            bool(source_files),
            f'{len(source_files)} source CAD file hash(es) verified',
            'Stage source CAD files and record exact SHA-256 hashes.',
        ),
        gate_row(
            'cleaned_geometry_hashes_verified',
            bool(cleaned_files),
            f'{len(cleaned_files)} cleaned geometry file hash(es) verified',
            'Stage cleaned geometry files and record exact SHA-256 hashes.',
        ),
        gate_row(
            'large_layout_coverage',
            large_layout and geometry_count >= 3,
            f'{geometry_count} geometries in large-layout campaign',
            'Mark large_layout_campaign true and provide at least three real geometries.',
        ),
        gate_row(
            'bbox_non_degenerate_m',
            bbox_ok,
            f"extent_m={extents}" if extents else '',
            'Provide finite meter-space bbox_min_m/bbox_max_m with nondegenerate layout extents.',
        ),
        gate_row(
            'scorecard_blocker_clearance',
            clears_blocker,
            'validated large-layout real-CAD cleanup package clears blocker',
            'All real-CAD package gates must pass before the production scorecard can clear this blocker.',
        ),
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    package_root = Path(args.package_root)
    manifest_path = Path(args.real_cad_cleanup_manifest)
    template_files = write_package_templates(package_root, args.campaign)
    blocking_gaps: list[str] = []
    validation: dict[str, Any] | None = None
    manifest_present = manifest_path.is_file()
    if not manifest_present:
        blocking_gaps.extend(
            [
                'real_cad_cleanup_manifest_missing',
                'source_cad_files_missing',
                'cleaned_geometry_files_missing',
                'large_layout_requires_at_least_three_real_geometries',
            ]
        )
    else:
        try:
            validation = validate_real_cad_cleanup_manifest(manifest_path, args.campaign)
        except (ManifestError, json.JSONDecodeError, OSError) as exc:
            blocking_gaps.append('real_cad_cleanup_manifest_invalid:' + safe_gap(str(exc)))

    clears_blocker = bool(
        validation
        and validation.get('status') == 'PASS'
        and validation.get('large_layout_campaign') is True
        and int(validation.get('geometry_count', 0)) >= 3
    )
    if validation and not clears_blocker:
        blocking_gaps.append('real_cad_cleanup_manifest_does_not_clear_large_layout_blocker')
    ready = clears_blocker and not blocking_gaps
    quality_gate_matrix = build_quality_gate_matrix(manifest_present, validation, clears_blocker)

    evidence_files = [
        evidence_entry('real_cad_cleanup_package_readme', package_root / 'README.md'),
        evidence_entry('real_cad_cleanup_manifest_template', package_root / 'real_cad_cleanup_manifest_template.json'),
        evidence_entry('real_cad_intake_checklist', package_root / 'real_cad_intake_checklist.csv'),
        evidence_entry('source_cad_readme', package_root / 'source_cad' / 'README.md'),
        evidence_entry('cleaned_geometry_readme', package_root / 'cleaned_geometry' / 'README.md'),
    ]
    if manifest_present:
        evidence_files.append(evidence_entry('real_cad_cleanup_manifest', manifest_path))

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 Real-CAD Cleanup Package',
        'campaign': args.campaign,
        'package_root': str(package_root),
        'real_cad_cleanup_manifest': str(manifest_path),
        'manifest_present': manifest_present,
        'clears_real_cad_cleanup_blocker': clears_blocker,
        'blocking_gaps': blocking_gaps,
        'quality_gate_matrix': quality_gate_matrix,
        'template_files': [str(path) for path in template_files],
        'validation_summary': validation,
        'current_inputs': {
            'cad_source_is_real': bool(validation and validation.get('source_type')),
            'large_layout_campaign': bool(validation and validation.get('large_layout_campaign')),
            'geometry_count': int(validation.get('geometry_count', 0)) if validation else 0,
            'source_cad_files_verified': bool(validation and validation.get('source_cad_files')),
            'cleaned_geometry_files_verified': bool(validation and validation.get('cleaned_geometry_files')),
        },
        'evidence_files': evidence_files,
        'limitations': [
            'This report prepares and validates a real-CAD cleanup evidence package; it is not external safety certification.',
            'The current default package is NOT_READY until real source CAD, cleaned geometry, hashes, provenance, and cleanup checks are supplied.',
            'The production scorecard can clear the real-CAD blocker only after a validated large-layout CAD manifest is attached to the campaign manifest.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, f"invalid status {data.get('status')}")
    require(str(data.get('campaign', '')).strip(), 'campaign missing')
    require(str(data.get('package_root', '')).strip(), 'package_root missing')
    require(isinstance(data.get('manifest_present'), bool), 'manifest_present is not boolean')
    require(isinstance(data.get('clears_real_cad_cleanup_blocker'), bool), 'clears flag is not boolean')
    gaps = data.get('blocking_gaps')
    require(isinstance(gaps, list), 'blocking_gaps is not a list')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality_gate_matrix missing')
    failed_matrix = [item for item in matrix if isinstance(item, dict) and item.get('status') != 'PASS']
    if data.get('status') == STATUS_READY:
        require(data.get('clears_real_cad_cleanup_blocker') is True, 'READY report does not clear blocker')
        require(not gaps, 'READY report still has blocking gaps')
        require(not failed_matrix, 'READY report has failed quality gates')
        summary = data.get('validation_summary')
        require(isinstance(summary, dict), 'READY report missing validation summary')
        require(summary.get('large_layout_campaign') is True, 'READY report is not large-layout')
        require(int(summary.get('geometry_count', 0)) >= 3, 'READY report has too few geometries')
    else:
        require(gaps, 'NOT_READY report must list blocking gaps')
        require(data.get('clears_real_cad_cleanup_blocker') is False, 'NOT_READY report cannot clear blocker')
        require(failed_matrix, 'NOT_READY report must list failed quality gates')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            p = Path(str(item.get('path', '')))
            require(p.is_file(), f'missing evidence file: {p}')
            require(sha256_file(p) == item.get('sha256'), f'evidence hash mismatch: {p}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Real-CAD Cleanup Package',
        '',
        f"Status: `{report['status']}`",
        f"Campaign: `{report['campaign']}`",
        f"Package root: `{report['package_root']}`",
        f"Manifest: `{report['real_cad_cleanup_manifest']}`",
        f"Clears real-CAD blocker: `{report['clears_real_cad_cleanup_blocker']}`",
        '',
        '## Current Inputs',
        '',
    ]
    for key, value in report['current_inputs'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Blocking Gaps', '']
    for gap in report['blocking_gaps']:
        lines.append(f'- `{gap}`')
    lines += ['', '## Quality Gate Matrix', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        gap = item['gap'] or item['evidence']
        lines.append(f"| `{item['name']}` | `{item['status']}` | {gap} |")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', default='engineering-h2-production-full')
    parser.add_argument('--package-root', default=str(DEFAULT_PACKAGE_ROOT))
    parser.add_argument('--real-cad-cleanup-manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_real_cad_cleanup_package VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"clears={report['clears_real_cad_cleanup_blocker']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_real_cad_cleanup_package PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"gaps={len(report['blocking_gaps'])}"
        )
        return 0
    except RealCadPackageError as exc:
        print(f'engineering_h2_real_cad_cleanup_package FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
