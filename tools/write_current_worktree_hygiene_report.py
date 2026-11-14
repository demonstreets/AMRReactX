#!/usr/bin/env python3
"""Write/verify a non-destructive current worktree hygiene audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_AUDITED = "AUDITED-CURRENT-WORKTREE-HYGIENE"
STATUS_NOT_READY = "NOT_READY-CURRENT-WORKTREE-HYGIENE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_worktree_hygiene_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_worktree_hygiene_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_worktree_hygiene_report.md"

CURRENT_SCOPE_REPORT = Path(
    "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
    "master_plan_current_scope_verification_report.json"
)
COMPLETION_AUDIT_REPORT = Path(
    "docs/codex_audit/evidence/master_plan_completion_audit_20260803/"
    "master_plan_completion_audit_report.json"
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


class WorktreeHygieneError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WorktreeHygieneError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorktreeHygieneError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorktreeHygieneError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def run_command(argv: list[str], timeout: int = 60) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    output_head = completed.stdout.replace("\0", "\n").strip().splitlines()[:120]
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stdout_head": output_head,
    }


def parse_porcelain(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for raw in text.splitlines():
        if not raw:
            continue
        status = raw[:2]
        path_text = raw[3:] if len(raw) > 3 else ""
        old_path = ""
        new_path = path_text
        if " -> " in path_text:
            old_path, new_path = path_text.split(" -> ", 1)
        entries.append(
            {
                "xy": status,
                "index": status[0],
                "worktree": status[1],
                "path": new_path,
                "old_path": old_path,
            }
        )
    return entries


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
    parts = path.parts
    for part in parts:
        if any(pattern.search(part) for pattern in GENERATED_COMPONENT_PATTERNS):
            return True
    name = path.name
    return any(pattern.search(name) for pattern in GENERATED_NAME_PATTERNS)


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


def high_attention(entry: dict[str, str], category: str) -> bool:
    if entry["xy"] == "??":
        return category in {"source_or_config", "example_source_or_config", "upstream_or_submodule"}
    if "D" in entry["xy"] and category not in {"generated_or_case_output", "audit_evidence"}:
        return True
    if category in {"source_or_config", "example_source_or_config", "upstream_or_submodule"}:
        return True
    return False


def disk_usage(path: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["du", "-sh", path],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        return {
            "path": path,
            "returncode": completed.returncode,
            "output": completed.stdout.strip(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"path": path, "returncode": None, "output": type(exc).__name__}


def build_report() -> dict[str, Any]:
    current_scope = load_json(CURRENT_SCOPE_REPORT)
    completion = load_json(COMPLETION_AUDIT_REPORT)
    git_status = run_command(["git", "status", "--porcelain=v1", "-z"])
    git_head = run_command(["git", "rev-parse", "HEAD"])
    require(git_status["returncode"] == 0, "git status failed")

    entries = parse_porcelain_z(git_status["stdout"])
    category_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    path_prefix_counts: Counter[str] = Counter()
    high_attention_entries = []
    samples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for entry in entries:
        category = classify_path(entry["path"])
        category_counts[category] += 1
        status_counts[entry["xy"]] += 1
        prefix = Path(entry["path"]).parts[0] if Path(entry["path"]).parts else "."
        path_prefix_counts[prefix] += 1
        item = {"xy": entry["xy"], "path": entry["path"], "category": category}
        if len(samples[category]) < 20:
            samples[category].append(item)
        if high_attention(entry, category) and len(high_attention_entries) < 80:
            high_attention_entries.append(item)

    generated_or_case_output_count = category_counts.get("generated_or_case_output", 0)
    high_attention_total = sum(
        1 for entry in entries if high_attention(entry, classify_path(entry["path"]))
    )
    deleted_generated_count = sum(
        1
        for entry in entries
        if "D" in entry["xy"] and classify_path(entry["path"]) == "generated_or_case_output"
    )

    current_scope_ok = (
        current_scope.get("status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"
        and current_scope.get("summary", {}).get("passed_gate_count") == 15
        and current_scope.get("summary", {}).get("gate_count") == 15
    )
    completion_boundary_ok = (
        completion.get("status") == "AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE"
        and completion.get("summary", {}).get("goal_complete") is False
    )

    ready = current_scope_ok and completion_boundary_ok and git_head["returncode"] == 0

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_AUDITED if ready else STATUS_NOT_READY,
        "summary": {
            "worktree_hygiene_audited": ready,
            "dirty_entry_count": len(entries),
            "generated_or_case_output_entry_count": generated_or_case_output_count,
            "deleted_generated_or_case_output_entry_count": deleted_generated_count,
            "high_attention_entry_count": high_attention_total,
            "category_count": len(category_counts),
            "current_scope_status": current_scope.get("status"),
            "current_scope_gate_count": current_scope.get("summary", {}).get("gate_count"),
            "current_scope_passed_gate_count": current_scope.get("summary", {}).get("passed_gate_count"),
            "completion_audit_status": completion.get("status"),
            "goal_complete": completion.get("summary", {}).get("goal_complete"),
            "cleanup_performed": False,
            "cleanup_policy": "audit-only; no files are deleted, restored, staged, or ignored by this report",
        },
        "git": {
            "head": git_head["stdout"].strip() if git_head["returncode"] == 0 else None,
            "status_counts": dict(sorted(status_counts.items())),
            "category_counts": dict(sorted(category_counts.items())),
            "top_level_prefix_counts": dict(path_prefix_counts.most_common(30)),
            "high_attention_samples": high_attention_entries,
            "samples_by_category": dict(samples),
        },
        "disk_usage": {
            ".": disk_usage("."),
            "docs": disk_usage("docs"),
            "examples": disk_usage("examples"),
            "tools": disk_usage("tools"),
        },
        "recommendations": [
            "Do not run destructive cleanup from automation while the worktree carries user and audit changes.",
            "Treat generated_or_case_output entries as cleanup candidates only after preserving required evidence reports and logs.",
            "Review high_attention_samples before staging, reverting, or packaging source/config changes.",
        ],
        "evidence_files": [
            evidence_entry("current_scope_verification_report", CURRENT_SCOPE_REPORT),
            evidence_entry("master_plan_completion_audit_report", COMPLETION_AUDIT_REPORT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_AUDITED, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("worktree_hygiene_audited") is True, "worktree hygiene was not audited")
    require(isinstance(summary.get("dirty_entry_count"), int), "dirty_entry_count is not an int")
    require(summary.get("cleanup_performed") is False, "hygiene audit must be non-destructive")
    require(summary.get("current_scope_status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION", "current-scope report is not passing")
    require(summary.get("current_scope_gate_count") == 15, "unexpected current-scope gate count")
    require(summary.get("current_scope_passed_gate_count") == 15, "not all current-scope gates passed")
    require(summary.get("completion_audit_status") == "AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE", "completion audit boundary changed")
    require(summary.get("goal_complete") is False, "goal completion boundary changed unexpectedly")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Worktree Hygiene Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Dirty entries: `{summary['dirty_entry_count']}`",
        f"- Generated/case-output entries: `{summary['generated_or_case_output_entry_count']}`",
        f"- Deleted generated/case-output entries: `{summary['deleted_generated_or_case_output_entry_count']}`",
        f"- High-attention entries: `{summary['high_attention_entry_count']}`",
        f"- Cleanup performed: `{summary['cleanup_performed']}`",
        f"- Current-scope gates: `{summary['current_scope_passed_gate_count']}/{summary['current_scope_gate_count']}`",
        f"- Completion audit: `{summary['completion_audit_status']}`",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in report["git"]["category_counts"].items():
        lines.append(f"- `{category}`: `{count}`")
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
        print(f"current_worktree_hygiene VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_worktree_hygiene PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
