#!/usr/bin/env python3
"""Static audit for obvious host-only constructs in GPU-marked code.

This is intentionally conservative: it does not prove CUDA/HIP builds work, but
it catches source patterns that should not appear inside functions explicitly
marked for AMReX GPU execution. The extended profile also checks example-level
CUDA bridge code that has caused real runtime failures in this repository.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

GPU_MARKERS = (
    "AMREX_GPU_DEVICE",
    "AMREX_GPU_HOST_DEVICE",
    "MYPELE_LEAK_HD",
)

SOURCE_PROFILES = {
    "default": ("src/academic", "src/engineering", "src/common"),
    "extended": (
        "src/academic",
        "src/engineering",
        "src/common",
        "examples/engineering/c3h8_gpu_test",
    ),
}

FORBIDDEN_PATTERNS = (
    ("std::vector", re.compile(r"\bstd::vector\b")),
    ("std::string", re.compile(r"\bstd::string\b")),
    ("std::map", re.compile(r"\bstd::map\b")),
    ("iostream", re.compile(r"\bstd::(?:cout|cerr|clog|endl)\b")),
    ("printf/fprintf", re.compile(r"\b(?:printf|fprintf|puts)\s*\(")),
    ("dynamic allocation", re.compile(r"\b(?:new|delete|malloc|free)\b")),
    ("exceptions", re.compile(r"\b(?:throw|try|catch)\b")),
    ("RTTI", re.compile(r"\b(?:dynamic_cast|typeid)\b")),
    ("file IO", re.compile(r"\b(?:fopen|fclose|fread|fwrite)\s*\(")),
)

SOURCE_SUFFIXES = {".H", ".h", ".hpp", ".hh", ".cpp", ".cc", ".cxx"}
PROBPARM_PTR_RE = re.compile(r"\b(?:const\s+)?(?:MyProbParm|ProbParm)\s*\*\s*\w+")
PP_ARROW_RE = re.compile(r"\bpp\s*->")
PP_REF_RE = re.compile(r"\b(?:MyProbParm|ProbParm)\b[^;=&]*&[^;=]*=\s*\*\s*pp\b")
GEOM_PTR_RE = re.compile(
    r"(?:const\s+)?(?:amrex::Real|Real)\s*\*\s*(\w+)\s*=\s*geomdata\.(ProbLo|CellSize)\s*\("
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    marker: str
    reason: str
    text: str


@dataclass(frozen=True)
class DeviceBlock:
    path: Path
    marker_line: int
    start_line: int
    end_line: int
    marker: str
    text: str


def is_comment_only(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*")


def brace_delta(line: str) -> int:
    # Good enough for source-audit use; these helpers do not contain raw brace-heavy strings.
    return line.count("{") - line.count("}")


def iter_source_files(root: Path, selected_roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for rel in selected_roots:
        base = root / rel
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in SOURCE_SUFFIXES:
                files.append(path)
    return sorted(files)


def extract_blocks(path: Path, repo_root: Path) -> list[DeviceBlock]:
    rel = path.relative_to(repo_root)
    lines = path.read_text(errors="replace").splitlines()
    blocks: list[DeviceBlock] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        marker = next((m for m in GPU_MARKERS if m in line), None)
        if marker is None or is_comment_only(line):
            i += 1
            continue

        signature_start = i
        j = i
        while j < len(lines) and "{" not in lines[j]:
            j += 1
        if j >= len(lines):
            i += 1
            continue

        depth = 0
        k = j
        while k < len(lines):
            depth += brace_delta(lines[k])
            if depth <= 0 and k > j:
                break
            k += 1
        if k >= len(lines):
            i += 1
            continue

        text = "\n".join(lines[signature_start : k + 1])
        blocks.append(DeviceBlock(rel, i + 1, signature_start + 1, k + 1, marker, text))
        i = k + 1
    return blocks


def scan_block(block: DeviceBlock) -> list[Finding]:
    findings: list[Finding] = []
    for offset, raw in enumerate(block.text.splitlines(), block.start_line):
        code = raw.split("//", 1)[0]
        for reason, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(code):
                findings.append(Finding(block.path, offset, block.marker, reason, raw.strip()))
    return findings


def scan_probparm_host_deref(path: Path, repo_root: Path) -> list[Finding]:
    rel = path.relative_to(repo_root)
    findings: list[Finding] = []
    has_probparm_pointer = False
    gpu_guard_depth = 0
    in_gpu_else = False

    for line_no, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        code = raw.split("//", 1)[0].strip()
        if not code:
            continue
        if PROBPARM_PTR_RE.search(code):
            has_probparm_pointer = True
        if re.match(r"#\s*ifn?def\s+AMREX_USE_GPU\b", code):
            gpu_guard_depth += 1
            in_gpu_else = False
            continue
        if gpu_guard_depth and re.match(r"#\s*else\b", code):
            in_gpu_else = not in_gpu_else
            continue
        if gpu_guard_depth and re.match(r"#\s*endif\b", code):
            gpu_guard_depth -= 1
            in_gpu_else = False
            continue
        if not has_probparm_pointer:
            continue

        direct_arrow = PP_ARROW_RE.search(code)
        direct_ref = PP_REF_RE.search(code)
        allowed_cpu_fallback = gpu_guard_depth > 0 and in_gpu_else
        if direct_arrow or (direct_ref and not allowed_cpu_fallback):
            findings.append(
                Finding(
                    rel,
                    line_no,
                    "ProbParm*",
                    "possible device ProbParm host dereference",
                    raw.strip(),
                )
            )
    return findings


def scan_geometry_pointer_capture(path: Path, repo_root: Path, blocks: list[DeviceBlock]) -> list[Finding]:
    rel = path.relative_to(repo_root)
    text = path.read_text(errors="replace")
    pointer_vars: dict[str, tuple[int, str]] = {}
    for line_no, raw in enumerate(text.splitlines(), 1):
        code = raw.split("//", 1)[0]
        match = GEOM_PTR_RE.search(code)
        if match:
            pointer_vars[match.group(1)] = (line_no, raw.strip())

    findings: list[Finding] = []
    for block in blocks:
        block_pos = text.find(block.text)
        prefix = text[:block_pos] if block_pos >= 0 else ""
        if "ParallelFor" not in prefix[-1000:] + block.text:
            continue
        for name, (line_no, raw) in pointer_vars.items():
            if re.search(rf"\b{re.escape(name)}\s*\[", block.text):
                findings.append(
                    Finding(
                        rel,
                        line_no,
                        "AMREX_GPU_DEVICE",
                        "GeometryData host pointer may be captured by GPU lambda",
                        raw,
                    )
                )
    return findings


def count_host_only_notes(files: list[Path], repo_root: Path) -> tuple[int, list[str]]:
    notes: list[str] = []
    host_vector_functions = 0
    for path in files:
        text = path.read_text(errors="replace")
        if "std::vector" in text and not any(marker in text for marker in GPU_MARKERS):
            host_vector_functions += text.count("std::vector")
            notes.append(str(path.relative_to(repo_root)))
    return host_vector_functions, sorted(set(notes))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument(
        "--profile",
        choices=sorted(SOURCE_PROFILES),
        default="default",
        help="named source-root profile to scan",
    )
    parser.add_argument(
        "--source-root",
        action="append",
        default=None,
        help="custom source root to scan; may be repeated and overrides --profile",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    selected_roots = args.source_root or list(SOURCE_PROFILES[args.profile])
    files = iter_source_files(repo_root, selected_roots)
    blocks: list[DeviceBlock] = []
    findings: list[Finding] = []
    for path in files:
        path_blocks = extract_blocks(path, repo_root)
        blocks.extend(path_blocks)
        findings.extend(scan_probparm_host_deref(path, repo_root))
        findings.extend(scan_geometry_pointer_capture(path, repo_root, path_blocks))
        for block in path_blocks:
            findings.extend(scan_block(block))

    if findings:
        print("gpu_source_audit FAIL")
        for finding in findings:
            print(
                f"{finding.path}:{finding.line}: {finding.reason} inside "
                f"{finding.marker} block: {finding.text}"
            )
        return 1

    host_vector_count, host_vector_files = count_host_only_notes(files, repo_root)
    print(
        "gpu_source_audit PASS "
        f"profile={args.profile} roots={','.join(selected_roots)} "
        f"files={len(files)} gpu_blocks={len(blocks)} forbidden_findings=0"
    )
    if host_vector_files:
        print(
            "gpu_source_audit NOTE host_only_vector_usage "
            f"occurrences={host_vector_count} files={','.join(host_vector_files)}"
        )
    print(
        "gpu_source_audit SCOPE static source audit only; clean CUDA/HIP build "
        "and device runtime smoke remain required for GPU PASS"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
