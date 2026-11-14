#!/usr/bin/env python3
"""Write an acceptance contract for EXP002 CFD pressure-sensor comparison."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-EXP002-PRESSURE-COMPARISON-CONTRACT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_exp002_pressure_comparison_contract_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_exp002_pressure_comparison_contract_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_exp002_pressure_comparison_contract_report.md"

OVERPRESSURE_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/"
    "h2_fire_exp002_overpressure_calibration_table_report.json"
)
DELAYED_IGNITION_BRIDGE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_exp002_delayed_ignition_bridge_20260805/"
    "engineering_h2_fire_exp002_delayed_ignition_bridge_report.json"
)
CROSS_PLATFORM = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json"
)
STRICT_FIRE_UPDATE = Path(
    "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
    "master_plan_strict_fire_calibration_update_report.json"
)
CUDA_HEADER = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805/"
    "runtime_evidence/plt00120/Header"
)
MPI_HEADER = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_mpi_20260805/"
    "runtime_evidence/plt00120/Header"
)


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def plot_header_variables(path: Path) -> list[str]:
    require(path.is_file(), f"missing plot header: {path}")
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    require(len(lines) >= 3, f"plot header too short: {path}")
    try:
        count = int(lines[1])
    except ValueError as exc:
        raise ContractError(f"cannot parse variable count in {path}") from exc
    variables = lines[2 : 2 + count]
    require(len(variables) == count, f"plot header variable count mismatch: {path}")
    return variables


def read_overpressure_rows(report: dict[str, Any]) -> list[dict[str, str]]:
    csv_path = Path(report["output_files"]["overpressure_metrics_csv"])
    require(csv_path.is_file(), f"missing overpressure CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == 4, f"expected four EXP002 pressure rows, got {len(rows)}")
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    table = load_json(Path(args.overpressure_table))
    bridge = load_json(Path(args.delayed_ignition_bridge))
    cross = load_json(Path(args.cross_platform))
    strict_fire = load_json(Path(args.strict_fire_update))

    require(table.get("status") == "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE", "EXP002 table not ready")
    require(bridge.get("status") == "PASS-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE", "EXP002 ignition bridge not ready")
    require(cross.get("status") == "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-GPU-PARITY", "CPU/GPU parity not ready")
    require(strict_fire.get("summary", {}).get("strict_fire_calibration_blocker_cleared") is False, "strict fire overclaimed")

    rows = read_overpressure_rows(table)
    cuda_vars = plot_header_variables(Path(args.cuda_header))
    mpi_vars = plot_header_variables(Path(args.mpi_header))
    common_vars = sorted(set(cuda_vars).intersection(mpi_vars))
    pressure_like = [name for name in common_vars if "press" in name.lower() or name.lower() in {"p", "pressure"}]
    has_only_domain_avg_pressure = pressure_like == ["avg_pressure"]

    acceptance_contract = {
        "required_reference_metrics": [row["metric_id"] for row in rows],
        "required_reference_metric_count": 4,
        "required_cfd_outputs": [
            "time_series_pressure_kpa_at_each_exp002_sensor",
            "peak_overpressure_kpa_at_each_exp002_sensor",
            "peak_arrival_time_ms_at_each_exp002_sensor",
            "baseline_or_ambient_pressure_definition",
            "sensor_position_mapping_or_documented_surrogate_mapping",
        ],
        "acceptance_criteria": {
            "all_four_sensor_metrics_present": True,
            "peak_overpressure_tolerance_source": "per-row tolerance_abs_kpa and tolerance_rel in overpressure_metrics.csv",
            "arrival_time_tolerance_ms": 25.0,
            "no_nan_inf_solver_abort": True,
            "cpu_or_gpu_parallel_run_required": True,
            "strict_credit_requires_radiation_table_too": True,
        },
    }

    current_gap = {
        "current_delayed_ignition_plot_has_pressure_like_variables": pressure_like,
        "current_delayed_ignition_has_only_domain_avg_pressure": has_only_domain_avg_pressure,
        "current_delayed_ignition_has_sensor_pressure_time_series": False,
        "current_delayed_ignition_has_exp002_sensor_position_mapping": False,
        "comparison_executed": False,
        "strict_fire_calibration_blocker_cleared": False,
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "H2 Fire EXP002 Pressure Comparison Acceptance Contract",
        "status": STATUS_PASS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "exp002_overpressure_table_ready": True,
            "exp002_metric_count": len(rows),
            "delayed_ignition_energy_bridge_ready": True,
            "cpu_gpu_delayed_ignition_parity_ready": True,
            "pressure_comparison_contract_ready": True,
            "current_cfd_pressure_sensor_comparison_executed": False,
            "current_outputs_sufficient_for_exp002_pressure_agreement": False,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "acceptance_contract": acceptance_contract,
        "current_gap": current_gap,
        "limitations": [
            "This is an acceptance contract and preflight, not an EXP002 CFD agreement result.",
            "The current delayed-ignition plotfiles expose avg_pressure, not four EXP002 pressure-sensor time series.",
            "Strict fire credit still requires an actual CFD pressure comparison and a radiation calibration table.",
        ],
        "evidence_files": [
            evidence_entry("overpressure_table_report", Path(args.overpressure_table)),
            evidence_entry("delayed_ignition_bridge", Path(args.delayed_ignition_bridge)),
            evidence_entry("cross_platform_delayed_ignition", Path(args.cross_platform)),
            evidence_entry("strict_fire_update", Path(args.strict_fire_update)),
            evidence_entry("cuda_final_plot_header", Path(args.cuda_header)),
            evidence_entry("cpu_mpi_final_plot_header", Path(args.mpi_header)),
            evidence_entry("overpressure_metrics_csv", Path(table["output_files"]["overpressure_metrics_csv"])),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS_PASS, f"status is not pass: {data.get('status')}")
    summary = data.get("summary", {})
    require(summary.get("exp002_overpressure_table_ready") is True, "EXP002 table not ready")
    require(summary.get("exp002_metric_count") == 4, "EXP002 metric count mismatch")
    require(summary.get("pressure_comparison_contract_ready") is True, "contract not ready")
    require(summary.get("current_cfd_pressure_sensor_comparison_executed") is False, "comparison overclaimed")
    require(summary.get("current_outputs_sufficient_for_exp002_pressure_agreement") is False, "output sufficiency overclaimed")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    contract = data.get("acceptance_contract", {})
    require(len(contract.get("required_reference_metrics", [])) == 4, "contract missing four metrics")
    require(data.get("current_gap", {}).get("current_delayed_ignition_has_only_domain_avg_pressure") is True, "pressure output gap not detected")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire EXP002 Pressure Comparison Acceptance Contract",
        "",
        f"- Status: `{report['status']}`",
        f"- EXP002 metrics: `{s['exp002_metric_count']}`",
        f"- Contract ready: `{s['pressure_comparison_contract_ready']}`",
        f"- CFD comparison executed: `{s['current_cfd_pressure_sensor_comparison_executed']}`",
        f"- Strict fire blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Current Gap",
        "",
        f"- Pressure-like plot variables: `{report['current_gap']['current_delayed_ignition_plot_has_pressure_like_variables']}`",
        f"- Sensor time series present: `{report['current_gap']['current_delayed_ignition_has_sensor_pressure_time_series']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overpressure-table", default=str(OVERPRESSURE_TABLE))
    parser.add_argument("--delayed-ignition-bridge", default=str(DELAYED_IGNITION_BRIDGE))
    parser.add_argument("--cross-platform", default=str(CROSS_PLATFORM))
    parser.add_argument("--strict-fire-update", default=str(STRICT_FIRE_UPDATE))
    parser.add_argument("--cuda-header", default=str(CUDA_HEADER))
    parser.add_argument("--mpi-header", default=str(MPI_HEADER))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_exp002_pressure_comparison_contract VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"h2_fire_exp002_pressure_comparison_contract PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
