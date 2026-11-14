#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
build_root="${CODEX_BUILD_DIR:-/tmp/codex_geometry_amrex_domain_smoke_20260715}"
raw_amrex_prefix="${AMREX_DIR:-$repo_root/external/amrex/build}"
log_file="${CODEX_RUN_LOG:-$build_root/run.log}"

rm -rf "$build_root"
mkdir -p "$build_root"

amrex_prefix="$raw_amrex_prefix"
if grep -R -E -q '/h[o]me/[^[:space:]]+/projects/amrex-development' "$raw_amrex_prefix/lib/cmake/AMReX" 2>/dev/null; then
  amrex_prefix="$build_root/amrex-sanitized"
  mkdir -p "$amrex_prefix/lib/cmake"
  cp -a "$raw_amrex_prefix/lib/cmake/AMReX" "$amrex_prefix/lib/cmake/"
  python3 - "$amrex_prefix/lib/cmake/AMReX" "$repo_root/external/amrex" <<'PY'
import pathlib
import re
import sys
cmake_dir = pathlib.Path(sys.argv[1])
replacement = sys.argv[2]
pattern = re.compile(r"/h[o]me/[^\s\"';)]+/projects/amrex-development")
for path in cmake_dir.rglob('*.cmake'):
    text = path.read_text()
    new_text = pattern.sub(replacement, text)
    if new_text != text:
        path.write_text(new_text)
PY
fi

cat > "$build_root/CMakeLists.txt" <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(codex_geometry_amrex_domain_smoke LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(AMReX REQUIRED)
add_executable(test_amrex_domain_builder
  ${REPO_ROOT}/test/unit/test_amrex_domain_builder.cpp
)
target_include_directories(test_amrex_domain_builder PRIVATE
  ${REPO_ROOT}/src/geometry
)
target_link_libraries(test_amrex_domain_builder PRIVATE AMReX::amrex_3d)
CMAKE

cmake -S "$build_root" -B "$build_root/build" \
  -DREPO_ROOT="$repo_root" \
  -DCMAKE_PREFIX_PATH="$amrex_prefix" \
  > "$build_root/configure.log"
cmake --build "$build_root/build" -j "${JOBS:-4}" > "$build_root/build.log"
"$build_root/build/test_amrex_domain_builder" | tee "$log_file"

grep -q 'AMReX BoxArray covers generated domain' "$log_file"
grep -q 'AMReX mesh rejects nonpositive cell counts' "$log_file"
