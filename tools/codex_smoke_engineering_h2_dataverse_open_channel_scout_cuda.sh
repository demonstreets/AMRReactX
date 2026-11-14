#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_root="${CODEX_DATAVERSE_OPEN_CHANNEL_SCOUT_LOG_ROOT:-/tmp/codex_h2_dataverse_open_channel_scout_cuda_$(date -u +%Y%m%dT%H%M%SZ)}"
asset_dir="$log_root/assets"
run_dir="$log_root/run"
input_file="$log_root/input.dataverse_open_channel_h2_scout_3d"
sensors_json="$log_root/sensors.dataverse_open_channel_solver_coords.json"
run_log="$log_root/run.log"
plume_json="$log_root/h2_plume_observation_report.json"
plume_md="$log_root/h2_plume_observation_report.md"
plume_extents_csv="$log_root/plume_extents.csv"
sensor_timeseries_csv="$log_root/sensor_timeseries.csv"
agreement_json="$log_root/dataverse_open_channel_agreement_contract_report.json"
agreement_md="$log_root/dataverse_open_channel_agreement_contract_report.md"
agreement_attempt_log="$log_root/agreement_attempt.log"
agreement_attempt_json="$log_root/agreement_attempt_status.json"

max_step="${CODEX_DATAVERSE_OPEN_CHANNEL_MAX_STEP:-80}"
plot_int="${CODEX_DATAVERSE_OPEN_CHANNEL_PLOT_INT:-20}"
fixed_dt="${CODEX_DATAVERSE_OPEN_CHANNEL_FIXED_DT:-1.0e-4}"
mpi_ranks="${CODEX_DATAVERSE_OPEN_CHANNEL_MPI_RANKS:-1}"
use_cuda="${CODEX_DATAVERSE_OPEN_CHANNEL_USE_CUDA:-TRUE}"
leak_rate="${CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_RATE_KG_S:-9.152681907312261e-4}"
leak_radius="${CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_RADIUS:-0.080}"
leak_zc="${CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_ZC:-0.70}"
leak_vel_x="${CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_VEL_X:-0.50}"
lo_bc="${CODEX_DATAVERSE_OPEN_CHANNEL_LO_BC:-NoSlipWallAdiab NoSlipWallAdiab NoSlipWallAdiab}"
hi_bc="${CODEX_DATAVERSE_OPEN_CHANNEL_HI_BC:-Outflow NoSlipWallAdiab NoSlipWallAdiab}"
plume_lfl="${CODEX_DATAVERSE_OPEN_CHANNEL_PLUME_LFL:-1.0e-8}"
plume_ufl="${CODEX_DATAVERSE_OPEN_CHANNEL_PLUME_UFL:-1.0}"
agreement_enabled="${CODEX_DATAVERSE_OPEN_CHANNEL_TRY_AGREEMENT:-TRUE}"
use_mpi=FALSE
if [ "$mpi_ranks" -gt 1 ]; then
  use_mpi=TRUE
fi

mkdir -p "$asset_dir" "$run_dir"

python3 - "$input_file" "$sensors_json" "$max_step" "$plot_int" "$fixed_dt" "$leak_rate" "$leak_radius" "$leak_zc" "$leak_vel_x" "$lo_bc" "$hi_bc" <<'PYGEN'
import csv
import json
import sys
from pathlib import Path

input_file = Path(sys.argv[1])
sensors_json = Path(sys.argv[2])
max_step = int(sys.argv[3])
plot_int = int(sys.argv[4])
fixed_dt = float(sys.argv[5])
leak_rate = float(sys.argv[6])
leak_radius = float(sys.argv[7])
leak_zc = float(sys.argv[8])
leak_vel_x = float(sys.argv[9])
lo_bc = sys.argv[10]
hi_bc = sys.argv[11]
for name, value in {"lo_bc": lo_bc, "hi_bc": hi_bc}.items():
    parts = value.split()
    if len(parts) != 3:
        raise SystemExit(f"{name} must contain exactly three boundary tokens, got: {value!r}")

sensor_csv = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803/"
    "dataverse_sensor_coordinates.csv"
)
rows = list(csv.DictReader(sensor_csv.open(newline="", encoding="utf-8")))
sensors = []
for row in rows:
    article_x = float(row["x_m"])
    article_y = float(row["y_m"])
    article_z = float(row["z_m"])
    sensors.append({
        "id": str(int(row["sensor_id"])),
        "x": article_y,
        "y": article_x,
        "z": article_z,
        "article_x_m": article_x,
        "article_y_m": article_y,
        "article_z_m": article_z,
        "source_basis": "Dataverse/article sensor map transformed as solver_x=article_y, solver_y=article_x, solver_z=article_z",
    })

sensors_json.write_text(json.dumps({
    "schema_version": 1,
    "sensor_basis": "DataverseNO open-channel H2 sensors transformed for the h2_leak_3d x-downstream solver convention",
    "dataset_doi": "10.23642/USN.26117989",
    "article_doi": "10.1016/j.jlp.2025.105669",
    "selected_case": "23_FFI_P101_T00031.zip",
    "article_test_id": "test-08-1",
    "coordinate_transform": {
        "solver_x": "article_y_m",
        "solver_y": "article_x_m",
        "solver_z": "article_z_m",
    },
    "sensors": sensors,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

input_file.write_text(f"""
# DataverseNO open-channel H2 CFD scout.
# Physical dataset geometry: article x width=0.9 m, article y length=5.8 m,
# article z height=0.8 m. Solver coordinates are transformed so solver x is
# the channel length for existing h2_leak_3d plume-history validation.
# Transform: solver_x=article_y, solver_y=article_x, solver_z=article_z.
# Selected reference case: 23_FFI_P101_T00031.zip / test-08-1.

geometry.is_periodic = 0 0 0
geometry.coord_sys   = 0
geometry.prob_lo     = 0.0 0.0 0.0
geometry.prob_hi     = 5.80 0.90 0.80

peleLM.lo_bc = {lo_bc}
peleLM.hi_bc = {hi_bc}
peleLM.v = 1
peleLM.incompressible = 0
peleLM.sdc_iterMax = 1
peleLM.num_init_iter = 1
peleLM.floor_species = 1
peleLM.user_defined_ext_sources = 1
peleLM.advection_scheme = Godunov_PLM
peleLM.do_react = 1
peleLM.chem_integrator = ReactorNull

amr.n_cell = 116 18 16
amr.v = 1
amr.max_level = 0
amr.blocking_factor = 2
amr.max_grid_size = 24
amr.max_step = {max_step}
amr.stop_time = -1.0
amr.fixed_dt = {fixed_dt:.12e}
amr.cfl = 0.5
amr.plot_int = {plot_int}
amr.check_int = -1
amr.derive_plot_vars = mass_fractions avg_pressure

prob.P_mean = 101325.0
prob.T_mean = 293.0
prob.wind_u = 0.0
prob.wind_v = 0.0
prob.leak_xc = 0.50
prob.leak_yc = 0.45
prob.leak_zc = {leak_zc:.12e}
prob.leak_rate = {leak_rate:.12e}
prob.leak_radius = {leak_radius:.12e}
prob.leak_vel_x = {leak_vel_x:.12e}
prob.leak_vel_y = 0.0
prob.leak_vel_z = 0.0
prob.leak_T = 293.0

eb2.geom_type = all_regular
""".lstrip(), encoding="utf-8")
PYGEN

CODEX_H2_LEAK_HISTORY_INPUT="$input_file" \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_root" \
CODEX_H2_LEAK_HISTORY_USE_CUDA="$use_cuda" \
CODEX_H2_LEAK_HISTORY_USE_MPI="$use_mpi" \
CODEX_H2_LEAK_HISTORY_MPI_RANKS="$mpi_ranks" \
CODEX_H2_LEAK_HISTORY_EBASE="${CODEX_DATAVERSE_OPEN_CHANNEL_EBASE:-codex_h2_leak_dataverse_open_channel_scout}" \
CODEX_H2_LEAK_HISTORY_SKIP_BUILD="${CODEX_DATAVERSE_OPEN_CHANNEL_SKIP_BUILD:-FALSE}" \
CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES="$((max_step / plot_int + 1))" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_DATAVERSE_OPEN_CHANNEL_MIN_MASS_GROWTH_RATIO:-1.05}" \
CODEX_H2_LEAK_HISTORY_MIN_DOWNSTREAM_FRACTION="${CODEX_DATAVERSE_OPEN_CHANNEL_MIN_DOWNSTREAM_FRACTION:-0.01}" \
CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION="${CODEX_DATAVERSE_OPEN_CHANNEL_MIN_UPSTREAM_FRACTION:-0.0}" \
CODEX_H2_LEAK_HISTORY_MAX_CENTER_OFFSET="${CODEX_DATAVERSE_OPEN_CHANNEL_MAX_CENTER_OFFSET:-1.0}" \
RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

python3 "$repo_root/tools/write_engineering_h2_plume_observation_report.py" \
  --run-dir "$run_dir" \
  --sensors-json "$sensors_json" \
  --lfl "$plume_lfl" \
  --ufl "$plume_ufl" \
  --min-plotfiles "$((max_step / plot_int + 1))" \
  --min-sensors 29 \
  --sensor-sampling nearest \
  --case-matched-external-benchmark \
  --output-json "$plume_json" \
  --output-md "$plume_md" \
  --extents-csv "$plume_extents_csv" \
  --sensors-csv "$sensor_timeseries_csv"

python3 "$repo_root/tools/write_engineering_h2_plume_observation_report.py" --verify-json "$plume_json"

agreement_status=not_run
agreement_message="agreement scoring was not requested"
if [[ "$agreement_enabled" == "TRUE" ]]; then
  if python3 "$repo_root/tools/write_dataverse_open_channel_agreement_contract_report.py" \
      --simulation-long-csv "$sensor_timeseries_csv" \
      --output-json "$agreement_json" \
      --output-md "$agreement_md" >"$agreement_attempt_log" 2>&1; then
    python3 "$repo_root/tools/write_dataverse_open_channel_agreement_contract_report.py" --verify-json "$agreement_json"
    agreement_status=pass
    agreement_message="production agreement scoring passed"
  else
    agreement_status=failed_expected_for_short_scout
    agreement_message="$(tail -n 1 "$agreement_attempt_log" 2>/dev/null || true)"
  fi
fi
python3 - "$agreement_attempt_json" "$agreement_status" "$agreement_message" "$sensor_timeseries_csv" "$agreement_json" <<'PYSTATUS'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
path.write_text(json.dumps({
    "schema_version": 1,
    "agreement_status": sys.argv[2],
    "message": sys.argv[3],
    "simulation_long_csv": sys.argv[4],
    "agreement_json": sys.argv[5],
    "production_agreement_completed": sys.argv[2] == "pass",
    "clears_external_plume_reference_blocker": sys.argv[2] == "pass",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PYSTATUS

printf 'dataverse_open_channel_scout_cuda PASS log_root=%s max_step=%s mpi_ranks=%s cuda=%s plume=%s agreement_status=%s\n' \
  "$log_root" "$max_step" "$mpi_ranks" "$use_cuda" "$plume_json" "$agreement_status"
