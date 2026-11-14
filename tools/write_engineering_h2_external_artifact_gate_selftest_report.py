#!/usr/bin/env python3
"""Run/write/verify an isolated synthetic self-test for the engineering H2 external artifact gates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-EXTERNAL-ARTIFACT-GATE-SELFTEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_external_artifact_gate_selftest_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_external_artifact_gate_selftest_report.md'
DEFAULT_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)


class GateSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateSelftestError(message)


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
        raise GateSelftestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise GateSelftestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def make_synthetic_closure(real_closure: dict[str, Any], target_root: Path, output_path: Path) -> dict[str, Any]:
    closure = json.loads(json.dumps(real_closure))
    for domain_record in closure.get('domain_closure_records', []):
        if not isinstance(domain_record, dict):
            continue
        domain = str(domain_record.get('domain', 'unknown_domain'))
        for artifact_record in domain_record.get('artifact_records', []):
            if not isinstance(artifact_record, dict):
                continue
            original = str(artifact_record.get('target_path', 'artifact'))
            name = Path(original.rstrip('/')).name or 'artifact'
            if original.endswith('/'):
                artifact_record['target_path'] = str(target_root / domain / name) + '/'
            else:
                artifact_record['target_path'] = str(target_root / domain / name)
            artifact_record['synthetic_target_path_rewrite'] = True
    closure['synthetic_selftest_manifest'] = True
    closure['synthetic_selftest_target_root'] = str(target_root)
    write_json(output_path, closure)
    return closure


def write_synthetic_drop(drop_root: Path) -> None:
    real_root = drop_root / 'real_cad_cleanup'
    write_json(
        real_root / 'real_cad_cleanup_manifest.json',
        {
            'schema_version': 1,
            'synthetic_selftest_only': True,
            'geometries': [
                {'label': 'tank_a', 'source': 'source_cad/tank_a.stp', 'cleaned': 'cleaned_geometry/tank_a.stl'},
                {'label': 'pipe_b', 'source': 'source_cad/pipe_b.stp', 'cleaned': 'cleaned_geometry/pipe_b.stl'},
                {'label': 'dike_c', 'source': 'source_cad/dike_c.stp', 'cleaned': 'cleaned_geometry/dike_c.stl'},
            ],
        },
    )
    for label in ('tank_a', 'pipe_b', 'dike_c'):
        write_text(real_root / 'source_cad' / f'{label}.stp', f'ISO-10303-21 synthetic selftest {label}\nEND-ISO-10303-21;\n')
        write_text(
            real_root / 'cleaned_geometry' / f'{label}.stl',
            f'solid {label}\n facet normal 0 0 1\n  outer loop\n   vertex 0 0 0\n   vertex 1 0 0\n   vertex 0 1 0\n  endloop\n endfacet\nendsolid {label}\n',
        )
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
                'units_declared': 'm',
                'watertight_or_closed_surface': 'true',
                'nondegenerate_elements': 'true',
                'positive_volume_or_area': 'true',
                'bbox_min_m': '0,0,0',
                'bbox_max_m': '1,1,1',
                'tool_or_method': 'synthetic-selftest',
                'reviewer': 'codex-selftest',
            }
            for label in ('tank_a', 'pipe_b', 'dike_c')
        ],
    )
    index_fields = ['file_role', 'label', 'relative_path', 'sha256', 'source_type', 'revision', 'owner_or_supplier']
    index_rows = []
    for role, subdir, ext in (
        ('source_cad', 'source_cad', 'stp'),
        ('cleaned_geometry', 'cleaned_geometry', 'stl'),
    ):
        for label in ('tank_a', 'pipe_b', 'dike_c'):
            rel = f'{subdir}/{label}.{ext}'
            index_rows.append(
                {
                    'file_role': role,
                    'label': label,
                    'relative_path': rel,
                    'sha256': sha256_file(real_root / rel),
                    'source_type': 'synthetic_selftest',
                    'revision': 'selftest-1',
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
            'source': {'type': 'synthetic_selftest'},
            'digitization': {'method': 'synthetic_selftest', 'uncertainty_m': 0.01},
        },
    )
    write_csv(
        plume_root / 'sensor_coordinates.csv',
        ['sensor_id', 'x_m', 'y_m', 'z_m', 'reliability', 'source_basis', 'digitization_uncertainty_m'],
        [
            {
                'sensor_id': f'Gas{idx:02d}',
                'x_m': 0.5 + idx * 0.1,
                'y_m': 0.0,
                'z_m': 0.25,
                'reliability': 'synthetic',
                'source_basis': 'selftest',
                'digitization_uncertainty_m': 0.01,
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
                'x_max_m': idx + 0.1,
                'y_min_m': -0.5,
                'y_max_m': 0.5,
                'z_min_m': 0.0,
                'z_max_m': 1.0,
                'source_basis': 'selftest',
                'digitization_uncertainty_m': 0.01,
            }
            for idx in range(1, 5)
        ],
    )
    ts_fields = ['time_s'] + [f'Gas{idx:02d}_vol_percent' for idx in range(1, 13)]
    write_csv(
        plume_root / 'experimental_timeseries.csv',
        ts_fields,
        [
            {'time_s': 0.0, **{f'Gas{idx:02d}_vol_percent': 0.0 for idx in range(1, 13)}},
            {'time_s': 120.0, **{f'Gas{idx:02d}_vol_percent': 0.1 * idx for idx in range(1, 13)}},
        ],
    )

    fire_root = drop_root / 'fire_consequence_calibration'
    write_json(
        fire_root / 'calibration_metadata.json',
        {
            'schema_version': 1,
            'dataset_type': 'synthetic_selftest',
            'case': 'h2_fire_gate_selftest',
            'source': {'type': 'synthetic_selftest'},
            'case_alignment': {'geometry': True, 'fuel': True, 'wind': True},
        },
    )
    write_csv(
        fire_root / 'radiation_metrics.csv',
        ['metric_id', 'distance_m', 'reference_flux_w_m2', 'tolerance_abs_w_m2', 'tolerance_rel', 'source_basis'],
        [{'metric_id': 'q001', 'distance_m': 5.0, 'reference_flux_w_m2': 2500.0, 'tolerance_abs_w_m2': 500.0, 'tolerance_rel': 0.2, 'source_basis': 'selftest'}],
    )
    write_csv(
        fire_root / 'overpressure_metrics.csv',
        ['metric_id', 'distance_m', 'reference_overpressure_kpa', 'tolerance_abs_kpa', 'tolerance_rel', 'source_basis'],
        [{'metric_id': 'p001', 'distance_m': 5.0, 'reference_overpressure_kpa': 2.5, 'tolerance_abs_kpa': 0.5, 'tolerance_rel': 0.2, 'source_basis': 'selftest'}],
    )
    write_json(
        fire_root / 'calibrated_fire_consequence_report.json',
        {'status': 'PASS-CALIBRATED-CONSEQUENCE-AGREEMENT', 'summary': {'synthetic_selftest_only': True}},
    )


def run_command(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        'command': ' '.join(argv),
        'returncode': completed.returncode,
        'output_tail': completed.stdout[-2000:],
    }


def run_checked(argv: list[str]) -> dict[str, Any]:
    record = run_command(argv)
    require(record['returncode'] == 0, f"command failed: {record['command']}\n{record['output_tail']}")
    return record


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.output_json).parent
    scratch = root / 'synthetic_fixture'
    drop_root = scratch / 'drop'
    target_root = scratch / 'controlled_targets'
    closure_path = root / 'synthetic_closure_manifest.json'
    drop_report = root / 'synthetic_drop_validator_report.json'
    drop_md = root / 'synthetic_drop_validator_report.md'
    plan_report = root / 'synthetic_ingestion_plan.json'
    plan_md = root / 'synthetic_ingestion_plan.md'
    dryrun_report = root / 'synthetic_controlled_copy_dryrun_report.json'
    dryrun_md = root / 'synthetic_controlled_copy_dryrun_report.md'
    apply_report = root / 'synthetic_controlled_copy_apply_report.json'
    apply_md = root / 'synthetic_controlled_copy_apply_report.md'

    root.mkdir(parents=True, exist_ok=True)
    if scratch.exists():
        shutil.rmtree(scratch)
    write_synthetic_drop(drop_root)
    real_closure_path = Path(args.production_blocker_closure_manifest_report)
    real_closure = load_json(real_closure_path)
    make_synthetic_closure(real_closure, target_root, closure_path)

    commands = []
    py = sys.executable
    commands.append(
        run_checked(
            [
                py,
                'tools/write_engineering_h2_external_artifact_drop_validator.py',
                '--drop-root',
                str(drop_root),
                '--production-blocker-closure-manifest-report',
                str(closure_path),
                '--allow-synthetic-selftest',
                '--output-json',
                str(drop_report),
                '--output-md',
                str(drop_md),
                '--no-ensure-scaffold',
            ]
        )
    )
    commands.append(run_checked([py, 'tools/write_engineering_h2_external_artifact_drop_validator.py', '--verify-json', str(drop_report)]))
    commands.append(
        run_checked(
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
        )
    )
    commands.append(run_checked([py, 'tools/write_engineering_h2_external_artifact_ingestion_plan.py', '--verify-json', str(plan_report)]))
    commands.append(
        run_checked(
            [
                py,
                'tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
                '--external-artifact-ingestion-plan-report',
                str(plan_report),
                '--output-json',
                str(dryrun_report),
                '--output-md',
                str(dryrun_md),
            ]
        )
    )
    commands.append(run_checked([py, 'tools/write_engineering_h2_external_artifact_controlled_copy_report.py', '--verify-json', str(dryrun_report)]))
    commands.append(
        run_checked(
            [
                py,
                'tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
                '--external-artifact-ingestion-plan-report',
                str(plan_report),
                '--output-json',
                str(apply_report),
                '--output-md',
                str(apply_md),
                '--apply',
                '--confirm-controlled-copy',
                'H2_EXTERNAL_ARTIFACTS_READY',
            ]
        )
    )
    commands.append(run_checked([py, 'tools/write_engineering_h2_external_artifact_controlled_copy_report.py', '--verify-json', str(apply_report)]))

    drop = load_json(drop_report)
    plan = load_json(plan_report)
    dryrun = load_json(dryrun_report)
    applied = load_json(apply_report)
    copied_count = int(applied.get('copied_file_count', 0))
    target_inventory = sorted(str(item) for item in target_root.rglob('*') if item.is_file())
    target_root_text = str(target_root)
    all_targets_isolated = all(str(record.get('target_path', '')).startswith(target_root_text) for record in applied.get('copy_action_records', []))
    quality_gate_matrix = [
        {
            'name': 'synthetic_drop_passes',
            'status': 'PASS' if drop.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-DROP' else 'MISSING',
            'evidence': str(drop_report),
            'gap': '',
        },
        {
            'name': 'synthetic_ingestion_plan_passes',
            'status': 'PASS' if plan.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN' else 'MISSING',
            'evidence': str(plan_report),
            'gap': '',
        },
        {
            'name': 'synthetic_controlled_copy_dryrun_no_writes',
            'status': 'PASS'
            if dryrun.get('status') == 'DRYRUN-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
            and dryrun.get('applied_copy_actions') is False
            and int(dryrun.get('copied_file_count', -1)) == 0
            else 'MISSING',
            'evidence': str(dryrun_report),
            'gap': '',
        },
        {
            'name': 'synthetic_controlled_copy_apply_is_isolated',
            'status': 'PASS'
            if applied.get('status') == 'PASS-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY'
            and applied.get('applied_copy_actions') is True
            and copied_count >= 14
            and all_targets_isolated
            else 'MISSING',
            'evidence': str(apply_report),
            'gap': '',
        },
        {
            'name': 'does_not_clear_production_blockers',
            'status': 'PASS',
            'evidence': 'synthetic self-test is excluded from production scorecard inputs',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 External Artifact Gate Synthetic Self-Test',
        'synthetic_selftest_only': True,
        'does_not_clear_production_blockers': True,
        'real_production_blocker_closure_manifest_report': str(real_closure_path),
        'synthetic_closure_manifest_report': str(closure_path),
        'synthetic_drop_root': str(drop_root),
        'synthetic_controlled_target_root': str(target_root),
        'synthetic_reports': {
            'drop_validator': str(drop_report),
            'ingestion_plan': str(plan_report),
            'controlled_copy_dryrun': str(dryrun_report),
            'controlled_copy_apply': str(apply_report),
        },
        'summary': {
            'drop_status': drop.get('status'),
            'drop_valid_artifact_count': drop.get('valid_artifact_count'),
            'drop_total_expected_artifact_count': drop.get('total_expected_artifact_count'),
            'ingestion_status': plan.get('status'),
            'ingestion_ready_copy_action_count': plan.get('ready_copy_action_count'),
            'dryrun_status': dryrun.get('status'),
            'dryrun_copied_file_count': dryrun.get('copied_file_count'),
            'apply_status': applied.get('status'),
            'apply_copied_file_count': copied_count,
            'target_file_count': len(target_inventory),
            'all_apply_targets_under_synthetic_root': all_targets_isolated,
        },
        'target_inventory_sample': target_inventory[:40],
        'command_records': commands,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('real_production_blocker_closure_manifest_report', real_closure_path),
            evidence_entry('synthetic_closure_manifest_report', closure_path),
            evidence_entry('synthetic_drop_validator_report', drop_report),
            evidence_entry('synthetic_ingestion_plan_report', plan_report),
            evidence_entry('synthetic_controlled_copy_dryrun_report', dryrun_report),
            evidence_entry('synthetic_controlled_copy_apply_report', apply_report),
        ],
        'limitations': [
            'This is synthetic gate-mechanics evidence only; it is not physical validation data.',
            'The controlled-copy apply step writes only under the synthetic self-test target root.',
            'This report must not be used to clear real-CAD, SBEPV5, or fire-calibration production blockers.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('synthetic_selftest_only') is True, 'self-test must be marked synthetic')
    require(data.get('does_not_clear_production_blockers') is True, 'self-test must not clear blockers')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('drop_status') == 'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'synthetic drop did not PASS')
    require(int(summary.get('drop_valid_artifact_count', 0)) == 14, 'synthetic drop valid count mismatch')
    require(summary.get('ingestion_status') == 'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'synthetic ingestion did not PASS')
    require(int(summary.get('ingestion_ready_copy_action_count', 0)) == 14, 'synthetic ingestion ready count mismatch')
    require(summary.get('dryrun_status') == 'DRYRUN-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY', 'synthetic dryrun did not DRYRUN')
    require(int(summary.get('dryrun_copied_file_count', -1)) == 0, 'synthetic dryrun copied files')
    require(summary.get('apply_status') == 'PASS-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY', 'synthetic apply did not PASS')
    require(int(summary.get('apply_copied_file_count', 0)) >= 14, 'synthetic apply copied too few files')
    require(summary.get('all_apply_targets_under_synthetic_root') is True, 'synthetic apply target escaped self-test root')
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
        '# Engineering H2 External Artifact Gate Synthetic Self-Test',
        '',
        f"Status: `{report['status']}`",
        f"Synthetic only: `{report['synthetic_selftest_only']}`",
        f"Does not clear production blockers: `{report['does_not_clear_production_blockers']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Synthetic Reports', '']
    for key, value in report['synthetic_reports'].items():
        lines.append(f'- `{key}`: `{value}`')
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
                'engineering_h2_external_artifact_gate_selftest VERIFY-PASS '
                f"json={args.verify_json} drop={summary['drop_valid_artifact_count']}/"
                f"{summary['drop_total_expected_artifact_count']} copied={summary['apply_copied_file_count']}"
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
            'engineering_h2_external_artifact_gate_selftest PASS '
            f"json={out_json} md={out_md} drop={summary['drop_valid_artifact_count']}/"
            f"{summary['drop_total_expected_artifact_count']} copied={summary['apply_copied_file_count']}"
        )
        return 0
    except GateSelftestError as exc:
        print(f'engineering_h2_external_artifact_gate_selftest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
