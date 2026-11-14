#!/usr/bin/env python3
"""Write/verify bubble-rise long-window probe evidence.

This report formalizes the negative long-window bubble-rise evidence: the
maintained 6000-step gate is stable, while longer source-coupled probes remain
NOT_READY because non-finite or negative-energy states were observed.
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
STATUS_NOT_READY = "NOT_READY-ACADEMIC-TWOPHASE-BUBBLE-RISE-LONG-WINDOW-PROBE-GATE"
DEFAULT_ROOT = Path(
    "docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/"
    "long_window_probe_gate_20260729"
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "bubble_rise_long_window_probe_gate_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "bubble_rise_long_window_probe_gate_report.md"
DEFAULT_MAIN_REPORT = Path(
    "docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/"
    "academic_twophase_bubble_rise_validation_report.json"
)
DEFAULT_ENERGY_PROBE = Path(
    "docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/"
    "energy_stability_probe_20260729/bubble_rise_long_window_energy_probe_report.json"
)
DEFAULT_LONGER_PROBE = Path(
    "docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/"
    "longer_window_probe_20260729/bubble_rise_longer_window_probe_report.json"
)
DEFAULT_ENERGY_CORRECTION_PROBE_ROOT = Path(
    "docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/"
    "energy_correction_probe_20260729"
)
DEFAULT_POSITIVITY_PROBE_REPORT = Path(
    "docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/"
    "positivity_long_window_probe_20260729/bubble_rise_positivity_long_window_probe_report.json"
)


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReportError(f"missing JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f"invalid JSON {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON root is not an object: {path}")
    return data


def finite_number(value: Any, label: str) -> float:
    number = float(value)
    require(math.isfinite(number), f"{label} is not finite: {value!r}")
    return number


def collect_case_evidence(report_path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    base = report_path.parent
    cases = data.get("cases")
    if isinstance(cases, list):
        for idx, case in enumerate(cases):
            if not isinstance(case, dict):
                continue
            for key in ("run_log", "last_plotfile_validation_log"):
                raw = case.get(key)
                if raw:
                    entries.append(evidence_entry(f"{report_path.stem}_case_{idx}_{key}", Path(str(raw))))
            case_dir = base / str(case.get("case", ""))
            input_path = case_dir / "input"
            if input_path.is_file():
                entries.append(evidence_entry(f"{report_path.stem}_case_{idx}_input", input_path))
            backtrace = case_dir / "Backtrace.0"
            if backtrace.is_file():
                entries.append(evidence_entry(f"{report_path.stem}_case_{idx}_backtrace", backtrace))
    else:
        for case_dir in sorted(base.iterdir() if base.is_dir() else []):
            if not case_dir.is_dir():
                continue
            input_path = case_dir / "input"
            tail_path = case_dir / "run_tail.log"
            if input_path.is_file():
                entries.append(evidence_entry(f"{case_dir.name}_input", input_path))
            if tail_path.is_file():
                entries.append(evidence_entry(f"{case_dir.name}_run_tail", tail_path))
    return entries


def collect_energy_correction_evidence(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not root.is_dir():
        return entries
    for case_dir in sorted(root.iterdir()):
        if not case_dir.is_dir():
            continue
        for name in ("build.log", "run.log", "validation.log", "Backtrace.0"):
            path = case_dir / name
            if path.is_file():
                entries.append(evidence_entry(f"energy_correction_{case_dir.name}_{name}", path))
    return entries


def first_failure_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and (
            "FAIL" in stripped
            or "NaNs detected" in stripped
            or "SIGABRT" in stripped
            or "run_rc=" in stripped
        ):
            return stripped
    return ""


def summarize_energy_correction_probe(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        return {
            "root": str(root),
            "present": False,
            "case_count": 0,
            "nan_case_count": 0,
            "finalized_case_count": 0,
            "negative_energy_case_count": 0,
            "all_cases_failed_or_nonphysical": False,
            "cases": [],
        }

    cases: list[dict[str, Any]] = []
    for case_dir in sorted(root.iterdir()):
        if not case_dir.is_dir():
            continue
        run_log = case_dir / "run.log"
        validation_log = case_dir / "validation.log"
        run_text = run_log.read_text(encoding="utf-8", errors="replace") if run_log.is_file() else ""
        validation_text = validation_log.read_text(encoding="utf-8", errors="replace") if validation_log.is_file() else ""
        nan_detected = any(token in run_text for token in ("nan", "NaN", "NAN"))
        finalized = "finalized" in run_text
        negative_energy = "rho_e=-" in validation_text or "rho_E=-" in validation_text or "Temp=-" in validation_text
        validation_passed = " PASS " in validation_text or validation_text.startswith("academic_twophase_bubble_rise_validation PASS")
        cases.append({
            "case": case_dir.name,
            "run_log": str(run_log) if run_log.is_file() else "",
            "validation_log": str(validation_log) if validation_log.is_file() else "",
            "amrex_finalized": finalized,
            "nan_detected": nan_detected,
            "negative_energy_detected": negative_energy,
            "validation_passed": validation_passed,
            "failure_line": first_failure_line(validation_text + "\n" + run_text),
        })

    nan_cases = [case for case in cases if case["nan_detected"]]
    finalized_cases = [case for case in cases if case["amrex_finalized"]]
    negative_cases = [case for case in cases if case["negative_energy_detected"]]
    passing_cases = [case for case in cases if case["validation_passed"]]
    return {
        "root": str(root),
        "present": True,
        "case_count": len(cases),
        "nan_case_count": len(nan_cases),
        "finalized_case_count": len(finalized_cases),
        "negative_energy_case_count": len(negative_cases),
        "passing_case_count": len(passing_cases),
        "all_cases_failed_or_nonphysical": bool(cases) and not passing_cases,
        "diagnosis": (
            "Disabling the second-order buoyancy energy correction is not sufficient: "
            "molecular-transport cases still stopped on NaNs, while inviscid cases finalized "
            "with negative rho_e."
        ),
        "cases": cases,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    main_path = Path(args.main_report)
    energy_path = Path(args.energy_probe_report)
    longer_path = Path(args.longer_probe_report)
    energy_correction_root = Path(args.energy_correction_probe_root)
    positivity_path = Path(args.positivity_probe_report)
    main = load_json(main_path)
    energy = load_json(energy_path)
    longer = load_json(longer_path)
    energy_correction = summarize_energy_correction_probe(energy_correction_root)
    positivity = load_json(positivity_path) if positivity_path.is_file() else {}
    positivity_summary = positivity.get("summary") if isinstance(positivity.get("summary"), dict) else {}

    main_summary = main.get("summary") if isinstance(main.get("summary"), dict) else {}
    energy_summary = energy.get("summary") if isinstance(energy.get("summary"), dict) else {}
    longer_summary = longer.get("summary") if isinstance(longer.get("summary"), dict) else {}

    energy_cases = int(energy_summary.get("case_count", 0))
    stable_formal_steps = int(longer_summary.get("stable_formal_gate_steps", 0))
    nonfinite_step = int(longer_summary.get("nonfinite_boundary_observed_near_step", 0))
    main_short_clear = main_summary.get("clears_qlt_03_short_time_bubble_response_gap") is True
    main_long_clear = main_summary.get("clears_qlt_03_canonical_long_time_bubble_rise_gap") is True
    energy_long_clear = energy_summary.get("long_window_cleared") is True
    longer_long_clear = longer_summary.get("clears_long_physical_time_bubble_rise") is True

    cases = longer.get("summary", {}).get("cases", [])
    failed_long_cases = [
        case for case in cases
        if isinstance(case, dict) and (case.get("run_failed") is True or case.get("nan_stop") is True)
    ]

    gates = [
        {
            "name": "formal_6000_step_gate_remains_stable",
            "status": "PASS" if main.get("status") == "PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION" and main_short_clear else "FAIL",
            "metric": {
                "main_status": main.get("status"),
                "short_time_clear": main_short_clear,
                "centroid_rise": main_summary.get("centroid_rise"),
            },
        },
        {
            "name": "energy_probe_cases_are_attached",
            "status": "PASS" if energy_cases >= 10 else "FAIL",
            "metric": {"case_count": energy_cases, "energy_status": energy.get("status")},
        },
        {
            "name": "longer_window_failure_boundary_is_reproducible",
            "status": "PASS" if stable_formal_steps >= 6000 and nonfinite_step > stable_formal_steps else "FAIL",
            "metric": {
                "stable_formal_gate_steps": stable_formal_steps,
                "nonfinite_boundary_observed_near_step": nonfinite_step,
            },
        },
        {
            "name": "long_window_credit_remains_blocked",
            "status": "PASS" if not main_long_clear and not energy_long_clear and not longer_long_clear else "FAIL",
            "metric": {
                "main_long_clear": main_long_clear,
                "energy_long_clear": energy_long_clear,
                "longer_long_clear": longer_long_clear,
            },
        },
        {
            "name": "long_window_cases_include_failure_diagnostics",
            "status": "PASS" if failed_long_cases else "FAIL",
            "metric": {"failed_long_case_count": len(failed_long_cases)},
        },
        {
            "name": "energy_correction_probe_confirms_issue_is_not_single_switch",
            "status": "PASS" if (
                energy_correction["case_count"] >= 4
                and energy_correction["all_cases_failed_or_nonphysical"] is True
                and energy_correction["nan_case_count"] >= 1
                and energy_correction["negative_energy_case_count"] >= 1
            ) else "FAIL",
            "metric": {
                "case_count": energy_correction["case_count"],
                "nan_case_count": energy_correction["nan_case_count"],
                "negative_energy_case_count": energy_correction["negative_energy_case_count"],
                "passing_case_count": energy_correction["passing_case_count"],
            },
        },
        {
            "name": "positivity_probe_records_remaining_motion_gap",
            "status": "PASS" if (
                int(positivity_summary.get("case_count", 0)) >= 10
                and positivity_summary.get("clears_canonical_long_window_bubble_rise") is False
            ) else "FAIL",
            "metric": {
                "case_count": positivity_summary.get("case_count", 0),
                "passing_case_count": positivity_summary.get("passing_case_count", 0),
                "clears_canonical_long_window_bubble_rise": positivity_summary.get("clears_canonical_long_window_bubble_rise"),
            },
        },
    ]
    failed = [gate["name"] for gate in gates if gate["status"] == "FAIL"]
    require(not failed, f"failed gates while building NOT_READY probe report: {failed}")

    evidence_files = [
        evidence_entry("report_writer", Path("tools/write_academic_twophase_bubble_rise_long_window_probe_report.py")),
        evidence_entry("energy_stability_probe_report", energy_path),
        evidence_entry("longer_window_probe_report", longer_path),
    ]
    if positivity_path.is_file():
        evidence_files.append(evidence_entry("positivity_long_window_probe_report", positivity_path))
    evidence_files.extend(collect_case_evidence(energy_path, energy))
    evidence_files.extend(collect_case_evidence(longer_path, longer))
    evidence_files.extend(collect_energy_correction_evidence(energy_correction_root))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_NOT_READY,
        "title": "Academic Two-Phase Bubble-Rise Long-Window Probe Gate",
        "scope": (
            "Formal NOT_READY evidence for canonical long-window bubble-rise validation: "
            "the maintained 6000-step buoyancy-response gate passes, while longer source-coupled "
            "probe variants retain non-finite/negative-energy failure diagnostics."
        ),
        "summary": {
            "main_short_time_bubble_rise_report": str(main_path),
            "formal_short_time_gate_status": main.get("status"),
            "formal_short_time_gate_cleared": main_short_clear,
            "formal_centroid_rise": finite_number(main_summary.get("centroid_rise", 0.0), "centroid_rise"),
            "energy_probe_status": energy.get("status"),
            "energy_probe_case_count": energy_cases,
            "energy_probe_diagnosis": energy_summary.get("diagnosis"),
            "longer_window_probe_status": longer.get("status"),
            "stable_formal_gate_steps": stable_formal_steps,
            "nonfinite_boundary_observed_near_step": nonfinite_step,
            "failed_long_case_count": len(failed_long_cases),
            "energy_correction_probe_root": str(energy_correction_root),
            "energy_correction_probe_case_count": energy_correction["case_count"],
            "energy_correction_probe_nan_case_count": energy_correction["nan_case_count"],
            "energy_correction_probe_negative_energy_case_count": energy_correction["negative_energy_case_count"],
            "energy_correction_probe_passing_case_count": energy_correction["passing_case_count"],
            "energy_correction_probe_diagnosis": energy_correction.get("diagnosis", ""),
            "positivity_probe_status": positivity.get("status"),
            "positivity_probe_case_count": positivity_summary.get("case_count", 0),
            "positivity_probe_passing_case_count": positivity_summary.get("passing_case_count", 0),
            "positivity_probe_diagnosis": positivity_summary.get("diagnosis", ""),
            "clears_qlt_03_short_time_bubble_response_gap": main_short_clear,
            "clears_qlt_03_canonical_long_time_bubble_rise_gap": False,
            "clears_qlt_03_bubble_rise_gap": False,
        },
        "energy_correction_probe": energy_correction,
        "quality_gates": gates,
        "evidence_files": evidence_files,
        "limitations": [
            "This is a formal negative-evidence gate: it preserves the short-time PASS while making long-window NOT_READY reproducible.",
            "It does not attempt to repair the long-window instability; it prevents accidental broad QLT-03 credit until a stable long-window physical case exists.",
            "Future work should replace this NOT_READY gate with a positive canonical bubble-rise benchmark once the non-finite/negative-energy failure mode is resolved.",
        ],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS_NOT_READY, "status must remain NOT_READY")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("formal_short_time_gate_cleared") is True, "short-time gate must remain clear")
    require(summary.get("clears_qlt_03_canonical_long_time_bubble_rise_gap") is False, "long-time gap must not clear")
    require(summary.get("clears_qlt_03_bubble_rise_gap") is False, "broad bubble-rise gap must not clear")
    require(int(summary.get("energy_probe_case_count", 0)) >= 10, "energy probe case count too small")
    require(int(summary.get("stable_formal_gate_steps", 0)) >= 6000, "formal stable gate steps too small")
    require(
        int(summary.get("nonfinite_boundary_observed_near_step", 0)) > int(summary.get("stable_formal_gate_steps", 0)),
        "non-finite boundary step must be beyond the stable formal gate",
    )
    require(int(summary.get("energy_correction_probe_case_count", 0)) >= 4, "energy correction probe case count too small")
    require(
        int(summary.get("energy_correction_probe_nan_case_count", 0)) >= 1,
        "energy correction probe must include at least one NaN failure",
    )
    require(
        int(summary.get("energy_correction_probe_negative_energy_case_count", 0)) >= 1,
        "energy correction probe must include at least one negative-energy failure",
    )
    require(
        int(summary.get("energy_correction_probe_passing_case_count", 1)) == 0,
        "energy correction probe must not claim a passing long-window case",
    )
    require(int(summary.get("positivity_probe_case_count", 0)) >= 10, "positivity probe case count too small")
    require(
        data.get("summary", {}).get("clears_qlt_03_canonical_long_time_bubble_rise_gap") is False,
        "positivity probe must not clear canonical long-time bubble-rise",
    )
    gates = data.get("quality_gates")
    require(isinstance(gates, list) and gates, "quality_gates missing")
    failed = [gate.get("name") for gate in gates if isinstance(gate, dict) and gate.get("status") == "FAIL"]
    require(not failed, f"failed gates: {failed}")
    entries = data.get("evidence_files")
    require(isinstance(entries, list) and entries, "evidence_files missing")
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), "evidence entry is not object")
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Academic Two-Phase Bubble-Rise Long-Window Probe Gate",
        "",
        f"Status: `{report['status']}`",
        "",
        "Key metrics:",
        f"- formal short-time gate status: `{s['formal_short_time_gate_status']}`",
        f"- formal centroid rise: `{s['formal_centroid_rise']:.12e}`",
        f"- energy probe cases: `{s['energy_probe_case_count']}`",
        f"- stable formal gate steps: `{s['stable_formal_gate_steps']}`",
        f"- non-finite boundary observed near step: `{s['nonfinite_boundary_observed_near_step']}`",
        f"- failed long-window case count: `{s['failed_long_case_count']}`",
        f"- energy-correction probe cases: `{s['energy_correction_probe_case_count']}`",
        f"- energy-correction NaN cases: `{s['energy_correction_probe_nan_case_count']}`",
        f"- energy-correction negative-energy cases: `{s['energy_correction_probe_negative_energy_case_count']}`",
        f"- energy-correction passing cases: `{s['energy_correction_probe_passing_case_count']}`",
        f"- positivity probe cases: `{s['positivity_probe_case_count']}`",
        f"- positivity probe passing cases: `{s['positivity_probe_passing_case_count']}`",
        "",
        "Energy-correction probe diagnosis:",
        f"- {s['energy_correction_probe_diagnosis']}",
        "",
        "Positivity probe diagnosis:",
        f"- {s['positivity_probe_diagnosis']}",
        "",
        "Readiness:",
        f"- short-time bubble response: `{s['clears_qlt_03_short_time_bubble_response_gap']}`",
        f"- canonical long-time bubble rise: `{s['clears_qlt_03_canonical_long_time_bubble_rise_gap']}`",
        f"- broad bubble-rise QLT-03 gap: `{s['clears_qlt_03_bubble_rise_gap']}`",
        "",
        "Quality gates:",
        "",
        "| Gate | Status | Metric |",
        "| --- | --- | --- |",
    ]
    for gate in report["quality_gates"]:
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | `{json.dumps(gate['metric'], sort_keys=True)}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-report", default=str(DEFAULT_MAIN_REPORT))
    parser.add_argument("--energy-probe-report", default=str(DEFAULT_ENERGY_PROBE))
    parser.add_argument("--longer-probe-report", default=str(DEFAULT_LONGER_PROBE))
    parser.add_argument("--energy-correction-probe-root", default=str(DEFAULT_ENERGY_CORRECTION_PROBE_ROOT))
    parser.add_argument("--positivity-probe-report", default=str(DEFAULT_POSITIVITY_PROBE_REPORT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report_object(data, check_hashes=True)
            print(f"academic_twophase_bubble_rise_long_window_probe VERIFY-PASS json={args.verify_json}")
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        validate_report_object(report, check_hashes=False)
        print(f"academic_twophase_bubble_rise_long_window_probe PASS json={out_json} md={out_md}")
        return 0
    except ReportError as exc:
        print(f"academic_twophase_bubble_rise_long_window_probe FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
