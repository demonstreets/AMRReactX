#!/usr/bin/env python3
"""Lightweight DXF inspector for large ASCII CAD layouts.

This deliberately avoids third-party CAD dependencies. It is intended for
first-pass intake: layer names, entity counts, extents, and representative
2D primitives that can drive a simplified CFD geometry rebuild.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def iter_pairs(path: Path, encoding: str) -> Iterable[tuple[str, str]]:
    with path.open("r", encoding=encoding, errors="replace", newline=None) as fh:
        while True:
            code = fh.readline()
            if not code:
                return
            value = fh.readline()
            if not value:
                return
            yield code.strip(), value.rstrip("\r\n")


def as_float(value: str):
    try:
        return float(value)
    except ValueError:
        return None


def parse_dxf(path: Path, encoding: str, sample_limit: int) -> dict:
    header: dict[str, object] = {}
    layers: dict[str, dict[str, object]] = {}
    entity_counts: Counter[str] = Counter()
    layer_entity_counts: dict[str, Counter[str]] = defaultdict(Counter)
    sample_entities: list[dict[str, object]] = []
    text_entities: list[dict[str, object]] = []
    layer_bbox: dict[str, list[float | None]] = defaultdict(
        lambda: [None, None, None, None, None, None]
    )
    bbox = [None, None, None, None, None, None]

    section = None
    table = None
    current_header_key = None
    current_layer: dict[str, object] | None = None
    current_entity: dict[str, object] | None = None

    def update_bbox_box(box, x=None, y=None, z=None) -> None:
        vals = (x, y, z)
        for i, val in enumerate(vals):
            if val is None:
                continue
            lo = i * 2
            hi = lo + 1
            if box[lo] is None or val < box[lo]:
                box[lo] = val
            if box[hi] is None or val > box[hi]:
                box[hi] = val

    def update_bbox(layer=None, x=None, y=None, z=None) -> None:
        update_bbox_box(bbox, x=x, y=y, z=z)
        if layer:
            update_bbox_box(layer_bbox[layer], x=x, y=y, z=z)

    def finish_layer() -> None:
        nonlocal current_layer
        if current_layer and current_layer.get("name"):
            layers[str(current_layer["name"])] = current_layer
        current_layer = None

    def finish_entity() -> None:
        nonlocal current_entity
        if not current_entity:
            return
        etype = str(current_entity.get("type", "UNKNOWN"))
        layer = str(current_entity.get("layer", "0"))
        entity_counts[etype] += 1
        layer_entity_counts[layer][etype] += 1
        if len(sample_entities) < sample_limit:
            sample_entities.append(current_entity)
        if etype in {"TEXT", "MTEXT"} and current_entity.get("text"):
            text_entities.append(current_entity)
        current_entity = None

    entity_start_types = {
        "LINE",
        "LWPOLYLINE",
        "POLYLINE",
        "VERTEX",
        "CIRCLE",
        "ARC",
        "ELLIPSE",
        "SPLINE",
        "INSERT",
        "TEXT",
        "MTEXT",
        "HATCH",
        "POINT",
        "SOLID",
        "3DFACE",
    }

    for code, value in iter_pairs(path, encoding):
        if code == "0":
            if value == "SECTION":
                finish_entity()
                section = None
                table = None
                continue
            if value == "ENDSEC":
                finish_entity()
                finish_layer()
                section = None
                table = None
                continue
            if value == "TABLE":
                finish_entity()
                finish_layer()
                table = None
                continue
            if value == "ENDTAB":
                finish_entity()
                finish_layer()
                table = None
                continue
            if section == "TABLES" and table == "LAYER" and value == "LAYER":
                finish_layer()
                current_layer = {"name": None}
                continue
            if section == "ENTITIES" and value in entity_start_types:
                finish_entity()
                current_entity = {"type": value}
                continue
            if section == "ENTITIES":
                finish_entity()
            continue

        if code == "2" and section is None:
            section = value
            continue
        if code == "2" and section == "TABLES" and table is None:
            table = value
            continue

        if section == "HEADER":
            if code == "9":
                current_header_key = value
                header.setdefault(current_header_key, [])
            elif current_header_key:
                values = header.setdefault(current_header_key, [])
                assert isinstance(values, list)
                values.append({"code": code, "value": value})
            continue

        if section == "TABLES" and table == "LAYER" and current_layer is not None:
            if code == "2":
                current_layer["name"] = value
            elif code == "62":
                current_layer["color"] = value
            elif code == "6":
                current_layer["linetype"] = value
            elif code == "70":
                current_layer["flags"] = value
            continue

        if section == "ENTITIES" and current_entity is not None:
            if code == "8":
                current_entity["layer"] = value
            elif code == "2":
                current_entity.setdefault("name", value)
            elif code in {"10", "11", "12", "13"}:
                x = as_float(value)
                current_entity.setdefault("x", []).append(x)
                update_bbox(layer=current_entity.get("layer"), x=x)
            elif code in {"20", "21", "22", "23"}:
                y = as_float(value)
                current_entity.setdefault("y", []).append(y)
                update_bbox(layer=current_entity.get("layer"), y=y)
            elif code in {"30", "31", "32", "33"}:
                z = as_float(value)
                current_entity.setdefault("z", []).append(z)
                update_bbox(layer=current_entity.get("layer"), z=z)
            elif code == "40":
                current_entity.setdefault("radii_or_sizes", []).append(as_float(value))
            elif code in {"41", "42", "43"}:
                current_entity.setdefault("scales_or_bulges", []).append(as_float(value))
            elif code in {"50", "51"}:
                current_entity.setdefault("angles", []).append(as_float(value))
            elif code == "1":
                text = value.strip()
                if text:
                    current_entity.setdefault("text", text[:120])

    finish_entity()
    finish_layer()

    layer_summaries = []
    for name, counts in sorted(layer_entity_counts.items()):
        total = sum(counts.values())
        layer_summaries.append(
            {
                "name": name,
                "total_entities": total,
                "entity_counts": dict(counts.most_common()),
                "computed_bbox_xyz": layer_bbox.get(name),
                "layer_table": layers.get(name),
            }
        )
    layer_summaries.sort(key=lambda item: item["total_entities"], reverse=True)

    def header_values(key: str):
        return header.get(key, [])

    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "header": {
            "ACADVER": header_values("$ACADVER"),
            "DWGCODEPAGE": header_values("$DWGCODEPAGE"),
            "EXTMIN": header_values("$EXTMIN"),
            "EXTMAX": header_values("$EXTMAX"),
            "INSUNITS": header_values("$INSUNITS"),
        },
        "computed_bbox_xyz": bbox,
        "layer_count": len(layers),
        "entity_counts": dict(entity_counts.most_common()),
        "top_layers": layer_summaries[:80],
        "text_count": len(text_entities),
        "texts": text_entities[:500],
        "sample_entities": sample_entities,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dxf")
    parser.add_argument("--encoding", default="gbk")
    parser.add_argument("--sample-limit", type=int, default=80)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = parse_dxf(Path(args.dxf), args.encoding, args.sample_limit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"layers={result['layer_count']}")
    print(f"entity_counts={result['entity_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
