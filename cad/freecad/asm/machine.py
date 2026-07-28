"""Stage 7 - the whole machine, in one document, at a given pose.

Everything the earlier stages built, assembled together and then checked as a
whole:

    frame.py      the bottom frame and its feet
    carriage.py   the X rails, the print plate, the Y rails
    alpha.py      the slewing ring between its two plates
    column.py     the Z columns and the top frame

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/machine.py

## The pose

The machine has four axes and this builds it at one setting of them.  X and Y
are where the carriage sits along its rails, Z is the top frame's height on its
columns, and alpha is the rotation of the top plate.  Change `POSE` and
everything moves with it, which is the point of having built it out of joints
and datums rather than fixed placements.

## How the alpha axis meets the carriage

The one join the earlier stages did not make.  The alpha assembly rides the Y
rails: four LM8UU slide on them and the fixed plate is clamped down to those,
so the underside of `ALPHA_BOT_PLATE` sits on top of the bearings.  With the Y
rail axis at Y = 3.6 and an LM8UU 15 mm across, that puts it at **11.1**.

That is the least certain number in this file.  Manual step 6 says only "clip
the Alpha Axis Assembly to the LM8UU bearings", and step 7's four
`BOT_RAIL_CLAMP_*` are what do the clipping - they are modelled in stage 6, so
until then the plate rests directly on the bearings rather than on the clamps
that will eventually hold it. Whatever they add, they add it here.

## What is not in it yet

The lead screws, the springs and the handwheels (steps 7 to 9), the worm and
its shaft, and everything in stage 6 - the stencil clamp and the eccentrics.
The envelope below is therefore the machine's structure, not its full extent.
"""

import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import alpha     # noqa: E402
import asmprim   # noqa: E402
import carriage  # noqa: E402
import check     # noqa: E402
import column    # noqa: E402
import fasteners # noqa: E402
import frame     # noqa: E402
from asmprim import say  # noqa: E402

# One setting of the four axes.  X and Y are the carriage along its rails -- the
# author's names, so his Y is our Z -- Z is the top frame on its columns, and
# alpha is the turn of the top plate.
POSE = {"x": 0.0, "y": 0.0, "z": column.TOP_FRAME_Y, "alpha": 0.0}

# The two parts of the slewing ring that turn with alpha.
TURNS_WITH_ALPHA = ("SR_OUTER_RING_W_GEAR", "ALPHA_TOP_PLATE")

# Pairs that are meant to touch: a rod is a sliding fit in its bearing, and a
# clamp is meant to close on what it holds.
IGNORE = (("rail", "LM8UU"), ("rail", "RAIL_HOLDER"),
          ("rail", "BEARING_MOUNT"), ("column", "CLAMP_Z"), ("rail", "CLAMP"))

# The alpha assembly's fixed plate lands on top of the LM8UU that ride the Y
# rails, so its height comes from where the mounts put those rails.
LM8UU_OUTER = 15.0


def alpha_seat(mounts):
    """Y of the alpha assembly's underside: the top of an LM8UU on a Y rail."""
    return asmprim.frame(mounts[0], "TROUGH").Base.y + LM8UU_OUTER / 2.0


def alpha_axis(doc, asm, at_y, turn):
    """The slewing ring stack, lifted onto the carriage and turned.

    The turn is applied to the two parts that actually rotate -- the toothed
    outer ring and the plate bolted to it -- and not to the three that do not.
    """
    made, low, high = alpha.stack(doc, asm)
    lift = at_y - (low - alpha.PLATE_THICKNESS)
    spin = Rotation(Vector(0, 1, 0), turn)
    for name, link in made.items():
        turning = name in TURNS_WITH_ALPHA
        base = link.Placement
        link.Placement = Placement(
            Vector(0, lift, 0),
            spin if turning else Rotation()).multiply(base)
    doc.recompute()
    return made


def slide(links, offset):
    """Move a group of already-placed parts bodily, without disturbing them."""
    for link in links:
        link.Placement = Placement(offset, Rotation()).multiply(link.Placement)


def travel_limit(doc, axis, group, step=5.0, reach=200.0, riding=None):
    """How far a group can be driven before something touches.

    Walked outwards a step at a time rather than solved for, because what stops
    an axis is whichever pair of parts meets first and that is not known in
    advance.  The group is put back where it started afterwards.
    """
    unit = Vector(1, 0, 0) if axis == "x" else Vector(0, 0, 1)
    names = {link.Label for link in group}
    limits = []
    for sense in (1.0, -1.0):
        limit = 0.0
        moved = 0.0
        while moved < reach:
            slide(group, unit * (step * sense))
            moved += step
            doc.recompute()
            if check.interference(doc, lambda *a: None, ignore=IGNORE,
                                  only=names):
                break
            if riding is not None and not check.on_its_rod(riding):
                break
            limit = moved
        slide(group, unit * (-moved * sense))
        doc.recompute()
        limits.append(limit)
    return limits


# How far each layer is lifted in an exploded view.  Ordered bottom to top, so
# the machine comes apart the way it goes together.
EXPLODE = (
    ("STAND", -60.0),
    ("2020", 0.0), ("2040", 0.0),
    ("BOT_RAIL_HOLDER", 0.0), ("X rail", 0.0),
    ("LM8UU -", 40.0), ("LM8UU +", 40.0),
    ("BOT_BEARING_MOUNT_X_AXIS", 70.0),
    ("XY_PLATE", 55.0),
    ("Y rail", 90.0), ("LM8UU Y", 100.0),
    ("ALPHA_BOT_PLATE", 130.0), ("SR_BEARING_PLATE", 155.0),
    ("SR_INNER_RING", 175.0), ("SR_OUTER_RING_W_GEAR", 195.0),
    ("ALPHA_TOP_PLATE", 220.0),
    ("BOT_CLAMP_Z_AXIS", 0.0), ("M8x140 column", 30.0),
    ("TOP_CLAMP_Z_AXIS", 60.0),
    ("top 2020", 90.0), ("TOP_RAIL_HOLDER", 110.0), ("top rail", 110.0),
)


def explode(doc, amount=1.0):
    """Lift each layer clear of the one below, so the stack can be read.

    An exploded view is an offset applied to parts that are already assembled,
    not a second model -- which is the whole reason for keeping the machine in
    one document at a known pose.
    """
    lifted = 0
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is None or not shape.Solids:
            continue
        if obj.TypeId in check.CONTAINERS:
            continue
        for tag, rise in EXPLODE:
            if obj.Label.startswith(tag):
                if rise:
                    obj.Placement = Placement(
                        Vector(0, rise * amount, 0),
                        Rotation()).multiply(obj.Placement)
                    lifted += 1
                break
    doc.recompute()
    return lifted


# Where screws go, and what the manual buys for them.  A BOLT datum sits on the
# face the part is bolted *to*, with its axis pointing out of the part -- but
# which side the screw comes in from differs, so `enters` says which:
#
#   "far"   the head is counterbored at the other end and the screw runs
#           along the datum's axis, into whatever it is pulling on
#   "face"  the screw comes up from outside the datum face and runs back into
#           the part, so its head sits proud of that face
#
# ISO 4762's head is as tall as the thread is wide, which is what sets the
# head-side offset.
# `through` is material *outside* the datum face that the screw also passes
# on its way in.  The bearing mounts are the case that matters: their four M3
# come up through the print plate as well as the mount's own foot, and 2 + 4
# is exactly the M3x6 the manual buys for them.
BOLTED = (
    ("BOT_RAIL_HOLDER", "M4", 10.0, 11.4, 0.0, "slot", "far"),
    ("BOT_BEARING_MOUNT_X_AXIS", "M3", 6.0, 4.0,
     carriage.PLATE_THICKNESS, None, "face"),
    ("TOP_RAIL_HOLDER", "M4", 10.0, 11.4, 0.0, "slot", "far"),
)
HEAD = {"M3": 3.0, "M4": 4.0, "M5": 5.0, "M8": 8.0}


def bolt_up(doc, links):
    """Put a screw in every BOLT datum the placed parts carry.

    The datums were added for the joints; using them for the fasteners too
    means the screws land wherever the part says its holes are, rather than
    being positioned a second time and allowed to disagree.
    """
    placed = 0
    for link in links:
        body = link.LinkedObject
        for tag, size, length, grip, through, nut, enters in BOLTED:
            if not body.Label.startswith(tag):
                continue
            i = 1
            while True:
                try:
                    seat = asmprim.frame(link, f"BOLT{i}")
                except SystemExit:
                    break
                out = seat.Rotation.multVec(Vector(0, 0, 1))
                if enters == "far":
                    run, head_at = out, seat.Base - out * grip
                else:
                    run = -out
                    head_at = seat.Base + out * (through + HEAD[size])
                fasteners.bolt_through(
                    doc, size, length, head_at,
                    axis=(run.x, run.y, run.z),
                    with_nut=nut, grip=through + grip)
                placed += 1
                i += 1
            break
    doc.recompute()
    return placed


def build(pose=None):
    pose = dict(POSE, **(pose or {}))
    doc, asm = asmprim.assembly("Machine")

    say(f"=== pose: X {pose['x']:.0f}, Y {pose['y']:.0f}, "
        f"Z {pose['z']:.0f}, alpha {pose['alpha']:.0f} deg")

    say("=== bottom frame and feet")
    members = frame.bottom_frame(doc, asm)
    frame.check_size(members)
    frame.stands(doc, asm, members)

    say("=== the XY carriage")
    holders = carriage.rail_holders(doc, asm)
    rods = carriage.rails(doc, asm)
    x_bearings = carriage.bearings(doc, asm, rods)
    mounts = carriage.bearing_mounts(doc, asm)
    plate = carriage.print_plate(doc, asm, mounts)
    y_rods = carriage.y_rails(doc, asm, mounts)
    carriage.check_collinear(holders)
    carriage.check_bolts_land(mounts, plate)

    say("=== the alpha axis, on the Y rails")
    seat = alpha_seat(mounts)
    say(f"  its fixed plate rests at Y {seat:.1f}, on top of the LM8UU")
    stack = alpha_axis(doc, asm, seat, pose["alpha"])

    y_bearings = carriage.y_bearings(doc, asm, mounts, y_rods)

    # What each axis actually carries.  The alpha stack rides the Y rails, and
    # everything on the print plate rides the X rails -- including the Y rails
    # themselves and, through them, the alpha stack.
    on_y = list(stack.values()) + [b for b, _ in y_bearings]
    on_x = list(mounts) + [plate] + y_rods + on_y

    say("=== driving the axes")
    x_plus, x_minus = travel_limit(doc, "x", on_x, riding=x_bearings)
    y_plus, y_minus = travel_limit(doc, "y", on_y, riding=y_bearings)
    say(f"  X travels +{x_plus:.0f} / -{x_minus:.0f} mm before something "
        f"touches")
    say(f"  Y travels +{y_plus:.0f} / -{y_minus:.0f} mm")
    say(f"  so the work area is {x_plus + x_minus:.0f} x "
        f"{y_plus + y_minus:.0f} mm")

    before = plate.Placement.Base
    slide(on_x, Vector(pose["x"], 0, 0))
    slide(on_y, Vector(0, 0, pose["y"]))
    doc.recompute()
    if pose["x"] > x_plus or -pose["x"] > x_minus or \
            pose["y"] > y_plus or -pose["y"] > y_minus:
        raise SystemExit("the commanded pose is beyond the machine's travel")
    went = plate.Placement.Base - before
    say(f"  ok: driven to X {pose['x']:+.0f}, Y {pose['y']:+.0f} -- "
        f"the plate moved {went.Length:.0f} mm")

    say("=== the Z columns and the top frame")
    top = column.top_frame(doc, asm, pose["z"])
    column.check_size(top)
    top_holders, _ = column.top_rails(doc, asm, pose["z"])
    rods_z, clamps = column.columns(doc, asm, pose["z"])
    column.check_travel(rods_z, clamps)

    asmprim.solve(asm, context="the whole machine")

    say("=== the fasteners the manual buys for what is built")
    screws = bolt_up(doc, list(holders) + list(mounts) + list(top_holders))
    say(f"  {screws} screws placed, from the parts' own BOLT datums")

    say("=== interference")
    clashes = check.interference(doc, say, ignore=IGNORE)

    say("=== envelope")
    check.envelope(doc, say)

    asmprim.save(doc)

    say("=== exploded view")
    lifted = explode(doc)
    doc.recompute()
    exploded = os.path.join(asmprim.HERE, "MachineExploded.FCStd")
    doc.saveAs(exploded)
    say(f"  lifted {lifted} parts clear, saved {os.path.basename(exploded)}")

    if clashes:
        raise SystemExit(f"{len(clashes)} pairs of parts overlap")
    say("\nSTAGE 7 PASSED -- the whole machine stands up with nothing "
        "fouling")
    return doc


if asmprim.is_entry(__file__):
    build()
