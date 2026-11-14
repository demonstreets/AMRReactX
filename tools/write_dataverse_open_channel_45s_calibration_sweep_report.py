#!/usr/bin/env python3
"""Write/verify a DataverseNO 45 s calibration sweep report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-SWEEP-NO-PROMOTION"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_sweep_20260804")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_45s_calibration_sweep_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_45s_calibration_sweep_report.md"

BASELINE = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_window_mpi_cuda_20260803/"
    "dataverse_open_channel_cfd_agreement_attempt_report.json"
)
CASES = {
    "r005_z08": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r005_z08_mpi_cuda_20260804/"
        "dataverse_open_channel_cfd_agreement_attempt_report.json"
    ),
    "r006_z08": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r006_z08_mpi_cuda_20260804/"
        "dataverse_open_channel_cfd_agreement_attempt_report.json"
    ),
    "r004_z0775": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r004_z0775_mpi_cuda_20260804/"
        "dataverse_open_channel_cfd_agreement_attempt_report.json"
    ),
}
INPUTS = {
    "r005_z08": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r005_z08_mpi_cuda_20260804/"
        "input.dataverse_open_channel_h2_scout_3d"
    ),
    "r006_z08": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r006_z08_mpi_cuda_20260804/"
        "input.dataverse_open_channel_h2_scout_3d"
    ),
    "r004_z0775": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r004_z0775_mpi_cuda_20260804/"
        "input.dataverse_open_channel_h2_scout_3d"
    ),
}
VALIDATIONS = {
    "r005_z08": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r005_z08_mpi_cuda_20260804/"
        "validation.log"
    ),
    "r006_z08": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r006_z08_mpi_cuda_20260804/"
        "validation.log"
    ),
    "r004_z0775": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_calibration_r004_z0775_mpi_cuda_20260804/"
        "validation.log"
    ),
}


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


def report_metrics(path: Path) -> dict[str, Any]:
    data = load_json(path)
    summary = data["summary"]
    return {
        "status": data["status"],
        "sensor_count": summary["sensor_count"],
        "common_sample_count_min": summary["common_sample_count_min"],
        "peak_pass_count": summary["peak_pass_count"],
        "nrmse_pass_count": summary["nrmse_pass_count"],
        "arrival_pass_count": summary["arrival_pass_count"],
        "combined_pass_count": (
            summary["peak_pass_count"]
            + summary["nrmse_pass_count"]
            + summary["arrival_pass_count"]
        ),
        "failed_sensor_count": summary["failed_sensor_count"],
        "simulation_time_end_s": summary["simulation_time_end_s"],
        "simulation_mass_ratio_final": summary["simulation_mass_ratio_final"],
        "production_agreement_completed": summary["production_agreement_completed"],
        "clears_external_plume_reference_blocker": summary["clears_external_plume_reference_blocker"],
    }


def case_entry(label: str, baseline: dict[str, Any]) -> dict[str, Any]:
    metrics = report_metrics(CASES[label])
    params = parse_input_deck(INPUTS[label])
    promote = (
        metrics["peak_pass_count"] >= baseline["peak_pass_count"]
        and metrics["nrmse_pass_count"] >= baseline["nrmse_pass_count"]
        and metrics["arrival_pass_count"] >= baseline["arrival_pass_count"]
        and metrics["combined_pass_count"] > baseline["combined_pass_count"]
    )
    return {
        "label": label,
        "input": {
            "prob.leak_radius": first_float(params, "prob.leak_radius"),
            "prob.leak_zc": first_float(params, "prob.leak_zc"),
            "prob.leak_rate": first_float(params, "prob.leak_rate"),
            "amr.max_step": int(first_float(params, "amr.max_step")),
            "amr.fixed_dt": first_float(params, "amr.fixed_dt"),
        },
        "metrics": metrics,
        "delta_vs_baseline": {
            "peak_pass_count": metrics["peak_pass_count"] - baseline["peak_pass_count"],
            "nrmse_pass_count": metrics["nrmse_pass_count"] - baseline["nrmse_pass_count"],
            "arrival_pass_count": metrics["arrival_pass_count"] - baseline["arrival_pass_count"],
            "combined_pass_count": metrics["combined_pass_count"] - baseline["combined_pass_count"],
        },
        "promote_to_120s_peak_window": promote,
    }


def build_report() -> dict[str, Any]:
    baseline = report_metrics(BASELINE)
    cases = [case_entry(label, baseline) for label in sorted(CASES)]
    promoted = [case for case in cases if case["promote_to_120s_peak_window"]]
    stable_cases = [
        case for case in cases
        if case["metrics"]["simulation_time_end_s"] >= 44.9
        and case["metrics"]["simulation_mass_ratio_final"] == 1.0
    ]
    best = max(cases, key=lambda case: case["metrics"]["combined_pass_count"])

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "summary": {
            "baseline_combined_pass_count": baseline["combined_pass_count"],
            "case_count": len(cases),
            "stable_case_count": len(stable_cases),
            "promoted_case_count": len(promoted),
            "best_case_label": best["label"],
            "best_case_combined_pass_count": best["metrics"]["combined_pass_count"],
            "best_case_peak_pass_count": best["metrics"]["peak_pass_count"],
            "best_case_nrmse_pass_count": best["metrics"]["nrmse_pass_count"],
            "best_case_arrival_pass_count": best["metrics"]["arrival_pass_count"],
            "strict_external_plume_blocker_cleared": False,
            "ready_for_next_calibration_screen": True,
        },
        "baseline": baseline,
        "cases": cases,
        "decision": {
            "promote_any_case_to_120s": bool(promoted),
            "reason": (
                "All coarse-grid source-height/radius screens are numerically stable, but none improves "
                "the combined 45 s agreement score without regressing NRMSE or LFL arrival."
            ),
            "next_screen_parameters": [
                {"amr.n_cell": "174 27 24", "prob.leak_zc": 0.80, "prob.leak_radius": 0.04},
                {"boundary_condition_focus": "outlet/backflow and open-channel ventilation parity"},
                {"geometry_focus": "encode DataverseNO internal component/obstacle bounds instead of all_regular"},
            ],
        },
        "evidence_files": [
            evidence_entry("baseline_45s_agreement_report", BASELINE),
            *[
                evidence_entry(f"{label}_agreement_report", path)
                for label, path in sorted(CASES.items())
            ],
            *[
                evidence_entry(f"{label}_input_deck", path)
                for label, path in sorted(INPUTS.items())
            ],
            *[
                evidence_entry(f"{label}_validation_log", path)
                for label, path in sorted(VALIDATIONS.items())
            ],
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("case_count") == 3, "unexpected case count")
    require(summary.get("stable_case_count") == 3, "not all calibration screens are stable")
    require(summary.get("promoted_case_count") == 0, "a case was unexpectedly promoted")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "sweep must not clear blocker")
    require(summary.get("ready_for_next_calibration_screen") is True, "next calibration screen not ready")
    require(data.get("decision", {}).get("promote_any_case_to_120s") is False, "promotion decision mismatch")
    for case in data.get("cases", []):
        require(case.get("promote_to_120s_peak_window") is False, f"case unexpectedly promoted: {case.get('label')}")
        require(case.get("metrics", {}).get("simulation_mass_ratio_final") == 1.0, f"case mass ratio mismatch: {case.get('label')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO 45s Calibration Sweep",
        "",
        f"- Status: `{report['status']}`",
        f"- Cases: `{s['stable_case_count']}/{s['case_count']}` stable",
        f"- Promoted cases: `{s['promoted_case_count']}`",
        f"- Best case: `{s['best_case_label']}` with combined pass count `{s['best_case_combined_pass_count']}`",
        "",
        "## Cases",
        "",
    ]
    for case in report["cases"]:
        m = case["metrics"]
        d = case["delta_vs_baseline"]
        lines.append(
            f"- `{case['label']}` radius=`{case['input']['prob.leak_radius']}` z=`{case['input']['prob.leak_zc']}` "
            f"passes=`{m['peak_pass_count']}/{m['nrmse_pass_count']}/{m['arrival_pass_count']}` "
            f"delta=`{d['peak_pass_count']}/{d['nrmse_pass_count']}/{d['arrival_pass_count']}` "
            f"promote=`{case['promote_to_120s_peak_window']}`"
        )
    lines.extend(["", "## Decision", "", f"- {report['decision']['reason']}", ""])
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
        print(f"dataverse_open_channel_45s_calibration_sweep VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"dataverse_open_channel_45s_calibration_sweep PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
