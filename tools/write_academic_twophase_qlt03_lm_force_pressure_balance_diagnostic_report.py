#!/usr/bin/env python3
"""Write/verify QLT-03 force-pressure balance and symmetry diagnostic evidence."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import amrex_reader  # noqa: E402


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-FORCE-PRESSURE-BALANCE-DIAGNOSTIC"
SIGMA = 24.5
RHO_HEAVY = 1000.0
RHO_LIGHT = 100.0
GRAD_FLOOR = 1.0e-12


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def l2_norm(values: list[np.ndarray] | tuple[np.ndarray, ...]) -> float:
    total = 0.0
    for value in values:
        arr = np.asarray(value, dtype=float)
        total += float(np.sum(arr * arr))
    return float(math.sqrt(total))


def mirror_ratio(field: np.ndarray, parity: str) -> float:
    arr = np.asarray(field, dtype=float)
    mirror = np.flip(arr, axis=0)
    diff = arr - mirror if parity == "even" else arr + mirror
    denom = float(np.sum(np.abs(arr)) + np.sum(np.abs(mirror)))
    if denom <= 0.0:
        return 0.0
    return float(np.sum(np.abs(diff)) / denom)


def field_center(data: dict) -> dict:
    alpha = np.asarray(data["fields"]["alpha"], dtype=float)
    x = np.asarray(data["x"], dtype=float)
    y = np.asarray(data["y"], dtype=float)
    dx, dy = [float(v) for v in data["dx"][:2]]
    xx, yy = np.meshgrid(x, y, indexing="ij")
    integral = float(np.sum(alpha) * dx * dy)
    if integral <= 0.0:
        fail("alpha integral is non-positive")
    return {
        "center_x": float(np.sum(alpha * xx) * dx * dy / integral),
        "center_y": float(np.sum(alpha * yy) * dx * dy / integral),
        "alpha_max": float(np.max(alpha)),
    }


def reconstruct_csf_balance(plotfile: Path) -> dict:
    data = amrex_reader.read_plotfile(str(plotfile))
    fields = data["fields"]
    required = ("alpha", "x_velocity", "y_velocity", "gradpx", "gradpy")
    missing = [name for name in required if name not in fields]
    if missing:
        fail(f"missing fields in {plotfile}: {missing}")

    alpha = np.asarray(fields["alpha"], dtype=float)
    ux = np.asarray(fields["x_velocity"], dtype=float)
    uy = np.asarray(fields["y_velocity"], dtype=float)
    gradpx = np.asarray(fields["gradpx"], dtype=float)
    gradpy = np.asarray(fields["gradpy"], dtype=float)
    dx, dy = [float(v) for v in data["dx"][:2]]

    grad_x = np.gradient(alpha, dx, axis=0, edge_order=1)
    grad_y = np.gradient(alpha, dy, axis=1, edge_order=1)
    grad_mag = np.sqrt(grad_x * grad_x + grad_y * grad_y + GRAD_FLOOR * GRAD_FLOOR)
    lap_alpha = (
        np.gradient(grad_x, dx, axis=0, edge_order=1)
        + np.gradient(grad_y, dy, axis=1, edge_order=1)
    )
    curvature = -lap_alpha / grad_mag
    csf_x = -SIGMA * curvature * grad_x
    csf_y = -SIGMA * curvature * grad_y
    rho = np.maximum((1.0 - alpha) * RHO_HEAVY + alpha * RHO_LIGHT, 1.0e-30)
    csf_acc_x = csf_x / rho
    csf_acc_y = csf_y / rho
    gradp_acc_x = gradpx / rho
    gradp_acc_y = gradpy / rho

    threshold = max(1.0e-10, 0.01 * float(np.max(grad_mag)))
    mask = grad_mag > threshold
    if int(np.count_nonzero(mask)) <= 0:
        fail(f"empty interface mask in {plotfile}")

    csf_norm = l2_norm((csf_acc_x[mask], csf_acc_y[mask]))
    gradp_norm = l2_norm((gradp_acc_x[mask], gradp_acc_y[mask]))
    residual_minus = l2_norm((
        (csf_acc_x - gradp_acc_x)[mask],
        (csf_acc_y - gradp_acc_y)[mask],
    )) / max(csf_norm, 1.0e-99)
    residual_plus = l2_norm((
        (csf_acc_x + gradp_acc_x)[mask],
        (csf_acc_y + gradp_acc_y)[mask],
    )) / max(csf_norm, 1.0e-99)

    center = field_center(data)
    return {
        "plotfile": str(plotfile),
        "time": float(data["time"]),
        **center,
        "interface_cell_count": int(np.count_nonzero(mask)),
        "csf_acc_norm_interface": csf_norm,
        "gradp_acc_norm_interface": gradp_norm,
        "gradp_to_csf_norm_ratio_interface": gradp_norm / max(csf_norm, 1.0e-99),
        "residual_ratio_csf_minus_gradp": residual_minus,
        "residual_ratio_csf_plus_gradp": residual_plus,
        "best_residual_ratio": min(residual_minus, residual_plus),
        "best_residual_sign": "minus" if residual_minus <= residual_plus else "plus",
        "mirror_alpha_even_ratio": mirror_ratio(alpha, "even"),
        "mirror_csf_acc_x_odd_ratio": mirror_ratio(csf_acc_x, "odd"),
        "mirror_csf_acc_y_even_ratio": mirror_ratio(csf_acc_y, "even"),
        "mirror_gradpx_odd_ratio": mirror_ratio(gradpx, "odd"),
        "mirror_gradpy_even_ratio": mirror_ratio(gradpy, "even"),
        "mirror_ux_odd_ratio": mirror_ratio(ux, "odd"),
        "mirror_uy_even_ratio": mirror_ratio(uy, "even"),
        "max_abs_ux": float(np.max(np.abs(ux))),
        "max_abs_uy": float(np.max(np.abs(uy))),
    }


def last_plotfile(run_dir: Path) -> Path:
    plots = sorted(path for path in run_dir.glob("plt*") if path.is_dir())
    if not plots:
        fail(f"missing plotfiles in {run_dir}")
    return plots[-1]


def plotfile_for_min_circularity(t3_report: dict) -> Path:
    samples = t3_report.get("time_series", {}).get("samples", [])
    if not samples:
        fail("missing t3 time-series samples")
    sample = min(samples, key=lambda item: float(item.get("circularity", 1.0e99)))
    return Path(sample["plotfile"])


def build_report(
    drift_summary_path: Path,
    no_csf_run_dir: Path,
    no_gravity_run_dir: Path,
    t3_report_path: Path,
    t3_run_dir: Path,
) -> dict:
    drift = read_json(drift_summary_path)
    t3 = read_json(t3_report_path)
    no_csf = reconstruct_csf_balance(last_plotfile(no_csf_run_dir))
    no_gravity = reconstruct_csf_balance(last_plotfile(no_gravity_run_dir))
    t3_min_circularity = reconstruct_csf_balance(plotfile_for_min_circularity(t3))
    t3_final = reconstruct_csf_balance(last_plotfile(t3_run_dir))

    report = {
        "status": STATUS,
        "scope": (
            "QLT-03 low-Mach diagnostic that reconstructs the current cell-centered "
            "CSF acceleration from alpha plotfiles and compares it with plotted pressure "
            "gradient acceleration and mirror symmetry. It is a route-selection guard, "
            "not a readiness claim."
        ),
        "evidence": {
            "drift_summary": str(drift_summary_path),
            "no_csf_run_dir": str(no_csf_run_dir),
            "canonical_no_gravity_run_dir": str(no_gravity_run_dir),
            "t3_report": str(t3_report_path),
            "t3_run_dir": str(t3_run_dir),
        },
        "drift_controls": {
            "canonical_no_csf_center_x_drift": drift.get("canonical_no_csf", {}).get("center_x_drift"),
            "canonical_no_gravity_center_x_drift": drift.get("canonical_no_gravity", {}).get("center_x_drift"),
            "canonical_no_gravity_final_alpha_max": drift.get("canonical_no_gravity", {}).get("final_alpha_max"),
        },
        "diagnostics": {
            "canonical_no_csf_final": no_csf,
            "canonical_no_gravity_final": no_gravity,
            "t3_min_circularity_sample": t3_min_circularity,
            "t3_final": t3_final,
        },
        "contracts": {
            "plotfiles_read": True,
            "symmetry_control_no_csf_is_machine_symmetric": (
                abs(float(drift.get("canonical_no_csf", {}).get("center_x_drift", 1.0))) < 1.0e-12
                and no_csf["mirror_alpha_even_ratio"] < 1.0e-10
                and no_csf["mirror_ux_odd_ratio"] < 1.0e-10
                and no_csf["mirror_uy_even_ratio"] < 1.0e-10
            ),
            "canonical_no_gravity_csf_breaks_lateral_symmetry": (
                abs(float(drift.get("canonical_no_gravity", {}).get("center_x_drift", 0.0))) > 1.0e-2
                and no_gravity["mirror_ux_odd_ratio"] > 0.5
                and no_gravity["mirror_alpha_even_ratio"] > 0.1
            ),
            "canonical_no_gravity_pressure_csf_residual_large": (
                no_gravity["best_residual_ratio"] > 1.5
                and no_gravity["gradp_to_csf_norm_ratio_interface"] > 2.0
            ),
            "t3_pressure_csf_residual_large": (
                t3_min_circularity["best_residual_ratio"] > 1.5
                and t3_final["best_residual_ratio"] > 1.0
            ),
            "csf_pressure_symmetry_break_precedes_terminal_interface_diffusion": (
                no_gravity["alpha_max"] > 0.99
                and no_gravity["best_residual_ratio"] > 1.5
                and abs(float(drift.get("canonical_no_gravity", {}).get("center_x_drift", 0.0))) > 1.0e-2
                and t3_final["alpha_max"] < 0.5
            ),
            "qlt03_still_not_ready": t3.get("status") == "NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT",
        },
        "decision": {
            "promote_qlt03_to_ready": False,
            "next_route": (
                "Prioritize pressure-coupled balanced-force CSF on the low-Mach Aux-alpha path. "
                "The no-CSF control preserves symmetry, while canonical no-gravity CSF breaks "
                "lateral symmetry before terminal interface diffusion; transport sharpening alone "
                "should remain secondary until the force-pressure residual is reduced."
            ),
            "avoid_routes": [
                "Do not rely on another local curvature stencil swap without pressure coupling evidence.",
                "Do not promote pure interface sharpening as sufficient while no-gravity CSF residuals remain this large.",
            ],
        },
    }
    verify(report)
    return report


def verify(report: dict) -> None:
    if report.get("status") != STATUS:
        fail(f"unexpected status: {report.get('status')}")
    contracts = report.get("contracts", {})
    required_true = (
        "plotfiles_read",
        "symmetry_control_no_csf_is_machine_symmetric",
        "canonical_no_gravity_csf_breaks_lateral_symmetry",
        "canonical_no_gravity_pressure_csf_residual_large",
        "t3_pressure_csf_residual_large",
        "csf_pressure_symmetry_break_precedes_terminal_interface_diffusion",
        "qlt03_still_not_ready",
    )
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"force-pressure diagnostic contracts not true: {missing}")
    decision = report.get("decision", {})
    if decision.get("promote_qlt03_to_ready") is not False:
        fail("diagnostic report must not promote QLT-03")
    if "balanced-force" not in decision.get("next_route", ""):
        fail("next route must identify balanced-force CSF")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drift-summary", type=Path)
    parser.add_argument("--no-csf-run-dir", type=Path)
    parser.add_argument("--no-gravity-run-dir", type=Path)
    parser.add_argument("--t3-report", type=Path)
    parser.add_argument("--t3-run-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        verify(read_json(args.verify_json))
        return 0
    required = [
        args.drift_summary,
        args.no_csf_run_dir,
        args.no_gravity_run_dir,
        args.t3_report,
        args.t3_run_dir,
        args.output,
    ]
    if any(value is None for value in required):
        fail("all input paths and --output are required unless --verify-json is used")
    report = build_report(
        args.drift_summary,
        args.no_csf_run_dir,
        args.no_gravity_run_dir,
        args.t3_report,
        args.t3_run_dir,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
