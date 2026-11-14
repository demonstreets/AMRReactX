#!/usr/bin/env python3
"""Write/verify the current-scope delivery package manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE"
VOLATILE_HASH_LABELS = {"current_scope_state_snapshot"}

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_scope_delivery_package_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_scope_delivery_package_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_scope_delivery_package_report.md"

RELEASE_CANDIDATE = Path(
    "docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/"
    "current_scope_release_candidate_handoff_report.json"
)
CLOSEOUT_FORECAST = Path(
    "docs/codex_audit/evidence/project_closeout_forecast_20260812/"
    "project_closeout_forecast_report.json"
)
STRICT_COMPLETION_GATE = Path(
    "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
    "strict_master_plan_completion_gate_report.json"
)
STRICT_ARTIFACT_DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
STRICT_ARTIFACT_DROP_CHECKLIST = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/"
    "strict_external_artifact_drop_checklist_report.json"
)
FINAL_READINESS = Path(
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
    "master_plan_final_readiness_report.json"
)
COMPLETION_AUDIT = Path(
    "docs/codex_audit/evidence/master_plan_completion_audit_20260803/"
    "master_plan_completion_audit_report.json"
)
PARALLEL_MATRIX = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)
SCENARIO_MATRIX = Path(
    "docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805/"
    "current_scenario_readiness_matrix_report.json"
)
OPERATOR_RUNBOOK = Path(
    "docs/codex_audit/evidence/current_scope_operator_runbook_20260803/"
    "current_scope_operator_runbook_report.json"
)
COMMAND_INVENTORY = Path(
    "docs/codex_audit/evidence/current_operator_command_inventory_20260803/"
    "current_operator_command_inventory_report.json"
)
STATE_SNAPSHOT = Path(
    "docs/codex_audit/evidence/current_scope_state_snapshot_20260803/"
    "current_scope_state_snapshot_report.json"
)
FULL_LOG_DIR = Path("docs/codex_audit/evidence/current_scope_last_run_20260807")
FULL_LOG_GLOB = "current_scope_verify_after_*.log"
README = Path("README.md")
CURRENT_SCOPE_RUNBOOK_MD = Path("docs/codex_audit/current_scope_operator_runbook.md")
USER_GUIDES_INDEX = Path("docs/user_guides/README.md")
USER_GUIDES_INDEX_REPORT = Path(
    "docs/codex_audit/evidence/user_guides_index_20260818/"
    "user_guides_index_report.json"
)
USER_GUIDES_INDEX_VERIFY = Path("tools/verify_user_guides_index.sh")
COMPLETE_WALKTHROUGH_GUIDE = Path("docs/user_guides/从目录到排错_完整运行教程.md")
COMPLETE_WALKTHROUGH_REPORT = Path(
    "docs/codex_audit/evidence/complete_walkthrough_guide_20260818/"
    "complete_walkthrough_guide_report.json"
)
REAL_CASE_INTAKE_GUIDE = Path("docs/user_guides/真实工程资料交付与复验清单.md")
REAL_CASE_INTAKE_REPORT = Path(
    "docs/codex_audit/evidence/real_case_intake_guide_20260817/"
    "real_case_intake_guide_report.json"
)
STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_GUIDE = Path("docs/user_guides/真实资料投递清单_按文件路径.md")
STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_REPORT = Path(
    "docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/"
    "strict_external_artifact_cn_handoff_report.json"
)
STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_VERIFY = Path("tools/verify_strict_external_artifact_cn_handoff.sh")

REQUIRED_COMMANDS = [
    "bash tools/codex_verify_current_scope.sh",
    "python3 tools/codex_print_current_status.py",
    "python3 tools/codex_print_current_status.py --json",
    "python3 tools/write_current_scope_release_candidate_handoff_report.py",
    "bash tools/verify_current_scope_release_candidate_handoff.sh",
    "python3 tools/write_project_closeout_forecast_report.py",
    "bash tools/verify_project_closeout_forecast.sh",
    "python3 tools/write_strict_master_plan_completion_gate_report.py",
    "bash tools/verify_strict_master_plan_completion_gate.sh",
    "python3 tools/write_strict_external_artifact_drop_index_report.py",
    "bash tools/verify_strict_external_artifact_drop_index.sh",
    "python3 tools/write_strict_external_artifact_drop_checklist_report.py",
    "bash tools/verify_strict_external_artifact_drop_checklist.sh",
    "python3 tools/write_strict_external_artifact_cn_handoff_report.py",
    "bash tools/verify_strict_external_artifact_cn_handoff.sh",
    "python3 tools/write_user_guides_index_report.py",
    "bash tools/verify_user_guides_index.sh",
    "python3 tools/write_current_scope_delivery_package_report.py",
    "bash tools/verify_current_scope_delivery_package.sh",
]

EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class DeliveryPackageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DeliveryPackageError(message)


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
        raise DeliveryPackageError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DeliveryPackageError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    entry = {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    if label in VOLATILE_HASH_LABELS:
        entry["hash_verification"] = "skipped-cycle-reference"
    return entry


def log_has_success(path: Path) -> bool:
    require(path.is_file(), f"missing full verification log: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    return "[current-scope] PASS current-scope verification chain" in text and "CURRENT_SCOPE_RC=0" in text


def latest_passing_full_log() -> Path:
    require(FULL_LOG_DIR.is_dir(), f"missing full verification log directory: {FULL_LOG_DIR}")
    candidates = sorted(FULL_LOG_DIR.glob(FULL_LOG_GLOB), key=lambda path: path.stat().st_mtime, reverse=True)
    require(candidates, f"no full verification logs match {FULL_LOG_DIR / FULL_LOG_GLOB}")
    for path in candidates:
        if log_has_success(path):
            return path
    raise DeliveryPackageError(f"no passing full verification log found under {FULL_LOG_DIR}")


def command_inventory_contains(command_inventory: dict[str, Any], command: str) -> bool:
    return any(item.get("command") == command for item in command_inventory.get("commands", []))


def build_report() -> dict[str, Any]:
    release = load_json(RELEASE_CANDIDATE)
    closeout = load_json(CLOSEOUT_FORECAST)
    strict_gate = load_json(STRICT_COMPLETION_GATE)
    drop_index = load_json(STRICT_ARTIFACT_DROP_INDEX)
    drop_checklist = load_json(STRICT_ARTIFACT_DROP_CHECKLIST)
    final = load_json(FINAL_READINESS)
    completion = load_json(COMPLETION_AUDIT)
    parallel = load_json(PARALLEL_MATRIX)
    scenarios = load_json(SCENARIO_MATRIX)
    runbook = load_json(OPERATOR_RUNBOOK)
    commands = load_json(COMMAND_INVENTORY)
    snapshot = load_json(STATE_SNAPSHOT)
    user_guides = load_json(USER_GUIDES_INDEX_REPORT)
    complete_walkthrough = load_json(COMPLETE_WALKTHROUGH_REPORT)
    real_case_intake = load_json(REAL_CASE_INTAKE_REPORT)
    strict_external_artifact_cn_handoff = load_json(STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_REPORT)

    rsum = release["summary"]
    closeoutsum = closeout["summary"]
    strictgatesum = strict_gate["summary"]
    dropindexsum = drop_index["summary"]
    dropchecklistsum = drop_checklist["summary"]
    fsum = final["summary"]
    csum = completion["summary"]
    psum = parallel["summary"]
    ssum = scenarios["summary"]
    runbooksum = runbook["summary"]
    commandsum = commands["summary"]
    snapshotsum = snapshot["summary"]
    cn_handoff_sum = strict_external_artifact_cn_handoff["summary"]
    open_blockers = set(completion.get("open_strict_blockers", [])) or set(csum.get("open_strict_blockers", []))

    missing_commands = [cmd for cmd in REQUIRED_COMMANDS if not command_inventory_contains(commands, cmd)]
    last_full_log = latest_passing_full_log()
    full_log_passed = log_has_success(last_full_log)

    package_ready = all(
        [
            release.get("status") == "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF",
            rsum.get("release_candidate_handoff_ready") is True,
            closeout.get("status") == "PASS-PROJECT-CLOSEOUT-FORECAST",
            closeoutsum.get("current_scope_can_be_closed_now") is True,
            closeoutsum.get("strict_master_plan_can_be_closed_now") is False,
            strict_gate.get("status") == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS",
            strictgatesum.get("strict_master_plan_completion_gate_ready") is True,
            strictgatesum.get("current_scope_closure_allowed") is True,
            strictgatesum.get("strict_master_plan_completion_allowed") is False,
            drop_index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
            dropindexsum.get("strict_external_artifact_drop_index_ready") is True,
            drop_checklist.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST",
            dropchecklistsum.get("strict_external_artifact_drop_checklist_ready") is True,
            final.get("status") == "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS",
            fsum.get("current_user_priority_ready") is True,
            parallel.get("status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX",
            psum.get("cpu_mpi_ready_for_all_current_scenarios") is True,
            psum.get("single_gpu_ready_for_all_current_scenarios") is True,
            psum.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True,
            scenarios.get("status") == "PASS-CURRENT-SCENARIO-READINESS-MATRIX",
            ssum.get("ready_scenario_count") == ssum.get("scenario_count") == 4,
            runbooksum.get("operator_runbook_ready") is True,
            commandsum.get("current_operator_command_inventory_ready") is True,
            snapshotsum.get("current_scope_state_snapshot_ready") is True,
            USER_GUIDES_INDEX.is_file(),
            USER_GUIDES_INDEX_VERIFY.is_file(),
            user_guides.get("status") == "PASS-USER-GUIDES-INDEX",
            COMPLETE_WALKTHROUGH_GUIDE.is_file(),
            complete_walkthrough.get("status") == "PASS-COMPLETE-WALKTHROUGH-GUIDE",
            REAL_CASE_INTAKE_GUIDE.is_file(),
            real_case_intake.get("status") == "PASS-REAL-CASE-INTAKE-GUIDE",
            STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_GUIDE.is_file(),
            STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_VERIFY.is_file(),
            strict_external_artifact_cn_handoff.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF",
            cn_handoff_sum.get("strict_external_artifact_cn_handoff_ready") is True,
            cn_handoff_sum.get("required_file_count") == 14,
            cn_handoff_sum.get("missing_file_count") == dropchecklistsum["missing_file_count"],
            open_blockers == EXPECTED_STRICT_BLOCKERS,
            csum.get("strict_master_plan_complete") is False,
            csum.get("goal_complete") is False,
            full_log_passed,
            not missing_commands,
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "current-scope delivery package manifest for the usable release candidate",
        "summary": {
            "current_scope_delivery_package_ready": package_ready,
            "release_candidate_ready": rsum["release_candidate_handoff_ready"],
            "current_scope_can_be_closed_now": closeoutsum["current_scope_can_be_closed_now"],
            "current_scope_closeout_estimate": closeoutsum["current_scope_closeout_estimate"],
            "strict_master_plan_complete": csum["strict_master_plan_complete"],
            "strict_master_plan_can_be_closed_now": closeoutsum["strict_master_plan_can_be_closed_now"],
            "strict_master_plan_completion_gate_status": strict_gate["status"],
            "strict_master_plan_completion_gate_ready": strictgatesum[
                "strict_master_plan_completion_gate_ready"
            ],
            "strict_completion_current_scope_closure_allowed": strictgatesum[
                "current_scope_closure_allowed"
            ],
            "strict_completion_allowed": strictgatesum["strict_master_plan_completion_allowed"],
            "strict_completion_external_artifacts_missing": strictgatesum["strict_external_artifacts_missing"],
            "strict_external_artifact_drop_index_status": drop_index["status"],
            "strict_external_artifact_drop_index_ready": dropindexsum[
                "strict_external_artifact_drop_index_ready"
            ],
            "strict_external_artifact_drop_index_domain_count": dropindexsum["domain_count"],
            "strict_external_artifact_drop_index_contract_check_count": dropindexsum["contract_check_count"],
            "strict_external_artifact_drop_checklist_status": drop_checklist["status"],
            "strict_external_artifact_drop_checklist_ready": dropchecklistsum[
                "strict_external_artifact_drop_checklist_ready"
            ],
            "strict_external_artifact_drop_checklist_required_file_count": dropchecklistsum["required_file_count"],
            "strict_external_artifact_drop_checklist_missing_file_count": dropchecklistsum["missing_file_count"],
            "strict_external_artifact_drop_checklist_done_count": dropchecklistsum["checklist_done_count"],
            "strict_external_artifact_cn_handoff_status": strict_external_artifact_cn_handoff["status"],
            "strict_external_artifact_cn_handoff_ready": cn_handoff_sum[
                "strict_external_artifact_cn_handoff_ready"
            ],
            "strict_external_artifact_cn_handoff_required_file_count": cn_handoff_sum["required_file_count"],
            "strict_external_artifact_cn_handoff_missing_file_count": cn_handoff_sum["missing_file_count"],
            "strict_closeout_requires_external_artifacts": closeoutsum[
                "strict_closeout_requires_external_artifacts"
            ],
            "open_strict_blocker_count": csum["open_strict_blocker_count"],
            "open_strict_blockers": sorted(open_blockers),
            "scenario_count": ssum["scenario_count"],
            "ready_scenario_count": ssum["ready_scenario_count"],
            "cpu_mpi_ready_for_all_current_scenarios": psum["cpu_mpi_ready_for_all_current_scenarios"],
            "single_gpu_ready_for_all_current_scenarios": psum["single_gpu_ready_for_all_current_scenarios"],
            "multi_gpu_mpi_cuda_ready_for_all_current_scenarios": psum[
                "multi_gpu_mpi_cuda_ready_for_all_current_scenarios"
            ],
            "operator_runbook_ready": runbooksum["operator_runbook_ready"],
            "command_inventory_ready": commandsum["current_operator_command_inventory_ready"],
            "state_snapshot_ready": snapshotsum["current_scope_state_snapshot_ready"],
            "last_full_current_scope_log": str(last_full_log),
            "last_full_current_scope_log_glob": str(FULL_LOG_DIR / FULL_LOG_GLOB),
            "last_full_current_scope_log_passed": full_log_passed,
            "required_operator_command_count": len(REQUIRED_COMMANDS),
            "missing_required_operator_command_count": len(missing_commands),
        },
        "delivery_entrypoints": {
            "readme": str(README),
            "operator_runbook": str(CURRENT_SCOPE_RUNBOOK_MD),
            "user_guides_index": str(USER_GUIDES_INDEX),
            "user_guides_index_report": str(USER_GUIDES_INDEX_REPORT),
            "user_guides_index_verify": "bash tools/verify_user_guides_index.sh",
            "complete_walkthrough_guide": str(COMPLETE_WALKTHROUGH_GUIDE),
            "real_case_intake_guide": str(REAL_CASE_INTAKE_GUIDE),
            "strict_external_artifact_cn_handoff_guide": str(STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_GUIDE),
            "strict_external_artifact_cn_handoff_report": str(STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_REPORT),
            "strict_external_artifact_cn_handoff_verify": (
                "bash tools/verify_strict_external_artifact_cn_handoff.sh"
            ),
            "status_cli_text": "python3 tools/codex_print_current_status.py",
            "status_cli_json": "python3 tools/codex_print_current_status.py --json",
            "full_current_scope_verification": "bash tools/codex_verify_current_scope.sh",
        },
        "required_commands": REQUIRED_COMMANDS,
        "missing_required_commands": missing_commands,
        "do_not_claim": closeout["closeout_decision"]["do_not_claim"],
        "can_claim_for_current_scope": closeout["closeout_decision"]["can_claim_for_current_scope"],
        "evidence_files": [
            evidence_entry("current_scope_release_candidate_handoff", RELEASE_CANDIDATE),
            evidence_entry("project_closeout_forecast", CLOSEOUT_FORECAST),
            evidence_entry("strict_master_plan_completion_gate", STRICT_COMPLETION_GATE),
            evidence_entry("strict_external_artifact_drop_index", STRICT_ARTIFACT_DROP_INDEX),
            evidence_entry("strict_external_artifact_drop_checklist", STRICT_ARTIFACT_DROP_CHECKLIST),
            evidence_entry("master_plan_final_readiness", FINAL_READINESS),
            evidence_entry("master_plan_completion_audit", COMPLETION_AUDIT),
            evidence_entry("current_parallel_capability_matrix", PARALLEL_MATRIX),
            evidence_entry("current_scenario_readiness_matrix", SCENARIO_MATRIX),
            evidence_entry("current_scope_operator_runbook", OPERATOR_RUNBOOK),
            evidence_entry("current_operator_command_inventory", COMMAND_INVENTORY),
            evidence_entry("current_scope_state_snapshot", STATE_SNAPSHOT),
            evidence_entry("last_full_current_scope_log", last_full_log),
            evidence_entry("readme", README),
            evidence_entry("current_scope_operator_runbook_md", CURRENT_SCOPE_RUNBOOK_MD),
            evidence_entry("user_guides_index", USER_GUIDES_INDEX),
            evidence_entry("user_guides_index_report", USER_GUIDES_INDEX_REPORT),
            evidence_entry("user_guides_index_verify", USER_GUIDES_INDEX_VERIFY),
            evidence_entry("complete_walkthrough_guide", COMPLETE_WALKTHROUGH_GUIDE),
            evidence_entry("complete_walkthrough_guide_report", COMPLETE_WALKTHROUGH_REPORT),
            evidence_entry("real_case_intake_guide", REAL_CASE_INTAKE_GUIDE),
            evidence_entry("real_case_intake_guide_report", REAL_CASE_INTAKE_REPORT),
            evidence_entry("strict_external_artifact_cn_handoff_guide", STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_GUIDE),
            evidence_entry("strict_external_artifact_cn_handoff_report", STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_REPORT),
            evidence_entry("strict_external_artifact_cn_handoff_verify", STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_VERIFY),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_scope_delivery_package_ready") is True, "delivery package is not ready")
    require(summary.get("release_candidate_ready") is True, "release candidate is not ready")
    require(summary.get("current_scope_can_be_closed_now") is True, "current scope is not closable")
    require(summary.get("strict_master_plan_complete") is False, "strict master plan unexpectedly complete")
    require(summary.get("strict_master_plan_can_be_closed_now") is False, "strict closeout overclaimed")
    require(
        summary.get("strict_master_plan_completion_gate_status")
        == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS",
        "strict completion gate status is unexpected",
    )
    require(summary.get("strict_master_plan_completion_gate_ready") is True, "strict completion gate is not ready")
    require(
        summary.get("strict_completion_current_scope_closure_allowed") is True,
        "strict completion gate does not allow current-scope closure",
    )
    require(summary.get("strict_completion_allowed") is False, "strict completion gate overclaims completion")
    require(
        summary.get("strict_completion_external_artifacts_missing") is True,
        "strict completion gate lost external-artifact boundary",
    )
    require(
        summary.get("strict_external_artifact_drop_index_status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
        "strict external artifact drop index status is not passing",
    )
    require(
        summary.get("strict_external_artifact_drop_index_ready") is True,
        "strict external artifact drop index is not ready",
    )
    require(summary.get("strict_external_artifact_drop_index_domain_count") == 3, "unexpected drop index domain count")
    require(
        summary.get("strict_external_artifact_drop_index_contract_check_count") == 14,
        "unexpected drop index contract check count",
    )
    require(
        summary.get("strict_external_artifact_drop_checklist_status")
        == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST",
        "strict external artifact drop checklist status is not passing",
    )
    require(
        summary.get("strict_external_artifact_drop_checklist_ready") is True,
        "strict external artifact drop checklist is not ready",
    )
    require(
        summary.get("strict_external_artifact_drop_checklist_required_file_count") == 14,
        "unexpected drop checklist required file count",
    )
    checklist_missing_count = summary.get("strict_external_artifact_drop_checklist_missing_file_count")
    checklist_done_count = summary.get("strict_external_artifact_drop_checklist_done_count")
    require(isinstance(checklist_missing_count, int), "drop checklist missing count is not an integer")
    require(isinstance(checklist_done_count, int), "drop checklist done count is not an integer")
    require(0 <= checklist_missing_count <= 14, "drop checklist missing count is outside the contract range")
    require(0 <= checklist_done_count <= 14, "drop checklist done count is outside the contract range")
    require(
        checklist_missing_count + checklist_done_count == 14,
        "drop checklist done and missing counts do not match contract total",
    )
    require(
        summary.get("strict_external_artifact_cn_handoff_status")
        == "PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF",
        "strict external artifact Chinese handoff status is not passing",
    )
    require(
        summary.get("strict_external_artifact_cn_handoff_ready") is True,
        "strict external artifact Chinese handoff is not ready",
    )
    require(
        summary.get("strict_external_artifact_cn_handoff_required_file_count") == 14,
        "unexpected Chinese handoff required file count",
    )
    require(
        summary.get("strict_external_artifact_cn_handoff_missing_file_count") == checklist_missing_count,
        "Chinese handoff missing count disagrees with drop checklist",
    )
    require(summary.get("strict_closeout_requires_external_artifacts") is True, "external artifact boundary missing")
    require(summary.get("open_strict_blocker_count") == 3, "unexpected strict blocker count")
    require(set(summary.get("open_strict_blockers", [])) == EXPECTED_STRICT_BLOCKERS, "unexpected strict blocker set")
    require(summary.get("scenario_count") == 4, "unexpected scenario count")
    require(summary.get("ready_scenario_count") == 4, "not all scenarios are ready")
    require(summary.get("cpu_mpi_ready_for_all_current_scenarios") is True, "CPU/MPI readiness missing")
    require(summary.get("single_gpu_ready_for_all_current_scenarios") is True, "single GPU readiness missing")
    require(summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True, "MPI+CUDA readiness missing")
    require(summary.get("operator_runbook_ready") is True, "operator runbook not ready")
    require(summary.get("command_inventory_ready") is True, "command inventory not ready")
    require(summary.get("state_snapshot_ready") is True, "state snapshot not ready")
    require(summary.get("last_full_current_scope_log_passed") is True, "last full current-scope log did not pass")
    require(summary.get("missing_required_operator_command_count") == 0, "missing required operator commands")
    entrypoints = data.get("delivery_entrypoints")
    require(isinstance(entrypoints, dict), "missing delivery entrypoints")
    require(Path(entrypoints["readme"]).is_file(), "missing README entrypoint")
    require(Path(entrypoints["operator_runbook"]).is_file(), "missing operator runbook entrypoint")
    require(
        Path(entrypoints["strict_external_artifact_cn_handoff_guide"]).is_file(),
        "missing Chinese handoff guide entrypoint",
    )
    require(data.get("missing_required_commands") == [], "missing required commands list is not empty")
    require(len(data.get("do_not_claim", [])) >= 5, "claim boundary is too weak")
    require(len(data.get("can_claim_for_current_scope", [])) >= 4, "current claim list is too weak")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            if entry.get("label") in VOLATILE_HASH_LABELS:
                require(
                    entry.get("hash_verification") == "skipped-cycle-reference",
                    f"missing cycle-reference hash policy for {path}",
                )
                continue
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current-Scope Delivery Package",
        "",
        f"- Status: `{report['status']}`",
        f"- Delivery package ready: `{summary['current_scope_delivery_package_ready']}`",
        f"- Current scope can be closed now: `{summary['current_scope_can_be_closed_now']}`",
        f"- Current scope closeout estimate: `{summary['current_scope_closeout_estimate']}`",
        f"- Strict master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Strict completion gate: `{summary['strict_master_plan_completion_gate_status']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        f"- Strict external artifact drop index: `{summary['strict_external_artifact_drop_index_status']}`",
        f"- Strict external artifact drop checklist: `{summary['strict_external_artifact_drop_checklist_status']}`",
        f"- Strict closeout requires external artifacts: `{summary['strict_closeout_requires_external_artifacts']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        f"- Last full current-scope log passed: `{summary['last_full_current_scope_log_passed']}`",
        "",
        "## Entrypoints",
        "",
    ]
    for label, value in report["delivery_entrypoints"].items():
        lines.append(f"- `{label}`: `{value}`")
    lines.extend(["", "## Required Commands", ""])
    for command in report["required_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Can Claim For Current Scope", ""])
    for item in report["can_claim_for_current_scope"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Do Not Claim", ""])
    for item in report["do_not_claim"]:
        lines.append(f"- {item}")
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
        print(f"current_scope_delivery_package VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_scope_delivery_package PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
