#!/usr/bin/env python3
"""Write/verify the engineering H2 real-CAD boundary-tag contract report."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_READY = 'PASS-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT'
STATUS_NOT_READY = 'NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724')
DEFAULT_PACKAGE_ROOT = Path('docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package')
DEFAULT_BOUNDARY_TAGS = DEFAULT_PACKAGE_ROOT / 'real_cad_boundary_tags.csv'
DEFAULT_BOUNDARY_TAG_TEMPLATE = DEFAULT_PACKAGE_ROOT / 'real_cad_boundary_tags_template.csv'
DEFAULT_CLEANUP_PACKAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
    'real_cad_cleanup_package_report.json'
)
DEFAULT_REAL_CAD_INTAKE_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/'
    'real_cad_intake_preflight_report.json'
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'real_cad_boundary_tag_contract_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'real_cad_boundary_tag_contract_report.md'

REQUIRED_COLUMNS = (
    'label',
    'patch_id',
    'bc_type',
    'face_selector',
    'normal_hint',
    'area_m2',
    'source_basis',
    'engineering_role',
    'reviewer',
)
ALLOWED_BC_TYPES = {
    'wall',
    'inlet',
    'outlet',
    'symmetry',
    'vent',
    'ground',
    'open',
    'slip_wall',
    'no_slip_wall',
}
REQUIRED_ENGINEERING_ROLES = {'wall_or_obstacle', 'release_or_inlet', 'outflow_or_vent'}
PLACEHOLDER_MARKERS = ('<', 'replace', 'todo', 'tbd', 'placeholder', 'fill in')


class BoundaryTagContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryTagContractError(message)


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
        raise BoundaryTagContractError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise BoundaryTagContractError(f'invalid JSON evidence {path}: {exc}') from exc
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline='', encoding='utf-8') as fh:
            return [dict(row) for row in csv.DictReader(fh)]
    except OSError as exc:
        raise BoundaryTagContractError(f'failed reading CSV {path}: {exc}') from exc


def write_template(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        REQUIRED_COLUMNS,
        (
            'tank_001',
            'tank_001_wall_shell',
            'no_slip_wall',
            'cad_named_face:tank_shell',
            '0,0,1',
            '12.50',
            'drawing_layer_or_cad_face_id',
            'wall_or_obstacle',
            '<reviewer>',
        ),
        (
            'pipe_rack_001',
            'pipe_release_nozzle',
            'inlet',
            'cad_named_face:release_nozzle',
            '1,0,0',
            '0.0025',
            'piping_isometric_face_id',
            'release_or_inlet',
            '<reviewer>',
        ),
        (
            'bund_wall_001',
            'domain_outlet_east',
            'outlet',
            'domain_plane:x_hi',
            '1,0,0',
            '100.0',
            'simulation_domain_definition',
            'outflow_or_vent',
            '<reviewer>',
        ),
    ]
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)
    return path


def has_placeholder(value: Any) -> bool:
    text = str(value).strip().lower()
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def parse_float(value: Any, label: str, gaps: list[str]) -> float | None:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        gaps.append(f'invalid_float:{label}:{value}')
        return None
    if parsed != parsed or parsed in (float('inf'), float('-inf')):
        gaps.append(f'nonfinite_float:{label}:{value}')
        return None
    return parsed


def parse_normal(value: Any, label: str, gaps: list[str]) -> tuple[float, float, float] | None:
    parts = [part.strip() for part in str(value).replace(';', ',').split(',') if part.strip()]
    if len(parts) != 3:
        gaps.append(f'invalid_normal_hint:{label}:{value}')
        return None
    values = [parse_float(part, f'{label}:normal_hint', gaps) for part in parts]
    if any(item is None for item in values):
        return None
    mag2 = sum(float(item) ** 2 for item in values if item is not None)
    if mag2 <= 0.0:
        gaps.append(f'zero_normal_hint:{label}')
        return None
    return float(values[0]), float(values[1]), float(values[2])


def manifest_labels(cleanup_package: dict[str, Any]) -> set[str]:
    validation = cleanup_package.get('validation_summary')
    if not isinstance(validation, dict):
        return set()
    geometries = validation.get('geometries')
    if isinstance(geometries, list):
        return {str(item.get('label')).strip() for item in geometries if isinstance(item, dict) and item.get('label')}
    files = validation.get('source_cad_files')
    if isinstance(files, list):
        labels = set()
        for item in files:
            path = str(item.get('path', '')) if isinstance(item, dict) else str(item)
            stem = Path(path).stem
            if stem:
                labels.add(stem)
        return labels
    return set()


def validate_boundary_tags(path: Path, cleanup_package: dict[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    if not path.is_file():
        return False, {}, [f'missing_boundary_tags_csv:{path}']
    rows = read_csv_rows(path)
    gaps: list[str] = []
    if not rows:
        gaps.append('boundary_tags_empty')
        return False, {'path': str(path), 'row_count': 0}, gaps
    columns = set(rows[0].keys())
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing_columns:
        gaps.append('boundary_tags_missing_columns:' + ','.join(missing_columns))
        return False, {'path': str(path), 'row_count': len(rows), 'columns': sorted(columns)}, gaps

    patch_ids: set[str] = set()
    labels: set[str] = set()
    roles: set[str] = set()
    bc_types: set[str] = set()
    for idx, row in enumerate(rows, 1):
        label = str(row.get('label', '')).strip()
        patch_id = str(row.get('patch_id', '')).strip()
        bc_type = str(row.get('bc_type', '')).strip().lower()
        role = str(row.get('engineering_role', '')).strip()
        row_label = f'row{idx}:{label or patch_id or "unnamed"}'
        if not label:
            gaps.append(f'missing_label:{idx}')
        else:
            labels.add(label)
        if not patch_id:
            gaps.append(f'missing_patch_id:{idx}')
        elif patch_id in patch_ids:
            gaps.append(f'duplicate_patch_id:{patch_id}')
        else:
            patch_ids.add(patch_id)
        if bc_type not in ALLOWED_BC_TYPES:
            gaps.append(f'invalid_bc_type:{row_label}:{bc_type}')
        else:
            bc_types.add(bc_type)
        if not str(row.get('face_selector', '')).strip():
            gaps.append(f'missing_face_selector:{row_label}')
        parse_normal(row.get('normal_hint'), row_label, gaps)
        area = parse_float(row.get('area_m2'), f'{row_label}:area_m2', gaps)
        if area is not None and area <= 0.0:
            gaps.append(f'nonpositive_area_m2:{row_label}:{area}')
        if not str(row.get('source_basis', '')).strip():
            gaps.append(f'missing_source_basis:{row_label}')
        if not role:
            gaps.append(f'missing_engineering_role:{row_label}')
        else:
            roles.add(role)
        if not str(row.get('reviewer', '')).strip():
            gaps.append(f'missing_reviewer:{row_label}')
        if any(has_placeholder(row.get(column, '')) for column in REQUIRED_COLUMNS):
            gaps.append(f'placeholder_marker:{row_label}')

    if not roles & {'wall_or_obstacle'}:
        gaps.append('missing_wall_or_obstacle_role')
    if not roles & {'release_or_inlet'}:
        gaps.append('missing_release_or_inlet_role')
    if not roles & {'outflow_or_vent'}:
        gaps.append('missing_outflow_or_vent_role')
    required_labels = manifest_labels(cleanup_package)
    missing_label_tags = sorted(required_labels - labels)
    if required_labels and missing_label_tags:
        gaps.append('boundary_tags_missing_manifest_labels:' + ','.join(missing_label_tags))
    if len(labels) < 3:
        gaps.append(f'boundary_tags_label_count:{len(labels)}<3')

    summary = {
        'path': str(path),
        'sha256': sha256_file(path),
        'row_count': len(rows),
        'label_count': len(labels),
        'patch_count': len(patch_ids),
        'bc_types': sorted(bc_types),
        'engineering_roles': sorted(roles),
        'required_manifest_label_count': len(required_labels),
        'missing_manifest_labels': missing_label_tags,
    }
    return not gaps, summary, gaps


def gate_row(name: str, passed: bool, evidence: str, gap: str) -> dict[str, Any]:
    return {
        'name': name,
        'status': 'PASS' if passed else 'MISSING',
        'evidence': evidence if passed else '',
        'gap': '' if passed else gap,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    cleanup_package_path = Path(args.real_cad_cleanup_package_report)
    intake_preflight_path = Path(args.real_cad_intake_preflight_report)
    boundary_tags_path = Path(args.boundary_tags)
    template_path = write_template(Path(args.boundary_tag_template))
    cleanup_package = load_json(cleanup_package_path)
    intake_preflight = load_json(intake_preflight_path)
    valid, tag_summary, gaps = validate_boundary_tags(boundary_tags_path, cleanup_package)
    cleanup_ready = cleanup_package.get('clears_real_cad_cleanup_blocker') is True
    intake_ready = (
        isinstance(intake_preflight.get('summary'), dict)
        and intake_preflight['summary'].get('large_layout_valid') is True
    )
    ready = valid and cleanup_ready and intake_ready
    status = STATUS_READY if ready else STATUS_NOT_READY
    quality_gate_matrix = [
        gate_row(
            'boundary_tag_template_available',
            template_path.is_file(),
            str(template_path),
            'Boundary tag template was not generated.',
        ),
        gate_row(
            'boundary_tags_present',
            boundary_tags_path.is_file(),
            str(boundary_tags_path),
            'Provide real_cad_boundary_tags.csv in the real-CAD package root.',
        ),
        gate_row(
            'boundary_tags_schema_valid',
            valid,
            str(boundary_tags_path),
            ';'.join(gaps[:12]) or 'Boundary tags failed validation.',
        ),
        gate_row(
            'boundary_tags_cover_large_layout_labels',
            valid and int(tag_summary.get('label_count', 0)) >= 3,
            f"labels={tag_summary.get('label_count')}" if tag_summary else '',
            'Boundary tags must cover at least three large-layout geometry labels.',
        ),
        gate_row(
            'required_engineering_roles_present',
            valid and REQUIRED_ENGINEERING_ROLES.issubset(set(tag_summary.get('engineering_roles', []))),
            ','.join(tag_summary.get('engineering_roles', [])) if tag_summary else '',
            'Boundary tags must include wall_or_obstacle, release_or_inlet, and outflow_or_vent roles.',
        ),
        gate_row(
            'real_cad_cleanup_ready',
            cleanup_ready,
            str(cleanup_package_path),
            'Real-CAD cleanup package must clear its blocker before BC tags can receive production credit.',
        ),
        gate_row(
            'real_cad_intake_large_layout_ready',
            intake_ready,
            str(intake_preflight_path),
            'Real-CAD intake preflight must validate large-layout source and cleaned geometry.',
        ),
        gate_row(
            'does_not_clear_without_real_cad',
            status == STATUS_NOT_READY or (cleanup_ready and intake_ready),
            status,
            'Boundary tagging cannot clear production readiness without validated real-CAD package and intake evidence.',
        ),
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Engineering H2 Real-CAD Boundary Tag Contract',
        'boundary_tags': str(boundary_tags_path),
        'boundary_tag_template': str(template_path),
        'real_cad_cleanup_package_report': str(cleanup_package_path),
        'real_cad_intake_preflight_report': str(intake_preflight_path),
        'allowed_bc_types': sorted(ALLOWED_BC_TYPES),
        'required_columns': list(REQUIRED_COLUMNS),
        'required_engineering_roles': sorted(REQUIRED_ENGINEERING_ROLES),
        'boundary_tags_valid': valid,
        'boundary_tag_gap_count': len(gaps),
        'boundary_tag_gaps': gaps,
        'ready_for_real_cad_bc_tagging_credit': ready,
        'does_not_clear_production_blockers': True,
        'summary': {
            'template_available': template_path.is_file(),
            'boundary_tags_present': boundary_tags_path.is_file(),
            'boundary_tags_valid': valid,
            'boundary_tag_row_count': tag_summary.get('row_count', 0),
            'boundary_tag_label_count': tag_summary.get('label_count', 0),
            'boundary_tag_patch_count': tag_summary.get('patch_count', 0),
            'required_role_count': len(REQUIRED_ENGINEERING_ROLES),
            'observed_required_role_count': len(REQUIRED_ENGINEERING_ROLES & set(tag_summary.get('engineering_roles', []))),
            'cleanup_package_clears_blocker': cleanup_ready,
            'intake_preflight_large_layout_valid': intake_ready,
            'ready_for_real_cad_bc_tagging_credit': ready,
        },
        'boundary_tag_summary': tag_summary,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('boundary_tag_template', template_path),
            evidence_entry('real_cad_cleanup_package_report', cleanup_package_path),
            evidence_entry('real_cad_intake_preflight_report', intake_preflight_path),
        ]
        + ([evidence_entry('real_cad_boundary_tags', boundary_tags_path)] if boundary_tags_path.is_file() else []),
        'limitations': [
            'This contract validates CAD face/patch boundary labels but does not create or clean CAD geometry.',
            'The current default state remains NOT_READY until real-CAD cleanup, intake, and boundary tags are all valid.',
            'Boundary tags support ENG-05 traceability but cannot clear production blockers without the full engineering H2 verifier.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    require(data.get('does_not_clear_production_blockers') is True, 'boundary tag contract must not clear blockers')
    require(set(data.get('required_columns', [])) == set(REQUIRED_COLUMNS), 'required columns mismatch')
    require(set(data.get('allowed_bc_types', [])) == ALLOWED_BC_TYPES, 'allowed BC types mismatch')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('template_available') is True, 'template missing')
    require(isinstance(summary.get('boundary_tags_present'), bool), 'boundary tags presence missing')
    require(isinstance(summary.get('boundary_tags_valid'), bool), 'boundary tags validity missing')
    require(int(summary.get('required_role_count', 0)) == len(REQUIRED_ENGINEERING_ROLES), 'required role count mismatch')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality gate matrix missing')
    if data.get('status') == STATUS_READY:
        require(summary.get('boundary_tags_valid') is True, 'READY contract has invalid tags')
        require(summary.get('cleanup_package_clears_blocker') is True, 'READY contract lacks cleanup blocker clearance')
        require(summary.get('intake_preflight_large_layout_valid') is True, 'READY contract lacks intake large-layout validation')
        require(summary.get('ready_for_real_cad_bc_tagging_credit') is True, 'READY contract not credit-ready')
        require(all(item.get('status') == 'PASS' for item in matrix if isinstance(item, dict)), 'READY contract has failed gates')
    else:
        require(summary.get('ready_for_real_cad_bc_tagging_credit') is False, 'NOT_READY contract marked credit-ready')
        require(any(item.get('status') == 'MISSING' for item in matrix if isinstance(item, dict)), 'NOT_READY contract must retain missing gates')
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
        '# Engineering H2 Real-CAD Boundary Tag Contract',
        '',
        f"Status: `{report['status']}`",
        f"Boundary tags: `{report['boundary_tags']}`",
        f"Template: `{report['boundary_tag_template']}`",
        f"Ready for BC-tagging credit: `{report['ready_for_real_cad_bc_tagging_credit']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Boundary Tag Gaps', '']
    for gap in report['boundary_tag_gaps']:
        lines.append(f'- `{gap}`')
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
    parser.add_argument('--boundary-tags', default=str(DEFAULT_BOUNDARY_TAGS))
    parser.add_argument('--boundary-tag-template', default=str(DEFAULT_BOUNDARY_TAG_TEMPLATE))
    parser.add_argument('--real-cad-cleanup-package-report', default=str(DEFAULT_CLEANUP_PACKAGE))
    parser.add_argument('--real-cad-intake-preflight-report', default=str(DEFAULT_REAL_CAD_INTAKE_PREFLIGHT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_real_cad_boundary_tag_contract VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"tags={summary['boundary_tag_row_count']} valid={summary['boundary_tags_valid']}"
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
            'engineering_h2_real_cad_boundary_tag_contract PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"tags={report['summary']['boundary_tag_row_count']} valid={report['summary']['boundary_tags_valid']}"
        )
        return 0
    except BoundaryTagContractError as exc:
        print(f'engineering_h2_real_cad_boundary_tag_contract FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
