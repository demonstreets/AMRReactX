#!/usr/bin/env python3
"""Create a PeleLMeX gas-source input from an external vaporization CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = (
    "time_s",
    "mdot_kg_s",
    "vapor_T_K",
    "fuel_species",
)
OPTIONAL_COLUMNS = (
    "leak_vel_x_m_s",
    "leak_vel_y_m_s",
    "leak_vel_z_m_s",
    "source_radius_m",
    "source_x_m",
    "source_y_m",
    "source_z_m",
    "source_pressure_Pa",
)
ALLOWED_SURROGATE_SPECIES = {"H2", "CH4", "C3H8"}
MAX_SCHEDULE_POINTS = 64


class SourceInputError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceInputError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def finite(value: str, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SourceInputError(f"{label} is not numeric: {value!r}") from exc
    require(math.isfinite(number), f"{label} is not finite: {number!r}")
    return number


def read_source_csv(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f"missing source CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        missing = [name for name in REQUIRED_COLUMNS if name not in header]
        require(not missing, f"source CSV missing columns: {', '.join(missing)}")
        rows: list[dict[str, Any]] = []
        last_time = -math.inf
        for idx, row in enumerate(reader, 1):
            time_s = finite(row.get("time_s", ""), f"row {idx} time_s")
            mdot = finite(row.get("mdot_kg_s", ""), f"row {idx} mdot_kg_s")
            temp = finite(row.get("vapor_T_K", ""), f"row {idx} vapor_T_K")
            species = (row.get("fuel_species") or "").strip()
            require(time_s >= 0.0, f"row {idx} time_s must be nonnegative")
            require(time_s > last_time, "source CSV time_s values must be strictly increasing")
            require(mdot >= 0.0, f"row {idx} mdot_kg_s must be nonnegative")
            require(temp > 0.0, f"row {idx} vapor_T_K must be positive")
            require(species in ALLOWED_SURROGATE_SPECIES, f"row {idx} fuel_species must be one of {sorted(ALLOWED_SURROGATE_SPECIES)}")
            parsed: dict[str, Any] = {
                "time_s": time_s,
                "mdot_kg_s": mdot,
                "vapor_T_K": temp,
                "fuel_species": species,
            }
            for name in OPTIONAL_COLUMNS:
                raw = (row.get(name) or "").strip()
                if raw:
                    parsed[name] = finite(raw, f"row {idx} {name}")
            if "source_radius_m" in parsed:
                require(float(parsed["source_radius_m"]) > 0.0, f"row {idx} source_radius_m must be positive")
            rows.append(parsed)
            last_time = time_s
    require(rows, "source CSV contains no data rows")
    require(len(rows) <= MAX_SCHEDULE_POINTS, f"source CSV supports at most {MAX_SCHEDULE_POINTS} schedule rows")
    for name in OPTIONAL_COLUMNS:
        present_count = sum(1 for row in rows if name in row)
        require(
            present_count in (0, len(rows)),
            f"optional source CSV column {name} must be present on every row or omitted from every row",
        )
    location_columns = ("source_x_m", "source_y_m", "source_z_m")
    location_column_count = sum(1 for name in location_columns if all(name in row for row in rows))
    require(
        location_column_count in (0, len(location_columns)),
        "source_x_m, source_y_m, and source_z_m must be provided together or omitted together",
    )
    species_set = {str(row["fuel_species"]) for row in rows}
    require(len(species_set) == 1, "one generated PeleLMeX input supports exactly one fuel_species")
    return rows


def lerp(a: float, b: float, f: float) -> float:
    return a + (b - a) * f


def interpolate(rows: list[dict[str, Any]], time_s: float) -> dict[str, Any]:
    require(time_s >= 0.0, "sample time must be nonnegative")
    if time_s <= rows[0]["time_s"]:
        return dict(rows[0])
    if time_s >= rows[-1]["time_s"]:
        return dict(rows[-1])
    for left, right in zip(rows, rows[1:]):
        if left["time_s"] <= time_s <= right["time_s"]:
            dt = right["time_s"] - left["time_s"]
            frac = 0.0 if dt == 0.0 else (time_s - left["time_s"]) / dt
            out = {"time_s": time_s, "fuel_species": left["fuel_species"]}
            for name in ("mdot_kg_s", "vapor_T_K", *OPTIONAL_COLUMNS):
                if name in left and name in right:
                    out[name] = lerp(float(left[name]), float(right[name]), frac)
            return out
    raise SourceInputError("failed to interpolate source CSV")


def update_input_text(base_text: str, replacements: dict[str, str]) -> str:
    seen: set[str] = set()
    lines: list[str] = []
    for line in base_text.splitlines():
        stripped = line.strip()
        replaced = False
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in replacements:
                lines.append(f"{key} = {replacements[key]}")
                seen.add(key)
                replaced = True
        if not replaced:
            lines.append(line)
    missing = [key for key in replacements if key not in seen]
    if missing:
        lines.append("")
        lines.append("# External vaporization surrogate source mapping.")
        for key in missing:
            lines.append(f"{key} = {replacements[key]}")
    return "\n".join(lines) + "\n"


def format_series(values: list[float]) -> str:
    return " ".join(f"{value:.12g}" for value in values)


def build_replacements(sample: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, str]:
    replacements = {
        "prob.fuel_species": str(sample["fuel_species"]),
        "prob.leak_model": "fixed_mass_flow",
        "prob.leak_rate": f"{float(sample['mdot_kg_s']):.12g}",
        "prob.leak_T": f"{float(sample['vapor_T_K']):.12g}",
        "prob.leak_schedule_count": str(len(rows)),
        "prob.leak_schedule_times": format_series([float(row["time_s"]) for row in rows]),
        "prob.leak_schedule_rates": format_series([float(row["mdot_kg_s"]) for row in rows]),
        "prob.leak_schedule_temperatures": format_series([float(row["vapor_T_K"]) for row in rows]),
    }
    schedule_optional_map = {
        "leak_vel_x_m_s": "prob.leak_schedule_vel_x",
        "leak_vel_y_m_s": "prob.leak_schedule_vel_y",
        "leak_vel_z_m_s": "prob.leak_schedule_vel_z",
        "source_radius_m": "prob.leak_schedule_radius",
        "source_x_m": "prob.leak_schedule_x",
        "source_y_m": "prob.leak_schedule_y",
        "source_z_m": "prob.leak_schedule_z",
    }
    for csv_key, input_key in schedule_optional_map.items():
        if all(csv_key in row for row in rows):
            replacements[input_key] = format_series([float(row[csv_key]) for row in rows])
    optional_map = {
        "leak_vel_x_m_s": "prob.leak_vel_x",
        "leak_vel_y_m_s": "prob.leak_vel_y",
        "leak_vel_z_m_s": "prob.leak_vel_z",
        "source_radius_m": "prob.leak_radius",
        "source_x_m": "prob.leak_xc",
        "source_y_m": "prob.leak_yc",
        "source_z_m": "prob.leak_zc",
    }
    for csv_key, input_key in optional_map.items():
        if csv_key in sample:
            replacements[input_key] = f"{float(sample[csv_key]):.12g}"
    return replacements


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-csv", required=True)
    ap.add_argument("--base-input", required=True)
    ap.add_argument("--time", type=float, required=True)
    ap.add_argument("--output-input", required=True)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    source_csv = Path(args.source_csv)
    base_input = Path(args.base_input)
    output_input = Path(args.output_input)
    output_json = Path(args.output_json)
    require(base_input.is_file(), f"missing base input: {base_input}")

    rows = read_source_csv(source_csv)
    sample = interpolate(rows, args.time)
    replacements = build_replacements(sample, rows)
    rendered = update_input_text(base_input.read_text(encoding="utf-8"), replacements)
    output_input.parent.mkdir(parents=True, exist_ok=True)
    output_input.write_text(rendered, encoding="utf-8")

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS-EXTERNAL-VAPORIZATION-SOURCE-INPUT",
        "source_csv": str(source_csv),
        "base_input": str(base_input),
        "output_input": str(output_input),
        "sample_time_s": args.time,
        "sample": sample,
        "applied_replacements": replacements,
        "source_time_series": {
            "point_count": len(rows),
            "time_s": [float(row["time_s"]) for row in rows],
            "mdot_kg_s": [float(row["mdot_kg_s"]) for row in rows],
            "vapor_T_K": [float(row["vapor_T_K"]) for row in rows],
            "leak_vel_x_m_s": [float(row["leak_vel_x_m_s"]) for row in rows if "leak_vel_x_m_s" in row],
            "leak_vel_y_m_s": [float(row["leak_vel_y_m_s"]) for row in rows if "leak_vel_y_m_s" in row],
            "leak_vel_z_m_s": [float(row["leak_vel_z_m_s"]) for row in rows if "leak_vel_z_m_s" in row],
            "source_radius_m": [float(row["source_radius_m"]) for row in rows if "source_radius_m" in row],
            "source_x_m": [float(row["source_x_m"]) for row in rows if "source_x_m" in row],
            "source_y_m": [float(row["source_y_m"]) for row in rows if "source_y_m" in row],
            "source_z_m": [float(row["source_z_m"]) for row in rows if "source_z_m" in row],
            "fuel_species": str(rows[0]["fuel_species"]),
            "emitted_to_input": True,
            "interpolation": "PeleLMeX linearly interpolates prob.leak_schedule_rates and prob.leak_schedule_temperatures at the step midpoint for fixed_mass_flow",
        },
        "limitations": {
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
            "mapping": "external vaporization/blowdown model supplies gas-phase mdot(t)/T/species",
        },
        "evidence_files": [
            {"label": "source_csv", "path": str(source_csv), "sha256": sha256_file(source_csv)},
            {"label": "base_input", "path": str(base_input), "sha256": sha256_file(base_input)},
            {"label": "output_input", "path": str(output_input), "sha256": sha256_file(output_input)},
        ],
    }
    write_json(output_json, report)
    print(f"external_vaporization_source_input PASS input={output_input} json={output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
