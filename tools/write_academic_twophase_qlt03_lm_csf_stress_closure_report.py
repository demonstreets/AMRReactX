#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach CSF-stress closure evidence.

This report supersedes the earlier pre-stress QLT-03 path-decision evidence
without deleting it.  The older reports remain useful as a regression baseline:
they show that the legacy cell-centred CSF force did not clear the Hysing
bubble-rise gate.  This closure report records the current decision after the
stress-divergence CSF form cleared both coarse and 64x128 grid-confirmation
checks for the QLT-03 low-Mach bridge example.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CLOSURE"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_closure_20260730")
DEFAULT_JSON = DEFAULT_ROOT / "qlt03_lm_csf_stress_closure_report.json"
DEFAULT_MD = DEFAULT_ROOT / "qlt03_lm_csf_stress_closure_report.md"

REPORTS = {
    "candidate": Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_candidate_20260730/csf_stress_candidate_report.json"),
    "grid": Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_grid_confirmation_20260730/csf_stress_grid_confirmation_report.json"),
    "legacy_t3": Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_scout_20260730/academic_twophase_qlt03_lm_t3_scout_report.json"),
    "legacy_grid": Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_grid_confirmation_20260730/qlt03_lm_grid_confirmation_report.json"),
    "legacy_path": Path("docs/codex_audit/evidence/academic_twophase_qlt03_path_decision_20260730/academic_twophase_qlt03_path_decision_report.json"),
}

SOURCES = {
    "inputs": Path("examples/academic/qlt03_lm_aux_bridge/inputs"),
    "prob_h": Path("examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H"),
    "prob_cpp": Path("examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.cpp"),
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def evidence_entry(name: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "name": name,
        "path": str(path),
        "exists": exists,
        "sha256": sha256(path) if exists and path.is_file() else None,
    }


def status_passes(report: dict[str, Any]) -> bool:
    return str(report.get("status", "")).startswith("PASS-")


def nested(report: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = report
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def gate(name: str, passed: bool, metric: Any, target: Any, evidence: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "NOT_READY",
        "metric": metric,
        "target": target,
        "evidence": evidence or [],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    paths = {
        "candidate": Path(args.candidate_report),
        "grid": Path(args.grid_report),
        "legacy_t3": Path(args.legacy_t3_report),
        "legacy_grid": Path(args.legacy_grid_report),
        "legacy_path": Path(args.legacy_path_report),
    }
    source_paths = {
        "inputs": Path(args.inputs),
        "prob_h": Path(args.prob_h),
        "prob_cpp": Path(args.prob_cpp),
    }

    missing = [str(p) for p in [*paths.values(), *source_paths.values()] if not p.exists()]
    if missing:
        raise ReportError(f"missing required evidence/source files: {missing}")

    candidate = load_json(paths["candidate"])
    grid = load_json(paths["grid"])
    legacy_t3 = load_json(paths["legacy_t3"])
    legacy_grid = load_json(paths["legacy_grid"])
    legacy_path = load_json(paths["legacy_path"])

    inputs_text = read_text(source_paths["inputs"])
    prob_h_text = read_text(source_paths["prob_h"])
    prob_cpp_text = read_text(source_paths["prob_cpp"])

    candidate_decision = candidate.get("decision", {})
    candidate_summary = candidate.get("summary", {})
    grid_summary = grid.get("summary", {})
    grid_contracts = grid.get("contracts", {})
    grid_decision = grid.get("decision", {})

    legacy_path_summary = legacy_path.get("summary", {})
    legacy_grid_summary = legacy_grid.get("summary", {})
    legacy_t3_summary = legacy_t3.get("summary", {})

    candidate_contracts = candidate.get("contracts", {})
    candidate_promoted = (
        candidate.get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CANDIDATE-PROMOTION"
        and candidate_decision.get("promote_as_preferred_qlt03_low_mach_csf_form") is True
        and candidate_decision.get("promote_full_academic_twophase_readiness") is False
    )
    candidate_t3_ready = candidate_contracts.get("t3_reference_agreement_cleared") is True
    grid_confirmed = (
        grid.get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-GRID-CONFIRMATION"
        and grid_contracts.get("coarse_reference_agreement_cleared") is True
        and grid_contracts.get("fine_reference_agreement_cleared") is True
        and grid_contracts.get("full_grid_confirmation_cleared") is True
        and grid_decision.get("qlt03_low_mach_csf_stress_grid_confirmed") is True
    )
    promoted_inputs = "prob.surface_tension_force_form = 3" in inputs_text
    source_form3_present = (
        "force_form == 3" in prob_h_text
        and "csf_stress" in prob_h_text
        and "surface_tension_force_form" in prob_h_text
        and "surface_tension_force_form" in prob_cpp_text
    )
    legacy_form_retained = (
        "force_x = -sigma * curvature * grad_x" in prob_h_text
    )
    code_default_ab_retained = "int surface_tension_force_form = 1" in prob_h_text
    legacy_grid_contracts = legacy_grid.get("contracts", {})
    legacy_t3_contracts = legacy_t3.get("contracts", {})
    legacy_pre_stress_not_ready = (
        legacy_path_summary.get("qlt03_canonical_ready") is False
        and legacy_path_summary.get("pelelmex_low_mach_t3_reference_agreement") is False
        and str(legacy_grid.get("status", "")).startswith("NOT_READY-")
        and legacy_grid_contracts.get("full_grid_confirmation_cleared") is False
        and str(legacy_t3.get("status", "")).startswith("NOT_READY-")
        and legacy_t3_contracts.get("hysing_reference_agreement_cleared") is False
    )

    fine_metrics = grid.get("fine_metrics", {})
    coarse_metrics = grid.get("coarse_metrics", {})
    grid_deltas = grid.get("grid_differences", {})

    gates = [
        gate(
            "csf_stress_candidate_promoted",
            candidate_promoted and candidate_t3_ready,
            {"status": candidate.get("status"), "decision": candidate_decision, "summary": candidate_summary},
            "candidate t=3 reference agreement pass and force_form=3 promoted for QLT-03",
            [str(paths["candidate"])],
        ),
        gate(
            "csf_stress_grid_confirmation_cleared",
            grid_confirmed,
            {"status": grid.get("status"), "contracts": grid_contracts, "decision": grid_decision},
            "coarse and 64x128 runs pass QLT-03 reference-agreement contracts",
            [str(paths["grid"])],
        ),
        gate(
            "qlt03_inputs_promote_force_form_3",
            promoted_inputs,
            "prob.surface_tension_force_form = 3" if promoted_inputs else "missing",
            "QLT-03 example input selects CSF stress-divergence form by default",
            [str(source_paths["inputs"])],
        ),
        gate(
            "qlt03_source_contains_stress_divergence_form",
            source_form3_present,
            {
                "force_form_3": "force_form == 3" in prob_h_text,
                "csf_stress_helper": "csf_stress" in prob_h_text,
                "parameter": "surface_tension_force_form" in prob_h_text,
            },
            "source exposes force_form=3 continuum-surface-stress divergence implementation",
            [str(source_paths["prob_h"]), str(source_paths["prob_cpp"])],
        ),
        gate(
            "legacy_cell_centered_csf_ab_path_retained",
            legacy_form_retained and code_default_ab_retained,
            {
                "legacy_cell_centered_force": legacy_form_retained,
                "code_default_surface_tension_force_form_1": code_default_ab_retained,
            },
            "legacy force_form=1 remains available for A/B regression",
            [str(source_paths["prob_h"]), str(source_paths["prob_cpp"])],
        ),
        gate(
            "legacy_pre_stress_reports_superseded",
            legacy_pre_stress_not_ready,
            {
                "legacy_path_qlt03_canonical_ready": legacy_path_summary.get("qlt03_canonical_ready"),
                "legacy_path_t3_reference_agreement": legacy_path_summary.get("pelelmex_low_mach_t3_reference_agreement"),
                "legacy_grid_status": legacy_grid.get("status"),
                "legacy_grid_full_confirmation": legacy_grid_contracts.get("full_grid_confirmation_cleared"),
                "legacy_t3_status": legacy_t3.get("status"),
                "legacy_t3_clears_reference": legacy_t3_contracts.get("hysing_reference_agreement_cleared"),
            },
            "older pre-stress NOT_READY reports remain historical baselines and are superseded by this closure report",
            [str(paths["legacy_t3"]), str(paths["legacy_grid"]), str(paths["legacy_path"])],
        ),
    ]

    all_gates_pass = all(item["status"] == "PASS" for item in gates)
    if not all_gates_pass:
        failed = [item["name"] for item in gates if item["status"] != "PASS"]
        raise ReportError(f"closure gates failed: {failed}")

    summary = {
        "qlt03_low_mach_hysing_case1_current_grid_confirmed": True,
        "academic_twophase_qlt03_blocker_closed": True,
        "supersedes_legacy_pre_stress_reports": True,
        "preferred_surface_tension_force_form_for_qlt03": 3,
        "code_default_retains_force_form_1_for_ab_regression": True,
        "promote_full_academic_twophase_readiness": False,
        "remaining_academic_twophase_scope": [
            "Refresh higher-level readiness/path-decision rollups to consume this closure record.",
            "Broaden beyond QLT-03 low-Mach Hysing Case 1 to the remaining two-phase academic matrix.",
            "Gas-liquid detonation/spray production-readiness remains a separate gate.",
        ],
        "coarse_32x64_reference_agreement": coarse_metrics,
        "fine_64x128_reference_agreement": fine_metrics,
        "coarse_to_fine_deltas": grid_deltas,
    }

    report = {
        "schema_version": 1,
        "status": STATUS,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "Academic two-phase QLT-03 low-Mach Hysing Case 1 CSF-stress closure",
        "summary": summary,
        "gates": gates,
        "source_files": {name: str(path) for name, path in source_paths.items()},
        "input_reports": {name: str(path) for name, path in paths.items()},
        "evidence": [
            *(evidence_entry(name, path) for name, path in paths.items()),
            *(evidence_entry(name, path) for name, path in source_paths.items()),
            evidence_entry("closure_writer", Path("tools/write_academic_twophase_qlt03_lm_csf_stress_closure_report.py")),
        ],
        "interpretation": [
            "The legacy cell-centred CSF force is retained for A/B comparisons, but the QLT-03 bridge input now selects force_form=3.",
            "The closure is intentionally scoped to QLT-03 low-Mach Hysing Case 1 at the current 32x64/64x128 confirmation level.",
            "Full academic two-phase readiness is not promoted by this report alone.",
        ],
    }

    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# QLT-03 Low-Mach CSF-Stress Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Decision",
        "",
        f"- QLT-03 low-Mach Hysing Case 1 current-grid confirmed: `{summary['qlt03_low_mach_hysing_case1_current_grid_confirmed']}`",
        f"- Academic two-phase QLT-03 blocker closed: `{summary['academic_twophase_qlt03_blocker_closed']}`",
        f"- Preferred QLT-03 surface-tension force form: `{summary['preferred_surface_tension_force_form_for_qlt03']}`",
        f"- Promote full academic two-phase readiness: `{summary['promote_full_academic_twophase_readiness']}`",
        "",
        "## Gates",
        "",
    ]
    for item in report["gates"]:
        lines.append(f"- `{item['status']}` {item['name']}")
    lines.extend(["", "## Remaining Scope", ""])
    for item in summary["remaining_academic_twophase_scope"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_report(report: dict[str, Any]) -> None:
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ReportError(message)

    require(report.get("status") == STATUS, "unexpected closure status")
    summary = report.get("summary", {})
    require(summary.get("qlt03_low_mach_hysing_case1_current_grid_confirmed") is True, "QLT-03 current-grid confirmation missing")
    require(summary.get("academic_twophase_qlt03_blocker_closed") is True, "QLT-03 blocker closure missing")
    require(summary.get("supersedes_legacy_pre_stress_reports") is True, "legacy supersession missing")
    require(summary.get("preferred_surface_tension_force_form_for_qlt03") == 3, "preferred force form should be 3")
    require(summary.get("code_default_retains_force_form_1_for_ab_regression") is True, "A/B default-retention contract missing")
    require(summary.get("promote_full_academic_twophase_readiness") is False, "closure must not over-promote full two-phase readiness")
    require(bool(summary.get("coarse_32x64_reference_agreement")), "coarse QLT-03 metrics missing")
    require(bool(summary.get("fine_64x128_reference_agreement")), "fine QLT-03 metrics missing")
    require(bool(summary.get("coarse_to_fine_deltas")), "QLT-03 grid-delta metrics missing")
    gates = {item.get("name"): item for item in report.get("gates", [])}
    required_gates = {
        "csf_stress_candidate_promoted",
        "csf_stress_grid_confirmation_cleared",
        "qlt03_inputs_promote_force_form_3",
        "qlt03_source_contains_stress_divergence_form",
        "legacy_cell_centered_csf_ab_path_retained",
        "legacy_pre_stress_reports_superseded",
    }
    missing = required_gates - set(gates)
    require(not missing, f"missing gates: {sorted(missing)}")
    failed = [name for name, item in gates.items() if item.get("status") != "PASS"]
    require(not failed, f"non-PASS gates: {failed}")
    for entry in report.get("evidence", []):
        require(entry.get("exists") is True, f"missing evidence file: {entry.get('path')}")
        if str(entry.get("path", "")).endswith(".json") or str(entry.get("path", "")).endswith(".py") or "inputs" in str(entry.get("path", "")):
            require(bool(entry.get("sha256")), f"missing evidence hash: {entry.get('path')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    parser.add_argument("--verify-json", type=Path)
    parser.add_argument("--candidate-report", type=Path, default=REPORTS["candidate"])
    parser.add_argument("--grid-report", type=Path, default=REPORTS["grid"])
    parser.add_argument("--legacy-t3-report", type=Path, default=REPORTS["legacy_t3"])
    parser.add_argument("--legacy-grid-report", type=Path, default=REPORTS["legacy_grid"])
    parser.add_argument("--legacy-path-report", type=Path, default=REPORTS["legacy_path"])
    parser.add_argument("--inputs", type=Path, default=SOURCES["inputs"])
    parser.add_argument("--prob-h", type=Path, default=SOURCES["prob_h"])
    parser.add_argument("--prob-cpp", type=Path, default=SOURCES["prob_cpp"])
    args = parser.parse_args()

    if args.verify_json:
        report = load_json(args.verify_json)
        verify_report(report)
        print(
            "academic_twophase_qlt03_lm_csf_stress_closure VERIFY-PASS "
            f"json={args.verify_json} status={report['status']} "
            f"qlt03_closed={report['summary']['academic_twophase_qlt03_blocker_closed']}"
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
        "academic_twophase_qlt03_lm_csf_stress_closure PASS "
        f"json={args.output} status={report['status']} "
        f"qlt03_closed={report['summary']['academic_twophase_qlt03_blocker_closed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
