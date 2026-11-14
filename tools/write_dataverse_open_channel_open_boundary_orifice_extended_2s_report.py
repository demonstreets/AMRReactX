#!/usr/bin/env python3
"""Write/verify the 2s open/open DataverseNO orifice MPI+CUDA screen."""
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
STATUS = "PASS-DATAVERSE-OPEN-CHANNEL-OPEN-BOUNDARY-ORIFICE-EXTENDED-2S-MPI-CUDA"
ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807")
DEFAULT_OUTPUT_JSON = ROOT / "dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_screen_report.json"
DEFAULT_OUTPUT_MD = ROOT / "dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_screen_report.md"

RUN_LOG = ROOT / "run.log"
VALIDATION_LOG = ROOT / "validation_open_boundary_2s.log"
PLUME_REPORT = ROOT / "h2_plume_observation_report.json"
AGREEMENT_STATUS = ROOT / "agreement_attempt_status.json"
INPUT_DECK = ROOT / "input.dataverse_open_channel_h2_scout_3d"
SENSORS = ROOT / "sensors.dataverse_open_channel_solver_coords.json"
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


class OpenBoundary2sError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OpenBoundary2sError(message)


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
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def finite_float(value: Any) -> float:
    out = float(value)
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


def bad_markers(text: str) -> list[str]:
    return [pattern for pattern in BAD_LOG_PATTERNS if re.search(pattern, text)]


def build_report() -> dict[str, Any]:
    for path in (RUN_LOG, VALIDATION_LOG, PLUME_REPORT, AGREEMENT_STATUS, INPUT_DECK, SENSORS, STATUS_TXT, RUN_STATUS):
        require(path.is_file(), f"missing evidence file: {path}")
    run_text = RUN_LOG.read_text(encoding="utf-8", errors="replace")
    validation_text = VALIDATION_LOG.read_text(encoding="utf-8", errors="replace")
    input_text = INPUT_DECK.read_text(encoding="utf-8", errors="replace")
    status_text = STATUS_TXT.read_text(encoding="utf-8", errors="replace")
    run_status_text = RUN_STATUS.read_text(encoding="utf-8", errors="replace")
    plume = load_json(PLUME_REPORT)
    agreement = load_json(AGREEMENT_STATUS)
    sensors = load_json(SENSORS)
    pass_line = next((line for line in validation_text.splitlines() if line.startswith("h2_leak_plume_history_validation PASS")), "")
    require(pass_line, "2s open-boundary validation PASS line missing")
    validation = parse_pass_kv(pass_line)
    plume_summary = plume.get("summary", {})
    require(isinstance(plume_summary, dict), "plume summary missing")

    plotfiles = sorted((ROOT / "run").glob("plt*"))
    run_bad_markers = bad_markers(run_text)
    time_end_s = finite_float(validation.get("timeN"))
    mass_ratio = finite_float(validation.get("mass_ratioN"))
    mass_growth_ratio = finite_float(validation.get("mass_growth_ratio"))
    max_yh2 = finite_float(validation.get("max_YH2"))
    downstream_fraction = finite_float(validation.get("downstream_fraction"))
    upstream_fraction = finite_float(validation.get("upstream_fraction"))

    ready = (
        "DONE" in status_text
        and "run_rc=0" in run_status_text
        and "MPI initialized with 2 MPI processes" in run_text
        and "CUDA initialized with" in run_text
        and "AMReX" in run_text
        and "finalized" in run_text
        and not run_bad_markers
        and "STEP [19999]" in run_text
        and len(plotfiles) >= 21
        and (ROOT / "run" / "plt20000").is_dir()
        and abs(time_end_s - 2.0) <= 1.0e-12
        and 0.75 <= mass_ratio <= 1.05
        and mass_growth_ratio > 10.0
        and max_yh2 > 0.015
        and downstream_fraction > 0.99
        and upstream_fraction >= 0.0
        and plume.get("status") == "PASS-H2-PLUME-OBSERVATION"
        and int(plume.get("plotfile_count", 0)) >= 21
        and int(plume.get("sensor_count", 0)) == 29
        and int(plume_summary.get("sensor_rows", 0)) >= 600
        and agreement.get("production_agreement_completed") is False
        and agreement.get("clears_external_plume_reference_blocker") is False
        and "peleLM.lo_bc = Outflow NoSlipWallAdiab NoSlipWallAdiab" in input_text
        and "peleLM.hi_bc = Outflow NoSlipWallAdiab NoSlipWallAdiab" in input_text
        and "amr.max_step = 20000" in input_text
        and "amr.fixed_dt = 1.000000000000e-04" in input_text
        and "prob.leak_vel_x = 6.567687631723e+02" in input_text
        and isinstance(sensors.get("sensors"), list)
        and len(sensors["sensors"]) == 29
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-DATAVERSE-OPEN-CHANNEL-OPEN-BOUNDARY-ORIFICE-EXTENDED-2S-MPI-CUDA",
        "summary": {
            "open_boundary_orifice_extended_2s_ready": ready,
            "mpi_rank_count": 2,
            "cuda_initialized": "CUDA initialized with" in run_text,
            "run_returncode_zero": "run_rc=0" in run_status_text,
            "run_finalized": "AMReX" in run_text and "finalized" in run_text,
            "run_log_has_no_abort_nan_or_cuda_error": not run_bad_markers,
            "run_bad_markers": run_bad_markers,
            "plotfile_count": len(plotfiles),
            "sensor_count": int(plume.get("sensor_count", 0)),
            "sensor_timeseries_rows": int(plume_summary.get("sensor_rows", 0)),
            "time_end_s": time_end_s,
            "mass_ratio_final": mass_ratio,
            "mass_ratio_interpreted_as_open_boundary_retained_mass": True,
            "mass_growth_ratio": mass_growth_ratio,
            "max_yh2": max_yh2,
            "downstream_fraction": downstream_fraction,
            "upstream_fraction": upstream_fraction,
            "plume_observation_status": plume.get("status"),
            "agreement_attempt_status": agreement.get("agreement_status"),
            "production_agreement_completed": agreement.get("production_agreement_completed"),
            "clears_external_plume_reference_blocker": agreement.get("clears_external_plume_reference_blocker"),
            "strict_blocker_still_open": True,
        },
        "validation": validation,
        "agreement_attempt": agreement,
        "limitations": [
            "This is a 2s MPI+CUDA stability and agreement-screen window, not a production-duration match to the external plume-shape record.",
            "Open/open boundaries allow H2 to leave the domain; mass_ratio_final is retained in-domain mass divided by injected mass.",
            "This evidence strengthens the external-reference path but does not clear the strict external plume-shape blocker.",
        ],
        "evidence_files": [
            evidence_entry("run_log", RUN_LOG),
            evidence_entry("validation_open_boundary_2s_log", VALIDATION_LOG),
            evidence_entry("plume_observation_report", PLUME_REPORT),
            evidence_entry("agreement_attempt_status", AGREEMENT_STATUS),
            evidence_entry("input_deck", INPUT_DECK),
            evidence_entry("dataverse_sensor_solver_coords", SENSORS),
            evidence_entry("status_txt", STATUS_TXT),
            evidence_entry("run_status", RUN_STATUS),
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("open_boundary_orifice_extended_2s_ready") is True, "2s screen not ready")
    require(summary.get("cuda_initialized") is True, "CUDA was not initialized")
    require(summary.get("run_returncode_zero") is True, "run return code was not zero")
    require(summary.get("run_finalized") is True, "run did not finalize")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "run log has bad markers")
    require(int(summary.get("plotfile_count", 0)) >= 21, "plotfile count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "sensor count mismatch")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 600, "sensor rows too small")
    require(abs(float(summary.get("time_end_s", 0.0)) - 2.0) <= 1.0e-12, "time end is not 2s")
    require(0.75 <= float(summary.get("mass_ratio_final", 0.0)) <= 1.05, "open-boundary retained mass ratio out of expected range")
    require(float(summary.get("mass_growth_ratio", 0.0)) > 10.0, "mass growth too small")
    require(float(summary.get("max_yh2", 0.0)) > 0.015, "H2 plume too weak")
    require(float(summary.get("downstream_fraction", 0.0)) > 0.99, "downstream plume fraction too small")
    require(summary.get("plume_observation_status") == "PASS-H2-PLUME-OBSERVATION", "plume observation not PASS")
    require(summary.get("production_agreement_completed") is False, "2s screen must not claim production agreement")
    require(summary.get("clears_external_plume_reference_blocker") is False, "2s screen must not clear strict blocker")
    require(summary.get("strict_blocker_still_open") is True, "strict blocker boundary missing")
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
        "# DataverseNO Open-Channel Open-Boundary Orifice 2s MPI+CUDA Screen",
        "",
        f"- Status: `{report['status']}`",
        f"- Time end: `{s['time_end_s']}` s",
        f"- MPI ranks: `{s['mpi_rank_count']}`",
        f"- CUDA initialized: `{s['cuda_initialized']}`",
        f"- Plotfiles: `{s['plotfile_count']}`",
        f"- Sensor rows: `{s['sensor_timeseries_rows']}`",
        f"- Retained mass ratio: `{s['mass_ratio_final']}`",
        f"- Max Y(H2): `{s['max_yh2']}`",
        f"- Downstream fraction: `{s['downstream_fraction']}`",
        f"- Clears strict external plume blocker: `{s['clears_external_plume_reference_blocker']}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", "## Evidence", ""])
    lines.extend(f"- `{item['label']}`: `{item['path']}`" for item in report["evidence_files"])
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data)
            print(f"dataverse_open_channel_open_boundary_orifice_extended_2s VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        validate_report(report, verify_hashes=False)
        write_outputs(report, Path(args.output_json), Path(args.output_md))
        print(f"dataverse_open_channel_open_boundary_orifice_extended_2s {report['status']} json={args.output_json}")
        return 0
    except (OpenBoundary2sError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"dataverse_open_channel_open_boundary_orifice_extended_2s ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
