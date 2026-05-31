#!/usr/bin/env python3

import argparse
import csv
import math
import sys


def read_rows(path):
    with open(path, newline="") as f:
        return [{k: float(v) if k != "step" else int(v) for k, v in row.items()}
                for row in csv.DictReader(f)]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def close(value, expected, tol, name):
    require(abs(value - expected) <= tol,
            f"{name}: got {value:.17g}, expected {expected:.17g} +/- {tol:.3g}")


def outlet_face_rate_sum(row):
    return (row["outlet_xlo_rate"] + row["outlet_xhi_rate"]
            + row["outlet_ylo_rate"] + row["outlet_yhi_rate"]
            + row["outlet_zlo_rate"] + row["outlet_zhi_rate"])


def inflow_face_rate_sum(row):
    return (row["inflow_xlo_rate"] + row["inflow_xhi_rate"]
            + row["inflow_ylo_rate"] + row["inflow_yhi_rate"]
            + row["inflow_zlo_rate"] + row["inflow_zhi_rate"])


def check_outlet_rate_decomposition(row, tol=1.0e-12):
    close(outlet_face_rate_sum(row), row["outlet_rate"], tol,
          "sum of face outlet rates")


def check_inflow_rate_decomposition(row, tol=1.0e-12):
    close(inflow_face_rate_sum(row), row["boundary_inflow_rate"], tol,
          "sum of face boundary inflow rates")


def check_case(case, rows):
    require(rows, "history file is empty")
    first = rows[0]
    last = rows[-1]
    check_outlet_rate_decomposition(last)
    check_inflow_rate_decomposition(last)

    if case == "leak":
        close(last["mass"], 0.038577307826430318, 1.0e-9, "leak final mass")
        close(last["injected"], 0.038577308315055667, 1.0e-9, "leak injected")
        require(abs(last["balance_error"]) < 1.0e-8, "leak mass balance drift too large")
        require(last["cloud_volume"] > 0.9, "leak cloud volume did not grow")
        require(last["flammable_volume"] > 0.15, "leak flammable volume too small")
    elif case == "advection":
        close(last["mass"], first["mass"], 1.0e-9, "advection mass conservation")
        close(last["centroid_x"], 2.8, 1.0e-6, "advection centroid_x")
        close(last["centroid_y"], 2.0, 1.0e-12, "advection centroid_y")
        close(last["centroid_z"], 2.0, 1.0e-12, "advection centroid_z")
        require(abs(last["balance_error"]) < 1.0e-9, "advection balance error too large")
    elif case == "diffusion":
        close(last["mass"], first["mass"], 1.0e-9, "diffusion mass conservation")
        close(last["centroid_x"], 4.0, 1.0e-12, "diffusion centroid_x")
        close(last["centroid_y"], 2.0, 1.0e-12, "diffusion centroid_y")
        close(last["centroid_z"], 2.0, 1.0e-12, "diffusion centroid_z")
        require(last["max_Y"] < first["max_Y"], "diffusion max_Y did not decay")
    elif case == "wall":
        close(last["mass"], first["mass"], 1.0e-9, "wall mass conservation")
        close(last["outlet"], 0.0, 1.0e-14, "wall outlet mass")
        close(last["outlet_zlo_rate"], 0.0, 1.0e-14, "wall zlo outlet rate")
        require(last["centroid_z"] < first["centroid_z"], "wall cloud did not move toward zlo")
        require(abs(last["balance_error"]) < 1.0e-12, "wall balance error too large")
    elif case == "box":
        close(last["source_rate"], 0.1, 1.0e-12, "box source_rate")
        close(last["mass"], 0.04, 1.0e-12, "box final mass")
        close(last["injected"], 0.04, 1.0e-12, "box injected mass")
        close(last["cloud_volume"], 1.0, 1.0e-12, "box cloud volume")
        require(abs(last["balance_error"]) < 1.0e-12, "box balance error too large")
    elif case == "auto_dt":
        close(last["time"], 0.4, 1.0e-12, "auto_dt stop time")
        close(last["centroid_x"], 2.4, 1.0e-6, "auto_dt centroid_x")
        require(len(rows) == 8, "auto_dt should have initial row plus seven output steps")
    elif case == "volume_fraction":
        close(last["mass"], 0.04, 1.0e-12, "volume_fraction final mass")
        expected_x = (0.04 / 16.04) / ((0.04 / 16.04) + (0.96 / 28.97))
        close(last["max_concentration"], expected_x, 1.0e-12, "volume_fraction max concentration")
        close(last["cloud_volume"], 1.0, 1.0e-12, "volume_fraction cloud volume")
        close(last["flammable_volume"], 1.0, 1.0e-12, "volume_fraction flammable volume")
    elif case == "boundary_faces":
        require(last["outlet_yhi_rate"] > 0.0, "boundary_faces yhi outlet rate should be positive")
        close(last["outlet_xlo_rate"], 0.0, 1.0e-14, "boundary_faces xlo outlet rate")
        close(last["outlet_xhi_rate"], 0.0, 1.0e-14, "boundary_faces xhi outlet rate")
        close(last["outlet_ylo_rate"], 0.0, 1.0e-14, "boundary_faces ylo outlet rate")
        close(last["outlet_zlo_rate"], 0.0, 1.0e-14, "boundary_faces zlo outlet rate")
        close(last["outlet_zhi_rate"], 0.0, 1.0e-14, "boundary_faces zhi outlet rate")
        close(last["outlet_rate"], last["outlet_yhi_rate"], 1.0e-14, "boundary_faces total outlet rate")
        require(last["mass"] < first["mass"], "boundary_faces mass should leave through yhi")
        require(abs(last["balance_error"]) < 1.0e-9, "boundary_faces balance error too large")
    elif case == "inlet_scalar":
        close(last["boundary_inflow_rate"], 1.6, 1.0e-12, "inlet_scalar boundary inflow rate")
        close(last["inflow_xlo_rate"], 1.6, 1.0e-12, "inlet_scalar xlo inflow rate")
        close(last["boundary_inflow"], 0.64, 1.0e-12, "inlet_scalar accumulated boundary inflow")
        close(last["mass"], 0.64, 1.0e-12, "inlet_scalar final mass")
        close(last["outlet"], 0.0, 1.0e-14, "inlet_scalar outlet mass")
        require(abs(last["balance_error"]) < 1.0e-12, "inlet_scalar balance error too large")
    else:
        raise AssertionError(f"unknown case {case}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--history", required=True)
    args = parser.parse_args()

    rows = read_rows(args.history)
    check_case(args.case, rows)
    print(f"PASS {args.case}: {args.history}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
