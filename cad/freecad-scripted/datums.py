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


def collect(App, path):
    sys.path.append("/app/share/freecad/Mod/Assembly")
    import UtilsAssembly as U

    doc = App.openDocument(path)
    rows, failed = [], []

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
            body = link.LinkedObject
            part = body.Document.Name if body is not None else None
            try:
                plc = U.findPlacement(ref)
                at, axis, roll = decompose(App, plc)
            except Exception as e:
                failed.append({"assembly": doc.Name, "joint": j.Name,
                               "prop": prop, "part": part, "sub": sub,
                               "error": f"{type(e).__name__}: {e}"})
                continue
            try:
                shp = body.getSubObject(sub)
                kind = shp.ShapeType if shp is not None else None
                geom = (type(shp.Surface).__name__ if kind == "Face" else
                        type(shp.Curve).__name__ if kind == "Edge" else kind)
            except Exception:
                kind, geom = None, None
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
