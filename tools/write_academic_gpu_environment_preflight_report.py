#!/usr/bin/env python3
"""Write/verify academic GPU environment preflight evidence for ACD-10/QLT-05."""
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
STATUS_READY = 'PASS-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT'
STATUS_NOT_READY = 'NOT_READY-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT'
DEFAULT_ROOT = Path('docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728')
DEFAULT_MANIFEST = DEFAULT_ROOT / 'gpu_environment_preflight_manifest.json'
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / 'academic_gpu_environment_preflight_report.json'
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / 'academic_gpu_environment_preflight_report.md'


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


def evidence_entry(label: str, path: Path) -> dict[str, str]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {'label': label, 'path': str(path), 'sha256': sha256_file(path)}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise ReportError(f'failed to read JSON {path}: {exc}') from exc


def read_text(path: Path) -> str:
    require(path.is_file(), f'missing text evidence: {path}')
    return path.read_text(errors='replace')


def parse_not_found(ldd_text: str) -> list[str]:
    missing: list[str] = []
    for line in ldd_text.splitlines():
        if 'not found' in line:
            missing.append(line.strip().split()[0])
    return sorted(set(missing))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    paths = manifest.get('paths')
    require(isinstance(paths, dict), 'manifest paths missing')
    nvidia_log = Path(str(paths.get('nvidia_smi_log', '')))
    ldd_log = Path(str(paths.get('ldd_log', '')))
    cuda_find_log = Path(str(paths.get('cuda_find_log', '')))
    smoke_log = Path(str(paths.get('smoke_log', '')))
    smoke_input = Path(str(paths.get('smoke_input', '')))

    nvidia_rc = int(manifest.get('nvidia_smi_returncode', 999))
    smoke_rc = int(manifest.get('smoke_returncode', 999))
    ldd_text = read_text(ldd_log)
    missing_libs = parse_not_found(ldd_text)
    required_cuda_libs = [
        'libcudart.so',
        'libcurand.so',
        'libcusparse.so',
        'libcusolver.so',
    ]
    missing_cuda_runtime_libs = sorted(
        lib for lib in missing_libs if any(lib.startswith(required) for required in required_cuda_libs)
    )
    nvidia_text = read_text(nvidia_log)
    driver_library_mismatch = 'Driver/library version mismatch' in nvidia_text
    smoke_text = read_text(smoke_log)
    smoke_finalized = 'AMReX' in smoke_text and 'finalized' in smoke_text
    smoke_failure_tokens = bool(re.search(
        r'not found|error while loading shared libraries|'
        r'amrex::Error|Abort|SIG|'
        r'CUDA error|cudaError|cuda runtime error|'
        r'illegal memory access|unspecified launch failure',
        smoke_text,
        re.IGNORECASE,
    ))

    ready = (
        nvidia_rc == 0
        and not missing_cuda_runtime_libs
        and smoke_rc == 0
        and smoke_finalized
        and not smoke_failure_tokens
    )
    status = STATUS_READY if ready else STATUS_NOT_READY
    blocking_reasons: list[str] = []
    if nvidia_rc != 0:
        blocking_reasons.append('nvidia_smi_failed')
    if driver_library_mismatch:
        blocking_reasons.append('nvidia_driver_library_version_mismatch')
    if missing_cuda_runtime_libs:
        blocking_reasons.append('missing_cuda_runtime_libraries')
    if smoke_rc != 0:
        blocking_reasons.append('cuda_academic_detonation_smoke_failed')
    if smoke_failure_tokens:
        blocking_reasons.append('cuda_smoke_log_contains_failure_tokens')

    summary = {
        'ready_for_acd_10_gpu_credit': ready,
        'ready_for_qlt_05_gpu_compliance_credit': ready,
        'nvidia_smi_returncode': nvidia_rc,
        'driver_library_mismatch': driver_library_mismatch,
        'missing_cuda_runtime_libraries': missing_cuda_runtime_libs,
        'all_missing_libraries': missing_libs,
        'smoke_returncode': smoke_rc,
        'smoke_finalized': smoke_finalized,
        'blocking_reasons': blocking_reasons,
    }
    quality_gates = [
        {
            'name': 'gpu_driver_query',
            'status': 'PASS' if nvidia_rc == 0 and not driver_library_mismatch else 'FAIL',
            'gap': '' if nvidia_rc == 0 and not driver_library_mismatch else 'nvidia-smi does not report a healthy GPU driver state.',
            'evidence': [str(nvidia_log)],
        },
        {
            'name': 'cuda_runtime_libraries',
            'status': 'PASS' if not missing_cuda_runtime_libs else 'FAIL',
            'gap': '' if not missing_cuda_runtime_libs else 'CUDA runtime/math libraries required by the academic CUDA executable are missing from the loader path/cache.',
            'evidence': [str(ldd_log), str(cuda_find_log)],
        },
        {
            'name': 'academic_cuda_detonation_smoke',
            'status': 'PASS' if smoke_rc == 0 and smoke_finalized and not smoke_failure_tokens else 'FAIL',
            'gap': '' if smoke_rc == 0 and smoke_finalized and not smoke_failure_tokens else 'The CUDA detonation smoke run does not complete.',
            'evidence': [str(smoke_log), str(smoke_input)],
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'title': 'Academic GPU Environment Preflight',
        'scope': 'GPU runtime and academic CUDA detonation smoke preflight for ACD-10 and QLT-05 credit',
        'summary': summary,
        'quality_gates': quality_gates,
        'manifest': manifest,
        'evidence_files': [
            evidence_entry('manifest', manifest_path),
            evidence_entry('nvidia_smi_log', nvidia_log),
            evidence_entry('ldd_log', ldd_log),
            evidence_entry('cuda_find_log', cuda_find_log),
            evidence_entry('smoke_input', smoke_input),
            evidence_entry('smoke_log', smoke_log),
            evidence_entry('runner', Path('tools/codex_run_academic_gpu_environment_preflight.sh')),
            evidence_entry('report_writer', Path('tools/write_academic_gpu_environment_preflight_report.py')),
        ],
        'limitations': [
            'This preflight does not install or repair NVIDIA/CUDA drivers or toolkit libraries.',
            'A NOT_READY result is still useful evidence: it localizes why ACD-10/QLT-05 cannot receive GPU execution credit on the current server state.',
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {STATUS_READY, STATUS_NOT_READY}, 'invalid status')
    summary = data.get('summary')
    require(isinstance(summary, dict), 'summary missing')
    if data.get('status') == STATUS_READY:
        require(summary.get('ready_for_acd_10_gpu_credit') is True, 'PASS must clear ACD-10')
        require(summary.get('ready_for_qlt_05_gpu_compliance_credit') is True, 'PASS must clear QLT-05')
        require(not summary.get('blocking_reasons'), 'PASS has blocking reasons')
    else:
        require(summary.get('ready_for_acd_10_gpu_credit') is False, 'NOT_READY must not clear ACD-10')
        require(summary.get('ready_for_qlt_05_gpu_compliance_credit') is False, 'NOT_READY must not clear QLT-05')
        require(summary.get('blocking_reasons'), 'NOT_READY must list blocking reasons')
    gates = data.get('quality_gates')
    require(isinstance(gates, list) and gates, 'quality gates missing')
    if check_hashes:
        entries = data.get('evidence_files')
        require(isinstance(entries, list) and entries, 'evidence files missing')
        for item in entries:
            require(isinstance(item, dict), 'evidence entry not object')
            path = Path(str(item.get('path', '')))
            require(path.is_file(), f'missing evidence file: {path}')
            require(sha256_file(path) == item.get('sha256'), f'evidence sha256 mismatch: {path}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report['summary']
    lines = [
        '# Academic GPU Environment Preflight',
        '',
        f"Status: `{report['status']}`",
        f"Scope: `{report['scope']}`",
        '',
        '## Summary',
        '',
    ]
    for key in [
        'ready_for_acd_10_gpu_credit',
        'ready_for_qlt_05_gpu_compliance_credit',
        'nvidia_smi_returncode',
        'driver_library_mismatch',
        'missing_cuda_runtime_libraries',
        'smoke_returncode',
        'smoke_finalized',
        'blocking_reasons',
    ]:
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines += ['', '## Quality Gates', '', '| Gate | Status | Gap | Evidence |', '| --- | --- | --- | --- |']
    for gate in report['quality_gates']:
        evidence = '; '.join(str(x) for x in gate.get('evidence', []))
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | {gate.get('gap') or 'none'} | {evidence} |")
    lines += ['', '## Limitations', '']
    lines.extend(f"- {item}" for item in report['limitations'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument('--verify-json')
    args = parser.parse_args()

    try:
        if args.verify_json:
            path = Path(args.verify_json)
            data = load_json(path)
            validate_report_object(data, check_hashes=True)
            print(
                'academic_gpu_environment_preflight VERIFY-PASS '
                f'json={path} status={data.get("status")} '
                f'blocking={data.get("summary", {}).get("blocking_reasons")}'
            )
            return 0
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        write_markdown(report, out_md)
        print(
            'academic_gpu_environment_preflight PASS '
            f'json={out_json} status={report["status"]} '
            f'blocking={report["summary"].get("blocking_reasons")}'
        )
        return 0
    except ReportError as exc:
        print(f'academic_gpu_environment_preflight FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
