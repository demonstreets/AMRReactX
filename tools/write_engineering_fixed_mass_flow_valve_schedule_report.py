#!/usr/bin/env python3
"""Write/verify the fixed-mass-flow valve schedule smoke report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-FIXED-MASS-FLOW-VALVE-SCHEDULE"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_fixed_mass_flow_valve_schedule_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_fixed_mass_flow_valve_schedule_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_fixed_mass_flow_valve_schedule_report.md"

PROB_HEADER = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
SMOKE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_valve_schedule_smoke")
SMOKE_LOG = DEFAULT_ROOT / "fixed_mass_flow_valve_schedule_smoke.log"

BAD_LOG_TOKENS = (
    "Abort",
    "AMReX Error",
    "SIGABRT",
    "Segmentation fault",
    "nan",
    "NaN",
    "inf",
    "INF",
)


class ScheduleReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScheduleReportError(message)


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
        raise ScheduleReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScheduleReportError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_float_series(pattern: str, text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(pattern, text):
        values.append(float(match.group(1)))
    return values


def build_report() -> dict[str, Any]:
    require(PROB_HEADER.is_file(), f"missing problem header: {PROB_HEADER}")
    require(SMOKE_INPUT.is_file(), f"missing smoke input: {SMOKE_INPUT}")
    require(SMOKE_LOG.is_file(), f"missing smoke log: {SMOKE_LOG}")

    source_text = PROB_HEADER.read_text(encoding="utf-8")
    input_text = SMOKE_INPUT.read_text(encoding="utf-8")
    log_text = SMOKE_LOG.read_text(encoding="utf-8", errors="replace")

    source_scales_fixed_mdot = (
        "effective_mdot = scheduled_reference_mdot * valve_fraction_mid;" in source_text
        and "scheduled_reference_mdot = pp->leak_rate" in source_text
    )
    source_prints_schedule = "leak fixed-mass-flow schedule" in source_text
    input_uses_fixed_model = "prob.leak_model = fixed_mass_flow" in input_text
    input_uses_scheduled_valve = all(
        token in input_text
        for token in (
            "prob.leak_valve_initial_fraction = 0.0",
            "prob.leak_valve_final_fraction = 1.0",
            "prob.leak_valve_open_time =",
            "prob.leak_valve_ramp_time =",
        )
    )

    bad_tokens = sorted({token for token in BAD_LOG_TOKENS if token in log_text})
    scheduled_log_lines = [
        line for line in log_text.splitlines() if "leak fixed-mass-flow schedule:" in line
    ]
    applying_lines = [
        line
        for line in log_text.splitlines()
        if "Applying H2 leak source: model=fixed_mass_flow_scheduled" in line
    ]
    valve_fractions = parse_float_series(r"valve_fraction_mid=([0-9.eE+-]+)", "\n".join(scheduled_log_lines))
    effective_mdots = parse_float_series(r"effective_mdot=([0-9.eE+-]+)", "\n".join(scheduled_log_lines))
    applied_mdots = parse_float_series(
        r"Applying H2 leak source: model=fixed_mass_flow_scheduled, mdot=([0-9.eE+-]+)",
        log_text,
    )
    leak_source_mdots = parse_float_series(r"H2 leak source\[[0-9]+\]: .*?, mdot=([0-9.eE+-]+)", log_text)

    nonzero_mdots = [value for value in effective_mdots if value > 0.0]
    mdot_varies = bool(effective_mdots) and min(effective_mdots) < max(effective_mdots)
    schedule_reaches_closed = bool(valve_fractions) and min(valve_fractions) == 0.0
    schedule_reaches_open = bool(valve_fractions) and max(valve_fractions) >= 1.0
    applied_matches_effective = applied_mdots == effective_mdots[: len(applied_mdots)]

    ready = (
        source_scales_fixed_mdot
        and source_prints_schedule
        and input_uses_fixed_model
        and input_uses_scheduled_valve
        and not bad_tokens
        and len(scheduled_log_lines) >= 5
        and len(applying_lines) >= 5
        and mdot_varies
        and schedule_reaches_closed
        and schedule_reaches_open
        and len(nonzero_mdots) >= 3
        and applied_matches_effective
        and bool(leak_source_mdots)
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-FIXED-MASS-FLOW-VALVE-SCHEDULE",
        "summary": {
            "fixed_mass_flow_valve_schedule_ready": ready,
            "source_scales_fixed_mdot": source_scales_fixed_mdot,
            "source_prints_schedule": source_prints_schedule,
            "input_uses_fixed_model": input_uses_fixed_model,
            "input_uses_scheduled_valve": input_uses_scheduled_valve,
            "log_has_no_abort_or_nan": not bad_tokens,
            "bad_log_tokens": bad_tokens,
            "scheduled_log_line_count": len(scheduled_log_lines),
            "applying_line_count": len(applying_lines),
            "valve_fraction_min": min(valve_fractions) if valve_fractions else None,
            "valve_fraction_max": max(valve_fractions) if valve_fractions else None,
            "effective_mdot_min": min(effective_mdots) if effective_mdots else None,
            "effective_mdot_max": max(effective_mdots) if effective_mdots else None,
            "effective_mdot_varies": mdot_varies,
            "schedule_reaches_closed": schedule_reaches_closed,
            "schedule_reaches_open": schedule_reaches_open,
            "nonzero_effective_mdot_count": len(nonzero_mdots),
            "applied_mdot_matches_effective_mdot": applied_matches_effective,
            "leak_source_line_count": len(leak_source_mdots),
        },
        "log_samples": {
            "first_schedule_line": scheduled_log_lines[0] if scheduled_log_lines else "",
            "last_schedule_line": scheduled_log_lines[-1] if scheduled_log_lines else "",
            "effective_mdots": effective_mdots,
            "valve_fractions": valve_fractions,
        },
        "evidence_files": [
            evidence_entry("problem_header", PROB_HEADER),
            evidence_entry("smoke_input", SMOKE_INPUT),
            evidence_entry("smoke_log", SMOKE_LOG),
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("fixed_mass_flow_valve_schedule_ready") is True, "fixed schedule report is not ready")
    require(summary.get("source_scales_fixed_mdot") is True, "source does not scale fixed mdot")
    require(summary.get("source_prints_schedule") is True, "source does not print fixed schedule details")
    require(summary.get("input_uses_fixed_model") is True, "input does not use fixed_mass_flow")
    require(summary.get("input_uses_scheduled_valve") is True, "input does not configure valve schedule")
    require(summary.get("log_has_no_abort_or_nan") is True, "smoke log contains abort/nan markers")
    require(summary.get("scheduled_log_line_count", 0) >= 5, "too few schedule log lines")
    require(summary.get("applying_line_count", 0) >= 5, "too few applying log lines")
    require(summary.get("schedule_reaches_closed") is True, "schedule did not reach closed state")
    require(summary.get("schedule_reaches_open") is True, "schedule did not reach open state")
    require(summary.get("effective_mdot_varies") is True, "effective mdot did not vary")
    require(summary.get("nonzero_effective_mdot_count", 0) >= 3, "too few nonzero mdot samples")
    require(summary.get("applied_mdot_matches_effective_mdot") is True, "applied mdot does not match effective mdot")
    require(summary.get("leak_source_line_count", 0) >= 5, "too few leak source log lines")
    if verify_hashes:
        for item in data.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"evidence sha256 mismatch: {path}")


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = report["summary"]
    lines = [
        "# Engineering Fixed-Mass-Flow Valve Schedule",
        "",
        f"- Status: `{report['status']}`",
        f"- Source scales fixed mdot: `{summary['source_scales_fixed_mdot']}`",
        f"- Smoke log clean: `{summary['log_has_no_abort_or_nan']}`",
        f"- Schedule fraction range: `{summary['valve_fraction_min']}` to `{summary['valve_fraction_max']}`",
        f"- Effective mdot range: `{summary['effective_mdot_min']}` to `{summary['effective_mdot_max']}`",
        f"- Applied mdot matches effective mdot: `{summary['applied_mdot_matches_effective_mdot']}`",
        "",
        "## Evidence",
        "",
    ]
    for item in report["evidence_files"]:
        lines.append(f"- `{item['label']}`: `{item['path']}`")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data)
            print(f"engineering_fixed_mass_flow_valve_schedule VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        validate_report(report, verify_hashes=False)
        write_outputs(report, Path(args.output_json), Path(args.output_md))
        print(f"engineering_fixed_mass_flow_valve_schedule {report['status']} json={args.output_json}")
        return 0
    except ScheduleReportError as exc:
        print(f"engineering_fixed_mass_flow_valve_schedule ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
