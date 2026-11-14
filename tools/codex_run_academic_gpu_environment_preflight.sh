#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_GPU_PREFLIGHT_ROOT:-docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728}"
run_dir="$root/cuda_detonation_smoke"
manifest="$root/gpu_environment_preflight_manifest.json"
case_src="examples/academic/detonation_znd_gpu"
exe="$case_src/PeleC3d.gnu.CUDA.ex"
input_file="$run_dir/inputs"
smoke_log="$run_dir/run.log"
nvidia_log="$root/nvidia_smi.log"
ldd_log="$root/ldd_cuda_exe.log"
cuda_find_log="$root/cuda_library_search.log"

rm -rf "$run_dir"
mkdir -p "$run_dir"

set +e
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$nvidia_log" 2>&1
nvidia_rc=$?
set -e

ldd "$exe" >"$ldd_log" 2>&1 || true
{
  printf '== ldconfig ==\n'
  ldconfig -p 2>/dev/null | grep -E 'libcurand|libcusparse|libcusolver|libcudart|libcuda' || true
  printf '\n== filesystem ==\n'
  find /usr/local /usr/lib /opt "$repo_root" -name 'libcurand.so*' -o -name 'libcusparse.so*' -o -name 'libcusolver.so*' -o -name 'libcudart.so*' 2>/dev/null | sort | head -200
} >"$cuda_find_log"

cp "$case_src/inputs" "$input_file"
python3 - "$input_file" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
replacements = {
    'max_step': '5',
    'stop_time': '5.0e-8',
    'amr.n_cell': '64 8 8',
    'amr.blocking_factor': '8',
    'cvode.solve_type': 'GMRES',
    'amr.max_level': '0',
    'amr.plot_int': '5',
    'amr.check_int': '-1',
    'amr.checkpoint_files_output': '0',
    'pelec.sum_interval': '-1',
    'pelec.v': '1',
    'amr.v': '1',
}
lines = []
seen = set()
for raw in text.splitlines():
    stripped = raw.split('#', 1)[0].strip()
    if stripped and '=' in stripped:
        key = stripped.split('=', 1)[0].strip()
        if key in replacements:
            lines.append(f'{key} = {replacements[key]}')
            seen.add(key)
            continue
    lines.append(raw)
for key, value in replacements.items():
    if key not in seen:
        lines.append(f'{key} = {value}')
path.write_text('\n'.join(lines) + '\n')
PY

sundials_dirs=$(find "$repo_root/build-gpu2/Submodules/PelePhysics/Submodules/sundials/src" -type f -name 'libsundials_*.so*' -printf '%h\n' 2>/dev/null | sort -u | paste -sd: -)
export LD_LIBRARY_PATH="${sundials_dirs:+$sundials_dirs:}${LD_LIBRARY_PATH:-}"
set +e
(
  cd "$run_dir"
  timeout 180 "$repo_root/$exe" inputs > "$repo_root/$smoke_log" 2>&1
)
smoke_rc=$?
set -e

python3 - "$manifest" "$nvidia_rc" "$smoke_rc" "$nvidia_log" "$ldd_log" "$cuda_find_log" "$input_file" "$smoke_log" <<'PY'
from pathlib import Path
import json
import sys

manifest, nvidia_rc, smoke_rc, nvidia_log, ldd_log, cuda_find_log, input_file, smoke_log = sys.argv[1:]
data = {
    'schema_version': 1,
    'nvidia_smi_returncode': int(nvidia_rc),
    'smoke_returncode': int(smoke_rc),
    'paths': {
        'nvidia_smi_log': nvidia_log,
        'ldd_log': ldd_log,
        'cuda_find_log': cuda_find_log,
        'smoke_input': input_file,
        'smoke_log': smoke_log,
    },
}
path = Path(manifest)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
PY

python3 tools/write_academic_gpu_environment_preflight_report.py \
  --manifest "$manifest" \
  --output-json "$root/academic_gpu_environment_preflight_report.json" \
  --output-md "$root/academic_gpu_environment_preflight_report.md"

python3 tools/write_academic_gpu_environment_preflight_report.py \
  --verify-json "$root/academic_gpu_environment_preflight_report.json"

printf 'academic_gpu_environment_preflight RUNNER-DONE root=%s nvidia_rc=%s smoke_rc=%s\n' "$root" "$nvidia_rc" "$smoke_rc"
