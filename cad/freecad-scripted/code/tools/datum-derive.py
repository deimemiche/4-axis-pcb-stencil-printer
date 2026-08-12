"""Step 6 of ASSEMBLY.md Part II: say what each measured datum is *made of*.

**Read-only.**  `datum-plan.json` holds 308 datum positions as literals, because
that is what a measurement off the hand-built assembly gives.  This asks the
built part which of its own sketched features sits at each of those literals, so
the number in the plan can be replaced, in the part script, by the expression
that already draws that feature.

    DERIVE_OUT=<path.json> flatpak run --command=freecadcmd --filesystem=home \
        org.freecad.FreeCAD datum-derive.py [NAME ...]

With no names every document in the plan is looked at.  One document per
process is *not* required here -- nothing is written and no XLink is resolved --
but the output path still goes through the environment, because freecadcmd
prints its own banner onto stdout.

**What counts as a derivation.**  A datum is explained when a feature the part
script drew is at exactly the same place:

* `centre`   the centre of a sketched circle or arc, in the body's coordinates
* `axis`     a point on such a circle's axis, `d` mm along the sketch normal
* `vertex`   an endpoint of a sketched line
* `plane`    on a sketch's own plane, with the datum's Z along that normal
* `coords`   nothing whole matched, but each coordinate equals a dimension the
             sketches carry -- reported per axis, as a last resort

Only the first four are derivations.  `coords` is a hint for a human, and a
datum that reaches it is one the part script has to say something new about.

Geometry is named the way `fcprim` names it: `circle(..., name="bolt_a0")`
renames that circle's two locating constraints `bolt_a0_u` and `bolt_a0_v`, and
`polyline(..., name="plate")` names its dimensions `plate_x0`, `plate_y3`.  So
the constraint names give every matched feature the name the *script* knows it
by, which is the whole point -- `bolt_a0` can be found in the source, `Edge52`
cannot.
"""

import json
import math
import os
import re
import sys
import traceback

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the tree root
PLAN = os.path.join(HERE, "data", "datum-plan.json")
TOL = 1e-6          # a match is exact: both numbers came out of the same build
DIM = 1e-6          # ... and so does a coordinate matching a dimension


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def find_doc(name):
    """The built .FCStd for a document name, wherever its group put it.

    The plan is keyed by `doc.Name`, and FreeCAD will not let an internal name
    begin with a digit -- so the extrusions are `_2020_300` in the plan and
    `2020_300.FCStd` on disk.
    """
    for group in sorted(os.listdir(HERE)):
        for stem in (name, name.lstrip("_")):
            path = os.path.join(HERE, group, stem + ".FCStd")
            if os.path.isfile(path):
                return path
    return None


def geometry_names(sk):
    """Sketch geometry index -> the name the part script gave it.

    `fcprim` renames the constraints it adds after the geometry they hold, so
    the name is recoverable from any named constraint that refers to the
    element.  The trailing `_u`, `_v`, `_x3`, `_r0` is the role, not the name.
    """
    names = {}
    for c in sk.Constraints:
        if not c.Name:
            continue
        base = re.sub(r"_(u|v|half\d+|[xyr]\d+)$", "", c.Name)
        for geo in (c.First, c.Second, c.Third):
            if geo is not None and geo >= 0:
                names.setdefault(geo, base)
    return names


def dimensions(sk):
    """Every named dimension in a sketch: name -> value."""
    return {c.Name: c.Value for c in sk.Constraints
            if c.Name and c.Type in ("DistanceX", "DistanceY", "Distance",
                                     "Radius", "Diameter")}


def features(doc):
    """Every sketched circle, arc and line endpoint, in body coordinates.

    A sketch's own `Placement` already carries the origin plane it is mapped to
    and whatever `AttachmentOffset` the script asked for, so multiplying by it
    is exactly the trip from the numbers in the script to the numbers in the
    plan.
    """
    from FreeCAD import Vector
    circles, vertices, planes, dims = [], [], [], {}
    for sk in doc.Objects:
        if sk.TypeId != "Sketcher::SketchObject":
            continue
        plc = sk.Placement
        normal = plc.Rotation.multVec(Vector(0, 0, 1))
        names = geometry_names(sk)
        for name, value in dimensions(sk).items():
            dims.setdefault(round(value, 9), []).append(f"{sk.Label}:{name}")
        planes.append((sk.Label, plc.Base, normal))
        for i, g in enumerate(sk.Geometry):
            if getattr(sk, "getConstruction", None) and sk.getConstruction(i):
                continue
            kind = type(g).__name__
            name = names.get(i, f"geo{i}")
            if kind in ("Circle", "ArcOfCircle"):
                circles.append((sk.Label, name, plc.multVec(g.Center), normal,
                                g.Radius))
            elif kind == "LineSegment":
                vertices.append((sk.Label, name, plc.multVec(g.StartPoint)))
                vertices.append((sk.Label, name, plc.multVec(g.EndPoint)))
    return circles, vertices, planes, dims


def near(a, b):
    return abs(a - b) < TOL


def same(v, at):
    return all(near(c, p) for c, p in zip((v.x, v.y, v.z), at))


def explain(datum, circles, vertices, planes, dims):
    """How the part's own geometry accounts for this datum's position."""
    from FreeCAD import Vector
    at = datum["at"]
    axis = Vector(*datum["axis"])
    point = Vector(*at)

    for label, name, centre, normal, radius in circles:
        if same(centre, at):
            return {"how": "centre", "sketch": label, "geo": name,
                    "radius": round(radius, 6),
                    "along": round(abs(normal.dot(axis)), 6)}

    best = None
    for label, name, centre, normal, radius in circles:
        delta = point - centre
        d = delta.dot(normal)
        if (delta - normal * d).Length < TOL:
            cand = {"how": "axis", "sketch": label, "geo": name,
                    "radius": round(radius, 6), "offset": round(d, 9),
                    "along": round(abs(normal.dot(axis)), 6)}
            if best is None or abs(d) < abs(best["offset"]):
                best = cand
    if best is not None:
        return best

    for label, name, vertex in vertices:
        if same(vertex, at):
            return {"how": "vertex", "sketch": label, "geo": name}

    for label, base, normal in planes:
        if abs((point - base).dot(normal)) < TOL and \
                abs(abs(normal.dot(axis)) - 1.0) < 1e-6:
            return {"how": "plane", "sketch": label,
                    "offset": round((point - base).dot(normal), 9)}

    per = {}
    for name, value in zip("xyz", at):
        if abs(value) < DIM:
            per[name] = ["zero"]
            continue
        hits = dims.get(round(abs(value), 9), [])
        half = dims.get(round(abs(value) * 2, 9), [])
        per[name] = ([f"{'-' if value < 0 else ''}{h}" for h in hits[:3]] +
                     [f"half of {h}" for h in half[:2]]) or []
    return {"how": "coords", "per": per}


def main():
    plan = json.load(open(PLAN))
    wanted = [a for a in sys.argv[1:] if not a.endswith(".py")]
    names = [n for n in sorted(plan) if not wanted or n in wanted]

    import FreeCAD as App

    out, tally = {}, {}
    for name in names:
        path = find_doc(name)
        if path is None:
            say(f"  !! {name}: no built document")
            continue
        doc = App.openDocument(path)
        try:
            circles, vertices, planes, dims = features(doc)
            rows = []
            for d in plan[name]:
                got = explain(d, circles, vertices, planes, dims)
                got["name"] = d["name"]
                got["at"] = d["at"]
                got["axis"] = d["axis"]
                got["roll"] = d.get("roll", 0.0)
                got["fixed"] = d.get("fixed", False)
                got["why"] = d.get("why", "")
                rows.append(got)
                tally[got["how"]] = tally.get(got["how"], 0) + 1
            out[name] = rows
            done = sum(1 for r in rows if r["how"] != "coords")
            say(f"  {name:34s} {done}/{len(rows)} derived")
        finally:
            App.closeDocument(doc.Name)

    say("")
    for how in ("centre", "axis", "vertex", "plane", "coords"):
        if how in tally:
            say(f"  {how:8s} {tally[how]}")

    where = os.environ.get("DERIVE_OUT")
    if where:
        with open(where, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        say(f"\nwritten to {where}")


try:
    main()
except BaseException:
    say(traceback.format_exc())
