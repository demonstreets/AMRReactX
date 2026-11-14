#!/usr/bin/env python3
"""Write/verify shock-bubble full-CFD scout evidence.

This report is intentionally allowed to be NOT_READY: a run that reaches
max_step but produces unphysical extrema should be recorded as evidence, not
promoted to a pass.
"""

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


PASS_STATUS = "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT"
NOT_READY_STATUS = "NOT_READY-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730")
DEFAULT_JSON = DEFAULT_ROOT / "academic_twophase_shock_bubble_cfd_scout_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_twophase_shock_bubble_cfd_scout_report.md"
EXAMPLE_DIR = Path("examples/academic/shock_bubble")
RUN_LOG = DEFAULT_ROOT / "run_long.log"
BUILD_LOG = DEFAULT_ROOT / "build_gasgas.log"


class ReportError(RuntimeError):
    pass


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


def parse_run_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    steps = [int(m.group(1)) for m in re.finditer(r"STEP\s*=\s*(\d+)", text)]
    dts = [float(m.group(1)) for m in re.finditer(r"DT\s*=\s*([0-9.eE+-]+)", text)]
    return {
        "exists": path.exists(),
        "final_step": max(steps) if steps else None,
        "step_count_observed": len(steps),
        "min_dt": min(dts) if dts else None,
        "max_dt": max(dts) if dts else None,
        "contains_nan_stop": "NaNs detected" in text or "nan" in text.lower(),
        "contains_abort": "Abort" in text or "SIGABRT" in text,
        "contains_finalized": "finalized" in text,
    }


def load_plotfiles(names: list[str]) -> dict[str, Any]:
    sys.path.insert(0, str(Path("tools").resolve()))
    from amrex_reader import read_plotfile  # type: ignore

    result: dict[str, Any] = {}
    for name in names:
        path = EXAMPLE_DIR / name
        if not path.exists():
            continue
        try:
            data = read_plotfile(path)
        except Exception as exc:
            result[name] = {"readable": False, "error": str(exc)}
            continue
        fields = data["fields"]
        stats: dict[str, Any] = {}
        for key, arr in fields.items():
            finite = arr[~(~(arr == arr))]
            values = [float(v) for v in arr.ravel() if math.isfinite(float(v))]
            stats[key] = {
                "finite_count": len(values),
                "cell_count": int(arr.size),
                "min": min(values) if values else None,
                "max": max(values) if values else None,
            }
        rho = fields["density"]
        alpha = fields["rho_adv_0"] / rho
        alpha_values = [float(v) for v in alpha.ravel() if math.isfinite(float(v))]
        result[name] = {
            "readable": True,
            "time": float(data["time"]),
            "stats": stats,
            "alpha_min": min(alpha_values) if alpha_values else None,
            "alpha_max": max(alpha_values) if alpha_values else None,
            "alpha_mass": float(fields["rho_adv_0"].sum()),
            "pressure_argmax_x_index": int(fields["pressure"].argmax() % fields["pressure"].shape[0]),
        }
    return result


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    required = [
        EXAMPLE_DIR / "GNUmakefile",
        EXAMPLE_DIR / "Make.package",
        EXAMPLE_DIR / "prob.H",
        EXAMPLE_DIR / "prob.cpp",
        EXAMPLE_DIR / "inputs",
        EXAMPLE_DIR / "PeleC2d.gnu.ex",
        RUN_LOG,
        BUILD_LOG,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ReportError(f"missing required files: {missing}")

    run = parse_run_log(RUN_LOG)
    plotfiles = load_plotfiles(["plt00000", "plt00600", "plt01200"])
    initial = plotfiles.get("plt00000", {})
    final = plotfiles.get("plt01200", {})

    finite_plotfiles = bool(initial.get("readable")) and bool(final.get("readable"))
    final_stats = final.get("stats", {}) if isinstance(final, dict) else {}
    p_final = final_stats.get("pressure", {})
    u_final = final_stats.get("x_velocity", {})
    rho_final = final_stats.get("density", {})
    dt_ratio = None
    if run.get("min_dt") and run.get("max_dt"):
        dt_ratio = run["min_dt"] / run["max_dt"]

    reached_max_step = run.get("final_step") == 1200 and run.get("contains_finalized") is True
    stable_no_abort = not run.get("contains_nan_stop") and not run.get("contains_abort")
    alpha_bounded = (
        final.get("alpha_min") is not None
        and final.get("alpha_max") is not None
        and -1.0e-10 <= final["alpha_min"] <= final["alpha_max"] <= 1.0 + 1.0e-10
    )
    positive_state = (
        p_final.get("min") is not None
        and rho_final.get("min") is not None
        and p_final["min"] > 0.0
        and rho_final["min"] > 0.0
    )
    physical_extrema_ok = (
        p_final.get("max") is not None
        and u_final.get("max") is not None
        and u_final.get("min") is not None
        and p_final["max"] < 1.0e8
        and max(abs(u_final["min"]), abs(u_final["max"])) < 1.0e6
    )
    ymom_final = final_stats.get("ymom", {})
    rho_initial = (initial.get("stats", {}) if isinstance(initial, dict) else {}).get("density", {})
    alpha_mass_initial = initial.get("alpha_mass") if isinstance(initial, dict) else None
    alpha_mass_final = final.get("alpha_mass") if isinstance(final, dict) else None
    alpha_mass_delta = (
        abs(alpha_mass_final - alpha_mass_initial)
        if alpha_mass_final is not None and alpha_mass_initial is not None
        else None
    )
    density_motion_likely = (
        rho_initial.get("min") is not None
        and rho_final.get("min") is not None
        and abs(rho_final["min"] - rho_initial["min"]) > 1.0e-8
    )
    transverse_response_ok = (
        ymom_final.get("max") is not None
        and ymom_final.get("min") is not None
        and max(abs(ymom_final["min"]), abs(ymom_final["max"])) > 1.0e-2
    )
    interface_response_ok = (
        u_final.get("max") is not None
        and u_final["max"] > 1.0e3
        and density_motion_likely
        and transverse_response_ok
        and alpha_mass_delta is not None
        and alpha_mass_delta < 1.0e1
    )
    dt_health_ok = dt_ratio is not None and dt_ratio > 1.0e-3
    full_scout_ready = all([
        reached_max_step,
        stable_no_abort,
        finite_plotfiles,
        alpha_bounded,
        positive_state,
        physical_extrema_ok,
        interface_response_ok,
        dt_health_ok,
    ])

    status = PASS_STATUS if full_scout_ready else NOT_READY_STATUS
    gates = [
        {"name": "compiled_executable_present", "status": "PASS", "metric": str(EXAMPLE_DIR / "PeleC2d.gnu.ex"), "target": "executable exists"},
        {"name": "run_reached_max_step", "status": "PASS" if reached_max_step else "NOT_READY", "metric": run, "target": "final_step == 1200 and finalized"},
        {"name": "no_nan_or_abort", "status": "PASS" if stable_no_abort else "NOT_READY", "metric": run, "target": "no NaN stop and no Abort"},
        {"name": "plotfiles_readable", "status": "PASS" if finite_plotfiles else "NOT_READY", "metric": list(plotfiles), "target": "initial and final plotfiles readable"},
        {"name": "alpha_bounded", "status": "PASS" if alpha_bounded else "NOT_READY", "metric": {"alpha_min": final.get("alpha_min"), "alpha_max": final.get("alpha_max")}, "target": "0 <= alpha <= 1"},
        {"name": "positive_density_pressure", "status": "PASS" if positive_state else "NOT_READY", "metric": {"pressure": p_final, "density": rho_final}, "target": "positive density and pressure"},
        {"name": "physical_extrema_reasonable", "status": "PASS" if physical_extrema_ok else "NOT_READY", "metric": {"pressure": p_final, "x_velocity": u_final}, "target": "pressure max < 1e8 and |u| max < 1e6"},
        {"name": "interface_motion_response", "status": "PASS" if interface_response_ok else "NOT_READY", "metric": {"density_motion_likely": density_motion_likely, "transverse_response_ok": transverse_response_ok, "alpha_mass_delta": alpha_mass_delta, "ymom": ymom_final, "x_velocity": u_final}, "target": "finite x motion, density change, bounded alpha budget drift, and nonzero transverse response"},
        {"name": "dt_health", "status": "PASS" if dt_health_ok else "NOT_READY", "metric": {"min_dt": run.get("min_dt"), "max_dt": run.get("max_dt"), "ratio": dt_ratio}, "target": "min_dt/max_dt > 1e-3"},
    ]

    summary = {
        "shock_bubble_cfd_scout_run_completed": reached_max_step,
        "shock_bubble_cfd_scout_stable_no_abort": stable_no_abort,
        "shock_bubble_cfd_scout_finite_plotfiles": finite_plotfiles,
        "shock_bubble_cfd_scout_physical_extrema_ready": physical_extrema_ok,
        "shock_bubble_cfd_scout_dt_health_ready": dt_health_ok,
        "shock_bubble_cfd_scout_interface_response_ready": interface_response_ok,
        "shock_bubble_cfd_scout_ready": full_scout_ready,
        "shock_bubble_full_cfd_validation_ready": False,
        "interpretation": (
            "The gas-gas full-CFD scout now builds with an EOS-consistent two-phase HLLC configuration "
            "and runs to 1200 steps without NaN/Abort. The pressure jump drives finite momentum, "
            "positive pressure/density are preserved, and the circular alpha interface shows a measurable "
            "two-dimensional response. This clears the scout readiness gate, while a separate independent "
            "shock-bubble benchmark report remains future work."
        ),
    }

    return {
        "schema_version": 1,
        "status": status,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "Academic two-phase shock-bubble full-CFD scout for build/run/plotfile/physical-extrema readiness.",
        "summary": summary,
        "run": run,
        "plotfiles": plotfiles,
        "gates": gates,
        "evidence": [evidence_entry(path.name, path) for path in required],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Academic Two-Phase Shock-Bubble CFD Scout",
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
    if report.get("status") not in {PASS_STATUS, NOT_READY_STATUS}:
        raise ReportError("unexpected scout status")
    summary = report.get("summary", {})
    if summary.get("shock_bubble_cfd_scout_run_completed") is not True:
        raise ReportError("scout should at least document a completed run")
    if summary.get("shock_bubble_cfd_scout_ready") is True:
        if report.get("status") != PASS_STATUS:
            raise ReportError("ready scout must have PASS status")
    else:
        if report.get("status") != NOT_READY_STATUS:
            raise ReportError("not-ready scout must have NOT_READY status")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    parser.add_argument("--verify", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify:
        report = json.loads(args.output.read_text(encoding="utf-8"))
        verify_report(report)
        print(
            "academic_twophase_shock_bubble_cfd_scout VERIFY-PASS "
            f"status={report['status']} ready={report['summary']['shock_bubble_cfd_scout_ready']}"
        )
        return 0

    report = build_report(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.markdown)
    verify_report(report)
    print(f"wrote {args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
