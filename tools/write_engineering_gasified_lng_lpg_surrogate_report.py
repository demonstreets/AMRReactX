#!/usr/bin/env python3
"""Write/verify gasified LNG/LPG surrogate engineering-source capability evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-GASIFIED-LNG-LPG-SURROGATE-BOUNDARY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_gasified_lng_lpg_surrogate_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_gasified_lng_lpg_surrogate_report.md"
DEFAULT_STAGED_ROOT = DEFAULT_ROOT / "runtime_evidence"
DEFAULT_LNG_RUNTIME_ROOT = Path("/tmp/codex_gasified_lng_ch4_surrogate_mpicuda_120step_20260806")
DEFAULT_LNG_WARMED_FIRE_RUNTIME_ROOT = Path("/tmp/codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step_20260806")
DEFAULT_LPG_RUNTIME_ROOT = Path("/tmp/codex_gasified_lpg_c3h8_surrogate_mpicuda_120step_20260806")

LNG_TEMPLATE = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke")
LNG_WARMED_FIRE_TEMPLATE = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step")
LPG_TEMPLATE = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke")
PROB_H = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
PROB_CPP = Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")
CH4_COLD_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_cold_plume_cpu_probe_20260806/"
    "engineering_ch4_cold_plume_cpu_probe_report.json"
)
CH4_MPI_CUDA_500_REPORT = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/"
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json"
)
C3H8_REPORT = Path(
    "docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/"
    "engineering_c3h8_gas_phase_cpu_cuda_report.json"
)


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ReportError(f"missing required file: {path}") from exc


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReportError(f"missing required report: {path}") from exc


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing evidence file: {path}")
    return {"label": label, "path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def copy_if_needed(src: Path, dst: Path) -> None:
    require(src.exists(), f"missing runtime artifact: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)


def parse_input(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in read_text(path).splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def stage_runtime_evidence(lng_root: Path, lng_warmed_fire_root: Path, lpg_root: Path, staged_root: Path) -> None:
    for label, root, input_name in (
        ("lng_ch4_mpicuda", lng_root, LNG_TEMPLATE.name),
        ("lng_ch4_warmed_fire_mpicuda", lng_warmed_fire_root, LNG_WARMED_FIRE_TEMPLATE.name),
        ("lpg_c3h8_mpicuda", lpg_root, LPG_TEMPLATE.name),
    ):
        dst = staged_root / label
        if not root.exists():
            require(
                dst.exists(),
                f"missing runtime root {root} and no staged fallback exists at {dst}",
            )
            continue
        for name in (
            input_name,
            "run.log",
            "run.status",
            "rank_gpu_wrapper.sh",
            "fextrema_selected.log",
            "codex_merged_pipe_rack_obstacles.stl",
        ):
            copy_if_needed(root / name, dst / name)


def run_status(path: Path) -> int:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except FileNotFoundError as exc:
        raise ReportError(f"missing run.status: {path}") from exc
    except ValueError as exc:
        raise ReportError(f"invalid run.status: {path}") from exc


def no_failure_markers(text: str, label: str) -> None:
    for marker in ("nan", "abort", "cvode failed", "cuda error", "deltaT =", "SIGABRT"):
        require(marker not in text.lower(), f"{label} contains failure marker: {marker}")


def parse_fextrema(path: Path) -> dict[str, dict[str, dict[str, float]]]:
    extrema: dict[str, dict[str, dict[str, float]]] = {}
    current = ""
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if line.startswith("== ") and line.endswith(" =="):
            current = line[3:-3].strip()
            extrema[current] = {}
            continue
        if not current or not line:
            continue
        parts = line.split()
        if len(parts) == 3:
            try:
                extrema[current][parts[0]] = {"min": float(parts[1]), "max": float(parts[2])}
            except ValueError:
                pass
    return extrema


def validate_runtime(root: Path, input_name: str, fuel: str, expect_fire: bool, final_plot: str) -> dict[str, Any]:
    run_log = read_text(root / "run.log")
    extrema = parse_fextrema(root / "fextrema_selected.log")
    final = extrema.get(final_plot, {})
    fuel_var = f"Y({fuel})"
    ir_var = f"I_R({fuel})"
    peak_temp = max(plot.get("temp", {}).get("max", 0.0) for plot in extrema.values())
    peak_heat_abs = max(
        max(abs(plot.get("HeatRelease", {}).get("min", 0.0)), abs(plot.get("HeatRelease", {}).get("max", 0.0)))
        for plot in extrema.values()
    )
    require(run_status(root / "run.status") == 0, f"{fuel} surrogate run did not exit 0")
    require(f"Engineering leak fuel species: name={fuel}" in run_log, f"{fuel} surrogate did not select requested species")
    require("MPI initialized with 2 MPI processes" in run_log, f"{fuel} surrogate did not initialize two MPI ranks")
    require("CUDA initialized with 2 devices." in run_log, f"{fuel} surrogate did not expose two GPUs")
    require("rank_gpu_wrapper: local_rank=0 CUDA_VISIBLE_DEVICES=0" in run_log, f"{fuel} surrogate missing rank 0 GPU mapping")
    require("rank_gpu_wrapper: local_rank=1 CUDA_VISIBLE_DEVICES=1" in run_log, f"{fuel} surrogate missing rank 1 GPU mapping")
    require("AMReX" in run_log and "finalized" in run_log, f"{fuel} surrogate did not finalize AMReX")
    require(input_name in read_text(root / input_name) or Path(input_name).name == input_name, "input staging sanity failure")
    no_failure_markers(run_log, f"{fuel} surrogate")
    require(final.get(fuel_var, {}).get("max", 0.0) > 0.0, f"{fuel} final fuel mass fraction missing")
    require(peak_temp > 300.0, f"{fuel} surrogate did not heat above ambient")
    if expect_fire:
        require(peak_temp > 2000.0, f"{fuel} surrogate fire did not exceed 2000 K")
        require(final.get("Y(H2O)", {}).get("max", 0.0) > 1.0e-6, f"{fuel} surrogate fire water product too weak")
        require(peak_heat_abs > 1.0e6, f"{fuel} surrogate fire heat-release magnitude too weak")
    return {
        "status": f"PASS-GASIFIED-SURROGATE-{fuel}-MPI-CUDA",
        "input": input_name,
        "mpi_ranks": 2,
        "cuda_devices": 2,
        "rank_mapped": True,
        "final_plot": final_plot,
        "peak_temperature": peak_temp,
        "peak_heat_release_abs": peak_heat_abs,
        "final_fuel_max": final.get(fuel_var, {}).get("max", 0.0),
        "final_y_h2o_max": final.get("Y(H2O)", {}).get("max", 0.0),
        "final_y_co2_max": final.get("Y(CO2)", {}).get("max", 0.0),
        "min_reaction_rate_fuel": min(plot.get(ir_var, {}).get("min", 0.0) for plot in extrema.values()),
        "sustained_fire_probe": expect_fire,
    }


def validate_template(path: Path, fuel: str, phase_marker: str) -> dict[str, Any]:
    text = read_text(path)
    data = parse_input(path)
    require(data.get("prob.fuel_species") == fuel, f"{path} does not select {fuel}")
    require(data.get("peleLM.user_defined_ext_sources") == "1", f"{path} does not enable engineering source")
    require(data.get("prob.initial_flammable_cloud") == "1", f"{path} does not initialize flammable cloud")
    require(data.get("prob.ignition_source") == "1", f"{path} does not enable delayed ignition source")
    require("not a liquid" in text or "not an LPG tank rupture" in text, f"{path} lacks phase-boundary warning")
    require(phase_marker in text, f"{path} lacks {phase_marker} marker")
    return {
        "path": str(path),
        "fuel_species": fuel,
        "leak_temperature": float(data["prob.leak_T"]),
        "cloud_temperature": float(data["prob.cloud_T"]),
        "cloud_fuel_mass_fraction": float(data["prob.cloud_YFuel"]),
        "max_step": int(data["amr.max_step"]),
        "obstacle_geometry": data.get("prob.obstacle_geometry", data.get("eb2.geom_type", "")),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    staged_root = Path(args.staged_root)
    if not args.no_stage:
        stage_runtime_evidence(
            Path(args.lng_runtime_root),
            Path(args.lng_warmed_fire_runtime_root),
            Path(args.lpg_runtime_root),
            staged_root,
        )

    prob_h = read_text(PROB_H)
    prob_cpp = read_text(PROB_CPP)
    require("fuel_species_index" in prob_h, "ProbParm does not expose fuel_species_index")
    require("fuel_species_name" in prob_h, "ProbParm does not retain fuel_species_name")
    require('pp.query("fuel_species", fuel_species)' in prob_cpp, "prob.fuel_species parser missing")
    require("prob.fuel_species was not found" in prob_cpp, "missing fuel_species mechanism guard")
    require("mf[pp->fuel_species_index]=1.0" in prob_h, "leak source does not inject selected fuel species")
    require("mf[pp.fuel_species_index]=pp.cloud_YFuel" in prob_h, "flammable cloud does not use selected fuel species")

    lng_template = validate_template(LNG_TEMPLATE, "CH4", "gasified-LNG surrogate")
    lng_warmed_fire_template = validate_template(LNG_WARMED_FIRE_TEMPLATE, "CH4", "gasified-LNG CH4 warmed-vapor fire surrogate")
    lpg_template = validate_template(LPG_TEMPLATE, "C3H8", "gasified-LPG surrogate")

    ch4_cold = load_json(CH4_COLD_REPORT)
    ch4_fire = load_json(CH4_MPI_CUDA_500_REPORT)
    c3h8 = load_json(C3H8_REPORT)
    c3h8_summary = c3h8.get("summary", {})
    require(ch4_cold.get("status") == "PASS-ENGINEERING-CH4-COLD-PLUME-CPU-MPI-CUDA-PROBE", "CH4 cold evidence missing")
    require(ch4_fire.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP", "CH4 fire MPI+CUDA 500-step evidence missing")
    require(c3h8.get("status") == "PASS-ENGINEERING-C3H8-GAS-PHASE-CPU-CPU-MPI-SINGLE-CUDA-MPI-CUDA", "C3H8 gas-phase matrix evidence missing")
    require(c3h8_summary.get("c3h8_propane_fc_fire_mpi_cuda_passed") is True, "C3H8 MPI+CUDA fire evidence missing")
    require(c3h8_summary.get("liquefied_propane_or_lpg_phase_change_ready") is False, "C3H8 report overclaims LPG phase change")

    lng_runtime = validate_runtime(
        staged_root / "lng_ch4_mpicuda",
        LNG_TEMPLATE.name,
        "CH4",
        expect_fire=False,
        final_plot="plt00120",
    )
    lng_warmed_fire_runtime = validate_runtime(
        staged_root / "lng_ch4_warmed_fire_mpicuda",
        LNG_WARMED_FIRE_TEMPLATE.name,
        "CH4",
        expect_fire=True,
        final_plot="plt00500",
    )
    lpg_runtime = validate_runtime(
        staged_root / "lpg_c3h8_mpicuda",
        LPG_TEMPLATE.name,
        "C3H8",
        expect_fire=True,
        final_plot="plt00120",
    )

    summary = {
        "gasified_lng_ch4_surrogate_template_ready": True,
        "gasified_lpg_c3h8_surrogate_template_ready": True,
        "configurable_fuel_species_source_ready": True,
        "ch4_gas_phase_evidence_ready": True,
        "c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_evidence_ready": True,
        "given_gas_source_surrogate_ready": True,
        "gasified_lng_ch4_mpi_cuda_runtime_passed": True,
        "gasified_lng_ch4_cold_source_stable_passed": True,
        "gasified_lng_ch4_cold_source_sustained_fire_claim_allowed": False,
        "gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed": True,
        "gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed": True,
        "gasified_lpg_c3h8_mpi_cuda_runtime_passed": True,
        "gasified_lpg_c3h8_surrogate_fire_probe_passed": True,
        "liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation_ready": False,
        "lng_lpg_production_phase_change_claim_allowed": False,
        "prevents_liquid_phase_overclaim": True,
    }
    evidence = [
        evidence_entry("gasified_lng_ch4_surrogate_input", LNG_TEMPLATE),
        evidence_entry("gasified_lng_ch4_warmed_vapor_fire_input", LNG_WARMED_FIRE_TEMPLATE),
        evidence_entry("gasified_lpg_c3h8_surrogate_input", LPG_TEMPLATE),
        evidence_entry("pelelmex_prob_H", PROB_H),
        evidence_entry("pelelmex_prob_cpp", PROB_CPP),
        evidence_entry("ch4_cold_plume_report", CH4_COLD_REPORT),
        evidence_entry("ch4_mpi_cuda_500step_fire_report", CH4_MPI_CUDA_500_REPORT),
        evidence_entry("c3h8_cpu_cpu_mpi_single_cuda_mpi_cuda_report", C3H8_REPORT),
        evidence_entry("lng_ch4_mpicuda_run_log", staged_root / "lng_ch4_mpicuda" / "run.log"),
        evidence_entry("lng_ch4_mpicuda_run_status", staged_root / "lng_ch4_mpicuda" / "run.status"),
        evidence_entry("lng_ch4_mpicuda_input", staged_root / "lng_ch4_mpicuda" / LNG_TEMPLATE.name),
        evidence_entry("lng_ch4_mpicuda_rank_gpu_wrapper", staged_root / "lng_ch4_mpicuda" / "rank_gpu_wrapper.sh"),
        evidence_entry("lng_ch4_mpicuda_fextrema", staged_root / "lng_ch4_mpicuda" / "fextrema_selected.log"),
        evidence_entry("lng_ch4_warmed_fire_mpicuda_run_log", staged_root / "lng_ch4_warmed_fire_mpicuda" / "run.log"),
        evidence_entry("lng_ch4_warmed_fire_mpicuda_run_status", staged_root / "lng_ch4_warmed_fire_mpicuda" / "run.status"),
        evidence_entry("lng_ch4_warmed_fire_mpicuda_input", staged_root / "lng_ch4_warmed_fire_mpicuda" / LNG_WARMED_FIRE_TEMPLATE.name),
        evidence_entry("lng_ch4_warmed_fire_mpicuda_rank_gpu_wrapper", staged_root / "lng_ch4_warmed_fire_mpicuda" / "rank_gpu_wrapper.sh"),
        evidence_entry("lng_ch4_warmed_fire_mpicuda_fextrema", staged_root / "lng_ch4_warmed_fire_mpicuda" / "fextrema_selected.log"),
        evidence_entry("lpg_c3h8_mpicuda_run_log", staged_root / "lpg_c3h8_mpicuda" / "run.log"),
        evidence_entry("lpg_c3h8_mpicuda_run_status", staged_root / "lpg_c3h8_mpicuda" / "run.status"),
        evidence_entry("lpg_c3h8_mpicuda_input", staged_root / "lpg_c3h8_mpicuda" / LPG_TEMPLATE.name),
        evidence_entry("lpg_c3h8_mpicuda_rank_gpu_wrapper", staged_root / "lpg_c3h8_mpicuda" / "rank_gpu_wrapper.sh"),
        evidence_entry("lpg_c3h8_mpicuda_fextrema", staged_root / "lpg_c3h8_mpicuda" / "fextrema_selected.log"),
        evidence_entry("gasified_surrogate_pipe_rack_stl", staged_root / "lpg_c3h8_mpicuda" / "codex_merged_pipe_rack_obstacles.stl"),
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "Engineering Gasified LNG/LPG Surrogate Capability Boundary",
        "summary": summary,
        "templates": {
            "gasified_lng_ch4_surrogate": lng_template,
            "gasified_lng_ch4_warmed_vapor_fire_surrogate": lng_warmed_fire_template,
            "gasified_lpg_c3h8_surrogate": lpg_template,
        },
        "runtime": {
            "gasified_lng_ch4_mpi_cuda": lng_runtime,
            "gasified_lng_ch4_warmed_vapor_fire_mpi_cuda": lng_warmed_fire_runtime,
            "gasified_lpg_c3h8_mpi_cuda": lpg_runtime,
        },
        "source_model_boundary": {
            "supported_now": [
                "gas-phase fuel source selected by prob.fuel_species",
                "pre-vaporized methane-rich LNG surrogate cloud/source",
                "pre-vaporized and warmed methane-rich LNG fire surrogate after gas has reached flammable thermal conditions",
                "pre-vaporized propane LPG surrogate cloud/source",
                "delayed ignition/fire probes when the selected chemistry mechanism supports the fuel",
            ],
            "not_supported_now": [
                "liquid tank rupture mechanics",
                "flashing two-phase discharge",
                "liquid pool spread and evaporation",
                "cryogenic ground/wall heat-transfer closure",
                "sustained fire validation for still-cold cryogenic LNG vapor clouds",
                "aerosol/droplet rainout and multi-component LNG/LPG fractionation",
            ],
        },
        "evidence": evidence,
    }


def validate_report(data: dict[str, Any], verify_hashes: bool) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    for key in (
        "gasified_lng_ch4_surrogate_template_ready",
        "gasified_lpg_c3h8_surrogate_template_ready",
        "configurable_fuel_species_source_ready",
        "ch4_gas_phase_evidence_ready",
        "c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_evidence_ready",
        "given_gas_source_surrogate_ready",
        "gasified_lng_ch4_mpi_cuda_runtime_passed",
        "gasified_lng_ch4_cold_source_stable_passed",
        "gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed",
        "gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed",
        "gasified_lpg_c3h8_mpi_cuda_runtime_passed",
        "gasified_lpg_c3h8_surrogate_fire_probe_passed",
        "prevents_liquid_phase_overclaim",
    ):
        require(summary.get(key) is True, f"{key} must be true")
    for key in (
        "gasified_lng_ch4_cold_source_sustained_fire_claim_allowed",
        "liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation_ready",
        "lng_lpg_production_phase_change_claim_allowed",
    ):
        require(summary.get(key) is False, f"{key} must be false")
    templates = data.get("templates")
    require(isinstance(templates, dict), "templates section missing")
    require(templates["gasified_lng_ch4_surrogate"]["fuel_species"] == "CH4", "LNG surrogate is not CH4")
    require(templates["gasified_lng_ch4_warmed_vapor_fire_surrogate"]["fuel_species"] == "CH4", "LNG warmed fire surrogate is not CH4")
    require(templates["gasified_lpg_c3h8_surrogate"]["fuel_species"] == "C3H8", "LPG surrogate is not C3H8")
    runtime = data.get("runtime")
    require(isinstance(runtime, dict), "runtime section missing")
    lng_runtime = runtime.get("gasified_lng_ch4_mpi_cuda")
    lng_warmed_fire_runtime = runtime.get("gasified_lng_ch4_warmed_vapor_fire_mpi_cuda")
    lpg_runtime = runtime.get("gasified_lpg_c3h8_mpi_cuda")
    require(isinstance(lng_runtime, dict), "LNG CH4 MPI+CUDA runtime missing")
    require(isinstance(lng_warmed_fire_runtime, dict), "LNG CH4 warmed-vapor fire MPI+CUDA runtime missing")
    require(isinstance(lpg_runtime, dict), "LPG C3H8 MPI+CUDA runtime missing")
    require(lng_runtime.get("rank_mapped") is True and lng_runtime.get("cuda_devices") == 2, "LNG CH4 runtime GPU mapping missing")
    require(lng_runtime.get("peak_temperature", 0.0) > 300.0, "LNG CH4 runtime heating evidence missing")
    require(lng_runtime.get("sustained_fire_probe") is False, "LNG CH4 cold-source run must not claim sustained fire")
    require(lng_warmed_fire_runtime.get("rank_mapped") is True and lng_warmed_fire_runtime.get("cuda_devices") == 2, "LNG CH4 warmed fire runtime GPU mapping missing")
    require(lng_warmed_fire_runtime.get("peak_temperature", 0.0) > 2000.0, "LNG CH4 warmed fire peak temperature missing")
    require(lng_warmed_fire_runtime.get("final_y_h2o_max", 0.0) > 1.0e-5, "LNG CH4 warmed fire water product missing")
    require(lng_warmed_fire_runtime.get("peak_heat_release_abs", 0.0) > 1.0e6, "LNG CH4 warmed fire heat-release evidence missing")
    require(lpg_runtime.get("rank_mapped") is True and lpg_runtime.get("cuda_devices") == 2, "LPG C3H8 runtime GPU mapping missing")
    require(lpg_runtime.get("peak_temperature", 0.0) > 2000.0, "LPG C3H8 fire peak temperature missing")
    require(lpg_runtime.get("final_y_h2o_max", 0.0) > 1.0e-6, "LPG C3H8 water product missing")
    boundary = data.get("source_model_boundary")
    require(isinstance(boundary, dict), "source_model_boundary missing")
    require("flashing two-phase discharge" in boundary.get("not_supported_now", []), "phase-change boundary missing")
    evidence = data.get("evidence")
    require(isinstance(evidence, list) and len(evidence) >= 24, "evidence incomplete")
    if verify_hashes:
        for item in evidence:
            path = Path(item["path"])
            require(path.exists(), f"evidence file missing during verify: {path}")
            require(item.get("sha256") == sha256(path), f"hash mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Gasified LNG/LPG Surrogate Capability Boundary",
        "",
        f"- Status: `{report['status']}`",
        f"- Gasified LNG CH4 surrogate template ready: `{s['gasified_lng_ch4_surrogate_template_ready']}`",
        f"- Gasified LPG C3H8 surrogate template ready: `{s['gasified_lpg_c3h8_surrogate_template_ready']}`",
        f"- Given gas-source surrogate ready: `{s['given_gas_source_surrogate_ready']}`",
        f"- Gasified LNG CH4 MPI+CUDA cold-source runtime passed: `{s['gasified_lng_ch4_mpi_cuda_runtime_passed']}`",
        f"- Gasified LNG CH4 cold-source sustained-fire claim allowed: `{s['gasified_lng_ch4_cold_source_sustained_fire_claim_allowed']}`",
        f"- Gasified LNG CH4 warmed-vapor fire runtime passed: `{s['gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed']}`",
        f"- Gasified LNG CH4 warmed-vapor sustained-fire claim allowed: `{s['gasified_lng_ch4_warmed_vapor_sustained_fire_claim_allowed']}`",
        f"- Gasified LPG C3H8 MPI+CUDA fire runtime passed: `{s['gasified_lpg_c3h8_mpi_cuda_runtime_passed']}`",
        f"- Liquid rupture/flash/pool evaporation ready: `{s['liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation_ready']}`",
        f"- LNG/LPG phase-change production claim allowed: `{s['lng_lpg_production_phase_change_claim_allowed']}`",
        "",
        "## Templates",
        "",
    ]
    for name, item in report["templates"].items():
        lines.append(
            f"- `{name}`: `{item['path']}`, fuel `{item['fuel_species']}`, "
            f"leak_T `{item['leak_temperature']}`, cloud_T `{item['cloud_temperature']}`"
        )
    lines += ["", "## Runtime", ""]
    for name, item in report["runtime"].items():
        lines.append(
            f"- `{name}`: peak T `{item['peak_temperature']:.6g}`, "
            f"peak |HeatRelease| `{item['peak_heat_release_abs']:.6g}`, "
            f"final Y(H2O) `{item['final_y_h2o_max']:.6g}`, "
            f"rank-mapped `{item['rank_mapped']}`"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "Supported now:",
    ]
    lines.extend(f"- {item}" for item in report["source_model_boundary"]["supported_now"])
    lines += ["", "Not supported now:"]
    lines.extend(f"- {item}" for item in report["source_model_boundary"]["not_supported_now"])
    lines += ["", "## Evidence", ""]
    lines.extend(f"- `{item['label']}`: `{item['path']}`" for item in report["evidence"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--staged-root", default=str(DEFAULT_STAGED_ROOT))
    parser.add_argument("--lng-runtime-root", default=str(DEFAULT_LNG_RUNTIME_ROOT))
    parser.add_argument("--lng-warmed-fire-runtime-root", default=str(DEFAULT_LNG_WARMED_FIRE_RUNTIME_ROOT))
    parser.add_argument("--lpg-runtime-root", default=str(DEFAULT_LPG_RUNTIME_ROOT))
    parser.add_argument("--no-stage", action="store_true")
    parser.add_argument("--verify-json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.verify_json:
            data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(data, verify_hashes=True)
            print(f"engineering_gasified_lng_lpg_surrogate VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        validate_report(report, verify_hashes=False)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_gasified_lng_lpg_surrogate PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (ReportError, OSError, json.JSONDecodeError) as exc:
        print(f"engineering_gasified_lng_lpg_surrogate FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
