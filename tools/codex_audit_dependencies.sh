#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

echo "# Codex dependency audit"
echo "repo=$repo_root"
echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "## Git HEADs for external roots"
for p in external/amrex external/PelePhysics external/PeleC external/PeleLMeX external/PeleLMeX/Submodules/AMReX-Hydro; do
  echo "### $p"
  if [ -e "$p" ]; then
    ls -ld "$p"
    resolved=$(readlink -f "$p" || true)
    echo "resolved=$resolved"
    if git -C "$p" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      echo "head=$(git -C "$p" rev-parse HEAD)"
      echo "branch=$(git -C "$p" branch --show-current || true)"
      dirty=$(git -C "$p" status --porcelain=v1 | wc -l)
      echo "dirty_entries=$dirty"
    else
      echo "git=not-a-worktree"
    fi
  else
    echo "missing"
  fi
  echo
done

echo "## Top-level external symlinks"
find external -maxdepth 4 -type l -printf '%p -> %l\n' | sort
echo

echo "## Broken symlinks relevant to reproducibility"
find external examples tools docs -xtype l -printf '%p -> %l\n' 2>/dev/null | sort
echo


echo "## Stale paths excluded from maintained smoke discovery"
for p in examples/academic/deton_cpu_build external/PeleLMeX_BAK_20260708; do
  if [ -e "$p" ]; then
    echo "$p"
  fi
done
echo
echo "## Submodule status"
git submodule status --recursive 2>&1 || true
