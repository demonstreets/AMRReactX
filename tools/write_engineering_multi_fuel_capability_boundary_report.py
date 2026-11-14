#!/usr/bin/env python3
"""Write/verify the engineering multi-fuel and liquefied-gas capability boundary audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_multi_fuel_capability_boundary_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_multi_fuel_capability_boundary_report.md"

PROB_H = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
PROB_CPP = Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")
GNUMAKE = Path("examples/engineering/h2_leak_3d/GNUmakefile")
SCENARIO_MATRIX = Path(
    "docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805/"
    "current_scenario_readiness_matrix_report.json"
)
PROBE_ROOT = Path("docs/codex_audit/evidence/engineering_multi_fuel_source_probe_20260806")
H2_PROBE_RUN_LOG = PROBE_ROOT / "h2_default_fuel_species_run.log"
H2_PROBE_VALIDATION_LOG = PROBE_ROOT / "h2_default_fuel_species_validation.log"
CH4_PROBE_BUILD_LOG = PROBE_ROOT / "ch4_fuel_species_build.log"
CH4_PROBE_RUN_LOG = PROBE_ROOT / "ch4_fuel_species_run.log"
CH4_COLD_PLUME_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_cold_plume_cpu_probe_20260806/"
    "engineering_ch4_cold_plume_cpu_probe_report.json"
)
CH4_FIRE_CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_cuda_20260806/"
    "engineering_ch4_pipe_rack_delayed_ignition_cuda_report.json"
)
CH4_FIRE_MPI_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_20260806/"
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_report.json"
)
CH4_FIRE_MPI_CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_20260806/"
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.json"
)
CH4_FIRE_MPI_CUDA_500STEP_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/"
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json"
)
C3H8_GAS_PHASE_CPU_CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/"
    "engineering_c3h8_gas_phase_cpu_cuda_report.json"
)
GASIFIED_LNG_LPG_SURROGATE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/"
    "engineering_gasified_lng_lpg_surrogate_report.json"
)
CH4_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/"
    "ch4_timeseries_cuda/engineering_external_vaporization_ch4_timeseries_cuda_report.json"
)
C3H8_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/"
    "c3h8_timeseries_cuda/engineering_external_vaporization_c3h8_timeseries_cuda_report.json"
)
LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
    "engineering_liquefied_release_vaporization_source_model_report.json"
)
LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_NEGATIVE_SELFTEST_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/"
    "engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json"
)
LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_CUDA_SMOKE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/"
    "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"
)
LIQUEFIED_RELEASE_SOURCE_BALANCE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/"
    "engineering_liquefied_release_source_balance_report.json"
)
LIQUEFIED_RELEASE_SOURCE_BALANCE_NEGATIVE_SELFTEST_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/"
    "engineering_liquefied_release_source_balance_negative_selftest_report.json"
)
MECH_ROOT = Path("external/PeleLMeX/Submodules/PelePhysics/Mechanisms")

METHANE_MECHANISMS = ["CH4_lean", "grimech30", "grimech30-noArN", "drm19", "chem-CH4-2step"]
PROPANE_MECHANISMS = ["c3h8_mini", "C3MechLite", "propane_fc", "POLIMI2020"]
LIQUID_FUEL_MECHANISMS = ["liquid_fuels_nonreacting", "fuellib_posf_nonreacting"]


class CapabilityBoundaryError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CapabilityBoundaryError(message)


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
        raise CapabilityBoundaryError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CapabilityBoundaryError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def grep_count(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text))


def available_mechanisms(names: list[str]) -> list[str]:
    return [name for name in names if (MECH_ROOT / name).is_dir()]


def read_mechanism_model(make_text: str) -> str:
    match = re.search(r"^\s*Chemistry_Model\s*=\s*([A-Za-z0-9_.+-]+)\s*$", make_text, re.MULTILINE)
    return match.group(1) if match else ""


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    prob_h = PROB_H.read_text(encoding="utf-8", errors="replace")
    prob_cpp = PROB_CPP.read_text(encoding="utf-8", errors="replace")
    make_text = GNUMAKE.read_text(encoding="utf-8", errors="replace")
    matrix = load_json(SCENARIO_MATRIX)

    engineering = matrix.get("scenarios", {}).get("engineering_h2_leak_diffusion_fire", {})
    require(isinstance(engineering, dict), "engineering scenario matrix entry missing")

    chemistry_model = read_mechanism_model(make_text)
    h2_specific_markers = {
        "H2_ID": grep_count(prob_h + prob_cpp, r"\bH2_ID\b"),
        "cloud_YH2": grep_count(prob_h + prob_cpp, r"\bcloud_YH2\b"),
        "species_equals_H2_log": grep_count(prob_h + prob_cpp, r"species=H2"),
        "h2_named_abort_or_log": grep_count(prob_h + prob_cpp, r"H2 leak|configured H2|H2 delayed"),
        "lidryer_makefile": 1 if chemistry_model == "LiDryer" else 0,
    }
    source_fuel_species_configurable = (
        "fuel_species_index" in prob_h
        and "CKSYMS_STR(species_names)" in prob_cpp
        and 'pp.query("fuel_species", fuel_species)' in prob_cpp
        and "source.species_index = pp->fuel_species_index" in prob_h
        and "mf[pp->fuel_species_index]=1.0" in prob_h
    )
    source_is_h2_specific = not source_fuel_species_configurable

    h2_probe_run = H2_PROBE_RUN_LOG.read_text(encoding="utf-8", errors="replace")
    h2_probe_validation = H2_PROBE_VALIDATION_LOG.read_text(encoding="utf-8", errors="replace")
    ch4_probe_build = CH4_PROBE_BUILD_LOG.read_text(encoding="utf-8", errors="replace")
    ch4_probe_run = CH4_PROBE_RUN_LOG.read_text(encoding="utf-8", errors="replace")
    h2_default_probe_passed = (
        "Engineering leak fuel species: name=H2, index=0" in h2_probe_run
        and "h2_leak_plume_history_validation PASS" in h2_probe_validation
        and "AMReX" in h2_probe_run
        and "finalized" in h2_probe_run
    )
    ch4_probe_passed = (
        "Mechanisms/CH4_lean" in ch4_probe_build
        and "Engineering leak fuel species: name=CH4, index=10" in ch4_probe_run
        and "AMReX" in ch4_probe_run
        and "finalized" in ch4_probe_run
        and not re.search(r"\bnan\b|Abort::|amrex::Abort", ch4_probe_run, re.IGNORECASE)
    )
    ch4_cold_plume = load_json(CH4_COLD_PLUME_REPORT)
    ch4_cold_summary = ch4_cold_plume.get("summary")
    require(isinstance(ch4_cold_summary, dict), "CH4 cold plume report summary missing")
    ch4_cpu_mpi_cuda_cold_plume_passed = (
        ch4_cold_plume.get("status") == "PASS-ENGINEERING-CH4-COLD-PLUME-CPU-MPI-CUDA-PROBE"
        and ch4_cold_summary.get("cpu_probe_passed") is True
        and ch4_cold_summary.get("cpu_mpi_probe_passed") is True
        and ch4_cold_summary.get("mpi_probe_passed") is True
        and int(ch4_cold_summary.get("mpi_rank_count", 0)) == 2
        and ch4_cold_summary.get("single_cuda_probe_passed") is True
        and ch4_cold_summary.get("production_ready") is False
    )
    ch4_fire_cuda = load_json(CH4_FIRE_CUDA_REPORT)
    ch4_fire_summary = ch4_fire_cuda.get("run_summary", {}).get("sustained_reaction_checks", {})
    require(isinstance(ch4_fire_summary, dict), "CH4 fire CUDA report sustained checks missing")
    ch4_delayed_ignition_single_cuda_passed = (
        ch4_fire_cuda.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA"
        and ch4_fire_cuda.get("validated_capabilities", {}).get("ch4_leak_source") is True
        and ch4_fire_cuda.get("validated_capabilities", {}).get("single_gpu_cuda") is True
        and ch4_fire_cuda.get("validated_capabilities", {}).get("sustained_post_ignition_fire_development") is True
        and int(ch4_fire_cuda.get("run_summary", {}).get("max_step", 0)) >= 120
        and float(ch4_fire_summary.get("final_y_h2o_max", 0.0)) > 1.0e-6
        and float(ch4_fire_summary.get("final_y_co2_max", 0.0)) > 1.0e-10
    )
    ch4_fire_mpi = load_json(CH4_FIRE_MPI_REPORT)
    ch4_fire_mpi_summary = ch4_fire_mpi.get("run_summary", {}).get("sustained_reaction_checks", {})
    require(isinstance(ch4_fire_mpi_summary, dict), "CH4 fire CPU/MPI report sustained checks missing")
    ch4_delayed_ignition_cpu_mpi_passed = (
        ch4_fire_mpi.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-CPU-MPI"
        and ch4_fire_mpi.get("validated_capabilities", {}).get("ch4_leak_source") is True
        and ch4_fire_mpi.get("validated_capabilities", {}).get("cpu_mpi_parallel") is True
        and ch4_fire_mpi.get("validated_capabilities", {}).get("sustained_post_ignition_fire_development") is True
        and int(ch4_fire_mpi.get("run_summary", {}).get("max_step", 0)) >= 120
        and int(ch4_fire_mpi.get("run_summary", {}).get("mpi_ranks", 0)) == 2
        and int(ch4_fire_mpi.get("run_summary", {}).get("cuda_devices", 1)) == 0
        and float(ch4_fire_mpi_summary.get("final_y_h2o_max", 0.0)) > 1.0e-6
        and float(ch4_fire_mpi_summary.get("final_y_co2_max", 0.0)) > 1.0e-10
    )
    ch4_fire_mpi_cuda = load_json(CH4_FIRE_MPI_CUDA_REPORT)
    ch4_fire_mpi_cuda_summary = ch4_fire_mpi_cuda.get("run_summary", {}).get("sustained_reaction_checks", {})
    require(isinstance(ch4_fire_mpi_cuda_summary, dict), "CH4 fire MPI+CUDA report sustained checks missing")
    ch4_delayed_ignition_mpi_cuda_passed = (
        ch4_fire_mpi_cuda.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA"
        and ch4_fire_mpi_cuda.get("validated_capabilities", {}).get("ch4_leak_source") is True
        and ch4_fire_mpi_cuda.get("validated_capabilities", {}).get("mpi_cuda_parallel") is True
        and ch4_fire_mpi_cuda.get("validated_capabilities", {}).get("rank_local_gpu_binding") is True
        and ch4_fire_mpi_cuda.get("validated_capabilities", {}).get("two_physical_gpus_used") is True
        and ch4_fire_mpi_cuda.get("validated_capabilities", {}).get("sustained_post_ignition_fire_development") is True
        and int(ch4_fire_mpi_cuda.get("run_summary", {}).get("max_step", 0)) >= 120
        and int(ch4_fire_mpi_cuda.get("run_summary", {}).get("mpi_ranks", 0)) == 2
        and int(ch4_fire_mpi_cuda.get("run_summary", {}).get("cuda_devices", 0)) == 2
        and float(ch4_fire_mpi_cuda_summary.get("final_y_h2o_max", 0.0)) > 1.0e-6
        and float(ch4_fire_mpi_cuda_summary.get("final_y_co2_max", 0.0)) > 1.0e-10
    )
    ch4_fire_mpi_cuda_500 = load_json(CH4_FIRE_MPI_CUDA_500STEP_REPORT)
    ch4_fire_mpi_cuda_500_summary = ch4_fire_mpi_cuda_500.get("run_summary", {}).get("sustained_reaction_checks", {})
    require(isinstance(ch4_fire_mpi_cuda_500_summary, dict), "CH4 fire MPI+CUDA 500-step report sustained checks missing")
    ch4_delayed_ignition_mpi_cuda_500_passed = (
        ch4_fire_mpi_cuda_500.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP"
        and ch4_fire_mpi_cuda_500.get("validated_capabilities", {}).get("rank_mapped_mpi_cuda_parallel") is True
        and ch4_fire_mpi_cuda_500.get("validated_capabilities", {}).get("two_physical_gpus_used") is True
        and ch4_fire_mpi_cuda_500.get("validated_capabilities", {}).get("longer_sustained_post_ignition_fire_development") is True
        and ch4_fire_mpi_cuda_500.get("validated_capabilities", {}).get("late_window_reactive_fire_maintained") is True
        and int(ch4_fire_mpi_cuda_500.get("run_summary", {}).get("max_step", 0)) >= 500
        and int(ch4_fire_mpi_cuda_500.get("run_summary", {}).get("mpi_ranks", 0)) == 2
        and int(ch4_fire_mpi_cuda_500.get("run_summary", {}).get("cuda_devices", 0)) == 2
        and int(ch4_fire_mpi_cuda_500_summary.get("sustained_output_count", 0)) >= 8
        and int(ch4_fire_mpi_cuda_500_summary.get("late_reactive_output_count", 0)) >= 4
        and float(ch4_fire_mpi_cuda_500_summary.get("peak_y_h2o_max", 0.0)) > 1.0e-4
        and float(ch4_fire_mpi_cuda_500_summary.get("final_heat_release_abs", 0.0)) > 1.0e5
    )
    c3h8_gas_phase = load_json(C3H8_GAS_PHASE_CPU_CUDA_REPORT)
    c3h8_summary = c3h8_gas_phase.get("summary")
    require(isinstance(c3h8_summary, dict), "C3H8 gas-phase CPU/MPI/CUDA report summary missing")
    c3h8_gas_phase_cpu_cuda_passed = (
        c3h8_gas_phase.get("status") == "PASS-ENGINEERING-C3H8-GAS-PHASE-CPU-CPU-MPI-SINGLE-CUDA-MPI-CUDA"
        and c3h8_summary.get("c3h8_cold_plume_cpu_passed") is True
        and c3h8_summary.get("c3h8_propane_fc_fire_cpu_passed") is True
        and c3h8_summary.get("c3h8_propane_fc_fire_cpu_mpi_passed") is True
        and c3h8_summary.get("c3h8_propane_fc_fire_cuda_passed") is True
        and c3h8_summary.get("c3h8_propane_fc_fire_mpi_cuda_passed") is True
        and c3h8_summary.get("c3h8_rank_mapped_two_gpu_mpi_cuda_passed") is True
        and c3h8_summary.get("propane_gas_phase_production_ready") is False
        and c3h8_summary.get("liquefied_propane_or_lpg_phase_change_ready") is False
        and float(c3h8_gas_phase.get("cpu_fire", {}).get("peak_temperature", 0.0)) > 2000.0
        and float(c3h8_gas_phase.get("cuda_fire", {}).get("peak_temperature", 0.0)) > 2000.0
        and float(c3h8_gas_phase.get("cpu_fire", {}).get("final_y_h2o_max", 0.0)) > 1.0e-6
        and float(c3h8_gas_phase.get("mpi_fire", {}).get("peak_temperature", 0.0)) > 2000.0
        and float(c3h8_gas_phase.get("mpi_fire", {}).get("final_y_h2o_max", 0.0)) > 1.0e-6
        and float(c3h8_gas_phase.get("cuda_fire", {}).get("final_y_h2o_max", 0.0)) > 1.0e-6
        and float(c3h8_gas_phase.get("mpicuda_fire", {}).get("peak_temperature", 0.0)) > 2000.0
        and float(c3h8_gas_phase.get("mpicuda_fire", {}).get("final_y_h2o_max", 0.0)) > 1.0e-6
    )
    gasified_surrogate = load_json(GASIFIED_LNG_LPG_SURROGATE_REPORT)
    gasified_summary = gasified_surrogate.get("summary")
    require(isinstance(gasified_summary, dict), "gasified LNG/LPG surrogate report summary missing")
    gasified_lng_lpg_surrogate_passed = (
        gasified_surrogate.get("status") == "PASS-ENGINEERING-GASIFIED-LNG-LPG-SURROGATE-BOUNDARY"
        and gasified_summary.get("gasified_lng_ch4_surrogate_template_ready") is True
        and gasified_summary.get("gasified_lpg_c3h8_surrogate_template_ready") is True
        and gasified_summary.get("given_gas_source_surrogate_ready") is True
        and gasified_summary.get("gasified_lng_ch4_mpi_cuda_runtime_passed") is True
        and gasified_summary.get("gasified_lng_ch4_cold_source_sustained_fire_claim_allowed") is False
        and gasified_summary.get("gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed") is True
        and gasified_summary.get("gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed") is True
        and gasified_summary.get("gasified_lpg_c3h8_mpi_cuda_runtime_passed") is True
        and gasified_summary.get("gasified_lpg_c3h8_surrogate_fire_probe_passed") is True
        and gasified_summary.get("liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation_ready") is False
        and gasified_summary.get("lng_lpg_production_phase_change_claim_allowed") is False
        and gasified_summary.get("prevents_liquid_phase_overclaim") is True
    )
    ch4_external_vaporization_cuda = load_json(CH4_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA_REPORT)
    ch4_external_summary = ch4_external_vaporization_cuda.get("summary")
    require(isinstance(ch4_external_summary, dict), "CH4 external vaporization CUDA report summary missing")
    ch4_external_vaporization_timeseries_cuda_passed = (
        ch4_external_vaporization_cuda.get("status")
        == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-CH4-TIMESERIES-CUDA"
        and ch4_external_summary.get("external_vaporization_ch4_timeseries_cuda_ready") is True
        and ch4_external_summary.get("fuel_species_ch4_selected") is True
        and ch4_external_summary.get("stl_obstacles_built") is True
        and ch4_external_summary.get("run_log_has_no_abort_nan_or_cuda_error") is True
        and ch4_external_summary.get("scheduled_reference_mdot_varies") is True
        and ch4_external_summary.get("scheduled_leak_T_varies") is True
        and ch4_external_summary.get("scheduled_velocity_xy_varies") is True
        and ch4_external_summary.get("scheduled_radius_varies") is True
        and ch4_external_summary.get("scheduled_center_xy_varies") is True
    )
    c3h8_external_vaporization_cuda = load_json(C3H8_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA_REPORT)
    c3h8_external_summary = c3h8_external_vaporization_cuda.get("summary")
    require(isinstance(c3h8_external_summary, dict), "C3H8 external vaporization CUDA report summary missing")
    c3h8_external_vaporization_timeseries_cuda_passed = (
        c3h8_external_vaporization_cuda.get("status")
        == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-C3H8-TIMESERIES-CUDA"
        and c3h8_external_summary.get("external_vaporization_c3h8_timeseries_cuda_ready") is True
        and c3h8_external_summary.get("fuel_species_c3h8_selected") is True
        and c3h8_external_summary.get("stl_obstacles_built") is True
        and c3h8_external_summary.get("run_log_has_no_abort_nan_or_cuda_error") is True
        and c3h8_external_summary.get("scheduled_reference_mdot_varies") is True
        and c3h8_external_summary.get("scheduled_leak_T_varies") is True
        and c3h8_external_summary.get("scheduled_velocity_xy_varies") is True
        and c3h8_external_summary.get("scheduled_radius_varies") is True
        and c3h8_external_summary.get("scheduled_center_xy_varies") is True
    )
    liquefied_source_model = load_json(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_REPORT)
    liquefied_source_model_summary = liquefied_source_model.get("summary")
    require(isinstance(liquefied_source_model_summary, dict), "liquefied release source model summary missing")
    liquefied_source_model_passed = (
        liquefied_source_model.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL"
        and liquefied_source_model_summary.get("liquefied_release_vaporization_source_model_ready") is True
        and liquefied_source_model_summary.get("lng_ch4_screening_release_source_ready") is True
        and liquefied_source_model_summary.get("lpg_c3h8_screening_release_source_ready") is True
        and liquefied_source_model_summary.get("outputs_external_vaporization_csv") is True
        and liquefied_source_model_summary.get("outputs_pelelmex_fixed_mass_flow_schedule_input") is True
        and liquefied_source_model_summary.get("production_phase_change_claim_allowed") is False
        and liquefied_source_model_summary.get("cfd_solves_liquid_phase_change") is False
        and liquefied_source_model_summary.get("cfd_solves_flashing_discharge") is False
        and liquefied_source_model_summary.get("cfd_solves_pool_spread_evaporation") is False
    )
    liquefied_source_negative = load_json(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_NEGATIVE_SELFTEST_REPORT)
    liquefied_source_negative_summary = liquefied_source_negative.get("summary")
    require(isinstance(liquefied_source_negative_summary, dict), "liquefied release source negative selftest summary missing")
    liquefied_source_negative_passed = (
        liquefied_source_negative.get("status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST"
        and liquefied_source_negative_summary.get("negative_selftest_ready") is True
        and liquefied_source_negative_summary.get("negative_case_count") == 13
        and liquefied_source_negative_summary.get("negative_refused_count") == 13
        and liquefied_source_negative_summary.get("failed_negative_count") == 0
    )
    liquefied_source_cuda_smoke = load_json(LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_CUDA_SMOKE_REPORT)
    liquefied_source_cuda_smoke_summary = liquefied_source_cuda_smoke.get("summary")
    require(isinstance(liquefied_source_cuda_smoke_summary, dict), "liquefied release source CUDA smoke summary missing")
    liquefied_source_cuda_smoke_passed = (
        liquefied_source_cuda_smoke.get("status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE"
        and liquefied_source_cuda_smoke_summary.get("liquefied_release_source_model_cuda_smoke_ready") is True
        and liquefied_source_cuda_smoke_summary.get("lng_ch4_generated_input_cuda_smoke_passed") is True
        and liquefied_source_cuda_smoke_summary.get("lpg_c3h8_generated_input_cuda_smoke_passed") is True
        and liquefied_source_cuda_smoke_summary.get("environment_uses_cuda_12_6") is True
        and liquefied_source_cuda_smoke_summary.get("environment_uses_tesla_p100") is True
        and liquefied_source_cuda_smoke_summary.get("cfd_solves_liquid_phase_change") is False
        and liquefied_source_cuda_smoke_summary.get("cfd_solves_flashing_discharge") is False
        and liquefied_source_cuda_smoke_summary.get("cfd_solves_pool_spread_evaporation") is False
    )
    liquefied_source_balance = load_json(LIQUEFIED_RELEASE_SOURCE_BALANCE_REPORT)
    liquefied_source_balance_summary = liquefied_source_balance.get("summary")
    require(isinstance(liquefied_source_balance_summary, dict), "liquefied release source balance summary missing")
    liquefied_source_balance_passed = (
        liquefied_source_balance.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE"
        and liquefied_source_balance_summary.get("liquefied_release_source_balance_ready") is True
        and liquefied_source_balance_summary.get("species") == ["C3H8", "CH4"]
        and float(liquefied_source_balance_summary.get("total_gas_mass_integral_kg", 0.0)) > 0.0
        and float(liquefied_source_balance_summary.get("max_inventory_mass_relative_error", 1.0)) <= 0.20
        and liquefied_source_balance_summary.get("mapping_schedule_matches_csv") is True
        and liquefied_source_balance_summary.get("generated_input_matches_mapping") is True
        and liquefied_source_balance_summary.get("production_phase_change_claim_allowed") is False
        and liquefied_source_balance_summary.get("cfd_solves_liquid_phase_change") is False
        and liquefied_source_balance_summary.get("cfd_solves_flashing_discharge") is False
        and liquefied_source_balance_summary.get("cfd_solves_pool_spread_evaporation") is False
        and liquefied_source_balance_summary.get("overclaim_guard_active") is True
    )
    liquefied_source_balance_negative = load_json(LIQUEFIED_RELEASE_SOURCE_BALANCE_NEGATIVE_SELFTEST_REPORT)
    liquefied_source_balance_negative_summary = liquefied_source_balance_negative.get("summary")
    require(isinstance(liquefied_source_balance_negative_summary, dict), "liquefied release source balance negative selftest summary missing")
    liquefied_source_balance_negative_passed = (
        liquefied_source_balance_negative.get("status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST"
        and liquefied_source_balance_negative_summary.get("liquefied_release_source_balance_negative_selftest_ready") is True
        and int(liquefied_source_balance_negative_summary.get("negative_case_count", 0)) == 5
        and int(liquefied_source_balance_negative_summary.get("negative_rejected_count", 0)) == 5
        and int(liquefied_source_balance_negative_summary.get("expected_fragment_seen_count", 0)) == 5
        and liquefied_source_balance_negative_summary.get("guards_negative_mdot") is True
        and liquefied_source_balance_negative_summary.get("guards_species_drift") is True
        and liquefied_source_balance_negative_summary.get("guards_schedule_rate_mismatch") is True
        and liquefied_source_balance_negative_summary.get("guards_phase_change_overclaim") is True
        and liquefied_source_balance_negative_summary.get("guards_generated_input_species_mismatch") is True
    )

    methane_mechs = available_mechanisms(METHANE_MECHANISMS)
    propane_mechs = available_mechanisms(PROPANE_MECHANISMS)
    liquid_mechs = available_mechanisms(LIQUID_FUEL_MECHANISMS)

    capability_matrix = {
        "h2_gas_leak_dispersion_ignition_fire": {
            "status": "CURRENT_SCOPE_READY",
            "production_claim_allowed": bool(engineering.get("ready") is True),
            "cpu_mpi_ready": bool(engineering.get("modes", {}).get("cpu_mpi") is True),
            "single_gpu_ready": bool(engineering.get("modes", {}).get("single_gpu") is True),
            "multi_gpu_mpi_cuda_ready": bool(engineering.get("modes", {}).get("multi_gpu_mpi_cuda") is True),
            "evidence_path": engineering.get("evidence_paths", {}),
        },
        "methane_or_natural_gas_gas_phase": {
            "status": "CH4_CPU_MPI_CUDA_COLD_PLUME_AND_CPU_MPI_SINGLE_CUDA_MPI_CUDA_FIRE_PASS_BUT_NOT_PRODUCTION_VERIFIED",
            "production_claim_allowed": False,
            "available_mechanisms": methane_mechs,
            "source_entry_probe_passed": ch4_probe_passed,
            "cpu_mpi_cuda_cold_plume_probe_passed": ch4_cpu_mpi_cuda_cold_plume_passed,
            "delayed_ignition_single_cuda_fire_probe_passed": ch4_delayed_ignition_single_cuda_passed,
            "delayed_ignition_cpu_mpi_fire_probe_passed": ch4_delayed_ignition_cpu_mpi_passed,
            "delayed_ignition_mpi_cuda_fire_probe_passed": ch4_delayed_ignition_mpi_cuda_passed,
            "delayed_ignition_mpi_cuda_500step_fire_probe_passed": ch4_delayed_ignition_mpi_cuda_500_passed,
            "external_vaporization_timeseries_cuda_passed": ch4_external_vaporization_timeseries_cuda_passed,
            "required_work": [
                "extend CH4/natural-gas from reduced CPU/MPI, single-CUDA, rank-mapped MPI+CUDA, and 500-step MPI+CUDA fire probes to scenario-scale production-duration campaigns",
                "add LFL/UFL and heat-release metrics appropriate to the selected gas composition",
                "add production-duration CH4/natural-gas dispersion-to-fire acceptance thresholds",
            ],
        },
        "propane_gas_phase": {
            "status": "INITIAL_C3H8_GAS_PHASE_CPU_CPU_MPI_SINGLE_CUDA_AND_MPI_CUDA_FIRE_PROBES_PASS_BUT_NOT_PRODUCTION_VERIFIED",
            "production_claim_allowed": False,
            "available_mechanisms": propane_mechs,
            "c3h8_cold_plume_cpu_passed": c3h8_summary.get("c3h8_cold_plume_cpu_passed") is True,
            "c3h8_propane_fc_fire_cpu_passed": c3h8_summary.get("c3h8_propane_fc_fire_cpu_passed") is True,
            "c3h8_propane_fc_fire_cpu_mpi_passed": c3h8_summary.get("c3h8_propane_fc_fire_cpu_mpi_passed") is True,
            "c3h8_propane_fc_fire_cuda_passed": c3h8_summary.get("c3h8_propane_fc_fire_cuda_passed") is True,
            "c3h8_propane_fc_fire_mpi_cuda_passed": c3h8_summary.get("c3h8_propane_fc_fire_mpi_cuda_passed") is True,
            "c3h8_rank_mapped_two_gpu_mpi_cuda_passed": c3h8_summary.get("c3h8_rank_mapped_two_gpu_mpi_cuda_passed") is True,
            "gasified_lpg_c3h8_mpi_cuda_fire_probe_passed": gasified_summary.get("gasified_lpg_c3h8_surrogate_fire_probe_passed") is True,
            "external_vaporization_timeseries_cuda_passed": c3h8_external_vaporization_timeseries_cuda_passed,
            "liquefied_release_generated_input_cuda_smoke_passed": liquefied_source_cuda_smoke_summary.get("lpg_c3h8_generated_input_cuda_smoke_passed") is True,
            "evidence_path": str(C3H8_GAS_PHASE_CPU_CUDA_REPORT),
            "required_work": [
                "extend C3H8 from 120-step reduced probes to longer production-duration campaigns",
                "verify dense-gas/slumping behavior and ignition/fire gates",
                "add propane-specific acceptance thresholds and external comparison cases",
            ],
        },
        "gasified_lng_or_simplified_natural_gas_cloud": {
            "status": "GASIFIED_CH4_SURROGATE_TEMPLATE_AND_MPI_CUDA_COLD_SOURCE_RUNTIME_PASS_NOT_CRYOGENIC_FIRE_PRODUCTION_VERIFIED",
            "production_claim_allowed": False,
            "available_mechanisms": methane_mechs,
            "given_gas_source_surrogate_passed": gasified_lng_lpg_surrogate_passed,
            "gasified_lng_ch4_mpi_cuda_runtime_passed": gasified_summary.get("gasified_lng_ch4_mpi_cuda_runtime_passed") is True,
            "gasified_lng_ch4_cold_source_sustained_fire_claim_allowed": gasified_summary.get("gasified_lng_ch4_cold_source_sustained_fire_claim_allowed") is True,
            "gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed": gasified_summary.get("gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed") is True,
            "gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed": gasified_summary.get("gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed") is True,
            "external_vaporization_timeseries_cuda_passed": ch4_external_vaporization_timeseries_cuda_passed,
            "liquefied_release_generated_input_cuda_smoke_passed": liquefied_source_cuda_smoke_summary.get("lng_ch4_generated_input_cuda_smoke_passed") is True,
            "evidence_path": str(GASIFIED_LNG_LPG_SURROGATE_REPORT),
            "required_work": [
                "define LNG vapor composition surrogate, normally methane-rich with selected heavier components",
                "add low-temperature inlet/source thermodynamics and density/buoyancy checks",
                "verify ground-hugging cold-cloud dispersion before ignition/fire claims",
            ],
        },
        "liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation": {
            "status": "INTERNAL_PHASE_CHANGE_NOT_IMPLEMENTED_SCREENING_RELEASE_TO_GAS_SOURCE_GENERATOR_AND_CUDA_SMOKE_PASS",
            "production_claim_allowed": False,
            "available_related_mechanisms": liquid_mechs,
            "screening_release_to_gas_source_generator_passed": liquefied_source_model_passed,
            "screening_release_to_gas_source_negative_selftest_passed": liquefied_source_negative_passed,
            "generated_gas_source_inputs_cuda_smoke_passed": liquefied_source_cuda_smoke_passed,
            "external_gas_source_mass_balance_passed": liquefied_source_balance_passed,
            "external_gas_source_mass_balance_negative_selftest_passed": liquefied_source_balance_negative_passed,
            "external_gas_source_total_mass_integral_kg": liquefied_source_balance_summary.get("total_gas_mass_integral_kg"),
            "external_gas_source_max_inventory_mass_relative_error": liquefied_source_balance_summary.get("max_inventory_mass_relative_error"),
            "external_gas_source_balance_species": liquefied_source_balance_summary.get("species"),
            "lng_ch4_generated_input_cuda_smoke_passed": liquefied_source_cuda_smoke_summary.get("lng_ch4_generated_input_cuda_smoke_passed") is True,
            "lpg_c3h8_generated_input_cuda_smoke_passed": liquefied_source_cuda_smoke_summary.get("lpg_c3h8_generated_input_cuda_smoke_passed") is True,
            "cfd_internal_phase_change_ready": False,
            "required_work": [
                "two-phase or flashing discharge model at the rupture",
                "liquid pool spread or droplet/aerosol transport representation",
                "latent heat, wall/ground heat transfer, cryogenic property closure, and vaporization source coupling",
                "validation against LNG/LPG spill, vaporization, dense-cloud dispersion, and fire consequence datasets",
            ],
        },
    }

    promotion_gates = [
        {
            "gate": "configurable_fuel_species_source",
            "required_for": ["methane_or_natural_gas_gas_phase", "propane_gas_phase", "gasified_lng_or_simplified_natural_gas_cloud"],
            "current_status": "passed_for_H2_CH4_C3H8_source_selection",
            "acceptance": "prob.fuel_species or equivalent must select source/cloud fuel species without H2_ID-only source injection",
        },
        {
            "gate": "mechanism_specific_builds",
            "required_for": ["methane_or_natural_gas_gas_phase", "propane_gas_phase"],
            "current_status": "passed_for_CH4_and_C3H8_CPU_CPU_MPI_SINGLE_CUDA_MPI_CUDA_initial_probes",
            "acceptance": "CH4 and C3H8 executables compile and pass CPU/MPI, single-CUDA, and rank-mapped MPI+CUDA smoke tests",
        },
        {
            "gate": "fuel_specific_fire_validation",
            "required_for": ["methane_or_natural_gas_gas_phase", "propane_gas_phase", "gasified_lng_or_simplified_natural_gas_cloud"],
            "current_status": "initial_CH4_and_C3H8_reduced_fire_probes_pass_external_thresholds_and_production_duration_missing",
            "acceptance": "fuel-specific LFL/UFL, ignition, heat-release, and stable flame propagation reports pass",
        },
        {
            "gate": "liquefied_gas_phase_change_model",
            "required_for": ["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"],
            "current_status": "missing",
            "acceptance": "flashing/liquid-pool or droplet evaporation source terms are implemented and validated",
        },
    ]

    summary = {
        "h2_engineering_current_scope_ready": bool(engineering.get("ready") is True),
        "current_engineering_chemistry_model": chemistry_model,
        "engineering_source_is_h2_specific": source_is_h2_specific,
        "source_fuel_species_configurable": source_fuel_species_configurable,
        "h2_default_fuel_species_probe_passed": h2_default_probe_passed,
        "ch4_fuel_species_probe_passed": ch4_probe_passed,
        "ch4_cpu_mpi_cuda_cold_plume_probe_passed": ch4_cpu_mpi_cuda_cold_plume_passed,
        "ch4_delayed_ignition_single_cuda_fire_probe_passed": ch4_delayed_ignition_single_cuda_passed,
        "ch4_delayed_ignition_cpu_mpi_fire_probe_passed": ch4_delayed_ignition_cpu_mpi_passed,
        "ch4_delayed_ignition_mpi_cuda_fire_probe_passed": ch4_delayed_ignition_mpi_cuda_passed,
        "ch4_delayed_ignition_mpi_cuda_500step_fire_probe_passed": ch4_delayed_ignition_mpi_cuda_500_passed,
        "c3h8_gas_phase_cpu_cuda_probe_passed": c3h8_gas_phase_cpu_cuda_passed,
        "c3h8_gas_phase_cpu_mpi_cuda_probe_passed": c3h8_gas_phase_cpu_cuda_passed,
        "c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_probe_passed": c3h8_gas_phase_cpu_cuda_passed,
        "c3h8_propane_gas_phase_initial_ready": c3h8_summary.get("gas_phase_propane_initial_engineering_probe_ready") is True,
        "gasified_lng_lpg_surrogate_boundary_passed": gasified_lng_lpg_surrogate_passed,
        "gasified_lng_given_source_surrogate_ready": gasified_summary.get("gasified_lng_ch4_surrogate_template_ready") is True,
        "gasified_lpg_given_source_surrogate_ready": gasified_summary.get("gasified_lpg_c3h8_surrogate_template_ready") is True,
        "gasified_lng_ch4_mpi_cuda_runtime_passed": gasified_summary.get("gasified_lng_ch4_mpi_cuda_runtime_passed") is True,
        "gasified_lng_ch4_cold_source_sustained_fire_claim_allowed": gasified_summary.get("gasified_lng_ch4_cold_source_sustained_fire_claim_allowed") is True,
        "gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed": gasified_summary.get("gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed") is True,
        "gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed": gasified_summary.get("gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed") is True,
        "gasified_lpg_c3h8_mpi_cuda_fire_probe_passed": gasified_summary.get("gasified_lpg_c3h8_surrogate_fire_probe_passed") is True,
        "external_vaporization_ch4_timeseries_cuda_passed": ch4_external_vaporization_timeseries_cuda_passed,
        "external_vaporization_c3h8_timeseries_cuda_passed": c3h8_external_vaporization_timeseries_cuda_passed,
        "external_vaporization_multifuel_timeseries_cuda_passed": (
            ch4_external_vaporization_timeseries_cuda_passed
            and c3h8_external_vaporization_timeseries_cuda_passed
        ),
        "liquefied_release_vaporization_source_model_passed": liquefied_source_model_passed,
        "liquefied_release_vaporization_source_model_negative_selftest_passed": liquefied_source_negative_passed,
        "liquefied_release_vaporization_source_model_cuda_smoke_passed": liquefied_source_cuda_smoke_passed,
        "liquefied_release_source_balance_passed": liquefied_source_balance_passed,
        "liquefied_release_source_balance_negative_selftest_passed": liquefied_source_balance_negative_passed,
        "liquefied_release_source_balance_total_gas_mass_integral_kg": liquefied_source_balance_summary.get("total_gas_mass_integral_kg"),
        "liquefied_release_source_balance_max_inventory_mass_relative_error": liquefied_source_balance_summary.get("max_inventory_mass_relative_error"),
        "liquefied_release_source_balance_negative_rejected_count": liquefied_source_balance_negative_summary.get("negative_rejected_count"),
        "liquefied_release_source_balance_expected_fragment_seen_count": liquefied_source_balance_negative_summary.get("expected_fragment_seen_count"),
        "liquefied_release_lng_ch4_generated_input_cuda_smoke_passed": liquefied_source_cuda_smoke_summary.get("lng_ch4_generated_input_cuda_smoke_passed") is True,
        "liquefied_release_lpg_c3h8_generated_input_cuda_smoke_passed": liquefied_source_cuda_smoke_summary.get("lpg_c3h8_generated_input_cuda_smoke_passed") is True,
        "methane_mechanism_count": len(methane_mechs),
        "propane_mechanism_count": len(propane_mechs),
        "liquid_fuel_related_mechanism_count": len(liquid_mechs),
        "multi_fuel_production_ready": False,
        "gasified_lng_production_ready": False,
        "liquefied_gas_phase_change_ready": False,
        "prevents_overclaim": True,
        "promotion_gate_count": len(promotion_gates),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "Engineering Multi-Fuel And Liquefied-Gas Capability Boundary",
        "summary": summary,
        "h2_specific_markers": h2_specific_markers,
        "capability_matrix": capability_matrix,
        "promotion_gates": promotion_gates,
        "evidence_files": [
            evidence_entry("engineering_h2_leak_prob_h", PROB_H),
            evidence_entry("engineering_h2_leak_prob_cpp", PROB_CPP),
            evidence_entry("engineering_h2_leak_gnumakefile", GNUMAKE),
            evidence_entry("current_scenario_readiness_matrix", SCENARIO_MATRIX),
            evidence_entry("h2_default_fuel_species_run_log", H2_PROBE_RUN_LOG),
            evidence_entry("h2_default_fuel_species_validation_log", H2_PROBE_VALIDATION_LOG),
            evidence_entry("ch4_fuel_species_build_log", CH4_PROBE_BUILD_LOG),
            evidence_entry("ch4_fuel_species_run_log", CH4_PROBE_RUN_LOG),
            evidence_entry("ch4_cold_plume_cpu_mpi_cuda_probe_report", CH4_COLD_PLUME_REPORT),
            evidence_entry("ch4_pipe_rack_delayed_ignition_single_cuda_report", CH4_FIRE_CUDA_REPORT),
            evidence_entry("ch4_pipe_rack_delayed_ignition_cpu_mpi_report", CH4_FIRE_MPI_REPORT),
            evidence_entry("ch4_pipe_rack_delayed_ignition_mpi_cuda_report", CH4_FIRE_MPI_CUDA_REPORT),
            evidence_entry("ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report", CH4_FIRE_MPI_CUDA_500STEP_REPORT),
            evidence_entry("c3h8_gas_phase_cpu_cuda_report", C3H8_GAS_PHASE_CPU_CUDA_REPORT),
            evidence_entry("gasified_lng_lpg_surrogate_report", GASIFIED_LNG_LPG_SURROGATE_REPORT),
            evidence_entry("ch4_external_vaporization_timeseries_cuda_report", CH4_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA_REPORT),
            evidence_entry("c3h8_external_vaporization_timeseries_cuda_report", C3H8_EXTERNAL_VAPORIZATION_TIMESERIES_CUDA_REPORT),
            evidence_entry("liquefied_release_vaporization_source_model_report", LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_REPORT),
            evidence_entry("liquefied_release_vaporization_source_model_negative_selftest_report", LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_NEGATIVE_SELFTEST_REPORT),
            evidence_entry("liquefied_release_vaporization_source_model_cuda_smoke_report", LIQUEFIED_RELEASE_VAPORIZATION_SOURCE_MODEL_CUDA_SMOKE_REPORT),
            evidence_entry("liquefied_release_source_balance_report", LIQUEFIED_RELEASE_SOURCE_BALANCE_REPORT),
            evidence_entry("liquefied_release_source_balance_negative_selftest_report", LIQUEFIED_RELEASE_SOURCE_BALANCE_NEGATIVE_SELFTEST_REPORT),
        ],
        "limitations": [
            "This is a capability-boundary audit, not a multi-fuel production validation.",
            "H2 remains the only engineering gas leak/fire scenario with current long CPU/GPU evidence.",
            "CH4 has short CPU, CPU/MPI, and single-CUDA cold-plume evidence plus reduced CPU/MPI, single-CUDA, rank-mapped MPI+CUDA, and 500-step MPI+CUDA delayed-ignition fire probes, not scenario-scale natural-gas production validation.",
            "CH4 and C3H8 now also have CUDA runtime evidence for time-varying external-vaporization engineering sources with STL pipe-rack obstacles.",
            "C3H8 has gas-phase cold source plus reduced CPU, CPU/MPI, single-CUDA, rank-mapped MPI+CUDA propane_fc delayed-ignition fire probes, and external-vaporization-source CUDA evidence, not dense-gas, external-threshold, or production-duration validation.",
            "Gasified LNG/LPG given-source surrogates now have templates, 2-rank/2-GPU runtime evidence, CH4/C3H8 time-varying external-source CUDA evidence, generated-input CUDA smoke evidence, source-schedule mass-balance evidence, and negative selftests for the screening liquefied-release source generator; the LNG cold-source run is stable but does not claim sustained cryogenic fire validation, and internal liquefied-gas rupture, flashing, pool evaporation, and cryogenic dense-cloud production validation remain outside the current scope.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("h2_engineering_current_scope_ready") is True, "H2 current scope readiness missing")
    require(summary.get("current_engineering_chemistry_model") == "LiDryer", "current engineering chemistry model drifted")
    require(summary.get("engineering_source_is_h2_specific") is False, "source should no longer be H2-specific")
    require(summary.get("source_fuel_species_configurable") is True, "fuel species source configurability missing")
    require(summary.get("h2_default_fuel_species_probe_passed") is True, "H2 default fuel species probe missing")
    require(summary.get("ch4_fuel_species_probe_passed") is True, "CH4 fuel species probe missing")
    require(summary.get("ch4_cpu_mpi_cuda_cold_plume_probe_passed") is True, "CH4 CPU/MPI/CUDA cold plume probe missing")
    require(summary.get("ch4_delayed_ignition_single_cuda_fire_probe_passed") is True, "CH4 single-CUDA fire probe missing")
    require(summary.get("ch4_delayed_ignition_cpu_mpi_fire_probe_passed") is True, "CH4 CPU/MPI fire probe missing")
    require(summary.get("ch4_delayed_ignition_mpi_cuda_fire_probe_passed") is True, "CH4 MPI+CUDA fire probe missing")
    require(summary.get("ch4_delayed_ignition_mpi_cuda_500step_fire_probe_passed") is True, "CH4 MPI+CUDA 500-step fire probe missing")
    require(summary.get("c3h8_gas_phase_cpu_cuda_probe_passed") is True, "C3H8 gas-phase CPU/CUDA probe missing")
    require(summary.get("c3h8_gas_phase_cpu_mpi_cuda_probe_passed") is True, "C3H8 gas-phase CPU/MPI/CUDA probe missing")
    require(
        summary.get("c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_probe_passed") is True,
        "C3H8 gas-phase CPU/CPU-MPI/single-CUDA/MPI-CUDA probe missing",
    )
    require(summary.get("c3h8_propane_gas_phase_initial_ready") is True, "C3H8 gas-phase initial readiness missing")
    require(summary.get("gasified_lng_lpg_surrogate_boundary_passed") is True, "gasified LNG/LPG surrogate boundary missing")
    require(summary.get("gasified_lng_given_source_surrogate_ready") is True, "gasified LNG given-source surrogate missing")
    require(summary.get("gasified_lpg_given_source_surrogate_ready") is True, "gasified LPG given-source surrogate missing")
    require(summary.get("gasified_lng_ch4_mpi_cuda_runtime_passed") is True, "gasified LNG CH4 MPI+CUDA runtime missing")
    require(summary.get("gasified_lng_ch4_cold_source_sustained_fire_claim_allowed") is False, "gasified LNG CH4 cold-source run must not claim sustained fire")
    require(summary.get("gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed") is True, "gasified LNG CH4 warmed-vapor fire runtime missing")
    require(summary.get("gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed") is True, "gasified LNG CH4 warmed-vapor fire claim missing")
    require(summary.get("gasified_lpg_c3h8_mpi_cuda_fire_probe_passed") is True, "gasified LPG C3H8 MPI+CUDA fire runtime missing")
    require(summary.get("external_vaporization_ch4_timeseries_cuda_passed") is True, "CH4 external vaporization CUDA runtime missing")
    require(summary.get("external_vaporization_c3h8_timeseries_cuda_passed") is True, "C3H8 external vaporization CUDA runtime missing")
    require(summary.get("external_vaporization_multifuel_timeseries_cuda_passed") is True, "multi-fuel external vaporization CUDA runtime missing")
    require(summary.get("liquefied_release_vaporization_source_model_passed") is True, "liquefied release source model missing")
    require(
        summary.get("liquefied_release_vaporization_source_model_negative_selftest_passed") is True,
        "liquefied release source model negative selftest missing",
    )
    require(
        summary.get("liquefied_release_vaporization_source_model_cuda_smoke_passed") is True,
        "liquefied release source model CUDA smoke missing",
    )
    require(summary.get("liquefied_release_source_balance_passed") is True, "liquefied release source balance missing")
    require(
        summary.get("liquefied_release_source_balance_negative_selftest_passed") is True,
        "liquefied release source balance negative selftest missing",
    )
    require(
        float(summary.get("liquefied_release_source_balance_total_gas_mass_integral_kg", 0.0)) > 0.0,
        "liquefied release source balance total mass is not positive",
    )
    require(
        float(summary.get("liquefied_release_source_balance_max_inventory_mass_relative_error", 1.0)) <= 0.20,
        "liquefied release source balance mass error too large",
    )
    require(
        int(summary.get("liquefied_release_source_balance_negative_rejected_count", 0)) == 5,
        "liquefied release source balance negative rejection count missing",
    )
    require(
        int(summary.get("liquefied_release_source_balance_expected_fragment_seen_count", 0)) == 5,
        "liquefied release source balance negative diagnostics missing",
    )
    require(
        summary.get("liquefied_release_lng_ch4_generated_input_cuda_smoke_passed") is True,
        "LNG CH4 generated input CUDA smoke missing",
    )
    require(
        summary.get("liquefied_release_lpg_c3h8_generated_input_cuda_smoke_passed") is True,
        "LPG C3H8 generated input CUDA smoke missing",
    )
    require(int(summary.get("methane_mechanism_count", 0)) >= 1, "no methane-capable mechanism found")
    require(int(summary.get("propane_mechanism_count", 0)) >= 1, "no propane-capable mechanism found")
    require(summary.get("multi_fuel_production_ready") is False, "audit must not claim multi-fuel production readiness")
    require(summary.get("gasified_lng_production_ready") is False, "audit must not claim gasified LNG production readiness")
    require(summary.get("liquefied_gas_phase_change_ready") is False, "audit must not claim liquefied-gas phase-change readiness")
    require(summary.get("prevents_overclaim") is True, "overclaim prevention flag missing")
    matrix = data.get("capability_matrix")
    require(isinstance(matrix, dict), "capability_matrix missing")
    require(matrix["h2_gas_leak_dispersion_ignition_fire"]["production_claim_allowed"] is True, "H2 production claim not preserved")
    require(matrix["propane_gas_phase"]["c3h8_propane_fc_fire_cpu_passed"] is True, "C3H8 CPU fire evidence missing")
    require(matrix["propane_gas_phase"]["c3h8_propane_fc_fire_cpu_mpi_passed"] is True, "C3H8 CPU/MPI fire evidence missing")
    require(matrix["propane_gas_phase"]["c3h8_propane_fc_fire_cuda_passed"] is True, "C3H8 CUDA fire evidence missing")
    require(matrix["propane_gas_phase"]["c3h8_propane_fc_fire_mpi_cuda_passed"] is True, "C3H8 MPI+CUDA fire evidence missing")
    require(
        matrix["propane_gas_phase"]["c3h8_rank_mapped_two_gpu_mpi_cuda_passed"] is True,
        "C3H8 rank-mapped two-GPU MPI+CUDA evidence missing",
    )
    require(
        matrix["gasified_lng_or_simplified_natural_gas_cloud"]["given_gas_source_surrogate_passed"] is True,
        "gasified LNG surrogate evidence missing",
    )
    require(
        matrix["gasified_lng_or_simplified_natural_gas_cloud"]["gasified_lng_ch4_mpi_cuda_runtime_passed"] is True,
        "gasified LNG CH4 runtime evidence missing",
    )
    require(
        matrix["gasified_lng_or_simplified_natural_gas_cloud"]["gasified_lng_ch4_cold_source_sustained_fire_claim_allowed"] is False,
        "gasified LNG CH4 cold-source runtime must not allow sustained-fire claim",
    )
    require(
        matrix["gasified_lng_or_simplified_natural_gas_cloud"]["gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed"] is True,
        "gasified LNG CH4 warmed-vapor fire runtime evidence missing",
    )
    require(
        matrix["gasified_lng_or_simplified_natural_gas_cloud"]["gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed"] is True,
        "gasified LNG CH4 warmed-vapor fire claim evidence missing",
    )
    require(
        matrix["propane_gas_phase"]["gasified_lpg_c3h8_mpi_cuda_fire_probe_passed"] is True,
        "gasified LPG C3H8 fire runtime evidence missing",
    )
    require(
        matrix["methane_or_natural_gas_gas_phase"]["external_vaporization_timeseries_cuda_passed"] is True,
        "CH4 external vaporization matrix evidence missing",
    )
    require(
        matrix["propane_gas_phase"]["external_vaporization_timeseries_cuda_passed"] is True,
        "C3H8 external vaporization matrix evidence missing",
    )
    require(
        matrix["propane_gas_phase"]["liquefied_release_generated_input_cuda_smoke_passed"] is True,
        "C3H8/LPG generated source CUDA-smoke matrix evidence missing",
    )
    require(
        matrix["gasified_lng_or_simplified_natural_gas_cloud"]["external_vaporization_timeseries_cuda_passed"] is True,
        "gasified LNG external vaporization matrix evidence missing",
    )
    require(
        matrix["gasified_lng_or_simplified_natural_gas_cloud"]["liquefied_release_generated_input_cuda_smoke_passed"] is True,
        "LNG/CH4 generated source CUDA-smoke matrix evidence missing",
    )
    require(
        matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["screening_release_to_gas_source_generator_passed"] is True,
        "liquefied screening source generator matrix evidence missing",
    )
    require(
        matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["screening_release_to_gas_source_negative_selftest_passed"] is True,
        "liquefied screening source generator negative selftest matrix evidence missing",
    )
    require(
        matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["generated_gas_source_inputs_cuda_smoke_passed"] is True,
        "liquefied generated gas-source CUDA-smoke matrix evidence missing",
    )
    require(
        matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["external_gas_source_mass_balance_passed"] is True,
        "liquefied generated gas-source mass-balance evidence missing",
    )
    require(
        matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["external_gas_source_mass_balance_negative_selftest_passed"] is True,
        "liquefied generated gas-source mass-balance negative selftest evidence missing",
    )
    require(
        float(matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["external_gas_source_total_mass_integral_kg"]) > 0.0,
        "liquefied generated gas-source mass integral is not positive",
    )
    require(
        float(matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["external_gas_source_max_inventory_mass_relative_error"]) <= 0.20,
        "liquefied generated gas-source mass error too large",
    )
    require(
        matrix["liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation"]["cfd_internal_phase_change_ready"] is False,
        "liquefied internal phase-change readiness must remain false",
    )
    for label in (
        "methane_or_natural_gas_gas_phase",
        "propane_gas_phase",
        "gasified_lng_or_simplified_natural_gas_cloud",
        "liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation",
    ):
        require(matrix[label]["production_claim_allowed"] is False, f"{label} must not be production-ready")
    gates = data.get("promotion_gates")
    require(isinstance(gates, list) and len(gates) >= 4, "promotion gates incomplete")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Multi-Fuel Capability Boundary",
        "",
        f"- Status: `{report['status']}`",
        f"- Current engineering chemistry model: `{s['current_engineering_chemistry_model']}`",
        f"- H2 engineering current scope ready: `{s['h2_engineering_current_scope_ready']}`",
        f"- Engineering source is H2-specific: `{s['engineering_source_is_h2_specific']}`",
        f"- Source fuel species configurable: `{s['source_fuel_species_configurable']}`",
        f"- H2 default fuel-species probe passed: `{s['h2_default_fuel_species_probe_passed']}`",
        f"- CH4 fuel-species probe passed: `{s['ch4_fuel_species_probe_passed']}`",
        f"- CH4 CPU/MPI/CUDA cold-plume probe passed: `{s['ch4_cpu_mpi_cuda_cold_plume_probe_passed']}`",
        f"- CH4 delayed-ignition single-CUDA fire probe passed: `{s['ch4_delayed_ignition_single_cuda_fire_probe_passed']}`",
        f"- CH4 delayed-ignition CPU/MPI fire probe passed: `{s['ch4_delayed_ignition_cpu_mpi_fire_probe_passed']}`",
        f"- CH4 delayed-ignition MPI+CUDA fire probe passed: `{s['ch4_delayed_ignition_mpi_cuda_fire_probe_passed']}`",
        f"- CH4 delayed-ignition MPI+CUDA 500-step fire probe passed: `{s['ch4_delayed_ignition_mpi_cuda_500step_fire_probe_passed']}`",
        f"- C3H8 gas-phase CPU/CUDA probe passed: `{s['c3h8_gas_phase_cpu_cuda_probe_passed']}`",
        f"- C3H8 gas-phase CPU/MPI/CUDA probe passed: `{s['c3h8_gas_phase_cpu_mpi_cuda_probe_passed']}`",
        f"- C3H8 gas-phase CPU/CPU-MPI/single-CUDA/MPI-CUDA probe passed: `{s['c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_probe_passed']}`",
        f"- C3H8 propane gas-phase initial ready: `{s['c3h8_propane_gas_phase_initial_ready']}`",
        f"- Gasified LNG/LPG surrogate boundary passed: `{s['gasified_lng_lpg_surrogate_boundary_passed']}`",
        f"- Gasified LNG given-source surrogate ready: `{s['gasified_lng_given_source_surrogate_ready']}`",
        f"- Gasified LPG given-source surrogate ready: `{s['gasified_lpg_given_source_surrogate_ready']}`",
        f"- Gasified LNG CH4 MPI+CUDA runtime passed: `{s['gasified_lng_ch4_mpi_cuda_runtime_passed']}`",
        f"- Gasified LNG CH4 cold-source sustained-fire claim allowed: `{s['gasified_lng_ch4_cold_source_sustained_fire_claim_allowed']}`",
        f"- Gasified LNG CH4 warmed-vapor MPI+CUDA fire probe passed: `{s['gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed']}`",
        f"- Gasified LNG CH4 warmed-vapor sustained-fire claim allowed: `{s['gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed']}`",
        f"- Gasified LPG C3H8 MPI+CUDA fire probe passed: `{s['gasified_lpg_c3h8_mpi_cuda_fire_probe_passed']}`",
        f"- External-vaporization CH4 time-series CUDA runtime passed: `{s['external_vaporization_ch4_timeseries_cuda_passed']}`",
        f"- External-vaporization C3H8 time-series CUDA runtime passed: `{s['external_vaporization_c3h8_timeseries_cuda_passed']}`",
        f"- External-vaporization multi-fuel time-series CUDA runtime passed: `{s['external_vaporization_multifuel_timeseries_cuda_passed']}`",
        f"- Liquefied-release source model passed: `{s['liquefied_release_vaporization_source_model_passed']}`",
        f"- Liquefied-release source model negative selftest passed: `{s['liquefied_release_vaporization_source_model_negative_selftest_passed']}`",
        f"- Liquefied-release source model CUDA smoke passed: `{s['liquefied_release_vaporization_source_model_cuda_smoke_passed']}`",
        f"- Liquefied-release source balance passed: `{s['liquefied_release_source_balance_passed']}`",
        f"- Liquefied-release source balance negative selftest passed: `{s['liquefied_release_source_balance_negative_selftest_passed']}`",
        f"- Liquefied-release source balance total gas mass kg: `{s['liquefied_release_source_balance_total_gas_mass_integral_kg']}`",
        f"- Liquefied-release source balance max inventory mass relative error: `{s['liquefied_release_source_balance_max_inventory_mass_relative_error']}`",
        f"- Multi-fuel production ready: `{s['multi_fuel_production_ready']}`",
        f"- Gasified LNG production ready: `{s['gasified_lng_production_ready']}`",
        f"- Liquefied-gas phase-change ready: `{s['liquefied_gas_phase_change_ready']}`",
        "",
        "## Capability Matrix",
        "",
    ]
    for label, item in report["capability_matrix"].items():
        lines.append(f"- `{label}`: `{item['status']}`, production claim allowed: `{item['production_claim_allowed']}`")
    lines += ["", "## Promotion Gates", ""]
    for gate in report["promotion_gates"]:
        lines.append(f"- `{gate['gate']}`: `{gate['current_status']}`")
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
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
            print(f"engineering_multi_fuel_capability_boundary VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_multi_fuel_capability_boundary PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except CapabilityBoundaryError as exc:
        print(f"engineering_multi_fuel_capability_boundary FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
