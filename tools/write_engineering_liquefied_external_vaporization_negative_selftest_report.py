#!/usr/bin/env python3
"""Write/verify negative selftests for external vaporization source input mapping."""
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
STATUS = "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-NEGATIVE-SELFTEST"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_external_vaporization_negative_selftest_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_external_vaporization_negative_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_external_vaporization_negative_selftest_report.md"

CONVERTER = Path("tools/codex_make_external_vaporization_source_input.py")
BASE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke")
VALID_TEMPLATE = Path("examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv")
CONTRACT_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/"
    "engineering_liquefied_external_vaporization_contract_report.json"
)


NEGATIVE_CASES = {
    "negative_mdot": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species\n0.0,-1.0e-3,300.0,CH4\n",
        "expected": "mdot_kg_s must be nonnegative",
    },
    "negative_vapor_temperature": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species\n0.0,1.0e-3,-10.0,CH4\n",
        "expected": "vapor_T_K must be positive",
    },
    "unknown_species": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species\n0.0,1.0e-3,300.0,CODEX_NOT_A_SPECIES\n",
        "expected": "fuel_species must be one of",
    },
    "nonmonotonic_time": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species\n0.0,1.0e-3,300.0,CH4\n0.0,2.0e-3,300.0,CH4\n",
        "expected": "time_s values must be strictly increasing",
    },
    "missing_temperature_column": {
        "csv": "time_s,mdot_kg_s,fuel_species\n0.0,1.0e-3,CH4\n",
        "expected": "source CSV missing columns",
    },
    "mixed_species": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species\n0.0,1.0e-3,300.0,CH4\n1.0,2.0e-3,300.0,C3H8\n",
        "expected": "exactly one fuel_species",
    },
    "negative_sample_time": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species\n0.0,1.0e-3,300.0,CH4\n1.0,2.0e-3,300.0,CH4\n",
        "expected": "sample time must be nonnegative",
        "sample_time": "-0.1",
    },
    "too_many_schedule_rows": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species\n"
        + "".join(f"{idx}.0,1.0e-3,300.0,CH4\n" for idx in range(65)),
        "expected": "source CSV supports at most 64 schedule rows",
    },
    "partial_optional_velocity_column": {
        "csv": (
            "time_s,mdot_kg_s,vapor_T_K,fuel_species,leak_vel_x_m_s\n"
            "0.0,1.0e-3,300.0,CH4,0.5\n"
            "1.0,2.0e-3,310.0,CH4,\n"
        ),
        "expected": "optional source CSV column leak_vel_x_m_s must be present on every row or omitted from every row",
    },
    "negative_source_radius": {
        "csv": "time_s,mdot_kg_s,vapor_T_K,fuel_species,source_radius_m\n0.0,1.0e-3,300.0,CH4,-0.1\n",
        "expected": "source_radius_m must be positive",
    },
    "partial_location_columns": {
        "csv": (
            "time_s,mdot_kg_s,vapor_T_K,fuel_species,source_x_m\n"
            "0.0,1.0e-3,300.0,CH4,0.5\n"
            "1.0,2.0e-3,310.0,CH4,0.6\n"
        ),
        "expected": "source_x_m, source_y_m, and source_z_m must be provided together or omitted together",
    },
}


class SelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelftestError(message)


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
        raise SelftestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SelftestError(f"invalid JSON evidence {path}: {exc}") from exc
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


def run_converter(source_csv: Path, output_root: Path, sample_time: str = "0.5") -> subprocess.CompletedProcess[str]:
    output_input = output_root / f"{source_csv.stem}.input"
    output_json = output_root / f"{source_csv.stem}.json"
    cmd = [
        sys.executable,
        str(CONVERTER),
        "--source-csv",
        str(source_csv),
        "--base-input",
        str(BASE_INPUT),
        "--time",
        sample_time,
        "--output-input",
        str(output_input),
        "--output-json",
        str(output_json),
    ]
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def converter_output_json(output_root: Path, source_csv: Path) -> Path:
    return output_root / f"{source_csv.stem}.json"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_json).parent
    output_root.mkdir(parents=True, exist_ok=True)
    contract = load_json(CONTRACT_REPORT)
    require(contract.get("status") == "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT", "external vaporization contract is not passing")
    require(CONVERTER.is_file(), f"missing converter: {CONVERTER}")
    require(BASE_INPUT.is_file(), f"missing base input: {BASE_INPUT}")
    require(VALID_TEMPLATE.is_file(), f"missing valid CSV template: {VALID_TEMPLATE}")

    positive_root = output_root / "positive"
    positive = run_converter(VALID_TEMPLATE, positive_root, "2.0")
    positive_json = converter_output_json(positive_root, VALID_TEMPLATE)
    positive_mapping = load_json(positive_json) if positive_json.is_file() else {}
    positive_ready = (
        positive.returncode == 0
        and positive_mapping.get("status") == "PASS-EXTERNAL-VAPORIZATION-SOURCE-INPUT"
    )
    require(positive_ready, f"positive template conversion failed rc={positive.returncode}: {positive.stderr.strip()}")

    case_results: list[dict[str, Any]] = []
    for name, spec in NEGATIVE_CASES.items():
        csv_path = output_root / f"{name}.csv"
        csv_path.write_text(spec["csv"], encoding="utf-8")
        result = run_converter(csv_path, output_root / "negative", str(spec.get("sample_time", "0.5")))
        combined = f"{result.stdout}\n{result.stderr}"
        refused = result.returncode != 0 and str(spec["expected"]) in combined
        case_results.append(
            {
                "name": name,
                "csv_path": str(csv_path),
                "returncode": result.returncode,
                "expected_message": spec["expected"],
                "refused": refused,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )

    negative_refused = [case for case in case_results if case["refused"]]
    failed_negative = [case for case in case_results if not case["refused"]]
    ready = positive_ready and len(negative_refused) == len(NEGATIVE_CASES)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-NEGATIVE-SELFTEST",
        "summary": {
            "negative_selftest_ready": ready,
            "positive_template_conversion_passed": positive_ready,
            "negative_case_count": len(NEGATIVE_CASES),
            "negative_refused_count": len(negative_refused),
            "failed_negative_count": len(failed_negative),
            "guards_negative_mdot": next(case["refused"] for case in case_results if case["name"] == "negative_mdot"),
            "guards_negative_vapor_temperature": next(case["refused"] for case in case_results if case["name"] == "negative_vapor_temperature"),
            "guards_unknown_species": next(case["refused"] for case in case_results if case["name"] == "unknown_species"),
            "guards_nonmonotonic_time": next(case["refused"] for case in case_results if case["name"] == "nonmonotonic_time"),
            "guards_missing_required_column": next(case["refused"] for case in case_results if case["name"] == "missing_temperature_column"),
            "guards_mixed_species": next(case["refused"] for case in case_results if case["name"] == "mixed_species"),
            "guards_negative_sample_time": next(case["refused"] for case in case_results if case["name"] == "negative_sample_time"),
            "guards_too_many_schedule_rows": next(case["refused"] for case in case_results if case["name"] == "too_many_schedule_rows"),
            "guards_partial_optional_velocity_column": next(case["refused"] for case in case_results if case["name"] == "partial_optional_velocity_column"),
            "guards_negative_source_radius": next(case["refused"] for case in case_results if case["name"] == "negative_source_radius"),
            "guards_partial_location_columns": next(case["refused"] for case in case_results if case["name"] == "partial_location_columns"),
        },
        "positive_case": {
            "source_csv": str(VALID_TEMPLATE),
            "mapping_json": str(positive_json),
            "returncode": positive.returncode,
            "status": positive_mapping.get("status"),
            "stdout": positive.stdout.strip(),
            "stderr": positive.stderr.strip(),
        },
        "negative_cases": case_results,
        "evidence_files": [
            evidence_entry("converter", CONVERTER),
            evidence_entry("base_input", BASE_INPUT),
            evidence_entry("valid_template", VALID_TEMPLATE),
            evidence_entry("positive_mapping_json", positive_json),
            evidence_entry("contract_report", CONTRACT_REPORT),
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("negative_selftest_ready") is True, "negative selftest is not ready")
    require(summary.get("positive_template_conversion_passed") is True, "positive template conversion did not pass")
    require(summary.get("negative_case_count") == len(NEGATIVE_CASES), "unexpected negative case count")
    require(summary.get("negative_refused_count") == len(NEGATIVE_CASES), "not all negative cases were refused")
    require(summary.get("failed_negative_count") == 0, "some negative cases were accepted")
    for key in (
        "guards_negative_mdot",
        "guards_negative_vapor_temperature",
        "guards_unknown_species",
        "guards_nonmonotonic_time",
        "guards_missing_required_column",
        "guards_mixed_species",
        "guards_negative_sample_time",
        "guards_too_many_schedule_rows",
        "guards_partial_optional_velocity_column",
        "guards_negative_source_radius",
        "guards_partial_location_columns",
    ):
        require(summary.get(key) is True, f"{key} did not pass")
    if verify_hashes:
        for item in data.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"evidence sha256 mismatch: {path}")


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = report["summary"]
    lines = [
        "# Engineering Liquefied External Vaporization Negative Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Positive template conversion passed: `{summary['positive_template_conversion_passed']}`",
        f"- Negative cases refused: `{summary['negative_refused_count']}/{summary['negative_case_count']}`",
        "",
        "## Negative Cases",
        "",
    ]
    for case in report["negative_cases"]:
        lines.append(
            f"- `{case['name']}`: refused=`{case['refused']}` rc=`{case['returncode']}` expected=`{case['expected_message']}`"
        )
    lines += ["", "## Evidence", ""]
    for item in report["evidence_files"]:
        lines.append(f"- `{item['label']}`: `{item['path']}`")
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
            print(f"engineering_liquefied_external_vaporization_negative_selftest VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        validate_report(report, verify_hashes=False)
        write_outputs(report, Path(args.output_json), Path(args.output_md))
        print(f"engineering_liquefied_external_vaporization_negative_selftest PASS json={args.output_json} status={report['status']}")
        return 0
    except (SelftestError, OSError, json.JSONDecodeError) as exc:
        print(f"engineering_liquefied_external_vaporization_negative_selftest FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
