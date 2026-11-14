#!/usr/bin/env python3
"""Create and validate an engineering CFD campaign manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ManifestError(RuntimeError):
    pass


REAL_CAD_DATASET_TYPE = 'engineering_real_cad_cleanup_evidence'
REAL_CAD_SOURCE_TYPES = {
    'owner_operator_cad',
    'as_built_cad',
    'vendor_cad',
    'plant_cad',
}
CAD_FILE_EXTENSIONS = {'.stl', '.step', '.stp', '.iges', '.igs', '.brep', '.obj'}
REQUIRED_REAL_CAD_PROVENANCE_FIELDS = (
    'title',
    'owner_or_supplier',
    'drawing_or_package_id',
    'revision',
    'received_at_utc',
    'confidentiality',
)
UTC_TIMESTAMP_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def finite_number(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ManifestError(f'nonfinite {label}: {value!r}')
    return number


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def read_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f'missing case report: {path}')
    data = json.loads(path.read_text(encoding='utf-8'))
    require(data.get('schema_version') == 1, f'{path} schema_version is not 1')
    require(data.get('status') == 'PASS', f'{path} status is not PASS')
    require(data.get('case_name'), f'{path} missing case_name')
    require(data.get('evidence_root'), f'{path} missing evidence_root')
    limitations = data.get('limitations')
    require(isinstance(limitations, list) and limitations, f'{path} missing limitations')
    for key in ('reduced_long', 'plan_amr_compare', 'amr_overhead', 'logs', 'inputs', 'evidence_files'):
        require(key in data, f'{path} missing {key}')
    return data


def validate_report_payload(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    reduced = data['reduced_long']
    amr = reduced['amr']
    baseline = reduced['baseline']
    deltas = reduced['amr_deltas']
    overhead = data['amr_overhead']['amr_ratios']
    compare_amr = data['plan_amr_compare']['amr']

    ranks = int(amr['ranks'])
    max_step = int(amr['max_step'])
    plotfiles = int(amr['plotfiles'])
    final_time = finite_number(amr['final_time'], 'amr.final_time')
    final_cloud = finite_number(amr['final_cloud_volume'], 'amr.final_cloud_volume')
    final_peak = finite_number(amr['final_peak_X'], 'amr.final_peak_X')
    final_planes = int(amr['final_flammable_planes'])
    cloud_rel = finite_number(deltas['cloud_rel_diff'], 'amr.cloud_rel_diff')
    peak_rel = finite_number(deltas['peak_rel_diff'], 'amr.peak_rel_diff')
    mean_cell_ratio = finite_number(overhead['mean_ncells_ratio'], 'overhead.mean_ncells_ratio')
    advance_ratio = finite_number(overhead['advance_seconds_ratio'], 'overhead.advance_seconds_ratio')
    plot_bytes_ratio = finite_number(overhead['final_plotfile_bytes_ratio'], 'overhead.final_plotfile_bytes_ratio')

    require(ranks >= 1, 'MPI ranks must be positive')
    require(max_step >= 1 and int(amr['final_step']) == max_step, 'final_step must match max_step')
    require(plotfiles >= 2, 'case must include multiple plotfiles')
    require(final_time > 0.0, 'final_time must be positive')
    require(final_cloud > 0.0 and final_peak > 0.0 and final_planes >= 1, 'final hazard metrics must be positive')
    require(int(amr['finest_level']) >= 1, 'AMR case must reach at least Level 1')
    require(int(compare_amr['regrid_count']) > 0, 'AMR case must regrid dynamically')
    require(finite_number(baseline['final_cloud_volume'], 'baseline.final_cloud_volume') > 0.0, 'baseline final cloud must be positive')
    require(0.0 <= cloud_rel <= 0.60, f'cloud_rel_diff out of campaign bound: {cloud_rel}')
    require(0.0 <= peak_rel <= 0.65, f'peak_rel_diff out of campaign bound: {peak_rel}')
    require(mean_cell_ratio >= 1.0 and advance_ratio >= 1.0 and plot_bytes_ratio >= 1.0, 'AMR overhead ratios should be >= 1')

    input_hashes = []
    for item in data['inputs']:
        input_path = Path(item['path'])
        require(input_path.is_file(), f'missing hashed input: {input_path}')
        actual = sha256_file(input_path)
        require(actual == item['sha256'], f'input hash mismatch for {input_path}')
        input_hashes.append({'path': str(input_path), 'sha256': actual})

    evidence_hashes = []
    for name, item in sorted(data['evidence_files'].items()):
        evidence_path = Path(item['path'])
        require(evidence_path.is_file(), f'missing hashed evidence file: {evidence_path}')
        actual = sha256_file(evidence_path)
        require(actual == item['sha256'], f'evidence hash mismatch for {evidence_path}')
        evidence_hashes.append({'name': name, 'path': str(evidence_path), 'sha256': actual})

    for case in ('baseline', 'amr'):
        logs = data['logs'][case]
        for log_name in ('validation.log', 'profile_validation.log', 'hazard_summary.log', 'hazard_planes.log', 'hazard_timeseries.log', 'mpi_validation.log', 'run.log'):
            require(log_name in logs, f'{data["case_name"]} missing {case}/{log_name} log record')
            log_path = Path(logs[log_name]['path'])
            require(log_path.is_file(), f'missing log file {log_path}')

    return {
        'case_name': data['case_name'],
        'status': data['status'],
        'case_report_path': str(path),
        'case_report_sha256': sha256_file(path),
        'evidence_root': data['evidence_root'],
        'ranks': ranks,
        'max_step': max_step,
        'plotfiles': plotfiles,
        'final_time': final_time,
        'baseline_final_cloud_volume': finite_number(baseline['final_cloud_volume'], 'baseline.final_cloud_volume'),
        'amr_final_cloud_volume': final_cloud,
        'amr_final_peak_X': final_peak,
        'amr_final_flammable_planes': final_planes,
        'cloud_rel_diff': cloud_rel,
        'peak_rel_diff': peak_rel,
        'mean_ncells_ratio': mean_cell_ratio,
        'advance_seconds_ratio': advance_ratio,
        'final_plotfile_bytes_ratio': plot_bytes_ratio,
        'amr_finest_level': int(amr['finest_level']),
        'amr_regrid_count': int(compare_amr['regrid_count']),
        'input_hashes': input_hashes,
        'evidence_hashes': evidence_hashes,
        'limitations': data['limitations'],
    }


def validate_runner_case(case: dict[str, Any]) -> dict[str, Any]:
    name = str(case.get('name', ''))
    require(name, 'runner case missing name')
    suite = str(case.get('suite', ''))
    require(suite, f'{name} missing suite')
    require(case.get('status') == 'PASS', f'{name} status is not PASS')
    require(int(case.get('returncode', -1)) == 0, f'{name} returncode is not zero')
    require(not case.get('missing_required_files'), f'{name} has missing required files')
    require(not case.get('log_failure_markers'), f'{name} has log failure markers')

    root = Path(str(case.get('root', '')))
    require(root.is_dir(), f'{name} missing case root: {root}')
    log_path = Path(str(case.get('case_log', '')))
    require(log_path.is_file(), f'{name} missing case log: {log_path}')
    script = Path(str(case.get('script', '')))
    require(script.is_file(), f'{name} missing wrapper script: {script}')
    duration_s = finite_number(case.get('duration_s'), f'{name}.duration_s')
    require(duration_s > 0.0, f'{name} duration must be positive')

    required_files = case.get('required_files')
    required_hashes = case.get('required_file_hashes')
    require(isinstance(required_files, list) and required_files, f'{name} missing required_files')
    require(isinstance(required_hashes, list), f'{name} missing required_file_hashes')
    require(len(required_hashes) == len(required_files), f'{name} required hash count mismatch')

    evidence_hashes = []
    seen_required = set()
    for item in required_hashes:
        path = Path(str(item.get('path', '')))
        require(path.is_file(), f'{name} missing required evidence file: {path}')
        sha256 = str(item.get('sha256', ''))
        require(len(sha256) == 64, f'{name} malformed sha256 for {path}')
        actual = sha256_file(path)
        require(actual == sha256, f'{name} hash mismatch for {path}')
        seen_required.add(path.name)
        evidence_hashes.append({'path': str(path), 'sha256': actual})
    require(seen_required == set(required_files), f'{name} required file names do not match hashed files')

    return {
        'name': name,
        'suite': suite,
        'status': 'PASS',
        'script': str(script),
        'command': case.get('command', []),
        'case_log': str(log_path),
        'case_log_sha256': sha256_file(log_path),
        'root': str(root),
        'duration_s': duration_s,
        'timeout_s': int(case.get('timeout_s', 0)),
        'required_files': required_files,
        'required_file_hashes': evidence_hashes,
        'started_at_utc': case.get('started_at_utc'),
        'finished_at_utc': case.get('finished_at_utc'),
        'description': case.get('description', ''),
    }


def validate_cad_file_entry(entry: dict[str, Any], label: str) -> dict[str, Any]:
    path = Path(str(entry.get('path', '')))
    require(path.is_file(), f'{label} missing file: {path}')
    suffix = path.suffix.lower()
    require(suffix in CAD_FILE_EXTENSIONS, f'{label} has unsupported CAD/geometry extension: {path}')
    sha256 = str(entry.get('sha256', ''))
    require(len(sha256) == 64, f'{label} malformed sha256 for {path}')
    actual = sha256_file(path)
    require(actual == sha256, f'{label} hash mismatch for {path}')
    size_bytes = path.stat().st_size
    require(size_bytes > 0, f'{label} file is empty: {path}')
    return {'path': str(path), 'sha256': actual, 'size_bytes': size_bytes}


def validate_real_cad_provenance(provenance: Any, label: str) -> dict[str, Any]:
    require(isinstance(provenance, dict), f'{label} missing provenance object')
    cleaned: dict[str, Any] = {}
    for key in REQUIRED_REAL_CAD_PROVENANCE_FIELDS:
        value = str(provenance.get(key, '')).strip()
        require(value, f'{label} missing provenance.{key}')
        cleaned[key] = value
    received = cleaned['received_at_utc']
    require(UTC_TIMESTAMP_RE.match(received) is not None, f'{label} provenance.received_at_utc must be YYYY-MM-DDTHH:MM:SSZ')
    return cleaned


def validate_real_cad_cleanup_manifest(path: Path, campaign: str) -> dict[str, Any]:
    require(path.is_file(), f'missing real CAD cleanup manifest: {path}')
    data = json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(data, dict), f'{path} must contain a JSON object')
    require(data.get('schema_version') == 1, f'{path} schema_version is not 1')
    require(data.get('dataset_type') == REAL_CAD_DATASET_TYPE, f'{path} dataset_type is not {REAL_CAD_DATASET_TYPE}')
    require(data.get('campaign') == campaign, f'{path} campaign does not match {campaign}')
    require(data.get('status') == 'PASS', f'{path} status is not PASS')
    require(data.get('synthetic') is False, f'{path} must explicitly be non-synthetic')
    require(data.get('cad_source_is_real') is True, f'{path} must explicitly mark real CAD source')
    source_type = data.get('source_type')
    require(source_type in REAL_CAD_SOURCE_TYPES, f'{path} unsupported source_type: {source_type}')

    provenance = validate_real_cad_provenance(data.get('provenance'), str(path))

    geometries = data.get('geometries')
    require(isinstance(geometries, list) and geometries, f'{path} missing geometries')
    large_layout = data.get('large_layout_campaign') is True
    source_entries = []
    cleaned_entries = []
    seen_labels = set()
    bbox_union = None
    for idx, geom in enumerate(geometries):
        require(isinstance(geom, dict), f'{path} geometry #{idx} is not an object')
        label = str(geom.get('label', '')).strip()
        require(label, f'{path} geometry #{idx} missing label')
        require(label not in seen_labels, f'{path} duplicate geometry label: {label}')
        seen_labels.add(label)
        source_entries.append(validate_cad_file_entry(geom.get('source_cad', {}), f'{path}:{label}:source_cad'))
        cleaned_entries.append(validate_cad_file_entry(geom.get('cleaned_geometry', {}), f'{path}:{label}:cleaned_geometry'))

        cleanup = geom.get('cleanup_checks')
        require(isinstance(cleanup, dict), f'{path}:{label} missing cleanup_checks')
        for key in ('units_declared', 'watertight_or_closed_surface', 'nondegenerate_elements', 'positive_volume_or_area'):
            require(cleanup.get(key) is True, f'{path}:{label} cleanup check failed: {key}')
        for key in ('bbox_min_m', 'bbox_max_m'):
            values = cleanup.get(key)
            require(isinstance(values, list) and len(values) == 3, f'{path}:{label} invalid {key}')
            cleanup[key] = [finite_number(v, f'{label}.{key}') for v in values]
        bbox_min = cleanup['bbox_min_m']
        bbox_max = cleanup['bbox_max_m']
        for lo, hi in zip(bbox_min, bbox_max):
            require(hi > lo, f'{path}:{label} bbox max must exceed min')
        if bbox_union is None:
            bbox_union = [bbox_min[:], bbox_max[:]]
        else:
            bbox_union[0] = [min(a, b) for a, b in zip(bbox_union[0], bbox_min)]
            bbox_union[1] = [max(a, b) for a, b in zip(bbox_union[1], bbox_max)]

    require(len(geometries) >= 1, f'{path} real CAD cleanup requires at least one geometry')
    require(not large_layout or len(geometries) >= 3, f'{path} large-layout CAD evidence requires at least three geometries')
    extents = [hi - lo for lo, hi in zip(bbox_union[0], bbox_union[1])] if bbox_union else [0.0, 0.0, 0.0]
    require(not large_layout or sum(1 for value in extents if value > 0.0) >= 2, f'{path} large-layout CAD bbox is degenerate')
    return {
        'path': str(path),
        'sha256': sha256_file(path),
        'status': 'PASS',
        'dataset_type': REAL_CAD_DATASET_TYPE,
        'source_type': source_type,
        'provenance': provenance,
        'geometry_count': len(geometries),
        'large_layout_campaign': large_layout,
        'bbox_union_m': {'min': bbox_union[0], 'max': bbox_union[1], 'extent': extents},
        'source_cad_files': source_entries,
        'cleaned_geometry_files': cleaned_entries,
    }


def read_runner_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f'missing campaign run summary: {path}')
    data = json.loads(path.read_text(encoding='utf-8'))
    require(data.get('schema_version') == 1, f'{path} schema_version is not 1')
    require(data.get('status') == 'PASS', f'{path} status is not PASS')
    require(data.get('suite'), f'{path} missing suite')
    require(data.get('campaign'), f'{path} missing campaign')
    cases = data.get('cases')
    require(isinstance(cases, list) and cases, f'{path} missing cases')
    require(int(data.get('case_count', -1)) == len(cases), f'{path} case_count mismatch')
    output_root = Path(str(data.get('output_root', '')))
    require(output_root.is_dir(), f'{path} output_root is missing: {output_root}')
    summary_md = path.with_suffix('.md')
    require(summary_md.is_file(), f'{path} markdown summary is missing: {summary_md}')
    return data


def apply_real_cad_metadata(manifest: dict[str, Any], cad_manifest_path: Path | None) -> dict[str, Any]:
    if not cad_manifest_path:
        return manifest
    cad = validate_real_cad_cleanup_manifest(cad_manifest_path, manifest['campaign'])
    manifest.update({
        'geometry_evidence_tier': 'real_cad_cleanup',
        'real_cad_cleanup_campaign': True,
        'real_cad_large_layout_campaign': bool(cad['large_layout_campaign']),
        'real_cad_geometry_count': int(cad['geometry_count']),
        'clears_real_cad_cleanup_blocker': bool(cad['large_layout_campaign'] and cad['geometry_count'] >= 3),
        'real_cad_cleanup_evidence': cad,
    })
    manifest['global_limitations'] = [
        item for item in manifest['global_limitations']
        if 'real CAD' not in item and 'real CAD/tank-farm' not in item
    ]
    manifest['global_limitations'].append(
        'Real CAD evidence proves source/cleaned geometry provenance, hashes, and declared cleanup checks; it does not by itself prove CFD accuracy for every possible plant layout.'
    )
    return manifest


def build_report_manifest(campaign: str, reports: list[Path], cad_manifest_path: Path | None) -> dict[str, Any]:
    require(reports, 'at least one case report is required')
    cases = []
    seen = set()
    for report_path in reports:
        data = read_report(report_path)
        case = validate_report_payload(report_path, data)
        require(case['case_name'] not in seen, f'duplicate case name {case["case_name"]}')
        seen.add(case['case_name'])
        cases.append(case)
    geometry = geometry_coverage_metadata(cases)
    manifest = {
        'schema_version': 1,
        'status': 'PASS',
        'source_type': 'case_reports',
        'campaign': campaign,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'case_count': len(cases),
        'cases': cases,
        **geometry,
        'evidence_tier': 'reduced_long_scout',
        'campaign_scale': 'engineering_reduced_long_scout',
        'production_campaign': False,
        'production_size_mesh_campaign': False,
        'full_duration_campaign': False,
        'production_readiness_scope': 'engineering H2 leak reduced-long evidence packaging and verification',
        'global_limitations': [
            'Manifest proves evidence packaging and internal consistency for listed cases only.',
            'It does not prove production-scale CFD accuracy, real CAD/tank-farm coverage, scheduler affinity, overnight stability, fire heat-release validation, or experimental/reference-data agreement.',
        ],
    }
    return apply_real_cad_metadata(manifest, cad_manifest_path)


def compact_repo_metadata(repo: dict[str, Any]) -> dict[str, Any]:
    dirty_short = str(repo.get('dirty_short', ''))
    compact = {
        'branch': repo.get('branch'),
        'commit': repo.get('commit'),
        'dirty': bool(dirty_short.strip()),
        'dirty_short_line_count': len([line for line in dirty_short.splitlines() if line.strip()]),
    }
    if dirty_short:
        compact['dirty_short_sha256'] = hashlib.sha256(dirty_short.encode('utf-8')).hexdigest()
    return compact


def geometry_coverage_metadata(cases: list[dict[str, Any]]) -> dict[str, Any]:
    case_names = {str(case.get('name') or case.get('case_name') or '') for case in cases}
    has_synthetic_tank_farm = 'tank-farm' in case_names
    has_synthetic_stl = bool({'stl-multifile', 'stl-perfile-transform'} & case_names)
    return {
        'geometry_evidence_tier': 'synthetic_obstacle_regression' if (has_synthetic_tank_farm or has_synthetic_stl) else 'none',
        'synthetic_tank_farm_evidence': has_synthetic_tank_farm,
        'synthetic_stl_pipeline_evidence': has_synthetic_stl,
        'real_cad_cleanup_campaign': False,
        'real_cad_large_layout_campaign': False,
        'real_cad_geometry_count': 0,
        'clears_real_cad_cleanup_blocker': False,
    }


def build_runner_manifest(campaign: str, summary_path: Path, cad_manifest_path: Path | None) -> dict[str, Any]:
    data = read_runner_summary(summary_path)
    cases = []
    seen = set()
    suites = []
    for raw_case in data['cases']:
        case = validate_runner_case(raw_case)
        require(case['name'] not in seen, f'duplicate case name {case["name"]}')
        seen.add(case['name'])
        cases.append(case)
        if case['suite'] not in suites:
            suites.append(case['suite'])
    geometry = geometry_coverage_metadata(cases)
    manifest = {
        'schema_version': 1,
        'status': 'PASS',
        'source_type': 'campaign_run_summary',
        'campaign': campaign,
        'runner_campaign': data['campaign'],
        'suite': data['suite'],
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'case_count': len(cases),
        'suite_count': len(suites),
        'suites': suites,
        'run_summary_path': str(summary_path),
        'run_summary_sha256': sha256_file(summary_path),
        'run_summary_markdown_path': str(summary_path.with_suffix('.md')),
        'run_summary_markdown_sha256': sha256_file(summary_path.with_suffix('.md')),
        'output_root': data['output_root'],
        'host': data.get('host', {}),
        'repo': compact_repo_metadata(data.get('repo', {})),
        'cases': cases,
        **geometry,
        'evidence_tier': data.get('evidence_tier', 'workflow_regression'),
        'campaign_scale': data.get('campaign_scale', 'engineering_regression_smoke'),
        'production_campaign': bool(data.get('production_campaign', False)),
        'production_size_mesh_campaign': bool(data.get('production_size_mesh_campaign', False)),
        'full_duration_campaign': bool(data.get('full_duration_campaign', False)),
        'production_readiness_scope': 'engineering H2 leak full runner evidence packaging and verification',
        'global_limitations': [
            'Manifest proves runner orchestration, required-output presence, SHA-256 integrity, zero return codes, and absence of runner-detected failure markers for listed cases only.',
            'It does not prove production-scale CFD accuracy, production-size meshes, scheduler affinity, overnight stability, fire heat-release validation, real CAD cleanup, or experimental/reference-data agreement.',
        ],
    }
    return apply_real_cad_metadata(manifest, cad_manifest_path)


def build_manifest(
    campaign: str,
    reports: list[Path] | None,
    run_summary: Path | None,
    cad_manifest_path: Path | None,
) -> dict[str, Any]:
    if reports and run_summary:
        raise ManifestError('use either --case-report or --campaign-run-summary, not both')
    if run_summary:
        return build_runner_manifest(campaign, run_summary, cad_manifest_path)
    return build_report_manifest(campaign, reports or [], cad_manifest_path)


def write_case_reports_markdown(manifest: dict[str, Any], lines: list[str]) -> None:
    for case in manifest['cases']:
        lines.extend([
            f"### {case['case_name']}",
            '',
            f"- Report: `{case['case_report_path']}`",
            f"- Report SHA-256: `{case['case_report_sha256']}`",
            f"- Evidence root: `{case['evidence_root']}`",
            f"- MPI ranks / steps / plotfiles: `{case['ranks']}` / `{case['max_step']}` / `{case['plotfiles']}`",
            f"- Final time: `{case['final_time']:.12e}`",
            f"- AMR final cloud volume: `{case['amr_final_cloud_volume']:.8e}`",
            f"- AMR final peak X: `{case['amr_final_peak_X']:.8e}`",
            f"- AMR final flammable planes: `{case['amr_final_flammable_planes']}`",
            f"- Cloud / peak relative difference: `{case['cloud_rel_diff']:.8e}` / `{case['peak_rel_diff']:.8e}`",
            f"- AMR regrid count: `{case['amr_regrid_count']}`",
            f"- Mean cell / advance / final plotfile byte ratios: `{case['mean_ncells_ratio']:.8e}` / `{case['advance_seconds_ratio']:.8e}` / `{case['final_plotfile_bytes_ratio']:.8e}`",
            '',
        ])


def write_runner_summary_markdown(manifest: dict[str, Any], lines: list[str]) -> None:
    lines.extend([
        f"Suite: `{manifest['suite']}`",
        f"Suite count: `{manifest['suite_count']}`",
        f"Run summary: `{manifest['run_summary_path']}`",
        f"Run summary SHA-256: `{manifest['run_summary_sha256']}`",
        f"Run summary Markdown SHA-256: `{manifest['run_summary_markdown_sha256']}`",
        f"Output root: `{manifest['output_root']}`",
        '',
    ])
    for case in manifest['cases']:
        hashes = ', '.join(item['sha256'][:16] for item in case['required_file_hashes'])
        lines.extend([
            f"### {case['name']}",
            '',
            f"- Suite: `{case['suite']}`",
            f"- Script: `{case['script']}`",
            f"- Case log: `{case['case_log']}`",
            f"- Case log SHA-256: `{case['case_log_sha256']}`",
            f"- Duration seconds: `{case['duration_s']:.2f}`",
            f"- Required files: `{len(case['required_files'])}`",
            f"- Required SHA-256 prefixes: `{hashes}`",
            '',
        ])


def write_markdown(manifest: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Engineering Campaign Manifest: {manifest['campaign']}",
        '',
        f"Status: `{manifest['status']}`",
        f"Source type: `{manifest.get('source_type', 'case_reports')}`",
        f"Generated UTC: `{manifest['generated_at_utc']}`",
        f"Case count: `{manifest['case_count']}`",
        f"Evidence tier: `{manifest.get('evidence_tier', '')}`",
        f"Campaign scale: `{manifest.get('campaign_scale', '')}`",
        f"Production campaign: `{manifest.get('production_campaign', False)}`",
        f"Production-size mesh campaign: `{manifest.get('production_size_mesh_campaign', False)}`",
        f"Full-duration campaign: `{manifest.get('full_duration_campaign', False)}`",
        f"Geometry evidence tier: `{manifest.get('geometry_evidence_tier', '')}`",
        f"Synthetic tank-farm evidence: `{manifest.get('synthetic_tank_farm_evidence', False)}`",
        f"Synthetic STL pipeline evidence: `{manifest.get('synthetic_stl_pipeline_evidence', False)}`",
        f"Real CAD cleanup campaign: `{manifest.get('real_cad_cleanup_campaign', False)}`",
        f"Real CAD large-layout campaign: `{manifest.get('real_cad_large_layout_campaign', False)}`",
        f"Real CAD geometry count: `{manifest.get('real_cad_geometry_count', 0)}`",
        f"Clears real-CAD cleanup blocker: `{manifest.get('clears_real_cad_cleanup_blocker', False)}`",
        '',
        '## Cases',
        '',
    ]
    cad = manifest.get('real_cad_cleanup_evidence')
    if isinstance(cad, dict):
        lines.extend([
            '## Real CAD Cleanup Evidence',
            '',
            f"- Evidence manifest: `{cad['path']}`",
            f"- Evidence SHA-256: `{cad['sha256']}`",
            f"- Source type: `{cad['source_type']}`",
            f"- Geometry count: `{cad['geometry_count']}`",
            f"- Large-layout campaign: `{cad['large_layout_campaign']}`",
            '',
        ])
    if manifest.get('source_type') == 'campaign_run_summary':
        write_runner_summary_markdown(manifest, lines)
    else:
        write_case_reports_markdown(manifest, lines)
    lines.extend(['## Global Limitations', ''])
    for item in manifest['global_limitations']:
        lines.append(f'- {item}')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', required=True, help='Campaign name')
    parser.add_argument('--case-report', action='append', type=Path, help='Case report JSON path; repeatable')
    parser.add_argument('--campaign-run-summary', type=Path, help='Campaign runner summary JSON path')
    parser.add_argument('--real-cad-cleanup-manifest', type=Path, help='Optional real CAD cleanup evidence manifest JSON')
    parser.add_argument('--output-json', required=True, type=Path, help='Output campaign manifest JSON')
    parser.add_argument('--output-md', required=True, type=Path, help='Output campaign manifest Markdown')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = build_manifest(
            args.campaign,
            args.case_report,
            args.campaign_run_summary,
            args.real_cad_cleanup_manifest,
        )
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(manifest, args.output_md)
    except ManifestError as exc:
        raise SystemExit(f'engineering_campaign_manifest FAIL {exc}') from exc
    print(
        'engineering_campaign_manifest PASS '
        f'campaign={args.campaign} cases={manifest["case_count"]} json={args.output_json} md={args.output_md}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
