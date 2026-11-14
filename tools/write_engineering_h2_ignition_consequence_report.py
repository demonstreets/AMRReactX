#!/usr/bin/env python3
"""Write a compact engineering H2 ignition consequence report from validation logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ConsequenceReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ConsequenceReportError(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def marker_values() -> list[str]:
    values = [str(Path.home()), os.environ.get('HOME', '')]
    for key, value in os.environ.items():
        upper = key.upper()
        if any(token in upper for token in ('PASS', 'PASSWORD', 'SECRET', 'TOKEN')):
            values.append(value)
    return sorted({value for value in values if value and len(value) > 3})


def no_private_markers(text: str) -> bool:
    return not any(marker in text for marker in marker_values())


def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return str(path)


def parse_pairs(line: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for key, value in re.findall(r'([A-Za-z0-9_()]+)=([^\s]+)', line):
        pairs[key] = value.rstrip(',;')
    return pairs


def as_float(metrics: dict[str, str], key: str) -> float:
    require(key in metrics, f'missing metric {key}')
    value = float(metrics[key])
    require(math.isfinite(value), f'nonfinite metric {key}={metrics[key]!r}')
    return value


def load_pass_log(path: Path, prefix: str, repo: Path) -> tuple[str, dict[str, str], dict[str, Any]]:
    require(path.is_file(), f'missing log {path}')
    raw = path.read_text(encoding='utf-8', errors='replace')
    require(no_private_markers(raw), f'log contains machine-local/private markers: {path}')
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    matches = [line for line in lines if line.startswith(prefix + ' PASS')]
    require(matches, f'{path} lacks {prefix} PASS line')
    line = matches[-1]
    return line, parse_pairs(line), {'path': rel(path, repo), 'sha256': sha256_text(raw), 'pass_line': line}


def verify_report(path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing report {path}')
    raw = path.read_text(encoding='utf-8')
    require(no_private_markers(raw), 'report contains machine-local/private markers')
    report = json.loads(raw)
    require(report.get('schema_version') == 1, 'schema_version is not 1')
    require(report.get('status') == 'PASS-SMOKE', 'status is not PASS-SMOKE')
    checks = report.get('checks', {})
    for key in ('history', 'delay', 'sdc'):
        require(checks.get(key) == 'PASS', f'{key} check is not PASS')
    summary = report.get('summary', {})
    require(float(summary.get('h2_consumed_mean', 0.0)) > 0.0, 'missing H2 consumption')
    require(float(summary.get('h2o_produced_mean', 0.0)) > 0.0, 'missing H2O production')
    require(float(summary.get('history_temp_peak_max', 0.0)) >= 1900.0, 'weak peak temperature')
    require(float(summary.get('delay_fine_ignition_time_s', 0.0)) > 0.0, 'missing ignition delay')
    require(float(summary.get('sdc_heat_release_rel_linf', 1.0)) <= 5.0e-2, 'SDC heat release mismatch too large')
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report['summary']
    lines = [
        '# Engineering H2 Ignition Consequence Report',
        '',
        f"Status: `{report['status']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        '',
        '## Summary',
        '',
        f"- Ignition delay fine estimate: `{s['delay_fine_ignition_time_s']:.8e}` s",
        f"- Mid/fine ignition-delay relative difference: `{s['delay_mid_fine_rel']:.8e}`",
        f"- Mean H2 consumed: `{s['h2_consumed_mean']:.8e}`",
        f"- Mean O2 consumed: `{s['o2_consumed_mean']:.8e}`",
        f"- Mean H2O produced: `{s['h2o_produced_mean']:.8e}`",
        f"- History peak temperature range: `{s['history_temp_peak_min']:.8e}` to `{s['history_temp_peak_max']:.8e}` K",
        f"- History max heat/reaction rate metric: `{s['history_max_reaction_rate']:.8e}`",
        f"- SDC HeatRelease relative Linf: `{s['sdc_heat_release_rel_linf']:.8e}`",
        '',
        '## Evidence Logs',
        '',
    ]
    for key, log in report['logs'].items():
        lines.append(f"- {key}: `{log['path']}` sha256=`{log['sha256'][:16]}`")
    lines.extend(['', '## Limitations', ''])
    for item in report['limitations']:
        lines.append(f'- {item}')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history-log', type=Path)
    parser.add_argument('--delay-log', type=Path)
    parser.add_argument('--sdc-log', type=Path)
    parser.add_argument('--output-json', type=Path)
    parser.add_argument('--output-md', type=Path)
    parser.add_argument('--verify-json', type=Path, help='Verify an existing consequence report JSON')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.verify_json:
            report = verify_report(args.verify_json)
            print('engineering_h2_ignition_consequence_report VERIFY-PASS ' +
                  f"json={args.verify_json} status={report['status']}")
            return 0

        require(args.history_log and args.delay_log and args.sdc_log, 'history/delay/sdc logs are required unless --verify-json is used')
        require(args.output_json and args.output_md, 'output paths are required unless --verify-json is used')
        repo = repo_root()
        history_line, history, history_log = load_pass_log(args.history_log, 'h2_ignition_history_validation', repo)
        delay_line, delay, delay_log = load_pass_log(args.delay_log, 'h2_ignition_delay_validation', repo)
        sdc_line, sdc, sdc_log = load_pass_log(args.sdc_log, 'h2_ignition_sdc_compare', repo)

        # The finest case is printed last by validate_h2_ignition_delay.py.
        tign_values = [float(value) for value in re.findall(r'tign=([0-9.eE+-]+)', delay_line)]
        require(tign_values, 'delay log has no tign values')
        summary = {
            'delay_threshold_rise_K': as_float(delay, 'threshold_rise'),
            'delay_mid_fine_rel': as_float(delay, 'mid_fine_rel'),
            'delay_fine_ignition_time_s': tign_values[-1],
            'history_plotfiles': int(float(history['nplot'])),
            'history_final_time_s': as_float(history, 'timeN'),
            'h2_consumed_mean': as_float(history, 'h2_consumed_mean'),
            'o2_consumed_mean': as_float(history, 'o2_consumed_mean'),
            'h2o_produced_mean': as_float(history, 'h2o_produced_mean'),
            'history_temp_peak_min': as_float(history, 'temp_peak_min'),
            'history_temp_peak_max': as_float(history, 'temp_peak_max'),
            'history_temp_mean_change': as_float(history, 'temp_mean_change'),
            'history_max_hotspot_radius': as_float(history, 'max_hotspot_radius'),
            'history_species_sum_err': as_float(history, 'species_sum_err'),
            'history_active_reaction_slices': int(float(history['active_reaction_slices'])),
            'history_max_reaction_rate': as_float(history, 'max_reaction_rate'),
            'sdc_temp_rel_linf': as_float(sdc, 'temp_rel_linf'),
            'sdc_h2o_mean_sdc1': as_float(sdc, 'h2o_mean_sdc1'),
            'sdc_h2o_mean_sdc2': as_float(sdc, 'h2o_mean_sdc2'),
            'sdc_heat_release_rel_linf': as_float(sdc, 'heat_rel_linf'),
        }
        require(summary['delay_mid_fine_rel'] <= 2.5e-2, 'ignition-delay mid/fine mismatch too large')
        require(summary['h2_consumed_mean'] > 0.0 and summary['o2_consumed_mean'] > 0.0, 'fuel/oxidizer consumption missing')
        require(summary['h2o_produced_mean'] > 0.0, 'H2O production missing')
        require(summary['history_active_reaction_slices'] >= 8, 'too few active reaction slices')
        require(summary['history_temp_peak_max'] >= 1900.0, 'peak temperature too low')
        require(summary['sdc_heat_release_rel_linf'] <= 5.0e-2, 'SDC heat release mismatch too large')

        report = {
            'schema_version': 1,
            'status': 'PASS-SMOKE',
            'generated_at_utc': utc_now(),
            'case': 'engineering-h2-ignition-consequence-smoke',
            'checks': {'history': 'PASS', 'delay': 'PASS', 'sdc': 'PASS'},
            'summary': summary,
            'logs': {'history': history_log, 'delay': delay_log, 'sdc': sdc_log},
            'limitations': [
                'This is a short-time H2 ignition and heat-release consequence smoke report, not a calibrated fire model.',
                'It does not validate flame speed, radiant heat flux, pool-fire feedback, deflagration overpressure, ventilation effects, or production-scale obstacle fires.',
                'Ignition-delay evidence uses a homogeneous PelePhysics driver; history/SDC evidence uses the PeleLMeX hot-bubble engineering case.',
            ],
        }
        raw = json.dumps(report, indent=2, sort_keys=True) + '\n'
        require(no_private_markers(raw), 'report contains machine-local/private markers')
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(raw, encoding='utf-8')
        write_markdown(report, args.output_md)
        verify_report(args.output_json)
        print('engineering_h2_ignition_consequence_report PASS ' +
              f"json={args.output_json} md={args.output_md} " +
              f"tign={summary['delay_fine_ignition_time_s']:.8e} " +
              f"h2o={summary['h2o_produced_mean']:.8e} heat_rel_linf={summary['sdc_heat_release_rel_linf']:.8e}")
        return 0
    except ConsequenceReportError as exc:
        print(f'engineering_h2_ignition_consequence_report FAIL {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
