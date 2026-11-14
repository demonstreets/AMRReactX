#!/usr/bin/env python3
"""Write/verify the engineering multi-fuel operator runbook report."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-MULTI-FUEL-OPERATOR-RUNBOOK"

RUNBOOK = Path("docs/codex_audit/engineering_multi_fuel_operator_runbook.md")
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_multi_fuel_operator_runbook_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_multi_fuel_operator_runbook_report.md"

MULTI_FUEL_BOUNDARY = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
    "engineering_multi_fuel_capability_boundary_report.json"
)
GASIFIED_SURROGATE = Path(
    "docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/"
    "engineering_gasified_lng_lpg_surrogate_report.json"
)
C3H8_REPORT = Path(
    "docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/"
    "engineering_c3h8_gas_phase_cpu_cuda_report.json"
)
CH4_500STEP_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/"
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json"
)
H2_PRODUCTION_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json"
)
LIQUEFIED_EXTERNAL_VAPORIZATION_CONTRACT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/"
    "engineering_liquefied_external_vaporization_contract_report.json"
)
LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
    "engineering_liquefied_release_vaporization_source_model_report.json"
)
LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_NEGATIVE_SELFTEST = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/"
    "engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json"
)
LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_CUDA_SMOKE = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/"
    "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"
)
LIQUEFIED_EXTERNAL_VAPORIZATION_NEGATIVE_SELFTEST = Path(
    "docs/codex_audit/evidence/engineering_liquefied_external_vaporization_negative_selftest_20260806/"
    "engineering_liquefied_external_vaporization_negative_selftest_report.json"
)
FIXED_MASS_FLOW_VALVE_SCHEDULE = Path(
    "docs/codex_audit/evidence/engineering_fixed_mass_flow_valve_schedule_20260806/"
    "engineering_fixed_mass_flow_valve_schedule_report.json"
)
EXTERNAL_VAPORIZATION_TIMESERIES = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/"
    "engineering_external_vaporization_timeseries_report.json"
)
EXTERNAL_VAPORIZATION_TIMESERIES_CUDA = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/"
    "engineering_external_vaporization_timeseries_cuda_report.json"
)
EXTERNAL_VAPORIZATION_MULTIFUEL_SOURCE_MATRIX = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/"
    "engineering_external_vaporization_multifuel_source_matrix_report.json"
)
C3H8_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/"
    "c3h8_timeseries_cuda/engineering_external_vaporization_c3h8_timeseries_cuda_report.json"
)

REQUIRED_INPUTS = {
    "gasified_lng_ch4_cold_source": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke"),
    "gasified_lng_ch4_warmed_fire": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step"),
    "gasified_lpg_c3h8_fire": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke"),
    "fixed_mass_flow_valve_schedule": Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_valve_schedule_smoke"),
    "fixed_mass_flow_timeseries": Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke"),
    "lng_external_vaporization_csv_template": Path("examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv"),
}

REQUIRED_TOOLS = [
    Path("tools/codex_make_external_vaporization_source_input.py"),
    Path("tools/write_engineering_gasified_lng_lpg_surrogate_report.py"),
    Path("tools/verify_engineering_gasified_lng_lpg_surrogate.sh"),
    Path("tools/write_engineering_multi_fuel_capability_boundary_report.py"),
    Path("tools/verify_engineering_multi_fuel_capability_boundary.sh"),
    Path("tools/write_engineering_liquefied_external_vaporization_contract_report.py"),
    Path("tools/verify_engineering_liquefied_external_vaporization_contract.sh"),
    Path("tools/codex_make_liquefied_release_vaporization_csv.py"),
    Path("tools/write_engineering_liquefied_release_vaporization_source_model_report.py"),
    Path("tools/verify_engineering_liquefied_release_vaporization_source_model.sh"),
    Path("tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py"),
    Path("tools/verify_engineering_liquefied_release_vaporization_source_model_negative_selftest.sh"),
    Path("tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh"),
    Path("tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py"),
    Path("tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh"),
    Path("tools/write_engineering_liquefied_external_vaporization_negative_selftest_report.py"),
    Path("tools/verify_engineering_liquefied_external_vaporization_negative_selftest.sh"),
    Path("tools/write_engineering_fixed_mass_flow_valve_schedule_report.py"),
    Path("tools/verify_engineering_fixed_mass_flow_valve_schedule.sh"),
    Path("tools/write_engineering_external_vaporization_timeseries_report.py"),
    Path("tools/verify_engineering_external_vaporization_timeseries.sh"),
    Path("tools/write_engineering_external_vaporization_timeseries_cuda_report.py"),
    Path("tools/verify_engineering_external_vaporization_timeseries_cuda.sh"),
    Path("tools/write_engineering_external_vaporization_multifuel_source_matrix_report.py"),
    Path("tools/verify_engineering_external_vaporization_multifuel_source_matrix.sh"),
    Path("tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py"),
    Path("tools/verify_engineering_external_vaporization_c3h8_timeseries_cuda.sh"),
    Path("tools/codex_verify_current_scope.sh"),
]

REQUIRED_RUNBOOK_SNIPPETS = [
    "Engineering Multi-Fuel Operator Runbook",
    "prob.fuel_species",
    "H2",
    "CH4",
    "C3H8",
    "gasified LNG",
    "gasified LPG",
    "bash tools/codex_verify_current_scope.sh",
    "python3 tools/write_engineering_gasified_lng_lpg_surrogate_report.py",
    "bash tools/verify_engineering_gasified_lng_lpg_surrogate.sh",
    "python3 tools/write_engineering_multi_fuel_capability_boundary_report.py",
    "bash tools/verify_engineering_multi_fuel_capability_boundary.sh",
    "python3 tools/codex_make_external_vaporization_source_input.py",
    "python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py",
    "bash tools/verify_engineering_liquefied_external_vaporization_contract.sh",
    "python3 tools/codex_make_liquefied_release_vaporization_csv.py",
    "python3 tools/write_engineering_liquefied_release_vaporization_source_model_report.py",
    "bash tools/verify_engineering_liquefied_release_vaporization_source_model.sh",
    "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL",
    "python3 tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py",
    "bash tools/verify_engineering_liquefied_release_vaporization_source_model_negative_selftest.sh",
    "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST",
    "bash tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
    "python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py",
    "bash tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
    "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE",
    "Claim Boundary Quick Reference",
    "Gas-phase CFD claim: H2, CH4, and C3H8 gas sources can be selected when the compiled mechanism contains the species.",
    "Liquid-release bridge claim: LNG_CH4 and LPG_C3H8 rupture screening can be converted to generated gas-source CSV/PeleLMeX inputs.",
    "CFD-internal phase-change claim: not allowed for flashing discharge, liquid pool spread, or pool evaporation.",
    "Generated LNG_CH4 and LPG_C3H8 source inputs have CUDA smoke evidence.",
    "python3 tools/write_engineering_liquefied_external_vaporization_negative_selftest_report.py",
    "bash tools/verify_engineering_liquefied_external_vaporization_negative_selftest.sh",
    "python3 tools/write_engineering_fixed_mass_flow_valve_schedule_report.py",
    "bash tools/verify_engineering_fixed_mass_flow_valve_schedule.sh",
    "python3 tools/write_engineering_external_vaporization_timeseries_report.py",
    "bash tools/verify_engineering_external_vaporization_timeseries.sh",
    "python3 tools/write_engineering_external_vaporization_timeseries_cuda_report.py",
    "bash tools/verify_engineering_external_vaporization_timeseries_cuda.sh",
    "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA",
    "python3 tools/write_engineering_external_vaporization_multifuel_source_matrix_report.py",
    "bash tools/verify_engineering_external_vaporization_multifuel_source_matrix.sh",
    "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX",
    "python3 tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py",
    "bash tools/verify_engineering_external_vaporization_c3h8_timeseries_cuda.sh",
    "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-C3H8-TIMESERIES-CUDA",
    "input.codex_gasified_lng_ch4_surrogate_smoke",
    "input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step",
    "input.codex_gasified_lpg_c3h8_surrogate_smoke",
    "input.codex_fixed_mass_flow_valve_schedule_smoke",
    "input.codex_fixed_mass_flow_timeseries_smoke",
    "codex_lng_external_vaporization_source_template.csv",
    "liquid tank rupture mechanics",
    "flashing two-phase discharge",
    "liquid pool spread and evaporation",
    "lng_lpg_production_phase_change_claim_allowed = false",
    "external vaporization model supplies gas-phase source data",
    "fixed_mass_flow_scheduled",
    "prob.leak_schedule_times",
    "prob.leak_schedule_rates",
    "prob.leak_schedule_temperatures",
    "prob.leak_schedule_vel_x",
    "prob.leak_schedule_vel_y",
    "prob.leak_schedule_vel_z",
    "prob.leak_schedule_radius",
    "prob.leak_schedule_x",
    "prob.leak_schedule_y",
    "prob.leak_schedule_z",
    "fixed_mass_flow_timeseries",
    "cfd_solves_liquid_phase_change = false",
    "negative cases refused",
]


class RunbookError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RunbookError(message)


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
        raise RunbookError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunbookError(f"invalid JSON evidence {path}: {exc}") from exc
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


def write_runbook(path: Path, fuels: dict[str, Any], reports: dict[str, str]) -> None:
    lines = [
        "# Engineering Multi-Fuel Operator Runbook",
        "",
        "This runbook records the evidence-backed engineering fuel scope for the h2_leak_3d example family.",
        "",
        "## Verification Commands",
        "",
        "```bash",
        "python3 tools/write_engineering_gasified_lng_lpg_surrogate_report.py",
        "bash tools/verify_engineering_gasified_lng_lpg_surrogate.sh",
        "python3 tools/write_engineering_multi_fuel_capability_boundary_report.py",
        "bash tools/verify_engineering_multi_fuel_capability_boundary.sh",
        "python3 tools/codex_make_external_vaporization_source_input.py --source-csv examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv --base-input examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke --time 2.0 --output-input docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/input.codex_lng_external_vaporization_source_t2s --output-json docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/external_vaporization_source_mapping_t2s.json",
        "python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py",
        "bash tools/verify_engineering_liquefied_external_vaporization_contract.sh",
        "python3 tools/codex_make_liquefied_release_vaporization_csv.py --fluid LNG_CH4 --inventory-kg 25.0 --initial-pressure-Pa 650000.0 --hole-diameter-m 0.020 --duration-s 8.0 --points 9 --liquid-T-K 125.0 --vapor-T-K 285.0 --output-csv docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/lng_ch4_screening_release/lng_ch4_screening_release_source.csv --output-json docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/lng_ch4_screening_release/lng_ch4_screening_release_source_model.json",
        "python3 tools/write_engineering_liquefied_release_vaporization_source_model_report.py",
        "bash tools/verify_engineering_liquefied_release_vaporization_source_model.sh",
        "python3 tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py",
        "bash tools/verify_engineering_liquefied_release_vaporization_source_model_negative_selftest.sh",
        "bash tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
        "python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py",
        "bash tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
        "python3 tools/write_engineering_liquefied_external_vaporization_negative_selftest_report.py",
        "bash tools/verify_engineering_liquefied_external_vaporization_negative_selftest.sh",
        "python3 tools/write_engineering_fixed_mass_flow_valve_schedule_report.py",
        "bash tools/verify_engineering_fixed_mass_flow_valve_schedule.sh",
        "python3 tools/write_engineering_external_vaporization_timeseries_report.py",
        "bash tools/verify_engineering_external_vaporization_timeseries.sh",
        "python3 tools/write_engineering_external_vaporization_timeseries_cuda_report.py",
        "bash tools/verify_engineering_external_vaporization_timeseries_cuda.sh",
        "python3 tools/write_engineering_external_vaporization_multifuel_source_matrix_report.py",
        "bash tools/verify_engineering_external_vaporization_multifuel_source_matrix.sh",
        "python3 tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py",
        "bash tools/verify_engineering_external_vaporization_c3h8_timeseries_cuda.sh",
        "bash tools/codex_verify_current_scope.sh",
        "```",
        "",
        "Expected status for the screening liquefied-release source-model bridge: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL`.",
        "Expected negative-selftest status for the screening liquefied-release source-model bridge: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST`.",
        "Expected CUDA-smoke status for generated liquefied-release inputs: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE`.",
        "",
        "## Claim Boundary Quick Reference",
        "",
        "- Gas-phase CFD claim: H2, CH4, and C3H8 gas sources can be selected when the compiled mechanism contains the species.",
        "- Liquid-release bridge claim: LNG_CH4 and LPG_C3H8 rupture screening can be converted to generated gas-source CSV/PeleLMeX inputs.",
        "- CFD-internal phase-change claim: not allowed for flashing discharge, liquid pool spread, or pool evaporation.",
        "- Generated LNG_CH4 and LPG_C3H8 source inputs have CUDA smoke evidence.",
        "",
        "## Fuel Selection",
        "",
        "Use `prob.fuel_species` to choose the gas-phase source species supported by the compiled chemistry mechanism.",
        "",
        "| Fuel or surrogate | Current evidence-backed status | Production claim | Primary input/report |",
        "|---|---|---|---|",
    ]
    for key, item in fuels.items():
        lines.append(
            f"| `{key}` | `{item['status']}` | `{item['production_claim']}` | `{item['primary_artifact']}` |"
        )
    lines += [
        "",
        "## Gasified LNG/LPG Inputs",
        "",
        "- `input.codex_gasified_lng_ch4_surrogate_smoke`: cold gasified LNG/CH4 source stability probe.",
        "- `input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step`: warmed gasified LNG/CH4 fire surrogate.",
        "- `input.codex_gasified_lpg_c3h8_surrogate_smoke`: gasified LPG/C3H8 fire surrogate.",
        "",
        "## External Vaporization Source Contract",
        "",
        "- `codex_lng_external_vaporization_source_template.csv`: template for an external vaporization model time series.",
        "- The external vaporization model supplies gas-phase source data; the CFD mapping uses `prob.leak_model = fixed_mass_flow`.",
        "- `input.codex_fixed_mass_flow_valve_schedule_smoke` verifies scheduled fixed gas-source ramping through `fixed_mass_flow_scheduled`.",
        "- `input.codex_fixed_mass_flow_timeseries_smoke` verifies external `mdot(t)`, `vapor_T(t)`, `velocity(t)`, and single-source `radius/location(t)` coupling through `prob.leak_schedule_times`, `prob.leak_schedule_rates`, `prob.leak_schedule_temperatures`, `prob.leak_schedule_vel_x`, `prob.leak_schedule_vel_y`, `prob.leak_schedule_vel_z`, `prob.leak_schedule_radius`, `prob.leak_schedule_x`, `prob.leak_schedule_y`, `prob.leak_schedule_z`, and `fixed_mass_flow_timeseries`.",
        "- `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA` verifies the same external vaporization time-series source path on a single Tesla P100 CUDA run using CUDA 12.6 and CUDA-enabled SUNDIALS.",
        "- `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX` verifies generated external vaporization `mdot(t)` source inputs for `H2`, `CH4`, and `C3H8`; CH4/C3H8 runtime evidence remains gas-phase surrogate evidence, not liquid LNG/LPG phase-change validation.",
        "- `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-C3H8-TIMESERIES-CUDA` verifies a rebuilt `propane_fc` CUDA executable reads the generated `C3H8` external vaporization time-series source, builds the pipe-rack STL EB geometry, and completes a single-GPU runtime probe without unused `prob.leak_schedule_*` parameters.",
        "- `cfd_solves_liquid_phase_change = false`",
        "- `cfd_solves_flashing_discharge = false`",
        "- `cfd_solves_pool_spread_evaporation = false`",
        "- External source negative cases refused: negative mass flow, unknown species, nonmonotonic time, missing required columns, mixed species, and negative sample time.",
        "",
        "## Boundaries",
        "",
        "- `lng_lpg_production_phase_change_claim_allowed = false`",
        "- Not implemented: liquid tank rupture mechanics.",
        "- Not implemented: flashing two-phase discharge.",
        "- Not implemented: liquid pool spread and evaporation.",
        "- Not implemented: cryogenic ground/wall heat-transfer closure.",
        "",
        "## Evidence Reports",
        "",
    ]
    for label, report in reports.items():
        lines.append(f"- `{label}`: `{report}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report() -> dict[str, Any]:
    multi = load_json(MULTI_FUEL_BOUNDARY)
    gasified = load_json(GASIFIED_SURROGATE)
    liquefied_contract = load_json(LIQUEFIED_EXTERNAL_VAPORIZATION_CONTRACT)
    liquefied_source_model = load_json(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL)
    liquefied_source_model_negative = load_json(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_NEGATIVE_SELFTEST)
    liquefied_source_model_cuda_smoke = load_json(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_CUDA_SMOKE)
    liquefied_negative = load_json(LIQUEFIED_EXTERNAL_VAPORIZATION_NEGATIVE_SELFTEST)
    fixed_schedule = load_json(FIXED_MASS_FLOW_VALVE_SCHEDULE)
    external_timeseries = load_json(EXTERNAL_VAPORIZATION_TIMESERIES)
    external_timeseries_cuda = load_json(EXTERNAL_VAPORIZATION_TIMESERIES_CUDA)
    external_multifuel = load_json(EXTERNAL_VAPORIZATION_MULTIFUEL_SOURCE_MATRIX)
    c3h8_external_timeseries_cuda = load_json(C3H8_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA)
    c3h8 = load_json(C3H8_REPORT)
    ch4 = load_json(CH4_500STEP_REPORT)
    h2 = load_json(H2_PRODUCTION_REPORT)

    require(multi.get("status") == "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY", "multi-fuel boundary is not passing")
    require(gasified.get("status") == "PASS-ENGINEERING-GASIFIED-LNG-LPG-SURROGATE-BOUNDARY", "gasified surrogate report is not passing")
    require(
        liquefied_contract.get("status") == "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT",
        "liquefied external vaporization contract is not passing",
    )
    require(
        liquefied_source_model.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL",
        "liquefied release vaporization source model is not passing",
    )
    require(
        liquefied_source_model_negative.get("status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST",
        "liquefied release vaporization source model negative selftest is not passing",
    )
    require(
        liquefied_source_model_cuda_smoke.get("status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE",
        "liquefied release vaporization source model CUDA smoke is not passing",
    )
    require(
        liquefied_negative.get("status") == "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-NEGATIVE-SELFTEST",
        "liquefied external vaporization negative selftest is not passing",
    )
    require(
        fixed_schedule.get("status") == "PASS-ENGINEERING-FIXED-MASS-FLOW-VALVE-SCHEDULE",
        "fixed-mass-flow valve schedule is not passing",
    )
    require(
        external_timeseries.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES",
        "external vaporization time series is not passing",
    )
    require(
        external_timeseries_cuda.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA",
        "external vaporization CUDA time series is not passing",
    )
    require(
        external_multifuel.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX",
        "external vaporization multi-fuel source matrix is not passing",
    )
    require(
        c3h8_external_timeseries_cuda.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-C3H8-TIMESERIES-CUDA",
        "C3H8 external vaporization CUDA time-series runtime report is not passing",
    )
    require(c3h8.get("status") == "PASS-ENGINEERING-C3H8-GAS-PHASE-CPU-CPU-MPI-SINGLE-CUDA-MPI-CUDA", "C3H8 matrix is not passing")
    require(ch4.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP", "CH4 500-step MPI+CUDA fire report is not passing")
    require(h2.get("status") == "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-GPU-PARITY", "H2 cross-platform fire report is not passing")

    gasified_summary = gasified.get("summary", {})
    liquefied_summary = liquefied_contract.get("summary", {})
    liquefied_source_model_summary = liquefied_source_model.get("summary", {})
    liquefied_source_model_negative_summary = liquefied_source_model_negative.get("summary", {})
    liquefied_source_model_cuda_smoke_summary = liquefied_source_model_cuda_smoke.get("summary", {})
    liquefied_negative_summary = liquefied_negative.get("summary", {})
    fixed_schedule_summary = fixed_schedule.get("summary", {})
    external_timeseries_summary = external_timeseries.get("summary", {})
    external_timeseries_cuda_summary = external_timeseries_cuda.get("summary", {})
    external_multifuel_summary = external_multifuel.get("summary", {})
    c3h8_external_timeseries_cuda_summary = c3h8_external_timeseries_cuda.get("summary", {})
    require(gasified_summary.get("gasified_lng_ch4_cold_source_sustained_fire_claim_allowed") is False, "cold LNG source must not claim sustained fire")
    require(gasified_summary.get("gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed") is True, "warmed LNG fire surrogate missing")
    require(gasified_summary.get("lng_lpg_production_phase_change_claim_allowed") is False, "phase-change production claim must be false")
    require(liquefied_summary.get("external_vaporization_contract_ready") is True, "external vaporization contract not ready")
    require(liquefied_summary.get("cfd_solves_liquid_phase_change") is False, "external vaporization contract must not claim liquid phase change")
    require(liquefied_source_model_summary.get("liquefied_release_vaporization_source_model_ready") is True, "liquefied release vaporization source model not ready")
    require(liquefied_source_model_summary.get("lng_ch4_screening_release_source_ready") is True, "LNG CH4 screening release source not ready")
    require(liquefied_source_model_summary.get("lpg_c3h8_screening_release_source_ready") is True, "LPG C3H8 screening release source not ready")
    require(liquefied_source_model_summary.get("outputs_external_vaporization_csv") is True, "liquefied release source model did not output CSV")
    require(liquefied_source_model_summary.get("outputs_pelelmex_fixed_mass_flow_schedule_input") is True, "liquefied release source model did not output PeleLMeX input")
    require(liquefied_source_model_summary.get("cfd_solves_liquid_phase_change") is False, "liquefied source model must not claim liquid phase change")
    require(liquefied_source_model_negative_summary.get("negative_selftest_ready") is True, "liquefied source model negative selftest not ready")
    require(
        liquefied_source_model_negative_summary.get("negative_refused_count")
        == liquefied_source_model_negative_summary.get("negative_case_count"),
        "not all bad liquefied source-model inputs were refused",
    )
    require(
        liquefied_source_model_cuda_smoke_summary.get("liquefied_release_source_model_cuda_smoke_ready") is True,
        "liquefied source model CUDA smoke not ready",
    )
    require(
        liquefied_source_model_cuda_smoke_summary.get("lng_ch4_generated_input_cuda_smoke_passed") is True,
        "LNG CH4 generated input CUDA smoke missing",
    )
    require(
        liquefied_source_model_cuda_smoke_summary.get("lpg_c3h8_generated_input_cuda_smoke_passed") is True,
        "LPG C3H8 generated input CUDA smoke missing",
    )
    require(
        liquefied_source_model_cuda_smoke_summary.get("cfd_solves_liquid_phase_change") is False,
        "liquefied source model CUDA smoke must not claim liquid phase change",
    )
    require(liquefied_negative_summary.get("negative_selftest_ready") is True, "external vaporization negative selftest not ready")
    require(liquefied_negative_summary.get("negative_refused_count") == liquefied_negative_summary.get("negative_case_count"), "not all bad external vaporization inputs were refused")
    require(fixed_schedule_summary.get("fixed_mass_flow_valve_schedule_ready") is True, "fixed-mass-flow valve schedule not ready")
    require(fixed_schedule_summary.get("effective_mdot_varies") is True, "fixed-mass-flow schedule did not vary mdot")
    require(external_timeseries_summary.get("external_vaporization_timeseries_ready") is True, "external vaporization time series not ready")
    require(external_timeseries_summary.get("scheduled_reference_mdot_varies") is True, "external vaporization mdot(t) did not vary")
    require(external_timeseries_summary.get("scheduled_leak_T_varies") is True, "external vaporization vapor_T(t) did not vary")
    require(external_timeseries_summary.get("scheduled_velocity_x_varies") is True, "external vaporization velocity(t) did not vary")
    require(external_timeseries_summary.get("scheduled_radius_varies") is True, "external vaporization radius(t) did not vary")
    require(external_timeseries_summary.get("scheduled_center_x_varies") is True, "external vaporization location(t) did not vary")
    require(external_timeseries_cuda_summary.get("external_vaporization_timeseries_cuda_ready") is True, "external vaporization CUDA time series not ready")
    require(external_timeseries_cuda_summary.get("environment_uses_cuda_12_6") is True, "external vaporization CUDA environment was not CUDA 12.6")
    require(external_timeseries_cuda_summary.get("scheduled_reference_mdot_varies") is True, "external vaporization CUDA mdot(t) did not vary")
    require(external_timeseries_cuda_summary.get("scheduled_leak_T_varies") is True, "external vaporization CUDA vapor_T(t) did not vary")
    require(external_timeseries_cuda_summary.get("scheduled_velocity_x_varies") is True, "external vaporization CUDA velocity(t) did not vary")
    require(external_timeseries_cuda_summary.get("scheduled_radius_varies") is True, "external vaporization CUDA radius(t) did not vary")
    require(external_timeseries_cuda_summary.get("scheduled_center_x_varies") is True, "external vaporization CUDA location(t) did not vary")
    require(external_multifuel_summary.get("external_vaporization_multifuel_source_matrix_ready") is True, "external vaporization multi-fuel source matrix not ready")
    require(external_multifuel_summary.get("supported_species") == ["C3H8", "CH4", "H2"], "external vaporization multi-fuel supported species changed")
    require(external_multifuel_summary.get("phase_change_not_claimed") is True, "external vaporization multi-fuel source matrix overclaims phase change")
    require(c3h8_external_timeseries_cuda_summary.get("external_vaporization_c3h8_timeseries_cuda_ready") is True, "C3H8 external vaporization CUDA runtime not ready")
    require(c3h8_external_timeseries_cuda_summary.get("fuel_species_c3h8_selected") is True, "C3H8 external vaporization CUDA did not select C3H8")
    require(c3h8_external_timeseries_cuda_summary.get("leak_schedule_unused") is False, "C3H8 external vaporization CUDA schedule was unused")

    for path in REQUIRED_INPUTS.values():
        require(path.is_file(), f"missing operator input: {path}")
    for path in REQUIRED_TOOLS:
        require(path.is_file(), f"missing operator tool: {path}")

    fuels = {
        "H2": {
            "status": "current engineering production-scope gas leak/diffusion/fire ready",
            "production_claim": "allowed for current H2 scope",
            "primary_artifact": str(H2_PRODUCTION_REPORT),
        },
        "CH4": {
            "status": "gas-phase natural-gas surrogate fire evidence exists through 500-step MPI+CUDA",
            "production_claim": "not natural-gas production validated",
            "primary_artifact": str(CH4_500STEP_REPORT),
        },
        "C3H8": {
            "status": "gas-phase propane/LPG surrogate fire evidence exists through CPU/CPU-MPI/single-CUDA/MPI-CUDA",
            "production_claim": "not propane production validated",
            "primary_artifact": str(C3H8_REPORT),
        },
        "gasified LNG": {
            "status": "cold CH4 source stable; warmed CH4 fire surrogate passes 500-step MPI+CUDA",
            "production_claim": "not cryogenic LNG production validated",
            "primary_artifact": str(GASIFIED_SURROGATE),
        },
        "gasified LPG": {
            "status": "C3H8 gasified LPG fire surrogate passes 120-step MPI+CUDA",
            "production_claim": "not liquid LPG rupture/phase-change validated",
            "primary_artifact": str(GASIFIED_SURROGATE),
        },
        "liquefied gas rupture/flash/pool evaporation": {
            "status": "not implemented internally; screening rupture-to-gas-source generator and external gas-phase vaporization source contract exist",
            "production_claim": "not allowed for CFD-internal phase change",
            "primary_artifact": str(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL),
        },
    }
    reports = {
        "multi_fuel_boundary": str(MULTI_FUEL_BOUNDARY),
        "gasified_lng_lpg_surrogate": str(GASIFIED_SURROGATE),
        "liquefied_external_vaporization_contract": str(LIQUEFIED_EXTERNAL_VAPORIZATION_CONTRACT),
        "liquefied_release_vaporization_source_model": str(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL),
        "liquefied_release_vaporization_source_model_negative_selftest": str(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_NEGATIVE_SELFTEST),
        "liquefied_release_vaporization_source_model_cuda_smoke": str(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_CUDA_SMOKE),
        "liquefied_external_vaporization_negative_selftest": str(LIQUEFIED_EXTERNAL_VAPORIZATION_NEGATIVE_SELFTEST),
        "fixed_mass_flow_valve_schedule": str(FIXED_MASS_FLOW_VALVE_SCHEDULE),
        "external_vaporization_timeseries": str(EXTERNAL_VAPORIZATION_TIMESERIES),
        "external_vaporization_timeseries_cuda": str(EXTERNAL_VAPORIZATION_TIMESERIES_CUDA),
        "external_vaporization_multifuel_source_matrix": str(EXTERNAL_VAPORIZATION_MULTIFUEL_SOURCE_MATRIX),
        "c3h8_external_vaporization_timeseries_cuda": str(C3H8_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA),
        "c3h8_matrix": str(C3H8_REPORT),
        "ch4_500step_mpi_cuda_fire": str(CH4_500STEP_REPORT),
        "h2_cross_platform": str(H2_PRODUCTION_REPORT),
    }
    write_runbook(RUNBOOK, fuels, reports)
    runbook_text = RUNBOOK.read_text(encoding="utf-8")
    missing_snippets = [snippet for snippet in REQUIRED_RUNBOOK_SNIPPETS if snippet not in runbook_text]
    ready = not missing_snippets

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-MULTI-FUEL-OPERATOR-RUNBOOK",
        "summary": {
            "operator_runbook_ready": ready,
            "fuel_count": len(fuels),
            "gasified_lng_warmed_fire_surrogate_passed": gasified_summary.get("gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed") is True,
            "gasified_lpg_fire_surrogate_passed": gasified_summary.get("gasified_lpg_c3h8_surrogate_fire_probe_passed") is True,
            "lng_lpg_phase_change_production_claim_allowed": gasified_summary.get("lng_lpg_production_phase_change_claim_allowed") is True,
            "prevents_phase_change_overclaim": gasified_summary.get("prevents_liquid_phase_overclaim") is True,
            "liquefied_external_vaporization_contract_ready": liquefied_summary.get("external_vaporization_contract_ready") is True,
            "liquefied_release_vaporization_source_model_ready": liquefied_source_model_summary.get("liquefied_release_vaporization_source_model_ready") is True,
            "liquefied_release_vaporization_source_model_outputs_csv": liquefied_source_model_summary.get("outputs_external_vaporization_csv") is True,
            "liquefied_release_vaporization_source_model_outputs_pelelmex_input": liquefied_source_model_summary.get("outputs_pelelmex_fixed_mass_flow_schedule_input") is True,
            "liquefied_release_vaporization_source_model_production_phase_change_claim_allowed": liquefied_source_model_summary.get("production_phase_change_claim_allowed") is True,
            "liquefied_release_vaporization_source_model_negative_selftest_ready": liquefied_source_model_negative_summary.get("negative_selftest_ready") is True,
            "liquefied_release_vaporization_source_model_negative_cases_refused": liquefied_source_model_negative_summary.get("negative_refused_count"),
            "liquefied_release_vaporization_source_model_cuda_smoke_ready": liquefied_source_model_cuda_smoke_summary.get("liquefied_release_source_model_cuda_smoke_ready") is True,
            "liquefied_release_vaporization_source_model_lng_ch4_cuda_smoke_passed": liquefied_source_model_cuda_smoke_summary.get("lng_ch4_generated_input_cuda_smoke_passed") is True,
            "liquefied_release_vaporization_source_model_lpg_c3h8_cuda_smoke_passed": liquefied_source_model_cuda_smoke_summary.get("lpg_c3h8_generated_input_cuda_smoke_passed") is True,
            "liquefied_external_vaporization_negative_selftest_ready": liquefied_negative_summary.get("negative_selftest_ready") is True,
            "liquefied_external_vaporization_negative_cases_refused": liquefied_negative_summary.get("negative_refused_count"),
            "fixed_mass_flow_valve_schedule_ready": fixed_schedule_summary.get("fixed_mass_flow_valve_schedule_ready") is True,
            "fixed_mass_flow_effective_mdot_varies": fixed_schedule_summary.get("effective_mdot_varies") is True,
            "external_vaporization_timeseries_ready": external_timeseries_summary.get("external_vaporization_timeseries_ready") is True,
            "external_vaporization_timeseries_mdot_varies": external_timeseries_summary.get("scheduled_reference_mdot_varies") is True,
            "external_vaporization_timeseries_temperature_varies": external_timeseries_summary.get("scheduled_leak_T_varies") is True,
            "external_vaporization_timeseries_velocity_varies": external_timeseries_summary.get("scheduled_velocity_x_varies") is True,
            "external_vaporization_timeseries_radius_varies": external_timeseries_summary.get("scheduled_radius_varies") is True,
            "external_vaporization_timeseries_location_varies": external_timeseries_summary.get("scheduled_center_x_varies") is True,
            "external_vaporization_timeseries_cuda_ready": external_timeseries_cuda_summary.get("external_vaporization_timeseries_cuda_ready") is True,
            "external_vaporization_timeseries_cuda_uses_cuda_12_6": external_timeseries_cuda_summary.get("environment_uses_cuda_12_6") is True,
            "external_vaporization_timeseries_cuda_mdot_varies": external_timeseries_cuda_summary.get("scheduled_reference_mdot_varies") is True,
            "external_vaporization_timeseries_cuda_temperature_varies": external_timeseries_cuda_summary.get("scheduled_leak_T_varies") is True,
            "external_vaporization_timeseries_cuda_velocity_varies": external_timeseries_cuda_summary.get("scheduled_velocity_x_varies") is True,
            "external_vaporization_timeseries_cuda_radius_varies": external_timeseries_cuda_summary.get("scheduled_radius_varies") is True,
            "external_vaporization_timeseries_cuda_location_varies": external_timeseries_cuda_summary.get("scheduled_center_x_varies") is True,
            "external_vaporization_multifuel_source_matrix_ready": external_multifuel_summary.get("external_vaporization_multifuel_source_matrix_ready") is True,
            "external_vaporization_multifuel_supported_species": external_multifuel_summary.get("supported_species"),
            "external_vaporization_multifuel_phase_change_not_claimed": external_multifuel_summary.get("phase_change_not_claimed") is True,
            "c3h8_external_vaporization_timeseries_cuda_ready": c3h8_external_timeseries_cuda_summary.get("external_vaporization_c3h8_timeseries_cuda_ready") is True,
            "c3h8_external_vaporization_timeseries_cuda_fuel_species_selected": c3h8_external_timeseries_cuda_summary.get("fuel_species_c3h8_selected") is True,
            "c3h8_external_vaporization_timeseries_cuda_leak_schedule_unused": c3h8_external_timeseries_cuda_summary.get("leak_schedule_unused") is True,
            "cfd_internal_liquid_phase_change_claim_allowed": liquefied_summary.get("cfd_solves_liquid_phase_change") is True,
            "missing_runbook_snippet_count": len(missing_snippets),
        },
        "fuels": fuels,
        "reports": reports,
        "findings": {"missing_runbook_snippets": missing_snippets},
        "evidence_files": [
            evidence_entry("operator_runbook", RUNBOOK),
            evidence_entry("multi_fuel_boundary", MULTI_FUEL_BOUNDARY),
            evidence_entry("gasified_lng_lpg_surrogate", GASIFIED_SURROGATE),
            evidence_entry("liquefied_external_vaporization_contract", LIQUEFIED_EXTERNAL_VAPORIZATION_CONTRACT),
            evidence_entry("liquefied_release_vaporization_source_model", LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL),
            evidence_entry("liquefied_release_vaporization_source_model_negative_selftest", LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_NEGATIVE_SELFTEST),
            evidence_entry("liquefied_release_vaporization_source_model_cuda_smoke", LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_CUDA_SMOKE),
            evidence_entry("liquefied_external_vaporization_negative_selftest", LIQUEFIED_EXTERNAL_VAPORIZATION_NEGATIVE_SELFTEST),
            evidence_entry("fixed_mass_flow_valve_schedule", FIXED_MASS_FLOW_VALVE_SCHEDULE),
            evidence_entry("external_vaporization_timeseries", EXTERNAL_VAPORIZATION_TIMESERIES),
            evidence_entry("external_vaporization_timeseries_cuda", EXTERNAL_VAPORIZATION_TIMESERIES_CUDA),
            evidence_entry("external_vaporization_multifuel_source_matrix", EXTERNAL_VAPORIZATION_MULTIFUEL_SOURCE_MATRIX),
            evidence_entry("c3h8_external_vaporization_timeseries_cuda", C3H8_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA),
            evidence_entry("c3h8_matrix", C3H8_REPORT),
            evidence_entry("ch4_500step_mpi_cuda_fire", CH4_500STEP_REPORT),
            evidence_entry("h2_production", H2_PRODUCTION_REPORT),
            *[evidence_entry(label, path) for label, path in REQUIRED_INPUTS.items()],
            *[evidence_entry(path.name, path) for path in REQUIRED_TOOLS],
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "operator runbook status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("operator_runbook_ready") is True, "operator runbook not ready")
    require(summary.get("fuel_count") == 6, "unexpected fuel count")
    require(summary.get("gasified_lng_warmed_fire_surrogate_passed") is True, "LNG warmed fire surrogate missing")
    require(summary.get("gasified_lpg_fire_surrogate_passed") is True, "LPG fire surrogate missing")
    require(summary.get("lng_lpg_phase_change_production_claim_allowed") is False, "phase-change claim must remain false")
    require(summary.get("prevents_phase_change_overclaim") is True, "phase-change overclaim guard missing")
    require(summary.get("liquefied_external_vaporization_contract_ready") is True, "external vaporization contract missing")
    require(summary.get("liquefied_release_vaporization_source_model_ready") is True, "liquefied release vaporization source model missing")
    require(summary.get("liquefied_release_vaporization_source_model_outputs_csv") is True, "liquefied release source model CSV output missing")
    require(summary.get("liquefied_release_vaporization_source_model_outputs_pelelmex_input") is True, "liquefied release source model PeleLMeX input output missing")
    require(
        summary.get("liquefied_release_vaporization_source_model_production_phase_change_claim_allowed") is False,
        "liquefied release source model must not allow production phase-change claim",
    )
    require(
        summary.get("liquefied_release_vaporization_source_model_negative_selftest_ready") is True,
        "liquefied release source model negative selftest missing",
    )
    require(
        summary.get("liquefied_release_vaporization_source_model_negative_cases_refused") == 13,
        "liquefied release source model negative case coverage changed",
    )
    require(
        summary.get("liquefied_release_vaporization_source_model_cuda_smoke_ready") is True,
        "liquefied release source model CUDA smoke missing",
    )
    require(
        summary.get("liquefied_release_vaporization_source_model_lng_ch4_cuda_smoke_passed") is True,
        "LNG CH4 generated input CUDA smoke missing",
    )
    require(
        summary.get("liquefied_release_vaporization_source_model_lpg_c3h8_cuda_smoke_passed") is True,
        "LPG C3H8 generated input CUDA smoke missing",
    )
    require(summary.get("liquefied_external_vaporization_negative_selftest_ready") is True, "external vaporization negative selftest missing")
    require(summary.get("liquefied_external_vaporization_negative_cases_refused") == 11, "external vaporization negative case coverage changed")
    require(summary.get("fixed_mass_flow_valve_schedule_ready") is True, "fixed-mass-flow valve schedule missing")
    require(summary.get("fixed_mass_flow_effective_mdot_varies") is True, "fixed-mass-flow schedule did not vary mdot")
    require(summary.get("external_vaporization_timeseries_ready") is True, "external vaporization time series missing")
    require(summary.get("external_vaporization_timeseries_mdot_varies") is True, "external vaporization mdot(t) did not vary")
    require(summary.get("external_vaporization_timeseries_temperature_varies") is True, "external vaporization vapor_T(t) did not vary")
    require(summary.get("external_vaporization_timeseries_velocity_varies") is True, "external vaporization velocity(t) did not vary")
    require(summary.get("external_vaporization_timeseries_radius_varies") is True, "external vaporization radius(t) did not vary")
    require(summary.get("external_vaporization_timeseries_location_varies") is True, "external vaporization location(t) did not vary")
    require(summary.get("external_vaporization_timeseries_cuda_ready") is True, "external vaporization CUDA time series missing")
    require(summary.get("external_vaporization_timeseries_cuda_uses_cuda_12_6") is True, "external vaporization CUDA 12.6 evidence missing")
    require(summary.get("external_vaporization_timeseries_cuda_mdot_varies") is True, "external vaporization CUDA mdot(t) did not vary")
    require(summary.get("external_vaporization_timeseries_cuda_temperature_varies") is True, "external vaporization CUDA vapor_T(t) did not vary")
    require(summary.get("external_vaporization_timeseries_cuda_velocity_varies") is True, "external vaporization CUDA velocity(t) did not vary")
    require(summary.get("external_vaporization_timeseries_cuda_radius_varies") is True, "external vaporization CUDA radius(t) did not vary")
    require(summary.get("external_vaporization_timeseries_cuda_location_varies") is True, "external vaporization CUDA location(t) did not vary")
    require(summary.get("external_vaporization_multifuel_source_matrix_ready") is True, "external vaporization multi-fuel source matrix missing")
    require(summary.get("external_vaporization_multifuel_supported_species") == ["C3H8", "CH4", "H2"], "external vaporization supported species changed")
    require(summary.get("external_vaporization_multifuel_phase_change_not_claimed") is True, "external vaporization multi-fuel matrix overclaims phase change")
    require(summary.get("c3h8_external_vaporization_timeseries_cuda_ready") is True, "C3H8 external vaporization CUDA time-series runtime missing")
    require(summary.get("c3h8_external_vaporization_timeseries_cuda_fuel_species_selected") is True, "C3H8 external vaporization CUDA fuel selection missing")
    require(summary.get("c3h8_external_vaporization_timeseries_cuda_leak_schedule_unused") is False, "C3H8 external vaporization CUDA schedule was unused")
    require(summary.get("cfd_internal_liquid_phase_change_claim_allowed") is False, "CFD-internal liquid phase-change claim must remain false")
    require(summary.get("missing_runbook_snippet_count") == 0, "runbook snippets missing")
    fuels = data.get("fuels")
    require(isinstance(fuels, dict), "fuels missing")
    require(
        "not implemented internally" in fuels["liquefied gas rupture/flash/pool evaporation"]["status"],
        "phase-change boundary drifted",
    )
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Engineering Multi-Fuel Operator Runbook Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Fuel entries: `{report['summary']['fuel_count']}`",
        f"- LNG warmed fire surrogate passed: `{report['summary']['gasified_lng_warmed_fire_surrogate_passed']}`",
        f"- LPG fire surrogate passed: `{report['summary']['gasified_lpg_fire_surrogate_passed']}`",
        f"- LNG/LPG phase-change production claim allowed: `{report['summary']['lng_lpg_phase_change_production_claim_allowed']}`",
        f"- External vaporization source contract ready: `{report['summary']['liquefied_external_vaporization_contract_ready']}`",
        f"- Liquefied release vaporization source model ready: `{report['summary']['liquefied_release_vaporization_source_model_ready']}`",
        f"- Liquefied release source model outputs CSV: `{report['summary']['liquefied_release_vaporization_source_model_outputs_csv']}`",
        f"- Liquefied release source model outputs PeleLMeX input: `{report['summary']['liquefied_release_vaporization_source_model_outputs_pelelmex_input']}`",
        f"- Liquefied release source model negative cases refused: `{report['summary']['liquefied_release_vaporization_source_model_negative_cases_refused']}`",
        f"- Liquefied release source model CUDA smoke ready: `{report['summary']['liquefied_release_vaporization_source_model_cuda_smoke_ready']}`",
        f"- External vaporization negative cases refused: `{report['summary']['liquefied_external_vaporization_negative_cases_refused']}`",
        f"- Fixed-mass-flow valve schedule ready: `{report['summary']['fixed_mass_flow_valve_schedule_ready']}`",
        f"- External vaporization time series ready: `{report['summary']['external_vaporization_timeseries_ready']}`",
        f"- External vaporization time series CUDA ready: `{report['summary']['external_vaporization_timeseries_cuda_ready']}`",
        f"- External vaporization multi-fuel source matrix ready: `{report['summary']['external_vaporization_multifuel_source_matrix_ready']}`",
        f"- C3H8 external vaporization time series CUDA ready: `{report['summary']['c3h8_external_vaporization_timeseries_cuda_ready']}`",
        f"- CFD-internal liquid phase-change claim allowed: `{report['summary']['cfd_internal_liquid_phase_change_claim_allowed']}`",
        "",
        "## Runbook",
        "",
        f"- `{RUNBOOK}`",
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
            print(f"engineering_multi_fuel_operator_runbook VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_multi_fuel_operator_runbook PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (RunbookError, OSError, json.JSONDecodeError) as exc:
        print(f"engineering_multi_fuel_operator_runbook FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
