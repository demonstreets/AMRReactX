#!/usr/bin/env python3
"""Write/verify the engineering log-marker compatibility report."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-LOG-MARKER-COMPATIBILITY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_log_marker_compatibility_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_log_marker_compatibility_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_log_marker_compatibility_report.md"

PROB_CPP = Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")

CH4_REPORT_SCRIPTS = [
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_cuda_report.py"),
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_report.py"),
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.py"),
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.py"),
]
H2_EB_SMOKE_SCRIPTS = [
    Path("tools/codex_smoke_engineering_h2_leak_obstacle_cylinder.sh"),
    Path("tools/codex_smoke_engineering_h2_leak_pipe_rack_obstacle.sh"),
    Path("tools/codex_smoke_engineering_h2_leak_stl_multifile_obstacle.sh"),
    Path("tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh"),
    Path("tools/codex_smoke_engineering_h2_leak_stl_perfile_transform.sh"),
    Path("tools/codex_smoke_engineering_h2_leak_tank_farm_amr_compare.sh"),
    Path("tools/codex_smoke_engineering_h2_leak_tank_farm.sh"),
]
CH4_EVIDENCE_REPORTS = [
    (
        Path(
            "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_cuda_20260806/"
            "engineering_ch4_pipe_rack_delayed_ignition_cuda_report.json"
        ),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA",
    ),
    (
        Path(
            "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_20260806/"
            "engineering_ch4_pipe_rack_delayed_ignition_mpi_report.json"
        ),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-CPU-MPI",
    ),
    (
        Path(
            "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_20260806/"
            "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.json"
        ),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA",
    ),
    (
        Path(
            "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/"
            "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json"
        ),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP",
    ),
]


class LogMarkerCompatibilityError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LogMarkerCompatibilityError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LogMarkerCompatibilityError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LogMarkerCompatibilityError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def build_report() -> dict[str, Any]:
    prob_cpp = PROB_CPP.read_text(encoding="utf-8", errors="replace")
    source_eb_label_generic = "Engineering leak UserDefined EB" in prob_cpp
    source_eb_label_not_h2_specific = "H2 leak UserDefined EB" not in prob_cpp

    ch4_script_results = {}
    for path in CH4_REPORT_SCRIPTS:
        text = path.read_text(encoding="utf-8", errors="replace")
        ch4_script_results[path.name] = {
            "has_compat_helper": "def require_log_marker" in text,
            "accepts_engineering_eb_label": "Engineering leak UserDefined EB" in text,
            "accepts_legacy_h2_eb_label": "H2 leak UserDefined EB" in text,
            "accepts_ch4_delayed_ignition_label": "CH4 delayed ignition source: enabled=1" in text,
            "accepts_legacy_h2_delayed_ignition_label": "H2 delayed ignition source: enabled=1" in text,
        }

    h2_smoke_results = {}
    for path in H2_EB_SMOKE_SCRIPTS:
        text = path.read_text(encoding="utf-8", errors="replace")
        h2_smoke_results[path.name] = {
            "accepts_engineering_eb_label": "Engineering leak UserDefined EB" in text,
            "keeps_legacy_h2_eb_label": "H2 leak UserDefined EB" in text,
        }

    ch4_reports = {}
    for path, expected_status in CH4_EVIDENCE_REPORTS:
        data = load_json(path)
        ch4_reports[str(path)] = data.get("status")
        require(data.get("status") == expected_status, f"CH4 evidence status mismatch: {path}")

    ready = (
        source_eb_label_generic
        and source_eb_label_not_h2_specific
        and all(all(item.values()) for item in ch4_script_results.values())
        and all(all(item.values()) for item in h2_smoke_results.values())
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LOG-MARKER-COMPATIBILITY",
        "summary": {
            "source_eb_label_generic": source_eb_label_generic,
            "source_eb_label_not_h2_specific": source_eb_label_not_h2_specific,
            "ch4_report_script_count": len(CH4_REPORT_SCRIPTS),
            "h2_eb_smoke_script_count": len(H2_EB_SMOKE_SCRIPTS),
            "ch4_reports_reverified": len(CH4_EVIDENCE_REPORTS),
            "log_marker_compatibility_ready": ready,
        },
        "ch4_report_scripts": ch4_script_results,
        "h2_eb_smoke_scripts": h2_smoke_results,
        "ch4_evidence_statuses": ch4_reports,
        "evidence_files": [
            evidence_entry("engineering_leak_prob_cpp", PROB_CPP),
            *[evidence_entry(path.name, path) for path in CH4_REPORT_SCRIPTS],
            *[evidence_entry(path.name, path) for path in H2_EB_SMOKE_SCRIPTS],
            *[evidence_entry(path.name, path) for path, _ in CH4_EVIDENCE_REPORTS],
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("source_eb_label_generic") is True, "source EB label is not generic")
    require(summary.get("source_eb_label_not_h2_specific") is True, "source EB label is still H2-specific")
    require(summary.get("ch4_report_script_count") == 4, "unexpected CH4 report script count")
    require(summary.get("h2_eb_smoke_script_count") == 7, "unexpected H2 EB smoke script count")
    require(summary.get("ch4_reports_reverified") == 4, "unexpected CH4 evidence count")
    require(summary.get("log_marker_compatibility_ready") is True, "log marker compatibility not ready")
    for label, item in data.get("ch4_report_scripts", {}).items():
        require(all(item.values()), f"CH4 report script compatibility incomplete: {label}")
    for label, item in data.get("h2_eb_smoke_scripts", {}).items():
        require(all(item.values()), f"H2 EB smoke script compatibility incomplete: {label}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Log-Marker Compatibility Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Source EB label generic: `{s['source_eb_label_generic']}`",
        f"- Source EB label not H2-specific: `{s['source_eb_label_not_h2_specific']}`",
        f"- CH4 report scripts checked: `{s['ch4_report_script_count']}`",
        f"- H2 EB smoke scripts checked: `{s['h2_eb_smoke_script_count']}`",
        f"- CH4 reports reverified: `{s['ch4_reports_reverified']}`",
        f"- Compatibility ready: `{s['log_marker_compatibility_ready']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{entry['label']}`: `{entry['path']}`" for entry in report["evidence_files"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"engineering_log_marker_compatibility VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_log_marker_compatibility PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (LogMarkerCompatibilityError, OSError, json.JSONDecodeError) as exc:
        print(f"engineering_log_marker_compatibility FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
