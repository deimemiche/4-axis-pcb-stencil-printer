"""Stage 1 - the machine datum, and the bottom frame it is anchored to.

The bottom frame is four extrusions, all 300 mm, **butt jointed** into a
rectangle: two run the full length and the other two land between them.  The
build manual's step 1 lists them as 1 x 2040 x 300 and 3 x 2020 x 300.

That makes the frame **360 x 300**, not the 300 x 300 square it was first
modelled as, and the difference matters because the X rails hang off it.

Four things settle it, and they agree:

* **The corners are butt joints, not mitres.**  Zoom the manual's own STEP_1
  render on a corner and an extrusion's *end face* is visible, T-slots and all.
  A mitre would show a diagonal face.
* **The rail length is the span.**  The top frame is the same idea one storey
  up and its numbers are unambiguous: 2 x 2020 x 280 between two 300 mm
  members, and its rails are 8 mm x **280**.  So a rail runs the full distance
  between the inner faces of the two members it is bolted to, and equals the
  length of the members parallel to it.
* **The side members are therefore 300 apart.**  The X rails are 300 and run
  between their inner faces, so that spacing is fixed.
* **The 2040 is a side member, and lies flat.**  Butt joints do not care how
  wide a member is, so it can lie flat at 40 x 20 -- and then every member's
  top and bottom are flush and the four feet stand level, which as a mitred
  square they could not, as `check_level` said by failing.  That it is a
  *side* member rather than an end one was settled by the assembly itself:
  `machine.py`'s interference check found the X rails and the print plate
  driving straight through it when it was modelled across the front.

Adding a 40 and a 20 to the 300 gives **360 x 300**.  The frame is therefore
**not symmetric about the machine origin** -- the origin follows the rails,
which is what everything else is measured from, and the 2040's extra 20 mm
hangs off one side.  The X axis mounts on it, which is what
`BOT_BRACKET_X_AXIS` is for.

Run it directly:

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/frame.py

## The datum

One origin for the whole machine, **Y up**, matching every part script:

* **Y = 0 is the frame's top face.**  Everything the machine is built from
  stands on that face, so heights read directly as "how far above the frame".
* **X = 0, Z = 0 is the centre of the X rails**, which run -150 .. +150.  The
  frame reaches -190 .. +170 across, because the 2040 side is 20 mm wider than
  its opposite number, so the outline is not symmetric even though the axes
  are.

`stock.extrusion` therefore puts a section's **top** at its own local Y = 0
rather than centring it, so members of different heights hang from a common top
surface instead of needing an offset each.

## What the parts themselves say about it

Two groups were exported in assembly position rather than about a part origin,
and where they land under an identity placement is evidence about the author's
own datum.  `check_datum()` below reports it rather than assuming it, and what
it finds is this:

* the **SR** group stacks cleanly -- outer ring and inner ring both start at
  Y = -2, the inner ring ends at Y = 8 and the bearing plate runs 8 .. 11 --
  and all of it is centred on X = Z = 0;
* the **ECCF** group stacks just as cleanly -- bottom -18 .. -10, height
  -10 .. 0, then mount and top both from 0 -- centred on X = 0.

So each group carries its own **sub-assembly** datum, and a good one.  What
neither carries is a *machine* datum: the alpha axis and the front eccentric
are each drawn about their own centre, and nothing in the meshes relates one to
the other.  That is worth being explicit about, because "the parts are already
in assembly position" is true within a group and false between groups.
"""

import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import stock    # noqa: E402
from asmprim import say  # noqa: E402

# Every member is 300 long; the manual gives no other length.
MEMBER_LENGTH = 300.0
NARROW = 20.0            # a 2020 across the plan
WIDE = 40.0              # the one 2040, lying flat
TALL = 20.0              # all of them are one cell tall
STAND_DROP = 7.0         # how far a foot stands below the frame

# The X rails are 300 and run between the inner faces of the two side members,
# which is what sets the frame's width.
RAIL_SPAN = 300.0
HALF_SPAN = RAIL_SPAN / 2.0                  # the side members' inner faces
HALF_DEPTH = MEMBER_LENGTH / 2.0             # the side members run this far

# Side members run the full length along Z and the rails bolt to their inner
# faces; end members land between them.
#
# **The 2040 is a side member, not an end member**, and the assembly is what
# settled that.  Lying flat it is 40 mm across in plan, so as an end member it
# would reach from Z = -150 to -110 -- and the X rails sit at Z = +-111 with
# the print plate reaching +-128.5.  `machine.py`'s interference check found
# them driving straight through it.  As a *side* member it is clear of both,
# because the rails run between the side members rather than across them.
#
# That makes the frame 360 x 300 and **not symmetric about the machine origin**:
# the origin stays on the rails, which is what everything else is measured
# from, and the extra 20 mm of the 2040 hangs off one side.  The X axis mounts
# on it, which is what BOT_BRACKET_X_AXIS is for.
WIDE_SIDE = "left"
SIDES = {
    "left":  (0.0, WIDE, Vector(-(HALF_SPAN + WIDE / 2.0), 0.0, -HALF_DEPTH)),
    "right": (0.0, NARROW, Vector(HALF_SPAN + NARROW / 2.0, 0.0, -HALF_DEPTH)),
    # Turned a quarter turn so their length runs along X instead.
    "front": (90.0, NARROW, Vector(-HALF_SPAN, 0.0,
                                   -HALF_DEPTH + NARROW / 2.0)),
    "back":  (90.0, NARROW, Vector(-HALF_SPAN, 0.0,
                                   HALF_DEPTH - NARROW / 2.0)),
}

OUTER_X = RAIL_SPAN + NARROW + WIDE          # 360
OUTER_Z = MEMBER_LENGTH                      # 300


def bottom_frame(doc, asm):
    """The four extrusions, placed and grounded."""
    members = {}
    for name, (angle, across, base) in SIDES.items():
        cells_x = int(round(across / 20.0))
        label = f"{'2040' if cells_x == 2 else '2020'} {name}"
        member = stock.extrusion(doc, label, MEMBER_LENGTH, cells_x=cells_x)
        member.Placement = Placement(base, Rotation(Vector(0, 1, 0), angle))
        members[name] = member
    doc.recompute()
    # The frame is what everything else is measured from, so it is the thing
    # that gets grounded; every other joint chain hangs off it.
    for member in members.values():
        asmprim.ground(asm, member)
    return members


def stands(doc, asm, members):
    """The four printed feet, one under each corner.

    STAND is modelled growing from its own Y = 0, and in the machine that face
    is the one bolted up against the underside of the frame, so each is turned
    over and hung from the member above it.
    """
    body = asmprim.part("misc/STAND")
    corner_x = HALF_SPAN + NARROW / 2.0      # the 2020 side's centre line
    corner_z = HALF_DEPTH - NARROW / 2.0     # in from each end
    feet = []
    for i, (sx, sz) in enumerate(((-1, -1), (-1, 1), (1, 1), (1, -1))):
        at = Vector(sx * corner_x, -TALL, sz * corner_z)
        foot = asmprim.link(asm, f"STAND {i + 1}", body,
                            Placement(at, Rotation(Vector(1, 0, 0), 180.0)))
        feet.append(foot)
    doc.recompute()
    return feet


def check_size(members):
    """The frame must come out the size the build page says it is."""
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for member in members.values():
        bb = member.Shape.BoundBox
        for i, (a, b) in enumerate(((bb.XMin, bb.XMax), (bb.YMin, bb.YMax),
                                    (bb.ZMin, bb.ZMax))):
            lo[i], hi[i] = min(lo[i], a), max(hi[i], b)
    say(f"  frame {hi[0] - lo[0]:.1f} x {hi[2] - lo[2]:.1f} mm in plan, "
        f"Y {lo[1]:.1f} .. {hi[1]:.1f}")
    ok = True
    for i, axis, want in ((0, "X", OUTER_X), (2, "Z", OUTER_Z)):
        if abs((hi[i] - lo[i]) - want) > 1e-6:
            say(f"  FAIL {axis} is {hi[i] - lo[i]:.3f}, expected {want}")
            ok = False
    # Z is symmetric about the origin; X is not, because the 2040 side member
    # is 20 mm wider than its opposite number.  The origin follows the rails,
    # not the outline.
    if abs(lo[2] + hi[2]) > 1e-6:
        say("  FAIL Z is not centred on the origin")
        ok = False
    if abs(abs(lo[0]) - (HALF_SPAN + WIDE)) > 1e-6:
        say(f"  FAIL the 2040 side is at {lo[0]:.1f}, "
            f"expected {-(HALF_SPAN + WIDE):.1f}")
        ok = False
    if abs(hi[1]) > 1e-6:
        say(f"  FAIL the top face is at Y = {hi[1]:.3f}, expected 0")
        ok = False

    # The whole point of the width: an X rail has to reach from one side
    # member's inner face to the other, and it is 300 long.
    gap = 2 * HALF_SPAN
    if abs(gap - RAIL_SPAN) > 1e-6:
        say(f"  FAIL the side members are {gap:.3f} apart, "
            f"but the X rail is {RAIL_SPAN}")
        ok = False
    if not ok:
        raise SystemExit("the bottom frame is not the size it should be")
    say(f"  ok: {OUTER_X:.0f} x {OUTER_Z:.0f} outer, top face on Y = 0, "
        f"the 2040 hanging off the {WIDE_SIDE}")
    say(f"  ok: side members {gap:.0f} apart, which is the X rail exactly")


def check_level(feet):
    """Do all four feet reach the floor?

    This is the assembly earning its keep on its first day.  `WIDE_SIDE` is
    modelled as a 2040 standing 40 mm tall, hanging 20 mm below the three
    2020s, and the consequence is that the two feet on that side finish 20 mm
    lower than the other two: the machine would rock on a flat surface, which a
    stencil printer plainly does not.

    So the model is telling us the assumption is probably wrong, and the 2040
    is more likely 40 mm **wide** lying flat, with every member 20 mm tall and
    the frame uniform in height.  That reading has its own problem -- a 40 mm
    member cannot mitre into 20 mm neighbours -- so it is not a change to make
    silently.  It is written up as the first open question in ASSEMBLY.md; this
    reports the discrepancy rather than hiding it.
    """
    bottoms = sorted(round(f.Shape.BoundBox.YMin, 3) for f in feet)
    say(f"  4 stands, resting on Y = {', '.join(f'{b:.1f}' for b in bottoms)}")
    spread = bottoms[-1] - bottoms[0]
    if spread > 1e-6:
        say(f"  NOTE the feet are not level -- {spread:.1f} mm between the "
            f"highest and lowest.")
        say("       See open question 1 in ASSEMBLY.md: this is the 2040's "
            "orientation")
        say("       showing up, and it wants confirming against the real "
            "machine.")
    else:
        say(f"  ok: level, the machine rests on Y = {bottoms[0]:.1f}")


def check_datum():
    """Report where the two pre-positioned groups actually sit.

    This is the cheap test the plan asks for before anything is built on top of
    the datum: it prints, it does not assume.
    """
    groups = {
        "sr": ("SR_OUTER_RING_W_GEAR", "SR_INNER_RING", "SR_BEARING_PLATE"),
        "eccf": ("ECCF_BOT", "ECCF_HEIGHT", "ECCF_MOUNT", "ECCF_TOP"),
    }
    for folder, names in groups.items():
        say(f"  {folder}/ with an identity placement:")
        for name in names:
            bb = asmprim.part(f"{folder}/{name}").Shape.BoundBox
            say(f"    {name:24s} X[{bb.XMin:7.2f},{bb.XMax:7.2f}] "
                f"Y[{bb.YMin:7.2f},{bb.YMax:7.2f}] "
                f"Z[{bb.ZMin:7.2f},{bb.ZMax:7.2f}]")


def build():
    doc, asm = asmprim.assembly("BottomFrame")
    say("=== the four extrusions")
    members = bottom_frame(doc, asm)
    check_size(members)

    say("=== the four feet")
    feet = stands(doc, asm, members)
    asmprim.solve(asm, context="placing the frame and feet")
    check_level(feet)

    say("=== what the pre-positioned groups say about the datum")
    check_datum()

    asmprim.save(doc)
    say("\nSTAGE 1 PASSED -- datum fixed, bottom frame and feet stand up")


if asmprim.is_entry(__file__):
    build()
