#!/usr/bin/env python3
"""Write/verify H2 engineering reference-threshold agreement evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = 'PASS-REFERENCE-THRESHOLD-AGREEMENT'
EXTERNAL_PLUME_SOURCE_TYPES = {'field_test', 'wind_tunnel', 'literature_digitized'}
EXTERNAL_PLUME_METRIC_TYPES = {
    'plume_extent',
    'sensor_concentration',
    'arrival_time',
    'concentration_peak',
    'flammable_cloud_volume',
}
EXTERNAL_PLUME_SHAPE_METRIC_TYPES = {'plume_extent', 'sensor_concentration', 'arrival_time'}
MAX_EXTERNAL_TOLERANCE_REL = 0.50
RESERVED_SOURCE_HOST_MARKERS = {
    'example.com',
    'example.invalid',
    'example.org',
    'localhost',
    '127.0.0.1',
}
SYNTHETIC_SOURCE_MARKERS = ('synthetic', 'selftest', 'copied from', 'not production')

DEFAULT_SCOUT_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/'
    'hybrid_largegrid_8rank_120step_scout_report.json'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/'
    'h2_reference_agreement_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/'
    'h2_reference_agreement_report.md'
)
DEFAULT_PLUME_OBSERVATION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_plume_observation_20260723/'
    'h2_plume_observation_report.json'
)

H2_LEL = 0.04
H2_UEL = 0.75
ALOHA_RED_LOC = 0.60 * H2_LEL
ALOHA_YELLOW_LOC = 0.10 * H2_LEL

REFERENCE_SOURCES = [
    {
        'label': 'NOAA CAMEO Chemicals HYDROGEN datasheet',
        'url': 'https://cameochemicals.noaa.gov/chemical/8729',
        'used_for': 'H2 Lower Explosive Limit 4% and Upper Explosive Limit 75% by volume.',
        'retrieved_utc': '2026-07-21',
    },
    {
        'label': 'NOAA ORR Flammable Levels of Concern',
        'url': 'https://response.restoration.noaa.gov/oil-and-chemical-spills/chemical-spills/resources/flammable-levels-concern.html',
        'used_for': 'ALOHA default flammable LOCs: 60% LEL red zone and 10% LEL yellow zone.',
        'retrieved_utc': '2026-07-21',
    },
    {
        'label': 'NIST glossary: Flammable Limit',
        'url': 'https://www.nist.gov/glossary-term/24026',
        'used_for': 'Flammable limits are expressed as fuel volume percent in air.',
        'retrieved_utc': '2026-07-21',
    },
]


class ReportError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ReportError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON in {path}: {exc}') from exc
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


def scout_file(report: dict[str, Any], suffix: str) -> Path:
    files = report.get('files')
    require(isinstance(files, list), 'scout report files list missing')
    matches: list[Path] = []
    for item in files:
        if isinstance(item, dict) and str(item.get('path', '')).endswith(suffix):
            matches.append(Path(str(item['path'])))
    require(len(matches) == 1, f'expected one scout file ending with {suffix!r}, got {len(matches)}')
    return matches[0]


def pass_kv(path: Path, prefix: str) -> dict[str, Any]:
    text = path.read_text(encoding='utf-8', errors='replace')
    line = next((raw.strip() for raw in text.splitlines() if raw.startswith(prefix)), '')
    require(bool(line), f'missing PASS line in {path}')
    out: dict[str, Any] = {'pass_line': line}
    for key, raw in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)=([^ ]+)', line):
        try:
            out[key] = float(raw)
        except ValueError:
            out[key] = raw
    return out


def final_csv_row(path: Path) -> dict[str, Any]:
    with path.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    require(bool(rows), f'empty CSV: {path}')
    out: dict[str, Any] = {}
    for key, value in rows[-1].items():
        try:
            out[key] = float(value)
        except (TypeError, ValueError):
            out[key] = value
    return out


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def sanitize_key(value: Any) -> str:
    text = re.sub(r'[^A-Za-z0-9]+', '_', str(value).strip())
    text = re.sub(r'_+', '_', text).strip('_').lower()
    return text or 'unnamed'


def optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return load_json(path)


def approx(value: Any, expected: float, tol: float = 1.0e-12) -> bool:
    return finite(value) and abs(float(value) - expected) <= tol


def rel_error(value: float, reference: float) -> float:
    denom = max(abs(reference), 1.0e-300)
    return abs(value - reference) / denom


def add_plume_observation_metrics(
    report: dict[str, Any] | None,
    comparison_summary: dict[str, Any],
) -> dict[str, Any] | None:
    if report is None:
        return None
    require(report.get('schema_version') == 1, 'plume observation schema_version must be 1')
    require(report.get('status') == 'PASS-H2-PLUME-OBSERVATION', 'plume observation report did not PASS')
    summary = report.get('summary') if isinstance(report.get('summary'), dict) else {}
    outputs = report.get('outputs') if isinstance(report.get('outputs'), dict) else {}
    for key, value in summary.items():
        if finite(value):
            comparison_summary[f'observation_{key}'] = float(value)
    extents_path = Path(str(outputs.get('plume_extents_csv', '')))
    sensors_path = Path(str(outputs.get('sensor_timeseries_csv', '')))
    require(extents_path.is_file(), f'missing plume extents CSV: {extents_path}')
    require(sensors_path.is_file(), f'missing sensor timeseries CSV: {sensors_path}')
    extent_rows = read_csv_rows(extents_path)
    sensor_rows = read_csv_rows(sensors_path)
    require(bool(extent_rows), 'plume extents CSV is empty')
    require(bool(sensor_rows), 'sensor timeseries CSV is empty')
    max_flammable_x_extent = max(
        (float(row['flammable_x_extent']) for row in extent_rows if finite(row.get('flammable_x_extent'))),
        default=0.0,
    )
    max_flammable_z_extent = max(
        (float(row['flammable_z_extent']) for row in extent_rows if finite(row.get('flammable_z_extent'))),
        default=0.0,
    )
    comparison_summary['observation_max_flammable_x_extent'] = max_flammable_x_extent
    comparison_summary['observation_max_flammable_z_extent'] = max_flammable_z_extent
    by_sensor: dict[str, list[dict[str, str]]] = {}
    for row in sensor_rows:
        sensor_id = str(row.get('sensor_id', ''))
        require(bool(sensor_id), 'sensor row missing sensor_id')
        require(finite(row.get('time')), f'sensor row has non-finite time for {sensor_id}')
        require(finite(row.get('X(H2)')), f'sensor row has non-finite X(H2) for {sensor_id}')
        by_sensor.setdefault(sensor_id, []).append(row)
    for sensor_id, rows in by_sensor.items():
        rows.sort(key=lambda row: float(row['time']))
        key = sanitize_key(sensor_id)
        values = [float(row['X(H2)']) for row in rows]
        times = [float(row['time']) for row in rows]
        peak_idx = int(max(range(len(values)), key=lambda idx: values[idx]))
        arrival = next((time for time, value in zip(times, values) if value >= H2_LEL), None)
        comparison_summary[f'observation_sensor_{key}_peak_X'] = float(values[peak_idx])
        comparison_summary[f'observation_sensor_{key}_peak_time'] = float(times[peak_idx])
        comparison_summary[f'observation_sensor_{key}_final_X'] = float(values[-1])
        if arrival is not None:
            comparison_summary[f'observation_sensor_{key}_arrival_time_lfl'] = float(arrival)
    return {
        'path': report.get('outputs'),
        'sensor_count': len(by_sensor),
        'observation_metric_keys': sorted(k for k in comparison_summary if k.startswith('observation_')),
    }


def metric_key_matches_type(metric_type: str, key: str) -> bool:
    if metric_type == 'plume_extent':
        return key.startswith('observation_max_flammable_') or key in {
            'observation_max_cloud_volume',
            'observation_max_flammable_x',
            'observation_max_flammable_z',
        }
    if metric_type in {'sensor_concentration', 'concentration_peak'}:
        return key.startswith('observation_sensor_') and (
            key.endswith('_peak_X') or key.endswith('_final_X')
        )
    if metric_type == 'arrival_time':
        return key.startswith('observation_sensor_') and key.endswith('_arrival_time_lfl')
    if metric_type == 'flammable_cloud_volume':
        return key in {'amr_lel_cloud_volume', 'baseline_lel_cloud_volume', 'observation_max_cloud_volume'}
    return False


def source_url_host(url: str) -> str:
    match = re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]+)', str(url).strip())
    return match.group(1).split('@')[-1].split(':')[0].lower() if match else ''


def validate_external_source_quality(dataset: dict[str, Any], allow_synthetic_selftest: bool) -> None:
    source = dataset.get('source') if isinstance(dataset.get('source'), dict) else {}
    title = str(source.get('title', ''))
    url = str(source.get('url', ''))
    doi = str(source.get('doi', ''))
    combined = ' '.join([title, url, doi, str(dataset.get('dataset_name', ''))]).lower()
    if allow_synthetic_selftest:
        return
    require(
        not any(marker in combined for marker in SYNTHETIC_SOURCE_MARKERS),
        'external plume source appears to be synthetic/selftest evidence',
    )
    host = source_url_host(url)
    require(
        not host or host not in RESERVED_SOURCE_HOST_MARKERS,
        f'external plume source uses reserved/non-production host: {host}',
    )
    require(
        bool(doi) or (host and '.' in host),
        'external plume source must include a real DOI or resolvable-looking public URL host',
    )
    if dataset.get('source_type') == 'literature_digitized':
        digitization = dataset.get('digitization')
        require(isinstance(digitization, dict), 'literature_digitized dataset must include digitization metadata')
        require(bool(digitization.get('source_figure') or digitization.get('source_table')), 'digitization source figure/table missing')
        require(bool(digitization.get('method')), 'digitization method missing')
        require(bool(digitization.get('operator') or digitization.get('tool')), 'digitization operator/tool missing')


def validate_selftest_output_scope(args: argparse.Namespace) -> None:
    if not args.allow_synthetic_selftest:
        return
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    require(out_json != DEFAULT_OUTPUT_JSON, '--allow-synthetic-selftest cannot write the official reference JSON')
    require(out_md != DEFAULT_OUTPUT_MD, '--allow-synthetic-selftest cannot write the official reference Markdown')
    combined = f'{out_json.as_posix()} {out_md.as_posix()}'.lower()
    require(
        'selftest' in combined,
        '--allow-synthetic-selftest outputs must be isolated under a selftest path',
    )


def evaluate_case(label: str, hazard: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    require(approx(hazard.get('lfl'), H2_LEL), f'{label} LFL does not match H2 LEL')
    require(approx(hazard.get('ufl'), H2_UEL), f'{label} UFL does not match H2 UEL')
    require(hazard.get('status') == 'flammable_cloud_detected', f'{label} flammable cloud not detected')

    peak_x = float(hazard.get('max_X', float('nan')))
    cloud_volume = float(hazard.get('cloud_volume', float('nan')))
    cloud_mass = float(hazard.get('cloud_species_mass', float('nan')))
    total_mass = float(hazard.get('total_species_mass', float('nan')))
    final_peak_x = float(row.get('peak_X', float('nan')))
    flammable_planes = int(float(row.get('flammable_planes', 0)))

    require(math.isfinite(peak_x) and peak_x >= H2_LEL, f'{label} peak below LEL')
    require(peak_x >= ALOHA_RED_LOC, f'{label} peak below ALOHA red LOC')
    require(peak_x >= ALOHA_YELLOW_LOC, f'{label} peak below ALOHA yellow LOC')
    require(peak_x < H2_UEL, f'{label} peak exceeds UEL; rich-region handling needs separate evidence')
    require(math.isfinite(cloud_volume) and cloud_volume > 0.0, f'{label} nonpositive LEL cloud volume')
    require(math.isfinite(cloud_mass) and cloud_mass > 0.0, f'{label} nonpositive LEL cloud H2 mass')
    require(math.isfinite(total_mass) and total_mass > 0.0, f'{label} nonpositive total H2 mass')
    require(cloud_mass <= 1.01 * total_mass, f'{label} cloud H2 mass exceeds total H2 mass')
    require(math.isfinite(final_peak_x) and final_peak_x >= H2_LEL, f'{label} final timeseries peak below LEL')
    require(flammable_planes > 0, f'{label} final flammable plane count is zero')

    return {
        'lfl_matches_reference': True,
        'ufl_matches_reference': True,
        'peak_x': peak_x,
        'peak_above_aloha_yellow_loc': peak_x >= ALOHA_YELLOW_LOC,
        'peak_above_aloha_red_loc': peak_x >= ALOHA_RED_LOC,
        'peak_above_lel': peak_x >= H2_LEL,
        'peak_below_uel': peak_x < H2_UEL,
        'lel_cloud_volume': cloud_volume,
        'lel_cloud_species_mass': cloud_mass,
        'total_species_mass': total_mass,
        'final_peak_x': final_peak_x,
        'final_flammable_planes': flammable_planes,
        'final_active_planes': int(float(row.get('active_planes', 0))),
    }


def evaluate_external_plume_dataset(
    dataset_path: Path,
    scout: dict[str, Any],
    summary: dict[str, Any],
    allow_synthetic_selftest: bool = False,
) -> dict[str, Any]:
    dataset = load_json(dataset_path)
    require(dataset.get('schema_version') == 1, 'external plume dataset schema_version must be 1')
    require(
        dataset.get('dataset_type') == 'external_h2_plume_shape_agreement',
        'external plume dataset_type must be external_h2_plume_shape_agreement',
    )
    require(str(dataset.get('case')) == str(scout.get('case')), 'external plume dataset case does not match scout report case')
    source = dataset.get('source')
    require(isinstance(source, dict), 'external plume dataset source must be an object')
    require(bool(source.get('title')), 'external plume source title missing')
    require(bool(source.get('url') or source.get('doi')), 'external plume source must include url or doi')
    source_type = str(dataset.get('source_type', ''))
    require(
        source_type in EXTERNAL_PLUME_SOURCE_TYPES,
        f'invalid external plume source_type: {source_type}',
    )
    validate_external_source_quality(dataset, allow_synthetic_selftest)
    alignment = dataset.get('case_alignment')
    require(isinstance(alignment, dict), 'external plume dataset case_alignment must be an object')
    for key in ('geometry', 'release_rate', 'release_direction', 'boundary_conditions'):
        require(alignment.get(key) is True, f'external plume case_alignment.{key} must be true')

    metrics = dataset.get('metrics')
    require(isinstance(metrics, list) and len(metrics) >= 2, 'external plume dataset must contain at least two metrics')
    checks: list[dict[str, Any]] = []
    metric_types: set[str] = set()
    for idx, metric in enumerate(metrics):
        require(isinstance(metric, dict), f'external metric {idx} is not an object')
        key = str(metric.get('simulation_summary_key', ''))
        require(bool(key), f'external metric {idx} missing simulation_summary_key')
        require(key in summary, f'external metric {idx} key not present in scout summary: {key}')
        require(finite(summary.get(key)), f'external metric {idx} simulation value is not finite: {key}')
        require(finite(metric.get('reference_value')), f'external metric {idx} reference_value is not finite')
        require(bool(metric.get('reference_basis')), f'external metric {idx} missing reference_basis')
        metric_type = str(metric.get('metric_type', ''))
        require(metric_type in EXTERNAL_PLUME_METRIC_TYPES, f'external metric {idx} invalid metric_type: {metric_type}')
        require(
            metric_key_matches_type(metric_type, key),
            f'external metric {idx} key {key!r} is not compatible with metric_type {metric_type!r}',
        )
        metric_types.add(metric_type)
        sim = float(summary[key])
        ref = float(metric['reference_value'])
        tol_rel = metric.get('tolerance_rel')
        tol_abs = metric.get('tolerance_abs')
        require(finite(tol_rel) or finite(tol_abs), f'external metric {idx} needs tolerance_rel or tolerance_abs')
        if finite(tol_rel):
            require(
                0.0 < float(tol_rel) <= MAX_EXTERNAL_TOLERANCE_REL,
                f'external metric {idx} tolerance_rel must be in (0, {MAX_EXTERNAL_TOLERANCE_REL}]',
            )
        if finite(tol_abs):
            require(float(tol_abs) > 0.0, f'external metric {idx} tolerance_abs must be positive')
        abs_err = abs(sim - ref)
        rel_err = rel_error(sim, ref)
        passed = True
        if finite(tol_rel):
            passed = passed and rel_err <= float(tol_rel)
        if finite(tol_abs):
            passed = passed and abs_err <= float(tol_abs)
        checks.append({
            'name': metric.get('name', key),
            'metric_type': metric_type,
            'simulation_summary_key': key,
            'quantity': metric.get('quantity'),
            'units': metric.get('units'),
            'simulation_value': sim,
            'reference_value': ref,
            'reference_basis': metric.get('reference_basis'),
            'abs_error': abs_err,
            'rel_error': rel_err,
            'tolerance_rel': float(tol_rel) if finite(tol_rel) else None,
            'tolerance_abs': float(tol_abs) if finite(tol_abs) else None,
            'passed': passed,
        })
    require(all(item['passed'] for item in checks), 'one or more external plume metrics failed tolerance')
    require(
        bool(metric_types & EXTERNAL_PLUME_SHAPE_METRIC_TYPES),
        'external plume dataset must include at least one plume-shape metric type',
    )
    return {
        'dataset_path': str(dataset_path),
        'dataset_name': dataset.get('dataset_name'),
        'source_type': source_type,
        'source': source,
        'digitization': dataset.get('digitization'),
        'case_alignment': alignment,
        'case': dataset.get('case'),
        'comparison_basis': dataset.get('comparison_basis', 'summary_metrics'),
        'metric_count': len(checks),
        'metric_types': sorted(metric_types),
        'checks': checks,
        'all_metrics_passed': True,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    scout_path = Path(args.scout_report)
    scout = load_json(scout_path)
    require(scout.get('status') == 'PASS-HYBRID-CFD-SCOUT', 'scout report did not PASS')
    summary = scout.get('summary', {}) if isinstance(scout.get('summary'), dict) else {}
    require(int(summary.get('ranks', 0)) >= args.min_ranks, 'scout ranks too small')
    require(int(summary.get('threads_per_rank', 0)) >= args.min_threads, 'scout threads too small')
    require(int(summary.get('base_cell_count', 0)) >= args.min_base_cells, 'base grid too small')
    require(finite(summary.get('cloud_rel_diff')) and float(summary['cloud_rel_diff']) <= args.max_cloud_rel_diff, 'cloud_rel_diff too high')
    require(finite(summary.get('peak_rel_diff')) and float(summary['peak_rel_diff']) <= args.max_peak_rel_diff, 'peak_rel_diff too high')

    paths = {
        'baseline_hazard_summary': scout_file(scout, 'files/baseline/hazard_summary.log'),
        'amr_hazard_summary': scout_file(scout, 'files/amr/hazard_summary.log'),
        'baseline_hazard_timeseries': scout_file(scout, 'files/baseline/hazard_timeseries.csv'),
        'amr_hazard_timeseries': scout_file(scout, 'files/amr/hazard_timeseries.csv'),
        'plan_amr_compare_summary': scout_file(scout, 'files/plan_amr_compare_summary.csv'),
    }
    baseline = evaluate_case(
        'baseline',
        pass_kv(paths['baseline_hazard_summary'], 'h2_leak_hazard_summary PASS'),
        final_csv_row(paths['baseline_hazard_timeseries']),
    )
    amr = evaluate_case(
        'amr',
        pass_kv(paths['amr_hazard_summary'], 'h2_leak_hazard_summary PASS'),
        final_csv_row(paths['amr_hazard_timeseries']),
    )
    comparison_summary = dict(summary)
    comparison_summary.update({
        'baseline_peak_x': baseline['peak_x'],
        'amr_peak_x': amr['peak_x'],
        'baseline_lel_cloud_volume': baseline['lel_cloud_volume'],
        'amr_lel_cloud_volume': amr['lel_cloud_volume'],
        'baseline_final_flammable_planes': baseline['final_flammable_planes'],
        'amr_final_flammable_planes': amr['final_flammable_planes'],
    })
    plume_observation_path = Path(args.plume_observation_report)
    plume_observation = optional_json(plume_observation_path)
    plume_observation_summary = add_plume_observation_metrics(plume_observation, comparison_summary)
    external_plume = None
    if args.external_plume_dataset_json:
        external_plume = evaluate_external_plume_dataset(
            Path(args.external_plume_dataset_json), scout, comparison_summary, args.allow_synthetic_selftest)

    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': STATUS,
        'title': 'Engineering H2 Reference Threshold Agreement',
        'scout_report': str(scout_path),
        'plume_observation_report': str(plume_observation_path) if plume_observation else None,
        'agreement_tier': (
            'external_plume_shape_dataset_agreement'
            if external_plume else 'reference_threshold_agreement'
        ),
        'threshold_reference_agreement': True,
        'external_plume_shape_dataset_agreement': external_plume is not None,
        'external_consequence_dataset_agreement': False,
        'field_or_wind_tunnel_dataset_agreement': (
            external_plume is not None and
            external_plume.get('source_type') in {'field_test', 'wind_tunnel', 'literature_digitized'}
        ),
        'clears_reference_data_blocker': external_plume is not None,
        'reference_thresholds': {
            'h2_lel_volume_fraction': H2_LEL,
            'h2_uel_volume_fraction': H2_UEL,
            'aloha_red_loc_volume_fraction': ALOHA_RED_LOC,
            'aloha_yellow_loc_volume_fraction': ALOHA_YELLOW_LOC,
        },
        'reference_sources': REFERENCE_SOURCES,
        'summary': {
            'ranks': summary.get('ranks'),
            'threads_per_rank': summary.get('threads_per_rank'),
            'max_step': summary.get('max_step'),
            'base_cell_count': summary.get('base_cell_count'),
            'amr_equivalent_fine_cell_count': summary.get('amr_equivalent_fine_cell_count'),
            'cloud_rel_diff': summary.get('cloud_rel_diff'),
            'peak_rel_diff': summary.get('peak_rel_diff'),
            'baseline_peak_x': baseline['peak_x'],
            'amr_peak_x': amr['peak_x'],
            'baseline_lel_cloud_volume': baseline['lel_cloud_volume'],
            'amr_lel_cloud_volume': amr['lel_cloud_volume'],
            'amr_final_flammable_planes': amr['final_flammable_planes'],
            'plume_observation_metric_count': (
                len(plume_observation_summary['observation_metric_keys'])
                if plume_observation_summary else 0
            ),
            'all_threshold_checks_passed': True,
            'external_plume_metric_count': (
                external_plume.get('metric_count') if external_plume else 0
            ),
            'external_plume_all_metrics_passed': (
                external_plume.get('all_metrics_passed') if external_plume else False
            ),
        },
        'case_checks': {'baseline': baseline, 'amr': amr},
        'plume_observation_summary': plume_observation_summary,
        'external_plume_shape_comparison': external_plume,
        'criteria': {
            'min_ranks': args.min_ranks,
            'min_threads': args.min_threads,
            'min_base_cells': args.min_base_cells,
            'max_cloud_rel_diff': args.max_cloud_rel_diff,
            'max_peak_rel_diff': args.max_peak_rel_diff,
        },
        'evidence_files': [evidence_entry('scout_report', scout_path)] + [
            evidence_entry(label, path) for label, path in paths.items()
        ] + (
            [evidence_entry('plume_observation_report', plume_observation_path)]
            if plume_observation else []
        ) + (
            [evidence_entry('external_plume_dataset', Path(args.external_plume_dataset_json))]
            if args.external_plume_dataset_json else []
        ),
        'limitations': [
            (
                'This report includes external plume-shape metric agreement.'
                if external_plume else
                'This is an engineering threshold-agreement report, not external field-test or wind-tunnel plume validation.'
            ),
            'It verifies H2 LEL/UEL thresholds, ALOHA-style LOC interpretation, positive flammable-cloud metrics, and AMR-vs-baseline drift on maintained large-grid evidence.',
            (
                'It clears the reference-data blocker only for the external plume-shape metrics declared in the dataset; external consequence calibration remains separate.'
                if external_plume else
                'It does not clear the reference-data blocker by itself; experimental/literature plume-shape and consequence comparisons remain required.'
            ),
        ],
    }
    validate_report_object(report, check_hashes=False)
    return report


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') == STATUS, f'invalid status {data.get("status")}')
    require(data.get('threshold_reference_agreement') in {None, True}, 'threshold_reference_agreement must be true when present')
    external_ok = data.get('external_plume_shape_dataset_agreement') is True
    require(data.get('external_plume_shape_dataset_agreement') in {None, False, True}, 'invalid external plume flag')
    require(data.get('external_consequence_dataset_agreement') in {None, False}, 'external consequence agreement is not supported by this report')
    require(data.get('field_or_wind_tunnel_dataset_agreement') in {None, False, True}, 'invalid field/wind-tunnel flag')
    require(data.get('clears_reference_data_blocker') in {None, False, True}, 'invalid clears_reference_data_blocker flag')
    if data.get('clears_reference_data_blocker') is True:
        require(external_ok, 'clears_reference_data_blocker requires external plume agreement')
    thresholds = data.get('reference_thresholds', {}) if isinstance(data.get('reference_thresholds'), dict) else {}
    require(approx(thresholds.get('h2_lel_volume_fraction'), H2_LEL), 'LEL threshold mismatch')
    require(approx(thresholds.get('h2_uel_volume_fraction'), H2_UEL), 'UEL threshold mismatch')
    require(approx(thresholds.get('aloha_red_loc_volume_fraction'), ALOHA_RED_LOC), 'red LOC mismatch')
    require(approx(thresholds.get('aloha_yellow_loc_volume_fraction'), ALOHA_YELLOW_LOC), 'yellow LOC mismatch')
    summary = data.get('summary', {}) if isinstance(data.get('summary'), dict) else {}
    require(summary.get('all_threshold_checks_passed') is True, 'threshold checks did not pass')
    require(finite(summary.get('cloud_rel_diff')) and float(summary['cloud_rel_diff']) <= 0.05, 'cloud_rel_diff too high')
    require(finite(summary.get('peak_rel_diff')) and float(summary['peak_rel_diff']) <= 0.05, 'peak_rel_diff too high')
    if external_ok:
        require(summary.get('external_plume_all_metrics_passed') is True, 'external plume metrics did not pass')
        require(int(summary.get('external_plume_metric_count', 0)) >= 2, 'external plume metric count too small')
        comparison = data.get('external_plume_shape_comparison')
        require(isinstance(comparison, dict), 'external plume comparison missing')
        require(comparison.get('all_metrics_passed') is True, 'external plume comparison not passed')
        checks_ext = comparison.get('checks')
        require(isinstance(checks_ext, list) and len(checks_ext) >= 2, 'external plume checks missing')
        require(
            comparison.get('source_type') in EXTERNAL_PLUME_SOURCE_TYPES,
            'external plume source type is not experimental or literature-digitized',
        )
        alignment = comparison.get('case_alignment')
        require(isinstance(alignment, dict), 'external plume case alignment missing')
        for key in ('geometry', 'release_rate', 'release_direction', 'boundary_conditions'):
            require(alignment.get(key) is True, f'external plume case alignment missing {key}')
        metric_types = comparison.get('metric_types')
        require(isinstance(metric_types, list), 'external plume metric_types missing')
        require(
            bool(set(str(item) for item in metric_types) & EXTERNAL_PLUME_SHAPE_METRIC_TYPES),
            'external plume shape metric type missing',
        )
        for item in checks_ext:
            require(isinstance(item, dict), 'external plume check is not an object')
            require(item.get('passed') is True, 'external plume check did not pass')
            require(item.get('metric_type') in EXTERNAL_PLUME_METRIC_TYPES, 'external plume check metric_type invalid')
            require(finite(item.get('simulation_value')), 'external plume simulation value not finite')
            require(finite(item.get('reference_value')), 'external plume reference value not finite')
            require(bool(item.get('reference_basis')), 'external plume reference basis missing')
            require(finite(item.get('abs_error')), 'external plume abs_error not finite')
            require(finite(item.get('rel_error')), 'external plume rel_error not finite')
            require(
                metric_key_matches_type(str(item.get('metric_type')), str(item.get('simulation_summary_key'))),
                'external plume check key is incompatible with metric type',
            )
    else:
        require(summary.get('external_plume_all_metrics_passed') in {None, False}, 'external plume pass flag set without agreement')
    checks = data.get('case_checks', {}) if isinstance(data.get('case_checks'), dict) else {}
    for label in ('baseline', 'amr'):
        item = checks.get(label, {}) if isinstance(checks.get(label), dict) else {}
        for key in ('lfl_matches_reference', 'ufl_matches_reference', 'peak_above_aloha_red_loc', 'peak_above_lel', 'peak_below_uel'):
            require(item.get(key) is True, f'{label} missing {key}')
        require(finite(item.get('lel_cloud_volume')) and float(item['lel_cloud_volume']) > 0.0, f'{label} invalid cloud volume')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = ['# Engineering H2 Reference Threshold Agreement', '', f"Status: `{report['status']}`", '']
    lines += [
        f"Agreement tier: `{report.get('agreement_tier', '')}`",
        f"Threshold reference agreement: `{report.get('threshold_reference_agreement', False)}`",
        f"External plume-shape dataset agreement: `{report.get('external_plume_shape_dataset_agreement', False)}`",
        f"External consequence dataset agreement: `{report.get('external_consequence_dataset_agreement', False)}`",
        f"Field/wind-tunnel dataset agreement: `{report.get('field_or_wind_tunnel_dataset_agreement', False)}`",
        f"Clears reference-data blocker: `{report.get('clears_reference_data_blocker', False)}`",
        '',
    ]
    lines += ['## Summary', '']
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += ['', '## Reference Sources', '']
    for source in report['reference_sources']:
        lines.append(f"- {source['label']}: {source['url']} ({source['used_for']})")
    comparison = report.get('external_plume_shape_comparison')
    if isinstance(comparison, dict):
        lines += ['', '## External Plume Shape Comparison', '']
        lines.append(f"- Dataset: `{comparison.get('dataset_name')}`")
        lines.append(f"- Source type: `{comparison.get('source_type')}`")
        source = comparison.get('source', {}) if isinstance(comparison.get('source'), dict) else {}
        lines.append(f"- Source: `{source.get('title')}`")
        lines += ['', '| Metric | Simulation | Reference | Rel. error | Passed |', '| --- | ---: | ---: | ---: | --- |']
        for item in comparison.get('checks', []):
            lines.append(
                f"| `{item.get('name')}` | `{item.get('simulation_value')}` | "
                f"`{item.get('reference_value')}` | `{item.get('rel_error')}` | `{item.get('passed')}` |"
            )
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scout-report', default=str(DEFAULT_SCOUT_REPORT))
    ap.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument('--plume-observation-report', default=str(DEFAULT_PLUME_OBSERVATION_REPORT))
    ap.add_argument('--verify-json')
    ap.add_argument('--min-ranks', type=int, default=8)
    ap.add_argument('--min-threads', type=int, default=2)
    ap.add_argument('--min-base-cells', type=int, default=200000)
    ap.add_argument('--max-cloud-rel-diff', type=float, default=0.05)
    ap.add_argument('--max-peak-rel-diff', type=float, default=0.05)
    ap.add_argument(
        '--external-plume-dataset-json',
        help='Optional external plume-shape dataset with case-matched summary-metric tolerances.',
    )
    ap.add_argument(
        '--allow-synthetic-selftest',
        action='store_true',
        help='Allow reserved/synthetic external source metadata only for non-official selftests.',
    )
    args = ap.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(
                'engineering_h2_reference_agreement_report VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"peak={float(data['summary']['amr_peak_x']):.8e} "
                f"cloud_rel={float(data['summary']['cloud_rel_diff']):.8e}"
            )
            return 0
        validate_selftest_output_scope(args)
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_reference_agreement_report PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"peak={float(report['summary']['amr_peak_x']):.8e} "
            f"cloud_rel={float(report['summary']['cloud_rel_diff']):.8e}"
        )
        return 0
    except ReportError as exc:
        print(f'engineering_h2_reference_agreement_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
