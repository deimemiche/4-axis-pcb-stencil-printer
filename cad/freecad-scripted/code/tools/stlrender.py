"""Draw an STL so it can actually be looked at.

    python3 stlrender.py cad/original-stl/ECCF_LEVER.stl                 # four views
    python3 stlrender.py cad/original-stl/ECCF_LEVER.stl out.png size=700 views=iso,top
    python3 stlrender.py a.stl b.stl                        # overlay, two colours

Measuring a mesh tells you what is there; a picture tells you what it *is*.
Arc fitting cannot distinguish a fillet from a sweep from a draft, and a part
whose outline is nothing but tangent arcs is far quicker to read than to
measure.  This renders orthographic views so that reading comes first.

Pure Python and Pillow: a z-buffered triangle rasteriser, flat shaded from a
headlight.  Slow by any real standard and fast enough for a printed part.
"""

import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stlmeasure

# Camera direction and which way is up, per named view.  Y is up in this
# project, so the plan view has to be told to use Z instead.
VIEWS = {
    "front": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    "back":  ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    "side":  ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    "left":  ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    "top":   ((0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
    "under": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "iso":   ((-0.9, -0.7, -1.0), (0.0, 1.0, 0.0)),
    "iso2":  ((0.9, -0.7, 1.0), (0.0, 1.0, 0.0)),
}

BACKGROUND = (24, 24, 28)
PALETTE = ((190, 200, 215), (215, 165, 120))   # one colour per mesh


def _unit(v):
    length = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / length, v[1] / length, v[2] / length)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _basis(direction, up):
    """Right, up and forward for a camera looking along `direction`."""
    forward = _unit(direction)
    right = _unit(_cross(forward, up))
    return right, _cross(right, forward), forward


def _normal(tri):
    a, b, c = tri
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = _cross(e1, e2)
    if n == (0.0, 0.0, 0.0):
        return None
    return _unit(n)


def view(meshes, name, size, extent=None, centre=None):
    """One orthographic view of every mesh in `meshes`, as an RGB image.

    `extent` and `centre` come from the whole set of views when several are
    drawn together, so that all of them share one scale.
    """
    right, up, forward = _basis(*VIEWS[name])
    project = []
    for tris in meshes:
        flat = []
        for tri in tris:
            n = _normal(tri)
            if n is None or n[0] * forward[0] + n[1] * forward[1] \
                    + n[2] * forward[2] > 0.0:
                continue                       # facing away; the mesh is closed
            flat.append(([(p[0] * right[0] + p[1] * right[1] + p[2] * right[2],
                           p[0] * up[0] + p[1] * up[1] + p[2] * up[2],
                           p[0] * forward[0] + p[1] * forward[1]
                           + p[2] * forward[2]) for p in tri], n))
        project.append(flat)

    if extent is None:
        xs = [p[0] for flat in project for tri, _ in flat for p in tri]
        ys = [p[1] for flat in project for tri, _ in flat for p in tri]
        centre = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)))
        extent = max(max(xs) - min(xs), max(ys) - min(ys))

    scale = (size - 24) / extent
    half = size / 2.0
    depth = [1e30] * (size * size)
    pixels = bytearray(BACKGROUND * (size * size))

    for flat, colour in zip(project, PALETTE):
        # A headlight, tilted a little so that faces square to the camera are
        # not all the same shade.
        light = _unit((forward[0] - 0.35 * right[0] - 0.45 * up[0],
                       forward[1] - 0.35 * right[1] - 0.45 * up[1],
                       forward[2] - 0.35 * right[2] - 0.45 * up[2]))
        for tri, n in flat:
            lit = 0.22 + 0.78 * max(0.0, -(n[0] * light[0] + n[1] * light[1]
                                           + n[2] * light[2]))
            shade = bytes(min(255, int(c * lit)) for c in colour)
            pts = [((p[0] - centre[0]) * scale + half,
                    half - (p[1] - centre[1]) * scale, p[2]) for p in tri]
            _fill(pixels, depth, size, pts, shade)

    return Image.frombytes("RGB", (size, size), bytes(pixels))


def _fill(pixels, depth, size, pts, shade):
    """Z-buffer one triangle, barycentric, no clipping beyond the frame."""
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts
    area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if abs(area) < 1e-9:
        return
    lo_x = max(0, int(min(ax, bx, cx)))
    hi_x = min(size - 1, int(max(ax, bx, cx)) + 1)
    lo_y = max(0, int(min(ay, by, cy)))
    hi_y = min(size - 1, int(max(ay, by, cy)) + 1)
    for y in range(lo_y, hi_y + 1):
        py = y + 0.5
        row = y * size
        for x in range(lo_x, hi_x + 1):
            px = x + 0.5
            w0 = ((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / area
            w1 = ((px - ax) * (cy - ay) - (py - ay) * (cx - ax)) / area
            if w0 < 0.0 or w1 < 0.0 or w0 + w1 > 1.0:
                continue
            z = az + w1 * (bz - az) + w0 * (cz - az)
            if z >= depth[row + x]:
                continue
            depth[row + x] = z
            pixels[3 * (row + x):3 * (row + x) + 3] = shade


def sheet(meshes, names, size):
    """Several views side by side, all drawn to the same scale."""
    spans, centres = [], []
    for name in names:
        right, up, _ = _basis(*VIEWS[name])
        xs = [p[0] * right[0] + p[1] * right[1] + p[2] * right[2]
              for tris in meshes for tri in tris for p in tri]
        ys = [p[0] * up[0] + p[1] * up[1] + p[2] * up[2]
              for tris in meshes for tri in tris for p in tri]
        centres.append((0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys))))
        spans.append(max(max(xs) - min(xs), max(ys) - min(ys)))
    extent = max(spans)

    columns = 2 if len(names) > 1 else 1
    rows = (len(names) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * size, rows * size), BACKGROUND)
    for i, name in enumerate(names):
        panel = view(meshes, name, size, extent, centres[i])
        ImageDraw.Draw(panel).text((10, 8), name, fill=(150, 150, 160))
        sheet.paste(panel, ((i % columns) * size, (i // columns) * size))
    return sheet


def main(argv):
    options = dict(a.split("=", 1) for a in argv if "=" in a and
                   not a.endswith(".stl") and not a.endswith(".png"))
    stls = [a for a in argv if a.endswith(".stl")]
    out = next((a for a in argv if a.endswith(".png")), None)
    if not stls:
        raise SystemExit(__doc__)
    if out is None:
        out = os.path.splitext(os.path.basename(stls[0]))[0] + ".png"

    size = int(options.get("size", 420))
    names = options.get("views", "iso,front,side,top").split(",")
    meshes = [stlmeasure.read_stl(path) for path in stls]
    sheet(meshes, names, size).save(out)
    print(f"{out}: {' '.join(names)}, {sum(len(m) for m in meshes)} facets")


if __name__ == "__main__":
    main(sys.argv[1:])
