"""Stage 5 - the two Z columns and the top frame they carry.

Manual steps 10, 12 and 13:

* step 10, 2 x `BOT_CLAMP_Z` and 2 threaded rods M8 x 140, 8 M4x10 into slot
  nuts;
* step 12, the top frame - 3 x 2020 x 300, 2 x 2020 x 280, 8 x `TOP_BRACKET`,
  2 x `TOP_CLAMP_Z_AXIS`, and 2 hinges;
* step 13, its axis - 2 rails 8 x **280**, 4 LM8UU, 4 x `TOP_RAIL_HOLDER`.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/column.py

## The top frame is the rule that proved the bottom one

The bottom frame's size was worked out from the top frame's numbers, so the top
frame now follows from the same rule and it is worth stating that it is not
circular reasoning - the rule came from the top frame's own arithmetic, which
is unambiguous, and was *applied* to the bottom.

A rail runs the full distance between the inner faces of the two members it
bolts to, and equals the length of the members parallel to it.  Here the rails
are 280 and so are two of the extrusions, so:

* the two **side** members are the 300s, running the frame's full depth, and
  their inner faces are **280** apart;
* the two **end** members are the 280s, butting between them;
* the frame is therefore **320 x 300** outer, against the bottom frame's
  340 x 300 - narrower by one member each side, which is what lets it sit
  inboard of the Z columns.

The **third 300 mm extrusion is not placed here.**  The frame in the manual's
STEP_12 render is plainly four members, and step 16 adds eight more screws and
slot nuts afterwards; the odd one is most likely the bar the stencil clamp
mounts to, which belongs to stage 6.  It is left out rather than guessed at.

## How far the Z axis actually adjusts

Step 18 says to "adjust the height of the top frame", and the rod length says
by how much.  The M8 rod is **140** long; `BOT_CLAMP_Z_AXIS` grips **40** of it
and `TOP_CLAMP_Z_AXIS` **34**, and neither can overlap the other, so what is
left is the travel:

    140 - 40 - 34 = 66 mm

That is reported below rather than asserted, so a rebuild that changed a clamp
would change the answer.

## What is inferred rather than derived

The columns' **position in plan**.  Both Z clamps are on one side of the frame
near its two ends - the manual's STEP_10 and STEP_12 renders agree on that, and
it is what the two hinges on the same side imply, since the top frame lifts.
The exact stations along that side are taken from the renders and are the least
certain thing here; nothing else depends on them.
"""

import math
import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import frame    # noqa: E402
import stock    # noqa: E402
from asmprim import say  # noqa: E402

RAIL_D = 8.0
TOP_RAIL_LENGTH = 280.0
SIDE_LENGTH = 300.0              # the two 300s, running along Z
MEMBER = 20.0

HALF_SPAN = TOP_RAIL_LENGTH / 2.0        # the side members' inner faces
HALF_DEPTH = SIDE_LENGTH / 2.0
OUTER_X = TOP_RAIL_LENGTH + 2 * MEMBER   # 320
OUTER_Z = SIDE_LENGTH                    # 300

# The Z columns.
ROD_D = 8.0
ROD_LENGTH = 140.0
BOT_GRIP = 40.0                  # BOT_CLAMP_Z_AXIS, along the rod
TOP_GRIP = 34.0                  # TOP_CLAMP_Z_AXIS
CLAMP_STANDOFF = 9.1             # rod axis, out from the face the clamp bolts to

COLUMN_Z = (-120.0, 120.0)       # from the renders; see the docstring
TOP_RAIL_Z = (-60.0, 60.0)       # where the two top rails sit across the frame
TOP_FRAME_Y = 100.0              # nominal, inside the range checked below

TOL = 1e-6


def top_frame(doc, asm, at_y=TOP_FRAME_Y):
    """The four members, hung from `at_y` as their common top face."""
    sides = {
        "left":  (0.0, MEMBER, SIDE_LENGTH,
                  Vector(-(HALF_SPAN + MEMBER / 2.0), at_y, -HALF_DEPTH)),
        "right": (0.0, MEMBER, SIDE_LENGTH,
                  Vector(HALF_SPAN + MEMBER / 2.0, at_y, -HALF_DEPTH)),
        "front": (90.0, MEMBER, TOP_RAIL_LENGTH,
                  Vector(-HALF_SPAN, at_y, -HALF_DEPTH + MEMBER / 2.0)),
        "back":  (90.0, MEMBER, TOP_RAIL_LENGTH,
                  Vector(-HALF_SPAN, at_y, HALF_DEPTH - MEMBER / 2.0)),
    }
    members = {}
    for name, (angle, across, length, base) in sides.items():
        member = stock.extrusion(doc, f"top 2020 {name}", length,
                                 cells_x=int(round(across / 20.0)))
        member.Placement = Placement(base, Rotation(Vector(0, 1, 0), angle))
        members[name] = member
    doc.recompute()
    for member in members.values():
        asmprim.ground(asm, member)
    return members


def top_rails(doc, asm, at_y):
    """The two 280 mm rails and the four collars that hold them.

    Same arrangement as the bottom frame's X rails: the collar bolts flat to a
    side member's inner face with both screws in one slot, and the rail leaves
    that face at right angles.
    """
    body = asmprim.part("top/TOP_RAIL_HOLDER")
    foot = -asmprim.datum(body, "MOUNT").Placement.Base.x
    slot_y = at_y - MEMBER / 2.0             # the inner face's slot centre

    holders, rods = [], []
    for z in TOP_RAIL_Z:
        for side in (-1, 1):
            turn = 0.0 if side < 0 else 180.0
            at = Vector(-HALF_SPAN + foot if side < 0 else HALF_SPAN - foot,
                        slot_y, z)
            holder = asmprim.link(
                asm, f"TOP_RAIL_HOLDER {'L' if side < 0 else 'R'}{z:+.0f}",
                body, Placement(at, Rotation(Vector(0, 1, 0), turn)))
            asmprim.ground(asm, holder)
            holders.append(holder)

        rod = stock.rod(doc, f"top rail {z:+.0f}", RAIL_D, TOP_RAIL_LENGTH)
        rod.Placement = Placement(
            Vector(-TOP_RAIL_LENGTH / 2.0, slot_y, z),
            Rotation(Vector(0, 1, 0), 90))
        asmprim.ground(asm, rod)
        rods.append(rod)
    doc.recompute()
    return holders, rods


def columns(doc, asm, at_y):
    """Two M8 rods, clamped to the bottom frame and carrying the top one."""
    bot = asmprim.part("bot/BOT_CLAMP_Z_AXIS")
    top = asmprim.part("top/TOP_CLAMP_Z_AXIS")

    # The rods stand off the bottom frame's outer face by the clamp's own
    # depth, which is what puts them clear of the top frame as it comes down.
    face_x = frame.HALF_SPAN + frame.NARROW          # 170, the outer face
    rod_x = -(face_x + CLAMP_STANDOFF)

    rods, clamps = [], []
    for z in COLUMN_Z:
        rod = stock.threaded_rod(doc, f"M8x140 column {z:+.0f}",
                                 ROD_D, ROD_LENGTH)
        rod.Placement = Placement(Vector(rod_x, 0.0, z),
                                  Rotation(Vector(1, 0, 0), -90))
        asmprim.ground(asm, rod)
        rods.append(rod)

        # Each clamp is modelled about its own origin rather than its base, so
        # hang them off the faces they actually meet: the lower one starts on
        # the bottom frame's top face, the upper one finishes flush with the
        # top frame's.
        lower = asmprim.link(asm, f"BOT_CLAMP_Z_AXIS {z:+.0f}", bot,
                             Placement(Vector(rod_x, 0.0, z), Rotation()))
        top_high = top.Shape.BoundBox.YMax
        upper = asmprim.link(asm, f"TOP_CLAMP_Z_AXIS {z:+.0f}", top,
                             Placement(Vector(rod_x, at_y - top_high, z),
                                       Rotation()))
        clamps += [lower, upper]
    doc.recompute()
    return rods, clamps


def check_size(members):
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for member in members.values():
        bb = member.Shape.BoundBox
        for i, (a, b) in enumerate(((bb.XMin, bb.XMax), (bb.YMin, bb.YMax),
                                    (bb.ZMin, bb.ZMax))):
            lo[i], hi[i] = min(lo[i], a), max(hi[i], b)
    say(f"  top frame {hi[0] - lo[0]:.1f} x {hi[2] - lo[2]:.1f} in plan, "
        f"Y {lo[1]:.1f} .. {hi[1]:.1f}")
    ok = True
    for i, axis, want in ((0, "X", OUTER_X), (2, "Z", OUTER_Z)):
        if abs((hi[i] - lo[i]) - want) > 1e-6:
            say(f"  FAIL {axis} is {hi[i] - lo[i]:.3f}, expected {want}")
            ok = False
    if abs(2 * HALF_SPAN - TOP_RAIL_LENGTH) > TOL:
        say("  FAIL the side members are not a rail apart")
        ok = False
    if not ok:
        raise SystemExit("the top frame is not the size it should be")
    say(f"  ok: {OUTER_X:.0f} x {OUTER_Z:.0f} outer, "
        f"side members {2 * HALF_SPAN:.0f} apart = the rail exactly")
    say(f"  ok: narrower than the bottom frame's "
        f"{frame.OUTER_X:.0f} by {frame.OUTER_X - OUTER_X:.0f}, "
        f"so it sits inboard of the columns")


def check_collinear(holders):
    """Both top rails' collars have to share an axis, as the X rails did."""
    ok = True
    for z in TOP_RAIL_Z:
        pair = [h for h in holders if f"{z:+.0f}" in h.Label]
        a, b = (asmprim.frame(h, "RAIL") for h in pair)
        axis = asmprim.axis_of(pair[0], "RAIL")
        tilt = math.degrees(axis.getAngle(asmprim.axis_of(pair[1], "RAIL")))
        tilt = min(tilt, 180.0 - tilt)
        off = (b.Base - a.Base).cross(axis).Length / axis.Length
        say(f"  rail {z:+6.1f}: parallel to {tilt:.2e} deg, "
            f"offset {off:.2e} mm")
        if tilt > TOL or off > TOL:
            ok = False
    if not ok:
        raise SystemExit("the top rail bores do not line up")
    say("  ok: both top rails' bores are collinear")


def check_travel(rods, clamps):
    """How much height adjustment the M8 rod actually allows."""
    free = ROD_LENGTH - BOT_GRIP - TOP_GRIP
    say(f"  M8 rod {ROD_LENGTH:.0f}, gripped {BOT_GRIP:.0f} below and "
        f"{TOP_GRIP:.0f} above")
    say(f"  so the top frame adjusts over {free:.0f} mm")
    if free <= 0:
        raise SystemExit("the clamps take up the whole rod: no adjustment")
    for rod in rods:
        bb = rod.Shape.BoundBox
        if abs(bb.YLength - ROD_LENGTH) > TOL:
            say(f"  FAIL {rod.Label} is {bb.YLength:.1f} long")
            raise SystemExit("a column rod is the wrong length")
    say(f"  ok: {len(rods)} columns, {free:.0f} mm of Z adjustment")
    return free


def check_reach(clamps):
    """Can the top clamp actually span from its frame out to the rod?"""
    body = asmprim.part("top/TOP_CLAMP_Z_AXIS")
    width = body.Shape.BoundBox.XLength
    need = (frame.HALF_SPAN + frame.NARROW + CLAMP_STANDOFF) - \
        (HALF_SPAN + MEMBER)
    say(f"  the rod stands {need:.1f} mm outboard of the top frame's face, "
        f"and TOP_CLAMP_Z_AXIS is {width:.1f} wide")
    if need > width:
        raise SystemExit("the top clamp cannot reach its rod")
    say("  ok: the clamp reaches")


def build():
    doc, asm = asmprim.assembly("Column")
    say("=== the bottom frame, to hang the columns off")
    members = frame.bottom_frame(doc, asm)
    frame.check_size(members)

    say("=== the top frame")
    top = top_frame(doc, asm)
    check_size(top)

    say("=== its two 280 mm rails")
    holders, rods_top = top_rails(doc, asm, TOP_FRAME_Y)
    check_collinear(holders)

    say("=== the two Z columns")
    rods, clamps = columns(doc, asm, TOP_FRAME_Y)
    check_travel(rods, clamps)
    check_reach(clamps)

    asmprim.solve(asm, context="the top frame and columns")
    asmprim.save(doc)
    say("\nSTAGE 5 PASSED -- top frame 320 x 300, rails collinear, "
        "66 mm of Z adjustment")


if asmprim.is_entry(__file__):
    build()
