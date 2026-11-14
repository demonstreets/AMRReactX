#!/usr/bin/env python3
"""Write/verify the DataverseNO AMR source-projection implementation report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION"
STATUS_NOT_READY = "NOT_READY-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION"

DEFAULT_ROOT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811"
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_amr_source_projection_implementation_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_amr_source_projection_implementation_report.md"

FORCES_CPP = Path("external/PeleLMeX/Source/PeleLMeX_Forces.cpp")
CONTRACT_REPORT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_contract_20260811/"
    "dataverse_open_channel_amr_source_projection_contract_report.json"
)
BUILD_MPI_CPU_LOG = DEFAULT_ROOT / "build_mpi_cpu.log"
BUILD_MPI_CUDA_LOG = DEFAULT_ROOT / "build_mpi_cuda.log"
BUILD_MPI_CUDA_SUNDIALS_LOCAL_LOG = DEFAULT_ROOT / "build_mpi_cuda_sundials_local.log"
CUDA_ENV_SCRIPT = Path("tools/codex_setup_cuda126_sundials_env.sh")
CUDA_REPRO_BUILD_SCRIPT = Path("tools/codex_build_h2_leak_mpi_cuda_repro.sh")


class ImplementationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ImplementationError(message)


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
        raise ImplementationError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ImplementationError(f"invalid JSON evidence {path}: {exc}") from exc
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


def extract_get_external_sources(text: str) -> str:
    marker = "PeleLM::getExternalSources"
    idx = text.find(marker)
    require(idx >= 0, "PeleLM::getExternalSources not found")
    brace = text.find("{", idx)
    require(brace >= 0, "getExternalSources opening brace not found")
    depth = 0
    for pos in range(brace, len(text)):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
            if depth == 0:
                return text[idx : pos + 1]
    raise ImplementationError("getExternalSources closing brace not found")


def build_report() -> dict[str, Any]:
    forces_text = FORCES_CPP.read_text(encoding="utf-8", errors="replace")
    body = extract_get_external_sources(forces_text)
    contract = load_json(CONTRACT_REPORT)
    contract_summary = contract.get("summary", {})
    require(
        contract.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-CONTRACT",
        "AMR source-projection contract is not PASS",
    )
    require(isinstance(contract_summary, dict), "contract summary missing")

    checks = {
        "user_source_hook_present": "call_modify_ext_sources" in body,
        "coarse_level_guard_present": "lev < finest_level" in body,
        "pre_user_source_snapshot_present": "ext_src_before" in body and "MultiFab::Copy" in body,
        "fine_mask_constructed": "amrex::makeFineMask" in body,
        "fine_mask_uses_next_level_grids": "grids[lev + 1]" in body,
        "fine_mask_uses_ref_ratio": "refRatio(lev)" in body,
        "mask_has_owner_semantics": re.search(r"makeFineMask\([^;]+,\s*1\s*,\s*0\s*,", body, re.S)
        is not None,
        "restores_non_user_sources_on_fine_covered_coarse_cells": re.search(
            r"if\s*\(\s*mask_arrs\[box_no\]\(i,\s*j,\s*k\)\s*==\s*0\s*\)\s*\{[^}]+"
            r"ext_arrs\[box_no\]\(i,\s*j,\s*k,\s*n\)\s*=\s*before_arrs\[box_no\]\(i,\s*j,\s*k,\s*n\)",
            body,
            re.S,
        )
        is not None,
        "gpu_parallel_restore_present": "amrex::ParallelFor" in body and "AMREX_GPU_DEVICE" in body,
        "restore_synchronized": "amrex::Gpu::streamSynchronize()" in body,
    }
    build_mpi_cpu_text = BUILD_MPI_CPU_LOG.read_text(encoding="utf-8", errors="replace")
    build_checks = {
        "mpi_cpu_build_log_present": BUILD_MPI_CPU_LOG.is_file(),
        "mpi_cpu_build_recompiled_forces": "PeleLMeX_Forces.o" in build_mpi_cpu_text,
        "mpi_cpu_build_linked_executable": "codex_amr_source_projection_impl_cpu3d.gnu.MPI.ex" in build_mpi_cpu_text,
        "mpi_cpu_build_has_success_marker": "SUCCESS" in build_mpi_cpu_text,
        "mpi_cpu_build_has_no_error": " Error " not in build_mpi_cpu_text and "error:" not in build_mpi_cpu_text,
    }
    cuda_build_summary = None
    cuda_log_for_summary = (
        BUILD_MPI_CUDA_SUNDIALS_LOCAL_LOG
        if BUILD_MPI_CUDA_SUNDIALS_LOCAL_LOG.is_file()
        else BUILD_MPI_CUDA_LOG
    )
    if cuda_log_for_summary.is_file():
        cuda_text = cuda_log_for_summary.read_text(encoding="utf-8", errors="replace")
        cuda_build_summary = {
            "log_present": True,
            "log_path": str(cuda_log_for_summary),
            "compiled_forces_object": "PeleLMeX_Forces.o" in cuda_text,
            "linked_executable": (
                "codex_amr_source_projection_impl3d.gnu.MPI.CUDA.ex" in cuda_text
                and "Error 1" not in cuda_text
                and "ld returned 1 exit status" not in cuda_text
                and "CUDA_BUILD_RC=0" in cuda_text
            ),
            "blocked_by_cuda_toolkit_version": "unsupported" in cuda_text and "nvcc version is 12.0" in cuda_text,
            "requires_cuda_12_2_or_newer": "12.2 or newer" in cuda_text,
            "blocked_by_missing_cuda_sundials_link_libraries": "cannot find -lsundials" in cuda_text,
            "uses_cuda_12_6": "/usr/local/cuda-12.6" in cuda_text,
            "uses_local_sundials_cuda": ".local/sundials-cuda-6.4.1" in cuda_text,
        }
    env_script_text = CUDA_ENV_SCRIPT.read_text(encoding="utf-8", errors="replace")
    repro_script_text = CUDA_REPRO_BUILD_SCRIPT.read_text(encoding="utf-8", errors="replace")
    reproducible_cuda_entrypoint_checks = {
        "cuda_env_script_present": CUDA_ENV_SCRIPT.is_file(),
        "cuda_env_uses_cuda_12_6_default": "/usr/local/cuda-12.6" in env_script_text,
        "cuda_env_uses_home_relative_sundials": "${HOME}/.local/sundials-cuda-6.4.1" in env_script_text,
        "cuda_env_exports_sundials_lib_dir": "export SUNDIALS_LIB_DIR" in env_script_text,
        "cuda_repro_build_script_present": CUDA_REPRO_BUILD_SCRIPT.is_file(),
        "cuda_repro_build_sources_env": "codex_setup_cuda126_sundials_env.sh" in repro_script_text,
        "cuda_repro_build_passes_sundials_lib_dir": 'SUNDIALS_LIB_DIR="${SUNDIALS_LIB_DIR}"' in repro_script_text,
        "cuda_repro_build_writes_success_log": "CUDA_BUILD_RC=0" in repro_script_text,
    }
    implementation_ready = all(checks.values()) and all(build_checks.values())
    strict_blocker_still_open = True

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if implementation_ready else STATUS_NOT_READY,
        "summary": {
            "amr_source_projection_implementation_ready": implementation_ready,
            "contract_status": contract["status"],
            "contract_ready": contract_summary.get("amr_source_projection_contract_ready"),
            "framework_level_owner_mask_implemented": checks["fine_mask_constructed"],
            "coarse_cells_covered_by_fine_level_receive_no_user_source_delta": checks[
                "restores_non_user_sources_on_fine_covered_coarse_cells"
            ],
            "non_user_ext_sources_preserved_on_fine_covered_coarse_cells": checks[
                "pre_user_source_snapshot_present"
            ],
            "source_projected_only_on_finest_available_level": implementation_ready,
            "gpu_mpi_safe_restore_path_present": checks["gpu_parallel_restore_present"],
            "mpi_cpu_build_verified": all(build_checks.values()),
            "mpi_cpu_build_log": str(BUILD_MPI_CPU_LOG),
            "mpi_cuda_rebuild_attempted": BUILD_MPI_CUDA_LOG.is_file(),
            "mpi_cuda_source_compile_verified": bool(
                cuda_build_summary and cuda_build_summary["compiled_forces_object"]
            ),
            "mpi_cuda_linked_executable": bool(cuda_build_summary and cuda_build_summary["linked_executable"]),
            "mpi_cuda_reproducible_build_entrypoint_ready": all(
                reproducible_cuda_entrypoint_checks.values()
            ),
            "mpi_cuda_reproducible_build_log": str(cuda_log_for_summary),
            "mpi_cuda_reproducible_build_uses_cuda_12_6": bool(
                cuda_build_summary and cuda_build_summary["uses_cuda_12_6"]
            ),
            "mpi_cuda_reproducible_build_uses_local_sundials_cuda": bool(
                cuda_build_summary and cuda_build_summary["uses_local_sundials_cuda"]
            ),
            "mpi_cuda_rebuild_blocked_by_toolkit_version": bool(
                cuda_build_summary and cuda_build_summary["blocked_by_cuda_toolkit_version"]
            ),
            "mpi_cuda_rebuild_blocked_by_missing_sundials": bool(
                cuda_build_summary
                and cuda_build_summary["blocked_by_missing_cuda_sundials_link_libraries"]
            ),
            "clears_external_plume_reference_blocker": False,
            "strict_external_plume_blocker_cleared": False,
            "strict_blocker_still_open": strict_blocker_still_open,
        },
        "checks": checks,
        "build_checks": build_checks,
        "reproducible_cuda_entrypoint_checks": reproducible_cuda_entrypoint_checks,
        "cuda_build_summary": cuda_build_summary,
        "implementation_notes": [
            "User-defined external sources are still authored through the problem hook.",
            "For coarse levels covered by a finer AMR level, the framework snapshots ext_src before the user hook and restores those cells after the hook.",
            "This preserves pre-existing non-user external sources while preventing user source double counting across coarse/fine overlap.",
            "This implementation satisfies the AMR projection precondition, but a longer DataverseNO plume agreement run is still required for strict external-source credit.",
        ],
        "evidence_files": [
            evidence_entry("pelelmex_forces_cpp", FORCES_CPP),
            evidence_entry("dataverse_amr_source_projection_contract", CONTRACT_REPORT),
            evidence_entry("mpi_cpu_build_log", BUILD_MPI_CPU_LOG),
            evidence_entry("cuda_env_script", CUDA_ENV_SCRIPT),
            evidence_entry("cuda_repro_build_script", CUDA_REPRO_BUILD_SCRIPT),
        ],
    }
    if BUILD_MPI_CUDA_LOG.is_file():
        report["evidence_files"].append(evidence_entry("mpi_cuda_build_failed_probe_log", BUILD_MPI_CUDA_LOG))
    if BUILD_MPI_CUDA_SUNDIALS_LOCAL_LOG.is_file():
        report["evidence_files"].append(
            evidence_entry("mpi_cuda_sundials_local_build_log", BUILD_MPI_CUDA_SUNDIALS_LOCAL_LOG)
        )
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "AMR source-projection implementation is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("amr_source_projection_implementation_ready") is True, "implementation is not ready")
    require(summary.get("contract_ready") is True, "contract is not ready")
    require(summary.get("framework_level_owner_mask_implemented") is True, "framework owner mask missing")
    require(
        summary.get("coarse_cells_covered_by_fine_level_receive_no_user_source_delta") is True,
        "coarse covered-cell user source restore missing",
    )
    require(
        summary.get("non_user_ext_sources_preserved_on_fine_covered_coarse_cells") is True,
        "non-user external source preservation missing",
    )
    require(summary.get("source_projected_only_on_finest_available_level") is True, "finest-owner projection missing")
    require(summary.get("mpi_cpu_build_verified") is True, "MPI CPU build evidence missing")
    require(summary.get("mpi_cuda_source_compile_verified") is True, "MPI CUDA source compile evidence missing")
    require(summary.get("mpi_cuda_linked_executable") is True, "MPI CUDA executable link evidence missing")
    require(
        summary.get("mpi_cuda_reproducible_build_entrypoint_ready") is True,
        "MPI CUDA reproducible build entrypoint missing",
    )
    require(
        summary.get("mpi_cuda_reproducible_build_uses_cuda_12_6") is True,
        "MPI CUDA build did not use CUDA 12.6 evidence",
    )
    require(
        summary.get("mpi_cuda_reproducible_build_uses_local_sundials_cuda") is True,
        "MPI CUDA build did not use local SUNDIALS CUDA evidence",
    )
    require(summary.get("strict_external_plume_blocker_cleared") is False, "implementation must not clear strict blocker")
    require(summary.get("strict_blocker_still_open") is True, "strict blocker state missing")
    checks = data.get("checks")
    require(isinstance(checks, dict), "missing checks")
    for key, value in checks.items():
        require(value is True, f"implementation check failed: {key}")
    build_checks = data.get("build_checks")
    require(isinstance(build_checks, dict), "missing build_checks")
    for key, value in build_checks.items():
        require(value is True, f"build check failed: {key}")
    cuda_entry = data.get("reproducible_cuda_entrypoint_checks")
    require(isinstance(cuda_entry, dict), "missing reproducible_cuda_entrypoint_checks")
    for key, value in cuda_entry.items():
        require(value is True, f"CUDA entrypoint check failed: {key}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], output: Path) -> None:
    summary = report["summary"]
    lines = [
        "# DataverseNO AMR Source Projection Implementation",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- Implementation ready: `{summary['amr_source_projection_implementation_ready']}`",
        f"- Framework owner mask: `{summary['framework_level_owner_mask_implemented']}`",
        f"- Coarse covered-cell user delta removed: `{summary['coarse_cells_covered_by_fine_level_receive_no_user_source_delta']}`",
        f"- Non-user external sources preserved: `{summary['non_user_ext_sources_preserved_on_fine_covered_coarse_cells']}`",
        f"- MPI CPU build verified: `{summary['mpi_cpu_build_verified']}`",
        f"- MPI CUDA source compile verified: `{summary['mpi_cuda_source_compile_verified']}`",
        f"- MPI CUDA linked executable: `{summary['mpi_cuda_linked_executable']}`",
        f"- MPI CUDA reproducible build entrypoint: `{summary['mpi_cuda_reproducible_build_entrypoint_ready']}`",
        f"- MPI CUDA build uses CUDA 12.6: `{summary['mpi_cuda_reproducible_build_uses_cuda_12_6']}`",
        f"- MPI CUDA build uses local SUNDIALS CUDA: `{summary['mpi_cuda_reproducible_build_uses_local_sundials_cuda']}`",
        f"- MPI CUDA rebuild blocked by toolkit version: `{summary['mpi_cuda_rebuild_blocked_by_toolkit_version']}`",
        f"- MPI CUDA rebuild blocked by missing SUNDIALS: `{summary['mpi_cuda_rebuild_blocked_by_missing_sundials']}`",
        f"- Strict external plume blocker cleared: `{summary['strict_external_plume_blocker_cleared']}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in report["checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {item}" for item in report["implementation_notes"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(
            "dataverse_open_channel_amr_source_projection_implementation "
            f"VERIFY-PASS json={args.verify_json} status={data['status']}"
        )
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(
        "dataverse_open_channel_amr_source_projection_implementation "
        f"PASS json={output_json} md={output_md} status={report['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
