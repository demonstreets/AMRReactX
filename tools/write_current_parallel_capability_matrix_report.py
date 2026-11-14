#!/usr/bin/env python3
"""Write/verify the current CPU/GPU parallel capability matrix report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX"
STATUS_NOT_READY = "NOT_READY-CURRENT-PARALLEL-CAPABILITY-MATRIX"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_parallel_capability_matrix_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_parallel_capability_matrix_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_parallel_capability_matrix_report.md"


CAPABILITIES: dict[str, dict[str, Any]] = {
    "engineering_h2_leak_diffusion_fire": {
        "claim": "H2 plant/tank-farm/pipe-rack leak, dispersion, ignition, and reacting fire can run on CPU/MPI, single CUDA GPU, and multi-GPU MPI+CUDA in the current user-priority scope.",
        "cpu_mpi": {
            "path": "docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.json",
            "status": "PASS-PRODUCTION-MESH-FULL-DURATION-CAMPAIGN",
            "mode": "multi-core CPU / MPI",
        },
        "single_gpu": {
            "path": "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_cuda_2000step_20260727/pipe_rack_direct_reacting_cuda_report.json",
            "status": "PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED",
            "mode": "single CUDA GPU",
        },
        "multi_gpu_mpi_cuda": {
            "path": "docs/codex_audit/evidence/engineering_h2_pipe_rack_mpi_cuda_long_revalidation_20260731/pipe_rack_direct_reacting_mpi_cuda_report.json",
            "status": "PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-SUSTAINED",
            "mode": "multi-GPU MPI+CUDA",
        },
        "integration_evidence": [
            {
                "path": "docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728/h2_integrated_initial_acceptance_report.json",
                "status": "PASS-H2-INTEGRATED-ENGINEERING-INITIAL-ACCEPTANCE",
            },
            {
                "path": "docs/codex_audit/evidence/engineering_h2_large_acceptance_20260727/h2_large_acceptance_report.json",
                "status": "PASS-H2-LARGE-ENGINEERING-ACCEPTANCE",
            },
            {
                "path": "docs/codex_audit/evidence/engineering_h2_pipe_rack_gpu_fire_obstacle_20260727/pipe_rack_gpu_fire_obstacle_report.json",
                "status": "PASS-H2-PIPE-RACK-GPU-FIRE-OBSTACLE-SMOKE",
            },
        ],
        "limitation": "Current engineering production credibility excludes strict external plume-shape agreement, real CAD cleanup, and calibrated radiation/overpressure closure until controlled artifacts are supplied.",
    },
    "engineering_multifuel_lng_lpg_surrogate_sources": {
        "claim": "Engineering gas-source cases can be configured for H2, CH4, C3H8, gasified LNG/CH4, gasified LPG/C3H8, and external vaporization schedules with CPU/MPI, single CUDA GPU, and MPI+CUDA evidence in the current user-priority scope.",
        "cpu_mpi": {
            "path": "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json",
            "status": "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
            "mode": "multi-fuel gas-source CPU/MPI evidence",
            "summary_true": [
                "source_fuel_species_configurable",
                "ch4_delayed_ignition_cpu_mpi_fire_probe_passed",
                "c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_probe_passed",
            ],
        },
        "single_gpu": {
            "path": "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json",
            "status": "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
            "mode": "multi-fuel gas-source single CUDA evidence",
            "summary_true": [
                "source_fuel_species_configurable",
                "ch4_delayed_ignition_single_cuda_fire_probe_passed",
                "c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_probe_passed",
                "external_vaporization_multifuel_timeseries_cuda_passed",
            ],
        },
        "multi_gpu_mpi_cuda": {
            "path": "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json",
            "status": "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
            "mode": "multi-fuel gasified LNG/LPG MPI+CUDA evidence",
            "summary_true": [
                "source_fuel_species_configurable",
                "ch4_delayed_ignition_mpi_cuda_500step_fire_probe_passed",
                "c3h8_gas_phase_cpu_mpi_cuda_probe_passed",
                "gasified_lng_ch4_warmed_vapor_mpi_cuda_fire_probe_passed",
                "gasified_lpg_c3h8_mpi_cuda_fire_probe_passed",
                "liquefied_release_vaporization_source_model_cuda_smoke_passed",
            ],
        },
        "integration_evidence": [
            {
                "path": "docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/engineering_multi_fuel_template_catalog_report.json",
                "status": "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG",
            },
            {
                "path": "docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/engineering_gasified_lng_lpg_surrogate_report.json",
                "status": "PASS-ENGINEERING-GASIFIED-LNG-LPG-SURROGATE-BOUNDARY",
            },
            {
                "path": "docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811/engineering_liquefied_phase_change_overclaim_guard_report.json",
                "status": "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD",
            },
        ],
        "limitation": "This is evidence for gas-phase configurable-source and screening vaporization workflows; it does not claim CFD-internal flashing discharge, liquid pool spread, boiling, or pool evaporation.",
    },
    "academic_gas_detonation": {
        "claim": "Gas-phase detonation can run on CPU/MPI-oriented gates, a single CUDA GPU, and multi-GPU MPI+CUDA detonation runtime gates in the current academic gas priority scope.",
        "cpu_mpi": {
            "path": "docs/codex_audit/evidence/academic_gas_detonation_priority_matrix_20260731/academic_gas_detonation_priority_matrix_report.json",
            "status": "PASS-ACADEMIC-GAS-DETONATION-PRIORITY-MATRIX",
            "mode": "CPU/MPI-capable gas detonation priority matrix",
        },
        "single_gpu": {
            "path": "docs/codex_audit/evidence/academic_gas_detonation_single_cuda_20260803/academic_gas_detonation_single_cuda_report.json",
            "status": "PASS-ACADEMIC-GAS-DETONATION-SINGLE-CUDA",
            "mode": "1-rank / 1-device CUDA gas detonation",
            "summary_true": ["academic_gas_detonation_single_cuda_ready"],
        },
        "multi_gpu_mpi_cuda": {
            "path": "docs/codex_audit/evidence/academic_gas_detonation_mpi_cuda_20260731/academic_gas_detonation_mpi_cuda_report.json",
            "status": "PASS-ACADEMIC-GAS-DETONATION-MPI-CUDA",
            "mode": "2-rank / 2-device MPI+CUDA gas detonation",
        },
        "integration_evidence": [],
        "limitation": "The gate demonstrates current runtime capability and stability, not final publication-grade grid convergence for every mechanism/domain variant.",
    },
    "academic_gas_liquid_twophase_detonation": {
        "claim": "Gas-liquid/two-phase droplet/spray detonation-adjacent capability can run on CPU-oriented two-phase gates, single GPU, and extended 2-GPU MPI+CUDA reacting spray gates.",
        "cpu_mpi": {
            "path": "docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/academic_twophase_broader_matrix_report.json",
            "status": "PASS-ACADEMIC-TWOPHASE-BROADER-MATRIX-AUDIT",
            "mode": "CPU-oriented broader two-phase matrix",
        },
        "single_gpu": {
            "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_cuda_scout_20260731/academic_gas_liquid_detonation_cuda_scout_report.json",
            "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CUDA-SCOUT",
            "mode": "single CUDA GPU reacting spray scout",
            "summary_true": ["single_gpu_reacting_spray_ready"],
        },
        "multi_gpu_mpi_cuda": {
            "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json",
            "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-EXTENDED",
            "mode": "1000-step 2-rank / 2-device MPI+CUDA reacting spray",
            "summary_true": ["mpi_cuda_reacting_spray_1000step_ready"],
        },
        "integration_evidence": [
            {
                "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_certification_20260731/academic_gas_liquid_detonation_certification_report.json",
                "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CERTIFICATION",
            },
            {
                "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_long_20260803/academic_gas_liquid_detonation_mpi_cuda_long_report.json",
                "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-LONG",
            },
        ],
        "limitation": "The 1000-step MPI+CUDA gate is a reduced-resolution stability proof for reacting spray coupling; final quantitative two-phase detonation validation still needs case-specific grid convergence and external comparison.",
    },
}


STRICT_BLOCKER_PATH = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)
CURRENT_SCOPE_PATH = Path(
    "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
    "master_plan_current_scope_verification_report.json"
)
ACADEMIC_SCOPE_PATH = Path(
    "docs/codex_audit/evidence/academic_current_priority_scope_20260731/"
    "academic_current_priority_scope_report.json"
)


class CapabilityMatrixError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CapabilityMatrixError(message)


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
        raise CapabilityMatrixError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CapabilityMatrixError(f"invalid JSON evidence {path}: {exc}") from exc
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


def check_report(spec: dict[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    path = Path(spec["path"])
    data = load_json(path)
    failures: list[str] = []
    if data.get("status") != spec["status"]:
        failures.append(f"status {data.get('status')!r} != {spec['status']!r}")
    summary = data.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    for key in spec.get("summary_true", []):
        if summary.get(key) is not True:
            failures.append(f"summary.{key} is not true")
    return not failures, data, failures


def build_mode_entry(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ready, data, failures = check_report(spec)
    path = Path(spec["path"])
    return (
        {
            "mode": spec["mode"],
            "ready": ready,
            "status": data.get("status"),
            "expected_status": spec["status"],
            "path": str(path),
            "failures": failures,
        },
        evidence_entry(spec["mode"], path),
    )


def build_report() -> dict[str, Any]:
    evidence_files: list[dict[str, Any]] = []
    capabilities: dict[str, Any] = {}

    for name, spec in CAPABILITIES.items():
        mode_results: dict[str, Any] = {}
        for mode in ["cpu_mpi", "single_gpu", "multi_gpu_mpi_cuda"]:
            entry, evidence = build_mode_entry(spec[mode])
            mode_results[mode] = entry
            evidence_files.append(evidence)

        integration_results = []
        for item in spec.get("integration_evidence", []):
            ready, data, failures = check_report(item)
            path = Path(item["path"])
            integration_results.append(
                {
                    "ready": ready,
                    "status": data.get("status"),
                    "expected_status": item["status"],
                    "path": str(path),
                    "failures": failures,
                }
            )
            evidence_files.append(evidence_entry(f"{name}_integration", path))

        capabilities[name] = {
            "claim": spec["claim"],
            "ready": all(item["ready"] for item in mode_results.values()) and all(
                item["ready"] for item in integration_results
            ),
            "modes": mode_results,
            "integration_evidence": integration_results,
            "limitation": spec["limitation"],
        }

    strict_blocker = load_json(STRICT_BLOCKER_PATH)
    current_scope = load_json(CURRENT_SCOPE_PATH)
    academic_scope = load_json(ACADEMIC_SCOPE_PATH)
    evidence_files.extend(
        [
            evidence_entry("strict_blocker_matrix", STRICT_BLOCKER_PATH),
            evidence_entry("master_plan_current_scope_verification", CURRENT_SCOPE_PATH),
            evidence_entry("academic_current_priority_scope", ACADEMIC_SCOPE_PATH),
        ]
    )

    all_capabilities_ready = all(item["ready"] for item in capabilities.values())
    current_scope_ready = current_scope.get("status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"
    academic_scope_ready = academic_scope.get("status") == "PASS-ACADEMIC-CURRENT-PRIORITY-SCOPE"
    strict_open = strict_blocker.get("summary", {}).get("open_strict_blockers", [])
    status = STATUS_PASS if all_capabilities_ready and current_scope_ready and academic_scope_ready else STATUS_NOT_READY

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "current_parallel_capability_matrix_ready": status == STATUS_PASS,
            "scenario_count": len(capabilities),
            "ready_scenario_count": sum(1 for item in capabilities.values() if item["ready"]),
            "cpu_mpi_ready_for_all_current_scenarios": all(
                item["modes"]["cpu_mpi"]["ready"] for item in capabilities.values()
            ),
            "single_gpu_ready_for_all_current_scenarios": all(
                item["modes"]["single_gpu"]["ready"] for item in capabilities.values()
            ),
            "multi_gpu_mpi_cuda_ready_for_all_current_scenarios": all(
                item["modes"]["multi_gpu_mpi_cuda"]["ready"] for item in capabilities.values()
            ),
            "current_scope_verification_ready": current_scope_ready,
            "academic_current_priority_ready": academic_scope_ready,
            "strict_master_plan_complete": strict_blocker.get("summary", {}).get("strict_master_plan_complete"),
            "open_strict_blocker_count": strict_blocker.get("summary", {}).get("open_strict_blocker_count"),
            "open_strict_blockers": strict_open,
        },
        "capabilities": capabilities,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("scenario_count") == 4, "unexpected scenario_count")
    require(summary.get("ready_scenario_count") == 4, "not all scenarios are ready")
    require(summary.get("cpu_mpi_ready_for_all_current_scenarios") is True, "CPU/MPI is not ready for all scenarios")
    require(summary.get("single_gpu_ready_for_all_current_scenarios") is True, "single GPU is not ready for all scenarios")
    require(summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True, "multi-GPU MPI+CUDA is not ready for all scenarios")
    require(summary.get("current_scope_verification_ready") is True, "current-scope verification is not ready")
    require(summary.get("academic_current_priority_ready") is True, "academic current-priority scope is not ready")
    require(summary.get("strict_master_plan_complete") is False, "strict master-plan blocker state should remain explicit")
    require(summary.get("open_strict_blocker_count") == 3, "unexpected strict blocker count")

    capabilities = data.get("capabilities")
    require(isinstance(capabilities, dict), "missing capabilities")
    require(set(capabilities) == set(CAPABILITIES), "unexpected capability set")
    for name, capability in capabilities.items():
        require(capability.get("ready") is True, f"{name} is not ready")
        modes = capability.get("modes")
        require(isinstance(modes, dict), f"{name} missing modes")
        require(set(modes) == {"cpu_mpi", "single_gpu", "multi_gpu_mpi_cuda"}, f"{name} mode set mismatch")
        for mode, result in modes.items():
            require(result.get("ready") is True, f"{name}.{mode} is not ready: {result.get('failures')}")
            path = Path(result.get("path", ""))
            require(path.is_file(), f"{name}.{mode} missing evidence path: {path}")
        for idx, result in enumerate(capability.get("integration_evidence", [])):
            require(result.get("ready") is True, f"{name}.integration[{idx}] is not ready: {result.get('failures')}")
            path = Path(result.get("path", ""))
            require(path.is_file(), f"{name}.integration[{idx}] missing evidence path: {path}")

    evidence_files = data.get("evidence_files")
    require(isinstance(evidence_files, list) and evidence_files, "missing evidence_files")
    if verify_hashes:
        for item in evidence_files:
            path = Path(item["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(item["sha256"] == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Current Parallel Capability Matrix",
        "",
        f"- Status: `{report['status']}`",
        f"- Generated: `{report['generated_at_utc']}`",
        f"- CPU/MPI ready for all current scenarios: `{report['summary']['cpu_mpi_ready_for_all_current_scenarios']}`",
        f"- Single GPU ready for all current scenarios: `{report['summary']['single_gpu_ready_for_all_current_scenarios']}`",
        f"- Multi-GPU MPI+CUDA ready for all current scenarios: `{report['summary']['multi_gpu_mpi_cuda_ready_for_all_current_scenarios']}`",
        f"- Strict master-plan complete: `{report['summary']['strict_master_plan_complete']}`",
        f"- Open strict blockers: `{report['summary']['open_strict_blocker_count']}`",
        "",
        "| Scenario | CPU/MPI | Single GPU | Multi-GPU MPI+CUDA | Limitation |",
        "|---|---:|---:|---:|---|",
    ]
    for name, capability in report["capabilities"].items():
        modes = capability["modes"]
        lines.append(
            "| "
            + name
            + " | "
            + str(modes["cpu_mpi"]["ready"])
            + " | "
            + str(modes["single_gpu"]["ready"])
            + " | "
            + str(modes["multi_gpu_mpi_cuda"]["ready"])
            + " | "
            + capability["limitation"].replace("|", "/")
            + " |"
        )
    lines.append("")
    lines.append("## Open Strict Blockers")
    lines.append("")
    for blocker in report["summary"]["open_strict_blockers"]:
        lines.append(f"- `{blocker}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_JSON), help="output JSON report path")
    parser.add_argument("--markdown", default=str(DEFAULT_OUTPUT_MD), help="output Markdown report path")
    parser.add_argument("--verify-json", help="verify an existing JSON report instead of writing one")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_parallel_capability_matrix VERIFY-PASS {args.verify_json}")
        return 0

    report = build_report()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, Path(args.markdown))
    print(f"wrote {output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
