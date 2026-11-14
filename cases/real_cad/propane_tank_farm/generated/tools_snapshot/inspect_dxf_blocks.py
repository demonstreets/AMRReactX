#!/usr/bin/env python3
"""Inspect DXF BLOCK definitions and INSERT references."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def iter_pairs(path: Path, encoding: str):
    with path.open("r", encoding=encoding, errors="replace", newline=None) as fh:
        while True:
            code = fh.readline()
            if not code:
                return
            value = fh.readline()
            if not value:
                return
            yield code.strip(), value.rstrip("\r\n")


def as_float(value: str, default=0.0) -> float:
    try:
        return float(value)
    except ValueError:
        return default


def update_box(box, x=None, y=None, z=None):
    for i, val in enumerate((x, y, z)):
        if val is None:
            continue
        lo = 2 * i
        hi = lo + 1
        if box[lo] is None or val < box[lo]:
            box[lo] = val
        if box[hi] is None or val > box[hi]:
            box[hi] = val


def inspect(path: Path, encoding: str) -> dict:
    blocks = {}
    inserts = []
    section = None
    in_block = False
    block_name = None
    current = None
    pending_x = None
    pending_z = 0.0
    current_insert = None

    def finish_entity():
        nonlocal current, pending_x, pending_z, current_insert
        if current and in_block and block_name:
            b = blocks.setdefault(
                block_name,
                {"entity_counts": Counter(), "layers": Counter(), "bbox": [None] * 6, "max_radius": 0.0},
            )
            b["entity_counts"][current["type"]] += 1
            if current.get("layer"):
                b["layers"][current["layer"]] += 1
            for x, y, z in current.get("points", []):
                update_box(b["bbox"], x, y, z)
            if current.get("radius"):
                r = current["radius"]
                b["max_radius"] = max(b["max_radius"], r)
                if current.get("points"):
                    x, y, z = current["points"][0]
                    update_box(b["bbox"], x - r, y - r, z)
                    update_box(b["bbox"], x + r, y + r, z)
        if current_insert:
            inserts.append(current_insert)
        current = None
        current_insert = None
        pending_x = None
        pending_z = 0.0

    entity_types = {"LINE", "LWPOLYLINE", "CIRCLE", "ARC", "POLYLINE", "VERTEX", "INSERT"}

    for code, value in iter_pairs(path, encoding):
        if code == "0":
            if value == "SECTION":
                finish_entity()
                section = None
                continue
            if value == "ENDSEC":
                finish_entity()
                section = None
                in_block = False
                block_name = None
                continue
            if section == "BLOCKS" and value == "BLOCK":
                finish_entity()
                in_block = True
                block_name = None
                continue
            if section == "BLOCKS" and value == "ENDBLK":
                finish_entity()
                in_block = False
                block_name = None
                continue
            if section in {"BLOCKS", "ENTITIES"} and value in entity_types:
                finish_entity()
                if value == "INSERT" and section == "ENTITIES":
                    current_insert = {"type": "INSERT", "layer": "0", "name": None, "point": None, "scale": [1.0, 1.0, 1.0], "angle": 0.0}
                else:
                    current = {"type": value, "layer": "0", "points": []}
                continue
            if section in {"BLOCKS", "ENTITIES"}:
                finish_entity()
            continue

        if code == "2" and section is None:
            section = value
            continue
        if section == "BLOCKS" and in_block and block_name is None and code == "2":
            block_name = value
            blocks.setdefault(
                block_name,
                {"entity_counts": Counter(), "layers": Counter(), "bbox": [None] * 6, "max_radius": 0.0},
            )
            continue

        target = current_insert if current_insert is not None else current
        if section in {"BLOCKS", "ENTITIES"} and target is not None:
            if code == "8":
                target["layer"] = value
            elif code == "2":
                target["name"] = value
            elif code == "10":
                pending_x = as_float(value)
            elif code == "30":
                pending_z = as_float(value)
            elif code == "20" and pending_x is not None:
                if current_insert is not None:
                    target["point"] = [pending_x, as_float(value), pending_z]
                else:
                    target.setdefault("points", []).append((pending_x, as_float(value), pending_z))
                pending_x = None
                pending_z = 0.0
            elif current_insert is not None and code in {"41", "42", "43"}:
                idx = int(code) - 41
                target["scale"][idx] = as_float(value, 1.0)
            elif current_insert is not None and code == "50":
                target["angle"] = as_float(value)
            elif current is not None and code == "40":
                target["radius"] = as_float(value)

    finish_entity()
    output_blocks = []
    for name, data in blocks.items():
        bbox = data["bbox"]
        width = None if bbox[0] is None else bbox[1] - bbox[0]
        height = None if bbox[2] is None else bbox[3] - bbox[2]
        output_blocks.append(
            {
                "name": name,
                "entity_counts": dict(data["entity_counts"].most_common()),
                "layers": dict(data["layers"].most_common(12)),
                "bbox": bbox,
                "width": width,
                "height": height,
                "max_radius": data["max_radius"],
            }
        )
    output_blocks.sort(key=lambda x: ((x["width"] or 0) * (x["height"] or 0), x["max_radius"]), reverse=True)
    insert_counts = Counter((i["layer"], i["name"]) for i in inserts)
    return {
        "block_count": len(blocks),
        "insert_count": len(inserts),
        "largest_blocks": output_blocks[:200],
        "insert_counts": [
            {"layer": layer, "name": name, "count": count}
            for (layer, name), count in insert_counts.most_common(200)
        ],
        "inserts": inserts[:2000],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dxf")
    parser.add_argument("--encoding", default="gbk")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = inspect(Path(args.dxf), args.encoding)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(f"blocks={result['block_count']} inserts={result['insert_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
