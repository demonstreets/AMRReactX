#!/usr/bin/env python3
"""Write/verify the DataverseNO AMR source-projection contract report."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-CONTRACT"
STATUS_NOT_READY = "NOT_READY-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-CONTRACT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_contract_20260811")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_amr_source_projection_contract_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_amr_source_projection_contract_report.md"

PROB_HEADER = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
REFINED_PROJECTION_PROBE = Path(
    "docs/codex_audit/evidence/dataverse_refined_source_projection_probe_mpi_cuda_20260807/"
    "dataverse_refined_source_projection_probe_report.json"
)
FULL_CHANNEL_DX025_1000 = Path(
    "docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_cuda_20260807/"
    "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_report.json"
)
PHYSICS_ALIGNMENT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_physics_alignment_20260804/"
    "dataverse_open_channel_physics_alignment_report.json"
)
INPUT_DECKS = [
    Path("examples/engineering/h2_leak_3d/input.dataverse_refined_source_projection_probe_3d"),
    Path("examples/engineering/h2_leak_3d/input.dataverse_full_channel_refined_source_dx025_1000step_dt5em6_3d"),
]


class AmrSourceProjectionContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AmrSourceProjectionContractError(message)


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
        raise AmrSourceProjectionContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AmrSourceProjectionContractError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def read_kv_input(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, raw = stripped.split("=", 1)
        out[key.strip()] = raw.strip()
    return out


def floats(raw: str) -> list[float]:
    values = [float(item) for item in raw.split()]
    require(all(math.isfinite(value) for value in values), f"non-finite value in {raw!r}")
    return values


def input_dx(path: Path) -> list[float]:
    kv = read_kv_input(path)
    lo = floats(kv["geometry.prob_lo"])
    hi = floats(kv["geometry.prob_hi"])
    n_cell = [int(float(item)) for item in kv["amr.n_cell"].split()]
    return [(right - left) / n for left, right, n in zip(lo, hi, n_cell)]


def build_report() -> dict[str, Any]:
    header_text = PROB_HEADER.read_text(encoding="utf-8", errors="replace")
    refined = load_json(REFINED_PROJECTION_PROBE)
    full_1000 = load_json(FULL_CHANNEL_DX025_1000)
    physics = load_json(PHYSICS_ALIGNMENT)

    refined_summary = refined.get("summary", {})
    full_summary = full_1000.get("summary", {})
    physics_summary = physics.get("summary", {})

    uses_cell_centered_active_volume = "Leak::cell_centered_active_volume" in header_text
    uses_current_geometry_cell_size = "geomdata.CellSize" in header_text
    lacks_level_aware_mask = not re.search(
        r"fine[_ ]level|covered[_ ]cell|level_mask|level_aware|source_projection_level",
        header_text,
        re.I,
    )
    lacks_finest_level_owner_guard = not re.search(
        r"finest[_ ]level|source[_ ]owner|covered[_ ]cell", header_text, re.I
    )
    applies_source_to_all_ext_src_tiles = "amrex::ParallelFor(*ext_src" in header_text

    experimental_radius = 0.0023
    full_dx = [float(value) for value in full_summary.get("dx_m", [])]
    refined_dx = [float(value) for value in refined_summary.get("dx_m", [])]
    target_dx = experimental_radius
    current_full_min_dx = min(full_dx) if full_dx else math.inf
    current_refined_min_dx = min(refined_dx) if refined_dx else math.inf
    required_refinement_from_full_dx025 = math.ceil(current_full_min_dx / target_dx) if math.isfinite(current_full_min_dx) else None
    recommended_refinement_ratio = 16
    recommended_finest_dx = current_full_min_dx / recommended_refinement_ratio if math.isfinite(current_full_min_dx) else None
    recommended_cells_per_radius = experimental_radius / recommended_finest_dx if recommended_finest_dx else None

    input_dx_map = {str(path): input_dx(path) for path in INPUT_DECKS}
    current_single_level_projection_ready = (
        refined.get("status") == "PASS-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA"
        and refined_summary.get("active_volume_equals_single_cell") is True
        and refined_summary.get("strict_blocker_still_open") is True
        and full_1000.get("status") == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA"
        and full_summary.get("active_volume_equals_single_cell") is True
        and full_summary.get("strict_blocker_still_open") is True
    )
    contract_ready = (
        current_single_level_projection_ready
        and physics.get("status") == "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS"
        and uses_cell_centered_active_volume
        and uses_current_geometry_cell_size
        and applies_source_to_all_ext_src_tiles
        and lacks_level_aware_mask
        and lacks_finest_level_owner_guard
        and recommended_refinement_ratio >= 8
        and recommended_cells_per_radius is not None
        and recommended_cells_per_radius >= 1.0
    )

    required_acceptance = {
        "source_projected_only_on_finest_available_level": True,
        "coarse_cells_covered_by_fine_level_receive_zero_source": True,
        "sum_active_volume_over_all_levels_counts_each_physical_cell_once": True,
        "source_mass_integral_conserved_across_amr_regrid": True,
        "gpu_mpi_parity_for_projected_source_mass": True,
        "dataverse_agreement_not_cleared_by_contract_alone": True,
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if contract_ready else STATUS_NOT_READY,
        "summary": {
            "amr_source_projection_contract_ready": contract_ready,
            "current_source_projection_is_single_level_cell_centered": True,
            "current_single_level_projection_probe_ready": current_single_level_projection_ready,
            "uses_cell_centered_active_volume": uses_cell_centered_active_volume,
            "uses_current_geometry_cell_size": uses_current_geometry_cell_size,
            "applies_source_to_all_ext_src_tiles": applies_source_to_all_ext_src_tiles,
            "lacks_level_aware_mask": lacks_level_aware_mask,
            "lacks_finest_level_owner_guard": lacks_finest_level_owner_guard,
            "experimental_orifice_radius_m": experimental_radius,
            "target_finest_dx_m": target_dx,
            "current_full_channel_min_dx_m": current_full_min_dx,
            "current_refined_probe_min_dx_m": current_refined_min_dx,
            "required_refinement_from_full_dx025": required_refinement_from_full_dx025,
            "recommended_refinement_ratio_from_dx025": recommended_refinement_ratio,
            "recommended_finest_dx_m": recommended_finest_dx,
            "recommended_cells_per_orifice_radius": recommended_cells_per_radius,
            "physics_alignment_status": physics.get("status"),
            "physics_alignment_active_cell_count_for_experimental_radius": physics_summary.get(
                "active_cell_count_for_experimental_radius"
            ),
            "strict_external_plume_blocker_cleared": False,
            "clears_external_plume_reference_blocker": False,
            "strict_blocker_still_open": True,
        },
        "required_acceptance": required_acceptance,
        "input_dx": input_dx_map,
        "implementation_notes": [
            "The current h2_leak_3d source uses cell-centered active volume on the GeometryData passed to modify_ext_sources.",
            "A strict AMR implementation must normalize over the finest uncovered cells only, avoiding coarse/fine double counting.",
            "The contract recommends at least 16x refinement from dx=0.025 m so the 2.3 mm Dataverse orifice radius is represented by at least one finest cell radius.",
            "Passing this contract is a precondition for a future longer Dataverse plume-shape agreement run; it does not clear the strict blocker by itself.",
        ],
        "evidence_files": [
            evidence_entry("h2_leak_3d_prob_header", PROB_HEADER),
            evidence_entry("dataverse_refined_source_projection_probe", REFINED_PROJECTION_PROBE),
            evidence_entry("dataverse_full_channel_refined_source_dx025_1000step_dt5em6", FULL_CHANNEL_DX025_1000),
            evidence_entry("dataverse_physics_alignment", PHYSICS_ALIGNMENT),
        ]
        + [evidence_entry(f"input_deck_{idx}", path) for idx, path in enumerate(INPUT_DECKS)],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "AMR source-projection contract is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("amr_source_projection_contract_ready") is True, "contract is not ready")
    require(summary.get("current_single_level_projection_probe_ready") is True, "single-level projection evidence missing")
    require(summary.get("uses_cell_centered_active_volume") is True, "cell-centered active-volume implementation missing")
    require(summary.get("uses_current_geometry_cell_size") is True, "GeometryData cell-size use missing")
    require(summary.get("lacks_level_aware_mask") is True, "contract no longer matches implementation: level-aware mask detected")
    require(summary.get("lacks_finest_level_owner_guard") is True, "contract no longer matches implementation: finest-level guard detected")
    require(summary.get("recommended_refinement_ratio_from_dx025") >= 8, "recommended refinement ratio too small")
    require(summary.get("recommended_cells_per_orifice_radius") >= 1.0, "recommended finest dx does not resolve radius")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "contract must not clear strict blocker")
    require(summary.get("clears_external_plume_reference_blocker") is False, "contract overclaims external plume blocker")
    require(summary.get("strict_blocker_still_open") is True, "strict blocker state missing")
    required = data.get("required_acceptance")
    require(isinstance(required, dict), "missing required_acceptance")
    for key, value in required.items():
        require(value is True, f"required acceptance item is not asserted: {key}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], output: Path) -> None:
    summary = report["summary"]
    lines = [
        "# DataverseNO AMR Source Projection Contract",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- Contract ready: `{summary['amr_source_projection_contract_ready']}`",
        f"- Current projection: single-level cell-centered = `{summary['current_source_projection_is_single_level_cell_centered']}`",
        f"- Experimental radius: `{summary['experimental_orifice_radius_m']}` m",
        f"- Current full-channel min dx: `{summary['current_full_channel_min_dx_m']}` m",
        f"- Recommended refinement ratio from dx=0.025 m: `{summary['recommended_refinement_ratio_from_dx025']}`",
        f"- Recommended finest dx: `{summary['recommended_finest_dx_m']}` m",
        f"- Strict blocker cleared: `{summary['strict_external_plume_blocker_cleared']}`",
        "",
        "## Required Acceptance",
        "",
    ]
    for key in report["required_acceptance"]:
        lines.append(f"- `{key}`")
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
        print(f"dataverse_open_channel_amr_source_projection_contract VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"dataverse_open_channel_amr_source_projection_contract PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
