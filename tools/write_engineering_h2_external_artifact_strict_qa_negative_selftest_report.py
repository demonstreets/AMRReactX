#!/usr/bin/env python3
"""Run/write/verify an all-present invalid-content self-test for H2 external artifact strict QA."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS = 'PASS-H2-EXTERNAL-ARTIFACT-STRICT-QA-NEGATIVE-SELFTEST'
EXPECTED_CONTENT_QUALITY_GATE_LEVEL = 'strict-v5-placeholder-free'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_strict_qa_negative_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_strict_qa_negative_selftest_report.md'
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)


class StrictQANegativeSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StrictQANegativeSelftestError(message)


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
        raise StrictQANegativeSelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise StrictQANegativeSelftestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_command(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        'command': ' '.join(argv),
        'returncode': completed.returncode,
        'output_tail': completed.stdout[-2000:],
    }


def run_expect_zero(argv: list[str]) -> dict[str, Any]:
    record = run_command(argv)
    require(record['returncode'] == 0, f"command failed: {record['command']}\n{record['output_tail']}")
    return record


def run_expect_nonzero(argv: list[str]) -> dict[str, Any]:
    record = run_command(argv)
    require(record['returncode'] != 0, f"command unexpectedly passed: {record['command']}")
    return record


def write_all_present_bad_fixture(drop_root: Path) -> None:
    real_root = drop_root / 'real_cad_cleanup'
    labels = ('tank_a', 'pipe_b', 'dike_c')
    write_json(
        real_root / 'real_cad_cleanup_manifest.json',
        {
            'schema_version': 1,
            'geometries': [
                {'label': label, 'source': f'source_cad/{label}.stp', 'cleaned': f'cleaned_geometry/{label}.stl'}
                for label in labels
            ],
            'provenance_note': 'strict qa negative synthetic selftest marker <replace-with-real-provenance>',
        },
    )
    for label in labels:
        write_text(real_root / 'source_cad' / f'{label}.stp', f'ISO-10303-21 synthetic selftest {label} <pending-real-cad>\n')
        write_text(real_root / 'cleaned_geometry' / f'{label}.stl', f'solid synthetic_selftest_{label}_replace\nendsolid\n')
    write_text(real_root / 'cleaned_geometry' / 'pipe_b_index_mismatch.stl', 'solid synthetic_selftest_pipe_b_mismatch_placeholder\nendsolid\n')

    quality_fields = [
        'label',
        'units_declared',
        'watertight_or_closed_surface',
        'nondegenerate_elements',
        'positive_volume_or_area',
        'bbox_min_m',
        'bbox_max_m',
        'tool_or_method',
        'reviewer',
    ]
    write_csv(
        real_root / 'real_cad_cleanup_quality_record.csv',
        quality_fields,
        [
            {
                'label': label,
                'units_declared': 'mm',
                'watertight_or_closed_surface': 'false',
                'nondegenerate_elements': 'true',
                'positive_volume_or_area': 'false',
                'bbox_min_m': '1,1,1',
                'bbox_max_m': '0,0,0',
                'tool_or_method': '<replace-with-cleanup-tool>',
                'reviewer': 'pending',
            }
            for label in labels
        ],
    )
    index_fields = ['file_role', 'label', 'relative_path', 'sha256', 'source_type', 'revision', 'owner_or_supplier']
    index_rows = []
    for role, subdir, ext in (
        ('source_cad', 'source_cad', 'stp'),
        ('cleaned_geometry', 'cleaned_geometry', 'stl'),
    ):
        for label in labels:
            rel = f'{subdir}/{label}.{ext}'
            if role == 'cleaned_geometry' and label == 'pipe_b':
                rel = 'cleaned_geometry/pipe_b_index_mismatch.stl'
            index_rows.append(
                {
                    'file_role': role,
                    'label': label,
                    'relative_path': rel,
                    'sha256': '<64 hex sha256>',
                    'source_type': 'replace-with-real-source-type',
                    'revision': 'pending',
                    'owner_or_supplier': 'codex-selftest',
                }
            )
    write_csv(real_root / 'real_cad_data_room_index.csv', index_fields, index_rows)

    plume_root = drop_root / 'external_plume_shape_reference'
    write_json(
        plume_root / 'dataset_metadata.json',
        {
            'schema_version': 1,
            'benchmark_id': 'hysafe_sbepv5_d27',
            'source': {
                'type': 'synthetic_selftest',
                'url': 'https://replace-with-public-source-or-use-doi',
                'source_file_sha256': '<64 hex sha256>',
            },
            'digitization': {'method': '<replace-with-digitization-method>'},
        },
    )
    write_csv(
        plume_root / 'sensor_coordinates.csv',
        ['sensor_id', 'x_m', 'y_m', 'z_m', 'reliability', 'source_basis', 'digitization_uncertainty_m'],
        [
            {
                'sensor_id': f'Gas{idx:02d}',
                'x_m': 'bad-number' if idx == 1 else idx,
                'y_m': 0.0,
                'z_m': 0.25,
                'reliability': 'pending',
                'source_basis': '<source figure or table>',
                'digitization_uncertainty_m': 0.5,
            }
            for idx in range(1, 13)
        ],
    )
    write_csv(
        plume_root / 'baffle_geometry.csv',
        ['baffle_id', 'x_min_m', 'x_max_m', 'y_min_m', 'y_max_m', 'z_min_m', 'z_max_m', 'source_basis', 'digitization_uncertainty_m'],
        [
            {
                'baffle_id': f'B{idx}',
                'x_min_m': idx,
                'x_max_m': idx,
                'y_min_m': 0.5,
                'y_max_m': -0.5,
                'z_min_m': 1.0,
                'z_max_m': 0.0,
                'source_basis': '<source figure or table>',
                'digitization_uncertainty_m': 0.5,
            }
            for idx in range(1, 5)
        ],
    )
    ts_fields = ['time_s'] + [f'Gas{idx:02d}_vol_percent' for idx in range(1, 13)]
    write_csv(
        plume_root / 'experimental_timeseries.csv',
        ts_fields,
        [
            {'time_s': 10.0, **{f'Gas{idx:02d}_vol_percent': 0.0 for idx in range(1, 13)}},
            {'time_s': 5.0, **{f'Gas{idx:02d}_vol_percent': 150.0 for idx in range(1, 13)}},
        ],
    )

    fire_root = drop_root / 'fire_consequence_calibration'
    write_json(
        fire_root / 'calibration_metadata.json',
        {
            'schema_version': 1,
            'dataset_type': 'synthetic_selftest',
            'case': 'bad_content',
            'source': {
                'type': 'synthetic_selftest',
                'url': 'https://replace-with-public-source-or-use-doi',
                'source_file_sha256': '<64 hex sha256>',
            },
            'case_alignment': {'geometry': True, 'fuel': False, 'wind': True},
        },
    )
    write_csv(
        fire_root / 'radiation_metrics.csv',
        ['metric_id', 'distance_m', 'reference_flux_w_m2', 'tolerance_abs_w_m2', 'tolerance_rel', 'source_basis'],
        [
            {'metric_id': 'q001', 'distance_m': -5.0, 'reference_flux_w_m2': 0.0, 'tolerance_abs_w_m2': -1.0, 'tolerance_rel': 2.0, 'source_basis': '<instrument log pending>'},
            {'metric_id': 'q001', 'distance_m': -4.0, 'reference_flux_w_m2': 0.0, 'tolerance_abs_w_m2': -1.0, 'tolerance_rel': 2.0, 'source_basis': '<instrument log pending>'},
        ],
    )
    write_csv(
        fire_root / 'overpressure_metrics.csv',
        ['metric_id', 'distance_m', 'reference_overpressure_kpa', 'tolerance_abs_kpa', 'tolerance_rel', 'source_basis'],
        [
            {'metric_id': 'p001', 'distance_m': -5.0, 'reference_overpressure_kpa': 0.0, 'tolerance_abs_kpa': -1.0, 'tolerance_rel': 2.0, 'source_basis': '<instrument log pending>'},
            {'metric_id': 'p001', 'distance_m': -4.0, 'reference_overpressure_kpa': 0.0, 'tolerance_abs_kpa': -1.0, 'tolerance_rel': 2.0, 'source_basis': '<instrument log pending>'},
        ],
    )
    write_json(
        fire_root / 'calibrated_fire_consequence_report.json',
        {'status': 'PASS-SMOKE', 'summary': {'note': 'synthetic_selftest marker <replace-with-calibrated-report>'}},
    )


def count_present_artifacts(drop: dict[str, Any]) -> int:
    present = 0
    for domain in drop.get('domain_records', []):
        if not isinstance(domain, dict):
            continue
        for item in domain.get('artifact_validations', []):
            if not isinstance(item, dict):
                continue
            validation = item.get('drop_validation')
            if isinstance(validation, dict) and validation.get('present') is True:
                present += 1
    return present


def collect_gap_sample(drop: dict[str, Any], limit: int = 30) -> list[str]:
    gaps: list[str] = []
    for domain in drop.get('domain_records', []):
        if not isinstance(domain, dict):
            continue
        for gap in domain.get('domain_quality_gaps', []):
            gaps.append(f"{domain.get('domain')}:domain_quality_gap:{gap}")
        for item in domain.get('artifact_validations', []):
            if not isinstance(item, dict):
                continue
            artifact = item.get('artifact')
            validation = item.get('drop_validation')
            if not isinstance(validation, dict):
                continue
            for gap in validation.get('gaps', []):
                gaps.append(f'{artifact}:{gap}')
    return gaps[:limit]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.output_json).parent
    drop_root = root / 'strict_qa_negative_fixture' / 'drop'
    drop_report = root / 'strict_qa_negative_drop_validator_report.json'
    drop_md = root / 'strict_qa_negative_drop_validator_report.md'
    plan_report = root / 'strict_qa_negative_ingestion_plan.json'
    plan_md = root / 'strict_qa_negative_ingestion_plan.md'
    copy_report = root / 'strict_qa_negative_controlled_copy_report.json'
    copy_md = root / 'strict_qa_negative_controlled_copy_report.md'
    closure_path = Path(args.production_blocker_closure_manifest_report)

    root.mkdir(parents=True, exist_ok=True)
    write_all_present_bad_fixture(drop_root)

    py = sys.executable
    commands = [
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_drop_validator.py',
                '--drop-root',
                str(drop_root),
                '--production-blocker-closure-manifest-report',
                str(closure_path),
                '--output-json',
                str(drop_report),
                '--output-md',
                str(drop_md),
                '--no-ensure-scaffold',
            ]
        ),
        run_expect_zero([py, 'tools/write_engineering_h2_external_artifact_drop_validator.py', '--verify-json', str(drop_report)]),
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_ingestion_plan.py',
                '--external-artifact-drop-validator-report',
                str(drop_report),
                '--production-blocker-closure-manifest-report',
                str(closure_path),
                '--output-json',
                str(plan_report),
                '--output-md',
                str(plan_md),
            ]
        ),
        run_expect_zero([py, 'tools/write_engineering_h2_external_artifact_ingestion_plan.py', '--verify-json', str(plan_report)]),
        run_expect_zero(
            [
                py,
                'tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
                '--external-artifact-ingestion-plan-report',
                str(plan_report),
                '--output-json',
                str(copy_report),
                '--output-md',
                str(copy_md),
            ]
        ),
        run_expect_zero([py, 'tools/write_engineering_h2_external_artifact_controlled_copy_report.py', '--verify-json', str(copy_report)]),
    ]
    refused_apply = run_expect_nonzero(
        [
            py,
            'tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
            '--external-artifact-ingestion-plan-report',
            str(plan_report),
            '--apply',
            '--confirm-controlled-copy',
            'H2_EXTERNAL_ARTIFACTS_READY',
            '--output-json',
            str(root / 'strict_qa_negative_apply_should_not_exist.json'),
            '--output-md',
            str(root / 'strict_qa_negative_apply_should_not_exist.md'),
        ]
    )
    commands.append(refused_apply)

    drop = load_json(drop_report)
    plan = load_json(plan_report)
    copy = load_json(copy_report)
    present_count = count_present_artifacts(drop)
    gap_sample = collect_gap_sample(drop)
    placeholder_gap_detected = any('placeholder' in gap or 'template' in gap for gap in gap_sample)
    quality_gate_matrix = [
        {
            'name': 'all_expected_artifacts_are_present_in_fixture',
            'status': 'PASS' if present_count == int(drop.get('total_expected_artifact_count', -1)) == 14 else 'MISSING',
            'evidence': f'present={present_count} expected={drop.get("total_expected_artifact_count")}',
            'gap': '',
        },
        {
            'name': 'strict_content_qa_rejects_bad_complete_drop',
            'status': 'PASS'
            if drop.get('status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'
            and int(drop.get('valid_artifact_count', 14)) < 14
            and drop.get('content_quality_gate_level') == EXPECTED_CONTENT_QUALITY_GATE_LEVEL
            else 'MISSING',
            'evidence': str(drop_report),
            'gap': '',
        },
        {
            'name': 'strict_placeholder_qa_rejects_template_values',
            'status': 'PASS' if placeholder_gap_detected else 'MISSING',
            'evidence': ';'.join(gap_sample),
            'gap': '',
        },
        {
            'name': 'ingestion_plan_stays_not_ready',
            'status': 'PASS'
            if plan.get('status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'
            and int(plan.get('ready_copy_action_count', 14)) < 14
            else 'MISSING',
            'evidence': str(plan_report),
            'gap': '',
        },
        {
            'name': 'controlled_copy_stays_no_write',
            'status': 'PASS'
            if copy.get('status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
            and copy.get('applied_copy_actions') is False
            and int(copy.get('copied_file_count', -1)) == 0
            else 'MISSING',
            'evidence': str(copy_report),
            'gap': '',
        },
        {
            'name': 'apply_refused_for_invalid_complete_drop',
            'status': 'PASS' if int(refused_apply.get('returncode', 0)) != 0 else 'MISSING',
            'evidence': refused_apply.get('output_tail', ''),
            'gap': '',
        },
        {
            'name': 'does_not_clear_production_blockers',
            'status': 'PASS',
            'evidence': 'strict QA negative self-test is gate-mechanics evidence only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Artifact Strict-QA Negative Self-Test',
        'negative_selftest_only': True,
        'all_expected_artifacts_present_fixture': True,
        'does_not_clear_production_blockers': True,
        'production_blocker_closure_manifest_report': str(closure_path),
        'strict_qa_negative_drop_root': str(drop_root),
        'strict_qa_negative_reports': {
            'drop_validator': str(drop_report),
            'ingestion_plan': str(plan_report),
            'controlled_copy': str(copy_report),
        },
        'summary': {
            'drop_status': drop.get('status'),
            'drop_content_quality_gate_level': drop.get('content_quality_gate_level'),
            'drop_placeholder_gap_detected': placeholder_gap_detected,
            'drop_domain_quality_gap_count': drop.get('domain_quality_gap_count'),
            'drop_present_artifact_count': present_count,
            'drop_valid_artifact_count': drop.get('valid_artifact_count'),
            'drop_total_expected_artifact_count': drop.get('total_expected_artifact_count'),
            'drop_missing_or_invalid_artifact_count': drop.get('missing_or_invalid_artifact_count'),
            'ingestion_status': plan.get('status'),
            'ingestion_ready_copy_action_count': plan.get('ready_copy_action_count'),
            'controlled_copy_status': copy.get('status'),
            'controlled_copy_copied_file_count': copy.get('copied_file_count'),
            'controlled_copy_applied_copy_actions': copy.get('applied_copy_actions'),
            'apply_refused_returncode': refused_apply.get('returncode'),
            'gap_sample': gap_sample,
        },
        'command_records': commands,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('production_blocker_closure_manifest_report', closure_path),
            evidence_entry('strict_qa_negative_drop_validator_report', drop_report),
            evidence_entry('strict_qa_negative_ingestion_plan_report', plan_report),
            evidence_entry('strict_qa_negative_controlled_copy_report', copy_report),
        ],
        'limitations': [
            'This negative self-test uses a deliberately invalid complete fixture.',
            'It proves that all expected files being present is insufficient to pass strict-v5 placeholder-free content QA.',
            'It must not be used to clear real-CAD, SBEPV5, or fire-calibration blockers.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('negative_selftest_only') is True, 'negative self-test must be marked synthetic')
    require(data.get('all_expected_artifacts_present_fixture') is True, 'fixture must be all-present')
    require(data.get('does_not_clear_production_blockers') is True, 'negative self-test must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('drop_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP', 'bad complete drop unexpectedly ready')
    require(
        summary.get('drop_content_quality_gate_level') == EXPECTED_CONTENT_QUALITY_GATE_LEVEL,
        'strict-v5 placeholder-free gate not exercised',
    )
    require(summary.get('drop_placeholder_gap_detected') is True, 'strict-v5 did not detect placeholder/template markers')
    require(int(summary.get('drop_domain_quality_gap_count', 0)) >= 1, 'strict-v3 did not detect domain quality gaps')
    require(int(summary.get('drop_present_artifact_count', -1)) == 14, 'all-present fixture did not present all artifacts')
    require(int(summary.get('drop_valid_artifact_count', 14)) < 14, 'bad complete drop validated all artifacts')
    require(summary.get('ingestion_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'bad complete ingestion unexpectedly ready')
    require(summary.get('controlled_copy_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY', 'bad complete copy unexpectedly ready')
    require(summary.get('controlled_copy_applied_copy_actions') is False, 'bad complete copy applied actions')
    require(int(summary.get('controlled_copy_copied_file_count', -1)) == 0, 'bad complete copy wrote files')
    require(int(summary.get('apply_refused_returncode', 0)) != 0, 'bad complete apply was not refused')
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
        '# Engineering H2 External Artifact Strict-QA Negative Self-Test',
        '',
        f"Status: `{report['status']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        if key == 'gap_sample':
            continue
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Gap Sample', '']
    for item in report['summary']['gap_sample']:
        lines.append(f'- `{item}`')
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
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'engineering_h2_external_artifact_strict_qa_negative_selftest VERIFY-PASS '
                f"json={args.verify_json} present={summary['drop_present_artifact_count']} "
                f"valid={summary['drop_valid_artifact_count']}/{summary['drop_total_expected_artifact_count']}"
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
        summary = report['summary']
        print(
            'engineering_h2_external_artifact_strict_qa_negative_selftest PASS '
            f"json={out_json} md={out_md} present={summary['drop_present_artifact_count']} "
            f"valid={summary['drop_valid_artifact_count']}/{summary['drop_total_expected_artifact_count']}"
        )
        return 0
    except StrictQANegativeSelftestError as exc:
        print(f'engineering_h2_external_artifact_strict_qa_negative_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
