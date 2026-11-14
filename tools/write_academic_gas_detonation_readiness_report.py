#!/usr/bin/env python3
"""Write/verify the academic gas detonation and chemistry readiness report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = 'PASS-ACADEMIC-GAS-DETONATION-READINESS'
STATUS_PARTIAL = 'PARTIAL-ACADEMIC-GAS-DETONATION-READINESS'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-GAS-DETONATION-READINESS'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_gas_detonation_readiness_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_gas_detonation_readiness_report.md'
REMOTE_REPO_ROOT_TEXT = '/' + '/'.join(('home', 'cj', 'my-pele'))
REMOTE_REPO_ROOT = Path(REMOTE_REPO_ROOT_TEXT)
DEFAULT_CTEST_LIST_LOG = DEFAULT_ROOT / 'ctest_list.log'
DEFAULT_DETONATION_VALIDATION_LOG = DEFAULT_ROOT / 'detonation_wave_validation.log'
DEFAULT_IGNITION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/'
    'ignition_consequence_report.json'
)
DEFAULT_CANTERA_REFERENCE_REPORT = Path(
    'docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724/'
    'cantera_ignition_reference_report.json'
)
DEFAULT_CANTERA_MECHANISM_COMPARISON_REPORT = Path(
    'docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/'
    'cantera_mechanism_comparison_report.json'
)
DEFAULT_PELEPHYSICS_RATE_KERNEL_EQUIVALENCE_REPORT = Path(
    'docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728/'
    'pelephysics_rate_kernel_equivalence_report.json'
)
DEFAULT_TWO_D_DETONATION_REFERENCE_REPORT = Path(
    'docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/'
    'academic_gas_2d_detonation_reference_report.json'
)
DEFAULT_THREE_D_DETONATION_REFERENCE_REPORT = Path(
    'docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/'
    'academic_gas_3d_detonation_reference_report.json'
)
DEFAULT_DETONATION_FRONT_AMR_VALIDATION_REPORT = Path(
    'docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/'
    'academic_gas_detonation_front_amr_validation_report.json'
)
DEFAULT_DETONATION_SCRIPT = Path('tools/codex_smoke_academic_detonation_wave.sh')
DEFAULT_DETONATION_VALIDATOR = Path('tools/validate_detonation_wave.py')
DEFAULT_SOD_SCRIPT = Path('tools/codex_smoke_academic_sod_plotfile.sh')
DEFAULT_SOD_VALIDATOR = Path('tools/validate_sod_plotfile.py')
DEFAULT_VORTEX_SCRIPT = Path('tools/codex_smoke_academic_pelec_isentropic_vortex.sh')
DEFAULT_VORTEX_VALIDATOR = Path('tools/validate_pelec_isentropic_vortex.py')

FOUNDATION_CTESTS = {
    'weno5_smoke',
    'pelec_weno_smoke',
    'sod_shock_tube_smoke',
    'isentropic_vortex_smoke',
}

QUALITY_GATE_NAMES = {
    'ctest_list_present',
    'weno_foundation_ctests_present',
    'compressible_baseline_ctests_present',
    'ignition_consequence_evidence_present',
    'academic_detonation_tooling_present',
    'short_2d_detonation_wave_validation',
    'cantera_mechanism_comparison',
    'compiled_pelephysics_rate_kernel_equivalence',
    'zero_d_ignition_delay_reference_curve',
    'two_d_detonation_reference_validation',
    'three_d_detonation_reference_validation',
    'detonation_front_amr_validation',
    'detonation_subreport_evidence_hashes_verified',
}


class AcademicGasReadinessError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcademicGasReadinessError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def repo_root() -> Path:
    return Path.cwd().resolve()


def resolve_evidence_path(path: Path) -> Path:
    candidates = [path]
    raw = str(path).replace('\\', '/')
    remote_root = str(REMOTE_REPO_ROOT).replace('\\', '/')
    remote_prefix = f'{remote_root}/'
    if raw == remote_root:
        candidates.append(repo_root())
    elif raw.startswith(remote_prefix):
        candidates.append(repo_root() / raw[len(remote_prefix):])
    if path.is_absolute():
        try:
            candidates.append(repo_root() / path.relative_to(REMOTE_REPO_ROOT))
        except ValueError:
            pass
    else:
        candidates.append(repo_root() / path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return path


def archive_path_text(path: Path) -> str:
    raw = str(path).replace('\\', '/')
    remote_root = str(REMOTE_REPO_ROOT).replace('\\', '/')
    remote_prefix = f'{remote_root}/'
    if raw == remote_root:
        return '.'
    if raw.startswith(remote_prefix):
        return raw[len(remote_prefix):]
    if path.is_absolute():
        try:
            return str(path.relative_to(REMOTE_REPO_ROOT))
        except ValueError:
            try:
                return str(path.resolve().relative_to(repo_root()))
            except ValueError:
                pass
    return str(path)


def load_json(path: Path) -> dict[str, Any]:
    resolved = resolve_evidence_path(path)
    try:
        data = json.loads(resolved.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise AcademicGasReadinessError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise AcademicGasReadinessError(f'invalid JSON evidence {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    resolved = resolve_evidence_path(path)
    require(resolved.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': archive_path_text(path),
        'sha256': sha256_file(resolved),
        'size_bytes': resolved.stat().st_size,
    }


def verify_embedded_evidence_hashes(label: str, report: dict[str, Any]) -> int:
    entries = report.get('evidence_files')
    require(isinstance(entries, list) and entries, f'{label} evidence_files missing')
    verified = 0
    for item in entries:
        require(isinstance(item, dict), f'{label} evidence entry is not an object')
        raw_path = Path(str(item.get('path', '')))
        resolved = resolve_evidence_path(raw_path)
        require(resolved.is_file(), f'{label} missing embedded evidence file: {raw_path}')
        require(
            sha256_file(resolved) == item.get('sha256'),
            f'{label} embedded evidence hash mismatch: {raw_path}',
        )
        verified += 1
    return verified


def parse_ctest_names(path: Path) -> set[str]:
    require(path.is_file(), f'missing CTest list log: {path}')
    names: set[str] = set()
    pattern = re.compile(r'^\s*Test\s+#\d+:\s+(\S+)\s*$')
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        match = pattern.match(line)
        if match:
            names.add(match.group(1))
    return names


def parse_validation_metrics(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding='utf-8', errors='replace')
    match = re.search(r'^detonation_wave_validation PASS\s+(.*)$', text, re.MULTILINE)
    if not match:
        return {}
    metrics: dict[str, Any] = {'verdict': 'PASS'}
    for item in match.group(1).split():
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        try:
            metrics[key] = float(value)
        except ValueError:
            metrics[key] = value
    return metrics


def gate(name: str, status: str, evidence: list[str], gap: str = '') -> dict[str, Any]:
    require(name in QUALITY_GATE_NAMES, f'unknown quality gate: {name}')
    require(status in {'PASS', 'PARTIAL', 'MISSING'}, f'invalid quality gate status: {status}')
    if status != 'PASS':
        require(gap, f'non-PASS quality gate missing gap: {name}')
    return {'name': name, 'status': status, 'evidence': evidence, 'gap': gap}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    ctest_list_path = Path(args.ctest_list_log)
    detonation_validation_path = Path(args.detonation_validation_log)
    ignition_path = Path(args.ignition_report)
    cantera_reference_path = Path(args.cantera_reference_report)
    cantera_mechanism_comparison_path = Path(args.cantera_mechanism_comparison_report)
    pelephysics_rate_kernel_equivalence_path = Path(args.pelephysics_rate_kernel_equivalence_report)
    two_d_detonation_reference_path = Path(args.two_d_detonation_reference_report)
    three_d_detonation_reference_path = Path(args.three_d_detonation_reference_report)
    detonation_front_amr_validation_path = Path(args.detonation_front_amr_validation_report)
    detonation_script_path = Path(args.detonation_script)
    detonation_validator_path = Path(args.detonation_validator)
    sod_script_path = Path(args.sod_script)
    sod_validator_path = Path(args.sod_validator)
    vortex_script_path = Path(args.vortex_script)
    vortex_validator_path = Path(args.vortex_validator)

    ctest_names = parse_ctest_names(ctest_list_path)
    ignition = load_json(ignition_path)
    cantera_reference = load_json(cantera_reference_path)
    cantera_mechanism_comparison = load_json(cantera_mechanism_comparison_path)
    pelephysics_rate_kernel_equivalence = load_json(pelephysics_rate_kernel_equivalence_path)
    two_d_detonation_reference = load_json(two_d_detonation_reference_path)
    three_d_detonation_reference = load_json(three_d_detonation_reference_path)
    detonation_front_amr_validation = load_json(detonation_front_amr_validation_path)
    subreport_evidence_counts = {
        'two_d': verify_embedded_evidence_hashes('two_d_detonation_reference', two_d_detonation_reference),
        'three_d': verify_embedded_evidence_hashes('three_d_detonation_reference', three_d_detonation_reference),
        'detonation_front_amr': verify_embedded_evidence_hashes(
            'detonation_front_amr_validation',
            detonation_front_amr_validation,
        ),
    }
    validation_metrics = parse_validation_metrics(detonation_validation_path)

    missing_foundation = sorted(FOUNDATION_CTESTS - ctest_names)
    weno_ctests_present = {'weno5_smoke', 'pelec_weno_smoke'}.issubset(ctest_names)
    baseline_ctests_present = {'sod_shock_tube_smoke', 'isentropic_vortex_smoke'}.issubset(ctest_names)
    ignition_ok = ignition.get('status') == 'PASS-SMOKE'
    cantera_summary = (
        cantera_reference.get('summary', {})
        if isinstance(cantera_reference.get('summary'), dict)
        else {}
    )
    cantera_curve_ok = (
        cantera_reference.get('status') == 'PASS-ACADEMIC-GAS-CANTERA-IGNITION-REFERENCE'
        and cantera_summary.get('clears_zero_d_ignition_delay_reference_curve_gap') is True
    )
    cantera_mechanism_summary = (
        cantera_mechanism_comparison.get('summary', {})
        if isinstance(cantera_mechanism_comparison.get('summary'), dict)
        else {}
    )
    cantera_mechanism_comparison_ok = (
        cantera_mechanism_comparison.get('status') == 'PASS-ACADEMIC-GAS-CANTERA-MECHANISM-COMPARISON'
        and cantera_mechanism_summary.get('clears_cantera_mechanism_comparison_gap') is True
        and cantera_mechanism_summary.get('clears_full_pelephysics_source_rate_equivalence') is False
    )
    rate_kernel_summary = (
        pelephysics_rate_kernel_equivalence.get('summary', {})
        if isinstance(pelephysics_rate_kernel_equivalence.get('summary'), dict)
        else {}
    )
    pelephysics_rate_kernel_equivalence_ok = (
        pelephysics_rate_kernel_equivalence.get('status') == 'PASS-ACADEMIC-GAS-PELEPHYSICS-RATE-KERNEL-EQUIVALENCE'
        and rate_kernel_summary.get('clears_full_pelephysics_source_rate_equivalence') is True
        and rate_kernel_summary.get('clears_acd_02_rate_kernel_gap') is True
    )
    two_d_summary = (
        two_d_detonation_reference.get('summary', {})
        if isinstance(two_d_detonation_reference.get('summary'), dict)
        else {}
    )
    two_d_reference_ok = (
        two_d_detonation_reference.get('status') == 'PASS-ACADEMIC-GAS-2D-DETONATION-REFERENCE'
        and two_d_summary.get('clears_two_d_detonation_reference_validation_gap') is True
        and two_d_summary.get('clears_three_d_detonation_reference_validation_gap') is False
        and two_d_summary.get('clears_detonation_front_amr_validation_gap') is False
    )
    three_d_summary = (
        three_d_detonation_reference.get('summary', {})
        if isinstance(three_d_detonation_reference.get('summary'), dict)
        else {}
    )
    three_d_reference_ok = (
        three_d_detonation_reference.get('status') == 'PASS-ACADEMIC-GAS-3D-DETONATION-REFERENCE'
        and three_d_summary.get('clears_three_d_detonation_reference_validation_gap') is True
        and three_d_summary.get('clears_detonation_front_amr_validation_gap') is False
    )
    amr_summary = (
        detonation_front_amr_validation.get('summary', {})
        if isinstance(detonation_front_amr_validation.get('summary'), dict)
        else {}
    )
    detonation_front_amr_ok = (
        detonation_front_amr_validation.get('status') == 'PASS-ACADEMIC-GAS-DETONATION-FRONT-AMR-VALIDATION'
        and amr_summary.get('clears_detonation_front_amr_validation_gap') is True
    )
    tooling_paths = [
        detonation_script_path,
        detonation_validator_path,
        sod_script_path,
        sod_validator_path,
        vortex_script_path,
        vortex_validator_path,
    ]
    tooling_present = all(path.is_file() for path in tooling_paths)
    detonation_wave_pass = validation_metrics.get('verdict') == 'PASS'
    foundation_ready = (
        not missing_foundation
        and weno_ctests_present
        and baseline_ctests_present
        and ignition_ok
        and tooling_present
    )

    quality_gate_matrix = [
        gate(
            'ctest_list_present',
            'PASS' if ctest_names else 'MISSING',
            [str(ctest_list_path)] if ctest_names else [],
            '' if ctest_names else 'Generate ctest -N output from build-codex-smoke.',
        ),
        gate(
            'weno_foundation_ctests_present',
            'PASS' if weno_ctests_present else 'MISSING',
            ['weno5_smoke', 'pelec_weno_smoke'] if weno_ctests_present else [],
            '' if weno_ctests_present else 'weno5_smoke and pelec_weno_smoke must both be present in the maintained CTest list.',
        ),
        gate(
            'compressible_baseline_ctests_present',
            'PASS' if baseline_ctests_present else 'MISSING',
            ['sod_shock_tube_smoke', 'isentropic_vortex_smoke'] if baseline_ctests_present else [],
            '' if baseline_ctests_present else 'Sod and isentropic vortex CTests must both be present in the maintained CTest list.',
        ),
        gate(
            'ignition_consequence_evidence_present',
            'PASS' if ignition_ok else 'MISSING',
            [str(ignition_path)] if ignition_ok else [],
            '' if ignition_ok else 'PelePhysics-linked ignition consequence evidence must verify as PASS-SMOKE.',
        ),
        gate(
            'academic_detonation_tooling_present',
            'PASS' if tooling_present else 'MISSING',
            [str(path) for path in tooling_paths if path.is_file()],
            '' if tooling_present else 'Academic detonation, Sod, and vortex smoke scripts/validators must exist.',
        ),
        gate(
            'short_2d_detonation_wave_validation',
            'PASS' if detonation_wave_pass else 'MISSING',
            [str(detonation_validation_path)] if detonation_wave_pass else [],
            '' if detonation_wave_pass else 'Run tools/codex_smoke_academic_detonation_wave.sh and archive its validation log.',
        ),
        gate(
            'cantera_mechanism_comparison',
            'PASS' if cantera_mechanism_comparison_ok else 'MISSING',
            [str(cantera_mechanism_comparison_path)] if cantera_mechanism_comparison_ok else [],
            '' if cantera_mechanism_comparison_ok else 'No maintained report compares loaded Chemkin/Cantera mechanism thermochemistry/reaction rates against Cantera.',
        ),
        gate(
            'compiled_pelephysics_rate_kernel_equivalence',
            'PASS' if pelephysics_rate_kernel_equivalence_ok else 'MISSING',
            [str(pelephysics_rate_kernel_equivalence_path)] if pelephysics_rate_kernel_equivalence_ok else [],
            '' if pelephysics_rate_kernel_equivalence_ok else 'No maintained report compares compiled PelePhysics LiDryer rate kernels against Cantera for the same mechanism.',
        ),
        gate(
            'zero_d_ignition_delay_reference_curve',
            'PASS' if cantera_curve_ok else ('PARTIAL' if ignition_ok else 'MISSING'),
            [str(cantera_reference_path)] if cantera_curve_ok else ([str(ignition_path)] if ignition_ok else []),
            '' if cantera_curve_ok else (
                'Short H2 ignition evidence exists, but no maintained multi-condition 0D ignition-delay curve '
                'against Cantera/reference data is attached.'
            ),
        ),
        gate(
            'two_d_detonation_reference_validation',
            'PASS' if two_d_reference_ok else ('PARTIAL' if detonation_wave_pass else 'MISSING'),
            [str(two_d_detonation_reference_path)] if two_d_reference_ok else ([str(detonation_validation_path)] if detonation_wave_pass else []),
            '' if two_d_reference_ok else (
                'A short 2D wave smoke exists, but no reference-quality 2D detonation speed/cell-size/grid-convergence '
                'validation is attached.'
            ),
        ),
        gate(
            'three_d_detonation_reference_validation',
            'PASS' if three_d_reference_ok else 'MISSING',
            [str(three_d_detonation_reference_path)] if three_d_reference_ok else [],
            '' if three_d_reference_ok else 'No maintained 3D gas detonation validation evidence is attached.',
        ),
        gate(
            'detonation_front_amr_validation',
            'PASS' if detonation_front_amr_ok else 'MISSING',
            [str(detonation_front_amr_validation_path)] if detonation_front_amr_ok else [],
            '' if detonation_front_amr_ok else 'No maintained detonation-front AMR tagging/refinement efficiency validation is attached.',
        ),
        gate(
            'detonation_subreport_evidence_hashes_verified',
            'PASS',
            [
                f'two_d={subreport_evidence_counts["two_d"]}',
                f'three_d={subreport_evidence_counts["three_d"]}',
                f'detonation_front_amr={subreport_evidence_counts["detonation_front_amr"]}',
            ],
        ),
    ]
    missing_or_partial = [item['name'] for item in quality_gate_matrix if item['status'] != 'PASS']
    academic_gas_detonation_ready = foundation_ready and not missing_or_partial
    status = (
        STATUS_PASS
        if academic_gas_detonation_ready
        else (STATUS_PARTIAL if foundation_ready else STATUS_NOT_READY)
    )

    evidence_files = [
        evidence_entry('ctest_list_log', ctest_list_path),
        evidence_entry('ignition_consequence_report', ignition_path),
        evidence_entry('cantera_ignition_reference_report', cantera_reference_path),
        evidence_entry('cantera_mechanism_comparison_report', cantera_mechanism_comparison_path),
        evidence_entry('pelephysics_rate_kernel_equivalence_report', pelephysics_rate_kernel_equivalence_path),
        evidence_entry('two_d_detonation_reference_report', two_d_detonation_reference_path),
        evidence_entry('three_d_detonation_reference_report', three_d_detonation_reference_path),
        evidence_entry('detonation_front_amr_validation_report', detonation_front_amr_validation_path),
        evidence_entry('academic_detonation_wave_script', detonation_script_path),
        evidence_entry('academic_detonation_wave_validator', detonation_validator_path),
        evidence_entry('academic_sod_plotfile_script', sod_script_path),
        evidence_entry('academic_sod_plotfile_validator', sod_validator_path),
        evidence_entry('academic_isentropic_vortex_script', vortex_script_path),
        evidence_entry('academic_isentropic_vortex_validator', vortex_validator_path),
    ]
    if detonation_validation_path.is_file():
        evidence_files.append(evidence_entry('detonation_wave_validation_log', detonation_validation_path))

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Academic Gas Detonation and Chemistry Readiness',
        'scope': 'master-plan ACD-02/ACD-03 gas-phase chemistry and gas detonation readiness',
        'ctest_list_log': str(ctest_list_path),
        'ignition_report': str(ignition_path),
        'cantera_reference_report': str(cantera_reference_path),
        'cantera_mechanism_comparison_report': str(cantera_mechanism_comparison_path),
        'pelephysics_rate_kernel_equivalence_report': str(pelephysics_rate_kernel_equivalence_path),
        'two_d_detonation_reference_report': str(two_d_detonation_reference_path),
        'three_d_detonation_reference_report': str(three_d_detonation_reference_path),
        'detonation_front_amr_validation_report': str(detonation_front_amr_validation_path),
        'summary': {
            'ignition_status': ignition.get('status'),
            'ctest_foundation_tests_present': sorted(FOUNDATION_CTESTS & ctest_names),
            'ctest_foundation_tests_missing': missing_foundation,
            'foundation_ready': foundation_ready,
            'short_2d_detonation_wave_validation_passed': detonation_wave_pass,
            'cantera_mechanism_comparison_available': cantera_mechanism_comparison_ok,
            'compiled_pelephysics_rate_kernel_equivalence_available': pelephysics_rate_kernel_equivalence_ok,
            'zero_d_reference_curve_available': cantera_curve_ok,
            'two_d_reference_validation_available': two_d_reference_ok,
            'three_d_reference_validation_available': three_d_reference_ok,
            'detonation_front_amr_validation_available': detonation_front_amr_ok,
            'detonation_subreport_evidence_hash_counts': subreport_evidence_counts,
            'academic_gas_detonation_ready': academic_gas_detonation_ready,
            'clears_acd_02': (
                cantera_curve_ok
                and cantera_mechanism_comparison_ok
                and pelephysics_rate_kernel_equivalence_ok
            ),
            'clears_acd_03': academic_gas_detonation_ready,
            'missing_or_partial_quality_gate_count': len(missing_or_partial),
        },
        'detonation_wave_metrics': validation_metrics,
        'quality_gate_matrix': quality_gate_matrix,
        'blocking_gaps': missing_or_partial,
        'next_required_artifacts': [] if academic_gas_detonation_ready else [
            'detonation-front AMR tagging/refinement efficiency validation',
        ],
        'evidence_files': evidence_files,
        'limitations': [
            'This report clears maintained in-repository ACD-02/ACD-03 readiness gates when all quality gates pass.',
            'Short smoke-scale detonation evidence, when present, is not a substitute for reference-quality 2D/3D detonation validation.',
            'The compiled rate-kernel evidence samples the CPU LiDryer C++ mechanism kernel; GPU bitwise source-rate equivalence remains a deeper certification task.',
            'The 2D detonation reference evidence is solver self-consistency/grid evidence; external literature agreement remains a deeper certification task.',
            'The 3D detonation reference evidence is a thin-slab ZND-style gate; external literature agreement remains a deeper certification task.',
            'The detonation-front AMR evidence is an in-repository validation gate; external literature agreement remains a deeper certification task.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_PASS, STATUS_PARTIAL, STATUS_NOT_READY}, 'invalid status')
    summ = data.get('summary')
    require(isinstance(summ, dict), 'summary missing')
    require(isinstance(summ.get('clears_acd_03'), bool), 'clears_acd_03 missing')
    require(isinstance(summ.get('clears_acd_02'), bool), 'clears_acd_02 missing')
    require(isinstance(summ.get('missing_or_partial_quality_gate_count'), int), 'quality gate count missing')
    gates = data.get('quality_gate_matrix')
    require(isinstance(gates, list), 'quality_gate_matrix missing')
    names = {str(item.get('name')) for item in gates if isinstance(item, dict)}
    require(names == QUALITY_GATE_NAMES, f'quality gate set mismatch: missing={sorted(QUALITY_GATE_NAMES - names)} extra={sorted(names - QUALITY_GATE_NAMES)}')
    non_pass = [item for item in gates if isinstance(item, dict) and item.get('status') != 'PASS']
    require(len(non_pass) == int(summ['missing_or_partial_quality_gate_count']), 'quality gate count mismatch')
    if data.get('status') == STATUS_PASS:
        require(not non_pass, 'PASS readiness cannot have remaining quality gaps')
        require(summ.get('foundation_ready') is True, 'PASS readiness requires foundation_ready')
        require(summ.get('academic_gas_detonation_ready') is True, 'PASS readiness requires academic gas detonation ready')
        require(summ.get('clears_acd_03') is True, 'PASS readiness must clear ACD-03')
        require(summ.get('clears_acd_02') is True, 'PASS readiness must clear ACD-02')
    elif data.get('status') == STATUS_PARTIAL:
        require(non_pass, 'PARTIAL readiness must have remaining quality gaps')
        require(summ.get('foundation_ready') is True, 'PARTIAL readiness requires foundation_ready')
    else:
        require(non_pass, 'NOT_READY readiness must have remaining quality gaps')
        require(summ.get('foundation_ready') is False, 'NOT_READY readiness should reflect incomplete foundation')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            resolved = resolve_evidence_path(path)
            require(resolved.is_file(), f'missing evidence file: {path}')
            require(sha256_file(resolved) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Academic Gas Detonation and Chemistry Readiness',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Quality Gates', '', '| Gate | Status | Evidence | Gap |', '| --- | --- | --- | --- |']
    for item in report['quality_gate_matrix']:
        evidence = '; '.join(item['evidence']) or 'none'
        gap_text = item['gap'] or 'none'
        lines.append(f"| `{item['name']}` | `{item['status']}` | {evidence} | {gap_text} |")
    lines += ['', '## Next Required Artifacts', '']
    for item in report['next_required_artifacts']:
        lines.append(f'- {item}')
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ctest-list-log', default=str(DEFAULT_CTEST_LIST_LOG))
    parser.add_argument('--detonation-validation-log', default=str(DEFAULT_DETONATION_VALIDATION_LOG))
    parser.add_argument('--ignition-report', default=str(DEFAULT_IGNITION_REPORT))
    parser.add_argument('--cantera-reference-report', default=str(DEFAULT_CANTERA_REFERENCE_REPORT))
    parser.add_argument('--cantera-mechanism-comparison-report', default=str(DEFAULT_CANTERA_MECHANISM_COMPARISON_REPORT))
    parser.add_argument('--pelephysics-rate-kernel-equivalence-report', default=str(DEFAULT_PELEPHYSICS_RATE_KERNEL_EQUIVALENCE_REPORT))
    parser.add_argument('--two-d-detonation-reference-report', default=str(DEFAULT_TWO_D_DETONATION_REFERENCE_REPORT))
    parser.add_argument('--three-d-detonation-reference-report', default=str(DEFAULT_THREE_D_DETONATION_REFERENCE_REPORT))
    parser.add_argument('--detonation-front-amr-validation-report', default=str(DEFAULT_DETONATION_FRONT_AMR_VALIDATION_REPORT))
    parser.add_argument('--detonation-script', default=str(DEFAULT_DETONATION_SCRIPT))
    parser.add_argument('--detonation-validator', default=str(DEFAULT_DETONATION_VALIDATOR))
    parser.add_argument('--sod-script', default=str(DEFAULT_SOD_SCRIPT))
    parser.add_argument('--sod-validator', default=str(DEFAULT_SOD_VALIDATOR))
    parser.add_argument('--vortex-script', default=str(DEFAULT_VORTEX_SCRIPT))
    parser.add_argument('--vortex-validator', default=str(DEFAULT_VORTEX_VALIDATOR))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summ = report.get('summary', {})
            print(
                'academic_gas_detonation_readiness VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"foundation={summ.get('foundation_ready')} "
                f"missing_or_partial={summ.get('missing_or_partial_quality_gate_count')}"
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
            'academic_gas_detonation_readiness PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"foundation={report['summary']['foundation_ready']} "
            f"missing_or_partial={report['summary']['missing_or_partial_quality_gate_count']}"
        )
        return 0
    except AcademicGasReadinessError as exc:
        print(f'academic_gas_detonation_readiness FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
