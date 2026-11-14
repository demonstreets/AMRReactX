#!/usr/bin/env python3
"""Write/verify the DataverseNO refined near-source projection MPI+CUDA probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA"
ROOT = Path("docs/codex_audit/evidence/dataverse_refined_source_projection_probe_mpi_cuda_20260807")
DEFAULT_OUTPUT_JSON = ROOT / "dataverse_refined_source_projection_probe_report.json"
DEFAULT_OUTPUT_MD = ROOT / "dataverse_refined_source_projection_probe_report.md"

RUN_LOG = ROOT / "run.log"
VALIDATION_LOG = ROOT / "validation.log"
INPUT_DECK = ROOT / "input.dataverse_refined_source_projection_probe_3d"
STATUS_TXT = ROOT / "status.txt"
RUN_STATUS = ROOT / "run.status"

BAD_LOG_PATTERNS = (
    r"\bAbort\b",
    r"AMReX Error",
    r"SIGABRT",
    r"Segmentation fault",
    r"\b[Nn]a[Nn]\b",
    r"\binf\b",
    r"\bINF\b",
    r"CUDA error",
    r"cudaError",
)


class RefinedSourceProjectionProbeError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RefinedSourceProjectionProbeError(message)


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


def read_kv_from_input(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, raw = stripped.split("=", 1)
        out[key.strip()] = raw.strip()
    return out


def floats(raw: str) -> list[float]:
    values = [float(item) for item in raw.split()]
    require(all(math.isfinite(v) for v in values), f"non-finite input values: {raw}")
    return values


def parse_pass_kv(line: str) -> dict[str, Any]:
    out: dict[str, Any] = {"pass_line": line}
    for key, raw in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^ ]+)", line):
        try:
            out[key] = float(raw)
        except ValueError:
            out[key] = raw
    return out


def bad_markers(text: str) -> list[str]:
    return [pattern for pattern in BAD_LOG_PATTERNS if re.search(pattern, text)]


def first_match(pattern: str, text: str, message: str) -> re.Match[str]:
    match = re.search(pattern, text)
    require(match is not None, message)
    return match


def build_report() -> dict[str, Any]:
    for path in (RUN_LOG, VALIDATION_LOG, INPUT_DECK, STATUS_TXT, RUN_STATUS):
        require(path.is_file(), f"missing evidence file: {path}")
    run_text = RUN_LOG.read_text(encoding="utf-8", errors="replace")
    validation_text = VALIDATION_LOG.read_text(encoding="utf-8", errors="replace")
    input_text = INPUT_DECK.read_text(encoding="utf-8", errors="replace")
    status_text = STATUS_TXT.read_text(encoding="utf-8", errors="replace")
    run_status_text = RUN_STATUS.read_text(encoding="utf-8", errors="replace")
    run_bad_markers = bad_markers(run_text)

    kv = read_kv_from_input(input_text)
    prob_lo = floats(kv["geometry.prob_lo"])
    prob_hi = floats(kv["geometry.prob_hi"])
    n_cell = [int(float(item)) for item in kv["amr.n_cell"].split()]
    dx = [(hi - lo) / n for lo, hi, n in zip(prob_lo, prob_hi, n_cell)]
    leak_center = [float(kv["prob.leak_xc"]), float(kv["prob.leak_yc"]), float(kv["prob.leak_zc"])]
    leak_radius = float(kv["prob.leak_radius"])
    leak_rate = float(kv["prob.leak_rate"])
    leak_vel_x = float(kv["prob.leak_vel_x"])
    fixed_dt = float(kv["amr.fixed_dt"])
    max_step = int(float(kv["amr.max_step"]))
    plot_int = int(float(kv["amr.plot_int"]))
    cell_volume = dx[0] * dx[1] * dx[2]
    cell_center_offsets = [((center - lo) / d) - 0.5 for center, lo, d in zip(leak_center, prob_lo, dx)]
    cell_center_indices = [round(offset) for offset in cell_center_offsets]
    center_alignment_error = max(abs(offset - round(offset)) for offset in cell_center_offsets)

    source_line = first_match(
        r"H2 leak source\[0\]: center=\(([^)]+)\), radius=([^,]+), fraction=([^,]+), "
        r"pressure_fraction=([^,]+), mdot=([^,]+), active_volume=([^,]+), mdot_vol=([^\n]+)",
        run_text,
        "source diagnostic line missing",
    )
    active_volume = float(source_line.group(6))
    mdot_vol = float(source_line.group(7))
    pass_line = next((line for line in validation_text.splitlines() if line.startswith("h2_leak_plume_history_validation PASS")), "")
    require(pass_line, "plume-history validation PASS line missing")
    validation = parse_pass_kv(pass_line)
    plotfiles = sorted((ROOT / "run").glob("plt*"))
    expected_plotfiles = max_step // plot_int + 1
    target_dx = 0.0125
    experimental_radius = 0.0023
    experimental_diameter = 0.0046

    ready = (
        "DONE" in status_text
        and "run_rc=0" in run_status_text
        and "MPI initialized with 2 MPI processes" in run_text
        and "CUDA initialized with" in run_text
        and "finalized" in run_text
        and not run_bad_markers
        and f"STEP [{max_step - 1}]" in run_text
        and len(plotfiles) >= expected_plotfiles
        and (ROOT / "run" / f"plt{max_step:05d}").is_dir()
        and all(abs(value - target_dx) <= 1.0e-12 for value in dx)
        and abs(leak_radius - experimental_radius) <= 1.0e-15
        and abs(experimental_diameter - 2.0 * leak_radius) <= 1.0e-15
        and center_alignment_error <= 1.0e-12
        and abs(active_volume - cell_volume) <= max(1.0e-18, cell_volume * 1.0e-8)
        and mdot_vol > 0.0
        and leak_rate > 0.0
        and leak_vel_x > 600.0
        and fixed_dt * leak_vel_x / min(dx) < 0.01
        and float(validation.get("mass_ratioN", 0.0)) > 0.0
        and float(validation.get("max_YH2", 0.0)) > 0.0
        and float(validation.get("downstream_fraction", 0.0)) >= 0.0
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA",
        "summary": {
            "refined_source_projection_probe_ready": ready,
            "mpi_rank_count": 2,
            "cuda_initialized": "CUDA initialized with" in run_text,
            "run_returncode_zero": "run_rc=0" in run_status_text,
            "run_finalized": "finalized" in run_text,
            "run_log_has_no_abort_nan_or_cuda_error": not run_bad_markers,
            "run_bad_markers": run_bad_markers,
            "n_cell": n_cell,
            "dx_m": dx,
            "target_dx_m": target_dx,
            "experimental_orifice_diameter_m": experimental_diameter,
            "experimental_orifice_radius_m": experimental_radius,
            "leak_radius_m": leak_radius,
            "leak_center_m": leak_center,
            "cell_center_indices": cell_center_indices,
            "center_alignment_error_cells": center_alignment_error,
            "active_volume_m3": active_volume,
            "single_cell_volume_m3": cell_volume,
            "active_volume_equals_single_cell": abs(active_volume - cell_volume) <= max(1.0e-18, cell_volume * 1.0e-8),
            "mdot_kg_s": leak_rate,
            "mdot_vol_kg_m3_s": mdot_vol,
            "equivalent_orifice_velocity_m_s": leak_vel_x,
            "fixed_dt_s": fixed_dt,
            "max_step": max_step,
            "time_end_s": max_step * fixed_dt,
            "source_cfl": fixed_dt * leak_vel_x / min(dx),
            "plotfile_count": len(plotfiles),
            "validation_mass_ratio_final": float(validation.get("mass_ratioN", 0.0)),
            "validation_max_yh2": float(validation.get("max_YH2", 0.0)),
            "validation_downstream_fraction": float(validation.get("downstream_fraction", 0.0)),
            "production_agreement_completed": False,
            "clears_external_plume_reference_blocker": False,
            "strict_blocker_still_open": True,
        },
        "validation": validation,
        "limitations": [
            "This is a near-source refined projection stability probe, not a full-channel Dataverse plume-shape agreement case.",
            "The experimental 2.3 mm radius is represented by one cell-centered source cell at dx=0.0125 m; longer full-domain refinement or source projection is still required for production agreement.",
            "This evidence reduces the source/grid mismatch risk but does not clear the strict external plume-shape blocker.",
        ],
        "evidence_files": [
            evidence_entry("run_log", RUN_LOG),
            evidence_entry("validation_log", VALIDATION_LOG),
            evidence_entry("input_deck", INPUT_DECK),
            evidence_entry("status_txt", STATUS_TXT),
            evidence_entry("run_status", RUN_STATUS),
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("refined_source_projection_probe_ready") is True, "probe not ready")
    require(summary.get("mpi_rank_count") == 2, "MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "CUDA missing")
    require(summary.get("run_returncode_zero") is True, "run return code not zero")
    require(summary.get("run_finalized") is True, "run did not finalize")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "bad run-log marker")
    require(all(abs(float(v) - 0.0125) <= 1.0e-12 for v in summary.get("dx_m", [])), "target dx mismatch")
    require(abs(float(summary.get("leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "experimental leak radius mismatch")
    require(float(summary.get("center_alignment_error_cells", 1.0)) <= 1.0e-12, "source center is not cell-centered")
    require(summary.get("active_volume_equals_single_cell") is True, "source active volume is not one refined cell")
    require(float(summary.get("source_cfl", 1.0)) < 0.01, "source CFL too large for probe")
    require(float(summary.get("validation_mass_ratio_final", 0.0)) > 0.0, "no retained H2 mass")
    require(float(summary.get("validation_max_yh2", 0.0)) > 0.0, "no H2 plume")
    require(summary.get("production_agreement_completed") is False, "probe must not claim production agreement")
    require(summary.get("clears_external_plume_reference_blocker") is False, "probe must not clear strict blocker")
    require(summary.get("strict_blocker_still_open") is True, "strict blocker state missing")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = report["summary"]
    lines = [
        "# DataverseNO Refined Source Projection Probe",
        "",
        f"- Status: `{report['status']}`",
        f"- MPI ranks: `{s['mpi_rank_count']}`",
        f"- CUDA initialized: `{s['cuda_initialized']}`",
        f"- Grid: `{s['n_cell']}`",
        f"- dx: `{s['dx_m']}` m",
        f"- Leak radius: `{s['leak_radius_m']}` m",
        f"- Active volume: `{s['active_volume_m3']}` m3",
        f"- Single-cell volume: `{s['single_cell_volume_m3']}` m3",
        f"- Source CFL: `{s['source_cfl']}`",
        f"- Time end: `{s['time_end_s']}` s",
        f"- Max Y(H2): `{s['validation_max_yh2']}`",
        f"- Clears strict external plume blocker: `{s['clears_external_plume_reference_blocker']}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    output_md.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify_json:
        data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
        validate_report(data, verify_hashes=True)
        print(f"dataverse_refined_source_projection_probe VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0
    report = build_report()
    validate_report(report, verify_hashes=False)
    write_outputs(report, Path(args.output_json), Path(args.output_md))
    print(f"dataverse_refined_source_projection_probe PASS json={args.output_json} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
