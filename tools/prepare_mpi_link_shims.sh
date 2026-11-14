#!/usr/bin/env bash
# Prepare project-local linker shims for systems where the MPI wrapper emits
# development-link names but only versioned runtime libraries are installed.
# Source this script before MPI builds so LIBRARY_PATH/LD_LIBRARY_PATH inherit it.
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
shim_dir="${CODEX_MPI_LINK_SHIM_DIR:-$repo_root/.codex/lib/mpi-link}"
mkdir -p "$shim_dir"

search_dirs=(
  /usr/lib/x86_64-linux-gnu
  /usr/lib64
  /usr/lib
  /usr/local/lib64
  /usr/local/lib
)

find_library() {
  local pattern=$1
  local dir candidate
  for dir in "${search_dirs[@]}"; do
    [ -d "$dir" ] || continue
    for candidate in "$dir"/$pattern; do
      [ -e "$candidate" ] || continue
      printf '%s\n' "$candidate"
      return 0
    done
  done
  return 1
}

link_library() {
  local link_name=$1
  shift
  local pattern target
  for pattern in "$@"; do
    if target=$(find_library "$pattern"); then
      ln -sfn "$target" "$shim_dir/$link_name"
      return 0
    fi
  done
  printf '[codex-mpi-shim] missing target for %s patterns=%s\n' "$link_name" "$*" >&2
  return 1
}

missing=0
link_library libmpi_cxx.so 'libmpi_cxx.so' 'libmpi_cxx.so.*' || missing=1
link_library libopen-rte.so 'libopen-rte.so' 'libopen-rte.so.*' || missing=1
link_library libopen-pal.so 'libopen-pal.so' 'libopen-pal.so.*' || missing=1
link_library libhwloc.so 'libhwloc.so' 'libhwloc.so.*' || missing=1
link_library libevent_core.so 'libevent_core.so' 'libevent_core-*.so.*' || missing=1
link_library libevent_pthreads.so 'libevent_pthreads.so' 'libevent_pthreads-*.so.*' || missing=1

if [ "$missing" -ne 0 ]; then
  exit 1
fi

case ":${LIBRARY_PATH:-}:" in
  *":$shim_dir:"*) ;;
  *) export LIBRARY_PATH="$shim_dir${LIBRARY_PATH:+:$LIBRARY_PATH}" ;;
esac
case ":${LD_LIBRARY_PATH:-}:" in
  *":$shim_dir:"*) ;;
  *) export LD_LIBRARY_PATH="$shim_dir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ;;
esac

printf '[codex-mpi-shim] using mpi link shim dir=%s\n' "$shim_dir"
