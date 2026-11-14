#!/usr/bin/env python3
"""Bridge delayed-ignition engineering evidence to the EXP002 fire dataset."""

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
STATUS_PASS = "PASS-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE"
STATUS_NOT_READY = "NOT_READY-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE"

DEFAULT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_exp002_delayed_ignition_bridge_20260805"
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_h2_fire_exp002_delayed_ignition_bridge_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_h2_fire_exp002_delayed_ignition_bridge_report.md"

CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_cuda_report.json"
)
MPI_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_mpi_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_mpi_report.json"
)
CROSS_PLATFORM_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json"
)
EXP002_REPORT = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/"
    "h2_fire_overpressure_reduced_exp002_report.json"
)
METADATA_REPORT = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805/"
    "h2_fire_overpressure_dataverse_metadata_report.json"
)

EXPECTED_STATUS = {
    CUDA_REPORT: "PASS-H2-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA",
    MPI_REPORT: "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-MPI",
    CROSS_PLATFORM_REPORT: "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-GPU-PARITY",
    EXP002_REPORT: "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002",
    METADATA_REPORT: "PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA",
}

IGNITION_RE = re.compile(
    r"H2 delayed ignition source: enabled=(?P<enabled>[01]), "
    r"time=(?P<time>[-+0-9.eE]+), dt=(?P<dt>[-+0-9.eE]+), "
    r"start_time=(?P<start>[-+0-9.eE]+), duration=(?P<duration>[-+0-9.eE]+), "
    r"power=(?P<power>[-+0-9.eE]+), active_volume=(?P<active_volume>[-+0-9.eE]+), "
    r"time_fraction=(?P<time_fraction>[-+0-9.eE]+), qdot=(?P<qdot>[-+0-9.eE]+)"
)


class BridgeError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BridgeError(message)


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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BridgeError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BridgeError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def staged_log_path(report: dict[str, Any]) -> Path:
    for item in report.get("evidence_files", []):
        if item.get("label") == "staged_run_log":
            return Path(str(item["path"]))
    raise BridgeError("delayed-ignition report does not list staged_run_log")


def parse_ignition_log(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing delayed ignition run log: {path}")
    records: dict[tuple[float, float, float, float], dict[str, float]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = IGNITION_RE.search(line)
        if not match:
            continue
        rec = {key: float(value) for key, value in match.groupdict().items()}
        key = (rec["time"], rec["dt"], rec["time_fraction"], rec["qdot"])
        records.setdefault(key, rec)

    rows = list(records.values())
    require(rows, f"no delayed ignition source log rows parsed from {path}")
    active = [row for row in rows if row["enabled"] == 1.0 and row["time_fraction"] > 1.0e-12]
    require(active, f"no active delayed ignition rows parsed from {path}")

    starts = {row["start"] for row in rows}
    durations = {row["duration"] for row in rows}
    powers = {row["power"] for row in rows}
    volumes = {row["active_volume"] for row in active}
    require(len(starts) == 1, f"non-constant ignition start time in {path}")
    require(len(durations) == 1, f"non-constant ignition duration in {path}")
    require(len(powers) == 1, f"non-constant ignition power in {path}")
    require(len(volumes) == 1, f"non-constant active ignition volume in {path}")

    integrated_energy_j = sum(row["qdot"] * row["active_volume"] * row["dt"] for row in active)
    expected_energy_j = next(iter(powers)) * next(iter(durations))
    rel_error = abs(integrated_energy_j - expected_energy_j) / expected_energy_j
    max_rel_error = 1.0e-10

    return {
        "log_path": str(path),
        "parsed_unique_ignition_rows": len(rows),
        "active_unique_ignition_rows": len(active),
        "active_time_first_s": min(row["time"] for row in active),
        "active_time_last_s": max(row["time"] for row in active),
        "start_time_s": next(iter(starts)),
        "duration_s": next(iter(durations)),
        "power_w": next(iter(powers)),
        "active_volume_m3": next(iter(volumes)),
        "qdot_w_per_m3": active[0]["qdot"],
        "integrated_energy_j": integrated_energy_j,
        "expected_energy_j": expected_energy_j,
        "relative_energy_error": rel_error,
        "max_relative_energy_error_allowed": max_rel_error,
        "energy_conservation_pass": rel_error <= max_rel_error,
    }


def load_and_check_inputs() -> dict[str, dict[str, Any]]:
    reports = {
        "single_cuda": load_json(CUDA_REPORT),
        "cpu_mpi": load_json(MPI_REPORT),
        "cross_platform": load_json(CROSS_PLATFORM_REPORT),
        "exp002": load_json(EXP002_REPORT),
        "metadata": load_json(METADATA_REPORT),
    }
    for path, expected in EXPECTED_STATUS.items():
        data = load_json(path)
        require(data.get("status") == expected, f"{path} status {data.get('status')} != {expected}")
    return reports


def build_report() -> dict[str, Any]:
    reports = load_and_check_inputs()
    cuda_report = reports["single_cuda"]
    mpi_report = reports["cpu_mpi"]
    cross_report = reports["cross_platform"]
    exp002 = reports["exp002"]
    metadata = reports["metadata"]

    cuda_energy = parse_ignition_log(staged_log_path(cuda_report))
    mpi_energy = parse_ignition_log(staged_log_path(mpi_report))

    cuda_input = cuda_report["input_summary"]
    mpi_input = mpi_report["input_summary"]
    for key in ("ignition_source", "ignition_hotspot", "ignition_start_time", "ignition_duration", "ignition_power"):
        require(cuda_input.get(key) == mpi_input.get(key), f"CPU/GPU ignition input mismatch for {key}")

    exp_row = exp002["experiment_matrix_row"]
    pressure_channels = exp002["csv_scan"]["pressure_channels"]
    peak_times = [
        channel["peak_overpressure_baseline_corrected_time_ms"] for channel in pressure_channels.values()
    ]
    peak_values = [
        channel["peak_overpressure_baseline_corrected_bar"] for channel in pressure_channels.values()
    ]
    release_time = float(exp_row["H2 release time [s]"])
    ignition_delay = float(exp_row["Ignition delay time [s]"])
    avg_mfr = float(exp_row["Avg MFR [kg/s]"])
    max_mfr = float(exp_row["Max MFR [kg/s]"])

    exp002_targets = {
        "dataset_doi": exp002["summary"]["source_dataset_doi"],
        "experiment_id": int(exp_row["EXP Number"]),
        "release_time_s": release_time,
        "ignition_delay_time_s": ignition_delay,
        "avg_mfr_kg_s": avg_mfr,
        "max_mfr_kg_s": max_mfr,
        "obstacle_distance_from_nozzle_m": float(exp_row["Obstacle distance from the nozzle [cm]"]) / 100.0,
        "ignition_place": int(exp_row["Ignition place"]),
        "source_csv_filename": exp002["summary"]["source_csv_filename"],
        "source_csv_md5_matches_dataverse": exp002["summary"]["source_csv_md5_matches_dataverse"],
        "pressure_channel_count": len(pressure_channels),
        "peak_corrected_overpressure_bar": max(peak_values),
        "peak_corrected_overpressure_time_range_ms": [min(peak_times), max(peak_times)],
        "calibration_curve": metadata["summary"]["overpressure_calibration_curve_from_readme"],
    }

    model_bridge = {
        "model_has_timed_energy_source": bool(cuda_input["ignition_source"] and mpi_input["ignition_source"]),
        "model_uses_initial_hotspot": bool(cuda_input["ignition_hotspot"] or mpi_input["ignition_hotspot"]),
        "model_ignition_start_time_s": float(cuda_input["ignition_start_time"]),
        "model_ignition_duration_s": float(cuda_input["ignition_duration"]),
        "model_ignition_power_w": float(cuda_input["ignition_power"]),
        "model_injected_energy_j": float(cuda_input["ignition_power"]) * float(cuda_input["ignition_duration"]),
        "model_h2_mdot_kg_s": 5.0e-4,
        "model_final_time_s": cross_report["comparison"]["final_time_cuda"],
        "cpu_gpu_final_h2o_relative_difference": cross_report["comparison"]["final_y_h2o_rel_diff"],
        "cpu_gpu_final_h2o_relative_difference_limit": cross_report["comparison"][
            "max_final_h2o_rel_diff_allowed"
        ],
        "sustained_reaction_output_count": cross_report["comparison"]["sustained_output_count_cuda"],
    }

    scale_gap = {
        "release_time_ratio_exp002_to_current_model": release_time / model_bridge["model_final_time_s"],
        "ignition_delay_ratio_exp002_to_current_model_start": ignition_delay
        / model_bridge["model_ignition_start_time_s"],
        "avg_mfr_ratio_exp002_to_current_model": avg_mfr / model_bridge["model_h2_mdot_kg_s"],
        "max_mfr_ratio_exp002_to_current_model": max_mfr / model_bridge["model_h2_mdot_kg_s"],
    }

    checks = {
        "source_reports_pass": all(load_json(path).get("status") == status for path, status in EXPECTED_STATUS.items()),
        "cuda_energy_conservation_pass": cuda_energy["energy_conservation_pass"],
        "cpu_mpi_energy_conservation_pass": mpi_energy["energy_conservation_pass"],
        "cpu_gpu_delayed_ignition_parity_pass": cross_report.get("status")
        == EXPECTED_STATUS[CROSS_PLATFORM_REPORT],
        "exp002_ready_for_reduced_validation_case": bool(
            exp002["summary"]["ready_for_reduced_validation_case"]
        ),
        "pressure_targets_available": len(pressure_channels) == 4 and max(peak_values) > 0.0,
        "strict_fire_calibration_blocker_cleared": False,
    }

    status = STATUS_PASS if all(value for key, value in checks.items() if key != "strict_fire_calibration_blocker_cleared") else STATUS_NOT_READY
    decision = (
        "delayed_ignition_energy_conserved_and_exp002_mapping_ready"
        if status == STATUS_PASS
        else "delayed_ignition_exp002_bridge_not_ready"
    )

    evidence_files = [
        evidence_entry("single_cuda_report", CUDA_REPORT),
        evidence_entry("cpu_mpi_report", MPI_REPORT),
        evidence_entry("cross_platform_report", CROSS_PLATFORM_REPORT),
        evidence_entry("exp002_reduced_overpressure_report", EXP002_REPORT),
        evidence_entry("exp002_metadata_report", METADATA_REPORT),
        evidence_entry("single_cuda_staged_run_log", staged_log_path(cuda_report)),
        evidence_entry("cpu_mpi_staged_run_log", staged_log_path(mpi_report)),
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "title": "Engineering H2 Fire EXP002 Delayed-Ignition Bridge",
        "status": status,
        "decision": decision,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "validated_capabilities": {
            "timed_energy_ignition_source_integrates_to_requested_energy": checks[
                "cuda_energy_conservation_pass"
            ]
            and checks["cpu_mpi_energy_conservation_pass"],
            "cpu_mpi_and_single_gpu_same_delayed_ignition_case": checks[
                "cpu_gpu_delayed_ignition_parity_pass"
            ],
            "exp002_overpressure_targets_ingested": checks["pressure_targets_available"],
            "exp002_parameters_mapped_for_future_calibration": checks[
                "exp002_ready_for_reduced_validation_case"
            ],
        },
        "checks": checks,
        "energy_conservation": {
            "single_cuda": cuda_energy,
            "cpu_mpi": mpi_energy,
        },
        "exp002_targets": exp002_targets,
        "current_model_bridge": model_bridge,
        "scale_gap_to_exp002": scale_gap,
        "limitations": [
            "This bridge proves energy-source accounting and EXP002 target availability; it is not calibrated CFD overpressure agreement.",
            "The current delayed-ignition run is a stiff reduced window, not the full 3 s EXP002 release and 2.5 s ignition delay.",
            "The current geometry remains synthetic cube/cylinder/pipe-rack STL, not the EXP002 pipe geometry or a cleaned plant CAD import.",
        ],
        "recommended_next_steps": [
            "Build an EXP002-scaled delayed-ignition validation case with the 0.006350705865770578 kg/s average mass flow and 0.29 m obstacle distance.",
            "Compare simulated pressure sensors against the four baseline-corrected EXP002 peaks and arrival times.",
            "Promote the strict fire blocker only after calibrated overpressure or radiation agreement passes the acceptance contract.",
        ],
        "evidence_files": evidence_files,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = [
        f"# {report['title']}",
        "",
        f"- status: `{report['status']}`",
        f"- decision: `{report['decision']}`",
        f"- strict fire calibration blocker cleared: `{report['checks']['strict_fire_calibration_blocker_cleared']}`",
        f"- CUDA ignition energy relative error: `{report['energy_conservation']['single_cuda']['relative_energy_error']:.3e}`",
        f"- CPU/MPI ignition energy relative error: `{report['energy_conservation']['cpu_mpi']['relative_energy_error']:.3e}`",
        f"- EXP002 peak corrected overpressure: `{report['exp002_targets']['peak_corrected_overpressure_bar']}` bar",
        f"- EXP002 ignition delay: `{report['exp002_targets']['ignition_delay_time_s']}` s",
        "",
        "## Limitations",
        "",
    ]
    summary.extend(f"- {item}" for item in report["limitations"])
    path.write_text("\n".join(summary) + "\n", encoding="utf-8")


def verify_report(report: dict[str, Any]) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, f"status is not pass: {report.get('status')}")
    checks = report.get("checks", {})
    for key in (
        "source_reports_pass",
        "cuda_energy_conservation_pass",
        "cpu_mpi_energy_conservation_pass",
        "cpu_gpu_delayed_ignition_parity_pass",
        "exp002_ready_for_reduced_validation_case",
        "pressure_targets_available",
    ):
        require(checks.get(key) is True, f"check did not pass: {key}")
    require(checks.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")

    for platform in ("single_cuda", "cpu_mpi"):
        energy = report["energy_conservation"][platform]
        require(energy["expected_energy_j"] > 0.0, f"{platform} expected energy not positive")
        require(
            math.isclose(
                energy["integrated_energy_j"],
                energy["expected_energy_j"],
                rel_tol=energy["max_relative_energy_error_allowed"],
                abs_tol=1.0e-9,
            ),
            f"{platform} injected energy does not match requested energy",
        )
    require(report["exp002_targets"]["pressure_channel_count"] == 4, "EXP002 pressure channel count mismatch")
    require(report["exp002_targets"]["source_csv_md5_matches_dataverse"] is True, "EXP002 MD5 not verified")
    require(report["current_model_bridge"]["model_uses_initial_hotspot"] is False, "initial hotspot was used")
    require(report["current_model_bridge"]["cpu_gpu_final_h2o_relative_difference"] <= 0.05, "CPU/GPU parity failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()

    if args.verify_json:
        report = load_json(args.verify_json)
        verify_report(report)
        print(f"PASS: {args.verify_json}")
        return 0

    report = build_report()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    verify_report(report)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
