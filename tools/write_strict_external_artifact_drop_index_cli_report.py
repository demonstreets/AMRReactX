#!/usr/bin/env python3
"""Write/verify a self-check report for the strict artifact drop-index CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX-CLI"
STATUS_NOT_READY = "NOT_READY-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX-CLI"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_artifact_drop_index_cli_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_artifact_drop_index_cli_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_artifact_drop_index_cli_report.md"

CLI = Path("tools/codex_print_strict_external_artifact_drop_index.py")
INDEX_REPORT = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)

REQUIRED_TEXT_SNIPPETS = [
    "strict external artifact drop index",
    "status: PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
    "strict completion allowed: no",
    "domains: 3",
    "templates: 16",
    "required files:",
    "present files:",
    "missing files:",
    "external_plume",
    "real_cad",
    "fire_calibration",
    "docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json",
    "docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json",
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json",
]


class DropIndexCliError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DropIndexCliError(message)


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
        raise DropIndexCliError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DropIndexCliError(f"invalid JSON evidence {path}: {exc}") from exc
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


def run_cli(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    return {
        "argv": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_head": proc.stdout[:4000],
        "stderr_head": proc.stderr[:4000],
    }


def parse_cli_json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DropIndexCliError(f"drop-index CLI JSON output is invalid: {exc}") from exc
    require(isinstance(data, dict), "drop-index CLI JSON output is not an object")
    return data


def build_report() -> dict[str, Any]:
    require(CLI.is_file(), f"missing drop-index CLI: {CLI}")
    require(INDEX_REPORT.is_file(), f"missing drop-index report: {INDEX_REPORT}")

    text_run = run_cli(["python3", str(CLI)])
    json_run = run_cli(["python3", str(CLI), "--json"])
    parsed = parse_cli_json(json_run["stdout"]) if json_run["returncode"] == 0 else {}
    missing_text_snippets = [snippet for snippet in REQUIRED_TEXT_SNIPPETS if snippet not in text_run["stdout"]]

    domain_names = sorted(domain.get("domain") for domain in parsed.get("domains", []))
    domain_required_counts = {
        domain.get("domain"): domain.get("required_artifact_count")
        for domain in parsed.get("domains", [])
    }
    domain_missing_counts = {
        domain.get("domain"): domain.get("missing_artifact_count")
        for domain in parsed.get("domains", [])
    }
    ready = (
        text_run["returncode"] == 0
        and json_run["returncode"] == 0
        and not missing_text_snippets
        and parsed.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX"
        and parsed.get("strict_completion_allowed") is False
        and parsed.get("domain_count") == 3
        and parsed.get("template_count") == 16
        and parsed.get("required_file_count") == 14
        and isinstance(parsed.get("present_file_count"), int)
        and isinstance(parsed.get("missing_file_count"), int)
        and 0 <= parsed.get("present_file_count") <= 14
        and 0 <= parsed.get("missing_file_count") <= 14
        and parsed.get("present_file_count") + parsed.get("missing_file_count") == 14
        and domain_names == ["external_plume", "fire_calibration", "real_cad"]
        and domain_required_counts == {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}
        and all(
            isinstance(domain_missing_counts.get(domain), int)
            and 0 <= domain_missing_counts[domain] <= required
            for domain, required in {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}.items()
        )
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "strict_external_artifact_drop_index_cli_ready": ready,
            "text_returncode": text_run["returncode"],
            "json_returncode": json_run["returncode"],
            "missing_text_snippet_count": len(missing_text_snippets),
            "index_status": parsed.get("status"),
            "strict_completion_allowed": parsed.get("strict_completion_allowed"),
            "domain_count": parsed.get("domain_count"),
            "template_count": parsed.get("template_count"),
            "required_file_count": parsed.get("required_file_count"),
            "present_file_count": parsed.get("present_file_count"),
            "missing_file_count": parsed.get("missing_file_count"),
            "domain_names": domain_names,
            "domain_required_counts": domain_required_counts,
            "domain_missing_counts": domain_missing_counts,
        },
        "missing_text_snippets": missing_text_snippets,
        "command_runs": {
            "text": {
                "argv": text_run["argv"],
                "returncode": text_run["returncode"],
                "stdout_head": text_run["stdout_head"],
            },
            "json": {
                "argv": json_run["argv"],
                "returncode": json_run["returncode"],
                "stdout_head": json_run["stdout_head"],
            },
        },
        "evidence_files": [
            evidence_entry("strict_external_artifact_drop_index_cli", CLI),
            evidence_entry("strict_external_artifact_drop_index_report", INDEX_REPORT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_external_artifact_drop_index_cli_ready") is True, "drop-index CLI is not ready")
    require(summary.get("text_returncode") == 0, "text CLI invocation failed")
    require(summary.get("json_returncode") == 0, "JSON CLI invocation failed")
    require(summary.get("missing_text_snippet_count") == 0, "text CLI output missing required snippets")
    require(summary.get("index_status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX", "unexpected index status")
    require(summary.get("strict_completion_allowed") is False, "strict completion unexpectedly allowed")
    require(summary.get("domain_count") == 3, "unexpected domain count")
    require(summary.get("template_count") == 16, "unexpected template count")
    require(summary.get("required_file_count") == 14, "unexpected required file count")
    present_count = summary.get("present_file_count")
    missing_count = summary.get("missing_file_count")
    require(isinstance(present_count, int), "present file count is not an integer")
    require(isinstance(missing_count, int), "missing file count is not an integer")
    require(0 <= present_count <= 14, "present file count is outside the contract range")
    require(0 <= missing_count <= 14, "missing file count is outside the contract range")
    require(present_count + missing_count == 14, "present and missing file counts do not match contract total")
    require(summary.get("domain_names") == ["external_plume", "fire_calibration", "real_cad"], "unexpected domains")
    require(
        summary.get("domain_required_counts") == {"external_plume": 5, "fire_calibration": 5, "real_cad": 4},
        "unexpected domain required counts",
    )
    domain_missing = summary.get("domain_missing_counts")
    require(isinstance(domain_missing, dict), "domain missing counts are not a dict")
    for domain, required in {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}.items():
        value = domain_missing.get(domain)
        require(isinstance(value, int), f"missing count for {domain} is not an integer")
        require(0 <= value <= required, f"missing count for {domain} is outside the contract range")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Drop Index CLI",
        "",
        f"- Status: `{report['status']}`",
        f"- CLI ready: `{summary['strict_external_artifact_drop_index_cli_ready']}`",
        f"- Domains: `{summary['domain_count']}`",
        f"- Required files: `{summary['required_file_count']}`",
        f"- Present files: `{summary['present_file_count']}`",
        f"- Missing files: `{summary['missing_file_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
        "## Command",
        "",
        "```bash",
        "python3 tools/codex_print_strict_external_artifact_drop_index.py",
        "python3 tools/codex_print_strict_external_artifact_drop_index.py --json",
        "```",
    ]
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
        validate_report(data)
        print(f"strict_external_artifact_drop_index_cli VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_artifact_drop_index_cli PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
