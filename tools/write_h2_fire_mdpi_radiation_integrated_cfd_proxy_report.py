#!/usr/bin/env python3
"""Write an integrated HeatRelease radiation proxy report for MDPI targets."""
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
STATUS = "PASS-H2-FIRE-MDPI-RADIATION-INTEGRATED-CFD-PROXY"
ROOT = Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807")
DEFAULT_JSON = ROOT / "h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json"
DEFAULT_MD = ROOT / "h2_fire_mdpi_radiation_integrated_cfd_proxy_report.md"
DEFAULT_HISTORY_CSV = ROOT / "integrated_heat_release_history.csv"
DEFAULT_COMPARISON_CSV = ROOT / "integrated_radiation_proxy_comparison.csv"
PLOT_ROOT = Path("docs/codex_audit/evidence/engineering_h2_pipe_rack_mpi_cuda_long_revalidation_20260731/run_root/run")
RADIATION_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT / "tools"))

import amrex_reader  # noqa: E402


class IntegratedRadiationProxyError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegratedRadiationProxyError(message)


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
        raise IntegratedRadiationProxyError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise IntegratedRadiationProxyError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def read_radiation_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    output_files = report.get("output_files")
    require(isinstance(output_files, dict), "radiation table missing output_files")
    csv_path = Path(str(output_files.get("radiation_metrics_csv", "")))
    require(csv_path.is_file(), f"missing radiation metrics CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    parsed = []
    for row in rows:
        parsed.append(
            {
                "metric_id": row["metric_id"],
                "distance_m": float(row["distance_m"]),
                "reference_flux_w_m2": float(row["reference_flux_w_m2"]),
                "tolerance_abs_w_m2": float(row["tolerance_abs_w_m2"]),
                "tolerance_rel": float(row["tolerance_rel"]),
            }
        )
    require(len(parsed) >= 4, "MDPI radiation table has too few rows")
    return parsed


def find_plotfiles(plot_root: Path) -> list[Path]:
    require(plot_root.is_dir(), f"missing plot root: {plot_root}")
    plots = []
    for header in sorted(plot_root.glob("plt*/Header")):
        plot = header.parent
        if (plot / "Level_0" / "Cell_H").is_file() and "HeatRelease" in header.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            plots.append(plot)
    require(len(plots) >= 3, "not enough complete HeatRelease plotfiles")
    return plots


def integrate_plotfile(plot: Path, radiative_fraction: float) -> dict[str, Any]:
    data = amrex_reader.read_plotfile(str(plot))
    fields = data.get("fields")
    require(isinstance(fields, dict), f"{plot} fields missing")
    require("HeatRelease" in fields, f"{plot} missing HeatRelease")
    arr = fields["HeatRelease"]
    dx = [float(v) for v in data["dx"]]
    cell_volume = math.prod(dx)
    positive_heat_release_w = float(arr[arr > 0.0].sum() * cell_volume)
    abs_heat_release_w = float(abs(arr).sum() * cell_volume)
    peak_heat_release_w_m3 = float(arr.max())
    require(math.isfinite(positive_heat_release_w), f"{plot} integrated heat release is not finite")
    require(math.isfinite(abs_heat_release_w), f"{plot} abs integrated heat release is not finite")
    require(math.isfinite(peak_heat_release_w_m3), f"{plot} peak heat release is not finite")
    return {
        "plotfile": str(plot),
        "time_s": float(data["time"]),
        "dx_m": dx,
        "cell_volume_m3": cell_volume,
        "positive_heat_release_w": positive_heat_release_w,
        "abs_heat_release_w": abs_heat_release_w,
        "peak_heat_release_w_m3": peak_heat_release_w_m3,
        "radiative_fraction": radiative_fraction,
        "integrated_radiative_power_w": positive_heat_release_w * radiative_fraction,
    }


def point_flux(power_w: float, distance_m: float) -> float:
    require(distance_m > 0.0, "radiometer distance must be positive")
    return power_w / (4.0 * math.pi * distance_m * distance_m)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    require(0.0 < args.radiative_fraction <= 1.0, "radiative fraction must be in (0, 1]")
    radiation_table = load_json(Path(args.radiation_table))
    require(
        radiation_table.get("status") == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
        "MDPI radiation table not ready",
    )
    radiation_rows = read_radiation_rows(radiation_table)
    plotfiles = find_plotfiles(Path(args.plot_root))
    history = [integrate_plotfile(plot, args.radiative_fraction) for plot in plotfiles]
    history.sort(key=lambda row: (float(row["time_s"]), row["plotfile"]))
    peak = max(history, key=lambda row: float(row["integrated_radiative_power_w"]))
    peak_power = float(peak["integrated_radiative_power_w"])
    require(peak_power > 0.0, "peak integrated radiative proxy power is not positive")

    comparisons = []
    for row in radiation_rows:
        reference = float(row["reference_flux_w_m2"])
        flux = point_flux(peak_power, float(row["distance_m"]))
        comparisons.append(
            {
                **row,
                "peak_integrated_proxy_flux_w_m2": flux,
                "proxy_to_reference_ratio": flux / reference,
                "proxy_rel_error": abs(flux - reference) / reference,
                "agreement_passed": False,
            }
        )

    output_history = Path(args.output_history_csv)
    output_comparison = Path(args.output_comparison_csv)
    write_csv(
        output_history,
        history,
        [
            "plotfile",
            "time_s",
            "dx_m",
            "cell_volume_m3",
            "positive_heat_release_w",
            "abs_heat_release_w",
            "peak_heat_release_w_m3",
            "radiative_fraction",
            "integrated_radiative_power_w",
        ],
    )
    write_csv(
        output_comparison,
        comparisons,
        [
            "metric_id",
            "distance_m",
            "reference_flux_w_m2",
            "tolerance_abs_w_m2",
            "tolerance_rel",
            "peak_integrated_proxy_flux_w_m2",
            "proxy_to_reference_ratio",
            "proxy_rel_error",
            "agreement_passed",
        ],
    )

    ready = (
        len(history) >= 3
        and len(comparisons) >= 4
        and peak_power > 0.0
        and all(math.isfinite(float(row["peak_integrated_proxy_flux_w_m2"])) for row in comparisons)
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-H2-FIRE-MDPI-RADIATION-INTEGRATED-CFD-PROXY",
        "summary": {
            "integrated_cfd_proxy_extracted": ready,
            "plotfile_count": len(history),
            "mdpi_radiation_metric_count": len(comparisons),
            "radiative_fraction": args.radiative_fraction,
            "peak_integrated_radiative_power_w": peak_power,
            "peak_integrated_positive_heat_release_w": float(peak["positive_heat_release_w"]),
            "peak_plotfile": peak["plotfile"],
            "peak_time_s": float(peak["time_s"]),
            "virtual_radiometer_flux_generated": True,
            "comparison_executed": True,
            "agreement_pass_count": 0,
            "agreement_fail_count": len(comparisons),
            "case_aligned_cfd_radiation_agreement": False,
            "current_outputs_sufficient_for_mdpi_radiation_agreement": False,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "proxy_definition": {
            "source_field": "HeatRelease",
            "positive_integral": "sum(max(HeatRelease, 0))*cell_volume",
            "virtual_flux": "radiative_fraction*positive_integral/(4*pi*distance_m^2)",
            "claim": "finite integrated CFD observable and virtual-radiometer export path, not calibrated radiation physics",
        },
        "history": history,
        "comparisons": comparisons,
        "output_files": {
            "history_csv": str(output_history),
            "comparison_csv": str(output_comparison),
        },
        "limitations": [
            "Uses positive HeatRelease volume integral with an assumed radiative fraction.",
            "Does not model flame surface, gas radiation, wall/obstruction view factors, absorption, soot, or radiometer orientation.",
            "Uses MDPI distance anchors only; it is not case-aligned to a full experiment setup.",
            "Does not clear strict calibrated radiation or overpressure credit.",
        ],
        "evidence_files": [
            evidence_entry("radiation_table", Path(args.radiation_table)),
            evidence_entry("radiation_metrics_csv", Path(radiation_table["output_files"]["radiation_metrics_csv"])),
            evidence_entry("history_csv", output_history),
            evidence_entry("comparison_csv", output_comparison),
            evidence_entry("peak_plotfile_header", Path(peak["plotfile"]) / "Header"),
            evidence_entry("peak_plotfile_cell_h", Path(peak["plotfile"]) / "Level_0" / "Cell_H"),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("integrated_cfd_proxy_extracted") is True, "integrated proxy not extracted")
    require(int(summary.get("plotfile_count", 0)) >= 3, "too few plotfiles integrated")
    require(int(summary.get("mdpi_radiation_metric_count", 0)) >= 4, "too few MDPI radiation metrics")
    require(float(summary.get("peak_integrated_radiative_power_w", 0.0)) > 0.0, "peak radiative proxy not positive")
    require(summary.get("virtual_radiometer_flux_generated") is True, "virtual radiometer flux missing")
    require(summary.get("comparison_executed") is True, "comparison not executed")
    require(summary.get("agreement_pass_count") == 0, "integrated proxy must not claim agreement passes")
    require(int(summary.get("agreement_fail_count", 0)) >= 4, "integrated proxy fail count too small")
    require(summary.get("case_aligned_cfd_radiation_agreement") is False, "case-aligned radiation agreement overclaimed")
    require(
        summary.get("current_outputs_sufficient_for_mdpi_radiation_agreement") is False,
        "MDPI radiation sufficiency overclaimed",
    )
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire MDPI Radiation Integrated CFD Proxy",
        "",
        f"- Status: `{report['status']}`",
        f"- Plotfiles integrated: `{s['plotfile_count']}`",
        f"- MDPI radiation metrics: `{s['mdpi_radiation_metric_count']}`",
        f"- Radiative fraction: `{s['radiative_fraction']}`",
        f"- Peak integrated radiative proxy power: `{s['peak_integrated_radiative_power_w']}` W",
        f"- Peak plotfile: `{s['peak_plotfile']}`",
        f"- Virtual radiometer flux generated: `{s['virtual_radiometer_flux_generated']}`",
        f"- Agreement pass/fail: `{s['agreement_pass_count']}/{s['agreement_fail_count']}`",
        f"- Strict fire calibration blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines += ["", "## Evidence", ""]
    lines.extend(f"- `{entry['label']}`: `{entry['path']}`" for entry in report["evidence_files"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plot-root", type=Path, default=PLOT_ROOT)
    ap.add_argument("--radiation-table", type=Path, default=RADIATION_TABLE)
    ap.add_argument("--radiative-fraction", type=float, default=0.2)
    ap.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    ap.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    ap.add_argument("--output-history-csv", type=Path, default=DEFAULT_HISTORY_CSV)
    ap.add_argument("--output-comparison-csv", type=Path, default=DEFAULT_COMPARISON_CSV)
    ap.add_argument("--verify-json", type=Path)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(args.verify_json)
            validate_report(data)
            print(f"h2_fire_mdpi_radiation_integrated_cfd_proxy VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report(args)
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, args.output_md)
        print(f"h2_fire_mdpi_radiation_integrated_cfd_proxy PASS json={args.output_json} md={args.output_md} status={report['status']}")
        return 0
    except (IntegratedRadiationProxyError, amrex_reader.PlotfileError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"h2_fire_mdpi_radiation_integrated_cfd_proxy FAIL: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
