"""Stage 7 - the whole machine, in one document, at a given pose.

Everything the earlier stages built, assembled together and then checked as a
whole:

    frame.py      the bottom frame and its feet
    carriage.py   the X rails, the print plate, the Y rails
    alpha.py      the slewing ring between its two plates
    column.py     the Z columns, the hinge bar and the lid
    stencil.py    the clamp, on the lid's rails
    eccentric.py  what the lid comes down onto

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/machine.py

## The pose

The machine has four axes and this builds it at one setting of them.  X and Y
are where the carriage sits along its rails, Z is the hinge bar's height on its
columns, and alpha is the rotation of the top plate.  Change `POSE` and
everything moves with it, which is the point of having built it out of joints
and datums rather than fixed placements.

There is a fifth number in `POSE` that is not an axis: **`lid`**, the angle the
stencil frame is swung up to.  It is not a degree of freedom you set and print
at -- it is open or it is shut -- but it is how the machine is *used*, and a
model that cannot show it open is not a model of a stencil printer.  Build it
at `lid = 60` to see what putting a board in looks like.

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
import drive      # noqa: E402
import eccentric  # noqa: E402
import frame      # noqa: E402
import stencil    # noqa: E402
from asmprim import say  # noqa: E402

# One setting of the four axes.  X and Y are the carriage along its rails, Z is
# the top frame on its columns, alpha is the turn of the top plate.
# Z is the top frame's own height, and `None` means "down on the eccentrics",
# which is where the machine works; see eccentric.py for where 65 comes from.
POSE = {"x": 0.0, "y": 0.0, "z": None, "alpha": 0.0, "lid": 0.0}

# Pairs that are meant to touch: a rod is a sliding fit in its bearing, a clamp
# closes on what it holds, a nut grips its screw and a worm meshes with its
# wheel.  Everything else overlapping is a mistake.
TOUCHING = (
    ("rail", "LM8UU"), ("rail", "RAIL_HOLDER"), ("rail", "BEARING_MOUNT"),
    ("rail", "CLAMP"), ("column", "CLAMP_Z"), ("column", "LM8UU"),
    ("screw", "nut"), ("screw", "spring"), ("screw", "HANDWHEEL"),
    ("screw", "CLAMP"), ("screw", "BRACKET_X"), ("screw", "MOUNT_Y"),
    ("shaft", "ROD_HOLDER"), ("shaft", "WORM"), ("shaft", "HANDWHEEL"),
    ("WORM_GEAR", "OUTER_RING"), ("nut", "spring"),
    ("STAND", "BOT_BRACKETS"),
    # The mod's Z axis: the bearing is a press fit in the mount that holds it.
    # The rod needs no pair of its own -- it runs in the bracket's 8.2 collar
    # and in the bearing's own bore, and clears both.  It had one while that
    # collar had no bore drilled in it at all, and this pair was the only thing
    # standing between that and being noticed.
    ("LM8UU", "TOP_Z_AXIS"),
    # A nut in a spring loaded drive is captured in the arm's own pocket.
    ("nut", "RAIL_CLAMP"), ("nut", "BEARING_MOUNT"),
    ("spring", "RAIL_CLAMP"), ("spring", "BEARING_MOUNT"),
    # The stencil clamp slides on the lid's rails, and its angles are bolted
    # to the mounts that carry them.
    ("rail", "SPRING_PLATE"), ("rail", "spring"), ("rail", "CLAMP_STOP"),
    ("STENCIL_HOLDER", "CLAMP_BEARING"), ("spring", "SPRING_PLATE"),
    ("STENCIL_HOLDER", "NUT_HOLDER"), ("CLAMP_BEARING", "SPRING_PLATE"),
    # A hinge is two leaves on one pin, screwed to the two bars it joins.
    ("hinge", "hinge"), ("hinge", "2020"), ("hinge", "lid 2020"),
    # The hinge lock's channel closes on the member it hooks, and its two M4
    # go straight through that member -- they are 24 long, which is a 4 mm wall
    # and a 20 mm extrusion exactly, so the extrusion is drilled through.  The
    # stock section here has no such holes, so the bolts have nowhere to be and
    # what shows instead is the block closing on the bar.
    ("HINGE_LOCK", "lid 2020"), ("HINGE_LOCK", "HINGE_LOCK"),
    # A clamp bar is a pair of angles with the foil pinched between them.
    ("STENCIL_HOLDER", "stencil foil"), ("STENCIL_HOLDER", "STENCIL_HOLDER"),
    ("stencil foil", "NUT_HOLDER"),
    ("spring", "CLAMP_STOP"),
    # An eccentric's rod starts down in the extrusion's own slot, where its
    # bottom nuts are.
    ("eccenter", "2020"),
    # An eccentric is one stack of parts that grip each other, on one rod.
    ("ECCF", "ECCF"), ("ECCF", "eccenter"),
)

# Not fits, and not excused: pairs the model gets wrong because something about
# the real machine is still not understood.  They print as OPEN every build so
# they stay visible instead of quietly becoming furniture.
#
# It was empty, and it took finding out that the stencil clamp sits beside its
# rails rather than under them to empty it; see stencil.py.  Keep it as near
# empty as it will go -- a pair belongs here only while it is being worked out.
#
# **The hand levers foul the lid's right hand member by 88 mm3.**  Michael's
# levers point outward, away from the machine, which is what a hand lever has
# to do and what `eccentric.py` now builds; turning them that way swings each
# hub inboard to x 130, and on the +X side that is under the lid.  The levers
# are right and something else here is not: the eccenter body they pivot on was
# never published, so the hub's true height and offset are the one part of this
# assembly taken from the lever alone.  Left open rather than nudged until the
# number goes away, because the number is the evidence.
OPEN_PAIRS = (("lid 2020", "ECCF_LEVER"),)

# The other half of the same idea, for `check.connected`: parts that touch
# nothing because the thing they hold is not in the repository at all.
#
# There is exactly one, and the connectedness check is what turned it up.  A
# hand lever is a *pair* of cheeks that grip the eccenter's shaft between them,
# 6 mm apart -- and `eccf/` has ECCF_BOT, _HEIGHT, _MOUNT, _TOP and _LEVER but
# **no eccenter body**.  The author never published it, the way he never
# published the back eccentric's ECCB_*.  The inner cheek happens to land
# against `ECCF_TOP`; the outer one has nothing to reach, and saying so is
# more use than moving it until it touches something.
ADRIFT = ("ECCF_LEVER",)


def build(pose=None, name=None):
    pose = dict(POSE, **(pose or {}))
    if pose["z"] is None:
        # Down at its working height, which is where the clamp just clears the
        # work surface; the eccentrics' own stack lands within a hair of it.
        pose["z"] = stencil.working_height(eccentric.BOARD_Y)
    name = name or ("Machine" if not pose["lid"] else "MachineOpen")
    doc, asm = asmprim.assembly(name)

    say(f"=== pose: X {pose['x']:.0f}, Y {pose['y']:.0f}, "
        f"Z {pose['z']:.0f}, alpha {pose['alpha']:.0f} deg, "
        f"lid {pose['lid']:.0f} deg")

    say("=== bottom frame, brackets and feet")
    members = frame.bottom_frame(doc, asm)
    frame.check_size(members)
    frame.step1(doc, asm)
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
    clamps = drive.rail_clamps(doc, asm, mounts)

    say("=== the alpha axis, on the Y rails")
    seat = drive.rail_y(mounts) + drive.alpha_seat()
    say(f"  its fixed plate hangs at Y {seat:.1f}, a bearing holder's flange "
        f"above the rail")
    stack = alpha.place(doc, asm, seat, pose["alpha"])
    fixed = asmprim.part("plate/ALPHA_BOT_PLATE")
    bearings = drive.lm8uu_mounts(doc, asm, drive.rail_y(mounts), fixed)

    say("=== the three screws")
    _, shaft_x, axis_y = drive.worm_drive(doc, asm, alpha.plate_top(seat),
                                          fixed)
    drive.check_mesh(shaft_x, axis_y, stack["SR_OUTER_RING_W_GEAR"])
    bracket = [o for o in asm.Group if o.Label == "BOT_BRACKET_X_AXIS"][0]
    drive.x_screw(doc, asm, bracket,
                  clamps[("bot/BOT_RAIL_CLAMP_X_DRIVE", -1, -1)])
    driven = [b for b in bearings if "DRIVEN" in b.Label][0]
    drive.y_screw(doc, asm, driven,
                  clamps[("bot/BOT_RAIL_CLAMP_Y_AXIS_1", -1, 1)])

    say(f"=== the Z columns and the hinge bar, down at y {pose['z']:.0f}")
    lid = column.lid_placement(pose["z"], pose["lid"])
    bar = column.hinge_bar(doc, asm, pose["z"])
    rods_z, clamps_z = column.columns(doc, asm, pose["z"])
    column.check_travel(rods_z, clamps_z)
    column.check_reach(rods_z, bar)

    say(f"=== the lid, swung {pose['lid']:.0f} degrees off it")
    top = column.top_frame(doc, asm, pose["z"], lid)
    column.hinges(doc, asm, pose["z"], lid)
    column.check_size(top, bar, lid)
    holders_top, _ = column.top_rails(doc, asm, pose["z"], lid)
    column.check_collinear(holders_top)
    hook, plate = column.hinge_locks(doc, asm, pose["z"], lid, pose["lid"])
    column.check_lock(hook, plate)
    column.check_lap(hook)

    say("=== the stencil clamp on the lid's rails")
    stencil.check_seat()
    stencil.check_pair()
    bars = stencil.bar_stations()
    gear, rail_y = stencil.running_gear(doc, asm, pose["z"], bars, lid)
    stencil.clamp_bars(doc, asm, bars, rail_y, lid)
    stencil.nut_holders(doc, asm, bars, rail_y, lid)
    stencil.foil(doc, asm, bars, rail_y, lid)
    if not pose["lid"]:
        stencil.check_foil(bars, rail_y, eccentric.BOARD_Y)

    say("=== the four eccentrics")
    eccentric.eccentrics(doc, asm)
    eccentric.check_stack()
    if not pose["lid"]:
        eccentric.check_gap(pose["z"])
        eccentric.check_reach(pose["z"])

    asmprim.solve(asm, context="the whole machine")

    say("=== interference")
    clashes = check.interference(doc, say, ignore=TOUCHING,
                                 open_pairs=OPEN_PAIRS)

    say("=== is it one machine, or a pile of parts?")
    loose = check.connected(doc, say, adrift=ADRIFT)

    say("=== envelope")
    check.envelope(doc, say)

    asmprim.save(doc)
    if clashes:
        raise SystemExit(f"{len(clashes)} pairs of parts overlap")
    if loose:
        raise SystemExit(f"{len(loose)} groups of parts are held by nothing")
    say("\nSTAGE 7 PASSED -- the whole machine stands up in one piece with "
        "nothing fouling")
    return doc


def main(argv):
    """Any of the pose's numbers can be given on the command line.

        ... asm/machine.py                 the machine as it works
        ... asm/machine.py lid=60          the same, with the stencil lifted
        ... asm/machine.py alpha=15 x=20   somewhere else on its axes

    An open lid is saved as `MachineOpen` rather than over the top of the one
    that is set up to print, so both can be looked at.
    """
    pose = {}
    for arg in argv:
        if "=" in arg and not arg.endswith(".py"):
            key, value = arg.split("=", 1)
            if key not in POSE:
                raise SystemExit(f"{key} is not one of {', '.join(POSE)}")
            pose[key] = float(value)
    build(pose or None)


if asmprim.is_entry(__file__):
    main(sys.argv[1:])
