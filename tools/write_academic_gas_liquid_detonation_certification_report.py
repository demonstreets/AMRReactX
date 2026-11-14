#!/usr/bin/env python3
"""Write/verify ACD-07 gas-liquid detonation certification evidence.

The certification deliberately sits above the older reacting-spray response
report. It only passes when the response, source-history budget, and closed
gas-particle control-volume budget reports are all PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cfd_evidence_checks import archived_chemistry


STATUS = "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CERTIFICATION"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_gas_liquid_detonation_certification_20260731")
DEFAULT_JSON = DEFAULT_ROOT / "academic_gas_liquid_detonation_certification_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_gas_liquid_detonation_certification_report.md"

REPORTS = {
    "spray_detonation_response": Path("docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/academic_spray_detonation_validation_report.json"),
    "spray_detonation_source_budget": Path("docs/codex_audit/evidence/academic_spray_detonation_source_budget_validation_20260729/academic_spray_detonation_source_budget_validation_report.json"),
    "reacting_closed_control_volume_budget": Path("docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729/academic_reacting_spray_closed_control_volume_budget_report.json"),
    "coupled_budget_rollup": Path("docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.json"),
    "academic_readiness_summary": Path("docs/codex_audit/evidence/academic_readiness_summary_20260729/academic_readiness_summary_report.json"),
}


class ReportError(RuntimeError):
    pass


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise ReportError(msg)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite(value: Any, label: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ReportError(f"{label} not numeric: {value!r}") from exc
    require(math.isfinite(out), f"{label} not finite: {out!r}")
    return out


def gate(name: str, passed: bool, metric: Any, target: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "NOT_READY",
        "metric": metric,
        "target": target,
        "evidence": evidence,
    }


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    missing = [str(path) for path in REPORTS.values() if not path.exists()]
    require(not missing, f"missing required reports: {missing}")

    reports = {name: load_json(path) for name, path in REPORTS.items()}
    summaries = {name: data.get("summary", {}) for name, data in reports.items()}

    response = reports["spray_detonation_response"]
    response_summary = summaries["spray_detonation_response"]
    chemistry_checks = []
    for case in response.get("cases", []):
        chemistry_checks.append(archived_chemistry(case["plotfile_final"]))
    reactive_mechanism = bool(chemistry_checks) and all(
        item["gas_reactions"] > 0 for item in chemistry_checks)
    # The existing reports contain neither time-resolved cellular metrics nor
    # an external reference comparison. Budget PASS cannot close those gaps.
    cellular_reference_verified = False
    external_reference_verified = False
    source = reports["spray_detonation_source_budget"]
    source_summary = summaries["spray_detonation_source_budget"]
    reacting_cv = reports["reacting_closed_control_volume_budget"]
    reacting_cv_summary = summaries["reacting_closed_control_volume_budget"]
    coupled = reports["coupled_budget_rollup"]
    coupled_summary = summaries["coupled_budget_rollup"]

    response_ready = (
        response.get("status") == "PASS-ACADEMIC-SPRAY-DETONATION-VALIDATION"
        and response_summary.get("clears_acd_07_reacting_spray_response_gate") is True
        and finite(response_summary.get("pressure_front_shift_cells"), "response pressure_front_shift_cells") >= 5.0
        and finite(response_summary.get("heat_release_absmax"), "response heat_release_absmax") >= 1.0
        and finite(response_summary.get("particle_growth_factor"), "response particle_growth_factor") >= 2.0
        and finite(response_summary.get("spray_temp_increase"), "response spray_temp_increase") >= 50.0
        and finite(response_summary.get("spray_x_vel_absmax"), "response spray_x_vel_absmax") >= 100.0
        and finite(response_summary.get("species_closure_rel"), "response species_closure_rel") <= 2.0e-12
    )
    source_budget_ready = (
        source.get("status") == "PASS-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION"
        and source_summary.get("clears_acd_07_reacting_spray_detonation_budget") is True
        and finite(source_summary.get("particle_source_relative_mismatch"), "source particle mismatch") <= 5.0e-3
        and finite(source_summary.get("heatRelease_absmax"), "source heatRelease_absmax") > 0.0
        and finite(source_summary.get("pressure_front_shift_cells"), "source pressure_front_shift_cells") > 0.0
    )
    reacting_cv_ready = (
        reacting_cv.get("status") == "PASS-ACADEMIC-REACTING-SPRAY-CLOSED-CONTROL-VOLUME-BUDGET"
        and reacting_cv_summary.get("clears_acd_07_reacting_control_volume_total_budget") is True
        and finite(reacting_cv_summary.get("relative_errors", {}).get("total_mass"), "reacting CV total mass") <= 1.0e-3
        and finite(reacting_cv_summary.get("relative_errors", {}).get("total_xmom"), "reacting CV total xmom") <= 1.0e-3
        and finite(reacting_cv_summary.get("reaction_heatRelease_absmax"), "reacting CV heat release") > 0.0
    )
    coupled_budget_ready = (
        coupled.get("status") == "PASS-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL"
        and coupled_summary.get("clears_full_closed_gas_particle_budget_gap") is True
        and coupled_summary.get("closed_control_volume_available") is True
        and finite(coupled_summary.get("reacting_closed_control_volume_total_mass_relative_error"), "coupled total mass") <= 1.0e-3
        and finite(coupled_summary.get("reacting_closed_control_volume_total_xmom_relative_error"), "coupled total xmom") <= 1.0e-3
    )
    certification_ready = all([
        reactive_mechanism,
        cellular_reference_verified,
        external_reference_verified,
        response_ready,
        source_budget_ready,
        reacting_cv_ready,
        coupled_budget_ready,
    ])
    # Write an honest NOT_READY report; verification and CLI exit remain failing.

    gates = [
        gate("nonzero_gas_chemistry", reactive_mechanism, chemistry_checks, "archived run mechanism must contain reactions", []),
        gate("cellular_structure_reference", cellular_reference_verified, None, "time-resolved cellular validation required", []),
        gate("external_reference", external_reference_verified, None, "independent reference comparison required", []),
        gate("reacting_spray_detonation_front_response", response_ready, response_summary, "front shift, heat release, particle breakup/growth, evaporation, species closure", [str(REPORTS["spray_detonation_response"])]),
        gate("reacting_spray_source_budget", source_budget_ready, source_summary, "spray detonation source-history budget PASS with finite front motion and heat release", [str(REPORTS["spray_detonation_source_budget"])]),
        gate("reacting_closed_control_volume_budget", reacting_cv_ready, reacting_cv_summary, "reacting periodic gas-particle closed control-volume budget PASS", [str(REPORTS["reacting_closed_control_volume_budget"])]),
        gate("closed_gas_particle_coupled_budget_rollup", coupled_budget_ready, coupled_summary, "full closed gas-particle coupled-budget rollup PASS", [str(REPORTS["coupled_budget_rollup"])]),
    ]

    summary = {
        "acd_07_full_gas_liquid_detonation_ready": certification_ready,
        "clears_acd_07_spray_detonation_gap": certification_ready,
        "clears_acd_07_full_cellular_gas_liquid_detonation_gap": certification_ready,
        "clears_acd_07_external_reference_gap": certification_ready,
        "certification_basis": "raw chemistry and physical evidence required; existing budget rollups are insufficient",
        "chemistry_checks": chemistry_checks,
        "spray_response_pressure_front_shift_cells": response_summary.get("pressure_front_shift_cells"),
        "spray_response_heat_release_absmax": response_summary.get("heat_release_absmax"),
        "spray_response_particle_growth_factor": response_summary.get("particle_growth_factor"),
        "spray_response_spray_temp_increase": response_summary.get("spray_temp_increase"),
        "spray_source_budget_particle_source_relative_mismatch": source_summary.get("particle_source_relative_mismatch"),
        "reacting_cv_total_mass_relative_error": reacting_cv_summary.get("relative_errors", {}).get("total_mass"),
        "reacting_cv_total_xmom_relative_error": reacting_cv_summary.get("relative_errors", {}).get("total_xmom"),
        "coupled_budget_ready": coupled_budget_ready,
        "interpretation": (
            "NOT_READY: existing shock/particle transport budgets do not certify gas-liquid "
            "detonation. The archived heptane_3sp run is nonreacting; cellular and independent "
            "reference validation are absent. Historical metrics are retained as diagnostics."
        ),
    }

    return {
        "schema_version": 2,
        "status": STATUS if certification_ready else "NOT_READY-ACADEMIC-GAS-LIQUID-DETONATION",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "ACD-07 gas-liquid/droplet-cloud reacting spray detonation certification rollup.",
        "summary": summary,
        "gates": gates,
        "input_reports": {name: str(path) for name, path in REPORTS.items()},
        "evidence": [evidence_entry(name, path) for name, path in REPORTS.items()]
        + [evidence_entry("certification_writer", Path("tools/write_academic_gas_liquid_detonation_certification_report.py"))],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Academic Gas-Liquid Detonation Certification",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Gates", ""])
    for item in report["gates"]:
        lines.append(f"- `{item['status']}` {item['name']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_report(report: dict[str, Any]) -> None:
    current = build_report(argparse.Namespace())
    require(current.get("status") == STATUS,
            "raw physical evidence does not certify gas-liquid detonation: "
            + json.dumps(current["summary"]["chemistry_checks"]))
    require(report.get("schema_version") == 2, "obsolete certification schema; re-evaluate raw evidence")
    require(report.get("status") == STATUS, "unexpected certification status")
    summary = report.get("summary", {})
    require(summary.get("acd_07_full_gas_liquid_detonation_ready") is True, "ACD-07 certification flag missing")
    require(summary.get("clears_acd_07_spray_detonation_gap") is True, "spray detonation gap not cleared")
    gates = {item.get("name"): item.get("status") for item in report.get("gates", [])}
    for name in (
        "reacting_spray_detonation_front_response",
        "reacting_spray_source_budget",
        "reacting_closed_control_volume_budget",
        "closed_gas_particle_coupled_budget_rollup",
    ):
        require(gates.get(name) == "PASS", f"expected PASS gate missing: {name}")
    for item in report.get("evidence", []):
        path = Path(str(item.get("path", "")))
        require(path.is_file(), f"missing evidence: {path}")
        require(sha256(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    parser.add_argument("--verify-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify_json:
        report = json.loads(args.verify_json.read_text(encoding="utf-8"))
        verify_report(report)
        print(
            "academic_gas_liquid_detonation_certification VERIFY-PASS "
            f"json={args.verify_json} status={report['status']}"
        )
        return 0
    report = build_report(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.markdown)
    if report["status"] != STATUS:
        print(f"academic_gas_liquid_detonation_certification NOT_READY json={args.output}")
        return 2
    verify_report(report)
    print(f"academic_gas_liquid_detonation_certification PASS json={args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
