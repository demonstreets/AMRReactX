#!/usr/bin/env python3
"""Write/verify the DataverseNO 45 s r=0.05, z=0.80 calibration screen report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-R005-Z08-NOT-PROMOTED"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_r005_z08_screen_20260804")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_45s_calibration_r005_z08_screen_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_45s_calibration_r005_z08_screen_report.md"

BASELINE = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_window_mpi_cuda_20260803/"
    "dataverse_open_channel_cfd_agreement_attempt_report.json"
)
CANDIDATE_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r005_z08_mpi_cuda_20260804")
CANDIDATE = CANDIDATE_ROOT / "dataverse_open_channel_cfd_agreement_attempt_report.json"
VALIDATION_LOG = CANDIDATE_ROOT / "validation.log"
INPUT_DECK = CANDIDATE_ROOT / "input.dataverse_open_channel_h2_scout_3d"


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    require(isinstance(data, dict), f"expected JSON object: {path}")
    return data


def metric_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["summary"]
    return {
        "status": report["status"],
        "sensor_count": summary["sensor_count"],
        "common_sample_count_min": summary["common_sample_count_min"],
        "peak_pass_count": summary["peak_pass_count"],
        "nrmse_pass_count": summary["nrmse_pass_count"],
        "arrival_pass_count": summary["arrival_pass_count"],
        "failed_sensor_count": summary["failed_sensor_count"],
        "simulation_time_end_s": summary["simulation_time_end_s"],
        "simulation_mass_ratio_final": summary["simulation_mass_ratio_final"],
        "production_agreement_completed": summary["production_agreement_completed"],
        "clears_external_plume_reference_blocker": summary["clears_external_plume_reference_blocker"],
    }


def parse_input_deck(path: Path) -> dict[str, str]:
    params: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        params[key.strip()] = value.strip()
    return params


def first_float(params: dict[str, str], key: str) -> float:
    require(key in params, f"missing parameter {key}")
    return float(params[key].split()[0])


def build_report() -> dict[str, Any]:
    baseline_report = load_json(BASELINE)
    candidate_report = load_json(CANDIDATE)
    baseline = metric_summary(baseline_report)
    candidate = metric_summary(candidate_report)
    params = parse_input_deck(INPUT_DECK)

    require(candidate["status"] == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING", "candidate status mismatch")
    require(candidate["simulation_time_end_s"] >= 44.9, "candidate did not reach 45 s")
    require(candidate["simulation_mass_ratio_final"] == 1.0, "candidate mass ratio mismatch")
    require(candidate["production_agreement_completed"] is False, "candidate unexpectedly completed production agreement")

    baseline_score = baseline["peak_pass_count"] + baseline["nrmse_pass_count"] + baseline["arrival_pass_count"]
    candidate_score = candidate["peak_pass_count"] + candidate["nrmse_pass_count"] + candidate["arrival_pass_count"]
    not_promoted = candidate_score < baseline_score or candidate["arrival_pass_count"] < baseline["arrival_pass_count"]

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "summary": {
            "candidate_stable": True,
            "candidate_reached_45s": True,
            "candidate_mass_ratio_final": candidate["simulation_mass_ratio_final"],
            "candidate_peak_pass_count": candidate["peak_pass_count"],
            "candidate_nrmse_pass_count": candidate["nrmse_pass_count"],
            "candidate_arrival_pass_count": candidate["arrival_pass_count"],
            "baseline_peak_pass_count": baseline["peak_pass_count"],
            "baseline_nrmse_pass_count": baseline["nrmse_pass_count"],
            "baseline_arrival_pass_count": baseline["arrival_pass_count"],
            "candidate_combined_pass_count": candidate_score,
            "baseline_combined_pass_count": baseline_score,
            "candidate_improved_peak_count": candidate["peak_pass_count"] > baseline["peak_pass_count"],
            "candidate_regressed_nrmse_count": candidate["nrmse_pass_count"] < baseline["nrmse_pass_count"],
            "candidate_regressed_arrival_count": candidate["arrival_pass_count"] < baseline["arrival_pass_count"],
            "promote_to_120s_peak_window": False,
            "strict_external_plume_blocker_cleared": False,
            "ready_for_next_calibration_screen": True,
        },
        "candidate_input": {
            "prob.leak_radius": first_float(params, "prob.leak_radius"),
            "prob.leak_zc": first_float(params, "prob.leak_zc"),
            "prob.leak_rate": first_float(params, "prob.leak_rate"),
            "amr.fixed_dt": first_float(params, "amr.fixed_dt"),
            "amr.max_step": int(first_float(params, "amr.max_step")),
            "amr.plot_int": int(first_float(params, "amr.plot_int")),
        },
        "baseline": baseline,
        "candidate": candidate,
        "decision": {
            "not_promoted": not_promoted,
            "reason": (
                "The candidate is numerically stable and improves peak pass count by one sensor, "
                "but it regresses NRMSE and LFL-arrival pass counts relative to the 45 s baseline."
            ),
            "next_screen_parameters": [
                {"prob.leak_zc": 0.80, "prob.leak_radius": 0.06},
                {"prob.leak_zc": 0.775, "prob.leak_radius": 0.04},
                {"amr.n_cell": "174 27 24", "prob.leak_zc": 0.80, "prob.leak_radius": 0.04},
            ],
        },
        "evidence_files": [
            evidence_entry("baseline_45s_agreement_report", BASELINE),
            evidence_entry("candidate_45s_agreement_report", CANDIDATE),
            evidence_entry("candidate_validation_log", VALIDATION_LOG),
            evidence_entry("candidate_input_deck", INPUT_DECK),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("candidate_stable") is True, "candidate stability evidence missing")
    require(summary.get("candidate_reached_45s") is True, "candidate 45 s evidence missing")
    require(summary.get("candidate_mass_ratio_final") == 1.0, "candidate mass ratio mismatch")
    require(summary.get("candidate_peak_pass_count") == 2, "candidate peak count changed")
    require(summary.get("candidate_nrmse_pass_count") == 23, "candidate NRMSE count changed")
    require(summary.get("candidate_arrival_pass_count") == 2, "candidate arrival count changed")
    require(summary.get("baseline_nrmse_pass_count") == 26, "baseline NRMSE count changed")
    require(summary.get("baseline_arrival_pass_count") == 5, "baseline arrival count changed")
    require(summary.get("promote_to_120s_peak_window") is False, "candidate should not be promoted")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "screen must not clear strict blocker")
    require(data.get("decision", {}).get("not_promoted") is True, "not-promoted decision missing")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO 45s Calibration R005 Z08 Screen",
        "",
        f"- Status: `{report['status']}`",
        f"- Candidate stable: `{s['candidate_stable']}`",
        f"- Candidate peak/NRMSE/arrival pass counts: `{s['candidate_peak_pass_count']}` / `{s['candidate_nrmse_pass_count']}` / `{s['candidate_arrival_pass_count']}`",
        f"- Baseline peak/NRMSE/arrival pass counts: `{s['baseline_peak_pass_count']}` / `{s['baseline_nrmse_pass_count']}` / `{s['baseline_arrival_pass_count']}`",
        f"- Promote to 120s peak window: `{s['promote_to_120s_peak_window']}`",
        "",
        "## Decision",
        "",
        f"- {report['decision']['reason']}",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"dataverse_open_channel_45s_calibration_r005_z08_screen VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"dataverse_open_channel_45s_calibration_r005_z08_screen PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
