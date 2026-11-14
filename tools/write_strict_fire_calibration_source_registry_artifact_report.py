#!/usr/bin/env python3
"""Write/verify the strict fire-calibration public source registry artifact."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-FIRE-CALIBRATION-SOURCE-REGISTRY-ARTIFACT"

DEFAULT_PUBLIC_TRIAGE = Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/fire_calibration_public_source_triage_report.json")
DEFAULT_LITERATURE_PREFLIGHT = Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/fire_calibration_literature_metric_preflight_report.json")
DEFAULT_REGISTRY = Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry.csv")
DEFAULT_OUTPUT_ROOT = Path("docs/codex_audit/evidence/strict_fire_calibration_source_registry_artifact_20260817")
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / "strict_fire_calibration_source_registry_artifact_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / "strict_fire_calibration_source_registry_artifact_report.md"

HEADER = ("family", "candidate_id", "title", "url_or_doi", "selected_for_calibration", "required_digitization")
PLACEHOLDER_MARKERS = ("<", "replace", "pending", "todo", "tbd", "placeholder", "fill in")


class RegistryError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RegistryError(message)


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
        raise RegistryError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {"label": label, "path": path.as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def candidate_rows(public_triage: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for family, key in (("radiation", "radiation_candidates"), ("overpressure", "overpressure_candidates")):
        candidates = public_triage.get(key)
        require(isinstance(candidates, list) and candidates, f"missing {key}")
        for candidate in candidates:
            require(isinstance(candidate, dict), f"invalid candidate in {key}")
            required_digitization = candidate.get("required_digitization")
            require(isinstance(required_digitization, list) and required_digitization, "candidate missing digitization list")
            rows.append(
                {
                    "family": family,
                    "candidate_id": str(candidate.get("id", "")).strip(),
                    "title": str(candidate.get("title", "")).strip(),
                    "url_or_doi": str(candidate.get("url") or candidate.get("doi") or "").strip(),
                    "selected_for_calibration": "false",
                    "required_digitization": "; ".join(str(item).strip() for item in required_digitization if str(item).strip()),
                }
            )
    return rows


def write_registry(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(HEADER))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_registry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require(tuple(reader.fieldnames or ()) == HEADER, "registry header mismatch")
        rows = list(reader)
    require(rows, "registry is empty")
    return rows


def validate_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    ids: set[str] = set()
    gaps: list[str] = []
    for idx, row in enumerate(rows, 1):
        text = " ".join(row.get(key, "") for key in HEADER).lower()
        if any(marker in text for marker in PLACEHOLDER_MARKERS):
            gaps.append(f"row_{idx}_placeholder_marker")
        candidate_id = row.get("candidate_id", "").strip()
        if not candidate_id:
            gaps.append(f"row_{idx}_missing_candidate_id")
        if candidate_id in ids:
            gaps.append(f"duplicate_candidate_id:{candidate_id}")
        ids.add(candidate_id)
        if row.get("family", "").strip() not in {"radiation", "overpressure"}:
            gaps.append(f"row_{idx}_invalid_family")
        if row.get("selected_for_calibration", "").strip().lower() not in {"true", "false"}:
            gaps.append(f"row_{idx}_bad_selected_for_calibration")
        for key in ("title", "url_or_doi", "required_digitization"):
            if not row.get(key, "").strip():
                gaps.append(f"row_{idx}_missing_{key}")
    require(not gaps, "registry validation gaps: " + ",".join(gaps))
    return {
        "row_count": len(rows),
        "radiation_candidate_count": sum(1 for row in rows if row["family"] == "radiation"),
        "overpressure_candidate_count": sum(1 for row in rows if row["family"] == "overpressure"),
        "selected_for_calibration_count": sum(1 for row in rows if row["selected_for_calibration"].lower() == "true"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    public_triage_path = Path(args.public_triage)
    literature_preflight_path = Path(args.literature_preflight)
    registry_path = Path(args.registry)
    public_triage = load_json(public_triage_path)
    literature_preflight = load_json(literature_preflight_path)
    require(public_triage.get("status") == "PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE", "public triage is not PASS")
    require(literature_preflight.get("status") == "PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT", "literature metric preflight is not PASS")
    write_registry(candidate_rows(public_triage), registry_path)
    registry_rows = read_registry(registry_path)
    registry_summary = validate_rows(registry_rows)
    ready = (
        registry_summary["radiation_candidate_count"] >= 3
        and registry_summary["overpressure_candidate_count"] >= 2
        and registry_summary["selected_for_calibration_count"] == 0
        and public_triage.get("summary", {}).get("ready_for_dataset_ingestion") is False
        and literature_preflight.get("summary", {}).get("ready_for_dataset_ingestion") is False
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "strict fire calibration public source registry artifact",
        "summary": {
            "strict_fire_calibration_source_registry_artifact_ready": ready,
            "registry_path": registry_path.as_posix(),
            "registry_row_count": registry_summary["row_count"],
            "radiation_candidate_count": registry_summary["radiation_candidate_count"],
            "overpressure_candidate_count": registry_summary["overpressure_candidate_count"],
            "selected_for_calibration_count": registry_summary["selected_for_calibration_count"],
            "registry_is_source_list_not_calibration_dataset": True,
            "radiation_metrics_still_required": True,
            "overpressure_metrics_still_required": True,
            "calibration_metadata_still_required": True,
            "strict_completion_allowed": False,
            "strict_master_plan_still_open": True,
        },
        "registry_rows": registry_rows,
        "evidence_files": [
            evidence_entry("fire_calibration_public_source_triage", public_triage_path),
            evidence_entry("fire_calibration_literature_metric_preflight", literature_preflight_path),
            evidence_entry("fire_calibration_source_registry", registry_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_fire_calibration_source_registry_artifact_ready") is True, "registry artifact not ready")
    require(summary.get("registry_row_count") == 5, "unexpected registry row count")
    require(summary.get("radiation_candidate_count") >= 3, "too few radiation candidates")
    require(summary.get("overpressure_candidate_count") >= 2, "too few overpressure candidates")
    require(summary.get("selected_for_calibration_count") == 0, "registry prematurely selects calibration source")
    require(summary.get("registry_is_source_list_not_calibration_dataset") is True, "registry overclaims calibration")
    require(summary.get("radiation_metrics_still_required") is True, "radiation metrics overclaimed")
    require(summary.get("overpressure_metrics_still_required") is True, "overpressure metrics overclaimed")
    require(summary.get("calibration_metadata_still_required") is True, "metadata overclaimed")
    require(summary.get("strict_completion_allowed") is False, "registry overclaims strict completion")
    require(summary.get("strict_master_plan_still_open") is True, "registry overclaims strict closure")
    rows = data.get("registry_rows")
    require(isinstance(rows, list) and len(rows) == 5, "invalid registry rows")
    validate_rows(rows)
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Fire Calibration Source Registry Artifact",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['strict_fire_calibration_source_registry_artifact_ready']}`",
        f"- Registry rows: `{summary['registry_row_count']}`",
        f"- Radiation candidates: `{summary['radiation_candidate_count']}`",
        f"- Overpressure candidates: `{summary['overpressure_candidate_count']}`",
        f"- Selected for calibration: `{summary['selected_for_calibration_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-triage", default=str(DEFAULT_PUBLIC_TRIAGE))
    parser.add_argument("--literature-preflight", default=str(DEFAULT_LITERATURE_PREFLIGHT))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"strict_fire_calibration_source_registry_artifact VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0
    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_fire_calibration_source_registry_artifact PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
