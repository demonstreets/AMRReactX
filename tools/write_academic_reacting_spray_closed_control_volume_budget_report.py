#!/usr/bin/env python3
"""Write/verify ACD-07 reacting spray closed control-volume budget evidence."""
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
import write_academic_spray_closed_control_volume_budget_report as base_budget  # noqa: E402
from write_academic_droplet_spray_budget_preflight_report import field  # noqa: E402

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ACADEMIC-REACTING-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729")
DEFAULT_JSON = DEFAULT_ROOT / "academic_reacting_spray_closed_control_volume_budget_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_reacting_spray_closed_control_volume_budget_report.md"
REACTING_FIELDS = ("heatRelease", "rhoe_dot", "Y(NC7H16)", "Y(O2)", "Y(N2)", "Temp", "pressure")


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


def parse_inputs(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        lhs, rhs = line.split("=", 1)
        values[lhs.strip()] = rhs.strip().strip('"')
    return values


def stats(arr: np.ndarray) -> dict[str, float]:
    require(np.isfinite(arr).all(), "non-finite plot field")
    return {"min": float(np.min(arr)), "max": float(np.max(arr)), "sum": float(np.sum(arr)), "absmax": float(np.max(np.abs(arr)))}


def reaction_records(run_dir: Path) -> list[dict[str, Any]]:
    plots = sorted(run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
    require(len(plots) >= 3, f"need at least 3 plotfiles, found {len(plots)}")
    rows: list[dict[str, Any]] = []
    for plot_path in plots:
        plot = amrex_reader.read_plotfile(str(plot_path))
        comps = set(plot.get("comp_names", []))
        missing = [name for name in REACTING_FIELDS if name not in comps]
        require(not missing, f"{plot_path} missing reacting fields: {missing}")
        ysum = field(plot, "Y(NC7H16)") + field(plot, "Y(O2)") + field(plot, "Y(N2)")
        rows.append(
            {
                "path": str(plot_path),
                "time": float(plot["time"]),
                "field_stats": {name: stats(field(plot, name)) for name in REACTING_FIELDS},
                "species_closure_absmax": float(np.max(np.abs(ysum - 1.0))),
            }
        )
    return rows


def input_contract(values: dict[str, str]) -> list[str]:
    expected = {
        "geometry.is_periodic": "1 1",
        "pelec.lo_bc": "Interior Interior",
        "pelec.hi_bc": "Interior Interior",
        "pelec.do_react": "1",
        "pelec.chem_integrator": "ReactorCvode",
        "cvode.solve_type": "dense_direct",
        "pelec.do_spray_particles": "1",
        "particles.mass_transfer": "1",
        "particles.mom_transfer": "1",
        "particles.fixed_parts": "0",
        "particles.plot_src": "1",
        "pelec.plot_rhoy": "1",
        "pelec.plot_massfrac": "1",
    }
    problems: list[str] = []
    for key, want in expected.items():
        got = values.get(key)
        if got != want:
            problems.append(f"{key}={got!r}, expected {want!r}")
    return problems


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir)
    input_file = Path(args.input) if args.input else run_dir / "inputs"
    run_log = Path(args.run_log) if args.run_log else run_dir / "run.log"
    init_file = Path(args.init_file) if args.init_file else run_dir / "initspraydata_2d_single.dat"
    base_args = argparse.Namespace(
        run_dir=str(run_dir),
        input=str(input_file),
        run_log=str(run_log),
        init_file=str(init_file),
        rel_tol=args.rel_tol,
        ymom_abs_tol=args.ymom_abs_tol,
        min_xmom_source=args.min_xmom_source,
    )
    base = base_budget.build_report(base_args)
    base_budget.validate_report(base, check_hashes=False)
    summary0 = base["summary"]
    rels = dict(summary0["relative_errors"])
    source_integrals = dict(summary0["source_integrals"])
    records = reaction_records(run_dir)
    inputs = parse_inputs(input_file)
    contract_errors = input_contract(inputs)
    max_heat_release = max(rec["field_stats"]["heatRelease"]["absmax"] for rec in records)
    max_rhoe_dot = max(rec["field_stats"]["rhoe_dot"]["absmax"] for rec in records)
    max_species_closure = max(float(rec["species_closure_absmax"]) for rec in records)
    min_density = min(rec["field_stats"]["pressure"]["min"] for rec in records)
    min_temp = min(rec["field_stats"]["Temp"]["min"] for rec in records)
    rho_source_abs = abs(float(source_integrals["rho"]))
    energy_source_abs = abs(float(source_integrals["rho_E"]))
    xmom_source_abs = abs(float(source_integrals["xmom"]))
    gates = [
        {"name": "reacting_periodic_closed_control_volume_input_contract", "status": "PASS" if not contract_errors else "FAIL", "metric": contract_errors},
        {"name": "base_closed_control_volume_budget_gates", "status": "PASS", "metric": [gate["name"] for gate in base["quality_gates"]]},
        {"name": "finite_positive_reacting_state", "status": "PASS" if min_density > 0.0 and min_temp > 0.0 else "FAIL", "metric": {"min_pressure": min_density, "min_temp": min_temp}},
        {"name": "reaction_heat_release_present", "status": "PASS" if max_heat_release >= args.min_heat_release_absmax and max_rhoe_dot >= args.min_rhoe_dot_absmax else "FAIL", "metric": {"heatRelease_absmax": max_heat_release, "rhoe_dot_absmax": max_rhoe_dot}},
        {"name": "spray_mass_transfer_present", "status": "PASS" if rho_source_abs >= args.min_rho_source_integral else "FAIL", "metric": rho_source_abs},
        {"name": "spray_momentum_transfer_present", "status": "PASS" if xmom_source_abs >= args.min_xmom_source_integral else "FAIL", "metric": xmom_source_abs},
        {"name": "spray_energy_transfer_present", "status": "PASS" if energy_source_abs >= args.min_energy_source_integral else "FAIL", "metric": energy_source_abs},
        {"name": "gas_mass_source_history_closure", "status": "PASS" if rels["gas_mass"] <= args.rel_tol else "FAIL", "metric": rels["gas_mass"]},
        {"name": "gas_fuel_source_history_closure", "status": "PASS" if rels["gas_fuel"] <= args.rel_tol else "FAIL", "metric": rels["gas_fuel"]},
        {"name": "gas_xmomentum_source_history_closure", "status": "PASS" if rels["gas_xmom"] <= args.rel_tol else "FAIL", "metric": rels["gas_xmom"]},
        {"name": "gas_total_energy_source_history_closure", "status": "PASS" if rels["gas_rho_E"] <= args.rel_tol else "FAIL", "metric": rels["gas_rho_E"]},
        {"name": "particle_mass_thickness_scaled_source_closure", "status": "PASS" if rels["particle_mass"] <= args.rel_tol else "FAIL", "metric": rels["particle_mass"]},
        {"name": "particle_xmomentum_thickness_scaled_source_closure", "status": "PASS" if rels["particle_xmom"] <= args.rel_tol else "FAIL", "metric": rels["particle_xmom"]},
        {"name": "thickness_scaled_total_mass_control_volume_closure", "status": "PASS" if rels["total_mass"] <= args.rel_tol else "FAIL", "metric": rels["total_mass"]},
        {"name": "thickness_scaled_total_xmomentum_control_volume_closure", "status": "PASS" if rels["total_xmom"] <= args.rel_tol else "FAIL", "metric": rels["total_xmom"]},
        {"name": "species_mass_fraction_closure", "status": "PASS" if max_species_closure <= args.max_species_closure_absmax else "FAIL", "metric": max_species_closure},
    ]
    failed = [gate["name"] for gate in gates if gate["status"] != "PASS"]
    status = STATUS_PASS if not failed else "FAIL-ACADEMIC-REACTING-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET"
    summary = {
        **summary0,
        "base_nonreacting_writer_status": base["status"],
        "reaction_heatRelease_absmax": max_heat_release,
        "reaction_rhoe_dot_absmax": max_rhoe_dot,
        "reaction_species_closure_absmax": max_species_closure,
        "spray_mass_source_integral_abs": rho_source_abs,
        "spray_energy_source_integral_abs": energy_source_abs,
        "spray_xmomentum_source_integral_abs": xmom_source_abs,
        "clears_acd_05_closed_control_volume_mass_momentum_energy_budget": False,
        "clears_acd_07_reacting_control_volume_total_budget": status == STATUS_PASS,
        "clears_acd_07_reacting_control_volume_budget": status == STATUS_PASS,
        "clears_acd_07_full_cellular_gas_liquid_detonation_gap": False,
        "clears_acd_07_external_reference_gap": False,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "title": "Academic Reacting Spray Closed Control-Volume Budget",
        "scope": "PeleC 2D periodic heptane-air reacting spray box with CVODE chemistry, evaporation, drag, spray source plotfields, and thickness-scaled gas-particle mass/momentum plus gas total-energy source-history closure.",
        "case": {
            "run_dir": str(run_dir),
            "input_file": str(input_file),
            "run_log": str(run_log),
            "init_file": str(init_file),
            "periodic": True,
            "reaction": True,
            "chem_integrator": inputs.get("pelec.chem_integrator"),
            "mass_transfer": True,
            "momentum_transfer": True,
        },
        "summary": summary,
        "quality_gates": gates,
        "base_budget_records": base["records"],
        "reaction_records": records,
        "limitations": [
            "This clears a dedicated periodic reacting spray control-volume budget gate for ACD-07; it is not a cellular gas-liquid detonation morphology/reference gate.",
            "Gas total-energy is closed against the PeleC spray energy source history. Native particle plotfile data provide robust mass and momentum budgets; independent liquid enthalpy closure remains outside this plotfile-level gate.",
            "The 2D particle budget follows PeleC's effective-thickness convention; gas integrals are thickness-scaled before total gas-particle mass/momentum comparison.",
        ],
        "evidence_files": [
            evidence_entry("report_writer", Path("tools/write_academic_reacting_spray_closed_control_volume_budget_report.py")),
            evidence_entry("runner", Path("tools/codex_run_academic_reacting_spray_closed_control_volume_budget.sh")),
            evidence_entry("base_budget_writer", Path("tools/write_academic_spray_closed_control_volume_budget_report.py")),
            evidence_entry("input_file", input_file),
            evidence_entry("run_log", run_log),
            evidence_entry("init_file", init_file),
            evidence_entry("initial_plot_header", sorted(run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))[0] / "Header"),
            evidence_entry("final_plot_header", sorted(run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))[-1] / "Header"),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    summary = report.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("clears_acd_07_reacting_control_volume_total_budget") is True, "ACD-07 reacting control-volume budget not cleared")
    require(summary.get("clears_acd_07_full_cellular_gas_liquid_detonation_gap") is False, "full cellular gap must remain false")
    rels = summary.get("relative_errors", {})
    for key in ("gas_mass", "gas_xmom", "gas_rho_E", "gas_fuel", "particle_mass", "particle_xmom", "total_mass", "total_xmom"):
        require(float(rels.get(key, 1.0)) <= 1.0e-3, f"relative error too large: {key}")
    require(float(summary.get("reaction_heatRelease_absmax", 0.0)) > 0.0, "heatRelease absent")
    require(float(summary.get("reaction_rhoe_dot_absmax", 0.0)) > 0.0, "rhoe_dot absent")
    require(float(summary.get("spray_mass_source_integral_abs", 0.0)) > 0.0, "mass transfer absent")
    require(float(summary.get("spray_energy_source_integral_abs", 0.0)) > 0.0, "energy transfer absent")
    gates = report.get("quality_gates", [])
    require(isinstance(gates, list) and gates, "quality gates missing")
    failed = [gate.get("name") for gate in gates if gate.get("status") != "PASS"]
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
        "# Academic Reacting Spray Closed Control-Volume Budget",
        "",
        f"Status: `{report['status']}`",
        "",
        "Key relative errors:",
        f"- gas mass/source: `{r['gas_mass']:.6e}`",
        f"- gas fuel/source: `{r['gas_fuel']:.6e}`",
        f"- gas x-momentum/source: `{r['gas_xmom']:.6e}`",
        f"- gas total-energy/source: `{r['gas_rho_E']:.6e}`",
        f"- particle mass/source: `{r['particle_mass']:.6e}`",
        f"- particle x-momentum/source: `{r['particle_xmom']:.6e}`",
        f"- total mass closure: `{r['total_mass']:.6e}`",
        f"- total x-momentum closure: `{r['total_xmom']:.6e}`",
        "",
        "Reaction/source signals:",
        f"- heatRelease absmax: `{s['reaction_heatRelease_absmax']:.6e}`",
        f"- rhoe_dot absmax: `{s['reaction_rhoe_dot_absmax']:.6e}`",
        f"- |integrated spray_rho_src|: `{s['spray_mass_source_integral_abs']:.6e}`",
        f"- |integrated spray_eng_src|: `{s['spray_energy_source_integral_abs']:.6e}`",
        "",
        "Readiness:",
        f"- ACD-07 reacting control-volume budget: `{s['clears_acd_07_reacting_control_volume_total_budget']}`",
        f"- full cellular gas-liquid detonation: `{s['clears_acd_07_full_cellular_gas_liquid_detonation_gap']}`",
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
    parser.add_argument("--min-heat-release-absmax", type=float, default=1.0e-8)
    parser.add_argument("--min-rhoe-dot-absmax", type=float, default=1.0e-8)
    parser.add_argument("--min-rho-source-integral", type=float, default=1.0e-16)
    parser.add_argument("--min-xmom-source-integral", type=float, default=1.0e-12)
    parser.add_argument("--min-energy-source-integral", type=float, default=1.0e-6)
    parser.add_argument("--max-species-closure-absmax", type=float, default=2.0e-12)
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(report, check_hashes=True)
            print(f"academic_reacting_spray_closed_control_volume_budget VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        require(args.run_dir, "--run-dir is required")
        report = build_report(args)
        validate_report(report, check_hashes=False)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_md(report, out_md)
        print(f"academic_reacting_spray_closed_control_volume_budget PASS json={out_json} status={report['status']}")
        return 0
    except (ReportError, base_budget.ReportError) as exc:
        print(f"academic_reacting_spray_closed_control_volume_budget FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
