"""Compare a saved FCStd body against the STL it was reconstructed from.

Matching volumes are good evidence but not proof -- material moved from one
place to another cancels out.  This instead classifies random points against
both: `isInside` on the reconstructed solid, ray casting on the raw mesh.  Any
disagreement means the two shapes differ somewhere.

Points within `skin` of the solid's surface are excused, because there the mesh
and the true surface legitimately differ by the faceting error.  That test is
expensive, so it only runs on the points that actually disagreed.

    freecadcmd cad/freecad/verify.py cad/freecad/eccf/ECCF_BOT.FCStd \
        cad/ECCF_BOT.stl [--samples=20000]
"""
import random
import struct
import sys

import FreeCAD as App
import Part
from FreeCAD import Vector

SKIN = 0.05
CELL = 2.0                                     # mm, the ray index's bucket size


def _arg(suffix, default):
    # freecadcmd puts its own script path in argv, so pick by extension.
    for a in sys.argv[1:]:
        if a.endswith(suffix):
            return a
    return default


def _option(name, default):
    # No leading dashes: freecadcmd parses those itself and rejects them.
    for a in sys.argv[1:]:
        if a.startswith(f"{name}="):
            return int(a.split("=", 1)[1])
    return default


def load_mesh(path):
    data = open(path, "rb").read()
    count = struct.unpack("<I", data[80:84])[0]
    tris, off = [], 84
    for _ in range(count):
        v = struct.unpack("<12f", data[off:off + 48])
        off += 50
        tris.append((v[3:6], v[6:9], v[9:12]))
    return tris


def index(tris):
    """Bucket the facets by the Y-Z cell they cover.

    Every ray is cast along +X, so a facet can only ever be hit by rays whose
    Y and Z fall inside its own Y-Z footprint.  Without this the cast is a scan
    over every facet in the mesh and the check takes minutes per part.
    """
    grid = {}
    for tri in tris:
        y0 = int(min(v[1] for v in tri) // CELL)
        y1 = int(max(v[1] for v in tri) // CELL)
        z0 = int(min(v[2] for v in tri) // CELL)
        z1 = int(max(v[2] for v in tri) // CELL)
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                grid.setdefault((y, z), []).append(tri)
    return grid


def in_mesh(p, grid):
    """Ray cast along +X, counting crossings (Moller-Trumbore, dir = 1,0,0)."""
    hits = 0
    px, py, pz = p
    for a, b, c in grid.get((int(py // CELL), int(pz // CELL)), ()):
        if max(a[1], b[1], c[1]) < py or min(a[1], b[1], c[1]) > py:
            continue
        if max(a[2], b[2], c[2]) < pz or min(a[2], b[2], c[2]) > pz:
            continue
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        h = (0.0, -e2[2], e2[1])
        det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
        if abs(det) < 1e-12:
            continue
        inv = 1.0 / det
        s = (px - a[0], py - a[1], pz - a[2])
        u = inv * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])
        if u < 0.0 or u > 1.0:
            continue
        q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2],
             s[0] * e1[1] - s[1] * e1[0])
        v = inv * q[0]
        if v < 0.0 or u + v > 1.0:
            continue
        if inv * (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) > 1e-9:
            hits += 1
    return hits % 2 == 1


def main():
    fcstd = _arg(".FCStd", None)
    stl = _arg(".stl", None)
    samples = _option("samples", 20000)
    if not fcstd or not stl:
        raise SystemExit("usage: verify.py <part.FCStd> <part.stl>")

    doc = App.openDocument(fcstd)
    bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    if not bodies:
        raise SystemExit(f"{fcstd}: no PartDesign body")
    shape = bodies[0].Shape
    grid = index(load_mesh(stl))

    bb = shape.BoundBox
    print(f"solid  volume {shape.Volume:.3f} mm^3, valid={shape.isValid()}")
    print(f"bbox   X[{bb.XMin:.3f},{bb.XMax:.3f}] "
          f"Y[{bb.YMin:.3f},{bb.YMax:.3f}] Z[{bb.ZMin:.3f},{bb.ZMax:.3f}]")
    sys.stdout.flush()

    random.seed(11)
    mismatches = skipped = 0
    for _ in range(samples):
        p = (random.uniform(bb.XMin - 1, bb.XMax + 1),
             random.uniform(bb.YMin - 1, bb.YMax + 1),
             random.uniform(bb.ZMin - 1, bb.ZMax + 1))
        inside = shape.isInside(Vector(*p), 0.0, True)
        if inside == in_mesh(p, grid):
            continue
        # Only now pay for the distance query, to excuse the faceting skin.
        if shape.distToShape(Part.Vertex(Vector(*p)))[0] < SKIN:
            skipped += 1
            continue
        mismatches += 1
        if mismatches <= 10:
            print(f"  MISMATCH ({p[0]:7.3f},{p[1]:7.3f},{p[2]:7.3f}) "
                  f"solid={inside} mesh={not inside}")
    print(f"{samples} samples: {mismatches} mismatches, "
          f"{skipped} excused within {SKIN} mm of a surface")
    sys.stdout.flush()
    if mismatches:
        raise SystemExit("solid and mesh disagree")
    print("OK - solid matches the original mesh")


main()
