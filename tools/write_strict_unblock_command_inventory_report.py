#!/usr/bin/env python3
"""Audit command references needed to unblock strict master-plan blockers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-UNBLOCK-COMMAND-INVENTORY"
STATUS_NOT_READY = "NOT_READY-STRICT-UNBLOCK-COMMAND-INVENTORY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_unblock_command_inventory_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_unblock_command_inventory_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_unblock_command_inventory_report.md"

SOURCE_DOCS = [
    Path("docs/codex_audit/strict_master_plan_unblock_runbook.md"),
    Path(
        "docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/"
        "master_plan_strict_artifact_intake_manifest_report.md"
    ),
    Path(
        "docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731/"
        "master_plan_strict_artifact_drop_preflight_report.md"
    ),
]

STRICT_BLOCKER_MATRIX = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)

REQUIRED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class InventoryError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


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
        raise InventoryError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InventoryError(f"invalid JSON evidence {path}: {exc}") from exc
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


def extract_commands_from_doc(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    commands: dict[str, dict[str, Any]] = {}

    candidates: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        candidates.append((line_no, line))
        for match in re.finditer(r"`([^`]*(?:python3|bash)\s+tools/[^`]*)`", line):
            candidates.append((line_no, match.group(1)))

    for line_no, raw in candidates:
        command = normalize_command(raw)
        if not command:
            continue
        entry = commands.setdefault(
            command,
            {
                "command": command,
                "source": str(path),
                "line_numbers": [],
            },
        )
        entry["line_numbers"].append(line_no)
    return list(commands.values())


def command_tool_path(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    for index, part in enumerate(parts):
        if part in {"python3", "bash"} and index + 1 < len(parts):
            candidate = parts[index + 1]
            if candidate.startswith("tools/"):
                return candidate
    return None


def build_report() -> dict[str, Any]:
    strict = load_json(STRICT_BLOCKER_MATRIX)
    strict_blockers = set(strict.get("summary", {}).get("open_strict_blockers", []))

    evidence_files = [evidence_entry("strict_blocker_matrix", STRICT_BLOCKER_MATRIX)]
    command_entries: list[dict[str, Any]] = []
    for path in SOURCE_DOCS:
        evidence_files.append(evidence_entry(path.as_posix(), path))
        command_entries.extend(extract_commands_from_doc(path))

    deduped: dict[str, dict[str, Any]] = {}
    for entry in command_entries:
        command = entry["command"]
        existing = deduped.setdefault(
            command,
            {
                "command": command,
                "sources": [],
                "tool_path": command_tool_path(command),
                "tool_exists": False,
            },
        )
        existing["sources"].append(
            {
                "path": entry["source"],
                "line_numbers": sorted(set(entry["line_numbers"])),
            }
        )

    for entry in deduped.values():
        tool_path = entry.get("tool_path")
        entry["tool_exists"] = bool(tool_path and Path(str(tool_path)).is_file())

    commands = sorted(deduped.values(), key=lambda item: item["command"])
    missing = [entry for entry in commands if not entry["tool_exists"]]
    strict_blocker_set_ok = strict_blockers == REQUIRED_STRICT_BLOCKERS
    source_docs_ready = all(path.is_file() for path in SOURCE_DOCS)
    ready = source_docs_ready and strict_blocker_set_ok and bool(commands) and not missing

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "strict_unblock_command_inventory_ready": ready,
            "source_doc_count": len(SOURCE_DOCS),
            "command_count": len(commands),
            "missing_tool_count": len(missing),
            "strict_blocker_set_ok": strict_blocker_set_ok,
            "open_strict_blockers": sorted(strict_blockers),
        },
        "commands": commands,
        "missing_commands": missing,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_unblock_command_inventory_ready") is True, "command inventory is not ready")
    require(summary.get("source_doc_count") == len(SOURCE_DOCS), "unexpected source doc count")
    require(summary.get("command_count", 0) > 0, "no strict unblock commands found")
    require(summary.get("missing_tool_count") == 0, "strict unblock command references missing tools")
    require(summary.get("strict_blocker_set_ok") is True, "strict blocker set changed")
    commands = data.get("commands")
    require(isinstance(commands, list), "missing commands list")
    for entry in commands:
        require(isinstance(entry, dict), "invalid command entry")
        require(entry.get("tool_exists") is True, f"missing tool for command: {entry.get('command')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Unblock Command Inventory",
        "",
        f"- Status: `{report['status']}`",
        f"- Source docs: `{summary['source_doc_count']}`",
        f"- Commands found: `{summary['command_count']}`",
        f"- Missing tools: `{summary['missing_tool_count']}`",
        f"- Strict blocker set ok: `{summary['strict_blocker_set_ok']}`",
        "",
        "## Commands",
        "",
    ]
    for entry in report["commands"]:
        lines.append(f"- `{entry['command']}` -> `{entry['tool_path']}` exists=`{entry['tool_exists']}`")
    if report["missing_commands"]:
        lines.extend(["", "## Missing Commands", ""])
        for entry in report["missing_commands"]:
            lines.append(f"- `{entry['command']}`")
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
        print(f"strict_unblock_command_inventory VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_unblock_command_inventory PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
