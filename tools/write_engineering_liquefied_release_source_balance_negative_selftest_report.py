#!/usr/bin/env python3
"""Negative self-test for liquefied-release external-source balance auditing."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_release_source_balance_negative_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_release_source_balance_negative_selftest_report.md"
WORK_ROOT = DEFAULT_ROOT / "mutated_inputs"

BALANCE_TOOL = Path("tools/write_engineering_liquefied_release_source_balance_report.py")


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


def load_balance_module() -> Any:
    require(BALANCE_TOOL.is_file(), f"missing balance tool: {BALANCE_TOOL}")
    spec = importlib.util.spec_from_file_location("liquefied_release_source_balance", BALANCE_TOOL)
    require(spec is not None and spec.loader is not None, "unable to load balance tool module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def case_spec_from_paths(case_dir: Path, case_name: str, species: str) -> dict[str, Any]:
    if case_name == "lng_ch4_screening_release":
        prefix = "lng_ch4_screening_release"
        input_name = "input.lng_ch4_screening_release.generated"
    else:
        prefix = "lpg_c3h8_screening_release"
        input_name = "input.lpg_c3h8_screening_release.generated"
    return {
        "species": species,
        "csv": case_dir / f"{prefix}_source.csv",
        "model": case_dir / f"{prefix}_source_model.json",
        "mapping": case_dir / f"{prefix}_source_mapping.json",
        "input": case_dir / input_name,
    }


def copy_case(module: Any, case_name: str, dst_root: Path) -> dict[str, Any]:
    source = module.CASE_SPECS[case_name]
    case_dir = dst_root / case_name
    case_dir.mkdir(parents=True, exist_ok=True)
    copied = {}
    for key in ("csv", "model", "mapping", "input"):
        src = Path(source[key])
        dst = case_dir / src.name
        shutil.copy2(src, dst)
        copied[key] = dst
    mapping = load_json(copied["mapping"])
    mapping["source_csv"] = str(copied["csv"])
    mapping["output_input"] = str(copied["input"])
    for entry in mapping.get("evidence_files", []):
        if entry.get("label") == "source_csv":
            entry["path"] = str(copied["csv"])
            entry["sha256"] = sha256_file(copied["csv"])
        elif entry.get("label") == "output_input":
            entry["path"] = str(copied["input"])
            entry["sha256"] = sha256_file(copied["input"])
    write_json(copied["mapping"], mapping)
    return {
        "species": source["species"],
        "csv": copied["csv"],
        "model": copied["model"],
        "mapping": copied["mapping"],
        "input": copied["input"],
    }


def expect_failure(module: Any, case_name: str, spec: dict[str, Any], expected_fragment: str) -> dict[str, Any]:
    try:
        module.audit_case(case_name, spec)
    except Exception as exc:  # noqa: BLE001 - self-test records the rejection class/message.
        message = str(exc)
        return {
            "case": case_name,
            "rejected": True,
            "exception_type": type(exc).__name__,
            "message": message,
            "expected_fragment": expected_fragment,
            "expected_fragment_seen": expected_fragment in message,
        }
    return {
        "case": case_name,
        "rejected": False,
        "exception_type": None,
        "message": "mutated case unexpectedly passed",
        "expected_fragment": expected_fragment,
        "expected_fragment_seen": False,
    }


def mutate_negative_mdot(spec: dict[str, Any]) -> str:
    fieldnames, rows = read_csv_rows(Path(spec["csv"]))
    rows[1]["mdot_kg_s"] = "-0.01"
    write_csv_rows(Path(spec["csv"]), fieldnames, rows)
    return "negative mdot"


def mutate_species_drift(spec: dict[str, Any]) -> str:
    fieldnames, rows = read_csv_rows(Path(spec["csv"]))
    rows[0]["fuel_species"] = "H2"
    write_csv_rows(Path(spec["csv"]), fieldnames, rows)
    return "species drifted"


def mutate_schedule_rate(spec: dict[str, Any]) -> str:
    mapping = load_json(Path(spec["mapping"]))
    applied = mapping["applied_replacements"]
    values = applied["prob.leak_schedule_rates"].split()
    values[0] = str(float(values[0]) * 1.25)
    applied["prob.leak_schedule_rates"] = " ".join(values)
    write_json(Path(spec["mapping"]), mapping)
    return "schedule rates"


def mutate_overclaim_phase_change(spec: dict[str, Any]) -> str:
    model = load_json(Path(spec["model"]))
    model["summary"]["cfd_solves_liquid_phase_change"] = True
    write_json(Path(spec["model"]), model)
    return "overclaims liquid phase-change CFD"


def mutate_generated_input_species(spec: dict[str, Any]) -> str:
    input_path = Path(spec["input"])
    text = input_path.read_text(encoding="utf-8")
    text = text.replace(f"prob.fuel_species = {spec['species']}", "prob.fuel_species = H2")
    input_path.write_text(text, encoding="utf-8")
    return "generated input missing fuel species"


NEGATIVE_CASES: list[tuple[str, str, Callable[[dict[str, Any]], str]]] = [
    ("negative_mdot", "lng_ch4_screening_release", mutate_negative_mdot),
    ("species_drift", "lng_ch4_screening_release", mutate_species_drift),
    ("schedule_rate_mismatch", "lpg_c3h8_screening_release", mutate_schedule_rate),
    ("phase_change_overclaim", "lng_ch4_screening_release", mutate_overclaim_phase_change),
    ("generated_input_species_mismatch", "lpg_c3h8_screening_release", mutate_generated_input_species),
]


def build_report() -> dict[str, Any]:
    module = load_balance_module()
    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)

    positive_results: dict[str, Any] = {}
    evidence_files = [evidence_entry("balance_tool", BALANCE_TOOL)]
    positive_root = WORK_ROOT / "positive_control"
    for case_name in module.CASE_SPECS:
        spec = copy_case(module, case_name, positive_root)
        result, evidence = module.audit_case(case_name, spec)
        positive_results[case_name] = result
        evidence_files.extend(evidence_entry(f"positive_{case_name}_{key}", Path(spec[key])) for key in ("csv", "model", "mapping", "input"))

    negative_results: dict[str, Any] = {}
    for test_name, case_name, mutator in NEGATIVE_CASES:
        test_root = WORK_ROOT / test_name
        spec = copy_case(module, case_name, test_root)
        expected_fragment = mutator(spec)
        negative_results[test_name] = expect_failure(module, case_name, spec, expected_fragment)
        evidence_files.extend(evidence_entry(f"{test_name}_{key}", Path(spec[key])) for key in ("csv", "model", "mapping", "input"))

    negative_rejected_count = sum(1 for result in negative_results.values() if result["rejected"])
    expected_fragment_seen_count = sum(1 for result in negative_results.values() if result["expected_fragment_seen"])
    ready = (
        len(positive_results) == len(module.CASE_SPECS)
        and len(negative_results) == len(NEGATIVE_CASES)
        and negative_rejected_count == len(NEGATIVE_CASES)
        and expected_fragment_seen_count == len(NEGATIVE_CASES)
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST",
        "summary": {
            "liquefied_release_source_balance_negative_selftest_ready": ready,
            "positive_control_count": len(positive_results),
            "negative_case_count": len(negative_results),
            "negative_rejected_count": negative_rejected_count,
            "expected_fragment_seen_count": expected_fragment_seen_count,
            "guards_negative_mdot": negative_results.get("negative_mdot", {}).get("rejected"),
            "guards_species_drift": negative_results.get("species_drift", {}).get("rejected"),
            "guards_schedule_rate_mismatch": negative_results.get("schedule_rate_mismatch", {}).get("rejected"),
            "guards_phase_change_overclaim": negative_results.get("phase_change_overclaim", {}).get("rejected"),
            "guards_generated_input_species_mismatch": negative_results.get("generated_input_species_mismatch", {}).get("rejected"),
        },
        "positive_controls": positive_results,
        "negative_cases": negative_results,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, f"unexpected status: {data.get('status')}")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("liquefied_release_source_balance_negative_selftest_ready") is True, "negative selftest is not ready")
    require(summary.get("positive_control_count") == 2, "unexpected positive control count")
    require(summary.get("negative_case_count") == len(NEGATIVE_CASES), "unexpected negative case count")
    require(summary.get("negative_rejected_count") == len(NEGATIVE_CASES), "not all negative cases were rejected")
    require(summary.get("expected_fragment_seen_count") == len(NEGATIVE_CASES), "not all negative cases had expected diagnostics")
    for key in (
        "guards_negative_mdot",
        "guards_species_drift",
        "guards_schedule_rate_mismatch",
        "guards_phase_change_overclaim",
        "guards_generated_input_species_mismatch",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Engineering Liquefied-Release Source Balance Negative Selftest Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Positive controls: `{summary['positive_control_count']}`",
        f"- Negative cases: `{summary['negative_case_count']}`",
        f"- Rejected negative cases: `{summary['negative_rejected_count']}`",
        f"- Expected diagnostics: `{summary['expected_fragment_seen_count']}`",
        f"- Guards negative mdot: `{summary['guards_negative_mdot']}`",
        f"- Guards species drift: `{summary['guards_species_drift']}`",
        f"- Guards schedule rate mismatch: `{summary['guards_schedule_rate_mismatch']}`",
        f"- Guards phase-change overclaim: `{summary['guards_phase_change_overclaim']}`",
        f"- Guards generated input species mismatch: `{summary['guards_generated_input_species_mismatch']}`",
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
        data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
        validate_report(data, verify_hashes=True)
        print(
            "engineering_liquefied_release_source_balance_negative_selftest "
            f"VERIFY-PASS json={args.verify_json} status={data.get('status')}"
        )
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(
        "engineering_liquefied_release_source_balance_negative_selftest "
        f"PASS json={output_json} md={output_md} status={report['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
