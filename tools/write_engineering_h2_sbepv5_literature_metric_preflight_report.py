#!/usr/bin/env python3
"""Write/verify SBEPV5 D27 literature metric preflight evidence.

This report records response metrics that can be extracted from public paper text.
It intentionally does not clear the external plume-shape blocker; the production
gate still requires local experimental coordinates and time-series data.
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
STATUS = 'PASS-SBEPV5-D27-LITERATURE-METRIC-PREFLIGHT'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_sbepv5_d27_literature_metric_preflight_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'sbepv5_d27_literature_metric_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'sbepv5_d27_literature_metric_preflight_report.md'
DEFAULT_PUBLIC_SOURCE_TRIAGE_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/'
    'external_plume_public_source_triage_report.json'
)
DEFAULT_DIGITIZATION_PREFLIGHT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724/'
    'sbepv5_d27_digitization_preflight_report.json'
)

REQUIRED_RESPONSE_SENSORS = (9, 10)


class LiteratureMetricPreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LiteratureMetricPreflightError(message)


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
        raise LiteratureMetricPreflightError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise LiteratureMetricPreflightError(f'invalid JSON evidence {path}: {exc}') from exc
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


def source_ids(data: dict[str, Any]) -> set[str]:
    sources = data.get('sources')
    if not isinstance(sources, list):
        return set()
    return {str(item.get('id')) for item in sources if isinstance(item, dict)}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    public_source_path = Path(args.public_source_triage_report)
    digitization_path = Path(args.digitization_preflight_report)
    public_source = load_json(public_source_path)
    digitization = load_json(digitization_path)
    ids = source_ids(public_source)
    public_source_ready = (
        public_source.get('status') == 'PASS-H2-EXTERNAL-PLUME-PUBLIC-SOURCE-TRIAGE'
        and public_source.get('benchmark_id') == 'hysafe_sbepv5_d27'
        and {'kitopen_230068969', 'researchgate_311396790'}.issubset(ids)
    )
    digitization_ready = (
        digitization.get('status') == 'PASS-SBEPV5-D27-DIGITIZATION-PREFLIGHT'
        and digitization.get('benchmark_id') == 'hysafe_sbepv5_d27'
    )

    metric_anchors = [
        {
            'metric_id': 'gas09_time_to_15pct_h2_s',
            'sensor_id': 9,
            'quantity': 'time when concentration reaches 15 vol% H2',
            'reported_interval_s': [16.0, 19.0],
            'source_ids': ['researchgate_311396790'],
            'use_in_future_agreement': 'arrival-time sanity bound after local experimental time series is ingested',
        },
        {
            'metric_id': 'gas10_time_to_15pct_h2_s',
            'sensor_id': 10,
            'quantity': 'time when concentration reaches 15 vol% H2',
            'reported_interval_s': [17.0, 20.0],
            'source_ids': ['researchgate_311396790'],
            'use_in_future_agreement': 'arrival-time sanity bound after local experimental time series is ingested',
        },
        {
            'metric_id': 'gas12_late_rise_qualitative',
            'sensor_id': 12,
            'quantity': 'relative concentration rise timing',
            'reported_relation': 'Gas12 begins to rise much later than Gas09 and Gas10',
            'source_ids': ['researchgate_311396790'],
            'use_in_future_agreement': 'qualitative ordering check for baffled-compartment filling',
        },
        {
            'metric_id': 'gas09_gas10_sensitive_buoyant_jet_region',
            'sensor_ids': [9, 10],
            'quantity': 'sensitive response region for buoyant jet/baffle interaction',
            'reported_relation': 'Gas09 and Gas10 are the most sensitive positions for the baffle-split buoyant jet',
            'source_ids': ['researchgate_311396790'],
            'use_in_future_agreement': 'priority sensor subset for plume-shape acceptance tolerances',
        },
    ]
    quality_gate_matrix = [
        {
            'name': 'public_source_triage_ready',
            'status': 'PASS' if public_source_ready else 'MISSING',
            'evidence': str(public_source_path) if public_source_ready else '',
            'gap': '' if public_source_ready else 'Public-source triage report must PASS and include KITopen/ResearchGate anchors.',
        },
        {
            'name': 'digitization_preflight_ready',
            'status': 'PASS' if digitization_ready else 'MISSING',
            'evidence': str(digitization_path) if digitization_ready else '',
            'gap': '' if digitization_ready else 'Digitization preflight report must PASS.',
        },
        {
            'name': 'gas09_arrival_metric_available',
            'status': 'PASS',
            'evidence': 'reported interval 16-19 s to 15 vol% H2',
            'gap': '',
        },
        {
            'name': 'gas10_arrival_metric_available',
            'status': 'PASS',
            'evidence': 'reported interval 17-20 s to 15 vol% H2',
            'gap': '',
        },
        {
            'name': 'full_timeseries_still_missing',
            'status': 'MISSING',
            'evidence': '',
            'gap': 'Original Excel or accepted digitized Gas01..Gas12 concentration time series is still required.',
        },
    ]
    missing_artifacts = [
        {
            'artifact': 'experimental_timeseries.csv',
            'required_action': 'ingest original Excel or reviewed digitized curves for Gas01..Gas12 through at least 120 s',
        },
        {
            'artifact': 'literature_metric_acceptance_overlay.json',
            'required_action': 'after program sensor probes exist, compare Gas09/Gas10 arrival-time metrics to reported intervals',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'benchmark_id': 'hysafe_sbepv5_d27',
        'title': 'HySafe SBEPV5 D27 Literature Metric Preflight',
        'clears_reference_data_blocker': False,
        'ready_for_reference_agreement_consumption': False,
        'metric_anchor_count': len(metric_anchors),
        'metric_anchors': metric_anchors,
        'quality_gate_matrix': quality_gate_matrix,
        'missing_artifacts': missing_artifacts,
        'summary': {
            'public_source_triage_ready': public_source_ready,
            'digitization_preflight_ready': digitization_ready,
            'literature_metric_anchor_available': True,
            'gas09_arrival_interval_s': [16.0, 19.0],
            'gas10_arrival_interval_s': [17.0, 20.0],
            'required_response_sensor_ids': list(REQUIRED_RESPONSE_SENSORS),
            'ready_for_reference_agreement_consumption': False,
            'missing_artifact_count': len(missing_artifacts),
        },
        'evidence_files': [
            evidence_entry('external_plume_public_source_triage_report', public_source_path),
            evidence_entry('sbepv5_digitization_preflight_report', digitization_path),
        ],
        'limitations': [
            'The metric anchors are literature-level checks, not a replacement for local experimental time series.',
            'This report cannot clear the external plume-shape blocker without ingested coordinates, baffle geometry, and sensor histories.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('benchmark_id') == 'hysafe_sbepv5_d27', 'benchmark_id mismatch')
    require(data.get('clears_reference_data_blocker') is False, 'literature preflight cannot clear blocker')
    require(data.get('ready_for_reference_agreement_consumption') is False, 'literature preflight cannot be consumption-ready')
    metrics = data.get('metric_anchors')
    require(isinstance(metrics, list) and len(metrics) >= 4, 'metric anchors incomplete')
    metric_ids = {str(item.get('metric_id')) for item in metrics if isinstance(item, dict)}
    require('gas09_time_to_15pct_h2_s' in metric_ids, 'Gas09 metric missing')
    require('gas10_time_to_15pct_h2_s' in metric_ids, 'Gas10 metric missing')
    for sensor_id in REQUIRED_RESPONSE_SENSORS:
        matching = [item for item in metrics if isinstance(item, dict) and item.get('sensor_id') == sensor_id]
        require(matching, f'missing metric for sensor {sensor_id}')
        interval = matching[0].get('reported_interval_s')
        require(isinstance(interval, list) and len(interval) == 2, f'invalid interval for sensor {sensor_id}')
        require(float(interval[0]) < float(interval[1]), f'bad interval order for sensor {sensor_id}')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('public_source_triage_ready') is True, 'public-source triage not ready')
    require(summary.get('digitization_preflight_ready') is True, 'digitization preflight not ready')
    require(summary.get('literature_metric_anchor_available') is True, 'metric anchors unavailable')
    require(summary.get('ready_for_reference_agreement_consumption') is False, 'summary cannot be reference-consumption ready')
    require(int(summary.get('missing_artifact_count', 0)) >= 1, 'missing artifact count too small')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality gate matrix missing')
    missing = [item for item in matrix if isinstance(item, dict) and item.get('status') == 'MISSING']
    require(missing, 'literature metric preflight must retain missing gates')
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
        '# HySafe SBEPV5 D27 Literature Metric Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Clears reference-data blocker: `{report['clears_reference_data_blocker']}`",
        f"Ready for reference agreement consumption: `{report['ready_for_reference_agreement_consumption']}`",
        '',
        '## Metric Anchors',
        '',
    ]
    for item in report['metric_anchors']:
        lines.append(f"- `{item['metric_id']}`: `{item.get('reported_interval_s', item.get('reported_relation'))}`")
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
                'engineering_h2_sbepv5_literature_metric_preflight VERIFY-PASS '
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
            'engineering_h2_sbepv5_literature_metric_preflight PASS '
            f"json={out_json} md={out_md} metrics={report['metric_anchor_count']} "
            f"missing={report['summary']['missing_artifact_count']}"
        )
        return 0
    except LiteratureMetricPreflightError as exc:
        print(f'engineering_h2_sbepv5_literature_metric_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
