#!/usr/bin/env python3
"""Write/verify bubble-rise canonical observable diagnostics."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amrex_reader  # noqa: E402

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-OBSERVABLE-DIAGNOSTICS"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_observables_20260729")
DEFAULT_JSON = DEFAULT_ROOT / "academic_twophase_bubble_rise_observables_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_twophase_bubble_rise_observables_report.md"
DEFAULT_RUN_DIR = Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/bubble_rise_buoyancy_6000step_low_cfl/run")
DEFAULT_BUBBLE_REPORT = Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json")


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


def field(plot: dict[str, Any], name: str) -> np.ndarray:
    fields = plot.get("fields", {})
    require(isinstance(fields, dict) and name in fields, f"missing plot field {name}")
    arr = np.asarray(fields[name], dtype=float)
    require(np.isfinite(arr).all(), f"non-finite plot field {name}")
    return arr


def cell_spacing(plot: dict[str, Any]) -> tuple[float, float]:
    x = np.asarray(plot.get("x", []), dtype=float)
    y = np.asarray(plot.get("y", []), dtype=float)
    require(x.size >= 2 and y.size >= 2, "plotfile grid too small")
    return float(abs(x[1] - x[0])), float(abs(y[1] - y[0]))


def mesh(plot: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(plot.get("x", []), dtype=float)
    y = np.asarray(plot.get("y", []), dtype=float)
    require(x.size >= 2 and y.size >= 2, "plotfile grid too small")
    return np.meshgrid(x, y, indexing="ij")


def interface_length(alpha: np.ndarray, dx: float, dy: float, eps: float = 1.0e-12) -> float:
    # Marching-squares edge crossing count; robust enough for regression diagnostics on diffuse/VOF alpha.
    length = 0.0
    a = np.clip(alpha, 0.0, 1.0)
    horizontal = (a[:, :-1] - 0.5) * (a[:, 1:] - 0.5) < -eps
    vertical = (a[:-1, :] - 0.5) * (a[1:, :] - 0.5) < -eps
    length += float(np.count_nonzero(horizontal)) * dx
    length += float(np.count_nonzero(vertical)) * dy
    return length


def plot_observable(plot_path: Path) -> dict[str, Any]:
    plot = amrex_reader.read_plotfile(str(plot_path))
    rho = field(plot, "density")
    adv = field(plot, "rho_adv_0")
    ymom = field(plot, "ymom")
    dx, dy = cell_spacing(plot)
    xx, yy = mesh(plot)
    area = dx * dy
    alpha = adv / np.maximum(rho, 1.0e-300)
    light = np.clip(1.0 - alpha, 0.0, 1.0)
    light_sum = float(np.sum(light))
    require(light_sum > 0.0, f"no light phase in {plot_path}")
    volume = float(light_sum * area)
    cx = float(np.sum(light * xx) / light_sum)
    cy = float(np.sum(light * yy) / light_sum)
    vy = float(np.sum(light * ymom / np.maximum(rho, 1.0e-300)) / light_sum)
    perimeter = interface_length(alpha, dx, dy)
    circularity = float(math.sqrt(4.0 * math.pi * volume) / perimeter) if perimeter > 0.0 else 0.0
    return {
        "plotfile": str(plot_path),
        "time": float(plot.get("time", 0.0)),
        "light_volume": volume,
        "center_of_mass_x": cx,
        "center_of_mass_y": cy,
        "mean_rise_velocity_y": vy,
        "interface_perimeter_estimate": perimeter,
        "circularity_estimate": circularity,
        "alpha_min": float(np.min(alpha)),
        "alpha_max": float(np.max(alpha)),
        "grid": [int(rho.shape[0]), int(rho.shape[1])],
        "dx": dx,
        "dy": dy,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir)
    require(run_dir.is_dir(), f"missing run dir: {run_dir}")
    plots = sorted(run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
    require(len(plots) >= 2, f"need at least 2 plotfiles, found {len(plots)}")
    records = [plot_observable(path) for path in plots]
    for prev, cur in zip(records, records[1:]):
        dtv = cur["time"] - prev["time"]
        require(dtv > 0.0, "plot times must increase")
        cur["finite_difference_rise_velocity_y"] = (cur["center_of_mass_y"] - prev["center_of_mass_y"]) / dtv
    records[0]["finite_difference_rise_velocity_y"] = 0.0
    volumes = [rec["light_volume"] for rec in records]
    circularities = [rec["circularity_estimate"] for rec in records]
    cys = [rec["center_of_mass_y"] for rec in records]
    fdv = [rec["finite_difference_rise_velocity_y"] for rec in records[1:]] or [0.0]
    volume_rel_drift = abs(volumes[-1] - volumes[0]) / max(abs(volumes[0]), 1.0e-300)
    gates = [
        {"name": "observable_fields_present", "status": "PASS", "metric": ["density", "rho_adv_0", "ymom"]},
        {"name": "at_least_endpoint_observables", "status": "PASS" if len(records) >= 2 else "FAIL", "metric": len(records)},
        {"name": "canonical_timeseries_sampling", "status": "PASS" if len(records) >= args.min_canonical_samples else "NOT_READY", "metric": len(records), "target": args.min_canonical_samples},
        {"name": "center_of_mass_history_available", "status": "PASS", "metric": [cys[0], cys[-1]]},
        {"name": "rise_velocity_history_available", "status": "PASS" if len(records) >= 2 else "FAIL", "metric": {"max_fd_velocity": max(fdv), "min_fd_velocity": min(fdv)}},
        {"name": "circularity_history_available", "status": "PASS" if all(math.isfinite(c) and c > 0.0 for c in circularities) else "FAIL", "metric": {"min": min(circularities), "max": max(circularities)}},
        {"name": "light_volume_conservation_diagnostic", "status": "PASS" if volume_rel_drift <= args.max_volume_rel_drift else "NOT_READY", "metric": volume_rel_drift, "target": args.max_volume_rel_drift},
    ]
    failed = [g["name"] for g in gates if g["status"] == "FAIL"]
    status = STATUS_PASS if not failed else "FAIL-ACADEMIC-TWOPHASE-BUBBLE-RISE-OBSERVABLE-DIAGNOSTICS"
    canonical_observable_gate_names = {
        "observable_fields_present",
        "at_least_endpoint_observables",
        "canonical_timeseries_sampling",
        "center_of_mass_history_available",
        "rise_velocity_history_available",
        "circularity_history_available",
    }
    clears_canonical_observable_gap = all(
        g["status"] == "PASS" for g in gates if g["name"] in canonical_observable_gate_names
    )
    summary = {
        "plot_count": len(records),
        "time0": records[0]["time"],
        "time1": records[-1]["time"],
        "center_of_mass_y0": cys[0],
        "center_of_mass_y1": cys[-1],
        "center_of_mass_y_rise": cys[-1] - cys[0],
        "max_finite_difference_rise_velocity_y": max(fdv),
        "min_circularity_estimate": min(circularities),
        "time_at_min_circularity_estimate": records[int(np.argmin(circularities))]["time"],
        "light_volume_rel_drift": volume_rel_drift,
        "clears_canonical_observable_timeseries_gap": clears_canonical_observable_gap,
        "clears_qlt_03_canonical_long_time_bubble_rise_gap": False,
    }
    bubble_report = Path(args.bubble_report)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "title": "Academic Bubble-Rise Canonical Observable Diagnostics",
        "scope": "Extract Hysing-style center-of-mass, rise-velocity, and circularity diagnostics from maintained PeleC bubble-rise plotfiles.",
        "summary": summary,
        "quality_gates": gates,
        "records": records,
        "limitations": [
            "This report supplies observable extraction only; it does not make the current PeleC case physically equivalent to the Hysing benchmark.",
            "Canonical time-series sampling is judged from center-of-mass, rise-velocity, and circularity histories; conservation drift remains a separate diagnostic gate.",
            "Circularity is estimated from cell-edge alpha=0.5 crossings and is intended as a regression/preflight diagnostic, not a high-order geometric reference value.",
        ],
        "evidence_files": [
            evidence_entry("report_writer", Path("tools/write_academic_twophase_bubble_rise_observables_report.py")),
            evidence_entry("bubble_rise_validation_report", bubble_report),
            evidence_entry("initial_plot_header", plots[0] / "Header"),
            evidence_entry("final_plot_header", plots[-1] / "Header"),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "unexpected status")
    summary = report.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(int(summary.get("plot_count", 0)) >= 2, "plot_count too small")
    require(summary.get("clears_qlt_03_canonical_long_time_bubble_rise_gap") is False, "canonical gap must remain false")
    gates = report.get("quality_gates", [])
    require(isinstance(gates, list) and gates, "quality gates missing")
    failed = [g.get("name") for g in gates if g.get("status") == "FAIL"]
    require(not failed, f"failed gates: {failed}")
    statuses = {g.get("name"): g.get("status") for g in gates}
    require(statuses.get("canonical_timeseries_sampling") in {"PASS", "NOT_READY"}, "timeseries gate missing")
    if check_hashes:
        for item in report.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def write_md(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Academic Bubble-Rise Canonical Observable Diagnostics",
        "",
        f"Status: `{report['status']}`",
        "",
        "Key diagnostics:",
        f"- plot count: `{s['plot_count']}`",
        f"- final time: `{s['time1']:.12e}`",
        f"- center-of-mass rise: `{s['center_of_mass_y_rise']:.12e}`",
        f"- max finite-difference rise velocity: `{s['max_finite_difference_rise_velocity_y']:.12e}`",
        f"- min circularity estimate: `{s['min_circularity_estimate']:.12e}`",
        f"- light volume relative drift: `{s['light_volume_rel_drift']:.12e}`",
        "",
        "Quality gates:",
        "",
        "| Gate | Status | Metric |",
        "| --- | --- | --- |",
    ]
    for gate in report["quality_gates"]:
        metric = json.dumps(gate.get("metric"), sort_keys=True)
        lines.append(f"| `{gate['name']}` | `{gate['status']}` | `{metric}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    parser.add_argument("--bubble-report", default=str(DEFAULT_BUBBLE_REPORT))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    parser.add_argument("--verify-json")
    parser.add_argument("--min-canonical-samples", type=int, default=16)
    parser.add_argument("--max-volume-rel-drift", type=float, default=1.0e-8)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(report, check_hashes=True)
            print(f"academic_twophase_bubble_rise_observables VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        report = build_report(args)
        validate_report(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_md(report, out_md)
        print(f"academic_twophase_bubble_rise_observables PASS json={out_json} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"academic_twophase_bubble_rise_observables FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
