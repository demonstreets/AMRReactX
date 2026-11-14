#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path.cwd().resolve()
DOCS = REPO / "docs" / "user_guides"
OUT_DIR = REPO / "docs" / "codex_audit" / "evidence" / "real_case_intake_guide_20260817"

FILES = {
    "index": DOCS / "README.md",
    "real_case_intake_guide": DOCS / "真实工程资料交付与复验清单.md",
}

REQUIRED_PATTERNS = {
    "index_links_real_case_guide": (FILES["index"], "真实工程资料交付与复验清单.md"),
    "real_cad_section": (FILES["real_case_intake_guide"], "真实 CAD 与边界标签"),
    "external_plume_section": (FILES["real_case_intake_guide"], "外部 plume/泄漏扩散标定数据"),
    "fire_calibration_section": (FILES["real_case_intake_guide"], "火灾、热辐射、过压标定数据"),
    "master_scope_command": (FILES["real_case_intake_guide"], "bash tools/verify_master_plan_current_scope.sh"),
    "release_refresh_command": (FILES["real_case_intake_guide"], "bash tools/run_current_scope_release_refresh.sh"),
    "h2_rebuild_command": (FILES["real_case_intake_guide"], "bash tools/rebuild_engineering_h2_evidence_chain.sh"),
    "real_cad_drop_root": (
        FILES["real_case_intake_guide"],
        "docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package",
    ),
    "external_plume_drop_root": (
        FILES["real_case_intake_guide"],
        "docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset",
    ),
    "fire_calibration_drop_root": (
        FILES["real_case_intake_guide"],
        "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset",
    ),
    "fire_calibration_residual_budget_command": (
        FILES["real_case_intake_guide"],
        "bash tools/verify_h2_fire_calibration_residual_budget.sh",
    ),
    "fire_calibration_residual_budget_report": (
        FILES["real_case_intake_guide"],
        "docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/h2_fire_calibration_residual_budget_report.md",
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    docs = {}
    failures = []

    for name, path in FILES.items():
        rel = path.relative_to(REPO).as_posix()
        exists = path.is_file()
        entry = {"path": rel, "exists": exists}
        if exists:
            entry["sha256"] = sha256(path)
            entry["bytes"] = path.stat().st_size
        else:
            failures.append(f"missing {rel}")
        docs[name] = entry

    checks = {}
    for name, (path, pattern) in REQUIRED_PATTERNS.items():
        ok = path.is_file() and pattern in path.read_text(encoding="utf-8")
        checks[name] = {
            "path": path.relative_to(REPO).as_posix(),
            "pattern": pattern,
            "pass": ok,
        }
        if not ok:
            failures.append(f"missing pattern {name}")

    status = "PASS-REAL-CASE-INTAKE-GUIDE" if not failures else "FAIL-REAL-CASE-INTAKE-GUIDE"
    report = {
        "status": status,
        "documents": docs,
        "checks": checks,
        "failures": failures,
    }

    json_path = OUT_DIR / "real_case_intake_guide_report.json"
    md_path = OUT_DIR / "real_case_intake_guide_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Real Case Intake Guide Delivery",
        "",
        f"Status: `{status}`",
        "",
        "## Documents",
    ]
    for name, entry in docs.items():
        lines.append(f"- `{name}` `{entry.get('sha256', 'missing')}` `{entry['path']}`")
    lines.extend(["", "## Checks"])
    for name, check in checks.items():
        mark = "PASS" if check["pass"] else "FAIL"
        lines.append(f"- `{mark}` `{name}`")
    if failures:
        lines.extend(["", "## Failures"])
        for failure in failures:
            lines.append(f"- {failure}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"real_case_intake_guide {status} json={json_path.relative_to(REPO)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
