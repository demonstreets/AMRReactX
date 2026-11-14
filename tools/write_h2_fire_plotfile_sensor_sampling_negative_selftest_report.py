#!/usr/bin/env python3
"""Write/verify negative selftests for the H2 fire plotfile sensor extractor."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-NEGATIVE-SELFTEST"
ROOT = Path("docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807")
DEFAULT_JSON = ROOT / "h2_fire_plotfile_sensor_sampling_negative_selftest_report.json"
DEFAULT_MD = ROOT / "h2_fire_plotfile_sensor_sampling_negative_selftest_report.md"
EXTRACTOR = Path("tools/codex_extract_plotfile_sensor_timeseries.py")
PLOTFILE = Path("examples/engineering/h2_leak_3d/plt00001")


class NegativeSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NegativeSelftestError(message)


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
        raise NegativeSelftestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NegativeSelftestError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def run_cmd(label: str, cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = ROOT / f"{label}.log"
    log.write_text(proc.stdout, encoding="utf-8")
    return {"label": label, "returncode": proc.returncode, "log": str(log), "stdout_tail": proc.stdout[-1200:]}


def extractor_cmd(sensor_csv: Path, output_stem: str, extra: list[str] | None = None) -> list[str]:
    cmd = [
        "python3",
        str(EXTRACTOR),
        "--sensor-csv",
        str(sensor_csv),
        "--plotfile",
        str(PLOTFILE),
        "--variables",
        "avg_pressure",
        "temp",
        "--sampling-mode",
        "linear",
        "--output-csv",
        str(ROOT / f"{output_stem}.csv"),
        "--output-json",
        str(ROOT / f"{output_stem}.json"),
    ]
    if extra:
        cmd.extend(extra)
    return cmd


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    require(EXTRACTOR.is_file(), f"missing extractor: {EXTRACTOR}")
    require((PLOTFILE / "Header").is_file(), f"missing plotfile Header: {PLOTFILE}")
    ROOT.mkdir(parents=True, exist_ok=True)

    positive_csv = ROOT / "positive_linear_sensors.csv"
    write_csv(
        positive_csv,
        ["sensor_id", "x_m", "y_m", "z_m"],
        [["P01", 0.25, 0.25, 0.25], ["P02", 0.5, 0.3125, 0.3125]],
    )
    positive = run_cmd("positive_linear", extractor_cmd(positive_csv, "positive_linear"))
    require(positive["returncode"] == 0, "positive linear extractor selftest failed")

    cases: list[dict[str, Any]] = []
    fixtures = [
        ("duplicate_sensor_id", ["sensor_id", "x_m", "y_m", "z_m"], [["P01", 0.25, 0.25, 0.25], ["P01", 0.5, 0.25, 0.25]]),
        ("missing_x_column", ["sensor_id", "y_m", "z_m"], [["P01", 0.25, 0.25]]),
        ("nan_coordinate", ["sensor_id", "x_m", "y_m", "z_m"], [["P01", "nan", 0.25, 0.25]]),
        ("outside_domain_x", ["sensor_id", "x_m", "y_m", "z_m"], [["P01", 1.50, 0.25, 0.25]]),
        ("empty_sensor_csv", ["sensor_id", "x_m", "y_m", "z_m"], []),
    ]
    for label, header, rows in fixtures:
        sensor_csv = ROOT / f"{label}.csv"
        write_csv(sensor_csv, header, rows)
        result = run_cmd(label, extractor_cmd(sensor_csv, label))
        cases.append({**result, "expected_failure": True, "passed": result["returncode"] != 0})

    missing_variable = run_cmd(
        "missing_variable",
        [
            "python3",
            str(EXTRACTOR),
            "--sensor-csv",
            str(positive_csv),
            "--plotfile",
            str(PLOTFILE),
            "--variables",
            "not_a_plotfile_variable",
            "--sampling-mode",
            "linear",
            "--output-csv",
            str(ROOT / "missing_variable.csv"),
            "--output-json",
            str(ROOT / "missing_variable.json"),
        ],
    )
    cases.append({**missing_variable, "expected_failure": True, "passed": missing_variable["returncode"] != 0})

    invalid_mode = run_cmd(
        "invalid_sampling_mode",
        [
            "python3",
            str(EXTRACTOR),
            "--sensor-csv",
            str(positive_csv),
            "--plotfile",
            str(PLOTFILE),
            "--variables",
            "avg_pressure",
            "--sampling-mode",
            "spline",
            "--output-csv",
            str(ROOT / "invalid_sampling_mode.csv"),
            "--output-json",
            str(ROOT / "invalid_sampling_mode.json"),
        ],
    )
    cases.append({**invalid_mode, "expected_failure": True, "passed": invalid_mode["returncode"] != 0})

    no_plotfile = run_cmd(
        "no_plotfile",
        [
            "python3",
            str(EXTRACTOR),
            "--sensor-csv",
            str(positive_csv),
            "--variables",
            "avg_pressure",
            "--sampling-mode",
            "linear",
            "--output-csv",
            str(ROOT / "no_plotfile.csv"),
            "--output-json",
            str(ROOT / "no_plotfile.json"),
        ],
    )
    cases.append({**no_plotfile, "expected_failure": True, "passed": no_plotfile["returncode"] != 0})

    refused = sum(1 for case in cases if case["passed"])
    ready = positive["returncode"] == 0 and refused == len(cases)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-NEGATIVE-SELFTEST",
        "summary": {
            "negative_selftest_ready": ready,
            "positive_linear_extractor_case_passed": positive["returncode"] == 0,
            "negative_case_count": len(cases),
            "negative_refused_count": refused,
            "failed_negative_count": len(cases) - refused,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "positive_case": positive,
        "negative_cases": cases,
        "claim_boundary": [
            "This selftest verifies extractor input refusal behavior.",
            "It does not create experimental sensor coordinates.",
            "It does not clear calibrated overpressure or radiation agreement.",
        ],
        "evidence_files": [
            evidence_entry("plotfile_sensor_extractor", EXTRACTOR),
            evidence_entry("positive_linear_sensors", positive_csv),
            evidence_entry("positive_linear_log", ROOT / "positive_linear.log"),
            evidence_entry("positive_linear_json", ROOT / "positive_linear.json"),
            *[evidence_entry(f"{case['label']}_log", Path(case["log"])) for case in cases],
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("negative_selftest_ready") is True, "negative selftest not ready")
    require(summary.get("positive_linear_extractor_case_passed") is True, "positive linear extractor case missing")
    require(summary.get("negative_case_count") == 8, "negative case count changed")
    require(summary.get("negative_refused_count") == 8, "not all negative cases were refused")
    require(summary.get("failed_negative_count") == 0, "one or more negative cases unexpectedly passed")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    for case in data.get("negative_cases", []):
        require(case.get("passed") is True, f"negative case did not fail as expected: {case.get('label')}")
        require(int(case.get("returncode", 0)) != 0, f"negative case return code not failing: {case.get('label')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire Plotfile Sensor Sampling Negative Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Positive linear case passed: `{s['positive_linear_extractor_case_passed']}`",
        f"- Negative cases refused: `{s['negative_refused_count']}/{s['negative_case_count']}`",
        f"- Strict fire calibration blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Negative Cases",
        "",
    ]
    lines.extend(
        f"- `{case['label']}`: returncode=`{case['returncode']}`, passed=`{case['passed']}`"
        for case in report["negative_cases"]
    )
    lines += ["", "## Evidence", ""]
    lines.extend(f"- `{entry['label']}`: `{entry['path']}`" for entry in report["evidence_files"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    ap.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    ap.add_argument("--verify-json", type=Path)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(args.verify_json)
            validate_report(data)
            print(f"h2_fire_plotfile_sensor_sampling_negative_selftest VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report(args)
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, args.output_md)
        print(f"h2_fire_plotfile_sensor_sampling_negative_selftest PASS json={args.output_json} md={args.output_md} status={report['status']}")
        return 0
    except (NegativeSelftestError, OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
        print(f"h2_fire_plotfile_sensor_sampling_negative_selftest FAIL: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
