#!/usr/bin/env python3
"""Audit current operator command references and script syntax."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-OPERATOR-COMMAND-INVENTORY"
STATUS_NOT_READY = "NOT_READY-CURRENT-OPERATOR-COMMAND-INVENTORY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_operator_command_inventory_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_operator_command_inventory_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_operator_command_inventory_report.md"

SOURCE_FILES = [
    Path("README.md"),
    Path("docs/codex_audit/current_scope_operator_runbook.md"),
    Path("docs/codex_audit/engineering_multi_fuel_operator_runbook.md"),
    Path("docs/user_guides/README.md"),
    Path("docs/user_guides/Pele_CFD_中文使用手册.md"),
    Path("docs/user_guides/从目录到排错_完整运行教程.md"),
    Path("docs/user_guides/从零设置完整算例_工程H2泄漏火灾与学术爆轰.md"),
    Path("docs/user_guides/命令速查与场景矩阵.md"),
    Path("docs/user_guides/工程场景_泄漏扩散火灾_Tutorial.md"),
    Path("docs/user_guides/学术场景_气相与两相爆轰_Tutorial.md"),
    Path("docs/user_guides/真实工程资料交付与复验清单.md"),
    Path("examples/engineering/h2_leak_3d/README_中文快速教程.md"),
    Path("examples/academic/detonation_2D/README_中文快速教程.md"),
    Path("tools/codex_verify_current_scope.sh"),
    Path("tools/run_current_scope_release_refresh.sh"),
]

REQUIRED_COMMAND_SNIPPETS = {
    "bash tools/codex_verify_current_scope.sh",
    "python3 tools/codex_print_current_status.py",
    "python3 tools/codex_print_current_status.py --json",
    "python3 tools/write_current_scope_state_snapshot_report.py",
    "bash tools/verify_current_scope_state_snapshot.sh",
    "python3 tools/write_current_operator_command_inventory_report.py",
    "bash tools/verify_current_operator_command_inventory.sh",
    "python3 tools/write_engineering_multi_fuel_operator_runbook_report.py",
    "bash tools/verify_engineering_multi_fuel_operator_runbook.sh",
    "python3 tools/write_engineering_multi_fuel_template_catalog_report.py",
    "bash tools/verify_engineering_multi_fuel_template_catalog.sh",
    "python3 tools/write_strict_artifact_drop_contract_selftest_report.py",
    "bash tools/verify_strict_artifact_drop_contract_selftest.sh",
    "python3 tools/write_current_scope_delivery_package_report.py",
    "bash tools/verify_current_scope_delivery_package.sh",
    "python3 tools/write_current_scope_final_handoff_note_report.py",
    "bash tools/verify_current_scope_final_handoff_note.sh",
    "python3 tools/write_current_scope_release_refresh_entrypoint_report.py",
    "bash tools/verify_current_scope_release_refresh_entrypoint.sh",
    "bash tools/run_current_scope_release_refresh.sh",
    "python3 tools/write_strict_master_plan_completion_gate_report.py",
    "bash tools/verify_strict_master_plan_completion_gate.sh",
    "python3 tools/write_strict_external_artifact_drop_index_report.py",
    "bash tools/verify_strict_external_artifact_drop_index.sh",
    "python3 tools/codex_print_strict_external_artifact_drop_index.py",
    "python3 tools/codex_print_strict_external_artifact_drop_index.py --json",
    "python3 tools/write_strict_external_artifact_drop_index_cli_report.py",
    "bash tools/verify_strict_external_artifact_drop_index_cli.sh",
    "python3 tools/write_strict_external_artifact_drop_checklist_report.py",
    "bash tools/verify_strict_external_artifact_drop_checklist.sh",
    "python3 tools/write_strict_external_artifact_progress_selftest_report.py",
    "bash tools/verify_strict_external_artifact_progress_selftest.sh",
    "python3 tools/write_user_guides_index_report.py",
    "bash tools/verify_user_guides_index.sh",
    "python3 tools/write_strict_master_plan_closeout_action_pack_report.py",
    "bash tools/verify_strict_master_plan_closeout_action_pack.sh",
    "python3 tools/write_current_phase_final_delivery_index_report.py",
    "bash tools/verify_current_phase_final_delivery_index.sh",
    "python3 tools/write_project_closeout_acceptance_gate_report.py",
    "bash tools/verify_project_closeout_acceptance_gate.sh",
    "python3 tools/write_current_operator_quickstart_smoke_report.py",
    "bash tools/verify_current_operator_quickstart_smoke.sh",
    "python3 tools/write_current_phase_closure_certificate_report.py",
    "bash tools/verify_current_phase_closure_certificate.sh",
    "python3 tools/write_current_worktree_hygiene_report.py",
    "bash tools/verify_current_worktree_hygiene.sh",
    "python3 tools/check_machine_local_paths.py --strict",
    "python3 tools/write_current_worktree_source_ledger_report.py",
    "bash tools/verify_current_worktree_source_ledger.sh",
    "python3 tools/write_current_case_output_cleanup_manifest_report.py",
    "bash tools/verify_current_case_output_cleanup_manifest.sh",
    "python3 tools/write_sundials_local_link_audit_report.py",
    "bash tools/verify_sundials_local_link_audit.sh",
    "python3 tools/write_current_worktree_review_queue_report.py",
    "bash tools/verify_current_worktree_review_queue.sh",
    "python3 tools/write_current_phase_release_manifest_report.py",
    "bash tools/verify_current_phase_release_manifest.sh",
    "python3 tools/write_current_verification_chain_coverage_report.py",
    "bash tools/verify_current_verification_chain_coverage.sh",
    "python3 tools/write_current_report_hash_cycle_guard_report.py",
    "bash tools/verify_current_report_hash_cycle_guard.sh",
}


class CommandInventoryError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CommandInventoryError(message)


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
        raise CommandInventoryError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CommandInventoryError(f"invalid JSON evidence {path}: {exc}") from exc
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


def normalize_command(raw: str) -> str | None:
    command = raw.strip()
    command = command.removeprefix("-").strip()
    if command.startswith("`") and command.endswith("`"):
        command = command[1:-1].strip()
    command = command.rstrip(".")
    if " tools/" not in f" {command}":
        return None
    if not re.search(r"(^|\s)(python3|bash)\s+tools/", command):
        return None
    return command


def extract_commands(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    commands: dict[str, dict[str, Any]] = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        candidates = [line]
        candidates.extend(match.group(1) for match in re.finditer(r"`([^`]*(?:python3|bash)\s+tools/[^`]*)`", line))
        for raw in candidates:
            command = normalize_command(raw)
            if not command:
                continue
            entry = commands.setdefault(
                command,
                {"command": command, "source": str(path), "line_numbers": []},
            )
            entry["line_numbers"].append(line_no)
    return list(commands.values())


def command_tool_path(command: str) -> tuple[str | None, str | None]:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None, None
    for index, part in enumerate(parts):
        if part in {"python3", "bash"} and index + 1 < len(parts):
            candidate = parts[index + 1]
            if candidate.startswith("tools/"):
                return part, candidate
    return None, None


def run_syntax_check(kind: str | None, tool_path: Path) -> dict[str, Any]:
    if kind == "python3":
        argv = ["python_ast_parse", str(tool_path)]
        try:
            ast.parse(tool_path.read_text(encoding="utf-8"), filename=str(tool_path))
        except SyntaxError as exc:
            return {
                "argv": argv,
                "returncode": 1,
                "output_head": [f"{exc.__class__.__name__}: {exc}"],
            }
        return {"argv": argv, "returncode": 0, "output_head": []}
    elif kind == "bash":
        argv = ["bash", "-n", str(tool_path)]
    else:
        return {"argv": [], "returncode": None, "output_head": ["unsupported command kind"]}
    completed = subprocess.run(
        argv,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "output_head": completed.stdout.strip().splitlines()[:20],
    }


def build_report() -> dict[str, Any]:
    command_map: dict[str, dict[str, Any]] = {}
    for path in SOURCE_FILES:
        for entry in extract_commands(path):
            command = entry["command"]
            target = command_map.setdefault(
                command,
                {
                    "command": command,
                    "sources": [],
                    "kind": None,
                    "tool_path": None,
                    "tool_exists": False,
                    "syntax_check": None,
                    "ready": False,
                },
            )
            target["sources"].append(
                {
                    "path": entry["source"],
                    "line_numbers": sorted(set(entry["line_numbers"])),
                }
            )

    for entry in command_map.values():
        kind, tool_path_text = command_tool_path(entry["command"])
        entry["kind"] = kind
        entry["tool_path"] = tool_path_text
        path = Path(tool_path_text) if tool_path_text else None
        entry["tool_exists"] = bool(path and path.is_file())
        if path and path.is_file():
            entry["sha256"] = sha256_file(path)
            entry["syntax_check"] = run_syntax_check(kind, path)
            entry["ready"] = entry["syntax_check"]["returncode"] == 0
        else:
            entry["syntax_check"] = {"returncode": None, "output_head": ["missing tool"]}
            entry["ready"] = False

    commands = sorted(command_map.values(), key=lambda item: item["command"])
    missing = [entry for entry in commands if not entry["tool_exists"]]
    syntax_failures = [entry for entry in commands if entry["tool_exists"] and not entry["ready"]]
    snippets_found = set(command_map)
    missing_required_snippets = sorted(REQUIRED_COMMAND_SNIPPETS - snippets_found)
    ready = bool(commands) and not missing and not syntax_failures and not missing_required_snippets

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "current_operator_command_inventory_ready": ready,
            "source_file_count": len(SOURCE_FILES),
            "command_count": len(commands),
            "missing_tool_count": len(missing),
            "syntax_failure_count": len(syntax_failures),
            "required_snippet_count": len(REQUIRED_COMMAND_SNIPPETS),
            "missing_required_snippet_count": len(missing_required_snippets),
        },
        "commands": commands,
        "missing_commands": missing,
        "syntax_failures": syntax_failures,
        "missing_required_snippets": missing_required_snippets,
        "evidence_files": [evidence_entry(path.as_posix(), path) for path in SOURCE_FILES],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_operator_command_inventory_ready") is True, "operator command inventory is not ready")
    require(summary.get("source_file_count") == len(SOURCE_FILES), "unexpected source file count")
    require(summary.get("command_count", 0) >= len(REQUIRED_COMMAND_SNIPPETS), "too few operator commands found")
    require(summary.get("missing_tool_count") == 0, "operator command references missing tools")
    require(summary.get("syntax_failure_count") == 0, "operator command script syntax failures")
    require(summary.get("missing_required_snippet_count") == 0, "missing required command snippets")
    for entry in data.get("commands", []):
        require(isinstance(entry, dict), "invalid command entry")
        require(entry.get("tool_exists") is True, f"missing tool: {entry.get('tool_path')}")
        require(entry.get("ready") is True, f"syntax check failed: {entry.get('command')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Operator Command Inventory",
        "",
        f"- Status: `{report['status']}`",
        f"- Commands: `{summary['command_count']}`",
        f"- Missing tools: `{summary['missing_tool_count']}`",
        f"- Syntax failures: `{summary['syntax_failure_count']}`",
        f"- Missing required snippets: `{summary['missing_required_snippet_count']}`",
        "",
        "## Commands",
        "",
    ]
    for entry in report["commands"]:
        lines.append(
            f"- `{entry['command']}` -> `{entry['tool_path']}` "
            f"exists=`{entry['tool_exists']}` syntax_rc=`{entry['syntax_check']['returncode']}`"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_operator_command_inventory VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_operator_command_inventory PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
