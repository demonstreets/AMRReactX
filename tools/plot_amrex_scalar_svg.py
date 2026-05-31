#!/usr/bin/env python3

import argparse
import math
import re
import struct
import zlib
from pathlib import Path


BOX_RE = re.compile(r"\(\(([-0-9]+),([-0-9]+),([-0-9]+)\) \(([-0-9]+),([-0-9]+),([-0-9]+)\)")


def read_plot_header(plotdir):
    lines = (plotdir / "Header").read_text().splitlines()
    ncomp = int(lines[1])
    names = lines[2:2 + ncomp]
    dim = int(lines[2 + ncomp])
    time = float(lines[3 + ncomp])
    prob_lo = [float(x) for x in lines[5 + ncomp].split()]
    prob_hi = [float(x) for x in lines[6 + ncomp].split()]
    domain_match = BOX_RE.search(lines[8 + ncomp])
    if not domain_match:
        raise ValueError("Could not parse domain box")
    lo = [int(domain_match.group(i)) for i in range(1, 4)]
    hi = [int(domain_match.group(i)) for i in range(4, 7)]
    shape = [hi[d] - lo[d] + 1 for d in range(3)]
    return names, dim, time, prob_lo, prob_hi, shape


def read_level_header(plotdir):
    lines = (plotdir / "Level_0" / "Cell_H").read_text().splitlines()
    # First line like "(30 0"; the following lines contain boxes until ")".
    box_count = int(lines[4].strip().lstrip("(").split()[0])
    boxes = []
    idx = 5
    while len(boxes) < box_count:
        match = BOX_RE.search(lines[idx])
        if match:
            boxes.append(tuple(int(match.group(i)) for i in range(1, 7)))
        idx += 1
    while idx < len(lines) and lines[idx].strip() != str(box_count):
        idx += 1
    idx += 1
    fabs = []
    for _ in range(box_count):
        parts = lines[idx].split()
        fabs.append((parts[1], int(parts[2])))
        idx += 1
    return boxes, fabs


def read_fab_component(path, offset, npoints, ncomp, component):
    raw = path.read_bytes()[offset:]
    first_newline = raw.find(b"\n")
    data = raw[first_newline + 1:]
    start = component * npoints * 8
    return struct.unpack_from(f"<{npoints}d", data, start)


def load_component(plotdir, component):
    names, dim, time, prob_lo, prob_hi, shape = read_plot_header(plotdir)
    boxes, fabs = read_level_header(plotdir)
    nx, ny, nz = shape
    ncomp = len(names)
    data = [[[0.0 for _ in range(nz)] for _ in range(ny)] for _ in range(nx)]

    for box, (filename, offset) in zip(boxes, fabs):
        i0, j0, k0, i1, j1, k1 = box
        nx_b = i1 - i0 + 1
        ny_b = j1 - j0 + 1
        nz_b = k1 - k0 + 1
        npoints = nx_b * ny_b * nz_b
        vals = read_fab_component(plotdir / "Level_0" / filename, offset, npoints, ncomp, component)
        for k in range(k0, k1 + 1):
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    local = (i - i0) + nx_b * ((j - j0) + ny_b * (k - k0))
                    data[i][j][k] = vals[local]
    return data, names, time, prob_lo, prob_hi, shape


def infer_color(v, vmax):
    if vmax <= 0:
        t = 0.0
    else:
        t = max(0.0, min(1.0, v / vmax))
    # dark blue -> cyan -> yellow -> red
    stops = [
        (0.00, (10, 22, 50)),
        (0.25, (20, 105, 180)),
        (0.50, (35, 190, 210)),
        (0.75, (245, 215, 85)),
        (1.00, (190, 35, 25)),
    ]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            a = (t - t0) / (t1 - t0)
            rgb = tuple(round(c0[i] + a * (c1[i] - c0[i])) for i in range(3))
            return rgb
    return (190, 35, 25)


def rgb_string(rgb):
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def write_heatmap_svg(path, values, title, x_label, y_label, vmax):
    rows = len(values)
    cols = len(values[0])
    cell = max(3, min(10, 900 // max(cols, rows)))
    margin_l, margin_t, margin_r, margin_b = 70, 55, 140, 55
    width = margin_l + cols * cell + margin_r
    height = margin_t + rows * cell + margin_b

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f8fb"/>',
        f'<text x="{margin_l}" y="28" font-family="Arial" font-size="20" font-weight="700" fill="#172033">{title}</text>',
        f'<text x="{margin_l}" y="{height - 15}" font-family="Arial" font-size="13" fill="#334155">{x_label}</text>',
        f'<text x="18" y="{margin_t + rows * cell / 2}" transform="rotate(-90 18 {margin_t + rows * cell / 2})" font-family="Arial" font-size="13" fill="#334155">{y_label}</text>',
    ]
    for r in range(rows):
        for c in range(cols):
            color = rgb_string(infer_color(values[rows - 1 - r][c], vmax))
            x = margin_l + c * cell
            y = margin_t + r * cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}"/>')
    parts.append(f'<rect x="{margin_l}" y="{margin_t}" width="{cols * cell}" height="{rows * cell}" fill="none" stroke="#0f172a" stroke-width="1"/>')

    legend_x = margin_l + cols * cell + 35
    legend_y = margin_t
    legend_h = rows * cell
    legend_w = 22
    for q in range(80):
        y = legend_y + q * legend_h / 80
        color = rgb_string(infer_color(1.0 - q / 79, 1.0))
        parts.append(f'<rect x="{legend_x}" y="{y}" width="{legend_w}" height="{legend_h / 80 + 1}" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 32}" y="{legend_y + 5}" font-family="Arial" font-size="12" fill="#334155">{vmax:.3g}</text>')
    parts.append(f'<text x="{legend_x + 32}" y="{legend_y + legend_h}" font-family="Arial" font-size="12" fill="#334155">0</text>')
    parts.append(f'<text x="{legend_x}" y="{legend_y + legend_h + 24}" font-family="Arial" font-size="12" fill="#334155">Y_leak</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def png_chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def write_heatmap_png(path, values, vmax, scale=5):
    rows = len(values)
    cols = len(values[0])
    width = cols * scale
    height = rows * scale
    raw_rows = []
    for r in range(rows):
        row = bytearray()
        source_row = rows - 1 - r
        for c in range(cols):
            rgb = infer_color(values[source_row][c], vmax)
            for _ in range(scale):
                row.extend(rgb)
        expanded = bytes(row)
        for _ in range(scale):
            raw_rows.append(b"\x00" + expanded)
    raw = b"".join(raw_rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plotdir", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--prefix", default="scene_leak")
    parser.add_argument("--x-slice", type=float, default=4.0)
    parser.add_argument("--y-slice", type=float, default=5.0)
    parser.add_argument("--z-slice", type=float, default=0.5)
    args = parser.parse_args()

    plotdir = Path(args.plotdir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    data, names, time, prob_lo, prob_hi, shape = load_component(plotdir, names_index("Y_leak", plotdir))
    nx, ny, nz = shape
    dx = [(prob_hi[d] - prob_lo[d]) / shape[d] for d in range(3)]
    vmax = max(data[i][j][k] for i in range(nx) for j in range(ny) for k in range(nz))

    k_near_ground = min(range(nz), key=lambda k: abs(prob_lo[2] + (k + 0.5) * dx[2] - args.z_slice))
    j_center = min(range(ny), key=lambda j: abs(prob_lo[1] + (j + 0.5) * dx[1] - args.y_slice))
    i_downstream = min(range(nx), key=lambda i: abs(prob_lo[0] + (i + 0.5) * dx[0] - args.x_slice))

    xy = [[data[i][j][k_near_ground] for i in range(nx)] for j in range(ny)]
    xz = [[data[i][j_center][k] for i in range(nx)] for k in range(nz)]
    yz = [[data[i_downstream][j][k] for j in range(ny)] for k in range(nz)]

    z_value = prob_lo[2] + (k_near_ground + 0.5) * dx[2]
    y_value = prob_lo[1] + (j_center + 0.5) * dx[1]
    x_value = prob_lo[0] + (i_downstream + 0.5) * dx[0]
    write_heatmap_svg(outdir / f"{args.prefix}_xy_near_ground.svg", xy,
                      f"Y_leak horizontal slice, z={z_value:.2f} m, t={time:.2f} s",
                      "x streamwise (m)", "y lateral (m)", vmax)
    write_heatmap_svg(outdir / f"{args.prefix}_xz_centerline.svg", xz,
                      f"Y_leak centerline vertical slice, y={y_value:.2f} m, t={time:.2f} s",
                      "x streamwise (m)", "z vertical (m)", vmax)
    write_heatmap_svg(outdir / f"{args.prefix}_yz_downstream.svg", yz,
                      f"Y_leak crosswind slice, x={x_value:.2f} m, t={time:.2f} s",
                      "y lateral (m)", "z vertical (m)", vmax)
    write_heatmap_png(outdir / f"{args.prefix}_xy_near_ground.png", xy, vmax)
    write_heatmap_png(outdir / f"{args.prefix}_xz_centerline.png", xz, vmax)
    write_heatmap_png(outdir / f"{args.prefix}_yz_downstream.png", yz, vmax)
    print(f"vmax={vmax:.12g}")
    print(outdir / f"{args.prefix}_xy_near_ground.svg")
    print(outdir / f"{args.prefix}_xz_centerline.svg")
    print(outdir / f"{args.prefix}_yz_downstream.svg")
    print(outdir / f"{args.prefix}_xy_near_ground.png")
    print(outdir / f"{args.prefix}_xz_centerline.png")
    print(outdir / f"{args.prefix}_yz_downstream.png")


def names_index(name, plotdir):
    names, *_ = read_plot_header(Path(plotdir))
    return names.index(name)


if __name__ == "__main__":
    main()
