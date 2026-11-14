#!/usr/bin/env python3
"""Write/verify the engineering H2 evidence-chain rebuild manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS = 'PASS-H2-EVIDENCE-CHAIN-REBUILD-MANIFEST'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_evidence_chain_rebuild_manifest_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'h2_evidence_chain_rebuild_manifest.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'h2_evidence_chain_rebuild_manifest.md'
DEFAULT_REBUILD_SCRIPT = Path('tools/rebuild_engineering_h2_evidence_chain.sh')
DEFAULT_BOOTSTRAP_LOG = Path(
    'docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/'
    'full_verify_after_rebuild_bootstrap_20260724.log'
)

EXPECTED_REBUILD_COMMANDS = [
    'python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py',
    'python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py',
    'python3 tools/write_engineering_h2_real_cad_boundary_tag_contract_report.py',
    'python3 tools/write_engineering_h2_external_plume_public_source_triage_report.py',
    'python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py',
    'python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_selftest_report.py',
    'python3 tools/write_engineering_h2_sbepv5_digitization_preflight_report.py',
    'python3 tools/write_engineering_h2_sbepv5_literature_metric_preflight_report.py',
    'python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py',
    'python3 tools/write_engineering_h2_sbepv5_case_package_report.py',
    'python3 tools/write_engineering_h2_sbepv5_case_package_preflight_report.py',
    'python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py',
    'python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_selftest_report.py',
    'python3 tools/write_engineering_h2_fire_calibration_digitization_preflight_report.py',
    'python3 tools/write_engineering_h2_fire_calibration_literature_metric_preflight_report.py',
    'python3 tools/write_engineering_h2_fire_calibration_package_report.py',
    'python3 tools/write_engineering_h2_fire_calibration_dataset_report.py',
    'python3 tools/write_engineering_h2_reference_agreement_report.py',
    'python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py',
    'python3 tools/write_engineering_production_scorecard.py',
    'python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py',
    'python3 tools/write_engineering_h2_production_blocker_data_room_report.py',
    'python3 tools/write_engineering_h2_production_blocker_closure_manifest_report.py',
    'python3 tools/write_engineering_h2_external_evidence_intake_kit_manifest.py',
    'python3 tools/write_engineering_h2_external_artifact_operator_receipt_report.py',
    'python3 tools/write_engineering_h2_external_artifact_operator_receipt_gate_selftest_report.py',
    'python3 tools/write_engineering_h2_external_artifact_drop_validator.py',
    'python3 tools/write_engineering_h2_external_artifact_ingestion_plan.py',
    'python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py',
    'python3 tools/write_engineering_h2_external_evidence_operations_dashboard.py',
    'python3 tools/write_engineering_h2_external_evidence_acceptance_worksheet.py',
    'python3 tools/write_engineering_h2_external_artifact_mapping_alias_report.py',
    'python3 tools/write_engineering_h2_external_evidence_case_validation_plan.py',
    'python3 tools/run_engineering_h2_external_evidence_case_validation_campaigns.py --ledger-json',
    'python3 tools/run_engineering_h2_external_evidence_case_validation_campaigns.py --verify-ledger',
    'python3 tools/write_engineering_h2_case_validation_runner_ledger_selftest_report.py',
    'python3 tools/write_engineering_h2_case_validation_acceptance_contract_report.py',
    'python3 tools/write_engineering_h2_case_validation_acceptance_evaluation_report.py',
    'python3 tools/write_engineering_h2_case_validation_failure_attribution_report.py',
    'python3 tools/write_engineering_h2_case_validation_closure_matrix_report.py',
    'python3 tools/write_engineering_h2_external_artifact_unlock_forecast_report.py',
    'python3 tools/write_engineering_h2_external_evidence_case_validation_plan_selftest_report.py',
    'python3 tools/write_engineering_h2_case_validation_runner_preflight_report.py',
    'python3 tools/write_engineering_h2_case_validation_command_contract_report.py',
    'python3 tools/write_engineering_h2_case_validation_command_contract_selftest_report.py',
    'python3 tools/write_engineering_h2_external_artifact_gate_selftest_report.py',
    'python3 tools/write_engineering_h2_external_artifact_gate_negative_selftest_report.py',
    'python3 tools/write_engineering_h2_external_artifact_strict_qa_negative_selftest_report.py',
    'python3 tools/write_engineering_h2_synthetic_selftest_isolation_guard_report.py',
    'python3 tools/write_academic_droplet_spray_budget_preflight_report.py',
    'bash tools/codex_run_academic_spray_closed_particle_budget.sh',
    'python3 tools/write_academic_spray_closed_particle_budget_report.py',
    'python3 tools/write_engineering_h2_production_handoff_report.py',
    'python3 tools/write_engineering_h2_master_plan_traceability_report.py',
    'python3 tools/write_engineering_h2_quality_review_coverage_report.py',
]


class RebuildManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RebuildManifestError(message)


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
        raise RebuildManifestError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RebuildManifestError(f'invalid JSON evidence {path}: {exc}') from exc
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


def infer_ctest_count(log_text: str) -> int | None:
    if '100% tests passed, 0 tests failed out of 22' in log_text:
        return 22
    return None


def infer_ctest_skipped(log_text: str) -> bool:
    return 'skipping CTest because CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE' in log_text


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    script_path = Path(args.rebuild_script)
    bootstrap_log_path = Path(args.bootstrap_log)
    require(script_path.is_file(), f'missing rebuild script: {script_path}')
    require(bootstrap_log_path.is_file(), f'missing bootstrap log: {bootstrap_log_path}')
    script_text = script_path.read_text(encoding='utf-8', errors='replace')
    log_text = bootstrap_log_path.read_text(encoding='utf-8', errors='replace')
    missing_commands = [item for item in EXPECTED_REBUILD_COMMANDS if item not in script_text]
    ctest_count = infer_ctest_count(log_text)
    ctest_skipped = infer_ctest_skipped(log_text)
    ctest_evidence_status = 'PASS' if ctest_count == 22 else ('SKIPPED' if ctest_skipped else 'MISSING')
    verifier_passed = '[engineering-h2-verify] PASS engineering H2 production evidence verification' in log_text
    returncode_zero = 'CODEX_VERIFY_RC:0' in log_text
    skip_report_bootstrap = 'CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE' in script_text and (
        'skipping production evidence verification report because CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE'
        in log_text
    )
    all_expected_commands_present = not missing_commands
    quality_gate_matrix = [
        {
            'name': 'rebuild_script_present',
            'status': 'PASS',
            'evidence': str(script_path),
            'gap': '',
        },
        {
            'name': 'expected_rebuild_commands_present',
            'status': 'PASS' if all_expected_commands_present else 'MISSING',
            'evidence': f'{len(EXPECTED_REBUILD_COMMANDS) - len(missing_commands)}/{len(EXPECTED_REBUILD_COMMANDS)} command(s)',
            'gap': ', '.join(missing_commands),
        },
        {
            'name': 'bootstrap_log_passed',
            'status': 'PASS' if verifier_passed and returncode_zero else 'MISSING',
            'evidence': str(bootstrap_log_path),
            'gap': '',
        },
        {
            'name': 'bootstrap_ctest_evidence_recorded',
            'status': 'PASS' if ctest_evidence_status in {'PASS', 'SKIPPED'} else 'MISSING',
            'evidence': f'ctest_status={ctest_evidence_status} ctest_tests={ctest_count}',
            'gap': '',
        },
        {
            'name': 'bootstrap_report_cycle_broken',
            'status': 'PASS' if skip_report_bootstrap else 'MISSING',
            'evidence': 'bootstrap verifier skips production evidence report before regenerating it',
            'gap': '',
        },
        {
            'name': 'does_not_clear_production_blockers',
            'status': 'PASS',
            'evidence': 'rebuild manifest is reproducibility evidence only',
            'gap': '',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Evidence Chain Rebuild Manifest',
        'rebuild_script': str(script_path),
        'bootstrap_verification_log': str(bootstrap_log_path),
        'expected_rebuild_command_count': len(EXPECTED_REBUILD_COMMANDS),
        'missing_rebuild_commands': missing_commands,
        'all_expected_rebuild_commands_present': all_expected_commands_present,
        'bootstrap_verifier_passed': verifier_passed,
        'bootstrap_returncode_zero': returncode_zero,
        'bootstrap_ctest_tests': ctest_count,
        'bootstrap_ctest_skipped': ctest_skipped,
        'bootstrap_ctest_evidence_status': ctest_evidence_status,
        'bootstrap_report_cycle_broken': skip_report_bootstrap,
        'does_not_clear_production_blockers': True,
        'quality_gate_matrix': quality_gate_matrix,
        'evidence_files': [
            evidence_entry('engineering_h2_evidence_chain_rebuild_script', script_path),
            evidence_entry('engineering_h2_rebuild_bootstrap_verification_log', bootstrap_log_path),
        ],
        'limitations': [
            'This manifest proves the reproducible rebuild path and bootstrap verifier result; it does not provide external CAD, SBEPV5, or calibrated fire data.',
            'Production readiness still depends on clearing the remaining external-data blockers and rerunning the full verifier.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, 'invalid status')
    require(data.get('all_expected_rebuild_commands_present') is True, 'rebuild script missing expected commands')
    require(data.get('bootstrap_verifier_passed') is True, 'bootstrap verifier did not PASS')
    require(data.get('bootstrap_returncode_zero') is True, 'bootstrap verifier returncode was not zero')
    ctest_status = data.get('bootstrap_ctest_evidence_status')
    if ctest_status == 'PASS':
        require(int(data.get('bootstrap_ctest_tests', 0)) == 22, 'bootstrap CTest count mismatch')
        require(data.get('bootstrap_ctest_skipped') is False, 'bootstrap CTest cannot be both PASS and skipped')
    elif ctest_status == 'SKIPPED':
        require(data.get('bootstrap_ctest_tests') is None, 'skipped bootstrap CTest cannot report a test count')
        require(data.get('bootstrap_ctest_skipped') is True, 'bootstrap CTest skip marker missing')
    else:
        raise RebuildManifestError('bootstrap CTest evidence missing')
    require(data.get('bootstrap_report_cycle_broken') is True, 'bootstrap report cycle was not broken')
    require(data.get('does_not_clear_production_blockers') is True, 'rebuild manifest must not clear blockers')
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
        '# Engineering H2 Evidence Chain Rebuild Manifest',
        '',
        f"Status: `{report['status']}`",
        f"Rebuild script: `{report['rebuild_script']}`",
        f"Bootstrap log: `{report['bootstrap_verification_log']}`",
        f"Expected rebuild commands: `{report['expected_rebuild_command_count']}`",
        f"Bootstrap CTest evidence: `{report['bootstrap_ctest_evidence_status']}`",
        f"Bootstrap CTest tests: `{report['bootstrap_ctest_tests']}`",
        '',
        '## Quality Gates',
        '',
    ]
    for row in report['quality_gate_matrix']:
        lines.append(f"- `{row['name']}`: `{row['status']}`")
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
    parser.add_argument('--rebuild-script', default=str(DEFAULT_REBUILD_SCRIPT))
    parser.add_argument('--bootstrap-log', default=str(DEFAULT_BOOTSTRAP_LOG))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_evidence_chain_rebuild_manifest VERIFY-PASS '
                f"json={args.verify_json} commands={report['expected_rebuild_command_count']} "
                f"ctest={report['bootstrap_ctest_tests']}"
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
            'engineering_h2_evidence_chain_rebuild_manifest PASS '
            f"json={out_json} md={out_md} commands={report['expected_rebuild_command_count']} "
            f"ctest={report['bootstrap_ctest_tests']}"
        )
        return 0
    except RebuildManifestError as exc:
        print(f'engineering_h2_evidence_chain_rebuild_manifest FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
