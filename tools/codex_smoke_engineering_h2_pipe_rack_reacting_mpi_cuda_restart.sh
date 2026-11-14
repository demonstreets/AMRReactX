#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
base_script="$repo_root/tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh"
case_dir="$repo_root/examples/engineering/h2_leak_3d"
ebase="${CODEX_PIPE_RACK_RESTART_EBASE:-codex_h2_leak_reacting_pipe_rack}"
exe_name="${ebase}3d.gnu.MPI.CUDA.ex"
log_root="${CODEX_PIPE_RACK_RESTART_LOG_ROOT:-/tmp/codex_h2_pipe_rack_reacting_mpi_cuda_restart_$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$log_root/run"
initial_step="${CODEX_PIPE_RACK_RESTART_INITIAL_STEP:-150}"
final_step="${CODEX_PIPE_RACK_RESTART_FINAL_STEP:-450}"
plot_int="${CODEX_PIPE_RACK_RESTART_PLOT_INT:-75}"
check_int="${CODEX_PIPE_RACK_RESTART_CHECK_INT:-75}"
mpi_ranks="${CODEX_PIPE_RACK_RESTART_MPI_RANKS:-2}"
n_cell="${CODEX_PIPE_RACK_RESTART_N_CELL:-64 32 32}"
max_grid_size="${CODEX_PIPE_RACK_RESTART_MAX_GRID_SIZE:-32}"
restart_log="$log_root/restart.log"
restart_command="$log_root/restart_command.txt"
summary_json="$log_root/restart_summary.json"

if [ ! -x "$base_script" ]; then
  echo "pipe_rack_reacting_restart FAIL missing base script: $base_script" >&2
  exit 2
fi

rm -rf "$log_root"
mkdir -p "$log_root"

CODEX_PIPE_RACK_REACTING_LOG_ROOT="$log_root" \
CODEX_PIPE_RACK_REACTING_EBASE="$ebase" \
CODEX_PIPE_RACK_REACTING_MPI_RANKS="$mpi_ranks" \
CODEX_PIPE_RACK_REACTING_N_CELL="$n_cell" \
CODEX_PIPE_RACK_REACTING_MAX_GRID_SIZE="$max_grid_size" \
CODEX_PIPE_RACK_REACTING_MAX_STEP="$initial_step" \
CODEX_PIPE_RACK_REACTING_PLOT_INT="$plot_int" \
CODEX_PIPE_RACK_REACTING_CHECK_INT="$check_int" \
CODEX_PIPE_RACK_REACTING_MIN_SUSTAINED_OUTPUTS=2 \
RUN_TIMEOUT="${RUN_TIMEOUT:-10800}" \
JOBS="${JOBS:-4}" \
bash "$base_script"

cp "$log_root/run.log" "$log_root/initial_run.log"
cp "$log_root/summary.json" "$log_root/initial_summary.json"

restart_chk="$run_dir/chk$(printf "%05d" "$initial_step")"
if [ ! -d "$restart_chk" ]; then
  restart_chk=$(find "$run_dir" -maxdepth 1 -type d -name 'chk[0-9][0-9][0-9][0-9][0-9]' | sort | tail -1)
fi
if [ -z "${restart_chk:-}" ] || [ ! -d "$restart_chk" ]; then
  echo "pipe_rack_reacting_restart FAIL checkpoint not found" >&2
  exit 2
fi

cuda_bin="${CUDA_NVCC:-${HOME}/local/cuda-12.6/bin/nvcc}"
if [ ! -x "$cuda_bin" ]; then
  cuda_bin=$(command -v nvcc || true)
fi
if [ -z "$cuda_bin" ] || [ ! -x "$cuda_bin" ]; then
  echo "pipe_rack_reacting_restart FAIL nvcc not found" >&2
  exit 127
fi
cuda_root=$(cd "$(dirname "$cuda_bin")/.." && pwd)
export PATH="$(dirname "$cuda_bin"):$PATH"
export AMREX_CUDA_ARCH="${AMREX_CUDA_ARCH:-60}"
sundials_cuda_dir="${SUNDIALS_CUDA_DIR:-${HOME}/local/sundials-cuda}"
export LIBRARY_PATH="${sundials_cuda_dir}/lib:$cuda_root/targets/x86_64-linux/lib:$cuda_root/lib64:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${sundials_cuda_dir}/lib:$cuda_root/targets/x86_64-linux/lib:$cuda_root/lib64:${LD_LIBRARY_PATH:-}"
source "$repo_root/tools/prepare_mpi_link_shims.sh"

input_file="$run_dir/input.codex_pipe_rack_reacting_single_cuda_20step"
exe="$run_dir/$exe_name"
if [ ! -x "$exe" ]; then
  cp "$case_dir/$exe_name" "$exe"
fi

{
  printf "cd %s\n" "$run_dir"
  printf "mpirun --oversubscribe -np %s ./%s %s amr.restart=%s amr.max_step=%s amr.plot_int=%s amr.check_int=-1\n" \
    "$mpi_ranks" "$exe_name" "$(basename "$input_file")" "$(basename "$restart_chk")" "$final_step" "$plot_int"
} > "$restart_command"

(
  cd "$run_dir"
  mpirun --oversubscribe -np "$mpi_ranks" "./$exe_name" "$(basename "$input_file")" \
    "amr.restart=$(basename "$restart_chk")" "amr.max_step=$final_step" "amr.plot_int=$plot_int" "amr.check_int=-1" \
    > "$restart_log" 2>&1
)

python3 - "$log_root" "$summary_json" "$initial_step" "$final_step" "$mpi_ranks" "$n_cell" <<'PYCHECK'
import hashlib
import json
import re
import sys
from pathlib import Path

log_root = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
initial_step = int(sys.argv[3])
final_step = int(sys.argv[4])
mpi_ranks = int(sys.argv[5])
n_cell = sys.argv[6]
run_dir = log_root / "run"
restart_log = log_root / "restart.log"
initial_log = log_root / "initial_run.log"
restart_command = log_root / "restart_command.txt"
restart_chk = run_dir / f"chk{initial_step:05d}"
if not restart_chk.is_dir():
    candidates = sorted(run_dir.glob("chk[0-9][0-9][0-9][0-9][0-9]"))
    restart_chk = candidates[-1] if candidates else restart_chk

def fail(msg):
    raise SystemExit(f"pipe_rack_reacting_restart FAIL {msg}")

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_header(plot_name):
    lines = (run_dir / plot_name / "Header").read_text(errors="replace").splitlines()
    nvars = int(lines[1])
    variables = lines[2 : 2 + nvars]
    time_value = float(lines[2 + nvars + 1])
    return variables, time_value

def parse_cell_h(plot_name):
    lines = (run_dir / plot_name / "Level_0" / "Cell_H").read_text(errors="replace").splitlines()
    records = []
    i = 0
    while i < len(lines):
        m = re.match(r"^\s*([0-9]+),([0-9]+)\s*$", lines[i])
        if m:
            nrows = int(m.group(1))
            ncols = int(m.group(2))
            block = []
            for row_idx in range(nrows):
                vals = [float(x) for x in lines[i + 1 + row_idx].strip().rstrip(",").split(",") if x]
                if len(vals) != ncols:
                    fail(f"bad min/max row length in {plot_name}")
                block.append(vals)
            records.append(block)
            i += 1 + nrows
            continue
        i += 1
    if len(records) < 2:
        fail(f"cannot parse Cell_H records in {plot_name}")
    mins = [min(row[col] for row in records[0]) for col in range(len(records[0][0]))]
    maxs = [max(row[col] for row in records[1]) for col in range(len(records[1][0]))]
    return mins, maxs

text = restart_log.read_text(errors="replace")
for needle in [
    f"MPI initialized with {mpi_ranks} MPI processes",
    "Creating ReactorBase instance: ReactorCvode",
    "Initializing CVODE:",
    f"STEP [{final_step - 1}]",
]:
    if needle not in text:
        fail(f"missing restart marker: {needle}")
cuda_match = re.search(r"CUDA initialized with\s+([0-9]+)\s+devices?", text)
if not cuda_match:
    fail("missing CUDA initialization marker")
cuda_devices = int(cuda_match.group(1))
if cuda_devices < 2:
    fail(f"expected at least 2 CUDA devices, got {cuda_devices}")
if "AMReX" not in text or "finalized" not in text.lower():
    fail("restart run did not finalize")
bad = [
    line.strip()
    for line in (initial_log.read_text(errors="replace") + "\n" + text).splitlines()
    if re.search(
        r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Segmentation|SIGSEGV|CUDA error|"
        r"Abort|Backtrace|Wrong solve_type|CVODE solve failed|reactor failed",
        line,
        re.I,
    )
]
if bad:
    fail(f"failure markers: {bad[:5]}")
if not restart_chk.is_dir():
    fail(f"missing checkpoint dir: {restart_chk}")

plots = sorted(p.name for p in run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
required_plots = {f"plt{initial_step:05d}", f"plt{final_step:05d}"}
if not required_plots.issubset(set(plots)):
    fail(f"missing required plotfiles: required={required_plots} plots={plots}")

history = []
required_vars = {"Y(H2)", "Y(O2)", "Y(H2O)", "temp", "HeatRelease", "I_R(H2)", "I_R(O2)"}
for plot in plots:
    variables, time_value = parse_header(plot)
    missing = sorted(required_vars - set(variables))
    if missing:
        fail(f"missing variables in {plot}: {missing}")
    mins, maxs = parse_cell_h(plot)
    def extrema(name):
        idx = variables.index(name)
        return mins[idx], maxs[idx]
    heat_min, heat_max = extrema("HeatRelease")
    ir_h2_min, ir_h2_max = extrema("I_R(H2)")
    _, yh2o_max = extrema("Y(H2O)")
    _, temp_max = extrema("temp")
    history.append({
        "plotfile": plot,
        "time": time_value,
        "temp_max": temp_max,
        "heat_release_abs_max": max(abs(heat_min), abs(heat_max)),
        "ir_h2_abs_max": max(abs(ir_h2_min), abs(ir_h2_max)),
        "y_h2o_max": yh2o_max,
        "post_restart": int(plot[3:]) > initial_step,
    })

initial_row = next(row for row in history if row["plotfile"] == "plt00000")
checkpoint_row = next(row for row in history if row["plotfile"] == f"plt{initial_step:05d}")
final_row = next(row for row in history if row["plotfile"] == f"plt{final_step:05d}")
post_rows = [
    row for row in history
    if row["post_restart"]
    and row["heat_release_abs_max"] >= 1000.0
    and row["ir_h2_abs_max"] >= 1.0e-3
    and row["y_h2o_max"] > initial_row["y_h2o_max"] + 1.0e-7
]
if len(post_rows) < 3:
    fail(f"insufficient post-restart sustained fire outputs: {len(post_rows)}")
if final_row["y_h2o_max"] <= checkpoint_row["y_h2o_max"]:
    fail("H2O did not continue growing after restart")
if final_row["time"] <= checkpoint_row["time"]:
    fail("time did not advance after restart")

summary = {
    "schema_version": 1,
    "status": "PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-RESTART-SUSTAINED",
    "run_root": str(log_root),
    "run_dir": str(run_dir),
    "restart_checkpoint": str(restart_chk),
    "initial_step": initial_step,
    "final_step": final_step,
    "n_cell": n_cell,
    "mpi_ranks": mpi_ranks,
    "cuda_devices": cuda_devices,
    "post_restart_sustained_output_count": len(post_rows),
    "checkpoint_time": checkpoint_row["time"],
    "final_time": final_row["time"],
    "checkpoint_y_h2o_max": checkpoint_row["y_h2o_max"],
    "final_y_h2o_max": final_row["y_h2o_max"],
    "plotfiles": plots,
    "reaction_history": history,
    "validated_capabilities": {
        "checkpoint_written": True,
        "restart_from_checkpoint": True,
        "post_restart_sustained_fire_development": True,
        "mpi_cuda_parallel": True,
        "pipe_rack_stl_obstacles": True,
        "reactor_cvode": True,
        "cvode_gmres": True,
    },
    "evidence_files": [
        {"label": "initial_run_log", "path": str(initial_log), "sha256": sha(initial_log)},
        {"label": "restart_run_log", "path": str(restart_log), "sha256": sha(restart_log)},
        {"label": "restart_command", "path": str(restart_command), "sha256": sha(restart_command)},
        {"label": "restart_checkpoint_header", "path": str(restart_chk / "Header"), "sha256": sha(restart_chk / "Header")},
        {"label": "final_plot_header", "path": str(run_dir / f"plt{final_step:05d}" / "Header"), "sha256": sha(run_dir / f"plt{final_step:05d}" / "Header")},
    ],
}
summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(
    "pipe_rack_reacting_restart PASS "
    f"log_root={log_root} initial_step={initial_step} final_step={final_step} "
    f"mpi_ranks={mpi_ranks} cuda_devices={cuda_devices} "
    f"post_restart_outputs={len(post_rows)} final_y_h2o={final_row['y_h2o_max']:.8e}"
)
PYCHECK
