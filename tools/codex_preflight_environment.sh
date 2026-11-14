#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

require_cuda=0
strict_sundials_64=0
for arg in "$@"; do
  case "$arg" in
    --require-cuda) require_cuda=1 ;;
    --strict-sundials-6.4) strict_sundials_64=1 ;;
    -h|--help)
      cat <<'USAGE'
Usage: tools/codex_preflight_environment.sh [--require-cuda] [--strict-sundials-6.4]

Checks the current machine against the Codex-maintained my-pele worktree:
  - release provenance strict gate
  - machine-local absolute path audit for maintained sources/scripts
  - core build tools
  - git dependency/symlink layout
  - optional CUDA hardware/toolchain
  - SUNDIALS_CUDA_DIR/SUNDIALS_DIR include/lib/version/library requirements
USAGE
      exit 0
      ;;
    *) echo "preflight FAIL unknown argument: $arg" >&2; exit 2 ;;
  esac
done

failures=0
warnings=0

pass() { printf 'preflight PASS %s
' "$*"; }
info() { printf 'preflight INFO %s
' "$*"; }
warn() { warnings=$((warnings + 1)); printf 'preflight WARN %s
' "$*"; }
fail() { failures=$((failures + 1)); printf 'preflight FAIL %s
' "$*"; }

check_cmd() {
  local cmd=$1
  if command -v "$cmd" >/dev/null 2>&1; then
    pass "command $cmd=$(command -v "$cmd")"
  else
    fail "missing command $cmd"
  fi
}

for cmd in git cmake make python3 c++ cc; do
  check_cmd "$cmd"
done

if python3 tools/check_release_provenance.py --strict >/tmp/codex_preflight_release_provenance.log 2>&1; then
  pass "release provenance strict log=/tmp/codex_preflight_release_provenance.log"
else
  cat /tmp/codex_preflight_release_provenance.log >&2 || true
  fail "release provenance strict failed"
fi

if python3 tools/check_machine_local_paths.py --strict >/tmp/codex_preflight_machine_local_paths.log 2>&1; then
  pass "machine-local path audit strict log=/tmp/codex_preflight_machine_local_paths.log"
else
  cat /tmp/codex_preflight_machine_local_paths.log >&2 || true
  fail "machine-local path audit strict failed"
fi

while IFS=$'	' read -r dep_path dep_kind dep_source dep_notes; do
  [ "$dep_path" = "path" ] && continue
  [ -z "$dep_path" ] && continue
  case "$dep_kind" in
    relative-symlink)
      if [ ! -L "$dep_path" ]; then
        fail "$dep_path expected relative symlink"
      else
        actual=$(readlink "$dep_path")
        if [ "$actual" = "$dep_source" ]; then
          pass "$dep_path symlink=$actual"
        else
          fail "$dep_path symlink expected $dep_source got $actual"
        fi
      fi
      ;;
    git-submodule)
      if [ -d "$dep_path/.git" ] || git -C "$dep_path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        pass "$dep_path git worktree present"
      else
        fail "$dep_path expected git worktree/submodule"
      fi
      ;;
    local-cmake-shim)
      if [ -f "$dep_path/CMakeLists.txt" ]; then
        pass "$dep_path local CMake shim present"
      else
        fail "$dep_path missing CMakeLists.txt shim"
      fi
      ;;
    *)
      warn "$dep_path has unrecognized dependency kind $dep_kind"
      ;;
  esac
done < docs/codex_audit/DEPENDENCY_PROVENANCE.tsv

sundials_dir="${SUNDIALS_CUDA_DIR:-${SUNDIALS_DIR:-}}"
if [ -z "$sundials_dir" ]; then
  fail "SUNDIALS_CUDA_DIR or SUNDIALS_DIR is not set"
else
  info "SUNDIALS_CUDA_DIR=$sundials_dir"
  if [ -d "$sundials_dir/include" ]; then
    pass "SUNDIALS include directory exists"
  else
    fail "missing SUNDIALS include directory: $sundials_dir/include"
  fi
  if [ -d "$sundials_dir/lib" ]; then
    pass "SUNDIALS lib directory exists"
  else
    fail "missing SUNDIALS lib directory: $sundials_dir/lib"
  fi
  config="$sundials_dir/include/sundials/sundials_config.h"
  if [ -f "$config" ]; then
    version=$(awk '$1 == "#define" && $2 == "SUNDIALS_VERSION" {gsub(/"/, "", $3); print $3; exit}' "$config")
    cuda_version=$(awk '$1 == "#define" && $2 == "SUN_CUDA_VERSION" {gsub(/"/, "", $3); print $3; exit}' "$config")
    info "SUNDIALS_VERSION=${version:-unknown}"
    info "SUN_CUDA_VERSION=${cuda_version:-unknown}"
    if [ "$strict_sundials_64" -eq 1 ] && [ "${version:-}" != "6.4.0" ]; then
      fail "master-plan strict SUNDIALS 6.4 requested but found ${version:-unknown}"
    elif [ "${version%%.*}" = "6" ]; then
      pass "SUNDIALS major version is 6 (validated server uses 6.7.0)"
    else
      warn "SUNDIALS version ${version:-unknown} differs from validated 6.x line"
    fi
  else
    fail "missing SUNDIALS config header: $config"
  fi
  for lib in libsundials_cvode libsundials_core libsundials_nvecserial; do
    if compgen -G "$sundials_dir/lib/${lib}.so*" >/dev/null || [ -f "$sundials_dir/lib/${lib}.a" ]; then
      pass "SUNDIALS library $lib present"
    else
      fail "missing SUNDIALS library $lib in $sundials_dir/lib"
    fi
  done
  for lib in libsundials_nveccuda libsundials_sunlinsolcusolversp libsundials_sunmatrixcusparse; do
    if compgen -G "$sundials_dir/lib/${lib}.so*" >/dev/null || [ -f "$sundials_dir/lib/${lib}.a" ]; then
      pass "SUNDIALS CUDA library $lib present"
    elif [ "$require_cuda" -eq 1 ]; then
      fail "missing SUNDIALS CUDA library $lib in $sundials_dir/lib"
    else
      warn "missing optional SUNDIALS CUDA library $lib in $sundials_dir/lib"
    fi
  done
fi

if [ "$require_cuda" -eq 1 ]; then
  for cmd in nvcc nvidia-smi; do
    check_cmd "$cmd"
  done
  if command -v nvcc >/dev/null 2>&1; then
    nvcc --version | sed 's/^/preflight INFO nvcc /'
  fi
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader | sed 's/^/preflight INFO gpu /'
  fi
else
  if command -v nvcc >/dev/null 2>&1; then
    info "nvcc=$(command -v nvcc)"
  else
    warn "nvcc not found; CUDA smokes require --require-cuda machines"
  fi
fi

if [ "$failures" -ne 0 ]; then
  printf 'preflight SUMMARY FAIL failures=%d warnings=%d
' "$failures" "$warnings"
  exit 1
fi
printf 'preflight SUMMARY PASS warnings=%d
' "$warnings"
