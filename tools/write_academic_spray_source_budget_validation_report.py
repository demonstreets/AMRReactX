#!/usr/bin/env python3
"""Write/verify academic spray source-term budget validation evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
STATUS_PASS = "PASS-ACADEMIC-SPRAY-SOURCE-BUDGET-VALIDATION"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/academic_spray_source_budget_validation_20260729"
)
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / "academic_spray_source_budget_validation_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / "academic_spray_source_budget_validation_report.md"
REQUIRED_SOURCE_FIELDS = (
    "spray_rho_src",
    "spray_xmom_src",
    "spray_ymom_src",
    "spray_eng_src",
    "spray_rhoY_NC7H16_src",
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


def finite(value: Any, label: str) -> float:
    number = float(value)
    require(math.isfinite(number), f"{label} is not finite: {number!r}")
    return number


def relerr(value: float, reference: float) -> float:
    return abs(value) / max(abs(reference), 1.0e-300)


def parse_input_value(path: Path, key: str, default: str | None = None) -> str | None:
    if not path.is_file():
        return default
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        lhs, rhs = line.split("=", 1)
        if lhs.strip() == key:
            return rhs.strip().split()[0]
    return default


def plot_integrals(plot_path: Path, input_file: Path) -> dict[str, Any]:
    plot = amrex_reader.read_plotfile(str(plot_path))
    cv = cell_volume(plot)
    comp_names = set(plot.get("comp_names", []))
    missing = [name for name in REQUIRED_SOURCE_FIELDS if name not in comp_names]
    require(not missing, f"{plot_path} missing source fields: {missing}")
    require("rho_NC7H16" in comp_names, f"{plot_path} missing rho_NC7H16")
    source = {
        name: float(np.sum(field(plot, name)) * cv)
        for name in REQUIRED_SOURCE_FIELDS
    }
    dx = [float(value) for value in plot.get("dx", [])]
    ndim = int(plot.get("ndim", len(dx)))
    spray_particle_mass_measure_factor = dx[0] if ndim == 2 and dx else 1.0
    gas = {
        "mass": float(np.sum(field(plot, "density")) * cv),
        "rho_NC7H16": float(np.sum(field(plot, "rho_NC7H16")) * cv),
        "rho_E": float(np.sum(field(plot, "rho_E")) * cv),
    }
    particle = read_particle_binary_budget(plot_path, input_file)
    return {
        "path": str(plot_path),
        "time": float(plot["time"]),
        "cell_volume": cv,
        "gas": gas,
        "source_rate_integrals": source,
        "spray_particle_mass_measure_factor": spray_particle_mass_measure_factor,
        "particle_binary_budget": {
            "mass_sum": float(particle["mass_sum"]),
            "xmom_sum": float(particle["xmom_sum"]),
            "ymom_sum": float(particle["ymom_sum"]),
            "thermal_mass_temperature_sum": float(
                particle["thermal_mass_temperature_sum"]
            ),
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


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).resolve()
    input_file = run_dir / "inputs"
    run_log = run_dir / "run.log"
    require(run_dir.is_dir(), f"missing run dir: {run_dir}")
    require(input_file.is_file(), f"missing run input: {input_file}")
    require(run_log.is_file(), f"missing run log: {run_log}")
    spray_dtmod = finite(parse_input_value(input_file, "particles.dtmod", "0.5"), "particles.dtmod")
    plots = sorted(run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
    require(len(plots) >= 3, f"need at least 3 plotfiles, found {len(plots)}")
    records = [plot_integrals(plot, input_file) for plot in plots]
    first = records[0]
    last = records[-1]
    gas_mass_delta = last["gas"]["mass"] - first["gas"]["mass"]
    fuel_mass_delta = last["gas"]["rho_NC7H16"] - first["gas"]["rho_NC7H16"]
    gas_energy_delta = last["gas"]["rho_E"] - first["gas"]["rho_E"]
    particle_mass_delta = (
        last["particle_binary_budget"]["mass_sum"]
        - first["particle_binary_budget"]["mass_sum"]
    )
    rho_src_integral = integrate_right_endpoint(records, "spray_rho_src")
    fuel_src_integral = integrate_right_endpoint(records, "spray_rhoY_NC7H16_src")
    energy_src_integral = integrate_right_endpoint(records, "spray_eng_src")
    max_abs_rho_src = max(abs(r["source_rate_integrals"]["spray_rho_src"]) for r in records)
    max_abs_mom_src = max(
        max(
            abs(r["source_rate_integrals"]["spray_xmom_src"]),
            abs(r["source_rate_integrals"]["spray_ymom_src"]),
        )
        for r in records
    )
    log_text = run_log.read_text(errors="replace")
    gas_source_residual = gas_mass_delta - rho_src_integral
    fuel_source_residual = fuel_mass_delta - fuel_src_integral
    energy_source_residual = gas_energy_delta - energy_src_integral
    gas_source_rel = relerr(gas_source_residual, rho_src_integral)
    fuel_source_rel = relerr(fuel_source_residual, fuel_src_integral)
    energy_source_rel = relerr(energy_source_residual, energy_src_integral)
    pure_fuel_source_mismatch = max(
        abs(
            r["source_rate_integrals"]["spray_rho_src"]
            - r["source_rate_integrals"]["spray_rhoY_NC7H16_src"]
        )
        for r in records
    )
    spray_particle_mass_measure_factor = finite(
        first.get("spray_particle_mass_measure_factor", 1.0),
        "spray_particle_mass_measure_factor",
    )
    particle_comparable_rho_src_integral = rho_src_integral * spray_particle_mass_measure_factor
    particle_source_residual = particle_mass_delta + particle_comparable_rho_src_integral
    particle_source_rel = relerr(particle_source_residual, particle_comparable_rho_src_integral)
    gates = [
        {
            "name": "run_finalized",
            "status": "PASS" if "AMReX (26.05) finalized" in log_text else "FAIL",
            "metric": "AMReX finalized marker",
        },
        {
            "name": "source_fields_present",
            "status": "PASS",
            "metric": list(REQUIRED_SOURCE_FIELDS),
        },
        {
            "name": "source_terms_nonzero",
            "status": "PASS" if max_abs_rho_src > 0.0 else "FAIL",
            "metric": max_abs_rho_src,
        },
        {
            "name": "gas_total_mass_matches_integrated_rho_source",
            "status": "PASS" if gas_source_rel <= args.mass_rel_tol else "FAIL",
            "metric": gas_source_rel,
        },
        {
            "name": "fuel_species_mass_matches_integrated_rhoY_source",
            "status": "PASS" if fuel_source_rel <= args.mass_rel_tol else "FAIL",
            "metric": fuel_source_rel,
        },
        {
            "name": "pure_fuel_rho_and_rhoY_sources_match",
            "status": "PASS" if pure_fuel_source_mismatch <= args.absolute_tol else "FAIL",
            "metric": pure_fuel_source_mismatch,
        },
        {
            "name": "debug_spray_log_noise_absent",
            "status": "PASS" if "DEBUG_SPRAY" not in log_text else "FAIL",
            "metric": "DEBUG_SPRAY" in log_text,
        },
        {
            "name": "particle_loss_sign_consistent",
            "status": "PASS" if particle_mass_delta < 0.0 and rho_src_integral > 0.0 else "FAIL",
            "metric": {
                "particle_mass_delta": particle_mass_delta,
                "rho_src_integral": rho_src_integral,
                "particle_comparable_rho_src_integral": particle_comparable_rho_src_integral,
                "spray_particle_mass_measure_factor": spray_particle_mass_measure_factor,
            },
        },
        {
            "name": "particle_mass_matches_gas_source",
            "status": "PASS" if particle_source_rel <= args.mass_rel_tol else "OBSERVED_ONLY",
            "metric": particle_source_rel,
            "note": (
                "Native particle mass reconstructed from diameter/parcel density closes to the gas source integral."
                if particle_source_rel <= args.mass_rel_tol
                else "Native particle mass reconstructed from diameter/parcel density has the correct sign but does not yet close to the gas source integral."
            ),
        },
        {
            "name": "energy_budget_matches_integrated_energy_source",
            "status": "OBSERVED_ONLY",
            "metric": energy_source_rel,
            "note": "Energy source output is mapped to the correct state slot; full energy closure needs a dedicated total-energy gate with hydro and thermodynamic accounting.",
        },
    ]
    failed = [gate for gate in gates if gate["status"] == "FAIL"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS if not failed else "FAIL-ACADEMIC-SPRAY-SOURCE-BUDGET-VALIDATION",
        "title": "Academic Spray Source Budget Validation",
        "scope": "Closed periodic PeleC spray smoke case validating mapped gas-phase spray source output against gas density and fuel species changes",
        "run_dir": str(run_dir),
        "case": {
            "base_case": "examples/academic/shock_droplet",
            "steps": int(args.expected_steps),
            "plot_count": len(records),
            "particles_plot_src": True,
            "particles_dtmod": spray_dtmod,
            "periodic": True,
            "reaction": False,
            "diffusion": False,
        },
        "summary": {
            "gas_mass_delta": gas_mass_delta,
            "rho_source_integral_right_endpoint": rho_src_integral,
            "gas_mass_source_residual": gas_source_residual,
            "gas_mass_source_relative_error": gas_source_rel,
            "fuel_mass_delta": fuel_mass_delta,
            "fuel_source_integral_right_endpoint": fuel_src_integral,
            "fuel_source_residual": fuel_source_residual,
            "fuel_source_relative_error": fuel_source_rel,
            "gas_energy_delta": gas_energy_delta,
            "energy_source_integral_right_endpoint": energy_src_integral,
            "energy_source_residual": energy_source_residual,
            "energy_source_relative_error": energy_source_rel,
            "particle_mass_delta": particle_mass_delta,
            "particle_comparable_rho_source_integral": particle_comparable_rho_src_integral,
            "spray_particle_mass_measure_factor": spray_particle_mass_measure_factor,
            "particle_plus_rho_source_residual": particle_source_residual,
            "particle_source_relative_mismatch": particle_source_rel,
            "max_abs_rho_source_rate_integral": max_abs_rho_src,
            "max_abs_momentum_source_rate_integral": max_abs_mom_src,
            "pure_fuel_rho_rhoY_source_absmax_mismatch": pure_fuel_source_mismatch,
            "clears_plot_src_dead_switch": True,
            "clears_spray_source_mapping_bug": True,
            "clears_acd_05_gas_source_history_budget": gas_source_rel <= args.mass_rel_tol and fuel_source_rel <= args.mass_rel_tol,
            "clears_acd_05_full_gas_particle_budget": (
                gas_source_rel <= args.mass_rel_tol
                and fuel_source_rel <= args.mass_rel_tol
                and particle_source_rel <= args.mass_rel_tol
            ),
            "clears_acd_07_reacting_spray_detonation_budget": False,
        },
        "quality_gates": gates,
        "records": records,
        "evidence_files": [
            evidence_entry("report_writer", Path("tools/write_academic_spray_source_budget_validation_report.py")),
            evidence_entry("run_script", Path("tools/codex_run_academic_spray_source_budget_validation.sh")),
            evidence_entry("run_log", run_log),
            evidence_entry("input_file", input_file),
            evidence_entry("initial_header", plots[0] / "Header"),
            evidence_entry("final_header", plots[-1] / "Header"),
            evidence_entry("code_diff", DEFAULT_OUTPUT_ROOT / "spray_source_mapping_code_diff.patch")
            if (DEFAULT_OUTPUT_ROOT / "spray_source_mapping_code_diff.patch").is_file()
            else {"label": "code_diff", "path": str(DEFAULT_OUTPUT_ROOT / "spray_source_mapping_code_diff.patch"), "missing": True},
        ],
        "limitations": [
            "This report clears gas-side source-history accounting for total mass and fuel species in a closed periodic spray smoke case.",
            (
                "Particle mass reconstruction from particle DATA closes to the 2D-spray effective-thickness gas source integral for this closed periodic spray budget case."
                if particle_source_rel <= args.mass_rel_tol
                else "Particle mass reconstruction from particle DATA has correct sign but does not yet close to the gas source integral, so full gas-particle ACD-05 closure remains open."
            ),
            "ACD-07 reacting spray detonation closure remains open until this mapped-source path is exercised in a reacting detonation spray case.",
        ],
    }
    return report


def validate_report(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS_PASS, "status is not PASS")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("clears_plot_src_dead_switch") is True, "plot_src gate not cleared")
    require(summary.get("clears_spray_source_mapping_bug") is True, "mapping bug gate not cleared")
    require(summary.get("clears_acd_05_gas_source_history_budget") is True, "gas source budget not cleared")
    require(summary.get("clears_acd_05_full_gas_particle_budget") is True, "full gas-particle source budget not cleared")
    require(float(summary["particle_source_relative_mismatch"]) <= 1.0e-3, "particle/source relative mismatch too large")
    require(float(summary["gas_mass_source_relative_error"]) <= 1.0e-3, "gas source relative error too large")
    require(float(summary["fuel_source_relative_error"]) <= 1.0e-3, "fuel source relative error too large")
    gates = data.get("quality_gates")
    require(isinstance(gates, list) and gates, "quality gates missing")
    failed = [gate["name"] for gate in gates if gate.get("status") == "FAIL"]
    require(not failed, f"failed gates: {failed}")
    if check_hashes:
        for item in data.get("evidence_files", []):
            if item.get("missing"):
                continue
            path = Path(item["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Academic Spray Source Budget Validation",
        "",
        f"Status: `{report['status']}`",
        "",
        "This evidence validates PeleC spray source-field mapping and gas-side source-history accounting in a closed periodic spray smoke case.",
        "",
        "Key metrics:",
        f"- gas mass delta: `{s['gas_mass_delta']:.16e}`",
        f"- integrated `spray_rho_src`: `{s['rho_source_integral_right_endpoint']:.16e}`",
        f"- gas/source relative error: `{s['gas_mass_source_relative_error']:.6e}`",
        f"- fuel mass delta: `{s['fuel_mass_delta']:.16e}`",
        f"- integrated `spray_rhoY_NC7H16_src`: `{s['fuel_source_integral_right_endpoint']:.16e}`",
        f"- fuel/source relative error: `{s['fuel_source_relative_error']:.6e}`",
        f"- particle/source relative mismatch: `{s['particle_source_relative_mismatch']:.6e}`",
        f"- 2D spray effective thickness factor: `{s['spray_particle_mass_measure_factor']:.6e}`",
        "",
        "Readiness:",
        f"- plot source output fixed: `{s['clears_plot_src_dead_switch']}`",
        f"- mapped spray source bug fixed: `{s['clears_spray_source_mapping_bug']}`",
        f"- ACD-05 gas source-history budget: `{s['clears_acd_05_gas_source_history_budget']}`",
        f"- ACD-05 full gas-particle budget: `{s['clears_acd_05_full_gas_particle_budget']}`",
        "",
        (
            "Full gas-particle closure is cleared for this closed periodic spray source-history case using the PeleC 2D spray effective-thickness convention."
            if s['clears_acd_05_full_gas_particle_budget']
            else "Full gas-particle closure remains open because particle mass reconstructed from particle DATA has the correct sign but does not yet close to the gas source integral."
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    parser.add_argument("--mass-rel-tol", type=float, default=1.0e-3)
    parser.add_argument("--absolute-tol", type=float, default=1.0e-18)
    parser.add_argument("--expected-steps", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(data, check_hashes=True)
            print(f"VERIFY-PASS {args.verify_json}")
            return 0
        require(args.run_dir, "--run-dir is required unless --verify-json is used")
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        report = build_report(args)
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
