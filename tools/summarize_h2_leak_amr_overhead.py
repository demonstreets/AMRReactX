#!/usr/bin/env python3
"""Summarize H2 leak AMR-vs-uniform overhead from maintained smoke logs."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import amrex_reader  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def dir_bytes(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def latest_plotfile(run_dir: Path) -> Path:
    plots = []
    for item in run_dir.iterdir():
        if item.is_dir():
            m = re.fullmatch(r"plt(\d+)", item.name)
            if m:
                plots.append((int(m.group(1)), item))
    if not plots:
        fail(f"no plotfiles found in {run_dir}")
    return max(plots, key=lambda p: p[0])[1]


def count_fabs(plot: Path, finest_level: int) -> tuple[int, int]:
    finest_fabs = 0
    total_fabs = 0
    for level in range(finest_level + 1):
        cell_h = plot / f"Level_{level}" / "Cell_H"
        text = read_text(cell_h)
        count = sum(1 for line in text.splitlines() if line.strip().startswith("FabOnDisk:"))
        total_fabs += count
        if level == finest_level:
            finest_fabs = count
    return finest_fabs, total_fabs


def parse_diag_float(pattern: str, text: str, label: str) -> float:
    m = re.search(pattern, text)
    if not m:
        fail(f"missing {label}")
    return float(m.group(1))


def parse_diag_int(pattern: str, text: str, label: str) -> int:
    m = re.search(pattern, text)
    if not m:
        fail(f"missing {label}")
    return int(m.group(1))


def summarize_case(name: str, case_dir: Path) -> dict[str, object]:
    run_dir = case_dir / "run"
    if not run_dir.is_dir():
        fail(f"missing run directory for {name}: {run_dir}")
    run_log = read_text(case_dir / "run.log")
    for marker in ("Unused ParmParse Variables", "RuntimeWarning", "Traceback"):
        if marker in run_log:
            fail(f"{marker} present in {name} run.log")

    step_matches = [
        (int(m.group(1)), float(m.group(2)), int(m.group(3)))
        for m in re.finditer(
            r"STEP \[(\d+)\]\s*-\s*Time:\s*([0-9.eE+-]+),\s*dt\s*[0-9.eE+-]+,\s*Ncells\s+(\d+)",
            run_log,
        )
    ]
    if not step_matches:
        fail(f"no STEP/Ncells records in {name} run.log")
    advance_times = [
        float(m.group(1))
        for m in re.finditer(r"PeleLMeX::Advance\(\)\s*-->\s*Time:\s*([0-9.eE+-]+)", run_log)
    ]
    if not advance_times:
        fail(f"no PeleLMeX::Advance timing records in {name} run.log")

    plot = latest_plotfile(run_dir)
    meta = amrex_reader._parse_header(str(plot / "Header"))
    finest_fabs, total_fabs = count_fabs(plot, int(meta["finest_level"]))
    plotfiles = [item for item in run_dir.iterdir() if item.is_dir() and re.fullmatch(r"plt\d+", item.name)]

    hazard = read_text(case_dir / "hazard_summary.log")
    planes = read_text(case_dir / "hazard_planes.log")
    validation = read_text(case_dir / "validation.log")

    ncells = [item[2] for item in step_matches]
    max_step_index = max(item[0] for item in step_matches)
    return {
        "case": name,
        "log_dir": str(case_dir),
        "final_plotfile": str(plot),
        "finest_level": int(meta["finest_level"]),
        "finest_fab_count": finest_fabs,
        "total_fab_count": total_fabs,
        "plotfile_count": len(plotfiles),
        "steps_observed": len(step_matches),
        "max_step_index": max_step_index,
        "mean_ncells": sum(ncells) / len(ncells),
        "max_ncells": max(ncells),
        "advance_samples": len(advance_times),
        "advance_seconds": sum(advance_times),
        "mean_advance_seconds": sum(advance_times) / len(advance_times),
        "final_plotfile_bytes": dir_bytes(plot),
        "all_plotfiles_bytes": sum(dir_bytes(item) for item in plotfiles),
        "mass_ratioN": parse_diag_float(r"mass_ratioN=([0-9.eE+-]+)", validation, f"{name} mass_ratioN"),
        "cloud_volume": parse_diag_float(r"cloud_volume=([0-9.eE+-]+)", hazard, f"{name} cloud_volume"),
        "max_X": parse_diag_float(r"max_X=([0-9.eE+-]+)", hazard, f"{name} max_X"),
        "active_planes": parse_diag_int(r"active_planes=([0-9]+)", planes, f"{name} active_planes"),
        "flammable_planes": parse_diag_int(r"flammable_planes=([0-9]+)", planes, f"{name} flammable_planes"),
    }


def ratio(num: float, den: float) -> float:
    if den <= 0.0:
        fail(f"nonpositive denominator for ratio: {den}")
    return num / den


def add_ratios(base: dict[str, object], amr: dict[str, object]) -> dict[str, float]:
    return {
        "mean_ncells_ratio": ratio(float(amr["mean_ncells"]), float(base["mean_ncells"])),
        "max_ncells_ratio": ratio(float(amr["max_ncells"]), float(base["max_ncells"])),
        "advance_seconds_ratio": ratio(float(amr["advance_seconds"]), float(base["advance_seconds"])),
        "mean_advance_seconds_ratio": ratio(float(amr["mean_advance_seconds"]), float(base["mean_advance_seconds"])),
        "final_plotfile_bytes_ratio": ratio(float(amr["final_plotfile_bytes"]), float(base["final_plotfile_bytes"])),
        "all_plotfiles_bytes_ratio": ratio(float(amr["all_plotfiles_bytes"]), float(base["all_plotfiles_bytes"])),
    }


def format_row(row: dict[str, object], ratios: dict[str, float] | None = None) -> dict[str, object]:
    out = dict(row)
    for key in ("mean_ncells", "advance_seconds", "mean_advance_seconds", "mass_ratioN", "cloud_volume", "max_X"):
        out[key] = f"{float(out[key]):.8e}"
    for key in ("mean_ncells_ratio", "max_ncells_ratio", "advance_seconds_ratio", "mean_advance_seconds_ratio", "final_plotfile_bytes_ratio", "all_plotfiles_bytes_ratio"):
        out[key] = "" if ratios is None else f"{ratios[key]:.8e}"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", required=True, type=Path)
    parser.add_argument("--amr-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-mean-ncells-ratio", type=float, default=8.0)
    parser.add_argument("--max-advance-seconds-ratio", type=float, default=20.0)
    parser.add_argument("--max-final-plotfile-bytes-ratio", type=float, default=20.0)
    args = parser.parse_args()

    base = summarize_case("baseline", args.baseline_dir)
    amr = summarize_case("amr", args.amr_dir)
    if int(base["finest_level"]) != 0:
        fail(f"baseline finest_level expected 0, got {base['finest_level']}")
    if int(amr["finest_level"]) < 1 or int(amr["finest_fab_count"]) <= 0:
        fail(f"AMR case missing populated fine level: {amr}")

    ratios = add_ratios(base, amr)
    if ratios["mean_ncells_ratio"] > args.max_mean_ncells_ratio:
        fail(f"mean Ncells ratio too large: {ratios['mean_ncells_ratio']:.6g}")
    if ratios["advance_seconds_ratio"] > args.max_advance_seconds_ratio:
        fail(f"advance seconds ratio too large: {ratios['advance_seconds_ratio']:.6g}")
    if ratios["final_plotfile_bytes_ratio"] > args.max_final_plotfile_bytes_ratio:
        fail(f"final plotfile byte ratio too large: {ratios['final_plotfile_bytes_ratio']:.6g}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case", "log_dir", "final_plotfile", "finest_level", "finest_fab_count", "total_fab_count",
        "plotfile_count", "steps_observed", "max_step_index", "mean_ncells", "max_ncells",
        "advance_samples", "advance_seconds", "mean_advance_seconds", "final_plotfile_bytes",
        "all_plotfiles_bytes", "mass_ratioN", "cloud_volume", "max_X", "active_planes",
        "flammable_planes", "mean_ncells_ratio", "max_ncells_ratio", "advance_seconds_ratio",
        "mean_advance_seconds_ratio", "final_plotfile_bytes_ratio", "all_plotfiles_bytes_ratio",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(format_row(base))
        writer.writerow(format_row(amr, ratios))

    print(
        "h2_leak_amr_overhead_summary PASS "
        f"output={args.output} "
        f"mean_ncells_ratio={ratios['mean_ncells_ratio']:.8e} "
        f"advance_seconds_ratio={ratios['advance_seconds_ratio']:.8e} "
        f"final_plotfile_bytes_ratio={ratios['final_plotfile_bytes_ratio']:.8e} "
        f"amr_finest_level={amr['finest_level']} amr_finest_fabs={amr['finest_fab_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
