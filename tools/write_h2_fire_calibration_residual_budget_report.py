#!/usr/bin/env python3
"""Write/verify the H2 fire calibration residual-budget evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET"
ROOT = Path("docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811")
DEFAULT_JSON = ROOT / "h2_fire_calibration_residual_budget_report.json"
DEFAULT_MD = ROOT / "h2_fire_calibration_residual_budget_report.md"

STRICT_FIRE = Path(
    "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
    "master_plan_strict_fire_calibration_update_report.json"
)
CANDIDATE_SOURCES = Path(
    "docs/codex_audit/evidence/h2_fire_calibration_candidate_sources_20260805/"
    "h2_fire_calibration_candidate_sources_report.json"
)
EXP002_PRESSURE_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/"
    "h2_fire_exp002_overpressure_calibration_table_report.json"
)
EXP002_PRESSURE_CONTRACT = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_pressure_comparison_contract_20260805/"
    "h2_fire_exp002_pressure_comparison_contract_report.json"
)
EXP002_PRESSURE_CFD_PROXY = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/"
    "h2_fire_exp002_pressure_cfd_proxy_report.json"
)
PLOTFILE_SENSOR_SAMPLING = Path(
    "docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/"
    "h2_fire_plotfile_sensor_sampling_contract_report.json"
)
MDPI_RADIATION_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)
MDPI_RADIATION_SCREENING = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_screening_comparison_20260805/"
    "h2_fire_mdpi_radiation_screening_comparison_report.json"
)
MDPI_RADIATION_INTEGRATED_PROXY = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/"
    "h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json"
)


class ResidualBudgetError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ResidualBudgetError(message)


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
        raise ResidualBudgetError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ResidualBudgetError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float))


def build_report() -> dict[str, Any]:
    strict = load_json(STRICT_FIRE)
    candidates = load_json(CANDIDATE_SOURCES)
    pressure_table = load_json(EXP002_PRESSURE_TABLE)
    pressure_contract = load_json(EXP002_PRESSURE_CONTRACT)
    pressure_proxy = load_json(EXP002_PRESSURE_CFD_PROXY)
    sensor_contract = load_json(PLOTFILE_SENSOR_SAMPLING)
    radiation_table = load_json(MDPI_RADIATION_TABLE)
    radiation_screening = load_json(MDPI_RADIATION_SCREENING)
    radiation_integrated = load_json(MDPI_RADIATION_INTEGRATED_PROXY)

    strict_summary = strict.get("summary", {})
    candidate_summary = candidates.get("summary", {})
    pressure_table_summary = pressure_table.get("summary", {})
    pressure_contract_summary = pressure_contract.get("summary", {})
    pressure_proxy_summary = pressure_proxy.get("summary", {})
    sensor_summary = sensor_contract.get("summary", {})
    radiation_table_summary = radiation_table.get("summary", {})
    radiation_screening_summary = radiation_screening.get("summary", {})
    radiation_integrated_summary = radiation_integrated.get("summary", {})
    for label, summary in [
        ("strict fire", strict_summary),
        ("candidate sources", candidate_summary),
        ("pressure table", pressure_table_summary),
        ("pressure contract", pressure_contract_summary),
        ("pressure proxy", pressure_proxy_summary),
        ("sensor contract", sensor_summary),
        ("radiation table", radiation_table_summary),
        ("radiation screening", radiation_screening_summary),
        ("radiation integrated", radiation_integrated_summary),
    ]:
        require(isinstance(summary, dict), f"{label} summary missing")

    pressure_gates = {
        "candidate_overpressure_available": candidate_summary.get("overpressure_candidate_available") is True,
        "target_table_ready": pressure_table.get("status") == "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE",
        "comparison_contract_ready": pressure_contract_summary.get("pressure_comparison_contract_ready") is True,
        "pressure_proxy_extracted": pressure_proxy_summary.get("pressure_proxy_extracted") is True,
        "cpu_gpu_pressure_proxy_parity_passed": pressure_proxy_summary.get("cpu_gpu_pressure_proxy_parity_passed")
        is True,
        "sensor_sampling_contract_ready": sensor_summary.get("plotfile_sensor_sampling_contract_ready") is True,
        "case_aligned_pressure_agreement": pressure_proxy_summary.get("case_aligned_pressure_sensor_agreement")
        is True,
        "outputs_sufficient_for_pressure_agreement": pressure_proxy_summary.get(
            "current_outputs_sufficient_for_exp002_pressure_agreement"
        )
        is True,
    }
    radiation_gates = {
        "candidate_radiation_available": candidate_summary.get("radiation_candidate_available") is True,
        "target_table_ready": radiation_table.get("status") == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
        "screening_comparison_executed": radiation_screening_summary.get("screening_comparison_executed") is True,
        "screening_all_metrics_passed": radiation_screening_summary.get("all_screening_metrics_passed") is True,
        "integrated_cfd_proxy_extracted": radiation_integrated_summary.get("integrated_cfd_proxy_extracted") is True,
        "virtual_radiometer_flux_generated": radiation_integrated_summary.get("virtual_radiometer_flux_generated")
        is True,
        "case_aligned_radiation_agreement": radiation_integrated_summary.get(
            "case_aligned_cfd_radiation_agreement"
        )
        is True,
        "outputs_sufficient_for_radiation_agreement": radiation_integrated_summary.get(
            "current_outputs_sufficient_for_mdpi_radiation_agreement"
        )
        is True,
    }
    pressure_agreement_ready = all(
        pressure_gates[key]
        for key in (
            "target_table_ready",
            "comparison_contract_ready",
            "sensor_sampling_contract_ready",
            "case_aligned_pressure_agreement",
            "outputs_sufficient_for_pressure_agreement",
        )
    )
    radiation_agreement_ready = all(
        radiation_gates[key]
        for key in (
            "target_table_ready",
            "integrated_cfd_proxy_extracted",
            "case_aligned_radiation_agreement",
            "outputs_sufficient_for_radiation_agreement",
        )
    )
    blocker_cleared = pressure_agreement_ready and radiation_agreement_ready
    strict_blocker_cleared = strict_summary.get("strict_fire_calibration_blocker_cleared") is True

    pressure_missing = [
        "exact EXP002 sensor coordinates and mapping into the CFD geometry",
        "case-aligned pressure-sensor time histories from Pele plotfiles",
        "peak overpressure plus arrival-time acceptance against EXP002 channels",
    ]
    radiation_missing = [
        "case-aligned radiometer geometry/view factors and orientation",
        "calibrated radiation model or accepted radiative-fraction closure",
        "radiation target agreement within the MDPI comparison contract tolerances",
    ]

    max_screening_ratio = radiation_screening_summary.get("max_source_limited_to_reference_ratio")
    min_screening_ratio = radiation_screening_summary.get("min_source_limited_to_reference_ratio")
    require(finite_number(max_screening_ratio), "missing radiation screening max source/reference ratio")
    require(finite_number(min_screening_ratio), "missing radiation screening min source/reference ratio")

    summary = {
        "fire_calibration_residual_budget_ready": True,
        "strict_fire_calibration_status": strict.get("status"),
        "strict_fire_calibration_blocker_cleared": strict_blocker_cleared,
        "residual_budget_clears_strict_blocker": blocker_cleared,
        "pressure_agreement_ready": pressure_agreement_ready,
        "radiation_agreement_ready": radiation_agreement_ready,
        "pressure_candidate_available": pressure_gates["candidate_overpressure_available"],
        "radiation_candidate_available": radiation_gates["candidate_radiation_available"],
        "pressure_proxy_cpu_gpu_parity_passed": pressure_gates["cpu_gpu_pressure_proxy_parity_passed"],
        "pressure_proxy_cpu_gpu_rel_diff": pressure_proxy_summary.get("cpu_gpu_peak_abs_pressure_rel_diff"),
        "pressure_case_aligned_agreement": pressure_gates["case_aligned_pressure_agreement"],
        "pressure_outputs_sufficient_for_agreement": pressure_gates["outputs_sufficient_for_pressure_agreement"],
        "radiation_integrated_proxy_extracted": radiation_gates["integrated_cfd_proxy_extracted"],
        "radiation_virtual_radiometer_flux_generated": radiation_gates["virtual_radiometer_flux_generated"],
        "radiation_case_aligned_agreement": radiation_gates["case_aligned_radiation_agreement"],
        "radiation_outputs_sufficient_for_agreement": radiation_gates["outputs_sufficient_for_radiation_agreement"],
        "radiation_screening_metric_pass_count": radiation_screening_summary.get("metric_pass_count"),
        "radiation_screening_metric_fail_count": radiation_screening_summary.get("metric_fail_count"),
        "radiation_screening_min_source_reference_ratio": min_screening_ratio,
        "radiation_screening_max_source_reference_ratio": max_screening_ratio,
        "pressure_missing_artifact_count": len(pressure_missing),
        "radiation_missing_artifact_count": len(radiation_missing),
        "production_fire_calibration_claim_allowed": False,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "scope": "strict fire radiation/overpressure calibration residual budget",
        "summary": summary,
        "pressure_gates": pressure_gates,
        "radiation_gates": radiation_gates,
        "missing_artifacts": {
            "pressure": pressure_missing,
            "radiation": radiation_missing,
        },
        "acceptance_policy": {
            "strict_credit_requires_pressure_agreement": True,
            "strict_credit_requires_radiation_agreement": True,
            "cpu_gpu_parity_alone_clears_strict_fire_blocker": False,
            "screening_radiation_proxy_alone_clears_strict_fire_blocker": False,
        },
        "evidence_files": [
            evidence_entry("strict_fire_calibration_update", STRICT_FIRE),
            evidence_entry("candidate_sources", CANDIDATE_SOURCES),
            evidence_entry("exp002_pressure_table", EXP002_PRESSURE_TABLE),
            evidence_entry("exp002_pressure_contract", EXP002_PRESSURE_CONTRACT),
            evidence_entry("exp002_pressure_cfd_proxy", EXP002_PRESSURE_CFD_PROXY),
            evidence_entry("plotfile_sensor_sampling_contract", PLOTFILE_SENSOR_SAMPLING),
            evidence_entry("mdpi_radiation_table", MDPI_RADIATION_TABLE),
            evidence_entry("mdpi_radiation_screening", MDPI_RADIATION_SCREENING),
            evidence_entry("mdpi_radiation_integrated_proxy", MDPI_RADIATION_INTEGRATED_PROXY),
        ],
        "limitations": [
            "This report budgets the remaining calibration residuals; it does not clear strict fire credit.",
            "Pressure credit still requires mapped EXP002 sensor time histories and acceptance checks.",
            "Radiation credit still requires case-aligned radiometer comparisons or a validated radiation closure.",
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "unexpected residual-budget status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("fire_calibration_residual_budget_ready") is True, "residual budget is not ready")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker was overclaimed")
    require(summary.get("residual_budget_clears_strict_blocker") is False, "residual budget should not clear blocker")
    require(summary.get("pressure_agreement_ready") is False, "pressure agreement unexpectedly ready")
    require(summary.get("radiation_agreement_ready") is False, "radiation agreement unexpectedly ready")
    require(summary.get("pressure_proxy_cpu_gpu_parity_passed") is True, "pressure CPU/GPU parity regressed")
    require(summary.get("radiation_integrated_proxy_extracted") is True, "radiation integrated proxy missing")
    require(summary.get("radiation_virtual_radiometer_flux_generated") is True, "virtual radiometer flux missing")
    require(summary.get("production_fire_calibration_claim_allowed") is False, "production fire claim overclaimed")
    require(summary.get("pressure_missing_artifact_count") >= 3, "pressure missing-artifact budget too small")
    require(summary.get("radiation_missing_artifact_count") >= 3, "radiation missing-artifact budget too small")
    require(data.get("acceptance_policy", {}).get("cpu_gpu_parity_alone_clears_strict_fire_blocker") is False, "CPU/GPU parity overclaimed")
    require(data.get("acceptance_policy", {}).get("screening_radiation_proxy_alone_clears_strict_fire_blocker") is False, "screening radiation overclaimed")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# H2 Fire Calibration Residual Budget",
        "",
        f"- Status: `{report['status']}`",
        f"- Residual budget ready: `{summary['fire_calibration_residual_budget_ready']}`",
        f"- Strict fire blocker cleared: `{summary['strict_fire_calibration_blocker_cleared']}`",
        f"- Pressure agreement ready: `{summary['pressure_agreement_ready']}`",
        f"- Radiation agreement ready: `{summary['radiation_agreement_ready']}`",
        f"- Pressure CPU/GPU parity: `{summary['pressure_proxy_cpu_gpu_parity_passed']}`",
        f"- Radiation integrated proxy extracted: `{summary['radiation_integrated_proxy_extracted']}`",
        f"- Radiation screening pass/fail: `{summary['radiation_screening_metric_pass_count']}/{summary['radiation_screening_metric_fail_count']}`",
        f"- Production fire calibration claim allowed: `{summary['production_fire_calibration_claim_allowed']}`",
        "",
        "## Missing Artifacts",
        "",
        "### Pressure",
        "",
    ]
    lines.extend(f"- {item}" for item in report["missing_artifacts"]["pressure"])
    lines.extend(["", "### Radiation", ""])
    lines.extend(f"- {item}" for item in report["missing_artifacts"]["radiation"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data)
            print(f"h2_fire_calibration_residual_budget VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report()
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"h2_fire_calibration_residual_budget PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except ResidualBudgetError as exc:
        print(f"h2_fire_calibration_residual_budget FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
