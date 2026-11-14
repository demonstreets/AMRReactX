#!/usr/bin/env python3
"""Write/verify CUDA evidence for external vaporization mdot(t) coupling."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_external_vaporization_timeseries_cuda_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_external_vaporization_timeseries_cuda_report.md"

CPU_REPORT = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/"
    "engineering_external_vaporization_timeseries_report.json"
)
SMOKE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke")
CUDA_EXE = Path("examples/engineering/h2_leak_3d/PeleLMeX3d.gnu.CUDA.ex")
ENV_LOG = DEFAULT_ROOT / "environment.log"
BUILD_LOG = DEFAULT_ROOT / "build_relink.log"
RUN_STATUS = DEFAULT_ROOT / "run_status.txt"
CUDA_RUN_LOG = DEFAULT_ROOT / "fixed_mass_flow_timeseries_cuda.log"
CUDA_SUNDIALS_HOME = str(Path.home() / ".local" / "sundials-cuda-6.4.1")

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
)


class CudaTimeSeriesReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CudaTimeSeriesReportError(message)


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
        raise CudaTimeSeriesReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CudaTimeSeriesReportError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_float_series(pattern: str, text: str) -> list[float]:
    return [float(match.group(1)) for match in re.finditer(pattern, text)]


def bad_markers(text: str) -> list[str]:
    found: list[str] = []
    for pattern in BAD_LOG_PATTERNS:
        if re.search(pattern, text):
            found.append(pattern)
    return found


def build_report() -> dict[str, Any]:
    cpu_report = load_json(CPU_REPORT)
    require(cpu_report.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES", "CPU time-series report is not passing")
    require(SMOKE_INPUT.is_file(), f"missing smoke input: {SMOKE_INPUT}")
    require(CUDA_EXE.is_file(), f"missing CUDA executable: {CUDA_EXE}")
    require(ENV_LOG.is_file(), f"missing CUDA environment log: {ENV_LOG}")
    require(BUILD_LOG.is_file(), f"missing CUDA build log: {BUILD_LOG}")
    require(RUN_STATUS.is_file(), f"missing CUDA run status: {RUN_STATUS}")
    require(CUDA_RUN_LOG.is_file(), f"missing CUDA run log: {CUDA_RUN_LOG}")

    env_text = ENV_LOG.read_text(encoding="utf-8", errors="replace")
    build_text = BUILD_LOG.read_text(encoding="utf-8", errors="replace")
    status_text = RUN_STATUS.read_text(encoding="utf-8", errors="replace")
    run_text = CUDA_RUN_LOG.read_text(encoding="utf-8", errors="replace")

    schedule_lines = [
        line for line in run_text.splitlines() if "leak fixed-mass-flow schedule:" in line
    ]
    schedule_text = "\n".join(schedule_lines)
    scheduled_mdots = parse_float_series(r"scheduled_reference_mdot=([0-9.eE+-]+)", schedule_text)
    scheduled_temps = parse_float_series(r"scheduled_leak_T=([0-9.eE+-]+)", schedule_text)
    scheduled_vx = parse_float_series(r"scheduled_velocity=\(([0-9.eE+-]+),", schedule_text)
    scheduled_vy = parse_float_series(r"scheduled_velocity=\([0-9.eE+-]+,([0-9.eE+-]+),", schedule_text)
    scheduled_vz = parse_float_series(r"scheduled_velocity=\([0-9.eE+-]+,[0-9.eE+-]+,([0-9.eE+-]+)\)", schedule_text)
    scheduled_radius = parse_float_series(r"scheduled_radius=([0-9.eE+-]+)", schedule_text)
    scheduled_x = parse_float_series(r"scheduled_center=\(([0-9.eE+-]+),", schedule_text)
    scheduled_y = parse_float_series(r"scheduled_center=\([0-9.eE+-]+,([0-9.eE+-]+),", schedule_text)
    scheduled_z = parse_float_series(r"scheduled_center=\([0-9.eE+-]+,[0-9.eE+-]+,([0-9.eE+-]+)\)", schedule_text)
    effective_mdots = parse_float_series(r"effective_mdot=([0-9.eE+-]+)", schedule_text)
    applied_mdots = parse_float_series(
        r"Applying H2 leak source: model=fixed_mass_flow_timeseries, mdot=([0-9.eE+-]+)",
        run_text,
    )
    steps = [int(value) for value in re.findall(r"STEP \[([0-9]+)\]", run_text)]
    schedule_counts = parse_float_series(r"schedule_count=([0-9.eE+-]+)", schedule_text)

    run_bad_markers = bad_markers(run_text)
    build_bad_markers = [
        token
        for token in (
            "cannot find -lsundials",
            "ld returned 1 exit status",
            "Error 1",
            "Cuda compilation tools, release 12.0",
        )
        if token in build_text
    ]
    env_uses_p100 = "Tesla P100" in env_text
    env_uses_cuda126 = "release 12.6" in env_text and "/usr/local/cuda-12.6" in env_text
    build_uses_cuda126 = "release 12.6" in build_text
    build_uses_cuda_sundials = CUDA_SUNDIALS_HOME in build_text
    build_passed = "CUDA 12.6 relink PASS" in build_text and not build_bad_markers
    run_rc_ok = "run_rc=0" in status_text
    finalized = "AMReX" in run_text and "finalized" in run_text
    gpu_memory_reported = "Total GPU global memory" in run_text
    schedule_count_ok = bool(schedule_counts) and all(int(value) == 4 for value in schedule_counts)
    mdot_varies = bool(scheduled_mdots) and min(scheduled_mdots) < max(scheduled_mdots)
    temp_varies = bool(scheduled_temps) and min(scheduled_temps) < max(scheduled_temps)
    vx_varies = bool(scheduled_vx) and min(scheduled_vx) < max(scheduled_vx)
    vy_varies = bool(scheduled_vy) and min(scheduled_vy) < max(scheduled_vy)
    vz_varies = bool(scheduled_vz) and min(scheduled_vz) < max(scheduled_vz)
    radius_varies = bool(scheduled_radius) and min(scheduled_radius) < max(scheduled_radius)
    x_varies = bool(scheduled_x) and min(scheduled_x) < max(scheduled_x)
    y_varies = bool(scheduled_y) and min(scheduled_y) < max(scheduled_y)
    z_varies = bool(scheduled_z) and min(scheduled_z) < max(scheduled_z)
    applied_matches_effective = applied_mdots == effective_mdots[: len(applied_mdots)]
    reached_expected_steps = steps == [0, 1, 2, 3, 4, 5]

    ready = (
        env_uses_p100
        and env_uses_cuda126
        and build_uses_cuda126
        and build_uses_cuda_sundials
        and build_passed
        and run_rc_ok
        and finalized
        and gpu_memory_reported
        and not run_bad_markers
        and len(schedule_lines) >= 6
        and reached_expected_steps
        and schedule_count_ok
        and mdot_varies
        and temp_varies
        and vx_varies
        and vy_varies
        and vz_varies
        and radius_varies
        and x_varies
        and y_varies
        and z_varies
        and applied_matches_effective
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA",
        "summary": {
            "external_vaporization_timeseries_cuda_ready": ready,
            "cpu_timeseries_report_passed": cpu_report.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES",
            "environment_uses_tesla_p100": env_uses_p100,
            "environment_uses_cuda_12_6": env_uses_cuda126,
            "build_uses_cuda_12_6": build_uses_cuda126,
            "build_uses_cuda_sundials_home": build_uses_cuda_sundials,
            "build_passed": build_passed,
            "build_bad_markers": build_bad_markers,
            "run_returncode_zero": run_rc_ok,
            "run_finalized": finalized,
            "gpu_memory_reported": gpu_memory_reported,
            "run_log_has_no_abort_nan_or_cuda_error": not run_bad_markers,
            "run_bad_markers": run_bad_markers,
            "step_count": len(steps),
            "steps": steps,
            "reached_expected_steps": reached_expected_steps,
            "schedule_log_line_count": len(schedule_lines),
            "schedule_count_ok": schedule_count_ok,
            "scheduled_reference_mdot_min": min(scheduled_mdots) if scheduled_mdots else None,
            "scheduled_reference_mdot_max": max(scheduled_mdots) if scheduled_mdots else None,
            "scheduled_reference_mdot_varies": mdot_varies,
            "scheduled_leak_T_min": min(scheduled_temps) if scheduled_temps else None,
            "scheduled_leak_T_max": max(scheduled_temps) if scheduled_temps else None,
            "scheduled_leak_T_varies": temp_varies,
            "scheduled_velocity_x_min": min(scheduled_vx) if scheduled_vx else None,
            "scheduled_velocity_x_max": max(scheduled_vx) if scheduled_vx else None,
            "scheduled_velocity_y_min": min(scheduled_vy) if scheduled_vy else None,
            "scheduled_velocity_y_max": max(scheduled_vy) if scheduled_vy else None,
            "scheduled_velocity_z_min": min(scheduled_vz) if scheduled_vz else None,
            "scheduled_velocity_z_max": max(scheduled_vz) if scheduled_vz else None,
            "scheduled_velocity_x_varies": vx_varies,
            "scheduled_velocity_y_varies": vy_varies,
            "scheduled_velocity_z_varies": vz_varies,
            "scheduled_radius_min": min(scheduled_radius) if scheduled_radius else None,
            "scheduled_radius_max": max(scheduled_radius) if scheduled_radius else None,
            "scheduled_radius_varies": radius_varies,
            "scheduled_center_x_min": min(scheduled_x) if scheduled_x else None,
            "scheduled_center_x_max": max(scheduled_x) if scheduled_x else None,
            "scheduled_center_y_min": min(scheduled_y) if scheduled_y else None,
            "scheduled_center_y_max": max(scheduled_y) if scheduled_y else None,
            "scheduled_center_z_min": min(scheduled_z) if scheduled_z else None,
            "scheduled_center_z_max": max(scheduled_z) if scheduled_z else None,
            "scheduled_center_x_varies": x_varies,
            "scheduled_center_y_varies": y_varies,
            "scheduled_center_z_varies": z_varies,
            "applied_mdot_matches_effective_mdot": applied_matches_effective,
        },
        "log_samples": {
            "first_schedule_line": schedule_lines[0] if schedule_lines else "",
            "last_schedule_line": schedule_lines[-1] if schedule_lines else "",
            "scheduled_reference_mdots": scheduled_mdots,
            "scheduled_leak_Ts": scheduled_temps,
            "scheduled_velocity_x": scheduled_vx,
            "scheduled_velocity_y": scheduled_vy,
            "scheduled_velocity_z": scheduled_vz,
            "scheduled_radius": scheduled_radius,
            "scheduled_center_x": scheduled_x,
            "scheduled_center_y": scheduled_y,
            "scheduled_center_z": scheduled_z,
            "effective_mdots": effective_mdots,
        },
        "evidence_files": [
            evidence_entry("cpu_timeseries_report", CPU_REPORT),
            evidence_entry("smoke_input", SMOKE_INPUT),
            evidence_entry("cuda_executable", CUDA_EXE),
            evidence_entry("environment_log", ENV_LOG),
            evidence_entry("build_relink_log", BUILD_LOG),
            evidence_entry("run_status", RUN_STATUS),
            evidence_entry("cuda_run_log", CUDA_RUN_LOG),
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("external_vaporization_timeseries_cuda_ready") is True, "CUDA time-series evidence is not ready")
    require(summary.get("cpu_timeseries_report_passed") is True, "CPU time-series report is not passing")
    require(summary.get("environment_uses_tesla_p100") is True, "CUDA environment is not P100 evidence")
    require(summary.get("environment_uses_cuda_12_6") is True, "CUDA 12.6 environment evidence missing")
    require(summary.get("build_uses_cuda_12_6") is True, "CUDA 12.6 build evidence missing")
    require(summary.get("build_uses_cuda_sundials_home") is True, "CUDA SUNDIALS_HOME evidence missing")
    require(summary.get("build_passed") is True, "CUDA build did not pass")
    require(summary.get("run_returncode_zero") is True, "CUDA run did not return zero")
    require(summary.get("run_finalized") is True, "CUDA run did not finalize")
    require(summary.get("gpu_memory_reported") is True, "CUDA GPU memory report missing")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "CUDA run log has bad markers")
    require(summary.get("reached_expected_steps") is True, "CUDA run did not reach expected six steps")
    require(summary.get("schedule_log_line_count", 0) >= 6, "too few CUDA schedule log lines")
    require(summary.get("schedule_count_ok") is True, "wrong CUDA schedule count")
    require(summary.get("scheduled_reference_mdot_varies") is True, "CUDA mdot(t) did not vary")
    require(summary.get("scheduled_leak_T_varies") is True, "CUDA vapor_T(t) did not vary")
    require(summary.get("scheduled_velocity_x_varies") is True, "CUDA velocity x did not vary")
    require(summary.get("scheduled_velocity_y_varies") is True, "CUDA velocity y did not vary")
    require(summary.get("scheduled_velocity_z_varies") is True, "CUDA velocity z did not vary")
    require(summary.get("scheduled_radius_varies") is True, "CUDA radius did not vary")
    require(summary.get("scheduled_center_x_varies") is True, "CUDA source x did not vary")
    require(summary.get("scheduled_center_y_varies") is True, "CUDA source y did not vary")
    require(summary.get("scheduled_center_z_varies") is True, "CUDA source z did not vary")
    require(summary.get("applied_mdot_matches_effective_mdot") is True, "CUDA applied mdot does not match effective mdot")
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
        "# Engineering External Vaporization Time Series CUDA",
        "",
        f"- Status: `{report['status']}`",
        f"- CUDA 12.6 environment: `{summary['environment_uses_cuda_12_6']}`",
        f"- CUDA SUNDIALS path used: `{summary['build_uses_cuda_sundials_home']}`",
        f"- Run finalized: `{summary['run_finalized']}`",
        f"- Steps: `{summary['steps']}`",
        f"- Smoke log clean: `{summary['run_log_has_no_abort_nan_or_cuda_error']}`",
        f"- Schedule mdot range: `{summary['scheduled_reference_mdot_min']}` to `{summary['scheduled_reference_mdot_max']}`",
        f"- Schedule temperature range: `{summary['scheduled_leak_T_min']}` to `{summary['scheduled_leak_T_max']}`",
        f"- Schedule velocity x range: `{summary['scheduled_velocity_x_min']}` to `{summary['scheduled_velocity_x_max']}`",
        f"- Schedule radius range: `{summary['scheduled_radius_min']}` to `{summary['scheduled_radius_max']}`",
        f"- Schedule center x range: `{summary['scheduled_center_x_min']}` to `{summary['scheduled_center_x_max']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{item['label']}`: `{item['path']}`" for item in report["evidence_files"])
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
            print(f"engineering_external_vaporization_timeseries_cuda VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        validate_report(report, verify_hashes=False)
        write_outputs(report, Path(args.output_json), Path(args.output_md))
        print(f"engineering_external_vaporization_timeseries_cuda {report['status']} json={args.output_json}")
        return 0
    except (CudaTimeSeriesReportError, OSError) as exc:
        print(f"engineering_external_vaporization_timeseries_cuda ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
