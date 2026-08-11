"""Step 4 of ASSEMBLY_SCRIPT.md: build the nine assemblies from the model.

    ASM_MODEL=model.json ASM_WIRING=wiring.json \
    flatpak run --command=freecadcmd --filesystem=home \
        org.freecad.FreeCAD asmbuild.py [Document_Name ...]

Writes into `assembly/`, under Michael's own names and nesting.  It never opens
anything in `../freecad/`; the parts it links are this tree's, the ones carrying
the datums `fcprim.apply_datums` put on them.

**Every joint names a datum.**  Where the hand-built assembly said
`Pocket001.Edge34`, this says `LCS007.` -- the internal name of the datum
labelled `LEVER2`.  `wiring.json` is the bridge, and `wiring.py` built it by
matching each measured attachment frame to the datum the plan put there.

**Fasteners are not built yet.**  The Fasteners workbench reads a hole's
diameter and plane off a circular edge, which a datum does not have, so a
scripted fastener cannot use `BaseObject` and must be placed from its datum
instead.  The datum is in the right place -- the joints built on the same datums
reproduce the machine exactly -- but the transform from an attachment frame to a
fastener's own `Placement` is not yet right, and only 25 of 245 land correctly.
`ASM_FASTENERS=1` builds them anyway.  See `place_fasteners`.

Order matters.  A document must exist and be saved before anything can XLink to
it, and a sub-assembly must be built before the container that links it, so the
build runs leaves first.
"""

import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from categories import GROUPS, category  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assembly")

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


FRAMES = {} if os.environ.get("ASM_FRAMES") else None


def fastener_class(App):
    """The Fasteners workbench proxy class, loaded the only way that works.

    `import FastenersCmd` segfaults under freecadcmd.  The module loads safely
    only when FreeCAD restores it while opening a document that holds a
    fastener, so `assembly/FASTENER_SEED.FCStd` exists to be that document.  See
    `fastener-seed.py`.
    """
    seed = os.path.join(OUT, "FASTENER_SEED.FCStd")
    if not os.path.exists(seed):
        return None
    doc = App.openDocument(seed)
    got = [o for o in doc.Objects if "BaseObject" in o.PropertiesList]
    cls = type(got[0].Proxy) if got else None
    App.closeDocument(doc.Name)
    return cls


def _only_instance(link, part):
    """The one child of `link` that is an instance of the part `part`.

    The prefix `wiring.json` records is a chain of *hand-built* link names, and
    the builder does not always mint the same ones: `Bottom_Frame` holds a
    single X-axis bracket, which the hand document called
    `BOT_BRACKET_X_AXIS001` and the build calls `BOT_BRACKET_X_AXIS`.  The path
    then resolves to nothing and the nut in that bracket is never placed.

    Where the sub-assembly holds exactly **one** instance of the part, there is
    no ambiguity about which link was meant, whatever it is called.  Where it
    holds more than one there is, and this hands back nothing rather than
    guessing.
    """
    found = []
    for child in getattr(link, "getSubObjects", lambda: ())():
        try:
            obj = link.getSubObject(child, retType=1)
        except Exception:
            continue
        tail = obj
        while tail is not None and tail.TypeId in (
                "App::Link", "Assembly::AssemblyLink"):
            tail = tail.LinkedObject
        if tail is not None and tail.TypeId == "PartDesign::Body" \
                and tail.Label == part:
            found.append(child)
    return found[0] if len(found) == 1 else None


def datum_sub(link, prefix, label, name, part=None):
    """Where a datum is *now*, addressed by what the part script called it.

    `wiring.json` records a path made of names read out of the **hand-built**
    documents -- a chain of link names and then the datum's own internal object
    name, `BOT_BRACKET_X_AXIS001.LCS008.`.  Both halves of that are fragile.
    An internal name depends on the order objects were created in, and the
    builder does not always mint the same link names the hand document had: a
    sub-assembly holding one X-axis bracket calls it `BOT_BRACKET_X_AXIS` where
    the hand document called it `BOT_BRACKET_X_AXIS001`, so the path resolves
    to nothing and the nut in that bracket is never placed.

    What does not move is the **label**: `BOLT4` is what the part script wrote,
    and nothing downstream renames it.  So this walks the path and asks the
    part which of its datums is called `label`, falling back to the recorded
    name only when it cannot.  Where the prefix itself is the part that will
    not resolve, `_only_instance` finds the link by what it is an instance of.
    """
    owner, used = link, prefix
    if prefix:
        try:
            owner = link.getSubObject(prefix, retType=1)
        except Exception:
            owner = None
        if owner is None and part:
            found = _only_instance(link, part)
            if found:
                used = found
                try:
                    owner = link.getSubObject(found, retType=1)
                except Exception:
                    owner = None
    if owner is None or not label:
        return used + name + "."
    while owner.TypeId in ("App::Link", "Assembly::AssemblyLink"):
        if owner.LinkedObject is None:
            return used + name + "."
        owner = owner.LinkedObject
    group = getattr(owner, "Group", None) or getattr(owner, "OutList", ())
    for o in group:
        if o.TypeId == "PartDesign::CoordinateSystem" and o.Label == label:
            return used + o.Name + "."
    return used + name + "."


def place_fasteners(App, doc, asm, spec, wiring, links, fcls, notes,
                    offsets, frames=None):
    """Every fastener, put where its datum is.

    A fastener cannot use `BaseObject` here: the Fasteners workbench reads a
    hole's diameter and plane off a circular edge, and a datum has no edge.  It
    gets the datum's own global placement instead -- the same frame the hole
    would have given, addressed by name rather than by number.

    This runs after the solve, because a link's placement is an output: the
    datum is only in the right place once the joints have put its part there.
    """
    made = 0
    for f in spec["fasteners"]:
        w = wiring["fasteners"].get(f"{spec['document']}/{f['name']}")
        if w is None:
            notes.append(f"fastener {f['name']}: not wired")
            continue
        # Which link the datum is reached through is the wiring's to say, not
        # the model's.  `base.via` is whatever the hand-built document's
        # `BaseObject` pointed at, and that is only a link when the base was a
        # part.  `Nut031` is based on the *nut in front of it* -- it is a jam
        # nut -- so its `via` is `Nut030`, which is a fastener and no link at
        # all.  The wiring knows the datum lives in a part and which link
        # reaches it.  For the other 244 the two agree exactly, so this only
        # ever changes the ones the model could not answer for.
        via = w.get("via_link") or f["base"]["via"]
        link = links.get(via)
        if link is None:
            notes.append(f"fastener {f['name']}: no link {via}")
            continue
        sub = datum_sub(link, w.get("prefix", ""), w.get("datum"),
                        w["object"], w.get("part"))
        try:
            datum = link.getSubObject(sub, retType=1)
        except Exception as e:
            notes.append(f"fastener {f['name']}: {sub} -> {e}")
            continue
        if datum is None:
            notes.append(f"fastener {f['name']}: {sub} resolved to nothing")
            continue
        o = doc.addObject("Part::FeaturePython", f["name"])
        fcls(o, f.get("Type", "ISO4762"), None)
        o.Label = f["label"]
        for prop in ("Type", "Diameter", "Length", "Thread", "Invert",
                     "OffsetAngle", "MatchOuter", "LeftHanded"):
            if prop in f and prop in o.PropertiesList:
                try:
                    setattr(o, prop, f[prop])
                except Exception:
                    pass
        asm.addObject(o)
        # The datum, plus the offset calibrated in this very frame.  See
        # calibrate.py: measuring the offset from the hand-built assembly's own
        # geometry meant composing two different resolutions of one edge, and
        # OCC orients those inconsistently.  Measured here, there is nothing to
        # compose.
        frame = link.getSubObject(sub, retType=3)
        # Record the frame this build actually used.  `calibrate.py` measures in
        # a saved, reopened document, and for a container that is not the same
        # frame -- a sub-assembly's links are still settling while it is being
        # assembled.  Calibrating against what the build itself saw closes that
        # gap; see calibrate-from-build.py.
        if frames is not None:
            frames[f"{spec['document']}/{f['name']}"] = [
                frame.Base.x, frame.Base.y, frame.Base.z,
                frame.Rotation.Q[0], frame.Rotation.Q[1],
                frame.Rotation.Q[2], frame.Rotation.Q[3]]
        off = offsets.get(f"{spec['document']}/{f['name']}")
        if off:
            frame = frame.multiply(App.Placement(
                App.Vector(*off["offset"][:3]),
                App.Rotation(*off["offset"][3:])))
        o.Placement = frame
        made += 1
    return made


def group_parts(doc, asm):
    """Sort what the assembly holds into groups, the way the hand-built ones are.

    Organisational only -- nothing here moves a part or touches a joint.  The
    groups hang under the assembly container, and a part stays a member of the
    container as well as of its group, which is how the hand-built documents
    have it and what keeps the solver seeing every instance.

    `Group` is assigned rather than `addObject`ed for that reason: a group that
    claims its members would take them out of the assembly.
    """
    sorted_out = {name: [] for name in GROUPS}
    for obj in asm.Group:
        kind = category(obj)
        if kind:
            sorted_out[kind].append(obj)

    made = {}
    for name in GROUPS:
        members = sorted_out[name]
        if not members:
            continue                       # no empty groups in the tree
        grp = doc.addObject("App::DocumentObjectGroup", name)
        grp.Label = name
        # Into the assembly *first*.  An assembly is a geo-feature group, and a
        # plain group standing outside it may not hold anything that lives
        # inside one -- FreeCAD says the links "go out of the allowed scope"
        # and drops them.  Once the group is itself a child of the assembly the
        # two are in the same scope and the members are accepted.
        asm.addObject(grp)
        grp.Group = members
        made[name] = len(members)
    return made


def check_assembly(asm, doc):
    """The DOF check, run on every build.

    Two things, both of which bit the hand-built assembly.  `solve()` returns
    non-zero when the solver cannot converge.  And anything still touched after
    a recompute is what an over-constraint looks like from outside: both
    `Top_Assembly` and `4-Axis_Stencil_Printer` were over-constrained by exactly
    one `Parallel` where an `Angle` would do, and that is how it showed.

    `isPartConnected` is deliberately NOT used.  It reports almost every part in
    a working assembly as unreached -- including ones whose solved placement is
    exact to 1e-6 -- so it does not mean what its name suggests, and a check
    that cries wolf on a good build is worse than no check.
    """
    out = []
    try:
        rc = asm.solve()
        if rc != 0:
            out.append(f"solver did not converge (rc={rc})")
    except Exception as e:
        out.append(f"solve() raised: {type(e).__name__}: {e}")
    doc.recompute()
    touched = [o.Label for o in doc.Objects if o.State and "Touched" in o.State]
    if touched:
        out.append(f"still touched after recompute: {', '.join(touched[:6])}")
    return out


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

    # OFF by default.  The joints and the parts are verified exact; the
    # fasteners are NOT -- only 25 of 245 land where the hand-built assembly
    # puts them.  The attachment frame is measured correctly (the datums are
    # right, and the joints built on them reproduce the machine), but the
    # transform from that frame to a fastener's own Placement is still wrong:
    # `getSubObject(edge, retType=3)` does not return the part-global frame
    # this assumed, so the measured offset is composed from the wrong basis.
    # Set ASM_FASTENERS=1 to build them anyway and work on it.
    # Fasteners are OFF by default.  The joints and the parts are verified
    # exact; the fasteners are NOT -- only 25 of 245 land where the hand-built
    # assembly puts them.  The datums are in the right place (the joints built
    # on them reproduce the machine), but the transform from an attachment
    # frame to a fastener's own Placement is still wrong: getSubObject(edge,
    # retType=3) does not return the part-global frame this assumed, so the
    # measured offset is composed from the wrong basis.
    # ASM_FASTENERS=1 builds them anyway, to work on it.
    fastened = 0
    if os.environ.get("ASM_FASTENERS"):
        fcls = fastener_class(App)
        if fcls is None:
            notes.append("no FASTENER_SEED.FCStd -- run fastener-seed.py")
        else:
            offsets = {}
            cal = os.environ.get("ASM_OFFSETS")
            if cal and os.path.exists(cal):
                offsets = json.load(open(cal))
            fastened = place_fasteners(App, doc, asm, spec, wiring, links,
                                       fcls, notes, offsets, FRAMES)

    doc.recompute()
    grouped = group_parts(doc, asm)
    doc.recompute()
    notes += check_assembly(asm, doc)
    doc.save()
    return doc, made, fastened, notes, grouped


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

    say(f"\n{'document':26} {'links':>6} {'joints':>7} {'ground':>7} "
        f"{'bolts':>7} {'notes':>6}  groups")
    for name in todo:
        doc, made, fastened, notes, grouped = build(App, name, model, wiring,
                                                    files, cache)
        shown = " ".join(f"{k.split('_')[0]}:{v}" for k, v in grouped.items())
        say(f"{name:26} {len(model[name]['instances']):6} {made:7} "
            f"{len(model[name]['grounded']):7} {fastened:7} {len(notes):6}  "
            f"{shown}")
        for t in notes[:6]:
            say(f"   ! {t}")

    if FRAMES is not None:
        with open(os.environ["ASM_FRAMES"], "w") as fh:
            json.dump(FRAMES, fh, indent=1, sort_keys=True)
        say(f"\n{len(FRAMES)} build-time datum frames written to "
            f"{os.environ['ASM_FRAMES']}")


try:
    main()
except Exception:
    say("BUILD RAISED:")
    say(traceback.format_exc())
    sys.exit(1)
