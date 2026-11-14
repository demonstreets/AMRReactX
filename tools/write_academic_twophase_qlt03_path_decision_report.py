#!/usr/bin/env python3
"""Write/verify QLT-03 canonical bubble-rise implementation-path decision evidence."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-PATH-DECISION"
STATUS_NOT_READY = "NOT_READY-ACADEMIC-TWOPHASE-QLT03-PATH-DECISION"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_qlt03_path_decision_20260730")
DEFAULT_JSON = DEFAULT_ROOT / "academic_twophase_qlt03_path_decision_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_twophase_qlt03_path_decision_report.md"
DEFAULT_REFERENCE_REPORT = Path("docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_reference_20260729/academic_twophase_canonical_bubble_rise_reference_report.json")
DEFAULT_FINAL_TIME_SCOUT_REPORT = Path("docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_final_time_scout_20260730/canonical_bubble_rise_final_time_scout_report.json")
DEFAULT_CANDIDATE_REPORT = Path("docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_candidate_20260730/canonical_bubble_rise_candidate_report.json")
DEFAULT_LM_BRIDGE_FOLLOWUP_REPORT = Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_bridge_followup_20260730/academic_twophase_qlt03_lm_bridge_followup_report.json")
DEFAULT_LM_CANONICAL_CSF_SCOUT_REPORT = Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_canonical_csf_scout_20260730/academic_twophase_qlt03_lm_canonical_csf_scout_report.json")
DEFAULT_LM_T3_SCOUT_REPORT = Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_scout_20260730/academic_twophase_qlt03_lm_t3_scout_report.json")
DEFAULT_LM_GRID_CONFIRMATION_REPORT = Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_grid_confirmation_20260730/qlt03_lm_grid_confirmation_report.json")


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


def contains(path: Path, needle: str) -> bool:
    return path.is_file() and needle in path.read_text(errors="replace")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    reference_path = Path(args.reference_report)
    scout_path = Path(args.final_time_scout_report)
    candidate_path = Path(args.candidate_report)
    lm_bridge_followup_path = Path(args.lm_bridge_followup_report)
    lm_canonical_csf_scout_path = Path(args.lm_canonical_csf_scout_report)
    lm_t3_scout_path = Path(args.lm_t3_scout_report)
    lm_grid_confirmation_path = Path(args.lm_grid_confirmation_report)

    reference = load_json(reference_path)
    scout = load_json(scout_path)
    candidate = load_json(candidate_path)
    lm_bridge_followup = load_json(lm_bridge_followup_path)
    lm_canonical_csf_scout = load_json(lm_canonical_csf_scout_path)
    lm_t3_scout = load_json(lm_t3_scout_path)
    lm_grid_confirmation = load_json(lm_grid_confirmation_path)

    scout_summary = scout.get("summary", {})
    candidate_summary = candidate.get("summary", {})
    bridge_contracts = lm_bridge_followup.get("source_contracts", {})
    csf_contracts = lm_canonical_csf_scout.get("canonical_csf_contracts", {})
    t3_contracts = lm_t3_scout.get("contracts", {})
    grid_contracts = lm_grid_confirmation.get("contracts", {})

    qlt03_sources_present = (
        contains(Path("external/PeleLMeX/Source/PeleLMeX_Advance.cpp"), "pelelmex_aux_limited_state")
        and contains(Path("examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H"), "force_x = -sigma * curvature * grad_x")
        and contains(Path("examples/academic/qlt03_lm_aux_bridge/inputs"), "peleLM.incompressible_aux_advect_scheme = 2")
    )
    direct_t3_ruled_out = (
        scout_summary.get("stable_long_window_scout") is True
        and scout_summary.get("direct_t3_runtime_viable_on_current_compressible_explicit_path") is not True
        and scout_summary.get("clears_qlt_03_canonical_final_time_contract") is not True
    )
    lm_bridge_ready = (
        lm_bridge_followup.get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-LM-BRIDGE-FOLLOWUP"
        and bridge_contracts.get("incompressible_aux_advance_uses_mac_face_flux") is True
        and bridge_contracts.get("problem_specific_ext_source_hook_accepts_aux_argument") is True
        and bridge_contracts.get("qlt03_bridge_csf_source_reads_aux_alpha") is True
        and bridge_contracts.get("incompressible_velocity_force_scaling_reads_aux_density") is True
        and bridge_contracts.get("incompressible_aux_density_projection_uses_alpha_sigma") is True
        and bridge_contracts.get("incompressible_aux_viscosity_sets_diffusion_coefficients") is True
        and bridge_contracts.get("qlt03_bridge_uses_canonical_boundary_conditions") is True
        and bridge_contracts.get("qlt03_bridge_records_canonical_observables") is True
        and bridge_contracts.get("qlt03_bridge_rises_with_light_alpha_phase") is True
    )
    csf_short_window_ready = (
        lm_canonical_csf_scout.get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CANONICAL-CSF-SCOUT"
        and csf_contracts.get("sigma_is_hysing_case1_value") is True
        and csf_contracts.get("csf_force_cap_disabled") is True
        and csf_contracts.get("short_window_stable_no_nan_abort_or_segfault") is True
        and csf_contracts.get("alpha_mass_conserved") is True
        and csf_contracts.get("alpha_center_of_mass_rises") is True
    )
    t3_stable = (
        lm_t3_scout.get("status") in {
            "PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT",
            "NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT",
        }
        and t3_contracts.get("t3_final_time_reached") is True
        and t3_contracts.get("short_log_has_no_nan_abort_or_segfault") is True
        and t3_contracts.get("alpha_mass_conserved") is True
        and t3_contracts.get("time_series_extrema_used_for_reference") is True
        and t3_contracts.get("time_series_sample_count_sufficient") is True
    )
    t3_reference_agreement = (
        lm_t3_scout.get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT"
        and t3_contracts.get("hysing_reference_agreement_cleared") is True
    )
    grid_center_confirmed = (
        lm_grid_confirmation.get("status") == "NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-GRID-CONFIRMATION"
        and grid_contracts.get("coarse_reaches_t3") is True
        and grid_contracts.get("fine_reaches_t3") is True
        and grid_contracts.get("center_height_grid_consistency_cleared") is True
        and grid_contracts.get("fine_center_reference_error_cleared") is True
        and grid_contracts.get("full_grid_confirmation_cleared") is False
    )

    gates = [
        {"name": "compressible_explicit_direct_t3_path_ruled_out", "status": "PASS" if direct_t3_ruled_out else "NOT_READY", "metric": scout_summary, "target": "stable scout plus direct t=3 not viable"},
        {"name": "canonical_candidate_has_geometry_csf_viscosity_contracts", "status": "PASS" if candidate_summary.get("remaining_canonical_model_gaps") == ["canonical_final_time_contract"] else "NOT_READY", "metric": candidate_summary.get("remaining_canonical_model_gaps"), "target": ["canonical_final_time_contract"]},
        {"name": "pelelmex_low_mach_aux_csf_bridge_present", "status": "PASS" if lm_bridge_ready and qlt03_sources_present else "NOT_READY", "metric": bridge_contracts, "target": "Aux transport/material/CSF source contracts present"},
        {"name": "pelelmex_low_mach_canonical_strength_csf_short_window_cleared", "status": "PASS" if csf_short_window_ready else "NOT_READY", "metric": csf_contracts, "target": "uncapped sigma=24.5 short-window stable rise"},
        {"name": "pelelmex_low_mach_t3_final_time_stable", "status": "PASS" if t3_stable else "NOT_READY", "metric": {"status": lm_t3_scout.get("status"), "errors": lm_t3_scout.get("reference_errors"), "sample_count": lm_t3_scout.get("time_series", {}).get("sample_count")}, "target": "t=3 stable with time-series extrema comparison"},
        {"name": "pelelmex_low_mach_grid_center_confirmation_cleared", "status": "PASS" if grid_center_confirmed else "NOT_READY", "metric": {"grid_differences": lm_grid_confirmation.get("grid_differences"), "contracts": grid_contracts}, "target": "32/64 center-height consistency but full shape gate remains open"},
    ]
    path_decision_ready = all(g["status"] == "PASS" for g in gates)
    remaining = [] if t3_reference_agreement and grid_contracts.get("full_grid_confirmation_cleared") is True else [
        "hysing_minimum_circularity_time_series_contract",
        "hysing_maximum_rise_velocity_refined_grid_contract",
        "qlt03_grid_convergence_contract",
        "csf_curvature_balanced_force_contract",
    ]
    summary = {
        "path_decision_ready": path_decision_ready,
        "qlt03_canonical_ready": False,
        "compressible_explicit_direct_t3_ruled_out": direct_t3_ruled_out,
        "pelelmex_low_mach_aux_csf_bridge_present": lm_bridge_ready,
        "pelelmex_low_mach_canonical_strength_csf_short_window": csf_short_window_ready,
        "pelelmex_low_mach_t3_final_time_stable": t3_stable,
        "pelelmex_low_mach_t3_reference_agreement": t3_reference_agreement,
        "pelelmex_low_mach_grid_center_confirmation": grid_center_confirmed,
        "pelelmex_ready_vof_csf_path_present": False,
        "remaining_canonical_model_gaps": remaining,
        "recommended_paths": [
            {
                "path": "preferred",
                "name": "Improve low-Mach QLT-03 CSF curvature/balanced-force treatment before strict promotion",
                "why": "The repaired low-Mach path reaches t=3 and conserves alpha on 32x64 and 64x128 grids, with grid-consistent final center height; however time-series minimum circularity and refined-grid peak rise velocity are not yet within Hysing Case 1 tolerances.",
                "minimum_next_gates": [
                    "reduce minimum-circularity error below tolerance using a better curvature/balanced-force treatment",
                    "clear refined-grid maximum rise-velocity agreement",
                    "rerun 32/64 or better grid-confirmation evidence",
                ],
            }
        ],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS if path_decision_ready else STATUS_NOT_READY,
        "title": "Academic Two-Phase QLT-03 Path Decision",
        "scope": "Machine-checkable decision record for strict Hysing QLT-03 readiness after low-Mach t=3 and 32/64 grid-confirmation evidence.",
        "summary": summary,
        "quality_gates": gates,
        "source_reports": {
            "canonical_reference": str(reference_path),
            "canonical_candidate": str(candidate_path),
            "compressible_final_time_scout": str(scout_path),
            "lm_bridge_followup": str(lm_bridge_followup_path),
            "lm_canonical_csf_scout": str(lm_canonical_csf_scout_path),
            "lm_t3_scout": str(lm_t3_scout_path),
            "lm_grid_confirmation": str(lm_grid_confirmation_path),
        },
        "limitations": [
            "This report can PASS as a decision record while qlt03_canonical_ready remains false.",
            "The low-Mach bridge is not yet a final production VOF/CSF topology-preserving solver.",
            "Strict Hysing readiness still requires time-series circularity/velocity and grid-convergence closure.",
        ],
        "evidence_files": [
            evidence_entry("path_decision_writer", Path("tools/write_academic_twophase_qlt03_path_decision_report.py")),
            evidence_entry("qlt03_t3_strict_report", lm_t3_scout_path),
            evidence_entry("qlt03_grid_confirmation_report", lm_grid_confirmation_path),
            evidence_entry("qlt03_bridge_followup_report", lm_bridge_followup_path),
            evidence_entry("qlt03_bridge_prob", Path("examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H")),
            evidence_entry("pelelmex_advance", Path("external/PeleLMeX/Source/PeleLMeX_Advance.cpp")),
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Academic Two-Phase QLT-03 Path Decision",
        "",
        f"Status: `{report['status']}`",
        f"QLT-03 canonical ready: `{summary['qlt03_canonical_ready']}`",
        "",
        "## Remaining Gaps",
    ]
    for gap in summary.get("remaining_canonical_model_gaps", []):
        lines.append(f"- {gap}")
    lines.append("")
    lines.append("## Gates")
    for gate in report.get("quality_gates", []):
        lines.append(f"- `{gate['name']}`: `{gate['status']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def validate_report(report: dict[str, Any], check_hashes: bool) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "decision evidence did not pass")
    summary = report.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("path_decision_ready") is True, "path decision did not pass")
    require(summary.get("qlt03_canonical_ready") is False, "strict QLT-03 should remain open until circularity/velocity/grid gates clear")
    require(summary.get("compressible_explicit_direct_t3_ruled_out") is True, "direct compressible t=3 path not ruled out")
    require(summary.get("pelelmex_low_mach_aux_csf_bridge_present") is True, "low-Mach Aux/CSF bridge not detected")
    require(summary.get("pelelmex_low_mach_canonical_strength_csf_short_window") is True, "canonical-strength short-window scout missing")
    require(summary.get("pelelmex_low_mach_t3_final_time_stable") is True, "low-Mach t=3 stability missing")
    require(summary.get("pelelmex_low_mach_t3_reference_agreement") is False, "strict reference agreement should not be claimed")
    require(summary.get("pelelmex_low_mach_grid_center_confirmation") is True, "grid center confirmation missing")
    gates = {g.get("name"): g.get("status") for g in report.get("quality_gates", [])}
    for name in (
        "compressible_explicit_direct_t3_path_ruled_out",
        "canonical_candidate_has_geometry_csf_viscosity_contracts",
        "pelelmex_low_mach_aux_csf_bridge_present",
        "pelelmex_low_mach_canonical_strength_csf_short_window_cleared",
        "pelelmex_low_mach_t3_final_time_stable",
        "pelelmex_low_mach_grid_center_confirmation_cleared",
    ):
        require(gates.get(name) == "PASS", f"{name} did not pass")
    if check_hashes:
        for item in report.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch: {path}")


def verify_json(path: Path, check_hashes: bool) -> int:
    report = load_json(path)
    validate_report(report, check_hashes)
    print(f"academic_twophase_qlt03_path_decision VERIFY-PASS json={path} status={report['status']} qlt03_ready={report['summary']['qlt03_canonical_ready']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD)
    parser.add_argument("--reference-report", type=Path, default=DEFAULT_REFERENCE_REPORT)
    parser.add_argument("--final-time-scout-report", type=Path, default=DEFAULT_FINAL_TIME_SCOUT_REPORT)
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--lm-bridge-followup-report", type=Path, default=DEFAULT_LM_BRIDGE_FOLLOWUP_REPORT)
    parser.add_argument("--lm-canonical-csf-scout-report", type=Path, default=DEFAULT_LM_CANONICAL_CSF_SCOUT_REPORT)
    parser.add_argument("--lm-t3-scout-report", type=Path, default=DEFAULT_LM_T3_SCOUT_REPORT)
    parser.add_argument("--lm-grid-confirmation-report", type=Path, default=DEFAULT_LM_GRID_CONFIRMATION_REPORT)
    parser.add_argument("--verify-json", type=Path)
    parser.add_argument("--check-hashes", action="store_true")
    args = parser.parse_args()
    if args.verify_json is not None:
        return verify_json(args.verify_json, args.check_hashes)
    report = build_report(args)
    validate_report(report, check_hashes=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, args.markdown_output)
    print(f"academic_twophase_qlt03_path_decision PASS json={args.output} status={report['status']} qlt03_ready={report['summary']['qlt03_canonical_ready']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
