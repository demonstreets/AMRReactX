#!/usr/bin/env python3
"""Write a CFD-derived radiation proxy report for MDPI radiation targets.

The report uses delayed-ignition CFD reaction histories and plotfile grid
metadata to build a finite, reproducible near-field radiation proxy from the
maximum HeatRelease cell. It is an observability and CPU/GPU parity gate, not a
calibrated radiation agreement.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-MDPI-RADIATION-CFD-PROXY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_cfd_proxy_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_mdpi_radiation_cfd_proxy_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_mdpi_radiation_cfd_proxy_report.md"
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / "mdpi_radiation_cfd_proxy_comparison.csv"

CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_cuda_report.json"
)
MPI_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_mpi_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_mpi_report.json"
)
RADIATION_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)


class CfdProxyError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CfdProxyError(message)


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


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
        raise CfdProxyError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CfdProxyError(f"invalid JSON evidence {path}: {exc}") from exc
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


def runtime_summary_path(report: dict[str, Any]) -> Path:
    root = Path(str(report.get("staged_evidence_root", "")))
    path = root / "summary.json"
    require(path.is_file(), f"missing staged runtime summary: {path}")
    return path


def final_header_path(report: dict[str, Any]) -> Path:
    root = Path(str(report.get("staged_evidence_root", "")))
    path = root / "plt00120" / "Header"
    require(path.is_file(), f"missing final plotfile header: {path}")
    return path


def read_dx_from_header(path: Path) -> list[float]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    require(len(lines) > 40, f"plotfile header too short: {path}")
    ndim = int(lines[35])
    pattern = re.compile(r"^[0-9eE+\-.]+(?:\s+[0-9eE+\-.]+){%d}$" % (ndim - 1))
    candidates: list[list[float]] = []
    for line in lines[40:]:
        if pattern.match(line):
            vals = [float(item) for item in line.split()]
            if all(val > 0.0 for val in vals):
                candidates.append(vals)
    require(candidates, f"no dx candidate found in header: {path}")
    return candidates[0]


def read_radiation_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    output_files = report.get("output_files")
    require(isinstance(output_files, dict), "radiation table missing output_files")
    csv_path = Path(str(output_files.get("radiation_metrics_csv", "")))
    require(csv_path.is_file(), f"missing radiation metrics CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "metric_id": row["metric_id"],
                "distance_m": float(row["distance_m"]),
                "reference_flux_w_m2": float(row["reference_flux_w_m2"]),
                "tolerance_abs_w_m2": float(row["tolerance_abs_w_m2"]),
                "tolerance_rel": float(row["tolerance_rel"]),
            }
        )
    require(len(out) >= 4, "MDPI radiation table has too few rows")
    return out


def peak_heat_release(history: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in history if finite(row.get("heat_release_abs_max")) and finite(row.get("time"))]
    require(len(rows) >= 10, "reaction history too short for proxy")
    peak = max(rows, key=lambda row: float(row["heat_release_abs_max"]))
    require(float(peak["heat_release_abs_max"]) > 1.0e5, "peak HeatRelease too small for fire proxy")
    return peak


def point_flux(power_w: float, distance_m: float) -> float:
    return power_w / (4.0 * math.pi * distance_m * distance_m)


def build_run_proxy(label: str, report_path: Path, radiative_fraction: float) -> dict[str, Any]:
    report = load_json(report_path)
    require(report.get("status") in {
        "PASS-H2-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA",
        "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-MPI",
    }, f"{label} delayed ignition report is not PASS")
    summary_path = runtime_summary_path(report)
    runtime_summary = load_json(summary_path)
    history = runtime_summary.get("reaction_history")
    require(isinstance(history, list), f"{label} runtime summary missing reaction_history")
    peak = peak_heat_release(history)
    dx = read_dx_from_header(final_header_path(report))
    cell_volume = math.prod(dx)
    peak_heat_release_w_m3 = float(peak["heat_release_abs_max"])
    proxy_cell_heat_release_w = peak_heat_release_w_m3 * cell_volume
    proxy_radiative_power_w = proxy_cell_heat_release_w * radiative_fraction
    return {
        "label": label,
        "report_path": str(report_path),
        "runtime_summary_path": str(summary_path),
        "peak_plotfile": peak.get("plotfile"),
        "peak_time_s": float(peak["time"]),
        "peak_heat_release_abs_max_w_m3": peak_heat_release_w_m3,
        "dx_m": dx,
        "cell_volume_m3": cell_volume,
        "radiative_fraction": radiative_fraction,
        "proxy_cell_heat_release_w": proxy_cell_heat_release_w,
        "proxy_radiative_power_w": proxy_radiative_power_w,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    require(0.0 < args.radiative_fraction <= 1.0, "radiative fraction must be in (0, 1]")
    cuda = build_run_proxy("single_cuda", Path(args.cuda_report), args.radiative_fraction)
    mpi = build_run_proxy("cpu_mpi", Path(args.mpi_report), args.radiative_fraction)
    radiation_table = load_json(Path(args.radiation_table))
    require(
        radiation_table.get("status") == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
        "MDPI radiation table not ready",
    )
    rows = read_radiation_rows(radiation_table)
    cuda_power = float(cuda["proxy_radiative_power_w"])
    mpi_power = float(mpi["proxy_radiative_power_w"])
    parity_rel_diff = abs(cuda_power - mpi_power) / max(abs(cuda_power), abs(mpi_power), 1.0e-300)
    comparisons: list[dict[str, Any]] = []
    for row in rows:
        distance = float(row["distance_m"])
        reference = float(row["reference_flux_w_m2"])
        cuda_flux = point_flux(cuda_power, distance)
        mpi_flux = point_flux(mpi_power, distance)
        cuda_rel_error = abs(cuda_flux - reference) / reference
        comparisons.append(
            {
                **row,
                "single_cuda_proxy_flux_w_m2": cuda_flux,
                "cpu_mpi_proxy_flux_w_m2": mpi_flux,
                "cpu_gpu_proxy_flux_rel_diff": abs(cuda_flux - mpi_flux) / max(abs(cuda_flux), abs(mpi_flux), 1.0e-300),
                "single_cuda_proxy_rel_error": cuda_rel_error,
                "single_cuda_to_reference_ratio": cuda_flux / reference,
                "agreement_passed": False,
            }
        )

    output_csv = Path(args.output_csv)
    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "H2 Fire MDPI Radiation CFD-Derived Proxy",
        "status": STATUS_PASS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "cfd_proxy_extracted": True,
            "mdpi_radiation_metric_count": len(comparisons),
            "single_cuda_proxy_radiative_power_w": cuda_power,
            "cpu_mpi_proxy_radiative_power_w": mpi_power,
            "cpu_gpu_proxy_radiative_power_rel_diff": parity_rel_diff,
            "cpu_gpu_proxy_parity_passed": parity_rel_diff <= args.max_cpu_gpu_rel_diff,
            "case_aligned_cfd_radiation_agreement": False,
            "current_outputs_sufficient_for_mdpi_radiation_agreement": False,
            "strict_fire_calibration_blocker_cleared": False,
            "proxy_agreement_pass_count": 0,
            "proxy_agreement_fail_count": len(comparisons),
        },
        "proxy_definition": {
            "source_field": "HeatRelease abs max from delayed-ignition plotfile reaction history",
            "formula": "proxy_flux = max_cell_HeatRelease_W_m3 * cell_volume_m3 * radiative_fraction / (4*pi*distance_m^2)",
            "radiative_fraction": args.radiative_fraction,
            "purpose": "CFD observability and CPU/GPU parity gate; not a flame radiation model",
        },
        "run_proxies": {
            "single_cuda": cuda,
            "cpu_mpi": mpi,
        },
        "comparisons": comparisons,
        "output_files": {
            "comparison_csv": str(output_csv),
        },
        "limitations": [
            "Uses one-cell peak HeatRelease as a radiation proxy, not integrated flame emissive power.",
            "Does not model flame surface, soot, gas radiation, view factor, obstruction shielding, or radiometer geometry.",
            "Does not clear strict MDPI radiation agreement; it only proves a finite CFD-derived observable path.",
        ],
        "evidence_files": [
            evidence_entry("single_cuda_delayed_ignition_report", Path(args.cuda_report)),
            evidence_entry("cpu_mpi_delayed_ignition_report", Path(args.mpi_report)),
            evidence_entry("mdpi_radiation_table", Path(args.radiation_table)),
            evidence_entry("single_cuda_runtime_summary", Path(cuda["runtime_summary_path"])),
            evidence_entry("cpu_mpi_runtime_summary", Path(mpi["runtime_summary_path"])),
            evidence_entry("mdpi_radiation_metrics_csv", Path(radiation_table["output_files"]["radiation_metrics_csv"])),
        ],
    }
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv(comparisons, output_csv)
    report["evidence_files"].append(evidence_entry("comparison_csv", output_csv))
    validate_report(report, verify_hashes=False)
    return report


def write_csv(comparisons: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "metric_id",
        "distance_m",
        "reference_flux_w_m2",
        "single_cuda_proxy_flux_w_m2",
        "cpu_mpi_proxy_flux_w_m2",
        "cpu_gpu_proxy_flux_rel_diff",
        "single_cuda_proxy_rel_error",
        "single_cuda_to_reference_ratio",
        "agreement_passed",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in comparisons:
            writer.writerow({key: item[key] for key in fields})


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS_PASS, f"unexpected status: {data.get('status')}")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("cfd_proxy_extracted") is True, "CFD proxy not extracted")
    require(summary.get("mdpi_radiation_metric_count", 0) >= 4, "too few MDPI radiation metrics")
    require(summary.get("cpu_gpu_proxy_parity_passed") is True, "CPU/GPU proxy parity failed")
    require(summary.get("case_aligned_cfd_radiation_agreement") is False, "case-aligned agreement overclaimed")
    require(
        summary.get("current_outputs_sufficient_for_mdpi_radiation_agreement") is False,
        "output sufficiency overclaimed",
    )
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    require(summary.get("proxy_agreement_fail_count", 0) >= 4, "proxy should not claim MDPI agreement")
    for item in data.get("comparisons", []):
        require(isinstance(item, dict), "invalid comparison item")
        for key in (
            "single_cuda_proxy_flux_w_m2",
            "cpu_mpi_proxy_flux_w_m2",
            "cpu_gpu_proxy_flux_rel_diff",
            "single_cuda_proxy_rel_error",
        ):
            require(finite(item.get(key)), f"non-finite comparison value: {key}")
        require(item.get("agreement_passed") is False, "proxy comparison overclaimed agreement")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire MDPI Radiation CFD-Derived Proxy",
        "",
        f"- Status: `{report['status']}`",
        f"- CFD proxy extracted: `{s['cfd_proxy_extracted']}`",
        f"- CPU/GPU proxy parity relative diff: `{s['cpu_gpu_proxy_radiative_power_rel_diff']:.8e}`",
        f"- Case-aligned agreement: `{s['case_aligned_cfd_radiation_agreement']}`",
        f"- Strict fire blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Comparison",
        "",
        "| Metric | Distance m | Reference W/m2 | CUDA proxy W/m2 | CPU/MPI proxy W/m2 | CUDA rel error |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report["comparisons"]:
        lines.append(
            f"| `{item['metric_id']}` | {item['distance_m']:.3g} | {item['reference_flux_w_m2']:.8e} | "
            f"{item['single_cuda_proxy_flux_w_m2']:.8e} | {item['cpu_mpi_proxy_flux_w_m2']:.8e} | "
            f"{item['single_cuda_proxy_rel_error']:.8e} |"
        )
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda-report", default=str(CUDA_REPORT))
    parser.add_argument("--mpi-report", default=str(MPI_REPORT))
    parser.add_argument("--radiation-table", default=str(RADIATION_TABLE))
    parser.add_argument("--radiative-fraction", type=float, default=0.15)
    parser.add_argument("--max-cpu-gpu-rel-diff", type=float, default=0.05)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_mdpi_radiation_cfd_proxy VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"h2_fire_mdpi_radiation_cfd_proxy PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
