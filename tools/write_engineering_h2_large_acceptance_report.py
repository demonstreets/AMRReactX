#!/usr/bin/env python3
"""Package and verify the self-built large H2 engineering acceptance run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-LARGE-ENGINEERING-ACCEPTANCE"
STATUS_FAIL = "FAIL-H2-LARGE-ENGINEERING-ACCEPTANCE"
DEFAULT_SOURCE_ROOT = Path("/tmp/codex_h2_engineering_acceptance_20260727_8rank_96x48x48_120step_v2")
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_large_acceptance_20260727"
)
FAIL_MARKERS = (
    "FAIL",
    "Traceback",
    "RuntimeError",
    "Segmentation fault",
    "SIGSEGV",
    "Backtrace",
    "Unused ParmParse Variables",
)
COPY_FILES = [
    "plan_amr_compare_summary.csv",
    "amr_overhead_summary.csv",
    "inputs/input.codex_open_domain_plan_amr_baseline_smoke",
    "inputs/input.codex_open_domain_plan_amr_level1_smoke",
    "baseline/validation.log",
    "baseline/profile_validation.log",
    "baseline/hazard_summary.log",
    "baseline/hazard_planes.log",
    "baseline/hazard_planes.csv",
    "baseline/hazard_timeseries.log",
    "baseline/hazard_timeseries.csv",
    "baseline/mpi_validation.log",
    "baseline/run/input.codex_open_domain_plan_amr_baseline_smoke",
    "amr/validation.log",
    "amr/profile_validation.log",
    "amr/hazard_summary.log",
    "amr/hazard_planes.log",
    "amr/hazard_planes.csv",
    "amr/hazard_timeseries.log",
    "amr/hazard_timeseries.csv",
    "amr/mpi_validation.log",
    "amr/run/input.codex_open_domain_plan_amr_level1_smoke",
]


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON report is not an object: {path}")
    return data


def finite(value: Any, label: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise AcceptanceError(f"invalid numeric value {label}={value!r}") from exc
    require(math.isfinite(out), f"nonfinite numeric value {label}={value!r}")
    return out


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f"empty CSV: {path}")
    return rows


def row_by_case(rows: list[dict[str, str]], case: str) -> dict[str, str]:
    matches = [row for row in rows if row.get("case") == case]
    require(len(matches) == 1, f"expected one {case} row, found {len(matches)}")
    return matches[0]


def parse_setting(path: Path, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}\s*=\s*(.+?)\s*$", read_text(path), re.M)
    require(match is not None, f"missing {key} in {path}")
    return match.group(1)


def parse_int_triplet(path: Path, key: str) -> list[int]:
    parts = parse_setting(path, key).split()
    require(len(parts) >= 3, f"{key} must contain at least three integers in {path}")
    return [int(part) for part in parts[:3]]


def parse_float_triplet(path: Path, key: str) -> list[float]:
    parts = parse_setting(path, key).split()
    require(len(parts) == 3, f"{key} must contain three floats in {path}")
    return [finite(part, f"{key}[{idx}]") for idx, part in enumerate(parts)]


def parse_mpi_validation(path: Path) -> dict[str, Any]:
    text = read_text(path)
    ranks = re.search(r"\branks=([0-9]+)\b", text)
    final_time = re.search(r"\bfinal_time=([0-9.eE+-]+)\b", text)
    finalized = re.search(r"\bfinalized=([0-9]+)\b", text)
    require(ranks is not None, f"missing ranks in {path}")
    require(final_time is not None, f"missing final_time in {path}")
    require(finalized is not None, f"missing finalized flag in {path}")
    return {
        "ranks": int(ranks.group(1)),
        "final_time": finite(final_time.group(1), "mpi final_time"),
        "finalized": int(finalized.group(1)),
    }


def scan_failure_markers(source_root: Path) -> list[str]:
    hits: list[str] = []
    for path in sorted(source_root.rglob("*.log")):
        text = read_text(path)
        rel = path.relative_to(source_root)
        for marker in FAIL_MARKERS:
            if marker in text:
                hits.append(f"{rel}:{marker}")
        if re.search(r"(?<![A-Za-z0-9_])(?:nan|inf)(?![A-Za-z0-9_])", text, re.I):
            hits.append(f"{rel}:nonfinite-token")
    return hits


def copy_text_evidence(source_root: Path, output_root: Path) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    files_root = output_root / "files"
    if files_root.exists():
        shutil.rmtree(files_root)
    for rel in COPY_FILES:
        src = source_root / rel
        require(src.is_file(), f"missing required acceptance evidence: {src}")
        dst = files_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = read_text(src)
        text = text.replace(str(source_root), "${ACCEPTANCE_ROOT}")
        dst.write_text(text, encoding="utf-8")
        copied.append(
            {
                "relative_path": rel,
                "path": str(dst),
                "sha256": sha256_file(dst),
                "size_bytes": dst.stat().st_size,
            }
        )
    return copied


def plotfile_header_entry(source_root: Path, case: str, step: int) -> dict[str, Any]:
    plot = source_root / case / "run" / f"plt{step:05d}"
    header = plot / "Header"
    require(header.is_file(), f"missing final plotfile Header: {header}")
    levels = []
    for level_dir in sorted(plot.glob("Level_*")):
        cell_h = level_dir / "Cell_H"
        require(cell_h.is_file(), f"missing {cell_h}")
        fab_count = sum(1 for line in read_text(cell_h).splitlines() if line.strip().startswith("FabOnDisk:"))
        require(fab_count > 0, f"no FabOnDisk entries in {cell_h}")
        levels.append(
            {
                "level": int(level_dir.name.split("_", 1)[1]),
                "cell_h_sha256": sha256_file(cell_h),
                "fab_count": fab_count,
            }
        )
    return {
        "case": case,
        "plotfile": str(plot),
        "header_sha256": sha256_file(header),
        "levels": levels,
    }


def build_report(source_root: Path, output_root: Path) -> dict[str, Any]:
    require(source_root.is_dir(), f"missing source root: {source_root}")
    failures = scan_failure_markers(source_root)
    require(not failures, "failure or nonfinite markers found: " + "; ".join(failures[:20]))

    summary_rows = load_csv(source_root / "plan_amr_compare_summary.csv")
    overhead_rows = load_csv(source_root / "amr_overhead_summary.csv")
    base = row_by_case(summary_rows, "baseline")
    amr = row_by_case(summary_rows, "amr")
    overhead = row_by_case(overhead_rows, "amr")
    baseline_mpi = parse_mpi_validation(source_root / "baseline/mpi_validation.log")
    amr_mpi = parse_mpi_validation(source_root / "amr/mpi_validation.log")
    require(baseline_mpi["ranks"] == amr_mpi["ranks"], "baseline/AMR MPI rank mismatch")
    require(baseline_mpi["finalized"] == 1 and amr_mpi["finalized"] == 1, "MPI finalization check failed")

    baseline_input = source_root / "inputs/input.codex_open_domain_plan_amr_baseline_smoke"
    amr_input = source_root / "inputs/input.codex_open_domain_plan_amr_level1_smoke"
    n_cell = parse_int_triplet(baseline_input, "amr.n_cell")
    prob_hi = parse_float_triplet(baseline_input, "geometry.prob_hi")
    max_step = int(parse_setting(baseline_input, "amr.max_step"))
    plot_int = int(parse_setting(baseline_input, "amr.plot_int"))
    ref_ratio = parse_int_triplet(amr_input, "amr.ref_ratio")
    equivalent_finest = [n * ref_ratio[idx] for idx, n in enumerate(n_cell)]

    metrics = {
        "ranks": baseline_mpi["ranks"],
        "baseline_final_time": baseline_mpi["final_time"],
        "amr_final_time": amr_mpi["final_time"],
        "max_step": max_step,
        "plot_int": plot_int,
        "base_n_cell": n_cell,
        "base_cell_count": math.prod(n_cell),
        "domain_prob_hi": prob_hi,
        "amr_ref_ratio": ref_ratio,
        "equivalent_finest_n_cell": equivalent_finest,
        "equivalent_finest_cell_count": math.prod(equivalent_finest),
        "baseline_finest_level": int(base["finest_level"]),
        "amr_finest_level": int(amr["finest_level"]),
        "amr_regrid_count": int(amr["regrid_count"]),
        "baseline_final_mass_ratio": finite(base["mass_ratio"], "baseline mass_ratio"),
        "amr_final_mass_ratio": finite(amr["mass_ratio"], "amr mass_ratio"),
        "baseline_cloud_volume": finite(base["cloud_volume"], "baseline cloud_volume"),
        "amr_cloud_volume": finite(amr["cloud_volume"], "amr cloud_volume"),
        "baseline_max_x": finite(base["max_X"], "baseline max_X"),
        "amr_max_x": finite(amr["max_X"], "amr max_X"),
        "cloud_rel_diff": finite(amr["cloud_rel_diff"], "cloud_rel_diff"),
        "peak_rel_diff": finite(amr["peak_rel_diff"], "peak_rel_diff"),
        "centroid_abs_diff": finite(amr["centroid_abs_diff"], "centroid_abs_diff"),
        "downstream_abs_diff": finite(amr["downstream_abs_diff"], "downstream_abs_diff"),
        "mean_ncells_ratio": finite(overhead["mean_ncells_ratio"], "mean_ncells_ratio"),
        "advance_seconds_ratio": finite(overhead["advance_seconds_ratio"], "advance_seconds_ratio"),
        "final_plotfile_bytes_ratio": finite(overhead["final_plotfile_bytes_ratio"], "final_plotfile_bytes_ratio"),
    }

    require(metrics["ranks"] >= 8, "acceptance run must use at least 8 MPI ranks")
    require(metrics["base_cell_count"] >= 200_000, "base grid is too small for large engineering acceptance")
    require(metrics["equivalent_finest_cell_count"] >= 1_500_000, "AMR equivalent fine grid is too small")
    require(metrics["amr_finest_level"] >= 1, "AMR acceptance must create level 1")
    require(metrics["amr_regrid_count"] >= 1, "AMR acceptance must exercise regridding")
    require(abs(metrics["baseline_final_mass_ratio"] - 1.0) <= 5.0e-3, "baseline mass ratio outside tolerance")
    require(abs(metrics["amr_final_mass_ratio"] - 1.0) <= 5.0e-3, "AMR mass ratio outside tolerance")
    require(metrics["baseline_cloud_volume"] > 0.0 and metrics["amr_cloud_volume"] > 0.0, "missing flammable cloud")
    require(metrics["baseline_max_x"] > 0.0 and metrics["amr_max_x"] > 0.0, "missing positive peak H2")
    require(metrics["cloud_rel_diff"] <= 0.45, "AMR cloud drift too large")
    require(metrics["peak_rel_diff"] <= 0.50, "AMR peak drift too large")
    require(metrics["advance_seconds_ratio"] <= 20.0, "AMR advance overhead too large")

    copied = copy_text_evidence(source_root, output_root)
    plot_headers = [
        plotfile_header_entry(source_root, "baseline", max_step),
        plotfile_header_entry(source_root, "amr", max_step),
    ]
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "Self-built Large H2 Engineering Acceptance Run",
        "source_root": str(source_root),
        "acceptance_basis": "user-authorized self-built large engineering case; public external benchmark data is optional for this gate",
        "metrics": metrics,
        "mpi_acceptance": {
            "mode": "mpi",
            "expected_ranks": metrics["ranks"],
            "validated_finalization": True,
            "validated_no_failure_or_nonfinite_markers": True,
        },
        "plotfile_headers": plot_headers,
        "evidence_files": copied,
        "limitations": [
            "This clears the engineering stability acceptance criterion, not external experimental validation.",
            "The acceptance is scoped to gas-phase H2 leak dispersion/open-domain AMR engineering behavior.",
        ],
    }
    return report


def validate_report(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS_PASS, "status is not PASS")
    metrics = data.get("metrics")
    require(isinstance(metrics, dict), "missing metrics")
    require(int(metrics.get("ranks", 0)) >= 8, "rank count too low")
    require(int(metrics.get("base_cell_count", 0)) >= 200_000, "base grid too small")
    require(int(metrics.get("equivalent_finest_cell_count", 0)) >= 1_500_000, "equivalent fine grid too small")
    require(int(metrics.get("amr_finest_level", 0)) >= 1, "missing AMR level")
    require(float(metrics.get("cloud_rel_diff", 999.0)) <= 0.45, "cloud drift too large")
    require(float(metrics.get("peak_rel_diff", 999.0)) <= 0.50, "peak drift too large")
    require(data.get("mpi_acceptance", {}).get("validated_no_failure_or_nonfinite_markers") is True, "nonfinite scan missing")
    entries = data.get("evidence_files")
    require(isinstance(entries, list) and entries, "missing evidence_files")
    if check_hashes:
        for entry in entries:
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], output: Path) -> None:
    m = report["metrics"]
    lines = [
        "# Self-built Large H2 Engineering Acceptance Run",
        "",
        f"- Status: {report['status']}",
        f"- Source root: `{report['source_root']}`",
        f"- MPI ranks: {m['ranks']}",
        f"- Base grid: {m['base_n_cell']} ({m['base_cell_count']} cells)",
        f"- AMR equivalent fine grid: {m['equivalent_finest_n_cell']} ({m['equivalent_finest_cell_count']} cells)",
        f"- Max step / plot interval: {m['max_step']} / {m['plot_int']}",
        f"- AMR finest level / regrid count: {m['amr_finest_level']} / {m['amr_regrid_count']}",
        f"- Mass ratios baseline/AMR: {m['baseline_final_mass_ratio']:.8e} / {m['amr_final_mass_ratio']:.8e}",
        f"- Cloud relative diff / peak relative diff: {m['cloud_rel_diff']:.8e} / {m['peak_rel_diff']:.8e}",
        f"- AMR advance overhead ratio: {m['advance_seconds_ratio']:.8e}",
        "",
        "The run passed the engineering stability gate: parallel finalization, AMR level creation, regridding, plotfile integrity, finite metrics, positive H2 cloud/hazard metrics, and no failure/NaN/Inf log markers.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"VERIFY-PASS {args.verify_json} status={data['status']}")
        return 0

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    report = build_report(Path(args.source_root), output_root)
    validate_report(report, check_hashes=True)
    json_path = output_root / "h2_large_acceptance_report.json"
    md_path = output_root / "h2_large_acceptance_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    validate_report(load_json(json_path), check_hashes=True)
    print(f"WROTE {json_path} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
