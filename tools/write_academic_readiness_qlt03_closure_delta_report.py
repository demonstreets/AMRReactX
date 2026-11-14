#!/usr/bin/env python3
"""Write/verify academic readiness delta evidence for the QLT-03 CSF-stress closure."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-READINESS-QLT03-CSF-STRESS-DELTA"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_readiness_qlt03_closure_delta_20260730")
DEFAULT_JSON = DEFAULT_ROOT / "academic_readiness_qlt03_closure_delta_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_readiness_qlt03_closure_delta_report.md"

DEFAULT_READINESS = Path("docs/codex_audit/evidence/academic_readiness_summary_20260729/academic_readiness_summary_report.json")
DEFAULT_CLOSURE = Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_closure_20260730/qlt03_lm_csf_stress_closure_report.json")
DEFAULT_PATH_DECISION = Path("docs/codex_audit/evidence/academic_twophase_qlt03_path_decision_20260730/academic_twophase_qlt03_path_decision_report.json")


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


def evidence_entry(name: str, path: Path) -> dict[str, Any]:
    return {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256(path) if path.is_file() else None,
    }


def status_passes(report: dict[str, Any]) -> bool:
    return str(report.get("status", "")).startswith("PASS-")


def gate(name: str, passed: bool, metric: Any, target: Any, evidence: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "NOT_READY",
        "metric": metric,
        "target": target,
        "evidence": evidence,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    readiness_path = Path(args.readiness_report)
    closure_path = Path(args.closure_report)
    path_decision_path = Path(args.path_decision_report)
    writer_path = Path("tools/write_academic_readiness_qlt03_closure_delta_report.py")

    missing = [str(path) for path in (readiness_path, closure_path, path_decision_path, writer_path) if not path.exists()]
    if missing:
        raise ReportError(f"missing required evidence files: {missing}")

    readiness = load_json(readiness_path)
    closure = load_json(closure_path)
    path_decision = load_json(path_decision_path)

    readiness_summary = readiness.get("summary", {})
    closure_summary = closure.get("summary", {})
    path_summary = path_decision.get("summary", {})

    old_readiness_is_historical = (
        readiness.get("status") == "PASS-ACADEMIC-INITIAL-CPU-READINESS"
        and readiness_summary.get("academic_initial_cpu_readiness") is True
        and readiness_summary.get("academic_twophase_canonical_bubble_ready") is False
    )
    closure_clears_qlt03 = (
        closure.get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CLOSURE"
        and closure_summary.get("academic_twophase_qlt03_blocker_closed") is True
        and closure_summary.get("qlt03_low_mach_hysing_case1_current_grid_confirmed") is True
        and closure_summary.get("preferred_surface_tension_force_form_for_qlt03") == 3
        and closure_summary.get("promote_full_academic_twophase_readiness") is False
        and bool(closure_summary.get("coarse_32x64_reference_agreement"))
        and bool(closure_summary.get("fine_64x128_reference_agreement"))
        and bool(closure_summary.get("coarse_to_fine_deltas"))
    )
    path_decision_superseded = (
        path_decision.get("status") == "PASS-ACADEMIC-TWOPHASE-QLT03-PATH-DECISION"
        and path_summary.get("qlt03_canonical_ready") is False
        and path_summary.get("pelelmex_low_mach_t3_reference_agreement") is False
    )

    old_blocking_gaps = list(readiness.get("blocking_gaps", []))
    residual_blocking_gaps = [
        gap for gap in old_blocking_gaps if gap != "qlt_03_canonical_bubble_rise_reference"
    ]
    residual_blocking_gaps.append("academic_twophase_broader_non_qlt_matrix")

    gates = [
        gate(
            "historical_readiness_summary_preserved",
            old_readiness_is_historical,
            {
                "status": readiness.get("status"),
                "academic_initial_cpu_readiness": readiness_summary.get("academic_initial_cpu_readiness"),
                "academic_twophase_canonical_bubble_ready": readiness_summary.get("academic_twophase_canonical_bubble_ready"),
            },
            "old summary remains a verified historical rollup",
            [str(readiness_path)],
        ),
        gate(
            "qlt03_low_mach_closure_consumed",
            closure_clears_qlt03,
            {
                "status": closure.get("status"),
                "preferred_form": closure_summary.get("preferred_surface_tension_force_form_for_qlt03"),
                "coarse_metrics": closure_summary.get("coarse_32x64_reference_agreement"),
                "fine_metrics": closure_summary.get("fine_64x128_reference_agreement"),
                "grid_deltas": closure_summary.get("coarse_to_fine_deltas"),
            },
            "QLT-03 low-Mach Hysing Case 1 current-grid blocker closed by CSF-stress closure",
            [str(closure_path)],
        ),
        gate(
            "legacy_path_decision_superseded",
            path_decision_superseded,
            {
                "status": path_decision.get("status"),
                "qlt03_canonical_ready": path_summary.get("qlt03_canonical_ready"),
                "pelelmex_low_mach_t3_reference_agreement": path_summary.get("pelelmex_low_mach_t3_reference_agreement"),
            },
            "older pre-stress path-decision remains historical and is superseded for the QLT-03 low-Mach route",
            [str(path_decision_path)],
        ),
        gate(
            "full_academic_twophase_not_over_promoted",
            closure_summary.get("promote_full_academic_twophase_readiness") is False,
            closure_summary.get("remaining_academic_twophase_scope"),
            "closure is scoped to QLT-03 low-Mach Hysing Case 1, not the whole academic two-phase matrix",
            [str(closure_path)],
        ),
    ]

    if any(item["status"] != "PASS" for item in gates):
        failed = [item["name"] for item in gates if item["status"] != "PASS"]
        raise ReportError(f"readiness delta gates failed: {failed}")

    summary = {
        "academic_initial_cpu_readiness_retained": True,
        "academic_twophase_qlt03_low_mach_hysing_case1_ready": True,
        "academic_twophase_canonical_bubble_old_rollup_superseded": True,
        "academic_twophase_full_matrix_ready": False,
        "academic_full_master_plan_readiness": False,
        "old_blocking_gaps": old_blocking_gaps,
        "residual_blocking_gaps_after_qlt03_closure": residual_blocking_gaps,
        "residual_blocking_gap_count_after_qlt03_closure": len(residual_blocking_gaps),
        "progress_interpretation": "QLT-03 low-Mach Hysing Case 1 is closed at the current CSF-stress 32x64/64x128 confirmation level; remaining academic two-phase readiness is now broader-matrix coverage, not the old pre-stress QLT-03 blocker.",
    }

    return {
        "schema_version": 1,
        "status": STATUS,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "High-level academic readiness delta after QLT-03 low-Mach CSF-stress closure.",
        "summary": summary,
        "gates": gates,
        "input_reports": {
            "readiness_summary": str(readiness_path),
            "qlt03_csf_stress_closure": str(closure_path),
            "legacy_path_decision": str(path_decision_path),
        },
        "evidence": [
            evidence_entry("readiness_summary", readiness_path),
            evidence_entry("qlt03_csf_stress_closure", closure_path),
            evidence_entry("legacy_path_decision", path_decision_path),
            evidence_entry("delta_writer", writer_path),
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Academic Readiness QLT-03 Closure Delta",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- QLT-03 low-Mach ready: `{summary['academic_twophase_qlt03_low_mach_hysing_case1_ready']}`",
        f"- Full academic two-phase matrix ready: `{summary['academic_twophase_full_matrix_ready']}`",
        f"- Full master-plan readiness: `{summary['academic_full_master_plan_readiness']}`",
        f"- Residual blocking gaps: `{summary['residual_blocking_gap_count_after_qlt03_closure']}`",
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

    require(report.get("status") == STATUS, "unexpected readiness delta status")
    summary = report.get("summary", {})
    require(summary.get("academic_initial_cpu_readiness_retained") is True, "initial CPU readiness not retained")
    require(summary.get("academic_twophase_qlt03_low_mach_hysing_case1_ready") is True, "QLT-03 low-Mach closure not consumed")
    require(summary.get("academic_twophase_canonical_bubble_old_rollup_superseded") is True, "old QLT-03 rollup not marked superseded")
    require(summary.get("academic_twophase_full_matrix_ready") is False, "full two-phase matrix must remain open")
    require(summary.get("academic_full_master_plan_readiness") is False, "full master-plan readiness must remain open")
    require("academic_twophase_broader_non_qlt_matrix" in summary.get("residual_blocking_gaps_after_qlt03_closure", []), "broader two-phase residual gap missing")
    gates = {item.get("name"): item.get("status") for item in report.get("gates", [])}
    for name in (
        "historical_readiness_summary_preserved",
        "qlt03_low_mach_closure_consumed",
        "legacy_path_decision_superseded",
        "full_academic_twophase_not_over_promoted",
    ):
        require(gates.get(name) == "PASS", f"gate did not pass: {name}")
    for entry in report.get("evidence", []):
        path = Path(str(entry.get("path", "")))
        require(path.is_file(), f"missing evidence file: {path}")
        require(sha256(path) == entry.get("sha256"), f"sha256 mismatch: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    parser.add_argument("--verify-json", type=Path)
    parser.add_argument("--readiness-report", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--closure-report", type=Path, default=DEFAULT_CLOSURE)
    parser.add_argument("--path-decision-report", type=Path, default=DEFAULT_PATH_DECISION)
    args = parser.parse_args()

    if args.verify_json:
        report = load_json(args.verify_json)
        verify_report(report)
        print(
            "academic_readiness_qlt03_closure_delta VERIFY-PASS "
            f"json={args.verify_json} status={report['status']} "
            f"qlt03_ready={report['summary']['academic_twophase_qlt03_low_mach_hysing_case1_ready']}"
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
        "academic_readiness_qlt03_closure_delta PASS "
        f"json={args.output} status={report['status']} "
        f"qlt03_ready={report['summary']['academic_twophase_qlt03_low_mach_hysing_case1_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
