#!/usr/bin/env python3
"""Build a validated engineering H2 case report from maintained smoke evidence."""

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

PASS_TOKEN = "PASS"
REQUIRED_ROOT_FILES = (
    "plan_amr_compare_summary.csv",
    "amr_overhead_summary.csv",
    "reduced_long_summary.csv",
)
CASE_LOGS = (
    "validation.log",
    "profile_validation.log",
    "hazard_summary.log",
    "hazard_planes.log",
    "hazard_timeseries.log",
    "mpi_validation.log",
)
FINITE_CASE_COLUMNS = (
    "final_mass",
    "final_cloud_volume",
    "final_peak_X",
    "max_cloud_volume",
    "max_peak_X",
)
AMR_DIFF_COLUMNS = (
    "cloud_rel_diff",
    "peak_rel_diff",
    "centroid_abs_diff",
    "downstream_abs_diff",
)
OVERHEAD_RATIO_COLUMNS = (
    "mean_ncells_ratio",
    "max_ncells_ratio",
    "advance_seconds_ratio",
    "mean_advance_seconds_ratio",
    "final_plotfile_bytes_ratio",
    "all_plotfiles_bytes_ratio",
)


class ReportError(RuntimeError):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ReportError(f"empty CSV: {path}")
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_float(raw: str, label: str) -> float:
    if raw == "":
        raise ReportError(f"missing numeric value for {label}")
    value = float(raw)
    if not math.isfinite(value):
        raise ReportError(f"nonfinite value for {label}: {raw!r}")
    return value


def positive_int(raw: str, label: str, allow_zero: bool = False) -> int:
    value = int(raw)
    if value < 0 or (value == 0 and not allow_zero):
        raise ReportError(f"invalid integer for {label}: {raw!r}")
    return value


def require_columns(rows: list[dict[str, str]], columns: tuple[str, ...], label: str) -> None:
    available = set(rows[0].keys())
    missing = [col for col in columns if col not in available]
    if missing:
        raise ReportError(f"{label} missing columns: {', '.join(missing)}")


def rows_by_case(rows: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    require_columns(rows, ("case",), label)
    by_case: dict[str, dict[str, str]] = {}
    for row in rows:
        case = row["case"].strip()
        if case in by_case:
            raise ReportError(f"duplicate case {case!r} in {label}")
        by_case[case] = row
    for case in ("baseline", "amr"):
        if case not in by_case:
            raise ReportError(f"{label} missing {case!r} row")
    return by_case


def first_pass_line(path: Path) -> str:
    text = read_text(path)
    for line in text.splitlines():
        if PASS_TOKEN in line:
            return line.strip()
    raise ReportError(f"missing PASS line in {path}")


def check_case_logs(root: Path, case: str) -> dict[str, Any]:
    case_dir = root / case
    if not case_dir.is_dir():
        raise ReportError(f"missing case directory: {case_dir}")
    logs: dict[str, Any] = {}
    for name in CASE_LOGS:
        path = case_dir / name
        if not path.is_file():
            raise ReportError(f"missing {case} log: {path}")
        logs[name] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "pass_line": first_pass_line(path),
        }
    run_log = case_dir / "run.log"
    if not run_log.is_file():
        raise ReportError(f"missing {case} run log: {run_log}")
    run_text = read_text(run_log)
    bad_markers = ["Traceback", "RuntimeError", "Segmentation fault", "SIGSEGV", "Backtrace", "Unused ParmParse Variables"]
    hits = [marker for marker in bad_markers if marker in run_text]
    if re.search(r"(?<![A-Za-z0-9_])(?:nan|inf)(?![A-Za-z0-9_])", run_text, re.IGNORECASE):
        hits.append("nonfinite-token")
    if hits:
        raise ReportError(f"failure markers in {run_log}: {', '.join(hits)}")
    logs["run.log"] = {
        "path": str(run_log),
        "sha256": sha256_file(run_log),
        "line_count": len(run_text.splitlines()),
    }
    return logs


def parse_reduced_long(root: Path) -> dict[str, Any]:
    rows = read_csv_rows(root / "reduced_long_summary.csv")
    require_columns(
        rows,
        (
            "case",
            "ranks",
            "max_step",
            "plot_int",
            "plotfiles",
            "final_step",
            "final_time",
            "finest_level",
            "final_flammable_planes",
            "max_flammable_planes",
            "log_files",
        )
        + FINITE_CASE_COLUMNS,
        "reduced_long_summary.csv",
    )
    by_case = rows_by_case(rows, "reduced_long_summary.csv")
    parsed: dict[str, Any] = {}
    for case, row in by_case.items():
        ranks = positive_int(row["ranks"], f"{case}.ranks")
        max_step = positive_int(row["max_step"], f"{case}.max_step")
        final_step = positive_int(row["final_step"], f"{case}.final_step")
        plotfiles = positive_int(row["plotfiles"], f"{case}.plotfiles")
        final_time = finite_float(row["final_time"], f"{case}.final_time")
        if final_step != max_step:
            raise ReportError(f"{case} final_step={final_step} does not match max_step={max_step}")
        if final_time <= 0.0:
            raise ReportError(f"{case} final_time is not positive: {final_time}")
        metrics = {col: finite_float(row[col], f"{case}.{col}") for col in FINITE_CASE_COLUMNS}
        if metrics["final_mass"] <= 0.0 or metrics["final_cloud_volume"] <= 0.0 or metrics["final_peak_X"] <= 0.0:
            raise ReportError(f"{case} final hazard metrics are not positive")
        parsed[case] = {
            "ranks": ranks,
            "max_step": max_step,
            "plot_int": positive_int(row["plot_int"], f"{case}.plot_int"),
            "plotfiles": plotfiles,
            "final_step": final_step,
            "final_time": final_time,
            "finest_level": positive_int(row["finest_level"], f"{case}.finest_level", allow_zero=True),
            "fabs": row.get("fabs", ""),
            "final_flammable_planes": positive_int(row["final_flammable_planes"], f"{case}.final_flammable_planes"),
            "max_flammable_planes": positive_int(row["max_flammable_planes"], f"{case}.max_flammable_planes"),
            "log_files": positive_int(row["log_files"], f"{case}.log_files"),
            **metrics,
        }
    amr_row = by_case["amr"]
    parsed["amr_deltas"] = {col: finite_float(amr_row[col], f"amr.{col}") for col in AMR_DIFF_COLUMNS}
    return parsed


def parse_compare(root: Path) -> dict[str, Any]:
    rows = read_csv_rows(root / "plan_amr_compare_summary.csv")
    require_columns(rows, ("case", "mass_ratio", "mass_ratioN", "cloud_volume", "max_X", "active_planes", "flammable_planes") + AMR_DIFF_COLUMNS, "plan_amr_compare_summary.csv")
    by_case = rows_by_case(rows, "plan_amr_compare_summary.csv")
    parsed: dict[str, Any] = {}
    for case, row in by_case.items():
        parsed[case] = {
            "mass_ratio": finite_float(row["mass_ratio"], f"compare.{case}.mass_ratio"),
            "mass_ratioN": finite_float(row["mass_ratioN"], f"compare.{case}.mass_ratioN"),
            "cloud_volume": finite_float(row["cloud_volume"], f"compare.{case}.cloud_volume"),
            "max_X": finite_float(row["max_X"], f"compare.{case}.max_X"),
            "active_planes": positive_int(row["active_planes"], f"compare.{case}.active_planes"),
            "flammable_planes": positive_int(row["flammable_planes"], f"compare.{case}.flammable_planes"),
            "finest_level": positive_int(row["finest_level"], f"compare.{case}.finest_level", allow_zero=True),
            "finest_fab_count": positive_int(row["finest_fab_count"], f"compare.{case}.finest_fab_count"),
            "regrid_count": positive_int(row["regrid_count"], f"compare.{case}.regrid_count", allow_zero=True),
        }
    parsed["amr_deltas"] = {col: finite_float(by_case["amr"][col], f"compare.amr.{col}") for col in AMR_DIFF_COLUMNS}
    if parsed["amr"]["finest_level"] < 1 or parsed["amr"]["regrid_count"] <= 0:
        raise ReportError("AMR compare summary does not prove dynamic AMR")
    return parsed


def parse_overhead(root: Path) -> dict[str, Any]:
    rows = read_csv_rows(root / "amr_overhead_summary.csv")
    require_columns(rows, ("case", "advance_seconds", "final_plotfile_bytes", "mean_ncells") + OVERHEAD_RATIO_COLUMNS, "amr_overhead_summary.csv")
    by_case = rows_by_case(rows, "amr_overhead_summary.csv")
    parsed: dict[str, Any] = {}
    for case, row in by_case.items():
        parsed[case] = {
            "advance_seconds": finite_float(row["advance_seconds"], f"overhead.{case}.advance_seconds"),
            "final_plotfile_bytes": positive_int(row["final_plotfile_bytes"], f"overhead.{case}.final_plotfile_bytes"),
            "mean_ncells": finite_float(row["mean_ncells"], f"overhead.{case}.mean_ncells"),
        }
    parsed["amr_ratios"] = {col: finite_float(by_case["amr"][col], f"overhead.amr.{col}") for col in OVERHEAD_RATIO_COLUMNS}
    return parsed


def collect_inputs(root: Path) -> list[dict[str, str]]:
    input_dir = root / "inputs"
    if not input_dir.is_dir():
        raise ReportError(f"missing inputs directory: {input_dir}")
    inputs = sorted(p for p in input_dir.iterdir() if p.is_file())
    if len(inputs) < 2:
        raise ReportError(f"expected at least two generated inputs in {input_dir}")
    return [{"path": str(path), "sha256": sha256_file(path)} for path in inputs]


def build_report(case_name: str, root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ReportError(f"missing evidence root: {root}")
    for name in REQUIRED_ROOT_FILES:
        if not (root / name).is_file():
            raise ReportError(f"missing required evidence file: {root / name}")
    reduced = parse_reduced_long(root)
    compare = parse_compare(root)
    overhead = parse_overhead(root)
    logs = {case: check_case_logs(root, case) for case in ("baseline", "amr")}
    evidence_files = {name: {"path": str(root / name), "sha256": sha256_file(root / name)} for name in REQUIRED_ROOT_FILES}
    report = {
        "schema_version": 1,
        "status": "PASS",
        "case_name": case_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evidence_root": str(root),
        "inputs": collect_inputs(root),
        "evidence_files": evidence_files,
        "reduced_long": reduced,
        "plan_amr_compare": compare,
        "amr_overhead": overhead,
        "logs": logs,
        "limitations": [
            "Reduced-long smoke evidence, not production completion.",
            "Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.",
        ],
    }
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    reduced = report["reduced_long"]
    amr = reduced["amr"]
    base = reduced["baseline"]
    deltas = reduced["amr_deltas"]
    ratios = report["amr_overhead"]["amr_ratios"]
    lines = [
        f"# Engineering H2 Case Report: {report['case_name']}",
        "",
        f"Status: `{report['status']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        f"Evidence root: `{report['evidence_root']}`",
        "",
        "## Run Summary",
        "",
        f"- MPI ranks: `{amr['ranks']}`",
        f"- Steps: `{amr['max_step']}` with plot interval `{amr['plot_int']}`",
        f"- Plotfiles: baseline `{base['plotfiles']}`, AMR `{amr['plotfiles']}`",
        f"- Final time: `{amr['final_time']:.12e}`",
        f"- Baseline FABs: `{base['fabs']}`",
        f"- AMR FABs: `{amr['fabs']}`",
        "",
        "## Hazard Metrics",
        "",
        f"- Baseline final cloud volume: `{base['final_cloud_volume']:.8e}`",
        f"- AMR final cloud volume: `{amr['final_cloud_volume']:.8e}`",
        f"- Baseline final peak X: `{base['final_peak_X']:.8e}`",
        f"- AMR final peak X: `{amr['final_peak_X']:.8e}`",
        f"- AMR final flammable planes: `{amr['final_flammable_planes']}`",
        f"- Cloud relative difference: `{deltas['cloud_rel_diff']:.8e}`",
        f"- Peak relative difference: `{deltas['peak_rel_diff']:.8e}`",
        f"- Centroid absolute difference: `{deltas['centroid_abs_diff']:.8e}`",
        f"- Downstream absolute difference: `{deltas['downstream_abs_diff']:.8e}`",
        "",
        "## AMR Overhead",
        "",
        f"- Mean cell ratio: `{ratios['mean_ncells_ratio']:.8e}`",
        f"- Advance seconds ratio: `{ratios['advance_seconds_ratio']:.8e}`",
        f"- Final plotfile bytes ratio: `{ratios['final_plotfile_bytes_ratio']:.8e}`",
        "",
        "## Evidence Hashes",
        "",
    ]
    for item in report["inputs"]:
        lines.append(f"- `{item['path']}` sha256 `{item['sha256']}`")
    for item in report["evidence_files"].values():
        lines.append(f"- `{item['path']}` sha256 `{item['sha256']}`")
    lines.extend(["", "## Limitations", ""])
    for limitation in report["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="Human-readable case name for the report")
    parser.add_argument("--root", required=True, type=Path, help="Evidence root containing maintained H2 case CSV/log outputs")
    parser.add_argument("--output-json", required=True, type=Path, help="Path for the machine-readable JSON report")
    parser.add_argument("--output-md", required=True, type=Path, help="Path for the Markdown report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.case, args.root)
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, args.output_md)
    except ReportError as exc:
        raise SystemExit(f"engineering_h2_case_report FAIL {exc}") from exc
    print(
        "engineering_h2_case_report PASS "
        f"case={args.case} root={args.root.resolve()} json={args.output_json} md={args.output_md}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
