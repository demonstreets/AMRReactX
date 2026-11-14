#!/usr/bin/env python3
"""Write and verify an engineering H2 acceptance matrix from local evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

DEFAULT_RELEASE_PACK = Path(
    'docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json'
)
DEFAULT_PRODUCTION_MESH_1200 = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_8RANK = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_16RANK = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_8RANK_600STEP = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json'
)
DEFAULT_IGNITION = Path(
    'docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json'
)
DEFAULT_FIRE = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json'
)
DEFAULT_SCHEDULER = Path(
    'docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json'
)

REQUIRED_CASES = {
    'dispersion_core': {'open-domain', 'release-rate', 'crosswind', 'low-wind'},
    'source_physics': {
        'pressure-orifice', 'real-gas-orifice', 'tank-blowdown', 'real-gas-tank-blowdown',
        'pipe-loss', 'linepack-blowdown', 'linepack-valve-schedule',
    },
    'geometry_obstacles': {'tank-farm', 'stl-multifile', 'stl-perfile-transform'},
    'amr_mpi': {'plan-amr-mpi-rank-sweep', 'plan-amr-mpi-reduced-long'},
}

class MatrixError(RuntimeError):
    pass


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
        raise MatrixError(f'missing evidence file: {path}') from exc
    except json.JSONDecodeError as exc:
        raise MatrixError(f'invalid JSON in {path}: {exc}') from exc
    if not isinstance(data, dict):
        raise MatrixError(f'evidence JSON is not an object: {path}')
    return data


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def release_case_index(release: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = release.get('cases')
    if not isinstance(cases, list):
        raise MatrixError('release pack cases is not a list')
    index: dict[str, dict[str, Any]] = {}
    for item in cases:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name', ''))
        if name:
            index[name] = item
    return index


def case_ok(case: dict[str, Any] | None) -> bool:
    if not case:
        return False
    files = case.get('required_files')
    return case.get('status') == 'PASS' and isinstance(files, list) and bool(files)


def group_row(name: str, title: str, required: set[str], case_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    passed = sorted(case for case in required if case_ok(case_index.get(case)))
    missing = sorted(required - set(passed))
    status = 'PASS-SMOKE' if not missing else 'NOT_READY'
    return {
        'name': name,
        'title': title,
        'status': status,
        'required_cases': sorted(required),
        'passed_cases': passed,
        'missing_or_failed_cases': missing,
        'evidence_level': 'smoke_campaign',
        'production_gaps': [
            'smoke-scale internal campaign only; external reference-data agreement and production-size case matrix remain open'
        ] if status == 'PASS-SMOKE' else ['required smoke campaign cases missing or failed'],
    }


def production_mesh_row(
    report: dict[str, Any],
    report8: dict[str, Any],
    report16: dict[str, Any],
    report8long: dict[str, Any],
) -> dict[str, Any]:
    s = report.get('summary') if isinstance(report.get('summary'), dict) else {}
    s8 = report8.get('summary') if isinstance(report8.get('summary'), dict) else {}
    s16 = report16.get('summary') if isinstance(report16.get('summary'), dict) else {}
    s8long = report8long.get('summary') if isinstance(report8long.get('summary'), dict) else {}
    rank8_stability_ok = (
        report8long.get('status') in {'PASS-STABILITY', 'PASS-SCOUT'}
        and '8rank' in str(report8long.get('case', ''))
        and '600step' in str(report8long.get('case', ''))
        and int(s8long.get('ranks', 0)) >= 8
        and int(s8long.get('max_step', 0)) >= 600
        and int(s8long.get('baseline_plotfiles', 0)) >= 11
        and int(s8long.get('amr_plotfiles', 0)) >= 11
        and finite(s8long.get('cloud_rel_diff')) and float(s8long.get('cloud_rel_diff')) <= 0.25
        and finite(s8long.get('peak_rel_diff')) and float(s8long.get('peak_rel_diff')) <= 0.25
    )
    rank16_scout_ok = (
        report16.get('status') == 'PASS-SCOUT'
        and '16rank' in str(report16.get('case', ''))
        and int(s16.get('ranks', 0)) >= 16
        and int(s16.get('max_step', 0)) >= 120
        and int(s16.get('baseline_plotfiles', 0)) >= 5
        and int(s16.get('amr_plotfiles', 0)) >= 5
        and finite(s16.get('cloud_rel_diff')) and float(s16.get('cloud_rel_diff')) <= 0.20
        and finite(s16.get('peak_rel_diff')) and float(s16.get('peak_rel_diff')) <= 0.20
        and finite(s16.get('advance_seconds_ratio')) and float(s16.get('advance_seconds_ratio')) <= 4.0
    )
    ok = (
        report.get('status') in {'PASS-STABILITY', 'PASS-SCOUT'}
        and '1200step' in str(report.get('case', ''))
        and int(s.get('ranks', 0)) >= 4
        and int(s.get('max_step', 0)) >= 1200
        and int(s.get('base_cell_count', 0)) >= 60000
        and int(s.get('amr_equivalent_fine_cell_count', 0)) >= 500000
        and int(s.get('baseline_plotfiles', 0)) >= 11
        and int(s.get('amr_plotfiles', 0)) >= 11
        and finite(s.get('cloud_rel_diff')) and float(s.get('cloud_rel_diff')) <= 0.25
        and finite(s.get('peak_rel_diff')) and float(s.get('peak_rel_diff')) <= 0.25
        and finite(s.get('advance_seconds_ratio')) and float(s.get('advance_seconds_ratio')) <= 25.0
        and report8.get('status') == 'PASS-SCOUT'
        and int(s8.get('ranks', 0)) >= 8
        and rank8_stability_ok
        and rank16_scout_ok
    )
    return {
        'name': 'production_mesh_amr_mpi_stability',
        'title': 'Production-mesh AMR/MPI stability scout',
        'status': 'PASS-SCOUT' if ok else 'NOT_READY',
        'evidence_level': 'production_mesh_scout',
        'metrics': {
            'ranks': s.get('ranks'),
            'max_step': s.get('max_step'),
            'base_cell_count': s.get('base_cell_count'),
            'amr_equivalent_fine_cell_count': s.get('amr_equivalent_fine_cell_count'),
            'cloud_rel_diff': s.get('cloud_rel_diff'),
            'peak_rel_diff': s.get('peak_rel_diff'),
            'advance_seconds_ratio': s.get('advance_seconds_ratio'),
            'rank_scaling_scout_ranks': s8.get('ranks'),
            'rank16_scout_ranks': s16.get('ranks'),
            'rank16_scout_advance_seconds_ratio': s16.get('advance_seconds_ratio'),
            'rank8_stability_max_step': s8long.get('max_step'),
            'rank8_stability_advance_seconds_ratio': s8long.get('advance_seconds_ratio'),
        },
        'production_gaps': [
            '1200-step production-mesh, 8-rank/600-step stability, and 16-rank short scouts exist; scheduler-managed overnight/full-duration production campaigns remain open'
        ] if ok else ['production-mesh 1200-step, 8-rank/600-step stability, or 16-rank scout evidence missing or outside bounds'],
    }


def fire_row(ignition: dict[str, Any], fire: dict[str, Any]) -> dict[str, Any]:
    isum = ignition.get('summary') if isinstance(ignition.get('summary'), dict) else {}
    fsum = fire.get('summary') if isinstance(fire.get('summary'), dict) else {}
    ok = (
        ignition.get('status') == 'PASS-SMOKE'
        and fire.get('status') == 'PASS-SCREENING'
        and finite(isum.get('delay_fine_ignition_time_s'))
        and finite(fsum.get('max_screening_flux_w_m2'))
        and finite(fsum.get('max_screening_overpressure_kpa'))
        and float(fsum.get('max_screening_flux_w_m2')) > 0.0
        and float(fsum.get('max_screening_overpressure_kpa')) > 0.0
    )
    return {
        'name': 'ignition_fire_consequence_screening',
        'title': 'Ignition and fire consequence screening',
        'status': 'PASS-SCREENING' if ok else 'NOT_READY',
        'evidence_level': 'screening_not_calibrated',
        'metrics': {
            'delay_fine_ignition_time_s': isum.get('delay_fine_ignition_time_s'),
            'max_screening_flux_w_m2': fsum.get('max_screening_flux_w_m2'),
            'max_screening_overpressure_kpa': fsum.get('max_screening_overpressure_kpa'),
        },
        'production_gaps': [
            'screening consequence metrics exist; calibrated radiation, overpressure, flame-speed, and reference fire validation remain open'
        ] if ok else ['ignition/fire screening evidence missing or nonpositive'],
    }


def scheduler_row(scheduler: dict[str, Any]) -> dict[str, Any]:
    status = scheduler.get('status')
    ok = status == 'PASS'
    return {
        'name': 'scheduler_managed_campaign',
        'title': 'Scheduler-managed production campaign handoff',
        'status': 'PASS' if ok else 'NOT_READY',
        'evidence_level': 'scheduler_allocation' if ok else 'diagnostic_only',
        'metrics': {
            'scheduler_report_status': status,
            'submit_attempt_status': scheduler.get('submit_attempt', {}).get('status') if isinstance(scheduler.get('submit_attempt'), dict) else None,
        },
        'production_gaps': [] if ok else ['no scheduler-managed PASS run outputs; current scheduler evidence remains diagnostic only'],
    }


def build_matrix(args: argparse.Namespace) -> dict[str, Any]:
    release_path = Path(args.release_pack)
    mesh_path = Path(args.production_mesh_1200_report)
    mesh8_path = Path(args.production_mesh_8rank_report)
    mesh16_path = Path(args.production_mesh_16rank_report)
    mesh8long_path = Path(args.production_mesh_8rank_600step_report)
    ignition_path = Path(args.ignition_report)
    fire_path = Path(args.fire_report)
    scheduler_path = Path(args.scheduler_report)

    release = load_json(release_path)
    mesh = load_json(mesh_path)
    mesh8 = load_json(mesh8_path)
    mesh16 = load_json(mesh16_path)
    mesh8long = load_json(mesh8long_path)
    ignition = load_json(ignition_path)
    fire = load_json(fire_path)
    scheduler = load_json(scheduler_path)

    if release.get('status') != 'PASS':
        raise MatrixError('release pack status is not PASS')
    case_index = release_case_index(release)

    rows = [
        group_row('dispersion_core', 'Open-domain dispersion, wind, and release-rate response', REQUIRED_CASES['dispersion_core'], case_index),
        group_row('source_physics', 'Tank/pipe/orifice/linepack source physics', REQUIRED_CASES['source_physics'], case_index),
        group_row('geometry_obstacles', 'Tank-farm and STL obstacle geometry', REQUIRED_CASES['geometry_obstacles'], case_index),
        group_row('amr_mpi_smoke', 'Dynamic AMR and MPI smoke campaign', REQUIRED_CASES['amr_mpi'], case_index),
        production_mesh_row(mesh, mesh8, mesh16, mesh8long),
        fire_row(ignition, fire),
        scheduler_row(scheduler),
    ]
    not_ready = [row['name'] for row in rows if row['status'] == 'NOT_READY']
    status = 'PARTIAL-PRODUCTION' if not_ready else 'PASS-PRODUCTION-MATRIX'
    production_blockers = sorted({gap for row in rows for gap in row.get('production_gaps', []) if gap})
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'scope': 'engineering H2 storage/pipeline leak dispersion, ignition, and fire screening acceptance matrix',
        'rows': rows,
        'summary': {
            'row_count': len(rows),
            'pass_like_rows': len(rows) - len(not_ready),
            'not_ready_rows': not_ready,
            'campaign_case_count': release.get('case_count'),
            'campaign_suite_count': release.get('suite_count'),
        },
        'evidence_files': [
            evidence_entry('release_pack', release_path),
            evidence_entry('production_mesh_1200step_stability_scout_report', mesh_path),
            evidence_entry('production_mesh_8rank_scout_report', mesh8_path),
            evidence_entry('production_mesh_16rank_scout_report', mesh16_path),
            evidence_entry('production_mesh_8rank_600step_stability_scout_report', mesh8long_path),
            evidence_entry('ignition_consequence_report', ignition_path),
            evidence_entry('fire_consequence_metrics_report', fire_path),
            evidence_entry('scheduler_run_report', scheduler_path),
        ],
        'production_blockers': production_blockers,
        'limitations': [
            'This matrix is an internal engineering acceptance ledger, not an external safety certification.',
            'PASS smoke/screening/scout rows do not prove external reference-data agreement or calibrated consequence prediction.',
        ],
    }


def write_markdown(matrix: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Acceptance Matrix',
        '',
        f"Status: `{matrix['status']}`",
        '',
        '## Summary',
        '',
        f"- Rows: `{matrix['summary']['row_count']}`",
        f"- Pass-like rows: `{matrix['summary']['pass_like_rows']}`",
        f"- Not-ready rows: `{matrix['summary']['not_ready_rows']}`",
        '',
        '## Matrix',
        '',
        '| Row | Status | Evidence level | Main gaps |',
        '| --- | --- | --- | --- |',
    ]
    for row in matrix['rows']:
        gaps = '; '.join(row.get('production_gaps', [])) or 'none recorded'
        lines.append(f"| `{row['name']}` | `{row['status']}` | `{row.get('evidence_level', '')}` | {gaps} |")
    lines += ['', '## Evidence Files', '']
    for item in matrix['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify_matrix(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if data.get('schema_version') != SCHEMA_VERSION:
        raise MatrixError('schema version mismatch')
    if data.get('status') not in {'PARTIAL-PRODUCTION', 'PASS-PRODUCTION-MATRIX'}:
        raise MatrixError(f'unexpected status {data.get("status")}')
    rows = data.get('rows')
    if not isinstance(rows, list) or len(rows) < 7:
        raise MatrixError('matrix rows missing')
    names = {row.get('name') for row in rows if isinstance(row, dict)}
    required_names = {
        'dispersion_core', 'source_physics', 'geometry_obstacles', 'amr_mpi_smoke',
        'production_mesh_amr_mpi_stability', 'ignition_fire_consequence_screening',
        'scheduler_managed_campaign',
    }
    if not required_names <= names:
        raise MatrixError('matrix required rows missing')
    for item in data.get('evidence_files', []):
        p = Path(item.get('path', ''))
        if not p.is_file():
            raise MatrixError(f'missing evidence file: {p}')
        if sha256_file(p) != item.get('sha256'):
            raise MatrixError(f'evidence hash mismatch: {p}')
    summary = data.get('summary', {})
    if summary.get('row_count') != len(rows):
        raise MatrixError('row_count mismatch')
    if data.get('status') == 'PASS-PRODUCTION-MATRIX' and summary.get('not_ready_rows'):
        raise MatrixError('PASS matrix cannot retain not-ready rows')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release-pack', default=str(DEFAULT_RELEASE_PACK))
    ap.add_argument('--production-mesh-1200-report', default=str(DEFAULT_PRODUCTION_MESH_1200))
    ap.add_argument('--production-mesh-8rank-report', default=str(DEFAULT_PRODUCTION_MESH_8RANK))
    ap.add_argument('--production-mesh-16rank-report', default=str(DEFAULT_PRODUCTION_MESH_16RANK))
    ap.add_argument('--production-mesh-8rank-600step-report', default=str(DEFAULT_PRODUCTION_MESH_8RANK_600STEP))
    ap.add_argument('--ignition-report', default=str(DEFAULT_IGNITION))
    ap.add_argument('--fire-report', default=str(DEFAULT_FIRE))
    ap.add_argument('--scheduler-report', default=str(DEFAULT_SCHEDULER))
    ap.add_argument('--output-json')
    ap.add_argument('--output-md')
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)
    try:
        if args.verify_json:
            data = verify_matrix(Path(args.verify_json))
            print(
                'engineering_h2_acceptance_matrix VERIFY-PASS ' +
                f"json={args.verify_json} status={data['status']} " +
                f"pass_like_rows={data['summary']['pass_like_rows']} " +
                f"not_ready_rows={len(data['summary']['not_ready_rows'])}"
            )
            return 0
        if not args.output_json or not args.output_md:
            raise MatrixError('--output-json and --output-md are required unless --verify-json is used')
        matrix = build_matrix(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(matrix, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(matrix, out_md)
        print(
            'engineering_h2_acceptance_matrix PASS ' +
            f"json={out_json} md={out_md} status={matrix['status']} " +
            f"pass_like_rows={matrix['summary']['pass_like_rows']} " +
            f"not_ready_rows={len(matrix['summary']['not_ready_rows'])}"
        )
        return 0
    except (MatrixError, OSError, ValueError, KeyError) as exc:
        print(f'engineering_h2_acceptance_matrix FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
