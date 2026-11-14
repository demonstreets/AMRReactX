#!/usr/bin/env python3
"""Build F4/F5 v2 CFD geometry from total-plan DXF plus equipment PDFs data."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from build_dxf_cfd_simplified_model import (
    add_box,
    add_extruded_polygon,
    add_line_prism,
    in_site,
    layer_role,
    parse_dxf,
    parse_header_pair_values,
    tri_normal,
    write_stl,
)


def add_tri(tris, a, b, c, role: str) -> None:
    tris.append((tri_normal(a, b, c), a, b, c, role))


def rotate_point(x: float, y: float, angle_deg: float) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


def add_oriented_box(
    tris,
    cx: float,
    cy: float,
    length: float,
    width: float,
    zmin: float,
    zmax: float,
    angle_deg: float,
    role: str,
) -> list[tuple[float, float, float]]:
    hx, hy = length / 2.0, width / 2.0
    local = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    pts = []
    for x, y in local:
        rx, ry = rotate_point(x, y, angle_deg)
        pts.append((cx + rx, cy + ry))
    add_extruded_polygon(tris, pts, zmax - zmin, role)
    if zmin:
        # The helper extrudes from z=0. For elevated slabs/equipment, add a
        # second shifted shell by direct boxes for conservative bounding volume.
        before = len(tris)
        del tris[before - (len(pts) * 2 + (len(pts) - 2) * 2):]
        bottom = [(x, y, zmin) for x, y in pts]
        top = [(x, y, zmax) for x, y in pts]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            add_tri(tris, bottom[i], bottom[j], top[j], role)
            add_tri(tris, bottom[i], top[j], top[i], role)
        for i in range(1, n - 1):
            add_tri(tris, bottom[0], bottom[i + 1], bottom[i], role)
            add_tri(tris, top[0], top[i], top[i + 1], role)
    return [(x, y, zmin) for x, y in pts] + [(x, y, zmax) for x, y in pts]


def add_vertical_cylinder(
    tris,
    cx: float,
    cy: float,
    radius: float,
    zmin: float,
    zmax: float,
    role: str,
    segments: int = 72,
) -> None:
    bottom = []
    top = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        x = cx + radius * math.cos(a)
        y = cy + radius * math.sin(a)
        bottom.append((x, y, zmin))
        top.append((x, y, zmax))
    for i in range(segments):
        j = (i + 1) % segments
        add_tri(tris, bottom[i], bottom[j], top[j], role)
        add_tri(tris, bottom[i], top[j], top[i], role)
    for i in range(1, segments - 1):
        add_tri(tris, bottom[0], bottom[i + 1], bottom[i], role)
        add_tri(tris, top[0], top[i], top[i + 1], role)


def add_horizontal_cylinder(
    tris,
    cx: float,
    cy: float,
    zc: float,
    length: float,
    radius: float,
    angle_deg: float,
    role: str,
    segments: int = 24,
) -> None:
    ux, uy = rotate_point(1.0, 0.0, angle_deg)
    vx, vy = -uy, ux
    p1 = (cx - ux * length / 2.0, cy - uy * length / 2.0, zc)
    p2 = (cx + ux * length / 2.0, cy + uy * length / 2.0, zc)
    rings = []
    for base in [p1, p2]:
        ring = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            x = base[0] + vx * radius * math.cos(a)
            y = base[1] + vy * radius * math.cos(a)
            z = base[2] + radius * math.sin(a)
            ring.append((x, y, z))
        rings.append(ring)
    r0, r1 = rings
    for i in range(segments):
        j = (i + 1) % segments
        add_tri(tris, r0[i], r1[i], r1[j], role)
        add_tri(tris, r0[i], r1[j], r0[j], role)
    for i in range(1, segments - 1):
        add_tri(tris, r0[0], r0[i], r0[i + 1], role)
        add_tri(tris, r1[0], r1[i + 1], r1[i], role)


def write_preview_png(path: Path, features: list[dict[str, object]], width=1800, height=1200) -> None:
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:
        print(f"preview skipped: {exc}", file=sys.stderr)
        return
    xs = [p[0] for f in features for p in f["points"]]
    ys = [p[1] for f in features for p in f["points"]]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    pad = 40
    scale = min((width - 2 * pad) / max(xmax - xmin, 1.0), (height - 2 * pad) / max(ymax - ymin, 1.0))

    def mp(p):
        return (pad + (p[0] - xmin) * scale, height - pad - (p[1] - ymin) * scale)

    colors = {
        "cryogenic_propane_tank": (190, 30, 30),
        "cryogenic_butane_tank": (220, 100, 20),
        "ambient_vertical_tank": (160, 70, 200),
        "horizontal_lpg_tank": (120, 80, 200),
        "piperack": (30, 100, 220),
        "piperack_column": (30, 80, 180),
        "wall": (20, 20, 20),
        "bund_or_tank_area": (150, 80, 30),
        "pipe_or_line": (0, 140, 80),
        "bog_platform": (0, 110, 170),
        "loading_station": (100, 100, 100),
        "flare_area": (230, 70, 20),
        "equipment": (200, 90, 40),
    }
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 18), f"F4/F5 CFD geometry v2 preview: {len(features)} features", fill=(0, 0, 0))
    for feat in features:
        role = str(feat["role"])
        color = colors.get(role, (90, 90, 90))
        pts = [mp(p) for p in feat["points"]]
        kind = feat.get("kind")
        if kind == "circle":
            cx, cy = mp(feat["points"][0])
            r = float(feat["radius"]) * scale
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
        elif kind == "polygon":
            draw.polygon(pts, outline=color, fill=tuple(int(c * 0.18 + 255 * 0.82) for c in color))
        elif len(pts) >= 2:
            draw.line(pts, fill=color, width=2)
        elif pts:
            x, y = pts[0]
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=color)
        if feat.get("label"):
            x, y = pts[0]
            draw.text((x + 4, y + 4), str(feat["label"]), fill=color)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def add_f4_backbone(dxf_path: Path, encoding: str, tris, features, margin: float) -> dict:
    header, entities = parse_dxf(dxf_path, encoding)
    extmin = parse_header_pair_values(header.get("$EXTMIN", []))
    extmax = parse_header_pair_values(header.get("$EXTMAX", []))
    if len(extmin) < 2 or len(extmax) < 2:
        raise ValueError("DXF lacks usable EXTMIN/EXTMAX")
    xmin, ymin = extmin[0], extmin[1]
    xmax, ymax = extmax[0], extmax[1]
    origin = (xmin, ymin)
    stats: dict[str, int] = {}
    kept_roles = {"piperack", "piperack_column", "wall", "bund_or_tank_area", "pipe_or_line", "equipment"}
    for ent in entities:
        role_info = layer_role(ent.layer)
        if role_info is None:
            continue
        role, default_width, default_height = role_info
        if role not in kept_roles:
            continue
        if not in_site(ent.points, xmin, ymin, xmax, ymax, margin):
            continue
        local = [(x - origin[0], y - origin[1], z) for x, y, z in ent.points]
        before = len(tris)
        if ent.type == "LINE" and len(local) >= 2:
            add_line_prism(tris, local[0][0], local[0][1], local[1][0], local[1][1], default_width, default_height, role)
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
            # Keep small process/utility circles from the DXF, but replace known
            # large tanks with explicit F5 dimensions below.
            if ent.radius < 20.0:
                add_vertical_cylinder(tris, local[0][0], local[0][1], ent.radius, 0.0, default_height, role)
                features.append({"kind": "circle", "role": role, "layer": ent.layer, "points": local[:1], "radius": ent.radius})
        elif ent.type == "INSERT" and local:
            x, y, _ = local[0]
            half = default_width / 2.0
            add_box(tris, x - half, y - half, 0.0, x + half, y + half, default_height, role)
            features.append({"kind": "point", "role": role, "layer": ent.layer, "points": local[:1]})
        if len(tris) > before:
            stats[role] = stats.get(role, 0) + 1
    return {"origin": origin, "extmin": extmin, "extmax": extmax, "backbone_role_counts": stats}


def add_equipment_overlay(tris, features) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    def circle_feature(label, role, cx, cy, radius, zmin, zmax, confidence, source):
        add_vertical_cylinder(tris, cx, cy, radius, zmin, zmax, role)
        features.append({"kind": "circle", "role": role, "label": label, "points": [(cx, cy, zmin)], "radius": radius})
        items.append({"tag": label, "role": role, "center_xy_m": [cx, cy], "radius_m": radius, "zmin_m": zmin, "zmax_m": zmax, "confidence": confidence, "source": source})

    def h_cyl_feature(label, role, cx, cy, zc, length, radius, angle, confidence, source):
        add_horizontal_cylinder(tris, cx, cy, zc, length, radius, angle, role)
        features.append({"kind": "circle", "role": role, "label": label, "points": [(cx, cy, zc)], "radius": radius})
        items.append({"tag": label, "role": role, "center_xy_m": [cx, cy], "center_z_m": zc, "length_m": length, "radius_m": radius, "angle_deg": angle, "confidence": confidence, "source": source})

    def box_feature(label, role, cx, cy, length, width, zmin, zmax, angle, confidence, source):
        pts = add_oriented_box(tris, cx, cy, length, width, zmin, zmax, angle, role)
        features.append({"kind": "polygon", "role": role, "label": label, "points": pts[:4]})
        items.append({"tag": label, "role": role, "center_xy_m": [cx, cy], "length_m": length, "width_m": width, "zmin_m": zmin, "zmax_m": zmax, "angle_deg": angle, "confidence": confidence, "source": source})

    site_angle = 143.8877001

    # Low-temperature butane tank center is present as a large F4 circle.
    circle_feature(
        "TK-51201",
        "cryogenic_butane_tank",
        956.941,
        1290.219,
        26.8,
        2.5,
        2.5 + 34.4,
        "high",
        "F4 large circle + F5 PDF TK-51201 outer tank Phi53.6 x 34.4 m",
    )

    # Low-temperature propane group placement is constrained by the northern
    # F4 tank-farm boundary and F5 group geometry; exact block geometry needs
    # native CAD block explosion for final survey-grade placement.
    circle_feature(
        "TK-51101",
        "cryogenic_propane_tank",
        1103.0,
        1302.0,
        30.0,
        2.5,
        2.5 + 38.1,
        "medium",
        "F5 PDF TK-51101 outer tank Phi60.0 x 38.1 m; F4 northern tank-farm placement",
    )
    circle_feature(
        "TK-51102",
        "cryogenic_propane_tank",
        1194.0,
        1302.0,
        30.0,
        2.5,
        2.5 + 38.1,
        "medium",
        "F5 PDF TK-51102 outer tank Phi60.0 x 38.1 m; F4 northern tank-farm placement",
    )

    for tag, cx, cy in [
        ("TK53001", 1014.361, 1158.487),
        ("TK53002", 989.722, 1176.462),
        ("TK53003", 965.533, 1194.109),
        ("TK53004", 940.873, 1160.308),
    ]:
        circle_feature(
            tag,
            "ambient_vertical_tank",
            cx,
            cy,
            9.85,
            0.7,
            24.1,
            "medium",
            "F4 repeated tank arcs + F5 PDF constant-temperature tank Phi19.7 seen in F4 tag text; platform EL+23.400",
        )

    h_cyl_feature(
        "TK53005",
        "horizontal_lpg_tank",
        941.485,
        1211.917,
        0.7 + 1.6,
        17.5,
        1.6,
        site_angle,
        "medium",
        "F4 tag coordinate + F5 PDF horizontal LPG tank Phi3.2 x 17.5 m",
    )
    h_cyl_feature(
        "TK53006",
        "horizontal_lpg_tank",
        917.204,
        1178.570,
        0.7 + 1.6,
        17.5,
        1.6,
        site_angle,
        "medium",
        "F4 tag coordinate + F5 PDF horizontal LPG tank Phi3.2 x 17.5 m",
    )

    box_feature("BOG_ground_platform", "bog_platform", 1042.383, 1068.704, 55.0, 30.0, 0.0, 0.35, site_angle, "medium", "F4 BOG label + F5 PDF PD03-01")
    box_feature("BOG_EL5_platform", "bog_platform", 1042.383, 1068.704, 28.0, 16.0, 5.0, 5.35, site_angle, "medium", "F5 PDF PD03-02 EL+5.000 platform")
    box_feature("BOG_EL10_platform", "bog_platform", 1060.0, 1082.0, 28.0, 16.0, 10.0, 10.35, site_angle, "medium", "F5 PDF PD03-02/03 EL+10.000 platform")
    for i, offset in enumerate([-16.0, 0.0, 16.0], start=1):
        dx, dy = rotate_point(offset, 0.0, site_angle)
        box_feature(f"C-52001{chr(64+i)}", "equipment", 1042.383 + dx, 1068.704 + dy, 8.0, 4.0, 0.2, 4.2, site_angle, "medium", "F5 PDF BOG compressors")

    box_feature("loading_station_canopy", "loading_station", 755.54, 1052.44, 130.0, 18.0, -0.2, 7.0, site_angle, "medium", "F4 loading-station label + F5 PDF 20 visible loading bays")
    box_feature("air_nitrogen_station", "equipment", 757.99, 974.04, 24.0, 14.0, -0.2, 5.5, site_angle, "medium", "F4 label + F5 PDF air-compressor/nitrogen building section")
    circle_feature("flare_unit_A", "flare_area", 884.0, 1024.0, 15.0, 0.0, 4.0, "medium", "F4 flare-system label + F5 PDF two circular flare units")
    circle_feature("flare_unit_B", "flare_area", 916.0, 1036.0, 15.0, 0.0, 4.0, "medium", "F4 flare-system label + F5 PDF two circular flare units")

    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dxf", required=True)
    parser.add_argument("--equipment-data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--encoding", default="gbk")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    tris = []
    features: list[dict[str, object]] = []
    f4_info = add_f4_backbone(Path(args.dxf), args.encoding, tris, features, margin=500.0)
    equipment_items = add_equipment_overlay(tris, features)

    stl = out / "F4_F5_propane_storage_cfd_model_v2.stl"
    preview = out / "F4_F5_propane_storage_cfd_model_v2_preview.png"
    manifest = out / "F4_F5_propane_storage_cfd_model_v2_manifest.json"
    write_stl(stl, tris)
    write_preview_png(preview, features)
    data = json.loads(Path(args.equipment_data).read_text(encoding="utf-8"))
    manifest.write_text(
        json.dumps(
            {
                "status": "DRAFT-F4-F5-CFD-MODEL-V2",
                "source_dxf": args.dxf,
                "source_equipment_data": args.equipment_data,
                "f4_coordinate_info": f4_info,
                "f5_data_status": data.get("status"),
                "model_policy": "F4 total plan supplies plant coordinates/backbone; F5 equipment PDFs supply tank dimensions, elevations, and platform heights.",
                "feature_count": len(features),
                "triangle_count": len(tris),
                "equipment_overlay": equipment_items,
                "outputs": {
                    "stl": str(stl),
                    "preview_png": str(preview),
                    "manifest": str(manifest),
                },
                "known_limitations": [
                    "Low-temperature propane tank exact center placement remains medium confidence until native CAD block explosion or survey coordinates are supplied.",
                    "Detailed pipe diameters, nozzle/leak positions, and equipment elevations still require P&ID, equipment tables, or operator-specified scenario data.",
                    "This model is a CFD obstacle/geometry intake model, not a fabrication-grade 3D CAD model.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {stl}")
    print(f"Wrote {preview}")
    print(f"Wrote {manifest}")
    print(f"features={len(features)} triangles={len(tris)} equipment_overlay={len(equipment_items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
