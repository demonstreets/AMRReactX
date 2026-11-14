#!/usr/bin/env python3
"""Write a reproducible Codex checkpoint markdown file."""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from pathlib import Path


def slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text.strip()).strip("-").lower()
    return slug[:80] or "checkpoint"


def run_git_status(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "status", "--short"], cwd=root, text=True, stderr=subprocess.STDOUT
        )
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return [f"git status unavailable: {exc}"]
    lines = [line.rstrip() for line in out.splitlines() if line.strip()]
    return lines or ["clean"]


def bullet_lines(values: list[str]) -> str:
    if not values:
        return "- none recorded\n"
    return "".join(f"- {value}\n" for value in values)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--title", required=True, help="checkpoint title")
    parser.add_argument("--items", action="append", default=[], help="master-plan item, repeatable")
    parser.add_argument("--summary", action="append", default=[], help="summary bullet, repeatable")
    parser.add_argument("--changed", action="append", default=[], help="changed file/module, repeatable")
    parser.add_argument("--command", action="append", default=[], help="verification command/result, repeatable")
    parser.add_argument("--evidence", action="append", default=[], help="evidence log/path, repeatable")
    parser.add_argument("--limitation", action="append", default=[], help="known limitation, repeatable")
    parser.add_argument("--agent", default="Codex", help="agent name")
    parser.add_argument("--slug", default=None, help="filename slug override")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    checkpoint_dir = root / "CHECKPOINTS"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now().astimezone()
    slug = slugify(args.slug or args.title)
    filename = f"checkpoint-{now:%Y%m%d-%H%M%S}-{slug}.md"
    output = checkpoint_dir / filename

    git_status = run_git_status(root)
    if len(git_status) > 120:
        git_status = git_status[:120] + ["... truncated after 120 entries"]

    content = []
    content.append(f"# Checkpoint - {args.title}\n\n")
    content.append(f"> Date: {now.isoformat(timespec='seconds')}\n")
    content.append(f"> Agent: {args.agent}\n")
    content.append(f"> Related items: {', '.join(args.items) if args.items else 'not specified'}\n\n")
    content.append("## Summary\n\n")
    content.append(bullet_lines(args.summary))
    content.append("\n## Changed Files / Modules\n\n")
    content.append(bullet_lines(args.changed))
    content.append("\n## Verification\n\n")
    content.append(bullet_lines(args.command))
    content.append("\n## Evidence Paths\n\n")
    content.append(bullet_lines(args.evidence))
    content.append("\n## Known Limitations\n\n")
    content.append(bullet_lines(args.limitation))
    content.append("\n## Git Status Snapshot\n\n")
    content.append("```text\n")
    content.append("\n".join(git_status))
    content.append("\n```\n")

    output.write_text("".join(content))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
