#!/usr/bin/env python3
"""Build and verify the academic readiness summary evidence report."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs/codex_audit/evidence/academic_readiness_summary_20260729/academic_readiness_summary_report.json"

REPORTS = {
    "gas_readiness": "docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/academic_gas_detonation_readiness_report.json",
    "weno5": "docs/codex_audit/evidence/academic_weno5_convergence_validation_20260729/academic_weno5_convergence_validation_report.json",
    "double_mach": "docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.json",
    "mms_constant": "docs/codex_audit/evidence/academic_mms_shim_validation_20260728/academic_mms_shim_validation_report.json",
    "mms_nonconstant": "docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729/academic_mms_nonconstant_density_shim_validation_report.json",
    "twophase_rt": "docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/academic_twophase_rayleigh_taylor_validation_report.json",
    "twophase_interface_amr": "docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/academic_twophase_interface_amr_validation_report.json",
    "bubble_rise": "docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json",
    "bubble_rise_inviscid_long": "docs/codex_audit/evidence/academic_twophase_bubble_rise_inviscid_long_window_validation_20260729/academic_twophase_bubble_rise_inviscid_long_window_validation_report.json",
    "bubble_rise_mol_long": "docs/codex_audit/evidence/academic_twophase_bubble_rise_mol_long_window_validation_20260729/academic_twophase_bubble_rise_mol_long_window_validation_report.json",
    "canonical_bubble_rise_reference": "docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_reference_20260729/academic_twophase_canonical_bubble_rise_reference_report.json",
    "canonical_bubble_candidate": "docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_candidate_20260730/canonical_bubble_rise_candidate_report.json",
    "droplet_euler_lagrange": "docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/academic_droplet_euler_lagrange_validation_report.json",
    "spray_detonation": "docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/academic_spray_detonation_validation_report.json",
    "spray_closed_particle_budget": "docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/academic_spray_closed_particle_budget_report.json",
    "spray_closed_control_volume_budget": "docs/codex_audit/evidence/academic_spray_closed_control_volume_budget_20260729/academic_spray_closed_control_volume_budget_report.json",
    "reacting_spray_closed_control_volume_budget": "docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729/academic_reacting_spray_closed_control_volume_budget_report.json",
    "spray_source_budget": "docs/codex_audit/evidence/academic_spray_source_budget_validation_20260729/academic_spray_source_budget_validation_report.json",
    "spray_detonation_source_budget": "docs/codex_audit/evidence/academic_spray_detonation_source_budget_validation_20260729/academic_spray_detonation_source_budget_validation_report.json",
    "spray_coupled_budget_residual": "docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.json",
    "gpu_preflight": "docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/academic_gpu_environment_preflight_report.json",
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def load_report(path: str) -> dict[str, Any]:
    full = REPO_ROOT / path
    if not full.is_file():
        raise FileNotFoundError(path)
    return json.loads(full.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def status_passes(report: dict[str, Any]) -> bool:
    return str(report.get("status", "")).startswith("PASS")


def gate(name: str, status: str, evidence: list[str], gap: str = "") -> dict[str, Any]:
    return {"name": name, "status": status, "evidence": evidence, "gap": gap}


def build_report() -> dict[str, Any]:
    reports = {name: load_report(path) for name, path in REPORTS.items()}
    summaries = {name: data.get("summary", {}) for name, data in reports.items()}

    gas_ready = (
        status_passes(reports["gas_readiness"])
        and summaries["gas_readiness"].get("clears_acd_02") is True
        and summaries["gas_readiness"].get("clears_acd_03") is True
        and status_passes(reports["weno5"])
        and summaries["weno5"].get("clears_acd_01_weno5_order_gap") is True
        and status_passes(reports["double_mach"])
        and status_passes(reports["mms_constant"])
        and status_passes(reports["mms_nonconstant"])
    )

    two_phase_vof_initial_ready = (
        status_passes(reports["twophase_rt"])
        and status_passes(reports["twophase_interface_amr"])
        and summaries["twophase_interface_amr"].get("clears_acd_08_two_phase_interface_amr_gap") is True
        and status_passes(reports["bubble_rise"])
        and summaries["bubble_rise"].get("clears_qlt_03_short_time_bubble_response_gap") is True
        and summaries["bubble_rise"].get("clears_inviscid_long_window_bubble_rise_stability") is True
        and summaries["bubble_rise"].get("clears_mol_long_window_bubble_rise_stability") is True
        and status_passes(reports["bubble_rise_inviscid_long"])
        and status_passes(reports["bubble_rise_mol_long"])
    )
    canonical_bubble_ready = (
        status_passes(reports["canonical_bubble_rise_reference"])
        and summaries["canonical_bubble_rise_reference"].get("clears_qlt_03_canonical_long_time_bubble_rise_gap") is True
    )

    spray_response_ready = status_passes(reports["droplet_euler_lagrange"]) and status_passes(reports["spray_detonation"])
    spray_source_summary = summaries["spray_source_budget"]
    spray_det_source_summary = summaries["spray_detonation_source_budget"]
    spray_acd05_source_budget_ready = (
        status_passes(reports["spray_source_budget"])
        and spray_source_summary.get("clears_acd_05_gas_source_history_budget") is True
        and spray_source_summary.get("clears_acd_05_full_gas_particle_budget") is True
    )
    spray_acd07_source_budget_ready = (
        status_passes(reports["spray_detonation_source_budget"])
        and spray_det_source_summary.get("clears_acd_07_reacting_spray_detonation_budget") is True
        and spray_det_source_summary.get("clears_acd_07_reacting_gas_mass_energy_source_budget") is True
    )
    spray_acd05_control_volume_ready = (
        status_passes(reports["spray_closed_control_volume_budget"])
        and summaries["spray_closed_control_volume_budget"].get("clears_acd_05_closed_control_volume_mass_momentum_energy_budget") is True
    )
    spray_acd07_reacting_control_volume_ready = (
        status_passes(reports["reacting_spray_closed_control_volume_budget"])
        and summaries["reacting_spray_closed_control_volume_budget"].get("clears_acd_07_reacting_control_volume_total_budget") is True
    )
    spray_source_budget_ready = spray_acd05_source_budget_ready and spray_acd07_source_budget_ready
    spray_reacting_control_volume_ready = spray_acd07_reacting_control_volume_ready
    spray_full_detonation_ready = summaries["spray_detonation"].get("clears_acd_07_spray_detonation_gap") is True
    gpu_environment_ready = summaries["gpu_preflight"].get("ready_for_acd_10_gpu_credit") is True

    gates = [
        gate("acd_01_weno5_convergence", "PASS" if summaries["weno5"].get("clears_acd_01_weno5_order_gap") is True else "NOT_READY", [REPORTS["weno5"]]),
        gate("acd_02_chemistry_readiness", "PASS" if summaries["gas_readiness"].get("clears_acd_02") is True else "NOT_READY", [REPORTS["gas_readiness"]]),
        gate("acd_03_gas_detonation_2d_3d_amr", "PASS" if gas_ready else "NOT_READY", [REPORTS["gas_readiness"], REPORTS["double_mach"]]),
        gate("acd_04_vof_twophase_initial_readiness", "PASS" if two_phase_vof_initial_ready else "NOT_READY", [REPORTS["twophase_rt"], REPORTS["twophase_interface_amr"], REPORTS["bubble_rise"]]),
        gate("qlt_03_canonical_bubble_rise_reference", "PASS" if canonical_bubble_ready else "NOT_READY", [REPORTS["bubble_rise"], REPORTS["canonical_bubble_candidate"], REPORTS["canonical_bubble_rise_reference"]], "External/canonical long-time bubble-rise deformation reference remains deferred; geometry/gravity candidate is separated from surface-tension/viscosity/final-time blockers."),
        gate("acd_05_droplet_response", "PASS" if spray_response_ready else "NOT_READY", [REPORTS["droplet_euler_lagrange"], REPORTS["spray_closed_particle_budget"]]),
        gate("acd_05_closed_periodic_source_history_budget", "PASS" if spray_acd05_source_budget_ready else "NOT_READY", [REPORTS["spray_source_budget"]]),
        gate("acd_07_reacting_spray_mass_energy_source_history_budget", "PASS" if spray_acd07_source_budget_ready else "NOT_READY", [REPORTS["spray_detonation_source_budget"]]),
        gate("acd_05_closed_control_volume_mass_momentum_energy_budget", "PASS" if spray_acd05_control_volume_ready else "NOT_READY", [REPORTS["spray_closed_control_volume_budget"]]),
        gate(
            "acd_07_reacting_control_volume_total_budget",
            "PASS" if spray_reacting_control_volume_ready else "NOT_READY",
            [REPORTS["reacting_spray_closed_control_volume_budget"], REPORTS["spray_coupled_budget_residual"]],
            "" if spray_reacting_control_volume_ready else "Dedicated periodic reacting spray closed control-volume budget remains open.",
        ),
        gate("acd_07_full_gas_liquid_detonation", "PASS" if spray_full_detonation_ready else "NOT_READY", [REPORTS["spray_detonation"]], "Current evidence is a reacting spray/detonation-style response gate, not full cellular gas-liquid detonation certification."),
        gate(
            "acd_10_qlt_05_academic_gpu_environment",
            "PASS" if gpu_environment_ready else "NOT_READY",
            [REPORTS["gpu_preflight"]],
            "" if gpu_environment_ready else "Current server GPU driver/runtime preflight is NOT_READY; this is an environment blocker for academic GPU execution credit.",
        ),
    ]

    blocking_gaps = [g["name"] for g in gates if g["status"] != "PASS"]
    evidence_files = []
    for label, path in REPORTS.items():
        full = REPO_ROOT / path
        evidence_files.append({"label": label, "path": path, "sha256": sha256_file(full), "size_bytes": full.stat().st_size})
    evidence_files.append({"label": "report_writer", "path": rel(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__).resolve()), "size_bytes": Path(__file__).resolve().stat().st_size})

    summary = {
        "academic_gas_ready": gas_ready,
        "academic_twophase_vof_initial_ready": two_phase_vof_initial_ready,
        "academic_twophase_canonical_bubble_ready": canonical_bubble_ready,
        "academic_droplet_response_ready": spray_response_ready,
        "academic_spray_acd05_closed_source_budget_ready": spray_acd05_source_budget_ready,
        "academic_spray_acd07_reacting_source_budget_ready": spray_acd07_source_budget_ready,
        "academic_spray_acd05_closed_control_volume_budget_ready": spray_acd05_control_volume_ready,
        "academic_spray_acd07_reacting_control_volume_budget_ready": spray_acd07_reacting_control_volume_ready,
        "academic_spray_source_budget_ready": spray_source_budget_ready,
        "academic_spray_reacting_control_volume_budget_ready": spray_reacting_control_volume_ready,
        "academic_gas_liquid_detonation_full_ready": spray_full_detonation_ready,
        "academic_gpu_environment_ready": gpu_environment_ready,
        "blocking_gap_count": len(blocking_gaps),
    }
    summary["academic_initial_cpu_readiness"] = gas_ready and two_phase_vof_initial_ready and spray_response_ready and spray_source_budget_ready and spray_acd05_control_volume_ready and spray_acd07_reacting_control_volume_ready
    summary["academic_full_master_plan_readiness"] = summary["academic_initial_cpu_readiness"] and canonical_bubble_ready and spray_full_detonation_ready and gpu_environment_ready

    return {
        "schema_version": 1,
        "title": "Academic Readiness Summary",
        "generated_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS-ACADEMIC-INITIAL-CPU-READINESS" if summary["academic_initial_cpu_readiness"] else "PARTIAL-ACADEMIC-READINESS",
        "scope": "Cross-report readiness summary for master-plan academic gas, VOF two-phase, Euler-Lagrange spray, gas-liquid detonation, and academic GPU evidence.",
        "summary": summary,
        "blocking_gaps": blocking_gaps,
        "quality_gates": gates,
        "limitations": [
            "This summary does not rerun CFD cases; it verifies and summarizes the maintained evidence reports.",
            "Gas-phase detonation and initial CPU academic readiness are separated from full gas-liquid detonation and canonical external references; GPU environment credit is reported by the dedicated GPU preflight gate.",
            "NOT_READY gates are intentionally retained so progress reporting cannot promote response-only or environment-blocked evidence into full master-plan completion.",
        ],
        "source_reports": REPORTS,
        "evidence_files": evidence_files,
    }


def verify_report(path: Path) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema_version") != 1:
        raise SystemExit("schema_version mismatch")
    if report.get("status") not in {"PASS-ACADEMIC-INITIAL-CPU-READINESS", "PARTIAL-ACADEMIC-READINESS"}:
        raise SystemExit(f"unexpected status {report.get('status')!r}")
    summary = report.get("summary", {})
    required_true = [
        "academic_gas_ready",
        "academic_twophase_vof_initial_ready",
        "academic_droplet_response_ready",
        "academic_spray_acd05_closed_source_budget_ready",
        "academic_spray_acd07_reacting_source_budget_ready",
        "academic_spray_acd05_closed_control_volume_budget_ready",
        "academic_spray_acd07_reacting_control_volume_budget_ready",
        "academic_spray_source_budget_ready",
        "academic_initial_cpu_readiness",
        "academic_gpu_environment_ready",
    ]
    for key in required_true:
        if summary.get(key) is not True:
            raise SystemExit(f"required summary flag is not true: {key}")
    required_false = [
        "academic_twophase_canonical_bubble_ready",
        "academic_gas_liquid_detonation_full_ready",
        "academic_full_master_plan_readiness",
    ]
    for key in required_false:
        if summary.get(key) is not False:
            raise SystemExit(f"expected open-gap summary flag is not false: {key}")
    gates = report.get("quality_gates", [])
    if not gates:
        raise SystemExit("quality_gates missing")
    statuses = {g.get("name"): g.get("status") for g in gates}
    for name in ("acd_01_weno5_convergence", "acd_02_chemistry_readiness", "acd_03_gas_detonation_2d_3d_amr", "acd_04_vof_twophase_initial_readiness", "acd_05_closed_periodic_source_history_budget", "acd_07_reacting_spray_mass_energy_source_history_budget", "acd_05_closed_control_volume_mass_momentum_energy_budget", "acd_07_reacting_control_volume_total_budget", "acd_10_qlt_05_academic_gpu_environment"):
        if statuses.get(name) != "PASS":
            raise SystemExit(f"expected PASS gate missing: {name}")
    for name in ("qlt_03_canonical_bubble_rise_reference", "acd_07_full_gas_liquid_detonation"):
        if statuses.get(name) != "NOT_READY":
            raise SystemExit(f"expected NOT_READY gate missing: {name}")
    for item in report.get("evidence_files", []):
        full = REPO_ROOT / item["path"]
        if not full.is_file():
            raise SystemExit(f"missing evidence file: {item['path']}")
        if sha256_file(full) != item.get("sha256"):
            raise SystemExit(f"sha256 mismatch: {item['path']}")
    print(f"VERIFY-PASS academic readiness summary: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json:
        verify_report(args.verify_json)
        return
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE {args.output}")


if __name__ == "__main__":
    main()