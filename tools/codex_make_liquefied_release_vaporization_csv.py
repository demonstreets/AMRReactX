#!/usr/bin/env python3
"""Create a screening liquefied-release vaporization CSV for the gas-source bridge."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FLUIDS: dict[str, dict[str, float | str]] = {
    "LNG_CH4": {
        "fuel_species": "CH4",
        "liquid_density_kg_m3": 420.0,
        "boiling_T_K": 111.7,
        "liquid_cp_J_kg_K": 3500.0,
        "latent_heat_J_kg": 510000.0,
        "vapor_T_K": 285.0,
        "gas_constant_J_kg_K": 518.3,
        "default_pool_vapor_fraction": 0.05,
    },
    "LPG_C3H8": {
        "fuel_species": "C3H8",
        "liquid_density_kg_m3": 493.0,
        "boiling_T_K": 231.0,
        "liquid_cp_J_kg_K": 2400.0,
        "latent_heat_J_kg": 356000.0,
        "vapor_T_K": 300.0,
        "gas_constant_J_kg_K": 188.6,
        "default_pool_vapor_fraction": 0.08,
    },
}

CSV_COLUMNS = (
    "time_s",
    "mdot_kg_s",
    "vapor_T_K",
    "fuel_species",
    "leak_vel_x_m_s",
    "leak_vel_y_m_s",
    "leak_vel_z_m_s",
    "source_radius_m",
    "source_x_m",
    "source_y_m",
    "source_z_m",
    "source_pressure_Pa",
)


class LiquefiedReleaseError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LiquefiedReleaseError(message)


def positive(value: float, label: str) -> float:
    require(math.isfinite(value) and value > 0.0, f"{label} must be positive and finite")
    return value


def nonnegative(value: float, label: str) -> float:
    require(math.isfinite(value) and value >= 0.0, f"{label} must be nonnegative and finite")
    return value


def finite_value(value: float, label: str) -> float:
    require(math.isfinite(value), f"{label} must be finite")
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize(x: float, y: float, z: float) -> tuple[float, float, float]:
    mag = math.sqrt(x * x + y * y + z * z)
    require(mag > 0.0, "jet direction vector must be nonzero")
    return x / mag, y / mag, z / mag


def auto_vaporized_fraction(props: dict[str, float | str], liquid_T_K: float, pool_fraction: float | None) -> float:
    sensible = max(0.0, liquid_T_K - float(props["boiling_T_K"]))
    flash = sensible * float(props["liquid_cp_J_kg_K"]) / float(props["latent_heat_J_kg"])
    pool = float(props["default_pool_vapor_fraction"]) if pool_fraction is None else pool_fraction
    return clamp(flash + pool, 1.0e-4, 0.95)


def pressure_from_inventory(
    remaining_kg: float,
    initial_inventory_kg: float,
    initial_pressure_Pa: float,
    ambient_pressure_Pa: float,
    pressure_decay_exponent: float,
) -> float:
    if remaining_kg <= 0.0:
        return ambient_pressure_Pa
    frac = clamp(remaining_kg / initial_inventory_kg, 0.0, 1.0)
    return ambient_pressure_Pa + (initial_pressure_Pa - ambient_pressure_Pa) * frac**pressure_decay_exponent


def liquid_mdot(
    pressure_Pa: float,
    ambient_pressure_Pa: float,
    liquid_density_kg_m3: float,
    hole_diameter_m: float,
    discharge_coeff: float,
) -> float:
    dp = max(pressure_Pa - ambient_pressure_Pa, 0.0)
    if dp <= 0.0:
        return 0.0
    area = math.pi * (0.5 * hole_diameter_m) ** 2
    return discharge_coeff * area * math.sqrt(2.0 * liquid_density_kg_m3 * dp)


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    props = FLUIDS[args.fluid]
    initial_inventory = positive(args.inventory_kg, "inventory_kg")
    initial_pressure = positive(args.initial_pressure_Pa, "initial_pressure_Pa")
    ambient_pressure = positive(args.ambient_pressure_Pa, "ambient_pressure_Pa")
    require(initial_pressure >= ambient_pressure, "initial pressure must be at least ambient pressure")
    hole_diameter = positive(args.hole_diameter_m, "hole_diameter_m")
    duration = positive(args.duration_s, "duration_s")
    points = int(args.points)
    require(2 <= points <= 64, "points must be in [2, 64]")
    discharge_coeff = positive(args.discharge_coeff, "discharge_coeff")
    require(discharge_coeff <= 1.0, "discharge_coeff must be <= 1")
    source_radius = positive(args.source_radius_m, "source_radius_m")
    pressure_decay_exponent = positive(args.pressure_decay_exponent, "pressure_decay_exponent")
    liquid_T = positive(args.liquid_T_K, "liquid_T_K")
    vapor_T = positive(args.vapor_T_K or float(props["vapor_T_K"]), "vapor_T_K")
    max_jet_speed = positive(args.max_jet_speed_m_s, "max_jet_speed_m_s")
    if args.pool_vapor_fraction is None:
        pool_fraction = None
    else:
        pool_fraction = nonnegative(args.pool_vapor_fraction, "pool_vapor_fraction")
        require(pool_fraction <= 0.95, "pool_vapor_fraction must be <= 0.95")
    if args.vaporized_fraction is None:
        vapor_fraction = auto_vaporized_fraction(props, liquid_T, pool_fraction)
    else:
        vapor_fraction = nonnegative(args.vaporized_fraction, "vaporized_fraction")
        require(vapor_fraction <= 0.95, "vaporized_fraction must be <= 0.95")
    source_x = finite_value(args.source_x_m, "source_x_m")
    source_y = finite_value(args.source_y_m, "source_y_m")
    source_z = finite_value(args.source_z_m, "source_z_m")
    direction = normalize(args.jet_dir_x, args.jet_dir_y, args.jet_dir_z)
    times = [duration * i / (points - 1) for i in range(points)]
    remaining = initial_inventory
    rows: list[dict[str, Any]] = []
    liquid_rates: list[float] = []
    gas_rates: list[float] = []
    pressures: list[float] = []

    for i, t in enumerate(times):
        pressure = pressure_from_inventory(
            remaining,
            initial_inventory,
            initial_pressure,
            ambient_pressure,
            pressure_decay_exponent,
        )
        mliq = liquid_mdot(
            pressure,
            ambient_pressure,
            float(props["liquid_density_kg_m3"]),
            hole_diameter,
            discharge_coeff,
        )
        if i < len(times) - 1:
            dt_next = times[i + 1] - t
            mliq = min(mliq, remaining / dt_next if dt_next > 0.0 else 0.0)
        else:
            mliq = 0.0 if remaining <= 0.0 else mliq
        mgas = mliq * vapor_fraction
        vapor_density = ambient_pressure / (float(props["gas_constant_J_kg_K"]) * vapor_T)
        jet_area = math.pi * source_radius**2
        speed = 0.0 if mgas <= 0.0 else mgas / max(vapor_density * jet_area, 1.0e-30)
        speed = min(speed, max_jet_speed)
        row = {
            "time_s": t,
            "mdot_kg_s": mgas,
            "vapor_T_K": vapor_T,
            "fuel_species": str(props["fuel_species"]),
            "leak_vel_x_m_s": speed * direction[0],
            "leak_vel_y_m_s": speed * direction[1],
            "leak_vel_z_m_s": speed * direction[2],
            "source_radius_m": source_radius,
            "source_x_m": source_x,
            "source_y_m": source_y,
            "source_z_m": source_z,
            "source_pressure_Pa": ambient_pressure,
        }
        rows.append(row)
        liquid_rates.append(mliq)
        gas_rates.append(mgas)
        pressures.append(pressure)
        if i < len(times) - 1:
            remaining = max(0.0, remaining - mliq * (times[i + 1] - t))

    summary = {
        "fluid": args.fluid,
        "fuel_species": str(props["fuel_species"]),
        "screening_model": "orifice_liquid_discharge_inventory_decay_plus_vaporized_fraction",
        "initial_inventory_kg": initial_inventory,
        "remaining_inventory_kg": remaining,
        "inventory_depleted": remaining <= 1.0e-9,
        "initial_pressure_Pa": initial_pressure,
        "ambient_pressure_Pa": ambient_pressure,
        "hole_diameter_m": hole_diameter,
        "discharge_coeff": discharge_coeff,
        "liquid_T_K": liquid_T,
        "vapor_T_K": vapor_T,
        "vaporized_fraction_to_gas_source": vapor_fraction,
        "time_point_count": len(times),
        "time_start_s": times[0],
        "time_end_s": times[-1],
        "liquid_mdot_max_kg_s": max(liquid_rates),
        "gas_mdot_max_kg_s": max(gas_rates),
        "gas_mdot_positive": max(gas_rates) > 0.0,
        "gas_mdot_decays": gas_rates[-1] < max(gas_rates),
        "pressure_decays": pressures[-1] <= pressures[0],
        "cfd_solves_liquid_phase_change": False,
        "cfd_solves_flashing_discharge": False,
        "cfd_solves_pool_spread_evaporation": False,
        "model_is_screening_source_generator": True,
    }
    return rows, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (f"{value:.12g}" if isinstance(value, float) else value)
                    for key, value in row.items()
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fluid", choices=sorted(FLUIDS), required=True)
    parser.add_argument("--inventory-kg", type=float, required=True)
    parser.add_argument("--initial-pressure-Pa", type=float, required=True)
    parser.add_argument("--ambient-pressure-Pa", type=float, default=101325.0)
    parser.add_argument("--hole-diameter-m", type=float, required=True)
    parser.add_argument("--duration-s", type=float, required=True)
    parser.add_argument("--points", type=int, default=9)
    parser.add_argument("--discharge-coeff", type=float, default=0.62)
    parser.add_argument("--pressure-decay-exponent", type=float, default=1.0)
    parser.add_argument("--liquid-T-K", type=float, required=True)
    parser.add_argument("--vapor-T-K", type=float)
    parser.add_argument("--vaporized-fraction", type=float)
    parser.add_argument("--pool-vapor-fraction", type=float)
    parser.add_argument("--source-radius-m", type=float, default=0.08)
    parser.add_argument("--source-x-m", type=float, default=0.55)
    parser.add_argument("--source-y-m", type=float, default=0.50)
    parser.add_argument("--source-z-m", type=float, default=0.50)
    parser.add_argument("--jet-dir-x", type=float, default=1.0)
    parser.add_argument("--jet-dir-y", type=float, default=0.0)
    parser.add_argument("--jet-dir-z", type=float, default=0.0)
    parser.add_argument("--max-jet-speed-m-s", type=float, default=200.0)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args(argv)

    try:
        rows, summary = build_rows(args)
        output_csv = Path(args.output_csv)
        output_json = Path(args.output_json)
        write_csv(output_csv, rows)
        report = {
            "schema_version": 1,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "PASS-LIQUEFIED-RELEASE-VAPORIZATION-CSV",
            "summary": summary,
            "output_csv": str(output_csv),
            "evidence_files": [
                {
                    "label": "liquefied_release_vaporization_csv",
                    "path": str(output_csv),
                    "sha256": sha256_file(output_csv),
                    "size_bytes": output_csv.stat().st_size,
                }
            ],
            "limitations": [
                "This tool produces a screening gas-source schedule for PeleLMeX.",
                "It does not solve internal tank rupture mechanics, flashing multiphase discharge, liquid-pool spread, or ground heat transfer.",
                "Use measured, process-safety, or higher-fidelity external-source data when available.",
            ],
        }
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"liquefied_release_vaporization_csv PASS csv={output_csv} json={output_json}")
        return 0
    except LiquefiedReleaseError as exc:
        print(f"liquefied_release_vaporization_csv FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
