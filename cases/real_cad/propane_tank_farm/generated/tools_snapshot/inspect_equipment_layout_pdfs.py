#!/usr/bin/env python3
"""Extract first-pass equipment-layout data from Chinese engineering PDFs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber


KEYWORDS = [
    "丙烷",
    "丁烷",
    "储罐",
    "罐组",
    "常温",
    "低温",
    "BOG",
    "复热",
    "空压",
    "制氮",
    "槽车",
    "装车",
    "火炬",
    "设备",
    "管廊",
    "标高",
    "EL",
    "直径",
    "DN",
    "高度",
    "防火堤",
    "围堰",
    "泵",
    "压缩机",
    "换热器",
]


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def keyword_context(text: str, window: int = 80) -> list[dict[str, str]]:
    hits = []
    for kw in KEYWORDS:
        for match in re.finditer(re.escape(kw), text, flags=re.IGNORECASE):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            hits.append({"keyword": kw, "context": text[start:end].replace("\n", " ")})
            if len(hits) >= 120:
                return hits
    return hits


def inspect_pdf(path: Path) -> dict:
    item = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "pages": [],
        "all_text": "",
        "tables": [],
        "keyword_hits": [],
    }
    with pdfplumber.open(path) as pdf:
        texts = []
        for page_idx, page in enumerate(pdf.pages, start=1):
            text = clean_text(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
            texts.append(text)
            page_item = {
                "page": page_idx,
                "width": page.width,
                "height": page.height,
                "rotation": page.rotation,
                "char_count": len(page.chars),
                "line_count": len(page.lines),
                "rect_count": len(page.rects),
                "curve_count": len(page.curves),
                "image_count": len(page.images),
                "text_preview": text[:1200],
            }
            item["pages"].append(page_item)
            try:
                tables = page.extract_tables()
            except Exception as exc:  # pragma: no cover - defensive PDF intake
                tables = [[["TABLE_EXTRACT_ERROR", str(exc)]]]
            for table in tables[:8]:
                cleaned = [
                    [clean_text(cell or "") for cell in row]
                    for row in table[:80]
                ]
                item["tables"].append({"page": page_idx, "rows": cleaned})
        all_text = clean_text("\n\n".join(texts))
        item["all_text"] = all_text
        item["keyword_hits"] = keyword_context(all_text)
    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("pdfs", nargs="+")
    args = parser.parse_args()

    results = [inspect_pdf(Path(p)) for p in args.pdfs]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for result in results:
        pages = len(result["pages"])
        chars = sum(page["char_count"] for page in result["pages"])
        lines = sum(page["line_count"] for page in result["pages"])
        tables = len(result["tables"])
        hits = len(result["keyword_hits"])
        print(f"{Path(result['path']).name}: pages={pages} chars={chars} lines={lines} tables={tables} keyword_hits={hits}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
