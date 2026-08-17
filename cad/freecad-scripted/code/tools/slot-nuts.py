"""Where every slot nut goes -- the `Nutenstein` behind each M4 in a profile.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \
        code/tools/slot-nuts.py [4-Axis_Stencil_Printer] [--write]

Nothing in either tree models the slot nuts: the M4s that hold the machine's
brackets to its extrusions are drawn threading into thin air.  This finds them
instead of listing them, by asking each bolt where it goes, and writes
`data/slot-nuts.json` -- a nut per bolt, with the frame to place it at.

## How a nut is found

Two tests, and a bolt has to pass both.

1. **Its axis enters a slot.**  Take the bolt's own solved frame, put it in the
   stick's coordinates, and cross it with the four slot faces.  A hit counts
   when the bolt runs square into the face (within a degree), crosses the plane
   of the channel floor inside the 6 mm mouth, and does it somewhere along the
   stick rather than past its end.  This alone finds 120 of the machine's 128
   M4 cap screws; the eight it passes over are the eccentrics', which bolt
   printed part to printed part.

2. **What it clamps is unbroken.**  A bolt into a slot nut pulls a part down
   ONTO the profile, so between its head and the profile's face there is
   nothing but that part -- solid all the way, bar the bolt's own clearance
   hole.  Sampled on a ring 4 mm off the axis, outside the widest counterbore
   in the machine, so a counterbored head does not read as a gap.

The second test is what the two `PINCH_BOLT`s of `BOT_Z_AXIS_BRACKET` fail.
They point squarely into the frame's outer slot and their tips would reach it,
but they stand 13.4 mm off it, holding nothing against it: they cross the
bracket's saw cut to pull its collar shut on the Z rod.  Every real one clamps
1.5 to 6 mm of part with no gap in it (`solid` = 1.00 exactly); those two clamp
13.4 mm with 1.1 mm of air in the middle (`solid` = 0.92).  The margin is the
whole gap, not a tolerance, which is why this is a test rather than a list of
names to skip.

## Where the nut itself sits

On the slot's own centre line -- a nut is captive there, it cannot be anywhere
else -- at the bolt's position along the stick, with its top face against the
channel floor 2 mm inside the profile.  So the bolt gives one coordinate, the
section gives the other two, and `across` (how far the bolt misses the centre
line by) is a check rather than a placement: it should be zero, and where it is
not, the bolt cannot thread a captive nut.

Sixteen of them are not zero.  See `report`.
"""
import json
import math
import os
import sys
import traceback

import FreeCAD as App
from FreeCAD import Placement, Rotation, Vector

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASM = os.path.join(HERE, "assembly")
DATA = os.path.join(HERE, "data")

# The section, from `stock/2020-extrusion.py`.  Kept as numbers rather than
# imported because that script runs inside FreeCAD and builds documents as a
# side effect of being imported.
HALF = 10.0             # half the 20 mm cell
MOUTH = 6.0             # the gap a nut drops through
WALL = 2.0              # and the wall it goes through, to the channel floor
CHANNEL = 11.0          # the widest the channel gets, behind that wall
CORE = 8.0              # across the boss the centre bore is drilled through

# The nut: slot 6, M4, the common hammer-nut size.  Only `height` places
# anything -- the rest is here so the fit can be checked against the section.
NUT_H = 3.0             # how tall, which is how deep into the channel it sits
NUT_W = 5.8             # across the mouth
NUT_L = 10.0            # along the stick

LENGTHS = {"2020_300": 300.0, "2020_280": 280.0, "2020_300_TOP_FRONT": 300.0}
FACES = (("XP", Vector(1, 0, 0)), ("XN", Vector(-1, 0, 0)),
         ("YP", Vector(0, 1, 0)), ("YN", Vector(0, -1, 0)))

RING = 4.0              # where the stack is sampled, off the bolt's axis
STEP = 0.5              # and how finely
SQUARE = 0.99           # how square to the face a bolt has to run


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def part_doc_name(link):
    """The part a link points at, by its document rather than its label."""
    target = getattr(link, "LinkedObject", None)
    if target is None:
        return None
    src = getattr(target.Document, "FileName", "") or ""
    return os.path.basename(src)[:-6] if src else target.Document.Name


def assembly_of(doc):
    for o in doc.Objects:
        if o.TypeId == "Assembly::AssemblyObject":
            return o
    return None


def walk(asm, where, path, parts, bolts, seen):
    """Every part and every fastener in the machine, in machine coordinates.

    `getGlobalPlacement` is no use here: a bolt three documents down is not an
    object of the document this opened, so its global frame has to be composed
    on the way down.  `seen` guards a cycle that does not exist yet.
    """
    for obj in asm.Group:
        if obj.TypeId == "App::DocumentObjectGroup":
            continue
        if obj.TypeId == "Assembly::AssemblyLink":
            target = getattr(obj, "LinkedObject", None)
            if target is None:
                continue
            key = (asm.Document.Name, obj.Name)
            if key in seen:
                continue
            sub = assembly_of(target.Document)
            if sub is None:
                continue
            walk(sub, where.multiply(obj.Placement), path + "/" + obj.Label,
                 parts, bolts, seen | {key})
        elif obj.TypeId == "App::Link":
            parts.append((path + "/" + obj.Label, part_doc_name(obj), obj,
                          where.multiply(obj.Placement)))
        elif obj.TypeId == "Part::FeaturePython":
            bolts.append((path, obj, where.multiply(obj.Placement)))


def shaft(obj):
    """Which way the bolt's own Z runs into the work.

    Read off the shape, in the shape's own frame: `obj.Shape.BoundBox` is the
    placed one, and taking the sign from that points half the machine's bolts
    outwards.
    """
    sh = obj.Shape.copy()
    sh.Placement = Placement()
    bb = sh.BoundBox
    return -1.0 if abs(bb.ZMin) > abs(bb.ZMax) else 1.0


def enters(base, d, length):
    """The first slot this axis enters, in one stick's own coordinates."""
    best = None
    for face, n in FACES:
        if d.dot(n) > -SQUARE:               # must run INTO the face, square
            continue
        t = (HALF - WALL - base.dot(n)) / d.dot(n)
        if t < -1.0:                         # behind the head
            continue
        p = base + d * t
        across = p.x if abs(n.y) > 0.5 else p.y
        if abs(across) > MOUTH / 2.0 + 1.5:  # outside the mouth
            continue
        if not (-2.0 <= p.z <= length + 2.0):
            continue
        if best is None or t < best[1]:
            best = (face, t, p, across, n)
    return best


def solidity(shapes, spath, spl, p_local, n, stack):
    """How much of the clamped stack is material, at its most generous.

    Eight lines parallel to the bolt and `RING` off it, from just under the
    head to just short of the profile's face.  The best of the eight, because a
    bolt at the edge of a flange legitimately has air on one side of it; what
    is being asked is whether there is a continuous part there at all.
    """
    u = Vector(0, 0, 1)
    v = n.cross(u)
    best, held = 0.0, set()
    for i in range(8):
        a = i * math.pi / 4.0
        off = u * (RING * math.cos(a)) + v * (RING * math.sin(a))
        solid = total = 0
        s = 0.3
        while s < stack - 0.2:
            q = spl.multVec(p_local + n * (WALL + (stack - s)) + off)
            total += 1
            for opath, oname, sh, bb in shapes:
                if opath == spath or not bb.isInside(q):
                    continue
                try:
                    if sh.isInside(q, 1e-6, True):
                        solid += 1
                        held.add(oname)
                        break
                except Exception:
                    pass
            s += STEP
        if total:
            best = max(best, solid / float(total))
    return best, sorted(held)


def nut_frame(spl, p_local, n, z):
    """Where the nut goes: on the slot's centre line, against the floor.

    Its own Z points out of the slot, the way the bolt comes in, and its X runs
    along the stick, which is the way it is slid or turned in.
    """
    centre = n * (HALF - WALL - NUT_H / 2.0) + Vector(0, 0, z)
    axis_z = n
    axis_x = Vector(0, 0, 1)
    rot = Rotation(axis_x, axis_x.cross(axis_z), axis_z)
    return spl.multiply(Placement(centre, rot))


def find(doc):
    parts, bolts = [], []
    walk(assembly_of(doc), Placement(), "", parts, bolts, set())
    sticks = [(p, n, o, pl) for p, n, o, pl in parts if n in LENGTHS]

    shapes = []
    for path, name, obj, pl in parts:
        try:
            sh = obj.LinkedObject.Shape.copy()
            sh.Placement = pl.multiply(sh.Placement)
            shapes.append((path, name, sh, sh.BoundBox))
        except Exception:
            pass

    nuts, rejected = [], []
    for path, obj, gp in bolts:
        kind = str(getattr(obj, "Type", ""))
        if "4762" not in kind and "912" not in kind:
            continue
        if str(getattr(obj, "Diameter", "")) != "M4":
            continue
        d = gp.Rotation.multVec(Vector(0, 0, shaft(obj)))
        got = []
        for spath, sname, _, spl in sticks:
            inv = spl.inverse()
            h = enters(inv.multVec(gp.Base), inv.Rotation.multVec(d),
                       LENGTHS[sname])
            if h and h[1] < 30.0:
                got.append((spath, sname, spl, h))
        if not got:
            continue
        got.sort(key=lambda g: g[3][1])
        spath, sname, spl, (face, t, p_local, across, n) = got[0]
        stack = t - WALL
        length = float(str(getattr(obj, "Length", "0")).split()[0] or 0)
        solid, held = solidity(shapes, spath, spl, p_local, n, stack)
        frame = nut_frame(spl, p_local, n, p_local.z)
        row = {"bolt": obj.Label, "in": path, "bolt_length": length,
               "holds": held,
               "stick": sname, "stick_at": spath, "face": face,
               "z": round(p_local.z, 3), "across": round(across, 3),
               "stack": round(stack, 3), "solid": round(solid, 3),
               "engagement": round(length - t, 3),
               "at": [round(v, 4) for v in tuple(frame.Base)],
               "rot": [round(v, 6) for v in frame.Rotation.Q]}
        if solid < 0.999:
            row["why"] = (f"the {stack:.2f} mm it clamps is not solid "
                          f"({solid:.2f}) -- it holds nothing against the slot")
            rejected.append(row)
        else:
            nuts.append(row)
    return nuts, rejected


def report(nuts, rejected):
    from collections import defaultdict
    say(f"\n{len(nuts)} slot nuts, {len(rejected)} bolts rejected\n")

    per = defaultdict(int)
    for r in nuts:
        per[(r["in"], r["stick"])] += 1
    say("  where they are")
    for k in sorted(per):
        say(f"    {k[0][-30:]:30} {k[1]:20} {per[k]:4}")

    say("\n  what they hold down")
    holds = defaultdict(int)
    for r in nuts:
        holds[", ".join(r["holds"]) or "?"] += 1
    for k in sorted(holds, key=lambda k: -holds[k]):
        say(f"    {holds[k]:4}  {k}")

    say("\n  what the bolts are")
    kinds = defaultdict(int)
    for r in nuts:
        kinds[(r["bolt_length"], r["stack"])] += 1
    for k in sorted(kinds):
        say(f"    M4x{k[0]:.0f} clamping {k[1]:5.2f} mm : {kinds[k]:4}")

    off = [r for r in nuts if abs(r["across"]) > 0.05]
    say(f"\n  {len(off)} bolts miss the slot's centre line, so no captive nut "
        "can take them:")
    seen = defaultdict(list)
    for r in off:
        seen[round(abs(r["across"]), 3)].append(r["bolt"])
    for k in sorted(seen, reverse=True):
        say(f"    {k:5.2f} mm  x{len(seen[k])}")

    deep = [r for r in nuts if r["engagement"] > HALF - WALL - CORE / 2.0]
    say(f"\n  {len(deep)} bolts reach deeper than the channel is (over "
        f"{HALF - WALL - CORE / 2.0:.1f} mm past the floor)")

    say("\n  how the nuts sit in each slot")
    slots = defaultdict(list)
    for r in nuts:
        slots[(r["stick_at"], r["face"])].append(r["z"])
    tightest = None
    for k in sorted(slots):
        zs = sorted(slots[k])
        gap = min((b - a for a, b in zip(zs, zs[1:])), default=None)
        if gap is not None and (tightest is None or gap < tightest[0]):
            tightest = (gap, k)
        say(f"    {k[0][-40:]:40} {k[1]} n={len(zs):2}"
            + (f"  closest {gap:6.2f}" if gap is not None else ""))
    if tightest:
        say(f"    tightest pair anywhere: {tightest[0]:.2f} mm, against a nut "
            f"{NUT_L:.0f} mm long")

    if rejected:
        say("\n  rejected")
        for r in rejected:
            say(f"    {r['bolt']:18} {r['in'][-28:]:28} {r['stick']:16} "
                f"{r['face']} z={r['z']:7.2f}  {r['why']}")

    say(f"\n  the nut against the section: {NUT_W} wide in a {MOUTH} mouth, "
        f"{NUT_L} long in an {CHANNEL} channel,")
    say(f"  {NUT_H} tall in the {HALF - WALL - CORE / 2.0:.0f} mm between the "
        "channel floor and the boss")


def main(argv):
    name = next((a for a in argv if not a.startswith("-")
                 and not a.endswith(".py")), "4-Axis_Stencil_Printer")
    path = os.path.join(ASM, name + ".FCStd")
    if not os.path.exists(path):
        say(f"no such assembly: {path}")
        return 1
    nuts, rejected = find(App.openDocument(path))
    report(nuts, rejected)
    if "--write" in argv:
        out = os.path.join(DATA, "slot-nuts.json")
        with open(out, "w") as fh:
            json.dump({"assembly": name, "nut": {"height": NUT_H,
                                                 "width": NUT_W,
                                                 "length": NUT_L},
                       "nuts": nuts, "rejected": rejected}, fh,
                      indent=1, sort_keys=True)
        say(f"\n-> {os.path.relpath(out, HERE)}")
    return 0


STATUS = 1
try:
    STATUS = main(sys.argv[1:])
except BaseException:
    say("SLOT NUTS RAISED:")
    say(traceback.format_exc())
finally:
    os._exit(STATUS)
