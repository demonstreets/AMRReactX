#!/usr/bin/env python3
"""Write/verify the engineering fuel-species guard report."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-FUEL-SPECIES-GUARD"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_fuel_species_guard_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_fuel_species_guard_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_fuel_species_guard_report.md"

PROB_H = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
PROB_CPP = Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")
INVALID_INPUT = DEFAULT_ROOT / "input.invalid_fuel_species"
INVALID_RUN_LOG = DEFAULT_ROOT / "invalid_fuel_species_run.log"
INVALID_RC = DEFAULT_ROOT / "invalid_fuel_species_rc.txt"
MULTI_FUEL_OPERATOR = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806/"
    "engineering_multi_fuel_operator_runbook_report.json"
)
MULTI_FUEL_BOUNDARY = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
    "engineering_multi_fuel_capability_boundary_report.json"
)


class FuelSpeciesGuardError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FuelSpeciesGuardError(message)


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
        raise FuelSpeciesGuardError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FuelSpeciesGuardError(f"invalid JSON evidence {path}: {exc}") from exc
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


def parse_rc(path: Path) -> int:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except FileNotFoundError as exc:
        raise FuelSpeciesGuardError(f"missing return-code evidence: {path}") from exc
    except ValueError as exc:
        raise FuelSpeciesGuardError(f"invalid return-code evidence: {path}") from exc


def build_report() -> dict[str, Any]:
    prob_h = PROB_H.read_text(encoding="utf-8", errors="replace")
    prob_cpp = PROB_CPP.read_text(encoding="utf-8", errors="replace")
    invalid_input = INVALID_INPUT.read_text(encoding="utf-8", errors="replace")
    invalid_log = INVALID_RUN_LOG.read_text(encoding="utf-8", errors="replace")
    invalid_rc = parse_rc(INVALID_RC)
    operator = load_json(MULTI_FUEL_OPERATOR)
    boundary = load_json(MULTI_FUEL_BOUNDARY)

    source_lookup_guard_ready = (
        "prob_parm->fuel_species_index = -1" in prob_cpp
        and "CKSYMS_STR(species_names)" in prob_cpp
        and "species_names[n] == fuel_species" in prob_cpp
        and "prob.fuel_species was not found in the compiled chemistry mechanism" in prob_cpp
        and "source.species_index = pp->fuel_species_index" in prob_h
        and "mf[pp->fuel_species_index]=1.0" in prob_h
    )
    invalid_runtime_abort_passed = (
        invalid_rc != 0
        and "prob.fuel_species = CODEX_NOT_A_SPECIES" in invalid_input
        and "prob.fuel_species was not found in the compiled chemistry mechanism" in invalid_log
        and "Applying CODEX_NOT_A_SPECIES leak source" not in invalid_log
        and "Engineering leak fuel species: name=H2" not in invalid_log
    )
    upstream_multifuel_reports_ready = (
        operator.get("status") == "PASS-ENGINEERING-MULTI-FUEL-OPERATOR-RUNBOOK"
        and boundary.get("status") == "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY"
    )
    ready = source_lookup_guard_ready and invalid_runtime_abort_passed and upstream_multifuel_reports_ready

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-FUEL-SPECIES-GUARD",
        "summary": {
            "source_lookup_guard_ready": source_lookup_guard_ready,
            "invalid_species_runtime_abort_passed": invalid_runtime_abort_passed,
            "invalid_species_return_code": invalid_rc,
            "unknown_species_silent_h2_fallback_detected": "Engineering leak fuel species: name=H2" in invalid_log,
            "unknown_species_source_applied_detected": "Applying CODEX_NOT_A_SPECIES leak source" in invalid_log,
            "upstream_multifuel_reports_ready": upstream_multifuel_reports_ready,
            "prevents_unknown_fuel_silent_fallback": ready,
        },
        "runtime_probe": {
            "input": str(INVALID_INPUT),
            "run_log": str(INVALID_RUN_LOG),
            "return_code_file": str(INVALID_RC),
            "expected_abort_marker": "prob.fuel_species was not found in the compiled chemistry mechanism",
        },
        "evidence_files": [
            evidence_entry("engineering_h2_leak_prob_h", PROB_H),
            evidence_entry("engineering_h2_leak_prob_cpp", PROB_CPP),
            evidence_entry("invalid_fuel_species_input", INVALID_INPUT),
            evidence_entry("invalid_fuel_species_run_log", INVALID_RUN_LOG),
            evidence_entry("invalid_fuel_species_rc", INVALID_RC),
            evidence_entry("engineering_multi_fuel_operator_runbook_report", MULTI_FUEL_OPERATOR),
            evidence_entry("engineering_multi_fuel_capability_boundary_report", MULTI_FUEL_BOUNDARY),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("source_lookup_guard_ready") is True, "source lookup guard missing")
    require(summary.get("invalid_species_runtime_abort_passed") is True, "invalid species runtime abort missing")
    require(int(summary.get("invalid_species_return_code", 0)) != 0, "invalid species run unexpectedly succeeded")
    require(summary.get("unknown_species_silent_h2_fallback_detected") is False, "unknown species silently fell back to H2")
    require(summary.get("unknown_species_source_applied_detected") is False, "unknown species source was applied")
    require(summary.get("upstream_multifuel_reports_ready") is True, "upstream multi-fuel reports missing")
    require(summary.get("prevents_unknown_fuel_silent_fallback") is True, "unknown fuel fallback guard not ready")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Fuel-Species Guard Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Source lookup guard ready: `{s['source_lookup_guard_ready']}`",
        f"- Invalid species runtime abort passed: `{s['invalid_species_runtime_abort_passed']}`",
        f"- Invalid species return code: `{s['invalid_species_return_code']}`",
        f"- Silent H2 fallback detected: `{s['unknown_species_silent_h2_fallback_detected']}`",
        f"- Unknown species source applied: `{s['unknown_species_source_applied_detected']}`",
        f"- Prevents unknown fuel silent fallback: `{s['prevents_unknown_fuel_silent_fallback']}`",
        "",
        "## Runtime Probe",
        "",
        f"- Input: `{report['runtime_probe']['input']}`",
        f"- Run log: `{report['runtime_probe']['run_log']}`",
        f"- Expected abort marker: `{report['runtime_probe']['expected_abort_marker']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{entry['label']}`: `{entry['path']}`" for entry in report["evidence_files"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"engineering_fuel_species_guard VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_fuel_species_guard PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (FuelSpeciesGuardError, OSError, json.JSONDecodeError) as exc:
        print(f"engineering_fuel_species_guard FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
