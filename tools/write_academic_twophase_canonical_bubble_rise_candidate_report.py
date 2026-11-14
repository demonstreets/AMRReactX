#!/usr/bin/env python3
"""Write/verify canonical bubble-rise geometry/gravity candidate evidence."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-CANDIDATE"
STATUS_NOT_READY = "NOT_READY-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-CANDIDATE"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_candidate_20260730")
DEFAULT_CASE_SUMMARY = DEFAULT_ROOT / "canonical_bubble_rise_geometry_gravity_csf_viscosity_1000step_smoke" / "case_summary.json"
DEFAULT_JSON = DEFAULT_ROOT / "canonical_bubble_rise_candidate_report.json"
DEFAULT_MD = DEFAULT_ROOT / "canonical_bubble_rise_candidate_report.md"
METRIC_RE = re.compile(r"^academic_twophase_bubble_rise_validation PASS\s+(.*)$", re.MULTILINE)


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
    require(path.is_file(), f"missing JSON: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON root is not an object: {path}")
    return data


def parse_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in text.split():
        if "=" in item:
            key, value = item.split("=", 1)
            values[key] = value.rstrip(",")
    return values


def parse_validation_log(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing validation log: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    match = METRIC_RE.search(text)
    require(match is not None, f"validation PASS line missing in {path}")
    raw = parse_values(match.group(1))
    nx, ny = [int(item) for item in raw["grid"].split("x", 1)]
    return {
        "time0": float(raw["time0"]),
        "time1": float(raw["time1"]),
        "grid_nx": nx,
        "grid_ny": ny,
        "mass_rel_drift": float(raw["mass_rel_drift"]),
        "adv_mass_rel_drift": float(raw["adv_mass_rel_drift"]),
        "light_y0": float(raw["light_y0"]),
        "light_y1": float(raw["light_y1"]),
        "centroid_rise": float(raw["centroid_rise"]),
        "ymom_sum": float(raw["ymom_sum"]),
        "ymom_absmax": float(raw["ymom_absmax"]),
    }


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
    return [float(item) for item in raw.replace('"', "").split()]


def one_float(values: dict[str, str], key: str) -> float:
    vals = floats(values, key)
    require(vals, f"missing numeric value for {key}")
    return vals[0]


def close(value: float, target: float, tol: float = 1.0e-12) -> bool:
    return abs(value - target) <= tol * max(abs(target), 1.0e-300)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case_summary_path = Path(args.case_summary)
    case = load_json(case_summary_path)
    input_file = Path(str(case["input_file"]))
    build_log = Path(str(case["build_log"]))
    run_log = Path(str(case["run_log"]))
    validation_log = Path(str(case["validation_log"]))
    initial_plot = Path(str(case["initial_plot"]))
    final_plot = Path(str(case["final_plot"]))
    for path in (input_file, build_log, run_log, validation_log):
        require(path.is_file(), f"missing evidence file: {path}")
    run_text = run_log.read_text(encoding="utf-8", errors="replace")
    blocking: list[str] = []
    if int(case.get("run_returncode", 1)) != 0:
        blocking.append("canonical_candidate_run_failed")
    if int(case.get("validation_returncode", 1)) != 0:
        blocking.append("canonical_candidate_validation_failed")
    if "AMReX" not in run_text or "finalized" not in run_text:
        blocking.append("amrex_finalization_missing")
    if any(token in run_text for token in ("nan", "NaN", "NAN", "SIGSEGV", "SIGABRT", "Abort::")):
        blocking.append("failure_token_in_run_log")
    metrics: dict[str, Any] = {}
    if not blocking:
        require(initial_plot.is_dir(), f"missing initial plotfile directory: {initial_plot}")
        require(final_plot.is_dir(), f"missing final plotfile directory: {final_plot}")
        metrics = parse_validation_log(validation_log)
    values = parse_inputs(input_file)
    lo = floats(values, "geometry.prob_lo")[:2]
    hi = floats(values, "geometry.prob_hi")[:2]
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
    surface_tension_sigma = one_float(values, "prob.surface_tension_sigma") if "prob.surface_tension_sigma" in values else 0.0
    mu_heavy = one_float(values, "prob.phase_viscosity_mu_heavy") if "prob.phase_viscosity_mu_heavy" in values else 0.0
    mu_light = one_float(values, "prob.phase_viscosity_mu_light") if "prob.phase_viscosity_mu_light" in values else 0.0
    phase_viscosity_force_cap = one_float(values, "prob.phase_viscosity_force_cap") if "prob.phase_viscosity_force_cap" in values else -1.0
    derived = {
        "domain_width": width,
        "domain_height": height,
        "domain_aspect_height_over_width": height / width,
        "bubble_radius_over_domain_width": radius / width,
        "bubble_center_over_domain": [cx / width, cy / height],
        "density_ratio_heavy_over_light": rho_heavy / rho_light,
        "gravity": gravity,
        "stop_time": stop_time,
        "plot_int": plot_int,
        "surface_tension_sigma": surface_tension_sigma,
        "phase_viscosity_mu_heavy": mu_heavy,
        "phase_viscosity_mu_light": mu_light,
        "phase_viscosity_force_cap": phase_viscosity_force_cap,
    }
    viscosity_contract_pass = close(mu_heavy, 10.0, 1.0e-12) and close(mu_light, 1.0, 1.0e-12) and phase_viscosity_force_cap > 0.0
    gates = [
        {"name": "candidate_smoke_run_finalized", "status": "PASS" if not blocking else "NOT_READY", "metric": blocking},
        {"name": "domain_matches_hysing_1x2", "status": "PASS" if close(width, 1.0) and close(height, 2.0) else "NOT_READY", "metric": [width, height], "target": [1.0, 2.0]},
        {"name": "bubble_radius_fraction_matches_hysing", "status": "PASS" if close(radius / width, 0.25, 1.0e-12) else "NOT_READY", "metric": radius / width, "target": 0.25},
        {"name": "bubble_center_matches_hysing", "status": "PASS" if close(cx / width, 0.5) and close(cy / height, 0.25) else "NOT_READY", "metric": [cx / width, cy / height], "target": [0.5, 0.25]},
        {"name": "density_ratio_matches_hysing_case_1", "status": "PASS" if close(rho_heavy / rho_light, 10.0) else "NOT_READY", "metric": rho_heavy / rho_light, "target": 10.0},
        {"name": "gravity_matches_hysing_case_1", "status": "PASS" if close(gravity, 0.98, 1.0e-12) else "NOT_READY", "metric": gravity, "target": 0.98},
        {"name": "candidate_short_time_smoke_not_canonical_final_time", "status": "PASS", "metric": stop_time, "target": "short smoke only; canonical target t=3.0 remains open"},
        {"name": "surface_tension_model_contract", "status": "PASS" if close(surface_tension_sigma, 24.5, 1.0e-12) else "NOT_READY", "metric": surface_tension_sigma, "target": 24.5},
        {"name": "phase_viscosity_model_contract", "status": "PASS" if viscosity_contract_pass else "NOT_READY", "metric": {"mu_heavy": mu_heavy, "mu_light": mu_light, "force_cap": phase_viscosity_force_cap}, "target": "phase viscosity model equivalent to mu_liquid/mu_bubble=10/1 with capped explicit smoke source"},
    ]
    status = STATUS_PASS if not blocking and all(g["status"] == "PASS" for g in gates[:7]) else STATUS_NOT_READY
    summary = {
        "clears_canonical_geometry_gravity_case_package": status == STATUS_PASS,
        "clears_qlt_03_canonical_long_time_bubble_rise_gap": False,
        "ready_for_surface_tension_viscosity_model_work": status == STATUS_PASS,
        "remaining_canonical_model_gaps": ["canonical_final_time_contract"] if close(surface_tension_sigma, 24.5, 1.0e-12) and viscosity_contract_pass else ["surface_tension_model_contract", "phase_viscosity_model_contract", "canonical_final_time_contract"],
        "derived_contract": derived,
        "blocking_reasons": blocking,
        **metrics,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "title": "Academic Two-Phase Canonical Bubble-Rise Geometry/Gravity Candidate",
        "scope": "Short PeleC smoke case that aligns Hysing-style domain, initial bubble geometry, density ratio, gravity scale, an explicit capped CSF surface-tension source, and an explicit capped phase-viscosity source without claiming t=3 benchmark completion.",
        "case": case,
        "summary": summary,
        "quality_gates": gates,
        "limitations": [
            "This is a geometry/gravity plus capped-CSF and capped phase-viscosity candidate smoke, not a full Hysing benchmark validation.",
            "The current PeleC problem now has explicit sigma=24.5 and mu_heavy/mu_light=10/1 smoke controls, but the implementation remains a capped explicit source path rather than a calibrated production VOF viscous stress discretization.",
            "The run intentionally stops at a short smoke time; canonical t=3 comparison remains open.",
        ],
        "evidence_files": [
            evidence_entry("case_summary", case_summary_path),
            evidence_entry("input_file", input_file),
            evidence_entry("build_log", build_log),
            evidence_entry("run_log", run_log),
            evidence_entry("validation_log", validation_log),
            evidence_entry("runner", Path("tools/codex_run_academic_twophase_canonical_bubble_rise_candidate.sh")),
            evidence_entry("validator", Path("tools/validate_academic_twophase_bubble_rise.py")),
            evidence_entry("report_writer", Path("tools/write_academic_twophase_canonical_bubble_rise_candidate_report.py")),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "unexpected status")
    summary = report.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("clears_canonical_geometry_gravity_case_package") is True, "geometry/gravity package not cleared")
    require(summary.get("clears_qlt_03_canonical_long_time_bubble_rise_gap") is False, "full canonical gap must remain open")
    statuses = {g.get("name"): g.get("status") for g in report.get("quality_gates", [])}
    for name in ("domain_matches_hysing_1x2", "bubble_radius_fraction_matches_hysing", "gravity_matches_hysing_case_1"):
        require(statuses.get(name) == "PASS", f"{name} did not pass")
    require(statuses.get("surface_tension_model_contract") == "PASS", "surface tension contract should pass for this candidate")
    require(statuses.get("phase_viscosity_model_contract") == "PASS", "phase viscosity contract should pass for this candidate")
    if check_hashes:
        for item in report.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def write_md(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Academic Two-Phase Canonical Bubble-Rise Geometry/Gravity Candidate",
        "",
        f"Status: `{report['status']}`",
        "",
        "Quality gates:",
        "",
        "| Gate | Status | Metric |",
        "| --- | --- | --- |",
    ]
    for gate in report["quality_gates"]:
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | `{json.dumps(gate.get('metric'), sort_keys=True)}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-summary", default=str(DEFAULT_CASE_SUMMARY))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            report = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(report, check_hashes=True)
            print(f"academic_twophase_canonical_bubble_rise_candidate VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        report = build_report(args)
        validate_report(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_md(report, out_md)
        print(f"academic_twophase_canonical_bubble_rise_candidate PASS json={out_json} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"academic_twophase_canonical_bubble_rise_candidate FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
