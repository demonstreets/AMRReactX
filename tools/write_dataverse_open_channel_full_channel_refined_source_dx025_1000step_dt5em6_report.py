#!/usr/bin/env python3
"""Write/verify the DataverseNO full-channel dx=0.025 refined-source 1000-step dt=5e-6 MPI+CUDA probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA"
ROOT = Path("docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_cuda_20260807")
REPORT = ROOT / "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_report.json"
REPORT_MD = ROOT / "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_report.md"
RUN_LOG = ROOT / "run.log"
VALIDATION_LOG = ROOT / "validation.log"
INPUT_DECK = ROOT / "input.dataverse_full_channel_refined_source_dx025_1000step_dt5em6_3d"
STATUS_TXT = ROOT / "status.txt"
RUN_STATUS = ROOT / "run.status"

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


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {"label": label, "path": str(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def parse_input(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        clean = line.split("#", 1)[0].strip()
        if clean and "=" in clean:
            key, value = clean.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def floats(raw: str) -> list[float]:
    vals = [float(item) for item in raw.split()]
    require(all(math.isfinite(v) for v in vals), f"non-finite values: {raw}")
    return vals


def bad_markers(text: str) -> list[str]:
    return [pattern for pattern in BAD_LOG_PATTERNS if re.search(pattern, text)]


def parse_pass_line(text: str) -> dict[str, Any]:
    line = next((item for item in text.splitlines() if item.startswith("h2_leak_plume_history_validation PASS")), "")
    require(line, "validation PASS line missing")
    out: dict[str, Any] = {"pass_line": line}
    for key, raw in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^ ]+)", line):
        try:
            out[key] = float(raw)
        except ValueError:
            out[key] = raw
    return out


def source_metrics(run_text: str) -> tuple[float, float]:
    match = re.search(r"H2 leak source\[0\]: .* active_volume=([^,]+), mdot_vol=([^\n]+)", run_text)
    require(match is not None, "source metric line missing")
    return float(match.group(1)), float(match.group(2))


def build_report() -> dict[str, Any]:
    for path in (RUN_LOG, VALIDATION_LOG, INPUT_DECK, STATUS_TXT, RUN_STATUS):
        require(path.is_file(), f"missing evidence file: {path}")
    run_text = RUN_LOG.read_text(encoding="utf-8", errors="replace")
    validation_text = VALIDATION_LOG.read_text(encoding="utf-8", errors="replace")
    input_text = INPUT_DECK.read_text(encoding="utf-8", errors="replace")
    status_text = STATUS_TXT.read_text(encoding="utf-8", errors="replace")
    run_status_text = RUN_STATUS.read_text(encoding="utf-8", errors="replace")
    kv = parse_input(input_text)
    prob_lo = floats(kv["geometry.prob_lo"])
    prob_hi = floats(kv["geometry.prob_hi"])
    n_cell = [int(float(item)) for item in kv["amr.n_cell"].split()]
    dx = [(hi - lo) / n for lo, hi, n in zip(prob_lo, prob_hi, n_cell)]
    leak_radius = float(kv["prob.leak_radius"])
    leak_vel_x = float(kv["prob.leak_vel_x"])
    fixed_dt = float(kv["amr.fixed_dt"])
    max_step = int(float(kv["amr.max_step"]))
    plot_int = int(float(kv["amr.plot_int"]))
    active_volume, mdot_vol = source_metrics(run_text)
    cell_volume = dx[0] * dx[1] * dx[2]
    validation = parse_pass_line(validation_text)
    plotfiles = sorted((ROOT / "run").glob("plt*"))
    bad = bad_markers(run_text)
    full_domain = (
        all(abs(v - e) <= 1.0e-12 for v, e in zip(prob_lo, [0.0, 0.0, 0.0]))
        and all(abs(v - e) <= 1.0e-12 for v, e in zip(prob_hi, [5.8, 0.9, 0.8]))
    )
    ready = (
        "DONE" in status_text
        and "run_rc=0" in run_status_text
        and "MPI initialized with 2 MPI processes" in run_text
        and "CUDA initialized with" in run_text
        and "finalized" in run_text
        and not bad
        and "STEP [999]" in run_text
        and (ROOT / "run" / "plt01000").is_dir()
        and len(plotfiles) >= (max_step // plot_int + 1)
        and full_domain
        and all(abs(v - 0.025) <= 1.0e-12 for v in dx)
        and abs(leak_radius - 0.0023) <= 1.0e-15
        and abs(active_volume - cell_volume) <= max(1.0e-18, cell_volume * 1.0e-8)
        and fixed_dt * leak_vel_x / min(dx) < 0.15
        and float(validation.get("mass_ratioN", 0.0)) > 0.0
        and float(validation.get("max_YH2", 0.0)) > 0.0
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA",
        "summary": {
            "full_channel_refined_source_dx025_1000step_dt5em6_ready": ready,
            "full_dataverse_domain": full_domain,
            "mpi_rank_count": 2,
            "cuda_initialized": "CUDA initialized with" in run_text,
            "run_returncode_zero": "run_rc=0" in run_status_text,
            "run_finalized": "finalized" in run_text,
            "run_log_has_no_abort_nan_or_cuda_error": not bad,
            "run_bad_markers": bad,
            "n_cell": n_cell,
            "dx_m": dx,
            "leak_radius_m": leak_radius,
            "active_volume_equals_single_cell": abs(active_volume - cell_volume) <= max(1.0e-18, cell_volume * 1.0e-8),
            "active_volume_m3": active_volume,
            "single_cell_volume_m3": cell_volume,
            "source_cfl": fixed_dt * leak_vel_x / min(dx),
            "max_step": max_step,
            "time_end_s": max_step * fixed_dt,
            "plotfile_count": len(plotfiles),
            "validation_mass_ratio_final": float(validation.get("mass_ratioN", 0.0)),
            "validation_max_yh2": float(validation.get("max_YH2", 0.0)),
            "validation_downstream_fraction": float(validation.get("downstream_fraction", 0.0)),
            "production_agreement_completed": False,
            "clears_external_plume_reference_blocker": False,
            "strict_blocker_still_open": True,
        },
        "validation": validation,
        "limitations": [
            "This is a 1000-step dt=5e-6 full-channel refined-source stability screen, not a production-duration Dataverse plume-shape agreement case.",
            "The strict external plume blocker still requires longer sensor-time-history agreement against the public reference data.",
        ],
        "evidence_files": [
            evidence_entry("run_log", RUN_LOG),
            evidence_entry("validation_log", VALIDATION_LOG),
            evidence_entry("input_deck", INPUT_DECK),
            evidence_entry("status_txt", STATUS_TXT),
            evidence_entry("run_status", RUN_STATUS),
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    s = data.get("summary")
    require(isinstance(s, dict), "summary missing")
    require(s.get("full_channel_refined_source_dx025_1000step_dt5em6_ready") is True, "1000-step dt=5e-6 screen not ready")
    require(s.get("full_dataverse_domain") is True, "not full Dataverse domain")
    require(s.get("mpi_rank_count") == 2, "MPI rank mismatch")
    require(s.get("cuda_initialized") is True, "CUDA missing")
    require(s.get("run_log_has_no_abort_nan_or_cuda_error") is True, "bad runtime marker")
    require(all(abs(float(v) - 0.025) <= 1.0e-12 for v in s.get("dx_m", [])), "dx mismatch")
    require(abs(float(s.get("leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "radius mismatch")
    require(s.get("active_volume_equals_single_cell") is True, "active volume mismatch")
    require(float(s.get("source_cfl", 1.0)) < 0.15, "source CFL too large")
    require(int(s.get("max_step", 0)) == 1000, "max_step mismatch")
    require(abs(float(s.get("time_end_s", 0.0)) - 0.005) <= 1.0e-12, "time_end mismatch")
    require(float(s.get("validation_max_yh2", 0.0)) > 0.0, "no plume")
    require(s.get("clears_external_plume_reference_blocker") is False, "must not clear blocker")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = report["summary"]
    lines = [
        "# DataverseNO Full-Channel Refined-Source dx=0.025 1000-Step dt=5e-6 Probe",
        "",
        f"- Status: `{report['status']}`",
        f"- Full Dataverse domain: `{s['full_dataverse_domain']}`",
        f"- MPI ranks: `{s['mpi_rank_count']}`",
        f"- CUDA initialized: `{s['cuda_initialized']}`",
        f"- Grid: `{s['n_cell']}`",
        f"- dx: `{s['dx_m']}` m",
        f"- Time end: `{s['time_end_s']}` s",
        f"- Max Y(H2): `{s['validation_max_yh2']}`",
        f"- Clears strict external plume blocker: `{s['clears_external_plume_reference_blocker']}`",
        "",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    if args.verify_json:
        data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
        validate_report(data, verify_hashes=True)
        print(f"dataverse_full_channel_refined_source_dx025_1000step_dt5em6 VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0
    report = build_report()
    validate_report(report, verify_hashes=False)
    write_outputs(report, REPORT, REPORT_MD)
    print(f"dataverse_full_channel_refined_source_dx025_1000step_dt5em6 PASS json={REPORT} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
