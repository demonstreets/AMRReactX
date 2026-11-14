#!/usr/bin/env python3
"""Write/verify the current report hash-cycle guard report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-REPORT-HASH-CYCLE-GUARD"

OUT_DIR = Path("docs/codex_audit/evidence/current_report_hash_cycle_guard_20260818")
OUT_JSON = OUT_DIR / "current_report_hash_cycle_guard_report.json"
OUT_MD = OUT_DIR / "current_report_hash_cycle_guard_report.md"

CYCLE_POLICY = "skipped-cycle-reference"
REPORTS = {
    "current_scope_delivery_package": Path(
        "docs/codex_audit/evidence/current_scope_delivery_package_20260812/"
        "current_scope_delivery_package_report.json"
    ),
    "current_scope_state_snapshot": Path(
        "docs/codex_audit/evidence/current_scope_state_snapshot_20260803/"
        "current_scope_state_snapshot_report.json"
    ),
    "current_phase_release_manifest": Path(
        "docs/codex_audit/evidence/current_phase_release_manifest_20260812/"
        "current_phase_release_manifest_report.json"
    ),
    "current_status_cli": Path(
        "docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json"
    ),
    "current_verification_chain_coverage": Path(
        "docs/codex_audit/evidence/current_verification_chain_coverage_20260803/"
        "current_verification_chain_coverage_report.json"
    ),
    "current_scope_release_refresh_entrypoint": Path(
        "docs/codex_audit/evidence/current_scope_release_refresh_entrypoint_20260812/"
        "current_scope_release_refresh_entrypoint_report.json"
    ),
}

ENTRYPOINT_FORBIDDEN_HASH_LABELS = {
    "current_phase_release_manifest",
    "current_status_cli",
    "current_scope_state_snapshot",
    "current_report_hash_cycle_guard",
    "current_verification_chain_coverage",
}

EXPECTED_SKIPS = {
    "current_scope_delivery_package": {"current_scope_state_snapshot"},
    "current_scope_state_snapshot": {
        "current_scope_delivery_package",
        "current_phase_release_manifest",
        "current_status_cli",
        "current_verification_chain_coverage",
    },
}

EXPECTED_STATUS = {
    "current_scope_delivery_package": "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
    "current_scope_state_snapshot": "PASS-CURRENT-SCOPE-STATE-SNAPSHOT",
    "current_phase_release_manifest": "PASS-CURRENT-PHASE-RELEASE-MANIFEST",
    "current_status_cli": "PASS-CURRENT-STATUS-CLI",
    "current_verification_chain_coverage": "PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE",
    "current_scope_release_refresh_entrypoint": "PASS-CURRENT-SCOPE-RELEASE-REFRESH-ENTRYPOINT",
}

VERIFY_COMMANDS = [
    ["bash", "tools/verify_current_scope_delivery_package.sh"],
    ["bash", "tools/verify_current_scope_state_snapshot.sh"],
]


class HashCycleGuardError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HashCycleGuardError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing JSON report: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON report is not an object: {path}")
    return data


def report_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing report file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def run_verify(argv: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
        check=False,
    )
    lines = proc.stdout.strip().splitlines()
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "output_tail": lines[-12:],
        "pass": proc.returncode == 0,
    }


def skipped_labels(report: dict[str, Any]) -> set[str]:
    labels = set()
    for entry in report.get("evidence_files", []):
        if isinstance(entry, dict) and entry.get("hash_verification") == CYCLE_POLICY:
            labels.add(str(entry.get("label")))
    return labels


def cycle_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        entry
        for entry in report.get("evidence_files", [])
        if isinstance(entry, dict) and entry.get("hash_verification") == CYCLE_POLICY
    ]


def evidence_labels(report: dict[str, Any]) -> set[str]:
    return {
        str(entry.get("label"))
        for entry in report.get("evidence_files", [])
        if isinstance(entry, dict)
    }


def build_report() -> dict[str, Any]:
    failures: list[str] = []

    command_results = [run_verify(argv) for argv in VERIFY_COMMANDS]
    for result in command_results:
        if not result["pass"]:
            failures.append(f"verify command failed: {' '.join(result['argv'])}")

    loaded = {label: load_json(path) for label, path in REPORTS.items()}

    statuses = {}
    for label, data in loaded.items():
        status = data.get("status")
        expected = EXPECTED_STATUS[label]
        ok = status == expected
        statuses[label] = {"status": status, "expected_status": expected, "pass": ok}
        if not ok:
            failures.append(f"status mismatch for {label}: {status} != {expected}")

    cycle_policy_checks = {}
    for report_label, expected_labels in EXPECTED_SKIPS.items():
        actual = skipped_labels(loaded[report_label])
        ok = actual == expected_labels
        cycle_policy_checks[report_label] = {
            "expected_skipped_labels": sorted(expected_labels),
            "actual_skipped_labels": sorted(actual),
            "pass": ok,
        }
        if not ok:
            failures.append(
                f"cycle policy mismatch for {report_label}: {sorted(actual)} != {sorted(expected_labels)}"
            )
        for entry in cycle_entries(loaded[report_label]):
            path = Path(str(entry.get("path", "")))
            if not path.is_file():
                failures.append(f"cycle-reference target missing for {report_label}: {path}")
            if not isinstance(entry.get("sha256"), str) or len(str(entry.get("sha256"))) != 64:
                failures.append(f"cycle-reference sha256 malformed for {report_label}: {entry.get('label')}")

    entrypoint_labels = evidence_labels(loaded["current_scope_release_refresh_entrypoint"])
    forbidden_entrypoint_labels = sorted(entrypoint_labels & ENTRYPOINT_FORBIDDEN_HASH_LABELS)
    entrypoint_dynamic_hash_check = {
        "forbidden_hashed_labels": sorted(ENTRYPOINT_FORBIDDEN_HASH_LABELS),
        "actual_forbidden_hashed_labels": forbidden_entrypoint_labels,
        "pass": not forbidden_entrypoint_labels,
    }
    if forbidden_entrypoint_labels:
        failures.append(
            "release refresh entrypoint hashes dynamic reports: "
            + ", ".join(forbidden_entrypoint_labels)
        )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if not failures else "FAIL-CURRENT-REPORT-HASH-CYCLE-GUARD",
        "summary": {
            "current_report_hash_cycle_guard_ready": not failures,
            "cycle_policy": CYCLE_POLICY,
            "guarded_report_count": len(REPORTS),
            "cycle_policy_report_count": len(EXPECTED_SKIPS),
            "entrypoint_forbidden_hash_label_count": len(ENTRYPOINT_FORBIDDEN_HASH_LABELS),
            "entrypoint_forbidden_hash_hit_count": len(forbidden_entrypoint_labels),
            "verify_command_count": len(VERIFY_COMMANDS),
            "verify_command_failure_count": sum(1 for item in command_results if not item["pass"]),
            "failure_count": len(failures),
        },
        "report_statuses": statuses,
        "cycle_policy_checks": cycle_policy_checks,
        "entrypoint_dynamic_hash_check": entrypoint_dynamic_hash_check,
        "verify_commands": command_results,
        "evidence_files": [report_entry(label, path) for label, path in REPORTS.items()],
        "failures": failures,
    }
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    require(data.get("failures") == [], "guard report contains failures")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_report_hash_cycle_guard_ready") is True, "guard is not ready")
    require(summary.get("cycle_policy") == CYCLE_POLICY, "unexpected cycle policy")
    require(summary.get("guarded_report_count") == len(REPORTS), "unexpected guarded report count")
    require(summary.get("cycle_policy_report_count") == len(EXPECTED_SKIPS), "unexpected cycle policy report count")
    require(
        summary.get("entrypoint_forbidden_hash_label_count") == len(ENTRYPOINT_FORBIDDEN_HASH_LABELS),
        "unexpected entrypoint forbidden hash label count",
    )
    require(summary.get("entrypoint_forbidden_hash_hit_count") == 0, "entrypoint hashes dynamic reports")
    require(summary.get("verify_command_failure_count") == 0, "one or more verify commands failed")
    for check in data.get("cycle_policy_checks", {}).values():
        require(isinstance(check, dict) and check.get("pass") is True, "cycle policy check failed")
    entrypoint_check = data.get("entrypoint_dynamic_hash_check")
    require(
        isinstance(entrypoint_check, dict) and entrypoint_check.get("pass") is True,
        "entrypoint dynamic hash check failed",
    )
    for result in data.get("verify_commands", []):
        require(isinstance(result, dict) and result.get("pass") is True, "verify command did not pass")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Report Hash-Cycle Guard",
        "",
        f"- Status: `{report['status']}`",
        f"- Guard ready: `{summary['current_report_hash_cycle_guard_ready']}`",
        f"- Cycle policy: `{summary['cycle_policy']}`",
        f"- Guarded reports: `{summary['guarded_report_count']}`",
        f"- Entrypoint forbidden hash hits: `{summary['entrypoint_forbidden_hash_hit_count']}`",
        f"- Verify command failures: `{summary['verify_command_failure_count']}`",
        "",
        "## Cycle Policy Checks",
        "",
    ]
    for label, check in report["cycle_policy_checks"].items():
        lines.append(
            f"- `{label}` expected=`{check['expected_skipped_labels']}` "
            f"actual=`{check['actual_skipped_labels']}` pass=`{check['pass']}`"
        )
    entrypoint_check = report["entrypoint_dynamic_hash_check"]
    lines.extend(
        [
            "",
            "## Entrypoint Dynamic Hash Check",
            "",
            f"- forbidden=`{entrypoint_check['forbidden_hashed_labels']}`",
            f"- actual=`{entrypoint_check['actual_forbidden_hashed_labels']}`",
            f"- pass=`{entrypoint_check['pass']}`",
        ]
    )
    lines.extend(["", "## Verify Commands", ""])
    for result in report["verify_commands"]:
        lines.append(f"- `{ ' '.join(result['argv']) }` pass=`{result['pass']}` rc=`{result['returncode']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(OUT_JSON))
    parser.add_argument("--output-md", default=str(OUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_report_hash_cycle_guard VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    validate_report(report, verify_hashes=False)
    print(f"current_report_hash_cycle_guard PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
