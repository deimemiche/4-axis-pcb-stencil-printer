"""Step 1 of ASSEMBLY.md Part II: the nine hand-built assemblies to a neutral model.

**Read-only.**  Opens each document, records what is authored in it, and closes
it without saving.  Nothing here writes to `../freecad/`.

    flatpak run --command=freecadcmd --filesystem=home \
        ASM_OUT=<path.json> org.freecad.FreeCAD extract.py [One_Assembly.FCStd]

**One document per process.**  Opening all nine in one session and closing each
before the next makes FreeCAD fail to restore links between them -- `Top_Assembly`
loses every link into `Stencil_Clamp.FCStd` that way, because the document it
points at was opened and closed earlier in the same session.  Run it once per
assembly and merge, which is what `extract-all.sh` does.

The point is to separate what Michael authored from what FreeCAD materialised.
A container document looks enormous -- `4-Axis_Stencil_Printer` holds 542
objects -- but almost all of that is a sub-assembly's contents mirrored upward,
created by the `Assembly::AssemblyLink` rather than by anyone.  The test used
here is membership of the `Assembly::AssemblyObject`'s own `Group`: what is in
it was put there, and what is not was materialised.  The
`App::DocumentObjectGroup`s inside are UI folders whose members are already in
`Group` directly, so they are walked but never double-counted.

freecadcmd swallows tracebacks, so everything runs inside a `try` that prints
its own.
"""

import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the tree root
ASSEMBLIES = os.path.normpath(os.path.join(HERE, "..", "freecad", "assembly"))

LINK_TYPES = ("App::Link", "Assembly::AssemblyLink")
FASTENER_PROPS = ("Type", "Diameter", "Thread", "Length", "Invert", "Offset",
                  "OffsetAngle", "MatchOuter", "LeftHanded")
JOINT_PROPS = ("JointType", "Distance", "Distance2", "Angle", "Activated",
               "Offset", "Rotation")


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def placement(p):
    return [round(v, 9) for v in
            (p.Base.x, p.Base.y, p.Base.z,
             p.Rotation.Q[0], p.Rotation.Q[1], p.Rotation.Q[2], p.Rotation.Q[3])]


def reference(ref, here):
    """A joint or fastener reference, with the target named by document."""
    if ref is None:
        return None
    obj, subs = (ref if isinstance(ref, tuple) else (ref, []))
    if obj is None:
        return None
    target = obj.LinkedObject if obj.TypeId in LINK_TYPES else obj
    doc = target.Document if target is not None else None
    return {
        "via": obj.Name,
        "via_label": obj.Label,
        "document": doc.Name if doc else None,
        "file": (os.path.relpath(doc.FileName, here)
                 if doc and doc.FileName else None),
        "subs": list(subs),
    }


def members(group, seen=None):
    """Everything in an Assembly's Group, walking UI folders, without repeats."""
    seen = seen if seen is not None else set()
    out = []
    for o in group:
        if o.Name in seen:
            continue
        seen.add(o.Name)
        out.append(o)
        if o.TypeId == "App::DocumentObjectGroup":
            out += members(o.Group, seen)
    return out


def extract(App, path):
    doc = App.openDocument(path)
    here = os.path.dirname(path)
    asms = [o for o in doc.Objects if o.TypeId == "Assembly::AssemblyObject"]
    if len(asms) != 1:
        raise RuntimeError(f"{doc.Name}: expected 1 AssemblyObject, got {len(asms)}")
    asm = asms[0]

    authored = members(asm.Group)
    authored_names = {o.Name for o in authored}

    instances, fasteners, joints, grounded, unknown = [], [], [], [], []

    for o in authored:
        if o.TypeId in LINK_TYPES:
            linked = o.LinkedObject
            ldoc = linked.Document if linked else None
            instances.append({
                "name": o.Name,
                "label": o.Label,
                "type": o.TypeId,
                "is_subassembly": o.TypeId == "Assembly::AssemblyLink",
                "document": ldoc.Name if ldoc else None,
                "file": (os.path.relpath(ldoc.FileName, here)
                         if ldoc and ldoc.FileName else None),
                "linked_object": linked.Name if linked else None,
                "placement": placement(o.Placement),
            })
        elif "BaseObject" in o.PropertiesList:
            rec = {"name": o.Name, "label": o.Label, "type_id": o.TypeId,
                   "base": reference(o.BaseObject, here)}
            for p in FASTENER_PROPS:
                if p in o.PropertiesList:
                    rec[p] = str(getattr(o, p))
            fasteners.append(rec)
        elif "Reference1" in o.PropertiesList:
            rec = {"name": o.Name, "label": o.Label,
                   "ref1": reference(o.Reference1, here),
                   "ref2": reference(o.Reference2, here)}
            for p in JOINT_PROPS:
                if p in o.PropertiesList:
                    rec[p] = str(getattr(o, p))
            joints.append(rec)
        elif "ObjectToGround" in o.PropertiesList:
            g = o.ObjectToGround
            grounded.append({"name": o.Name, "label": o.Label,
                             "object": g.Name if g else None,
                             "object_label": g.Label if g else None,
                             "placement": placement(o.Placement)
                             if "Placement" in o.PropertiesList else None})
        elif o.TypeId in ("Assembly::JointGroup", "App::DocumentObjectGroup"):
            pass
        else:
            unknown.append({"name": o.Name, "type_id": o.TypeId,
                            "label": o.Label})

    result = {
        "document": doc.Name,
        "file": os.path.basename(path),
        "objects_total": len(doc.Objects),
        "authored_total": len(authored_names),
        "instances": instances,
        "fasteners": fasteners,
        "joints": joints,
        "grounded": grounded,
        "unknown": unknown,
    }
    App.closeDocument(doc.Name)
    return result


def main():
    import FreeCAD as App

    # The output path comes through the environment, not argv: freecadcmd
    # treats any argument containing ".json" as a file to import and dies in
    # the FEM mesh reader, after this script has already finished.
    out = os.environ.get("ASM_OUT") or os.path.join(HERE, "extracted.json")

    only = [a for a in sys.argv[1:] if a.endswith(".FCStd")]
    if only:
        files = [a if os.path.isabs(a) else os.path.join(ASSEMBLIES, a)
                 for a in only]
    else:
        files = sorted(os.path.join(ASSEMBLIES, n)
                       for n in os.listdir(ASSEMBLIES) if n.endswith(".FCStd"))
    if not files:
        raise RuntimeError(f"no assemblies under {ASSEMBLIES}")
    if len(files) > 1:
        say("WARNING: more than one document in one process; links between them"
            " may fail to restore.  Prefer extract-all.sh.")

    model = {}
    for f in files:
        model[os.path.basename(f)[:-6]] = extract(App, f)

    unresolved = [(n, i["name"]) for n, d in model.items()
                  for i in d["instances"] if i["document"] is None]
    if unresolved:
        say(f"\nUNRESOLVED LINKS: {len(unresolved)}")
        for n, i in unresolved[:10]:
            say(f"   {n}: {i}")

    with open(out, "w") as fh:
        json.dump(model, fh, indent=1, sort_keys=True)

    say(f"\n{'document':26} {'objects':>8} {'authored':>9} {'parts':>6} "
        f"{'subasm':>7} {'joints':>7} {'ground':>7} {'fasten':>7}")
    tot = [0] * 7
    for name, d in model.items():
        subs = sum(1 for i in d["instances"] if i["is_subassembly"])
        row = [d["objects_total"], d["authored_total"],
               len(d["instances"]) - subs, subs, len(d["joints"]),
               len(d["grounded"]), len(d["fasteners"])]
        tot = [a + b for a, b in zip(tot, row)]
        say(f"{name:26} {row[0]:8} {row[1]:9} {row[2]:6} {row[3]:7} "
            f"{row[4]:7} {row[5]:7} {row[6]:7}")
    say(f"{'TOTAL':26} {tot[0]:8} {tot[1]:9} {tot[2]:6} {tot[3]:7} "
        f"{tot[4]:7} {tot[5]:7} {tot[6]:7}")

    strays = {n: d["unknown"] for n, d in model.items() if d["unknown"]}
    say(f"\nauthored objects of a kind this script does not model: "
        f"{sum(len(v) for v in strays.values())}")
    for n, v in strays.items():
        say(f"   {n}: {[(x['name'], x['type_id']) for x in v]}")

    say("\n--- the sub-assembly tree, from authored links only ---")
    for name in sorted(model):
        kids = sorted(str(i["document"]) for i in model[name]["instances"]
                      if i["is_subassembly"])
        say(f"   {name:26} {kids if kids else '(parts only)'}")

    say(f"\nwritten to {out}")


try:
    main()
except Exception:
    say("EXTRACT RAISED:")
    say(traceback.format_exc())
    sys.exit(1)
