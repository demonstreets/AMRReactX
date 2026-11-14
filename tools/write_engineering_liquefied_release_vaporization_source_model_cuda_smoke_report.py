#!/usr/bin/env python3
"""Write/verify CUDA runtime smoke evidence for generated liquefied-release gas-source inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.md"

RUN_SCRIPT = Path("tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh")
SOURCE_MODEL_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
    "engineering_liquefied_release_vaporization_source_model_report.json"
)
SOURCE_MODEL_NEGATIVE = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/"
    "engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json"
)
CASE_SPECS = {
    "lng_ch4": {
        "species": "CH4",
        "input": Path(
            "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
            "lng_ch4_screening_release/input.lng_ch4_screening_release.generated"
        ),
        "mapping": Path(
            "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
            "lng_ch4_screening_release/lng_ch4_screening_release_source_mapping.json"
        ),
        "run_dir": DEFAULT_ROOT / "lng_ch4",
    },
    "lpg_c3h8": {
        "species": "C3H8",
        "input": Path(
            "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
            "lpg_c3h8_screening_release/input.lpg_c3h8_screening_release.generated"
        ),
        "mapping": Path(
            "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
            "lpg_c3h8_screening_release/lpg_c3h8_screening_release_source_mapping.json"
        ),
        "run_dir": DEFAULT_ROOT / "lpg_c3h8",
    },
}
BAD_LOG_PATTERNS = (
    r"\bAbort\b",
    r"AMReX Error",
    r"SIGABRT",
    r"Segmentation fault",
    r"\b[Nn]a[Nn]\b",
    r"\binf\b",
    r"\bINF\b",
    r"CUDA error",
    r"cudaError",
    r"CVODE failed",
)


class CudaSmokeReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CudaSmokeReportError(message)


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
        raise CudaSmokeReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CudaSmokeReportError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def bad_markers(text: str) -> list[str]:
    return [pattern for pattern in BAD_LOG_PATTERNS if re.search(pattern, text)]


def parse_float_series(pattern: str, text: str) -> list[float]:
    return [float(match.group(1)) for match in re.finditer(pattern, text)]


def validate_case(label: str, spec: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(spec["run_dir"])
    species = str(spec["species"])
    run_log = run_dir / "run.log"
    status_file = run_dir / "run.status"
    executable_log = run_dir / "executable.log"
    staged_input = run_dir / Path(spec["input"]).name
    stl = run_dir / "codex_merged_pipe_rack_obstacles.stl"
    for path in (run_log, status_file, executable_log, staged_input, stl, spec["input"], spec["mapping"]):
        require(Path(path).is_file(), f"{label} missing evidence: {path}")

    mapping = load_json(Path(spec["mapping"]))
    source_series = mapping.get("source_time_series", {})
    require(mapping.get("status") == "PASS-EXTERNAL-VAPORIZATION-SOURCE-INPUT", f"{label} mapping is not passing")
    require(source_series.get("fuel_species") == species, f"{label} mapping species drifted")
    require(source_series.get("emitted_to_input") is True, f"{label} mapping did not emit schedule")

    status_text = status_file.read_text(encoding="utf-8", errors="replace")
    run_text = run_log.read_text(encoding="utf-8", errors="replace")
    input_text = staged_input.read_text(encoding="utf-8", errors="replace")
    bad = bad_markers(run_text)
    steps = [int(value) for value in re.findall(r"STEP \[([0-9]+)\]", run_text)]
    schedule_lines = [line for line in run_text.splitlines() if "fixed-mass-flow schedule:" in line]
    schedule_text = "\n".join(schedule_lines)
    mdots = parse_float_series(r"scheduled_reference_mdot=([0-9.eE+-]+)", schedule_text)
    effective_mdots = parse_float_series(r"effective_mdot=([0-9.eE+-]+)", schedule_text)
    velocities = parse_float_series(r"scheduled_velocity=\(([0-9.eE+-]+),", schedule_text)

    unused_block = ""
    match = re.search(r"Unused ParmParse Variables:(.*?)(?:\n\n|Total GPU global memory)", run_text, flags=re.S)
    if match:
        unused_block = match.group(1)
    leak_schedule_unused = "prob.leak_schedule" in unused_block
    ready = (
        "run_rc=0" in status_text
        and f"Engineering leak fuel species: name={species}" in run_text
        and "CUDA initialized" in run_text
        and "Total GPU global memory" in run_text
        and "built AMReX EB2 IndexSpace from codex_merged_pipe_rack_obstacles.stl" in run_text
        and "AMReX" in run_text
        and "finalized" in run_text
        and not bad
        and len(steps) >= 5
        and max(steps or [0]) >= 5
        and len(schedule_lines) >= 5
        and bool(mdots)
        and min(mdots) < max(mdots)
        and bool(effective_mdots)
        and max(effective_mdots) > 0.0
        and bool(velocities)
        and max(velocities) > 0.0
        and f"prob.fuel_species = {species}" in input_text
        and "prob.leak_schedule_count = 9" in input_text
        and not leak_schedule_unused
    )
    return {
        "label": label,
        "species": species,
        "status": "PASS-GENERATED-LIQUEFIED-SOURCE-CUDA-SMOKE" if ready else "NOT_READY-GENERATED-LIQUEFIED-SOURCE-CUDA-SMOKE",
        "ready": ready,
        "run_returncode_zero": "run_rc=0" in status_text,
        "cuda_initialized": "CUDA initialized" in run_text,
        "gpu_memory_reported": "Total GPU global memory" in run_text,
        "stl_obstacles_built": "built AMReX EB2 IndexSpace from codex_merged_pipe_rack_obstacles.stl" in run_text,
        "run_finalized": "AMReX" in run_text and "finalized" in run_text,
        "run_log_has_no_abort_nan_or_cuda_error": not bad,
        "run_bad_markers": bad,
        "steps": steps,
        "schedule_log_line_count": len(schedule_lines),
        "scheduled_reference_mdot_min": min(mdots) if mdots else None,
        "scheduled_reference_mdot_max": max(mdots) if mdots else None,
        "scheduled_reference_mdot_varies": bool(mdots) and min(mdots) < max(mdots),
        "effective_mdot_max": max(effective_mdots) if effective_mdots else None,
        "scheduled_velocity_x_max": max(velocities) if velocities else None,
        "leak_schedule_unused": leak_schedule_unused,
        "input_sha256": sha256_file(Path(spec["input"])),
        "staged_input_sha256": sha256_file(staged_input),
    }


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    source_model = load_json(SOURCE_MODEL_REPORT)
    negative = load_json(SOURCE_MODEL_NEGATIVE)
    require(source_model.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL", "source-model report is not passing")
    require(
        negative.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST",
        "source-model negative selftest is not passing",
    )
    env_log = DEFAULT_ROOT / "environment.log"
    require(env_log.is_file(), f"missing environment log: {env_log}")
    env_text = env_log.read_text(encoding="utf-8", errors="replace")
    cases = [validate_case(label, spec) for label, spec in CASE_SPECS.items()]
    ready = (
        all(case["ready"] for case in cases)
        and "Tesla P100" in env_text
        and "release 12.6" in env_text
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE",
        "summary": {
            "liquefied_release_source_model_cuda_smoke_ready": ready,
            "environment_uses_tesla_p100": "Tesla P100" in env_text,
            "environment_uses_cuda_12_6": "release 12.6" in env_text,
            "source_model_report_passed": source_model.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL",
            "source_model_negative_selftest_passed": negative.get("status")
            == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST",
            "case_count": len(cases),
            "ready_case_count": sum(1 for case in cases if case["ready"]),
            "lng_ch4_generated_input_cuda_smoke_passed": next(case["ready"] for case in cases if case["label"] == "lng_ch4"),
            "lpg_c3h8_generated_input_cuda_smoke_passed": next(case["ready"] for case in cases if case["label"] == "lpg_c3h8"),
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
        },
        "cases": cases,
        "evidence_files": [
            evidence_entry("run_script", RUN_SCRIPT),
            evidence_entry("source_model_report", SOURCE_MODEL_REPORT),
            evidence_entry("source_model_negative_selftest", SOURCE_MODEL_NEGATIVE),
            evidence_entry("environment_log", env_log),
            *[
                evidence_entry(f"{label}_run_log", Path(spec["run_dir"]) / "run.log")
                for label, spec in CASE_SPECS.items()
            ],
            *[
                evidence_entry(f"{label}_run_status", Path(spec["run_dir"]) / "run.status")
                for label, spec in CASE_SPECS.items()
            ],
            *[
                evidence_entry(f"{label}_generated_input", Path(spec["input"]))
                for label, spec in CASE_SPECS.items()
            ],
            *[
                evidence_entry(f"{label}_mapping", Path(spec["mapping"]))
                for label, spec in CASE_SPECS.items()
            ],
        ],
        "limitations": [
            "This is a short CUDA smoke test of generated gas-source inputs, not a production-duration liquid-release validation.",
            "It confirms PeleLMeX can read and advance the generated CH4/LNG-surrogate and C3H8/LPG-surrogate fixed-mass-flow schedules with STL obstacles on CUDA.",
            "It does not implement internal flashing discharge, liquid-pool spread, or pool evaporation physics.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("liquefied_release_source_model_cuda_smoke_ready") is True, "CUDA smoke not ready")
    require(summary.get("environment_uses_tesla_p100") is True, "Tesla P100 evidence missing")
    require(summary.get("environment_uses_cuda_12_6") is True, "CUDA 12.6 evidence missing")
    require(summary.get("source_model_report_passed") is True, "source-model report missing")
    require(summary.get("source_model_negative_selftest_passed") is True, "source-model negative selftest missing")
    require(summary.get("case_count") == 2, "case count changed")
    require(summary.get("ready_case_count") == 2, "not all generated-input CUDA cases passed")
    require(summary.get("lng_ch4_generated_input_cuda_smoke_passed") is True, "LNG CH4 generated input CUDA smoke missing")
    require(summary.get("lpg_c3h8_generated_input_cuda_smoke_passed") is True, "LPG C3H8 generated input CUDA smoke missing")
    require(summary.get("cfd_solves_liquid_phase_change") is False, "must not claim liquid phase-change solving")
    for case in data.get("cases", []):
        require(case.get("ready") is True, f"case not ready: {case.get('label')}")
        require(case.get("run_log_has_no_abort_nan_or_cuda_error") is True, f"case log has bad marker: {case.get('label')}")
        require(case.get("scheduled_reference_mdot_varies") is True, f"case source mdot did not vary: {case.get('label')}")
        require(case.get("leak_schedule_unused") is False, f"case schedule unused: {case.get('label')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Liquefied Release Source Model CUDA Smoke",
        "",
        f"- Status: `{report['status']}`",
        f"- CUDA smoke ready: `{s['liquefied_release_source_model_cuda_smoke_ready']}`",
        f"- LNG CH4 generated input CUDA smoke passed: `{s['lng_ch4_generated_input_cuda_smoke_passed']}`",
        f"- LPG C3H8 generated input CUDA smoke passed: `{s['lpg_c3h8_generated_input_cuda_smoke_passed']}`",
        f"- CFD solves liquid phase change: `{s['cfd_solves_liquid_phase_change']}`",
        "",
        "## Cases",
        "",
    ]
    for case in report["cases"]:
        lines.append(
            f"- `{case['label']}`: species `{case['species']}`, schedule lines `{case['schedule_log_line_count']}`, "
            f"mdot range `{case['scheduled_reference_mdot_min']}`-`{case['scheduled_reference_mdot_max']}`"
        )
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"engineering_liquefied_release_vaporization_source_model_cuda_smoke VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_liquefied_release_vaporization_source_model_cuda_smoke PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except CudaSmokeReportError as exc:
        print(f"engineering_liquefied_release_vaporization_source_model_cuda_smoke FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
