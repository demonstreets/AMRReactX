#!/usr/bin/env python3
"""Write/verify closed control-volume gas-particle spray budget evidence."""
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
from write_academic_droplet_spray_budget_preflight_report import (  # noqa: E402
    cell_volume,
    field,
    read_particle_binary_budget,
)

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ACADEMIC-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_spray_closed_control_volume_budget_20260729")
DEFAULT_JSON = DEFAULT_ROOT / "academic_spray_closed_control_volume_budget_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_spray_closed_control_volume_budget_report.md"
SOURCE_FIELDS = (
    "spray_rho_src",
    "spray_xmom_src",
    "spray_ymom_src",
    "spray_eng_src",
    "spray_rhoY_NC7H16_src",
)
GAS_FIELDS = ("density", "xmom", "ymom", "rho_E", "rho_NC7H16")


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def finite(value: Any, label: str) -> float:
    number = float(value)
    require(math.isfinite(number), f"{label} is not finite: {number!r}")
    return number


def relerr(residual: float, reference: float) -> float:
    return abs(residual) / max(abs(reference), 1.0e-300)


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


def plot_record(plot_path: Path, input_file: Path) -> dict[str, Any]:
    plot = amrex_reader.read_plotfile(str(plot_path))
    comps = set(plot.get("comp_names", []))
    missing = [name for name in (*SOURCE_FIELDS, *GAS_FIELDS) if name not in comps]
    require(not missing, f"{plot_path} missing fields: {missing}")
    cv = cell_volume(plot)
    dx = [float(value) for value in plot.get("dx", [])]
    ndim = int(plot.get("ndim", len(dx)))
    thickness = dx[0] if ndim == 2 and dx else 1.0
    particle = read_particle_binary_budget(plot_path, input_file)
    gas = {
        "mass": float(np.sum(field(plot, "density")) * cv),
        "xmom": float(np.sum(field(plot, "xmom")) * cv),
        "ymom": float(np.sum(field(plot, "ymom")) * cv),
        "rho_E": float(np.sum(field(plot, "rho_E")) * cv),
        "rho_NC7H16": float(np.sum(field(plot, "rho_NC7H16")) * cv),
    }
    source = {
        "rho": float(np.sum(field(plot, "spray_rho_src")) * cv),
        "xmom": float(np.sum(field(plot, "spray_xmom_src")) * cv),
        "ymom": float(np.sum(field(plot, "spray_ymom_src")) * cv),
        "rho_E": float(np.sum(field(plot, "spray_eng_src")) * cv),
        "rho_NC7H16": float(np.sum(field(plot, "spray_rhoY_NC7H16_src")) * cv),
    }
    return {
        "path": str(plot_path),
        "time": float(plot["time"]),
        "cell_volume": cv,
        "spray_particle_mass_measure_factor": thickness,
        "gas": gas,
        "source_rate_integrals": source,
        "particle": {
            "mass": float(particle["mass_sum"]),
            "xmom": float(particle["xmom_sum"]),
            "ymom": float(particle["ymom_sum"]),
            "thermal_mass_temperature_sum": float(particle["thermal_mass_temperature_sum"]),
            "particle_count": int(particle["particle_count"]),
            "mass_model": particle["mass_model"],
        },
    }


def integrate(records: list[dict[str, Any]], key: str) -> float:
    total = 0.0
    for prev, cur in zip(records, records[1:]):
        t0 = finite(prev["time"], "prev.time")
        t1 = finite(cur["time"], "cur.time")
        require(t1 > t0, "plotfile times must be strictly increasing")
        total += (t1 - t0) * finite(cur["source_rate_integrals"][key], key)
    return total


def delta(records: list[dict[str, Any]], section: str, key: str) -> float:
    return finite(records[-1][section][key], f"final.{section}.{key}") - finite(
        records[0][section][key], f"initial.{section}.{key}"
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir)
    input_file = Path(args.input) if args.input else run_dir / "inputs"
    run_log = Path(args.run_log) if args.run_log else run_dir / "run.log"
    init_file = Path(args.init_file) if args.init_file else run_dir / "initspraydata_2d_single.dat"
    require(run_dir.is_dir(), f"missing run dir: {run_dir}")
    require(input_file.is_file(), f"missing input file: {input_file}")
    require(run_log.is_file(), f"missing run log: {run_log}")
    plots = sorted(run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
    require(len(plots) >= 3, f"need at least 3 plotfiles, found {len(plots)}")
    records = [plot_record(plot, input_file) for plot in plots]
    thickness = finite(records[0]["spray_particle_mass_measure_factor"], "thickness")
    require(thickness > 0.0, "2D effective thickness must be positive")

    source_int = {key: integrate(records, key) for key in ("rho", "xmom", "ymom", "rho_E", "rho_NC7H16")}
    gas_delta = {
        "mass": delta(records, "gas", "mass"),
        "xmom": delta(records, "gas", "xmom"),
        "ymom": delta(records, "gas", "ymom"),
        "rho_E": delta(records, "gas", "rho_E"),
        "rho_NC7H16": delta(records, "gas", "rho_NC7H16"),
    }
    particle_delta = {
        "mass": delta(records, "particle", "mass"),
        "xmom": delta(records, "particle", "xmom"),
        "ymom": delta(records, "particle", "ymom"),
    }
    gas_residual = {
        "mass": gas_delta["mass"] - source_int["rho"],
        "xmom": gas_delta["xmom"] - source_int["xmom"],
        "ymom": gas_delta["ymom"] - source_int["ymom"],
        "rho_E": gas_delta["rho_E"] - source_int["rho_E"],
        "rho_NC7H16": gas_delta["rho_NC7H16"] - source_int["rho_NC7H16"],
    }
    particle_residual = {
        "mass": particle_delta["mass"] + thickness * source_int["rho"],
        "xmom": particle_delta["xmom"] + thickness * source_int["xmom"],
        "ymom": particle_delta["ymom"] + thickness * source_int["ymom"],
    }
    total_residual = {
        "mass": thickness * gas_delta["mass"] + particle_delta["mass"],
        "xmom": thickness * gas_delta["xmom"] + particle_delta["xmom"],
        "ymom": thickness * gas_delta["ymom"] + particle_delta["ymom"],
    }
    rels = {
        "gas_mass": relerr(gas_residual["mass"], source_int["rho"]),
        "gas_xmom": relerr(gas_residual["xmom"], source_int["xmom"]),
        "gas_rho_E": relerr(gas_residual["rho_E"], source_int["rho_E"]),
        "gas_fuel": relerr(gas_residual["rho_NC7H16"], source_int["rho_NC7H16"]),
        "particle_mass": relerr(particle_residual["mass"], thickness * source_int["rho"]),
        "particle_xmom": relerr(particle_residual["xmom"], thickness * source_int["xmom"]),
        "total_mass": relerr(total_residual["mass"], thickness * source_int["rho"]),
        "total_xmom": relerr(total_residual["xmom"], thickness * source_int["xmom"]),
    }
    max_abs_xmom_source = max(abs(r["source_rate_integrals"]["xmom"]) for r in records)
    run_text = run_log.read_text(encoding="utf-8", errors="replace")
    failure_tokens = ["nan", "SIGSEGV", "Segmentation", "Backtrace", "Abort", "Simulation stopped early"]
    has_failure = any(token.lower() in run_text.lower() for token in failure_tokens)
    gates = [
        {"name": "run_finalized_without_failure_tokens", "status": "PASS" if "finalized" in run_text and not has_failure else "FAIL", "metric": {"has_failure_token": has_failure}},
        {"name": "source_fields_present", "status": "PASS", "metric": list(SOURCE_FIELDS)},
        {"name": "strong_x_momentum_source", "status": "PASS" if max_abs_xmom_source >= args.min_xmom_source else "FAIL", "metric": max_abs_xmom_source},
        {"name": "gas_mass_matches_source_history", "status": "PASS" if rels["gas_mass"] <= args.rel_tol else "FAIL", "metric": rels["gas_mass"]},
        {"name": "gas_xmomentum_matches_source_history", "status": "PASS" if rels["gas_xmom"] <= args.rel_tol else "FAIL", "metric": rels["gas_xmom"]},
        {"name": "gas_total_energy_matches_source_history", "status": "PASS" if rels["gas_rho_E"] <= args.rel_tol else "FAIL", "metric": rels["gas_rho_E"]},
        {"name": "gas_fuel_species_matches_source_history", "status": "PASS" if rels["gas_fuel"] <= args.rel_tol else "FAIL", "metric": rels["gas_fuel"]},
        {"name": "particle_mass_matches_thickness_scaled_source", "status": "PASS" if rels["particle_mass"] <= args.rel_tol else "FAIL", "metric": rels["particle_mass"]},
        {"name": "particle_xmomentum_matches_thickness_scaled_source", "status": "PASS" if rels["particle_xmom"] <= args.rel_tol else "FAIL", "metric": rels["particle_xmom"]},
        {"name": "total_mass_control_volume_closure", "status": "PASS" if rels["total_mass"] <= args.rel_tol else "FAIL", "metric": rels["total_mass"]},
        {"name": "total_xmomentum_control_volume_closure", "status": "PASS" if rels["total_xmom"] <= args.rel_tol else "FAIL", "metric": rels["total_xmom"]},
        {"name": "y_momentum_transverse_absolute_residual_small", "status": "PASS" if abs(total_residual["ymom"]) <= args.ymom_abs_tol else "FAIL", "metric": total_residual["ymom"]},
    ]
    failed = [g for g in gates if g["status"] != "PASS"]
    summary = {
        "case_name": run_dir.name,
        "plot_count": len(records),
        "final_time": records[-1]["time"],
        "spray_particle_mass_measure_factor": thickness,
        "max_abs_xmom_source_rate_integral": max_abs_xmom_source,
        "source_integrals": source_int,
        "gas_delta": gas_delta,
        "particle_delta": particle_delta,
        "gas_residual": gas_residual,
        "particle_residual": particle_residual,
        "thickness_scaled_total_residual": total_residual,
        "relative_errors": rels,
        "clears_acd_05_closed_control_volume_mass_momentum_energy_budget": not failed,
        "clears_acd_07_reacting_control_volume_budget": False,
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS if not failed else "FAIL-ACADEMIC-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET",
        "title": "Academic Spray Closed Control-Volume Budget",
        "scope": "Closed periodic non-reacting PeleC spray case with strong particle x-momentum validating gas and particle mass, x-momentum, and gas total-energy source-history closure.",
        "case": {
            "run_dir": str(run_dir),
            "input_file": str(input_file),
            "run_log": str(run_log),
            "init_file": str(init_file),
            "periodic": True,
            "reaction": False,
            "diffusion": False,
            "momentum_transfer": True,
            "mass_transfer": True,
        },
        "summary": summary,
        "quality_gates": gates,
        "records": records,
        "limitations": [
            "This clears the ACD-05 closed periodic spray control-volume budget for a non-reacting evaporation/momentum-transfer case.",
            "It does not clear ACD-07 reacting spray/gas-liquid detonation control-volume or cellular detonation morphology credit.",
            "The 2D spray particle budget uses PeleC's effective-thickness convention; gas integrals are scaled by this factor before comparing with native particle DATA budgets.",
        ],
        "evidence_files": [
            evidence_entry("report_writer", Path("tools/write_academic_spray_closed_control_volume_budget_report.py")),
            evidence_entry("runner", Path("tools/codex_run_academic_spray_closed_control_volume_budget.sh")),
            evidence_entry("input_file", input_file),
            evidence_entry("run_log", run_log),
            evidence_entry("init_file", init_file),
            evidence_entry("initial_header", plots[0] / "Header"),
            evidence_entry("final_header", plots[-1] / "Header"),
        ],
    }
    return report


def validate_report(report: dict[str, Any], check_hashes: bool) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    summary = report.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("clears_acd_05_closed_control_volume_mass_momentum_energy_budget") is True, "ACD-05 control-volume budget not cleared")
    require(summary.get("clears_acd_07_reacting_control_volume_budget") is False, "must not clear ACD-07 reacting budget")
    rels = summary.get("relative_errors", {})
    for key in ("gas_mass", "gas_xmom", "gas_rho_E", "gas_fuel", "particle_mass", "particle_xmom", "total_mass", "total_xmom"):
        require(float(rels.get(key, 1.0)) <= 1.0e-3, f"relative error too large: {key}")
    require(float(summary.get("max_abs_xmom_source_rate_integral", 0.0)) >= 1.0e-5, "x-momentum source is too weak")
    gates = report.get("quality_gates", [])
    require(isinstance(gates, list) and gates, "quality gates missing")
    failed = [g.get("name") for g in gates if g.get("status") != "PASS"]
    require(not failed, f"failed gates: {failed}")
    if check_hashes:
        for item in report.get("evidence_files", []):
            path = Path(item["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def write_md(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    r = s["relative_errors"]
    lines = [
        "# Academic Spray Closed Control-Volume Budget",
        "",
        f"Status: `{report['status']}`",
        "",
        "Key relative errors:",
        f"- gas mass/source: `{r['gas_mass']:.6e}`",
        f"- gas x-momentum/source: `{r['gas_xmom']:.6e}`",
        f"- gas total-energy/source: `{r['gas_rho_E']:.6e}`",
        f"- particle mass/source: `{r['particle_mass']:.6e}`",
        f"- particle x-momentum/source: `{r['particle_xmom']:.6e}`",
        f"- total mass closure: `{r['total_mass']:.6e}`",
        f"- total x-momentum closure: `{r['total_xmom']:.6e}`",
        "",
        "This gate clears ACD-05 closed periodic spray control-volume budget credit and keeps ACD-07 reacting gas-liquid detonation credit open.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir")
    parser.add_argument("--input")
    parser.add_argument("--run-log")
    parser.add_argument("--init-file")
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    parser.add_argument("--verify-json")
    parser.add_argument("--rel-tol", type=float, default=1.0e-3)
    parser.add_argument("--ymom-abs-tol", type=float, default=1.0e-16)
    parser.add_argument("--min-xmom-source", type=float, default=1.0e-5)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(report, check_hashes=True)
            print(f"academic_spray_closed_control_volume_budget VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        require(args.run_dir, "--run-dir is required")
        report = build_report(args)
        validate_report(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_md(report, out_md)
        print(f"academic_spray_closed_control_volume_budget PASS json={out_json} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"academic_spray_closed_control_volume_budget FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())