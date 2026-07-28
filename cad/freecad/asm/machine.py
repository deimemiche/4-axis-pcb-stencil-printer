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
import frame     # noqa: E402
from asmprim import say  # noqa: E402

# One setting of the four axes.  X and Y are the carriage along its rails, Z is
# the top frame on its columns, alpha is the turn of the top plate.
POSE = {"x": 0.0, "y": 0.0, "z": column.TOP_FRAME_Y, "alpha": 0.0}

# The alpha assembly's fixed plate lands on top of the LM8UU that ride the Y
# rails, so its height comes from where the mounts put those rails.
LM8UU_OUTER = 15.0


def alpha_seat(mounts):
    """Y of the alpha assembly's underside: the top of an LM8UU on a Y rail."""
    return asmprim.frame(mounts[0], "TROUGH").Base.y + LM8UU_OUTER / 2.0


def alpha_axis(doc, asm, at_y, turn):
    """The slewing ring stack, lifted onto the carriage and turned."""
    made, low, high = alpha.stack(doc, asm)
    lift = at_y - (low - alpha.PLATE_THICKNESS)
    spin = Rotation(Vector(0, 1, 0), turn)
    for name, link in made.items():
        turning = name in ("SR_OUTER_RING_W_GEAR", "ALPHA_TOP_PLATE")
        base = link.Placement
        link.Placement = Placement(
            Vector(0, lift, 0),
            spin if turning else Rotation()).multiply(base)
    doc.recompute()
    return made


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
    carriage.bearings(doc, asm, rods)
    mounts = carriage.bearing_mounts(doc, asm)
    plate = carriage.print_plate(doc, asm, mounts)
    carriage.y_rails(doc, asm, mounts)
    carriage.check_collinear(holders)
    carriage.check_bolts_land(mounts, plate)

    say("=== the alpha axis, on the Y rails")
    seat = alpha_seat(mounts)
    say(f"  its fixed plate rests at Y {seat:.1f}, on top of the LM8UU")
    alpha_axis(doc, asm, seat, pose["alpha"])

    say("=== the Z columns and the top frame")
    top = column.top_frame(doc, asm, pose["z"])
    column.check_size(top)
    column.top_rails(doc, asm, pose["z"])
    rods_z, clamps = column.columns(doc, asm, pose["z"])
    column.check_travel(rods_z, clamps)

    asmprim.solve(asm, context="the whole machine")

    say("=== interference")
    clashes = check.interference(
        doc, say,
        # A rod is a sliding fit in its bearing and a clamp is meant to close
        # on what it holds, so those pairs are expected to touch.
        ignore=(("rail", "LM8UU"), ("rail", "RAIL_HOLDER"),
                ("rail", "BEARING_MOUNT"), ("column", "CLAMP_Z"),
                ("rail", "CLAMP")))

    say("=== envelope")
    check.envelope(doc, say)

    asmprim.save(doc)
    if clashes:
        raise SystemExit(f"{len(clashes)} pairs of parts overlap")
    say("\nSTAGE 7 PASSED -- the whole machine stands up with nothing "
        "fouling")
    return doc


if asmprim.is_entry(__file__):
    build()
