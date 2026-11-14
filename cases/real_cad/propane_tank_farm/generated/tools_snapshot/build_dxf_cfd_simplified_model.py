#!/usr/bin/env python3
"""Build a simplified CFD STL model from an ASCII DXF plant layout.

The output is intentionally conservative: it converts plan-view CAD entities
into simple obstacles suitable for early CFD intake, not a design-grade 3D CAD
reconstruction.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Entity:
    type: str
    layer: str = "0"
    name: str | None = None
    points: list[tuple[float, float, float]] = field(default_factory=list)
    radius: float | None = None
    flags: int = 0
    text: str | None = None


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


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except ValueError:
        return default


def parse_header_pair_values(values: list[dict[str, str]]) -> list[float]:
    return [to_float(item["value"]) for item in values if item["code"] in {"10", "20", "30"}]


def parse_dxf(path: Path, encoding: str) -> tuple[dict[str, list[dict[str, str]]], list[Entity]]:
    header: dict[str, list[dict[str, str]]] = {}
    entities: list[Entity] = []
    section = None
    current_header_key = None
    current: Entity | None = None
    pending_x: float | None = None
    pending_z = 0.0

    entity_start_types = {
        "LINE",
        "LWPOLYLINE",
        "CIRCLE",
        "ARC",
        "INSERT",
        "TEXT",
        "MTEXT",
    }

    def finish_entity() -> None:
        nonlocal current, pending_x, pending_z
        if current is not None:
            entities.append(current)
        current = None
        pending_x = None
        pending_z = 0.0

    for code, value in iter_pairs(path, encoding):
        if code == "0":
            if value == "SECTION":
                finish_entity()
                section = None
                continue
            if value == "ENDSEC":
                finish_entity()
                section = None
                continue
            if section == "ENTITIES" and value in entity_start_types:
                finish_entity()
                current = Entity(type=value)
                continue
            if section == "ENTITIES":
                finish_entity()
            continue

        if code == "2" and section is None:
            section = value
            continue

        if section == "HEADER":
            if code == "9":
                current_header_key = value
                header.setdefault(current_header_key, [])
            elif current_header_key:
                header.setdefault(current_header_key, []).append({"code": code, "value": value})
            continue

        if section != "ENTITIES" or current is None:
            continue

        if code == "8":
            current.layer = value
        elif code == "2":
            current.name = value
        elif code == "70":
            try:
                current.flags = int(value.strip())
            except ValueError:
                current.flags = 0
        elif code in {"10", "11"}:
            pending_x = to_float(value)
        elif code in {"30", "31"}:
            pending_z = to_float(value)
        elif code in {"20", "21"} and pending_x is not None:
            current.points.append((pending_x, to_float(value), pending_z))
            pending_x = None
            pending_z = 0.0
        elif code == "40":
            current.radius = to_float(value)
        elif code == "1":
            current.text = value

    finish_entity()
    return header, entities


def normal(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0:
        return (0.0, 0.0, 0.0)
    return (x / n, y / n, z / n)


def tri_normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return normal((uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx))


def add_tri(tris, a, b, c, role: str) -> None:
    tris.append((tri_normal(a, b, c), a, b, c, role))


def add_box(tris, xmin, ymin, zmin, xmax, ymax, zmax, role: str) -> None:
    p = [
        (xmin, ymin, zmin),
        (xmax, ymin, zmin),
        (xmax, ymax, zmin),
        (xmin, ymax, zmin),
        (xmin, ymin, zmax),
        (xmax, ymin, zmax),
        (xmax, ymax, zmax),
        (xmin, ymax, zmax),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    for i, j, k in faces:
        add_tri(tris, p[i], p[j], p[k], role)


def add_line_prism(tris, x1, y1, x2, y2, width, height, role: str) -> bool:
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length <= 1.0e-9:
        return False
    nx, ny = -dy / length * width / 2.0, dx / length * width / 2.0
    pts = [(x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x2 - nx, y2 - ny), (x2 + nx, y2 + ny)]
    add_extruded_polygon(tris, pts, height, role)
    return True


def signed_area(points: list[tuple[float, float]]) -> float:
    return 0.5 * sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )


def add_extruded_polygon(tris, points: list[tuple[float, float]], height: float, role: str) -> bool:
    clean: list[tuple[float, float]] = []
    for p in points:
        if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1.0e-6:
            clean.append(p)
    if len(clean) >= 2 and math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < 1.0e-6:
        clean.pop()
    if len(clean) < 3 or abs(signed_area(clean)) < 1.0e-6:
        return False
    if signed_area(clean) < 0:
        clean.reverse()
    bottom = [(x, y, 0.0) for x, y in clean]
    top = [(x, y, height) for x, y in clean]
    n = len(clean)
    for i in range(n):
        j = (i + 1) % n
        add_tri(tris, bottom[i], bottom[j], top[j], role)
        add_tri(tris, bottom[i], top[j], top[i], role)
    for i in range(1, n - 1):
        add_tri(tris, bottom[0], bottom[i + 1], bottom[i], role)
        add_tri(tris, top[0], top[i], top[i + 1], role)
    return True


def add_cylinder(tris, cx, cy, radius, height, role: str, segments=40) -> bool:
    if radius <= 0:
        return False
    pts = [
        (
            cx + radius * math.cos(2.0 * math.pi * i / segments),
            cy + radius * math.sin(2.0 * math.pi * i / segments),
        )
        for i in range(segments)
    ]
    return add_extruded_polygon(tris, pts, height, role)


def layer_role(layer: str) -> tuple[str, float, float] | None:
    lower = layer.lower()
    if "管廊柱角" in layer:
        return ("piperack_column", 0.8, 8.0)
    if "管廊" in layer or "piperack" in lower:
        return ("piperack", 1.2, 8.0)
    if "围墙" in layer:
        return ("wall", 0.6, 3.0)
    if "防火堤" in layer or "罐区" in layer:
        return ("bund_or_tank_area", 0.5, 2.0)
    if "设备" in layer:
        return ("equipment", 1.0, 8.0)
    if "pipe" in lower or "管" in layer:
        return ("pipe_or_line", 0.35, 3.0)
    return None


def in_site(points, xmin, ymin, xmax, ymax, margin) -> bool:
    if not points:
        return False
    for x, y, _ in points:
        if xmin - margin <= x <= xmax + margin and ymin - margin <= y <= ymax + margin:
            return True
    return False


def write_stl(path: Path, tris) -> None:
    with path.open("w", encoding="ascii") as fh:
        fh.write("solid dxf_simplified_cfd_model\n")
        for n, a, b, c, _role in tris:
            fh.write(f"  facet normal {n[0]:.9e} {n[1]:.9e} {n[2]:.9e}\n")
            fh.write("    outer loop\n")
            for p in (a, b, c):
                fh.write(f"      vertex {p[0]:.9e} {p[1]:.9e} {p[2]:.9e}\n")
            fh.write("    endloop\n")
            fh.write("  endfacet\n")
        fh.write("endsolid dxf_simplified_cfd_model\n")


def write_svg(path: Path, features, width=1400, height=900) -> None:
    xs = [p[0] for f in features for p in f["points"]]
    ys = [p[1] for f in features for p in f["points"]]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    pad = 20
    sx = (width - 2 * pad) / max(xmax - xmin, 1.0)
    sy = (height - 2 * pad) / max(ymax - ymin, 1.0)
    s = min(sx, sy)

    colors = {
        "equipment": "#c2410c",
        "piperack": "#2563eb",
        "piperack_column": "#1d4ed8",
        "wall": "#111827",
        "bund_or_tank_area": "#7c2d12",
        "pipe_or_line": "#059669",
    }

    def map_pt(p):
        return (pad + (p[0] - xmin) * s, height - pad - (p[1] - ymin) * s)

    with path.open("w", encoding="utf-8") as fh:
        fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n')
        fh.write('<rect width="100%" height="100%" fill="white"/>\n')
        fh.write(f'<text x="20" y="28" font-size="18" fill="#111827">DXF simplified CFD extraction: {len(features)} features</text>\n')
        for feat in features:
            color = colors.get(feat["role"], "#64748b")
            pts = [map_pt(p) for p in feat["points"]]
            if feat["kind"] == "polygon":
                data = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
                fh.write(f'<polygon points="{data}" fill="{color}" fill-opacity="0.18" stroke="{color}" stroke-width="1"/>\n')
            elif len(pts) >= 2:
                x1, y1 = pts[0]
                x2, y2 = pts[-1]
                fh.write(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="2"/>\n')
            elif pts:
                x, y = pts[0]
                fh.write(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="{color}"/>\n')
        fh.write("</svg>\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dxf")
    parser.add_argument("--encoding", default="gbk")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--margin", type=float, default=500.0)
    args = parser.parse_args()

    dxf_path = Path(args.dxf)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    header, entities = parse_dxf(dxf_path, args.encoding)
    extmin = parse_header_pair_values(header.get("$EXTMIN", []))
    extmax = parse_header_pair_values(header.get("$EXTMAX", []))
    if len(extmin) < 2 or len(extmax) < 2:
        raise SystemExit("DXF header lacks usable EXTMIN/EXTMAX")
    xmin, ymin = extmin[0], extmin[1]
    xmax, ymax = extmax[0], extmax[1]
    origin = (xmin, ymin)

    tris = []
    features = []
    stats: dict[str, int] = {}

    for ent in entities:
        role_info = layer_role(ent.layer)
        if role_info is None:
            continue
        role, default_width, default_height = role_info
        if not in_site(ent.points, xmin, ymin, xmax, ymax, args.margin):
            continue

        local = [(x - origin[0], y - origin[1], z) for x, y, z in ent.points]
        before = len(tris)
        if ent.type == "LINE" and len(local) >= 2:
            add_line_prism(
                tris,
                local[0][0],
                local[0][1],
                local[1][0],
                local[1][1],
                default_width,
                default_height,
                role,
            )
            features.append({"kind": "line", "role": role, "layer": ent.layer, "points": local[:2]})
        elif ent.type == "LWPOLYLINE" and len(local) >= 2:
            xy = [(x, y) for x, y, _ in local]
            closed = bool(ent.flags & 1) or (
                len(xy) >= 3 and math.hypot(xy[0][0] - xy[-1][0], xy[0][1] - xy[-1][1]) < 1.0e-6
            )
            if closed and len(xy) >= 3:
                add_extruded_polygon(tris, xy, default_height, role)
                features.append({"kind": "polygon", "role": role, "layer": ent.layer, "points": local})
            else:
                for a, b in zip(local, local[1:]):
                    add_line_prism(tris, a[0], a[1], b[0], b[1], default_width, default_height, role)
                features.append({"kind": "line", "role": role, "layer": ent.layer, "points": local})
        elif ent.type == "CIRCLE" and ent.radius and local:
            add_cylinder(tris, local[0][0], local[0][1], ent.radius, default_height, role)
            features.append({"kind": "polygon", "role": role, "layer": ent.layer, "points": local})
        elif ent.type == "INSERT" and local:
            x, y, _ = local[0]
            half = default_width / 2.0
            add_box(tris, x - half, y - half, 0.0, x + half, y + half, default_height, role)
            features.append({"kind": "point", "role": role, "layer": ent.layer, "points": local[:1]})
        if len(tris) > before:
            stats[role] = stats.get(role, 0) + 1

    stl = out / "F4_simplified_cfd_obstacles.stl"
    svg = out / "F4_simplified_cfd_plan_preview.svg"
    manifest = out / "F4_simplified_cfd_manifest.json"
    write_stl(stl, tris)
    write_svg(svg, features)
    manifest.write_text(
        json.dumps(
            {
                "status": "DRAFT-SIMPLIFIED-CFD-MODEL-FROM-DXF",
                "source_dxf": str(dxf_path),
                "coordinate_treatment": {
                    "source_header_extmin": extmin,
                    "source_header_extmax": extmax,
                    "local_origin_xy": origin,
                    "assumed_units": "m",
                    "insunits": header.get("$INSUNITS", []),
                },
                "engineering_assumptions": {
                    "equipment_height_m": 8.0,
                    "piperack_height_m": 8.0,
                    "piperack_width_m": 1.2,
                    "piperack_column_width_m": 0.8,
                    "wall_height_m": 3.0,
                    "wall_width_m": 0.6,
                    "bund_height_m": 2.0,
                    "pipe_line_placeholder_width_m": 0.35,
                    "pipe_line_placeholder_height_m": 3.0,
                },
                "feature_count": len(features),
                "triangle_count": len(tris),
                "role_feature_counts": stats,
                "outputs": {
                    "stl": str(stl),
                    "svg_plan_preview": str(svg),
                },
                "limitations": [
                    "Block definitions are represented by INSERT anchor placeholders unless exploded by a CAD tool.",
                    "Entity elevations, real equipment heights, pipe diameters, and nozzle/leak points need engineering data.",
                    "This is a CFD obstacle intake model, not a design-grade 3D CAD reconstruction.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {stl}")
    print(f"Wrote {svg}")
    print(f"Wrote {manifest}")
    print(f"features={len(features)} triangles={len(tris)} roles={stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
