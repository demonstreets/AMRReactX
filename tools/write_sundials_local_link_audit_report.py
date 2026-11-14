#!/usr/bin/env python3
"""Audit the machine-local SUNDIALS link layout without modifying it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-SUNDIALS-LOCAL-LINK-AUDIT"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/sundials_local_link_audit_20260820")
DEFAULT_JSON = DEFAULT_ROOT / "sundials_local_link_audit_report.json"
DEFAULT_MD = DEFAULT_ROOT / "sundials_local_link_audit_report.md"

SUNDIALS_LINK = Path("external/PelePhysics/Submodules/sundials")
EXPECTED_TRACKED_MODE = "120000"
EXPECTED_TRACKED_TARGET = Path("/", "tmp", "sundials-6.7.0").as_posix()


class SundialsLocalLinkAuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SundialsLocalLinkAuditError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def tracked_mode(path: Path) -> str:
    line = run_git(["ls-files", "-s", "--", path.as_posix()]).strip()
    return line.split()[0] if line else ""


def tracked_target(path: Path) -> str:
    return run_git(["show", f"HEAD:{path.as_posix()}"]).strip()


def porcelain_xy(path: Path) -> str:
    output = run_git(["status", "--short", "--", path.as_posix()])
    for line in output.splitlines():
        if line.endswith(path.as_posix()) or line[3:].startswith(path.as_posix()):
            return line[:2]
    return ""


def replacement_kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    if path.is_file():
        return "file"
    if path.exists():
        return "other_existing_path"
    return "missing"


def path_info(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists() or path.is_symlink(),
        "kind": replacement_kind(path),
    }
    if path.is_symlink():
        info["symlink_target"] = os.readlink(path)
    if path.exists() and not path.is_symlink():
        try:
            stat = path.stat()
            info["mode_octal"] = oct(stat.st_mode & 0o777)
            info["size_bytes"] = stat.st_size
        except OSError as exc:
            info["stat_error"] = str(exc)
    return info


def directory_markers(path: Path) -> dict[str, Any]:
    markers = [
        "CMakeLists.txt",
        "include",
        "include/sundials",
        "lib",
        "lib64",
        "src",
    ]
    return {
        "path": str(path),
        "exists": path.exists(),
        "kind": replacement_kind(path),
        "markers": {marker: (path / marker).exists() for marker in markers},
    }


def sundials_candidate_paths() -> list[Path]:
    home = Path.home()
    candidates = []
    env_value = os.environ.get("SUNDIALS_CUDA_DIR") or os.environ.get("SUNDIALS_DIR")
    if env_value:
        candidates.append(Path(env_value))
    candidates.extend(
        [
            home / "local" / "sundials-cuda",
            home / ".local" / "sundials-cuda-6.4.1",
            Path(EXPECTED_TRACKED_TARGET),
        ]
    )
    result: list[Path] = []
    seen = set()
    for item in candidates:
        key = str(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def cuda_sundials_install_ready(path: Path) -> bool:
    return (path / "include").is_dir() and ((path / "lib").is_dir() or (path / "lib64").is_dir())


def file_hashes(paths: list[Path]) -> list[dict[str, Any]]:
    entries = []
    for path in paths:
        if path.is_file():
            entries.append(
                {
                    "path": str(path),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return entries


def build_report() -> dict[str, Any]:
    mode = tracked_mode(SUNDIALS_LINK)
    target = tracked_target(SUNDIALS_LINK)
    current_kind = replacement_kind(SUNDIALS_LINK)
    current_xy = porcelain_xy(SUNDIALS_LINK)
    expected_target_path = Path(target or EXPECTED_TRACKED_TARGET)
    target_info = directory_markers(expected_target_path)
    candidates = [
        {
            **directory_markers(path),
            "cuda_sundials_install_ready": cuda_sundials_install_ready(path),
        }
        for path in sundials_candidate_paths()
    ]
    current_is_expected_symlink = (
        SUNDIALS_LINK.is_symlink()
        and os.readlink(SUNDIALS_LINK) == (target or EXPECTED_TRACKED_TARGET)
    )
    tracked_symlink_ok = mode == EXPECTED_TRACKED_MODE and target == EXPECTED_TRACKED_TARGET
    local_link_drift_present = not current_is_expected_symlink
    cuda_ready_candidates = [item for item in candidates if item["cuda_sundials_install_ready"]]

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "scope": "non-destructive audit of the repository SUNDIALS symlink and CUDA SUNDIALS candidates",
        "summary": {
            "audit_ready": True,
            "cleanup_performed": False,
            "tracked_symlink_ok": tracked_symlink_ok,
            "tracked_mode": mode,
            "tracked_target": target,
            "expected_tracked_mode": EXPECTED_TRACKED_MODE,
            "expected_tracked_target": EXPECTED_TRACKED_TARGET,
            "current_replacement_kind": current_kind,
            "current_git_xy": current_xy,
            "current_is_expected_symlink": current_is_expected_symlink,
            "local_link_drift_present": local_link_drift_present,
            "expected_target_exists": expected_target_path.exists(),
            "cuda_sundials_ready_candidate_count": len(cuda_ready_candidates),
            "safe_to_auto_restore": False,
            "restore_requires_explicit_operator_review": True,
            "current_scope_cuda_validation_can_use_alternate_sundials_dir": len(cuda_ready_candidates) > 0,
        },
        "repo_link": {
            "tracked": {
                "path": SUNDIALS_LINK.as_posix(),
                "mode": mode,
                "target": target,
            },
            "current": path_info(SUNDIALS_LINK),
            "expected_target": target_info,
        },
        "cuda_sundials_candidates": candidates,
        "operator_guidance": [
            "Do not delete or replace external/PelePhysics/Submodules/sundials from this report alone.",
            "If packaging source, resolve the tracked symlink versus replacement directory deliberately.",
            "CUDA smoke scripts may still pass when SUNDIALS_CUDA_DIR points to a separate ready install.",
            "After manual dependency repair, rerun this audit and the current worktree review queue.",
        ],
        "hashed_artifacts": file_hashes(
            [
                Path("tools/write_sundials_local_link_audit_report.py"),
                Path("tools/verify_sundials_local_link_audit.sh"),
                Path("tools/codex_setup_cuda126_sundials_env.sh"),
                Path("tools/check_machine_local_paths.py"),
            ]
        ),
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("audit_ready") is True, "audit is not ready")
    require(summary.get("cleanup_performed") is False, "audit must be non-destructive")
    require(summary.get("tracked_mode") == EXPECTED_TRACKED_MODE, "unexpected tracked SUNDIALS mode")
    require(summary.get("tracked_target") == EXPECTED_TRACKED_TARGET, "unexpected tracked SUNDIALS target")
    require(summary.get("safe_to_auto_restore") is False, "audit must not mark auto-restore safe")
    require(
        summary.get("restore_requires_explicit_operator_review") is True,
        "missing explicit-review restore guard",
    )
    require(
        summary.get("current_replacement_kind") in {"symlink", "directory", "file", "missing", "other_existing_path"},
        "invalid current replacement kind",
    )
    require(isinstance(data.get("repo_link"), dict), "missing repo link details")
    candidates = data.get("cuda_sundials_candidates")
    require(isinstance(candidates, list) and candidates, "missing SUNDIALS candidates")
    guidance = data.get("operator_guidance")
    require(isinstance(guidance, list), "missing operator guidance")
    require(any("Do not delete" in item for item in guidance), "missing non-destructive warning")
    if verify_hashes:
        for entry in data.get("hashed_artifacts", []):
            require(isinstance(entry, dict), "invalid hashed artifact entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing hashed artifact: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# SUNDIALS Local Link Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Audit ready: `{summary['audit_ready']}`",
        f"- Cleanup performed: `{summary['cleanup_performed']}`",
        f"- Tracked mode: `{summary['tracked_mode']}`",
        f"- Tracked target: `{summary['tracked_target']}`",
        f"- Current replacement kind: `{summary['current_replacement_kind']}`",
        f"- Current Git XY: `{summary['current_git_xy']}`",
        f"- Local link drift present: `{summary['local_link_drift_present']}`",
        f"- Expected target exists: `{summary['expected_target_exists']}`",
        f"- CUDA SUNDIALS ready candidates: `{summary['cuda_sundials_ready_candidate_count']}`",
        f"- Safe to auto-restore: `{summary['safe_to_auto_restore']}`",
        f"- Restore requires explicit operator review: `{summary['restore_requires_explicit_operator_review']}`",
        "",
        "## CUDA SUNDIALS Candidates",
        "",
    ]
    for item in report["cuda_sundials_candidates"]:
        lines.append(
            f"- `{item['path']}` kind=`{item['kind']}` exists=`{item['exists']}` "
            f"ready=`{item['cuda_sundials_install_ready']}`"
        )
    lines.extend(["", "## Operator Guidance", ""])
    for item in report["operator_guidance"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
        validate_report(data, verify_hashes=True)
        print(f"sundials_local_link_audit VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"sundials_local_link_audit PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
