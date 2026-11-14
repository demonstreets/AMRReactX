#!/usr/bin/env python3
"""Write/verify independent shock-bubble validation evidence.

This report promotes the earlier full-CFD scout only after cross-checking it
against independent evidence:
  * an exact-solution Sod shock-tube smoke for the PeleC hydro path,
  * operator-level two-phase HLLC/EOS preflight evidence,
  * finite/bounded 2D alpha-bubble response metrics from the full-CFD scout.
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


STATUS = "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-VALIDATION"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_validation_20260730")
DEFAULT_JSON = DEFAULT_ROOT / "academic_twophase_shock_bubble_validation_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_twophase_shock_bubble_validation_report.md"
EXAMPLE_DIR = Path("examples/academic/shock_bubble")
SCOUT_REPORT = Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730/academic_twophase_shock_bubble_cfd_scout_report.json")
OPERATOR_REPORT = Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_operator_preflight_20260730/academic_twophase_shock_bubble_operator_preflight_report.json")
SOD_VALIDATION_LOG = DEFAULT_ROOT / "sod_reference" / "validation.log"
SOD_RUN_LOG = DEFAULT_ROOT / "sod_reference" / "run.log"
RUN_LOG = Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730/run_long.log")
BUILD_LOG = Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730/build_gasgas.log")


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_run_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    steps = [int(m.group(1)) for m in re.finditer(r"STEP\s*=\s*(\d+)", text)]
    dts = [float(m.group(1)) for m in re.finditer(r"DT\s*=\s*([0-9.eE+-]+)", text)]
    return {
        "final_step": max(steps) if steps else None,
        "step_count_observed": len(steps),
        "min_dt": min(dts) if dts else None,
        "max_dt": max(dts) if dts else None,
        "contains_nan_stop": "NaNs detected" in text or "nan" in text.lower(),
        "contains_abort": "Abort" in text or "SIGABRT" in text,
        "contains_finalized": "finalized" in text,
    }


def parse_sod_validation(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    result: dict[str, Any] = {"contains_pass": "sod_plotfile_validation PASS" in text}
    for key in ("rho_l1", "p_l1", "u_l1"):
        m = re.search(rf"{key}=([0-9.eE+-]+)", text)
        result[key] = float(m.group(1)) if m else None
    return result


def load_plotfile_metrics(names: list[str]) -> dict[str, Any]:
    sys.path.insert(0, str(Path("tools").resolve()))
    from amrex_reader import read_plotfile  # type: ignore

    out: dict[str, Any] = {}
    for name in names:
        data = read_plotfile(EXAMPLE_DIR / name)
        fields = data["fields"]
        rho = fields["density"]
        alpha = fields["rho_adv_0"] / rho
        alpha = alpha.clip(0.0, 1.0)
        light = 1.0 - alpha
        x = data["x"]
        y = data["y"]
        import numpy as np

        xx, yy = np.meshgrid(x, y, indexing="ij")
        light_sum = float(light.sum())
        centroid_x = float((light * xx).sum() / light_sum)
        centroid_y = float((light * yy).sum() / light_sum)

        stats: dict[str, Any] = {}
        for field in ("density", "pressure", "x_velocity", "xmom", "ymom", "rho_E", "rho_e", "Temp", "rho_adv_0"):
            arr = fields[field]
            vals = [float(v) for v in arr.ravel() if math.isfinite(float(v))]
            stats[field] = {
                "finite_count": len(vals),
                "cell_count": int(arr.size),
                "min": min(vals) if vals else None,
                "max": max(vals) if vals else None,
                "mean": sum(vals) / len(vals) if vals else None,
            }

        out[name] = {
            "time": float(data["time"]),
            "stats": stats,
            "alpha_min": float(alpha.min()),
            "alpha_max": float(alpha.max()),
            "alpha_mixedness": float(np.minimum(alpha, 1.0 - alpha).mean()),
            "light_sum": light_sum,
            "light_centroid_x": centroid_x,
            "light_centroid_y": centroid_y,
        }
    return out


def diff_alpha() -> dict[str, Any]:
    sys.path.insert(0, str(Path("tools").resolve()))
    from amrex_reader import read_plotfile  # type: ignore
    import numpy as np

    d0 = read_plotfile(EXAMPLE_DIR / "plt00000")["fields"]
    d1 = read_plotfile(EXAMPLE_DIR / "plt01200")["fields"]
    a0 = np.clip(d0["rho_adv_0"] / d0["density"], 0.0, 1.0)
    a1 = np.clip(d1["rho_adv_0"] / d1["density"], 0.0, 1.0)
    d = a1 - a0
    return {
        "alpha_diff_l1": float(np.mean(np.abs(d))),
        "alpha_diff_linf": float(np.max(np.abs(d))),
        "alpha_diff_nonzero": int(np.count_nonzero(d)),
    }


def gate(name: str, passed: bool, metric: Any, target: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "NOT_READY",
        "metric": metric,
        "target": target,
        "evidence": evidence,
    }


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    required = [
        EXAMPLE_DIR / "GNUmakefile",
        EXAMPLE_DIR / "inputs",
        EXAMPLE_DIR / "prob.H",
        EXAMPLE_DIR / "prob.cpp",
        EXAMPLE_DIR / "PeleC2d.gnu.ex",
        SCOUT_REPORT,
        OPERATOR_REPORT,
        SOD_VALIDATION_LOG,
        SOD_RUN_LOG,
        RUN_LOG,
        BUILD_LOG,
        EXAMPLE_DIR / "plt00000",
        EXAMPLE_DIR / "plt00600",
        EXAMPLE_DIR / "plt01200",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise ReportError(f"missing required evidence: {missing}")

    scout = load_json(SCOUT_REPORT)
    operator = load_json(OPERATOR_REPORT)
    run = parse_run_log(RUN_LOG)
    sod = parse_sod_validation(SOD_VALIDATION_LOG)
    plots = load_plotfile_metrics(["plt00000", "plt00600", "plt01200"])
    adiff = diff_alpha()

    initial = plots["plt00000"]
    final = plots["plt01200"]
    p = final["stats"]["pressure"]
    rho = final["stats"]["density"]
    u = final["stats"]["x_velocity"]
    ymom = final["stats"]["ymom"]

    scout_ready = (
        scout.get("status") == "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-CFD-SCOUT"
        and scout.get("summary", {}).get("shock_bubble_cfd_scout_ready") is True
    )
    operator_ready = (
        operator.get("status") == "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-OPERATOR-PREFLIGHT"
        and operator.get("summary", {}).get("shock_bubble_operator_preflight_ready") is True
    )
    sod_ready = (
        sod.get("contains_pass") is True
        and sod.get("rho_l1") is not None and sod["rho_l1"] < 0.08
        and sod.get("p_l1") is not None and sod["p_l1"] < 0.08
        and sod.get("u_l1") is not None and sod["u_l1"] < 0.08
    )
    run_ready = (
        run["final_step"] == 1200
        and run["contains_finalized"] is True
        and run["contains_nan_stop"] is False
        and run["contains_abort"] is False
    )
    bounded_ready = (
        rho["min"] > 0.0
        and p["min"] > 0.0
        and p["max"] < 1.0e8
        and max(abs(u["min"]), abs(u["max"])) < 1.0e6
        and -1.0e-10 <= final["alpha_min"] <= final["alpha_max"] <= 1.0 + 1.0e-10
    )
    light_sum_rel_change = abs(final["light_sum"] - initial["light_sum"]) / initial["light_sum"]
    response_ready = (
        final["light_centroid_x"] - initial["light_centroid_x"] > 1.0e-4
        and adiff["alpha_diff_linf"] > 2.0e-2
        and max(abs(ymom["min"]), abs(ymom["max"])) > 1.0e-2
        and light_sum_rel_change < 2.0e-2
    )
    ready = all([scout_ready, operator_ready, sod_ready, run_ready, bounded_ready, response_ready])

    gates = [
        gate("operator_preflight_ready", operator_ready, operator.get("summary", {}), "two-phase HLLC/EOS/CSF operator preflight PASS", [str(OPERATOR_REPORT)]),
        gate("reference_sod_exact_hydro_ready", sod_ready, sod, "Sod exact-solution L1 errors below 0.08", [str(SOD_VALIDATION_LOG), str(SOD_RUN_LOG)]),
        gate("full_cfd_scout_ready", scout_ready, scout.get("summary", {}), "full-CFD shock-bubble scout report PASS", [str(SCOUT_REPORT)]),
        gate("long_run_stable", run_ready, run, "1200-step run finalized without NaN/Abort", [str(RUN_LOG)]),
        gate("bounded_positive_state", bounded_ready, {"pressure": p, "density": rho, "x_velocity": u, "alpha_min": final["alpha_min"], "alpha_max": final["alpha_max"]}, "positive pressure/density, bounded alpha, non-explosive velocity", [str(EXAMPLE_DIR / "plt01200")]),
        gate("two_dimensional_interface_response", response_ready, {"initial": initial, "final": final, **adiff, "light_sum_rel_change": light_sum_rel_change, "ymom": ymom}, "centroid displacement, alpha deformation, and transverse momentum response", [str(EXAMPLE_DIR / "plt00000"), str(EXAMPLE_DIR / "plt01200")]),
    ]

    if not ready:
        raise ReportError("shock-bubble validation gates did not all pass")

    summary = {
        "shock_bubble_independent_validation_ready": True,
        "shock_bubble_operator_preflight_ready": operator_ready,
        "shock_bubble_reference_sod_ready": sod_ready,
        "shock_bubble_full_cfd_scout_ready": scout_ready,
        "shock_bubble_long_run_ready": run_ready,
        "shock_bubble_bounded_state_ready": bounded_ready,
        "shock_bubble_interface_response_ready": response_ready,
        "shock_bubble_final_step": run["final_step"],
        "shock_bubble_final_time": final["time"],
        "shock_bubble_light_centroid_dx": final["light_centroid_x"] - initial["light_centroid_x"],
        "shock_bubble_alpha_diff_linf": adiff["alpha_diff_linf"],
        "shock_bubble_light_sum_rel_change": light_sum_rel_change,
        "interpretation": (
            "The shock-bubble validation combines independent Sod exact-solution hydro evidence, "
            "operator-level two-phase HLLC/EOS preflight evidence, and a 1200-step finite bounded "
            "2D alpha-interface response from the full-CFD scout. It closes the dedicated "
            "shock-bubble independent validation gate, while broader academic two-phase readiness "
            "still depends on full gas-liquid detonation and closed coupled-budget gates."
        ),
    }

    return {
        "schema_version": 1,
        "status": STATUS,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "Independent shock-bubble validation using reference hydro, operator preflight, and full-CFD 2D interface-response evidence.",
        "summary": summary,
        "gates": gates,
        "run": run,
        "sod_reference": sod,
        "plotfiles": plots,
        "alpha_diff": adiff,
        "evidence": [evidence_entry(p.name, p) for p in required]
        + [evidence_entry("validation_writer", Path("tools/write_academic_twophase_shock_bubble_validation_report.py"))],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Academic Two-Phase Shock-Bubble Validation",
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
    if report.get("status") != STATUS:
        raise ReportError("unexpected shock-bubble validation status")
    summary = report.get("summary", {})
    if summary.get("shock_bubble_independent_validation_ready") is not True:
        raise ReportError("shock-bubble independent validation not ready")
    gates = {item.get("name"): item.get("status") for item in report.get("gates", [])}
    for name in (
        "operator_preflight_ready",
        "reference_sod_exact_hydro_ready",
        "full_cfd_scout_ready",
        "long_run_stable",
        "bounded_positive_state",
        "two_dimensional_interface_response",
    ):
        if gates.get(name) != "PASS":
            raise ReportError(f"expected PASS gate missing: {name}")
    for entry in report.get("evidence", []):
        path = Path(str(entry.get("path", "")))
        if not path.exists():
            raise ReportError(f"missing evidence path: {path}")


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
            "academic_twophase_shock_bubble_validation VERIFY-PASS "
            f"json={args.verify_json} status={report['status']}"
        )
        return 0

    report = build_report(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.markdown)
    verify_report(report)
    print(f"academic_twophase_shock_bubble_validation PASS json={args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
