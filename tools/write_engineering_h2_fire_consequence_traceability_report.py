#!/usr/bin/env python3
"""Audit traceability from H2 reacting-fire evidence to consequence screening metrics."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-CONSEQUENCE-TRACEABILITY"
DEFAULT_FIRE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_fire_consequence_metrics_20260727/"
    "fire_consequence_metrics_report.json"
)
DEFAULT_DIRECT_CUDA = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_cuda_1000step_20260727/"
    "pipe_rack_direct_reacting_cuda_report.json"
)
DEFAULT_LARGEGRID_MPI_CUDA = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_20260727/"
    "pipe_rack_direct_reacting_mpi_cuda_report.json"
)
DEFAULT_RESTART = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_restart_20260727/"
    "pipe_rack_reacting_mpi_cuda_restart_report.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_consequence_traceability_20260727"
)


class TraceabilityError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TraceabilityError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TraceabilityError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TraceabilityError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


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


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def assert_close(name: str, actual: float, expected: float, rel_tol: float = 1.0e-10) -> dict[str, Any]:
    abs_error = abs(actual - expected)
    rel_error = abs_error / max(abs(expected), 1.0e-300)
    passed = rel_error <= rel_tol
    require(passed, f"{name} mismatch: actual={actual} expected={expected} rel_error={rel_error}")
    return {
        "name": name,
        "actual": actual,
        "expected": expected,
        "abs_error": abs_error,
        "rel_error": rel_error,
        "rel_tol": rel_tol,
        "passed": passed,
    }


def monotonic_decreasing(name: str, rows: list[dict[str, Any]], value_key: str) -> dict[str, Any]:
    previous_distance = -math.inf
    previous_value = math.inf
    distances: list[float] = []
    values: list[float] = []
    for row in rows:
        distance = row.get("distance_m")
        value = row.get(value_key)
        require(finite_number(distance) and float(distance) > previous_distance, f"{name} distances not increasing")
        require(finite_number(value) and float(value) > 0.0, f"{name} has nonpositive value")
        require(float(value) <= previous_value + 1.0e-9, f"{name} is not monotonic decreasing")
        previous_distance = float(distance)
        previous_value = float(value)
        distances.append(previous_distance)
        values.append(previous_value)
    return {
        "name": name,
        "distances_m": distances,
        "values": values,
        "passed": True,
    }


def sustained_checks(report: dict[str, Any], *, min_outputs: int, min_y_h2o: float) -> dict[str, Any]:
    plot = report.get("plotfile_checks", {})
    checks = plot.get("sustained_reaction_checks", {})
    require(isinstance(checks, dict), "missing sustained reaction checks")
    outputs = int(checks.get("sustained_output_count", 0))
    final_y_h2o = float(checks.get("final_y_h2o_max", 0.0))
    require(outputs >= min_outputs, f"too few sustained reaction outputs: {outputs}")
    require(final_y_h2o >= min_y_h2o, f"final Y(H2O) too small: {final_y_h2o}")
    return {
        "status": report.get("status"),
        "final_time": checks.get("final_time", plot.get("final_time")),
        "sustained_output_count": outputs,
        "final_y_h2o_max": final_y_h2o,
        "passed": True,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    fire_path = Path(args.fire_report)
    direct_path = Path(args.direct_cuda_report)
    largegrid_mpi_path = Path(args.largegrid_mpi_cuda_report)
    restart_path = Path(args.restart_report)

    fire = load_json(fire_path)
    direct = load_json(direct_path)
    largegrid_mpi = load_json(largegrid_mpi_path)
    restart = load_json(restart_path)

    require(fire.get("status") == "PASS-SCREENING", "fire consequence report is not PASS-SCREENING")
    require(fire.get("model_scope") == "engineering_screening_not_calibrated", "fire report model_scope changed")
    require(fire.get("clears_calibrated_fire_consequence_blocker") is False, "screening report must not clear blocker")
    summary = fire.get("summary", {})
    inputs = fire.get("inputs", {})
    require(isinstance(summary, dict) and isinstance(inputs, dict), "fire report summary/inputs missing")

    total_h2_mass = float(summary["total_h2_mass_kg"])
    final_time = float(summary["leak_final_time_s"])
    cloud_h2_mass = float(summary["flammable_cloud_h2_mass_kg"])
    lhv = float(inputs["h2_lhv_j_per_kg"])
    tnt_j_per_kg = float(inputs["tnt_j_per_kg"])
    radiative_fraction = float(inputs["radiative_fraction"])
    blast_efficiency = float(inputs["blast_efficiency"])
    burn_duration = float(inputs["assumed_burn_duration_s"])
    require(total_h2_mass > 0.0 and final_time > 0.0 and cloud_h2_mass > 0.0, "fire report mass/time invalid")

    source_hrr = total_h2_mass / final_time * lhv
    cloud_energy = cloud_h2_mass * lhv
    cloud_hrr = cloud_energy / burn_duration
    source_radiative_power = radiative_fraction * source_hrr
    cloud_radiative_power = radiative_fraction * cloud_hrr
    tnt_mass = cloud_energy * blast_efficiency / tnt_j_per_kg

    formula_checks = [
        assert_close("source_limited_heat_release_w", float(summary["source_limited_heat_release_w"]), source_hrr),
        assert_close("flammable_cloud_energy_j", float(summary["flammable_cloud_energy_j"]), cloud_energy),
        assert_close("cloud_average_heat_release_w", float(summary["cloud_average_heat_release_w"]), cloud_hrr),
        assert_close("source_limited_radiative_power_w", float(summary["source_limited_radiative_power_w"]), source_radiative_power),
        assert_close("cloud_average_radiative_power_w", float(summary["cloud_average_radiative_power_w"]), cloud_radiative_power),
        assert_close("tnt_equivalent_mass_kg", float(summary["tnt_equivalent_mass_kg"]), tnt_mass),
    ]

    radiation = fire.get("radiation_by_distance", [])
    overpressure = fire.get("overpressure_by_distance", [])
    require(isinstance(radiation, list) and isinstance(overpressure, list), "distance sweeps missing")
    distance_checks = [
        monotonic_decreasing("radiation_source_limited_flux", radiation, "source_limited_flux_w_m2"),
        monotonic_decreasing("overpressure_screening_peak", overpressure, "screening_peak_overpressure_kpa"),
    ]
    for row in radiation:
        distance = float(row["distance_m"])
        expected_source_flux = source_radiative_power / (4.0 * math.pi * distance * distance)
        expected_cloud_flux = cloud_radiative_power / (4.0 * math.pi * distance * distance)
        formula_checks.append(
            assert_close(
                f"source_flux_at_{distance:g}m",
                float(row["source_limited_flux_w_m2"]),
                expected_source_flux,
            )
        )
        formula_checks.append(
            assert_close(
                f"cloud_flux_at_{distance:g}m",
                float(row["cloud_average_flux_w_m2"]),
                expected_cloud_flux,
            )
        )

    direct_checks = {
        "single_cuda_1000step": sustained_checks(direct, min_outputs=6, min_y_h2o=0.10),
        "largegrid_mpi_cuda": sustained_checks(largegrid_mpi, min_outputs=4, min_y_h2o=1.0e-3),
    }
    restart_checks = restart.get("restart_checks", {})
    require(isinstance(restart_checks, dict), "restart checks missing")
    require(restart.get("status") == "PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-RESTART-SUSTAINED", "restart report not PASS")
    require(int(restart_checks.get("post_restart_sustained_output_count", 0)) >= 3, "restart post outputs too small")
    require(float(restart_checks.get("final_y_h2o_max", 0.0)) > float(restart_checks.get("checkpoint_y_h2o_max", 0.0)), "restart H2O did not grow")
    direct_checks["restart_mpi_cuda"] = {
        "status": restart.get("status"),
        "initial_step": restart_checks.get("initial_step"),
        "final_step": restart_checks.get("final_step"),
        "post_restart_sustained_output_count": restart_checks.get("post_restart_sustained_output_count"),
        "checkpoint_y_h2o_max": restart_checks.get("checkpoint_y_h2o_max"),
        "final_y_h2o_max": restart_checks.get("final_y_h2o_max"),
        "passed": True,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Fire Consequence Traceability Audit",
        "decision": "screening_consequence_formulae_and_direct_reacting_fire_evidence_traceable",
        "validated_capabilities": {
            "fire_screening_formula_traceable": True,
            "radiation_distance_sweep_traceable": True,
            "overpressure_distance_sweep_traceable": True,
            "direct_reacting_fire_evidence_linked": True,
            "restart_reacting_fire_evidence_linked": True,
            "calibrated_fire_or_blast_model": False,
        },
        "screening_traceability": {
            "source_hrr_formula": "total_h2_mass_kg / leak_final_time_s * h2_lhv_j_per_kg",
            "radiation_formula": "radiative_fraction * source_limited_heat_release_w / (4*pi*r^2)",
            "cloud_energy_formula": "flammable_cloud_h2_mass_kg * h2_lhv_j_per_kg",
            "tnt_equivalent_formula": "flammable_cloud_energy_j * blast_efficiency / tnt_j_per_kg",
            "formula_checks": formula_checks,
            "distance_checks": distance_checks,
        },
        "direct_reacting_fire_checks": direct_checks,
        "limitations": [
            "This audit proves traceability and internal consistency of screening metrics, not external calibration.",
            "Direct reacting plotfile heat-release extrema are linked as fire-existence evidence; they are not converted into calibrated radiative or overpressure loads.",
            "The fire-consequence production blocker remains until accepted external radiation and overpressure data pass the calibrated report gate.",
        ],
        "evidence_files": [
            evidence_entry("fire_consequence_metrics_report", fire_path),
            evidence_entry("direct_reacting_single_cuda_report", direct_path),
            evidence_entry("direct_reacting_largegrid_mpi_cuda_report", largegrid_mpi_path),
            evidence_entry("direct_reacting_mpi_cuda_restart_report", restart_path),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status mismatch")
    caps = report.get("validated_capabilities", {})
    for name in (
        "fire_screening_formula_traceable",
        "radiation_distance_sweep_traceable",
        "overpressure_distance_sweep_traceable",
        "direct_reacting_fire_evidence_linked",
        "restart_reacting_fire_evidence_linked",
    ):
        require(caps.get(name) is True, f"{name} not validated")
    require(caps.get("calibrated_fire_or_blast_model") is False, "traceability report must not claim calibration")
    screening = report.get("screening_traceability", {})
    require(isinstance(screening.get("formula_checks"), list) and len(screening["formula_checks"]) >= 10, "formula checks incomplete")
    require(all(item.get("passed") is True for item in screening["formula_checks"]), "a formula check failed")
    require(all(item.get("passed") is True for item in screening.get("distance_checks", [])), "a distance check failed")
    direct = report.get("direct_reacting_fire_checks", {})
    require(direct.get("single_cuda_1000step", {}).get("passed") is True, "single-CUDA direct fire not linked")
    require(direct.get("largegrid_mpi_cuda", {}).get("passed") is True, "large-grid MPI+CUDA direct fire not linked")
    require(direct.get("restart_mpi_cuda", {}).get("passed") is True, "restart fire not linked")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    direct = report["direct_reacting_fire_checks"]
    lines = [
        "# H2 Fire Consequence Traceability Audit",
        "",
        f"- Status: `{report['status']}`",
        "- Scope: internal formula and evidence traceability for screening consequence metrics.",
        "- Calibration claim: `False`",
        "",
        "## Linked Fire Evidence",
        "",
        f"- Single CUDA 1000-step final Y(H2O)_max: `{direct['single_cuda_1000step']['final_y_h2o_max']}`",
        f"- Large-grid MPI+CUDA final Y(H2O)_max: `{direct['largegrid_mpi_cuda']['final_y_h2o_max']}`",
        f"- Restart MPI+CUDA Y(H2O)_max: `{direct['restart_mpi_cuda']['checkpoint_y_h2o_max']} -> {direct['restart_mpi_cuda']['final_y_h2o_max']}`",
        "",
        "## Formula Checks",
        "",
        "| Check | Relative error |",
        "| --- | ---: |",
    ]
    for item in report["screening_traceability"]["formula_checks"]:
        lines.append(f"| `{item['name']}` | {item['rel_error']:.3e} |")
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fire-report", default=str(DEFAULT_FIRE_REPORT))
    ap.add_argument("--direct-cuda-report", default=str(DEFAULT_DIRECT_CUDA))
    ap.add_argument("--largegrid-mpi-cuda-report", default=str(DEFAULT_LARGEGRID_MPI_CUDA))
    ap.add_argument("--restart-report", default=str(DEFAULT_RESTART))
    ap.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    ap.add_argument("--verify-json")
    args = ap.parse_args()
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report(report)
            print(f"VERIFY-PASS {args.verify_json} status={report['status']}")
            return 0
        output_root = Path(args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        report = build_report(args)
        validate_report(report)
        json_path = output_root / "fire_consequence_traceability_report.json"
        md_path = output_root / "fire_consequence_traceability_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        validate_report(load_json(json_path))
        print(f"WROTE {json_path} status={report['status']}")
        return 0
    except TraceabilityError as exc:
        print(f"fire_consequence_traceability_report FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
