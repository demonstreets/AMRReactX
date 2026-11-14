#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


REPO = Path.cwd().resolve()
DOCS = REPO / "docs" / "user_guides"
OUT_DIR = REPO / "docs" / "codex_audit" / "evidence" / "user_guides_index_20260818"
STATUS_PASS = "PASS-USER-GUIDES-INDEX"

GUIDES = {
    "readme": "README.md",
    "main_manual": "Pele_CFD_中文使用手册.md",
    "complete_walkthrough": "从目录到排错_完整运行教程.md",
    "from_zero_case_tutorial": "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
    "command_cheatsheet": "命令速查与场景矩阵.md",
    "engineering_tutorial": "工程场景_泄漏扩散火灾_Tutorial.md",
    "academic_tutorial": "学术场景_气相与两相爆轰_Tutorial.md",
    "real_case_intake": "真实工程资料交付与复验清单.md",
    "strict_external_artifact_cn_handoff": "真实资料投递清单_按文件路径.md",
}

CASE_GUIDES = {
    "engineering_h2_leak_quickstart": "examples/engineering/h2_leak_3d/README_中文快速教程.md",
    "academic_detonation_quickstart": "examples/academic/detonation_2D/README_中文快速教程.md",
}

REQUIRED_PATTERNS = {
    "readme_lists_main_manual": ("README.md", "Pele_CFD_中文使用手册.md"),
    "readme_lists_complete_walkthrough": ("README.md", "从目录到排错_完整运行教程.md"),
    "readme_lists_from_zero_case_tutorial": ("README.md", "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md"),
    "readme_lists_command_cheatsheet": ("README.md", "命令速查与场景矩阵.md"),
    "readme_lists_engineering_tutorial": ("README.md", "工程场景_泄漏扩散火灾_Tutorial.md"),
    "readme_lists_academic_tutorial": ("README.md", "学术场景_气相与两相爆轰_Tutorial.md"),
    "readme_lists_real_case_intake": ("README.md", "真实工程资料交付与复验清单.md"),
    "readme_lists_strict_external_artifact_cn_handoff": ("README.md", "真实资料投递清单_按文件路径.md"),
    "readme_lists_engineering_case_quickstart": (
        "README.md",
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
    ),
    "readme_lists_academic_case_quickstart": (
        "README.md",
        "examples/academic/detonation_2D/README_中文快速教程.md",
    ),
    "main_manual_has_directory_section": ("Pele_CFD_中文使用手册.md", "## 1. 项目目录"),
    "main_manual_has_input_section": ("Pele_CFD_中文使用手册.md", "## 2. 输入文件"),
    "main_manual_has_run_section": ("Pele_CFD_中文使用手册.md", "## 3. 推荐运行方式"),
    "main_manual_points_to_from_zero_case_tutorial": (
        "Pele_CFD_中文使用手册.md",
        "docs/user_guides/从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
    ),
    "complete_walkthrough_has_troubleshooting": ("从目录到排错_完整运行教程.md", "## 7. 常见错误怎么查"),
    "complete_walkthrough_has_case_output_cleanup": (
        "从目录到排错_完整运行教程.md",
        "### 7.8 工作区污染和算例输出清理",
    ),
    "complete_walkthrough_has_source_ledger_command": (
        "从目录到排错_完整运行教程.md",
        "python3 tools/write_current_worktree_source_ledger_report.py",
    ),
    "complete_walkthrough_has_cleanup_manifest_command": (
        "从目录到排错_完整运行教程.md",
        "python3 tools/write_current_case_output_cleanup_manifest_report.py",
    ),
    "from_zero_has_engineering_case_dir": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "examples/engineering/h2_leak_3d",
    ),
    "from_zero_has_selected_case_walkthrough": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "本教程选定的两个“照做”案例",
    ),
    "from_zero_has_minimal_file_types": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "算例源码文件",
    ),
    "from_zero_has_first_run_checks": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "跑完以后先看三件事",
    ),
    "from_zero_has_academic_case_dir": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "examples/academic/detonation_2D",
    ),
    "from_zero_has_custom_engineering_input": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "input.my_h2_open_domain",
    ),
    "from_zero_has_custom_academic_input": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "inputs.my_detonation_wave",
    ),
    "from_zero_has_engineering_cpu_command": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "bash tools/codex_smoke_engineering_h2_leak_open_domain.sh",
    ),
    "from_zero_has_engineering_mpi_command": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh",
    ),
    "from_zero_has_engineering_gpu_fire_command": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh",
    ),
    "from_zero_has_engineering_mpi_cuda_restart_command": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh",
    ),
    "from_zero_has_academic_cpu_command": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "bash tools/codex_smoke_academic_detonation_wave.sh",
    ),
    "from_zero_has_academic_mpi_command": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "bash tools/codex_smoke_academic_pelec_mpi.sh",
    ),
    "from_zero_has_academic_gpu_command": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "bash tools/codex_smoke_academic_pelec_cuda.sh",
    ),
    "from_zero_has_outputs_section": (
        "从零设置完整算例_工程H2泄漏火灾与学术爆轰.md",
        "## 4. 学术算例输出怎么看",
    ),
    "command_cheatsheet_has_engineering_h2_section": ("命令速查与场景矩阵.md", "## 2. 工程 H2 泄漏、扩散、火灾"),
    "command_cheatsheet_has_academic_section": ("命令速查与场景矩阵.md", "## 5. 学术气相爆轰"),
    "command_cheatsheet_has_parallel_section": ("命令速查与场景矩阵.md", "## 7. CPU、GPU、MPI 并行矩阵"),
    "command_cheatsheet_has_real_artifact_section": ("命令速查与场景矩阵.md", "## 9. 真实资料接收"),
    "command_cheatsheet_has_master_scope_command": (
        "命令速查与场景矩阵.md",
        "bash tools/verify_master_plan_current_scope.sh",
    ),
    "command_cheatsheet_has_gpu_fire_command": (
        "命令速查与场景矩阵.md",
        "CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh",
    ),
    "command_cheatsheet_has_academic_cuda_command": (
        "命令速查与场景矩阵.md",
        "CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_academic_pelec_cuda.sh",
    ),
    "command_cheatsheet_has_receiving_preflight_command": (
        "命令速查与场景矩阵.md",
        "bash tools/run_strict_external_artifact_receiving_preflight.sh",
    ),
    "engineering_tutorial_has_h2": ("工程场景_泄漏扩散火灾_Tutorial.md", "H2"),
    "engineering_tutorial_has_fire": ("工程场景_泄漏扩散火灾_Tutorial.md", "火灾"),
    "academic_tutorial_has_detonation": ("学术场景_气相与两相爆轰_Tutorial.md", "爆轰"),
    "academic_tutorial_has_two_phase": ("学术场景_气相与两相爆轰_Tutorial.md", "两相"),
    "real_case_intake_has_real_cad": ("真实工程资料交付与复验清单.md", "真实 CAD 与边界标签"),
    "real_case_intake_has_fire_calibration": ("真实工程资料交付与复验清单.md", "火灾、热辐射、过压标定数据"),
    "real_case_intake_has_fire_residual_budget": (
        "真实工程资料交付与复验清单.md",
        "bash tools/verify_h2_fire_calibration_residual_budget.sh",
    ),
    "strict_external_artifact_cn_handoff_has_status": ("真实资料投递清单_按文件路径.md", "## 1. 当前状态"),
    "strict_external_artifact_cn_handoff_has_drop_paths": ("真实资料投递清单_按文件路径.md", "## 3. 投递目录与文件"),
    "strict_external_artifact_cn_handoff_has_preflight": (
        "真实资料投递清单_按文件路径.md",
        "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
    ),
    "strict_external_artifact_cn_handoff_has_receiving_preflight_wrapper": (
        "真实资料投递清单_按文件路径.md",
        "bash tools/run_strict_external_artifact_receiving_preflight.sh",
    ),
    "readme_has_receiving_preflight_wrapper": (
        "README.md",
        "bash tools/run_strict_external_artifact_receiving_preflight.sh",
    ),
}

CASE_REQUIRED_PATTERNS = {
    "engineering_case_has_minimal_file_package": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "## 1. 最小文件包",
    ),
    "engineering_case_has_copy_run_checklist": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "## 0. 从零照做清单",
    ),
    "engineering_case_explains_file_roles": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "pelelmex_prob.cpp",
    ),
    "engineering_case_explains_real_case_parameters": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "把这个案例改成自己的储罐区/管廊泄漏",
    ),
    "engineering_case_has_custom_input_copy": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "input.my_h2_open_domain",
    ),
    "engineering_case_has_cpu_command": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "bash tools/codex_smoke_engineering_h2_leak_open_domain.sh",
    ),
    "engineering_case_has_mpi_command": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh",
    ),
    "engineering_case_has_gpu_fire_command": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh",
    ),
    "engineering_case_has_mpi_cuda_restart_command": (
        "examples/engineering/h2_leak_3d/README_中文快速教程.md",
        "bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh",
    ),
    "academic_case_has_minimal_file_package": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "## 1. 最小文件包",
    ),
    "academic_case_has_copy_run_checklist": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "## 0. 从零照做清单",
    ),
    "academic_case_explains_file_roles": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "prob_parm.H",
    ),
    "academic_case_explains_real_case_parameters": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "把这个案例改成自己的二维/三维气相爆轰",
    ),
    "academic_case_has_custom_input_copy": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "inputs.my_detonation_wave",
    ),
    "academic_case_has_cpu_command": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "bash tools/codex_smoke_academic_detonation_wave.sh",
    ),
    "academic_case_has_mpi_command": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "bash tools/codex_smoke_academic_pelec_mpi.sh",
    ),
    "academic_case_has_hybrid_command": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "bash tools/codex_smoke_academic_pelec_hybrid.sh",
    ),
    "academic_case_has_gpu_command": (
        "examples/academic/detonation_2D/README_中文快速教程.md",
        "bash tools/codex_smoke_academic_pelec_cuda.sh",
    ),
}

COMMAND_REF_RE = re.compile(
    r"(?:^|\s)(?:[A-Z_][A-Z0-9_]*=[^\s]+(?:\s+|$))*"
    r"(bash|python3)\s+(tools/[A-Za-z0-9_./-]+)",
    re.MULTILINE,
)


class UserGuidesIndexError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UserGuidesIndexError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def documented_command_references() -> list[dict[str, object]]:
    refs = []
    seen = set()
    all_guides = {
        **{name: DOCS / filename for name, filename in GUIDES.items()},
        **{name: REPO / filename for name, filename in CASE_GUIDES.items()},
    }
    for guide_name, path in all_guides.items():
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for match in COMMAND_REF_RE.finditer(text):
            runner = match.group(1)
            command_path = match.group(2).rstrip("`)")
            key = (guide_name, runner, command_path)
            if key in seen:
                continue
            seen.add(key)
            target = REPO / command_path
            entry = {
                "guide": guide_name,
                "runner": runner,
                "path": command_path,
                "exists": target.is_file(),
            }
            if target.is_file():
                entry["sha256"] = sha256(target)
                entry["bytes"] = target.stat().st_size
            refs.append(entry)
    return refs


def syntax_check_targets(command_refs: list[dict[str, object]]) -> list[dict[str, object]]:
    checks = []
    seen = set()
    for item in command_refs:
        runner = str(item["runner"])
        command_path = str(item["path"])
        key = (runner, command_path)
        if key in seen:
            continue
        seen.add(key)
        target = REPO / command_path
        if not target.is_file():
            checks.append(
                {
                    "runner": runner,
                    "path": command_path,
                    "checked": False,
                    "pass": False,
                    "reason": "missing target",
                }
            )
            continue
        if runner == "bash":
            cmd = ["bash", "-n", command_path]
        elif runner == "python3":
            cmd = [sys.executable, "-m", "py_compile", command_path]
        else:
            checks.append(
                {
                    "runner": runner,
                    "path": command_path,
                    "checked": False,
                    "pass": False,
                    "reason": f"unsupported runner {runner}",
                }
            )
            continue
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        checks.append(
            {
                "runner": runner,
                "path": command_path,
                "checked": True,
                "pass": proc.returncode == 0,
                "returncode": proc.returncode,
                "stderr_excerpt": proc.stderr.strip()[:500],
            }
        )
    return checks


def build_report() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = []

    documents = {}
    for name, filename in GUIDES.items():
        path = DOCS / filename
        entry = {"path": rel(path), "exists": path.is_file()}
        if path.is_file():
            entry["sha256"] = sha256(path)
            entry["bytes"] = path.stat().st_size
        else:
            failures.append(f"missing guide: {rel(path)}")
        documents[name] = entry
    for name, filename in CASE_GUIDES.items():
        path = REPO / filename
        entry = {"path": rel(path), "exists": path.is_file()}
        if path.is_file():
            entry["sha256"] = sha256(path)
            entry["bytes"] = path.stat().st_size
        else:
            failures.append(f"missing case guide: {rel(path)}")
        documents[name] = entry

    checks = {}
    for name, (filename, pattern) in REQUIRED_PATTERNS.items():
        path = DOCS / filename
        ok = path.is_file() and pattern in path.read_text(encoding="utf-8")
        checks[name] = {
            "path": rel(path),
            "pattern": pattern,
            "pass": ok,
        }
        if not ok:
            failures.append(f"missing required guide pattern: {name}")
    for name, (filename, pattern) in CASE_REQUIRED_PATTERNS.items():
        path = REPO / filename
        ok = path.is_file() and pattern in path.read_text(encoding="utf-8")
        checks[name] = {
            "path": rel(path),
            "pattern": pattern,
            "pass": ok,
        }
        if not ok:
            failures.append(f"missing required case guide pattern: {name}")

    command_refs = documented_command_references()
    missing_command_refs = [item for item in command_refs if not item["exists"]]
    if len(command_refs) < 50:
        failures.append(f"too few documented command references discovered: {len(command_refs)}")
    for item in missing_command_refs:
        failures.append(f"missing documented command target: {item['guide']} -> {item['path']}")
    syntax_checks = syntax_check_targets(command_refs)
    failed_syntax_checks = [item for item in syntax_checks if not item["pass"]]
    for item in failed_syntax_checks:
        failures.append(f"documented command syntax check failed: {item['runner']} {item['path']}")

    status = STATUS_PASS if not failures else "FAIL-USER-GUIDES-INDEX"
    return {
        "status": status,
        "documents": documents,
        "checks": checks,
        "command_references": command_refs,
        "summary": {
            "guide_count": len(GUIDES),
            "case_guide_count": len(CASE_GUIDES),
            "document_count": len(GUIDES) + len(CASE_GUIDES),
            "existing_guide_count": sum(1 for item in documents.values() if item["exists"]),
            "required_pattern_count": len(REQUIRED_PATTERNS) + len(CASE_REQUIRED_PATTERNS),
            "passed_required_pattern_count": sum(1 for item in checks.values() if item["pass"]),
            "documented_command_reference_count": len(command_refs),
            "missing_documented_command_reference_count": len(missing_command_refs),
            "unique_documented_command_target_count": len(syntax_checks),
            "documented_command_syntax_failure_count": len(failed_syntax_checks),
        },
        "command_syntax_checks": syntax_checks,
        "failures": failures,
    }


def validate_report(report: dict[str, object], verify_hashes: bool = True) -> None:
    require(report.get("status") == STATUS_PASS, "invalid status")
    require(report.get("failures") == [], "report contains failures")
    summary = report.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("guide_count") == len(GUIDES), "guide count mismatch")
    require(summary.get("case_guide_count") == len(CASE_GUIDES), "case guide count mismatch")
    require(summary.get("document_count") == len(GUIDES) + len(CASE_GUIDES), "document count mismatch")
    require(summary.get("existing_guide_count") == len(GUIDES) + len(CASE_GUIDES), "not all guides exist")
    require(summary.get("passed_required_pattern_count") == summary.get("required_pattern_count"),
            "not all required patterns passed")
    require(summary.get("missing_documented_command_reference_count") == 0, "missing command references")
    require(summary.get("documented_command_syntax_failure_count") == 0, "syntax failures recorded")
    require(int(summary.get("documented_command_reference_count", 0)) >= 50, "too few command references")

    documents = report.get("documents")
    require(isinstance(documents, dict), "missing documents")
    for name, filename in GUIDES.items():
        entry = documents.get(name)
        require(isinstance(entry, dict), f"missing document entry {name}")
        path = REPO / str(entry.get("path", ""))
        require(path.is_file(), f"missing guide on disk: {path}")
        if verify_hashes:
            require(entry.get("sha256") == sha256(path), f"guide hash mismatch: {path}")
    for name, filename in CASE_GUIDES.items():
        entry = documents.get(name)
        require(isinstance(entry, dict), f"missing case document entry {name}")
        path = REPO / str(entry.get("path", ""))
        require(path.is_file(), f"missing case guide on disk: {path}")
        if verify_hashes:
            require(entry.get("sha256") == sha256(path), f"case guide hash mismatch: {path}")

    checks = report.get("checks")
    require(isinstance(checks, dict), "missing checks")
    for name in [*REQUIRED_PATTERNS, *CASE_REQUIRED_PATTERNS]:
        entry = checks.get(name)
        require(isinstance(entry, dict) and entry.get("pass") is True, f"required pattern failed: {name}")

    command_refs = report.get("command_references")
    require(isinstance(command_refs, list), "missing command references")
    for item in command_refs:
        require(isinstance(item, dict), "invalid command reference entry")
        path = REPO / str(item.get("path", ""))
        require(path.is_file(), f"missing documented command target: {path}")
        if verify_hashes and "sha256" in item:
            require(item.get("sha256") == sha256(path), f"command target hash mismatch: {path}")

    syntax_checks = syntax_check_targets(command_refs)
    failed = [item for item in syntax_checks if not item["pass"]]
    require(not failed, f"documented command syntax checks failed: {failed[:3]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write/verify the Chinese user-guides index report.")
    parser.add_argument("--verify-json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify_json:
        data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
        validate_report(data, verify_hashes=True)
        print(f"user_guides_index VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    validate_report(report, verify_hashes=False)
    status = str(report["status"])
    failures = list(report["failures"])
    documents = report["documents"]
    checks = report["checks"]
    command_refs = report["command_references"]
    syntax_checks = report["command_syntax_checks"]
    json_path = OUT_DIR / "user_guides_index_report.json"
    md_path = OUT_DIR / "user_guides_index_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# User Guides Index",
        "",
        f"Status: `{status}`",
        "",
        "## Documents",
    ]
    for name, entry in documents.items():
        mark = "PASS" if entry["exists"] else "FAIL"
        lines.append(f"- `{mark}` `{name}` `{entry['path']}`")
    lines.extend(["", "## Required Content"])
    for name, check in checks.items():
        mark = "PASS" if check["pass"] else "FAIL"
        lines.append(f"- `{mark}` `{name}`")
    lines.extend(["", "## Documented Command Targets"])
    for item in command_refs:
        mark = "PASS" if item["exists"] else "FAIL"
        lines.append(f"- `{mark}` `{item['guide']}` `{item['runner']} {item['path']}`")
    lines.extend(["", "## Documented Command Syntax"])
    for item in syntax_checks:
        mark = "PASS" if item["pass"] else "FAIL"
        lines.append(f"- `{mark}` `{item['runner']} {item['path']}`")
    if failures:
        lines.extend(["", "## Failures"])
        for failure in failures:
            lines.append(f"- {failure}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"user_guides_index {status} json={rel(json_path)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
