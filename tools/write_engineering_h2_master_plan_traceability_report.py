#!/usr/bin/env python3
"""Write/verify traceability from pele_cfd_master_plan.md to current evidence."""
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
STATUS_PASS = 'PASS-H2-MASTER-PLAN-TRACEABILITY'
STATUS_NOT_READY = 'NOT_READY-H2-MASTER-PLAN-TRACEABILITY'

DEFAULT_MASTER_PLAN = Path('../pele_cfd_master_plan.md')
DEFAULT_OUTPUT_ROOT = Path('docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724')
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / 'h2_master_plan_traceability_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / 'h2_master_plan_traceability_report.md'
DEFAULT_PRODUCTION_EVIDENCE = Path(
    'docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/'
    'production_evidence_verification_report.json'
)
DEFAULT_HANDOFF = Path(
    'docs/codex_audit/evidence/engineering_h2_production_handoff_20260723/'
    'h2_production_handoff_report.json'
)
DEFAULT_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/'
    'h2_blocker_clearance_preflight_report.json'
)
DEFAULT_SCORECARD = Path(
    'docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json'
)
DEFAULT_ACADEMIC_GAS = Path(
    'docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/'
    'academic_gas_detonation_readiness_report.json'
)
DEFAULT_ACADEMIC_WENO5_CONVERGENCE = Path(
    'docs/codex_audit/evidence/academic_weno5_convergence_validation_20260729/'
    'academic_weno5_convergence_validation_report.json'
)
DEFAULT_ACADEMIC_TWOPHASE_RT = Path(
    'docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/'
    'academic_twophase_rayleigh_taylor_validation_report.json'
)
DEFAULT_ACADEMIC_TWOPHASE_INTERFACE_AMR = Path(
    'docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/'
    'academic_twophase_interface_amr_validation_report.json'
)
DEFAULT_ACADEMIC_DROPLET_EL = Path(
    'docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/'
    'academic_droplet_euler_lagrange_validation_report.json'
)
DEFAULT_ACADEMIC_SPRAY_DETONATION = Path(
    'docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/'
    'academic_spray_detonation_validation_report.json'
)
DEFAULT_ACADEMIC_SPRAY_DETONATION_SOURCE_BUDGET = Path(
    'docs/codex_audit/evidence/academic_spray_detonation_source_budget_validation_20260729/'
    'academic_spray_detonation_source_budget_validation_report.json'
)
DEFAULT_ACADEMIC_SPRAY_SOURCE_BUDGET_VALIDATION = Path(
    'docs/codex_audit/evidence/academic_spray_source_budget_validation_20260729/'
    'academic_spray_source_budget_validation_report.json'
)
DEFAULT_ACADEMIC_DROPLET_SPRAY_BUDGET_PREFLIGHT = Path(
    'docs/codex_audit/evidence/academic_droplet_spray_budget_preflight_20260729/'
    'academic_droplet_spray_budget_preflight_report.json'
)
DEFAULT_ACADEMIC_SPRAY_CLOSED_PARTICLE_BUDGET = Path(
    'docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/'
    'academic_spray_closed_particle_budget_report.json'
)
DEFAULT_ACADEMIC_SPRAY_COUPLED_BUDGET_RESIDUAL = Path(
    'docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/'
    'academic_spray_coupled_budget_residual_report.json'
)
DEFAULT_ACADEMIC_GPU_PREFLIGHT = Path(
    'docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/'
    'academic_gpu_environment_preflight_report.json'
)
DEFAULT_ACADEMIC_GAS_DOUBLE_MACH = Path(
    'docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/'
    'academic_gas_double_mach_validation_report.json'
)
DEFAULT_ACADEMIC_TWOPHASE_BUBBLE_RISE = Path(
    'docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/'
    'academic_twophase_bubble_rise_validation_report.json'
)
DEFAULT_ACADEMIC_MMS_SHIM = Path(
    'docs/codex_audit/evidence/academic_mms_shim_validation_20260728/'
    'academic_mms_shim_validation_report.json'
)
DEFAULT_ACADEMIC_MMS_NONCONSTANT_DENSITY_SHIM = Path(
    'docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729/'
    'academic_mms_nonconstant_density_shim_validation_report.json'
)
DEFAULT_REAL_CAD_BOUNDARY_TAG_CONTRACT = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724/'
    'real_cad_boundary_tag_contract_report.json'
)
DEFAULT_QUALITY_REVIEW_COVERAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_quality_review_coverage_20260724/'
    'h2_quality_review_coverage_report.json'
)

EXPECTED_REQUIREMENT_IDS = {
    *(f'ENG-{idx:02d}' for idx in range(1, 15)),
    *(f'ACD-{idx:02d}' for idx in range(1, 11)),
    *(f'QLT-{idx:02d}' for idx in range(1, 6)),
}
VALID_COVERAGE = {'PASS', 'PARTIAL', 'NOT_READY', 'DEFERRED'}

COVERAGE_RULES: dict[str, dict[str, Any]] = {
    'ENG-01': {
        'coverage': 'PARTIAL',
        'evidence': ['geometry_pipeline_smoke', 'real_cad_cleanup_package_report'],
        'gap': 'STL/synthetic geometry path exists, but production real-CAD/STEP cleanup evidence is still NOT_READY.',
    },
    'ENG-02': {
        'coverage': 'PASS',
        'evidence': ['geometry_pipeline_smoke', 'production_mesh_scout_report'],
        'gap': '',
    },
    'ENG-03': {
        'coverage': 'PASS',
        'evidence': ['refinement_tags_smoke', 'production_mesh_8rank_scout_report'],
        'gap': '',
    },
    'ENG-04': {
        'coverage': 'PARTIAL',
        'evidence': ['geometry_pipeline_smoke', 'real_cad_cleanup_package_report'],
        'gap': 'EB/STL pipeline is tested, but scorecard still blocks on synthetic geometry rather than real CAD cleanup.',
    },
    'ENG-05': {
        'coverage': 'PARTIAL',
        'evidence': ['wall_functions_smoke', 'bfs_kepsilon_reference_report', 'real_cad_boundary_tag_contract_report'],
        'gap': 'Boundary/wall-function evidence and a face-level BC tag contract exist, but real CAD boundary tags are not production-cleared.',
    },
    'ENG-06': {
        'coverage': 'PASS',
        'evidence': ['engineering_h2_reference_agreement_report', 'production_mesh_8rank_scout_report'],
        'gap': '',
    },
    'ENG-07': {
        'coverage': 'PASS',
        'evidence': ['wall_functions_smoke', 'engineering_bfs_kepsilon_reference_report'],
        'gap': '',
    },
    'ENG-08': {
        'coverage': 'PARTIAL',
        'evidence': ['evaporation_model_smoke', 'pool_vof_coupling_smoke'],
        'gap': 'Evaporation/pool coupling smoke tests exist, but no production calibrated liquid-pool release validation is attached.',
    },
    'ENG-09': {
        'coverage': 'PASS',
        'evidence': ['wind_profile_smoke'],
        'gap': '',
    },
    'ENG-10': {
        'coverage': 'PARTIAL',
        'evidence': ['ignition_consequence_report', 'fire_calibration_package_report'],
        'gap': 'Ignition and screening fire metrics pass, but calibrated radiation/overpressure data are still missing.',
    },
    'ENG-11': {
        'coverage': 'PASS',
        'evidence': ['yaml_parser_smoke'],
        'gap': '',
    },
    'ENG-12': {
        'coverage': 'PASS',
        'evidence': ['second_order_advection_smoke', 'isentropic_vortex_smoke'],
        'gap': '',
    },
    'ENG-13': {
        'coverage': 'PASS',
        'evidence': ['engineering_h2_mpi_scaling_report', 'hybrid_runtime_affinity_manifest'],
        'gap': '',
    },
    'ENG-14': {
        'coverage': 'DEFERRED',
        'evidence': ['academic_gpu_environment_preflight_report'],
        'gap': 'GPU backend is a later-phase plan item; current GPU preflight is NOT_READY due NVIDIA driver/library mismatch and missing CUDA runtime libraries.',
    },
    'ACD-01': {
        'coverage': 'PASS',
        'evidence': ['weno5_smoke', 'pelec_weno_smoke', 'academic_weno5_convergence_validation_report'],
        'gap': '',
    },
    'ACD-02': {
        'coverage': 'PASS',
        'evidence': ['ignition_consequence_report', 'academic_gas_detonation_readiness_report'],
        'gap': '',
    },
    'ACD-03': {
        'coverage': 'PASS',
        'evidence': ['sod_shock_tube_smoke', 'isentropic_vortex_smoke', 'pelec_weno_smoke', 'academic_gas_detonation_readiness_report'],
        'gap': '',
    },
    'ACD-04': {
        'coverage': 'PASS',
        'evidence': ['vof_fct_smoke', 'vof_plic_smoke', 'twophase_eos_smoke', 'twophase_hllc_smoke', 'academic_twophase_rayleigh_taylor_validation_report'],
        'gap': '',
    },
    'ACD-05': {
        'coverage': 'PARTIAL',
        'evidence': ['d2_law_smoke', 'academic_droplet_euler_lagrange_validation_report', 'academic_spray_source_budget_validation_report', 'academic_droplet_spray_budget_preflight_report', 'academic_spray_closed_particle_budget_report', 'academic_spray_coupled_budget_residual_report'],
        'gap': 'D2-law, shock-droplet response, gas/spray plotfield budgets, native particle binary budgets, closed fixed-particle budget, gas mass/species/energy source-history budgets, particle/source mass closure, and momentum-source sanity pass, but broad evaporating spray momentum/total-energy state closure plus external breakup/reference validation remain open.',
    },
    'ACD-06': {
        'coverage': 'PARTIAL',
        'evidence': ['csf_smoke', 'static_droplet_laplace_smoke'],
        'gap': 'CSF normal/curvature/source-work smoke evidence exists, but coupled capillary-wave or solver-coupled static-droplet CFD benchmark validation is still open.',
    },
    'ACD-07': {
        'coverage': 'PARTIAL',
        'evidence': ['academic_spray_detonation_validation_report', 'academic_spray_detonation_source_budget_validation_report', 'academic_droplet_spray_budget_preflight_report', 'academic_spray_coupled_budget_residual_report'],
        'gap': 'Reacting spray shock/detonation-style response, source-field mapping, particle/source mass closure, gas/spray plotfield budgets, native particle binary budgets, and coupled-budget residual diagnostics pass, but full cellular gas-liquid detonation morphology and external reference agreement remain open.',
    },
    'ACD-08': {
        'coverage': 'PASS',
        'evidence': ['refinement_tags_smoke', 'pelec_weno_smoke', 'academic_gas_detonation_readiness_report', 'academic_twophase_rayleigh_taylor_validation_report', 'academic_twophase_interface_amr_validation_report'],
        'gap': '',
    },
    'ACD-09': {
        'coverage': 'PASS',
        'evidence': ['engineering_h2_mpi_scaling_report', 'hybrid_runtime_affinity_manifest'],
        'gap': '',
    },
    'ACD-10': {
        'coverage': 'DEFERRED',
        'evidence': ['academic_gpu_environment_preflight_report'],
        'gap': 'Academic GPU backend is not verified on the current server because the CUDA detonation smoke cannot load required NVIDIA/CUDA runtime libraries.',
    },
    'QLT-01': {
        'coverage': 'PARTIAL',
        'evidence': ['docs/codex_audit', 'quality_review_coverage_report'],
        'gap': 'Audit records and a module coverage inventory exist, but independent Type A review-agent artifacts are not complete for every module.',
    },
    'QLT-02': {
        'coverage': 'PARTIAL',
        'evidence': ['h2_blocker_clearance_preflight_report', 'production_evidence_verification_report', 'quality_review_coverage_report'],
        'gap': 'Integration gates and a phase coverage inventory are machine-verified, but formal independent Type B review reports are not complete for every phase.',
    },
    'QLT-03': {
        'coverage': 'PARTIAL',
        'evidence': ['ctest_22', 'sod_shock_tube_smoke', 'isentropic_vortex_smoke', 'academic_weno5_convergence_validation_report', 'academic_gas_double_mach_validation_report', 'academic_twophase_bubble_rise_validation_report', 'academic_mms_shim_validation_report', 'academic_mms_nonconstant_density_shim_validation_report'],
        'gap': '22 smoke/verification tests plus WENO5 fifth-order convergence, Double-Mach, strengthened 6000-step low-CFL short-time bubble response, constant-state MMS wiring validation, and nonconstant-density MMS shim validation pass; external nonlinear MASA, canonical long physical-time bubble-rise stability, and experiment-grade comparisons remain incomplete.',
    },
    'QLT-04': {
        'coverage': 'PASS',
        'evidence': ['docs/codex_audit', 'h2_production_handoff_report'],
        'gap': '',
    },
    'QLT-05': {
        'coverage': 'DEFERRED',
        'evidence': ['academic_gpu_environment_preflight_report'],
        'gap': 'GPU compliance cannot receive credit until the NVIDIA driver/library mismatch and missing CUDA runtime libraries are repaired and the CUDA smoke gate passes.',
    },
}


class TraceabilityError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TraceabilityError(message)


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
        raise TraceabilityError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise TraceabilityError(f'invalid JSON evidence {path}: {exc}') from exc
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


def parse_requirements(master_plan: Path) -> list[dict[str, Any]]:
    require(master_plan.is_file(), f'missing master plan: {master_plan}')
    text = master_plan.read_text(encoding='utf-8', errors='replace')
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.startswith('|'):
            continue
        parts = [part.strip() for part in line.strip().strip('|').split('|')]
        if len(parts) < 3:
            continue
        req_id = parts[0]
        if not re.fullmatch(r'(ENG|ACD|QLT)-\d{2}', req_id):
            continue
        if req_id.startswith(('ENG', 'ACD')):
            priority = parts[2] if len(parts) >= 4 else ''
            description = parts[3] if len(parts) >= 4 else ''
        else:
            priority = ''
            description = parts[2] if len(parts) >= 3 else ''
        rows.append({
            'id': req_id,
            'requirement': parts[1],
            'priority': priority,
            'description': description,
            'source_line': line_no,
        })
    return rows


def build_matrix(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for req in requirements:
        req_id = req['id']
        rule = COVERAGE_RULES.get(req_id)
        require(rule is not None, f'missing coverage rule for {req_id}')
        coverage = str(rule['coverage'])
        require(coverage in VALID_COVERAGE, f'invalid coverage for {req_id}: {coverage}')
        matrix.append({
            **req,
            'coverage': coverage,
            'evidence_labels': list(rule.get('evidence', [])),
            'remaining_gap': str(rule.get('gap', '')),
        })
    return matrix


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    master_plan = Path(args.master_plan)
    production_path = Path(args.production_evidence_report)
    handoff_path = Path(args.production_handoff_report)
    preflight_path = Path(args.blocker_clearance_preflight_report)
    scorecard_path = Path(args.scorecard)
    academic_gas_path = Path(args.academic_gas_detonation_readiness_report)
    academic_weno5_convergence_path = Path(args.academic_weno5_convergence_validation_report)
    academic_twophase_rt_path = Path(args.academic_twophase_rayleigh_taylor_validation_report)
    academic_twophase_interface_amr_path = Path(args.academic_twophase_interface_amr_validation_report)
    academic_droplet_el_path = Path(args.academic_droplet_euler_lagrange_validation_report)
    academic_spray_detonation_path = Path(args.academic_spray_detonation_validation_report)
    academic_spray_detonation_source_budget_path = Path(args.academic_spray_detonation_source_budget_validation_report)
    academic_spray_source_budget_validation_path = Path(args.academic_spray_source_budget_validation_report)
    academic_droplet_spray_budget_preflight_path = Path(args.academic_droplet_spray_budget_preflight_report)
    academic_spray_closed_particle_budget_path = Path(args.academic_spray_closed_particle_budget_report)
    academic_spray_coupled_budget_residual_path = Path(args.academic_spray_coupled_budget_residual_report)
    academic_gpu_preflight_path = Path(args.academic_gpu_environment_preflight_report)
    academic_gas_double_mach_path = Path(args.academic_gas_double_mach_validation_report)
    academic_twophase_bubble_rise_path = Path(args.academic_twophase_bubble_rise_validation_report)
    academic_mms_shim_path = Path(args.academic_mms_shim_validation_report)
    academic_mms_nonconstant_density_shim_path = Path(args.academic_mms_nonconstant_density_shim_validation_report)
    boundary_tag_path = Path(args.real_cad_boundary_tag_contract_report)
    quality_review_path = Path(args.quality_review_coverage_report)
    production = load_json(production_path)
    handoff = load_json(handoff_path)
    preflight = load_json(preflight_path)
    scorecard = load_json(scorecard_path)
    academic_gas = load_json(academic_gas_path)
    academic_weno5_convergence = load_json(academic_weno5_convergence_path)
    academic_twophase_rt = load_json(academic_twophase_rt_path)
    academic_twophase_interface_amr = load_json(academic_twophase_interface_amr_path)
    academic_droplet_el = load_json(academic_droplet_el_path)
    academic_spray_detonation = load_json(academic_spray_detonation_path)
    academic_spray_detonation_source_budget = load_json(academic_spray_detonation_source_budget_path)
    academic_spray_source_budget_validation = load_json(academic_spray_source_budget_validation_path)
    academic_droplet_spray_budget_preflight = load_json(academic_droplet_spray_budget_preflight_path)
    academic_spray_closed_particle_budget = load_json(academic_spray_closed_particle_budget_path)
    academic_spray_coupled_budget_residual = load_json(academic_spray_coupled_budget_residual_path)
    academic_gpu_preflight = load_json(academic_gpu_preflight_path)
    academic_gas_double_mach = load_json(academic_gas_double_mach_path)
    academic_twophase_bubble_rise = load_json(academic_twophase_bubble_rise_path)
    academic_mms_shim = load_json(academic_mms_shim_path)
    academic_mms_nonconstant_density_shim = load_json(academic_mms_nonconstant_density_shim_path)
    boundary_tag = load_json(boundary_tag_path)
    quality_review = load_json(quality_review_path)
    academic_gas_summary = (
        academic_gas.get('summary', {})
        if isinstance(academic_gas.get('summary'), dict)
        else {}
    )
    academic_weno5_convergence_summary = (
        academic_weno5_convergence.get('summary', {})
        if isinstance(academic_weno5_convergence.get('summary'), dict)
        else {}
    )
    academic_twophase_rt_summary = (
        academic_twophase_rt.get('summary', {})
        if isinstance(academic_twophase_rt.get('summary'), dict)
        else {}
    )
    academic_twophase_interface_amr_summary = (
        academic_twophase_interface_amr.get('summary', {})
        if isinstance(academic_twophase_interface_amr.get('summary'), dict)
        else {}
    )
    academic_droplet_el_summary = (
        academic_droplet_el.get('summary', {})
        if isinstance(academic_droplet_el.get('summary'), dict)
        else {}
    )
    academic_spray_detonation_summary = (
        academic_spray_detonation.get('summary', {})
        if isinstance(academic_spray_detonation.get('summary'), dict)
        else {}
    )
    academic_spray_detonation_source_budget_summary = (
        academic_spray_detonation_source_budget.get('summary', {})
        if isinstance(academic_spray_detonation_source_budget.get('summary'), dict)
        else {}
    )
    academic_spray_source_budget_validation_summary = (
        academic_spray_source_budget_validation.get('summary', {})
        if isinstance(academic_spray_source_budget_validation.get('summary'), dict)
        else {}
    )
    academic_droplet_spray_budget_preflight_summary = (
        academic_droplet_spray_budget_preflight.get('summary', {})
        if isinstance(academic_droplet_spray_budget_preflight.get('summary'), dict)
        else {}
    )
    academic_spray_closed_particle_budget_summary = (
        academic_spray_closed_particle_budget.get('summary', {})
        if isinstance(academic_spray_closed_particle_budget.get('summary'), dict)
        else {}
    )
    academic_spray_coupled_budget_residual_summary = (
        academic_spray_coupled_budget_residual.get('summary', {})
        if isinstance(academic_spray_coupled_budget_residual.get('summary'), dict)
        else {}
    )
    academic_gpu_preflight_summary = (
        academic_gpu_preflight.get('summary', {})
        if isinstance(academic_gpu_preflight.get('summary'), dict)
        else {}
    )
    academic_gas_double_mach_summary = (
        academic_gas_double_mach.get('summary', {})
        if isinstance(academic_gas_double_mach.get('summary'), dict)
        else {}
    )
    academic_twophase_bubble_rise_summary = (
        academic_twophase_bubble_rise.get('summary', {})
        if isinstance(academic_twophase_bubble_rise.get('summary'), dict)
        else {}
    )
    academic_mms_shim_summary = (
        academic_mms_shim.get('summary', {})
        if isinstance(academic_mms_shim.get('summary'), dict)
        else {}
    )
    academic_mms_nonconstant_density_shim_summary = (
        academic_mms_nonconstant_density_shim.get('summary', {})
        if isinstance(academic_mms_nonconstant_density_shim.get('summary'), dict)
        else {}
    )
    requirements = parse_requirements(master_plan)
    ids = {item['id'] for item in requirements}
    require(ids == EXPECTED_REQUIREMENT_IDS, f'master plan requirement ids mismatch: missing={sorted(EXPECTED_REQUIREMENT_IDS - ids)} extra={sorted(ids - EXPECTED_REQUIREMENT_IDS)}')
    matrix = build_matrix(requirements)
    counts = {status: sum(1 for item in matrix if item['coverage'] == status) for status in sorted(VALID_COVERAGE)}
    p0_items = [item for item in matrix if item.get('priority') == 'P0']
    p0_not_pass = [item['id'] for item in p0_items if item['coverage'] != 'PASS']
    blocker_records = preflight.get('blocker_records') if isinstance(preflight.get('blocker_records'), list) else []
    production_summary = production.get('summary') if isinstance(production.get('summary'), dict) else {}
    ready = (
        production.get('status') == 'PASS'
        and handoff.get('status') == 'PASS-H2-PRODUCTION-HANDOFF'
        and scorecard.get('status') == 'PRODUCTION_READY'
        and counts.get('NOT_READY', 0) == 0
        and not p0_not_pass
    )
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS_PASS if ready else STATUS_NOT_READY,
        'title': 'Engineering H2 Master Plan Traceability Matrix',
        'master_plan': str(master_plan),
        'master_plan_sha256': sha256_file(master_plan),
        'production_evidence_report': str(production_path),
        'production_handoff_report': str(handoff_path),
        'blocker_clearance_preflight_report': str(preflight_path),
        'scorecard': str(scorecard_path),
        'current_scores': {
            'functional_coverage_percent': production_summary.get('scorecard_functional_percent'),
            'production_credibility_percent': production_summary.get('scorecard_production_credibility_percent'),
            'ctest_tests': production_summary.get('ctest_tests'),
            'ctest_passed': production_summary.get('ctest_passed'),
            'scorecard_status': scorecard.get('status'),
            'handoff_status': handoff.get('status'),
            'remaining_blocker_count': preflight.get('remaining_blocker_count'),
            'academic_gas_detonation_readiness_status': academic_gas.get('status'),
            'academic_gas_foundation_ready': academic_gas_summary.get('foundation_ready'),
            'academic_gas_short_2d_detonation_wave_validation_passed': academic_gas_summary.get(
                'short_2d_detonation_wave_validation_passed'
            ),
            'academic_gas_detonation_front_amr_validation_available': academic_gas_summary.get(
                'detonation_front_amr_validation_available'
            ),
            'academic_weno5_convergence_validation_status': academic_weno5_convergence.get('status'),
            'academic_weno5_convergence_clears_acd_01': academic_weno5_convergence_summary.get(
                'clears_acd_01_weno5_order_gap'
            ),
            'academic_weno5_convergence_clears_qlt_03': academic_weno5_convergence_summary.get(
                'clears_qlt_03_weno5_mms_order_subgap'
            ),
            'academic_weno5_convergence_pelec_p32_64': academic_weno5_convergence_summary.get(
                'pelec_weno5z_p32_64'
            ),
            'academic_weno5_convergence_pelec_p64_128': academic_weno5_convergence_summary.get(
                'pelec_weno5z_p64_128'
            ),
            'academic_weno5_convergence_error_ratio': academic_weno5_convergence_summary.get(
                'weno_to_second_order_error_ratio'
            ),
            'academic_twophase_rayleigh_taylor_status': academic_twophase_rt.get('status'),
            'academic_twophase_rayleigh_taylor_clears_acd_04': academic_twophase_rt_summary.get(
                'clears_acd_04_two_phase_validation_gap'
            ),
            'academic_twophase_interface_amr_available': academic_twophase_rt_summary.get(
                'clears_acd_08_two_phase_interface_amr_gap'
            ),
            'academic_twophase_interface_amr_validation_status': academic_twophase_interface_amr.get('status'),
            'academic_twophase_interface_amr_clears_acd_08': academic_twophase_interface_amr_summary.get(
                'clears_acd_08_two_phase_interface_amr_gap'
            ),
            'academic_droplet_euler_lagrange_status': academic_droplet_el.get('status'),
            'academic_droplet_euler_lagrange_clears_response_gate': academic_droplet_el_summary.get(
                'clears_acd_05_response_gate'
            ),
            'academic_droplet_euler_lagrange_clears_budget_gap': academic_droplet_el_summary.get(
                'clears_acd_05_closed_gas_particle_budget_gap'
            ),
            'academic_droplet_euler_lagrange_clears_external_reference_gap': academic_droplet_el_summary.get(
                'clears_acd_05_external_reference_gap'
            ),
            'academic_droplet_euler_lagrange_clears_acd_05': academic_droplet_el_summary.get(
                'clears_acd_05_euler_lagrange_gap'
            ),
            'academic_droplet_euler_lagrange_particle_growth_factor': academic_droplet_el_summary.get(
                'particle_growth_factor'
            ),
            'academic_spray_detonation_status': academic_spray_detonation.get('status'),
            'academic_spray_detonation_clears_response_gate': academic_spray_detonation_summary.get(
                'clears_acd_07_reacting_spray_response_gate'
            ),
            'academic_spray_detonation_clears_budget_gap': academic_spray_detonation_summary.get(
                'clears_acd_07_closed_gas_particle_budget_gap'
            ),
            'academic_spray_detonation_clears_cellular_detonation_gap': academic_spray_detonation_summary.get(
                'clears_acd_07_full_cellular_gas_liquid_detonation_gap'
            ),
            'academic_spray_detonation_clears_external_reference_gap': academic_spray_detonation_summary.get(
                'clears_acd_07_external_reference_gap'
            ),
            'academic_spray_detonation_clears_acd_07': academic_spray_detonation_summary.get(
                'clears_acd_07_spray_detonation_gap'
            ),
            'academic_spray_detonation_pressure_front_shift_cells': academic_spray_detonation_summary.get(
                'pressure_front_shift_cells'
            ),
            'academic_spray_detonation_source_budget_status': academic_spray_detonation_source_budget.get('status'),
            'academic_spray_detonation_source_budget_clears_subgate': academic_spray_detonation_source_budget_summary.get(
                'clears_acd_07_reacting_spray_detonation_budget'
            ),
            'academic_spray_detonation_source_budget_particle_mismatch': academic_spray_detonation_source_budget_summary.get(
                'particle_source_relative_mismatch'
            ),
            'academic_spray_detonation_source_budget_heat_release_absmax': academic_spray_detonation_source_budget_summary.get(
                'heatRelease_absmax'
            ),
            'academic_spray_detonation_source_budget_pressure_front_shift_cells': academic_spray_detonation_source_budget_summary.get(
                'pressure_front_shift_cells'
            ),
            'academic_spray_detonation_source_budget_clears_cellular_gap': academic_spray_detonation_source_budget_summary.get(
                'clears_acd_07_full_cellular_gas_liquid_detonation_gap'
            ),
            'academic_spray_detonation_source_budget_clears_external_reference_gap': academic_spray_detonation_source_budget_summary.get(
                'clears_acd_07_external_reference_gap'
            ),
            'academic_spray_detonation_source_budget_clears_broad_acd_07': academic_spray_detonation_source_budget_summary.get(
                'clears_acd_07_broad_spray_detonation_gap'
            ),
            'academic_spray_source_budget_validation_status': academic_spray_source_budget_validation.get('status'),
            'academic_spray_source_budget_clears_acd05_gas_source_history_budget': academic_spray_source_budget_validation_summary.get(
                'clears_acd_05_gas_source_history_budget'
            ),
            'academic_spray_source_budget_clears_acd05_full_gas_particle_budget': academic_spray_source_budget_validation_summary.get(
                'clears_acd_05_full_gas_particle_budget'
            ),
            'academic_spray_source_budget_particle_mismatch': academic_spray_source_budget_validation_summary.get(
                'particle_source_relative_mismatch'
            ),
            'academic_spray_source_budget_gas_mass_error': academic_spray_source_budget_validation_summary.get(
                'gas_mass_source_relative_error'
            ),
            'academic_spray_source_budget_fuel_error': academic_spray_source_budget_validation_summary.get(
                'fuel_source_relative_error'
            ),
            'academic_spray_source_budget_energy_error': academic_spray_source_budget_validation_summary.get(
                'energy_source_relative_error'
            ),
            'academic_spray_source_budget_energy_residual': academic_spray_source_budget_validation_summary.get(
                'energy_source_residual'
            ),
            'academic_spray_source_budget_max_abs_momentum_source_rate_integral': academic_spray_source_budget_validation_summary.get(
                'max_abs_momentum_source_rate_integral'
            ),
            'academic_spray_source_budget_clears_acd07': academic_spray_source_budget_validation_summary.get(
                'clears_acd_07_reacting_spray_detonation_budget'
            ),
            'academic_droplet_spray_budget_preflight_status': academic_droplet_spray_budget_preflight.get('status'),
            'academic_droplet_spray_budget_preflight_clears_plotfield_gate': academic_droplet_spray_budget_preflight_summary.get(
                'clears_projected_plotfield_budget_preflight'
            ),
            'academic_droplet_spray_budget_preflight_particle_binary_parser_ready': academic_droplet_spray_budget_preflight_summary.get(
                'per_particle_binary_budget_parser_ready'
            ),
            'academic_droplet_spray_budget_preflight_clears_full_budget_gap': academic_droplet_spray_budget_preflight_summary.get(
                'clears_full_closed_gas_particle_budget_gap'
            ),
            'academic_spray_closed_particle_budget_status': academic_spray_closed_particle_budget.get('status'),
            'academic_spray_closed_particle_budget_clears_fixed_particle_subgap': academic_spray_closed_particle_budget_summary.get(
                'clears_acd_05_closed_fixed_particle_budget_subgap'
            ),
            'academic_spray_closed_particle_budget_clears_full_acd05_budget': academic_spray_closed_particle_budget_summary.get(
                'clears_acd_05_full_gas_particle_budget_gap'
            ),
            'academic_spray_closed_particle_budget_mass_rel_drift': academic_spray_closed_particle_budget_summary.get(
                'mass_rel_drift'
            ),
            'academic_spray_coupled_budget_residual_status': academic_spray_coupled_budget_residual.get('status'),
            'academic_spray_coupled_budget_residual_particle_plotfield_ready': academic_spray_coupled_budget_residual_summary.get(
                'particle_plotfield_mass_consistency_ready'
            ),
            'academic_spray_coupled_budget_residual_signs_consistent': academic_spray_coupled_budget_residual_summary.get(
                'mass_transfer_signs_consistent'
            ),
            'academic_spray_coupled_budget_residual_source_history_available': academic_spray_coupled_budget_residual_summary.get(
                'source_history_accounting_available'
            ),
            'academic_spray_coupled_budget_residual_clears_acd05': academic_spray_coupled_budget_residual_summary.get(
                'clears_acd_05_coupled_budget_gap'
            ),
            'academic_spray_coupled_budget_residual_clears_acd07': academic_spray_coupled_budget_residual_summary.get(
                'clears_acd_07_coupled_budget_gap'
            ),
            'academic_spray_coupled_budget_residual_max_mass_residual_over_particle_loss': academic_spray_coupled_budget_residual_summary.get(
                'max_gas_plus_particle_mass_residual_over_particle_loss'
            ),
            'academic_gpu_environment_preflight_status': academic_gpu_preflight.get('status'),
            'academic_gpu_environment_ready_for_acd_10': academic_gpu_preflight_summary.get(
                'ready_for_acd_10_gpu_credit'
            ),
            'academic_gpu_environment_ready_for_qlt_05': academic_gpu_preflight_summary.get(
                'ready_for_qlt_05_gpu_compliance_credit'
            ),
            'academic_gpu_environment_blocking_reasons': academic_gpu_preflight_summary.get('blocking_reasons'),
            'academic_gas_double_mach_validation_status': academic_gas_double_mach.get('status'),
            'academic_gas_double_mach_clears_qlt_03_gap': academic_gas_double_mach_summary.get(
                'clears_qlt_03_double_mach_gap'
            ),
            'academic_gas_double_mach_front_x': academic_gas_double_mach_summary.get('front_x'),
            'academic_twophase_bubble_rise_validation_status': academic_twophase_bubble_rise.get('status'),
            'academic_twophase_bubble_rise_clears_short_time_response_gap': academic_twophase_bubble_rise_summary.get(
                'clears_qlt_03_short_time_bubble_response_gap'
            ),
            'academic_twophase_bubble_rise_clears_canonical_long_time_gap': academic_twophase_bubble_rise_summary.get(
                'clears_qlt_03_canonical_long_time_bubble_rise_gap'
            ),
            'academic_twophase_bubble_rise_clears_qlt_03_gap': academic_twophase_bubble_rise_summary.get(
                'clears_qlt_03_bubble_rise_gap'
            ),
            'academic_twophase_bubble_rise_centroid_rise': academic_twophase_bubble_rise_summary.get(
                'centroid_rise'
            ),
            'academic_mms_shim_validation_status': academic_mms_shim.get('status'),
            'academic_mms_shim_clears_qlt_03_wiring_gap': academic_mms_shim_summary.get(
                'clears_qlt_03_mms_wiring_gap'
            ),
            'academic_mms_shim_clears_nonlinear_masa_benchmark': academic_mms_shim_summary.get(
                'clears_nonlinear_masa_mms_benchmark'
            ),
            'academic_mms_shim_max_error': academic_mms_shim_summary.get('max_error'),
            'academic_mms_nonconstant_density_shim_validation_status': academic_mms_nonconstant_density_shim.get('status'),
            'academic_mms_nonconstant_density_shim_clears_qlt_03': academic_mms_nonconstant_density_shim_summary.get(
                'clears_qlt_03_nonconstant_mms_shim_gap'
            ),
            'academic_mms_nonconstant_density_shim_clears_external_nonlinear_masa': academic_mms_nonconstant_density_shim_summary.get(
                'clears_external_nonlinear_masa_benchmark'
            ),
            'academic_mms_nonconstant_density_shim_pressure_error_relative': academic_mms_nonconstant_density_shim_summary.get(
                'pressure_error_relative'
            ),
            'real_cad_boundary_tag_contract_status': boundary_tag.get('status'),
            'real_cad_boundary_tag_ready_for_credit': boundary_tag.get('ready_for_real_cad_bc_tagging_credit'),
            'quality_review_coverage_status': quality_review.get('status'),
            'quality_review_ready_for_qlt01_credit': quality_review.get('summary', {}).get('ready_for_qlt01_credit')
            if isinstance(quality_review.get('summary'), dict)
            else None,
            'quality_review_ready_for_qlt02_credit': quality_review.get('summary', {}).get('ready_for_qlt02_credit')
            if isinstance(quality_review.get('summary'), dict)
            else None,
        },
        'coverage_counts': counts,
        'p0_not_pass': p0_not_pass,
        'remaining_blockers': [
            {
                'domain': item.get('domain'),
                'blocker': item.get('blocker'),
                'failed_quality_gates': item.get('failed_quality_gates', []),
            }
            for item in blocker_records
            if isinstance(item, dict) and item.get('status') != 'CLEARED'
        ],
        'requirement_matrix': matrix,
        'evidence_files': [
            evidence_entry('master_plan', master_plan),
            evidence_entry('production_evidence_verification_report', production_path),
            evidence_entry('production_handoff_report', handoff_path),
            evidence_entry('blocker_clearance_preflight_report', preflight_path),
            evidence_entry('engineering_production_scorecard', scorecard_path),
            evidence_entry('academic_gas_detonation_readiness_report', academic_gas_path),
            evidence_entry('academic_weno5_convergence_validation_report', academic_weno5_convergence_path),
            evidence_entry('academic_twophase_rayleigh_taylor_validation_report', academic_twophase_rt_path),
            evidence_entry('academic_twophase_interface_amr_validation_report', academic_twophase_interface_amr_path),
            evidence_entry('academic_droplet_euler_lagrange_validation_report', academic_droplet_el_path),
            evidence_entry('academic_spray_detonation_validation_report', academic_spray_detonation_path),
            evidence_entry('academic_spray_detonation_source_budget_validation_report', academic_spray_detonation_source_budget_path),
            evidence_entry('academic_spray_source_budget_validation_report', academic_spray_source_budget_validation_path),
            evidence_entry('academic_droplet_spray_budget_preflight_report', academic_droplet_spray_budget_preflight_path),
            evidence_entry('academic_spray_closed_particle_budget_report', academic_spray_closed_particle_budget_path),
            evidence_entry('academic_spray_coupled_budget_residual_report', academic_spray_coupled_budget_residual_path),
            evidence_entry('academic_gpu_environment_preflight_report', academic_gpu_preflight_path),
            evidence_entry('academic_gas_double_mach_validation_report', academic_gas_double_mach_path),
            evidence_entry('academic_twophase_bubble_rise_validation_report', academic_twophase_bubble_rise_path),
            evidence_entry('academic_mms_shim_validation_report', academic_mms_shim_path),
            evidence_entry('academic_mms_nonconstant_density_shim_validation_report', academic_mms_nonconstant_density_shim_path),
            evidence_entry('real_cad_boundary_tag_contract_report', boundary_tag_path),
            evidence_entry('quality_review_coverage_report', quality_review_path),
        ],
        'limitations': [
            'This report traces master-plan requirements to current maintained evidence; it does not create new physical validation.',
            'PASS means evidence exists in the maintained verification chain, not external certification.',
            'PARTIAL and NOT_READY items require stronger validation or real external data before production readiness can be claimed.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_PASS, STATUS_NOT_READY}, 'invalid status')
    matrix = data.get('requirement_matrix')
    require(isinstance(matrix, list), 'requirement_matrix missing')
    ids = {str(item.get('id')) for item in matrix if isinstance(item, dict)}
    require(ids == EXPECTED_REQUIREMENT_IDS, 'requirement ids do not match master plan set')
    for item in matrix:
        require(isinstance(item, dict), 'matrix row is not an object')
        require(item.get('coverage') in VALID_COVERAGE, f"invalid coverage for {item.get('id')}")
        if item.get('coverage') == 'PASS':
            require(item.get('evidence_labels'), f"PASS row missing evidence labels: {item.get('id')}")
            require(not item.get('remaining_gap'), f"PASS row has remaining gap: {item.get('id')}")
        else:
            require(item.get('remaining_gap'), f"non-PASS row missing remaining gap: {item.get('id')}")
    counts = data.get('coverage_counts')
    require(isinstance(counts, dict), 'coverage_counts missing')
    require(sum(int(v) for v in counts.values()) == len(matrix), 'coverage counts do not sum to matrix length')
    status = data.get('current_scores')
    require(isinstance(status, dict), 'current_scores missing')
    require(status.get('ctest_passed') is True, 'traceability requires passing CTest evidence')
    require(int(status.get('ctest_tests', 0)) == 22, 'traceability CTest count mismatch')
    require(
        status.get('academic_gas_detonation_readiness_status')
        in {
            'PASS-ACADEMIC-GAS-DETONATION-READINESS',
            'PARTIAL-ACADEMIC-GAS-DETONATION-READINESS',
            'NOT_READY-ACADEMIC-GAS-DETONATION-READINESS',
        },
        'invalid academic gas detonation readiness status',
    )
    require(
        status.get('academic_weno5_convergence_validation_status')
        == 'PASS-ACADEMIC-WENO5-CONVERGENCE-VALIDATION',
        'invalid academic WENO5 convergence validation status',
    )
    require(
        status.get('academic_weno5_convergence_clears_acd_01') is True,
        'academic WENO5 convergence validation must clear ACD-01 order gap',
    )
    require(
        status.get('academic_weno5_convergence_clears_qlt_03') is True,
        'academic WENO5 convergence validation must clear QLT-03 WENO order subgap',
    )
    require(
        float(status.get('academic_weno5_convergence_pelec_p32_64', 0.0)) >= 4.5,
        'PeleC WENO5-Z p32-64 order below traceability gate',
    )
    require(
        float(status.get('academic_weno5_convergence_pelec_p64_128', 0.0)) >= 4.5,
        'PeleC WENO5-Z p64-128 order below traceability gate',
    )
    require(
        float(status.get('academic_weno5_convergence_error_ratio', 1.0)) <= 0.02,
        'PeleC WENO5-Z error ratio above traceability gate',
    )
    require(
        status.get('academic_twophase_rayleigh_taylor_status')
        == 'PASS-ACADEMIC-TWOPHASE-RAYLEIGH-TAYLOR-VALIDATION',
        'invalid academic two-phase Rayleigh-Taylor validation status',
    )
    require(
        status.get('academic_twophase_rayleigh_taylor_clears_acd_04') is True,
        'academic two-phase validation must clear ACD-04',
    )
    require(
        status.get('academic_twophase_interface_amr_available') is False,
        'Rayleigh-Taylor uniform-grid validation cannot clear two-phase interface AMR',
    )
    require(
        status.get('academic_twophase_interface_amr_validation_status')
        == 'PASS-ACADEMIC-TWOPHASE-INTERFACE-AMR-VALIDATION',
        'invalid academic two-phase interface AMR validation status',
    )
    require(
        status.get('academic_twophase_interface_amr_clears_acd_08') is True,
        'academic two-phase interface AMR validation must clear ACD-08',
    )
    require(
        status.get('academic_droplet_euler_lagrange_status')
        == 'PASS-ACADEMIC-DROPLET-EULER-LAGRANGE-VALIDATION',
        'invalid academic droplet Euler-Lagrange validation status',
    )
    require(
        status.get('academic_droplet_euler_lagrange_clears_response_gate') is True,
        'academic droplet Euler-Lagrange validation must clear the maintained response gate',
    )
    require(
        status.get('academic_droplet_euler_lagrange_clears_budget_gap') is False,
        'academic droplet Euler-Lagrange validation must not clear closed gas+particle budget',
    )
    require(
        status.get('academic_droplet_euler_lagrange_clears_external_reference_gap') is False,
        'academic droplet Euler-Lagrange validation must not clear external reference validation',
    )
    require(
        status.get('academic_droplet_euler_lagrange_clears_acd_05') is False,
        'academic droplet Euler-Lagrange validation must not clear broad ACD-05',
    )
    require(
        status.get('academic_spray_detonation_status')
        == 'PASS-ACADEMIC-SPRAY-DETONATION-VALIDATION',
        'invalid academic spray detonation validation status',
    )
    require(
        status.get('academic_spray_detonation_clears_response_gate') is True,
        'academic spray detonation validation must clear the maintained response gate',
    )
    require(
        status.get('academic_spray_detonation_clears_budget_gap') is False,
        'academic spray detonation validation must not clear closed gas+particle budget',
    )
    require(
        status.get('academic_spray_detonation_clears_cellular_detonation_gap') is False,
        'academic spray detonation validation must not clear cellular gas-liquid detonation',
    )
    require(
        status.get('academic_spray_detonation_clears_external_reference_gap') is False,
        'academic spray detonation validation must not clear external reference validation',
    )
    require(
        status.get('academic_spray_detonation_clears_acd_07') is False,
        'academic spray detonation validation must not clear broad ACD-07',
    )
    require(
        status.get('academic_spray_detonation_source_budget_status')
        == 'PASS-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION',
        'invalid academic spray detonation source-budget validation status',
    )
    require(
        status.get('academic_spray_detonation_source_budget_clears_subgate') is True,
        'academic spray detonation source-budget validation must clear the maintained ACD-07 source-budget subgate',
    )
    require(
        float(status.get('academic_spray_detonation_source_budget_particle_mismatch', 1.0)) <= 5.0e-3,
        'academic spray detonation source-budget particle/source mismatch too large',
    )
    require(
        float(status.get('academic_spray_detonation_source_budget_heat_release_absmax', 0.0)) > 0.0,
        'academic spray detonation source-budget heat release must be nonzero',
    )
    require(
        float(status.get('academic_spray_detonation_source_budget_pressure_front_shift_cells', 0.0)) > 0.0,
        'academic spray detonation source-budget pressure front must move',
    )
    require(
        status.get('academic_spray_detonation_source_budget_clears_cellular_gap') is False,
        'academic spray detonation source-budget validation must not clear cellular gas-liquid detonation',
    )
    require(
        status.get('academic_spray_detonation_source_budget_clears_external_reference_gap') is False,
        'academic spray detonation source-budget validation must not clear external reference validation',
    )
    require(
        status.get('academic_spray_detonation_source_budget_clears_broad_acd_07') is False,
        'academic spray detonation source-budget validation must not clear broad ACD-07',
    )
    require(
        status.get('academic_spray_source_budget_validation_status')
        == 'PASS-ACADEMIC-SPRAY-SOURCE-BUDGET-VALIDATION',
        'invalid academic spray source-budget validation status',
    )
    require(
        status.get('academic_spray_source_budget_clears_acd05_gas_source_history_budget') is True,
        'academic spray source-budget validation must clear the ACD-05 gas source-history budget subgate',
    )
    require(
        status.get('academic_spray_source_budget_clears_acd05_full_gas_particle_budget') is True,
        'academic spray source-budget validation must clear the maintained ACD-05 gas/particle source-budget subgate',
    )
    require(
        float(status.get('academic_spray_source_budget_particle_mismatch', 1.0)) <= 1.0e-3,
        'academic spray source-budget particle/source mismatch too large',
    )
    require(
        float(status.get('academic_spray_source_budget_gas_mass_error', 1.0)) <= 1.0e-3,
        'academic spray source-budget gas mass error too large',
    )
    require(
        float(status.get('academic_spray_source_budget_fuel_error', 1.0)) <= 1.0e-3,
        'academic spray source-budget fuel error too large',
    )
    require(
        float(status.get('academic_spray_source_budget_energy_error', 1.0)) <= 1.0e-3,
        'academic spray source-budget energy error too large',
    )
    require(
        abs(float(status.get('academic_spray_source_budget_energy_residual', 1.0))) <= 1.0e-6,
        'academic spray source-budget energy residual too large',
    )
    require(
        abs(float(status.get('academic_spray_source_budget_max_abs_momentum_source_rate_integral', 1.0))) <= 1.0e-12,
        'academic spray source-budget momentum-source sanity check failed',
    )
    require(
        status.get('academic_spray_source_budget_clears_acd07') is False,
        'academic spray source-budget validation must not clear reacting spray detonation ACD-07',
    )
    require(
        status.get('academic_droplet_spray_budget_preflight_status')
        == 'PASS-ACADEMIC-DROPLET-SPRAY-PLOTFIELD-BUDGET-PREFLIGHT',
        'invalid academic droplet/spray budget preflight status',
    )
    require(
        status.get('academic_droplet_spray_budget_preflight_clears_plotfield_gate') is True,
        'academic droplet/spray budget preflight must clear the plotfield budget gate',
    )
    require(
        status.get('academic_droplet_spray_budget_preflight_particle_binary_parser_ready') is True,
        'academic droplet/spray budget preflight must clear particle binary parser readiness',
    )
    require(
        status.get('academic_droplet_spray_budget_preflight_clears_full_budget_gap') is False,
        'academic droplet/spray budget preflight must not clear full closed gas+particle budget',
    )
    require(
        status.get('academic_spray_closed_particle_budget_status')
        == 'PASS-ACADEMIC-SPRAY-CLOSED-PARTICLE-BUDGET',
        'invalid academic spray closed particle budget status',
    )
    require(
        status.get('academic_spray_closed_particle_budget_clears_fixed_particle_subgap') is True,
        'academic spray closed particle budget must clear the fixed-particle budget subgap',
    )
    require(
        status.get('academic_spray_closed_particle_budget_clears_full_acd05_budget') is False,
        'academic spray closed particle budget must not clear the full ACD-05 budget',
    )
    require(
        float(status.get('academic_spray_closed_particle_budget_mass_rel_drift', 1.0)) <= 1.0e-14,
        'academic spray closed particle budget mass drift above traceability threshold',
    )
    require(
        status.get('academic_spray_coupled_budget_residual_status')
        == 'PASS-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL',
        'invalid academic spray coupled budget residual status',
    )
    require(
        status.get('academic_spray_coupled_budget_residual_particle_plotfield_ready') is True,
        'academic spray coupled residual must preserve particle/plotfield mass consistency',
    )
    require(
        status.get('academic_spray_coupled_budget_residual_signs_consistent') is True,
        'academic spray coupled residual must preserve mass-transfer sign sanity',
    )
    require(
        status.get('academic_spray_coupled_budget_residual_source_history_available') is True,
        'academic spray coupled residual must link maintained source-history accounting evidence',
    )
    require(
        status.get('academic_spray_coupled_budget_residual_clears_acd05') is True,
        'academic spray coupled residual must clear ACD-05 through closed control-volume budget evidence',
    )
    require(
        status.get('academic_spray_coupled_budget_residual_clears_acd07') is True,
        'academic spray coupled residual must clear ACD-07 through reacting closed control-volume budget evidence',
    )
    require(
        float(status.get('academic_spray_coupled_budget_residual_max_mass_residual_over_particle_loss', 0.0)) > 1.0,
        'academic spray coupled residual should retain endpoint residual diagnostics',
    )
    require(
        status.get('academic_gpu_environment_preflight_status')
        in {'PASS-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT', 'NOT_READY-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT'},
        'invalid academic GPU environment preflight status',
    )
    if status.get('academic_gpu_environment_preflight_status') == 'NOT_READY-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT':
        require(
            status.get('academic_gpu_environment_ready_for_acd_10') is False,
            'NOT_READY GPU preflight must not clear ACD-10',
        )
        require(
            status.get('academic_gpu_environment_blocking_reasons'),
            'NOT_READY GPU preflight must list blockers',
        )
    require(
        status.get('academic_gas_double_mach_validation_status')
        == 'PASS-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION',
        'invalid academic gas Double-Mach validation status',
    )
    require(
        status.get('academic_gas_double_mach_clears_qlt_03_gap') is True,
        'academic gas Double-Mach validation must clear the QLT-03 Double-Mach subgap',
    )
    require(
        status.get('academic_twophase_bubble_rise_validation_status')
        in {'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION', 'NOT_READY-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION'},
        'invalid academic two-phase bubble-rise validation status',
    )
    if status.get('academic_twophase_bubble_rise_validation_status') == 'PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION':
        require(
            status.get('academic_twophase_bubble_rise_clears_short_time_response_gap') is True,
            'academic two-phase bubble-rise validation must clear only the short-time response subgap',
        )
        require(
            status.get('academic_twophase_bubble_rise_clears_canonical_long_time_gap') is False,
            'academic two-phase bubble-rise validation must not clear canonical long-time stability',
        )
        require(
            status.get('academic_twophase_bubble_rise_clears_qlt_03_gap') is False,
            'academic two-phase bubble-rise validation must not clear the broad QLT-03 bubble-rise gap',
        )
    else:
        require(
            status.get('academic_twophase_bubble_rise_clears_short_time_response_gap') is False,
            'NOT_READY bubble-rise validation must not clear the short-time response subgap',
        )
        require(
            status.get('academic_twophase_bubble_rise_clears_qlt_03_gap') is False,
            'NOT_READY bubble-rise validation must not clear the QLT-03 bubble-rise subgap',
        )
    require(
        status.get('academic_mms_shim_validation_status')
        in {'PASS-ACADEMIC-MMS-SHIM-VALIDATION', 'NOT_READY-ACADEMIC-MMS-SHIM-VALIDATION'},
        'invalid academic MMS shim validation status',
    )
    if status.get('academic_mms_shim_validation_status') == 'PASS-ACADEMIC-MMS-SHIM-VALIDATION':
        require(
            status.get('academic_mms_shim_clears_qlt_03_wiring_gap') is True,
            'academic MMS shim must clear the QLT-03 MMS wiring subgap',
        )
        require(
            status.get('academic_mms_shim_clears_nonlinear_masa_benchmark') is False,
            'academic MMS shim must not clear nonlinear MASA benchmark',
        )
    else:
        require(
            status.get('academic_mms_shim_clears_qlt_03_wiring_gap') is False,
            'NOT_READY MMS shim validation must not clear the wiring subgap',
        )
    require(
        status.get('academic_mms_nonconstant_density_shim_validation_status')
        == 'PASS-ACADEMIC-MMS-NONCONSTANT-DENSITY-SHIM-VALIDATION',
        'invalid academic MMS nonconstant-density shim validation status',
    )
    require(
        status.get('academic_mms_nonconstant_density_shim_clears_qlt_03') is True,
        'academic MMS nonconstant-density shim must clear its QLT-03 subgap',
    )
    require(
        status.get('academic_mms_nonconstant_density_shim_clears_external_nonlinear_masa') is False,
        'nonconstant-density shim must not clear external nonlinear MASA benchmark',
    )
    require(
        float(status.get('academic_mms_nonconstant_density_shim_pressure_error_relative', 1.0)) <= 1.0e-7,
        'nonconstant-density MMS pressure relative error exceeds traceability gate',
    )
    require(
        status.get('real_cad_boundary_tag_contract_status')
        in {'PASS-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT', 'NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT'},
        'invalid real-CAD boundary tag contract status',
    )
    require(
        status.get('quality_review_coverage_status') == 'PASS-H2-QUALITY-REVIEW-COVERAGE',
        'invalid quality review coverage status',
    )
    require(status.get('quality_review_ready_for_qlt01_credit') is False, 'QLT-01 credit should remain false')
    require(status.get('quality_review_ready_for_qlt02_credit') is False, 'QLT-02 credit should remain false')
    if data.get('status') == STATUS_PASS:
        require(status.get('scorecard_status') == 'PRODUCTION_READY', 'PASS traceability requires production-ready scorecard')
        require(not data.get('remaining_blockers'), 'PASS traceability has remaining blockers')
        require(not data.get('p0_not_pass'), 'PASS traceability has P0 requirements not PASS')
    else:
        require(status.get('scorecard_status') == 'NOT_PRODUCTION_READY', 'NOT_READY traceability should reflect not-ready scorecard')
        require(data.get('remaining_blockers'), 'NOT_READY traceability must list remaining blockers')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')
        master = Path(str(data.get('master_plan', '')))
        require(sha256_file(master) == data.get('master_plan_sha256'), 'master plan sha256 mismatch')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Master Plan Traceability Matrix',
        '',
        f"Status: `{report['status']}`",
        f"Master plan: `{report['master_plan']}` sha256 `{report['master_plan_sha256'][:16]}`",
        '',
        '## Current Scores',
        '',
    ]
    for key, value in report['current_scores'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Coverage Counts', '']
    for key, value in report['coverage_counts'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Requirement Matrix', '', '| ID | Requirement | Priority | Coverage | Evidence | Gap |', '| --- | --- | --- | --- | --- | --- |']
    for item in report['requirement_matrix']:
        evidence = '; '.join(item['evidence_labels']) or 'none'
        gap = item['remaining_gap'] or 'none'
        lines.append(
            f"| `{item['id']}` | {item['requirement']} | `{item['priority']}` | `{item['coverage']}` | {evidence} | {gap} |"
        )
    lines += ['', '## Remaining Blockers', '']
    for item in report['remaining_blockers']:
        failed = '; '.join(item.get('failed_quality_gates', [])) or 'none'
        lines.append(f"- `{item['domain']}`: `{item['blocker']}` failed gates `{failed}`")
    lines += ['', '## Evidence Files', '']
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--master-plan', default=str(DEFAULT_MASTER_PLAN))
    parser.add_argument('--production-evidence-report', default=str(DEFAULT_PRODUCTION_EVIDENCE))
    parser.add_argument('--production-handoff-report', default=str(DEFAULT_HANDOFF))
    parser.add_argument('--blocker-clearance-preflight-report', default=str(DEFAULT_PREFLIGHT))
    parser.add_argument('--scorecard', default=str(DEFAULT_SCORECARD))
    parser.add_argument('--academic-gas-detonation-readiness-report', default=str(DEFAULT_ACADEMIC_GAS))
    parser.add_argument('--academic-weno5-convergence-validation-report', default=str(DEFAULT_ACADEMIC_WENO5_CONVERGENCE))
    parser.add_argument('--academic-twophase-rayleigh-taylor-validation-report', default=str(DEFAULT_ACADEMIC_TWOPHASE_RT))
    parser.add_argument('--academic-twophase-interface-amr-validation-report', default=str(DEFAULT_ACADEMIC_TWOPHASE_INTERFACE_AMR))
    parser.add_argument('--academic-droplet-euler-lagrange-validation-report', default=str(DEFAULT_ACADEMIC_DROPLET_EL))
    parser.add_argument('--academic-spray-detonation-validation-report', default=str(DEFAULT_ACADEMIC_SPRAY_DETONATION))
    parser.add_argument('--academic-spray-detonation-source-budget-validation-report', default=str(DEFAULT_ACADEMIC_SPRAY_DETONATION_SOURCE_BUDGET))
    parser.add_argument('--academic-spray-source-budget-validation-report', default=str(DEFAULT_ACADEMIC_SPRAY_SOURCE_BUDGET_VALIDATION))
    parser.add_argument('--academic-droplet-spray-budget-preflight-report', default=str(DEFAULT_ACADEMIC_DROPLET_SPRAY_BUDGET_PREFLIGHT))
    parser.add_argument('--academic-spray-closed-particle-budget-report', default=str(DEFAULT_ACADEMIC_SPRAY_CLOSED_PARTICLE_BUDGET))
    parser.add_argument('--academic-spray-coupled-budget-residual-report', default=str(DEFAULT_ACADEMIC_SPRAY_COUPLED_BUDGET_RESIDUAL))
    parser.add_argument('--academic-gpu-environment-preflight-report', default=str(DEFAULT_ACADEMIC_GPU_PREFLIGHT))
    parser.add_argument('--academic-gas-double-mach-validation-report', default=str(DEFAULT_ACADEMIC_GAS_DOUBLE_MACH))
    parser.add_argument('--academic-twophase-bubble-rise-validation-report', default=str(DEFAULT_ACADEMIC_TWOPHASE_BUBBLE_RISE))
    parser.add_argument('--academic-mms-shim-validation-report', default=str(DEFAULT_ACADEMIC_MMS_SHIM))
    parser.add_argument('--academic-mms-nonconstant-density-shim-validation-report', default=str(DEFAULT_ACADEMIC_MMS_NONCONSTANT_DENSITY_SHIM))
    parser.add_argument('--real-cad-boundary-tag-contract-report', default=str(DEFAULT_REAL_CAD_BOUNDARY_TAG_CONTRACT))
    parser.add_argument('--quality-review-coverage-report', default=str(DEFAULT_QUALITY_REVIEW_COVERAGE))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            print(
                'engineering_h2_master_plan_traceability VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"requirements={len(report['requirement_matrix'])}"
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
            'engineering_h2_master_plan_traceability PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"requirements={len(report['requirement_matrix'])}"
        )
        return 0
    except TraceabilityError as exc:
        print(f'engineering_h2_master_plan_traceability FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
