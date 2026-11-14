#!/usr/bin/env python3
"""Write/verify the engineering H2 production handoff index report."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS_READY = 'PASS-H2-PRODUCTION-HANDOFF'
STATUS_NOT_READY = 'NOT_READY-H2-PRODUCTION-HANDOFF'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_production_handoff_20260723')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_production_handoff_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_production_handoff_report.md'
DEFAULT_PRODUCTION_EVIDENCE = Path(
    'docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/'
    'production_evidence_verification_report.json'
)
DEFAULT_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/'
    'h2_blocker_clearance_preflight_report.json'
)

DEFAULT_REQUIRED_NEXT_ARTIFACTS = {
    'external_plume_shape_reference': [
        'case-matched PeleLMeX input and geometry generated from the selected benchmark specification',
        'exact sensor and baffle coordinates digitized from source figures or original tabular data',
        'program sensor probes compared against SBEPV5 Gas09/Gas10 literature arrival-time anchors',
        'digitized or tabulated experimental dataset with source metadata and uncertainty/tolerances',
        'official h2_reference_agreement_report regenerated with --external-plume-dataset-json',
    ],
    'real_cad_cleanup': [
        'real_cad_cleanup_manifest.json in the cleanup package root',
        'source CAD/STL files for at least three representative large-layout geometries',
        'complete source provenance, units, coordinate frame, and engineering simplification notes',
        'sha256 hashes for every source CAD file and cleaned geometry file',
        'cleaned watertight STL/geometry files with non-degenerate meter-scale bounding boxes',
        'boundary tag map covering leak source, walls, vents/openings, outlets, and far-field regions',
        'regenerated real CAD cleanup and boundary-tag contract reports showing scorecard blocker clearance',
    ],
    'calibrated_fire_radiation_overpressure': [
        'calibration_metadata.json with source, scenario, fuel, geometry, wind, and uncertainty metadata',
        'radiation_metrics.csv containing experimental or authoritative reference heat-flux metrics',
        'overpressure_metrics.csv containing experimental or authoritative reference pressure metrics',
        'case-alignment table mapping every metric to program inputs, probes, tolerances, and units',
        'radiation and overpressure reference families covering the intended fire/consequence claim',
        'regenerated fire calibration dataset-ingestion and package reports showing production gate clearance',
    ],
}


class HandoffError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HandoffError(message)


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
        raise HandoffError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise HandoffError(f'invalid JSON in {path}: {exc}') from exc
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


def next_data_requirements(preflight: dict[str, Any]) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for item in preflight.get('blocker_records', []):
        if not isinstance(item, dict) or item.get('status') == 'CLEARED':
            continue
        domain = item.get('domain')
        artifacts = item.get('required_next_artifacts', [])
        if not artifacts:
            artifacts = DEFAULT_REQUIRED_NEXT_ARTIFACTS.get(str(domain), [])
        requirements.append({
            'domain': domain,
            'blocker': item.get('blocker'),
            'gate_report': item.get('gate_report'),
            'failed_quality_gates': item.get('failed_quality_gates', []),
            'blocking_gaps': item.get('blocking_gaps', []),
            'required_next_artifacts': artifacts,
        })
    return requirements


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    production_path = Path(args.production_evidence_report)
    preflight_path = Path(args.blocker_clearance_preflight_report)
    production = load_json(production_path)
    preflight = load_json(preflight_path)
    summary = production.get('summary') if isinstance(production.get('summary'), dict) else {}
    production_verified = (
        production.get('status') == 'PASS'
        and summary.get('ctest_passed') is True
        and int(summary.get('ctest_tests', 0)) == 22
        and summary.get('path_audit_pass') is True
        and summary.get('mpi_link_shim_pass') is True
    )
    preflight_ready = preflight.get('ready_for_production_scorecard_clearance') is True
    ready = production_verified and preflight_ready
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_READY if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 Production Handoff Index',
        'production_evidence_report': str(production_path),
        'blocker_clearance_preflight_report': str(preflight_path),
        'current_status': {
            'production_evidence_status': production.get('status'),
            'production_evidence_schema_version': production.get('schema_version'),
            'functional_coverage_percent': summary.get('scorecard_functional_percent'),
            'production_credibility_percent': summary.get('scorecard_production_credibility_percent'),
            'ctest_tests': summary.get('ctest_tests'),
            'ctest_passed': summary.get('ctest_passed'),
            'scorecard_status': preflight.get('scorecard_status'),
            'remaining_blocker_count': preflight.get('remaining_blocker_count'),
            'cleared_blocker_count': preflight.get('cleared_blocker_count'),
            'ready_for_production_scorecard_clearance': preflight_ready,
        },
        'verified_entrypoints': [
            {
                'command': 'bash tools/verify_engineering_h2_production_evidence.sh',
                'purpose': 'Full maintained engineering H2 production evidence gate.',
                'expected_current_result': 'PASS with score below production-ready threshold until blockers clear.',
            },
            {
                'command': 'python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py --verify-json docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/h2_blocker_clearance_preflight_report.json',
                'purpose': 'Verify all production blockers are covered by domain gates.',
                'expected_current_result': 'VERIFY-PASS with NOT_READY status and remaining blockers.',
            },
            {
                'command': 'python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json',
                'purpose': 'Verify top-level evidence ledger hashes and summary invariants.',
                'expected_current_result': 'VERIFY-PASS.',
            },
        ],
        'next_data_requirements': next_data_requirements(preflight),
        'handoff_decision': (
            'ready_for_production_claim'
            if ready else 'continue_engineering_hardening_and_external_data_ingestion'
        ),
        'evidence_files': [
            evidence_entry('production_evidence_verification_report', production_path),
            evidence_entry('blocker_clearance_preflight_report', preflight_path),
        ],
        'limitations': [
            'This handoff report is an index over verified evidence; it does not launch CFD or clear production blockers.',
            'Production readiness still requires the scorecard to become PRODUCTION_READY with no blocking gaps.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    status = data.get('current_status')
    require(isinstance(status, dict), 'current_status missing')
    require(status.get('production_evidence_status') == 'PASS', 'production evidence is not PASS')
    require(status.get('ctest_passed') is True, 'handoff requires passing CTest evidence')
    require(int(status.get('ctest_tests', 0)) == 22, 'handoff CTest count mismatch')
    requirements = data.get('next_data_requirements')
    require(isinstance(requirements, list), 'next_data_requirements missing')
    for item in requirements:
        require(isinstance(item, dict), 'next_data_requirements item is not an object')
        artifacts = item.get('required_next_artifacts')
        require(
            isinstance(artifacts, list) and all(str(artifact).strip() for artifact in artifacts),
            f"next_data_requirements item has no actionable artifacts: {item.get('domain')}",
        )
    entrypoints = data.get('verified_entrypoints')
    require(isinstance(entrypoints, list) and entrypoints, 'verified_entrypoints missing')
    if data.get('status') == STATUS_READY:
        require(status.get('ready_for_production_scorecard_clearance') is True, 'ready handoff lacks clearance')
        require(int(status.get('remaining_blocker_count', -1)) == 0, 'ready handoff has remaining blockers')
    else:
        require(status.get('ready_for_production_scorecard_clearance') is False, 'not-ready handoff cannot claim clearance')
        require(int(status.get('remaining_blocker_count', 0)) >= 1, 'not-ready handoff must retain blockers')
        require(requirements, 'not-ready handoff must list data requirements')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            p = Path(str(item.get('path', '')))
            require(p.is_file(), f'missing evidence file: {p}')
            require(sha256_file(p) == item.get('sha256'), f'evidence sha256 mismatch: {p}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Production Handoff Index',
        '',
        f"Status: `{report['status']}`",
        f"Handoff decision: `{report['handoff_decision']}`",
        '',
        '## Current Status',
        '',
    ]
    for key, value in report['current_status'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Next Data Requirements', '']
    for item in report['next_data_requirements']:
        failed = '; '.join(item.get('failed_quality_gates', [])) or 'none'
        gaps = '; '.join(str(gap) for gap in item.get('blocking_gaps', [])) or 'none'
        lines.append(f"- `{item['domain']}`: failed gates `{failed}`; gaps `{gaps}`")
        for artifact in item.get('required_next_artifacts', []):
            lines.append(f"  - required artifact: {artifact}")
    lines += ['', '## Verified Entrypoints', '']
    for item in report['verified_entrypoints']:
        lines.append(f"- `{item['command']}`: {item['purpose']}")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--production-evidence-report', default=str(DEFAULT_PRODUCTION_EVIDENCE))
    parser.add_argument('--blocker-clearance-preflight-report', default=str(DEFAULT_PREFLIGHT))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_production_handoff VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"remaining={report['current_status']['remaining_blocker_count']}"
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
            'engineering_h2_production_handoff PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"remaining={report['current_status']['remaining_blocker_count']}"
        )
        return 0
    except HandoffError as exc:
        print(f'engineering_h2_production_handoff FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
