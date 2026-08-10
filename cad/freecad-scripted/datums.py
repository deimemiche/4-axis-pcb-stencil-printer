"""Step 2 of ASSEMBLY_SCRIPT.md: where every joint's datum would have to go.

**Read-only.**  Opens an assembly, asks FreeCAD where each joint's coordinate
system actually sits, expresses it in the part's own local frame, deduplicates,
and prints the `fcprim.lcs()` calls that would put a datum there.

    ASM_OUT=<path.json> flatpak run --command=freecadcmd --filesystem=home \
        org.freecad.FreeCAD datums.py <One_Assembly.FCStd>

One document per process, and the output path via the environment, for the two
reasons `extract.py` documents.

**The placement is FreeCAD's, not ours.**  `UtilsAssembly.findPlacement(ref)`
returns the joint coordinate system the Assembly solver itself uses for that
reference, in the coordinates of the part the reference lands on -- which is the
frame `fcprim.lcs` writes in.  Deriving it here instead (axis of a cylinder,
centre of a circle, normal of a plane) would be a second opinion about what the
joint means, and a second opinion is exactly what must not creep in: the whole
point is that a datum lands where the joint already is.

`roll` is recovered the way `fcprim.lcs` composes it -- `swing * Rotation(Z,
roll)`, where `swing` turns +Z onto `axis` -- so a proposed call reproduces the
placement it was measured from.
"""

import json
import math
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ASSEMBLIES = os.path.normpath(os.path.join(HERE, "..", "freecad", "assembly"))
TOL = 4          # decimal places position is rounded to when deduplicating
ATOL = 6         # ... and direction


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def decompose(App, plc):
    """A placement as fcprim.lcs would spell it: at, axis, roll."""
    from FreeCAD import Rotation, Vector
    axis = plc.Rotation.multVec(Vector(0, 0, 1))
    swing = Rotation(Vector(0, 0, 1), axis)
    residual = swing.inverted().multiply(plc.Rotation)
    roll = math.degrees(residual.Angle)
    if residual.Axis.z < 0:
        roll = -roll
    roll = (roll + 360.0) % 360.0
    return (
        [round(v, 9) for v in (plc.Base.x, plc.Base.y, plc.Base.z)],
        [round(v, 9) for v in (axis.x, axis.y, axis.z)],
        round(roll, 6),
    )


def leaf(link, sub):
    """The part document at the end of a reference, and the shape it names.

    A reference from a container assembly reads
    `Bottom_Frame001.BOT_Z_AXIS_BRACKET.Edge52` -- a path through the child
    links FreeCAD materialised, ending at a part.  The datum belongs on that
    part, not on the sub-assembly the path starts in, so the chain is walked to
    the end rather than stopping at the first hop.
    """
    obj = link.LinkedObject if link.TypeId in (
        "App::Link", "Assembly::AssemblyLink") else link
    try:
        tail = link.getSubObject(sub, retType=1)
    except Exception:
        tail = None
    if tail is not None:
        while tail.TypeId in ("App::Link", "Assembly::AssemblyLink") and \
                tail.LinkedObject is not None:
            tail = tail.LinkedObject
        obj = tail
    try:
        shp = link.getSubObject(sub)
        # A sub-element FreeCAD could not map comes back as a *null* shape
        # rather than None -- the four `?Edge39`-style references do this --
        # and asking a null shape its type raises.
        if shp is not None and shp.isNull():
            shp = None
    except Exception:
        shp = None
    return obj, shp


def body_sub(body, sub):
    """The sub-element, resolved from inside the part it belongs to.

    Deriving the frame from the body keeps it in the part's own coordinates,
    which is where `fcprim.lcs` writes.  Composing a global frame back down
    through `getSubObject(..., retType=3)` looks equivalent and is not: that
    returns something other than the owner's global placement, and using it
    puts most fasteners tens of millimetres out.
    """
    if body is None:
        return None
    parts = sub.split(".")
    for i in range(len(parts)):
        try:
            shp = body.getSubObject(".".join(parts[i:]))
        except Exception:
            continue
        if shp is not None and not shp.isNull():
            return shp
    return None


def circle_frame(App, shape):
    """A circular edge's own frame: its centre, with +Z down its axis."""
    from FreeCAD import Placement, Rotation, Vector
    if shape is None or shape.isNull() or shape.ShapeType != "Edge":
        return None
    curve = shape.Curve
    if not hasattr(curve, "Center") or not hasattr(curve, "Axis"):
        return None
    return Placement(curve.Center,
                     Rotation(Vector(0, 0, 1), curve.Axis))


def collect(App, path):
    sys.path.append("/app/share/freecad/Mod/Assembly")
    import UtilsAssembly as U

    doc = App.openDocument(path)
    rows, failed = [], []

    # Fasteners attach through BaseObject, always to a circular edge -- the
    # Fasteners workbench reads the hole's diameter and plane off it.  A datum
    # has no such edge, so a scripted fastener is placed by a joint onto a
    # datum instead, and that datum has to go where the hole is.  Same
    # measurement, same frame, so they are collected together.
    for f in doc.Objects:
        if "BaseObject" not in f.PropertiesList or f.BaseObject is None:
            continue
        link, subs = f.BaseObject
        if link is None or not subs:
            continue
        sub = subs[0]
        body, shape = leaf(link, sub)
        part = body.Document.Name if body is not None else None

        # NOT findPlacement.  That is built for joint references, which carry
        # two subs; a fastener's BaseObject carries one, and findPlacement
        # quietly returns the identity -- which put every fastener datum at the
        # part origin.  A fastener always attaches to a circular edge, so the
        # frame is the circle's own: centre, with Z down the axis.
        #
        # A reference reads `BOT_RAIL_HOLDER001.Pocket002.Edge66` through the
        # links but `Pocket002.Edge66` from inside the part, and how many
        # leading components to drop varies.  Rather than guess, try each
        # suffix and keep the first the body actually resolves.
        gframe = circle_frame(App, link.getSubObject(sub))
        frame = circle_frame(App, body_sub(body, sub))
        if frame is None:
            failed.append({"assembly": doc.Name, "joint": f.Name,
                           "prop": "BaseObject", "part": part, "sub": sub,
                           "error": "no circular edge to take a frame from"})
            continue
        at, axis, roll = decompose(App, frame)

        # Where the screw sits relative to that hole.  A fastener's Placement is
        # not its attachment frame: the workbench puts the head at one end,
        # flips it for Invert and adds Offset.  Measured in the hole's own
        # coordinates so the builder can re-apply it to the datum.
        # Stored as a distance ALONG the hole axis, not as a full placement.
        #
        # `Rotation(Z, axis)` is a shortest-arc rotation, and it is not
        # preserved by a transform: the frame taken globally and the datum
        # written into the part differ by a roll about the axis.  A full offset
        # expressed in one frame is then wrong in the other, unless it happens
        # to be purely on-axis.  A distance along the axis has no such problem,
        # and a bolt sitting in its own hole has no off-axis offset anyway --
        # so `perp` is kept too, as the check that the frame really is the
        # hole the fastener uses.
        # Measured along the DATUM's own axis, not the globally-resolved
        # edge's.  The same edge reached through the links and from inside the
        # body can come back with opposite orientation, and a circle's Axis
        # follows that -- so `along` measured one way and applied the other
        # slides the screw backwards, out by exactly twice the offset.  The
        # owner transform comes from retType=2's matrix, which is the
        # accumulated placement; retType=3 is not it.
        along = perp = None
        owner = None
        try:
            got = link.getSubObject(sub, retType=2)
            if isinstance(got, tuple) and len(got) > 1:
                owner = App.Placement(got[1])
        except Exception:
            owner = None
        if frame is not None and owner is not None:
            zaxis = owner.Rotation.multVec(
                frame.Rotation.multVec(App.Vector(0, 0, 1)))
            origin = owner.multVec(frame.Base)
            delta = f.Placement.Base.sub(origin)
            along = round(delta.dot(zaxis), 9)
            perp = round(delta.sub(zaxis.multiply(along)).Length, 9)

        kind = shape.ShapeType if shape is not None else None
        geom = (type(shape.Curve).__name__ if kind == "Edge" else
                type(shape.Surface).__name__ if kind == "Face" else kind)
        rows.append({"assembly": doc.Name, "joint": f.Name,
                     "joint_label": f.Label, "joint_type": "Fastener",
                     "prop": "BaseObject", "part": part, "sub": sub,
                     "kind": kind, "geom": geom, "at": at, "axis": axis,
                     "roll": roll, "along": along, "perp": perp,
                     "via_link": link.Name,
                     "fastener": str(getattr(f, "Type", "?")),
                     "diameter": str(getattr(f, "Diameter", "?"))})

    for j in doc.Objects:
        if "Reference1" not in j.PropertiesList:
            continue
        jtype = str(getattr(j, "JointType", "?"))
        for prop in ("Reference1", "Reference2"):
            ref = getattr(j, prop, None)
            if not ref or ref[0] is None or not ref[1]:
                continue
            link, subs = ref
            sub = subs[0]
            body, shape = leaf(link, sub)
            part = body.Document.Name if body is not None else None
            try:
                plc = U.findPlacement(ref)
                at, axis, roll = decompose(App, plc)
            except Exception as e:
                failed.append({"assembly": doc.Name, "joint": j.Name,
                               "prop": prop, "part": part, "sub": sub,
                               "error": f"{type(e).__name__}: {e}"})
                continue
            kind = shape.ShapeType if shape is not None else None
            geom = (type(shape.Curve).__name__ if kind == "Edge" else
                    type(shape.Surface).__name__ if kind == "Face" else kind)
            rows.append({"assembly": doc.Name, "joint": j.Name,
                         "joint_label": j.Label, "joint_type": jtype,
                         "prop": prop, "part": part, "sub": sub,
                         "kind": kind, "geom": geom,
                         "at": at, "axis": axis, "roll": roll})

    App.closeDocument(doc.Name)
    return {"rows": rows, "failed": failed}


def main():
    import FreeCAD as App

    out = os.environ.get("ASM_OUT") or os.path.join(HERE, "datums.json")
    only = [a for a in sys.argv[1:] if a.endswith(".FCStd")]
    files = ([a if os.path.isabs(a) else os.path.join(ASSEMBLIES, a) for a in only]
             or sorted(os.path.join(ASSEMBLIES, n)
                       for n in os.listdir(ASSEMBLIES) if n.endswith(".FCStd")))

    result = {"rows": [], "failed": []}
    for f in files:
        got = collect(App, f)
        result["rows"] += got["rows"]
        result["failed"] += got["failed"]

    with open(out, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    say(f"{os.path.basename(files[0]) if len(files) == 1 else 'all'}: "
        f"{len(result['rows'])} references, {len(result['failed'])} failed")
    for f in result["failed"][:10]:
        say(f"   FAILED {f['joint']}.{f['prop']} {f['part']}/{f['sub']}: {f['error']}")


try:
    main()
except Exception:
    say("DATUMS RAISED:")
    say(traceback.format_exc())
    sys.exit(1)
