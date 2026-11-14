#!/usr/bin/env python3
"""Write/verify the operator answer for non-H2 and liquefied-gas engineering use."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ENGINEERING-MULTIFUEL-LIQUEFIED-USER-ANSWER"
STATUS_NOT_READY = "NOT_READY-ENGINEERING-MULTIFUEL-LIQUEFIED-USER-ANSWER"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_multifuel_liquefied_user_answer_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_multifuel_liquefied_user_answer_report.md"

MULTI_FUEL = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
    "engineering_multi_fuel_capability_boundary_report.json"
)
TEMPLATE_CATALOG = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/"
    "engineering_multi_fuel_template_catalog_report.json"
)
LIQUEFIED_BREACH_PRESETS = Path(
    "docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/"
    "engineering_liquefied_breach_preset_templates_report.json"
)
LIQUEFIED_BREACH_CONTRACT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/"
    "engineering_liquefied_breach_source_contract_report.json"
)
PARALLEL_MATRIX = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)


class UserAnswerReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UserAnswerReportError(message)


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
        raise UserAnswerReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise UserAnswerReportError(f"invalid JSON evidence {path}: {exc}") from exc
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


def require_status(report: dict[str, Any], expected: str, label: str) -> None:
    require(report.get("status") == expected, f"{label} status mismatch: {report.get('status')}")


def build_report() -> dict[str, Any]:
    multi = load_json(MULTI_FUEL)
    catalog = load_json(TEMPLATE_CATALOG)
    presets = load_json(LIQUEFIED_BREACH_PRESETS)
    contract = load_json(LIQUEFIED_BREACH_CONTRACT)
    parallel = load_json(PARALLEL_MATRIX)

    require_status(multi, "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY", "multi-fuel")
    require_status(catalog, "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG", "template catalog")
    require_status(presets, "PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES", "liquefied presets")
    require_status(contract, "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT", "liquefied breach contract")
    require_status(parallel, "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX", "parallel matrix")

    msum = multi["summary"]
    csum = catalog["summary"]
    psum = presets["summary"]
    bsum = contract["summary"]
    parsum = parallel["summary"]

    gas_species = sorted(set(csum["fuel_species_seen"]) | set(psum["species"]) | set(bsum["species"]))
    liquefied_fluids = sorted(set(psum["fluids"]) | set(bsum["fluids"]))

    gas_phase_ready = all(
        msum.get(key) is True
        for key in [
            "source_fuel_species_configurable",
            "h2_engineering_current_scope_ready",
            "ch4_delayed_ignition_cpu_mpi_fire_probe_passed",
            "ch4_delayed_ignition_single_cuda_fire_probe_passed",
            "ch4_delayed_ignition_mpi_cuda_fire_probe_passed",
            "c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_probe_passed",
        ]
    )
    liquefied_screening_ready = all(
        value is True
        for value in [
            psum.get("liquefied_breach_preset_templates_ready"),
            psum.get("editable_json_presets"),
            psum.get("generates_cfd_source_csv"),
            bsum.get("liquefied_breach_source_contract_ready"),
            bsum.get("contract_accepts_screening_breach_inputs"),
            bsum.get("generates_external_gas_source_schedule"),
            msum.get("gasified_lng_given_source_surrogate_ready"),
            msum.get("gasified_lpg_given_source_surrogate_ready"),
            msum.get("external_vaporization_multifuel_timeseries_cuda_passed"),
            msum.get("liquefied_release_vaporization_source_model_cuda_smoke_passed"),
        ]
    )
    parallel_ready = all(
        parsum.get(key) is True
        for key in [
            "cpu_mpi_ready_for_all_current_scenarios",
            "single_gpu_ready_for_all_current_scenarios",
            "multi_gpu_mpi_cuda_ready_for_all_current_scenarios",
        ]
    )
    internal_phase_change_ready = any(
        value is True
        for value in [
            msum.get("liquefied_gas_phase_change_ready"),
            psum.get("cfd_solves_liquid_phase_change"),
            psum.get("cfd_solves_flashing_discharge"),
            psum.get("cfd_solves_pool_spread_evaporation"),
            bsum.get("cfd_solves_liquid_phase_change"),
            bsum.get("cfd_solves_flashing_discharge"),
            bsum.get("cfd_solves_pool_spread_evaporation"),
        ]
    )
    production_phase_change_claim_allowed = any(
        value is True
        for value in [
            psum.get("production_phase_change_claim_allowed"),
            bsum.get("production_phase_change_claim_allowed"),
            csum.get("cfd_internal_liquid_phase_change_claim_allowed"),
        ]
    )
    ready = (
        gas_phase_ready
        and liquefied_screening_ready
        and parallel_ready
        and not internal_phase_change_ready
        and not production_phase_change_claim_allowed
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "scope": "evidence-backed answer for non-H2 gases and LNG/LPG liquefied breach engineering use",
        "answers": {
            "can_compute_other_gases": (
                "Yes for current gas-phase source workflows with H2, CH4, and C3H8 evidence; "
                "additional species require a compatible mechanism and source template."
            ),
            "can_compute_propane": (
                "Yes for gas-phase C3H8/propane source, dispersion, ignition, and fire screening in the current scope."
            ),
            "can_compute_lng_lpg": (
                "Yes as gasified LNG/CH4 and LPG/C3H8 external-source or screening vaporization workflows."
            ),
            "can_compute_liquefied_tank_breach_vaporization": (
                "Screening external gas-source schedules can be generated from editable LNG/LPG breach presets; "
                "CFD-internal flashing discharge, liquid-pool spread, boiling, and evaporation are not yet solved."
            ),
        },
        "summary": {
            "gas_phase_non_h2_ready": gas_phase_ready,
            "gaseous_h2_ready": msum["h2_engineering_current_scope_ready"],
            "gaseous_ch4_ready": msum["ch4_delayed_ignition_mpi_cuda_500step_fire_probe_passed"],
            "gaseous_c3h8_propane_ready": msum["c3h8_propane_gas_phase_initial_ready"],
            "gas_species_supported_in_current_templates": gas_species,
            "gasified_lng_ch4_ready": msum["gasified_lng_given_source_surrogate_ready"],
            "gasified_lpg_c3h8_ready": msum["gasified_lpg_given_source_surrogate_ready"],
            "liquefied_fluids_with_screening_presets": liquefied_fluids,
            "liquefied_breach_external_source_ready": liquefied_screening_ready,
            "liquefied_breach_preset_count": psum["preset_count"],
            "liquefied_breach_generates_cfd_csv": psum["generates_cfd_source_csv"],
            "liquefied_breach_max_gas_mass_relative_error": bsum["max_gas_mass_relative_error"],
            "liquefied_breach_max_peak_jet_speed_m_s": bsum["max_peak_jet_speed_m_s"],
            "cpu_mpi_ready_for_current_scenarios": parsum["cpu_mpi_ready_for_all_current_scenarios"],
            "single_gpu_ready_for_current_scenarios": parsum["single_gpu_ready_for_all_current_scenarios"],
            "multi_gpu_mpi_cuda_ready_for_current_scenarios": parsum[
                "multi_gpu_mpi_cuda_ready_for_all_current_scenarios"
            ],
            "internal_liquid_phase_change_cfd_ready": internal_phase_change_ready,
            "cfd_solves_flashing_discharge": bsum["cfd_solves_flashing_discharge"],
            "cfd_solves_pool_spread_evaporation": bsum["cfd_solves_pool_spread_evaporation"],
            "production_phase_change_claim_allowed": production_phase_change_claim_allowed,
            "operator_answer_ready": ready,
        },
        "limitations": [
            "The current positive claim is for gas-phase source workflows and audited external vaporization schedules.",
            "A process-safety source schedule or measured release rate should replace the screening schedule when available.",
            "Complete LNG/LPG tank rupture, flashing multiphase discharge, pool spread, boiling, ground heat transfer, and EOS-coupled phase change remain outside the current production claim.",
        ],
        "evidence_files": [
            evidence_entry("engineering_multi_fuel_capability_boundary", MULTI_FUEL),
            evidence_entry("engineering_multi_fuel_template_catalog", TEMPLATE_CATALOG),
            evidence_entry("engineering_liquefied_breach_preset_templates", LIQUEFIED_BREACH_PRESETS),
            evidence_entry("engineering_liquefied_breach_source_contract", LIQUEFIED_BREACH_CONTRACT),
            evidence_entry("current_parallel_capability_matrix", PARALLEL_MATRIX),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "operator answer report is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("operator_answer_ready") is True, "operator answer is not ready")
    require(summary.get("gas_phase_non_h2_ready") is True, "non-H2 gas phase capability is not ready")
    require(summary.get("gaseous_h2_ready") is True, "H2 capability is not ready")
    require(summary.get("gaseous_ch4_ready") is True, "CH4 capability is not ready")
    require(summary.get("gaseous_c3h8_propane_ready") is True, "C3H8 capability is not ready")
    require(set(summary.get("gas_species_supported_in_current_templates", [])) == {"C3H8", "CH4", "H2"}, "unexpected gas species set")
    require(summary.get("gasified_lng_ch4_ready") is True, "gasified LNG/CH4 path is not ready")
    require(summary.get("gasified_lpg_c3h8_ready") is True, "gasified LPG/C3H8 path is not ready")
    require(set(summary.get("liquefied_fluids_with_screening_presets", [])) == {"LNG_CH4", "LPG_C3H8"}, "unexpected liquefied fluid set")
    require(summary.get("liquefied_breach_external_source_ready") is True, "liquefied breach external source is not ready")
    require(summary.get("liquefied_breach_preset_count") == 2, "unexpected liquefied breach preset count")
    require(summary.get("liquefied_breach_generates_cfd_csv") is True, "liquefied breach presets do not generate CSV")
    require(summary.get("liquefied_breach_max_gas_mass_relative_error") < 0.01, "liquefied breach mass error too large")
    require(summary.get("cpu_mpi_ready_for_current_scenarios") is True, "CPU/MPI current scenarios not ready")
    require(summary.get("single_gpu_ready_for_current_scenarios") is True, "single GPU current scenarios not ready")
    require(summary.get("multi_gpu_mpi_cuda_ready_for_current_scenarios") is True, "MPI+CUDA current scenarios not ready")
    require(summary.get("internal_liquid_phase_change_cfd_ready") is False, "internal phase-change CFD should not be overclaimed")
    require(summary.get("cfd_solves_flashing_discharge") is False, "flashing discharge should not be overclaimed")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, "pool spread/evaporation should not be overclaimed")
    require(summary.get("production_phase_change_claim_allowed") is False, "production phase-change claim should not be allowed")
    answers = data.get("answers")
    require(isinstance(answers, dict), "missing answers")
    for key in [
        "can_compute_other_gases",
        "can_compute_propane",
        "can_compute_lng_lpg",
        "can_compute_liquefied_tank_breach_vaporization",
    ]:
        require(isinstance(answers.get(key), str) and answers[key], f"missing answer: {key}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    answers = report["answers"]
    lines = [
        "# Engineering Multifuel And Liquefied-Gas User Answer",
        "",
        f"- Status: `{report['status']}`",
        f"- Operator answer ready: `{summary['operator_answer_ready']}`",
        f"- Gas species in current templates: `{', '.join(summary['gas_species_supported_in_current_templates'])}`",
        f"- Liquefied fluids with screening presets: `{', '.join(summary['liquefied_fluids_with_screening_presets'])}`",
        f"- CPU/MPI current scenarios: `{summary['cpu_mpi_ready_for_current_scenarios']}`",
        f"- Single GPU current scenarios: `{summary['single_gpu_ready_for_current_scenarios']}`",
        f"- MPI+CUDA current scenarios: `{summary['multi_gpu_mpi_cuda_ready_for_current_scenarios']}`",
        f"- Internal liquid phase-change CFD ready: `{summary['internal_liquid_phase_change_cfd_ready']}`",
        f"- Production phase-change claim allowed: `{summary['production_phase_change_claim_allowed']}`",
        "",
        "## Answers",
        "",
    ]
    for key, value in answers.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Limits"])
    for item in report["limitations"]:
        lines.append(f"- {item}")
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
        print(f"engineering_multifuel_liquefied_user_answer VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"engineering_multifuel_liquefied_user_answer PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
