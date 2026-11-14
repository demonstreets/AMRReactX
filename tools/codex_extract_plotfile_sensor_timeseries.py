#!/usr/bin/env python3
"""Extract sensor time series from AMReX plotfiles."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import amrex_reader  # noqa: E402


class SensorExtractionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SensorExtractionError(message)


def finite_float(value: str, label: str) -> float:
    try:
        out = float(value)
    except ValueError as exc:
        raise SensorExtractionError(f"{label} is not a float: {value!r}") from exc
    require(math.isfinite(out), f"{label} must be finite")
    return out


def load_sensors(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f"missing sensor CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require(reader.fieldnames is not None, "sensor CSV header missing")
        fields = set(reader.fieldnames)
        required = {"sensor_id", "x_m", "y_m"}
        require(required.issubset(fields), f"sensor CSV must include {sorted(required)}")
        sensors = []
        seen = set()
        for row_num, row in enumerate(reader, start=2):
            sid = (row.get("sensor_id") or "").strip()
            require(sid, f"sensor_id missing at row {row_num}")
            require(sid not in seen, f"duplicate sensor_id: {sid}")
            seen.add(sid)
            sensor = {
                "sensor_id": sid,
                "x_m": finite_float(row.get("x_m", ""), f"{sid}.x_m"),
                "y_m": finite_float(row.get("y_m", ""), f"{sid}.y_m"),
                "z_m": finite_float(row.get("z_m", "0.0") or "0.0", f"{sid}.z_m"),
            }
            sensors.append(sensor)
    require(sensors, "sensor CSV contains no sensors")
    return sensors


def nearest_index(coords: Any, value: float, axis: str, sensor_id: str) -> tuple[int, float]:
    vals = list(float(v) for v in coords)
    require(vals, f"plotfile has no {axis} coordinates")
    idx = min(range(len(vals)), key=lambda i: abs(vals[i] - value))
    return idx, vals[idx]


def interpolation_bracket(coords: Any, value: float, axis: str, sensor_id: str) -> tuple[int, int, float]:
    vals = list(float(v) for v in coords)
    require(vals, f"plotfile has no {axis} coordinates")
    if value <= vals[0]:
        return 0, 0, 0.0
    last = len(vals) - 1
    if value >= vals[last]:
        return last, last, 0.0
    for hi in range(1, len(vals)):
        if vals[hi] >= value:
            lo = hi - 1
            span = vals[hi] - vals[lo]
            require(span > 0.0, f"{sensor_id} {axis} coordinates are not strictly increasing")
            return lo, hi, (value - vals[lo]) / span
    raise SensorExtractionError(f"{sensor_id} {axis} interpolation bracket not found")


def lerp(a: float, b: float, t: float) -> float:
    return (1.0 - t) * a + t * b


def linear_sample(arr: Any, ndim: int, ix0: int, ix1: int, fx: float, iy0: int, iy1: int, fy: float, iz0: int, iz1: int, fz: float) -> float:
    if ndim >= 3:
        c000 = float(arr[ix0, iy0, iz0])
        c100 = float(arr[ix1, iy0, iz0])
        c010 = float(arr[ix0, iy1, iz0])
        c110 = float(arr[ix1, iy1, iz0])
        c001 = float(arr[ix0, iy0, iz1])
        c101 = float(arr[ix1, iy0, iz1])
        c011 = float(arr[ix0, iy1, iz1])
        c111 = float(arr[ix1, iy1, iz1])
        c00 = lerp(c000, c100, fx)
        c10 = lerp(c010, c110, fx)
        c01 = lerp(c001, c101, fx)
        c11 = lerp(c011, c111, fx)
        c0 = lerp(c00, c10, fy)
        c1 = lerp(c01, c11, fy)
        return lerp(c0, c1, fz)
    c00 = float(arr[ix0, iy0])
    c10 = float(arr[ix1, iy0])
    c01 = float(arr[ix0, iy1])
    c11 = float(arr[ix1, iy1])
    return lerp(lerp(c00, c10, fx), lerp(c01, c11, fx), fy)


def sample_variable(arr: Any, ndim: int, mode: str, indices: dict[str, int], fractions: dict[str, float]) -> float:
    if mode == "nearest":
        value = arr[indices["ix"], indices["iy"], indices["iz"]] if ndim >= 3 else arr[indices["ix"], indices["iy"]]
        return float(value)
    return linear_sample(
        arr,
        ndim,
        indices["ix0"],
        indices["ix1"],
        fractions["fx"],
        indices["iy0"],
        indices["iy1"],
        fractions["fy"],
        indices["iz0"],
        indices["iz1"],
        fractions["fz"],
    )


def sample_plotfile(
    plotfile: Path,
    sensors: list[dict[str, Any]],
    variables: list[str],
    sampling_mode: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = amrex_reader.read_plotfile(str(plotfile))
    fields = data["fields"]
    missing = [name for name in variables if name not in fields]
    require(not missing, f"{plotfile} missing variables: {missing}")
    ndim = int(data["ndim"])
    prob_lo = [float(v) for v in data["prob_lo"]]
    prob_hi = [float(v) for v in data["prob_hi"]]
    rows = []
    max_distance = 0.0
    for sensor in sensors:
        x = float(sensor["x_m"])
        y = float(sensor["y_m"])
        z = float(sensor["z_m"])
        require(prob_lo[0] <= x <= prob_hi[0], f"{sensor['sensor_id']} x outside domain")
        require(prob_lo[1] <= y <= prob_hi[1], f"{sensor['sensor_id']} y outside domain")
        if ndim >= 3:
            require(prob_lo[2] <= z <= prob_hi[2], f"{sensor['sensor_id']} z outside domain")
        ix, sx = nearest_index(data["x"], x, "x", sensor["sensor_id"])
        iy, sy = nearest_index(data["y"], y, "y", sensor["sensor_id"])
        ix0, ix1, fx = interpolation_bracket(data["x"], x, "x", sensor["sensor_id"])
        iy0, iy1, fy = interpolation_bracket(data["y"], y, "y", sensor["sensor_id"])
        if ndim >= 3:
            iz, sz = nearest_index(data["z"], z, "z", sensor["sensor_id"])
            iz0, iz1, fz = interpolation_bracket(data["z"], z, "z", sensor["sensor_id"])
        else:
            iz, sz = 0, 0.0
            iz0, iz1, fz = 0, 0, 0.0
        dist = math.sqrt((sx - x) ** 2 + (sy - y) ** 2 + ((sz - z) ** 2 if ndim >= 3 else 0.0))
        max_distance = max(max_distance, dist)
        indices = {
            "ix": ix,
            "iy": iy,
            "iz": iz,
            "ix0": ix0,
            "ix1": ix1,
            "iy0": iy0,
            "iy1": iy1,
            "iz0": iz0,
            "iz1": iz1,
        }
        fractions = {"fx": fx, "fy": fy, "fz": fz}
        row: dict[str, Any] = {
            "plotfile": str(plotfile),
            "time_s": float(data["time"]),
            "sensor_id": sensor["sensor_id"],
            "sampling_mode": sampling_mode,
            "requested_x_m": x,
            "requested_y_m": y,
            "requested_z_m": z,
            "sampled_i": ix,
            "sampled_j": iy,
            "sampled_k": iz,
            "sampled_x_m": sx,
            "sampled_y_m": sy,
            "sampled_z_m": sz,
            "nearest_cell_distance_m": dist,
        }
        for name in variables:
            arr = fields[name]
            value = sample_variable(arr, ndim, sampling_mode, indices, fractions)
            require(math.isfinite(value), f"{plotfile} {sensor['sensor_id']} {name} is not finite")
            row[name] = value
        rows.append(row)
    meta = {
        "plotfile": str(plotfile),
        "time_s": float(data["time"]),
        "ndim": ndim,
        "prob_lo": prob_lo,
        "prob_hi": prob_hi,
        "dx": [float(v) for v in data["dx"]],
        "variable_count": len(variables),
        "sensor_count": len(sensors),
        "sampling_mode": sampling_mode,
        "max_nearest_cell_distance_m": max_distance,
    }
    return rows, meta


def write_csv(path: Path, rows: list[dict[str, Any]], variables: list[str]) -> None:
    base = [
        "plotfile",
        "time_s",
        "sensor_id",
        "sampling_mode",
        "requested_x_m",
        "requested_y_m",
        "requested_z_m",
        "sampled_i",
        "sampled_j",
        "sampled_k",
        "sampled_x_m",
        "sampled_y_m",
        "sampled_z_m",
        "nearest_cell_distance_m",
    ]
    fieldnames = base + variables
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sensor-csv", required=True, type=Path)
    ap.add_argument("--plotfile", action="append", default=[], type=Path)
    ap.add_argument("--variables", nargs="+", required=True)
    ap.add_argument("--sampling-mode", choices=["nearest", "linear"], default="nearest")
    ap.add_argument("--output-csv", required=True, type=Path)
    ap.add_argument("--output-json", required=True, type=Path)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        plotfiles = args.plotfile
        require(plotfiles, "at least one --plotfile is required")
        sensors = load_sensors(args.sensor_csv)
        rows: list[dict[str, Any]] = []
        plot_meta = []
        for plotfile in plotfiles:
            require(plotfile.is_dir(), f"missing plotfile directory: {plotfile}")
            plot_rows, meta = sample_plotfile(plotfile, sensors, args.variables, args.sampling_mode)
            rows.extend(plot_rows)
            plot_meta.append(meta)
        rows.sort(key=lambda row: (float(row["time_s"]), str(row["sensor_id"])))
        write_csv(args.output_csv, rows, args.variables)
        summary = {
            "sensor_timeseries_extracted": True,
            "plotfile_count": len(plotfiles),
            "sensor_count": len(sensors),
            "variable_count": len(args.variables),
            "row_count": len(rows),
            "variables": args.variables,
            "sampling_mode": args.sampling_mode,
            "linear_interpolation_used": args.sampling_mode == "linear",
            "max_nearest_cell_distance_m": max(meta["max_nearest_cell_distance_m"] for meta in plot_meta),
            "strict_fire_calibration_blocker_cleared": False,
        }
        report = {
            "schema_version": 1,
            "status": "PASS-PLOTFILE-SENSOR-TIMESERIES-EXTRACTION",
            "summary": summary,
            "plotfiles": plot_meta,
            "sensor_csv": str(args.sensor_csv),
            "output_csv": str(args.output_csv),
            "claim_boundary": [
                "Nearest-cell and cell-centered linear plotfile sensor extraction only.",
                "Does not create experimental sensor coordinates.",
                "Does not clear calibrated overpressure or radiation agreement.",
            ],
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            "plotfile_sensor_timeseries_extraction PASS "
            f"csv={args.output_csv} json={args.output_json} rows={len(rows)}"
        )
        return 0
    except (SensorExtractionError, amrex_reader.PlotfileError, OSError, ValueError) as exc:
        print(f"plotfile_sensor_timeseries_extraction FAIL: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
