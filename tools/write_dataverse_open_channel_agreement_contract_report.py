#!/usr/bin/env python3
"""Write/verify DataverseNO open-channel H2 CFD/reference agreement contract evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-DATAVERSE-OPEN-CHANNEL-H2-AGREEMENT-CONTRACT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_agreement_contract_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_agreement_contract_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_agreement_contract_report.md"
DEFAULT_SELFTEST_CSV = DEFAULT_ROOT / "dataverse_agreement_selftest_simulation_timeseries_long.csv"
DEFAULT_REFERENCE_PACKAGE = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/"
    "dataverse_open_channel_reference_package_report.json"
)

H2_LFL_X = 0.04
DEFAULT_MAX_PEAK_REL_ERROR = 0.25
DEFAULT_MAX_NRMSE = 0.25
DEFAULT_MAX_ARRIVAL_ABS_ERROR_S = 10.0


class AgreementContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AgreementContractError(message)


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
        raise AgreementContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AgreementContractError(f"invalid JSON evidence {path}: {exc}") from exc
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


def finite_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def rel_error(value: float, reference: float) -> float:
    return abs(value - reference) / max(abs(reference), 1.0e-12)


def read_long_timeseries(path: Path) -> dict[str, list[tuple[float, float]]]:
    require(path.is_file(), f"missing long time-series CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = set(reader.fieldnames or [])
        for column in ("time", "sensor_id", "X(H2)"):
            require(column in header, f"long time-series CSV missing required column: {column}")
        by_sensor: dict[str, list[tuple[float, float]]] = {}
        for row_index, row in enumerate(reader):
            sensor_id = str(row.get("sensor_id", "")).strip()
            time = finite_float(row.get("time"))
            x_h2 = finite_float(row.get("X(H2)"))
            require(sensor_id, f"row {row_index} missing sensor_id")
            require(time is not None, f"row {row_index} has non-finite time")
            require(x_h2 is not None, f"row {row_index} has non-finite X(H2)")
            by_sensor.setdefault(sensor_id, []).append((time, x_h2))
    require(by_sensor, f"time-series CSV has no sensor rows: {path}")
    for sensor_id, rows in by_sensor.items():
        rows.sort(key=lambda item: item[0])
        require(len(rows) >= 2, f"sensor {sensor_id} has fewer than two samples")
        for (t0, _), (t1, _) in zip(rows, rows[1:]):
            require(t1 >= t0, f"sensor {sensor_id} times are not monotone")
    return by_sensor


def write_selftest_simulation_csv(reference_csv: Path, output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with reference_csv.open(newline="", encoding="utf-8") as src_fh, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as dst_fh:
        reader = csv.DictReader(src_fh)
        fieldnames = reader.fieldnames or []
        require({"time", "sensor_id", "X(H2)"}.issubset(set(fieldnames)), "reference long CSV missing contract columns")
        writer = csv.DictWriter(dst_fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            writer.writerow(row)


def interp_series(rows: list[tuple[float, float]], time: float) -> float | None:
    if time < rows[0][0] or time > rows[-1][0]:
        return None
    lo = 0
    hi = len(rows) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if rows[mid][0] <= time:
            lo = mid
        else:
            hi = mid
    t0, v0 = rows[lo]
    t1, v1 = rows[hi]
    if t1 == t0:
        return v0
    frac = (time - t0) / (t1 - t0)
    return v0 + frac * (v1 - v0)


def arrival_time(rows: list[tuple[float, float]], threshold: float = H2_LFL_X) -> float | None:
    previous_t, previous_v = rows[0]
    if previous_v >= threshold:
        return previous_t
    for time, value in rows[1:]:
        if value >= threshold:
            if value == previous_v:
                return time
            frac = (threshold - previous_v) / (value - previous_v)
            return previous_t + frac * (time - previous_t)
        previous_t, previous_v = time, value
    return None


def compare_sensor(
    sensor_id: str,
    reference: list[tuple[float, float]],
    simulation: list[tuple[float, float]],
    *,
    max_peak_rel_error: float,
    max_nrmse: float,
    max_arrival_abs_error_s: float,
) -> dict[str, Any]:
    ref_peak_time, ref_peak = max(reference, key=lambda item: item[1])
    sim_peak_time, sim_peak = max(simulation, key=lambda item: item[1])
    common_times = [time for time, _ in reference if simulation[0][0] <= time <= simulation[-1][0]]
    require(len(common_times) >= 2, f"sensor {sensor_id} has fewer than two common comparison samples")
    sq_err = 0.0
    max_abs_err = 0.0
    for time in common_times:
        ref_value = interp_series(reference, time)
        sim_value = interp_series(simulation, time)
        require(ref_value is not None and sim_value is not None, f"sensor {sensor_id} interpolation failed")
        err = sim_value - ref_value
        sq_err += err * err
        max_abs_err = max(max_abs_err, abs(err))
    rmse = math.sqrt(sq_err / len(common_times))
    nrmse = rmse / max(abs(ref_peak), H2_LFL_X, 1.0e-12)
    peak_abs_error = abs(sim_peak - ref_peak)
    peak_rel_error = rel_error(sim_peak, ref_peak)
    ref_arrival = arrival_time(reference)
    sim_arrival = arrival_time(simulation)
    if ref_arrival is None:
        arrival_abs_error_s = None
        arrival_passed = sim_arrival is None
    elif sim_arrival is None:
        arrival_abs_error_s = math.inf
        arrival_passed = False
    else:
        arrival_abs_error_s = abs(sim_arrival - ref_arrival)
        arrival_passed = arrival_abs_error_s <= max_arrival_abs_error_s
    peak_passed = peak_rel_error <= max_peak_rel_error
    nrmse_passed = nrmse <= max_nrmse
    return {
        "sensor_id": sensor_id,
        "common_sample_count": len(common_times),
        "reference_peak_x_h2": ref_peak,
        "reference_peak_time_s": ref_peak_time,
        "simulation_peak_x_h2": sim_peak,
        "simulation_peak_time_s": sim_peak_time,
        "peak_abs_error": peak_abs_error,
        "peak_rel_error": peak_rel_error,
        "peak_passed": peak_passed,
        "rmse_x_h2": rmse,
        "nrmse_by_reference_peak_or_lfl": nrmse,
        "nrmse_passed": nrmse_passed,
        "max_abs_error_x_h2": max_abs_err,
        "reference_arrival_lfl_s": ref_arrival,
        "simulation_arrival_lfl_s": sim_arrival,
        "arrival_abs_error_s": arrival_abs_error_s,
        "arrival_passed": arrival_passed,
        "passed": peak_passed and nrmse_passed and arrival_passed,
    }


def compare_timeseries(
    reference_csv: Path,
    simulation_csv: Path,
    *,
    max_peak_rel_error: float,
    max_nrmse: float,
    max_arrival_abs_error_s: float,
) -> dict[str, Any]:
    reference = read_long_timeseries(reference_csv)
    simulation = read_long_timeseries(simulation_csv)
    require(set(reference) == set(simulation), "simulation sensor IDs do not match reference sensor IDs")
    sensor_checks = [
        compare_sensor(
            sensor_id,
            reference[sensor_id],
            simulation[sensor_id],
            max_peak_rel_error=max_peak_rel_error,
            max_nrmse=max_nrmse,
            max_arrival_abs_error_s=max_arrival_abs_error_s,
        )
        for sensor_id in sorted(reference, key=lambda item: int(item))
    ]
    passed = all(item["passed"] for item in sensor_checks)
    lfl_sensors = [
        item
        for item in sensor_checks
        if item["reference_arrival_lfl_s"] is not None
    ]
    return {
        "sensor_count": len(sensor_checks),
        "lfl_sensor_count": len(lfl_sensors),
        "all_sensors_passed": passed,
        "peak_pass_count": sum(1 for item in sensor_checks if item["peak_passed"]),
        "nrmse_pass_count": sum(1 for item in sensor_checks if item["nrmse_passed"]),
        "arrival_pass_count": sum(1 for item in sensor_checks if item["arrival_passed"]),
        "max_peak_rel_error": max(float(item["peak_rel_error"]) for item in sensor_checks),
        "max_nrmse": max(float(item["nrmse_by_reference_peak_or_lfl"]) for item in sensor_checks),
        "max_arrival_abs_error_s": max(
            (
                float(item["arrival_abs_error_s"])
                for item in sensor_checks
                if item["arrival_abs_error_s"] is not None and math.isfinite(float(item["arrival_abs_error_s"]))
            ),
            default=0.0,
        ),
        "sensor_checks": sensor_checks,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    reference_package_path = Path(args.reference_package_report)
    reference_package = load_json(reference_package_path)
    require(
        reference_package.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE",
        "Dataverse reference package is not PASS",
    )
    outputs = reference_package.get("outputs")
    require(isinstance(outputs, dict), "Dataverse reference package outputs missing")
    reference_csv = Path(str(outputs.get("long_timeseries_csv", "")))
    simulation_csv = Path(args.simulation_long_csv) if args.simulation_long_csv else Path(args.selftest_csv)
    selftest_mode = not args.simulation_long_csv
    if selftest_mode:
        write_selftest_simulation_csv(reference_csv, simulation_csv)
    comparison = compare_timeseries(
        reference_csv,
        simulation_csv,
        max_peak_rel_error=args.max_peak_rel_error,
        max_nrmse=args.max_nrmse,
        max_arrival_abs_error_s=args.max_arrival_abs_error_s,
    )
    if not comparison["all_sensors_passed"]:
        raise AgreementContractError("one or more Dataverse agreement contract sensor checks failed")
    summary = reference_package["summary"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "reference_package_report": str(reference_package_path),
        "reference_long_timeseries_csv": str(reference_csv),
        "simulation_long_timeseries_csv": str(simulation_csv),
        "mode": "selftest_reference_identity" if selftest_mode else "cfd_reference_agreement_scoring",
        "production_agreement_completed": not selftest_mode,
        "clears_external_plume_reference_blocker": False if selftest_mode else comparison["all_sensors_passed"],
        "summary": {
            "selected_case_filename": summary.get("selected_case_filename"),
            "article_test_id": summary.get("article_test_id"),
            "reference_sensor_count": summary.get("sensor_count"),
            "reference_sensor_record_count": summary.get("sensor_record_count"),
            "agreement_sensor_count": comparison["sensor_count"],
            "agreement_lfl_sensor_count": comparison["lfl_sensor_count"],
            "all_sensors_passed": comparison["all_sensors_passed"],
            "peak_pass_count": comparison["peak_pass_count"],
            "nrmse_pass_count": comparison["nrmse_pass_count"],
            "arrival_pass_count": comparison["arrival_pass_count"],
            "max_peak_rel_error_seen": comparison["max_peak_rel_error"],
            "max_nrmse_seen": comparison["max_nrmse"],
            "max_arrival_abs_error_s_seen": comparison["max_arrival_abs_error_s"],
            "max_peak_rel_error_allowed": args.max_peak_rel_error,
            "max_nrmse_allowed": args.max_nrmse,
            "max_arrival_abs_error_s_allowed": args.max_arrival_abs_error_s,
            "ready_for_cfd_reference_agreement_scoring": True,
            "production_agreement_completed": not selftest_mode,
            "selftest_mode": selftest_mode,
            "clears_external_plume_reference_blocker": False if selftest_mode else comparison["all_sensors_passed"],
        },
        "simulation_input_contract": {
            "format": "CSV long table",
            "required_columns": ["time", "sensor_id", "X(H2)"],
            "sensor_ids": [str(item) for item in sorted(range(1, 16))] + [str(item) for item in range(17, 31)],
            "units": {
                "time": "s",
                "X(H2)": "hydrogen volume fraction",
            },
            "comparison_method": "linear interpolation of simulation X(H2) onto reference sensor times",
        },
        "agreement_comparison": comparison,
        "evidence_files": [
            evidence_entry("dataverse_reference_package", reference_package_path),
            evidence_entry("reference_long_timeseries_csv", reference_csv),
            evidence_entry("simulation_long_timeseries_csv", simulation_csv),
        ],
        "limitations": [
            "Default mode is a reference-identity selftest that proves the scorer contract and thresholds only.",
            "The strict external plume blocker remains open until a real CFD sensor-sampling CSV is supplied and scored in production mode.",
            "Exact Dataverse obstacle/component geometry bounds are still needed before full geometry mesh parity can be claimed.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("selected_case_filename") == "23_FFI_P101_T00031.zip", "selected case drifted")
    require(summary.get("article_test_id") == "test-08-1", "article test ID mismatch")
    require(int(summary.get("reference_sensor_count", 0)) == 29, "reference sensor count mismatch")
    require(int(summary.get("agreement_sensor_count", 0)) == 29, "agreement sensor count mismatch")
    require(int(summary.get("agreement_lfl_sensor_count", 0)) >= 3, "agreement LFL sensor count too small")
    require(summary.get("all_sensors_passed") is True, "not all agreement sensors passed")
    require(int(summary.get("peak_pass_count", 0)) == 29, "not all peak checks passed")
    require(int(summary.get("nrmse_pass_count", 0)) == 29, "not all NRMSE checks passed")
    require(summary.get("ready_for_cfd_reference_agreement_scoring") is True, "scorer is not ready")
    if summary.get("selftest_mode") is True:
        require(summary.get("production_agreement_completed") is False, "selftest cannot claim production agreement")
        require(
            summary.get("clears_external_plume_reference_blocker") is False,
            "selftest cannot clear external plume blocker",
        )
    require(float(summary.get("max_peak_rel_error_seen", 1.0)) <= float(summary["max_peak_rel_error_allowed"]), "peak tolerance failed")
    require(float(summary.get("max_nrmse_seen", 1.0)) <= float(summary["max_nrmse_allowed"]), "NRMSE tolerance failed")
    require(
        float(summary.get("max_arrival_abs_error_s_seen", 1.0e99)) <= float(summary["max_arrival_abs_error_s_allowed"]),
        "arrival tolerance failed",
    )
    contract = data.get("simulation_input_contract")
    require(isinstance(contract, dict), "simulation input contract missing")
    require(contract.get("required_columns") == ["time", "sensor_id", "X(H2)"], "required columns mismatch")
    comparison = data.get("agreement_comparison")
    require(isinstance(comparison, dict), "agreement comparison missing")
    sensor_checks = comparison.get("sensor_checks")
    require(isinstance(sensor_checks, list) and len(sensor_checks) == 29, "sensor checks missing")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 Agreement Contract",
        "",
        f"- Status: `{report['status']}`",
        f"- Mode: `{report['mode']}`",
        f"- Selected case: `{s['selected_case_filename']}` / `{s['article_test_id']}`",
        f"- Agreement sensors: `{s['agreement_sensor_count']}`",
        f"- LFL sensors: `{s['agreement_lfl_sensor_count']}`",
        f"- Peak checks: `{s['peak_pass_count']}/{s['agreement_sensor_count']}`",
        f"- NRMSE checks: `{s['nrmse_pass_count']}/{s['agreement_sensor_count']}`",
        f"- Arrival checks passed: `{s['arrival_pass_count']}`",
        f"- Ready for CFD/reference scoring: `{s['ready_for_cfd_reference_agreement_scoring']}`",
        f"- Production agreement completed: `{s['production_agreement_completed']}`",
        f"- Clears external plume blocker: `{s['clears_external_plume_reference_blocker']}`",
        "",
        "## Simulation Input Contract",
        "",
        f"- Required columns: `{report['simulation_input_contract']['required_columns']}`",
        f"- Method: `{report['simulation_input_contract']['comparison_method']}`",
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
    parser.add_argument("--reference-package-report", default=str(DEFAULT_REFERENCE_PACKAGE))
    parser.add_argument("--simulation-long-csv")
    parser.add_argument("--selftest-csv", default=str(DEFAULT_SELFTEST_CSV))
    parser.add_argument("--max-peak-rel-error", type=float, default=DEFAULT_MAX_PEAK_REL_ERROR)
    parser.add_argument("--max-nrmse", type=float, default=DEFAULT_MAX_NRMSE)
    parser.add_argument("--max-arrival-abs-error-s", type=float, default=DEFAULT_MAX_ARRIVAL_ABS_ERROR_S)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(
                "dataverse_open_channel_agreement_contract VERIFY-PASS "
                f"json={args.verify_json} status={data['status']} mode={data['mode']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        print(
            "dataverse_open_channel_agreement_contract PASS "
            f"json={out_json} md={out_md} status={report['status']} mode={report['mode']}"
        )
        return 0
    except AgreementContractError as exc:
        print(f"dataverse_open_channel_agreement_contract FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
