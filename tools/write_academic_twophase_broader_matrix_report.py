#!/usr/bin/env python3
"""Write/verify academic broader two-phase matrix readiness evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-TWOPHASE-BROADER-MATRIX-AUDIT"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730")
DEFAULT_JSON = DEFAULT_ROOT / "academic_twophase_broader_matrix_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_twophase_broader_matrix_report.md"

REPORTS = {
    "rayleigh_taylor": Path("docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/academic_twophase_rayleigh_taylor_validation_report.json"),
    "interface_amr": Path("docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/academic_twophase_interface_amr_validation_report.json"),
    "bubble_short": Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json"),
    "bubble_inviscid_long": Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_inviscid_long_window_validation_20260729/academic_twophase_bubble_rise_inviscid_long_window_validation_report.json"),
    "bubble_mol_long": Path("docs/codex_audit/evidence/academic_twophase_bubble_rise_mol_long_window_validation_20260729/academic_twophase_bubble_rise_mol_long_window_validation_report.json"),
    "qlt03_closure": Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_closure_20260730/qlt03_lm_csf_stress_closure_report.json"),
    "shock_bubble_operator_preflight": Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_operator_preflight_20260730/academic_twophase_shock_bubble_operator_preflight_report.json"),
    "shock_bubble_cfd_scout": Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730/academic_twophase_shock_bubble_cfd_scout_report.json"),
    "shock_bubble_validation": Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_validation_20260730/academic_twophase_shock_bubble_validation_report.json"),
    "gas_liquid_detonation_certification": Path("docs/codex_audit/evidence/academic_gas_liquid_detonation_certification_20260731/academic_gas_liquid_detonation_certification_report.json"),
    "droplet_response": Path("docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/academic_droplet_euler_lagrange_validation_report.json"),
    "spray_response": Path("docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/academic_spray_detonation_validation_report.json"),
    "spray_coupled_residual": Path("docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.json"),
    "readiness_delta": Path("docs/codex_audit/evidence/academic_readiness_qlt03_closure_delta_20260730/academic_readiness_qlt03_closure_delta_report.json"),
}

SOURCES = {
    "two_phase_hllc": Path("src/academic/twophase/TwoPhaseHLLC.H"),
    "csf": Path("src/academic/twophase/CSF.H"),
    "vof_advection_example": Path("examples/academic/vof_advection_1D/inputs"),
    "rt_example": Path("examples/academic/rayleigh_taylor/inputs"),
    "bubble_example": Path("examples/academic/bubble_rise/inputs"),
    "qlt03_example": Path("examples/academic/qlt03_lm_aux_bridge/inputs"),
    "shock_bubble_scout_example": Path("examples/academic/shock_bubble/inputs"),
    "shock_droplet_example": Path("examples/academic/shock_droplet/inputs"),
    "spray_example": Path("examples/academic/spray_test/inputs"),
}


class ReportError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def status_passes(report: dict[str, Any]) -> bool:
    return str(report.get("status", "")).startswith("PASS-")


def evidence_entry(name: str, path: Path) -> dict[str, Any]:
    return {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256(path) if path.is_file() else None,
    }


def gate(name: str, passed: bool, metric: Any, target: Any, evidence: list[str], gap: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "NOT_READY",
        "metric": metric,
        "target": target,
        "evidence": evidence,
        "gap": gap,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report_paths = {name: Path(path) for name, path in REPORTS.items()}
    source_paths = {name: Path(path) for name, path in SOURCES.items()}
    missing = [str(path) for path in [*report_paths.values(), *source_paths.values()] if not path.exists()]
    if missing:
        raise ReportError(f"missing required evidence/source files: {missing}")

    reports = {name: load_json(path) for name, path in report_paths.items()}
    summaries = {name: data.get("summary", {}) for name, data in reports.items()}

    rt_ready = (
        reports["rayleigh_taylor"].get("status") == "PASS-ACADEMIC-TWOPHASE-RAYLEIGH-TAYLOR-VALIDATION"
        and summaries["rayleigh_taylor"].get("clears_acd_04_two_phase_validation_gap") is True
    )
    interface_amr_ready = (
        reports["interface_amr"].get("status") == "PASS-ACADEMIC-TWOPHASE-INTERFACE-AMR-VALIDATION"
        and summaries["interface_amr"].get("clears_acd_08_two_phase_interface_amr_gap") is True
    )
    bubble_basic_ready = (
        reports["bubble_short"].get("status") == "PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION"
        and summaries["bubble_short"].get("clears_qlt_03_short_time_bubble_response_gap") is True
        and status_passes(reports["bubble_inviscid_long"])
        and summaries["bubble_inviscid_long"].get("clears_inviscid_long_window_bubble_rise_stability") is True
        and status_passes(reports["bubble_mol_long"])
        and summaries["bubble_mol_long"].get("clears_mol_long_window_bubble_rise_stability") is True
    )
    qlt03_ready = (
        reports["qlt03_closure"].get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CLOSURE"
        and summaries["qlt03_closure"].get("academic_twophase_qlt03_blocker_closed") is True
        and summaries["qlt03_closure"].get("qlt03_low_mach_hysing_case1_current_grid_confirmed") is True
    )
    acd04_vof_ready = rt_ready and bubble_basic_ready and qlt03_ready
    acd06_csf_ready = qlt03_ready and summaries["qlt03_closure"].get("preferred_surface_tension_force_form_for_qlt03") == 3
    acd08_interface_amr_ready = interface_amr_ready

    droplet_response_ready = (
        reports["droplet_response"].get("status") == "PASS-ACADEMIC-DROPLET-EULER-LAGRANGE-VALIDATION"
        and summaries["droplet_response"].get("clears_acd_05_response_gate") is True
    )
    spray_response_ready = (
        reports["spray_response"].get("status") == "PASS-ACADEMIC-SPRAY-DETONATION-VALIDATION"
        and summaries["spray_response"].get("clears_acd_07_reacting_spray_response_gate") is True
    )
    gas_liquid_full_ready = (
        reports["gas_liquid_detonation_certification"].get("status") == "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CERTIFICATION"
        and summaries["gas_liquid_detonation_certification"].get("acd_07_full_gas_liquid_detonation_ready") is True
        and summaries["gas_liquid_detonation_certification"].get("clears_acd_07_spray_detonation_gap") is True
    )
    coupled_budget_ready = (
        reports["spray_coupled_residual"].get("status", "").startswith("PASS-")
        and summaries["spray_coupled_residual"].get("clears_full_closed_gas_particle_budget_gap") is True
    )
    shock_bubble_operator_preflight_ready = (
        reports["shock_bubble_operator_preflight"].get("status") == "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-OPERATOR-PREFLIGHT"
        and summaries["shock_bubble_operator_preflight"].get("shock_bubble_operator_preflight_ready") is True
        and summaries["shock_bubble_operator_preflight"].get("shock_bubble_full_cfd_validation_ready") is False
    )
    shock_bubble_cfd_scout_attempted = (
        reports["shock_bubble_cfd_scout"].get("status") in {
            "NOT_READY-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT",
            "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT",
        }
        and summaries["shock_bubble_cfd_scout"].get("shock_bubble_cfd_scout_run_completed") is True
        and summaries["shock_bubble_cfd_scout"].get("shock_bubble_cfd_scout_stable_no_abort") is True
    )
    shock_bubble_cfd_scout_ready = (
        reports["shock_bubble_cfd_scout"].get("status") == "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT"
        and summaries["shock_bubble_cfd_scout"].get("shock_bubble_cfd_scout_ready") is True
    )
    shock_bubble_validation_ready = (
        reports["shock_bubble_validation"].get("status") == "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-VALIDATION"
        and summaries["shock_bubble_validation"].get("shock_bubble_independent_validation_ready") is True
    )

    readiness_delta_summary = summaries["readiness_delta"]
    readiness_delta_consumed = (
        reports["readiness_delta"].get("status") == "PASS-ACADEMIC-READINESS-QLT03-CSF-STRESS-DELTA"
        and readiness_delta_summary.get("academic_twophase_qlt03_low_mach_hysing_case1_ready") is True
        and readiness_delta_summary.get("academic_twophase_full_matrix_ready") is False
    )

    full_broader_matrix_ready = (
        acd04_vof_ready
        and acd06_csf_ready
        and acd08_interface_amr_ready
        and shock_bubble_operator_preflight_ready
        and shock_bubble_validation_ready
        and droplet_response_ready
        and spray_response_ready
        and gas_liquid_full_ready
        and coupled_budget_ready
    )

    gates = [
        gate("acd_04_vof_rt_bubble_qlt03_core", acd04_vof_ready, {
            "rt_ready": rt_ready,
            "bubble_basic_ready": bubble_basic_ready,
            "qlt03_ready": qlt03_ready,
        }, "RT, bubble response/stability, and QLT-03 current-grid closure all pass", [
            str(report_paths["rayleigh_taylor"]),
            str(report_paths["bubble_short"]),
            str(report_paths["qlt03_closure"]),
        ]),
        gate("acd_06_csf_surface_tension", acd06_csf_ready, {
            "preferred_force_form": summaries["qlt03_closure"].get("preferred_surface_tension_force_form_for_qlt03"),
            "qlt03_ready": qlt03_ready,
        }, "CSF stress-divergence form passes QLT-03 low-Mach Hysing Case 1", [str(report_paths["qlt03_closure"])]),
        gate("acd_08_interface_amr", acd08_interface_amr_ready, summaries["interface_amr"], "interface-refined AMR validation pass", [str(report_paths["interface_amr"])]),
        gate("shock_bubble_operator_preflight", shock_bubble_operator_preflight_ready, summaries["shock_bubble_operator_preflight"], "operator-level shock-interface HLLC/EOS/CSF preflight passes", [str(report_paths["shock_bubble_operator_preflight"])]),
        gate("shock_bubble_cfd_scout_attempt", shock_bubble_cfd_scout_attempted or shock_bubble_cfd_scout_ready, {
            "scout_attempted": shock_bubble_cfd_scout_attempted,
            "scout_ready": shock_bubble_cfd_scout_ready,
            **summaries["shock_bubble_cfd_scout"],
        }, "full-CFD scout is documented and may be ready when stability, physical extrema, dt health, and interface response gates pass", [str(report_paths["shock_bubble_cfd_scout"]), str(source_paths["shock_bubble_scout_example"])]),
        gate("shock_bubble_independent_validation", shock_bubble_validation_ready, {
            "operator_preflight_ready": shock_bubble_operator_preflight_ready,
            "cfd_scout_attempted": shock_bubble_cfd_scout_attempted,
            "cfd_scout_ready": shock_bubble_cfd_scout_ready,
            "validation_ready": shock_bubble_validation_ready,
            **summaries["shock_bubble_validation"],
        }, "dedicated shock-bubble validation report passes", [str(report_paths["shock_bubble_validation"]), str(report_paths["shock_bubble_operator_preflight"]), str(report_paths["shock_bubble_cfd_scout"])], ""),
        gate("acd_05_droplet_response", droplet_response_ready, summaries["droplet_response"], "Euler-Lagrange droplet response gate pass", [str(report_paths["droplet_response"])]),
        gate("acd_07_reacting_spray_response", spray_response_ready, summaries["spray_response"], "reacting spray response gate pass", [str(report_paths["spray_response"])]),
        gate("acd_07_full_gas_liquid_detonation", gas_liquid_full_ready, summaries["gas_liquid_detonation_certification"], "full gas-liquid detonation certification pass", [str(report_paths["gas_liquid_detonation_certification"]), str(report_paths["spray_response"]), str(report_paths["spray_coupled_residual"])], ""),
        gate(
            "closed_gas_particle_coupled_budget",
            coupled_budget_ready,
            summaries["spray_coupled_residual"],
            "closed gas+particle coupled budget residual pass",
            [str(report_paths["spray_coupled_residual"])],
            "" if coupled_budget_ready else "Current coupled residual report is NOT_READY.",
        ),
        gate("readiness_delta_consumed", readiness_delta_consumed, readiness_delta_summary, "QLT-03 closure consumed by high-level readiness delta", [str(report_paths["readiness_delta"])]),
    ]

    blocking_gaps = [item["name"] for item in gates if item["status"] != "PASS"]
    summary = {
        "acd_04_vof_core_ready": acd04_vof_ready,
        "acd_06_csf_ready": acd06_csf_ready,
        "acd_08_interface_amr_ready": acd08_interface_amr_ready,
        "qlt03_low_mach_hysing_case1_ready": qlt03_ready,
        "shock_bubble_operator_preflight_ready": shock_bubble_operator_preflight_ready,
        "shock_bubble_cfd_scout_attempted": shock_bubble_cfd_scout_attempted,
        "shock_bubble_cfd_scout_ready": shock_bubble_cfd_scout_ready,
        "shock_bubble_independent_validation_ready": shock_bubble_validation_ready,
        "acd_05_droplet_response_ready": droplet_response_ready,
        "acd_07_reacting_spray_response_ready": spray_response_ready,
        "acd_07_full_gas_liquid_detonation_ready": gas_liquid_full_ready,
        "closed_gas_particle_coupled_budget_ready": coupled_budget_ready,
        "academic_twophase_broader_matrix_ready": full_broader_matrix_ready,
        "blocking_gap_count": len(blocking_gaps),
        "blocking_gaps": blocking_gaps,
        "progress_interpretation": "VOF/RT/bubble/CSF/AMR evidence is now substantially ready, including the QLT-03 CSF-stress closure. Shock-bubble now has operator-level HLLC/EOS/CSF preflight evidence, an EOS-consistent full-CFD scout pass, and a dedicated independent validation report. The broader academic two-phase matrix remains open because full gas-liquid detonation certification and closed gas+particle coupled-budget residual gates are not ready.",
    }

    return {
        "schema_version": 1,
        "status": STATUS,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "Academic broader two-phase matrix audit against master-plan ACD-04/05/06/07/08 and QLT-03 evidence.",
        "summary": summary,
        "gates": gates,
        "source_files": {name: str(path) for name, path in source_paths.items()},
        "input_reports": {name: str(path) for name, path in report_paths.items()},
        "evidence": [
            *(evidence_entry(name, path) for name, path in report_paths.items()),
            *(evidence_entry(name, path) for name, path in source_paths.items()),
            evidence_entry("matrix_writer", Path("tools/write_academic_twophase_broader_matrix_report.py")),
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Academic Broader Two-Phase Matrix",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- ACD-04 VOF core ready: `{summary['acd_04_vof_core_ready']}`",
        f"- ACD-06 CSF ready: `{summary['acd_06_csf_ready']}`",
        f"- ACD-08 interface AMR ready: `{summary['acd_08_interface_amr_ready']}`",
        f"- Broader academic two-phase matrix ready: `{summary['academic_twophase_broader_matrix_ready']}`",
        f"- Blocking gaps: `{summary['blocking_gap_count']}`",
        "",
        "## Gates",
        "",
    ]
    for item in report["gates"]:
        lines.append(f"- `{item['status']}` {item['name']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_report(report: dict[str, Any]) -> None:
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ReportError(message)

    require(report.get("status") == STATUS, "unexpected matrix status")
    summary = report.get("summary", {})
    require(summary.get("acd_04_vof_core_ready") is True, "ACD-04 VOF core should be ready")
    require(summary.get("acd_06_csf_ready") is True, "ACD-06 CSF should be ready")
    require(summary.get("acd_08_interface_amr_ready") is True, "ACD-08 interface AMR should be ready")
    require(summary.get("qlt03_low_mach_hysing_case1_ready") is True, "QLT-03 closure should be consumed")
    require(summary.get("shock_bubble_operator_preflight_ready") is True, "shock-bubble operator preflight should be ready")
    require(summary.get("academic_twophase_broader_matrix_ready") is True, "broader matrix should now be ready after closing named residual gaps")
    for name in ():
        require(summary.get(name) is False, f"expected residual gap flag to remain false: {name}")
    expected_gaps = set()
    require(set(summary.get("blocking_gaps", [])) == expected_gaps, "expected no residual broader two-phase gaps")
    gates = {item.get("name"): item.get("status") for item in report.get("gates", [])}
    require(summary.get("shock_bubble_cfd_scout_attempted") is True, "shock-bubble CFD scout attempt should be documented")
    require(summary.get("shock_bubble_cfd_scout_ready") is True, "shock-bubble CFD scout should now be physical-ready")
    require(summary.get("shock_bubble_independent_validation_ready") is True, "shock-bubble independent validation should now be ready")
    require(summary.get("closed_gas_particle_coupled_budget_ready") is True, "closed gas-particle coupled budget should now be ready")
    require(summary.get("acd_07_full_gas_liquid_detonation_ready") is True, "ACD-07 gas-liquid detonation certification should now be ready")
    require(summary.get("academic_twophase_broader_matrix_ready") is True, "broader academic two-phase matrix should now be ready")
    for name in ("acd_04_vof_rt_bubble_qlt03_core", "acd_06_csf_surface_tension", "acd_08_interface_amr", "shock_bubble_operator_preflight", "shock_bubble_cfd_scout_attempt", "acd_05_droplet_response", "acd_07_reacting_spray_response", "readiness_delta_consumed"):
        require(gates.get(name) == "PASS", f"expected PASS gate missing: {name}")
    for name in expected_gaps:
        require(gates.get(name) == "NOT_READY", f"expected NOT_READY gate missing: {name}")
    for entry in report.get("evidence", []):
        path = Path(str(entry.get("path", "")))
        require(path.is_file(), f"missing evidence/source file: {path}")
        require(sha256(path) == entry.get("sha256"), f"sha256 mismatch: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()

    if args.verify_json:
        report = load_json(args.verify_json)
        verify_report(report)
        print(
            "academic_twophase_broader_matrix VERIFY-PASS "
            f"json={args.verify_json} status={report['status']} "
            f"ready={report['summary']['academic_twophase_broader_matrix_ready']}"
        )
        return 0

    report = build_report(args)
    verify_report(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(report, args.markdown)
    print(
        "academic_twophase_broader_matrix PASS "
        f"json={args.output} status={report['status']} "
        f"ready={report['summary']['academic_twophase_broader_matrix_ready']} "
        f"gaps={report['summary']['blocking_gap_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
