#!/usr/bin/env python3
"""Self-test strict artifact drop contract validators with synthetic temp files."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST"
STATUS_NOT_READY = "NOT_READY-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_artifact_drop_contract_selftest_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_artifact_drop_contract_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_artifact_drop_contract_selftest_report.md"

VALIDATOR_SCRIPT = Path("tools/write_strict_artifact_drop_contract_preflight_report.py")
VALIDATOR_REPORT = Path(
    "docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/"
    "strict_artifact_drop_contract_preflight_report.json"
)


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


def load_validator_module() -> Any:
    require(VALIDATOR_SCRIPT.is_file(), f"missing validator script: {VALIDATOR_SCRIPT}")
    spec = importlib.util.spec_from_file_location("drop_contract_validator", VALIDATOR_SCRIPT)
    require(spec is not None and spec.loader is not None, "unable to load validator module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_report() -> dict[str, Any]:
    validator_report = load_json(VALIDATOR_REPORT)
    require(
        validator_report.get("status") == "PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT",
        "drop contract preflight report is not ready",
    )
    validator = load_validator_module()

    tests: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="strict_drop_contract_selftest_") as tmpdir:
        tmp = Path(tmpdir)

        valid_json = tmp / "valid.json"
        valid_json.write_text(
            json.dumps(
                {
                    "benchmark_id": "synthetic_selftest",
                    "case_alignment": {},
                    "digitization": {},
                    "digitized_dataset_sha256": "0" * 64,
                    "original_dataset_sha256": "1" * 64,
                    "schema_version": 1,
                    "source": {},
                }
            ),
            encoding="utf-8",
        )
        result = validator.validate_json_artifact(
            "selftest.valid_json",
            "external_plume",
            valid_json,
            {"benchmark_id", "case_alignment", "digitization", "digitized_dataset_sha256", "original_dataset_sha256", "schema_version", "source"},
        )
        tests.append({"name": "valid_json_accepts_required_keys", "expected_ready": True, "observed_ready": result["ready"], "passed": result["ready"] is True, "result": result})

        missing_key_json = tmp / "missing_key.json"
        missing_key_json.write_text('{"schema_version": 1, "benchmark_id": "synthetic_selftest"}', encoding="utf-8")
        result = validator.validate_json_artifact(
            "selftest.missing_key_json",
            "external_plume",
            missing_key_json,
            {"benchmark_id", "case_alignment", "digitization", "digitized_dataset_sha256", "original_dataset_sha256", "schema_version", "source"},
        )
        tests.append({"name": "missing_json_keys_rejected", "expected_ready": False, "observed_ready": result["ready"], "passed": result["ready"] is False, "result": result})

        malformed_json = tmp / "malformed.json"
        malformed_json.write_text('{"schema_version": 1, ', encoding="utf-8")
        result = validator.validate_json_artifact(
            "selftest.malformed_json",
            "external_plume",
            malformed_json,
            {"schema_version"},
        )
        tests.append({"name": "malformed_json_rejected", "expected_ready": False, "observed_ready": result["ready"], "passed": result["ready"] is False, "result": result})

        valid_csv = tmp / "valid.csv"
        header = ["metric_id", "distance_m", "reference_flux_w_m2", "tolerance_abs_w_m2", "tolerance_rel", "source_basis"]
        valid_csv.write_text(",".join(header) + "\nrad01,1.0,1000.0,10.0,0.05,synthetic_selftest\n", encoding="utf-8")
        result = validator.validate_csv_artifact(
            "selftest.valid_csv",
            "fire_calibration",
            valid_csv,
            header,
            True,
        )
        tests.append({"name": "valid_required_csv_accepts_header_and_data", "expected_ready": True, "observed_ready": result["ready"], "passed": result["ready"] is True, "result": result})

        wrong_header_csv = tmp / "wrong_header.csv"
        wrong_header_csv.write_text("metric_id,distance_m,bad_column\nrad01,1.0,1000.0\n", encoding="utf-8")
        result = validator.validate_csv_artifact(
            "selftest.wrong_header_csv",
            "fire_calibration",
            wrong_header_csv,
            header,
            True,
        )
        tests.append({"name": "wrong_csv_header_rejected", "expected_ready": False, "observed_ready": result["ready"], "passed": result["ready"] is False, "result": result})

        header_only_csv = tmp / "header_only.csv"
        header_only_csv.write_text(",".join(header) + "\n", encoding="utf-8")
        result = validator.validate_csv_artifact(
            "selftest.header_only_required_csv",
            "fire_calibration",
            header_only_csv,
            header,
            True,
        )
        tests.append({"name": "required_csv_without_data_rows_rejected", "expected_ready": False, "observed_ready": result["ready"], "passed": result["ready"] is False, "result": result})

        duplicate_column_csv = tmp / "duplicate_columns.csv"
        duplicate_column_csv.write_text("metric_id,metric_id,source_basis\nrad01,rad01,synthetic_selftest\n", encoding="utf-8")
        result = validator.validate_csv_artifact(
            "selftest.duplicate_column_csv",
            "fire_calibration",
            duplicate_column_csv,
            header,
            True,
        )
        tests.append({"name": "duplicate_csv_columns_rejected", "expected_ready": False, "observed_ready": result["ready"], "passed": result["ready"] is False, "result": result})

        absent_optional = tmp / "optional_absent.csv"
        result = validator.validate_csv_artifact(
            "selftest.optional_absent_csv",
            "external_plume",
            absent_optional,
            ["artifact", "source_basis", "method", "axis_or_geometry_calibration", "estimated_uncertainty", "review_status"],
            False,
        )
        tests.append({"name": "absent_optional_csv_is_awaiting_not_invalid", "expected_ready": True, "observed_ready": result["ready"], "passed": result["ready"] is True and result["present"] is False, "result": result})

    passed_count = sum(1 for test in tests if test["passed"])
    ready = passed_count == len(tests)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "strict_artifact_drop_contract_selftest_ready": ready,
            "validator_report_status": validator_report.get("status"),
            "selftest_count": len(tests),
            "passed_selftest_count": passed_count,
            "failed_selftest_count": len(tests) - passed_count,
        },
        "tests": tests,
        "evidence_files": [
            evidence_entry("drop_contract_validator_script", VALIDATOR_SCRIPT),
            evidence_entry("drop_contract_preflight_report", VALIDATOR_REPORT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_artifact_drop_contract_selftest_ready") is True, "drop contract selftest is not ready")
    require(summary.get("validator_report_status") == "PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT", "validator report not ready")
    require(summary.get("selftest_count") == 8, "unexpected selftest count")
    require(summary.get("passed_selftest_count") == 8, "not all selftests passed")
    require(summary.get("failed_selftest_count") == 0, "selftest failures present")
    for test in data.get("tests", []):
        require(isinstance(test, dict), "invalid test entry")
        require(test.get("passed") is True, f"selftest failed: {test.get('name')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Artifact Drop Contract Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Selftests: `{summary['passed_selftest_count']}/{summary['selftest_count']}`",
        f"- Failed selftests: `{summary['failed_selftest_count']}`",
        "",
        "## Tests",
        "",
    ]
    for test in report["tests"]:
        lines.append(f"- `{test['name']}` expected_ready=`{test['expected_ready']}` observed_ready=`{test['observed_ready']}` passed=`{test['passed']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_artifact_drop_contract_selftest VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_artifact_drop_contract_selftest PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
