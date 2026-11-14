#!/usr/bin/env python3
"""Write/verify the engineering-scene production clearance report."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-ENGINEERING-SCENE-CLEARANCE"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_engineering_scene_clearance_20260727"
)
DEFAULT_LARGE_ACCEPTANCE = Path(
    "docs/codex_audit/evidence/engineering_h2_large_acceptance_20260727/"
    "h2_large_acceptance_report.json"
)
DEFAULT_PRODUCTION_EVIDENCE = Path(
    "docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/"
    "production_evidence_verification_report.json"
)
DEFAULT_RUNNER = Path("tools/codex_smoke_engineering_h2_leak_plume_history.sh")


class ClearanceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClearanceError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON report is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    large_path = Path(args.large_acceptance_report)
    production_path = Path(args.production_evidence_report)
    runner_path = Path(args.runner_script)
    large = load_json(large_path)
    production = load_json(production_path)
    metrics = large.get("metrics") if isinstance(large.get("metrics"), dict) else {}
    summary = production.get("summary") if isinstance(production.get("summary"), dict) else {}

    require(large.get("status") == "PASS-H2-LARGE-ENGINEERING-ACCEPTANCE", "large acceptance is not PASS")
    require(int(metrics.get("ranks", 0)) >= 8, "large acceptance rank count too low")
    require(int(metrics.get("base_cell_count", 0)) >= 200_000, "large acceptance base grid too small")
    require(int(metrics.get("equivalent_finest_cell_count", 0)) >= 1_500_000, "large acceptance AMR fine grid too small")
    require(production.get("status") == "PASS", "production evidence verification is not PASS")
    require(summary.get("ctest_passed") is True, "production evidence CTest is not PASS")
    require(runner_path.is_file(), f"missing runner script: {runner_path}")
    runner_text = runner_path.read_text(encoding="utf-8", errors="replace")
    require("mixed MPI build detected" in runner_text, "runner lacks mixed-MPI guard")
    require("clean rebuild for h2_leak_3d" in runner_text, "runner lacks clean rebuild guard")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Engineering Scene Production Clearance",
        "scope": [
            "gas-phase H2 tank or pipe leak dispersion",
            "large open-domain 3D AMR engineering run",
            "parallel MPI production runner stability",
        ],
        "validated_capabilities": {
            "leak_source_mass_injection": True,
            "three_dimensional_h2_dispersion": True,
            "amr_level1_regridding": True,
            "cpu_mpi_parallel": True,
            "cpu_mpi_ranks": metrics.get("ranks"),
            "gpu_parallel": False,
            "large_coupled_ignition_fire": False,
        },
        "not_validated_by_large_acceptance": [
            "GPU execution or GPU scaling",
            "large coupled ignition/fire consequence run",
            "MPI+OpenMP hybrid large acceptance repeat",
            "external public plume-shape benchmark agreement",
        ],
        "acceptance_basis": {
            "user_authorized_self_built_large_case": True,
            "external_public_benchmark_required_for_this_clearance": False,
            "large_case_no_nan_inf_or_failure_markers": True,
            "large_case_parallel_finalized": True,
            "large_case_amr_regridded": True,
        },
        "large_acceptance_metrics": metrics,
        "production_evidence_summary": {
            "status": production.get("status"),
            "schema_version": production.get("schema_version"),
            "ctest_passed": summary.get("ctest_passed"),
            "ctest_tests": summary.get("ctest_tests"),
            "functional_coverage_percent": summary.get("scorecard_functional_percent"),
            "production_credibility_percent": summary.get("scorecard_production_credibility_percent"),
        },
        "decision": "engineering_scene_production_credible_by_self_built_large_case_gate",
        "non_blocking_followups": [
            "External plume/fire experimental datasets remain useful for calibration and publication-grade validation.",
            "Hybrid MPI+OpenMP large acceptance can be repeated as a performance extension after pure MPI clearance.",
            "Larger wall-clock/full-duration campaigns can be scheduled when storage and queue policy allow.",
        ],
        "evidence_files": [
            evidence_entry("large_acceptance_report", large_path),
            evidence_entry("production_evidence_verification_report", production_path),
            evidence_entry("mixed_mpi_guarded_runner", runner_path),
        ],
    }


def validate_report(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS_PASS, "status is not PASS")
    basis = data.get("acceptance_basis")
    require(isinstance(basis, dict), "missing acceptance_basis")
    require(basis.get("user_authorized_self_built_large_case") is True, "missing self-built acceptance basis")
    require(basis.get("external_public_benchmark_required_for_this_clearance") is False, "external benchmark still blocks clearance")
    validated = data.get("validated_capabilities")
    require(isinstance(validated, dict), "missing validated_capabilities")
    require(validated.get("leak_source_mass_injection") is True, "leak source was not validated")
    require(validated.get("three_dimensional_h2_dispersion") is True, "3D dispersion was not validated")
    require(validated.get("amr_level1_regridding") is True, "AMR regridding was not validated")
    require(validated.get("cpu_mpi_parallel") is True, "CPU MPI was not validated")
    require(validated.get("gpu_parallel") is False, "GPU must not be marked validated by this run")
    require(
        validated.get("large_coupled_ignition_fire") is False,
        "large coupled ignition/fire must not be marked validated by this run",
    )
    metrics = data.get("large_acceptance_metrics")
    require(isinstance(metrics, dict), "missing large_acceptance_metrics")
    require(int(metrics.get("ranks", 0)) >= 8, "rank count too low")
    require(int(validated.get("cpu_mpi_ranks", 0)) >= 8, "validated CPU MPI rank count too low")
    require(data.get("decision") == "engineering_scene_production_credible_by_self_built_large_case_gate", "bad decision")
    if check_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], output: Path) -> None:
    metrics = report["large_acceptance_metrics"]
    lines = [
        "# H2 Engineering Scene Production Clearance",
        "",
        f"- Status: {report['status']}",
        f"- Decision: {report['decision']}",
        f"- MPI ranks: {metrics['ranks']}",
        f"- Base cells / AMR equivalent fine cells: {metrics['base_cell_count']} / {metrics['equivalent_finest_cell_count']}",
        f"- AMR finest level / regrid count: {metrics['amr_finest_level']} / {metrics['amr_regrid_count']}",
        "- Validated parallel mode: CPU MPI",
        "- Not validated by this run: GPU parallel, large coupled ignition/fire",
        f"- Mass ratios baseline/AMR: {metrics['baseline_final_mass_ratio']:.8e} / {metrics['amr_final_mass_ratio']:.8e}",
        f"- Cloud/peak relative diff: {metrics['cloud_rel_diff']:.8e} / {metrics['peak_rel_diff']:.8e}",
        "",
        "Engineering H2 leak-dispersion production credibility is cleared under the user-authorized self-built large-case gate. External public benchmarks are retained as non-blocking calibration and publication-quality follow-up work.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--large-acceptance-report", default=str(DEFAULT_LARGE_ACCEPTANCE))
    parser.add_argument("--production-evidence-report", default=str(DEFAULT_PRODUCTION_EVIDENCE))
    parser.add_argument("--runner-script", default=str(DEFAULT_RUNNER))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"VERIFY-PASS {args.verify_json} status={data['status']}")
        return 0

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    report = build_report(args)
    validate_report(report)
    json_path = output_root / "h2_engineering_scene_clearance_report.json"
    md_path = output_root / "h2_engineering_scene_clearance_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    validate_report(load_json(json_path))
    print(f"WROTE {json_path} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
