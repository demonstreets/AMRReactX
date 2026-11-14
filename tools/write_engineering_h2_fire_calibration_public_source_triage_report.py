#!/usr/bin/env python3
"""Write/verify public-source triage for H2 fire radiation and overpressure calibration."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'fire_calibration_public_source_triage_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'fire_calibration_public_source_triage_report.md'


class FireSourceTriageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FireSourceTriageError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise FireSourceTriageError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise FireSourceTriageError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    radiation_candidates = [
        {
            'id': 'mdpi_jet_fire_2024',
            'title': 'Study on Thermal Radiation Characteristics and the Multi-Point Source Model of Hydrogen Jet Fire',
            'url': 'https://www.mdpi.com/2076-3417/14/16/7098',
            'source_type': 'field_test_or_laboratory_jet_fire',
            'usable_measurements': [
                'four radiometers along flame axial direction',
                'radial distances 0.23 m and 0.50 m from flame axis',
                'longitudinal radiometer positions 0.25 m, 0.50 m, 0.75 m, 1.00 m',
                'leak diameter and pressure sensitivity',
            ],
            'required_digitization': [
                'case-specific pressure/leak diameter/mass-flow table',
                'radiometer heat-flux time average or peak values',
                'instrument uncertainty and averaging window',
            ],
        },
        {
            'id': 'sandia_cryogenic_h2_jet_fire_2019',
            'title': 'Thermal radiation from cryogenic hydrogen jet fires',
            'url': 'https://doi.org/10.1016/j.ijhydene.2018.08.107',
            'source_type': 'cryogenic_field_test_literature',
            'usable_measurements': [
                'Sandia cryogenic hydrogen fire data used for CFD validation',
                'radiative heat flux at different locations',
                'flame length comparison',
                'storage pressure up to 5 bar abs and 48-82 K release temperature range',
            ],
            'required_digitization': [
                'local numeric heat-flux table or accepted figure digitization',
                'release condition table including humidity/extraction-system assumptions',
                'flame length table for geometry cross-check',
            ],
        },
        {
            'id': 'bam_large_scale_h2_jet_flames_2025',
            'title': 'Thermal Radiation Of Inclined Large Scale Hydrogen Jet Flames',
            'url': 'https://hysafejournal.org/en/articles/10.58895/hysafe.27',
            'source_type': 'large_scale_field_test',
            'usable_measurements': [
                'real-scale inclined hydrogen jet flame experiments',
                'incident heat radiation at defined distances',
                'release rates 0.0125 kg/s to 0.175 kg/s',
                '30 mm orifice',
            ],
            'required_digitization': [
                'heat radiation sensor coordinates and time windows',
                'mass-flow/release-angle matrix',
                'radiant heat fraction or incident heat-flux table',
            ],
        },
    ]
    overpressure_candidates = [
        {
            'id': 'hyindoor_low_strength_enclosure_2017',
            'title': 'Experimental studies on vented deflagrations in a low strength enclosure',
            'url': 'https://h2tools.org/bibcite/reference/3540',
            'doi': '10.1016/j.ijhydene.2016.06.223',
            'source_type': 'vented_deflagration_field_test',
            'usable_measurements': [
                '31 m3 enclosure',
                'uniform and stratified H2 distributions',
                'internal and external pressure measurements',
                'maximum internal overpressure target 10 kPa',
            ],
            'required_digitization': [
                'test matrix with H2 concentration, vent configuration, ignition location',
                'peak pressure gauge readings',
                'pressure gauge coordinates and uncertainty',
            ],
        },
        {
            'id': 'container_deflagration_2020',
            'title': 'Experimental study of end-vented hydrogen deflagrations in a 40-foot container',
            'url': 'https://doi.org/10.1016/j.ijhydene.2020.04.036',
            'source_type': 'vented_container_deflagration',
            'usable_measurements': [
                '40-foot ISO-container-scale enclosure',
                'hydrogen concentration, ignition location, and obstacle effects',
                'overpressure and structural response measurements',
            ],
            'required_digitization': [
                'case-specific mixture concentration and obstacle layout',
                'peak overpressure time history or table',
                'boundary/vent details matching a simulation case',
            ],
        },
    ]
    missing_artifacts = [
        {
            'artifact': 'calibration_metadata.json',
            'required_action': 'select one radiation source and one overpressure source, record URL/DOI, source hashes, and case-alignment booleans',
        },
        {
            'artifact': 'radiation_metrics.csv',
            'required_action': 'digitize or obtain heat-flux measurements with distance, tolerance, and source basis',
        },
        {
            'artifact': 'overpressure_metrics.csv',
            'required_action': 'digitize or obtain peak overpressure measurements with distance, tolerance, and source basis',
        },
        {
            'artifact': 'calibrated_fire_consequence_report',
            'required_action': 'run the official fire consequence report against a generated calibration dataset JSON',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Fire Calibration Public Source Triage',
        'clears_fire_consequence_blocker': False,
        'radiation_candidates': radiation_candidates,
        'overpressure_candidates': overpressure_candidates,
        'missing_artifacts': missing_artifacts,
        'summary': {
            'public_source_registry_available': True,
            'radiation_candidate_count': len(radiation_candidates),
            'overpressure_candidate_count': len(overpressure_candidates),
            'radiation_candidate_available': True,
            'overpressure_candidate_available': True,
            'local_radiation_metrics_available': False,
            'local_overpressure_metrics_available': False,
            'ready_for_dataset_ingestion': False,
            'clears_fire_consequence_blocker': False,
            'missing_artifact_count': len(missing_artifacts),
        },
        'quality_gate_matrix': [
            {'name': 'radiation_public_source_candidates_available', 'status': 'PASS', 'gap': '', 'evidence': [item['url'] for item in radiation_candidates]},
            {'name': 'overpressure_public_source_candidates_available', 'status': 'PASS', 'gap': '', 'evidence': [item['url'] for item in overpressure_candidates]},
            {'name': 'calibration_metadata_local', 'status': 'MISSING', 'gap': 'No production calibration_metadata.json with source hashes and case-alignment booleans is local.', 'evidence': []},
            {'name': 'radiation_metrics_local', 'status': 'MISSING', 'gap': 'No local radiation_metrics.csv has been ingested.', 'evidence': []},
            {'name': 'overpressure_metrics_local', 'status': 'MISSING', 'gap': 'No local overpressure_metrics.csv has been ingested.', 'evidence': []},
            {'name': 'calibrated_consequence_report', 'status': 'MISSING', 'gap': 'Official fire consequence report has not been rerun with a calibration dataset JSON.', 'evidence': []},
        ],
        'limitations': [
            'This report identifies candidate public calibration sources only; it does not digitize or ingest calibration data.',
            'Radiation and overpressure data families may come from different experiments, but production credit requires explicit case-alignment metadata.',
            'The fire-consequence blocker remains until calibrated radiation and overpressure agreement reports pass.',
        ],
    }


def validate_report_object(data: dict[str, Any]) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('clears_fire_consequence_blocker') is False, 'triage cannot clear fire blocker')
    radiation = data.get('radiation_candidates')
    overpressure = data.get('overpressure_candidates')
    require(isinstance(radiation, list) and len(radiation) >= 2, 'radiation source candidates incomplete')
    require(isinstance(overpressure, list) and len(overpressure) >= 1, 'overpressure source candidates incomplete')
    for item in radiation + overpressure:
        require(isinstance(item, dict), 'candidate is not an object')
        require(bool(item.get('id')), 'candidate id missing')
        require(bool(item.get('url')), 'candidate URL missing')
        require(isinstance(item.get('usable_measurements'), list) and item['usable_measurements'], 'candidate usable measurements missing')
        require(isinstance(item.get('required_digitization'), list) and item['required_digitization'], 'candidate digitization needs missing')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('public_source_registry_available') is True, 'public source registry missing')
    require(summary.get('radiation_candidate_available') is True, 'radiation source candidate missing')
    require(summary.get('overpressure_candidate_available') is True, 'overpressure source candidate missing')
    require(summary.get('ready_for_dataset_ingestion') is False, 'triage cannot be ingestion-ready')
    require(summary.get('clears_fire_consequence_blocker') is False, 'triage cannot clear blocker')
    require(int(summary.get('missing_artifact_count', 0)) >= 3, 'missing artifact count too small')
    matrix = data.get('quality_gate_matrix')
    require(isinstance(matrix, list) and matrix, 'quality gate matrix missing')
    require(any(item.get('status') == 'MISSING' for item in matrix if isinstance(item, dict)), 'triage must retain missing local-data gates')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Fire Calibration Public Source Triage',
        '',
        f"Status: `{report['status']}`",
        f"Clears fire-consequence blocker: `{report['clears_fire_consequence_blocker']}`",
        '',
        '## Radiation Candidates',
        '',
    ]
    for item in report['radiation_candidates']:
        lines.append(f"- `{item['id']}`: {item['url']}")
    lines += ['', '## Overpressure Candidates', '']
    for item in report['overpressure_candidates']:
        lines.append(f"- `{item['id']}`: {item['url']}")
    lines += ['', '## Missing Artifacts', '']
    for item in report['missing_artifacts']:
        lines.append(f"- `{item['artifact']}`: {item['required_action']}")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap |', '| --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['gap'] or 'none'} |")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report_object(report)
            print(
                'engineering_h2_fire_calibration_public_source_triage VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"missing_artifacts={report['summary']['missing_artifact_count']}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_fire_calibration_public_source_triage PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"missing_artifacts={report['summary']['missing_artifact_count']}"
        )
        return 0
    except FireSourceTriageError as exc:
        print(f'engineering_h2_fire_calibration_public_source_triage FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
