#!/usr/bin/env python3
"""Write/verify ACD-07 reacting spray detonation source-budget evidence."""
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

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amrex_reader  # noqa: E402
from write_academic_droplet_spray_budget_preflight_report import (  # noqa: E402
    cell_volume,
    field,
    read_particle_binary_budget,
)

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/academic_spray_detonation_source_budget_validation_20260729"
)
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / "academic_spray_detonation_source_budget_validation_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / "academic_spray_detonation_source_budget_validation_report.md"

REQUIRED_SOURCE_FIELDS = (
    "spray_rho_src",
    "spray_xmom_src",
    "spray_ymom_src",
    "spray_eng_src",
    "spray_rhoY_NC7H16_src",
)
REQUIRED_REACTING_FIELDS = (
    "density",
    "Temp",
    "pressure",
    "heatRelease",
    "rhoe_dot",
    "rho_NC7H16",
    "Y(NC7H16)",
    "Y(O2)",
    "Y(N2)",
)


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def finite(value: Any, label: str) -> float:
    number = float(value)
    require(math.isfinite(number), f"{label} is not finite: {number!r}")
    return number


def relerr(value: float, reference: float) -> float:
    return abs(value) / max(abs(reference), 1.0e-300)


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


def parse_input(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        lhs, rhs = line.split("=", 1)
        values[lhs.strip()] = rhs.strip().strip('"')
    return values


def clean_log(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    require("AMReX" in text and "finalized" in text, f"run did not finalize: {path}")
    bad = re.search(
        r"\b(?:nan|SIGSEGV|Segmentation|Backtrace|Abort|Simulation stopped early)\b",
        text,
        re.IGNORECASE,
    )
    if bad is not None:
        raise ReportError(f"run log contains failure marker {bad.group(0)!r}: {path}")
    return text


def stats(arr: np.ndarray) -> dict[str, float]:
    require(np.isfinite(arr).all(), "non-finite plot field")
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "sum": float(np.sum(arr)),
        "absmax": float(np.max(np.abs(arr))),
    }


def rightmost_front(plot: dict[str, Any], name: str, threshold: float) -> float:
    arr = field(plot, name)
    x = np.asarray(plot["x"], dtype=float)
    axes = tuple(range(1, arr.ndim))
    line = np.max(arr, axis=axes) if axes else arr
    idx = np.where(line > threshold)[0]
    require(idx.size > 0, f"{name} has no cells above threshold {threshold}")
    return float(x[int(idx[-1])])


def plot_record(plot_path: Path, input_file: Path) -> dict[str, Any]:
    plot = amrex_reader.read_plotfile(str(plot_path))
    comp_names = set(plot.get("comp_names", []))
    missing_source = [name for name in REQUIRED_SOURCE_FIELDS if name not in comp_names]
    missing_reacting = [name for name in REQUIRED_REACTING_FIELDS if name not in comp_names]
    require(not missing_source, f"{plot_path} missing source fields: {missing_source}")
    require(not missing_reacting, f"{plot_path} missing reacting fields: {missing_reacting}")

    cv = cell_volume(plot)
    source = {name: float(np.sum(field(plot, name)) * cv) for name in REQUIRED_SOURCE_FIELDS}
    dx = [float(value) for value in plot.get("dx", [])]
    ndim = int(plot.get("ndim", len(dx)))
    particle_measure_factor = dx[0] if ndim == 2 and dx else 1.0
    particle = read_particle_binary_budget(plot_path, input_file)
    y_sum = field(plot, "Y(NC7H16)") + field(plot, "Y(O2)") + field(plot, "Y(N2)")
    return {
        "path": str(plot_path),
        "time": float(plot["time"]),
        "dx": dx,
        "source_rate_integrals": source,
        "spray_particle_mass_measure_factor": particle_measure_factor,
        "gas": {
            "mass": float(np.sum(field(plot, "density")) * cv),
            "xmom": float(np.sum(field(plot, "xmom")) * cv) if "xmom" in comp_names else 0.0,
            "ymom": float(np.sum(field(plot, "ymom")) * cv) if "ymom" in comp_names else 0.0,
            "rho_E": float(np.sum(field(plot, "rho_E")) * cv) if "rho_E" in comp_names else 0.0,
            "rho_NC7H16": float(np.sum(field(plot, "rho_NC7H16")) * cv),
        },
        "field_stats": {
            "density": stats(field(plot, "density")),
            "Temp": stats(field(plot, "Temp")),
            "pressure": stats(field(plot, "pressure")),
            "heatRelease": stats(field(plot, "heatRelease")),
            "rhoe_dot": stats(field(plot, "rhoe_dot")),
            "Y(NC7H16)": stats(field(plot, "Y(NC7H16)")),
            "Y(O2)": stats(field(plot, "Y(O2)")),
            "Y(N2)": stats(field(plot, "Y(N2)")),
            "species_closure_absmax": float(np.max(np.abs(y_sum - 1.0))),
        },
        "particle_binary_budget": {
            "mass_sum": float(particle["mass_sum"]),
            "xmom_sum": float(particle["xmom_sum"]),
            "ymom_sum": float(particle["ymom_sum"]),
            "mass_model": particle["mass_model"],
            "particle_count": int(particle["particle_count"]),
        },
    }


def integrate_right_endpoint(records: list[dict[str, Any]], key: str) -> float:
    total = 0.0
    for prev, cur in zip(records, records[1:]):
        dt = finite(cur["time"], "time") - finite(prev["time"], "time")
        require(dt > 0.0, "plotfile times must increase")
        total += finite(cur["source_rate_integrals"][key], key) * dt
    return total


def input_contract(values: dict[str, str]) -> list[str]:
    expected = {
        "pelec.do_react": "1",
        "pelec.do_spray_particles": "1",
        "particles.mass_transfer": "1",
        "particles.mom_transfer": "1",
        "particles.fixed_parts": "0",
        "particles.plot_src": "1",
        "pelec.plot_rhoy": "1",
        "pelec.plot_massfrac": "1",
        "pelec.chem_integrator": "ReactorCvode",
        "cvode.solve_type": "dense_direct",
    }
    missing: list[str] = []
    for key, want in expected.items():
        if values.get(key) != want:
            missing.append(f"{key}={values.get(key)!r}, expected {want!r}")
    return missing


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).resolve()
    input_file = Path(args.input) if args.input else run_dir / "inputs"
    run_log = Path(args.run_log) if args.run_log else run_dir / "run.log"
    require(run_dir.is_dir(), f"missing run dir: {run_dir}")
    require(input_file.is_file(), f"missing input file: {input_file}")
    require(run_log.is_file(), f"missing run log: {run_log}")
    log_text = clean_log(run_log)
    inputs = parse_input(input_file)

    plots = sorted(run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
    require(len(plots) >= args.min_plot_count, f"need at least {args.min_plot_count} plotfiles, found {len(plots)}")
    records = [plot_record(plot, input_file) for plot in plots]
    first = records[0]
    last = records[-1]

    rho_src_integral = integrate_right_endpoint(records, "spray_rho_src")
    fuel_src_integral = integrate_right_endpoint(records, "spray_rhoY_NC7H16_src")
    xmom_src_integral = integrate_right_endpoint(records, "spray_xmom_src")
    ymom_src_integral = integrate_right_endpoint(records, "spray_ymom_src")
    energy_src_integral = integrate_right_endpoint(records, "spray_eng_src")
    gas_mass_delta = last["gas"]["mass"] - first["gas"]["mass"]
    gas_fuel_delta = last["gas"]["rho_NC7H16"] - first["gas"]["rho_NC7H16"]
    gas_xmom_delta = last["gas"]["xmom"] - first["gas"]["xmom"]
    gas_ymom_delta = last["gas"]["ymom"] - first["gas"]["ymom"]
    gas_energy_delta = last["gas"]["rho_E"] - first["gas"]["rho_E"]
    gas_mass_source_rel = relerr(gas_mass_delta - rho_src_integral, rho_src_integral)
    gas_fuel_source_rel = relerr(gas_fuel_delta - fuel_src_integral, fuel_src_integral)
    gas_energy_source_rel = relerr(gas_energy_delta - energy_src_integral, energy_src_integral)
    gas_xmom_source_rel = relerr(gas_xmom_delta - xmom_src_integral, xmom_src_integral)
    gas_ymom_source_rel = relerr(gas_ymom_delta - ymom_src_integral, ymom_src_integral)
    particle_measure_factor = finite(
        first["spray_particle_mass_measure_factor"], "spray_particle_mass_measure_factor"
    )
    particle_mass_delta = (
        last["particle_binary_budget"]["mass_sum"]
        - first["particle_binary_budget"]["mass_sum"]
    )
    particle_comparable_rho_src_integral = rho_src_integral * particle_measure_factor
    particle_source_residual = particle_mass_delta + particle_comparable_rho_src_integral
    particle_source_rel = relerr(particle_source_residual, particle_comparable_rho_src_integral)

    pure_fuel_source_mismatch = max(
        abs(
            rec["source_rate_integrals"]["spray_rho_src"]
            - rec["source_rate_integrals"]["spray_rhoY_NC7H16_src"]
        )
        for rec in records
    )
    max_abs_rho_src = max(abs(rec["source_rate_integrals"]["spray_rho_src"]) for rec in records)
    max_abs_mom_src = max(
        max(
            abs(rec["source_rate_integrals"]["spray_xmom_src"]),
            abs(rec["source_rate_integrals"]["spray_ymom_src"]),
        )
        for rec in records
    )
    max_heat_release = max(rec["field_stats"]["heatRelease"]["absmax"] for rec in records)
    max_rhoe_dot = max(rec["field_stats"]["rhoe_dot"]["absmax"] for rec in records)
    species_closure = max(rec["field_stats"]["species_closure_absmax"] for rec in records)
    min_density = min(rec["field_stats"]["density"]["min"] for rec in records)
    min_temp = min(rec["field_stats"]["Temp"]["min"] for rec in records)
    min_pressure = min(rec["field_stats"]["pressure"]["min"] for rec in records)
    o2_consumption = (
        first["field_stats"]["Y(O2)"]["max"]
        - min(rec["field_stats"]["Y(O2)"]["min"] for rec in records)
    )
    fuel_vapor_increase = (
        max(rec["field_stats"]["Y(NC7H16)"]["max"] for rec in records)
        - first["field_stats"]["Y(NC7H16)"]["max"]
    )

    p_front0 = rightmost_front(
        amrex_reader.read_plotfile(str(plots[0])), "pressure", args.pressure_front_threshold
    )
    p_front1 = rightmost_front(
        amrex_reader.read_plotfile(str(plots[-1])), "pressure", args.pressure_front_threshold
    )
    t_front0 = rightmost_front(
        amrex_reader.read_plotfile(str(plots[0])), "Temp", args.temp_front_threshold
    )
    t_front1 = rightmost_front(
        amrex_reader.read_plotfile(str(plots[-1])), "Temp", args.temp_front_threshold
    )
    dx = finite(last["dx"][0], "dx[0]") if last["dx"] else 1.0
    pressure_front_shift = p_front1 - p_front0
    temp_front_shift = t_front1 - t_front0
    pressure_front_shift_cells = pressure_front_shift / dx

    contract_errors = input_contract(inputs)
    gates = [
        {
            "name": "input_reacting_spray_source_budget_contract",
            "status": "PASS" if not contract_errors else "FAIL",
            "metric": contract_errors,
        },
        {
            "name": "run_finalized_without_failure_markers",
            "status": "PASS",
            "metric": "AMReX finalized and log has no failure markers",
        },
        {
            "name": "finite_positive_gas_state",
            "status": "PASS" if min_density > 0.0 and min_temp > 0.0 and min_pressure > 0.0 else "FAIL",
            "metric": {"min_density": min_density, "min_temp": min_temp, "min_pressure": min_pressure},
        },
        {
            "name": "source_fields_present_and_nonzero",
            "status": "PASS" if max_abs_rho_src > 0.0 and max_abs_mom_src > 0.0 else "FAIL",
            "metric": {"max_abs_rho_src": max_abs_rho_src, "max_abs_mom_src": max_abs_mom_src},
        },
        {
            "name": "pure_heptane_rho_source_maps_to_rhoY_source",
            "status": "PASS" if pure_fuel_source_mismatch <= args.absolute_tol else "FAIL",
            "metric": pure_fuel_source_mismatch,
        },
        {
            "name": "particle_mass_closes_to_spray_rho_source",
            "status": "PASS" if particle_source_rel <= args.mass_rel_tol else "FAIL",
            "metric": {
                "particle_source_relative_mismatch": particle_source_rel,
                "particle_mass_delta": particle_mass_delta,
                "particle_comparable_rho_source_integral": particle_comparable_rho_src_integral,
                "spray_particle_mass_measure_factor": particle_measure_factor,
            },
        },
        {
            "name": "gas_mass_closes_to_spray_rho_source",
            "status": "PASS" if gas_mass_source_rel <= args.mass_rel_tol else "FAIL",
            "metric": gas_mass_source_rel,
        },
        {
            "name": "gas_fuel_closes_to_spray_rhoY_source",
            "status": "PASS" if gas_fuel_source_rel <= args.mass_rel_tol else "FAIL",
            "metric": gas_fuel_source_rel,
        },
        {
            "name": "gas_total_energy_closes_to_spray_energy_source",
            "status": "PASS" if gas_energy_source_rel <= args.energy_rel_tol else "FAIL",
            "metric": gas_energy_source_rel,
        },
        {
            "name": "stiff_reaction_heat_release_present",
            "status": "PASS" if max_heat_release >= args.min_heat_release_absmax and max_rhoe_dot > 0.0 else "FAIL",
            "metric": {"heatRelease_absmax": max_heat_release, "rhoe_dot_absmax": max_rhoe_dot},
        },
        {
            "name": "reacting_species_response_present",
            "status": "PASS" if o2_consumption >= args.min_o2_consumption and fuel_vapor_increase >= args.min_fuel_vapor_increase else "FAIL",
            "metric": {"o2_consumption": o2_consumption, "fuel_vapor_increase": fuel_vapor_increase},
        },
        {
            "name": "detonation_style_front_response_present",
            "status": "PASS" if pressure_front_shift_cells >= args.min_front_shift_cells and temp_front_shift >= args.min_temp_front_shift else "FAIL",
            "metric": {
                "pressure_front_shift": pressure_front_shift,
                "pressure_front_shift_cells": pressure_front_shift_cells,
                "temp_front_shift": temp_front_shift,
            },
        },
        {
            "name": "species_mass_fraction_closure",
            "status": "PASS" if species_closure <= args.max_species_closure_rel else "FAIL",
            "metric": species_closure,
        },
    ]
    failed = [gate["name"] for gate in gates if gate["status"] == "FAIL"]
    status = STATUS_PASS if not failed else "FAIL-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION"
    summary = {
        "plot_count": len(records),
        "time0": first["time"],
        "time1": last["time"],
        "rho_source_integral_right_endpoint": rho_src_integral,
        "fuel_source_integral_right_endpoint": fuel_src_integral,
        "xmom_source_integral_right_endpoint": xmom_src_integral,
        "ymom_source_integral_right_endpoint": ymom_src_integral,
        "energy_source_integral_right_endpoint": energy_src_integral,
        "gas_mass_delta": gas_mass_delta,
        "gas_fuel_delta": gas_fuel_delta,
        "gas_xmom_delta": gas_xmom_delta,
        "gas_ymom_delta": gas_ymom_delta,
        "gas_energy_delta": gas_energy_delta,
        "gas_mass_source_relative_error": gas_mass_source_rel,
        "gas_fuel_source_relative_error": gas_fuel_source_rel,
        "gas_energy_source_relative_error": gas_energy_source_rel,
        "gas_xmom_source_relative_error": gas_xmom_source_rel,
        "gas_ymom_source_relative_error": gas_ymom_source_rel,
        "particle_mass_delta": particle_mass_delta,
        "particle_comparable_rho_source_integral": particle_comparable_rho_src_integral,
        "spray_particle_mass_measure_factor": particle_measure_factor,
        "particle_plus_rho_source_residual": particle_source_residual,
        "particle_source_relative_mismatch": particle_source_rel,
        "pure_fuel_rho_rhoY_source_absmax_mismatch": pure_fuel_source_mismatch,
        "max_abs_rho_source_rate_integral": max_abs_rho_src,
        "max_abs_momentum_source_rate_integral": max_abs_mom_src,
        "heatRelease_absmax": max_heat_release,
        "rhoe_dot_absmax": max_rhoe_dot,
        "o2_consumption": o2_consumption,
        "fuel_vapor_increase": fuel_vapor_increase,
        "pressure_front_shift": pressure_front_shift,
        "pressure_front_shift_cells": pressure_front_shift_cells,
        "temp_front_shift": temp_front_shift,
        "species_closure_absmax": species_closure,
        "clears_acd_07_reacting_spray_detonation_budget": status == STATUS_PASS,
        "clears_acd_07_reacting_gas_mass_energy_source_budget": (
            gas_mass_source_rel <= args.mass_rel_tol
            and gas_fuel_source_rel <= args.mass_rel_tol
            and gas_energy_source_rel <= args.energy_rel_tol
            and particle_source_rel <= args.mass_rel_tol
        ),
        "clears_acd_07_reacting_xmomentum_control_volume_budget": False,
        "clears_acd_07_full_cellular_gas_liquid_detonation_gap": False,
        "clears_acd_07_external_reference_gap": False,
        "clears_acd_07_broad_spray_detonation_gap": False,
    }
    evidence_files = [
        evidence_entry("report_writer", Path("tools/write_academic_spray_detonation_source_budget_validation_report.py")),
        evidence_entry("run_script", Path("tools/codex_run_academic_spray_detonation_source_budget_validation.sh")),
        evidence_entry("input_file", input_file),
        evidence_entry("run_log", run_log),
        evidence_entry("initial_plot_header", plots[0] / "Header"),
        evidence_entry("final_plot_header", plots[-1] / "Header"),
        evidence_entry("initial_particle_header", plots[0] / "particles" / "Header"),
        evidence_entry("final_particle_header", plots[-1] / "particles" / "Header"),
    ]
    response_report = Path(
        "docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/"
        "academic_spray_detonation_validation_report.json"
    )
    if response_report.is_file():
        evidence_files.append(evidence_entry("reacting_spray_detonation_response_report", response_report))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "title": "Academic Reacting Spray Detonation Source Budget Validation",
        "scope": (
            "PeleC 2D heptane-air reacting shock-droplet source-budget gate with CVODE chemistry, "
            "spray source plotfields, Euler-Lagrange particle mass accounting, and detonation-style front response"
        ),
        "run_dir": str(run_dir),
        "summary": summary,
        "quality_gates": gates,
        "records": records,
        "evidence_files": evidence_files,
        "limitations": [
            "This clears the reacting spray source/particle budget subgate for ACD-07, not external experiment agreement.",
            "The broad full cellular gas-liquid detonation morphology gate remains open until a dedicated cellular benchmark is attached.",
            "Gas mass, gas fuel, gas total-energy, and particle mass source-history budgets are closed here; x-momentum is diagnostic-only because detonation-front hydrodynamic fluxes dominate gas momentum in this open shock-tube-style case.",
        ],
    }


def validate_report(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS_PASS, "status is not PASS")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("clears_acd_07_reacting_spray_detonation_budget") is True, "ACD-07 source-budget flag missing")
    require(summary.get("clears_acd_07_reacting_gas_mass_energy_source_budget") is True, "ACD-07 gas mass/energy source-budget flag missing")
    require(summary.get("clears_acd_07_reacting_xmomentum_control_volume_budget") is False, "x-momentum control-volume flag must remain false")
    require(summary.get("clears_acd_07_full_cellular_gas_liquid_detonation_gap") is False, "cellular gap flag must remain false")
    require(summary.get("clears_acd_07_external_reference_gap") is False, "external reference gap flag must remain false")
    require(float(summary["particle_source_relative_mismatch"]) <= 5.0e-3, "particle/source relative mismatch too large")
    require(float(summary["gas_mass_source_relative_error"]) <= 5.0e-3, "gas mass/source relative error too large")
    require(float(summary["gas_fuel_source_relative_error"]) <= 5.0e-3, "gas fuel/source relative error too large")
    require(float(summary["gas_energy_source_relative_error"]) <= 5.0e-3, "gas energy/source relative error too large")
    require(float(summary["heatRelease_absmax"]) > 0.0, "heatRelease response absent")
    require(float(summary["rhoe_dot_absmax"]) > 0.0, "rhoe_dot response absent")
    require(float(summary["pressure_front_shift_cells"]) > 0.0, "pressure front did not move")
    require(float(summary["species_closure_absmax"]) <= 2.0e-12, "species closure too large")
    gates = data.get("quality_gates")
    require(isinstance(gates, list) and gates, "quality gates missing")
    failed = [gate["name"] for gate in gates if gate.get("status") == "FAIL"]
    require(not failed, f"failed gates: {failed}")
    if check_hashes:
        for item in data.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Academic Reacting Spray Detonation Source Budget Validation",
        "",
        f"Status: `{report['status']}`",
        "",
        "Key metrics:",
        f"- plot count: `{s['plot_count']}`",
        f"- final time: `{s['time1']:.12e}`",
        f"- integrated `spray_rho_src`: `{s['rho_source_integral_right_endpoint']:.16e}`",
        f"- particle mass delta: `{s['particle_mass_delta']:.16e}`",
        f"- particle/source relative mismatch: `{s['particle_source_relative_mismatch']:.6e}`",
        f"- 2D spray effective thickness factor: `{s['spray_particle_mass_measure_factor']:.6e}`",
        f"- `heatRelease` absmax: `{s['heatRelease_absmax']:.6e}`",
        f"- `rhoe_dot` absmax: `{s['rhoe_dot_absmax']:.6e}`",
        f"- O2 consumption signal: `{s['o2_consumption']:.6e}`",
        f"- fuel vapor response: `{s['fuel_vapor_increase']:.6e}`",
        f"- pressure front shift cells: `{s['pressure_front_shift_cells']:.6e}`",
        f"- species closure absmax: `{s['species_closure_absmax']:.6e}`",
        "",
        "Readiness:",
        f"- ACD-07 reacting spray source-budget subgate: `{s['clears_acd_07_reacting_spray_detonation_budget']}`",
        f"- full cellular gas-liquid detonation gap: `{s['clears_acd_07_full_cellular_gas_liquid_detonation_gap']}`",
        f"- external reference gap: `{s['clears_acd_07_external_reference_gap']}`",
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
    parser.add_argument("--run-dir")
    parser.add_argument("--input")
    parser.add_argument("--run-log")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    parser.add_argument("--mass-rel-tol", type=float, default=5.0e-3)
    parser.add_argument("--energy-rel-tol", type=float, default=5.0e-3)
    parser.add_argument("--absolute-tol", type=float, default=1.0e-18)
    parser.add_argument("--min-plot-count", type=int, default=4)
    parser.add_argument("--pressure-front-threshold", type=float, default=2.0e6)
    parser.add_argument("--temp-front-threshold", type=float, default=1000.0)
    parser.add_argument("--min-front-shift-cells", type=float, default=1.0)
    parser.add_argument("--min-temp-front-shift", type=float, default=0.01)
    parser.add_argument("--min-heat-release-absmax", type=float, default=1.0e-8)
    parser.add_argument("--min-o2-consumption", type=float, default=1.0e-10)
    parser.add_argument("--min-fuel-vapor-increase", type=float, default=1.0e-10)
    parser.add_argument("--max-species-closure-rel", type=float, default=2.0e-12)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(data, check_hashes=True)
            print(f"VERIFY-PASS {args.verify_json}")
            return 0
        require(args.run_dir, "--run-dir is required unless --verify-json is used")
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        validate_report(report, check_hashes=False)
        print(json.dumps({"status": report["status"], "output_json": str(out_json)}, indent=2))
        return 0
    except ReportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
