#!/usr/bin/env python3
"""Write a strict engineering production-readiness scorecard from local evidence.

The scorecard intentionally separates engineering functional coverage from
production credibility. It fails closed when required evidence files are absent,
when hashes no longer match, or when known production blockers remain open.
"""
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

DEFAULT_CAMPAIGN_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.json'
)
DEFAULT_RELEASE_PACK = Path(
    'docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json'
)
DEFAULT_AFFINITY = Path(
    'docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json'
)
DEFAULT_HYBRID_AFFINITY = Path(
    'docs/codex_audit/evidence/engineering_runtime_affinity_hybrid_20260720/runtime_affinity_manifest.json'
)
DEFAULT_SCHEDULER = Path(
    'docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json'
)
DEFAULT_IGNITION = Path(
    'docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json'
)
DEFAULT_FIRE_CONSEQUENCE_METRICS = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json'
)
DEFAULT_PRODUCTION_SCALE_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/production_scale_scout_report.json'
)
DEFAULT_LONG_STABILITY_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/long_stability_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_8RANK_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_16RANK_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_8RANK_600STEP_STABILITY_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_600STEP_STABILITY_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/production_mesh_600step_stability_scout_report.json'
)
DEFAULT_PRODUCTION_MESH_1200STEP_STABILITY_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json'
)
DEFAULT_ENGINEERING_H2_PRODUCTION_MESH_CAMPAIGN = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.json'
)
DEFAULT_ENGINEERING_H2_FULL_DURATION_CANDIDATE = Path(
    'docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/full_duration_candidate_report.json'
)
DEFAULT_ENGINEERING_H2_ACCEPTANCE_MATRIX = Path(
    'docs/codex_audit/evidence/engineering_h2_acceptance_matrix_20260720/engineering_h2_acceptance_matrix.json'
)
DEFAULT_ENGINEERING_H2_MPI_SCALING = Path(
    'docs/codex_audit/evidence/engineering_h2_mpi_scaling_20260720/mpi_scaling_report.json'
)
DEFAULT_ENGINEERING_H2_HYBRID_CFD_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json'
)
DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/hybrid_production_mesh_scout_report.json'
)
DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_8RANK_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/hybrid_production_mesh_8rank_scout_report.json'
)
DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_8RANK_600STEP_STABILITY_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_600step_stability_scout_20260721/hybrid_production_mesh_8rank_600step_stability_scout_report.json'
)
DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_600STEP_STABILITY_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/hybrid_production_mesh_600step_stability_scout_report.json'
)
DEFAULT_ENGINEERING_H2_HYBRID_LARGEGRID_8RANK_120STEP_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/hybrid_largegrid_8rank_120step_scout_report.json'
)
DEFAULT_ENGINEERING_H2_REFERENCE_AGREEMENT = Path(
    'docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json'
)
DEFAULT_ENGINEERING_BFS_KEPSILON_REFERENCE = Path(
    'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json'
)
DEFAULT_ENGINEERING_H2_ENGINEERING_SCENE_CLEARANCE = Path(
    'docs/codex_audit/evidence/engineering_h2_engineering_scene_clearance_20260727/'
    'h2_engineering_scene_clearance_report.json'
)
DEFAULT_ENGINEERING_H2_PIPE_RACK_GPU_FIRE_OBSTACLE = Path(
    'docs/codex_audit/evidence/engineering_h2_pipe_rack_gpu_fire_obstacle_20260727/'
    'pipe_rack_gpu_fire_obstacle_report.json'
)
DEFAULT_ENGINEERING_H2_REACTING_MPI_CUDA_SMOKE = Path(
    'docs/codex_audit/evidence/engineering_h2_reacting_mpi_cuda_smoke_20260727/'
    'reacting_mpi_cuda_smoke_report.json'
)
DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_CUDA = Path(
    'docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_cuda_2000step_20260727/'
    'pipe_rack_direct_reacting_cuda_report.json'
)
DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_MPI_CUDA = Path(
    'docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_2000step_20260727/'
    'pipe_rack_direct_reacting_mpi_cuda_report.json'
)
DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_LARGEGRID_CUDA = Path(
    'docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_20260727/'
    'pipe_rack_direct_reacting_cuda_report.json'
)
DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_LARGEGRID_MPI_CUDA = Path(
    'docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_20260727/'
    'pipe_rack_direct_reacting_mpi_cuda_report.json'
)
DEFAULT_ENGINEERING_H2_PIPE_RACK_REACTING_MPI_CUDA_RESTART = Path(
    'docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_restart_20260727/'
    'pipe_rack_reacting_mpi_cuda_restart_report.json'
)
DEFAULT_ENGINEERING_H2_FIRE_CONSEQUENCE_TRACEABILITY = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_consequence_traceability_20260727/'
    'fire_consequence_traceability_report.json'
)
DEFAULT_ENGINEERING_H2_INTEGRATED_INITIAL_ACCEPTANCE = Path(
    'docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728/'
    'h2_integrated_initial_acceptance_report.json'
)

REQUIRED_SUITES = {
    'h2-core',
    'h2-source-physics',
    'h2-geometry',
    'h2-amr-mpi',
    'h2-production-scout',
}
REQUIRED_CASES = {
    'open-domain',
    'release-rate',
    'crosswind',
    'low-wind',
    'pressure-orifice',
    'real-gas-orifice',
    'tank-blowdown',
    'real-gas-tank-blowdown',
    'pipe-loss',
    'linepack-blowdown',
    'linepack-valve-schedule',
    'tank-farm',
    'stl-multifile',
    'stl-perfile-transform',
    'plan-amr-mpi-rank-sweep',
    'plan-amr-mpi-reduced-long',
}

PRODUCTION_BLOCKERS = [
    'bfs_kepsilon_reference_validation_failed',
]


class ScorecardError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open() as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise ScorecardError(f'missing evidence file: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ScorecardError(f'invalid JSON in {path}: {exc}') from exc
    if not isinstance(data, dict):
        raise ScorecardError(f'evidence JSON is not an object: {path}')
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def check_by_name(report: dict[str, Any], name: str) -> dict[str, Any] | None:
    checks = report.get('checks')
    if not isinstance(checks, list):
        return None
    for check in checks:
        if isinstance(check, dict) and check.get('name') == name:
            return check
    return None


def scheduler_blocking_gap(scheduler: dict[str, Any]) -> str | None:
    if scheduler.get('status') == 'PASS':
        return None
    accepted = check_by_name(scheduler, 'scheduler_submit_job_accepted')
    if accepted and accepted.get('status') != 'PASS':
        detail = str(accepted.get('detail', ''))
        if 'CONTROLLER_UNAVAILABLE' in detail or 'could not contact' in detail:
            return 'scheduler_controller_unavailable_or_job_not_accepted'
        return 'scheduler_job_not_accepted'
    run_summary = check_by_name(scheduler, 'campaign_run_summary_exists')
    if run_summary and run_summary.get('status') != 'PASS':
        return 'scheduler_run_summary_missing'
    return 'scheduler_run_summary_or_controller_not_ready'


def campaign_scale_blocking_gap(campaign: dict[str, Any], production_mesh_campaign: dict[str, Any] | None = None) -> str | None:
    if (
        campaign.get('production_campaign') is True
        and campaign.get('production_size_mesh_campaign') is True
        and campaign.get('full_duration_campaign') is True
    ):
        return None
    if production_mesh_campaign and production_mesh_campaign.get('status') == 'PASS-PRODUCTION-MESH-CAMPAIGN-SCOUT':
        if (
            production_mesh_campaign.get('production_size_mesh_campaign') is True
            and production_mesh_campaign.get('full_duration_campaign') is False
        ):
            return 'campaign_evidence_is_production_mesh_scout_not_full_duration'
    if production_mesh_campaign and (
        production_mesh_campaign.get('status') == 'PASS-PRODUCTION-MESH-FULL-DURATION-CAMPAIGN'
        and production_mesh_campaign.get('production_size_mesh_campaign') is True
        and production_mesh_campaign.get('full_duration_campaign') is True
        and production_mesh_campaign.get('full_plotfile_archive') is True
    ):
        return None
    scale = str(campaign.get('campaign_scale') or 'unspecified').strip().lower()
    if scale == 'engineering_regression_smoke':
        return 'campaign_evidence_is_smoke_regression_not_production_size'
    if scale == 'engineering_reduced_long_scout':
        return 'campaign_evidence_is_reduced_long_scout_not_production_size'
    return 'production_size_mesh_campaign_missing'


def stability_duration_blocking_gap(
    stability_report: dict[str, Any],
    full_duration_candidate: dict[str, Any] | None = None,
) -> str | None:
    if (
        (
            stability_report.get('full_duration_campaign') is True
            or stability_report.get('overnight_campaign') is True
        )
        and stability_report.get('full_plotfile_archive') is True
    ):
        return None
    if full_duration_candidate and (
        full_duration_candidate.get('status') == 'PASS-FULL-DURATION-EXECUTED'
        or (
            full_duration_candidate.get('status') == 'PASS-FULL-DURATION-CANDIDATE'
            and full_duration_candidate.get('executed') is True
            and full_duration_candidate.get('clears_stability_duration_blocker') is True
        )
    ):
        return None
    if full_duration_candidate and full_duration_candidate.get('status') == 'PASS-FULL-DURATION-CANDIDATE':
        return 'stability_evidence_is_production_mesh_1200step_scout_with_full_duration_candidate_not_executed'
    if full_duration_candidate and full_duration_candidate.get('status') == 'NOT_READY-FULL-DURATION-CANDIDATE':
        gaps = full_duration_candidate.get('blocking_gaps', [])
        if isinstance(gaps, list) and 'insufficient_free_disk_for_full_duration_candidate' in gaps:
            return 'stability_full_duration_candidate_blocked_by_insufficient_disk'
        return 'stability_full_duration_candidate_not_ready'
    duration_class = str(stability_report.get('stability_duration_class') or '').strip().lower()
    if duration_class:
        return f'stability_evidence_is_{duration_class}_not_overnight_or_full_duration'
    case = str(stability_report.get('case') or '').lower()
    if '1200step' in case:
        return 'stability_evidence_is_production_mesh_1200step_stability_scout_not_overnight_or_full_duration'
    if '600step' in case:
        return 'stability_evidence_is_production_mesh_600step_stability_scout_not_overnight_or_full_duration'
    if 'long-stability' in case:
        return 'stability_evidence_is_reduced_long_stability_scout_not_overnight_or_full_duration'
    return 'overnight_or_full_duration_stability_missing'


def reference_data_blocking_gap(reference_report: dict[str, Any]) -> str | None:
    if reference_report.get('clears_reference_data_blocker') is True:
        return None
    if (
        reference_report.get('threshold_reference_agreement') is True
        and reference_report.get('external_plume_shape_dataset_agreement') is False
    ):
        return 'reference_agreement_is_threshold_only_not_external_plume_shape_dataset'
    if reference_report.get('external_plume_shape_dataset_agreement') is False:
        return 'external_plume_shape_reference_dataset_agreement_missing'
    return 'reference_data_agreement_missing'


def real_cad_blocking_gap(campaign: dict[str, Any]) -> str | None:
    if campaign.get('clears_real_cad_cleanup_blocker') is True:
        return None
    if (
        campaign.get('synthetic_tank_farm_evidence') is True
        or campaign.get('synthetic_stl_pipeline_evidence') is True
    ):
        return 'geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup'
    if campaign.get('real_cad_cleanup_campaign') is False:
        return 'real_cad_cleanup_campaign_missing'
    if campaign.get('real_cad_large_layout_campaign') is False:
        return 'real_cad_large_layout_campaign_missing'
    return 'real_cad_cleanup_campaign_missing'


def fire_consequence_blocking_gap(fire_report: dict[str, Any]) -> str | None:
    if fire_report.get('clears_calibrated_fire_consequence_blocker') is True:
        return None
    if (
        fire_report.get('consequence_model_tier') == 'screening_metrics'
        or fire_report.get('model_scope') == 'engineering_screening_not_calibrated'
    ):
        return 'fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure'
    if fire_report.get('radiation_model_calibrated') is False:
        return 'calibrated_fire_radiation_model_missing'
    if fire_report.get('overpressure_model_calibrated') is False:
        return 'calibrated_fire_overpressure_model_missing'
    if fire_report.get('validated_against_fire_experiment') is False:
        return 'fire_consequence_experimental_validation_missing'
    return 'calibrated_fire_radiation_overpressure_metrics_missing'


def gate(
    name: str,
    status: str,
    functional_weight: float,
    functional_credit: float,
    production_weight: float,
    production_credit: float,
    evidence: list[str],
    gaps: list[str],
) -> dict[str, Any]:
    return {
        'name': name,
        'status': status,
        'functional_weight': functional_weight,
        'functional_points': round(functional_weight * functional_credit, 3),
        'production_weight': production_weight,
        'production_points': round(production_weight * production_credit, 3),
        'evidence': evidence,
        'gaps': gaps,
    }


def build_scorecard(args: argparse.Namespace) -> dict[str, Any]:
    campaign_path = Path(args.campaign_manifest)
    release_path = Path(args.release_pack)
    affinity_path = Path(args.runtime_affinity_manifest)
    hybrid_affinity_path = Path(args.hybrid_runtime_affinity_manifest)
    scheduler_path = Path(args.scheduler_report)
    ignition_path = Path(args.ignition_consequence_report)
    fire_metrics_path = Path(args.fire_consequence_metrics_report)
    production_scale_scout_path = Path(args.production_scale_scout_report)
    long_stability_scout_path = Path(args.long_stability_scout_report)
    production_mesh_scout_path = Path(args.production_mesh_scout_report)
    production_mesh_8rank_scout_path = Path(args.production_mesh_8rank_scout_report)
    production_mesh_16rank_scout_path = Path(args.production_mesh_16rank_scout_report)
    production_mesh_8rank_600step_stability_scout_path = Path(args.production_mesh_8rank_600step_stability_scout_report)
    production_mesh_600step_stability_scout_path = Path(args.production_mesh_600step_stability_scout_report)
    production_mesh_1200step_stability_scout_path = Path(args.production_mesh_1200step_stability_scout_report)
    production_mesh_campaign_path = Path(args.engineering_h2_production_mesh_campaign_report)
    full_duration_candidate_path = Path(args.engineering_h2_full_duration_candidate_report)
    acceptance_matrix_path = Path(args.engineering_h2_acceptance_matrix)
    mpi_scaling_path = Path(args.engineering_h2_mpi_scaling_report)
    hybrid_cfd_scout_path = Path(args.engineering_h2_hybrid_cfd_scout_report)
    hybrid_production_mesh_scout_path = Path(args.engineering_h2_hybrid_production_mesh_scout_report)
    hybrid_production_mesh_8rank_scout_path = Path(args.engineering_h2_hybrid_production_mesh_8rank_scout_report)
    hybrid_production_mesh_8rank_600step_stability_scout_path = Path(
        args.engineering_h2_hybrid_production_mesh_8rank_600step_stability_scout_report
    )
    hybrid_production_mesh_600step_stability_scout_path = Path(
        args.engineering_h2_hybrid_production_mesh_600step_stability_scout_report
    )
    hybrid_largegrid_8rank_120step_scout_path = Path(
        args.engineering_h2_hybrid_largegrid_8rank_120step_scout_report
    )
    reference_agreement_path = Path(args.engineering_h2_reference_agreement_report)
    bfs_kepsilon_reference_path = Path(args.engineering_bfs_kepsilon_reference_report)
    engineering_scene_clearance_path = Path(args.engineering_h2_engineering_scene_clearance_report)
    pipe_rack_gpu_fire_obstacle_path = Path(args.engineering_h2_pipe_rack_gpu_fire_obstacle_report)
    reacting_mpi_cuda_smoke_path = Path(args.engineering_h2_reacting_mpi_cuda_smoke_report)
    pipe_rack_direct_reacting_cuda_path = Path(args.engineering_h2_pipe_rack_direct_reacting_cuda_report)
    pipe_rack_direct_reacting_mpi_cuda_path = Path(args.engineering_h2_pipe_rack_direct_reacting_mpi_cuda_report)
    pipe_rack_direct_reacting_largegrid_cuda_path = Path(
        args.engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_report
    )
    pipe_rack_direct_reacting_largegrid_mpi_cuda_path = Path(
        args.engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_report
    )
    pipe_rack_reacting_mpi_cuda_restart_path = Path(
        args.engineering_h2_pipe_rack_reacting_mpi_cuda_restart_report
    )
    fire_consequence_traceability_path = Path(args.engineering_h2_fire_consequence_traceability_report)
    integrated_initial_acceptance_path = Path(args.engineering_h2_integrated_initial_acceptance_report)

    campaign = load_json(campaign_path)
    release = load_json(release_path)
    affinity = load_json(affinity_path)
    hybrid_affinity = load_json(hybrid_affinity_path)
    scheduler = load_json(scheduler_path)
    ignition = load_json(ignition_path)
    fire_metrics = load_json(fire_metrics_path)
    production_scale_scout = load_json(production_scale_scout_path)
    long_stability_scout = load_json(long_stability_scout_path)
    production_mesh_scout = load_json(production_mesh_scout_path)
    production_mesh_8rank_scout = load_json(production_mesh_8rank_scout_path)
    production_mesh_16rank_scout = load_json(production_mesh_16rank_scout_path)
    production_mesh_8rank_600step_stability_scout = load_json(production_mesh_8rank_600step_stability_scout_path)
    production_mesh_600step_stability_scout = load_json(production_mesh_600step_stability_scout_path)
    production_mesh_1200step_stability_scout = load_json(production_mesh_1200step_stability_scout_path)
    production_mesh_campaign = load_json(production_mesh_campaign_path)
    full_duration_candidate = load_json(full_duration_candidate_path)
    acceptance_matrix = load_json(acceptance_matrix_path)
    mpi_scaling = load_json(mpi_scaling_path)
    hybrid_cfd_scout = load_json(hybrid_cfd_scout_path)
    hybrid_production_mesh_scout = load_json(hybrid_production_mesh_scout_path)
    hybrid_production_mesh_8rank_scout = load_json(hybrid_production_mesh_8rank_scout_path)
    hybrid_production_mesh_8rank_600step_stability_scout = load_json(
        hybrid_production_mesh_8rank_600step_stability_scout_path
    )
    hybrid_production_mesh_600step_stability_scout = load_json(
        hybrid_production_mesh_600step_stability_scout_path
    )
    hybrid_largegrid_8rank_120step_scout = load_json(hybrid_largegrid_8rank_120step_scout_path)
    reference_agreement = load_json(reference_agreement_path)
    bfs_kepsilon_reference = load_json(bfs_kepsilon_reference_path)
    engineering_scene_clearance = load_json(engineering_scene_clearance_path)
    pipe_rack_gpu_fire_obstacle = load_json(pipe_rack_gpu_fire_obstacle_path)
    reacting_mpi_cuda_smoke = load_json(reacting_mpi_cuda_smoke_path)
    pipe_rack_direct_reacting_cuda = load_json(pipe_rack_direct_reacting_cuda_path)
    pipe_rack_direct_reacting_mpi_cuda = load_json(pipe_rack_direct_reacting_mpi_cuda_path)
    pipe_rack_direct_reacting_largegrid_cuda = load_json(pipe_rack_direct_reacting_largegrid_cuda_path)
    pipe_rack_direct_reacting_largegrid_mpi_cuda = load_json(pipe_rack_direct_reacting_largegrid_mpi_cuda_path)
    pipe_rack_reacting_mpi_cuda_restart = load_json(pipe_rack_reacting_mpi_cuda_restart_path)
    fire_consequence_traceability = load_json(fire_consequence_traceability_path)
    integrated_initial_acceptance = load_json(integrated_initial_acceptance_path)

    evidence = [
        evidence_entry('campaign_manifest', campaign_path),
        evidence_entry('release_pack', release_path),
        evidence_entry('runtime_affinity_manifest', affinity_path),
        evidence_entry('hybrid_runtime_affinity_manifest', hybrid_affinity_path),
        evidence_entry('scheduler_run_report', scheduler_path),
        evidence_entry('ignition_consequence_report', ignition_path),
        evidence_entry('fire_consequence_metrics_report', fire_metrics_path),
        evidence_entry('production_scale_scout_report', production_scale_scout_path),
        evidence_entry('long_stability_scout_report', long_stability_scout_path),
        evidence_entry('production_mesh_scout_report', production_mesh_scout_path),
        evidence_entry('production_mesh_8rank_scout_report', production_mesh_8rank_scout_path),
        evidence_entry('production_mesh_16rank_scout_report', production_mesh_16rank_scout_path),
        evidence_entry('production_mesh_8rank_600step_stability_scout_report', production_mesh_8rank_600step_stability_scout_path),
        evidence_entry('production_mesh_600step_stability_scout_report', production_mesh_600step_stability_scout_path),
        evidence_entry('production_mesh_1200step_stability_scout_report', production_mesh_1200step_stability_scout_path),
        evidence_entry('engineering_h2_production_mesh_campaign_report', production_mesh_campaign_path),
        evidence_entry('engineering_h2_full_duration_candidate_report', full_duration_candidate_path),
        evidence_entry('engineering_h2_acceptance_matrix', acceptance_matrix_path),
        evidence_entry('engineering_h2_mpi_scaling_report', mpi_scaling_path),
        evidence_entry('engineering_h2_hybrid_cfd_scout_report', hybrid_cfd_scout_path),
        evidence_entry('engineering_h2_hybrid_production_mesh_scout_report', hybrid_production_mesh_scout_path),
        evidence_entry('engineering_h2_hybrid_production_mesh_8rank_scout_report', hybrid_production_mesh_8rank_scout_path),
        evidence_entry(
            'engineering_h2_hybrid_production_mesh_600step_stability_scout_report',
            hybrid_production_mesh_600step_stability_scout_path,
        ),
        evidence_entry(
            'engineering_h2_hybrid_largegrid_8rank_120step_scout_report',
            hybrid_largegrid_8rank_120step_scout_path,
        ),
        evidence_entry('engineering_h2_reference_agreement_report', reference_agreement_path),
        evidence_entry('engineering_bfs_kepsilon_reference_report', bfs_kepsilon_reference_path),
        evidence_entry('engineering_h2_engineering_scene_clearance_report', engineering_scene_clearance_path),
        evidence_entry('engineering_h2_pipe_rack_gpu_fire_obstacle_report', pipe_rack_gpu_fire_obstacle_path),
        evidence_entry('engineering_h2_reacting_mpi_cuda_smoke_report', reacting_mpi_cuda_smoke_path),
        evidence_entry('engineering_h2_pipe_rack_direct_reacting_cuda_report', pipe_rack_direct_reacting_cuda_path),
        evidence_entry('engineering_h2_pipe_rack_direct_reacting_mpi_cuda_report', pipe_rack_direct_reacting_mpi_cuda_path),
        evidence_entry('engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_report', pipe_rack_direct_reacting_largegrid_cuda_path),
        evidence_entry('engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_report', pipe_rack_direct_reacting_largegrid_mpi_cuda_path),
        evidence_entry('engineering_h2_pipe_rack_reacting_mpi_cuda_restart_report', pipe_rack_reacting_mpi_cuda_restart_path),
        evidence_entry('engineering_h2_fire_consequence_traceability_report', fire_consequence_traceability_path),
        evidence_entry('engineering_h2_integrated_initial_acceptance_report', integrated_initial_acceptance_path),
    ]

    cases = release.get('cases', [])
    if not isinstance(cases, list):
        raise ScorecardError('release pack cases is not a list')
    case_names = {c.get('name') for c in cases if isinstance(c, dict)}
    suites = set(release.get('suites', []))
    missing_cases = sorted(REQUIRED_CASES - case_names)
    missing_suites = sorted(REQUIRED_SUITES - suites)
    failed_cases = sorted(
        str(c.get('name')) for c in cases if isinstance(c, dict) and c.get('status') != 'PASS'
    )

    release_ok = (
        release.get('status') == 'PASS'
        and release.get('case_count') == 16
        and release.get('suite_count') == 5
        and not missing_cases
        and not missing_suites
        and not failed_cases
    )
    campaign_ok = (
        campaign.get('status') == 'PASS'
        and campaign.get('case_count') == 16
        and campaign.get('suite_count') == 5
    )
    affinity_ok = affinity.get('status') == 'PASS' and affinity.get('mpi_probe', {}).get('returncode') == 0
    hybrid_requested = hybrid_affinity.get('requested', {}) if isinstance(hybrid_affinity.get('requested'), dict) else {}
    hybrid_scheduler_env = (
        hybrid_affinity.get('scheduler_environment', {})
        if isinstance(hybrid_affinity.get('scheduler_environment'), dict) else {}
    )
    hybrid_affinity_ok = (
        hybrid_affinity.get('status') == 'PASS'
        and hybrid_affinity.get('mpi_probe', {}).get('returncode') == 0
        and int(hybrid_requested.get('ranks', 0)) >= 4
        and int(hybrid_requested.get('threads_per_rank', 0)) >= 2
        and hybrid_scheduler_env.get('OMP_PROC_BIND') in {'spread', 'close', 'true', 'false'}
        and hybrid_scheduler_env.get('OMP_PLACES') not in {None, ''}
        and not hybrid_affinity.get('warnings')
    )
    hybrid_cfd_summary = hybrid_cfd_scout.get('summary', {}) if isinstance(
        hybrid_cfd_scout.get('summary'), dict
    ) else {}
    hybrid_cfd_scout_ok = (
        hybrid_cfd_scout.get('status') == 'PASS-HYBRID-CFD-SCOUT'
        and int(hybrid_cfd_summary.get('ranks', 0)) >= 4
        and int(hybrid_cfd_summary.get('threads_per_rank', 0)) >= 2
        and int(hybrid_cfd_summary.get('max_step', 0)) >= 40
        and int(hybrid_cfd_summary.get('baseline_plotfiles', 0)) >= 3
        and int(hybrid_cfd_summary.get('amr_plotfiles', 0)) >= 3
        and int(hybrid_cfd_summary.get('amr_finest_level', 0)) >= 1
        and finite_number(hybrid_cfd_summary.get('cloud_rel_diff'))
        and float(hybrid_cfd_summary.get('cloud_rel_diff')) <= 0.45
        and finite_number(hybrid_cfd_summary.get('peak_rel_diff'))
        and float(hybrid_cfd_summary.get('peak_rel_diff')) <= 0.50
        and finite_number(hybrid_cfd_summary.get('advance_seconds_ratio'))
        and float(hybrid_cfd_summary.get('advance_seconds_ratio')) <= 4.0
    )
    hybrid_production_mesh_summary = (
        hybrid_production_mesh_scout.get('summary', {})
        if isinstance(hybrid_production_mesh_scout.get('summary'), dict) else {}
    )
    hybrid_production_mesh_scout_ok = (
        hybrid_production_mesh_scout.get('status') == 'PASS-HYBRID-CFD-SCOUT'
        and int(hybrid_production_mesh_summary.get('ranks', 0)) >= 4
        and int(hybrid_production_mesh_summary.get('threads_per_rank', 0)) >= 2
        and int(hybrid_production_mesh_summary.get('max_step', 0)) >= 120
        and int(hybrid_production_mesh_summary.get('base_cell_count', 0)) >= 65536
        and int(hybrid_production_mesh_summary.get('amr_equivalent_fine_cell_count', 0)) >= 524288
        and int(hybrid_production_mesh_summary.get('baseline_plotfiles', 0)) >= 5
        and int(hybrid_production_mesh_summary.get('amr_plotfiles', 0)) >= 5
        and int(hybrid_production_mesh_summary.get('amr_finest_level', 0)) >= 1
        and finite_number(hybrid_production_mesh_summary.get('cloud_rel_diff'))
        and float(hybrid_production_mesh_summary.get('cloud_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_summary.get('peak_rel_diff'))
        and float(hybrid_production_mesh_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_summary.get('advance_seconds_ratio'))
        and float(hybrid_production_mesh_summary.get('advance_seconds_ratio')) <= 4.0
    )
    hybrid_production_mesh_8rank_summary = (
        hybrid_production_mesh_8rank_scout.get('summary', {})
        if isinstance(hybrid_production_mesh_8rank_scout.get('summary'), dict) else {}
    )
    hybrid_production_mesh_8rank_scout_ok = (
        hybrid_production_mesh_8rank_scout.get('status') == 'PASS-HYBRID-CFD-SCOUT'
        and int(hybrid_production_mesh_8rank_summary.get('ranks', 0)) >= 8
        and int(hybrid_production_mesh_8rank_summary.get('threads_per_rank', 0)) >= 2
        and int(hybrid_production_mesh_8rank_summary.get('max_step', 0)) >= 120
        and int(hybrid_production_mesh_8rank_summary.get('base_cell_count', 0)) >= 65536
        and int(hybrid_production_mesh_8rank_summary.get('amr_equivalent_fine_cell_count', 0)) >= 524288
        and int(hybrid_production_mesh_8rank_summary.get('baseline_plotfiles', 0)) >= 5
        and int(hybrid_production_mesh_8rank_summary.get('amr_plotfiles', 0)) >= 5
        and int(hybrid_production_mesh_8rank_summary.get('amr_finest_level', 0)) >= 1
        and finite_number(hybrid_production_mesh_8rank_summary.get('cloud_rel_diff'))
        and float(hybrid_production_mesh_8rank_summary.get('cloud_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_8rank_summary.get('peak_rel_diff'))
        and float(hybrid_production_mesh_8rank_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_8rank_summary.get('advance_seconds_ratio'))
        and float(hybrid_production_mesh_8rank_summary.get('advance_seconds_ratio')) <= 4.0
    )
    hybrid_production_mesh_8rank_600step_summary = (
        hybrid_production_mesh_8rank_600step_stability_scout.get('summary', {})
        if isinstance(hybrid_production_mesh_8rank_600step_stability_scout.get('summary'), dict) else {}
    )
    hybrid_production_mesh_8rank_600step_stability_ok = (
        hybrid_production_mesh_8rank_600step_stability_scout.get('status') == 'PASS-HYBRID-CFD-SCOUT'
        and int(hybrid_production_mesh_8rank_600step_summary.get('ranks', 0)) >= 8
        and int(hybrid_production_mesh_8rank_600step_summary.get('threads_per_rank', 0)) >= 2
        and int(hybrid_production_mesh_8rank_600step_summary.get('max_step', 0)) >= 600
        and int(hybrid_production_mesh_8rank_600step_summary.get('base_cell_count', 0)) >= 65536
        and int(hybrid_production_mesh_8rank_600step_summary.get('amr_equivalent_fine_cell_count', 0)) >= 524288
        and int(hybrid_production_mesh_8rank_600step_summary.get('baseline_plotfiles', 0)) >= 11
        and int(hybrid_production_mesh_8rank_600step_summary.get('amr_plotfiles', 0)) >= 11
        and int(hybrid_production_mesh_8rank_600step_summary.get('amr_finest_level', 0)) >= 1
        and finite_number(hybrid_production_mesh_8rank_600step_summary.get('cloud_rel_diff'))
        and float(hybrid_production_mesh_8rank_600step_summary.get('cloud_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_8rank_600step_summary.get('peak_rel_diff'))
        and float(hybrid_production_mesh_8rank_600step_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_8rank_600step_summary.get('advance_seconds_ratio'))
        and float(hybrid_production_mesh_8rank_600step_summary.get('advance_seconds_ratio')) <= 4.0
    )
    hybrid_production_mesh_600step_summary = (
        hybrid_production_mesh_600step_stability_scout.get('summary', {})
        if isinstance(hybrid_production_mesh_600step_stability_scout.get('summary'), dict) else {}
    )
    hybrid_production_mesh_600step_stability_ok = (
        hybrid_production_mesh_600step_stability_scout.get('status') == 'PASS-HYBRID-CFD-SCOUT'
        and int(hybrid_production_mesh_600step_summary.get('ranks', 0)) >= 4
        and int(hybrid_production_mesh_600step_summary.get('threads_per_rank', 0)) >= 2
        and int(hybrid_production_mesh_600step_summary.get('max_step', 0)) >= 600
        and int(hybrid_production_mesh_600step_summary.get('base_cell_count', 0)) >= 65536
        and int(hybrid_production_mesh_600step_summary.get('amr_equivalent_fine_cell_count', 0)) >= 524288
        and int(hybrid_production_mesh_600step_summary.get('baseline_plotfiles', 0)) >= 11
        and int(hybrid_production_mesh_600step_summary.get('amr_plotfiles', 0)) >= 11
        and int(hybrid_production_mesh_600step_summary.get('amr_finest_level', 0)) >= 1
        and finite_number(hybrid_production_mesh_600step_summary.get('cloud_rel_diff'))
        and float(hybrid_production_mesh_600step_summary.get('cloud_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_600step_summary.get('peak_rel_diff'))
        and float(hybrid_production_mesh_600step_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(hybrid_production_mesh_600step_summary.get('advance_seconds_ratio'))
        and float(hybrid_production_mesh_600step_summary.get('advance_seconds_ratio')) <= 4.0
    )
    hybrid_largegrid_8rank_120step_summary = (
        hybrid_largegrid_8rank_120step_scout.get('summary', {})
        if isinstance(hybrid_largegrid_8rank_120step_scout.get('summary'), dict) else {}
    )
    hybrid_largegrid_8rank_120step_ok = (
        hybrid_largegrid_8rank_120step_scout.get('status') == 'PASS-HYBRID-CFD-SCOUT'
        and int(hybrid_largegrid_8rank_120step_summary.get('ranks', 0)) >= 8
        and int(hybrid_largegrid_8rank_120step_summary.get('threads_per_rank', 0)) >= 2
        and int(hybrid_largegrid_8rank_120step_summary.get('max_step', 0)) >= 120
        and int(hybrid_largegrid_8rank_120step_summary.get('base_cell_count', 0)) >= 200000
        and int(hybrid_largegrid_8rank_120step_summary.get('amr_equivalent_fine_cell_count', 0)) >= 1500000
        and int(hybrid_largegrid_8rank_120step_summary.get('baseline_plotfiles', 0)) >= 5
        and int(hybrid_largegrid_8rank_120step_summary.get('amr_plotfiles', 0)) >= 5
        and int(hybrid_largegrid_8rank_120step_summary.get('amr_finest_level', 0)) >= 1
        and finite_number(hybrid_largegrid_8rank_120step_summary.get('cloud_rel_diff'))
        and float(hybrid_largegrid_8rank_120step_summary.get('cloud_rel_diff')) <= 0.20
        and finite_number(hybrid_largegrid_8rank_120step_summary.get('peak_rel_diff'))
        and float(hybrid_largegrid_8rank_120step_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(hybrid_largegrid_8rank_120step_summary.get('advance_seconds_ratio'))
        and float(hybrid_largegrid_8rank_120step_summary.get('advance_seconds_ratio')) <= 4.0
    )
    reference_summary = (
        reference_agreement.get('summary', {})
        if isinstance(reference_agreement.get('summary'), dict) else {}
    )
    reference_agreement_ok = (
        reference_agreement.get('status') == 'PASS-REFERENCE-THRESHOLD-AGREEMENT'
        and reference_summary.get('all_threshold_checks_passed') is True
        and int(reference_summary.get('ranks', 0)) >= 8
        and int(reference_summary.get('threads_per_rank', 0)) >= 2
        and int(reference_summary.get('base_cell_count', 0)) >= 200000
        and finite_number(reference_summary.get('amr_peak_x'))
        and 0.04 <= float(reference_summary.get('amr_peak_x')) < 0.75
        and finite_number(reference_summary.get('amr_lel_cloud_volume'))
        and float(reference_summary.get('amr_lel_cloud_volume')) > 0.0
        and finite_number(reference_summary.get('cloud_rel_diff'))
        and float(reference_summary.get('cloud_rel_diff')) <= 0.05
        and finite_number(reference_summary.get('peak_rel_diff'))
        and float(reference_summary.get('peak_rel_diff')) <= 0.05
    )
    bfs_kepsilon_summary = (
        bfs_kepsilon_reference.get('summary', {})
        if isinstance(bfs_kepsilon_reference.get('summary'), dict) else {}
    )
    bfs_kepsilon_reference_ok = (
        bfs_kepsilon_reference.get('status') == 'PASS-BFS-KEPSILON-REFERENCE'
        and bfs_kepsilon_summary.get('bfs_validator_returncode') == 0
        and bfs_kepsilon_summary.get('bfs_validator_verdict') == 'PASS'
        and finite_number(bfs_kepsilon_summary.get('reattachment_x_h'))
        and finite_number(bfs_kepsilon_summary.get('recirculation_length_h'))
        and bfs_kepsilon_summary.get('blocks_production_readiness') is False
    )
    engineering_scene_metrics = (
        engineering_scene_clearance.get('large_acceptance_metrics', {})
        if isinstance(engineering_scene_clearance.get('large_acceptance_metrics'), dict) else {}
    )
    engineering_scene_validated = (
        engineering_scene_clearance.get('validated_capabilities', {})
        if isinstance(engineering_scene_clearance.get('validated_capabilities'), dict) else {}
    )
    engineering_scene_basis = (
        engineering_scene_clearance.get('acceptance_basis', {})
        if isinstance(engineering_scene_clearance.get('acceptance_basis'), dict) else {}
    )
    engineering_scene_clearance_ok = (
        engineering_scene_clearance.get('status') == 'PASS-H2-ENGINEERING-SCENE-CLEARANCE'
        and engineering_scene_clearance.get('decision') == 'engineering_scene_production_credible_by_self_built_large_case_gate'
        and engineering_scene_basis.get('external_public_benchmark_required_for_this_clearance') is False
        and engineering_scene_validated.get('leak_source_mass_injection') is True
        and engineering_scene_validated.get('three_dimensional_h2_dispersion') is True
        and engineering_scene_validated.get('amr_level1_regridding') is True
        and engineering_scene_validated.get('cpu_mpi_parallel') is True
        and engineering_scene_validated.get('gpu_parallel') is False
        and engineering_scene_validated.get('large_coupled_ignition_fire') is False
        and int(engineering_scene_metrics.get('ranks', 0)) >= 8
        and int(engineering_scene_metrics.get('base_cell_count', 0)) >= 200000
        and int(engineering_scene_metrics.get('equivalent_finest_cell_count', 0)) >= 1500000
        and int(engineering_scene_metrics.get('amr_finest_level', 0)) >= 1
        and int(engineering_scene_metrics.get('amr_regrid_count', 0)) >= 1
    )
    hybrid_runtime_8rank_600step_ok = (
        affinity_ok
        and hybrid_affinity_ok
        and hybrid_cfd_scout_ok
        and hybrid_production_mesh_scout_ok
        and hybrid_production_mesh_8rank_scout_ok
        and hybrid_production_mesh_600step_stability_ok
        and hybrid_production_mesh_8rank_600step_stability_ok
    )
    hybrid_runtime_8rank_and_600step_ok = (
        affinity_ok
        and hybrid_affinity_ok
        and hybrid_cfd_scout_ok
        and hybrid_production_mesh_scout_ok
        and hybrid_production_mesh_8rank_scout_ok
        and hybrid_production_mesh_600step_stability_ok
    )
    hybrid_runtime_4rank_600step_ok = (
        affinity_ok
        and hybrid_affinity_ok
        and hybrid_cfd_scout_ok
        and hybrid_production_mesh_scout_ok
        and hybrid_production_mesh_600step_stability_ok
    )
    hybrid_runtime_production_mesh_ok = (
        affinity_ok
        and hybrid_affinity_ok
        and hybrid_cfd_scout_ok
        and hybrid_production_mesh_scout_ok
    )
    hybrid_runtime_short_ok = affinity_ok and hybrid_affinity_ok and hybrid_cfd_scout_ok

    scheduler_ready = scheduler.get('status') == 'PASS'
    ignition_summary = ignition.get('summary', {}) if isinstance(ignition.get('summary'), dict) else {}
    fire_summary = fire_metrics.get('summary', {}) if isinstance(fire_metrics.get('summary'), dict) else {}
    fire_metrics_ok = (
        fire_metrics.get('status') == 'PASS-SCREENING'
        and fire_metrics.get('model_scope') == 'engineering_screening_not_calibrated'
        and finite_number(fire_summary.get('flammable_cloud_h2_mass_kg'))
        and float(fire_summary.get('flammable_cloud_h2_mass_kg')) > 0.0
        and finite_number(fire_summary.get('source_limited_heat_release_w'))
        and float(fire_summary.get('source_limited_heat_release_w')) > 0.0
        and finite_number(fire_summary.get('max_screening_flux_w_m2'))
        and float(fire_summary.get('max_screening_flux_w_m2')) > 0.0
        and finite_number(fire_summary.get('max_screening_overpressure_kpa'))
        and float(fire_summary.get('max_screening_overpressure_kpa')) > 0.0
    )
    ignition_ok = (
        ignition.get('status') == 'PASS-SMOKE'
        and finite_number(ignition_summary.get('delay_fine_ignition_time_s'))
        and finite_number(ignition_summary.get('sdc_heat_release_rel_linf'))
    )
    pipe_rack_caps = (
        pipe_rack_gpu_fire_obstacle.get('validated_capabilities', {})
        if isinstance(pipe_rack_gpu_fire_obstacle.get('validated_capabilities'), dict) else {}
    )
    pipe_rack_cpu_metrics = (
        pipe_rack_gpu_fire_obstacle.get('cpu_metrics', {})
        if isinstance(pipe_rack_gpu_fire_obstacle.get('cpu_metrics'), dict) else {}
    )
    pipe_rack_gpu_metrics = (
        pipe_rack_gpu_fire_obstacle.get('gpu_metrics', {})
        if isinstance(pipe_rack_gpu_fire_obstacle.get('gpu_metrics'), dict) else {}
    )
    pipe_rack_fire_summary = (
        pipe_rack_gpu_fire_obstacle.get('fire_screening_summary', {})
        if isinstance(pipe_rack_gpu_fire_obstacle.get('fire_screening_summary'), dict) else {}
    )
    pipe_rack_gpu_fire_obstacle_ok = (
        pipe_rack_gpu_fire_obstacle.get('status') == 'PASS-H2-PIPE-RACK-GPU-FIRE-OBSTACLE-SMOKE'
        and pipe_rack_caps.get('cube_obstacle_stl') is True
        and pipe_rack_caps.get('vertical_cylinder_obstacle_stl') is True
        and pipe_rack_caps.get('pipe_rack_multi_pipe_obstacle_stl') is True
        and pipe_rack_caps.get('merged_multi_file_stl_obstacle') is True
        and pipe_rack_caps.get('cpu_obstacle_leak_dispersion') is True
        and pipe_rack_caps.get('gpu_obstacle_leak_dispersion') is True
        and pipe_rack_caps.get('mpi_cuda_obstacle_leak_dispersion') is True
        and int(pipe_rack_caps.get('mpi_cuda_ranks', 0)) >= 2
        and int(pipe_rack_caps.get('mpi_cuda_devices', 0)) >= 2
        and pipe_rack_caps.get('fire_consequence_screening') is True
        and pipe_rack_caps.get('direct_coupled_3d_fire_propagation') is False
        and pipe_rack_caps.get('calibrated_fire_or_blast_model') is False
        and finite_number(pipe_rack_cpu_metrics.get('cloud_volume'))
        and float(pipe_rack_cpu_metrics.get('cloud_volume')) > 0.0
        and finite_number(pipe_rack_gpu_metrics.get('cloud_volume'))
        and float(pipe_rack_gpu_metrics.get('cloud_volume')) > 0.0
        and int(pipe_rack_gpu_metrics.get('flammable_planes', 0)) >= 1
        and finite_number(pipe_rack_fire_summary.get('max_screening_flux_w_m2'))
        and float(pipe_rack_fire_summary.get('max_screening_flux_w_m2')) > 0.0
    )
    reacting_caps = (
        reacting_mpi_cuda_smoke.get('validated_capabilities', {})
        if isinstance(reacting_mpi_cuda_smoke.get('validated_capabilities'), dict) else {}
    )
    reacting_checks = (
        reacting_mpi_cuda_smoke.get('run_log_checks', {})
        if isinstance(reacting_mpi_cuda_smoke.get('run_log_checks'), dict) else {}
    )
    reacting_plot_checks = (
        reacting_mpi_cuda_smoke.get('plotfile_checks', {})
        if isinstance(reacting_mpi_cuda_smoke.get('plotfile_checks'), dict) else {}
    )
    reacting_mpi_cuda_smoke_ok = (
        reacting_mpi_cuda_smoke.get('status') == 'PASS-PELEC-H2-REACTING-MPI-CUDA-SMOKE'
        and reacting_caps.get('pelec_reacting_solver') is True
        and reacting_caps.get('h2_o2_lidryer_mechanism') is True
        and reacting_caps.get('reactor_rk64') is True
        and reacting_caps.get('mpi_cuda_2rank_2device') is True
        and reacting_caps.get('direct_engineering_obstacle_fire_propagation') is False
        and int(reacting_checks.get('mpi_ranks', 0)) >= 2
        and int(reacting_checks.get('cuda_devices', 0)) >= 2
        and finite_number(reacting_plot_checks.get('initial_time'))
        and finite_number(reacting_plot_checks.get('final_time'))
        and float(reacting_plot_checks.get('final_time')) > float(reacting_plot_checks.get('initial_time'))
    )
    direct_reacting_caps = (
        pipe_rack_direct_reacting_cuda.get('validated_capabilities', {})
        if isinstance(pipe_rack_direct_reacting_cuda.get('validated_capabilities'), dict) else {}
    )
    direct_reacting_checks = (
        pipe_rack_direct_reacting_cuda.get('run_log_checks', {})
        if isinstance(pipe_rack_direct_reacting_cuda.get('run_log_checks'), dict) else {}
    )
    direct_reacting_plot_checks = (
        pipe_rack_direct_reacting_cuda.get('plotfile_checks', {})
        if isinstance(pipe_rack_direct_reacting_cuda.get('plotfile_checks'), dict) else {}
    )
    direct_reacting_input = (
        pipe_rack_direct_reacting_cuda.get('input_summary', {})
        if isinstance(pipe_rack_direct_reacting_cuda.get('input_summary'), dict) else {}
    )
    pipe_rack_direct_reacting_cuda_ok = (
        pipe_rack_direct_reacting_cuda.get('status') in {
            'PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-20STEP',
            'PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED',
        }
        and direct_reacting_caps.get('direct_engineering_obstacle_reacting_smoke') is True
        and (
            pipe_rack_direct_reacting_cuda.get('status') != 'PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED'
            or direct_reacting_caps.get('sustained_reacting_fire_development') is True
        )
        and direct_reacting_caps.get('pipe_rack_stl_obstacles') is True
        and direct_reacting_caps.get('h2_leak_source') is True
        and direct_reacting_caps.get('initial_flammable_cloud') is True
        and direct_reacting_caps.get('ignition_hotspot') is True
        and direct_reacting_caps.get('reactor_cvode') is True
        and direct_reacting_caps.get('cvode_gmres') is True
        and direct_reacting_caps.get('reacting_heat_release_variables') is True
        and direct_reacting_caps.get('single_gpu_cuda') is True
        and int(direct_reacting_checks.get('mpi_ranks', 0)) == 1
        and int(direct_reacting_checks.get('cuda_devices', 0)) == 1
        and finite_number(direct_reacting_plot_checks.get('initial_time'))
        and finite_number(direct_reacting_plot_checks.get('final_time'))
        and float(direct_reacting_plot_checks.get('final_time')) > float(direct_reacting_plot_checks.get('initial_time'))
    )
    pipe_rack_direct_reacting_sustained_ok = (
        pipe_rack_direct_reacting_cuda_ok
        and pipe_rack_direct_reacting_cuda.get('status') == 'PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED'
        and isinstance(direct_reacting_plot_checks.get('sustained_reaction_checks'), dict)
        and int(direct_reacting_plot_checks['sustained_reaction_checks'].get('sustained_output_count', 0)) >= 4
        and finite_number(direct_reacting_plot_checks['sustained_reaction_checks'].get('final_y_h2o_max'))
        and float(direct_reacting_plot_checks['sustained_reaction_checks'].get('final_y_h2o_max')) > 1.0e-3
    )
    direct_reacting_mpi_cuda_caps = (
        pipe_rack_direct_reacting_mpi_cuda.get('validated_capabilities', {})
        if isinstance(pipe_rack_direct_reacting_mpi_cuda.get('validated_capabilities'), dict) else {}
    )
    direct_reacting_mpi_cuda_checks = (
        pipe_rack_direct_reacting_mpi_cuda.get('run_log_checks', {})
        if isinstance(pipe_rack_direct_reacting_mpi_cuda.get('run_log_checks'), dict) else {}
    )
    direct_reacting_mpi_cuda_plot_checks = (
        pipe_rack_direct_reacting_mpi_cuda.get('plotfile_checks', {})
        if isinstance(pipe_rack_direct_reacting_mpi_cuda.get('plotfile_checks'), dict) else {}
    )
    direct_reacting_mpi_cuda_sustained_checks = (
        direct_reacting_mpi_cuda_plot_checks.get('sustained_reaction_checks', {})
        if isinstance(direct_reacting_mpi_cuda_plot_checks.get('sustained_reaction_checks'), dict) else {}
    )
    pipe_rack_direct_reacting_mpi_cuda_ok = (
        pipe_rack_direct_reacting_mpi_cuda.get('status') == 'PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-SUSTAINED'
        and direct_reacting_mpi_cuda_caps.get('mpi_cuda_parallel') is True
        and direct_reacting_mpi_cuda_caps.get('sustained_reacting_fire_development') is True
        and direct_reacting_mpi_cuda_caps.get('direct_engineering_obstacle_reacting_smoke') is True
        and int(direct_reacting_mpi_cuda_checks.get('mpi_ranks', 0)) >= 2
        and int(direct_reacting_mpi_cuda_checks.get('cuda_devices', 0)) >= 2
        and int(direct_reacting_mpi_cuda_sustained_checks.get('sustained_output_count', 0)) >= 4
        and finite_number(direct_reacting_mpi_cuda_sustained_checks.get('final_y_h2o_max'))
        and float(direct_reacting_mpi_cuda_sustained_checks.get('final_y_h2o_max')) > 1.0e-4
    )
    direct_reacting_largegrid_caps = (
        pipe_rack_direct_reacting_largegrid_cuda.get('validated_capabilities', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_cuda.get('validated_capabilities'), dict) else {}
    )
    direct_reacting_largegrid_checks = (
        pipe_rack_direct_reacting_largegrid_cuda.get('run_log_checks', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_cuda.get('run_log_checks'), dict) else {}
    )
    direct_reacting_largegrid_input = (
        pipe_rack_direct_reacting_largegrid_cuda.get('input_summary', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_cuda.get('input_summary'), dict) else {}
    )
    direct_reacting_largegrid_plot_checks = (
        pipe_rack_direct_reacting_largegrid_cuda.get('plotfile_checks', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_cuda.get('plotfile_checks'), dict) else {}
    )
    direct_reacting_largegrid_sustained_checks = (
        direct_reacting_largegrid_plot_checks.get('sustained_reaction_checks', {})
        if isinstance(direct_reacting_largegrid_plot_checks.get('sustained_reaction_checks'), dict) else {}
    )
    pipe_rack_direct_reacting_largegrid_cuda_ok = (
        pipe_rack_direct_reacting_largegrid_cuda.get('status') == 'PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED'
        and direct_reacting_largegrid_caps.get('sustained_reacting_fire_development') is True
        and direct_reacting_largegrid_caps.get('single_gpu_cuda') is True
        and direct_reacting_largegrid_input.get('n_cell') == '64 32 32'
        and int(direct_reacting_largegrid_input.get('max_step', 0)) >= 300
        and int(direct_reacting_largegrid_checks.get('cuda_devices', 0)) == 1
        and int(direct_reacting_largegrid_sustained_checks.get('sustained_output_count', 0)) >= 4
        and finite_number(direct_reacting_largegrid_sustained_checks.get('final_y_h2o_max'))
        and float(direct_reacting_largegrid_sustained_checks.get('final_y_h2o_max')) > 1.0e-3
    )
    direct_reacting_largegrid_mpi_cuda_caps = (
        pipe_rack_direct_reacting_largegrid_mpi_cuda.get('validated_capabilities', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_mpi_cuda.get('validated_capabilities'), dict) else {}
    )
    direct_reacting_largegrid_mpi_cuda_checks = (
        pipe_rack_direct_reacting_largegrid_mpi_cuda.get('run_log_checks', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_mpi_cuda.get('run_log_checks'), dict) else {}
    )
    direct_reacting_largegrid_mpi_cuda_input = (
        pipe_rack_direct_reacting_largegrid_mpi_cuda.get('input_summary', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_mpi_cuda.get('input_summary'), dict) else {}
    )
    direct_reacting_largegrid_mpi_cuda_plot_checks = (
        pipe_rack_direct_reacting_largegrid_mpi_cuda.get('plotfile_checks', {})
        if isinstance(pipe_rack_direct_reacting_largegrid_mpi_cuda.get('plotfile_checks'), dict) else {}
    )
    direct_reacting_largegrid_mpi_cuda_sustained_checks = (
        direct_reacting_largegrid_mpi_cuda_plot_checks.get('sustained_reaction_checks', {})
        if isinstance(direct_reacting_largegrid_mpi_cuda_plot_checks.get('sustained_reaction_checks'), dict) else {}
    )
    pipe_rack_direct_reacting_largegrid_mpi_cuda_ok = (
        pipe_rack_direct_reacting_largegrid_mpi_cuda.get('status') == 'PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-SUSTAINED'
        and direct_reacting_largegrid_mpi_cuda_caps.get('sustained_reacting_fire_development') is True
        and direct_reacting_largegrid_mpi_cuda_caps.get('mpi_cuda_parallel') is True
        and direct_reacting_largegrid_mpi_cuda_input.get('n_cell') == '64 32 32'
        and int(direct_reacting_largegrid_mpi_cuda_input.get('max_step', 0)) >= 300
        and int(direct_reacting_largegrid_mpi_cuda_checks.get('mpi_ranks', 0)) >= 2
        and int(direct_reacting_largegrid_mpi_cuda_checks.get('cuda_devices', 0)) >= 2
        and int(direct_reacting_largegrid_mpi_cuda_sustained_checks.get('sustained_output_count', 0)) >= 4
        and finite_number(direct_reacting_largegrid_mpi_cuda_sustained_checks.get('final_y_h2o_max'))
        and float(direct_reacting_largegrid_mpi_cuda_sustained_checks.get('final_y_h2o_max')) > 1.0e-3
    )
    reacting_restart_caps = (
        pipe_rack_reacting_mpi_cuda_restart.get('validated_capabilities', {})
        if isinstance(pipe_rack_reacting_mpi_cuda_restart.get('validated_capabilities'), dict) else {}
    )
    reacting_restart_checks = (
        pipe_rack_reacting_mpi_cuda_restart.get('restart_checks', {})
        if isinstance(pipe_rack_reacting_mpi_cuda_restart.get('restart_checks'), dict) else {}
    )
    pipe_rack_reacting_mpi_cuda_restart_ok = (
        pipe_rack_reacting_mpi_cuda_restart.get('status')
        == 'PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-RESTART-SUSTAINED'
        and reacting_restart_caps.get('largegrid_64x32x32') is True
        and reacting_restart_caps.get('checkpoint_written') is True
        and reacting_restart_caps.get('restart_from_checkpoint') is True
        and reacting_restart_caps.get('post_restart_sustained_fire_development') is True
        and reacting_restart_caps.get('mpi_cuda_parallel') is True
        and reacting_restart_checks.get('n_cell') == '64 32 32'
        and int(reacting_restart_checks.get('mpi_ranks', 0)) >= 2
        and int(reacting_restart_checks.get('cuda_devices', 0)) >= 2
        and int(reacting_restart_checks.get('post_restart_sustained_output_count', 0)) >= 3
        and finite_number(reacting_restart_checks.get('checkpoint_y_h2o_max'))
        and finite_number(reacting_restart_checks.get('final_y_h2o_max'))
        and float(reacting_restart_checks.get('final_y_h2o_max'))
        > float(reacting_restart_checks.get('checkpoint_y_h2o_max'))
    )
    fire_trace_caps = (
        fire_consequence_traceability.get('validated_capabilities', {})
        if isinstance(fire_consequence_traceability.get('validated_capabilities'), dict) else {}
    )
    fire_trace_screening = (
        fire_consequence_traceability.get('screening_traceability', {})
        if isinstance(fire_consequence_traceability.get('screening_traceability'), dict) else {}
    )
    fire_trace_direct = (
        fire_consequence_traceability.get('direct_reacting_fire_checks', {})
        if isinstance(fire_consequence_traceability.get('direct_reacting_fire_checks'), dict) else {}
    )
    fire_trace_formula_checks = fire_trace_screening.get('formula_checks', [])
    fire_trace_distance_checks = fire_trace_screening.get('distance_checks', [])
    fire_consequence_traceability_ok = (
        fire_consequence_traceability.get('status') == 'PASS-H2-FIRE-CONSEQUENCE-TRACEABILITY'
        and fire_trace_caps.get('fire_screening_formula_traceable') is True
        and fire_trace_caps.get('radiation_distance_sweep_traceable') is True
        and fire_trace_caps.get('overpressure_distance_sweep_traceable') is True
        and fire_trace_caps.get('direct_reacting_fire_evidence_linked') is True
        and fire_trace_caps.get('restart_reacting_fire_evidence_linked') is True
        and fire_trace_caps.get('calibrated_fire_or_blast_model') is False
        and isinstance(fire_trace_formula_checks, list)
        and len(fire_trace_formula_checks) >= 10
        and all(isinstance(item, dict) and item.get('passed') is True for item in fire_trace_formula_checks)
        and isinstance(fire_trace_distance_checks, list)
        and len(fire_trace_distance_checks) >= 2
        and all(isinstance(item, dict) and item.get('passed') is True for item in fire_trace_distance_checks)
        and fire_trace_direct.get('single_cuda_1000step', {}).get('passed') is True
        and fire_trace_direct.get('largegrid_mpi_cuda', {}).get('passed') is True
        and fire_trace_direct.get('restart_mpi_cuda', {}).get('passed') is True
    )
    integrated_initial_acceptance_ok = (
        integrated_initial_acceptance.get('status') == 'PASS-H2-INTEGRATED-ENGINEERING-INITIAL-ACCEPTANCE'
        and integrated_initial_acceptance.get('clears_initial_integrated_engineering_goal') is True
        and integrated_initial_acceptance.get('clears_full_production_certification') is False
    )
    scout_summary = production_scale_scout.get('summary', {}) if isinstance(production_scale_scout.get('summary'), dict) else {}
    production_scale_scout_ok = (
        production_scale_scout.get('status') == 'PASS-SCOUT'
        and int(scout_summary.get('ranks', 0)) >= 4
        and int(scout_summary.get('max_step', 0)) >= 100
        and int(scout_summary.get('base_cell_count', 0)) >= 25000
        and int(scout_summary.get('amr_equivalent_fine_cell_count', 0)) >= 200000
        and finite_number(scout_summary.get('cloud_rel_diff'))
        and float(scout_summary.get('cloud_rel_diff')) <= 0.20
    )
    mesh_summary = production_mesh_scout.get('summary', {}) if isinstance(production_mesh_scout.get('summary'), dict) else {}
    production_mesh_scout_ok = (
        production_mesh_scout.get('status') == 'PASS-SCOUT'
        and 'production-mesh' in str(production_mesh_scout.get('case', ''))
        and int(mesh_summary.get('ranks', 0)) >= 4
        and int(mesh_summary.get('max_step', 0)) >= 120
        and int(mesh_summary.get('base_cell_count', 0)) >= 60000
        and int(mesh_summary.get('amr_equivalent_fine_cell_count', 0)) >= 500000
        and int(mesh_summary.get('baseline_plotfiles', 0)) >= 5
        and int(mesh_summary.get('amr_plotfiles', 0)) >= 5
        and finite_number(mesh_summary.get('cloud_rel_diff'))
        and finite_number(mesh_summary.get('peak_rel_diff'))
        and float(mesh_summary.get('cloud_rel_diff')) <= 0.20
        and float(mesh_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(mesh_summary.get('mean_ncells_ratio'))
        and finite_number(mesh_summary.get('advance_seconds_ratio'))
        and float(mesh_summary.get('mean_ncells_ratio')) <= 4.0
        and float(mesh_summary.get('advance_seconds_ratio')) <= 4.0
    )
    mesh8_summary = production_mesh_8rank_scout.get('summary', {}) if isinstance(production_mesh_8rank_scout.get('summary'), dict) else {}
    production_mesh_8rank_scout_ok = (
        production_mesh_8rank_scout.get('status') == 'PASS-SCOUT'
        and '8rank' in str(production_mesh_8rank_scout.get('case', ''))
        and int(mesh8_summary.get('ranks', 0)) >= 8
        and int(mesh8_summary.get('max_step', 0)) >= 120
        and int(mesh8_summary.get('base_cell_count', 0)) >= 60000
        and int(mesh8_summary.get('amr_equivalent_fine_cell_count', 0)) >= 500000
        and int(mesh8_summary.get('baseline_plotfiles', 0)) >= 5
        and int(mesh8_summary.get('amr_plotfiles', 0)) >= 5
        and finite_number(mesh8_summary.get('cloud_rel_diff'))
        and finite_number(mesh8_summary.get('peak_rel_diff'))
        and float(mesh8_summary.get('cloud_rel_diff')) <= 0.20
        and float(mesh8_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(mesh8_summary.get('mean_ncells_ratio'))
        and finite_number(mesh8_summary.get('advance_seconds_ratio'))
        and float(mesh8_summary.get('mean_ncells_ratio')) <= 4.0
        and float(mesh8_summary.get('advance_seconds_ratio')) <= 4.0
    )
    mesh16_summary = production_mesh_16rank_scout.get('summary', {}) if isinstance(production_mesh_16rank_scout.get('summary'), dict) else {}
    production_mesh_16rank_scout_ok = (
        production_mesh_16rank_scout.get('status') == 'PASS-SCOUT'
        and '16rank' in str(production_mesh_16rank_scout.get('case', ''))
        and int(mesh16_summary.get('ranks', 0)) >= 16
        and int(mesh16_summary.get('max_step', 0)) >= 120
        and int(mesh16_summary.get('base_cell_count', 0)) >= 60000
        and int(mesh16_summary.get('amr_equivalent_fine_cell_count', 0)) >= 500000
        and int(mesh16_summary.get('baseline_plotfiles', 0)) >= 5
        and int(mesh16_summary.get('amr_plotfiles', 0)) >= 5
        and finite_number(mesh16_summary.get('cloud_rel_diff'))
        and finite_number(mesh16_summary.get('peak_rel_diff'))
        and float(mesh16_summary.get('cloud_rel_diff')) <= 0.20
        and float(mesh16_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(mesh16_summary.get('mean_ncells_ratio'))
        and finite_number(mesh16_summary.get('advance_seconds_ratio'))
        and float(mesh16_summary.get('mean_ncells_ratio')) <= 4.0
        and float(mesh16_summary.get('advance_seconds_ratio')) <= 4.0
    )
    mesh8long_summary = production_mesh_8rank_600step_stability_scout.get('summary', {}) if isinstance(
        production_mesh_8rank_600step_stability_scout.get('summary'), dict
    ) else {}
    production_mesh_8rank_600step_stability_ok = (
        production_mesh_8rank_600step_stability_scout.get('status') in {'PASS-STABILITY', 'PASS-SCOUT'}
        and '8rank' in str(production_mesh_8rank_600step_stability_scout.get('case', ''))
        and '600step' in str(production_mesh_8rank_600step_stability_scout.get('case', ''))
        and int(mesh8long_summary.get('ranks', 0)) >= 8
        and int(mesh8long_summary.get('max_step', 0)) >= 600
        and int(mesh8long_summary.get('base_cell_count', 0)) >= 60000
        and int(mesh8long_summary.get('amr_equivalent_fine_cell_count', 0)) >= 500000
        and int(mesh8long_summary.get('baseline_plotfiles', 0)) >= 11
        and int(mesh8long_summary.get('amr_plotfiles', 0)) >= 11
        and finite_number(mesh8long_summary.get('cloud_rel_diff'))
        and finite_number(mesh8long_summary.get('peak_rel_diff'))
        and float(mesh8long_summary.get('cloud_rel_diff')) <= 0.25
        and float(mesh8long_summary.get('peak_rel_diff')) <= 0.25
        and finite_number(mesh8long_summary.get('advance_seconds_ratio'))
        and float(mesh8long_summary.get('advance_seconds_ratio')) <= 25.0
    )
    long_summary = long_stability_scout.get('summary', {}) if isinstance(long_stability_scout.get('summary'), dict) else {}
    long_stability_scout_ok = (
        long_stability_scout.get('status') in {'PASS-STABILITY', 'PASS-SCOUT'}
        and 'long-stability' in str(long_stability_scout.get('case', ''))
        and int(long_summary.get('ranks', 0)) >= 4
        and int(long_summary.get('max_step', 0)) >= 300
        and int(long_summary.get('base_cell_count', 0)) >= 25000
        and int(long_summary.get('amr_equivalent_fine_cell_count', 0)) >= 200000
        and int(long_summary.get('baseline_plotfiles', 0)) >= 11
        and int(long_summary.get('amr_plotfiles', 0)) >= 11
        and finite_number(long_summary.get('cloud_rel_diff'))
        and finite_number(long_summary.get('peak_rel_diff'))
        and float(long_summary.get('cloud_rel_diff')) <= 0.20
        and float(long_summary.get('peak_rel_diff')) <= 0.20
    )
    mesh600_summary = production_mesh_600step_stability_scout.get('summary', {}) if isinstance(
        production_mesh_600step_stability_scout.get('summary'), dict
    ) else {}
    production_mesh_600step_stability_ok = (
        production_mesh_600step_stability_scout.get('status') in {'PASS-STABILITY', 'PASS-SCOUT'}
        and '600step' in str(production_mesh_600step_stability_scout.get('case', ''))
        and int(mesh600_summary.get('ranks', 0)) >= 4
        and int(mesh600_summary.get('max_step', 0)) >= 600
        and int(mesh600_summary.get('base_cell_count', 0)) >= 60000
        and int(mesh600_summary.get('amr_equivalent_fine_cell_count', 0)) >= 500000
        and int(mesh600_summary.get('baseline_plotfiles', 0)) >= 11
        and int(mesh600_summary.get('amr_plotfiles', 0)) >= 11
        and finite_number(mesh600_summary.get('cloud_rel_diff'))
        and finite_number(mesh600_summary.get('peak_rel_diff'))
        and float(mesh600_summary.get('cloud_rel_diff')) <= 0.20
        and float(mesh600_summary.get('peak_rel_diff')) <= 0.20
        and finite_number(mesh600_summary.get('mean_ncells_ratio'))
        and finite_number(mesh600_summary.get('advance_seconds_ratio'))
        and float(mesh600_summary.get('mean_ncells_ratio')) <= 8.0
        and float(mesh600_summary.get('advance_seconds_ratio')) <= 20.0
    )
    mesh1200_summary = production_mesh_1200step_stability_scout.get('summary', {}) if isinstance(
        production_mesh_1200step_stability_scout.get('summary'), dict
    ) else {}
    production_mesh_1200step_stability_ok = (
        production_mesh_1200step_stability_scout.get('status') in {'PASS-STABILITY', 'PASS-SCOUT'}
        and '1200step' in str(production_mesh_1200step_stability_scout.get('case', ''))
        and int(mesh1200_summary.get('ranks', 0)) >= 4
        and int(mesh1200_summary.get('max_step', 0)) >= 1200
        and int(mesh1200_summary.get('base_cell_count', 0)) >= 60000
        and int(mesh1200_summary.get('amr_equivalent_fine_cell_count', 0)) >= 500000
        and int(mesh1200_summary.get('baseline_plotfiles', 0)) >= 11
        and int(mesh1200_summary.get('amr_plotfiles', 0)) >= 11
        and finite_number(mesh1200_summary.get('cloud_rel_diff'))
        and finite_number(mesh1200_summary.get('peak_rel_diff'))
        and float(mesh1200_summary.get('cloud_rel_diff')) <= 0.25
        and float(mesh1200_summary.get('peak_rel_diff')) <= 0.25
        and finite_number(mesh1200_summary.get('mean_ncells_ratio'))
        and finite_number(mesh1200_summary.get('advance_seconds_ratio'))
        and float(mesh1200_summary.get('mean_ncells_ratio')) <= 10.0
        and float(mesh1200_summary.get('advance_seconds_ratio')) <= 25.0
    )

    matrix_summary = acceptance_matrix.get('summary', {}) if isinstance(acceptance_matrix.get('summary'), dict) else {}
    matrix_ok = (
        acceptance_matrix.get('status') in {'PARTIAL-PRODUCTION', 'PASS-PRODUCTION-MATRIX'}
        and int(matrix_summary.get('row_count', 0)) >= 7
        and int(matrix_summary.get('pass_like_rows', 0)) >= 6
        and isinstance(matrix_summary.get('not_ready_rows'), list)
    )
    production_mesh_campaign_full_duration_ok = (
        production_mesh_campaign.get('status') == 'PASS-PRODUCTION-MESH-FULL-DURATION-CAMPAIGN'
        and production_mesh_campaign.get('production_size_mesh_campaign') is True
        and production_mesh_campaign.get('full_duration_campaign') is True
    )
    full_duration_candidate_executed_ok = full_duration_candidate.get('status') == 'PASS-FULL-DURATION-EXECUTED'

    mpi_scaling_summary = mpi_scaling.get('summary', {}) if isinstance(mpi_scaling.get('summary'), dict) else {}
    mpi_scaling_ok = (
        mpi_scaling.get('status') == 'PASS-SCALING-SCOUT'
        and mpi_scaling.get('rank_series') == [4, 8, 16]
        and finite_number(mpi_scaling_summary.get('baseline_speedup_4_to_16'))
        and float(mpi_scaling_summary.get('baseline_speedup_4_to_16')) > 1.0
        and finite_number(mpi_scaling_summary.get('amr_speedup_4_to_16'))
        and float(mpi_scaling_summary.get('amr_speedup_4_to_16')) > 1.0
        and finite_number(mpi_scaling_summary.get('cloud_rel_diff_spread'))
        and float(mpi_scaling_summary.get('cloud_rel_diff_spread')) <= 1.0e-10
        and finite_number(mpi_scaling_summary.get('peak_rel_diff_spread'))
        and float(mpi_scaling_summary.get('peak_rel_diff_spread')) <= 1.0e-10
        and finite_number(mpi_scaling_summary.get('max_advance_seconds_ratio'))
        and float(mpi_scaling_summary.get('max_advance_seconds_ratio')) <= 4.0
    )

    source_cases = {
        'pressure-orifice', 'real-gas-orifice', 'tank-blowdown', 'real-gas-tank-blowdown',
        'pipe-loss', 'linepack-blowdown', 'linepack-valve-schedule'
    }
    geometry_cases = {'tank-farm', 'stl-multifile', 'stl-perfile-transform'}
    amr_cases = {'plan-amr-mpi-rank-sweep', 'plan-amr-mpi-reduced-long'}
    dispersion_cases = {'open-domain', 'release-rate', 'crosswind', 'low-wind'}

    if (
        mpi_scaling_ok
        and production_mesh_16rank_scout_ok
        and production_mesh_8rank_600step_stability_ok
        and hybrid_largegrid_8rank_120step_ok
        and scheduler_ready
        and production_mesh_campaign_full_duration_ok
    ):
        amr_mpi_limitations = [
            'Scheduler handoff, production-mesh full-duration campaign evidence, 8-rank/600-step stability, 16-rank scout, 8x2 large-grid hybrid, and 4/8/16 short MPI scaling scouts exist; remaining AMR/MPI credibility gaps are production-scale scaling curves and broader plant-layout repeats'
        ]
    elif (
        mpi_scaling_ok
        and production_mesh_16rank_scout_ok
        and production_mesh_8rank_600step_stability_ok
        and hybrid_largegrid_8rank_120step_ok
    ):
        amr_mpi_limitations = [
            '4-rank/1200-step, 8-rank/600-step, 16-rank short production-mesh, 8x2 large-grid hybrid, and 4/8/16 short MPI scaling scouts exist; scheduler/full-duration evidence is tracked separately, and broader production-scale scaling curves remain open'
        ]
    elif mpi_scaling_ok and production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok:
        amr_mpi_limitations = [
            '4-rank/1200-step, 8-rank/600-step, 16-rank short production-mesh, and 4/8/16 short MPI scaling scouts exist; large-grid hybrid repeats and broader production-scale scaling curves remain open'
        ]
    elif production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok:
        amr_mpi_limitations = [
            '4-rank/1200-step, 8-rank/600-step, and 16-rank short production-mesh scouts exist; 4/8/16 scaling evidence, large-grid hybrid repeats, and broader production-scale scaling curves remain open'
        ]
    elif production_mesh_8rank_600step_stability_ok:
        amr_mpi_limitations = [
            '4-rank/1200-step and 8-rank/600-step production-mesh stability scouts exist; scheduler/large-rank scaling sweeps remain open'
        ]
    elif production_mesh_8rank_scout_ok:
        amr_mpi_limitations = [
            '4-rank/300-step stability, 4-rank production-mesh, and 8-rank production-mesh scouts exist; larger MPI scaling sweeps remain open'
        ]
    else:
        amr_mpi_limitations = [
            '4-rank/300-step stability and 64x32x32 production-mesh scouts exist; larger MPI sweeps remain open'
        ]

    gates = [
        gate(
            'reproducible_release_evidence',
            'PASS-SMOKE' if release_ok and campaign_ok else 'NOT_READY',
            10, 1.00 if release_ok and campaign_ok else 0.0,
            10, 0.90 if release_ok and campaign_ok else 0.0,
            ['16-case campaign manifest PASS', 'project-local release evidence pack PASS'] + (['engineering H2 acceptance matrix PARTIAL-PRODUCTION'] if matrix_ok else []),
            ['smoke-scale pack, no full plotfile archive'] if release_ok and campaign_ok else ['campaign or release pack evidence incomplete'],
        ),
        gate(
            'h2_leak_source_physics_chain',
            'PASS-SMOKE+' if release_ok and source_cases <= case_names else 'NOT_READY',
            16, 0.95 if release_ok and source_cases <= case_names else 0.0,
            12, 0.80 if release_ok and source_cases <= case_names else 0.0,
            sorted(source_cases & case_names),
            ['isothermal/lumped/steady approximations remain for several source models'],
        ),
        gate(
            'h2_dispersion_and_hazard_outputs',
            'PASS-SMOKE+' if release_ok and dispersion_cases <= case_names else 'NOT_READY',
            14, 0.95 if release_ok and dispersion_cases <= case_names else 0.0,
            12, 0.75 if release_ok and dispersion_cases <= case_names else 0.0,
            sorted(dispersion_cases & case_names),
            ['Gaussian-profile smoke only; no experimental or field reference agreement'],
        ),
        gate(
            'h2_engineering_scene_large_acceptance_clearance',
            'PASS-LARGE-CASE' if engineering_scene_clearance_ok else 'NOT_READY',
            0, 0.0,
            0, 0.0,
            (
                [
                    'self-built large H2 leak-dispersion acceptance PASS',
                    f"cpu_mpi_ranks={engineering_scene_metrics.get('ranks')}",
                    f"base_cells={engineering_scene_metrics.get('base_cell_count')}",
                    f"amr_equivalent_fine_cells={engineering_scene_metrics.get('equivalent_finest_cell_count')}",
                    f"amr_regrid_count={engineering_scene_metrics.get('amr_regrid_count')}",
                ]
                if engineering_scene_clearance_ok else []
            ),
            (
                [
                    'GPU execution is not validated by this large acceptance run',
                    'large coupled ignition/fire is not validated by this large acceptance run',
                    'external plume benchmarks remain non-blocking calibration/publication follow-up for this engineering-scene clearance',
                ]
                if engineering_scene_clearance_ok else
                ['self-built large engineering-scene clearance report missing or failed']
            ),
        ),
        gate(
            'obstacle_geometry_and_stl_pipeline',
            (
                'PASS-CPU-GPU-PIPE-RACK-SMOKE'
                if pipe_rack_gpu_fire_obstacle_ok else
                ('PASS-SMOKE' if release_ok and geometry_cases <= case_names else 'NOT_READY')
            ),
            12, (
                0.98 if pipe_rack_gpu_fire_obstacle_ok else
                (0.92 if release_ok and geometry_cases <= case_names else 0.0)
            ),
            10, (
                0.82 if pipe_rack_gpu_fire_obstacle_ok else
                (0.68 if release_ok and geometry_cases <= case_names else 0.0)
            ),
            (
                sorted(geometry_cases & case_names) +
                ([
                    'cube+cylinder+multi-pipe pipe-rack STL obstacle PASS on CPU and CUDA',
                    f"gpu_arch={pipe_rack_caps.get('gpu_cuda_arch')}",
                    f"mpi_cuda_ranks={pipe_rack_caps.get('mpi_cuda_ranks')}",
                    f"mpi_cuda_devices={pipe_rack_caps.get('mpi_cuda_devices')}",
                    f"cpu_cloud_volume={pipe_rack_cpu_metrics.get('cloud_volume')}",
                    f"gpu_cloud_volume={pipe_rack_gpu_metrics.get('cloud_volume')}",
                ] if pipe_rack_gpu_fire_obstacle_ok else [])
            ),
            (
                [
                    'synthetic cube/cylinder/pipe-rack STL validated on CPU and single-GPU CUDA; real CAD cleanup, GPU scaling, and larger plant-layout repeats remain open'
                ]
                if pipe_rack_gpu_fire_obstacle_ok else
                ['synthetic STL/tank-farm smoke only; real CAD cleanup and large layouts remain open']
            ),
        ),
        gate(
            'h2_pipe_rack_gpu_fire_obstacle_clearance',
            'PASS-CPU-GPU-FIRE-SCREENING' if pipe_rack_gpu_fire_obstacle_ok else 'NOT_READY',
            0, 0.0,
            0, 0.0,
            (
                [
                    'cube obstacle STL PASS',
                    'vertical cylinder obstacle STL PASS',
                    'multi-pipe pipe-rack STL PASS',
                    'CPU leak/dispersion/hazard PASS',
                    'CUDA leak/dispersion/hazard PASS',
                    '2-rank MPI+CUDA leak/dispersion/hazard PASS',
                    'fire consequence screening PASS',
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                ]
                if pipe_rack_gpu_fire_obstacle_ok else []
            ),
            (
                [
                    'direct coupled 3D calibrated fire propagation is not claimed by this gate',
                    'GPU evidence includes 2-rank MPI+CUDA smoke/stability, not a production GPU scaling curve',
                    'pipe-rack case is engineering synthetic geometry, not customer plant CAD',
                ]
                if pipe_rack_gpu_fire_obstacle_ok else
                ['pipe-rack CPU/GPU/fire-screening evidence report missing or failed']
            ),
        ),
        gate(
            'engineering_amr_mpi_efficiency',
            (
                'PASS-SMOKE++++++' if mpi_scaling_ok and production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok and hybrid_largegrid_8rank_120step_ok else
                ('PASS-SMOKE+++++' if mpi_scaling_ok and production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok else
                ('PASS-SMOKE++++' if production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok else
                 ('PASS-SMOKE+++' if production_mesh_8rank_600step_stability_ok else
                  ('PASS-SMOKE++' if production_mesh_8rank_scout_ok else ('PASS-SMOKE+' if release_ok and amr_cases <= case_names else 'NOT_READY')))))
            ),
            14, (
                0.98 if mpi_scaling_ok and production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok and hybrid_largegrid_8rank_120step_ok else
                (0.97 if mpi_scaling_ok and production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok else
                (0.96 if production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok else
                 (0.95 if production_mesh_8rank_600step_stability_ok else
                  (0.93 if production_mesh_8rank_scout_ok else (0.90 if release_ok and amr_cases <= case_names else 0.0)))))
            ),
            14, (
                0.88 if mpi_scaling_ok and production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok and hybrid_largegrid_8rank_120step_ok else
                (0.87 if mpi_scaling_ok and production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok else
                (0.85 if production_mesh_16rank_scout_ok and production_mesh_8rank_600step_stability_ok else
                 (0.82 if production_mesh_8rank_600step_stability_ok else
                  (0.78 if production_mesh_8rank_scout_ok else (0.72 if release_ok and amr_cases <= case_names else 0.0)))))
            ),
            (
                sorted(amr_cases & case_names) +
                ([f"8-rank/600-step production-mesh stability cloud_rel={mesh8long_summary.get('cloud_rel_diff')}"] if production_mesh_8rank_600step_stability_ok else
                 ([f"8-rank production-mesh scout cloud_rel={mesh8_summary.get('cloud_rel_diff')}"] if production_mesh_8rank_scout_ok else [])) +
                ([f"16-rank production-mesh scout cloud_rel={mesh16_summary.get('cloud_rel_diff')}"] if production_mesh_16rank_scout_ok else []) +
                ([f"4/8/16 MPI scaling scout amr_speedup_4_to_16={mpi_scaling_summary.get('amr_speedup_4_to_16')}"] if mpi_scaling_ok else []) +
                ([f"8x2 large-grid hybrid scout base_cells={hybrid_largegrid_8rank_120step_summary.get('base_cell_count')} fine_cells={hybrid_largegrid_8rank_120step_summary.get('amr_equivalent_fine_cell_count')} cloud_rel={hybrid_largegrid_8rank_120step_summary.get('cloud_rel_diff')}"] if hybrid_largegrid_8rank_120step_ok else [])
            ),
            amr_mpi_limitations,
        ),
        gate(
            'ignition_fire_consequence_chain',
            (
                'PARTIAL+++++++++++' if ignition_ok and fire_metrics_ok and fire_consequence_traceability_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok and pipe_rack_reacting_mpi_cuda_restart_ok else
                ('PARTIAL++++++++++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok and pipe_rack_reacting_mpi_cuda_restart_ok else
                ('PARTIAL+++++++++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok else
                ('PARTIAL++++++++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok else
                ('PARTIAL+++++++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok else
                ('PARTIAL++++++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok else
                ('PARTIAL+++++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_cuda_ok else
                ('PARTIAL++++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok else
                ('PARTIAL+++' if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok else
                ('PARTIAL++' if ignition_ok and fire_metrics_ok else ('PARTIAL+' if ignition_ok else 'NOT_READY'))
                ))))))))
            ),
            10, (
                1.0 if ignition_ok and fire_metrics_ok and fire_consequence_traceability_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok and pipe_rack_reacting_mpi_cuda_restart_ok else
                (0.995 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok and pipe_rack_reacting_mpi_cuda_restart_ok else
                (0.99 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok else
                (0.985 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok else
                (0.98 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok else
                (0.97 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok else
                (0.95 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_cuda_ok else
                (0.92 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok else
                (0.90 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok else
                (0.88 if ignition_ok and fire_metrics_ok else (0.85 if ignition_ok else 0.0))
                ))))))))
            ),
            12, (
                0.86 if ignition_ok and fire_metrics_ok and fire_consequence_traceability_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok and pipe_rack_reacting_mpi_cuda_restart_ok else
                (0.855 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok and pipe_rack_reacting_mpi_cuda_restart_ok else
                (0.845 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok else
                (0.835 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok else
                (0.82 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok else
                (0.80 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok else
                (0.76 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_cuda_ok else
                (0.70 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok else
                (0.66 if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok else
                (0.62 if ignition_ok and fire_metrics_ok else (0.55 if ignition_ok else 0.0))
                ))))))))
            ),
            (
                [
                    'ignition consequence PASS-SMOKE',
                    'fire consequence metrics PASS-SCREENING',
                    'pipe-rack fire-screening PASS',
                    'PeleC H2/O2 reacting solver 2-rank MPI+CUDA PASS',
                    f"h2_leak_3d pipe-rack direct reacting {direct_reacting_input.get('max_step')}-step sustained single-CUDA PASS",
                    'h2_leak_3d pipe-rack direct reacting 2-rank MPI+CUDA sustained PASS',
                    'h2_leak_3d pipe-rack direct reacting 64x32x32 large-grid single-CUDA sustained PASS',
                    f"tign={ignition_summary.get('delay_fine_ignition_time_s')}",
                    f"mpi_cuda_ranks={reacting_checks.get('mpi_ranks')}",
                    f"cuda_devices={reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_cuda_devices={direct_reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_final_time={direct_reacting_plot_checks.get('final_time')}",
                    f"direct_reacting_sustained_outputs={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('sustained_output_count')}",
                    f"direct_reacting_final_y_h2o={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('final_y_h2o_max')}",
                    f"direct_reacting_mpi_cuda_ranks={direct_reacting_mpi_cuda_checks.get('mpi_ranks')}",
                    f"direct_reacting_mpi_cuda_devices={direct_reacting_mpi_cuda_checks.get('cuda_devices')}",
                    f"direct_reacting_mpi_cuda_final_y_h2o={direct_reacting_mpi_cuda_sustained_checks.get('final_y_h2o_max')}",
                    f"direct_reacting_largegrid_n_cell={direct_reacting_largegrid_input.get('n_cell')}",
                    f"direct_reacting_largegrid_final_y_h2o={direct_reacting_largegrid_sustained_checks.get('final_y_h2o_max')}",
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                    'h2_leak_3d pipe-rack direct reacting 64x32x32 large-grid 2-rank MPI+CUDA sustained PASS',
                    f"direct_reacting_largegrid_mpi_cuda_n_cell={direct_reacting_largegrid_mpi_cuda_input.get('n_cell')}",
                    f"direct_reacting_largegrid_mpi_cuda_ranks={direct_reacting_largegrid_mpi_cuda_checks.get('mpi_ranks')}",
                    f"direct_reacting_largegrid_mpi_cuda_devices={direct_reacting_largegrid_mpi_cuda_checks.get('cuda_devices')}",
                    f"direct_reacting_largegrid_mpi_cuda_final_y_h2o={direct_reacting_largegrid_mpi_cuda_sustained_checks.get('final_y_h2o_max')}",
                    'h2_leak_3d pipe-rack direct reacting 64x32x32 MPI+CUDA checkpoint/restart sustained PASS',
                    f"reacting_restart_initial_step={reacting_restart_checks.get('initial_step')}",
                    f"reacting_restart_final_step={reacting_restart_checks.get('final_step')}",
                    f"reacting_restart_post_outputs={reacting_restart_checks.get('post_restart_sustained_output_count')}",
                    f"reacting_restart_final_y_h2o={reacting_restart_checks.get('final_y_h2o_max')}",
                    'H2 fire consequence traceability formula/direct-fire audit PASS',
                    f"fire_trace_formula_checks={len(fire_trace_formula_checks)}",
                    f"fire_trace_distance_checks={len(fire_trace_distance_checks)}",
                ]
                if ignition_ok and fire_metrics_ok and fire_consequence_traceability_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok and pipe_rack_direct_reacting_largegrid_mpi_cuda_ok and pipe_rack_reacting_mpi_cuda_restart_ok else
                [
                    'ignition consequence PASS-SMOKE',
                    'fire consequence metrics PASS-SCREENING',
                    'pipe-rack fire-screening PASS',
                    'PeleC H2/O2 reacting solver 2-rank MPI+CUDA PASS',
                    f"h2_leak_3d pipe-rack direct reacting {direct_reacting_input.get('max_step')}-step sustained single-CUDA PASS",
                    'h2_leak_3d pipe-rack direct reacting 2-rank MPI+CUDA sustained PASS',
                    'h2_leak_3d pipe-rack direct reacting 64x32x32 large-grid single-CUDA sustained PASS',
                    f"tign={ignition_summary.get('delay_fine_ignition_time_s')}",
                    f"mpi_cuda_ranks={reacting_checks.get('mpi_ranks')}",
                    f"cuda_devices={reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_cuda_devices={direct_reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_final_time={direct_reacting_plot_checks.get('final_time')}",
                    f"direct_reacting_sustained_outputs={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('sustained_output_count')}",
                    f"direct_reacting_final_y_h2o={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('final_y_h2o_max')}",
                    f"direct_reacting_mpi_cuda_ranks={direct_reacting_mpi_cuda_checks.get('mpi_ranks')}",
                    f"direct_reacting_mpi_cuda_devices={direct_reacting_mpi_cuda_checks.get('cuda_devices')}",
                    f"direct_reacting_mpi_cuda_final_y_h2o={direct_reacting_mpi_cuda_sustained_checks.get('final_y_h2o_max')}",
                    f"direct_reacting_largegrid_n_cell={direct_reacting_largegrid_input.get('n_cell')}",
                    f"direct_reacting_largegrid_final_y_h2o={direct_reacting_largegrid_sustained_checks.get('final_y_h2o_max')}",
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                ]
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok else
                [
                    'ignition consequence PASS-SMOKE',
                    'fire consequence metrics PASS-SCREENING',
                    'pipe-rack fire-screening PASS',
                    'PeleC H2/O2 reacting solver 2-rank MPI+CUDA PASS',
                    f"h2_leak_3d pipe-rack direct reacting {direct_reacting_input.get('max_step')}-step sustained single-CUDA PASS",
                    'h2_leak_3d pipe-rack direct reacting 2-rank MPI+CUDA sustained PASS',
                    f"tign={ignition_summary.get('delay_fine_ignition_time_s')}",
                    f"mpi_cuda_ranks={reacting_checks.get('mpi_ranks')}",
                    f"cuda_devices={reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_cuda_devices={direct_reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_final_time={direct_reacting_plot_checks.get('final_time')}",
                    f"direct_reacting_sustained_outputs={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('sustained_output_count')}",
                    f"direct_reacting_final_y_h2o={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('final_y_h2o_max')}",
                    f"direct_reacting_mpi_cuda_ranks={direct_reacting_mpi_cuda_checks.get('mpi_ranks')}",
                    f"direct_reacting_mpi_cuda_devices={direct_reacting_mpi_cuda_checks.get('cuda_devices')}",
                    f"direct_reacting_mpi_cuda_final_y_h2o={direct_reacting_mpi_cuda_sustained_checks.get('final_y_h2o_max')}",
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                ]
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok else
                [
                    'ignition consequence PASS-SMOKE',
                    'fire consequence metrics PASS-SCREENING',
                    'pipe-rack fire-screening PASS',
                    'PeleC H2/O2 reacting solver 2-rank MPI+CUDA PASS',
                    f"h2_leak_3d pipe-rack direct reacting {direct_reacting_input.get('max_step')}-step sustained single-CUDA PASS",
                    f"tign={ignition_summary.get('delay_fine_ignition_time_s')}",
                    f"mpi_cuda_ranks={reacting_checks.get('mpi_ranks')}",
                    f"cuda_devices={reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_cuda_devices={direct_reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_final_time={direct_reacting_plot_checks.get('final_time')}",
                    f"direct_reacting_sustained_outputs={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('sustained_output_count')}",
                    f"direct_reacting_final_y_h2o={direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('final_y_h2o_max')}",
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                ]
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok else
                [
                    'ignition consequence PASS-SMOKE',
                    'fire consequence metrics PASS-SCREENING',
                    'pipe-rack fire-screening PASS',
                    'PeleC H2/O2 reacting solver 2-rank MPI+CUDA PASS',
                    'h2_leak_3d pipe-rack direct reacting 20-step single-CUDA PASS',
                    f"tign={ignition_summary.get('delay_fine_ignition_time_s')}",
                    f"mpi_cuda_ranks={reacting_checks.get('mpi_ranks')}",
                    f"cuda_devices={reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_cuda_devices={direct_reacting_checks.get('cuda_devices')}",
                    f"direct_reacting_final_time={direct_reacting_plot_checks.get('final_time')}",
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                ]
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_cuda_ok else
                [
                    'ignition consequence PASS-SMOKE',
                    'fire consequence metrics PASS-SCREENING',
                    'pipe-rack fire-screening PASS',
                    'PeleC H2/O2 reacting solver 2-rank MPI+CUDA PASS',
                    f"tign={ignition_summary.get('delay_fine_ignition_time_s')}",
                    f"mpi_cuda_ranks={reacting_checks.get('mpi_ranks')}",
                    f"cuda_devices={reacting_checks.get('cuda_devices')}",
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                ]
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok else
                [
                    'ignition consequence PASS-SMOKE',
                    'fire consequence metrics PASS-SCREENING',
                    'pipe-rack fire-screening PASS',
                    f"tign={ignition_summary.get('delay_fine_ignition_time_s')}",
                    f"max_flux={pipe_rack_fire_summary.get('max_screening_flux_w_m2')}",
                    f"max_overpressure={pipe_rack_fire_summary.get('max_screening_overpressure_kpa')}",
                ]
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok else
                (['ignition consequence PASS-SMOKE', 'fire consequence metrics PASS-SCREENING', f"tign={ignition_summary.get('delay_fine_ignition_time_s')}", f"max_flux={fire_summary.get('max_screening_flux_w_m2')}", f"max_overpressure={fire_summary.get('max_screening_overpressure_kpa')}"] if fire_metrics_ok else ['ignition consequence PASS-SMOKE', f"tign={ignition_summary.get('delay_fine_ignition_time_s')}", f"heat_rel_linf={ignition_summary.get('sdc_heat_release_rel_linf')}"])
            ),
            (
                ['direct pipe-rack leak-cloud reacting CUDA sustained-fire gates now pass on single GPU, 2-rank MPI+CUDA, and 64x32x32 large-grid single-GPU; full-duration flame spread, flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing']
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok and pipe_rack_direct_reacting_largegrid_cuda_ok else
                ['direct pipe-rack leak-cloud reacting CUDA sustained-fire gates now pass on single GPU and 2-rank MPI+CUDA; full-duration flame spread, flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing']
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok and pipe_rack_direct_reacting_mpi_cuda_ok else
                ['direct pipe-rack leak-cloud reacting CUDA sustained-fire gate now passes for 500 steps with product growth; full-duration flame spread, flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing']
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_sustained_ok else
                ['direct pipe-rack leak-cloud reacting CUDA smoke now passes; full-duration flame spread, flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing']
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok and pipe_rack_direct_reacting_cuda_ok else
                ['screening radiation/overpressure metrics include the pipe-rack obstacle case and the reacting H2/O2 solver runs on 2-rank MPI+CUDA; direct pipe-rack leak-cloud flame propagation, flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing']
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok and reacting_mpi_cuda_smoke_ok else
                ['screening radiation/overpressure metrics now include the pipe-rack obstacle case, but flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing']
                if ignition_ok and fire_metrics_ok and pipe_rack_gpu_fire_obstacle_ok else
                (['screening radiation/overpressure metrics exist, but flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing'] if fire_metrics_ok else ['short-time reacting smoke only; flame speed, radiation, overpressure, and calibrated fire metrics missing'])
            ),
        ),
        gate(
            'runtime_affinity_and_scheduler_handoff',
            (
                'PASS' if scheduler_ready else
                ('PARTIAL++++++' if hybrid_runtime_8rank_600step_ok else
                 ('PARTIAL+++++' if hybrid_runtime_8rank_and_600step_ok else
                  ('PARTIAL++++' if hybrid_runtime_4rank_600step_ok else
                   ('PARTIAL+++' if hybrid_runtime_production_mesh_ok else
                   ('PARTIAL++' if hybrid_runtime_short_ok else
                    ('PARTIAL+' if affinity_ok and hybrid_affinity_ok else ('PARTIAL' if affinity_ok else 'NOT_READY')))))))
            ),
            8, (
                1.0 if scheduler_ready else
                (0.91 if hybrid_runtime_8rank_600step_ok else
                 (0.90 if hybrid_runtime_8rank_and_600step_ok else
                  (0.88 if hybrid_runtime_4rank_600step_ok else
                   (0.86 if hybrid_runtime_production_mesh_ok else
                   (0.82 if hybrid_runtime_short_ok else
                    (0.78 if affinity_ok and hybrid_affinity_ok else (0.70 if affinity_ok else 0.0)))))))
            ),
            10, (
                0.85 if scheduler_ready else
                (0.60 if hybrid_runtime_8rank_600step_ok else
                 (0.58 if hybrid_runtime_8rank_and_600step_ok else
                  (0.56 if hybrid_runtime_4rank_600step_ok else
                   (0.54 if hybrid_runtime_production_mesh_ok else
                   (0.50 if hybrid_runtime_short_ok else
                    (0.48 if affinity_ok and hybrid_affinity_ok else (0.45 if affinity_ok else 0.0)))))))
            ),
            (
                ['runtime affinity manifest PASS', f"scheduler_report_status={scheduler.get('status')}"] +
                ([
                    f"hybrid runtime affinity PASS ranks={hybrid_requested.get('ranks')} threads={hybrid_requested.get('threads_per_rank')}",
                    f"OMP_PROC_BIND={hybrid_scheduler_env.get('OMP_PROC_BIND')} OMP_PLACES={hybrid_scheduler_env.get('OMP_PLACES')}",
                ] if hybrid_affinity_ok else []) +
                ([
                    f"hybrid CFD scout PASS ranks={hybrid_cfd_summary.get('ranks')} threads={hybrid_cfd_summary.get('threads_per_rank')}",
                    f"hybrid CFD cloud_rel={hybrid_cfd_summary.get('cloud_rel_diff')} peak_rel={hybrid_cfd_summary.get('peak_rel_diff')}",
                ] if hybrid_cfd_scout_ok else []) +
                ([
                    f"hybrid production-mesh CFD scout PASS ranks={hybrid_production_mesh_summary.get('ranks')} threads={hybrid_production_mesh_summary.get('threads_per_rank')}",
                    f"hybrid production-mesh cloud_rel={hybrid_production_mesh_summary.get('cloud_rel_diff')} peak_rel={hybrid_production_mesh_summary.get('peak_rel_diff')} advance_ratio={hybrid_production_mesh_summary.get('advance_seconds_ratio')}",
                ] if hybrid_production_mesh_scout_ok else []) +
                ([
                    f"hybrid production-mesh 8-rank CFD scout PASS ranks={hybrid_production_mesh_8rank_summary.get('ranks')} threads={hybrid_production_mesh_8rank_summary.get('threads_per_rank')}",
                    f"hybrid production-mesh 8-rank cloud_rel={hybrid_production_mesh_8rank_summary.get('cloud_rel_diff')} peak_rel={hybrid_production_mesh_8rank_summary.get('peak_rel_diff')} advance_ratio={hybrid_production_mesh_8rank_summary.get('advance_seconds_ratio')}",
                ] if hybrid_production_mesh_8rank_scout_ok else []) +
                ([
                    f"hybrid production-mesh 8-rank 600-step stability PASS ranks={hybrid_production_mesh_8rank_600step_summary.get('ranks')} threads={hybrid_production_mesh_8rank_600step_summary.get('threads_per_rank')}",
                    f"hybrid production-mesh 8-rank 600-step cloud_rel={hybrid_production_mesh_8rank_600step_summary.get('cloud_rel_diff')} peak_rel={hybrid_production_mesh_8rank_600step_summary.get('peak_rel_diff')} advance_ratio={hybrid_production_mesh_8rank_600step_summary.get('advance_seconds_ratio')}",
                ] if hybrid_production_mesh_8rank_600step_stability_ok else []) +
                ([
                    f"hybrid production-mesh 600-step stability PASS ranks={hybrid_production_mesh_600step_summary.get('ranks')} threads={hybrid_production_mesh_600step_summary.get('threads_per_rank')}",
                    f"hybrid production-mesh 600-step cloud_rel={hybrid_production_mesh_600step_summary.get('cloud_rel_diff')} peak_rel={hybrid_production_mesh_600step_summary.get('peak_rel_diff')} advance_ratio={hybrid_production_mesh_600step_summary.get('advance_seconds_ratio')}",
                ] if hybrid_production_mesh_600step_stability_ok else []) +
                ([
                    f"hybrid large-grid 8-rank 120-step PASS base_cells={hybrid_largegrid_8rank_120step_summary.get('base_cell_count')} fine_cells={hybrid_largegrid_8rank_120step_summary.get('amr_equivalent_fine_cell_count')}",
                    f"hybrid large-grid cloud_rel={hybrid_largegrid_8rank_120step_summary.get('cloud_rel_diff')} peak_rel={hybrid_largegrid_8rank_120step_summary.get('peak_rel_diff')} advance_ratio={hybrid_largegrid_8rank_120step_summary.get('advance_seconds_ratio')}",
                ] if hybrid_largegrid_8rank_120step_ok else [])
            ),
            (
                ['interactive MPI+OpenMP affinity preflight plus short, 4x2 production-mesh, 8x2 production-mesh, 4x2 600-step, and 8x2 600-step production-mesh hybrid CFD scouts exist; scheduler campaign has not produced PASS run outputs']
                if hybrid_runtime_8rank_600step_ok and not scheduler_ready else
                (['interactive MPI+OpenMP affinity preflight plus short, 4x2 production-mesh, 8x2 production-mesh, and 4x2 600-step production-mesh hybrid CFD scouts exist; scheduler campaign has not produced PASS run outputs']
                 if hybrid_runtime_8rank_and_600step_ok and not scheduler_ready else
                (['interactive 4x2 MPI+OpenMP affinity preflight plus short, production-mesh, and 600-step production-mesh hybrid CFD scouts exist; scheduler campaign has not produced PASS run outputs']
                 if hybrid_affinity_ok and hybrid_cfd_scout_ok and hybrid_production_mesh_scout_ok and hybrid_production_mesh_600step_stability_ok and not scheduler_ready else
                (['interactive 4x2 MPI+OpenMP affinity preflight plus short and production-mesh hybrid CFD scouts exist; scheduler campaign has not produced PASS run outputs']
                 if hybrid_affinity_ok and hybrid_cfd_scout_ok and hybrid_production_mesh_scout_ok and not scheduler_ready else
                (['interactive 4x2 MPI+OpenMP affinity preflight and real hybrid CFD scout exist; production-mesh hybrid scout or scheduler PASS run outputs missing']
                 if hybrid_affinity_ok and hybrid_cfd_scout_ok and not scheduler_ready else
                 (['interactive 4x2 MPI+OpenMP affinity preflight exists; real hybrid CFD scout or scheduler PASS run outputs missing']
                  if hybrid_affinity_ok and not scheduler_ready else
                  (['scheduler campaign has not produced PASS run outputs'] if not scheduler_ready else []))))))
            ),
        ),
        gate(
            'long_duration_stability',
            (
                'PASS-FULL-DURATION' if production_mesh_campaign_full_duration_ok and full_duration_candidate_executed_ok else
                ('PASS-CANDIDATE' if full_duration_candidate_executed_ok else
                ('PARTIAL+++' if production_mesh_1200step_stability_ok else
                ('PARTIAL++' if production_mesh_600step_stability_ok else ('PARTIAL+' if long_stability_scout_ok else 'PARTIAL'))
                ))
            ),
            8, (
                0.98 if production_mesh_campaign_full_duration_ok and full_duration_candidate_executed_ok else
                (0.94 if full_duration_candidate_executed_ok else
                (0.88 if production_mesh_1200step_stability_ok else
                (0.82 if production_mesh_600step_stability_ok else (0.72 if long_stability_scout_ok else (0.55 if release_ok else 0.0)))
                ))
            ),
            12, (
                0.86 if production_mesh_campaign_full_duration_ok and full_duration_candidate_executed_ok else
                (0.78 if full_duration_candidate_executed_ok else
                (0.70 if production_mesh_1200step_stability_ok else
                (0.64 if production_mesh_600step_stability_ok else (0.56 if long_stability_scout_ok else (0.42 if release_ok else 0.0)))
                ))
            ),
            (
                ['production-mesh full-duration campaign PASS', f"full_duration_status={full_duration_candidate.get('status')}", f"target_max_step={full_duration_candidate.get('target', {}).get('max_step') if isinstance(full_duration_candidate.get('target'), dict) else None}", f"expected_plotfiles={full_duration_candidate.get('target', {}).get('expected_plotfiles_per_case') if isinstance(full_duration_candidate.get('target'), dict) else None}"]
                if production_mesh_campaign_full_duration_ok and full_duration_candidate_executed_ok else
                (['full-duration candidate executed', f"full_duration_status={full_duration_candidate.get('status')}", f"target_max_step={full_duration_candidate.get('target', {}).get('max_step') if isinstance(full_duration_candidate.get('target'), dict) else None}"]
                 if full_duration_candidate_executed_ok else
                (['production-mesh 1200-step stability scout PASS-STABILITY', f"max_step={mesh1200_summary.get('max_step')}", f"cloud_rel={mesh1200_summary.get('cloud_rel_diff')}", f"advance_ratio={mesh1200_summary.get('advance_seconds_ratio')}"]
                if production_mesh_1200step_stability_ok else
                (['production-mesh 600-step stability scout PASS-STABILITY', f"max_step={mesh600_summary.get('max_step')}", f"cloud_rel={mesh600_summary.get('cloud_rel_diff')}", f"advance_ratio={mesh600_summary.get('advance_seconds_ratio')}"]
                 if production_mesh_600step_stability_ok else
                 (['long-stability scout PASS-STABILITY', f"max_step={long_summary.get('max_step')}", f"cloud_rel={long_summary.get('cloud_rel_diff')}"] if long_stability_scout_ok else (['plan-amr-mpi-reduced-long smoke exists'] if 'plan-amr-mpi-reduced-long' in case_names else [])))
                ))
            ),
            (
                ['production-mesh full-duration evidence exists; remaining stability credibility gaps are repeat campaigns on real CAD layouts and external field/experiment agreement']
                if production_mesh_campaign_full_duration_ok and full_duration_candidate_executed_ok else
                (['full-duration candidate executed; production-mesh campaign archive attachment remains incomplete']
                 if full_duration_candidate_executed_ok else
                (['1200-step production-mesh MPI+AMR scout exists; overnight/full-duration stability campaigns still missing']
                if production_mesh_1200step_stability_ok else
                (['600-step production-mesh MPI+AMR scout exists; overnight/full-duration stability campaigns still missing'] if production_mesh_600step_stability_ok else (['300-step MPI+AMR scout exists; overnight/full-duration stability campaigns still missing'] if long_stability_scout_ok else ['overnight-style and production-duration stability campaigns missing']))
                ))
            ),
        ),
        gate(
            'production_scale_and_reference_accuracy',
            'PARTIAL++++' if reference_agreement_ok else ('PARTIAL+++' if hybrid_largegrid_8rank_120step_ok else ('PARTIAL++' if production_mesh_scout_ok else ('PARTIAL+' if production_scale_scout_ok else 'NOT_READY'))),
            8, 0.88 if reference_agreement_ok else (0.86 if hybrid_largegrid_8rank_120step_ok else (0.82 if production_mesh_scout_ok else (0.75 if production_scale_scout_ok else (0.55 if release_ok else 0.0)))),
            8, 0.62 if reference_agreement_ok else (0.59 if hybrid_largegrid_8rank_120step_ok else (0.54 if production_mesh_scout_ok else (0.45 if production_scale_scout_ok else (0.25 if release_ok else 0.0)))),
            (
                [
                    'H2 reference-threshold agreement PASS',
                    f"amr_peak_x={reference_summary.get('amr_peak_x')}",
                    f"amr_lel_cloud_volume={reference_summary.get('amr_lel_cloud_volume')}",
                    f"cloud_rel={reference_summary.get('cloud_rel_diff')}",
                ]
                if reference_agreement_ok else
                [
                    'hybrid large-grid 8x2 scout PASS',
                    f"base_cells={hybrid_largegrid_8rank_120step_summary.get('base_cell_count')}",
                    f"fine_cells={hybrid_largegrid_8rank_120step_summary.get('amr_equivalent_fine_cell_count')}",
                    f"cloud_rel={hybrid_largegrid_8rank_120step_summary.get('cloud_rel_diff')}",
                ]
                if hybrid_largegrid_8rank_120step_ok else
                (['production-mesh scout PASS-SCOUT', f"base_cells={mesh_summary.get('base_cell_count')}", f"fine_cells={mesh_summary.get('amr_equivalent_fine_cell_count')}", f"cloud_rel={mesh_summary.get('cloud_rel_diff')}"] if production_mesh_scout_ok else (['production-scale scout PASS-SCOUT', f"base_cells={scout_summary.get('base_cell_count')}", f"fine_cells={scout_summary.get('amr_equivalent_fine_cell_count')}"] if production_scale_scout_ok else ['smoke-scale Gaussian/profile and campaign evidence']))
            ),
            ['H2 LEL/UEL and ALOHA LOC threshold agreement exists, but external plume-shape datasets and case-specific acceptance tolerances remain missing'] if reference_agreement_ok else (['large-grid hybrid 8x2 scout exists, but real reference datasets and case-specific acceptance tolerances remain missing'] if hybrid_largegrid_8rank_120step_ok else (['production-mesh scout exists, but real reference datasets and case-specific acceptance tolerances remain missing'] if production_mesh_scout_ok else ['production-scale scout exists, but real reference datasets and case-specific acceptance tolerances remain missing'])),
        ),
    ]

    functional_total = round(sum(float(g['functional_points']) for g in gates), 1)
    production_total = round(sum(float(g['production_points']) for g in gates), 1)
    functional_weight = round(sum(float(g['functional_weight']) for g in gates), 1)
    production_weight = round(sum(float(g['production_weight']) for g in gates), 1)
    if functional_weight != 100.0 or production_weight != 100.0:
        raise ScorecardError(f'internal score weights must sum to 100, got {functional_weight}/{production_weight}')

    blocking_gaps = list(PRODUCTION_BLOCKERS)
    scheduler_gap = scheduler_blocking_gap(scheduler)
    if scheduler_gap:
        blocking_gaps.insert(0, scheduler_gap)
    campaign_gap = campaign_scale_blocking_gap(campaign, production_mesh_campaign)
    if campaign_gap:
        blocking_gaps.insert(1 if scheduler_gap else 0, campaign_gap)
    stability_gap = stability_duration_blocking_gap(
        production_mesh_1200step_stability_scout,
        full_duration_candidate,
    )
    if stability_gap:
        insert_at = int(bool(scheduler_gap)) + int(bool(campaign_gap))
        blocking_gaps.insert(insert_at, stability_gap)
    reference_gap = reference_data_blocking_gap(reference_agreement)
    if reference_gap:
        insert_at = int(bool(scheduler_gap)) + int(bool(campaign_gap)) + int(bool(stability_gap))
        blocking_gaps.insert(insert_at, reference_gap)
    real_cad_gap = real_cad_blocking_gap(campaign)
    if real_cad_gap:
        insert_at = (
            int(bool(scheduler_gap))
            + int(bool(campaign_gap))
            + int(bool(stability_gap))
            + int(bool(reference_gap))
        )
        blocking_gaps.insert(insert_at, real_cad_gap)
    fire_gap = fire_consequence_blocking_gap(fire_metrics)
    if fire_gap:
        insert_at = (
            int(bool(scheduler_gap))
            + int(bool(campaign_gap))
            + int(bool(stability_gap))
            + int(bool(reference_gap))
            + int(bool(real_cad_gap))
        )
        blocking_gaps.insert(insert_at, fire_gap)
    if bfs_kepsilon_reference_ok:
        blocking_gaps = [
            item for item in blocking_gaps
            if item != 'bfs_kepsilon_reference_validation_failed'
        ]
    status = 'NOT_PRODUCTION_READY'
    if not blocking_gaps and production_total >= 90.0:
        status = 'PRODUCTION_READY'

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'scores': {
            'engineering_functional_coverage_percent': functional_total,
            'engineering_production_credibility_percent': production_total,
            'engineering_initial_integrated_acceptance': integrated_initial_acceptance_ok,
            'interpretation': 'Functional coverage tracks maintained workflow breadth; production credibility tracks evidence strength for production use.',
        },
        'gates': gates,
        'evidence_files': evidence,
        'blocking_gaps': blocking_gaps,
        'summary': {
            'campaign_cases': len(case_names),
            'campaign_suites': len(suites),
            'campaign_evidence_tier': campaign.get('evidence_tier'),
            'campaign_scale': campaign.get('campaign_scale'),
            'campaign_production_campaign': campaign.get('production_campaign'),
            'campaign_production_size_mesh_campaign': campaign.get('production_size_mesh_campaign'),
            'campaign_full_duration_campaign': campaign.get('full_duration_campaign'),
            'campaign_scale_blocking_gap': campaign_gap,
            'production_mesh_campaign_status': production_mesh_campaign.get('status'),
            'production_mesh_campaign_scale': production_mesh_campaign.get('campaign_scale'),
            'production_mesh_campaign_production_size_mesh_campaign': (
                production_mesh_campaign.get('production_size_mesh_campaign')
            ),
            'production_mesh_campaign_full_duration_campaign': (
                production_mesh_campaign.get('full_duration_campaign')
            ),
            'full_duration_candidate_status': full_duration_candidate.get('status'),
            'full_duration_candidate_executed': full_duration_candidate.get('executed'),
            'full_duration_candidate_target': (
                full_duration_candidate.get('target')
                if isinstance(full_duration_candidate.get('target'), dict) else {}
            ),
            'geometry_evidence_tier': campaign.get('geometry_evidence_tier'),
            'synthetic_tank_farm_evidence': campaign.get('synthetic_tank_farm_evidence'),
            'synthetic_stl_pipeline_evidence': campaign.get('synthetic_stl_pipeline_evidence'),
            'real_cad_cleanup_campaign': campaign.get('real_cad_cleanup_campaign'),
            'real_cad_large_layout_campaign': campaign.get('real_cad_large_layout_campaign'),
            'real_cad_geometry_count': campaign.get('real_cad_geometry_count'),
            'real_cad_blocking_gap': real_cad_gap,
            'missing_cases': missing_cases,
            'missing_suites': missing_suites,
            'failed_cases': failed_cases,
            'scheduler_status': scheduler.get('status'),
            'scheduler_blocking_gap': scheduler_gap,
            'scheduler_submit_job_accepted': check_by_name(scheduler, 'scheduler_submit_job_accepted'),
            'runtime_affinity_status': affinity.get('status'),
            'hybrid_runtime_affinity_status': hybrid_affinity.get('status'),
            'hybrid_runtime_affinity_warnings': hybrid_affinity.get('warnings'),
            'ignition_status': ignition.get('status'),
            'fire_consequence_metrics_status': fire_metrics.get('status'),
            'fire_consequence_model_tier': fire_metrics.get('consequence_model_tier'),
            'fire_radiation_model_calibrated': fire_metrics.get('radiation_model_calibrated'),
            'fire_overpressure_model_calibrated': fire_metrics.get('overpressure_model_calibrated'),
            'fire_validated_against_fire_experiment': fire_metrics.get('validated_against_fire_experiment'),
            'fire_validated_against_blast_experiment': fire_metrics.get('validated_against_blast_experiment'),
            'fire_consequence_blocking_gap': fire_gap,
            'production_scale_scout_status': production_scale_scout.get('status'),
            'long_stability_scout_status': long_stability_scout.get('status'),
            'production_mesh_scout_status': production_mesh_scout.get('status'),
            'production_mesh_8rank_scout_status': production_mesh_8rank_scout.get('status'),
            'production_mesh_16rank_scout_status': production_mesh_16rank_scout.get('status'),
            'engineering_h2_mpi_scaling_status': mpi_scaling.get('status'),
            'engineering_h2_hybrid_cfd_scout_status': hybrid_cfd_scout.get('status'),
            'engineering_h2_hybrid_production_mesh_scout_status': hybrid_production_mesh_scout.get('status'),
            'engineering_h2_hybrid_production_mesh_8rank_scout_status': hybrid_production_mesh_8rank_scout.get('status'),
            'engineering_h2_hybrid_production_mesh_8rank_600step_stability_scout_status': (
                hybrid_production_mesh_8rank_600step_stability_scout.get('status')
            ),
            'engineering_h2_hybrid_production_mesh_600step_stability_scout_status': (
                hybrid_production_mesh_600step_stability_scout.get('status')
            ),
            'engineering_h2_hybrid_largegrid_8rank_120step_scout_status': (
                hybrid_largegrid_8rank_120step_scout.get('status')
            ),
            'engineering_h2_reference_agreement_status': reference_agreement.get('status'),
            'engineering_h2_reference_agreement_tier': reference_agreement.get('agreement_tier'),
            'engineering_h2_threshold_reference_agreement': (
                reference_agreement.get('threshold_reference_agreement')
            ),
            'engineering_h2_external_plume_shape_dataset_agreement': (
                reference_agreement.get('external_plume_shape_dataset_agreement')
            ),
            'engineering_h2_external_consequence_dataset_agreement': (
                reference_agreement.get('external_consequence_dataset_agreement')
            ),
            'engineering_h2_reference_data_blocking_gap': reference_gap,
            'engineering_bfs_kepsilon_reference_status': bfs_kepsilon_reference.get('status'),
            'engineering_bfs_kepsilon_reference_bfs_verdict': bfs_kepsilon_summary.get('bfs_validator_verdict'),
            'engineering_bfs_kepsilon_reference_loglaw_linf': bfs_kepsilon_summary.get('loglaw_linf'),
            'engineering_bfs_kepsilon_reference_blocks_production': (
                bfs_kepsilon_summary.get('blocks_production_readiness')
            ),
            'engineering_h2_engineering_scene_clearance_status': engineering_scene_clearance.get('status'),
            'engineering_h2_engineering_scene_clearance_ok': engineering_scene_clearance_ok,
            'engineering_h2_engineering_scene_clearance_decision': engineering_scene_clearance.get('decision'),
            'engineering_h2_engineering_scene_large_acceptance_cpu_mpi_ranks': (
                engineering_scene_metrics.get('ranks')
            ),
            'engineering_h2_engineering_scene_large_acceptance_base_cells': (
                engineering_scene_metrics.get('base_cell_count')
            ),
            'engineering_h2_engineering_scene_large_acceptance_equivalent_fine_cells': (
                engineering_scene_metrics.get('equivalent_finest_cell_count')
            ),
            'engineering_h2_engineering_scene_large_acceptance_amr_regrid_count': (
                engineering_scene_metrics.get('amr_regrid_count')
            ),
            'engineering_h2_engineering_scene_gpu_parallel_validated': (
                engineering_scene_validated.get('gpu_parallel')
            ),
            'engineering_h2_engineering_scene_large_coupled_ignition_fire_validated': (
                engineering_scene_validated.get('large_coupled_ignition_fire')
            ),
            'engineering_h2_pipe_rack_gpu_fire_obstacle_status': (
                pipe_rack_gpu_fire_obstacle.get('status')
            ),
            'engineering_h2_pipe_rack_gpu_parallel_validated': (
                pipe_rack_caps.get('gpu_obstacle_leak_dispersion')
            ),
            'engineering_h2_pipe_rack_mpi_cuda_parallel_validated': (
                pipe_rack_caps.get('mpi_cuda_obstacle_leak_dispersion')
            ),
            'engineering_h2_pipe_rack_mpi_cuda_ranks': pipe_rack_caps.get('mpi_cuda_ranks'),
            'engineering_h2_pipe_rack_mpi_cuda_devices': pipe_rack_caps.get('mpi_cuda_devices'),
            'engineering_h2_pipe_rack_fire_screening_validated': (
                pipe_rack_caps.get('fire_consequence_screening')
            ),
            'engineering_h2_pipe_rack_direct_coupled_3d_fire_validated': (
                pipe_rack_caps.get('direct_coupled_3d_fire_propagation')
            ),
            'engineering_h2_pipe_rack_gpu_arch': pipe_rack_caps.get('gpu_cuda_arch'),
            'engineering_h2_pipe_rack_gpu_cloud_volume': pipe_rack_gpu_metrics.get('cloud_volume'),
            'engineering_h2_pipe_rack_fire_max_flux_w_m2': (
                pipe_rack_fire_summary.get('max_screening_flux_w_m2')
            ),
            'engineering_h2_pipe_rack_fire_max_overpressure_kpa': (
                pipe_rack_fire_summary.get('max_screening_overpressure_kpa')
            ),
            'engineering_h2_reacting_mpi_cuda_smoke_status': reacting_mpi_cuda_smoke.get('status'),
            'engineering_h2_reacting_solver_mpi_cuda_validated': (
                reacting_caps.get('mpi_cuda_2rank_2device')
            ),
            'engineering_h2_reacting_solver_mpi_ranks': reacting_checks.get('mpi_ranks'),
            'engineering_h2_reacting_solver_cuda_devices': reacting_checks.get('cuda_devices'),
            'engineering_h2_reacting_direct_engineering_obstacle_fire_propagation': (
                reacting_caps.get('direct_engineering_obstacle_fire_propagation')
            ),
            'engineering_h2_pipe_rack_direct_reacting_cuda_status': (
                pipe_rack_direct_reacting_cuda.get('status')
            ),
            'engineering_h2_pipe_rack_direct_reacting_cuda_validated': (
                pipe_rack_direct_reacting_cuda_ok
            ),
            'engineering_h2_pipe_rack_direct_reacting_cuda_devices': (
                direct_reacting_checks.get('cuda_devices')
            ),
            'engineering_h2_pipe_rack_direct_reacting_max_step': (
                direct_reacting_input.get('max_step')
            ),
            'engineering_h2_pipe_rack_direct_reacting_final_time': (
                direct_reacting_plot_checks.get('final_time')
            ),
            'engineering_h2_pipe_rack_direct_reacting_final_y_h2o': (
                direct_reacting_plot_checks.get('sustained_reaction_checks', {}).get('final_y_h2o_max')
            ),
            'engineering_h2_pipe_rack_direct_reacting_full_duration_fire_propagation': (
                direct_reacting_caps.get('full_duration_fire_propagation')
            ),
            'engineering_h2_pipe_rack_direct_reacting_mpi_cuda_status': (
                pipe_rack_direct_reacting_mpi_cuda.get('status')
            ),
            'engineering_h2_pipe_rack_direct_reacting_mpi_cuda_validated': (
                pipe_rack_direct_reacting_mpi_cuda_ok
            ),
            'engineering_h2_pipe_rack_direct_reacting_mpi_cuda_ranks': (
                direct_reacting_mpi_cuda_checks.get('mpi_ranks')
            ),
            'engineering_h2_pipe_rack_direct_reacting_mpi_cuda_devices': (
                direct_reacting_mpi_cuda_checks.get('cuda_devices')
            ),
            'engineering_h2_pipe_rack_direct_reacting_mpi_cuda_final_time': (
                direct_reacting_mpi_cuda_plot_checks.get('final_time')
            ),
            'engineering_h2_pipe_rack_direct_reacting_mpi_cuda_final_y_h2o': (
                direct_reacting_mpi_cuda_sustained_checks.get('final_y_h2o_max')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_status': (
                pipe_rack_direct_reacting_largegrid_cuda.get('status')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_validated': (
                pipe_rack_direct_reacting_largegrid_cuda_ok
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_n_cell': (
                direct_reacting_largegrid_input.get('n_cell')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_final_time': (
                direct_reacting_largegrid_plot_checks.get('final_time')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_final_y_h2o': (
                direct_reacting_largegrid_sustained_checks.get('final_y_h2o_max')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_status': (
                pipe_rack_direct_reacting_largegrid_mpi_cuda.get('status')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_validated': (
                pipe_rack_direct_reacting_largegrid_mpi_cuda_ok
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_n_cell': (
                direct_reacting_largegrid_mpi_cuda_input.get('n_cell')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_ranks': (
                direct_reacting_largegrid_mpi_cuda_checks.get('mpi_ranks')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_devices': (
                direct_reacting_largegrid_mpi_cuda_checks.get('cuda_devices')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_final_time': (
                direct_reacting_largegrid_mpi_cuda_plot_checks.get('final_time')
            ),
            'engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_final_y_h2o': (
                direct_reacting_largegrid_mpi_cuda_sustained_checks.get('final_y_h2o_max')
            ),
            'engineering_h2_pipe_rack_reacting_mpi_cuda_restart_status': (
                pipe_rack_reacting_mpi_cuda_restart.get('status')
            ),
            'engineering_h2_pipe_rack_reacting_mpi_cuda_restart_validated': (
                pipe_rack_reacting_mpi_cuda_restart_ok
            ),
            'engineering_h2_pipe_rack_reacting_mpi_cuda_restart_initial_step': (
                reacting_restart_checks.get('initial_step')
            ),
            'engineering_h2_pipe_rack_reacting_mpi_cuda_restart_final_step': (
                reacting_restart_checks.get('final_step')
            ),
            'engineering_h2_pipe_rack_reacting_mpi_cuda_restart_post_outputs': (
                reacting_restart_checks.get('post_restart_sustained_output_count')
            ),
            'engineering_h2_pipe_rack_reacting_mpi_cuda_restart_final_y_h2o': (
                reacting_restart_checks.get('final_y_h2o_max')
            ),
            'engineering_h2_fire_consequence_traceability_status': (
                fire_consequence_traceability.get('status')
            ),
            'engineering_h2_fire_consequence_traceability_validated': (
                fire_consequence_traceability_ok
            ),
            'engineering_h2_fire_consequence_traceability_formula_checks': (
                len(fire_trace_formula_checks) if isinstance(fire_trace_formula_checks, list) else None
            ),
            'engineering_h2_fire_consequence_traceability_distance_checks': (
                len(fire_trace_distance_checks) if isinstance(fire_trace_distance_checks, list) else None
            ),
            'engineering_h2_integrated_initial_acceptance_status': (
                integrated_initial_acceptance.get('status')
            ),
            'engineering_h2_integrated_initial_acceptance_validated': (
                integrated_initial_acceptance_ok
            ),
            'engineering_h2_initial_integrated_goal_cleared': (
                integrated_initial_acceptance.get('clears_initial_integrated_engineering_goal')
            ),
            'engineering_h2_full_production_certification_cleared': (
                integrated_initial_acceptance.get('clears_full_production_certification')
            ),
            'production_mesh_8rank_600step_stability_scout_status': production_mesh_8rank_600step_stability_scout.get('status'),
            'production_mesh_600step_stability_scout_status': production_mesh_600step_stability_scout.get('status'),
            'production_mesh_1200step_stability_scout_status': production_mesh_1200step_stability_scout.get('status'),
            'production_mesh_1200step_stability_duration_class': (
                production_mesh_1200step_stability_scout.get('stability_duration_class')
            ),
            'production_mesh_1200step_full_duration_campaign': (
                production_mesh_1200step_stability_scout.get('full_duration_campaign')
            ),
            'production_mesh_1200step_overnight_campaign': (
                production_mesh_1200step_stability_scout.get('overnight_campaign')
            ),
            'production_mesh_1200step_full_plotfile_archive': (
                production_mesh_1200step_stability_scout.get('full_plotfile_archive')
            ),
            'stability_duration_blocking_gap': stability_gap,
            'engineering_h2_acceptance_matrix_status': acceptance_matrix.get('status'),
            'engineering_h2_acceptance_matrix_pass_like_rows': matrix_summary.get('pass_like_rows'),
            'engineering_h2_acceptance_matrix_not_ready_rows': matrix_summary.get('not_ready_rows'),
        },
        'limitations': [
            'This scorecard is an engineering evidence ledger, not an external safety certification.',
            'Scores are intentionally capped by remaining real-CAD, calibrated fire-consequence, and external reference-data evidence gaps.',
            'BFS/k-epsilon reference validation is reported separately in the summary and only blocks production when its validator status is NOT_READY.',
        ],
    }


def write_markdown(scorecard: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering Production Scorecard',
        '',
        f"Status: `{scorecard['status']}`",
        '',
        '## Scores',
        '',
        f"- Engineering functional coverage: `{scorecard['scores']['engineering_functional_coverage_percent']:.1f}%`",
        f"- Engineering production credibility: `{scorecard['scores']['engineering_production_credibility_percent']:.1f}%`",
        f"- Engineering initial integrated acceptance: `{scorecard['scores'].get('engineering_initial_integrated_acceptance')}`",
        '',
        '## Gates',
        '',
        '| Gate | Status | Functional pts | Production pts | Main gaps |',
        '| --- | --- | ---: | ---: | --- |',
    ]
    for g in scorecard['gates']:
        gaps = '; '.join(g['gaps']) if g['gaps'] else 'none recorded'
        lines.append(
            f"| `{g['name']}` | `{g['status']}` | {g['functional_points']:.1f}/{g['functional_weight']:.1f} | {g['production_points']:.1f}/{g['production_weight']:.1f} | {gaps} |"
        )
    lines += [
        '',
        '## Blocking Gaps',
        '',
    ]
    for item in scorecard['blocking_gaps']:
        lines.append(f'- `{item}`')
    lines += [
        '',
        '## Evidence Files',
        '',
    ]
    for item in scorecard['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    path.write_text('\n'.join(lines) + '\n')


def verify_scorecard(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if data.get('schema_version') != SCHEMA_VERSION:
        raise ScorecardError(f'schema_version mismatch in {path}')
    if data.get('status') not in {'NOT_PRODUCTION_READY', 'PRODUCTION_READY'}:
        raise ScorecardError(f'invalid scorecard status in {path}: {data.get("status")}')
    scores = data.get('scores', {})
    functional = scores.get('engineering_functional_coverage_percent')
    production = scores.get('engineering_production_credibility_percent')
    if not finite_number(functional) or not 0.0 <= float(functional) <= 100.0:
        raise ScorecardError('invalid functional coverage score')
    if not finite_number(production) or not 0.0 <= float(production) <= 100.0:
        raise ScorecardError('invalid production credibility score')
    if float(production) >= 90.0 and data.get('blocking_gaps'):
        raise ScorecardError('high production score cannot retain blocking gaps')
    initial_acceptance = scores.get('engineering_initial_integrated_acceptance')
    if initial_acceptance is not None and not isinstance(initial_acceptance, bool):
        raise ScorecardError('invalid initial integrated acceptance flag')
    summary = data.get('summary', {})
    if initial_acceptance and summary.get('engineering_h2_integrated_initial_acceptance_validated') is not True:
        raise ScorecardError('initial integrated acceptance score disagrees with summary')
    gates = data.get('gates')
    if not isinstance(gates, list) or not gates:
        raise ScorecardError('scorecard gates missing')
    for item in data.get('evidence_files', []):
        p = Path(item.get('path', ''))
        if not p.exists():
            raise ScorecardError(f'referenced evidence file missing: {p}')
        if sha256_file(p) != item.get('sha256'):
            raise ScorecardError(f'referenced evidence hash mismatch: {p}')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--campaign-manifest', default=str(DEFAULT_CAMPAIGN_MANIFEST))
    ap.add_argument('--release-pack', default=str(DEFAULT_RELEASE_PACK))
    ap.add_argument('--runtime-affinity-manifest', default=str(DEFAULT_AFFINITY))
    ap.add_argument('--hybrid-runtime-affinity-manifest', default=str(DEFAULT_HYBRID_AFFINITY))
    ap.add_argument('--scheduler-report', default=str(DEFAULT_SCHEDULER))
    ap.add_argument('--ignition-consequence-report', default=str(DEFAULT_IGNITION))
    ap.add_argument('--fire-consequence-metrics-report', default=str(DEFAULT_FIRE_CONSEQUENCE_METRICS))
    ap.add_argument('--production-scale-scout-report', default=str(DEFAULT_PRODUCTION_SCALE_SCOUT))
    ap.add_argument('--long-stability-scout-report', default=str(DEFAULT_LONG_STABILITY_SCOUT))
    ap.add_argument('--production-mesh-scout-report', default=str(DEFAULT_PRODUCTION_MESH_SCOUT))
    ap.add_argument('--production-mesh-8rank-scout-report', default=str(DEFAULT_PRODUCTION_MESH_8RANK_SCOUT))
    ap.add_argument('--production-mesh-16rank-scout-report', default=str(DEFAULT_PRODUCTION_MESH_16RANK_SCOUT))
    ap.add_argument(
        '--production-mesh-8rank-600step-stability-scout-report',
        default=str(DEFAULT_PRODUCTION_MESH_8RANK_600STEP_STABILITY_SCOUT),
    )
    ap.add_argument(
        '--production-mesh-600step-stability-scout-report',
        default=str(DEFAULT_PRODUCTION_MESH_600STEP_STABILITY_SCOUT),
    )
    ap.add_argument(
        '--production-mesh-1200step-stability-scout-report',
        default=str(DEFAULT_PRODUCTION_MESH_1200STEP_STABILITY_SCOUT),
    )
    ap.add_argument(
        '--engineering-h2-production-mesh-campaign-report',
        default=str(DEFAULT_ENGINEERING_H2_PRODUCTION_MESH_CAMPAIGN),
    )
    ap.add_argument(
        '--engineering-h2-full-duration-candidate-report',
        default=str(DEFAULT_ENGINEERING_H2_FULL_DURATION_CANDIDATE),
    )
    ap.add_argument(
        '--engineering-h2-acceptance-matrix',
        default=str(DEFAULT_ENGINEERING_H2_ACCEPTANCE_MATRIX),
    )
    ap.add_argument(
        '--engineering-h2-mpi-scaling-report',
        default=str(DEFAULT_ENGINEERING_H2_MPI_SCALING),
    )
    ap.add_argument(
        '--engineering-h2-hybrid-cfd-scout-report',
        default=str(DEFAULT_ENGINEERING_H2_HYBRID_CFD_SCOUT),
    )
    ap.add_argument(
        '--engineering-h2-hybrid-production-mesh-scout-report',
        default=str(DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_SCOUT),
    )
    ap.add_argument(
        '--engineering-h2-hybrid-production-mesh-8rank-scout-report',
        default=str(DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_8RANK_SCOUT),
    )
    ap.add_argument(
        '--engineering-h2-hybrid-production-mesh-8rank-600step-stability-scout-report',
        default=str(DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_8RANK_600STEP_STABILITY_SCOUT),
    )
    ap.add_argument(
        '--engineering-h2-hybrid-production-mesh-600step-stability-scout-report',
        default=str(DEFAULT_ENGINEERING_H2_HYBRID_PRODUCTION_MESH_600STEP_STABILITY_SCOUT),
    )
    ap.add_argument(
        '--engineering-h2-hybrid-largegrid-8rank-120step-scout-report',
        default=str(DEFAULT_ENGINEERING_H2_HYBRID_LARGEGRID_8RANK_120STEP_SCOUT),
    )
    ap.add_argument(
        '--engineering-h2-reference-agreement-report',
        default=str(DEFAULT_ENGINEERING_H2_REFERENCE_AGREEMENT),
    )
    ap.add_argument(
        '--engineering-bfs-kepsilon-reference-report',
        default=str(DEFAULT_ENGINEERING_BFS_KEPSILON_REFERENCE),
    )
    ap.add_argument(
        '--engineering-h2-engineering-scene-clearance-report',
        default=str(DEFAULT_ENGINEERING_H2_ENGINEERING_SCENE_CLEARANCE),
    )
    ap.add_argument(
        '--engineering-h2-pipe-rack-gpu-fire-obstacle-report',
        default=str(DEFAULT_ENGINEERING_H2_PIPE_RACK_GPU_FIRE_OBSTACLE),
    )
    ap.add_argument(
        '--engineering-h2-reacting-mpi-cuda-smoke-report',
        default=str(DEFAULT_ENGINEERING_H2_REACTING_MPI_CUDA_SMOKE),
    )
    ap.add_argument(
        '--engineering-h2-pipe-rack-direct-reacting-cuda-report',
        default=str(DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_CUDA),
    )
    ap.add_argument(
        '--engineering-h2-pipe-rack-direct-reacting-mpi-cuda-report',
        default=str(DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_MPI_CUDA),
    )
    ap.add_argument(
        '--engineering-h2-pipe-rack-direct-reacting-largegrid-cuda-report',
        default=str(DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_LARGEGRID_CUDA),
    )
    ap.add_argument(
        '--engineering-h2-pipe-rack-direct-reacting-largegrid-mpi-cuda-report',
        default=str(DEFAULT_ENGINEERING_H2_PIPE_RACK_DIRECT_REACTING_LARGEGRID_MPI_CUDA),
    )
    ap.add_argument(
        '--engineering-h2-pipe-rack-reacting-mpi-cuda-restart-report',
        default=str(DEFAULT_ENGINEERING_H2_PIPE_RACK_REACTING_MPI_CUDA_RESTART),
    )
    ap.add_argument(
        '--engineering-h2-fire-consequence-traceability-report',
        default=str(DEFAULT_ENGINEERING_H2_FIRE_CONSEQUENCE_TRACEABILITY),
    )
    ap.add_argument(
        '--engineering-h2-integrated-initial-acceptance-report',
        default=str(DEFAULT_ENGINEERING_H2_INTEGRATED_INITIAL_ACCEPTANCE),
    )
    ap.add_argument('--output-json')
    ap.add_argument('--output-md')
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)

    try:
        if args.verify_json:
            data = verify_scorecard(Path(args.verify_json))
            print(
                'engineering_production_scorecard VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"functional={data['scores']['engineering_functional_coverage_percent']:.1f} "
                f"production={data['scores']['engineering_production_credibility_percent']:.1f}"
            )
            return 0
        if not args.output_json or not args.output_md:
            raise ScorecardError('--output-json and --output-md are required unless --verify-json is used')
        scorecard = build_scorecard(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + '\n')
        write_markdown(scorecard, out_md)
        print(
            'engineering_production_scorecard PASS '
            f"json={out_json} md={out_md} status={scorecard['status']} "
            f"functional={scorecard['scores']['engineering_functional_coverage_percent']:.1f} "
            f"production={scorecard['scores']['engineering_production_credibility_percent']:.1f}"
        )
        return 0
    except ScorecardError as exc:
        print(f'engineering_production_scorecard FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
