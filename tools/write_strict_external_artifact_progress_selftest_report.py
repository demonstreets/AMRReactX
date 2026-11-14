#!/usr/bin/env python3
"""Self-test that strict external artifact gates accept partial completion progress."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-PROGRESS-SELFTEST"
STATUS_NOT_READY = "NOT_READY-STRICT-EXTERNAL-ARTIFACT-PROGRESS-SELFTEST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_artifact_progress_selftest_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_artifact_progress_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_artifact_progress_selftest_report.md"

SOURCE_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
SIMULATED_INDEX = DEFAULT_ROOT / "simulated_partial_drop_index.json"
SIMULATED_CHECKLIST = DEFAULT_ROOT / "simulated_partial_drop_checklist_report.json"
SIMULATED_CHECKLIST_MD = DEFAULT_ROOT / "simulated_partial_drop_checklist_report.md"

EXPECTED_DOMAIN_COUNTS = {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}


class ProgressSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProgressSelftestError(message)


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
        raise ProgressSelftestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProgressSelftestError(f"invalid JSON evidence {path}: {exc}") from exc
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


def run_command(argv: list[str]) -> dict[str, Any]:
    proc = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_head": proc.stdout[:4000],
        "stderr_head": proc.stderr[:4000],
    }


def make_simulated_index(source: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(source)
    present_count = 0
    missing_count = 0
    for domain in data["domain_drop_index"]:
        marked_one = False
        for check in domain["checks"]:
            if not marked_one:
                check["currently_present"] = True
                marked_one = True
            else:
                check["currently_present"] = False
            if check["currently_present"]:
                present_count += 1
            else:
                missing_count += 1
        domain["currently_present_artifact_count"] = 1
    data["summary"]["present_contract_artifact_count"] = present_count
    data["summary"]["awaiting_missing_artifact_count"] = missing_count
    return data


def build_report() -> dict[str, Any]:
    source = load_json(SOURCE_INDEX)
    simulated = make_simulated_index(source)
    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
    SIMULATED_INDEX.write_text(json.dumps(simulated, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    cli_json = run_command(
        [
            "python3",
            "tools/codex_print_strict_external_artifact_drop_index.py",
            "--index",
            str(SIMULATED_INDEX),
            "--json",
        ]
    )
    parsed = json.loads(cli_json["stdout"]) if cli_json["returncode"] == 0 else {}
    checklist_run = run_command(
        [
            "python3",
            "tools/write_strict_external_artifact_drop_checklist_report.py",
            "--index",
            str(SIMULATED_INDEX),
            "--output-json",
            str(SIMULATED_CHECKLIST),
            "--output-md",
            str(SIMULATED_CHECKLIST_MD),
        ]
    )
    checklist_verify = run_command(
        [
            "bash",
            "tools/verify_strict_external_artifact_drop_checklist.sh",
            str(SIMULATED_CHECKLIST),
        ]
    )
    checklist = load_json(SIMULATED_CHECKLIST) if SIMULATED_CHECKLIST.is_file() else {}

    domain_required_counts = {
        domain.get("domain"): domain.get("required_artifact_count")
        for domain in parsed.get("domains", [])
    }
    domain_missing_counts = {
        domain.get("domain"): domain.get("missing_artifact_count")
        for domain in parsed.get("domains", [])
    }
    ready = (
        source.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX"
        and cli_json["returncode"] == 0
        and checklist_run["returncode"] == 0
        and checklist_verify["returncode"] == 0
        and parsed.get("present_file_count") == 3
        and parsed.get("missing_file_count") == 11
        and parsed.get("required_file_count") == 14
        and domain_required_counts == EXPECTED_DOMAIN_COUNTS
        and domain_missing_counts == {"external_plume": 4, "fire_calibration": 4, "real_cad": 3}
        and checklist.get("summary", {}).get("checklist_done_count") == 3
        and checklist.get("summary", {}).get("missing_file_count") == 11
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "strict_external_artifact_progress_selftest_ready": ready,
            "source_index_status": source.get("status"),
            "simulated_present_file_count": parsed.get("present_file_count"),
            "simulated_missing_file_count": parsed.get("missing_file_count"),
            "simulated_required_file_count": parsed.get("required_file_count"),
            "simulated_domain_required_counts": domain_required_counts,
            "simulated_domain_missing_counts": domain_missing_counts,
            "simulated_checklist_done_count": checklist.get("summary", {}).get("checklist_done_count"),
            "simulated_checklist_missing_file_count": checklist.get("summary", {}).get("missing_file_count"),
            "cli_json_returncode": cli_json["returncode"],
            "checklist_run_returncode": checklist_run["returncode"],
            "checklist_verify_returncode": checklist_verify["returncode"],
        },
        "command_runs": {
            "cli_json": cli_json,
            "checklist_run": checklist_run,
            "checklist_verify": checklist_verify,
        },
        "evidence_files": [
            evidence_entry("source_strict_external_artifact_drop_index", SOURCE_INDEX),
            evidence_entry("simulated_partial_drop_index", SIMULATED_INDEX),
            evidence_entry("simulated_partial_drop_checklist", SIMULATED_CHECKLIST),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_external_artifact_progress_selftest_ready") is True, "progress selftest is not ready")
    require(summary.get("source_index_status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX", "source index not passing")
    require(summary.get("simulated_required_file_count") == 14, "unexpected simulated required file count")
    require(summary.get("simulated_present_file_count") == 3, "unexpected simulated present file count")
    require(summary.get("simulated_missing_file_count") == 11, "unexpected simulated missing file count")
    require(
        summary.get("simulated_domain_required_counts") == EXPECTED_DOMAIN_COUNTS,
        "unexpected simulated required domain counts",
    )
    require(
        summary.get("simulated_domain_missing_counts") == {"external_plume": 4, "fire_calibration": 4, "real_cad": 3},
        "unexpected simulated missing domain counts",
    )
    require(summary.get("simulated_checklist_done_count") == 3, "unexpected simulated checklist done count")
    require(summary.get("simulated_checklist_missing_file_count") == 11, "unexpected simulated checklist missing count")
    require(summary.get("cli_json_returncode") == 0, "simulated CLI JSON run failed")
    require(summary.get("checklist_run_returncode") == 0, "simulated checklist run failed")
    require(summary.get("checklist_verify_returncode") == 0, "simulated checklist verify failed")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Progress Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Simulated present files: `{summary['simulated_present_file_count']}`",
        f"- Simulated missing files: `{summary['simulated_missing_file_count']}`",
        f"- Simulated checklist done files: `{summary['simulated_checklist_done_count']}`",
        f"- Simulated checklist missing files: `{summary['simulated_checklist_missing_file_count']}`",
        "",
        "This selftest proves the drop index and checklist accept partial strict artifact delivery.",
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
        print(f"strict_external_artifact_progress_selftest VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_artifact_progress_selftest PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
