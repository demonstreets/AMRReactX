#!/usr/bin/env python3
"""Write/verify a source/tooling ledger for the current dirty worktree."""

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
STATUS_AUDITED = "AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER"
STATUS_NOT_READY = "NOT_READY-CURRENT-WORKTREE-SOURCE-LEDGER"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_worktree_source_ledger_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_worktree_source_ledger_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_worktree_source_ledger_report.md"

HYGIENE_REPORT = Path(
    "docs/codex_audit/evidence/current_worktree_hygiene_20260803/"
    "current_worktree_hygiene_report.json"
)
CURRENT_SCOPE_REPORT = Path(
    "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
    "master_plan_current_scope_verification_report.json"
)

GENERATED_COMPONENT_PATTERNS = [
    re.compile(r"^chk\d", re.IGNORECASE),
    re.compile(r"^plt\d", re.IGNORECASE),
    re.compile(r"^plotfile", re.IGNORECASE),
    re.compile(r"^Level_\d+$"),
    re.compile(r"^particles$"),
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
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".H",
    ".hpp",
    ".hh",
    ".py",
    ".sh",
    ".f",
    ".f90",
    ".F90",
    ".mk",
}
CONFIG_NAMES = {"inputs", "GNUmakefile", "CMakeLists.txt", "Make.package"}
DOC_SUFFIXES = {".md", ".rst", ".txt"}

LEDGER_CATEGORIES = {
    "source_or_config",
    "example_source_or_config",
    "tooling",
    "documentation",
    "audit_evidence",
    "upstream_or_submodule",
    "other",
}


class SourceLedgerError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceLedgerError(message)


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
        raise SourceLedgerError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceLedgerError(f"invalid JSON evidence {path}: {exc}") from exc
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
        entries.append(
            {
                "xy": status,
                "index": status[0],
                "worktree": status[1],
                "path": path_text,
                "old_path": old_path,
            }
        )
        i += 1
    return entries


def is_generated_or_output(path_text: str) -> bool:
    path = Path(path_text)
    for part in path.parts:
        if any(pattern.search(part) for pattern in GENERATED_COMPONENT_PATTERNS):
            return True
    return any(pattern.search(path.name) for pattern in GENERATED_NAME_PATTERNS)


def classify_path(path_text: str) -> str:
    path = Path(path_text)
    first = path.parts[0] if path.parts else ""
    if is_generated_or_output(path_text):
        return "generated_or_case_output"
    if first == "docs" and len(path.parts) > 2 and path.parts[1] == "codex_audit" and path.parts[2] == "evidence":
        return "audit_evidence"
    if first == "tools":
        return "tooling"
    if first == "docs" or path.name in {"README.md", "PROGRESS.md", "AGENTS.md"} or path.suffix in DOC_SUFFIXES:
        return "documentation"
    if first == "examples" and (path.name in CONFIG_NAMES or path.suffix in SOURCE_SUFFIXES):
        return "example_source_or_config"
    if path.suffix in SOURCE_SUFFIXES or path.name in CONFIG_NAMES:
        return "source_or_config"
    if first in {"Submodules", "PeleC", "PeleLMeX"}:
        return "upstream_or_submodule"
    return "other"


def diff_numstat() -> dict[str, dict[str, int | None]]:
    stats: dict[str, dict[str, int | None]] = {}
    for argv in (["git", "diff", "--numstat"], ["git", "diff", "--cached", "--numstat"]):
        result = run_command(argv, timeout=60)
        if result["returncode"] != 0:
            continue
        for line in result["stdout"].splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            added, deleted, path_text = parts[0], parts[1], parts[2]
            item = stats.setdefault(path_text, {"added": 0, "deleted": 0})
            if added == "-" or deleted == "-":
                item["added"] = None
                item["deleted"] = None
            elif item["added"] is not None and item["deleted"] is not None:
                item["added"] += int(added)
                item["deleted"] += int(deleted)
    return stats


def file_entry(entry: dict[str, str], category: str, numstat: dict[str, dict[str, int | None]]) -> dict[str, Any]:
    path = Path(entry["path"])
    exists = path.exists()
    is_file = path.is_file()
    item: dict[str, Any] = {
        "xy": entry["xy"],
        "path": entry["path"],
        "old_path": entry["old_path"],
        "category": category,
        "exists": exists,
        "is_file": is_file,
        "size_bytes": path.stat().st_size if is_file else None,
        "sha256": sha256_file(path) if is_file else None,
        "diff_numstat": numstat.get(entry["path"]),
    }
    return item


def build_report() -> dict[str, Any]:
    hygiene = load_json(HYGIENE_REPORT)
    current_scope = load_json(CURRENT_SCOPE_REPORT)

    git_status = run_command(["git", "status", "--porcelain=v1", "-z"])
    git_head = run_command(["git", "rev-parse", "HEAD"])
    require(git_status["returncode"] == 0, "git status failed")

    entries = parse_porcelain_z(git_status["stdout"])
    numstat = diff_numstat()
    ledger_entries: list[dict[str, Any]] = []
    generated_or_case_output_count = 0
    category_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    for entry in entries:
        category = classify_path(entry["path"])
        if category == "generated_or_case_output":
            generated_or_case_output_count += 1
            continue
        if category not in LEDGER_CATEGORIES:
            continue
        item = file_entry(entry, category, numstat)
        ledger_entries.append(item)
        category_counts[category] += 1
        status_counts[entry["xy"]] += 1

    high_attention = [
        item
        for item in ledger_entries
        if item["category"] in {"source_or_config", "example_source_or_config", "upstream_or_submodule", "other"}
        or "D" in item["xy"]
    ]

    hygiene_ok = (
        hygiene.get("status") == "AUDITED-CURRENT-WORKTREE-HYGIENE"
        and hygiene.get("summary", {}).get("cleanup_performed") is False
    )
    current_scope_ok = (
        current_scope.get("status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"
        and current_scope.get("summary", {}).get("passed_gate_count") == 15
    )
    ready = hygiene_ok and current_scope_ok and git_head["returncode"] == 0

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_AUDITED if ready else STATUS_NOT_READY,
        "summary": {
            "worktree_source_ledger_audited": ready,
            "ledger_entry_count": len(ledger_entries),
            "generated_or_case_output_excluded_count": generated_or_case_output_count,
            "high_attention_ledger_entry_count": len(high_attention),
            "category_counts": dict(sorted(category_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "hygiene_status": hygiene.get("status"),
            "hygiene_dirty_entry_count": hygiene.get("summary", {}).get("dirty_entry_count"),
            "hygiene_generated_or_case_output_entry_count": hygiene.get("summary", {}).get("generated_or_case_output_entry_count"),
            "current_scope_status": current_scope.get("status"),
            "current_scope_passed_gate_count": current_scope.get("summary", {}).get("passed_gate_count"),
            "cleanup_performed": False,
            "ledger_policy": "audit-only; generated/case-output entries are excluded from the source ledger and no files are modified",
        },
        "git": {
            "head": git_head["stdout"].strip() if git_head["returncode"] == 0 else None,
        },
        "ledger_entries": ledger_entries,
        "high_attention_entries": high_attention,
        "evidence_files": [
            evidence_entry("current_worktree_hygiene_report", HYGIENE_REPORT),
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
    require(summary.get("worktree_source_ledger_audited") is True, "worktree source ledger was not audited")
    require(isinstance(summary.get("ledger_entry_count"), int), "ledger_entry_count is not an int")
    require(summary.get("ledger_entry_count") > 0, "source ledger is unexpectedly empty")
    require(summary.get("cleanup_performed") is False, "source ledger must be non-destructive")
    require(summary.get("hygiene_status") == "AUDITED-CURRENT-WORKTREE-HYGIENE", "worktree hygiene audit is not passing")
    require(summary.get("current_scope_status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION", "current-scope report is not passing")
    require(summary.get("current_scope_passed_gate_count") == 15, "not all current-scope gates passed")
    require(len(data.get("ledger_entries", [])) == summary.get("ledger_entry_count"), "ledger entry count mismatch")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Worktree Source Ledger",
        "",
        f"- Status: `{report['status']}`",
        f"- Ledger entries: `{summary['ledger_entry_count']}`",
        f"- Generated/case-output entries excluded: `{summary['generated_or_case_output_excluded_count']}`",
        f"- High-attention ledger entries: `{summary['high_attention_ledger_entry_count']}`",
        f"- Cleanup performed: `{summary['cleanup_performed']}`",
        f"- Hygiene status: `{summary['hygiene_status']}`",
        f"- Current-scope status: `{summary['current_scope_status']}`",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in summary["category_counts"].items():
        lines.append(f"- `{category}`: `{count}`")
    lines.extend(["", "## High-Attention Sample", ""])
    for item in report["high_attention_entries"][:40]:
        lines.append(f"- `{item['xy']}` `{item['category']}` `{item['path']}`")
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
        print(f"current_worktree_source_ledger VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_worktree_source_ledger PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
