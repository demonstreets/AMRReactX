#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
root="${CODEX_PELEPHYSICS_RATE_KERNEL_ROOT:-$repo_root/docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728}"
exe="$root/academic_gas_pelephysics_lidryer_kernel_probe.ex"
csv="$root/pelephysics_lidryer_kernel_probe.csv"
build_log="$root/build.log"

mkdir -p "$root"

config_dir="${CODEX_AMREX_CONFIG_DIR:-}"
if [[ -z "$config_dir" ]]; then
  for candidate in \
    "$repo_root/external/PeleC/Exec/RegTests/DetonationZND/tmp_build_dir/s/3d.gnu.EXE" \
    "$repo_root/external/PeleLMeX/build/Submodules/PelePhysics/Submodules/amrex" \
    "$repo_root/build-gpu/Submodules/PelePhysics/Submodules/amrex"
  do
    if [[ -f "$candidate/AMReX_Config.H" ]]; then
      config_dir="$candidate"
      break
    fi
  done
fi

if [[ -z "$config_dir" || ! -f "$config_dir/AMReX_Config.H" ]]; then
  echo "Could not locate AMReX_Config.H; set CODEX_AMREX_CONFIG_DIR" >&2
  exit 2
fi

{
  printf '[academic-rate-kernel] repo=%s\n' "$repo_root"
  printf '[academic-rate-kernel] config_dir=%s\n' "$config_dir"
  g++ --version | head -1
  set -x
  g++ -std=c++20 -O2 \
    -I"$config_dir" \
    -I"$repo_root/external/amrex/Src/Base" \
    -I"$repo_root/external/PelePhysics/Mechanisms/LiDryer" \
    "$repo_root/tools/academic_gas_pelephysics_lidryer_kernel_probe.cpp" \
    "$repo_root/external/PelePhysics/Mechanisms/LiDryer/mechanism.cpp" \
    -o "$exe"
} > "$build_log" 2>&1

"$exe" > "$csv"

python3 "$repo_root/tools/write_academic_gas_pelephysics_rate_kernel_equivalence_report.py" \
  --probe-csv "$csv" \
  --build-log "$build_log"
python3 "$repo_root/tools/write_academic_gas_pelephysics_rate_kernel_equivalence_report.py" \
  --verify-json "$root/pelephysics_rate_kernel_equivalence_report.json"

printf '[academic-rate-kernel] PASS root=%s\n' "$root"
