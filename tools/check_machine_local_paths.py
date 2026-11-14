#!/usr/bin/env python3
"""Audit maintained sources for machine-local absolute paths.

This catches portability hazards that are easy to miss in a dirty HPC worktree:
user-home paths such as /home/cj or /home/demon*, and direct /tmp paths that are
not routed through the Codex smoke/test log conventions.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_ROOTS = [
    "tools",
    "src",
    "test/unit",
    "examples/academic",
    "examples/engineering",
    "external/PeleC/Source",
    "external/PeleC/CMake",
    "external/PeleC/Exec/RegTests/IsentropicVortex",
    "external/PeleLMeX/Source",
    "external/PeleLMeX/CMake",
    "external/PeleLMeX/Exec/RegTests",
    "external/PelePhysics/Source",
    "external/PelePhysics/Testing/Exec",
]

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "tmp_build_dir",
    "o",
    "build",
    "build_cuda",
    "build_cpu",
    "CMakeFiles",
    "Testing",
    "PeleLMeX_BAK_20260708",
    "checkpoints",
}

EXCLUDED_PART_PREFIXES = (
    "plt",
    "chk",
    "Backtrace",
    "bl_prof",
    "amrex_out",
)

EXCLUDED_FILE_SUFFIXES = (
    ".ex",
    ".o",
    ".a",
    ".so",
    ".mod",
)

EXCLUDED_FILE_NAMES = {
    "AMReX_buildInfo.cpp",
}

EXCLUDED_FILES = {
    Path("tools/check_machine_local_paths.py"),
    # This provenance checker intentionally names formerly hard-coded paths as
    # forbidden needles; those literals are not runtime dependencies.
    Path("tools/check_release_provenance.py"),
}

TEXT_SUFFIXES = {
    "",
    ".py", ".sh", ".bash", ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".H",
    ".cmake", ".txt", ".md", ".rst", ".yaml", ".yml", ".json", ".in", ".inputs",
    ".ini", ".cfg", ".tsv", ".csv",
}

HOME_RE = re.compile(r"/home/(?:cj|demon[^\s:'\";)]+)?")
TMP_RE = re.compile(r"/tmp/[A-Za-z0-9_.@%+=:,/\-]+")

ALLOWED_TMP_MARKERS = (
    "/tmp/codex",
    "${TMPDIR:-/tmp}",
    '"${TMPDIR:-/tmp}"',
    "mktemp",
    "CODEX_",
    "TMPDIR",
)

@dataclass(frozen=True)
class Finding:
    path: Path
    line_no: int
    kind: str
    value: str
    line: str


def is_excluded_part(part: str) -> bool:
    return part in EXCLUDED_PARTS or any(part.startswith(prefix) for prefix in EXCLUDED_PART_PREFIXES)


def should_skip_path(path: Path) -> bool:
    if path in EXCLUDED_FILES:
        return True
    if any(is_excluded_part(part) for part in path.parts):
        return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    return path.name.endswith(EXCLUDED_FILE_SUFFIXES)


def is_text_candidate(path: Path) -> bool:
    if path.suffix not in TEXT_SUFFIXES:
        return False
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\0" not in chunk


def iter_files(root: Path, roots: Iterable[str]) -> Iterable[Path]:
    for item in roots:
        base = root / item
        if not base.exists():
            continue
        if base.is_file():
            rel = base.relative_to(root)
            if not should_skip_path(rel) and is_text_candidate(base):
                yield rel
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            current = Path(dirpath)
            rel_dir = current.relative_to(root)
            if should_skip_path(rel_dir):
                dirnames[:] = []
                continue
            dirnames[:] = [name for name in dirnames if not is_excluded_part(name)]
            for filename in filenames:
                path = current / filename
                rel = path.relative_to(root)
                if should_skip_path(rel):
                    continue
                if is_text_candidate(path):
                    yield rel


def allowed_tmp(line: str, value: str) -> bool:
    if value.startswith("/tmp/codex"):
        return True
    return any(marker in line for marker in ALLOWED_TMP_MARKERS)


def scan_file(root: Path, rel: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = (root / rel).read_text(errors="replace")
    except OSError as exc:
        findings.append(Finding(rel, 0, "read-error", str(exc), ""))
        return findings

    for idx, line in enumerate(text.splitlines(), start=1):
        for match in HOME_RE.finditer(line):
            findings.append(Finding(rel, idx, "home-path", match.group(0), line.strip()))
        for match in TMP_RE.finditer(line):
            value = match.group(0)
            if not allowed_tmp(line, value):
                findings.append(Finding(rel, idx, "tmp-path", value, line.strip()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="*", default=DEFAULT_ROOTS, help="roots to scan, relative to repo root")
    parser.add_argument("--strict", action="store_true", help="return non-zero when findings exist")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    all_findings: list[Finding] = []
    scanned = 0
    for rel in sorted(set(iter_files(root, args.roots))):
        scanned += 1
        all_findings.extend(scan_file(root, rel))

    if all_findings:
        print(f"machine_local_paths FAIL findings={len(all_findings)} scanned_files={scanned}")
        for item in all_findings:
            loc = f"{item.path}:{item.line_no}" if item.line_no else str(item.path)
            print(f"{loc}: {item.kind}: {item.value}")
            if item.line:
                print(f"  {item.line}")
        return 1 if args.strict else 0

    print(f"machine_local_paths PASS scanned_files={scanned}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
