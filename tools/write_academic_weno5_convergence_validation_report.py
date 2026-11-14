#!/usr/bin/env python3
"""Write/verify the academic WENO5 convergence validation report."""
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
STATUS_PASS = 'PASS-ACADEMIC-WENO5-CONVERGENCE-VALIDATION'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-WENO5-CONVERGENCE-VALIDATION'

DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_weno5_convergence_validation_20260729')
DEFAULT_CASE_SUMMARY = DEFAULT_ROOT / 'case_summary.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_weno5_convergence_validation_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_weno5_convergence_validation_report.md'

TEST_NAMES = {'weno5_smoke', 'pelec_weno_smoke'}


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


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
        raise ReportError(f'missing JSON: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f'invalid JSON {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON root is not an object: {path}')
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def as_finite_float(value: str, label: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ReportError(f'invalid float for {label}: {value}') from exc
    require(math.isfinite(parsed), f'non-finite float for {label}: {value}')
    return parsed


def parse_ctest_log(path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing CTest log: {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    passed = set(re.findall(r'Test\s+#\d+:\s+(\S+)\s+\.+\s+Passed', text))
    if not passed:
        passed = set(re.findall(r'\d+/\d+\s+Test\s+#\d+:\s+(\S+)\s+\.+\s+Passed', text))

    standalone = re.search(r'T01: Sine 5th-order convergence\s+\(p=([0-9.eE+-]+)\)', text)
    require(standalone is not None, 'standalone WENO5 convergence order not found in CTest log')
    standalone_order = as_finite_float(standalone.group(1), 'standalone_weno5_order')

    pelec_order = re.search(
        r'PeleC WENO5-Z smooth sine regression order\s+'
        r'\(p32-64=([0-9.eE+-]+)\s+p64-128=([0-9.eE+-]+)\)',
        text,
    )
    require(pelec_order is not None, 'PeleC WENO5-Z smooth sine regression order not found in CTest log')
    p32_64 = as_finite_float(pelec_order.group(1), 'pelec_weno5z_p32_64')
    p64_128 = as_finite_float(pelec_order.group(2), 'pelec_weno5z_p64_128')

    baseline = re.search(
        r'PeleC WENO5-Z beats second-order face average on smooth sine\s+'
        r'\(weno=([0-9.eE+-]+)\s+linear=([0-9.eE+-]+)\)',
        text,
    )
    require(baseline is not None, 'PeleC WENO5-Z vs second-order baseline metrics not found')
    weno_l1 = as_finite_float(baseline.group(1), 'pelec_weno5z_l1')
    linear_l1 = as_finite_float(baseline.group(2), 'second_order_face_average_l1')
    require(linear_l1 > 0.0, 'second-order baseline error must be positive')

    return {
        'passed_tests': sorted(passed & TEST_NAMES),
        'standalone_weno5_sine_order': standalone_order,
        'pelec_weno5z_p32_64': p32_64,
        'pelec_weno5z_p64_128': p64_128,
        'pelec_weno5z_l1_n64': weno_l1,
        'second_order_face_average_l1_n64': linear_l1,
        'weno_to_second_order_error_ratio': weno_l1 / linear_l1,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case_summary_path = Path(args.case_summary)
    case = load_json(case_summary_path)
    cmake_log = Path(str(case['cmake_log']))
    build_log = Path(str(case['build_log']))
    ctest_list_log = Path(str(case['ctest_list_log']))
    ctest_log = Path(str(case['ctest_log']))
    for path in (cmake_log, build_log, ctest_list_log, ctest_log):
        require(path.is_file(), f'missing evidence file: {path}')

    metrics = parse_ctest_log(ctest_log)
    missing_tests = sorted(TEST_NAMES - set(metrics['passed_tests']))
    blocking_reasons: list[str] = []
    if int(case.get('ctest_returncode', 1)) != 0:
        blocking_reasons.append('weno_ctest_failed')
    if missing_tests:
        blocking_reasons.append('required_weno_ctests_not_passed')
    if metrics['standalone_weno5_sine_order'] < float(args.min_order):
        blocking_reasons.append('standalone_weno5_order_below_gate')
    if metrics['pelec_weno5z_p32_64'] < float(args.min_order):
        blocking_reasons.append('pelec_weno5z_p32_64_below_gate')
    if metrics['pelec_weno5z_p64_128'] < float(args.min_order):
        blocking_reasons.append('pelec_weno5z_p64_128_below_gate')
    if metrics['weno_to_second_order_error_ratio'] > float(args.max_weno_to_second_order_ratio):
        blocking_reasons.append('weno5z_not_sufficiently_better_than_second_order')

    status = STATUS_PASS if not blocking_reasons else STATUS_NOT_READY
    summary = {
        **metrics,
        'required_tests': sorted(TEST_NAMES),
        'missing_tests': missing_tests,
        'min_order_gate': float(args.min_order),
        'max_weno_to_second_order_ratio_gate': float(args.max_weno_to_second_order_ratio),
        'clears_acd_01_weno5_order_gap': status == STATUS_PASS,
        'clears_qlt_03_weno5_mms_order_subgap': status == STATUS_PASS,
        'blocking_reasons': blocking_reasons,
    }
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Academic WENO5 Convergence Validation',
        'scope': (
            'Maintained WENO5/WENO5-Z smooth-field convergence gate using the current CTest '
            'weno5_smoke and pelec_weno_smoke executables. This promotes the historical smooth '
            'sine regression into a reproducible report with explicit order and baseline-improvement gates.'
        ),
        'case': case,
        'summary': summary,
        'quality_gates': [
            {
                'name': 'weno_ctests_built_and_passed',
                'status': 'PASS' if not missing_tests and int(case.get('ctest_returncode', 1)) == 0 else 'NOT_READY',
                'gap': '' if not missing_tests else f'missing passing tests: {missing_tests}',
                'evidence': [str(ctest_log)],
            },
            {
                'name': 'standalone_weno5_sine_order',
                'status': 'PASS' if metrics['standalone_weno5_sine_order'] >= float(args.min_order) else 'NOT_READY',
                'gap': '' if metrics['standalone_weno5_sine_order'] >= float(args.min_order) else 'standalone WENO5 fitted order below gate',
                'evidence': [str(ctest_log)],
            },
            {
                'name': 'pelec_weno5z_sine_order',
                'status': 'PASS'
                if metrics['pelec_weno5z_p32_64'] >= float(args.min_order)
                and metrics['pelec_weno5z_p64_128'] >= float(args.min_order)
                else 'NOT_READY',
                'gap': ''
                if metrics['pelec_weno5z_p32_64'] >= float(args.min_order)
                and metrics['pelec_weno5z_p64_128'] >= float(args.min_order)
                else 'PeleC WENO5-Z order below gate',
                'evidence': [str(ctest_log)],
            },
            {
                'name': 'weno5z_beats_second_order_baseline',
                'status': 'PASS'
                if metrics['weno_to_second_order_error_ratio'] <= float(args.max_weno_to_second_order_ratio)
                else 'NOT_READY',
                'gap': ''
                if metrics['weno_to_second_order_error_ratio'] <= float(args.max_weno_to_second_order_ratio)
                else 'WENO5-Z smooth-field error ratio above gate',
                'evidence': [str(ctest_log)],
            },
        ],
        'evidence_files': [
            evidence_entry('case_summary', case_summary_path),
            evidence_entry('cmake_log', cmake_log),
            evidence_entry('build_log', build_log),
            evidence_entry('ctest_list_log', ctest_list_log),
            evidence_entry('ctest_log', ctest_log),
            evidence_entry('standalone_weno5_test_source', Path('test/unit/test_weno5.cpp')),
            evidence_entry('pelec_weno_test_source', Path('test/unit/test_pelec_weno.cpp')),
            evidence_entry('runner', Path('tools/codex_run_academic_weno5_convergence_validation.sh')),
            evidence_entry('report_writer', Path('tools/write_academic_weno5_convergence_validation_report.py')),
        ],
        'limitations': [
            'This is a smooth scalar/cell-average WENO order gate; it does not prove characteristic projection accuracy.',
            'This report strengthens ACD-01/QLT-03 order evidence but does not replace full-flow WENO-vs-PPM detonation comparisons.',
            'The gate uses current CTest output as authoritative evidence, so report verification also hashes the test sources and logs.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_PASS, STATUS_NOT_READY}, 'invalid status')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    require(summary.get('required_tests') == sorted(TEST_NAMES), 'required tests mismatch')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality_gates missing')
    for gate in gates:
        require(isinstance(gate, dict), 'quality gate is not an object')
        require(gate.get('status') in {'PASS', 'NOT_READY'}, f"invalid quality gate status: {gate.get('name')}")
    if data.get('status') == STATUS_PASS:
        require(summary.get('clears_acd_01_weno5_order_gap') is True, 'ACD-01 clear flag missing')
        require(summary.get('clears_qlt_03_weno5_mms_order_subgap') is True, 'QLT-03 clear flag missing')
        require(not summary.get('missing_tests'), 'PASS report has missing tests')
        require(not summary.get('blocking_reasons'), 'PASS report has blockers')
        require(float(summary.get('standalone_weno5_sine_order', 0.0)) >= float(summary.get('min_order_gate', 4.5)), 'standalone order below gate')
        require(float(summary.get('pelec_weno5z_p32_64', 0.0)) >= float(summary.get('min_order_gate', 4.5)), 'p32-64 below gate')
        require(float(summary.get('pelec_weno5z_p64_128', 0.0)) >= float(summary.get('min_order_gate', 4.5)), 'p64-128 below gate')
        require(
            float(summary.get('weno_to_second_order_error_ratio', 1.0))
            <= float(summary.get('max_weno_to_second_order_ratio_gate', 0.02)),
            'WENO baseline ratio above gate',
        )
        for gate in gates:
            require(gate.get('status') == 'PASS', f"quality gate not PASS: {gate.get('name')}")
    else:
        require(summary.get('clears_acd_01_weno5_order_gap') is False, 'NOT_READY report cannot clear ACD-01')
        require(summary.get('blocking_reasons'), 'NOT_READY report must list blockers')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Academic WENO5 Convergence Validation',
        '',
        f"Status: `{report['status']}`",
        '',
        f"Scope: {report['scope']}",
        '',
        '## Summary',
        '',
    ]
    for key in (
        'standalone_weno5_sine_order',
        'pelec_weno5z_p32_64',
        'pelec_weno5z_p64_128',
        'pelec_weno5z_l1_n64',
        'second_order_face_average_l1_n64',
        'weno_to_second_order_error_ratio',
        'clears_acd_01_weno5_order_gap',
        'clears_qlt_03_weno5_mms_order_subgap',
    ):
        lines.append(f'- `{key}`: `{summary.get(key)}`')
    lines += ['', '## Quality Gates', '']
    for gate in report['quality_gates']:
        lines.append(f"- `{gate['name']}`: `{gate['status']}`")
    lines += ['', '## Limitations', '']
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-summary', default=str(DEFAULT_CASE_SUMMARY))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--min-order', type=float, default=4.5)
    parser.add_argument('--max-weno-to-second-order-ratio', type=float, default=0.02)
    parser.add_argument('--verify-json')
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = verify_report(Path(args.verify_json))
            summary = report['summary']
            print(
                'academic_weno5_convergence_validation VERIFY-PASS '
                f"json={args.verify_json} status={report['status']} "
                f"p32_64={summary.get('pelec_weno5z_p32_64')} "
                f"p64_128={summary.get('pelec_weno5z_p64_128')} "
                f"ratio={summary.get('weno_to_second_order_error_ratio')}"
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        summary = report['summary']
        print(
            'academic_weno5_convergence_validation PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"p32_64={summary.get('pelec_weno5z_p32_64')} "
            f"p64_128={summary.get('pelec_weno5z_p64_128')}"
        )
        return 0
    except ReportError as exc:
        print(f'academic_weno5_convergence_validation FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
