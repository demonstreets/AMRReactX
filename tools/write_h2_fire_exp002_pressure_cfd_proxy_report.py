#!/usr/bin/env python3
"""Write a CFD pressure-observability proxy report for EXP002 pressure targets.

This report extracts avg_pressure statistics from the delayed-ignition CPU/MPI
and single-CUDA plotfiles. It proves that pressure-like CFD fields can be
postprocessed reproducibly and compared across CPU/GPU runs. It intentionally
does not claim EXP002 pressure-sensor agreement because avg_pressure is a
solver pressure-like field, not a mapped experimental sensor overpressure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-EXP002-PRESSURE-CFD-PROXY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_exp002_pressure_cfd_proxy_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_exp002_pressure_cfd_proxy_report.md"
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / "pressure_cfd_proxy_timeseries.csv"

CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_cuda_report.json"
)
MPI_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_mpi_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_mpi_report.json"
)
EXP002_PRESSURE_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/"
    "h2_fire_exp002_overpressure_calibration_table_report.json"
)


class PressureProxyError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PressureProxyError(message)


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
        raise PressureProxyError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PressureProxyError(f"invalid JSON evidence {path}: {exc}") from exc
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


def source_run_dir(report: dict[str, Any]) -> Path:
    root = Path(str(report.get("source_run_root", "")))
    run_dir = root / "run"
    require(run_dir.is_dir(), f"missing source run directory: {run_dir}")
    return run_dir


def plotfile_names(report: dict[str, Any]) -> list[str]:
    run_summary = report.get("run_summary", {})
    require(isinstance(run_summary, dict), "delayed ignition report missing run_summary")
    names = run_summary.get("plotfiles")
    require(isinstance(names, list) and len(names) >= 4, "delayed ignition report has too few plotfiles")
    return [str(name) for name in names]


def extract_timeseries(label: str, report_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sys.path.insert(0, str(Path("tools").resolve()))
    import amrex_reader  # type: ignore

    report = load_json(report_path)
    run_dir = source_run_dir(report)
    runtime = load_json(runtime_summary_path(report))
    names = plotfile_names(report)
    rows: list[dict[str, Any]] = []
    for name in names:
        plot = run_dir / name
        data = amrex_reader.read_plotfile(str(plot))
        fields = data["fields"]
        require("avg_pressure" in fields, f"avg_pressure missing in {plot}")
        arr = fields["avg_pressure"]
        rows.append(
            {
                "run_label": label,
                "plotfile": name,
                "time_s": float(data["time"]),
                "avg_pressure_min": float(arr.min()),
                "avg_pressure_max": float(arr.max()),
                "avg_pressure_mean": float(arr.mean()),
                "avg_pressure_abs_max": float(max(abs(float(arr.min())), abs(float(arr.max())))),
            }
        )
    peak = max(rows, key=lambda row: float(row["avg_pressure_abs_max"]))
    return rows, {
        "run_label": label,
        "source_run_dir": str(run_dir),
        "plotfile_count": len(rows),
        "peak_abs_pressure_plotfile": peak["plotfile"],
        "peak_abs_pressure_time_s": peak["time_s"],
        "peak_abs_pressure_proxy_pa": peak["avg_pressure_abs_max"],
        "final_avg_pressure_mean": rows[-1]["avg_pressure_mean"],
        "final_avg_pressure_abs_max": rows[-1]["avg_pressure_abs_max"],
    }


def write_timeseries_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "run_label",
        "plotfile",
        "time_s",
        "avg_pressure_min",
        "avg_pressure_max",
        "avg_pressure_mean",
        "avg_pressure_abs_max",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fields})


def load_timeseries_csv(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f"missing pressure proxy CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for row in rows:
        item = {
            "run_label": row["run_label"],
            "plotfile": row["plotfile"],
            "time_s": float(row["time_s"]),
            "avg_pressure_min": float(row["avg_pressure_min"]),
            "avg_pressure_max": float(row["avg_pressure_max"]),
            "avg_pressure_mean": float(row["avg_pressure_mean"]),
            "avg_pressure_abs_max": float(row["avg_pressure_abs_max"]),
        }
        out.append(item)
    require(len(out) >= 8, "pressure proxy CSV has too few rows")
    return out


def summarize_cached(label: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    subset = [row for row in rows if row["run_label"] == label]
    require(len(subset) >= 4, f"cached pressure rows missing for {label}")
    peak = max(subset, key=lambda row: float(row["avg_pressure_abs_max"]))
    return {
        "run_label": label,
        "source_run_dir": "",
        "plotfile_count": len(subset),
        "peak_abs_pressure_plotfile": peak["plotfile"],
        "peak_abs_pressure_time_s": peak["time_s"],
        "peak_abs_pressure_proxy_pa": peak["avg_pressure_abs_max"],
        "final_avg_pressure_mean": subset[-1]["avg_pressure_mean"],
        "final_avg_pressure_abs_max": subset[-1]["avg_pressure_abs_max"],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    output_csv = Path(args.output_csv)
    extraction_mode = "plotfile_extraction"
    try:
        cuda_rows, cuda_summary = extract_timeseries("single_cuda", Path(args.cuda_report))
        mpi_rows, mpi_summary = extract_timeseries("cpu_mpi", Path(args.mpi_report))
        rows = cuda_rows + mpi_rows
        write_timeseries_csv(rows, output_csv)
    except Exception:
        if not output_csv.is_file():
            raise
        extraction_mode = "cached_extraction_csv"
        rows = load_timeseries_csv(output_csv)
        cuda_summary = summarize_cached("single_cuda", rows)
        mpi_summary = summarize_cached("cpu_mpi", rows)

    pressure_table = load_json(Path(args.pressure_table))
    require(
        pressure_table.get("status") == "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE",
        "EXP002 pressure target table not ready",
    )
    pressure_summary = pressure_table.get("summary", {})
    require(isinstance(pressure_summary, dict), "EXP002 pressure table missing summary")
    target_count = pressure_summary.get("overpressure_metric_count")
    require(target_count == 4, "EXP002 pressure table should contain four pressure targets")

    cuda_peak = float(cuda_summary["peak_abs_pressure_proxy_pa"])
    mpi_peak = float(mpi_summary["peak_abs_pressure_proxy_pa"])
    peak_rel_diff = abs(cuda_peak - mpi_peak) / max(abs(cuda_peak), abs(mpi_peak), 1.0e-300)
    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "H2 Fire EXP002 Pressure CFD Proxy",
        "status": STATUS_PASS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "pressure_proxy_extracted": True,
            "extraction_mode": extraction_mode,
            "avg_pressure_field_present": True,
            "pressure_proxy_plotfile_count_per_run": min(cuda_summary["plotfile_count"], mpi_summary["plotfile_count"]),
            "single_cuda_peak_abs_pressure_proxy_pa": cuda_peak,
            "cpu_mpi_peak_abs_pressure_proxy_pa": mpi_peak,
            "cpu_gpu_peak_abs_pressure_rel_diff": peak_rel_diff,
            "cpu_gpu_pressure_proxy_parity_passed": peak_rel_diff <= args.max_cpu_gpu_rel_diff,
            "exp002_pressure_target_count": target_count,
            "case_aligned_pressure_sensor_agreement": False,
            "current_outputs_sufficient_for_exp002_pressure_agreement": False,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "proxy_definition": {
            "source_field": "avg_pressure min/max/mean from delayed-ignition plotfiles",
            "purpose": "pressure observability and CPU/GPU parity gate",
            "strict_credit_policy": "does not clear EXP002 pressure agreement without mapped sensor locations, peak overpressure, and arrival-time comparison",
        },
        "run_proxies": {
            "single_cuda": cuda_summary,
            "cpu_mpi": mpi_summary,
        },
        "limitations": [
            "avg_pressure is a pressure-like solver field and may be signed; it is not a direct experimental overpressure sensor.",
            "No EXP002 sensor positions or arrival-time waveforms are mapped in this report.",
            "The delayed-ignition smoke window is not the full EXP002 release and ignition timeline.",
        ],
        "output_files": {
            "pressure_proxy_timeseries_csv": str(output_csv),
        },
        "evidence_files": [
            evidence_entry("single_cuda_delayed_ignition_report", Path(args.cuda_report)),
            evidence_entry("cpu_mpi_delayed_ignition_report", Path(args.mpi_report)),
            evidence_entry("exp002_pressure_target_table", Path(args.pressure_table)),
            evidence_entry("pressure_proxy_timeseries_csv", output_csv),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS_PASS, f"unexpected status: {data.get('status')}")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("pressure_proxy_extracted") is True, "pressure proxy not extracted")
    require(summary.get("avg_pressure_field_present") is True, "avg_pressure not present")
    require(summary.get("pressure_proxy_plotfile_count_per_run", 0) >= 10, "too few pressure plotfiles")
    require(summary.get("cpu_gpu_pressure_proxy_parity_passed") is True, "CPU/GPU pressure proxy parity failed")
    require(summary.get("exp002_pressure_target_count") == 4, "EXP002 pressure target count mismatch")
    require(summary.get("case_aligned_pressure_sensor_agreement") is False, "case-aligned pressure agreement overclaimed")
    require(
        summary.get("current_outputs_sufficient_for_exp002_pressure_agreement") is False,
        "EXP002 pressure output sufficiency overclaimed",
    )
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    output_files = data.get("output_files", {})
    require(isinstance(output_files, dict), "output_files missing")
    rows = load_timeseries_csv(Path(str(output_files.get("pressure_proxy_timeseries_csv", ""))))
    labels = {row["run_label"] for row in rows}
    require({"single_cuda", "cpu_mpi"} <= labels, "pressure CSV missing one run label")
    for row in rows:
        for key in ("time_s", "avg_pressure_min", "avg_pressure_max", "avg_pressure_mean", "avg_pressure_abs_max"):
            require(finite(row.get(key)), f"non-finite pressure CSV value: {key}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire EXP002 Pressure CFD Proxy",
        "",
        f"- Status: `{report['status']}`",
        f"- avg_pressure extracted: `{s['avg_pressure_field_present']}`",
        f"- Plotfiles per run: `{s['pressure_proxy_plotfile_count_per_run']}`",
        f"- CPU/GPU peak-pressure proxy relative diff: `{s['cpu_gpu_peak_abs_pressure_rel_diff']:.8e}`",
        f"- Case-aligned EXP002 pressure agreement: `{s['case_aligned_pressure_sensor_agreement']}`",
        f"- Strict fire blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Run Proxies",
        "",
        "| Run | Peak plotfile | Peak time s | Peak abs pressure proxy Pa | Final abs pressure proxy Pa |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for label, item in report["run_proxies"].items():
        lines.append(
            f"| `{label}` | `{item['peak_abs_pressure_plotfile']}` | {item['peak_abs_pressure_time_s']:.8e} | "
            f"{item['peak_abs_pressure_proxy_pa']:.8e} | {item['final_avg_pressure_abs_max']:.8e} |"
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
    parser.add_argument("--pressure-table", default=str(EXP002_PRESSURE_TABLE))
    parser.add_argument("--max-cpu-gpu-rel-diff", type=float, default=0.05)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_exp002_pressure_cfd_proxy VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"h2_fire_exp002_pressure_cfd_proxy PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
