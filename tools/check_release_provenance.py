#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "docs/codex_audit/DEPENDENCY_PROVENANCE.tsv"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def run_git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.stdout.strip()


def tracked_symlink_target(path: str) -> str | None:
    out = run_git(["cat-file", "-p", f"HEAD:{path}"])
    if not out or out.startswith("fatal:"):
        return None
    return out


def read_manifest() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    if not MANIFEST.exists():
        return rows
    lines = MANIFEST.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return rows
    header = lines[0].split("\t")
    for lineno, line in enumerate(lines[1:], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != len(header):
            rows[f"__bad_line_{lineno}"] = {"path": f"malformed line {lineno}: {line}"}
            continue
        row = dict(zip(header, fields))
        rows[row["path"]] = row
    return rows


def actual_dependency_shape(path: Path) -> tuple[str, str | None]:
    if path.is_symlink():
        return "symlink", os.readlink(path)
    if path.is_dir():
        return "directory", None
    if path.exists():
        return "file", None
    return "missing", None


def scan_for_machine_local_sundials_paths() -> list[str]:
    needles = ("/home/cj/local/sundials-cuda", "/tmp/sundials")
    roots = [
        REPO_ROOT / "external/PeleLMeX/CMake",
        REPO_ROOT / "external/PeleC/CMake",
        REPO_ROOT / "external/PelePhysics/Submodules/sundials",
        REPO_ROOT / "tools",
    ]
    findings: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            files = [root]
        else:
            files = [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.resolve() != Path(__file__).resolve()]
        for file_path in files:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for needle in needles:
                if needle in text:
                    findings.append(f"{rel(file_path)} contains {needle}")
    return sorted(set(findings))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit nonzero on warnings")
    args = ap.parse_args()

    warnings: list[str] = []
    infos: list[str] = []

    gitmodules = REPO_ROOT / ".gitmodules"
    if not gitmodules.exists():
        warnings.append("missing .gitmodules")
    else:
        text = gitmodules.read_text(encoding="utf-8", errors="replace")
        if "external/PeleLMeX/Submodules/AMReX-Hydro" in text:
            infos.append(".gitmodules declares external/PeleLMeX/Submodules/AMReX-Hydro")
        else:
            warnings.append(".gitmodules does not declare external/PeleLMeX/Submodules/AMReX-Hydro")

    manifest = read_manifest()
    if not manifest:
        warnings.append(f"missing dependency provenance manifest {rel(MANIFEST)}")
    for key, row in manifest.items():
        if key.startswith("__bad_line_"):
            warnings.append(row["path"])

    expected_paths = {
        "external/PelePhysics/Submodules/amrex": ("relative-symlink", "../../amrex"),
        "external/PeleLMeX/Submodules/PelePhysics": ("relative-symlink", "../../PelePhysics"),
        "external/PeleC/Submodules/PelePhysics": ("relative-symlink", "../../PelePhysics"),
        "external/PelePhysics/Submodules/sundials": ("local-cmake-shim", None),
        "external/PeleLMeX/Submodules/AMReX-Hydro": ("git-submodule", None),
    }
    for dep, (kind, expected_target) in expected_paths.items():
        row = manifest.get(dep)
        if row is None:
            warnings.append(f"dependency provenance manifest does not declare {dep}")
            continue
        if row.get("kind") != kind:
            warnings.append(f"dependency provenance manifest kind mismatch for {dep}: expected {kind} got {row.get('kind')}")
        path = REPO_ROOT / dep
        shape, actual_target = actual_dependency_shape(path)
        if kind == "relative-symlink":
            if shape != "symlink":
                warnings.append(f"{dep} should be a relative symlink but is {shape}")
            elif actual_target != expected_target:
                warnings.append(f"{dep} symlink target mismatch: expected {expected_target} got {actual_target}")
            else:
                infos.append(f"{dep} worktree symlink target {actual_target}")
        elif kind == "local-cmake-shim":
            cmake = path / "CMakeLists.txt"
            if not cmake.exists():
                warnings.append(f"{dep} missing local CMake shim")
            else:
                infos.append(f"found local SUNDIALS shim {rel(cmake)}")
                text = cmake.read_text(encoding="utf-8", errors="replace")
                if "SUNDIALS_CUDA_DIR" not in text and "SUNDIALS_DIR" not in text:
                    warnings.append(f"{rel(cmake)} does not require configurable SUNDIALS path")
        elif kind == "git-submodule":
            if shape != "directory":
                warnings.append(f"{dep} should be a checked-out git submodule directory but is {shape}")

        tracked = tracked_symlink_target(dep)
        if tracked is not None and os.path.isabs(tracked):
            infos.append(f"{dep} is still absolute in HEAD until committed: {tracked}")

    for finding in scan_for_machine_local_sundials_paths():
        warnings.append(f"machine-local SUNDIALS path remains: {finding}")

    install_lib = REPO_ROOT / "external/PelePhysics/ThirdParty/INSTALL/gnu/lib"
    if install_lib.is_dir():
        libs = sorted(install_lib.glob("libsundials_*.a"))
        infos.append(f"repo-local PelePhysics ThirdParty SUNDIALS static link entries={len(libs)}")
    else:
        warnings.append("missing external/PelePhysics/ThirdParty/INSTALL/gnu/lib")

    for item in infos:
        print(f"release_provenance INFO {item}")
    for item in warnings:
        print(f"release_provenance WARN {item}")
    if warnings:
        print(f"release_provenance {'FAIL' if args.strict else 'PASS-WARN'} warnings={len(warnings)}")
        return 1 if args.strict else 0
    print("release_provenance PASS warnings=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
