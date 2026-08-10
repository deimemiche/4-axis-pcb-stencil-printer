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
        body, shape = leaf(link, subs[0])
        part = body.Document.Name if body is not None else None
        try:
            plc = U.findPlacement(f.BaseObject)
            at, axis, roll = decompose(App, plc)
        except Exception as e:
            failed.append({"assembly": doc.Name, "joint": f.Name,
                           "prop": "BaseObject", "part": part, "sub": subs[0],
                           "error": f"{type(e).__name__}: {e}"})
            continue
        kind = shape.ShapeType if shape is not None else None
        geom = (type(shape.Surface).__name__ if kind == "Face" else
                type(shape.Curve).__name__ if kind == "Edge" else kind)
        # Where the screw sits relative to the frame it attaches to.
        #
        # A fastener's Placement is NOT its attachment frame: the workbench puts
        # the head at one end, flips it for `Invert`, and adds `Offset`.  Give a
        # fastener the datum's own placement and every bolt lands tens of
        # millimetres out.  So the difference is measured here, in the
        # attachment frame's coordinates, and the builder re-applies it -- a
        # number taken from the assembly, like every other number in this file.
        # Relative to the DATUM's frame, not the owner's.  getSubObject(...,
        # retType=3) returns the owning object's placement; the datum sits at
        # `plc` inside it, and the builder will resolve the datum itself, whose
        # retType=3 already includes that.  Leaving it out here double-counts
        # and every bolt lands out by the datum's own offset.
        local = None
        try:
            owner = link.getSubObject(subs[0], retType=3)
            lp = owner.multiply(plc).inverse().multiply(f.Placement)
            local = [round(v, 9) for v in
                     (lp.Base.x, lp.Base.y, lp.Base.z,
                      lp.Rotation.Q[0], lp.Rotation.Q[1],
                      lp.Rotation.Q[2], lp.Rotation.Q[3])]
        except Exception:
            pass
        rows.append({"assembly": doc.Name, "joint": f.Name,
                     "joint_label": f.Label, "joint_type": "Fastener",
                     "prop": "BaseObject", "part": part, "sub": subs[0],
                     "kind": kind, "geom": geom, "at": at, "axis": axis,
                     "roll": roll, "local": local,
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
