#!/usr/bin/env python3
"""Write/verify a dry-run disk-usage manifest for the current repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_AUDITED = "AUDITED-CURRENT-DISK-USAGE-MANIFEST"
STATUS_NOT_READY = "NOT_READY-CURRENT-DISK-USAGE-MANIFEST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_disk_usage_manifest_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_disk_usage_manifest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_disk_usage_manifest_report.md"

CASE_OUTPUT_MANIFEST = Path(
    "docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/"
    "current_case_output_cleanup_manifest_report.json"
)
CURRENT_SCOPE_REPORT = Path(
    "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
    "master_plan_current_scope_verification_report.json"
)

SCAN_ROOTS = [
    Path("."),
    Path("examples"),
    Path("examples/academic"),
    Path("examples/engineering"),
    Path("docs"),
    Path("docs/codex_audit"),
    Path("docs/codex_audit/evidence"),
    Path("tools"),
    Path("test"),
    Path("build-gpu-mpi"),
    Path("build-gpu2"),
]

PROTECTED_PREFIXES = (
    "docs/codex_audit/evidence/",
    "docs/codex_audit/",
)
BUILD_PREFIXES = ("build-", "build_", "build/")
OUTPUT_PATTERNS = [
    re.compile(r"/plt\d", re.IGNORECASE),
    re.compile(r"/chk\d", re.IGNORECASE),
    re.compile(r"\.old\.", re.IGNORECASE),
    re.compile(r"/Level_\d/", re.IGNORECASE),
]
EXECUTABLE_SUFFIXES = (".ex",)


class DiskUsageManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiskUsageManifestError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DiskUsageManifestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DiskUsageManifestError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def run_command(argv: list[str], timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stdout_head": completed.stdout.strip().splitlines()[:80],
    }


def du_sk(path: Path) -> int | None:
    if not path.exists():
        return None
    result = run_command(["du", "-sk", str(path)], timeout=60)
    if result["returncode"] != 0:
        return None
    try:
        return int(result["stdout"].splitlines()[0].split()[0])
    except (ValueError, IndexError):
        return None


def classify_path(path_text: str) -> str:
    normalized = path_text.replace("\\", "/")
    if normalized.startswith(PROTECTED_PREFIXES):
        return "protected_audit_evidence"
    if normalized.startswith("docs/codex_audit/"):
        return "audit_documentation"
    if any(part.startswith(("build-", "build_")) for part in normalized.split("/")):
        return "build_artifact"
    if any(pattern.search(normalized) for pattern in OUTPUT_PATTERNS):
        return "case_output"
    if normalized.startswith("examples/") and normalized.endswith(EXECUTABLE_SUFFIXES):
        return "case_executable"
    if normalized.startswith("test/"):
        return "test_output_or_artifact"
    if normalized.startswith("examples/"):
        return "example_tree"
    return "other"


def retention_policy(category: str) -> str:
    if category == "protected_audit_evidence":
        return "protect_by_default"
    if category in {"case_output", "build_artifact", "test_output_or_artifact"}:
        return "cleanup_candidate_requires_review"
    if category == "case_executable":
        return "rebuildable_but_keep_until_rebuild_recipe_verified"
    return "review_before_cleanup"


def parse_find_size_line(line: str) -> tuple[int, str] | None:
    if "\t" not in line:
        return None
    size_text, path_text = line.split("\t", 1)
    try:
        return int(size_text), path_text.removeprefix("./")
    except ValueError:
        return None


def largest_files(limit: int = 120) -> list[dict[str, Any]]:
    result = run_command(
        ["find", ".", "-xdev", "-type", "f", "-printf", "%s\t%p\n"],
        timeout=120,
    )
    require(result["returncode"] == 0, "largest file scan failed")
    parsed = [item for item in (parse_find_size_line(line) for line in result["stdout"].splitlines()) if item]
    parsed.sort(key=lambda item: item[0], reverse=True)
    entries = []
    for size_bytes, path_text in parsed[:limit]:
        category = classify_path(path_text)
        entries.append(
            {
                "path": path_text,
                "size_bytes": size_bytes,
                "size_mib": round(size_bytes / 1024 / 1024, 2),
                "category": category,
                "retention_policy": retention_policy(category),
            }
        )
    return entries


def top_directories() -> list[dict[str, Any]]:
    roots = set(SCAN_ROOTS)
    for base in [Path("examples/academic"), Path("examples/engineering"), Path("docs/codex_audit/evidence"), Path("test")]:
        if base.is_dir():
            for child in base.iterdir():
                roots.add(child)
    entries = []
    for path in sorted(roots):
        size_kib = du_sk(path)
        if size_kib is None:
            continue
        path_text = path.as_posix()
        category = classify_path(path_text)
        entries.append(
            {
                "path": path_text,
                "size_kib": size_kib,
                "size_mib": round(size_kib / 1024, 2),
                "category": category,
                "retention_policy": retention_policy(category),
            }
        )
    entries.sort(key=lambda item: item["size_kib"], reverse=True)
    return entries[:160]


def summarize(entries: list[dict[str, Any]], size_key: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    for item in entries:
        category = str(item["category"])
        counts[category] += 1
        sizes[category] += int(item[size_key])
    return {
        "counts": dict(sorted(counts.items())),
        "sizes": dict(sorted(sizes.items())),
    }


def build_report() -> dict[str, Any]:
    case_manifest = load_json(CASE_OUTPUT_MANIFEST)
    current_scope = load_json(CURRENT_SCOPE_REPORT)

    directories = top_directories()
    files = largest_files(limit=120)

    repo_size = next((item["size_kib"] for item in directories if item["path"] == "."), None)
    protected_evidence_size = next(
        (item["size_kib"] for item in directories if item["path"] == "docs/codex_audit/evidence"),
        None,
    )

    current_scope_ok = (
        current_scope.get("status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"
        and current_scope.get("summary", {}).get("passed_gate_count") == 15
    )
    case_manifest_ok = (
        case_manifest.get("status") == "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST"
        and case_manifest.get("summary", {}).get("cleanup_performed") is False
    )
    ready = current_scope_ok and case_manifest_ok and repo_size is not None and len(files) > 0

    cleanup_candidate_file_size = sum(
        item["size_bytes"]
        for item in files
        if item["retention_policy"] == "cleanup_candidate_requires_review"
    )
    protected_file_size = sum(
        item["size_bytes"]
        for item in files
        if item["retention_policy"] == "protect_by_default"
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_AUDITED if ready else STATUS_NOT_READY,
        "summary": {
            "disk_usage_manifest_audited": ready,
            "cleanup_performed": False,
            "cleanup_policy": "dry-run manifest only; no files are deleted, restored, staged, or ignored",
            "repo_size_kib": repo_size,
            "protected_evidence_size_kib": protected_evidence_size,
            "top_directory_count": len(directories),
            "largest_file_count": len(files),
            "cleanup_candidate_largest_file_size_bytes": cleanup_candidate_file_size,
            "protected_largest_file_size_bytes": protected_file_size,
            "case_output_cleanup_manifest_status": case_manifest.get("status"),
            "current_scope_status": current_scope.get("status"),
            "current_scope_passed_gate_count": current_scope.get("summary", {}).get("passed_gate_count"),
        },
        "directory_summary": summarize(directories, "size_kib"),
        "file_summary": summarize(files, "size_bytes"),
        "top_directories": directories,
        "largest_files": files,
        "recommendations": [
            "Do not delete protected audit evidence without first exporting or replacing the evidence chain.",
            "Case-output, build, and test artifacts are cleanup candidates only after required logs, reports, and rebuild commands are preserved.",
            "The largest current space users are plotfiles and build/test artifacts, not the small git-tracked old-output cleanup candidates.",
        ],
        "evidence_files": [
            evidence_entry("current_case_output_cleanup_manifest_report", CASE_OUTPUT_MANIFEST),
            evidence_entry("current_scope_verification_report", CURRENT_SCOPE_REPORT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_AUDITED, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("disk_usage_manifest_audited") is True, "disk usage manifest was not audited")
    require(summary.get("cleanup_performed") is False, "disk usage manifest must be non-destructive")
    require(summary.get("repo_size_kib", 0) > 0, "repo size was not recorded")
    require(summary.get("top_directory_count", 0) > 0, "top directory list is empty")
    require(summary.get("largest_file_count", 0) > 0, "largest file list is empty")
    require(summary.get("case_output_cleanup_manifest_status") == "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST", "case-output cleanup manifest is not passing")
    require(summary.get("current_scope_status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION", "current-scope report is not passing")
    require(summary.get("current_scope_passed_gate_count") == 15, "not all current-scope gates passed")
    for item in data.get("top_directories", []):
        require(item.get("retention_policy") in {"protect_by_default", "cleanup_candidate_requires_review", "rebuildable_but_keep_until_rebuild_recipe_verified", "review_before_cleanup"}, "invalid retention policy")
    for item in data.get("largest_files", []):
        require(item.get("retention_policy") in {"protect_by_default", "cleanup_candidate_requires_review", "rebuildable_but_keep_until_rebuild_recipe_verified", "review_before_cleanup"}, "invalid file retention policy")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Disk Usage Manifest",
        "",
        f"- Status: `{report['status']}`",
        f"- Repo size KiB: `{summary['repo_size_kib']}`",
        f"- Protected evidence size KiB: `{summary['protected_evidence_size_kib']}`",
        f"- Top directories recorded: `{summary['top_directory_count']}`",
        f"- Largest files recorded: `{summary['largest_file_count']}`",
        f"- Cleanup performed: `{summary['cleanup_performed']}`",
        "",
        "## Largest Directories",
        "",
    ]
    for item in report["top_directories"][:40]:
        lines.append(
            f"- `{item['path']}` size_mib=`{item['size_mib']}` policy=`{item['retention_policy']}`"
        )
    lines.extend(["", "## Largest Files", ""])
    for item in report["largest_files"][:40]:
        lines.append(
            f"- `{item['path']}` size_mib=`{item['size_mib']}` policy=`{item['retention_policy']}`"
        )
    lines.extend(["", "## Recommendations", ""])
    for item in report["recommendations"]:
        lines.append(f"- {item}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_disk_usage_manifest VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_disk_usage_manifest PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
