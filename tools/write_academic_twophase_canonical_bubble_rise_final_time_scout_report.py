#!/usr/bin/env python3
"""Write/verify canonical bubble-rise final-time scout evidence."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-FINAL-TIME-SCOUT"
STATUS_NOT_READY = "NOT_READY-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-FINAL-TIME-SCOUT"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_final_time_scout_20260730")
DEFAULT_CASE_SUMMARY = DEFAULT_ROOT / "canonical_bubble_rise_csf_viscosity_5000step_final_time_scout" / "case_summary.json"
DEFAULT_JSON = DEFAULT_ROOT / "canonical_bubble_rise_final_time_scout_report.json"
DEFAULT_MD = DEFAULT_ROOT / "canonical_bubble_rise_final_time_scout_report.md"
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
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


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
        blocking.append("final_time_scout_run_failed")
    if int(case.get("validation_returncode", 1)) != 0:
        blocking.append("final_time_scout_validation_failed")
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
    target_stop_time = one_float(values, "stop_time")
    max_step = int(one_float(values, "max_step"))
    plot_int = int(one_float(values, "amr.plot_int"))
    surface_tension_sigma = one_float(values, "prob.surface_tension_sigma")
    mu_heavy = one_float(values, "prob.phase_viscosity_mu_heavy")
    mu_light = one_float(values, "prob.phase_viscosity_mu_light")
    wall_seconds = max(float(case.get("wall_seconds", 0.0)), 0.0)
    time1 = float(metrics.get("time1", 0.0))
    avg_dt = time1 / max_step if max_step > 0 else 0.0
    estimated_steps_to_t3 = math.inf if avg_dt <= 0.0 else math.ceil(3.0 / avg_dt)
    estimated_wall_seconds_to_t3 = (
        math.inf if max_step <= 0 or wall_seconds <= 0.0 else wall_seconds * estimated_steps_to_t3 / max_step
    )
    derived = {
        "domain_width": width,
        "domain_height": height,
        "domain_aspect_height_over_width": height / width,
        "bubble_radius_over_domain_width": radius / width,
        "bubble_center_over_domain": [cx / width, cy / height],
        "density_ratio_heavy_over_light": rho_heavy / rho_light,
        "gravity": gravity,
        "target_stop_time": target_stop_time,
        "max_step": max_step,
        "plot_int": plot_int,
        "surface_tension_sigma": surface_tension_sigma,
        "phase_viscosity_mu_heavy": mu_heavy,
        "phase_viscosity_mu_light": mu_light,
        "average_physical_dt": avg_dt,
        "estimated_steps_to_t3_at_scout_dt": estimated_steps_to_t3,
        "estimated_wall_seconds_to_t3_at_scout_rate": estimated_wall_seconds_to_t3,
    }
    final_time_reached = time1 >= 3.0
    stable_window = not blocking and time1 >= 5.0e-5
    gates = [
        {"name": "final_time_scout_run_finalized", "status": "PASS" if not blocking else "NOT_READY", "metric": blocking},
        {"name": "long_window_stability_probe", "status": "PASS" if stable_window else "NOT_READY", "metric": {"time1": time1, "mass_rel_drift": metrics.get("mass_rel_drift"), "adv_mass_rel_drift": metrics.get("adv_mass_rel_drift")}, "target": "stable >=5e-5 physical time with mass drifts <=1e-10"},
        {"name": "canonical_contract_inputs_retained", "status": "PASS" if close(width, 1.0) and close(height, 2.0) and close(radius / width, 0.25) and close(rho_heavy / rho_light, 10.0) and close(gravity, 0.98) and close(surface_tension_sigma, 24.5) and close(mu_heavy, 10.0) and close(mu_light, 1.0) else "NOT_READY", "metric": derived},
        {"name": "canonical_final_time_contract", "status": "PASS" if final_time_reached else "NOT_READY", "metric": time1, "target": 3.0},
        {"name": "direct_t3_runtime_viability", "status": "PASS" if estimated_steps_to_t3 <= 1_000_000 else "NOT_READY", "metric": {"estimated_steps_to_t3": estimated_steps_to_t3, "estimated_wall_seconds_to_t3": estimated_wall_seconds_to_t3}, "target": "<=1e6 steps for direct scout-lineage run"},
    ]
    status = STATUS_PASS if gates[0]["status"] == "PASS" and gates[1]["status"] == "PASS" and gates[2]["status"] == "PASS" else STATUS_NOT_READY
    summary = {
        "clears_qlt_03_canonical_final_time_contract": final_time_reached,
        "remaining_canonical_model_gaps": [] if final_time_reached else ["canonical_final_time_contract"],
        "stable_long_window_scout": stable_window,
        "direct_t3_runtime_viable_on_current_compressible_explicit_path": estimated_steps_to_t3 <= 1_000_000,
        "derived_contract": derived,
        "blocking_reasons": blocking,
        **metrics,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "title": "Academic Two-Phase Canonical Bubble-Rise Final-Time Scout",
        "scope": "Five-thousand-step canonical-input scout used to estimate whether the current compressible PeleC explicit CSF/phase-viscosity path can directly reach the Hysing t=3 final-time contract.",
        "case": case,
        "summary": summary,
        "quality_gates": gates,
        "limitations": [
            "This scout is intentionally not a t=3 benchmark validation unless the canonical_final_time_contract gate passes.",
            "The estimate is based on the current low-CFL compressible PeleC path with capped explicit CSF and phase-viscosity source terms; a different low-Mach/incompressible formulation or larger stable timestep could change the projection.",
            "Reference circularity and rise-velocity comparisons remain gated by the t=3 trajectory and final interface shape.",
        ],
        "evidence_files": [
            evidence_entry("case_summary", case_summary_path),
            evidence_entry("input_file", input_file),
            evidence_entry("build_log", build_log),
            evidence_entry("run_log", run_log),
            evidence_entry("validation_log", validation_log),
            evidence_entry("runner", Path("tools/codex_run_academic_twophase_canonical_bubble_rise_final_time_scout.sh")),
            evidence_entry("validator", Path("tools/validate_academic_twophase_bubble_rise.py")),
            evidence_entry("report_writer", Path("tools/write_academic_twophase_canonical_bubble_rise_final_time_scout_report.py")),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "unexpected status")
    summary = report.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("stable_long_window_scout") is True, "stable scout window not proved")
    require(summary.get("clears_qlt_03_canonical_final_time_contract") is False, "this scout should not claim t=3 completion")
    statuses = {g.get("name"): g.get("status") for g in report.get("quality_gates", [])}
    require(statuses.get("final_time_scout_run_finalized") == "PASS", "scout run did not finalize")
    require(statuses.get("long_window_stability_probe") == "PASS", "long-window stability probe did not pass")
    require(statuses.get("canonical_contract_inputs_retained") == "PASS", "canonical inputs were not retained")
    require(statuses.get("canonical_final_time_contract") == "NOT_READY", "final-time contract should remain explicit")
    if check_hashes:
        for item in report.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def write_md(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Academic Two-Phase Canonical Bubble-Rise Final-Time Scout",
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
            print(f"academic_twophase_canonical_bubble_rise_final_time_scout VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        report = build_report(args)
        validate_report(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_md(report, out_md)
        print(f"academic_twophase_canonical_bubble_rise_final_time_scout PASS json={out_json} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"academic_twophase_canonical_bubble_rise_final_time_scout FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
