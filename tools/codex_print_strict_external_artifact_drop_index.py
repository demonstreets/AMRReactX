#!/usr/bin/env python3
"""Print the strict external artifact drop index in an operator-friendly form."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"index report is not a JSON object: {path}")
    return data


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["summary"]
    domains = []
    for domain in report.get("domain_drop_index", []):
        checks = domain.get("checks", [])
        domains.append(
            {
                "domain": domain.get("domain"),
                "required_artifact_count": domain.get("required_artifact_count"),
                "currently_present_artifact_count": domain.get("currently_present_artifact_count"),
                "missing_artifact_count": sum(1 for check in checks if not check.get("currently_present")),
                "target_paths": [check.get("target_path") for check in checks],
                "template_paths": [check.get("template_path") for check in checks],
            }
        )
    return {
        "status": report.get("status"),
        "strict_completion_allowed": summary.get("strict_completion_allowed"),
        "domain_count": summary.get("domain_count"),
        "template_count": summary.get("template_count"),
        "required_file_count": summary.get("contract_check_count"),
        "present_file_count": summary.get("present_contract_artifact_count"),
        "missing_file_count": summary.get("awaiting_missing_artifact_count"),
        "domains": domains,
        "operator_next_steps": report.get("operator_next_steps", []),
    }


def print_text(data: dict[str, Any]) -> None:
    print("strict external artifact drop index")
    print("===================================")
    print(f"status: {data['status']}")
    print(f"strict completion allowed: {'yes' if data['strict_completion_allowed'] else 'no'}")
    print(f"domains: {data['domain_count']}")
    print(f"templates: {data['template_count']}")
    print(f"required files: {data['required_file_count']}")
    print(f"present files: {data['present_file_count']}")
    print(f"missing files: {data['missing_file_count']}")
    print()
    print("Operator next steps")
    print("-------------------")
    for step in data["operator_next_steps"]:
        print(f"- {step}")
    for domain in data["domains"]:
        print()
        print(f"{domain['domain']}")
        print("-" * len(str(domain["domain"])))
        print(f"required files: {domain['required_artifact_count']}")
        print(f"present files: {domain['currently_present_artifact_count']}")
        print(f"missing files: {domain['missing_artifact_count']}")
        for target, template in zip(domain["target_paths"], domain["template_paths"]):
            print(f"- target: {target}")
            print(f"  template: {template}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default=str(DEFAULT_INDEX))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = summarize(load_json(Path(args.index)))
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_text(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
