"""Count what the machine is made of, by walking the assembly that holds it.

    freecadcmd bom.py                      # the whole machine
    freecadcmd bom.py Rotation_Table       # one sub-assembly

Writes `data/bom.json` and `../../BOM.md`.

Counted from the built assembly rather than from a list somebody keeps up to
date, which is the only way a bill of materials stays true.  Every part is
already sorted into printed, machined, bought and bolted by
[`categories.py`](categories.py) -- the same call `asmbuild.py` groups them
with -- so this only has to walk and add up.

## Multiplicity is the whole difficulty

`Bottom_Assembly` links four `Eccenter`s, and an `Eccenter` is eight parts and
eight bolts.  Counting the nine documents separately would say there is one
eccenter; counting instances without recursing would say there are four
sub-assemblies and no parts.  So the walk starts at
`4-Axis_Stencil_Printer.FCStd` and goes down through every
`Assembly::AssemblyLink`, and a part deep in a sub-assembly linked four times
is counted four times.

## Norm parts say what they are

Michael asked that the bought fasteners resolve to the fastener actually
chosen, and they can: each one carries the `Type`, `Diameter` and `Length` the
Fasteners workbench built it from, so `ISO4762` + `M4` + `10` becomes
`ISO 4762 M4x10`.  That is read off the object, never off its label -- the
labels are FreeCAD's own `M4x10-Screw049` and drift as things are added.
"""

import json
import os
import sys
import traceback
from collections import defaultdict

import FreeCAD as App

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from categories import GROUPS, category   # noqa: E402

ASM = os.path.join(HERE, "assembly")
DATA = os.path.join(HERE, "data")
BOM_MD = os.path.normpath(os.path.join(HERE, "..", "..", "BOM.md"))
TOP = "4-Axis_Stencil_Printer"

# What a fastener standard is called on a drawing, rather than in FreeCAD's
# property.  Anything not here is printed as-is rather than guessed at.
STANDARD = {
    "ISO4762": "ISO 4762 socket head cap screw",
    "ISO4032": "ISO 4032 hex nut",
    "ISO4035": "ISO 4035 thin hex nut",
    "ISO7089": "ISO 7089 plain washer",
    "ISO7090": "ISO 7090 plain washer, chamfered",
    "ISO7380-1": "ISO 7380-1 button head screw",
    "ISO10642": "ISO 10642 countersunk screw",
    "ISO7045": "ISO 7045 pan head screw",
    "ISO2009": "ISO 2009 countersunk slotted screw",
    "ISO4026": "ISO 4026 set screw, flat point",
    "ISO4027": "ISO 4027 set screw, cone point",
    "ISO4028": "ISO 4028 set screw, dog point",
    "ISO4029": "ISO 4029 set screw, cup point",
    "ISO4017": "ISO 4017 hex head screw, full thread",
    "ISO4014": "ISO 4014 hex head screw",
    "DIN934": "DIN 934 hex nut",
    "DIN7991": "DIN 7991 countersunk socket screw",
    "DIN912": "DIN 912 socket head cap screw",
    # Not a fastener standard at all: the Fasteners workbench's brass heat-set
    # insert, which the machine uses eight of.  It is bought like a norm part
    # and belongs in the same table, so it is named rather than left as a
    # workbench identifier nobody can order from.
    "IUTHeatInsert": "Heat-set threaded insert, brass",
}


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def designation(obj):
    """What to order, for one fastener.

    `Length` is blank on a nut or a washer, which is why it is appended only
    when there is one rather than formatted in unconditionally.
    """
    kind = str(getattr(obj, "Type", "") or "?")
    size = str(getattr(obj, "Diameter", "") or "?")
    length = str(getattr(obj, "Length", "") or "").strip()
    name = STANDARD.get(kind, kind)
    return f"{name} {size}x{length}" if length else f"{name} {size}"


def part_name(link):
    """The part a link points at, by its document rather than its label.

    A link's label is per instance -- `BOT_BRACKETS004` -- and what wants
    counting is the part, which is the document it came from.
    """
    target = getattr(link, "LinkedObject", None)
    if target is None:
        return link.Label
    source = getattr(target.Document, "FileName", "") or ""
    return os.path.basename(source)[:-6] if source else target.Document.Name


def walk(App, doc, count, times=1, seen=None, depth=0, visits=None):
    """Add everything in `doc`'s assembly to `count`, `times` over.

    `seen` guards against a cycle; there are none in this machine, but a
    recursive walk that trusts that is a recursive walk that hangs one day.
    `visits` records how many times each document was reached, which is what
    `shortfall` needs to know how many of a missing bolt are missing.
    """
    seen = seen or set()
    if visits is not None:
        visits[doc.Name] = visits.get(doc.Name, 0) + times
    asm = next((o for o in doc.Objects
                if o.TypeId == "Assembly::AssemblyObject"), None)
    if asm is None:
        return
    for obj in asm.Group:
        kind = category(obj)
        if kind == "Assemblies":
            target = getattr(obj, "LinkedObject", None)
            if target is None:
                continue
            key = (doc.Name, obj.Name)
            if key in seen:
                continue
            walk(App, target.Document, count, times, seen | {key}, depth + 1,
                 visits)
        elif kind == "Norm_parts":
            count[kind][designation(obj)] += times
        elif kind:
            count[kind][part_name(obj)] += times


def shortfall(visits):
    """How many fasteners the build failed to place, counted with multiplicity.

    A bill of materials that quietly leaves parts out is worse than none, and
    this one is counted off the built assembly, so anything the build did not
    place is silently absent from it.  `data/model.json` says how many
    fasteners each document should have; the assembly says how many it got.
    The difference, times the number of times that document is used, is what
    is missing from the tables below.
    """
    path = os.path.join(DATA, "model.json")
    if not os.path.exists(path):
        return None
    model = json.load(open(path))
    missing, detail = 0, []
    for name, spec in model.items():
        used = visits.get(spec.get("document", name), 0) or visits.get(name, 0)
        if not used:
            continue
        want = len(spec.get("fasteners", []))
        doc = App.getDocument(spec.get("document", name))
        got = sum(1 for o in doc.Objects if o.TypeId == "Part::FeaturePython")
        if got < want:
            missing += (want - got) * used
            detail.append(f"{name}: {want - got} of {want}"
                          + (f", used {used} times" if used > 1 else ""))
    return missing, detail


def markdown(count, name, gap=None):
    total = sum(sum(v.values()) for v in count.values())
    out = [f"# Bill of materials -- {name.replace('_', ' ')}", "",
           "Counted by walking the built assembly, not kept by hand: see",
           "[`cad/freecad-scripted/bom.py`](cad/freecad-scripted/bom.py).",
           "A part inside a sub-assembly that is linked four times is counted",
           "four times, so these are the numbers to order.", "",
           f"**{total} pieces in all.**", ""]
    if gap and gap[0]:
        # `>` on the blank lines too, or Markdown ends the quote and starts
        # a new one at each gap, and the warning comes out as three fragments.
        out += [f"> **Incomplete: {gap[0]} fastener(s) are missing from the "
                "counts below.**",
                ">",
                "> They are counted off the built assembly, and the build did "
                "not place these:", ">"]
        out += [f"> * {d}" for d in gap[1]]
        out += [">", "> Every other line is exact; see `verify` in "
                "`rebuild.py`.", ""]
    titles = {"Printed_parts": "Printed parts",
              "CNC_parts": "Machined parts (aluminium)",
              "COTS": "Bought parts",
              "Norm_parts": "Fasteners"}
    for group in ("Printed_parts", "CNC_parts", "COTS", "Norm_parts"):
        rows = count.get(group) or {}
        if not rows:
            continue
        pieces = sum(rows.values())
        out += [f"## {titles[group]}", "",
                f"{len(rows)} distinct, {pieces} pieces.", "",
                "| Qty | Part |", "|---:|:---|"]
        for part, n in sorted(rows.items(), key=lambda kv: (-kv[1], kv[0])):
            out.append(f"| {n} | {part} |")
        out.append("")
    drawn = count.get("CNC_parts") or {}
    if drawn:
        out += ["Every machined part has a drawing in",
                "[`technical-drawings/`](technical-drawings/), with a PDF, a",
                "DXF and a CSV of its hole positions.", ""]
    return "\n".join(out)


def main(argv):
    name = next((a for a in argv if not a.endswith(".py")), TOP)
    path = os.path.join(ASM, name + ".FCStd")
    if not os.path.exists(path):
        say(f"no such assembly: {path}")
        return 1

    count = {g: defaultdict(int) for g in GROUPS}
    visits = {}
    doc = App.openDocument(path)
    walk(App, doc, count, visits=visits)
    gap = shortfall(visits)

    plain = {g: dict(v) for g, v in count.items() if v}
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "bom.json"), "w") as fh:
        json.dump({"assembly": name, "groups": plain,
                   "fasteners_missing": (gap or [0])[0]}, fh,
                  indent=1, sort_keys=True)
    with open(BOM_MD, "w") as fh:
        fh.write(markdown(count, name, gap) + "\n")

    total = 0
    for group in GROUPS:
        rows = count[group]
        if not rows:
            continue
        pieces = sum(rows.values())
        total += pieces
        say(f"  {group:15} {len(rows):4} distinct {pieces:5} pieces")
    say(f"  {'TOTAL':15} {'':4}          {total:5} pieces")
    if gap and gap[0]:
        say(f"  !! {gap[0]} fastener(s) missing, the build did not place them:")
        for d in gap[1]:
            say(f"       {d}")
    say(f"\n  -> data/bom.json and {os.path.relpath(BOM_MD, HERE)}")
    return 0


STATUS = 1
try:
    STATUS = main(sys.argv[1:])
except BaseException:
    say("BOM RAISED:")
    say(traceback.format_exc())
finally:
    os._exit(STATUS)
