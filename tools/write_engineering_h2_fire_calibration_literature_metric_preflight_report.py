#!/usr/bin/env python3
"""Write/verify H2 fire calibration literature metric preflight evidence.

This report records public literature anchors for radiation and overpressure
calibration. It is deliberately not a production-clearance artifact; final
credit still requires local radiation/overpressure metric CSVs and the official
calibrated consequence report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'fire_calibration_literature_metric_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'fire_calibration_literature_metric_preflight_report.md'
DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/'
    'fire_calibration_public_source_triage_report.json'
)
DEFAULT_DIGITIZATION_PREFLIGHT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/'
    'fire_calibration_digitization_preflight_report.json'
)


class FireLiteratureMetricPreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FireLiteratureMetricPreflightError(message)


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
        raise FireLiteratureMetricPreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise FireLiteratureMetricPreflightError(f'invalid JSON evidence {path}: {exc}') from exc
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


def source_ids(items: Any) -> set[str]:
    if not isinstance(items, list):
        return set()
    return {str(item.get('id')) for item in items if isinstance(item, dict)}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    public_source_path = Path(args.public_source_triage_report)
    digitization_path = Path(args.digitization_preflight_report)
    public_source = load_json(public_source_path)
    digitization = load_json(digitization_path)
    triage_summary = public_source.get('summary') if isinstance(public_source.get('summary'), dict) else {}
    digitization_summary = digitization.get('summary') if isinstance(digitization.get('summary'), dict) else {}
    radiation_ids = source_ids(public_source.get('radiation_candidates'))
    overpressure_ids = source_ids(public_source.get('overpressure_candidates'))
    public_source_ready = (
        public_source.get('status') == 'PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE'
        and triage_summary.get('radiation_candidate_available') is True
        and triage_summary.get('overpressure_candidate_available') is True
        and 'mdpi_jet_fire_2024' in radiation_ids
        and 'hyindoor_low_strength_enclosure_2017' in overpressure_ids
    )
    digitization_ready = (
        digitization.get('status') == 'PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT'
        and digitization_summary.get('templates_available') is True
    )

    metric_anchors = [
        {
            'metric_id': 'mdpi_jet_fire_radiometer_layout',
            'family': 'radiation',
            'source_id': 'mdpi_jet_fire_2024',
            'quantity': 'radiometer placement for hydrogen jet-fire heat flux',
            'values': {
                'flame_axis_heights_m': [0.25, 0.50, 0.75, 1.00],
                'radial_distances_m': [0.23, 0.50],
                'leak_diameters_mm': [1.2, 1.5, 2.0],
            },
            'use_in_future_agreement': 'build radiation_metrics.csv rows with distance/height/source-basis columns',
        },
        {
            'metric_id': 'mdpi_jet_fire_reference_flux_bounds',
            'family': 'radiation',
            'source_id': 'mdpi_jet_fire_2024',
            'quantity': 'published heat-flux examples for jet-fire radiation scale',
            'values': {
                'max_flux_w_m2_at_0p23m_1p2mm': 952.8,
                'max_flux_w_m2_at_0p23m_2p0mm': 3378.1,
                'flux_w_m2_1p5mm_0p6mpa_0p23m': 1360.5,
                'flux_w_m2_1p5mm_0p6mpa_0p50m': 412.1,
            },
            'use_in_future_agreement': 'set heat-flux sanity bounds before full table digitization',
        },
        {
            'metric_id': 'mdpi_jet_fire_model_error_anchor',
            'family': 'radiation',
            'source_id': 'mdpi_jet_fire_2024',
            'quantity': 'reported optimized multi-point source model error',
            'values': {'average_error_percent': 13.9, 'max_error_percent': 21.7},
            'use_in_future_agreement': 'initial radiation tolerance floor until experiment-specific uncertainty is ingested',
        },
        {
            'metric_id': 'hyindoor_overpressure_scale_anchor',
            'family': 'overpressure',
            'source_id': 'hyindoor_low_strength_enclosure_2017',
            'quantity': 'vented hydrogen deflagration enclosure and target pressure scale',
            'values': {
                'enclosure_volume_m3': 31.0,
                'maximum_internal_overpressure_target_kpa': 10.0,
                'maximum_h2_concentration_vv_percent': 14.0,
            },
            'use_in_future_agreement': 'seed overpressure_metrics.csv scale checks for low-strength enclosure cases',
        },
    ]
    quality_gate_matrix = [
        {
            'name': 'public_source_triage_ready',
            'status': 'PASS' if public_source_ready else 'MISSING',
            'evidence': str(public_source_path) if public_source_ready else '',
            'gap': '' if public_source_ready else 'Public-source triage must include radiation and overpressure source candidates.',
        },
        {
            'name': 'digitization_preflight_ready',
            'status': 'PASS' if digitization_ready else 'MISSING',
            'evidence': str(digitization_path) if digitization_ready else '',
            'gap': '' if digitization_ready else 'Fire calibration digitization preflight must PASS.',
        },
        {
            'name': 'radiation_metric_anchor_available',
            'status': 'PASS',
            'evidence': 'MDPI jet-fire radiometer layout and heat-flux examples recorded',
            'gap': '',
        },
        {
            'name': 'overpressure_metric_anchor_available',
            'status': 'PASS',
            'evidence': 'HyIndoor low-strength enclosure overpressure scale recorded',
            'gap': '',
        },
        {
            'name': 'local_metric_csvs_still_missing',
            'status': 'MISSING',
            'evidence': '',
            'gap': 'Local radiation_metrics.csv and overpressure_metrics.csv are still required for calibration ingestion.',
        },
    ]
    missing_artifacts = [
        {
            'artifact': 'radiation_metrics.csv',
            'required_action': 'digitize or obtain heat-flux rows with distance, tolerance, and source basis',
        },
        {
            'artifact': 'overpressure_metrics.csv',
            'required_action': 'digitize or obtain overpressure rows with gauge location, tolerance, and source basis',
        },
        {
            'artifact': 'fire_calibration_acceptance_overlay.json',
            'required_action': 'after calibrated consequence output exists, compare radiation/overpressure predictions to metric anchors',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Fire Calibration Literature Metric Preflight',
        'clears_fire_consequence_blocker': False,
        'ready_for_dataset_ingestion': False,
        'metric_anchor_count': len(metric_anchors),
        'metric_anchors': metric_anchors,
        'quality_gate_matrix': quality_gate_matrix,
        'missing_artifacts': missing_artifacts,
        'summary': {
            'public_source_triage_ready': public_source_ready,
            'digitization_preflight_ready': digitization_ready,
            'radiation_metric_anchor_available': True,
            'overpressure_metric_anchor_available': True,
            'radiation_anchor_count': len([item for item in metric_anchors if item['family'] == 'radiation']),
            'overpressure_anchor_count': len([item for item in metric_anchors if item['family'] == 'overpressure']),
            'ready_for_dataset_ingestion': False,
            'missing_artifact_count': len(missing_artifacts),
        },
        'evidence_files': [
            evidence_entry('fire_calibration_public_source_triage_report', public_source_path),
            evidence_entry('fire_calibration_digitization_preflight_report', digitization_path),
        ],
        'limitations': [
            'The metric anchors are public-literature intake checks, not calibrated consequence agreement.',
            'The fire-consequence blocker remains until local radiation/overpressure data are ingested and the official calibrated consequence report passes.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('clears_fire_consequence_blocker') is False, 'literature preflight cannot clear blocker')
    require(data.get('ready_for_dataset_ingestion') is False, 'literature preflight cannot be ingestion-ready')
    metrics = data.get('metric_anchors')
    require(isinstance(metrics, list) and len(metrics) >= 4, 'metric anchors incomplete')
    families = {str(item.get('family')) for item in metrics if isinstance(item, dict)}
    require({'radiation', 'overpressure'}.issubset(families), 'both radiation and overpressure anchors required')
    ids = {str(item.get('metric_id')) for item in metrics if isinstance(item, dict)}
    for required in (
        'mdpi_jet_fire_radiometer_layout',
        'mdpi_jet_fire_reference_flux_bounds',
        'hyindoor_overpressure_scale_anchor',
    ):
        require(required in ids, f'missing metric anchor: {required}')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('public_source_triage_ready') is True, 'public-source triage not ready')
    require(summary.get('digitization_preflight_ready') is True, 'digitization preflight not ready')
    require(summary.get('radiation_metric_anchor_available') is True, 'radiation anchors missing')
    require(summary.get('overpressure_metric_anchor_available') is True, 'overpressure anchors missing')
    require(int(summary.get('missing_artifact_count', 0)) >= 1, 'missing artifact count too small')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality gate matrix missing')
    missing = [item for item in matrix if isinstance(item, dict) and item.get('status') == 'MISSING']
    require(missing, 'literature preflight must retain missing gates')
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
        '# Engineering H2 Fire Calibration Literature Metric Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Clears fire-consequence blocker: `{report['clears_fire_consequence_blocker']}`",
        f"Ready for dataset ingestion: `{report['ready_for_dataset_ingestion']}`",
        '',
        '## Metric Anchors',
        '',
    ]
    for item in report['metric_anchors']:
        lines.append(f"- `{item['metric_id']}` ({item['family']}): `{item['values']}`")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['gap'] or item['evidence']} |")
    lines += ['', '## Missing Artifacts', '']
    for item in report['missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-source-triage-report', default=str(DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT))
    parser.add_argument('--digitization-preflight-report', default=str(DEFAULT_DIGITIZATION_PREFLIGHT_REPORT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report_object(report, check_hashes=True)
            print(
                'engineering_h2_fire_calibration_literature_metric_preflight VERIFY-PASS '
                f"json={args.verify_json} metrics={report['metric_anchor_count']} "
                f"missing={report['summary']['missing_artifact_count']}"
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
            'engineering_h2_fire_calibration_literature_metric_preflight PASS '
            f"json={out_json} md={out_md} metrics={report['metric_anchor_count']} "
            f"missing={report['summary']['missing_artifact_count']}"
        )
        return 0
    except FireLiteratureMetricPreflightError as exc:
        print(f'engineering_h2_fire_calibration_literature_metric_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
