#!/usr/bin/env python3
"""Write and verify H2 fire/radiation/overpressure consequence metrics.

This report intentionally produces engineering screening metrics from already
validated H2 leak and ignition evidence by default. A stricter optional
calibration dataset gate can upgrade the report only when external radiation
and overpressure reference comparisons are supplied and pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
H2_LHV_J_PER_KG = 120.0e6
TNT_J_PER_KG = 4.184e6
DEFAULT_DISTANCES_M = (1.0, 3.0, 5.0, 10.0, 20.0)

DEFAULT_IGNITION_REPORT = Path(
    'docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json'
)
DEFAULT_HAZARD_SUMMARY = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/files/amr/hazard_summary.log'
)
DEFAULT_HAZARD_TIMESERIES = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/files/amr/hazard_timeseries.log'
)
DEFAULT_HAZARD_PLANES = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/files/amr/hazard_planes.log'
)
CALIBRATION_DATASET_TYPE = 'h2_fire_consequence_calibration_agreement'
EXPERIMENTAL_SOURCE_TYPES = {'field_test', 'wind_tunnel', 'literature_digitized'}
ALLOWED_SOURCE_TYPES = EXPERIMENTAL_SOURCE_TYPES | {'validated_reference_model'}


class ConsequenceError(RuntimeError):
    pass


def distance_summary_token(distance_m: float) -> str:
    text = f'{float(distance_m):g}'.replace('.', 'p').replace('-', 'm')
    return f'{text}m'


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ConsequenceError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ConsequenceError(f'invalid JSON evidence {path}: {exc}') from exc
    if not isinstance(data, dict):
        raise ConsequenceError(f'JSON evidence is not an object: {path}')
    return data


def parse_key_value_log(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text()
    except FileNotFoundError as exc:
        raise ConsequenceError(f'missing log evidence: {path}') from exc
    first = text.splitlines()[0] if text.splitlines() else ''
    if ' PASS ' not in f' {first} ':
        raise ConsequenceError(f'log does not contain PASS status: {path}')
    out: dict[str, Any] = {'_raw_first_line': first}
    for key, value in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)', first):
        if value in {'PASS', 'FAIL'}:
            out[key] = value
            continue
        try:
            out[key] = float(value)
        except ValueError:
            out[key] = value
    return out


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def positive_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not finite(value) or float(value) <= 0.0:
        raise ConsequenceError(f'missing or nonpositive {key}')
    return float(value)


def overpressure_screening_kpa(scaled_distance: float) -> float:
    # Smooth TNT-equivalent screening curve; monotonic and intentionally conservative
    # enough for evidence triage, not for design or siting decisions.
    z = max(float(scaled_distance), 1.0e-9)
    return 1772.0 / (z**3 + 6.0 * z**2 + 15.0 * z + 1.0)


def compare_metric(metric: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    name = metric.get('name')
    family = metric.get('family')
    summary_key = metric.get('simulation_summary_key')
    if not isinstance(name, str) or not name:
        raise ConsequenceError('calibration metric is missing name')
    if family not in {'radiation', 'overpressure'}:
        raise ConsequenceError(f'unsupported calibration metric family for {name}: {family}')
    if not isinstance(summary_key, str) or summary_key not in summary:
        raise ConsequenceError(f'calibration metric {name} references unknown summary key: {summary_key}')
    simulation_value = summary.get(summary_key)
    reference_value = metric.get('reference_value')
    if not finite(simulation_value) or not finite(reference_value):
        raise ConsequenceError(f'calibration metric {name} has non-finite simulation/reference value')
    simulation_value = float(simulation_value)
    reference_value = float(reference_value)
    abs_error = abs(simulation_value - reference_value)
    rel_error = abs_error / max(abs(reference_value), 1.0e-300)
    tolerance_abs = metric.get('tolerance_abs')
    tolerance_rel = metric.get('tolerance_rel')
    if tolerance_abs is None and tolerance_rel is None:
        raise ConsequenceError(f'calibration metric {name} must define tolerance_abs or tolerance_rel')
    if tolerance_abs is not None and (not finite(tolerance_abs) or float(tolerance_abs) <= 0.0):
        raise ConsequenceError(f'calibration metric {name} has invalid tolerance_abs')
    if tolerance_rel is not None and (not finite(tolerance_rel) or float(tolerance_rel) <= 0.0):
        raise ConsequenceError(f'calibration metric {name} has invalid tolerance_rel')
    abs_pass = finite(tolerance_abs) and abs_error <= float(tolerance_abs)
    rel_pass = finite(tolerance_rel) and rel_error <= float(tolerance_rel)
    passed = bool(abs_pass or rel_pass)
    return {
        'name': name,
        'family': family,
        'units': metric.get('units'),
        'simulation_summary_key': summary_key,
        'simulation_value': simulation_value,
        'reference_value': reference_value,
        'abs_error': abs_error,
        'rel_error': rel_error,
        'tolerance_abs': tolerance_abs,
        'tolerance_rel': tolerance_rel,
        'passed': passed,
    }


def evaluate_calibration_dataset(path: Path, case: str, summary: dict[str, Any]) -> dict[str, Any]:
    dataset = load_json(path)
    if dataset.get('schema_version') != 1:
        raise ConsequenceError('calibration dataset schema_version must be 1')
    if dataset.get('dataset_type') != CALIBRATION_DATASET_TYPE:
        raise ConsequenceError(f'calibration dataset_type must be {CALIBRATION_DATASET_TYPE}')
    if dataset.get('case') != case:
        raise ConsequenceError(f'calibration dataset case mismatch: {dataset.get("case")} != {case}')
    source = dataset.get('source')
    if not isinstance(source, dict):
        raise ConsequenceError('calibration dataset source must be an object')
    if not isinstance(source.get('title'), str) or not source['title']:
        raise ConsequenceError('calibration dataset source.title is required')
    if not (isinstance(source.get('url'), str) and source['url']) and not (
        isinstance(source.get('doi'), str) and source['doi']
    ):
        raise ConsequenceError('calibration dataset source must include url or doi')
    source_type = dataset.get('source_type')
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ConsequenceError(f'unsupported calibration source_type: {source_type}')
    metrics = dataset.get('metrics')
    if not isinstance(metrics, list) or len(metrics) < 2:
        raise ConsequenceError('calibration dataset must include at least two metrics')
    checks = [compare_metric(metric, summary) for metric in metrics]
    families = {item['family'] for item in checks}
    all_passed = all(item['passed'] for item in checks)
    clears_blocker = (
        all_passed
        and {'radiation', 'overpressure'} <= families
        and source_type in EXPERIMENTAL_SOURCE_TYPES
    )
    return {
        'dataset_path': str(path),
        'dataset_sha256': sha256_file(path),
        'source': source,
        'source_type': source_type,
        'metric_count': len(checks),
        'metric_families': sorted(families),
        'all_metrics_passed': all_passed,
        'requires_experimental_source_to_clear_blocker': True,
        'clears_blocker': clears_blocker,
        'checks': checks,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    ignition_path = Path(args.ignition_report)
    hazard_summary_path = Path(args.hazard_summary)
    hazard_timeseries_path = Path(args.hazard_timeseries)
    hazard_planes_path = Path(args.hazard_planes)

    ignition = load_json(ignition_path)
    summary = parse_key_value_log(hazard_summary_path)
    timeseries = parse_key_value_log(hazard_timeseries_path)
    planes = parse_key_value_log(hazard_planes_path)

    if ignition.get('status') != 'PASS-SMOKE':
        raise ConsequenceError(f'ignition report is not PASS-SMOKE: {ignition.get("status")}')
    if summary.get('status') != 'flammable_cloud_detected':
        raise ConsequenceError('hazard summary did not detect a flammable cloud')

    final_time_s = positive_number(timeseries, 'timeN')
    total_h2_mass_kg = positive_number(summary, 'total_species_mass')
    cloud_h2_mass_kg = positive_number(summary, 'cloud_species_mass')
    cloud_volume_m3 = positive_number(summary, 'cloud_volume')
    max_x = positive_number(summary, 'max_X')
    flammable_planes = int(positive_number(planes, 'flammable_planes'))
    active_planes = int(positive_number(planes, 'active_planes'))
    mass_rate_kg_s = total_h2_mass_kg / final_time_s
    source_heat_release_w = mass_rate_kg_s * args.lhv_j_per_kg
    cloud_energy_j = cloud_h2_mass_kg * args.lhv_j_per_kg
    cloud_average_hrr_w = cloud_energy_j / max(args.assumed_burn_duration_s, 1.0e-12)
    radiative_source_w = args.radiative_fraction * source_heat_release_w
    radiative_cloud_w = args.radiative_fraction * cloud_average_hrr_w
    tnt_mass_kg = cloud_energy_j * args.blast_efficiency / args.tnt_j_per_kg

    radiation = []
    overpressure = []
    prev_flux = math.inf
    prev_overpressure = math.inf
    for distance in args.distances_m:
        if distance <= 0.0:
            raise ConsequenceError('radiation/overpressure distances must be positive')
        source_flux = radiative_source_w / (4.0 * math.pi * distance * distance)
        cloud_flux = radiative_cloud_w / (4.0 * math.pi * distance * distance)
        if source_flux > prev_flux + 1.0e-9:
            raise ConsequenceError('radiation flux is not monotonic with distance')
        prev_flux = source_flux
        radiation.append({
            'distance_m': distance,
            'source_limited_flux_w_m2': source_flux,
            'cloud_average_flux_w_m2': cloud_flux,
        })
        scaled_distance = distance / max(tnt_mass_kg, 1.0e-30) ** (1.0 / 3.0)
        peak_kpa = overpressure_screening_kpa(scaled_distance)
        if peak_kpa > prev_overpressure + 1.0e-9:
            raise ConsequenceError('overpressure metric is not monotonic with distance')
        prev_overpressure = peak_kpa
        overpressure.append({
            'distance_m': distance,
            'scaled_distance_m_kg13': scaled_distance,
            'screening_peak_overpressure_kpa': peak_kpa,
        })

    ignition_summary = ignition.get('summary', {}) if isinstance(ignition.get('summary'), dict) else {}
    summary_metrics = {
        'leak_final_time_s': final_time_s,
        'total_h2_mass_kg': total_h2_mass_kg,
        'flammable_cloud_h2_mass_kg': cloud_h2_mass_kg,
        'flammable_cloud_volume_m3': cloud_volume_m3,
        'max_h2_mole_fraction': max_x,
        'active_planes': active_planes,
        'flammable_planes': flammable_planes,
        'inferred_mass_rate_kg_s': mass_rate_kg_s,
        'source_limited_heat_release_w': source_heat_release_w,
        'flammable_cloud_energy_j': cloud_energy_j,
        'cloud_average_heat_release_w': cloud_average_hrr_w,
        'source_limited_radiative_power_w': radiative_source_w,
        'cloud_average_radiative_power_w': radiative_cloud_w,
        'tnt_equivalent_mass_kg': tnt_mass_kg,
        'max_screening_flux_w_m2': max(item['source_limited_flux_w_m2'] for item in radiation),
        'max_screening_overpressure_kpa': max(item['screening_peak_overpressure_kpa'] for item in overpressure),
        'ignition_time_s': ignition_summary.get('delay_fine_ignition_time_s'),
        'ignition_heat_release_sdc_rel_linf': ignition_summary.get('sdc_heat_release_rel_linf'),
    }
    for item in radiation:
        token = distance_summary_token(float(item['distance_m']))
        summary_metrics[f'screening_flux_at_{token}_w_m2'] = item['source_limited_flux_w_m2']
        summary_metrics[f'cloud_average_flux_at_{token}_w_m2'] = item['cloud_average_flux_w_m2']
    for item in overpressure:
        token = distance_summary_token(float(item['distance_m']))
        summary_metrics[f'screening_overpressure_at_{token}_kpa'] = item['screening_peak_overpressure_kpa']
    calibration = None
    if args.calibration_dataset_json:
        calibration = evaluate_calibration_dataset(Path(args.calibration_dataset_json), args.case, summary_metrics)

    clears_calibrated_blocker = bool(calibration and calibration['clears_blocker'])
    report = {
        'schema_version': SCHEMA_VERSION,
        'case': args.case,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': 'PASS-CALIBRATED-CONSEQUENCE-AGREEMENT' if clears_calibrated_blocker else 'PASS-SCREENING',
        'model_scope': (
            'calibrated_engineering_consequence_evidence'
            if clears_calibrated_blocker else 'engineering_screening_not_calibrated'
        ),
        'consequence_model_tier': (
            'external_fire_blast_calibration_agreement'
            if clears_calibrated_blocker else 'screening_metrics'
        ),
        'radiation_model_calibrated': clears_calibrated_blocker,
        'overpressure_model_calibrated': clears_calibrated_blocker,
        'flame_geometry_model': False,
        'validated_against_fire_experiment': clears_calibrated_blocker,
        'validated_against_blast_experiment': clears_calibrated_blocker,
        'clears_calibrated_fire_consequence_blocker': clears_calibrated_blocker,
        'inputs': {
            'h2_lhv_j_per_kg': args.lhv_j_per_kg,
            'tnt_j_per_kg': args.tnt_j_per_kg,
            'radiative_fraction': args.radiative_fraction,
            'blast_efficiency': args.blast_efficiency,
            'assumed_burn_duration_s': args.assumed_burn_duration_s,
            'distances_m': list(args.distances_m),
        },
        'evidence_files': [
            evidence_entry('ignition_consequence_report', ignition_path),
            evidence_entry('hazard_summary_log', hazard_summary_path),
            evidence_entry('hazard_timeseries_log', hazard_timeseries_path),
            evidence_entry('hazard_planes_log', hazard_planes_path),
        ],
        'summary': summary_metrics,
        'radiation_by_distance': radiation,
        'overpressure_by_distance': overpressure,
        'checks': {
            'ignition_report_status': 'PASS',
            'flammable_cloud_detected': 'PASS',
            'positive_cloud_mass': 'PASS',
            'positive_heat_release': 'PASS',
            'radiation_monotonic_with_distance': 'PASS',
            'overpressure_monotonic_with_distance': 'PASS',
        },
        'limitations': [
            'Screening-only consequence metrics derived from smoke/scout CFD evidence.',
            'Radiation uses an isotropic point-source fraction and does not model flame geometry, soot, view factors, terrain, or shielding.',
            'Overpressure uses a TNT-equivalent screening metric and is not a calibrated deflagration or congestion model.',
            'This report does not replace site-specific safety engineering, regulatory compliance, or validated consequence tools.',
        ],
    }
    if calibration:
        report['fire_calibration_agreement'] = calibration
        report['evidence_files'].append(evidence_entry('fire_calibration_dataset', Path(args.calibration_dataset_json)))
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        '# H2 Fire Consequence Screening Metrics',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['model_scope']}`",
        f"Consequence model tier: `{report.get('consequence_model_tier', '')}`",
        f"Radiation model calibrated: `{report.get('radiation_model_calibrated', False)}`",
        f"Overpressure model calibrated: `{report.get('overpressure_model_calibrated', False)}`",
        f"Flame geometry model: `{report.get('flame_geometry_model', False)}`",
        f"Validated against fire experiment: `{report.get('validated_against_fire_experiment', False)}`",
        f"Validated against blast experiment: `{report.get('validated_against_blast_experiment', False)}`",
        f"Clears calibrated fire consequence blocker: `{report.get('clears_calibrated_fire_consequence_blocker', False)}`",
        '',
        '## Summary',
        '',
        f"- Flammable-cloud H2 mass: `{s['flammable_cloud_h2_mass_kg']:.8e} kg`",
        f"- Flammable-cloud volume: `{s['flammable_cloud_volume_m3']:.8e} m^3`",
        f"- Inferred source heat release: `{s['source_limited_heat_release_w']:.8e} W`",
        f"- Flammable-cloud energy: `{s['flammable_cloud_energy_j']:.8e} J`",
        f"- TNT-equivalent screening mass: `{s['tnt_equivalent_mass_kg']:.8e} kg`",
        f"- Max screening radiation flux: `{s['max_screening_flux_w_m2']:.8e} W/m^2`",
        f"- Max screening overpressure: `{s['max_screening_overpressure_kpa']:.8e} kPa`",
        '',
        '## Radiation',
        '',
        '| Distance m | Source-limited W/m2 | Cloud-average W/m2 |',
        '| ---: | ---: | ---: |',
    ]
    for item in report['radiation_by_distance']:
        lines.append(
            f"| {item['distance_m']:.3g} | {item['source_limited_flux_w_m2']:.8e} | {item['cloud_average_flux_w_m2']:.8e} |"
        )
    lines += ['', '## Overpressure', '', '| Distance m | Scaled distance | Screening peak kPa |', '| ---: | ---: | ---: |']
    for item in report['overpressure_by_distance']:
        lines.append(
            f"| {item['distance_m']:.3g} | {item['scaled_distance_m_kg13']:.8e} | {item['screening_peak_overpressure_kpa']:.8e} |"
        )
    calibration = report.get('fire_calibration_agreement')
    if isinstance(calibration, dict):
        lines += [
            '',
            '## External Calibration Agreement',
            '',
            f"- Source type: `{calibration.get('source_type')}`",
            f"- Metric count: `{calibration.get('metric_count')}`",
            f"- All metrics passed: `{calibration.get('all_metrics_passed')}`",
            f"- Clears calibrated fire consequence blocker: `{calibration.get('clears_blocker')}`",
            '',
            '| Metric | Family | Simulation | Reference | Relative error | Passed |',
            '| --- | --- | ---: | ---: | ---: | --- |',
        ]
        for item in calibration.get('checks', []):
            lines.append(
                f"| `{item['name']}` | `{item['family']}` | {item['simulation_value']:.8e} | "
                f"{item['reference_value']:.8e} | {item['rel_error']:.8e} | `{item['passed']}` |"
            )
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if data.get('schema_version') != SCHEMA_VERSION:
        raise ConsequenceError('schema_version mismatch')
    if data.get('status') not in {'PASS-SCREENING', 'PASS-CALIBRATED-CONSEQUENCE-AGREEMENT'}:
        raise ConsequenceError(f'invalid status: {data.get("status")}')
    clears_blocker = data.get('clears_calibrated_fire_consequence_blocker') is True
    if clears_blocker:
        if data.get('model_scope') != 'calibrated_engineering_consequence_evidence':
            raise ConsequenceError('calibrated report has invalid model_scope')
        if data.get('consequence_model_tier') != 'external_fire_blast_calibration_agreement':
            raise ConsequenceError('calibrated report has invalid consequence_model_tier')
        for key in (
            'radiation_model_calibrated',
            'overpressure_model_calibrated',
            'validated_against_fire_experiment',
            'validated_against_blast_experiment',
        ):
            if data.get(key) is not True:
                raise ConsequenceError(f'{key} must be true for calibrated evidence')
    else:
        if data.get('model_scope') != 'engineering_screening_not_calibrated':
            raise ConsequenceError('model_scope must explicitly remain screening-only')
        if data.get('consequence_model_tier') not in {None, 'screening_metrics'}:
            raise ConsequenceError('consequence_model_tier must be screening_metrics when present')
        for key in (
            'radiation_model_calibrated',
            'overpressure_model_calibrated',
            'validated_against_fire_experiment',
            'validated_against_blast_experiment',
        ):
            if data.get(key) not in {None, False}:
                raise ConsequenceError(f'{key} must be false for screening-only evidence')
    if data.get('flame_geometry_model') not in {None, False}:
        raise ConsequenceError('flame_geometry_model is not implemented by this report')
    summary = data.get('summary', {})
    for key in (
        'flammable_cloud_h2_mass_kg', 'flammable_cloud_volume_m3', 'source_limited_heat_release_w',
        'flammable_cloud_energy_j', 'tnt_equivalent_mass_kg', 'max_screening_flux_w_m2',
        'max_screening_overpressure_kpa',
    ):
        if not finite(summary.get(key)) or float(summary[key]) <= 0.0:
            raise ConsequenceError(f'invalid summary metric: {key}')
    radiation = data.get('radiation_by_distance', [])
    overpressure = data.get('overpressure_by_distance', [])
    if len(radiation) < 3 or len(overpressure) != len(radiation):
        raise ConsequenceError('distance sweeps are incomplete')
    for seq, key in ((radiation, 'source_limited_flux_w_m2'), (overpressure, 'screening_peak_overpressure_kpa')):
        prev_distance = -math.inf
        prev_value = math.inf
        for item in seq:
            distance = item.get('distance_m')
            value = item.get(key)
            if not finite(distance) or not finite(value) or float(distance) <= prev_distance or float(value) <= 0.0:
                raise ConsequenceError(f'invalid distance sweep item for {key}')
            if float(value) > prev_value + 1.0e-9:
                raise ConsequenceError(f'{key} is not monotonic decreasing')
            prev_distance = float(distance)
            prev_value = float(value)
    for item in data.get('evidence_files', []):
        p = Path(item.get('path', ''))
        if not p.exists():
            raise ConsequenceError(f'referenced evidence missing: {p}')
        if sha256_file(p) != item.get('sha256'):
            raise ConsequenceError(f'referenced evidence hash mismatch: {p}')
    calibration = data.get('fire_calibration_agreement')
    if clears_blocker:
        if not isinstance(calibration, dict):
            raise ConsequenceError('calibrated report is missing fire_calibration_agreement')
        if calibration.get('clears_blocker') is not True:
            raise ConsequenceError('calibration agreement does not clear blocker')
        if calibration.get('source_type') not in EXPERIMENTAL_SOURCE_TYPES:
            raise ConsequenceError('calibrated report must use an experimental/literature source')
        if calibration.get('all_metrics_passed') is not True:
            raise ConsequenceError('not all calibration metrics passed')
        families = set(calibration.get('metric_families', []))
        if {'radiation', 'overpressure'} - families:
            raise ConsequenceError('calibration must include both radiation and overpressure metrics')
        checks = calibration.get('checks')
        if not isinstance(checks, list) or len(checks) < 2:
            raise ConsequenceError('calibration checks are incomplete')
        for item in checks:
            for key in ('simulation_value', 'reference_value', 'abs_error', 'rel_error'):
                if not finite(item.get(key)):
                    raise ConsequenceError(f'calibration check has non-finite {key}')
            if item.get('passed') is not True:
                raise ConsequenceError('calibration check failed')
    elif calibration and calibration.get('clears_blocker') is True:
        raise ConsequenceError('screening report cannot contain clearing calibration agreement')
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', default='engineering-h2-fire-consequence-screening')
    ap.add_argument('--ignition-report', default=str(DEFAULT_IGNITION_REPORT))
    ap.add_argument('--hazard-summary', default=str(DEFAULT_HAZARD_SUMMARY))
    ap.add_argument('--hazard-timeseries', default=str(DEFAULT_HAZARD_TIMESERIES))
    ap.add_argument('--hazard-planes', default=str(DEFAULT_HAZARD_PLANES))
    ap.add_argument('--lhv-j-per-kg', type=float, default=H2_LHV_J_PER_KG)
    ap.add_argument('--tnt-j-per-kg', type=float, default=TNT_J_PER_KG)
    ap.add_argument('--radiative-fraction', type=float, default=0.15)
    ap.add_argument('--blast-efficiency', type=float, default=0.03)
    ap.add_argument('--assumed-burn-duration-s', type=float, default=1.0)
    ap.add_argument('--distances-m', type=float, nargs='+', default=list(DEFAULT_DISTANCES_M))
    ap.add_argument('--calibration-dataset-json')
    ap.add_argument('--output-json')
    ap.add_argument('--output-md')
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)
    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            s = data['summary']
            print(
                'engineering_h2_fire_consequence_metrics VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"cloud_mass={s['flammable_cloud_h2_mass_kg']:.8e} "
                f"max_flux={s['max_screening_flux_w_m2']:.8e} "
                f"max_overpressure={s['max_screening_overpressure_kpa']:.8e}"
            )
            return 0
        if not args.output_json or not args.output_md:
            raise ConsequenceError('--output-json and --output-md are required unless --verify-json is used')
        if args.lhv_j_per_kg <= 0.0 or args.tnt_j_per_kg <= 0.0:
            raise ConsequenceError('energy constants must be positive')
        if not 0.0 < args.radiative_fraction <= 1.0:
            raise ConsequenceError('radiative fraction must be in (0, 1]')
        if not 0.0 < args.blast_efficiency <= 1.0:
            raise ConsequenceError('blast efficiency must be in (0, 1]')
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        write_markdown(report, out_md)
        s = report['summary']
        print(
            'engineering_h2_fire_consequence_metrics PASS '
            f"json={out_json} md={out_md} cloud_mass={s['flammable_cloud_h2_mass_kg']:.8e} "
            f"max_flux={s['max_screening_flux_w_m2']:.8e} max_overpressure={s['max_screening_overpressure_kpa']:.8e}"
        )
        return 0
    except ConsequenceError as exc:
        print(f'engineering_h2_fire_consequence_metrics FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
