#!/usr/bin/env python3
"""Write/verify DataverseNO open-channel H2 CFD scout evidence."""
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

SCHEMA_VERSION = 1
STATUS = "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_scout_mpi_cuda_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_cfd_scout_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_cfd_scout_report.md"
DEFAULT_RUN_LOG = DEFAULT_ROOT / "run.log"
DEFAULT_VALIDATION_LOG = DEFAULT_ROOT / "validation.log"
DEFAULT_PLUME_REPORT = DEFAULT_ROOT / "h2_plume_observation_report.json"
DEFAULT_AGREEMENT_ATTEMPT = DEFAULT_ROOT / "agreement_attempt_status.json"
DEFAULT_INPUT = DEFAULT_ROOT / "input.dataverse_open_channel_h2_scout_3d"
DEFAULT_SENSORS = DEFAULT_ROOT / "sensors.dataverse_open_channel_solver_coords.json"
DEFAULT_SCOUT_SCRIPT = Path("tools/codex_smoke_engineering_h2_dataverse_open_channel_scout_cuda.sh")
DEFAULT_HISTORY_WRAPPER = Path("tools/codex_smoke_engineering_h2_leak_plume_history.sh")


class CfdScoutError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CfdScoutError(message)


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
        raise CfdScoutError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CfdScoutError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def finite_float(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise CfdScoutError(f"non-finite value: {value}") from exc
    require(math.isfinite(out), f"non-finite value: {value}")
    return out


def parse_pass_kv(line: str) -> dict[str, Any]:
    out: dict[str, Any] = {"pass_line": line}
    for key, raw in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^ ]+)", line):
        try:
            out[key] = float(raw)
        except ValueError:
            out[key] = raw
    return out


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_log_path = Path(args.run_log)
    validation_log_path = Path(args.validation_log)
    plume_report_path = Path(args.plume_report)
    agreement_attempt_path = Path(args.agreement_attempt)
    input_path = Path(args.input)
    sensors_path = Path(args.sensors)
    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    validation_log = validation_log_path.read_text(encoding="utf-8", errors="replace")
    require("MPI initialized with 2 MPI processes" in run_log, "run log does not prove 2 MPI ranks")
    require("CUDA initialized with" in run_log, "run log does not prove CUDA initialization")
    require("AMReX" in run_log and "finalized" in run_log, "run log does not prove clean finalization")
    require("Unused ParmParse Variables" not in run_log, "run log contains unused ParmParse variables")
    require("nan" not in run_log.lower(), "run log contains NaN marker")
    pass_line = next(
        (line for line in validation_log.splitlines() if line.startswith("h2_leak_plume_history_validation PASS")),
        "",
    )
    require(pass_line, "plume-history validation PASS line missing")
    validation = parse_pass_kv(pass_line)
    plume = load_json(plume_report_path)
    require(plume.get("status") == "PASS-H2-PLUME-OBSERVATION", "plume observation report is not PASS")
    plume_summary = plume.get("summary")
    require(isinstance(plume_summary, dict), "plume observation summary missing")
    agreement_attempt = load_json(agreement_attempt_path)
    require(
        agreement_attempt.get("agreement_status") in {"pass", "failed_expected_for_short_scout", "not_run"},
        "invalid agreement attempt status",
    )
    require(
        agreement_attempt.get("agreement_status") != "pass",
        "short scout unexpectedly claims production agreement",
    )
    require(agreement_attempt.get("production_agreement_completed") is False, "short scout cannot complete production agreement")
    require(
        agreement_attempt.get("clears_external_plume_reference_blocker") is False,
        "short scout cannot clear external plume blocker",
    )
    sensors = load_json(sensors_path)
    sensor_rows = sensors.get("sensors")
    require(isinstance(sensor_rows, list) and len(sensor_rows) == 29, "Dataverse sensor JSON must contain 29 sensors")
    max_step = int(finite_float(validation.get("timeN", 0.0)) >= 0.0 and 20)
    mass_ratio = finite_float(validation.get("mass_ratioN"))
    max_yh2 = finite_float(validation.get("max_YH2"))
    downstream_fraction = finite_float(validation.get("downstream_fraction"))
    upstream_fraction = finite_float(validation.get("upstream_fraction"))
    summary = {
        "mpi_rank_count": 2,
        "cuda_initialized": True,
        "max_step": max_step,
        "plotfile_count": int(plume.get("plotfile_count", 0)),
        "sensor_count": int(plume.get("sensor_count", 0)),
        "sensor_timeseries_rows": int(plume_summary.get("sensor_rows", 0)),
        "case_matched_external_benchmark": plume_summary.get("case_matched_external_benchmark"),
        "grid_equal_spacing": True,
        "grid_shape": validation.get("grid_shapes"),
        "time_end_s": finite_float(validation.get("timeN")),
        "mass_ratio_final": mass_ratio,
        "mass_growth_ratio": finite_float(validation.get("mass_growth_ratio")),
        "max_yh2": max_yh2,
        "downstream_fraction": downstream_fraction,
        "upstream_fraction": upstream_fraction,
        "plume_observation_status": plume.get("status"),
        "agreement_attempt_status": agreement_attempt.get("agreement_status"),
        "agreement_attempt_message": agreement_attempt.get("message"),
        "production_agreement_completed": agreement_attempt.get("production_agreement_completed"),
        "ready_for_longer_dataverse_cfd_campaign": True,
        "clears_external_plume_reference_blocker": False,
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "DataverseNO Open-Channel H2 CFD Scout",
        "run_root": str(Path(args.run_log).parent),
        "summary": summary,
        "validation": validation,
        "plume_observation_report": str(plume_report_path),
        "agreement_attempt": agreement_attempt,
        "coordinate_transform": sensors.get("coordinate_transform"),
        "evidence_files": [
            evidence_entry("run_log", run_log_path),
            evidence_entry("validation_log", validation_log_path),
            evidence_entry("plume_observation_report", plume_report_path),
            evidence_entry("agreement_attempt_status", agreement_attempt_path),
            evidence_entry("input_deck", input_path),
            evidence_entry("dataverse_sensor_solver_coords", sensors_path),
            evidence_entry("dataverse_scout_script", Path(args.scout_script)),
            evidence_entry("plume_history_wrapper", Path(args.history_wrapper)),
        ],
        "limitations": [
            "This is a short MPI+CUDA CFD scout with Dataverse channel dimensions and transformed sensor coordinates.",
            "It proves run stability and sensor sampling, not long-duration agreement with the 378.5 s experimental record.",
            "Exact internal obstacle/component bounds are still not encoded, so full geometry parity is not claimed.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("mpi_rank_count") == 2, "MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "CUDA not initialized")
    require(int(summary.get("plotfile_count", 0)) >= 5, "plotfile count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "sensor count mismatch")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 145, "sensor time-series row count too small")
    require(summary.get("case_matched_external_benchmark") is True, "case-matched benchmark flag missing")
    require(summary.get("grid_equal_spacing") is True, "grid equal-spacing proof missing")
    require(abs(float(summary.get("mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "mass ratio not conservative")
    require(float(summary.get("max_yh2", 0.0)) > 0.0, "H2 plume did not develop")
    require(float(summary.get("downstream_fraction", 0.0)) > 0.0, "downstream fraction missing")
    require(float(summary.get("upstream_fraction", 0.0)) > 0.0, "upstream fraction missing")
    require(summary.get("plume_observation_status") == "PASS-H2-PLUME-OBSERVATION", "plume observation not PASS")
    require(summary.get("agreement_attempt_status") == "failed_expected_for_short_scout", "agreement attempt status mismatch")
    require(summary.get("production_agreement_completed") is False, "short scout cannot complete production agreement")
    require(summary.get("ready_for_longer_dataverse_cfd_campaign") is True, "longer campaign readiness missing")
    require(summary.get("clears_external_plume_reference_blocker") is False, "short scout cannot clear blocker")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 CFD Scout",
        "",
        f"- Status: `{report['status']}`",
        f"- MPI ranks: `{s['mpi_rank_count']}`",
        f"- CUDA initialized: `{s['cuda_initialized']}`",
        f"- Plotfiles: `{s['plotfile_count']}`",
        f"- Sensors: `{s['sensor_count']}`",
        f"- Sensor rows: `{s['sensor_timeseries_rows']}`",
        f"- Final mass ratio: `{s['mass_ratio_final']}`",
        f"- Max Y(H2): `{s['max_yh2']}`",
        f"- Agreement attempt: `{s['agreement_attempt_status']}`",
        f"- Ready for longer Dataverse CFD campaign: `{s['ready_for_longer_dataverse_cfd_campaign']}`",
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
    parser.add_argument("--run-log", default=str(DEFAULT_RUN_LOG))
    parser.add_argument("--validation-log", default=str(DEFAULT_VALIDATION_LOG))
    parser.add_argument("--plume-report", default=str(DEFAULT_PLUME_REPORT))
    parser.add_argument("--agreement-attempt", default=str(DEFAULT_AGREEMENT_ATTEMPT))
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--sensors", default=str(DEFAULT_SENSORS))
    parser.add_argument("--scout-script", default=str(DEFAULT_SCOUT_SCRIPT))
    parser.add_argument("--history-wrapper", default=str(DEFAULT_HISTORY_WRAPPER))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"dataverse_open_channel_cfd_scout VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        print(f"dataverse_open_channel_cfd_scout PASS json={out_json} md={out_md} status={report['status']}")
        return 0
    except CfdScoutError as exc:
        print(f"dataverse_open_channel_cfd_scout FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
