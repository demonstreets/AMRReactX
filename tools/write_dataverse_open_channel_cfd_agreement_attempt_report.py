#!/usr/bin/env python3
"""Write/verify a quantified DataverseNO CFD/reference agreement attempt report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASSING = "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT"
STATUS_QUANTIFIED_NOT_PASSING = "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_cfd_agreement_attempt_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_cfd_agreement_attempt_report.md"
DEFAULT_SIMULATION_CSV = DEFAULT_ROOT / "sensor_timeseries.csv"
DEFAULT_PLUME_REPORT = DEFAULT_ROOT / "h2_plume_observation_report.json"
DEFAULT_VALIDATION_LOG = DEFAULT_ROOT / "validation.log"
DEFAULT_RUN_LOG = DEFAULT_ROOT / "run.log"
DEFAULT_INPUT = DEFAULT_ROOT / "input.dataverse_open_channel_h2_scout_3d"
AGREEMENT_MODULE = Path("tools/write_dataverse_open_channel_agreement_contract_report.py")
REFERENCE_PACKAGE = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/"
    "dataverse_open_channel_reference_package_report.json"
)


class AgreementAttemptError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AgreementAttemptError(message)


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
        raise AgreementAttemptError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AgreementAttemptError(f"invalid JSON evidence {path}: {exc}") from exc
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


def load_agreement_module() -> Any:
    require(AGREEMENT_MODULE.is_file(), f"missing agreement scorer module: {AGREEMENT_MODULE}")
    spec = importlib.util.spec_from_file_location("dataverse_agreement_contract", AGREEMENT_MODULE)
    require(spec is not None and spec.loader is not None, "unable to load agreement scorer module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finite_max(values: list[Any]) -> float | None:
    finite = []
    for value in values:
        try:
            f = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f):
            finite.append(f)
    return max(finite) if finite else None


def parse_validation_log(path: Path) -> dict[str, float]:
    text = path.read_text(errors="replace")
    matches = re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([-+0-9.eE]+)", text)
    parsed: dict[str, float] = {}
    for key, value in matches:
        try:
            parsed[key] = float(value)
        except ValueError:
            continue
    return parsed


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    module = load_agreement_module()
    reference_package = load_json(Path(args.reference_package_report))
    require(
        reference_package.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE",
        "reference package is not PASS",
    )
    outputs = reference_package.get("outputs")
    require(isinstance(outputs, dict), "reference package outputs missing")
    reference_csv = Path(str(outputs.get("long_timeseries_csv", "")))
    simulation_csv = Path(args.simulation_long_csv)
    plume_report = load_json(Path(args.plume_report))
    plume_summary = plume_report.get("summary")
    require(isinstance(plume_summary, dict), "plume report summary missing")
    validation = parse_validation_log(Path(args.validation_log))
    simulation_time_end = plume_summary.get("time_end", plume_summary.get("time_end_s"))
    simulation_max_yh2 = plume_summary.get("max_peak_X", plume_summary.get("max_yh2"))
    simulation_mass_ratio = validation.get("mass_ratioN")

    comparison = module.compare_timeseries(
        reference_csv,
        simulation_csv,
        max_peak_rel_error=args.max_peak_rel_error,
        max_nrmse=args.max_nrmse,
        max_arrival_abs_error_s=args.max_arrival_abs_error_s,
    )
    sensor_checks = comparison["sensor_checks"]
    common_counts = [int(item["common_sample_count"]) for item in sensor_checks]
    failed_sensor_ids = [item["sensor_id"] for item in sensor_checks if not item["passed"]]
    lfl_failed_sensor_ids = [
        item["sensor_id"]
        for item in sensor_checks
        if item["reference_arrival_lfl_s"] is not None and not item["arrival_passed"]
    ]
    production_passed = bool(comparison["all_sensors_passed"])
    status = STATUS_PASSING if production_passed else STATUS_QUANTIFIED_NOT_PASSING

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "reference_package_report": str(args.reference_package_report),
        "reference_long_timeseries_csv": str(reference_csv),
        "simulation_long_timeseries_csv": str(simulation_csv),
        "plume_report": str(args.plume_report),
        "mode": "cfd_reference_agreement_scoring_attempt",
        "production_agreement_completed": production_passed,
        "clears_external_plume_reference_blocker": production_passed,
        "thresholds": {
            "max_peak_rel_error": args.max_peak_rel_error,
            "max_nrmse": args.max_nrmse,
            "max_arrival_abs_error_s": args.max_arrival_abs_error_s,
        },
        "comparison": comparison,
        "summary": {
            "agreement_attempt_quantified": True,
            "all_sensors_passed": production_passed,
            "sensor_count": comparison["sensor_count"],
            "lfl_sensor_count": comparison["lfl_sensor_count"],
            "failed_sensor_count": len(failed_sensor_ids),
            "failed_lfl_arrival_sensor_count": len(lfl_failed_sensor_ids),
            "peak_pass_count": comparison["peak_pass_count"],
            "nrmse_pass_count": comparison["nrmse_pass_count"],
            "arrival_pass_count": comparison["arrival_pass_count"],
            "common_sample_count_min": min(common_counts),
            "common_sample_count_max": max(common_counts),
            "max_peak_rel_error": comparison["max_peak_rel_error"],
            "max_nrmse": comparison["max_nrmse"],
            "max_arrival_abs_error_s": comparison["max_arrival_abs_error_s"],
            "simulation_time_end_s": simulation_time_end,
            "simulation_max_yh2": simulation_max_yh2,
            "simulation_mass_ratio_final": simulation_mass_ratio,
            "production_agreement_completed": production_passed,
            "clears_external_plume_reference_blocker": production_passed,
        },
        "failed_sensor_ids": failed_sensor_ids,
        "failed_lfl_arrival_sensor_ids": lfl_failed_sensor_ids,
        "limitations": [
            "This 2 s MPI+CUDA CFD window proves stable Dataverse sensor sampling and quantitative agreement scoring.",
            "It is far shorter than the 378.5 s experimental record, whose main H2 peaks occur near 113-117 s.",
            "The report intentionally does not clear the strict external plume reference blocker unless all threshold checks pass.",
        ],
        "evidence_files": [
            evidence_entry("reference_package_report", Path(args.reference_package_report)),
            evidence_entry("reference_long_timeseries_csv", reference_csv),
            evidence_entry("simulation_long_timeseries_csv", simulation_csv),
            evidence_entry("plume_report", Path(args.plume_report)),
            evidence_entry("validation_log", Path(args.validation_log)),
            evidence_entry("run_log", Path(args.run_log)),
            evidence_entry("input_deck", Path(args.input)),
            evidence_entry("agreement_scorer_module", AGREEMENT_MODULE),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASSING, STATUS_QUANTIFIED_NOT_PASSING}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("agreement_attempt_quantified") is True, "agreement attempt was not quantified")
    require(int(summary.get("sensor_count", 0)) == 29, "sensor count mismatch")
    require(int(summary.get("common_sample_count_min", 0)) >= 2, "not enough common samples")
    require(float(summary.get("simulation_time_end_s", 0.0)) >= 1.999, "simulation did not reach 2 s window")
    require(abs(float(summary.get("simulation_mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "mass ratio drift")
    require(float(summary.get("simulation_max_yh2", 0.0)) > 0.0, "H2 plume missing")
    if data.get("status") == STATUS_PASSING:
        require(summary.get("all_sensors_passed") is True, "PASS status without all sensors passing")
        require(summary.get("production_agreement_completed") is True, "PASS status without production agreement")
        require(summary.get("clears_external_plume_reference_blocker") is True, "PASS status does not clear blocker")
    else:
        require(summary.get("all_sensors_passed") is False, "not-passing status with all sensors passing")
        require(summary.get("production_agreement_completed") is False, "not-passing attempt cannot be production complete")
        require(summary.get("clears_external_plume_reference_blocker") is False, "not-passing attempt cannot clear blocker")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 CFD Agreement Attempt",
        "",
        f"- Status: `{report['status']}`",
        f"- Sensors: `{s['sensor_count']}`",
        f"- Common samples per sensor: `{s['common_sample_count_min']}` to `{s['common_sample_count_max']}`",
        f"- Peak pass count: `{s['peak_pass_count']}`",
        f"- NRMSE pass count: `{s['nrmse_pass_count']}`",
        f"- Arrival pass count: `{s['arrival_pass_count']}`",
        f"- Failed sensors: `{s['failed_sensor_count']}`",
        f"- Simulation time end: `{s['simulation_time_end_s']}`",
        f"- Production agreement completed: `{s['production_agreement_completed']}`",
        f"- Clears external plume blocker: `{s['clears_external_plume_reference_blocker']}`",
        "",
        "## Limitations",
        "",
    ]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-package-report", default=str(REFERENCE_PACKAGE))
    parser.add_argument("--simulation-long-csv", default=str(DEFAULT_SIMULATION_CSV))
    parser.add_argument("--plume-report", default=str(DEFAULT_PLUME_REPORT))
    parser.add_argument("--validation-log", default=str(DEFAULT_VALIDATION_LOG))
    parser.add_argument("--run-log", default=str(DEFAULT_RUN_LOG))
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--max-peak-rel-error", type=float, default=0.25)
    parser.add_argument("--max-nrmse", type=float, default=0.25)
    parser.add_argument("--max-arrival-abs-error-s", type=float, default=10.0)
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"dataverse_open_channel_cfd_agreement_attempt VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        print(f"dataverse_open_channel_cfd_agreement_attempt PASS json={out_json} status={report['status']}")
        return 0
    except AgreementAttemptError as exc:
        print(f"dataverse_open_channel_cfd_agreement_attempt FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
