#!/usr/bin/env python3

import argparse
import csv
import math
import sys
from pathlib import Path


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


def check_multilevel_plotfile(path, expected_finest_level):
    header = Path(path) / "Header"
    require(header.exists(), f"plotfile header does not exist: {header}")
    lines = header.read_text().splitlines()
    require(len(lines) > 13, f"plotfile header is too short: {header}")
    ncomp = int(lines[1])
    finest_level = int(lines[4 + ncomp])
    close(finest_level, expected_finest_level, 0.0, "plotfile finest AMR level")
    require((Path(path) / f"Level_{expected_finest_level}").exists(),
            f"plotfile is missing Level_{expected_finest_level}")


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
        close(last["cloud_mass"], 0.04, 1.0e-12, "box cloud mass")
        close(last["cloud_mean_concentration"], 0.04, 1.0e-12, "box cloud mean concentration")
        close(last["cloud_x_min"], 1.5625, 1.0e-12, "box cloud x min")
        close(last["cloud_x_max"], 2.4375, 1.0e-12, "box cloud x max")
        close(last["flammable_mass"], 0.04, 1.0e-12, "box flammable mass")
        close(last["flammable_mean_concentration"], 0.04, 1.0e-12,
              "box flammable mean concentration")
        require(abs(last["balance_error"]) < 1.0e-12, "box balance error too large")
    elif case == "source_total_rate":
        close(last["source_rate"], 0.2, 1.0e-12, "source_total_rate source_rate")
        close(last["mass"], 0.08, 1.0e-12, "source_total_rate final mass")
        close(last["injected"], 0.08, 1.0e-12, "source_total_rate injected mass")
        close(last["cloud_volume"], 8.0, 1.0e-12, "source_total_rate cloud volume")
        close(last["cloud_mass"], 0.08, 1.0e-12, "source_total_rate cloud mass")
        close(last["cloud_mean_concentration"], 0.01, 1.0e-12,
              "source_total_rate cloud mean concentration")
        close(last["cloud_x_min"], 1.0625, 1.0e-12, "source_total_rate cloud x min")
        close(last["cloud_x_max"], 2.9375, 1.0e-12, "source_total_rate cloud x max")
        close(last["cloud_y_min"], 1.0625, 1.0e-12, "source_total_rate cloud y min")
        close(last["cloud_y_max"], 2.9375, 1.0e-12, "source_total_rate cloud y max")
        close(last["cloud_z_min"], 1.0625, 1.0e-12, "source_total_rate cloud z min")
        close(last["cloud_z_max"], 2.9375, 1.0e-12, "source_total_rate cloud z max")
        close(last["flammable_volume"], 8.0, 1.0e-12, "source_total_rate flammable volume")
        close(last["flammable_mass"], 0.08, 1.0e-12, "source_total_rate flammable mass")
        close(last["flammable_mean_concentration"], 0.01, 1.0e-12,
              "source_total_rate flammable mean concentration")
        require(abs(last["balance_error"]) < 1.0e-12, "source_total_rate balance error too large")
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
    elif case == "open_backflow":
        close(last["boundary_inflow_rate"], 0.0, 1.0e-14, "open_backflow boundary inflow rate")
        close(last["inflow_xhi_rate"], 0.0, 1.0e-14, "open_backflow xhi inflow rate")
        close(last["boundary_inflow"], 0.0, 1.0e-14, "open_backflow accumulated boundary inflow")
        close(last["mass"], first["mass"], 1.0e-9, "open_backflow mass conservation")
        require(last["centroid_x"] < first["centroid_x"], "open_backflow cloud did not move toward xlo")
        require(abs(last["balance_error"]) < 1.0e-9, "open_backflow balance error too large")
    elif case == "tagging":
        close(last["tag_source_volume"], 1.0, 1.0e-12, "tagging source volume")
        require(last["tag_grad_y_volume"] > 0.0, "tagging gradient volume should be positive")
        require(last["tag_refine_volume"] >= last["tag_source_volume"],
                "tagging refine volume should include source tags")
        require(last["tag_refine_volume"] >= last["tag_grad_y_volume"],
                "tagging refine volume should include gradient tags")
        require(last["tag_refine_cell_count"] > 0.0, "tagging should collate tagged cells")
        require(last["tag_cluster_count"] > 0.0, "tagging should produce candidate boxes")
        require(last["tag_candidate_level1_cell_count"] > 0.0,
                "tagging should produce candidate level-1 cells")
        require(last["tag_candidate_level1_volume"] >= last["tag_refine_volume"],
                "candidate level-1 volume should cover refine tags")
        close(last["amr_restrict_max_abs_y_error"], 0.0, 1.0e-14,
              "tagging AMR restriction max Y error")
        close(last["amr_restrict_l1_y_error"], 0.0, 1.0e-14,
              "tagging AMR restriction L1 Y error")
        require(last["amr_restrict_coarse_cell_count"] > 0.0,
                "tagging AMR restriction should cover coarse cells")
        check_multilevel_plotfile("plt_verify_tagging_00000", 1)
    elif case == "level1_advance":
        require(len(rows) == 2, "level1_advance should write initial and step-1 rows")
        close(first["amr_restrict_max_abs_y_error"], 0.0, 1.0e-14,
              "initial level1 restriction max Y error")
        require(last["amr_restrict_max_abs_y_error"] > 1.0e-8,
                "advanced level1 state should diverge measurably from coarse restriction")
        require(last["amr_restrict_l1_y_error"] > 1.0e-10,
                "advanced level1 state should have nonzero L1 restriction error")
        require(last["amr_restrict_coarse_cell_count"] > 0.0,
                "level1 restriction should cover coarse cells")
        require(abs(last["amr_mass_delta"]) > 1.0e-10,
                "advanced level1 state should report a nonzero AMR mass delta")
        close(last["amr_applied_restriction_mass_delta"], 0.0, 1.0e-14,
              "level1_advance should not apply restriction mass correction")
        close(last["amr_sync_corrected_balance_error"], last["balance_error"],
              1.0e-14, "level1_advance corrected balance should match raw balance")
        check_multilevel_plotfile("plt_verify_level1_advance_00001", 1)
    elif case == "level1_restriction_update":
        require(len(rows) == 2,
                "level1_restriction_update should write initial and step-1 rows")
        close(first["amr_restrict_max_abs_y_error"], 0.0, 1.0e-14,
              "initial restriction-update max Y error")
        close(last["amr_restrict_max_abs_y_error"], 0.0, 1.0e-14,
              "restriction-updated max Y error")
        close(last["amr_restrict_l1_y_error"], 0.0, 1.0e-14,
              "restriction-updated L1 Y error")
        require(last["amr_restrict_coarse_cell_count"] > 0.0,
                "restriction update should cover coarse cells")
        close(last["amr_mass_delta"], 0.0, 1.0e-14,
              "restriction update should remove current AMR mass delta")
        require(abs(last["amr_applied_restriction_mass_delta"]) > 1.0e-10,
                "restriction update should report an applied mass correction")
        close(last["amr_applied_restriction_mass_delta"], last["balance_error"],
              1.0e-12, "restriction mass correction should match balance drift")
        close(last["amr_sync_corrected_balance_error"], 0.0, 1.0e-12,
              "restriction sync-corrected balance should close")
        check_multilevel_plotfile("plt_verify_level1_restriction_update_00001", 1)
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
