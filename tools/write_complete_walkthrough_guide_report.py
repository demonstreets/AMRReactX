#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


REPO = Path.cwd().resolve()
DOCS = REPO / "docs" / "user_guides"
OUT_DIR = REPO / "docs" / "codex_audit" / "evidence" / "complete_walkthrough_guide_20260818"
STATUS_PASS = "PASS-COMPLETE-WALKTHROUGH-GUIDE"

FILES = {
    "index": DOCS / "README.md",
    "complete_walkthrough": DOCS / "从目录到排错_完整运行教程.md",
}

REQUIRED_PATTERNS = {
    "index_links_complete_walkthrough": (FILES["index"], "从目录到排错_完整运行教程.md"),
    "directory_section": (FILES["complete_walkthrough"], "## 1. 目录怎么看"),
    "input_section": (FILES["complete_walkthrough"], "## 2. 输入文件怎么写"),
    "engineering_section": (FILES["complete_walkthrough"], "## 3. 工程泄漏/火灾怎么跑"),
    "academic_section": (FILES["complete_walkthrough"], "## 4. 学术爆轰怎么跑"),
    "parallel_section": (FILES["complete_walkthrough"], "## 5. CPU/GPU/MPI 怎么运行"),
    "output_section": (FILES["complete_walkthrough"], "## 6. 输出怎么看"),
    "troubleshooting_section": (FILES["complete_walkthrough"], "## 7. 常见错误怎么查"),
    "case_output_cleanup_section": (
        FILES["complete_walkthrough"],
        "### 7.8 工作区污染和算例输出清理",
    ),
    "engineering_mpi_command": (
        FILES["complete_walkthrough"],
        "MPI_RANKS=2 bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh",
    ),
    "engineering_cuda_fire_command": (
        FILES["complete_walkthrough"],
        "CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh",
    ),
    "academic_cuda_command": (
        FILES["complete_walkthrough"],
        "CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_academic_pelec_cuda.sh",
    ),
    "current_scope_command": (
        FILES["complete_walkthrough"],
        "bash tools/run_current_scope_release_refresh.sh",
    ),
    "source_ledger_command": (
        FILES["complete_walkthrough"],
        "python3 tools/write_current_worktree_source_ledger_report.py",
    ),
    "case_output_cleanup_manifest_command": (
        FILES["complete_walkthrough"],
        "python3 tools/write_current_case_output_cleanup_manifest_report.py",
    ),
    "real_case_boundary_statement": (
        FILES["complete_walkthrough"],
        "真实 CAD、真实边界条件和外部标定数据",
    ),
}

COMMAND_REF_RE = re.compile(
    r"(?:^|\s)(?:[A-Z_][A-Z0-9_]*=[^\s]+(?:\s+|$))*"
    r"(bash|python3)\s+(tools/[A-Za-z0-9_./-]+)",
    re.MULTILINE,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def command_references(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    refs = []
    seen = set()
    for match in COMMAND_REF_RE.finditer(text):
        runner = match.group(1)
        rel = match.group(2).rstrip("`)")
        key = (runner, rel)
        if key in seen:
            continue
        seen.add(key)
        target = REPO / rel
        entry = {
            "runner": runner,
            "path": rel,
            "exists": target.is_file(),
        }
        if target.is_file():
            entry["sha256"] = sha256(target)
            entry["bytes"] = target.stat().st_size
        refs.append(entry)
    return refs


class CompleteWalkthroughGuideError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CompleteWalkthroughGuideError(message)


def syntax_check_targets(command_refs: list[dict[str, object]]) -> list[dict[str, object]]:
    checks = []
    seen = set()
    for item in command_refs:
        runner = str(item["runner"])
        command_path = str(item["path"])
        key = (runner, command_path)
        if key in seen:
            continue
        seen.add(key)
        target = REPO / command_path
        if not target.is_file():
            checks.append(
                {
                    "runner": runner,
                    "path": command_path,
                    "checked": False,
                    "pass": False,
                    "reason": "missing target",
                }
            )
            continue
        if runner == "bash":
            cmd = ["bash", "-n", command_path]
        elif runner == "python3":
            cmd = [sys.executable, "-m", "py_compile", command_path]
        else:
            checks.append(
                {
                    "runner": runner,
                    "path": command_path,
                    "checked": False,
                    "pass": False,
                    "reason": f"unsupported runner {runner}",
                }
            )
            continue
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        checks.append(
            {
                "runner": runner,
                "path": command_path,
                "checked": True,
                "pass": proc.returncode == 0,
                "returncode": proc.returncode,
                "stderr_excerpt": proc.stderr.strip()[:500],
            }
        )
    return checks


def build_report() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    docs = {}
    failures = []

    for name, path in FILES.items():
        rel = path.relative_to(REPO).as_posix()
        exists = path.is_file()
        entry = {"path": rel, "exists": exists}
        if exists:
            entry["sha256"] = sha256(path)
            entry["bytes"] = path.stat().st_size
        else:
            failures.append(f"missing {rel}")
        docs[name] = entry

    checks = {}
    for name, (path, pattern) in REQUIRED_PATTERNS.items():
        ok = path.is_file() and pattern in path.read_text(encoding="utf-8")
        checks[name] = {
            "path": path.relative_to(REPO).as_posix(),
            "pattern": pattern,
            "pass": ok,
        }
        if not ok:
            failures.append(f"missing pattern {name}")

    commands = command_references(FILES["complete_walkthrough"])
    if len(commands) < 20:
        failures.append(f"too few command references discovered: {len(commands)}")
    for command in commands:
        if not command["exists"]:
            failures.append(f"missing documented command target: {command['path']}")

    syntax_checks = syntax_check_targets(commands)
    failed_syntax_checks = [item for item in syntax_checks if not item["pass"]]
    for item in failed_syntax_checks:
        failures.append(f"documented command syntax check failed: {item['runner']} {item['path']}")

    status = STATUS_PASS if not failures else "FAIL-COMPLETE-WALKTHROUGH-GUIDE"
    return {
        "status": status,
        "documents": docs,
        "checks": checks,
        "command_references": commands,
        "summary": {
            "documented_command_reference_count": len(commands),
            "missing_documented_command_reference_count": sum(1 for item in commands if not item["exists"]),
            "unique_documented_command_target_count": len(syntax_checks),
            "documented_command_syntax_failure_count": len(failed_syntax_checks),
        },
        "command_syntax_checks": syntax_checks,
        "failures": failures,
    }


def validate_report(report: dict[str, object], verify_hashes: bool = True) -> None:
    require(report.get("status") == STATUS_PASS, "invalid status")
    require(report.get("failures") == [], "report contains failures")
    summary = report.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(int(summary.get("documented_command_reference_count", 0)) >= 20, "too few command references")
    require(summary.get("missing_documented_command_reference_count") == 0, "missing command references")
    require(summary.get("documented_command_syntax_failure_count") == 0, "syntax failures recorded")

    documents = report.get("documents")
    require(isinstance(documents, dict), "missing documents")
    for name, path in FILES.items():
        entry = documents.get(name)
        require(isinstance(entry, dict), f"missing document entry {name}")
        require(path.is_file(), f"missing document on disk: {path}")
        if verify_hashes:
            require(entry.get("sha256") == sha256(path), f"document hash mismatch: {path}")

    checks = report.get("checks")
    require(isinstance(checks, dict), "missing checks")
    for name in REQUIRED_PATTERNS:
        entry = checks.get(name)
        require(isinstance(entry, dict) and entry.get("pass") is True, f"required pattern failed: {name}")

    command_refs = report.get("command_references")
    require(isinstance(command_refs, list), "missing command references")
    for item in command_refs:
        require(isinstance(item, dict), "invalid command reference entry")
        path = REPO / str(item.get("path", ""))
        require(path.is_file(), f"missing documented command target: {path}")
        if verify_hashes and "sha256" in item:
            require(item.get("sha256") == sha256(path), f"command target hash mismatch: {path}")

    syntax_checks = syntax_check_targets(command_refs)
    failed = [item for item in syntax_checks if not item["pass"]]
    require(not failed, f"documented command syntax checks failed: {failed[:3]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write/verify the complete Chinese walkthrough guide report.")
    parser.add_argument("--verify-json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify_json:
        data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
        validate_report(data, verify_hashes=True)
        print(f"complete_walkthrough_guide VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    validate_report(report, verify_hashes=False)
    status = str(report["status"])
    docs = report["documents"]
    checks = report["checks"]
    commands = report["command_references"]
    syntax_checks = report["command_syntax_checks"]
    failures = report["failures"]

    json_path = OUT_DIR / "complete_walkthrough_guide_report.json"
    md_path = OUT_DIR / "complete_walkthrough_guide_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Complete Walkthrough Guide Delivery",
        "",
        f"Status: `{status}`",
        "",
        "## Documents",
    ]
    for name, entry in docs.items():
        lines.append(f"- `{name}` `{entry.get('sha256', 'missing')}` `{entry['path']}`")
    lines.extend(["", "## Checks"])
    for name, check in checks.items():
        mark = "PASS" if check["pass"] else "FAIL"
        lines.append(f"- `{mark}` `{name}`")
    lines.extend(["", "## Documented Command Targets"])
    for command in commands:
        mark = "PASS" if command["exists"] else "FAIL"
        lines.append(f"- `{mark}` `{command['runner']} {command['path']}`")
    lines.extend(["", "## Documented Command Syntax"])
    for item in syntax_checks:
        mark = "PASS" if item["pass"] else "FAIL"
        lines.append(f"- `{mark}` `{item['runner']} {item['path']}`")
    if failures:
        lines.extend(["", "## Failures"])
        for failure in failures:
            lines.append(f"- {failure}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"complete_walkthrough_guide {status} json={json_path.relative_to(REPO)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
