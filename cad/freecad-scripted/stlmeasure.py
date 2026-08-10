"""Measure the original STL meshes, so the reconstructions can be drawn to fit.

The parts in ../ are meshes only -- the original author's sources were never
published.  Rather than eyeball them, this module takes the dimensions off the
triangles directly.

Most of the parts are 3D printed and therefore layered: a stack of prisms along
the print axis, each layer a constant cross section.  `analyse` finds that axis,
finds the heights at which the cross section changes, and returns the outline of
each layer as a polygon with its arcs fitted back to centres and radii.  That is
exactly the information needed to redraw the part as sketches and pads.

Uses nothing but the standard library, so it runs under plain python3 as well as
under FreeCAD's interpreter:

    python3 cad/freecad/stlmeasure.py cad/original-stl/BOT_RAIL_HOLDER.stl
    python3 cad/freecad/stlmeasure.py cad/original-stl/*.stl --summary
"""

import math
import struct
import sys
from collections import defaultdict

TOL = 1e-6

AXES = ("x", "y", "z")


# --------------------------------------------------------------------------- #
# mesh                                                                         #
# --------------------------------------------------------------------------- #

def read_stl(path):
    """Return the triangles of a binary STL as [(v0, v1, v2), ...]."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:5] == b"solid" and b"facet" in data[:512]:
        raise ValueError(f"{path}: ASCII STL, not supported")
    count = struct.unpack("<I", data[80:84])[0]
    tris = []
    for i in range(count):
        base = 84 + i * 50
        values = struct.unpack("<12f", data[base:base + 48])
        tris.append((values[3:6], values[6:9], values[9:12]))
    return tris


def bbox(tris):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for tri in tris:
        for vertex in tri:
            for k in range(3):
                lo[k] = min(lo[k], vertex[k])
                hi[k] = max(hi[k], vertex[k])
    return lo, hi


def volume(tris):
    """Signed volume via the divergence theorem, one tetrahedron per facet."""
    total = 0.0
    for a, b, c in tris:
        total += (a[0] * (b[1] * c[2] - b[2] * c[1])
                  - a[1] * (b[0] * c[2] - b[2] * c[0])
                  + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return abs(total) / 6.0


def _normal_area(tri):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length < TOL:
        return (0.0, 0.0, 0.0), 0.0
    return (nx / length, ny / length, nz / length), length / 2.0


# --------------------------------------------------------------------------- #
# layer structure                                                              #
# --------------------------------------------------------------------------- #

def prismatic_score(tris, axis):
    """Fraction of the surface area that a prism along `axis` would explain.

    A prism's surface is either perpendicular to the axis (the caps and any
    ledges between layers) or parallel to it (the walls).  Anything else --
    a chamfer, a dome, a helix -- shows up as the shortfall.
    """
    aligned = 0.0
    total = 0.0
    for tri in tris:
        normal, area = _normal_area(tri)
        if area == 0.0:
            continue
        total += area
        component = abs(normal[axis])
        if component > 0.9999 or component < 0.0001:
            aligned += area
    return aligned / total if total else 0.0


def levels(tris, axis, min_area=0.5):
    """Heights along `axis` at which the cross section changes.

    These are the planes of the facets facing along the axis, i.e. the caps and
    ledges.  Returned as [(height, area), ...] sorted by height; `min_area`
    drops slivers left by the mesher.
    """
    found = defaultdict(float)
    for tri in tris:
        normal, area = _normal_area(tri)
        if area == 0.0 or abs(normal[axis]) < 0.9999:
            continue
        found[round(tri[0][axis], 4)] += area
    return sorted((h, a) for h, a in found.items() if a >= min_area)


# --------------------------------------------------------------------------- #
# cross sections                                                               #
# --------------------------------------------------------------------------- #

def section(tris, axis, height):
    """The outline of the mesh cut at `height`, as a list of closed loops.

    Each loop is a list of (u, v) points in the plane, wound anticlockwise for
    material and clockwise for holes.  Cut between layers, never on one, so no
    facet ever lies in the cutting plane.
    """
    u_axis, v_axis = [k for k in range(3) if k != axis]
    segments = []
    for tri in tris:
        # A vertex sitting exactly in the cutting plane counts as above, so
        # every straddling facet always splits one against two.
        below = [v for v in tri if v[axis] < height]
        above = [v for v in tri if v[axis] >= height]
        if not below or not above:
            continue
        lone = below[0] if len(below) == 1 else above[0]
        others = above if len(below) == 1 else below
        crossings = []
        for other in others:
            t = (height - lone[axis]) / (other[axis] - lone[axis])
            crossings.append((lone[u_axis] + t * (other[u_axis] - lone[u_axis]),
                              lone[v_axis] + t * (other[v_axis] - lone[v_axis])))
        # Orient the segment so that material lies to its left, i.e. so that
        # the facet's outward normal points to its right.
        normal, _ = _normal_area(tri)
        edge = (crossings[1][0] - crossings[0][0], crossings[1][1] - crossings[0][1])
        if edge[0] * normal[v_axis] - edge[1] * normal[u_axis] > 0:
            crossings.reverse()
        segments.append(tuple(crossings))
    return _chain(segments)


def _chain(segments, grid=1e-4):
    """Join oriented segments end to end into closed loops."""
    def key(point):
        return (round(point[0] / grid), round(point[1] / grid))

    starts = defaultdict(list)
    for segment in segments:
        if key(segment[0]) != key(segment[1]):
            starts[key(segment[0])].append(segment)

    loops = []
    while starts:
        first = next(iter(starts))
        segment = starts[first].pop()
        if not starts[first]:
            del starts[first]
        loop = [segment[0], segment[1]]
        while True:
            here = key(loop[-1])
            if here == key(loop[0]) and len(loop) > 2:
                loop.pop()
                break
            if here not in starts:
                break
            segment = starts[here].pop()
            if not starts[here]:
                del starts[here]
            loop.append(segment[1])
        if len(loop) >= 3:
            loops.append(loop)
    return loops


def area(loop):
    """Signed area; positive anticlockwise, so holes come out negative."""
    total = 0.0
    for i, (x0, y0) in enumerate(loop):
        x1, y1 = loop[(i + 1) % len(loop)]
        total += x0 * y1 - x1 * y0
    return total / 2.0


# --------------------------------------------------------------------------- #
# turning a meshed loop back into lines and arcs                               #
# --------------------------------------------------------------------------- #

def _turn(prev, here, nxt):
    ax, ay = here[0] - prev[0], here[1] - prev[1]
    bx, by = nxt[0] - here[0], nxt[1] - here[1]
    return math.atan2(ax * by - ay * bx, ax * bx + ay * by)


def _drop_collinear(loop, tol=1e-4):
    kept = []
    for i, point in enumerate(loop):
        prev = loop[i - 1]
        nxt = loop[(i + 1) % len(loop)]
        if abs(_turn(prev, point, nxt)) > tol:
            kept.append(point)
    return kept or loop


def _fit_circle(points):
    """Kasa least squares circle; returns (cx, cy, r, max residual)."""
    n = len(points)
    sx = sy = sxx = syy = sxy = sxz = syz = sz = 0.0
    for x, y in points:
        z = x * x + y * y
        sx += x
        sy += y
        sxx += x * x
        syy += y * y
        sxy += x * y
        sxz += x * z
        syz += y * z
        sz += z
    a = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, float(n)]]
    b = [sxz, syz, sz]
    for col in range(3):                       # Gaussian elimination
        pivot = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            return None
        a[col], a[pivot] = a[pivot], a[col]
        b[col], b[pivot] = b[pivot], b[col]
        for row in range(3):
            if row == col:
                continue
            factor = a[row][col] / a[col][col]
            for k in range(col, 3):
                a[row][k] -= factor * a[col][k]
            b[row] -= factor * b[col]
    cx = b[0] / a[0][0] / 2.0
    cy = b[1] / a[1][1] / 2.0
    radius = math.sqrt(max(b[2] / a[2][2] + cx * cx + cy * cy, 0.0))
    worst = max(abs(math.hypot(x - cx, y - cy) - radius) for x, y in points)
    return cx, cy, radius, worst


MAX_ARC_RADIUS = 400.0                         # beyond this, call it a line


def _dedupe(loop, tol=1e-6):
    kept = [loop[0]]
    for point in loop[1:]:
        if math.hypot(point[0] - kept[-1][0], point[1] - kept[-1][1]) > tol:
            kept.append(point)
    if (len(kept) > 1
            and math.hypot(kept[0][0] - kept[-1][0],
                           kept[0][1] - kept[-1][1]) <= tol):
        kept.pop()
    return kept


def _sweep(centre, points):
    """Total turn about `centre` walking along `points`, sign included."""
    cx, cy = centre
    total = 0.0
    previous = math.atan2(points[0][1] - cy, points[0][0] - cx)
    for x, y in points[1:]:
        angle = math.atan2(y - cy, x - cx)
        step = angle - previous
        while step > math.pi:
            step -= 2 * math.pi
        while step < -math.pi:
            step += 2 * math.pi
        total += step
        previous = angle
    return total


def features(loop, tol=2e-3, min_points=5):
    """Describe a meshed loop as straight runs and fitted arcs.

    Grows an arc from each vertex for as long as a least squares circle still
    passes through every point of the run.  Matching the turn angle between
    consecutive vertices would be cheaper, but meshers duplicate vertices and
    split facets unevenly, and then the turn angles alternate and the arc is
    missed -- which matters here, where a blended lever is mostly arcs.

    Returns ('line', p0, p1) and ('arc', centre, radius, p0, p1, sweep) items.
    """
    loop = _dedupe(_drop_collinear(loop))
    n = len(loop)
    if n < 3:
        return []

    out = []
    i = 0
    while i < n:
        best = None
        j = i + min_points - 1
        while j < i + n:
            points = [loop[k % n] for k in range(i, j + 1)]
            fit = _fit_circle(points)
            if (fit is None or fit[2] > MAX_ARC_RADIUS
                    or fit[3] > tol * max(1.0, fit[2])):
                break
            best = (j, fit, points)
            j += 1
        if best is None:
            out.append(("line", loop[i], loop[(i + 1) % n]))
            i += 1
            continue
        end, (cx, cy, radius, _), points = best
        out.append(("arc", (cx, cy), radius, loop[i], loop[end % n],
                    _sweep((cx, cy), points)))
        i = end
    return out


# --------------------------------------------------------------------------- #
# cylinders                                                                    #
# --------------------------------------------------------------------------- #

def cylinders(tris, axis, tol=1e-3, min_facets=6):
    """Find the cylindrical faces whose axis runs along `axis`.

    A cylinder is meshed as a band of facets all parallel to its axis, joined
    edge to edge.  Grouping those bands and fitting a circle to each recovers
    the bores and bosses -- including the ones drilled across the build axis,
    which the layer sections cannot see.

    Returns [(centre_u, centre_v, radius, lo, hi, sweep_deg, is_bore), ...].
    """
    u_axis, v_axis = [k for k in range(3) if k != axis]
    parallel = [t for t in tris if abs(_normal_area(t)[0][axis]) < 1e-4
                and _normal_area(t)[1] > 0]

    # Connect facets that share an edge, in projection.
    def key(vertex):
        return (round(vertex[u_axis], 4), round(vertex[v_axis], 4))

    owners = defaultdict(list)
    for index, tri in enumerate(parallel):
        for vertex in tri:
            owners[key(vertex)].append(index)

    seen = set()
    found = []
    for start in range(len(parallel)):
        if start in seen:
            continue
        stack, group = [start], []
        seen.add(start)
        while stack:
            index = stack.pop()
            group.append(index)
            for vertex in parallel[index]:
                for other in owners[key(vertex)]:
                    if other not in seen:
                        seen.add(other)
                        stack.append(other)
        if len(group) < min_facets:
            continue

        points = {key(v) for i in group for v in parallel[i]}
        if len(points) < 4:
            continue
        fit = _fit_circle(sorted(points))
        if fit is None or fit[2] < 1e-3 or fit[3] > tol * max(fit[2], 1.0):
            continue
        cx, cy, radius, _ = fit

        angles = sorted(math.atan2(y - cy, x - cx) for x, y in points)
        gaps = [angles[i + 1] - angles[i] for i in range(len(angles) - 1)]
        gaps.append(angles[0] + 2 * math.pi - angles[-1])
        sweep = math.degrees(2 * math.pi - max(gaps))

        along = [v[axis] for i in group for v in parallel[i]]
        normal, _ = _normal_area(parallel[group[0]])
        first = parallel[group[0]][0]
        inward = (normal[u_axis] * (cx - first[u_axis])
                  + normal[v_axis] * (cy - first[v_axis])) > 0
        found.append((cx, cy, radius, min(along), max(along), sweep, inward))
    return sorted(found, key=lambda c: (-c[2], c[0], c[1]))


# --------------------------------------------------------------------------- #
# report                                                                       #
# --------------------------------------------------------------------------- #

def analyse(path, verbose=True, max_layers=40, axis=None, bores=True):
    tris = read_stl(path)
    lo, hi = bbox(tris)
    vol = volume(tris)
    scores = [prismatic_score(tris, k) for k in range(3)]
    if axis is None:
        axis = max(range(3), key=lambda k: scores[k])

    print(f"{path}")
    print(f"  {len(tris)} facets, volume {vol:.3f} mm^3")
    print(f"  bbox X[{lo[0]:.3f},{hi[0]:.3f}] "
          f"Y[{lo[1]:.3f},{hi[1]:.3f}] Z[{lo[2]:.3f},{hi[2]:.3f}]")
    print(f"  size {hi[0]-lo[0]:.3f} x {hi[1]-lo[1]:.3f} x {hi[2]-lo[2]:.3f}")
    print("  prismatic score  " + "  ".join(
        f"{AXES[k]}={scores[k]:.4f}" for k in range(3))
        + f"   -> build along {AXES[axis].upper()}")
    if not verbose:
        return

    if bores:
        for k in range(3):
            u_axis, v_axis = [j for j in range(3) if j != k]
            round_faces = cylinders(tris, k)
            if not round_faces:
                continue
            print(f"  round faces about {AXES[k].upper()} "
                  f"({AXES[u_axis]}, {AXES[v_axis]}, extent along {AXES[k]}):")
            for cx, cy, radius, c0, c1, sweep, inward in round_faces:
                kind = "bore" if inward else "boss"
                print(f"    {kind} centre ({cx:8.3f},{cy:8.3f}) "
                      f"d {radius*2:7.3f} r {radius:7.3f} "
                      f"{AXES[k]} [{c0:8.3f},{c1:8.3f}] sweep {sweep:5.1f}")

    steps = levels(tris, axis)
    print(f"  {len(steps)} step(s) along {AXES[axis].upper()}:")
    for height, step_area in steps:
        print(f"    {height:9.3f}  facing area {step_area:9.2f}")

    heights = [h for h, _ in steps]
    for i in range(len(heights) - 1):
        if i >= max_layers:
            print("    ...")
            break
        mid = (heights[i] + heights[i + 1]) / 2.0
        loops = section(tris, axis, mid)
        print(f"  layer {heights[i]:.3f} -> {heights[i+1]:.3f} "
              f"(thickness {heights[i+1]-heights[i]:.3f}), "
              f"{len(loops)} loop(s):")
        for loop in sorted(loops, key=lambda l: -abs(area(l))):
            kind = "outer" if area(loop) > 0 else "hole "
            print(f"    {kind} area {abs(area(loop)):9.3f}")
            for item in features(loop):
                if item[0] == "line":
                    (x0, y0), (x1, y1) = item[1], item[2]
                    print(f"      line ({x0:8.3f},{y0:8.3f}) -> "
                          f"({x1:8.3f},{y1:8.3f})")
                else:
                    _, (cx, cy), radius, _, _, sweep = item
                    print(f"      arc  centre ({cx:8.3f},{cy:8.3f}) "
                          f"r {radius:7.3f} d {radius*2:7.3f} "
                          f"sweep {math.degrees(sweep):7.1f} deg")


def main(argv):
    paths = [a for a in argv if not a.startswith("-")]
    verbose = "--summary" not in argv
    axis = None
    for name in AXES:
        if f"--axis={name}" in argv:
            axis = AXES.index(name)
    for path in paths:
        analyse(path, verbose=verbose, axis=axis,
                bores="--no-bores" not in argv)
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
