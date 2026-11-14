#!/usr/bin/env python3
"""Sanitize machine-local paths and private markers from scheduler evidence files."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    '.json', '.md', '.log', '.out', '.err', '.txt', '.csv', '.tsv', '.sh', '.inputs'
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def replacements(repo: Path) -> list[tuple[str, str]]:
    values = [
        (str(repo), '${REPO_ROOT}'),
        (str(Path.home()), '${USER_HOME}'),
        (os.environ.get('HOME', ''), '${USER_HOME}'),
    ]
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for old, new in values:
        if old and old not in seen:
            out.append((old, new))
            seen.add(old)
    return out


def sanitize_text(text: str, repl: list[tuple[str, str]]) -> tuple[str, int]:
    count = 0
    out = text
    for old, new in repl:
        n = out.count(old)
        if n:
            out = out.replace(old, new)
            count += n
    return out, count


def should_scan(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    if path.suffix in TEXT_SUFFIXES:
        return True
    return path.name in {'campaign_case.log'}


def sanitize_tree(root: Path, dry_run: bool) -> dict[str, int]:
    repo = repo_root()
    repl = replacements(repo)
    files = 0
    edited = 0
    replacements_count = 0
    for path in sorted(root.rglob('*')):
        if not should_scan(path):
            continue
        files += 1
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text = path.read_text(encoding='utf-8', errors='replace')
        new_text, count = sanitize_text(text, repl)
        if count:
            edited += 1
            replacements_count += count
            if not dry_run:
                path.write_text(new_text, encoding='utf-8')
    return {'files_scanned': files, 'files_edited': edited, 'replacements': replacements_count}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence_root', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.evidence_root
    if not root.is_absolute():
        root = repo_root() / root
    if not root.is_dir():
        print(f'engineering_scheduler_evidence_sanitize FAIL missing dir: {root}', file=sys.stderr)
        return 2
    summary = sanitize_tree(root, args.dry_run)
    print(
        'engineering_scheduler_evidence_sanitize PASS '
        f"root={root} files={summary['files_scanned']} edited={summary['files_edited']} replacements={summary['replacements']}"
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
