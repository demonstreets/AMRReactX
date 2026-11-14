#!/usr/bin/env python3
"""Write/verify the canonical bubble-rise reference preflight report."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_NOT_READY = "NOT_READY-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-REFERENCE"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_reference_20260729")
DEFAULT_JSON = DEFAULT_ROOT / "academic_twophase_canonical_bubble_rise_reference_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_twophase_canonical_bubble_rise_reference_report.md"
DEFAULT_BUBBLE_REPORT = Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json")
DEFAULT_OBSERVABLES_REPORT = Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_observable_timeseries_20260729/academic_twophase_bubble_rise_observable_timeseries_report.json")
DEFAULT_CANONICAL_CANDIDATE_REPORT = Path("docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_candidate_20260730/canonical_bubble_rise_candidate_report.json")


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
    return {"label": label, "path": str(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing JSON evidence: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON root is not an object: {path}")
    return data


def parse_inputs(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        lhs, rhs = line.split("=", 1)
        values[lhs.strip()] = rhs.strip().strip('"')
    return values


def floats(values: dict[str, str], key: str) -> list[float]:
    raw = values.get(key)
    require(raw is not None, f"missing input key: {key}")
    out = []
    for token in raw.replace('"', '').split():
        try:
            out.append(float(token))
        except ValueError as exc:
            raise ReportError(f"cannot parse float token {token!r} in {key}") from exc
    return out


def one_float(values: dict[str, str], key: str) -> float:
    vals = floats(values, key)
    require(vals, f"missing numeric value for {key}")
    return vals[0]


def rel_close(value: float, target: float, tol: float) -> bool:
    return abs(value - target) <= tol * max(abs(target), 1.0e-300)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    bubble_report_path = Path(args.bubble_report)
    observables_report_path = Path(args.observables_report)
    candidate_report_path = Path(args.canonical_candidate_report)
    bubble_report = load_json(bubble_report_path)
    observables_report = load_json(observables_report_path) if observables_report_path.is_file() else {}
    candidate_report = load_json(candidate_report_path) if candidate_report_path.is_file() else {}
    observables_summary = observables_report.get("summary") if isinstance(observables_report.get("summary"), dict) else {}
    candidate_summary = candidate_report.get("summary") if isinstance(candidate_report.get("summary"), dict) else {}
    case = bubble_report.get("case", {})
    contract_source = "bubble_rise_validation"
    if candidate_summary.get("clears_canonical_geometry_gravity_case_package") is True:
        candidate_case = candidate_report.get("case", {})
        if isinstance(candidate_case, dict) and candidate_case.get("input_file"):
            case = candidate_case
            contract_source = "canonical_geometry_gravity_candidate"
    require(isinstance(case, dict), "bubble/candidate report case missing")
    input_file = Path(str(case.get("input_file", "")))
    values = parse_inputs(input_file)
    lo = floats(values, "geometry.prob_lo")[:2]
    hi = floats(values, "geometry.prob_hi")[:2]
    ncell = [int(float(x)) for x in floats(values, "amr.n_cell")[:2]]
    width = hi[0] - lo[0]
    height = hi[1] - lo[1]
    radius = one_float(values, "prob.bubble_r")
    cx = one_float(values, "prob.bubble_cx")
    cy = one_float(values, "prob.bubble_cy")
    rho_heavy = one_float(values, "prob.rho_heavy")
    rho_light = one_float(values, "prob.rho_light")
    gravity = one_float(values, "prob.buoyancy_accel")
    stop_time = one_float(values, "stop_time")
    plot_int = one_float(values, "amr.plot_int")
    surface_tension_keys = [key for key in values if "sigma" in key.lower() or "surface" in key.lower()]
    viscosity_keys = [key for key in values if "visc" in key.lower() or "mu" in key.lower()]
    derived = {
        "domain_width": width,
        "domain_height": height,
        "domain_aspect_height_over_width": height / width,
        "bubble_radius_over_domain_width": radius / width,
        "bubble_center_over_domain": [cx / width, cy / height],
        "density_ratio_heavy_over_light": rho_heavy / rho_light,
        "grid": ncell,
        "stop_time": stop_time,
        "plot_int": plot_int,
        "gravity": gravity,
        "surface_tension_keys": surface_tension_keys,
        "viscosity_keys": viscosity_keys,
    }
    reference = {
        "name": "Hysing-Turek-Kuzmin-Parolini-Burman-Ganesan-Tobiska 2D rising bubble benchmark",
        "primary_doi": "10.1002/fld.1934",
        "primary_url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/fld.1934",
        "benchmark_quantities": ["center_of_mass", "mean_rise_velocity", "circularity"],
        "case_1_contract": {
            "domain": [1.0, 2.0],
            "initial_bubble_center": [0.5, 0.5],
            "initial_bubble_radius": 0.25,
            "rho_liquid": 1000.0,
            "rho_bubble": 100.0,
            "mu_liquid": 10.0,
            "mu_bubble": 1.0,
            "gravity": 0.98,
            "surface_tension": 24.5,
            "end_time": 3.0,
            "representative_reference_values": {
                "minimum_circularity": 0.9013,
                "time_at_minimum_circularity": 1.90,
                "maximum_mean_rise_velocity": 0.2417,
                "time_at_maximum_mean_rise_velocity": 0.92,
                "center_of_mass_y_at_t3": 1.0813,
            },
        },
    }
    checks = [
        {
            "name": "domain_aspect_ratio_matches_1x2_column",
            "status": "PASS" if rel_close(derived["domain_aspect_height_over_width"], 2.0, 1.0e-12) else "NOT_READY",
            "metric": derived["domain_aspect_height_over_width"],
            "target": 2.0,
        },
        {
            "name": "initial_bubble_radius_matches_canonical_fraction",
            "status": "PASS" if rel_close(derived["bubble_radius_over_domain_width"], 0.25, 1.0e-6) else "NOT_READY",
            "metric": derived["bubble_radius_over_domain_width"],
            "target": 0.25,
        },
        {
            "name": "initial_bubble_center_matches_canonical_fraction",
            "status": "PASS" if rel_close(derived["bubble_center_over_domain"][0], 0.5, 1.0e-6) and rel_close(derived["bubble_center_over_domain"][1], 0.25, 1.0e-6) else "NOT_READY",
            "metric": derived["bubble_center_over_domain"],
            "target": [0.5, 0.25],
        },
        {
            "name": "density_ratio_matches_hysing_case_1",
            "status": "PASS" if rel_close(derived["density_ratio_heavy_over_light"], 10.0, 1.0e-12) else "NOT_READY",
            "metric": derived["density_ratio_heavy_over_light"],
            "target": 10.0,
        },
        {
            "name": "gravity_matches_hysing_case_1_scale",
            "status": "PASS" if rel_close(gravity, 0.98, 1.0e-3) else "NOT_READY",
            "metric": gravity,
            "target": 0.98,
        },
        {
            "name": "surface_tension_contract_present",
            "status": "PASS" if surface_tension_keys else "NOT_READY",
            "metric": surface_tension_keys,
            "target": "surface tension parameter equivalent to sigma=24.5",
        },
        {
            "name": "viscosity_contract_present",
            "status": "PASS" if viscosity_keys else "NOT_READY",
            "metric": viscosity_keys,
            "target": "liquid/bubble viscosity equivalent to 10/1",
        },
        {
            "name": "canonical_observable_timeseries_available",
            "status": "PASS" if observables_summary.get("clears_canonical_observable_timeseries_gap") is True else "NOT_READY",
            "metric": {
                "observables_report_status": observables_report.get("status"),
                "plot_count": observables_summary.get("plot_count"),
                "has_center_of_mass": observables_summary.get("center_of_mass_y0") is not None,
                "has_rise_velocity": observables_summary.get("max_finite_difference_rise_velocity_y") is not None,
                "has_circularity": observables_summary.get("min_circularity_estimate") is not None,
                "clears_canonical_observable_timeseries_gap": observables_summary.get("clears_canonical_observable_timeseries_gap"),
            },
            "target": {"benchmark_quantities": reference["benchmark_quantities"], "minimum_time_samples": 16},
        },
        {
            "name": "canonical_final_time_contract",
            "status": "PASS" if stop_time >= 3.0 else "NOT_READY",
            "metric": stop_time,
            "target": 3.0,
        },
    ]
    blocking = [item["name"] for item in checks if item["status"] != "PASS"]
    summary = {
        "clears_qlt_03_canonical_long_time_bubble_rise_gap": False,
        "ready_to_run_canonical_benchmark": False,
        "blocking_gap_count": len(blocking),
        "blocking_gaps": blocking,
        "contract_source": contract_source,
        "current_case_derived_contract": derived,
        "canonical_candidate_summary": candidate_summary,
        "next_required_outputs": reference["benchmark_quantities"],
        "recommended_next_case": {
            "domain": [1.0, 2.0],
            "bubble_center": [0.5, 0.5],
            "bubble_radius": 0.25,
            "density_ratio": 10.0,
            "gravity": 0.98,
            "surface_tension": 24.5,
            "end_time": 3.0,
            "required_history": ["center_of_mass_y(t)", "mean_rise_velocity_y(t)", "circularity(t)", "final_interface_shape"],
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_NOT_READY,
        "title": "Academic Two-Phase Canonical Bubble-Rise Reference Preflight",
        "scope": "Machine-checkable comparison between the maintained PeleC bubble-rise evidence and the canonical Hysing et al. 2D rising-bubble benchmark contract.",
        "reference": reference,
        "summary": summary,
        "quality_gates": checks,
        "limitations": [
            "This report intentionally does not promote the current short-time/long-window PeleC bubble response gates into canonical external-reference validation.",
            "The maintained PeleC case has clean response/stability evidence and sampled observable diagnostics where available, but its current geometry, forcing scale, surface-tension/viscosity contract, and final time do not yet match the Hysing benchmark.",
            "Clearing QLT-03 canonical credit requires a dedicated case package plus center-of-mass, rise-velocity, circularity, and final-shape comparisons against the reference contract recorded here.",
        ],
        "source_reports": {"bubble_rise_validation": str(bubble_report_path), "bubble_rise_observables": str(observables_report_path), "canonical_candidate": str(candidate_report_path)},
        "evidence_files": [
            evidence_entry("report_writer", Path("tools/write_academic_twophase_canonical_bubble_rise_reference_report.py")),
            evidence_entry("bubble_rise_validation_report", bubble_report_path),
            evidence_entry("bubble_rise_observables_report", observables_report_path),
            *([evidence_entry("canonical_bubble_candidate_report", candidate_report_path)] if candidate_report_path.is_file() else []),
            evidence_entry("bubble_rise_input_file", input_file),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_NOT_READY, "unexpected status")
    summary = report.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("clears_qlt_03_canonical_long_time_bubble_rise_gap") is False, "canonical gap must remain open")
    require(int(summary.get("blocking_gap_count", 0)) > 0, "blocking gaps must be explicit")
    gates = report.get("quality_gates")
    require(isinstance(gates, list) and gates, "quality gates missing")
    statuses = {gate.get("name"): gate.get("status") for gate in gates}
    require(statuses.get("domain_aspect_ratio_matches_1x2_column") == "PASS", "domain aspect should be recognized")
    require(statuses.get("density_ratio_matches_hysing_case_1") == "PASS", "density ratio should be recognized")
    require(statuses.get("canonical_observable_timeseries_available") in {"PASS", "NOT_READY"}, "observable history gate missing")
    if check_hashes:
        for item in report.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def write_md(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Academic Two-Phase Canonical Bubble-Rise Reference Preflight",
        "",
        f"Status: `{report['status']}`",
        "",
        "Reference:",
        f"- `{report['reference']['name']}`",
        f"- DOI: `{report['reference']['primary_doi']}`",
        "",
        "Blocking gaps:",
    ]
    for gap in s["blocking_gaps"]:
        lines.append(f"- `{gap}`")
    lines.extend(["", "Quality gates:", "", "| Gate | Status | Metric | Target |", "| --- | --- | --- | --- |"])
    for gate in report["quality_gates"]:
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | `{json.dumps(gate['metric'], sort_keys=True)}` | `{json.dumps(gate['target'], sort_keys=True)}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bubble-report", default=str(DEFAULT_BUBBLE_REPORT))
    parser.add_argument("--observables-report", default=str(DEFAULT_OBSERVABLES_REPORT))
    parser.add_argument("--canonical-candidate-report", default=str(DEFAULT_CANONICAL_CANDIDATE_REPORT))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(report, check_hashes=True)
            print(f"academic_twophase_canonical_bubble_rise_reference VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        report = build_report(args)
        validate_report(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_md(report, out_md)
        print(f"academic_twophase_canonical_bubble_rise_reference PASS json={out_json} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"academic_twophase_canonical_bubble_rise_reference FAIL {exc}", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
