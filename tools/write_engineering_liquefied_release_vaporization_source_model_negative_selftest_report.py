#!/usr/bin/env python3
"""Write/verify negative selftests for the liquefied-release source generator."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST"
DEFAULT_ROOT = Path(
    "docs/codex_audit/evidence/"
    "engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807"
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_release_vaporization_source_model_negative_selftest_report.md"

GENERATOR = Path("tools/codex_make_liquefied_release_vaporization_csv.py")
SOURCE_MODEL_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
    "engineering_liquefied_release_vaporization_source_model_report.json"
)

BASE_ARGS = [
    "--fluid",
    "LNG_CH4",
    "--inventory-kg",
    "25.0",
    "--initial-pressure-Pa",
    "650000.0",
    "--ambient-pressure-Pa",
    "101325.0",
    "--hole-diameter-m",
    "0.020",
    "--duration-s",
    "8.0",
    "--points",
    "9",
    "--liquid-T-K",
    "125.0",
    "--vapor-T-K",
    "285.0",
    "--source-radius-m",
    "0.08",
]

NEGATIVE_CASES: dict[str, tuple[list[str], str]] = {
    "negative_inventory": (["--inventory-kg", "-1.0"], "inventory_kg must be positive and finite"),
    "initial_pressure_below_ambient": (["--initial-pressure-Pa", "90000.0"], "initial pressure must be at least ambient pressure"),
    "zero_hole_diameter": (["--hole-diameter-m", "0.0"], "hole_diameter_m must be positive and finite"),
    "too_many_points": (["--points", "65"], "points must be in [2, 64]"),
    "high_discharge_coeff": (["--discharge-coeff", "1.1"], "discharge_coeff must be <= 1"),
    "zero_jet_direction": (["--jet-dir-x", "0.0", "--jet-dir-y", "0.0", "--jet-dir-z", "0.0"], "jet direction vector must be nonzero"),
    "negative_max_jet_speed": (["--max-jet-speed-m-s", "-1.0"], "max_jet_speed_m_s must be positive and finite"),
    "negative_pool_vapor_fraction": (["--pool-vapor-fraction", "-0.1"], "pool_vapor_fraction must be nonnegative and finite"),
    "high_pool_vapor_fraction": (["--pool-vapor-fraction", "1.2"], "pool_vapor_fraction must be <= 0.95"),
    "negative_vaporized_fraction": (["--vaporized-fraction", "-0.1"], "vaporized_fraction must be nonnegative and finite"),
    "high_vaporized_fraction": (["--vaporized-fraction", "1.2"], "vaporized_fraction must be <= 0.95"),
    "negative_source_radius": (["--source-radius-m", "-0.1"], "source_radius_m must be positive and finite"),
    "negative_liquid_temperature": (["--liquid-T-K", "-10.0"], "liquid_T_K must be positive and finite"),
}


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


def replace_arg(args: list[str], replacement: list[str]) -> list[str]:
    out = list(args)
    key = replacement[0]
    try:
        idx = out.index(key)
    except ValueError:
        return out + replacement
    end = idx + 1
    while end < len(out) and not out[end].startswith("--"):
        end += 1
    return out[:idx] + replacement + out[end:]


def run_generator(arg_list: list[str], output_root: Path, stem: str) -> subprocess.CompletedProcess[str]:
    output_csv = output_root / f"{stem}.csv"
    output_json = output_root / f"{stem}.json"
    cmd = [
        sys.executable,
        str(GENERATOR),
        *arg_list,
        "--output-csv",
        str(output_csv),
        "--output-json",
        str(output_json),
    ]
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_json).parent
    output_root.mkdir(parents=True, exist_ok=True)
    require(GENERATOR.is_file(), f"missing generator: {GENERATOR}")
    source_model = load_json(SOURCE_MODEL_REPORT)
    require(
        source_model.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL",
        "positive source-model report is not passing",
    )

    positive_root = output_root / "positive"
    positive = run_generator(BASE_ARGS, positive_root, "lng_ch4_positive")
    positive_json = positive_root / "lng_ch4_positive.json"
    positive_report = load_json(positive_json) if positive_json.is_file() else {}
    positive_ready = (
        positive.returncode == 0
        and positive_report.get("status") == "PASS-LIQUEFIED-RELEASE-VAPORIZATION-CSV"
        and positive_report.get("summary", {}).get("gas_mdot_positive") is True
    )
    require(positive_ready, f"positive generator case failed rc={positive.returncode}: {positive.stderr.strip()}")

    case_results: list[dict[str, Any]] = []
    negative_root = output_root / "negative"
    for name, (replacement, expected) in NEGATIVE_CASES.items():
        result = run_generator(replace_arg(BASE_ARGS, replacement), negative_root, name)
        combined = f"{result.stdout}\n{result.stderr}"
        refused = result.returncode != 0 and expected in combined
        case_results.append(
            {
                "name": name,
                "returncode": result.returncode,
                "expected_message": expected,
                "refused": refused,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )

    refused_count = sum(1 for case in case_results if case["refused"])
    failed_cases = [case["name"] for case in case_results if not case["refused"]]
    ready = positive_ready and refused_count == len(NEGATIVE_CASES)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST",
        "summary": {
            "negative_selftest_ready": ready,
            "positive_generator_case_passed": positive_ready,
            "negative_case_count": len(NEGATIVE_CASES),
            "negative_refused_count": refused_count,
            "failed_negative_count": len(failed_cases),
            "failed_negative_cases": failed_cases,
            "guards_inventory": next(case["refused"] for case in case_results if case["name"] == "negative_inventory"),
            "guards_pressure": next(case["refused"] for case in case_results if case["name"] == "initial_pressure_below_ambient"),
            "guards_orifice": next(case["refused"] for case in case_results if case["name"] == "zero_hole_diameter"),
            "guards_schedule_count": next(case["refused"] for case in case_results if case["name"] == "too_many_points"),
            "guards_discharge_coeff": next(case["refused"] for case in case_results if case["name"] == "high_discharge_coeff"),
            "guards_jet_direction": next(case["refused"] for case in case_results if case["name"] == "zero_jet_direction"),
            "guards_max_jet_speed": next(case["refused"] for case in case_results if case["name"] == "negative_max_jet_speed"),
            "guards_pool_fraction": all(
                next(case["refused"] for case in case_results if case["name"] == name)
                for name in ("negative_pool_vapor_fraction", "high_pool_vapor_fraction")
            ),
            "guards_vaporized_fraction": all(
                next(case["refused"] for case in case_results if case["name"] == name)
                for name in ("negative_vaporized_fraction", "high_vaporized_fraction")
            ),
            "guards_source_radius": next(case["refused"] for case in case_results if case["name"] == "negative_source_radius"),
            "guards_liquid_temperature": next(case["refused"] for case in case_results if case["name"] == "negative_liquid_temperature"),
        },
        "positive_case": {
            "returncode": positive.returncode,
            "stdout": positive.stdout.strip(),
            "stderr": positive.stderr.strip(),
            "report_json": str(positive_json),
        },
        "negative_cases": case_results,
        "evidence_files": [
            evidence_entry("generator", GENERATOR),
            evidence_entry("positive_source_model_report", SOURCE_MODEL_REPORT),
            evidence_entry("positive_generator_report", positive_json),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("negative_selftest_ready") is True, "negative selftest is not ready")
    require(summary.get("positive_generator_case_passed") is True, "positive generator case did not pass")
    require(summary.get("negative_case_count") == len(NEGATIVE_CASES), "negative case count changed")
    require(summary.get("negative_refused_count") == len(NEGATIVE_CASES), "not all negative cases were refused")
    require(summary.get("failed_negative_count") == 0, "some negative cases were accepted")
    for key in (
        "guards_inventory",
        "guards_pressure",
        "guards_orifice",
        "guards_schedule_count",
        "guards_discharge_coeff",
        "guards_jet_direction",
        "guards_max_jet_speed",
        "guards_pool_fraction",
        "guards_vaporized_fraction",
        "guards_source_radius",
        "guards_liquid_temperature",
    ):
        require(summary.get(key) is True, f"{key} did not pass")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Liquefied Release Vaporization Source Model Negative Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Positive generator case passed: `{s['positive_generator_case_passed']}`",
        f"- Negative cases refused: `{s['negative_refused_count']}` / `{s['negative_case_count']}`",
        f"- Failed negative cases: `{s['failed_negative_cases']}`",
        "",
        "## Guarded Inputs",
        "",
    ]
    for key in (
        "guards_inventory",
        "guards_pressure",
        "guards_orifice",
        "guards_schedule_count",
        "guards_discharge_coeff",
        "guards_jet_direction",
        "guards_max_jet_speed",
        "guards_pool_fraction",
        "guards_vaporized_fraction",
        "guards_source_radius",
        "guards_liquid_temperature",
    ):
        lines.append(f"- `{key}`: `{s[key]}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(
                "engineering_liquefied_release_vaporization_source_model_negative_selftest "
                f"VERIFY-PASS json={args.verify_json} status={data.get('status')}"
            )
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(
            "engineering_liquefied_release_vaporization_source_model_negative_selftest "
            f"PASS json={output_json} md={output_md} status={report['status']}"
        )
        return 0
    except NegativeSelftestError as exc:
        print(f"engineering_liquefied_release_vaporization_source_model_negative_selftest FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
