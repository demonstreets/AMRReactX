#!/usr/bin/env python3
"""Reconcile DataverseNO long-window agreement evidence with current refined-source status."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_long_window_reconciliation_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_long_window_reconciliation_report.md"

AGREEMENT_120S = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/"
    "dataverse_open_channel_cfd_agreement_attempt_report.json"
)
AGREEMENT_120S_INPUT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/"
    "input.dataverse_open_channel_h2_scout_3d"
)
REFINED_1000 = Path(
    "docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_cuda_20260807/"
    "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_report.json"
)
REFINED_1000_INPUT = Path(
    "docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_cuda_20260807/"
    "input.dataverse_full_channel_refined_source_dx025_1000step_dt5em6_3d"
)
AMR_IMPLEMENTATION = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/"
    "dataverse_open_channel_amr_source_projection_implementation_report.json"
)
REFERENCE_PACKAGE = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/"
    "dataverse_open_channel_reference_package_report.json"
)


class ReconciliationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReconciliationError(message)


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
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReconciliationError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReconciliationError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_input(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line and "=" in line:
            key, value = line.split("=", 1)
            vals[key.strip()] = value.strip()
    return vals


def input_float(vals: dict[str, str], key: str) -> float:
    require(key in vals, f"missing input key: {key}")
    value = float(vals[key].split()[0])
    require(math.isfinite(value), f"non-finite input key: {key}")
    return value


def build_report() -> dict[str, Any]:
    agreement_120 = load_json(AGREEMENT_120S)
    refined_1000 = load_json(REFINED_1000)
    amr_impl = load_json(AMR_IMPLEMENTATION)
    reference = load_json(REFERENCE_PACKAGE)
    baseline_input = parse_input(AGREEMENT_120S_INPUT)
    refined_input = parse_input(REFINED_1000_INPUT)

    agreement_summary = agreement_120.get("summary", {})
    refined_summary = refined_1000.get("summary", {})
    amr_summary = amr_impl.get("summary", {})
    reference_summary = reference.get("summary", {})
    require(isinstance(agreement_summary, dict), "120s agreement summary missing")
    require(isinstance(refined_summary, dict), "refined 1000-step summary missing")
    require(isinstance(amr_summary, dict), "AMR implementation summary missing")
    require(isinstance(reference_summary, dict), "reference package summary missing")

    baseline_radius = input_float(baseline_input, "prob.leak_radius")
    refined_radius = input_float(refined_input, "prob.leak_radius")
    refined_dt = input_float(refined_input, "amr.fixed_dt")
    refined_time_end = float(refined_summary["time_end_s"])
    peak_window_start = 113.0
    peak_window_end = 117.0
    steps_to_113s_at_refined_dt = math.ceil(peak_window_start / refined_dt)
    steps_to_120s_at_refined_dt = math.ceil(120.0 / refined_dt)

    long_window_reached = float(agreement_summary["simulation_time_end_s"]) >= peak_window_end
    long_window_quantified = agreement_120.get("status") == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING"
    refined_source_ready = (
        refined_1000.get("status")
        == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA"
    )
    amr_ready = (
        amr_impl.get("status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION"
        and amr_summary.get("source_projected_only_on_finest_available_level") is True
    )
    baseline_uses_inflated_source = baseline_radius / refined_radius > 10.0
    strict_gap_ready = (
        long_window_reached
        and long_window_quantified
        and refined_source_ready
        and amr_ready
        and baseline_uses_inflated_source
        and refined_time_end < 1.0
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if strict_gap_ready else "NOT_READY-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
        "summary": {
            "long_window_reconciliation_ready": strict_gap_ready,
            "existing_120s_window_reaches_experimental_peak_interval": long_window_reached,
            "existing_120s_window_quantified_against_reference": long_window_quantified,
            "existing_120s_all_sensors_passed": agreement_summary.get("all_sensors_passed"),
            "existing_120s_failed_sensor_count": agreement_summary.get("failed_sensor_count"),
            "existing_120s_simulation_time_end_s": agreement_summary.get("simulation_time_end_s"),
            "existing_120s_peak_window_common_sample_count_min": agreement_summary.get("common_sample_count_min"),
            "existing_120s_peak_pass_count": agreement_summary.get("peak_pass_count"),
            "existing_120s_nrmse_pass_count": agreement_summary.get("nrmse_pass_count"),
            "existing_120s_arrival_pass_count": agreement_summary.get("arrival_pass_count"),
            "existing_120s_max_peak_rel_error": agreement_summary.get("max_peak_rel_error"),
            "existing_120s_max_nrmse": agreement_summary.get("max_nrmse"),
            "existing_120s_input_leak_radius_m": baseline_radius,
            "current_refined_source_ready": refined_source_ready,
            "current_refined_source_time_end_s": refined_time_end,
            "current_refined_source_leak_radius_m": refined_radius,
            "current_refined_source_dt_s": refined_dt,
            "current_refined_source_source_cfl": refined_summary.get("source_cfl"),
            "amr_finest_owner_projection_ready": amr_ready,
            "baseline_to_refined_source_radius_ratio": baseline_radius / refined_radius,
            "steps_to_113s_at_current_refined_dt": steps_to_113s_at_refined_dt,
            "steps_to_120s_at_current_refined_dt": steps_to_120s_at_refined_dt,
            "reference_peak_interval_s": [peak_window_start, peak_window_end],
            "reference_selected_case_filename": reference_summary.get("selected_case_filename"),
            "production_agreement_completed": False,
            "clears_external_plume_reference_blocker": False,
            "strict_blocker_still_open": True,
        },
        "interpretation": [
            "The repository already contains a 120 s MPI+CUDA agreement attempt that reaches the 113-117 s reference peak interval.",
            "That 120 s attempt used an inflated 0.08 m numerical source radius and did not pass the production agreement thresholds.",
            "The current refined 2.3 mm source plus AMR finest-owner projection is implemented and build-verified, but its full-channel run evidence currently reaches only 0.005 s.",
            "At dt=5e-6 s, a direct refined-source run to 113 s would require about 22.6 million steps, so a production long-window campaign needs either a calibrated stable larger timestep strategy, more resources, or additional modeling changes.",
        ],
        "evidence_files": [
            evidence_entry("120s_agreement_attempt", AGREEMENT_120S),
            evidence_entry("120s_input", AGREEMENT_120S_INPUT),
            evidence_entry("refined_1000step_report", REFINED_1000),
            evidence_entry("refined_1000step_input", REFINED_1000_INPUT),
            evidence_entry("amr_source_projection_implementation", AMR_IMPLEMENTATION),
            evidence_entry("reference_package", REFERENCE_PACKAGE),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "long-window reconciliation is not triaged")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("long_window_reconciliation_ready") is True, "reconciliation not ready")
    require(summary.get("existing_120s_window_reaches_experimental_peak_interval") is True, "120s window did not reach peak interval")
    require(summary.get("existing_120s_window_quantified_against_reference") is True, "120s window not quantified")
    require(summary.get("existing_120s_all_sensors_passed") is False, "unexpected 120s production agreement PASS")
    require(int(summary.get("existing_120s_failed_sensor_count", 0)) > 0, "120s failed sensor count missing")
    require(summary.get("current_refined_source_ready") is True, "current refined-source evidence missing")
    require(summary.get("amr_finest_owner_projection_ready") is True, "AMR finest-owner projection evidence missing")
    require(float(summary.get("baseline_to_refined_source_radius_ratio", 0.0)) > 10.0, "baseline/refined source radius ratio too small")
    require(int(summary.get("steps_to_113s_at_current_refined_dt", 0)) > 20_000_000, "refined long-window step estimate too small")
    require(summary.get("production_agreement_completed") is False, "reconciliation must not claim production agreement")
    require(summary.get("clears_external_plume_reference_blocker") is False, "reconciliation must not clear blocker")
    require(summary.get("strict_blocker_still_open") is True, "strict blocker state missing")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], output: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO Long-Window Reconciliation",
        "",
        f"- Status: `{report['status']}`",
        f"- Existing 120 s window reaches peak interval: `{s['existing_120s_window_reaches_experimental_peak_interval']}`",
        f"- Existing 120 s all sensors passed: `{s['existing_120s_all_sensors_passed']}`",
        f"- Existing 120 s failed sensors: `{s['existing_120s_failed_sensor_count']}`",
        f"- Current refined source ready: `{s['current_refined_source_ready']}`",
        f"- Current refined source time end: `{s['current_refined_source_time_end_s']}` s",
        f"- AMR finest-owner projection ready: `{s['amr_finest_owner_projection_ready']}`",
        f"- Steps to 113 s at current refined dt: `{s['steps_to_113s_at_current_refined_dt']}`",
        f"- Strict blocker cleared: `{s['clears_external_plume_reference_blocker']}`",
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in report["interpretation"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"dataverse_open_channel_long_window_reconciliation VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"dataverse_open_channel_long_window_reconciliation PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
