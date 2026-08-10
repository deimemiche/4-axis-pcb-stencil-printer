"""Step 4 of ASSEMBLY_SCRIPT.md: build the nine assemblies from the model.

    ASM_MODEL=model.json ASM_WIRING=wiring.json \
    flatpak run --command=freecadcmd --filesystem=home \
        org.freecad.FreeCAD asmbuild.py [Document_Name ...]

Writes into `asm/`, under Michael's own names and nesting.  It never opens
anything in `../freecad/`; the parts it links are this tree's, the ones carrying
the datums `fcprim.apply_datums` put on them.

**Every joint names a datum.**  Where the hand-built assembly said
`Pocket001.Edge34`, this says `LCS007.` -- the internal name of the datum
labelled `LEVER2`.  `wiring.json` is the bridge, and `wiring.py` built it by
matching each measured attachment frame to the datum the plan put there.

**Fasteners are placed from their datum too.**  The Fasteners workbench reads a
hole's diameter and plane off a circular edge, which a datum does not have, so a
scripted fastener cannot use `BaseObject`.  It gets the datum's own global
placement instead: same frame, same result, and nothing addressed by edge number.

Order matters.  A document must exist and be saved before anything can XLink to
it, and a sub-assembly must be built before the container that links it, so the
build runs leaves first.
"""

import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "asm")

# Leaves first: a container can only link a sub-assembly that already exists.
ORDER = ["Bottom_Frame", "Eccenter", "Rotation_Table", "X-Axis_Carriage",
         "Stencil_Clamp", "Top_Frame", "Bottom_Assembly", "Top_Assembly",
         "4-Axis_Stencil_Printer"]

# document name as FreeCAD mangles it -> the file it lives in
FILE_OF = {"X_Axis_Carriage": "X-Axis_Carriage",
           "_4_Axis_Stencil_Printer": "4-Axis_Stencil_Printer"}


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def part_files():
    """Every part document this tree builds, by document name."""
    import glob
    out = {}
    for f in glob.glob(os.path.join(HERE, "*", "*.FCStd")):
        base = os.path.basename(f)[:-6]
        out[base] = f
        if base[0].isdigit():
            out["_" + base] = f          # FreeCAD mangles a leading digit
    return out


def open_part(App, path, cache):
    if path in cache:
        return cache[path]
    doc = App.openDocument(path)
    cache[path] = doc
    return doc


def linkable(doc):
    """What a link should point at: the assembly if there is one, else the body."""
    for o in doc.Objects:
        if o.TypeId == "Assembly::AssemblyObject":
            return o
    for o in doc.Objects:
        if o.TypeId == "PartDesign::Body":
            return o
    return None


def datum_of(doc, internal_name):
    for o in doc.Objects:
        if o.Name == internal_name:
            return o
    return None


def build(App, name, model, wiring, files, cache):
    sys.path.append("/app/share/freecad/Mod/Assembly")
    import JointObject
    import UtilsAssembly

    spec = model[name]
    path = os.path.join(OUT, spec["file"])
    doc = App.newDocument(name)
    doc.saveAs(path)                      # an XLink needs a saved owner
    asm = doc.addObject("Assembly::AssemblyObject", "Assembly")

    # ---- part and sub-assembly instances -------------------------------
    links, notes = {}, []
    for inst in spec["instances"]:
        src = inst["document"]
        f = files.get(src) or files.get(src.lstrip("_"))
        if f is None:
            f = os.path.join(OUT, FILE_OF.get(src, src) + ".FCStd")
        if not os.path.exists(f):
            notes.append(f"no file for {src}")
            continue
        pdoc = open_part(App, f, cache)
        target = linkable(pdoc)
        if target is None:
            notes.append(f"nothing linkable in {src}")
            continue
        kind = ("Assembly::AssemblyLink"
                if target.TypeId == "Assembly::AssemblyObject" else "App::Link")
        link = asm.newObject(kind, inst["name"])
        link.LinkedObject = target
        link.Label = inst["label"]
        # A plausible start pose, so the solver cannot converge into the wrong
        # branch -- the lid folded through the frame rather than above it.
        link.Placement = App.Placement(
            App.Vector(*inst["placement"][:3]),
            App.Rotation(*inst["placement"][3:]))
        links[inst["name"]] = link

    doc.recompute()

    # ---- grounded ------------------------------------------------------
    for g in spec["grounded"]:
        target = links.get(g["object"])
        if target is None:
            notes.append(f"grounded joint {g['name']}: no link {g['object']}")
            continue
        gj = asm.newObject("App::FeaturePython", "GroundedJoint")
        JointObject.GroundedJoint(gj, target)
        gj.Label = g["label"]

    # ---- joints --------------------------------------------------------
    jg = UtilsAssembly.getJointGroup(asm)
    made = 0
    for j in spec["joints"]:
        # Keyed on the FreeCAD document name, not the file stem: the two
        # differ wherever a name has a hyphen or a leading digit
        # (X-Axis_Carriage opens as X_Axis_Carriage).
        wire = wiring["joints"].get(f"{spec['document']}/{j['name']}")
        if wire is None or len(wire) != 2:
            notes.append(f"joint {j['name']}: not wired")
            continue
        ends = []
        for prop in ("Reference1", "Reference2"):
            w = wire[prop]
            via = j[{"Reference1": "ref1", "Reference2": "ref2"}[prop]]["via"]
            link = links.get(via)
            if link is None:
                ends = None
                notes.append(f"joint {j['name']}.{prop}: no link {via}")
                break
            ends.append((link, w.get("prefix", "") + w["object"]))
        if not ends:
            continue
        o = jg.newObject("App::FeaturePython", "Joint")
        JointObject.Joint(o, JointObject.JointTypes.index(j["JointType"]))
        o.Label = j["label"]
        # Two subs, not one.  The Assembly workbench stores every reference as
        # (element, vertex) -- the second disambiguates which end of an edge a
        # placement snaps to -- and a one-element list makes its own validation
        # raise `list index out of range`.  A datum has no ends, so it is
        # simply named twice, exactly as the hand-built file does for its
        # spring: ['LCS002.', 'LCS002.'].
        o.Reference1 = (ends[0][0], [ends[0][1] + "."] * 2)
        o.Reference2 = (ends[1][0], [ends[1][1] + "."] * 2)
        for prop in ("Distance", "Distance2", "Angle", "Offset", "Rotation"):
            if prop in j and prop in o.PropertiesList:
                try:
                    setattr(o, prop, float(j[prop].split()[0]))
                except (ValueError, AttributeError):
                    pass
        made += 1

    doc.recompute()
    doc.save()
    return doc, made, notes


def main():
    import FreeCAD as App

    model = json.load(open(os.environ["ASM_MODEL"]))
    wiring = json.load(open(os.environ["ASM_WIRING"]))
    files = part_files()
    cache = {}
    os.makedirs(OUT, exist_ok=True)

    want = [a for a in sys.argv[1:] if not a.endswith(".py")]
    todo = [n for n in ORDER
            if not want or n in want or n.replace("-", "_") in want]
    # model keys are the file stems
    todo = [n for n in todo if n in model]

    say(f"\n{'document':26} {'links':>6} {'joints':>7} {'ground':>7} {'notes':>6}")
    for name in todo:
        doc, made, notes = build(App, name, model, wiring, files, cache)
        n_links = sum(1 for o in doc.Objects
                      if o.TypeId in ("App::Link", "Assembly::AssemblyLink"))
        say(f"{name:26} {len(model[name]['instances']):6} {made:7} "
            f"{len(model[name]['grounded']):7} {len(notes):6}")
        for t in notes[:6]:
            say(f"   ! {t}")


try:
    main()
except Exception:
    say("BUILD RAISED:")
    say(traceback.format_exc())
    sys.exit(1)
