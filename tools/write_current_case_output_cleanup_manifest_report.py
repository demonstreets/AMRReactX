#!/usr/bin/env python3
"""Write/verify a dry-run cleanup manifest for generated CFD case outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_AUDITED = "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST"
STATUS_NOT_READY = "NOT_READY-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_case_output_cleanup_manifest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_case_output_cleanup_manifest_report.md"

HYGIENE_REPORT = Path(
    "docs/codex_audit/evidence/current_worktree_hygiene_20260803/"
    "current_worktree_hygiene_report.json"
)
SOURCE_LEDGER_REPORT = Path(
    "docs/codex_audit/evidence/current_worktree_source_ledger_20260803/"
    "current_worktree_source_ledger_report.json"
)

GENERATED_COMPONENT_PATTERNS = [
    re.compile(r"^chk\d", re.IGNORECASE),
    re.compile(r"^plt\d", re.IGNORECASE),
    re.compile(r"^plotfile", re.IGNORECASE),
]
GENERATED_NAME_PATTERNS = [
    re.compile(r"\.old\.", re.IGNORECASE),
    re.compile(r"^AMReX_buildInfo\.cpp$"),
    re.compile(r"^CPUtime$"),
    re.compile(r"^EBMaxLevel$"),
    re.compile(r"^FabArrayHeaders\.txt$"),
    re.compile(r"^PeleCHeader$"),
    re.compile(r"^PeleLMeX_job_info$"),
    re.compile(r"^Header$"),
    re.compile(r"^[A-Za-z0-9_]+_D_\d+$"),
    re.compile(r"^[A-Za-z0-9_]+_H$"),
]
PROTECTED_PREFIXES = (
    "docs/codex_audit/evidence/",
    "docs/codex_audit/",
    "tools/",
)


class CleanupManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CleanupManifestError(message)


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
        raise CleanupManifestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CleanupManifestError(f"invalid JSON evidence {path}: {exc}") from exc
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


def run_command(argv: list[str], timeout: int = 60) -> dict[str, Any]:
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
        "stdout_head": completed.stdout.replace("\0", "\n").strip().splitlines()[:80],
    }


def parse_porcelain_z(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    items = [item for item in text.split("\0") if item]
    i = 0
    while i < len(items):
        raw = items[i]
        status = raw[:2]
        path_text = raw[3:] if len(raw) > 3 else ""
        old_path = ""
        if "R" in status or "C" in status:
            if i + 1 < len(items):
                old_path = items[i + 1]
                i += 1
        entries.append({"xy": status, "path": path_text, "old_path": old_path})
        i += 1
    return entries


def is_generated_or_output(path_text: str) -> bool:
    path = Path(path_text)
    for part in path.parts:
        if any(pattern.search(part) for pattern in GENERATED_COMPONENT_PATTERNS):
            return True
    return any(pattern.search(path.name) for pattern in GENERATED_NAME_PATTERNS)


def is_protected(path_text: str) -> bool:
    normalized = path_text.replace("\\", "/")
    return normalized.startswith(PROTECTED_PREFIXES)


def candidate_root(path_text: str) -> tuple[str, str]:
    path = Path(path_text)
    parts = path.parts
    for idx, part in enumerate(parts):
        if any(pattern.search(part) for pattern in GENERATED_COMPONENT_PATTERNS):
            return str(Path(*parts[: idx + 1])), "case_output_directory"
        if ".old." in part:
            return str(Path(*parts[: idx + 1])), "old_case_output_directory"
    if path.name == "AMReX_buildInfo.cpp":
        return str(path), "generated_build_metadata_file"
    if any(pattern.search(path.name) for pattern in GENERATED_NAME_PATTERNS):
        parent = str(path.parent) if str(path.parent) != "." else str(path)
        return parent, "generated_case_metadata_group"
    return str(path), "generated_or_case_output"


def du_sk(path: Path) -> int | None:
    if not path.exists():
        return None
    result = run_command(["du", "-sk", str(path)], timeout=30)
    if result["returncode"] != 0:
        return None
    first = result["stdout"].splitlines()[0].split()[0]
    try:
        return int(first)
    except (ValueError, IndexError):
        return None


def file_count(path: Path) -> int | None:
    if not path.exists():
        return None
    if path.is_file():
        return 1
    result = run_command(["find", str(path), "-type", "f"], timeout=30)
    if result["returncode"] != 0:
        return None
    return len([line for line in result["stdout"].splitlines() if line])


def build_report() -> dict[str, Any]:
    hygiene = load_json(HYGIENE_REPORT)
    source_ledger = load_json(SOURCE_LEDGER_REPORT)
    git_status = run_command(["git", "status", "--porcelain=v1", "-z"])
    git_head = run_command(["git", "rev-parse", "HEAD"])
    require(git_status["returncode"] == 0, "git status failed")

    entries = parse_porcelain_z(git_status["stdout"])
    grouped: dict[str, dict[str, Any]] = {}
    generated_entry_count = 0
    protected_generated_count = 0
    status_counts: Counter[str] = Counter()

    for entry in entries:
        path_text = entry["path"]
        if not is_generated_or_output(path_text):
            continue
        generated_entry_count += 1
        if is_protected(path_text):
            protected_generated_count += 1
            continue
        root, kind = candidate_root(path_text)
        item = grouped.setdefault(
            root,
            {
                "root": root,
                "kind": kind,
                "git_status_counts": Counter(),
                "sample_paths": [],
            },
        )
        item["git_status_counts"][entry["xy"]] += 1
        status_counts[entry["xy"]] += 1
        if len(item["sample_paths"]) < 12:
            item["sample_paths"].append({"xy": entry["xy"], "path": path_text})

    candidates = []
    existing_count = 0
    already_missing_count = 0
    total_existing_size_kib = 0
    for root, item in sorted(grouped.items()):
        path = Path(root)
        exists = path.exists()
        if exists:
            existing_count += 1
        else:
            already_missing_count += 1
        size_kib = du_sk(path)
        if size_kib is not None:
            total_existing_size_kib += size_kib
        candidate = {
            "root": root,
            "kind": item["kind"],
            "exists": exists,
            "is_dir": path.is_dir(),
            "is_file": path.is_file(),
            "size_kib": size_kib,
            "file_count": file_count(path),
            "git_status_counts": dict(sorted(item["git_status_counts"].items())),
            "sample_paths": item["sample_paths"],
            "cleanup_action": "no_action_dry_run",
            "cleanup_requires_explicit_user_approval": True,
        }
        candidates.append(candidate)

    hygiene_ok = (
        hygiene.get("status") == "AUDITED-CURRENT-WORKTREE-HYGIENE"
        and hygiene.get("summary", {}).get("cleanup_performed") is False
        and hygiene.get("summary", {}).get("generated_or_case_output_entry_count") == generated_entry_count
    )
    ledger_ok = (
        source_ledger.get("status") == "AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER"
        and source_ledger.get("summary", {}).get("cleanup_performed") is False
    )
    ready = hygiene_ok and ledger_ok and git_head["returncode"] == 0 and protected_generated_count == 0

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_AUDITED if ready else STATUS_NOT_READY,
        "summary": {
            "case_output_cleanup_manifest_audited": ready,
            "cleanup_performed": False,
            "cleanup_policy": "dry-run manifest only; no files are deleted, restored, staged, or ignored",
            "generated_or_case_output_git_entry_count": generated_entry_count,
            "protected_generated_entry_count": protected_generated_count,
            "cleanup_candidate_root_count": len(candidates),
            "existing_candidate_root_count": existing_count,
            "already_missing_candidate_root_count": already_missing_count,
            "total_existing_candidate_size_kib": total_existing_size_kib,
            "hygiene_status": hygiene.get("status"),
            "source_ledger_status": source_ledger.get("status"),
            "git_status_counts": dict(sorted(status_counts.items())),
        },
        "git": {
            "head": git_head["stdout"].strip() if git_head["returncode"] == 0 else None,
        },
        "cleanup_candidates": candidates,
        "recommendations": [
            "Review this manifest before any disk cleanup; it is not itself a cleanup command.",
            "Already-missing roots usually represent previous removal of generated outputs and should be reconciled separately from source changes.",
            "Existing roots may be cleanup candidates only after required evidence reports, logs, and plotfiles have been preserved.",
        ],
        "evidence_files": [
            evidence_entry("current_worktree_hygiene_report", HYGIENE_REPORT),
            evidence_entry("current_worktree_source_ledger_report", SOURCE_LEDGER_REPORT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_AUDITED, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("case_output_cleanup_manifest_audited") is True, "cleanup manifest was not audited")
    require(summary.get("cleanup_performed") is False, "cleanup manifest must be non-destructive")
    require(summary.get("protected_generated_entry_count") == 0, "protected evidence/tool paths were classified as cleanup candidates")
    require(summary.get("generated_or_case_output_git_entry_count", 0) > 0, "generated/case-output entry count is unexpectedly empty")
    require(summary.get("cleanup_candidate_root_count") > 0, "cleanup candidate list is unexpectedly empty")
    require(summary.get("hygiene_status") == "AUDITED-CURRENT-WORKTREE-HYGIENE", "hygiene audit is not passing")
    require(summary.get("source_ledger_status") == "AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER", "source ledger is not passing")
    for candidate in data.get("cleanup_candidates", []):
        require(candidate.get("cleanup_action") == "no_action_dry_run", "cleanup candidate is not marked dry-run")
        require(candidate.get("cleanup_requires_explicit_user_approval") is True, "cleanup candidate does not require explicit approval")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Case-Output Cleanup Manifest",
        "",
        f"- Status: `{report['status']}`",
        f"- Generated/case-output git entries: `{summary['generated_or_case_output_git_entry_count']}`",
        f"- Cleanup candidate roots: `{summary['cleanup_candidate_root_count']}`",
        f"- Existing candidate roots: `{summary['existing_candidate_root_count']}`",
        f"- Already-missing candidate roots: `{summary['already_missing_candidate_root_count']}`",
        f"- Existing candidate size KiB: `{summary['total_existing_candidate_size_kib']}`",
        f"- Cleanup performed: `{summary['cleanup_performed']}`",
        "",
        "## Candidate Sample",
        "",
    ]
    for item in report["cleanup_candidates"][:60]:
        lines.append(
            f"- `{item['root']}` kind=`{item['kind']}` exists=`{item['exists']}` size_kib=`{item['size_kib']}`"
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
        print(f"current_case_output_cleanup_manifest VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_case_output_cleanup_manifest PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
